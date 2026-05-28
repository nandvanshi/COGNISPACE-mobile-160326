"""
Appointment management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from dependencies import get_current_user, log_audit
from services.notification_service import NotificationService
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/appointments", tags=["appointments"])

# IST timezone
IST_TZ = ZoneInfo("Asia/Kolkata")
IST_OFFSET = timedelta(hours=5, minutes=30)

def format_datetime_ist(dt_str: str) -> tuple:
    """Convert ISO datetime string to IST date and time strings"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        ist_dt = dt + IST_OFFSET
        return ist_dt.strftime("%d/%m/%Y"), ist_dt.strftime("%H:%M")
    except Exception:
        return dt_str[:10], dt_str[11:16] if len(dt_str) > 16 else "N/A"


# ============= APPOINTMENT MODELS =============

class AppointmentCreate(BaseModel):
    client_id: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ClientAppointmentRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    status: str = "scheduled"
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    checked_in_by: Optional[str] = None
    checked_out_by: Optional[str] = None
    created_at: datetime


# ============= DEPENDENCIES =============

def get_effective_therapist_id(user: dict) -> str:
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None


async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Therapist or Assistant access required")
    return current_user


async def require_active_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "therapist":
        if current_user.get("subscription_status") not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Subscription expired")
        return current_user
    elif current_user["role"] == "assistant":
        therapist = await db.users.find_one({"id": current_user.get("therapist_id")}, {"_id": 0})
        if not therapist or therapist.get("subscription_status") not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Therapist subscription expired")
        return current_user
    raise HTTPException(status_code=403, detail="Access denied")


def parse_datetime(value):
    """Helper to parse datetime from string"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


# ============= APPOINTMENT ENDPOINTS =============

@router.get("/available-slots")
async def get_client_available_slots(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get available appointment slots for the client's assigned therapist"""
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can access this endpoint")
    
    therapist_id = current_user.get("therapist_id")
    if not therapist_id:
        profile = await db.client_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if profile:
            therapist_id = profile.get("therapist_id")
    
    if not therapist_id:
        raise HTTPException(status_code=400, detail="No therapist assigned to your account")
    
    # Get therapist profile for session duration
    therapist_profile = await db.therapist_profiles.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0, "session_duration": 1}
    )
    session_duration = therapist_profile.get("session_duration", 60) if therapist_profile else 60
    
    # Parse date - treat as IST date (the date the user selected in their IST calendar)
    if date:
        try:
            # If full ISO string, parse and get the IST date
            parsed = datetime.fromisoformat(date.replace('Z', '+00:00'))
            ist_date = parsed.astimezone(IST_TZ).date()
        except ValueError:
            # Simple YYYY-MM-DD format
            ist_date = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        ist_date = datetime.now(IST_TZ).date()
    
    # Create IST midnight for this date (availability hours are in IST)
    start_date_ist = datetime(ist_date.year, ist_date.month, ist_date.day, tzinfo=IST_TZ)
    
    # Get therapist's availability settings
    availability = await db.therapist_availability.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not availability:
        return {"slots": [], "message": "No availability configured"}
    
    # Get existing appointments to exclude (broad range to handle both old IST-in-UTC and new correct UTC formats)
    broad_start = (start_date_ist - timedelta(hours=6)).astimezone(timezone.utc)
    broad_end = (start_date_ist + timedelta(days=1, hours=6)).astimezone(timezone.utc)
    existing_appts = await db.appointments.find({
        "therapist_id": therapist_id,
        "start_time": {"$gte": broad_start.isoformat(), "$lt": broad_end.isoformat()},
        "status": {"$nin": ["cancelled", "no_show"]}
    }, {"_id": 0, "start_time": 1, "end_time": 1}).to_list(100)
    
    booked_times = [(a["start_time"], a["end_time"]) for a in existing_appts]
    
    # Generate available slots
    available_slots = []
    day_name = start_date_ist.strftime("%A").lower()
    
    # Support both formats: weekly_schedule.{day} or direct {day} key
    day_availability = availability.get("weekly_schedule", {}).get(day_name)
    if not day_availability:
        day_availability = availability.get(day_name, {})
    
    if day_availability.get("enabled", False):
        # Get time blocks - support both old format (start/end) and new format (time_blocks)
        time_blocks = day_availability.get("time_blocks", [])
        
        if time_blocks:
            # New format with time_blocks array
            for block in time_blocks:
                start_time = block.get("start_time") or block.get("start") or "09:00"
                end_time = block.get("end_time") or block.get("end") or "17:00"
                
                start_hour, start_min = map(int, start_time.split(":"))
                end_hour, end_min = map(int, end_time.split(":"))
                
                # Availability hours are IST - create IST datetime then convert to UTC
                slot_start_ist = start_date_ist.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
                slot_start = slot_start_ist.astimezone(timezone.utc)
                
                slot_end_limit_ist = start_date_ist.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
                slot_end_limit = slot_end_limit_ist.astimezone(timezone.utc)
                
                while slot_start < slot_end_limit:
                    slot_end = slot_start + timedelta(minutes=session_duration)
                    
                    if slot_start > datetime.now(timezone.utc):
                        is_available = True
                        for booked_start, booked_end in booked_times:
                            booked_start_dt = datetime.fromisoformat(booked_start.replace('Z', '+00:00'))
                            booked_end_dt = datetime.fromisoformat(booked_end.replace('Z', '+00:00'))
                            
                            if not (slot_end <= booked_start_dt or slot_start >= booked_end_dt):
                                is_available = False
                                break
                        
                        if is_available:
                            available_slots.append({
                                "start_time": slot_start.isoformat(),
                                "end_time": slot_end.isoformat(),
                                "display_time": slot_start.astimezone(IST_TZ).strftime("%H:%M")
                            })
                    
                    slot_start = slot_end
        else:
            # Old format with direct start/end
            start_hour, start_min = map(int, day_availability.get("start", "09:00").split(":"))
            end_hour, end_min = map(int, day_availability.get("end", "18:00").split(":"))
            
            # Availability hours are IST
            slot_start_ist = start_date_ist.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            slot_start = slot_start_ist.astimezone(timezone.utc)
            
            slot_end_limit_ist = start_date_ist.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
            slot_end_limit = slot_end_limit_ist.astimezone(timezone.utc)
            
            while slot_start < slot_end_limit:
                slot_end = slot_start + timedelta(minutes=session_duration)
                
                if slot_start > datetime.now(timezone.utc):
                    is_available = True
                    for booked_start, booked_end in booked_times:
                        booked_start_dt = datetime.fromisoformat(booked_start.replace('Z', '+00:00'))
                        booked_end_dt = datetime.fromisoformat(booked_end.replace('Z', '+00:00'))
                        
                        if not (slot_end <= booked_start_dt or slot_start >= booked_end_dt):
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append({
                            "start_time": slot_start.isoformat(),
                            "end_time": slot_end.isoformat(),
                            "display_time": slot_start.astimezone(IST_TZ).strftime("%H:%M")
                        })
                
                slot_start = slot_end
            
            slot_start = slot_end
    
    return {"slots": available_slots, "session_duration": session_duration}


@router.post("/client-request", response_model=Appointment)
async def client_request_appointment(appt_data: ClientAppointmentRequest, current_user: dict = Depends(get_current_user)):
    """Client requests an appointment with their assigned therapist - requires therapist approval"""
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can request appointments via this endpoint")
    
    therapist_id = current_user.get("therapist_id")
    if not therapist_id:
        profile = await db.client_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if profile:
            therapist_id = profile.get("therapist_id")
    
    if not therapist_id:
        raise HTTPException(status_code=400, detail="No therapist assigned to your account")
    
    if appt_data.start_time >= appt_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    # Check for conflicts with scheduled or pending appointments
    existing = await db.appointments.find_one({
        "therapist_id": therapist_id,
        "status": {"$nin": ["cancelled", "declined"]},
        "$or": [
            {"start_time": {"$lt": appt_data.end_time.isoformat()}, "end_time": {"$gt": appt_data.start_time.isoformat()}}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Time slot no longer available. Please choose a different time.")
    
    appointment_id = str(uuid.uuid4())
    appointment_doc = {
        "id": appointment_id,
        "therapist_id": therapist_id,
        "client_id": current_user["id"],
        "client_name": current_user["full_name"],
        "start_time": appt_data.start_time.isoformat(),
        "end_time": appt_data.end_time.isoformat(),
        "notes": appt_data.notes,
        "status": "pending_approval",  # Requires therapist approval
        "booked_by_client": True,
        "actual_start_time": None,
        "actual_end_time": None,
        "actual_duration_minutes": None,
        "checked_in_by": None,
        "checked_out_by": None,
        "confirmation_email_sent": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment_doc)
    await log_audit(current_user["id"], "client", "create", "appointment", appointment_id, {"booked_by_client": True, "status": "pending_approval"})
    
    # Get therapist info
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1, "mobile": 1})
    therapist_name = therapist["full_name"] if therapist else "Your Therapist"
    therapist_mobile = therapist.get("mobile") if therapist else None
    
    # Notify therapist about new appointment request (in-app)
    try:
        from routes.notifications import create_notification
        formatted_date, formatted_time = format_datetime_ist(appointment_doc["start_time"])
        await create_notification(
            user_id=therapist_id,
            role="therapist",
            notification_type="appointment_request",
            title=f"New appointment request from {current_user['full_name']}",
            message=f"Requested for {formatted_date} at {formatted_time}. Please review and approve.",
            metadata={"appointment_id": appointment_id, "client_id": current_user["id"]}
        )
    except Exception as e:
        print(f"Failed to send therapist in-app notification: {e}")
    
    # Send WhatsApp to therapist about appointment request
    if therapist_mobile:
        try:
            await NotificationService.send_appointment_request_whatsapp_to_therapist(
                therapist_mobile=therapist_mobile,
                therapist_name=therapist_name,
                client_name=current_user["full_name"],
                appointment_datetime=appointment_doc["start_time"]
            )
        except Exception as e:
            print(f"Failed to send therapist WhatsApp: {e}")
    
    # Send confirmation to client that request is submitted
    try:
        from routes.notifications import create_notification
        formatted_date, formatted_time = format_datetime_ist(appointment_doc["start_time"])
        await create_notification(
            user_id=current_user["id"],
            role="client",
            notification_type="appointment_pending",
            title="Appointment Request Submitted",
            message=f"Your request for {formatted_date} at {formatted_time} with {therapist_name} has been submitted. Waiting for approval.",
            metadata={"appointment_id": appointment_id}
        )
    except Exception as e:
        print(f"Failed to send client notification: {e}")
    
    return Appointment(
        id=appointment_doc["id"],
        therapist_id=appointment_doc["therapist_id"],
        client_id=appointment_doc["client_id"],
        client_name=appointment_doc["client_name"],
        start_time=parse_datetime(appointment_doc["start_time"]),
        end_time=parse_datetime(appointment_doc["end_time"]),
        notes=appointment_doc["notes"],
        status=appointment_doc["status"],
        created_at=parse_datetime(appointment_doc["created_at"])
    )


@router.post("", response_model=Appointment)
async def create_appointment(appt_data: AppointmentCreate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Create appointment - therapist or assistant"""
    therapist_id = get_effective_therapist_id(current_user)
    
    client = await db.users.find_one({"id": appt_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if appt_data.start_time >= appt_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    existing = await db.appointments.find_one({
        "therapist_id": therapist_id,
        "status": {"$ne": "cancelled"},
        "$or": [
            {"start_time": {"$lt": appt_data.end_time.isoformat()}, "end_time": {"$gt": appt_data.start_time.isoformat()}}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Time slot conflicts with existing appointment")
    
    # Get therapist name for notifications
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
    therapist_name = therapist["full_name"] if therapist else "Your Therapist"
    
    appointment_id = str(uuid.uuid4())
    appointment_doc = {
        "id": appointment_id,
        "therapist_id": therapist_id,
        "client_id": appt_data.client_id,
        "client_name": client["full_name"],
        "start_time": appt_data.start_time.isoformat(),
        "end_time": appt_data.end_time.isoformat(),
        "notes": appt_data.notes,
        "status": "scheduled",
        "actual_start_time": None,
        "actual_end_time": None,
        "actual_duration_minutes": None,
        "checked_in_by": None,
        "checked_out_by": None,
        "confirmation_email_sent": False,  # Track instant email confirmation
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "appointment", appointment_id)
    
    # Send in-app notification to client about appointment confirmation
    try:
        from routes.notifications import notify_client_appointment_confirmed
        # Format time in IST
        appt_date_ist, appt_time_ist = format_datetime_ist(appointment_doc['start_time'])
        formatted_time = f"{appt_date_ist} {appt_time_ist}"
        await notify_client_appointment_confirmed(
            appointment_doc["client_id"],
            therapist_name,
            formatted_time,
            appointment_id
        )
    except Exception as e:
        print(f"Failed to send in-app notification: {e}")
    
    # Send email confirmation to client
    try:
        from services.email import EmailService
        # Calculate duration in minutes
        duration = int((appt_data.end_time - appt_data.start_time).total_seconds() / 60)
        email_result = await EmailService.send_appointment_confirmation_email(
            client_id=appt_data.client_id,
            therapist_id=therapist_id,
            therapist_name=therapist_name,
            appointment_time=appointment_doc["start_time"],
            duration=duration
        )
        # Mark confirmation email as sent to avoid duplicate from scheduler
        if email_result.success:
            await db.appointments.update_one(
                {"id": appointment_id},
                {"$set": {"confirmation_email_sent": True}}
            )
    except Exception as e:
        print(f"Failed to send appointment confirmation email: {e}")
    
    # Send email confirmation to THERAPIST
    try:
        from services.email import EmailService
        duration = int((appt_data.end_time - appt_data.start_time).total_seconds() / 60)
        
        # Check therapist's notification preferences
        therapist_notif_pref = await db.notification_preferences.find_one(
            {"user_id": therapist_id, "event": "appointment_confirmation"},
            {"_id": 0}
        )
        send_therapist_email = therapist_notif_pref.get("send_email", True) if therapist_notif_pref else True
        send_therapist_whatsapp = therapist_notif_pref.get("send_whatsapp", False) if therapist_notif_pref else False
        
        if send_therapist_email:
            await EmailService.send_notification_email(
                to_user_id=therapist_id,
                event="appointment_confirmation_therapist",
                data={
                    "client_name": client["full_name"],
                    "appointment_time": appointment_doc["start_time"],
                    "duration": duration,
                    "appointment_type": appt_data.notes or "Session",
                    "dashboard_url": "/dashboard"
                },
                therapist_id=therapist_id,
                force=False
            )
        
        # Send WhatsApp to therapist if opted-in
        if send_therapist_whatsapp:
            from services.whatsapp import WhatsAppService
            therapist_user = await db.users.find_one({"id": therapist_id}, {"_id": 0, "mobile": 1})
            if therapist_user and therapist_user.get("mobile") and WhatsAppService.is_configured():
                appt_date, appt_time = format_datetime_ist(appointment_doc["start_time"])
                await WhatsAppService.send_text_message(
                    to_number=therapist_user.get("mobile"),
                    message=f"New Appointment: {client['full_name']} on {appt_date} at {appt_time}"
                )
    except Exception as e:
        print(f"Failed to send therapist appointment notification: {e}")
    
    # Send email confirmation to ASSISTANT (if exists)
    try:
        from services.email import EmailService
        assistants = await db.users.find({
            "role": "assistant",
            "therapist_id": therapist_id,
            "status": "active"
        }, {"_id": 0, "id": 1, "email": 1, "mobile": 1}).to_list(10)
        
        for assistant in assistants:
            asst_notif_pref = await db.notification_preferences.find_one(
                {"user_id": assistant.get("id"), "event": "appointment_confirmation"},
                {"_id": 0}
            )
            send_asst_email = asst_notif_pref.get("send_email", True) if asst_notif_pref else True
            
            if send_asst_email and assistant.get("email"):
                await EmailService.send_notification_email(
                    to_user_id=assistant.get("id"),
                    event="appointment_confirmation_therapist",
                    data={
                        "client_name": client["full_name"],
                        "appointment_time": appointment_doc["start_time"],
                        "duration": duration,
                        "appointment_type": appt_data.notes or "Session",
                        "dashboard_url": "/dashboard"
                    },
                    therapist_id=therapist_id,
                    force=False
                )
    except Exception as e:
        print(f"Failed to send assistant appointment notification: {e}")
    
    # Send WhatsApp confirmation to client using approved template
    try:
        # Calculate duration in minutes
        duration = int((appt_data.end_time - appt_data.start_time).total_seconds() / 60)
        await NotificationService.send_appointment_confirmation(
            client_name=client["full_name"],
            client_mobile=client.get("mobile"),
            client_email=client.get("email"),
            therapist_name=therapist_name,
            appointment_datetime=appointment_doc["start_time"],
            duration=duration
        )
    except Exception as e:
        print(f"Failed to send appointment confirmation notifications: {e}")
    
    return Appointment(
        id=appointment_doc["id"],
        therapist_id=appointment_doc["therapist_id"],
        client_id=appointment_doc["client_id"],
        client_name=appointment_doc["client_name"],
        start_time=parse_datetime(appointment_doc["start_time"]),
        end_time=parse_datetime(appointment_doc["end_time"]),
        notes=appointment_doc["notes"],
        status=appointment_doc["status"],
        created_at=parse_datetime(appointment_doc["created_at"])
    )


@router.get("", response_model=List[Appointment])
async def get_appointments(
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get appointments - filtered by role"""
    if current_user["role"] == "client":
        query = {"client_id": current_user["id"]}
    elif current_user["role"] in ["therapist", "assistant"]:
        therapist_id = get_effective_therapist_id(current_user)
        query = {"therapist_id": therapist_id}
        if client_id:
            query["client_id"] = client_id
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if status:
        query["status"] = status
    
    appointments = await db.appointments.find(query, {"_id": 0}).sort("start_time", -1).to_list(500)
    
    return [Appointment(
        id=a["id"],
        therapist_id=a["therapist_id"],
        client_id=a["client_id"],
        client_name=a.get("client_name"),
        start_time=parse_datetime(a["start_time"]),
        end_time=parse_datetime(a["end_time"]),
        notes=a.get("notes"),
        status=a.get("status", "scheduled"),
        actual_start_time=parse_datetime(a.get("actual_start_time")),
        actual_end_time=parse_datetime(a.get("actual_end_time")),
        actual_duration_minutes=a.get("actual_duration_minutes"),
        checked_in_by=a.get("checked_in_by"),
        checked_out_by=a.get("checked_out_by"),
        created_at=parse_datetime(a["created_at"])
    ) for a in appointments]


# ============= PUBLIC BOOKING APPROVAL ENDPOINTS =============
# NOTE: These routes MUST be defined before /{appointment_id} routes to avoid path conflicts

@router.get("/pending-approval")
async def get_pending_approval_appointments(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get all appointments pending approval from public booking"""
    therapist_id = get_effective_therapist_id(current_user)
    
    appointments = await db.appointments.find(
        {"therapist_id": therapist_id, "status": "pending_approval"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Enrich with client details
    for appt in appointments:
        client = await db.users.find_one(
            {"id": appt.get("client_id")},
            {"_id": 0, "full_name": 1, "email": 1, "mobile": 1}
        )
        if client:
            appt["client_name"] = client.get("full_name")
            appt["client_email"] = client.get("email")
            appt["client_mobile"] = client.get("mobile")
    
    return {"pending_appointments": appointments}


@router.get("/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    """Get single appointment"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if current_user["role"] == "client" and appointment["client_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user["role"] in ["therapist", "assistant"]:
        therapist_id = get_effective_therapist_id(current_user)
        if appointment["therapist_id"] != therapist_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return Appointment(
        id=appointment["id"],
        therapist_id=appointment["therapist_id"],
        client_id=appointment["client_id"],
        client_name=appointment.get("client_name"),
        start_time=parse_datetime(appointment["start_time"]),
        end_time=parse_datetime(appointment["end_time"]),
        notes=appointment.get("notes"),
        status=appointment.get("status", "scheduled"),
        actual_start_time=parse_datetime(appointment.get("actual_start_time")),
        actual_end_time=parse_datetime(appointment.get("actual_end_time")),
        actual_duration_minutes=appointment.get("actual_duration_minutes"),
        checked_in_by=appointment.get("checked_in_by"),
        checked_out_by=appointment.get("checked_out_by"),
        created_at=parse_datetime(appointment["created_at"])
    )


@router.put("/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, data: AppointmentUpdate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Update appointment"""
    therapist_id = get_effective_therapist_id(current_user)
    
    appointment = await db.appointments.find_one({"id": appointment_id, "therapist_id": therapist_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    update_data = {}
    if data.start_time:
        update_data["start_time"] = data.start_time.isoformat()
    if data.end_time:
        update_data["end_time"] = data.end_time.isoformat()
    if data.status:
        update_data["status"] = data.status
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    if update_data:
        await db.appointments.update_one({"id": appointment_id}, {"$set": update_data})
        await log_audit(current_user["id"], current_user["role"], "update", "appointment", appointment_id)
    
    updated = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    return Appointment(
        id=updated["id"],
        therapist_id=updated["therapist_id"],
        client_id=updated["client_id"],
        client_name=updated.get("client_name"),
        start_time=parse_datetime(updated["start_time"]),
        end_time=parse_datetime(updated["end_time"]),
        notes=updated.get("notes"),
        status=updated.get("status", "scheduled"),
        actual_start_time=parse_datetime(updated.get("actual_start_time")),
        actual_end_time=parse_datetime(updated.get("actual_end_time")),
        actual_duration_minutes=updated.get("actual_duration_minutes"),
        checked_in_by=updated.get("checked_in_by"),
        checked_out_by=updated.get("checked_out_by"),
        created_at=parse_datetime(updated["created_at"])
    )


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: str, 
    reason: str = "",
    current_user: dict = Depends(require_active_therapist_or_assistant)
):
    """Cancel appointment and send notifications"""
    therapist_id = get_effective_therapist_id(current_user)
    
    # Get appointment details before cancelling
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Cancel appointment
    result = await db.appointments.update_one(
        {"id": appointment_id, "therapist_id": therapist_id},
        {"$set": {
            "status": "cancelled",
            "cancelled_by": current_user["id"],
            "cancellation_reason": reason,
            "cancelled_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Get client, therapist, and assistant details for notifications
    client = await db.users.find_one({"id": appointment["client_id"]}, {"_id": 0})
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
    
    # Get assistant email if exists
    assistant_email = None
    assistant = await db.users.find_one(
        {"therapist_id": therapist_id, "role": "assistant"},
        {"_id": 0, "email": 1}
    )
    if assistant:
        assistant_email = assistant.get("email")
    
    # Send cancellation notifications
    try:
        await NotificationService.send_appointment_cancellation(
            client_name=client.get("full_name", "Client") if client else "Client",
            client_email=client.get("email") if client else None,
            therapist_name=therapist.get("full_name", "Therapist") if therapist else "Therapist",
            therapist_email=therapist.get("email") if therapist else None,
            assistant_email=assistant_email,
            appointment_datetime=appointment.get("start_time", ""),
            cancelled_by=current_user.get("full_name", current_user["role"]),
            cancellation_reason=reason
        )
    except Exception as e:
        print(f"Failed to send cancellation notifications: {e}")
    
    await log_audit(current_user["id"], current_user["role"], "cancel", "appointment", appointment_id)
    return {"message": "Appointment cancelled"}


@router.post("/{appointment_id}/check-in")
async def check_in_appointment(appointment_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Check-in to appointment"""
    therapist_id = get_effective_therapist_id(current_user)
    
    appointment = await db.appointments.find_one({"id": appointment_id, "therapist_id": therapist_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment.get("actual_start_time"):
        raise HTTPException(status_code=400, detail="Already checked in")
    
    now = datetime.now(timezone.utc)
    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {
            "actual_start_time": now.isoformat(),
            "checked_in_by": current_user["id"],
            "status": "in_progress"
        }}
    )
    
    await log_audit(current_user["id"], current_user["role"], "check_in", "appointment", appointment_id)
    return {"message": "Checked in", "actual_start_time": now.isoformat()}


@router.post("/{appointment_id}/check-out")
async def check_out_appointment(appointment_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Check-out from appointment"""
    therapist_id = get_effective_therapist_id(current_user)
    
    appointment = await db.appointments.find_one({"id": appointment_id, "therapist_id": therapist_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if not appointment.get("actual_start_time"):
        raise HTTPException(status_code=400, detail="Not checked in yet")
    
    if appointment.get("actual_end_time"):
        raise HTTPException(status_code=400, detail="Already checked out")
    
    now = datetime.now(timezone.utc)
    start_time = datetime.fromisoformat(appointment["actual_start_time"].replace('Z', '+00:00'))
    duration = int((now - start_time).total_seconds() / 60)
    
    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {
            "actual_end_time": now.isoformat(),
            "actual_duration_minutes": duration,
            "checked_out_by": current_user["id"],
            "status": "completed"
        }}
    )
    
    await log_audit(current_user["id"], current_user["role"], "check_out", "appointment", appointment_id)
    return {"message": "Checked out", "actual_end_time": now.isoformat(), "duration_minutes": duration}


@router.post("/{appointment_id}/mark-completed")
async def mark_appointment_completed(appointment_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Mark appointment as completed without check-in/out"""
    therapist_id = get_effective_therapist_id(current_user)
    
    result = await db.appointments.update_one(
        {"id": appointment_id, "therapist_id": therapist_id},
        {"$set": {"status": "completed"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    await log_audit(current_user["id"], current_user["role"], "complete", "appointment", appointment_id)
    return {"message": "Appointment marked as completed"}


@router.post("/{appointment_id}/no-show")
async def mark_no_show(appointment_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Mark appointment as no-show"""
    therapist_id = get_effective_therapist_id(current_user)
    
    result = await db.appointments.update_one(
        {"id": appointment_id, "therapist_id": therapist_id},
        {"$set": {"status": "no_show"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    await log_audit(current_user["id"], current_user["role"], "no_show", "appointment", appointment_id)
    return {"message": "Appointment marked as no-show"}


@router.post("/{appointment_id}/approve")
async def approve_appointment(appointment_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Approve a pending appointment from public booking"""
    therapist_id = get_effective_therapist_id(current_user)
    
    # Find appointment
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "therapist_id": therapist_id, "status": "pending_approval"},
        {"_id": 0}
    )
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found or already processed")
    
    # Check for time slot conflicts
    existing = await db.appointments.find_one({
        "therapist_id": therapist_id,
        "id": {"$ne": appointment_id},
        "status": {"$in": ["scheduled", "in_progress"]},
        "$or": [
            {"start_time": {"$lt": appointment["end_time"]}, "end_time": {"$gt": appointment["start_time"]}}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Time slot conflicts with existing appointment")
    
    # Approve appointment
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {
            "status": "scheduled",
            "approved_by": current_user["id"],
            "approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to approve appointment")
    
    # Get client and therapist info for notifications
    client = await db.users.find_one({"id": appointment["client_id"]}, {"_id": 0})
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1, "email": 1})
    
    # Create notification for client
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": appointment["client_id"],
        "role": "client",
        "type": "booking_approved",
        "title": "Appointment Confirmed",
        "message": f"Your appointment with {therapist['full_name']} on {appointment['start_time'][:10]} has been approved",
        "link": "appointments",
        "metadata": {"appointment_id": appointment_id},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification_doc)
    
    # Send email notification
    try:
        await NotificationService.send_appointment_confirmation(
            client_name=client.get("full_name", "Client") if client else "Client",
            client_mobile=client.get("mobile") if client else None,
            client_email=client.get("email") if client else None,
            therapist_name=therapist.get("full_name", "Therapist") if therapist else "Therapist",
            appointment_datetime=appointment.get("start_time", ""),
            duration=60
        )
    except Exception as e:
        print(f"Failed to send approval notification: {e}")
    
    await log_audit(current_user["id"], current_user["role"], "approve", "appointment", appointment_id)
    return {"message": "Appointment approved successfully", "status": "scheduled"}


@router.post("/{appointment_id}/decline")
async def decline_appointment(
    appointment_id: str, 
    reason: str = "",
    current_user: dict = Depends(require_therapist_or_assistant)
):
    """Decline a pending appointment from public booking"""
    therapist_id = get_effective_therapist_id(current_user)
    
    # Find appointment
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "therapist_id": therapist_id, "status": "pending_approval"},
        {"_id": 0}
    )
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found or already processed")
    
    # Decline appointment
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {
            "status": "declined",
            "declined_by": current_user["id"],
            "decline_reason": reason,
            "declined_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to decline appointment")
    
    # Get client and therapist info for notifications
    client = await db.users.find_one({"id": appointment["client_id"]}, {"_id": 0})
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
    
    # Create notification for client
    decline_message = f"Your appointment request with {therapist['full_name']} has been declined."
    if reason:
        decline_message += f" Reason: {reason}"
    
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": appointment["client_id"],
        "role": "client",
        "type": "booking_declined",
        "title": "Appointment Declined",
        "message": decline_message,
        "link": "appointments",
        "metadata": {"appointment_id": appointment_id},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification_doc)
    
    # Send email notification for declined booking
    try:
        if client and client.get("email"):
            await NotificationService.send_booking_declined_notification(
                client_email=client.get("email"),
                client_name=client.get("full_name", "Client"),
                therapist_name=therapist.get("full_name", "Therapist") if therapist else "Therapist",
                appointment_time=appointment.get("start_time", ""),
                reason=reason
            )
    except Exception as e:
        print(f"Failed to send decline notification: {e}")
    
    await log_audit(current_user["id"], current_user["role"], "decline", "appointment", appointment_id)
    return {"message": "Appointment declined", "status": "declined"}
