"""
Scheduled Jobs - Background notification tasks
"""
import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


async def check_appointment_reminders(db):
    """
    Check for upcoming appointments and send reminders.
    Sends reminders at:
    - 60 minutes before appointment
    - 30 minutes before appointment (optional second reminder)
    
    Runs every 5 minutes.
    """
    logger.info("Running appointment reminder check...")
    
    try:
        now = datetime.now(timezone.utc)
        
        # Time windows for reminders
        reminder_60_start = now + timedelta(minutes=55)
        reminder_60_end = now + timedelta(minutes=65)
        reminder_30_start = now + timedelta(minutes=25)
        reminder_30_end = now + timedelta(minutes=35)
        
        # Find appointments needing 60-minute reminder
        appointments_60 = await db.appointments.find({
            "status": "scheduled",
            "start_time": {
                "$gte": reminder_60_start.isoformat(),
                "$lt": reminder_60_end.isoformat()
            },
            "reminder_60_sent": {"$ne": True}
        }, {"_id": 0}).to_list(100)
        
        # Find appointments needing 30-minute reminder
        appointments_30 = await db.appointments.find({
            "status": "scheduled",
            "start_time": {
                "$gte": reminder_30_start.isoformat(),
                "$lt": reminder_30_end.isoformat()
            },
            "reminder_30_sent": {"$ne": True}
        }, {"_id": 0}).to_list(100)
        
        sent_count = 0
        
        # Process 60-minute reminders
        for appt in appointments_60:
            success = await _send_appointment_reminder(db, appt, "60 minutes")
            if success:
                await db.appointments.update_one(
                    {"id": appt["id"]},
                    {"$set": {"reminder_60_sent": True}}
                )
                sent_count += 1
        
        # Process 30-minute reminders
        for appt in appointments_30:
            success = await _send_appointment_reminder(db, appt, "30 minutes")
            if success:
                await db.appointments.update_one(
                    {"id": appt["id"]},
                    {"$set": {"reminder_30_sent": True}}
                )
                sent_count += 1
        
        if sent_count > 0:
            logger.info(f"Sent {sent_count} appointment reminders")
        
    except Exception as e:
        logger.error(f"Error in appointment reminder job: {e}")


async def _send_appointment_reminder(db, appointment: dict, time_until: str) -> bool:
    """Send appointment reminder notification"""
    try:
        client_id = appointment.get("client_id")
        therapist_id = appointment.get("therapist_id")
        
        if not client_id or not therapist_id:
            return False
        
        # Get client and therapist info
        client = await db.users.find_one({"id": client_id}, {"_id": 0, "full_name": 1, "email": 1})
        therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
        
        if not client or not therapist:
            return False
        
        # Create in-app notification
        from routes.notifications import create_notification
        await create_notification(
            user_id=client_id,
            role="client",
            notification_type="appointment_reminder",
            title="Appointment Reminder",
            message=f"Your session with {therapist['full_name']} is in {time_until}",
            link="/dashboard",
            db_override=db
        )
        
        # Send email notification
        if client.get("email"):
            try:
                from services.email import EmailService
                await EmailService.send_notification_email(
                    to_user_id=client_id,
                    event="appointment_reminder",
                    data={
                        "therapist_name": therapist["full_name"],
                        "appointment_time": appointment.get("start_time"),
                        "time_until": time_until
                    },
                    therapist_id=therapist_id
                )
            except Exception as e:
                logger.warning(f"Failed to send appointment reminder email: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending appointment reminder: {e}")
        return False


async def check_pending_session_notes(db):
    """
    Check for completed sessions without notes and remind therapists.
    Sends reminder if:
    - Session completed more than 1 hour ago
    - No session note linked to the appointment
    
    Runs every 15 minutes.
    """
    logger.info("Running pending session notes check...")
    
    try:
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        # Find completed appointments without notes (completed in last 24 hours)
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        completed_appointments = await db.appointments.find({
            "status": "completed",
            "end_time": {
                "$gte": twenty_four_hours_ago.isoformat(),
                "$lt": one_hour_ago.isoformat()
            },
            "note_reminder_sent": {"$ne": True}
        }, {"_id": 0}).to_list(100)
        
        sent_count = 0
        
        for appt in completed_appointments:
            # Check if a session note exists for this appointment
            existing_note = await db.session_notes.find_one({
                "appointment_id": appt["id"]
            }, {"_id": 0, "id": 1})
            
            if existing_note:
                # Note exists, mark as not needing reminder
                await db.appointments.update_one(
                    {"id": appt["id"]},
                    {"$set": {"note_reminder_sent": True}}
                )
                continue
            
            # Send reminder to therapist
            success = await _send_pending_note_reminder(db, appt)
            if success:
                await db.appointments.update_one(
                    {"id": appt["id"]},
                    {"$set": {"note_reminder_sent": True}}
                )
                sent_count += 1
        
        if sent_count > 0:
            logger.info(f"Sent {sent_count} pending note reminders")
        
    except Exception as e:
        logger.error(f"Error in pending notes job: {e}")


async def _send_pending_note_reminder(db, appointment: dict) -> bool:
    """Send pending session note reminder to therapist"""
    try:
        therapist_id = appointment.get("therapist_id")
        client_id = appointment.get("client_id")
        
        if not therapist_id or not client_id:
            return False
        
        # Get client name
        client = await db.users.find_one({"id": client_id}, {"_id": 0, "full_name": 1})
        if not client:
            return False
        
        # Create in-app notification for therapist
        from routes.notifications import create_notification
        
        # Format appointment time for display
        appt_time = appointment.get("start_time", "")
        if appt_time:
            try:
                dt = datetime.fromisoformat(appt_time.replace('Z', '+00:00'))
                ist_dt = dt.astimezone(IST)
                appt_time = ist_dt.strftime("%d/%m/%Y %H:%M")
            except:
                pass
        
        await create_notification(
            user_id=therapist_id,
            role="therapist",
            notification_type="pending_note",
            title="Session Note Pending",
            message=f"Please add notes for session with {client['full_name']} ({appt_time})",
            link="/session-notes",
            db_override=db
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending pending note reminder: {e}")
        return False


async def check_subscription_expiry(db):
    """
    Check for expiring subscriptions and send warnings.
    Sends warnings at:
    - 7 days before expiry
    - 3 days before expiry
    - 1 day before expiry
    
    Runs daily at 9 AM IST.
    """
    logger.info("Running subscription expiry check...")
    
    try:
        now = datetime.now(timezone.utc)
        
        # Define warning windows
        warning_days = [7, 3, 1]
        
        for days in warning_days:
            target_date = now + timedelta(days=days)
            target_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            target_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Find subscriptions expiring on this date
            expiring_subs = await db.subscriptions.find({
                "status": {"$in": ["trial", "active"]},
                "end_date": {
                    "$gte": target_start.isoformat(),
                    "$lte": target_end.isoformat()
                },
                f"expiry_warning_{days}d_sent": {"$ne": True}
            }, {"_id": 0}).to_list(100)
            
            for sub in expiring_subs:
                success = await _send_subscription_expiry_warning(db, sub, days)
                if success:
                    await db.subscriptions.update_one(
                        {"id": sub["id"]},
                        {"$set": {f"expiry_warning_{days}d_sent": True}}
                    )
        
    except Exception as e:
        logger.error(f"Error in subscription expiry job: {e}")


async def _send_subscription_expiry_warning(db, subscription: dict, days_remaining: int) -> bool:
    """Send subscription expiry warning to therapist"""
    try:
        therapist_id = subscription.get("therapist_id")
        if not therapist_id:
            return False
        
        # Get therapist info
        therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1, "email": 1})
        if not therapist:
            return False
        
        plan_name = subscription.get("plan_name", "Your subscription")
        
        # Create in-app notification
        from routes.notifications import create_notification
        await create_notification(
            user_id=therapist_id,
            role="therapist",
            notification_type="subscription_expiry",
            title="Subscription Expiring Soon",
            message=f"{plan_name} expires in {days_remaining} day{'s' if days_remaining > 1 else ''}. Renew now to avoid interruption.",
            link="/subscription",
            db_override=db
        )
        
        # Send email notification
        if therapist.get("email"):
            try:
                from services.email import EmailService
                await EmailService.send_notification_email(
                    to_user_id=therapist_id,
                    event="subscription_expiry",
                    data={
                        "plan_name": plan_name,
                        "expiry_date": subscription.get("end_date"),
                        "days_remaining": days_remaining,
                        "renewal_url": "/subscription"
                    },
                    therapist_id=therapist_id,
                    force=True  # Always send expiry warnings
                )
            except Exception as e:
                logger.warning(f"Failed to send subscription expiry email: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending subscription expiry warning: {e}")
        return False
