"""
Assistant Dashboard and Cash Settlement routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import pytz

from database import db
from dependencies import get_current_user, log_audit

router = APIRouter(tags=["assistant"])

IST = pytz.timezone('Asia/Kolkata')


# ============= MODELS =============

class CashHandover(BaseModel):
    cash_amount: float
    notes: Optional[str] = None


class SettlementDispute(BaseModel):
    reason: str


class CallReminderUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


# ============= DEPENDENCIES =============

def get_effective_therapist_id(user: dict) -> str:
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None


async def require_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "assistant":
        raise HTTPException(status_code=403, detail="Assistant access required")
    return current_user


async def require_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    return current_user


async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return current_user


# ============= ASSISTANT DASHBOARD =============

@router.get("/assistant/dashboard")
async def get_assistant_dashboard(current_user: dict = Depends(require_assistant)):
    """Get comprehensive dashboard data for assistant"""
    therapist_id = current_user.get("therapist_id")
    if not therapist_id:
        raise HTTPException(status_code=403, detail="Assistant not linked to a therapist")
    
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1, "email": 1, "mobile": 1})
    
    # Get current time in IST
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    
    # Today's date range in IST (midnight to midnight)
    today_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_ist = now_ist.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Convert to ISO string format for comparison
    # Note: Database stores appointments in ISO format, comparison should work with strings
    today_start_str = today_start_ist.isoformat()
    today_end_str = today_end_ist.isoformat()
    
    todays_appointments = await db.appointments.find({
        "therapist_id": therapist_id,
        "start_time": {"$gte": today_start_str, "$lte": today_end_str},
        "status": {"$in": ["scheduled", "in_progress", "completed"]}
    }, {"_id": 0}).sort("start_time", 1).to_list(50)
    
    call_reminders = await db.call_reminders.find({
        "therapist_id": therapist_id,
        "date": today_start_ist.strftime("%Y-%m-%d")
    }, {"_id": 0}).to_list(100)
    
    call_reminder_map = {cr["appointment_id"]: cr for cr in call_reminders}
    
    for appt in todays_appointments:
        reminder = call_reminder_map.get(appt["id"])
        appt["call_status"] = reminder.get("status", "pending") if reminder else "pending"
        appt["called_at"] = reminder.get("called_at") if reminder else None
    
    upcoming_cutoff = (now_utc + timedelta(hours=4)).isoformat()
    upcoming_sessions = [a for a in todays_appointments if a["start_time"] <= upcoming_cutoff and a["status"] == "scheduled"]
    pending_checkins = [a for a in todays_appointments if a["status"] == "in_progress"]
    
    thirty_days_ago = (now_utc - timedelta(days=30)).isoformat()
    all_clients = await db.client_profiles.find({"therapist_id": therapist_id}, {"_id": 0, "user_id": 1}).to_list(1000)
    client_ids = [c["user_id"] for c in all_clients]
    
    recent_appointments = await db.appointments.find({
        "therapist_id": therapist_id,
        "client_id": {"$in": client_ids},
        "start_time": {"$gte": thirty_days_ago},
        "status": {"$in": ["completed", "in_progress"]}
    }, {"_id": 0, "client_id": 1}).to_list(10000)
    
    active_client_ids = set(a["client_id"] for a in recent_appointments)
    inactive_count = len(set(client_ids) - active_client_ids)
    
    pending_payments = await db.payments.count_documents({
        "therapist_id": therapist_id,
        "payment_status": "pending"
    })
    
    today_settlement = await db.cash_settlements.find_one({
        "therapist_id": therapist_id,
        "assistant_id": current_user["id"],
        "date": today_start_ist.strftime("%Y-%m-%d")
    }, {"_id": 0})
    
    return {
        "therapist": therapist,
        "today_date": today_start_ist.strftime("%Y-%m-%d"),
        "stats": {
            "todays_appointments": len(todays_appointments),
            "upcoming_soon": len(upcoming_sessions),
            "pending_checkins": len(pending_checkins),
            "inactive_clients": inactive_count,
            "pending_payments": pending_payments
        },
        "todays_appointments": todays_appointments,
        "needs_attention": {
            "upcoming_sessions": upcoming_sessions[:5],
            "pending_checkins": pending_checkins
        },
        "cash_settlement": today_settlement
    }


@router.post("/assistant/call-reminder/{appointment_id}")
async def update_call_reminder(appointment_id: str, data: CallReminderUpdate, current_user: dict = Depends(require_assistant)):
    """Update call reminder status"""
    therapist_id = current_user.get("therapist_id")
    
    appointment = await db.appointments.find_one({"id": appointment_id, "therapist_id": therapist_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    now_ist = datetime.now(timezone.utc).astimezone(IST)
    today_str = now_ist.strftime("%Y-%m-%d")
    
    reminder = await db.call_reminders.find_one({
        "appointment_id": appointment_id,
        "date": today_str
    }, {"_id": 0})
    
    if reminder:
        await db.call_reminders.update_one(
            {"appointment_id": appointment_id, "date": today_str},
            {"$set": {
                "status": data.status,
                "notes": data.notes,
                "called_at": now_ist.isoformat() if data.status == "called" else None,
                "updated_by": current_user["id"]
            }}
        )
    else:
        reminder_doc = {
            "id": str(uuid.uuid4()),
            "therapist_id": therapist_id,
            "appointment_id": appointment_id,
            "date": today_str,
            "status": data.status,
            "notes": data.notes,
            "called_at": now_ist.isoformat() if data.status == "called" else None,
            "created_by": current_user["id"]
        }
        await db.call_reminders.insert_one(reminder_doc)
    
    return {"message": "Call reminder updated", "status": data.status}


# ============= CASH SETTLEMENT ENDPOINTS =============

@router.get("/settlements/today")
async def get_today_settlement(current_user: dict = Depends(require_assistant)):
    """Get today's settlement status for assistant"""
    therapist_id = current_user.get("therapist_id")
    
    now_ist = datetime.now(timezone.utc).astimezone(IST)
    today_str = now_ist.strftime("%Y-%m-%d")
    
    settlement = await db.cash_settlements.find_one({
        "therapist_id": therapist_id,
        "assistant_id": current_user["id"],
        "date": today_str
    }, {"_id": 0})
    
    today_cash = await db.payments.find({
        "therapist_id": therapist_id,
        "payment_method": "cash",
        "payment_status": "paid",
        "created_at": {"$regex": f"^{today_str}"}
    }, {"_id": 0}).to_list(100)
    
    total_cash = sum(p.get("amount", 0) for p in today_cash)
    
    return {
        "date": today_str,
        "total_cash_collected": total_cash,
        "settlement": settlement,
        "payments": today_cash
    }


@router.post("/settlements/handover")
async def handover_cash(data: CashHandover, current_user: dict = Depends(require_assistant)):
    """Assistant hands over cash to therapist"""
    therapist_id = current_user.get("therapist_id")
    
    now_ist = datetime.now(timezone.utc).astimezone(IST)
    today_str = now_ist.strftime("%Y-%m-%d")
    
    existing = await db.cash_settlements.find_one({
        "therapist_id": therapist_id,
        "assistant_id": current_user["id"],
        "date": today_str
    }, {"_id": 0})
    
    if existing and existing.get("status") in ["handed_over", "settled"]:
        raise HTTPException(status_code=400, detail="Settlement already processed for today")
    
    settlement_id = str(uuid.uuid4())
    settlement_doc = {
        "id": settlement_id,
        "therapist_id": therapist_id,
        "assistant_id": current_user["id"],
        "assistant_name": current_user.get("full_name"),
        "date": today_str,
        "cash_amount": data.cash_amount,
        "status": "handed_over",
        "notes": data.notes,
        "handed_over_at": now_ist.isoformat(),
        "settled_at": None,
        "disputed_reason": None
    }
    
    if existing:
        await db.cash_settlements.update_one(
            {"id": existing["id"]},
            {"$set": {
                "cash_amount": data.cash_amount,
                "status": "handed_over",
                "notes": data.notes,
                "handed_over_at": now_ist.isoformat()
            }}
        )
        settlement_id = existing["id"]
    else:
        await db.cash_settlements.insert_one(settlement_doc)
    
    await log_audit(current_user["id"], "assistant", "handover", "cash_settlement", settlement_id)
    
    return {"message": "Cash handover recorded", "settlement_id": settlement_id}


@router.get("/settlements/pending")
async def get_pending_settlements(current_user: dict = Depends(require_therapist)):
    """Therapist gets pending settlements to confirm"""
    settlements = await db.cash_settlements.find({
        "therapist_id": current_user["id"],
        "status": "handed_over"
    }, {"_id": 0}).sort("date", -1).to_list(50)
    
    return settlements


@router.post("/settlements/{settlement_id}/confirm")
async def confirm_settlement(settlement_id: str, current_user: dict = Depends(require_therapist)):
    """Therapist confirms cash receipt"""
    settlement = await db.cash_settlements.find_one({
        "id": settlement_id,
        "therapist_id": current_user["id"]
    }, {"_id": 0})
    
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    if settlement.get("status") != "handed_over":
        raise HTTPException(status_code=400, detail="Settlement not in handed_over status")
    
    now_ist = datetime.now(timezone.utc).astimezone(IST)
    
    await db.cash_settlements.update_one(
        {"id": settlement_id},
        {"$set": {
            "status": "settled",
            "settled_at": now_ist.isoformat()
        }}
    )
    
    await log_audit(current_user["id"], "therapist", "confirm", "cash_settlement", settlement_id)
    
    return {"message": "Settlement confirmed"}


@router.post("/settlements/{settlement_id}/dispute")
async def dispute_settlement(settlement_id: str, data: SettlementDispute, current_user: dict = Depends(require_therapist)):
    """Therapist disputes a settlement"""
    settlement = await db.cash_settlements.find_one({
        "id": settlement_id,
        "therapist_id": current_user["id"]
    }, {"_id": 0})
    
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    await db.cash_settlements.update_one(
        {"id": settlement_id},
        {"$set": {
            "status": "disputed",
            "disputed_reason": data.reason
        }}
    )
    
    await log_audit(current_user["id"], "therapist", "dispute", "cash_settlement", settlement_id)
    
    return {"message": "Settlement disputed"}


@router.get("/settlements/history")
async def get_settlement_history(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get settlement history"""
    therapist_id = get_effective_therapist_id(current_user)
    
    query = {"therapist_id": therapist_id}
    if current_user["role"] == "assistant":
        query["assistant_id"] = current_user["id"]
    
    settlements = await db.cash_settlements.find(query, {"_id": 0}).sort("date", -1).to_list(100)
    
    return settlements
