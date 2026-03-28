"""
Follow-Up Reminder Job - Automated reminders for unbooked follow-ups
Runs every 30 minutes, sends:
  - 2 days before recommended date
  - Same day as recommended date
  - 1 week after missed recommendation
  - 30 days after last session (dropout re-engagement)
"""
import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

REMINDER_TYPES = {
    "2day_before": {"template": "followup_2day_reminder", "flag": "reminder_2day_sent"},
    "same_day": {"template": "followup_sameday_reminder", "flag": "reminder_sameday_sent"},
    "1week_after": {"template": "followup_1week_missed", "flag": "reminder_1week_sent"},
    "30day_reengagement": {"template": "followup_30day_reengagement", "flag": "reminder_30day_sent"},
}


async def check_followup_reminders(db):
    """Main job: check all active follow-up recommendations and send reminders"""
    logger.info("Running follow-up reminder check...")

    try:
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(IST)

        # Only run between 8 AM and 9 PM IST
        if now_ist.hour < 8 or now_ist.hour > 21:
            return

        # Get all active recommendations
        recommendations = await db.follow_up_recommendations.find(
            {"status": "active"},
            {"_id": 0}
        ).to_list(500)

        sent_count = 0

        for rec in recommendations:
            client_id = rec.get("client_id")
            therapist_id = rec.get("therapist_id")
            rec_date_str = rec.get("recommended_date", "")
            rec_id = rec.get("id")

            if not client_id or not therapist_id or not rec_date_str:
                continue

            # Check if therapist has follow-up reminders enabled
            therapist_settings = await db.therapist_settings.find_one(
                {"therapist_id": therapist_id},
                {"_id": 0}
            )
            if therapist_settings and not therapist_settings.get("followup_email_enabled", True):
                continue

            whatsapp_enabled = therapist_settings.get("followup_whatsapp_enabled", False) if therapist_settings else False

            # Check if client already has upcoming appointment (skip if booked)
            upcoming = await db.appointments.find_one({
                "client_id": client_id,
                "therapist_id": therapist_id,
                "status": "scheduled",
                "start_time": {"$gte": now_utc.isoformat()}
            })
            if upcoming:
                # Client has booked - mark recommendation as fulfilled
                await db.follow_up_recommendations.update_one(
                    {"id": rec_id},
                    {"$set": {"status": "fulfilled", "fulfilled_at": now_utc.isoformat()}}
                )
                continue

            # Parse recommended date
            try:
                rec_date = datetime.strptime(rec_date_str[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            today_date = now_ist.date()
            days_until = (rec_date - today_date).days
            days_after = -days_until  # positive when past

            # Determine which reminder to send
            reminder_type = None
            if days_until == 2:
                reminder_type = "2day_before"
            elif days_until == 0:
                reminder_type = "same_day"
            elif days_after == 7:
                reminder_type = "1week_after"
            elif days_after == 30:
                reminder_type = "30day_reengagement"

            if not reminder_type:
                continue

            cfg = REMINDER_TYPES[reminder_type]
            flag = cfg["flag"]

            # Check if already sent
            if rec.get(flag):
                continue

            # Get client and therapist info
            client = await db.users.find_one(
                {"id": client_id},
                {"_id": 0, "full_name": 1, "email": 1, "mobile": 1}
            )
            therapist = await db.users.find_one(
                {"id": therapist_id},
                {"_id": 0, "full_name": 1}
            )

            if not client or not therapist:
                continue

            # Get last session for 30-day template
            days_since = None
            if reminder_type == "30day_reengagement":
                last_session = await db.appointments.find_one(
                    {"client_id": client_id, "therapist_id": therapist_id, "status": "completed"},
                    {"_id": 0, "start_time": 1},
                    sort=[("start_time", -1)]
                )
                if last_session:
                    try:
                        last_dt = datetime.fromisoformat(last_session["start_time"].replace("Z", "+00:00"))
                        days_since = (now_utc - last_dt).days
                    except (ValueError, TypeError):
                        days_since = 30

            # Build template data
            template_data = {
                "client_name": client.get("full_name", ""),
                "therapist_name": therapist.get("full_name", ""),
                "recommended_date": rec_date.strftime("%d %B %Y"),
                "notes": rec.get("notes", ""),
                "days_since": days_since or 30,
                "booking_url": "",  # Can be set to public booking URL if available
            }

            # Check for public booking URL
            therapist_profile = await db.therapist_profiles.find_one(
                {"user_id": therapist_id},
                {"_id": 0, "public_booking_enabled": 1, "custom_slug": 1}
            )
            if therapist_profile and therapist_profile.get("public_booking_enabled"):
                slug = therapist_profile.get("custom_slug", "")
                if slug:
                    template_data["booking_url"] = f"https://cognispace.in/book/{slug}"

            # Send email
            client_email = client.get("email")
            if client_email:
                try:
                    from services.email.templates import get_email_template
                    from services.email.registry import EmailProviderRegistry
                    from services.email.base import EmailMessage

                    email_content = get_email_template(cfg["template"], template_data)
                    message = EmailMessage(
                        to=client_email,
                        subject=email_content["subject"],
                        html_body=email_content["html_body"],
                        text_body=email_content["text_body"]
                    )
                    result = await EmailProviderRegistry.send_email(message)
                    if result.success:
                        logger.info(f"Follow-up {reminder_type} email sent to {client_email}")
                        sent_count += 1
                    else:
                        logger.warning(f"Follow-up email failed for {client_email}: {result.error}")
                except Exception as e:
                    logger.error(f"Follow-up email error: {e}")

            # Send WhatsApp if enabled using approved Twilio template
            if whatsapp_enabled and client.get("mobile"):
                try:
                    from services.whatsapp.registry import WhatsAppProviderRegistry

                    provider = WhatsAppProviderRegistry.get_provider("twilio")
                    if provider and provider.is_available:
                        result = await provider.send_template_message(
                            to_mobile=client["mobile"],
                            content_sid="HX0862a0816754c283b879c246f344c197",
                            content_variables={
                                "1": client.get("full_name", ""),
                                "2": therapist.get("full_name", ""),
                                "3": rec_date.strftime("%d %B %Y")
                            }
                        )
                        if result.success:
                            logger.info(f"WhatsApp follow-up reminder sent to {client.get('mobile')}")
                        else:
                            logger.warning(f"WhatsApp follow-up failed for {client.get('mobile')}: {result.error}")
                    else:
                        logger.debug("WhatsApp provider not available")
                except Exception as e:
                    logger.error(f"WhatsApp follow-up error: {e}")

            # Mark reminder as sent
            await db.follow_up_recommendations.update_one(
                {"id": rec_id},
                {"$set": {flag: True, f"{flag}_at": now_utc.isoformat()}}
            )

            # Log the reminder
            await db.follow_up_reminder_log.insert_one({
                "recommendation_id": rec_id,
                "client_id": client_id,
                "therapist_id": therapist_id,
                "reminder_type": reminder_type,
                "channel": "email" + ("+whatsapp" if whatsapp_enabled else ""),
                "sent_at": now_utc.isoformat(),
                "template": cfg["template"]
            })

        if sent_count > 0:
            logger.info(f"Sent {sent_count} follow-up reminders")

    except Exception as e:
        logger.error(f"Follow-up reminder job error: {e}", exc_info=True)
