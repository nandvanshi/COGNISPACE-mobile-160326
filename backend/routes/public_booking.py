"""
Public Booking Routes - No authentication required
Allows external visitors to book appointments with therapists
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
from database import db
import uuid
import secrets
import string
import re
from passlib.context import CryptContext
from services.notification_service import NotificationService

router = APIRouter(prefix="/public", tags=["public-booking"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PublicBookingRequest(BaseModel):
    therapist_id: str
    slot_start: str  # ISO datetime
    slot_end: str    # ISO datetime
    # Client details
    full_name: str
    email: EmailStr
    mobile: str
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    notes: Optional[str] = None


def generate_password(length=10):
    """Generate a random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_client_id():
    """Generate unique client ID"""
    import random
    return f"CL-{random.randint(100000, 999999)}"


def generate_booking_slug(name: str) -> str:
    """Generate a URL-friendly slug from therapist name"""
    # Remove special characters and convert to lowercase
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    # Replace spaces with nothing (drdeepak style)
    slug = slug.replace(' ', '')
    # Remove common prefixes like 'dr' if at start and add back
    if slug.startswith('dr'):
        slug = 'dr' + slug[2:]
    return slug


async def get_therapist_by_slug_or_id(identifier: str):
    """Find therapist by slug or ID"""
    # First try to find by public_booking_slug
    profile = await db.therapist_profiles.find_one(
        {"public_booking_slug": identifier},
        {"_id": 0, "therapist_id": 1}
    )
    
    if profile:
        therapist_id = profile["therapist_id"]
    else:
        # Fallback to treating identifier as therapist_id
        therapist_id = identifier
    
    # Get therapist
    therapist = await db.users.find_one(
        {"id": therapist_id, "role": "therapist", "$or": [{"status": "approved"}, {"account_status": "approved"}]},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1}
    )
    
    return therapist, therapist_id


@router.get("/therapist/{identifier}")
async def get_public_therapist_profile(identifier: str):
    """Get therapist's public profile for booking page (by slug or ID)"""
    
    therapist, therapist_id = await get_therapist_by_slug_or_id(identifier)
    
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Get therapist profile
    profile = await db.therapist_profiles.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not profile:
        raise HTTPException(status_code=404, detail="Therapist profile not found")
    
    # Check if public booking is enabled
    if not profile.get("public_booking_enabled", False):
        raise HTTPException(status_code=403, detail="Public booking is not available for this therapist")
    
    # Generate or get slug
    slug = profile.get("public_booking_slug")
    if not slug:
        slug = generate_booking_slug(therapist["full_name"])
        # Save slug for future use
        await db.therapist_profiles.update_one(
            {"therapist_id": therapist_id},
            {"$set": {"public_booking_slug": slug}}
        )
    
    return {
        "id": therapist["id"],
        "name": therapist["full_name"],
        "slug": slug,
        "qualifications": profile.get("qualifications", ""),
        "specializations": profile.get("specializations", []),
        "bio": profile.get("bio", ""),
        "consultation_fee": profile.get("consultation_fee", 0),
        "session_duration": profile.get("session_duration", 60),
        "clinic_name": profile.get("clinic_name", ""),
        "clinic_address": profile.get("clinic_address", ""),
    }


@router.get("/therapist/{identifier}/slots")
async def get_public_available_slots(identifier: str, date: Optional[str] = None):
    """Get available slots for a therapist (public access)"""
    
    # Get therapist by slug or ID
    therapist, therapist_id = await get_therapist_by_slug_or_id(identifier)
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Verify public booking enabled
    profile = await db.therapist_profiles.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0, "public_booking_enabled": 1, "session_duration": 1}
    )
    
    if not profile or not profile.get("public_booking_enabled", False):
        raise HTTPException(status_code=403, detail="Public booking not available")
    
    # Get date range (default: next 7 days)
    if date:
        # Parse date string and make it timezone aware
        try:
            start_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except ValueError:
            # If just date without time, parse and add timezone
            start_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start_date = datetime.now(timezone.utc)
    
    # Ensure start_date has timezone info
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    
    end_date = start_date + timedelta(days=7)
    
    # Get therapist's availability settings
    availability = await db.therapist_availability.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not availability:
        # Return default slots if no availability set
        return {"slots": [], "message": "No availability configured"}
    
    # Get existing appointments to exclude
    existing_appts = await db.appointments.find({
        "therapist_id": therapist_id,
        "start_time": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()},
        "status": {"$nin": ["cancelled", "no_show"]}
    }, {"_id": 0, "start_time": 1, "end_time": 1}).to_list(100)
    
    booked_times = [(a["start_time"], a["end_time"]) for a in existing_appts]
    
    # Generate available slots based on availability
    available_slots = []
    session_duration = profile.get("session_duration", 60)
    
    current_date = start_date
    while current_date < end_date:
        day_name = current_date.strftime("%A").lower()
        
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
                    
                    slot_start = current_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
                    if slot_start.tzinfo is None:
                        slot_start = slot_start.replace(tzinfo=timezone.utc)
                    day_end = current_date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
                    if day_end.tzinfo is None:
                        day_end = day_end.replace(tzinfo=timezone.utc)
                    
                    while slot_start + timedelta(minutes=session_duration) <= day_end:
                        slot_end = slot_start + timedelta(minutes=session_duration)
                        slot_start_iso = slot_start.isoformat()
                        slot_end_iso = slot_end.isoformat()
                        
                        # Check if slot is available
                        is_booked = any(
                            (slot_start_iso >= b[0] and slot_start_iso < b[1]) or
                            (slot_end_iso > b[0] and slot_end_iso <= b[1])
                            for b in booked_times
                        )
                        
                        # Only include future slots
                        if not is_booked and slot_start > datetime.now(timezone.utc):
                            available_slots.append({
                                "start": slot_start_iso,
                                "end": slot_end_iso,
                                "display": slot_start.strftime("%I:%M %p")
                            })
                        
                        slot_start = slot_end
            else:
                # Old format with direct start/end
                start_hour, start_min = map(int, day_availability.get("start", "09:00").split(":"))
                end_hour, end_min = map(int, day_availability.get("end", "18:00").split(":"))
                
                slot_start = current_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
                if slot_start.tzinfo is None:
                    slot_start = slot_start.replace(tzinfo=timezone.utc)
                day_end = current_date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
                if day_end.tzinfo is None:
                    day_end = day_end.replace(tzinfo=timezone.utc)
                
                while slot_start + timedelta(minutes=session_duration) <= day_end:
                    slot_end = slot_start + timedelta(minutes=session_duration)
                    slot_start_iso = slot_start.isoformat()
                    slot_end_iso = slot_end.isoformat()
                    
                    # Check if slot is available
                    is_booked = any(
                        (slot_start_iso >= b[0] and slot_start_iso < b[1]) or
                        (slot_end_iso > b[0] and slot_end_iso <= b[1])
                        for b in booked_times
                    )
                    
                    # Only include future slots
                    if not is_booked and slot_start > datetime.now(timezone.utc):
                        available_slots.append({
                            "start": slot_start_iso,
                            "end": slot_end_iso,
                            "display": slot_start.strftime("%I:%M %p")
                        })
                    
                    slot_start = slot_end
        
        current_date += timedelta(days=1)
    
    return {"slots": available_slots}


@router.post("/book")
async def create_public_booking(booking: PublicBookingRequest):
    """Create a booking from public page - creates client account if needed"""
    
    # Verify therapist and public booking enabled
    profile = await db.therapist_profiles.find_one(
        {"therapist_id": booking.therapist_id},
        {"_id": 0, "public_booking_enabled": 1}
    )
    
    if not profile or not profile.get("public_booking_enabled", False):
        raise HTTPException(status_code=403, detail="Public booking not available")
    
    # Get therapist info
    therapist = await db.users.find_one(
        {"id": booking.therapist_id},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1}
    )
    
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Check if client already exists
    existing_client = await db.users.find_one(
        {"$or": [{"email": booking.email}, {"mobile": booking.mobile}]},
        {"_id": 0, "id": 1, "full_name": 1}
    )
    
    if existing_client:
        client_id = existing_client["id"]
        client_name = existing_client["full_name"]
        is_new_client = False
        temp_password = None
    else:
        # Create new client account
        client_id = str(uuid.uuid4())
        client_display_id = generate_client_id()
        temp_password = generate_password()
        
        client_doc = {
            "id": client_id,
            "client_id": client_display_id,
            "full_name": booking.full_name,
            "email": booking.email,
            "mobile": booking.mobile,
            "gender": booking.gender,
            "date_of_birth": booking.date_of_birth,
            "role": "client",
            "password_hash": pwd_context.hash(temp_password),
            "therapist_id": booking.therapist_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "registered_via": "public_booking"
        }
        
        await db.users.insert_one(client_doc)
        client_name = booking.full_name
        is_new_client = True
    
    # Create appointment with pending_approval status
    appointment_id = str(uuid.uuid4())
    appointment_doc = {
        "id": appointment_id,
        "therapist_id": booking.therapist_id,
        "client_id": client_id,
        "client_name": client_name,
        "start_time": booking.slot_start,
        "end_time": booking.slot_end,
        "status": "pending_approval",  # Needs therapist approval
        "notes": booking.notes or f"Booked via public calendar",
        "source": "public_booking",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appointment_doc)
    
    # Create notification for therapist
    notification_doc = {
        "id": str(uuid.uuid4()),
        "user_id": booking.therapist_id,
        "type": "booking_request",
        "title": "New Booking Request",
        "message": f"New appointment request from {client_name} for {booking.slot_start[:10]}",
        "data": {"appointment_id": appointment_id, "client_id": client_id},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification_doc)
    
    # Send emails
    try:
        # Email to client
        if is_new_client and temp_password:
            await NotificationService.send_public_booking_confirmation(
                client_email=booking.email,
                client_name=client_name,
                therapist_name=therapist["full_name"],
                appointment_time=booking.slot_start,
                temp_password=temp_password,
                mobile=booking.mobile
            )
        else:
            await NotificationService.send_booking_request_notification(
                client_email=booking.email,
                client_name=client_name,
                therapist_name=therapist["full_name"],
                appointment_time=booking.slot_start
            )
        
        # Email to therapist
        await NotificationService.send_new_booking_request_to_therapist(
            therapist_email=therapist["email"],
            therapist_name=therapist["full_name"],
            client_name=client_name,
            appointment_time=booking.slot_start
        )
    except Exception as e:
        print(f"Email send error: {e}")
    
    return {
        "success": True,
        "message": "Booking request submitted successfully. Awaiting therapist approval.",
        "appointment_id": appointment_id,
        "is_new_client": is_new_client
    }


@router.get("/booking-link/{therapist_id}")
async def get_booking_link_info(therapist_id: str):
    """Check if therapist has public booking enabled"""
    profile = await db.therapist_profiles.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0, "public_booking_enabled": 1}
    )
    
    return {
        "enabled": profile.get("public_booking_enabled", False) if profile else False
    }
