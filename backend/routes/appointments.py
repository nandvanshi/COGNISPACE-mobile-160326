"""
Appointment management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user, log_audit

router = APIRouter(prefix="/appointments", tags=["appointments"])


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

@router.post("/client-request", response_model=Appointment)
async def client_request_appointment(appt_data: ClientAppointmentRequest, current_user: dict = Depends(get_current_user)):
    """Client requests an appointment with their assigned therapist"""
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
    
    existing = await db.appointments.find_one({
        "therapist_id": therapist_id,
        "status": {"$ne": "cancelled"},
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
        "status": "scheduled",
        "actual_start_time": None,
        "actual_end_time": None,
        "actual_duration_minutes": None,
        "checked_in_by": None,
        "checked_out_by": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment_doc)
    await log_audit(current_user["id"], "client", "create", "appointment", appointment_id, {"booked_by_client": True})
    
    # Get therapist name and send notifications
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
    therapist_name = therapist["full_name"] if therapist else "Your Therapist"
    
    # Send in-app notification
    try:
        from routes.notifications import notify_client_appointment_confirmed
        formatted_time = f"{appointment_doc['start_time'][:10]} {appointment_doc['start_time'][11:16]}"
        await notify_client_appointment_confirmed(
            current_user["id"],
            therapist_name,
            formatted_time,
            appointment_id
        )
    except Exception as e:
        print(f"Failed to send in-app notification: {e}")
    
    # Send email confirmation
    try:
        from services.email import EmailService
        duration = int((appt_data.end_time - appt_data.start_time).total_seconds() / 60)
        await EmailService.send_appointment_confirmation_email(
            client_id=current_user["id"],
            therapist_id=therapist_id,
            therapist_name=therapist_name,
            appointment_time=appointment_doc["start_time"],
            duration=duration
        )
    except Exception as e:
        print(f"Failed to send appointment confirmation email: {e}")
    
    # Notify therapist about client booking
    try:
        from routes.notifications import notify_therapist_appointment_booked
        await notify_therapist_appointment_booked(
            therapist_id,
            current_user["full_name"],
            formatted_time,
            appointment_id
        )
    except Exception as e:
        print(f"Failed to notify therapist: {e}")
    
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "appointment", appointment_id)
    
    # Send in-app notification to client about appointment confirmation
    try:
        from routes.notifications import notify_client_appointment_confirmed
        # Format time nicely
        formatted_time = f"{appointment_doc['start_time'][:10]} {appointment_doc['start_time'][11:16]}"
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
        await EmailService.send_appointment_confirmation_email(
            client_id=appt_data.client_id,
            therapist_id=therapist_id,
            therapist_name=therapist_name,
            appointment_time=appointment_doc["start_time"],
            duration=duration
        )
    except Exception as e:
        print(f"Failed to send appointment confirmation email: {e}")
    
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
async def cancel_appointment(appointment_id: str, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Cancel appointment"""
    therapist_id = get_effective_therapist_id(current_user)
    
    result = await db.appointments.update_one(
        {"id": appointment_id, "therapist_id": therapist_id},
        {"$set": {"status": "cancelled"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
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
