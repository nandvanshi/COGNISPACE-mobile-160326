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
