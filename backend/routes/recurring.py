"""
Recurring Appointments routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from dependencies import get_current_user, log_audit

router = APIRouter(prefix="/recurring-appointments", tags=["recurring"])


# ============= MODELS =============

class RecurringPatternCreate(BaseModel):
    client_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # "HH:MM" format
    end_time: str    # "HH:MM" format
    notes: Optional[str] = None
    start_date: str  # YYYY-MM-DD - when to start generating
    end_date: Optional[str] = None  # YYYY-MM-DD - when to stop (None = indefinite)


class RecurringPattern(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    day_of_week: int
    start_time: str
    end_time: str
    notes: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    is_active: bool = True
    created_at: datetime


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


# ============= RECURRING APPOINTMENTS ENDPOINTS =============

@router.post("", response_model=RecurringPattern)
async def create_recurring_pattern(data: RecurringPatternCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a recurring appointment pattern"""
    therapist_id = current_user["id"]
    
    # Validate client belongs to therapist
    client_profile = await db.client_profiles.find_one(
        {"user_id": data.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client name
    client_user = await db.users.find_one({"id": data.client_id}, {"_id": 0, "full_name": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
    
    # Validate day_of_week
    if data.day_of_week < 0 or data.day_of_week > 6:
        raise HTTPException(status_code=400, detail="day_of_week must be 0-6 (Monday=0, Sunday=6)")
    
    pattern_id = str(uuid.uuid4())
    pattern_doc = {
        "id": pattern_id,
        "therapist_id": therapist_id,
        "client_id": data.client_id,
        "client_name": client_name,
        "day_of_week": data.day_of_week,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "notes": data.notes,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.recurring_patterns.insert_one(pattern_doc)
    await log_audit(current_user["id"], "therapist", "create", "recurring_pattern", pattern_id)
    
    return RecurringPattern(
        id=pattern_doc["id"],
        therapist_id=pattern_doc["therapist_id"],
        client_id=pattern_doc["client_id"],
        client_name=pattern_doc["client_name"],
        day_of_week=pattern_doc["day_of_week"],
        start_time=pattern_doc["start_time"],
        end_time=pattern_doc["end_time"],
        notes=pattern_doc["notes"],
        start_date=pattern_doc["start_date"],
        end_date=pattern_doc["end_date"],
        is_active=pattern_doc["is_active"],
        created_at=parse_datetime(pattern_doc["created_at"])
    )


@router.get("", response_model=List[RecurringPattern])
async def get_recurring_patterns(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get all recurring patterns for the therapist"""
    therapist_id = get_effective_therapist_id(current_user)
    
    patterns = await db.recurring_patterns.find(
        {"therapist_id": therapist_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    return [RecurringPattern(
        id=p["id"],
        therapist_id=p["therapist_id"],
        client_id=p["client_id"],
        client_name=p.get("client_name", "Unknown"),
        day_of_week=p["day_of_week"],
        start_time=p["start_time"],
        end_time=p["end_time"],
        notes=p.get("notes"),
        start_date=p["start_date"],
        end_date=p.get("end_date"),
        is_active=p.get("is_active", True),
        created_at=parse_datetime(p["created_at"])
    ) for p in patterns]


@router.get("/{pattern_id}", response_model=RecurringPattern)
async def get_recurring_pattern(pattern_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Get a single recurring pattern"""
    therapist_id = get_effective_therapist_id(current_user)
    
    pattern = await db.recurring_patterns.find_one(
        {"id": pattern_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    
    return RecurringPattern(
        id=pattern["id"],
        therapist_id=pattern["therapist_id"],
        client_id=pattern["client_id"],
        client_name=pattern.get("client_name", "Unknown"),
        day_of_week=pattern["day_of_week"],
        start_time=pattern["start_time"],
        end_time=pattern["end_time"],
        notes=pattern.get("notes"),
        start_date=pattern["start_date"],
        end_date=pattern.get("end_date"),
        is_active=pattern.get("is_active", True),
        created_at=parse_datetime(pattern["created_at"])
    )


@router.put("/{pattern_id}/toggle")
async def toggle_recurring_pattern(pattern_id: str, current_user: dict = Depends(require_active_therapist)):
    """Toggle active status of a recurring pattern"""
    therapist_id = current_user["id"]
    
    pattern = await db.recurring_patterns.find_one(
        {"id": pattern_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    
    new_status = not pattern.get("is_active", True)
    
    await db.recurring_patterns.update_one(
        {"id": pattern_id},
        {"$set": {"is_active": new_status}}
    )
    
    await log_audit(current_user["id"], "therapist", "toggle", "recurring_pattern", pattern_id, {"is_active": new_status})
    
    return {"message": f"Pattern {'activated' if new_status else 'deactivated'}", "is_active": new_status}


@router.delete("/{pattern_id}")
async def delete_recurring_pattern(pattern_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a recurring pattern"""
    therapist_id = current_user["id"]
    
    result = await db.recurring_patterns.delete_one(
        {"id": pattern_id, "therapist_id": therapist_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    
    await log_audit(current_user["id"], "therapist", "delete", "recurring_pattern", pattern_id)
    
    return {"message": "Recurring pattern deleted"}


@router.post("/{pattern_id}/generate")
async def generate_appointments_from_pattern(
    pattern_id: str,
    weeks_ahead: int = Query(default=4, ge=1, le=12),
    current_user: dict = Depends(require_active_therapist)
):
    """Generate appointments from a recurring pattern for the next X weeks"""
    therapist_id = current_user["id"]
    
    pattern = await db.recurring_patterns.find_one(
        {"id": pattern_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    
    if not pattern.get("is_active", True):
        raise HTTPException(status_code=400, detail="Cannot generate from inactive pattern")
    
    # Get client info
    client_user = await db.users.find_one({"id": pattern["client_id"]}, {"_id": 0, "full_name": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
    
    # Parse times
    start_time_parts = pattern["start_time"].split(":")
    end_time_parts = pattern["end_time"].split(":")
    start_hour, start_min = int(start_time_parts[0]), int(start_time_parts[1])
    end_hour, end_min = int(end_time_parts[0]), int(end_time_parts[1])
    
    # Generate appointments
    today = datetime.now(timezone.utc).date()
    generated = []
    skipped = 0
    
    for week in range(weeks_ahead):
        # Calculate the target date (find the next occurrence of day_of_week)
        days_ahead = pattern["day_of_week"] - today.weekday()
        if days_ahead < 0:
            days_ahead += 7
        days_ahead += (week * 7)
        
        target_date = today + timedelta(days=days_ahead)
        
        # Check if within pattern date range
        pattern_start = datetime.strptime(pattern["start_date"], "%Y-%m-%d").date()
        if target_date < pattern_start:
            continue
        
        if pattern.get("end_date"):
            pattern_end = datetime.strptime(pattern["end_date"], "%Y-%m-%d").date()
            if target_date > pattern_end:
                continue
        
        # Create appointment times
        appt_start = datetime(
            target_date.year, target_date.month, target_date.day,
            start_hour, start_min, tzinfo=timezone.utc
        )
        appt_end = datetime(
            target_date.year, target_date.month, target_date.day,
            end_hour, end_min, tzinfo=timezone.utc
        )
        
        # Check for conflicts
        existing = await db.appointments.find_one({
            "therapist_id": therapist_id,
            "status": {"$ne": "cancelled"},
            "$or": [
                {"start_time": {"$lt": appt_end.isoformat()}, "end_time": {"$gt": appt_start.isoformat()}}
            ]
        })
        
        if existing:
            skipped += 1
            continue
        
        # Create appointment
        appointment_id = str(uuid.uuid4())
        appointment_doc = {
            "id": appointment_id,
            "therapist_id": therapist_id,
            "client_id": pattern["client_id"],
            "client_name": client_name,
            "start_time": appt_start.isoformat(),
            "end_time": appt_end.isoformat(),
            "notes": pattern.get("notes", ""),
            "status": "scheduled",
            "recurring_pattern_id": pattern_id,
            "actual_start_time": None,
            "actual_end_time": None,
            "actual_duration_minutes": None,
            "checked_in_by": None,
            "checked_out_by": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.appointments.insert_one(appointment_doc)
        generated.append({
            "id": appointment_id,
            "date": target_date.isoformat(),
            "start_time": pattern["start_time"],
            "end_time": pattern["end_time"]
        })
    
    await log_audit(current_user["id"], "therapist", "generate", "recurring_appointments", pattern_id, {
        "weeks_ahead": weeks_ahead,
        "generated": len(generated),
        "skipped": skipped
    })
    
    return {
        "message": f"Generated {len(generated)} appointments, skipped {skipped} due to conflicts",
        "generated_count": len(generated),
        "skipped_count": skipped,
        "appointments": generated
    }
