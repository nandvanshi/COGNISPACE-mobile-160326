"""
Scheduler Admin Routes - View and manage scheduled jobs
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timezone

from dependencies import get_current_user

router = APIRouter(prefix="/scheduler", tags=["Scheduler Admin"])


# ============= ADMIN ENDPOINTS =============

@router.get("/status")
async def get_scheduler_status(current_user: dict = Depends(get_current_user)):
    """Get scheduler status and list of jobs (Admin/Therapist only)"""
    if current_user["role"] not in ["super_admin", "therapist"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from services.scheduler import NotificationScheduler
    
    return {
        "is_running": NotificationScheduler.is_running(),
        "jobs": NotificationScheduler.get_jobs(),
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/run/{job_id}")
async def run_job_manually(job_id: str, current_user: dict = Depends(get_current_user)):
    """Manually trigger a scheduled job (Super Admin only)"""
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can manually trigger jobs")
    
    from services.scheduler import NotificationScheduler
    
    result = await NotificationScheduler.run_job_now(job_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/logs")
async def get_scheduler_logs(
    limit: int = 50,
    job_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get recent scheduler execution logs (Admin only)"""
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can view scheduler logs")
    
    from database import db
    
    query = {}
    if job_id:
        query["job_id"] = job_id
    
    logs = await db.scheduler_logs.find(
        query,
        {"_id": 0}
    ).sort("executed_at", -1).limit(limit).to_list(limit)
    
    return logs



@router.post("/migrate-appointment-timezone")
async def migrate_appointment_timezone(
    apply: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Migrate old IST-in-UTC appointments to correct UTC format.
    - Default: DRY-RUN mode (shows what would change)
    - Pass apply=true to actually fix the data
    - Super admin only
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    from scripts.migrate_appointment_timezone import run_migration
    result = await run_migration(dry_run=not apply)
    return result



@router.get("/debug-morning-briefing")
async def debug_morning_briefing(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Debug morning briefing - shows exactly what the morning email would contain.
    Pass ?date=2026-04-16 to check a specific date. Default: today IST.
    Super Admin only.
    """
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    from database import db
    from zoneinfo import ZoneInfo
    from datetime import timedelta
    
    IST = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(IST)
    
    if date:
        target_date_str = date
    else:
        target_date_str = now_ist.strftime("%Y-%m-%d")
    
    next_date_str = (datetime.strptime(target_date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    query_start = f"{target_date_str}T00:00:00"
    query_end = f"{next_date_str}T00:00:00"
    
    # Get all therapists
    therapists = await db.users.find(
        {"role": "therapist", "status": {"$in": ["active", "approved"]}},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "mobile": 1}
    ).to_list(100)
    
    results = []
    for therapist in therapists:
        tid = therapist["id"]
        
        # Query exactly like morning briefing does
        scheduled_appts = await db.appointments.find({
            "therapist_id": tid,
            "status": "scheduled",
            "start_time": {"$gte": query_start, "$lt": query_end}
        }, {"_id": 0, "id": 1, "client_id": 1, "start_time": 1, "status": 1}).to_list(50)
        
        # Also check ALL statuses for this date (to see if status is the issue)
        all_appts = await db.appointments.find({
            "therapist_id": tid,
            "start_time": {"$gte": query_start, "$lt": query_end}
        }, {"_id": 0, "id": 1, "client_id": 1, "start_time": 1, "status": 1}).to_list(50)
        
        # Also check without date filter (to see raw start_time format)
        sample_appts = await db.appointments.find(
            {"therapist_id": tid},
            {"_id": 0, "id": 1, "start_time": 1, "status": 1}
        ).sort("start_time", -1).limit(5).to_list(5)
        
        # Pending payments
        pending_payments = await db.payments.find({
            "therapist_id": tid,
            "payment_status": "pending"
        }, {"_id": 0, "amount": 1, "client_name": 1}).to_list(100)
        
        # All payments for this date
        all_payments = await db.payments.find({
            "therapist_id": tid,
            "date": {"$gte": query_start[:10], "$lte": query_start[:10]}
        }, {"_id": 0, "amount": 1, "payment_status": 1, "date": 1, "client_name": 1}).to_list(100)
        
        # Pending notes (last 7 days)
        from services.date_utils import get_past_days_utc
        seven_days_str = get_past_days_utc(7)
        pending_notes = await db.appointments.find({
            "therapist_id": tid,
            "status": "completed",
            "end_time": {"$gte": seven_days_str},
            "note_created": {"$ne": True}
        }, {"_id": 0, "id": 1, "client_id": 1, "start_time": 1}).to_list(50)
        
        pending_notes_count = 0
        for appt in pending_notes:
            note_exists = await db.session_notes.find_one({"appointment_id": appt.get("id")}, {"_id": 0, "id": 1})
            if not note_exists:
                pending_notes_count += 1
        
        results.append({
            "therapist": therapist["full_name"],
            "therapist_id": tid,
            "email": therapist.get("email"),
            "query": {"start": query_start, "end": query_end},
            "scheduled_appointments": len(scheduled_appts),
            "scheduled_details": scheduled_appts,
            "all_status_appointments": len(all_appts),
            "all_status_details": all_appts,
            "sample_recent_appts_raw": sample_appts,
            "pending_payments_total": sum(p.get("amount", 0) for p in pending_payments),
            "pending_payments": pending_payments,
            "all_payments_on_date": all_payments,
            "pending_notes_count": pending_notes_count,
        })
    
    return {
        "debug_date": target_date_str,
        "ist_now": now_ist.isoformat(),
        "query_range": {"start": query_start, "end": query_end},
        "therapist_count": len(therapists),
        "results": results
    }
