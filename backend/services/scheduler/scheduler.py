"""
Notification Scheduler - APScheduler integration for FastAPI
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST_TZ = ZoneInfo("Asia/Kolkata")


class NotificationScheduler:
    """
    Manages background jobs for time-based notifications.
    Uses APScheduler with AsyncIO for non-blocking execution.
    """
    
    _instance = None
    _scheduler: AsyncIOScheduler = None
    _db = None
    _is_running = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(cls, db):
        """Initialize scheduler with database connection"""
        cls._db = db
        cls._scheduler = AsyncIOScheduler(
            timezone='Asia/Kolkata',  # IST timezone
            job_defaults={
                'coalesce': True,  # Combine missed runs into one
                'max_instances': 1,  # Only one instance of each job
                'misfire_grace_time': 60  # Allow 60 seconds delay
            }
        )
        
        # Register jobs
        await cls._register_jobs()
        
        logger.info("Notification scheduler initialized")
    
    @classmethod
    async def _register_jobs(cls):
        """Register all scheduled jobs"""
        from .jobs import (
            check_appointment_reminders,
            check_pending_session_notes,
            check_subscription_expiry,
            send_morning_schedule_briefing,
            send_daily_payment_statement
        )
        from .followup_reminders import check_followup_reminders
        
        # Job 1: Appointment Reminders - Run every 5 minutes
        cls._scheduler.add_job(
            check_appointment_reminders,
            trigger=IntervalTrigger(minutes=5),
            id='appointment_reminders',
            name='Check Appointment Reminders',
            args=[cls._db],
            replace_existing=True
        )
        
        # Job 2: Pending Session Notes - Run every 15 minutes
        cls._scheduler.add_job(
            check_pending_session_notes,
            trigger=IntervalTrigger(minutes=15),
            id='pending_session_notes',
            name='Check Pending Session Notes',
            args=[cls._db],
            replace_existing=True
        )
        
        # Job 3: Subscription Expiry - Run daily at 9 AM IST
        cls._scheduler.add_job(
            check_subscription_expiry,
            trigger=CronTrigger(hour=9, minute=0, timezone=IST_TZ),
            id='subscription_expiry',
            name='Check Subscription Expiry',
            args=[cls._db],
            replace_existing=True
        )
        
        # Job 4: Morning Schedule Briefing - Run daily at 7 AM IST
        cls._scheduler.add_job(
            send_morning_schedule_briefing,
            trigger=CronTrigger(hour=7, minute=0, timezone=IST_TZ),
            id='morning_schedule_briefing',
            name='Morning Schedule Briefing',
            args=[cls._db],
            replace_existing=True
        )
        
        # Job 5: Daily Payment Statement - Run daily at 9 PM IST
        cls._scheduler.add_job(
            send_daily_payment_statement,
            trigger=CronTrigger(hour=21, minute=0, timezone=IST_TZ),
            id='daily_payment_statement',
            name='Daily Payment Statement',
            args=[cls._db],
            replace_existing=True
        )
        
        # Job 6: Follow-Up Reminders - Run every 30 minutes
        cls._scheduler.add_job(
            check_followup_reminders,
            trigger=IntervalTrigger(minutes=30),
            id='followup_reminders',
            name='Follow-Up Session Reminders',
            args=[cls._db],
            replace_existing=True
        )
        
        logger.info("Registered 6 scheduled jobs: appointment_reminders (5min), pending_notes (15min), subscription_expiry (daily 9AM), morning_briefing (daily 7AM), payment_statement (daily 9PM), followup_reminders (30min)")
    
    @classmethod
    def start(cls):
        """Start the scheduler"""
        if cls._scheduler and not cls._is_running:
            cls._scheduler.start()
            cls._is_running = True
            logger.info("Notification scheduler started")
    
    @classmethod
    def stop(cls):
        """Stop the scheduler"""
        if cls._scheduler and cls._is_running:
            cls._scheduler.shutdown(wait=False)
            cls._is_running = False
            logger.info("Notification scheduler stopped")
    
    @classmethod
    def get_jobs(cls):
        """Get list of all scheduled jobs"""
        if cls._scheduler is None:
            return []
        
        jobs = []
        for job in cls._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
    
    @classmethod
    async def run_job_now(cls, job_id: str):
        """Manually trigger a job (for testing/admin)"""
        if cls._scheduler is None:
            return {"success": False, "error": "Scheduler not initialized"}
        
        job = cls._scheduler.get_job(job_id)
        if job is None:
            return {"success": False, "error": f"Job '{job_id}' not found"}
        
        try:
            # Run the job function directly
            await job.func(*job.args)
            return {"success": True, "message": f"Job '{job_id}' executed"}
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    def is_running(cls) -> bool:
        """Check if scheduler is running"""
        return cls._is_running
