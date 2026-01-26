"""
Notification routes and helper functions
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid

from dependencies import get_current_user

# Database connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'cognispace')]

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ============= MODELS =============

class NotificationCreate(BaseModel):
    user_id: str
    role: str  # therapist, assistant, client
    type: str  # appointment, payment, session, report, system, etc.
    title: str
    message: str
    link: Optional[str] = None  # Route to navigate to
    metadata: Optional[dict] = None  # Additional data


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


# ============= HELPER FUNCTIONS =============

async def create_notification(
    user_id: str,
    role: str,
    notification_type: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    metadata: Optional[dict] = None,
    db_override = None  # Allow passing db from scheduler
) -> dict:
    """Create a new notification for a user"""
    target_db = db_override if db_override is not None else db
    
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "role": role,
        "type": notification_type,
        "title": title,
        "message": message,
        "link": link,
        "metadata": metadata or {},
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await target_db.notifications.insert_one(notification)
    return notification


async def create_bulk_notifications(notifications: List[dict]) -> int:
    """Create multiple notifications at once"""
    if not notifications:
        return 0
    
    for n in notifications:
        n["id"] = str(uuid.uuid4())
        n["is_read"] = False
        n["created_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.notifications.insert_many(notifications)
    return len(result.inserted_ids)


# ============= NOTIFICATION TRIGGERS =============

async def notify_therapist_new_client(therapist_id: str, client_name: str, client_id: str):
    """Notify therapist when a new client registers via their link"""
    await create_notification(
        user_id=therapist_id,
        role="therapist",
        notification_type="client",
        title="New Client Registered",
        message=f"{client_name} has registered as your client.",
        link="clients",
        metadata={"client_id": client_id}
    )


async def notify_therapist_appointment_booked(therapist_id: str, client_name: str, appointment_date: str, appointment_id: str):
    """Notify therapist when client books an appointment"""
    await create_notification(
        user_id=therapist_id,
        role="therapist",
        notification_type="appointment",
        title="Appointment Booked",
        message=f"{client_name} booked an appointment for {appointment_date}.",
        link="schedule",
        metadata={"appointment_id": appointment_id}
    )


async def notify_therapist_notes_pending(therapist_id: str, client_name: str, session_date: str):
    """Notify therapist about pending session notes"""
    await create_notification(
        user_id=therapist_id,
        role="therapist",
        notification_type="session",
        title="Session Notes Pending",
        message=f"Notes pending for {client_name}'s session on {session_date}.",
        link="notes"
    )


async def notify_therapist_payment_due(therapist_id: str, client_name: str, amount: float):
    """Notify therapist about payment due"""
    await create_notification(
        user_id=therapist_id,
        role="therapist",
        notification_type="payment",
        title="Payment Due",
        message=f"Payment of ₹{amount:.0f} pending from {client_name}.",
        link="payments"
    )


async def notify_therapist_subscription_expiring(therapist_id: str, days_remaining: int):
    """Notify therapist about subscription expiring"""
    await create_notification(
        user_id=therapist_id,
        role="therapist",
        notification_type="system",
        title="Subscription Expiring Soon",
        message=f"Your subscription expires in {days_remaining} days. Renew to continue services.",
        link="settings"
    )


async def notify_therapist_consent_pending(therapist_id: str, client_name: str):
    """Notify therapist when client consent is pending"""
    await create_notification(
        user_id=therapist_id,
        role="therapist",
        notification_type="client",
        title="Consent Pending",
        message=f"{client_name}'s consent form is awaiting signature.",
        link="clients"
    )


async def notify_assistant_appointments_today(assistant_id: str, count: int):
    """Notify assistant about today's appointments"""
    await create_notification(
        user_id=assistant_id,
        role="assistant",
        notification_type="appointment",
        title="Today's Schedule",
        message=f"{count} appointment(s) scheduled for today.",
        link="schedule"
    )


async def notify_assistant_checkin_pending(assistant_id: str, client_name: str, time: str):
    """Notify assistant about pending check-in"""
    await create_notification(
        user_id=assistant_id,
        role="assistant",
        notification_type="session",
        title="Check-in Pending",
        message=f"{client_name}'s appointment at {time} - check-in pending.",
        link="schedule"
    )


async def notify_assistant_payment_pending(assistant_id: str, client_name: str):
    """Notify assistant about pending payment"""
    await create_notification(
        user_id=assistant_id,
        role="assistant",
        notification_type="payment",
        title="Payment Pending",
        message=f"Payment pending for {client_name}'s session.",
        link="payments"
    )


async def notify_assistant_new_client(assistant_id: str, client_name: str):
    """Notify assistant about new client added"""
    await create_notification(
        user_id=assistant_id,
        role="assistant",
        notification_type="client",
        title="New Client Added",
        message=f"{client_name} has been added as a new client.",
        link="clients"
    )


async def notify_client_appointment_confirmed(client_id: str, therapist_name: str, date_time: str, appointment_id: str):
    """Notify client when appointment is confirmed"""
    await create_notification(
        user_id=client_id,
        role="client",
        notification_type="appointment",
        title="Appointment Confirmed",
        message=f"Your appointment with {therapist_name} on {date_time} is confirmed.",
        link="appointments",
        metadata={"appointment_id": appointment_id}
    )


async def notify_client_appointment_reminder(client_id: str, therapist_name: str, time_until: str):
    """Notify client with appointment reminder"""
    await create_notification(
        user_id=client_id,
        role="client",
        notification_type="appointment",
        title="Appointment Reminder",
        message=f"Reminder: Your session with {therapist_name} is {time_until}.",
        link="appointments"
    )


async def notify_client_homework_assigned(client_id: str, homework_title: str):
    """Notify client when homework is assigned"""
    await create_notification(
        user_id=client_id,
        role="client",
        notification_type="homework",
        title="New Homework Assigned",
        message=f"You have been assigned: {homework_title}",
        link="homework"
    )


async def notify_client_payment_receipt(client_id: str, amount: float, payment_id: str):
    """Notify client when payment receipt is available"""
    await create_notification(
        user_id=client_id,
        role="client",
        notification_type="payment",
        title="Payment Receipt Available",
        message=f"Receipt for ₹{amount:.0f} is now available.",
        link="payments",
        metadata={"payment_id": payment_id}
    )


async def notify_client_report_shared(client_id: str, report_title: str):
    """Notify client when diagnostic report is shared"""
    await create_notification(
        user_id=client_id,
        role="client",
        notification_type="report",
        title="Report Shared",
        message=f"Your therapist has shared a report: {report_title}",
        link="reports"
    )


# ============= API ENDPOINTS =============

@router.get("")
async def get_notifications(
    limit: int = 50,
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    query = {"user_id": current_user["id"]}
    
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(
        query, 
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return notifications


@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    count = await db.notifications.count_documents({
        "user_id": current_user["id"],
        "is_read": False
    })
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user["id"]},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True}


@router.patch("/mark-all-read")
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    result = await db.notifications.update_many(
        {"user_id": current_user["id"], "is_read": False},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"marked_read": result.modified_count}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a notification"""
    result = await db.notifications.delete_one({
        "id": notification_id,
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True}


@router.delete("/clear-all")
async def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    """Clear all notifications for current user"""
    result = await db.notifications.delete_many({"user_id": current_user["id"]})
    return {"deleted": result.deleted_count}
