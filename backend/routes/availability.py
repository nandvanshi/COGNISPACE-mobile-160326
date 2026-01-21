"""
Therapist Availability, Blocked Time, and Slot management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta, date
import uuid

from database import db
from dependencies import get_current_user

router = APIRouter(tags=["availability"])


# ============= MODELS =============

class TimeBlock(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    def get_start(self):
        return self.start or self.start_time or "09:00"
    
    def get_end(self):
        return self.end or self.end_time or "17:00"


class DayAvailability(BaseModel):
    enabled: bool = False
    time_blocks: List[TimeBlock] = []


class TherapistAvailability(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    session_duration: int = 60
    buffer_time: int = 0
    monday: DayAvailability = DayAvailability()
    tuesday: DayAvailability = DayAvailability()
    wednesday: DayAvailability = DayAvailability()
    thursday: DayAvailability = DayAvailability()
    friday: DayAvailability = DayAvailability()
    saturday: DayAvailability = DayAvailability()
    sunday: DayAvailability = DayAvailability()
    updated_at: datetime


class TherapistAvailabilityUpdate(BaseModel):
    session_duration: Optional[int] = None
    buffer_time: Optional[int] = None
    monday: Optional[DayAvailability] = None
    tuesday: Optional[DayAvailability] = None
    wednesday: Optional[DayAvailability] = None
    thursday: Optional[DayAvailability] = None
    friday: Optional[DayAvailability] = None
    saturday: Optional[DayAvailability] = None
    sunday: Optional[DayAvailability] = None


class BlockedTimeCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    is_recurring: bool = False


class BlockedTime(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    is_recurring: bool = False
    created_at: datetime


class AvailableSlot(BaseModel):
    start: datetime
    end: datetime


# ============= DEPENDENCIES =============

def get_effective_therapist_id(user: dict) -> str:
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None


async def require_active_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    if current_user.get("subscription_status") not in ["trial", "active"]:
        raise HTTPException(status_code=403, detail="Subscription expired")
    return current_user


async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return current_user


def parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


# ============= AVAILABILITY ENDPOINTS =============

@router.get("/availability", response_model=TherapistAvailability)
async def get_availability(current_user: dict = Depends(get_current_user)):
    """Get therapist's availability settings"""
    if current_user["role"] == "therapist":
        therapist_id = current_user["id"]
    elif current_user["role"] == "assistant":
        therapist_id = current_user.get("therapist_id")
        if not therapist_id:
            raise HTTPException(status_code=403, detail="Assistant not linked to a therapist")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    availability = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    
    if not availability:
        default_availability = {
            "id": str(uuid.uuid4()),
            "therapist_id": therapist_id,
            "session_duration": 60,
            "buffer_time": 0,
            "monday": {"enabled": False, "time_blocks": []},
            "tuesday": {"enabled": False, "time_blocks": []},
            "wednesday": {"enabled": False, "time_blocks": []},
            "thursday": {"enabled": False, "time_blocks": []},
            "friday": {"enabled": False, "time_blocks": []},
            "saturday": {"enabled": False, "time_blocks": []},
            "sunday": {"enabled": False, "time_blocks": []},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.therapist_availability.insert_one(default_availability)
        availability = default_availability
    
    return TherapistAvailability(**{k: parse_datetime(v) if k == "updated_at" else v for k, v in availability.items()})


@router.put("/availability", response_model=TherapistAvailability)
async def update_availability(update_data: TherapistAvailabilityUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update therapist's availability settings"""
    therapist_id = current_user["id"]
    
    availability = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    
    if not availability:
        availability = {
            "id": str(uuid.uuid4()),
            "therapist_id": therapist_id,
            "session_duration": 60,
            "buffer_time": 0,
            "monday": {"enabled": False, "time_blocks": []},
            "tuesday": {"enabled": False, "time_blocks": []},
            "wednesday": {"enabled": False, "time_blocks": []},
            "thursday": {"enabled": False, "time_blocks": []},
            "friday": {"enabled": False, "time_blocks": []},
            "saturday": {"enabled": False, "time_blocks": []},
            "sunday": {"enabled": False, "time_blocks": []},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.therapist_availability.insert_one(availability)
    
    update_dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if update_data.session_duration is not None:
        update_dict["session_duration"] = update_data.session_duration
    if update_data.buffer_time is not None:
        update_dict["buffer_time"] = update_data.buffer_time
    
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        day_data = getattr(update_data, day)
        if day_data is not None:
            update_dict[day] = day_data.model_dump()
    
    await db.therapist_availability.update_one(
        {"therapist_id": therapist_id},
        {"$set": update_dict}
    )
    
    updated = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    return TherapistAvailability(**{k: parse_datetime(v) if k == "updated_at" else v for k, v in updated.items()})


# ============= BLOCKED TIME ENDPOINTS =============

@router.post("/blocked-time", response_model=BlockedTime)
async def create_blocked_time(data: BlockedTimeCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a blocked time slot"""
    therapist_id = current_user["id"]
    
    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    blocked_id = str(uuid.uuid4())
    blocked_doc = {
        "id": blocked_id,
        "therapist_id": therapist_id,
        "start_time": data.start_time.isoformat(),
        "end_time": data.end_time.isoformat(),
        "reason": data.reason,
        "is_recurring": data.is_recurring,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.blocked_times.insert_one(blocked_doc)
    
    return BlockedTime(
        id=blocked_id,
        therapist_id=therapist_id,
        start_time=data.start_time,
        end_time=data.end_time,
        reason=data.reason,
        is_recurring=data.is_recurring,
        created_at=parse_datetime(blocked_doc["created_at"])
    )


@router.get("/blocked-time", response_model=List[BlockedTime])
@router.get("/blocked-times", response_model=List[BlockedTime])
async def get_blocked_times(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get all blocked time slots"""
    therapist_id = get_effective_therapist_id(current_user)
    
    blocked_times = await db.blocked_times.find({"therapist_id": therapist_id}, {"_id": 0}).to_list(500)
    
    result = []
    for bt in blocked_times:
        # Handle both old (start_datetime) and new (start_time) field names
        start = bt.get("start_time") or bt.get("start_datetime")
        end = bt.get("end_time") or bt.get("end_datetime")
        
        if start and end:
            result.append(BlockedTime(
                id=bt["id"],
                therapist_id=bt["therapist_id"],
                start_time=parse_datetime(start),
                end_time=parse_datetime(end),
                reason=bt.get("reason"),
                is_recurring=bt.get("is_recurring", False),
                created_at=parse_datetime(bt["created_at"])
            ))
    
    return result


@router.delete("/blocked-time/{blocked_id}")
async def delete_blocked_time(blocked_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a blocked time slot"""
    result = await db.blocked_times.delete_one({"id": blocked_id, "therapist_id": current_user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blocked time not found")
    
    return {"message": "Blocked time deleted"}


# ============= AVAILABLE SLOTS ENDPOINT =============

@router.get("/available-slots", response_model=List[AvailableSlot])
async def get_available_slots(
    therapist_id: Optional[str] = None,
    date_str: str = Query(..., alias="date"),
    current_user: dict = Depends(get_current_user)
):
    """Get available appointment slots for a specific date"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"available-slots called: user_role={current_user['role']}, user_id={current_user['id']}, therapist_id_param={therapist_id}")
    
    if current_user["role"] == "client":
        profile = await db.client_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
        logger.info(f"Client profile: {profile}")
        if profile:
            therapist_id = profile.get("therapist_id")
        if not therapist_id:
            raise HTTPException(status_code=400, detail="No therapist assigned")
    elif current_user["role"] in ["therapist", "assistant"]:
        therapist_id = get_effective_therapist_id(current_user)
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    logger.info(f"Final therapist_id: {therapist_id}")
    
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day_name = target_date.strftime("%A").lower()
    logger.info(f"Looking for availability on {day_name} for therapist {therapist_id}")
    
    availability = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    logger.info(f"Found availability: {availability is not None}")
    
    if not availability:
        return []
    
    day_availability = availability.get(day_name, {})
    logger.info(f"Day availability for {day_name}: {day_availability}")
    if not day_availability.get("enabled", False):
        return []
    
    session_duration = availability.get("session_duration", 60)
    buffer_time = availability.get("buffer_time", 0)
    
    appointments = await db.appointments.find({
        "therapist_id": therapist_id,
        "status": {"$ne": "cancelled"},
        "start_time": {"$regex": f"^{date_str}"}
    }, {"_id": 0}).to_list(100)
    
    blocked_times = await db.blocked_times.find({
        "therapist_id": therapist_id,
        "$or": [
            {"start_time": {"$regex": f"^{date_str}"}},
            {"is_recurring": True}
        ]
    }, {"_id": 0}).to_list(100)
    
    booked_ranges = []
    for appt in appointments:
        start = datetime.fromisoformat(appt["start_time"].replace('Z', '+00:00'))
        end = datetime.fromisoformat(appt["end_time"].replace('Z', '+00:00'))
        booked_ranges.append((start, end))
    
    for bt in blocked_times:
        start = datetime.fromisoformat(bt["start_time"].replace('Z', '+00:00'))
        end = datetime.fromisoformat(bt["end_time"].replace('Z', '+00:00'))
        booked_ranges.append((start, end))
    
    available_slots = []
    time_blocks = day_availability.get("time_blocks", [])
    
    for block in time_blocks:
        # Support both old format (start/end) and new format (start_time/end_time)
        block_start_str = block.get("start_time") or block.get("start", "09:00")
        block_end_str = block.get("end_time") or block.get("end", "17:00")
        
        try:
            block_start_time = datetime.strptime(block_start_str, "%H:%M").time()
            block_end_time = datetime.strptime(block_end_str, "%H:%M").time()
        except ValueError:
            continue
        
        block_start = datetime.combine(target_date, block_start_time, tzinfo=timezone.utc)
        block_end = datetime.combine(target_date, block_end_time, tzinfo=timezone.utc)
        
        current_slot_start = block_start
        while current_slot_start + timedelta(minutes=session_duration) <= block_end:
            slot_end = current_slot_start + timedelta(minutes=session_duration)
            
            is_available = True
            for booked_start, booked_end in booked_ranges:
                if current_slot_start < booked_end and slot_end > booked_start:
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(AvailableSlot(start=current_slot_start, end=slot_end))
            
            current_slot_start = slot_end + timedelta(minutes=buffer_time)
    
    return available_slots
