"""
Notification Settings Routes - Therapist notification preferences
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os

from dependencies import get_current_user

# Database connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'cognispace')]

router = APIRouter(prefix="/notification-settings", tags=["Notification Settings"])


# ============= MODELS =============

class NotificationPreference(BaseModel):
    event_key: str
    event_name: str
    send_email: bool = True
    send_whatsapp: bool = False


class NotificationPreferenceUpdate(BaseModel):
    event_key: str
    send_email: Optional[bool] = None
    send_whatsapp: Optional[bool] = None


class ChannelAvailability(BaseModel):
    email_allowed: bool
    whatsapp_allowed: bool


# ============= NOTIFICATION EVENTS =============

NOTIFICATION_EVENTS = [
    {"key": "welcome_credentials", "name": "Login Credentials (New Client)", "supports_email": True, "supports_whatsapp": True},
    {"key": "password_changed", "name": "Password Changed", "supports_email": True, "supports_whatsapp": False},
    {"key": "appointment_confirmation", "name": "Appointment Confirmation", "supports_email": True, "supports_whatsapp": True},
    {"key": "appointment_reminder", "name": "Appointment Reminder", "supports_email": True, "supports_whatsapp": True},
    {"key": "payment_receipt", "name": "Payment Receipt", "supports_email": True, "supports_whatsapp": True},
    {"key": "subscription_expiry", "name": "Subscription Expiry Warning", "supports_email": True, "supports_whatsapp": False},
]


# ============= HELPER FUNCTIONS =============

async def get_subscription_channel_availability(therapist_id: str) -> ChannelAvailability:
    """Check which notification channels are allowed by subscription"""
    # Check both collections for backward compatibility
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0, "plan_id": 1, "end_date": 1, "status": 1}
    )
    
    if not subscription:
        subscription = await db.therapist_subscriptions.find_one(
            {"therapist_id": therapist_id},
            {"_id": 0, "plan_id": 1, "end_date": 1}
        )
    
    # Default: email allowed, whatsapp not allowed
    result = ChannelAvailability(email_allowed=True, whatsapp_allowed=False)
    
    if not subscription:
        return result
    
    # Check if subscription is active
    end_date = subscription.get("end_date")
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if end_dt < datetime.now(timezone.utc):
                # Expired subscription - no notifications
                return ChannelAvailability(email_allowed=False, whatsapp_allowed=False)
        except:
            pass
    
    # Check plan features
    plan_id = subscription.get("plan_id")
    if plan_id:
        plan = await db.subscription_plans.find_one(
            {"id": plan_id},
            {"_id": 0, "features": 1}
        )
        if plan:
            features = plan.get("features", {})
            if isinstance(features, dict):
                result.email_allowed = features.get("email_notifications", True)
                result.whatsapp_allowed = features.get("whatsapp_notifications", False)
    
    return result


# ============= API ENDPOINTS =============

@router.get("/channel-availability")
async def get_channel_availability(current_user: dict = Depends(get_current_user)):
    """Get available notification channels based on subscription"""
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Only therapists can access notification settings")
    
    therapist_id = current_user["id"]
    if current_user["role"] == "assistant":
        # Get linked therapist
        assistant = await db.assistants.find_one({"user_id": current_user["id"]}, {"_id": 0, "therapist_id": 1})
        if assistant:
            therapist_id = assistant["therapist_id"]
    
    availability = await get_subscription_channel_availability(therapist_id)
    
    # Check if WhatsApp is configured at system level (provider available)
    from services.whatsapp import WhatsAppService
    whatsapp_provider_configured = WhatsAppService.is_configured()
    
    return {
        "email_allowed": availability.email_allowed,
        "whatsapp_allowed": availability.whatsapp_allowed and whatsapp_provider_configured,
        "whatsapp_configured": whatsapp_provider_configured
    }


@router.get("/events")
async def get_notification_events(current_user: dict = Depends(get_current_user)):
    """Get list of notification events with current preferences"""
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Only therapists can access notification settings")
    
    therapist_id = current_user["id"]
    if current_user["role"] == "assistant":
        assistant = await db.assistants.find_one({"user_id": current_user["id"]}, {"_id": 0, "therapist_id": 1})
        if assistant:
            therapist_id = assistant["therapist_id"]
    
    # Get channel availability
    availability = await get_subscription_channel_availability(therapist_id)
    
    # Get current preferences
    prefs_cursor = db.notification_preferences.find(
        {"therapist_id": therapist_id},
        {"_id": 0}
    )
    prefs_list = await prefs_cursor.to_list(100)
    prefs_dict = {p["event_key"]: p for p in prefs_list}
    
    result = []
    for event in NOTIFICATION_EVENTS:
        pref = prefs_dict.get(event["key"], {})
        result.append({
            "event_key": event["key"],
            "event_name": event["name"],
            "supports_email": event["supports_email"],
            "supports_whatsapp": event["supports_whatsapp"],
            "send_email": pref.get("send_email", True) if availability.email_allowed else False,
            "send_whatsapp": pref.get("send_whatsapp", False) if availability.whatsapp_allowed else False,
            "email_allowed": availability.email_allowed and event["supports_email"],
            "whatsapp_allowed": availability.whatsapp_allowed and event["supports_whatsapp"]
        })
    
    return result


@router.put("/preference")
async def update_notification_preference(
    update: NotificationPreferenceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update notification preference for a specific event"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can update notification settings")
    
    therapist_id = current_user["id"]
    
    # Verify event key is valid
    valid_keys = [e["key"] for e in NOTIFICATION_EVENTS]
    if update.event_key not in valid_keys:
        raise HTTPException(status_code=400, detail="Invalid event key")
    
    # Get channel availability
    availability = await get_subscription_channel_availability(therapist_id)
    
    # Build update document
    update_doc = {"therapist_id": therapist_id, "event_key": update.event_key}
    
    if update.send_email is not None:
        if update.send_email and not availability.email_allowed:
            raise HTTPException(status_code=403, detail="Email notifications not allowed by your subscription")
        update_doc["send_email"] = update.send_email
    
    if update.send_whatsapp is not None:
        if update.send_whatsapp and not availability.whatsapp_allowed:
            raise HTTPException(status_code=403, detail="WhatsApp notifications not allowed by your subscription")
        update_doc["send_whatsapp"] = update.send_whatsapp
    
    update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.notification_preferences.update_one(
        {"therapist_id": therapist_id, "event_key": update.event_key},
        {"$set": update_doc},
        upsert=True
    )
    
    return {"message": "Preference updated successfully"}


@router.put("/preferences/bulk")
async def update_notification_preferences_bulk(
    updates: List[NotificationPreferenceUpdate],
    current_user: dict = Depends(get_current_user)
):
    """Update multiple notification preferences at once"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can update notification settings")
    
    therapist_id = current_user["id"]
    availability = await get_subscription_channel_availability(therapist_id)
    
    valid_keys = [e["key"] for e in NOTIFICATION_EVENTS]
    updated_count = 0
    
    for update in updates:
        if update.event_key not in valid_keys:
            continue
        
        update_doc = {
            "therapist_id": therapist_id,
            "event_key": update.event_key,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if update.send_email is not None:
            update_doc["send_email"] = update.send_email and availability.email_allowed
        
        if update.send_whatsapp is not None:
            update_doc["send_whatsapp"] = update.send_whatsapp and availability.whatsapp_allowed
        
        await db.notification_preferences.update_one(
            {"therapist_id": therapist_id, "event_key": update.event_key},
            {"$set": update_doc},
            upsert=True
        )
        updated_count += 1
    
    return {"message": f"Updated {updated_count} preferences"}
