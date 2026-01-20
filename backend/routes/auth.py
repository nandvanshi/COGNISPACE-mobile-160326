"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid
import os

from database import db
from dependencies import (
    validate_mobile, hash_password, verify_password, create_token,
    get_current_user, log_audit, get_feature_toggles_for_therapist,
    calculate_days_remaining, DEFAULT_FEATURE_TOGGLES
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ============= AUTH MODELS =============

class UserRegister(BaseModel):
    mobile: str
    password: str
    full_name: str
    email: Optional[str] = None


class TherapistApplication(BaseModel):
    mobile: str
    email: EmailStr
    full_name: str
    password: str
    credentials: str
    specialization: str
    years_of_experience: int


class SuperAdminLogin(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    identifier: str
    password: str


class User(BaseModel):
    id: str
    client_id: Optional[str] = None
    therapist_id: Optional[str] = None
    mobile: str
    email: Optional[str] = None
    full_name: str
    role: str
    status: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    token: str
    user: User


class UserPreferences(BaseModel):
    theme: Optional[str] = "calm-professional"


VALID_THEMES = ["calm-professional", "soft-reassuring", "warm-approachable", "clean-saas", "dark-calm"]


# ============= AUTH ENDPOINTS =============

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Client self-registration is DISABLED"""
    raise HTTPException(
        status_code=403, 
        detail="Client self-registration is disabled. Please contact your therapist."
    )


@router.post("/therapist-application")
async def apply_as_therapist(application: TherapistApplication):
    if not validate_mobile(application.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    existing_mobile = await db.users.find_one({"mobile": application.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    existing_email = await db.users.find_one({"email": application.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    application_id = str(uuid.uuid4())
    application_doc = {
        "id": application_id,
        "mobile": application.mobile,
        "email": application.email,
        "full_name": application.full_name,
        "credentials": application.credentials,
        "specialization": application.specialization,
        "years_of_experience": application.years_of_experience,
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None
    }
    
    await db.therapist_applications.insert_one(application_doc)
    
    return {"message": "Application submitted successfully.", "application_id": application_id}


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    user = None
    if validate_mobile(login_data.identifier):
        user = await db.users.find_one({"mobile": login_data.identifier}, {"_id": 0})
    else:
        user = await db.users.find_one({"email": login_data.identifier}, {"_id": 0})
    
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check therapist account status
    if user["role"] == "therapist":
        if user.get("status") != "approved":
            status = user.get("status", "pending_approval")
            if status == "pending_approval":
                raise HTTPException(status_code=403, detail="Your account is pending approval")
            elif status == "suspended":
                raise HTTPException(status_code=403, detail="Your account has been suspended")
            elif status == "rejected":
                raise HTTPException(status_code=403, detail="Your application was rejected")
    
    # Check assistant account status
    if user["role"] == "assistant":
        if user.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Your account has been suspended")
        if user.get("status") == "deleted":
            raise HTTPException(status_code=403, detail="Your account has been deleted")
        therapist = await db.users.find_one({"id": user.get("therapist_id"), "role": "therapist"}, {"_id": 0})
        if not therapist:
            raise HTTPException(status_code=403, detail="Linked therapist account no longer exists")
        if therapist.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Linked therapist account has been suspended")
    
    await log_audit(user["id"], user["role"], "login", "user", user["id"])
    
    # Get therapist_id for clients
    user_therapist_id = user.get("therapist_id")
    if user["role"] == "client":
        profile = await db.client_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        if profile:
            user_therapist_id = profile.get("therapist_id")
    
    token = create_token(user["id"], user.get("mobile", user.get("email", "")), user["role"])
    user_obj = User(
        id=user["id"],
        client_id=user.get("client_id"),
        therapist_id=user_therapist_id,
        mobile=user.get("mobile", ""),
        email=user.get("email"),
        full_name=user["full_name"],
        role=user["role"],
        status=user.get("status"),
        subscription_status=user.get("subscription_status"),
        subscription_plan=user.get("subscription_plan"),
        created_at=datetime.fromisoformat(user["created_at"])
    )
    
    return TokenResponse(token=token, user=user_obj)


@router.post("/super-admin-login", response_model=TokenResponse)
async def super_admin_login(login_data: SuperAdminLogin):
    super_admin_username = os.environ.get('SUPER_ADMIN_USERNAME', 'admin')
    super_admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', 'admin123')
    
    if login_data.username != super_admin_username or login_data.password != super_admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    admin_id = "super_admin"
    token = create_token(admin_id, login_data.username, "super_admin")
    user_obj = User(
        id=admin_id,
        mobile="0000000000",
        email="admin@haven.com",
        full_name="Super Admin",
        role="super_admin",
        created_at=datetime.now(timezone.utc)
    )
    
    return TokenResponse(token=token, user=user_obj)


@router.get("/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    user_therapist_id = current_user.get("therapist_id")
    if current_user["role"] == "client":
        profile = await db.client_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if profile:
            user_therapist_id = profile.get("therapist_id")
    
    return User(
        id=current_user["id"],
        client_id=current_user.get("client_id"),
        therapist_id=user_therapist_id,
        mobile=current_user.get("mobile", ""),
        email=current_user.get("email"),
        full_name=current_user["full_name"],
        role=current_user["role"],
        status=current_user.get("status"),
        subscription_status=current_user.get("subscription_status"),
        subscription_plan=current_user.get("subscription_plan"),
        created_at=datetime.fromisoformat(current_user["created_at"])
    )


@router.get("/subscription-status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status"""
    if current_user["role"] == "assistant":
        therapist = await db.users.find_one({"id": current_user.get("therapist_id")}, {"_id": 0})
        if not therapist:
            return {"is_read_only": True, "subscription_status": None, "feature_toggles": DEFAULT_FEATURE_TOGGLES}
        subscription_status = therapist.get("subscription_status")
        is_read_only = subscription_status not in ["trial", "active"]
        subscription = await db.subscriptions.find_one(
            {"therapist_id": therapist["id"]}, {"_id": 0}, sort=[("start_date", -1)]
        )
        subscription_end_date = subscription.get("end_date") if subscription else None
        feature_toggles = await get_feature_toggles_for_therapist(therapist["id"])
        days_remaining = calculate_days_remaining(subscription_end_date) if subscription_end_date else 0
        return {
            "is_read_only": is_read_only,
            "subscription_status": subscription_status,
            "subscription_plan": therapist.get("subscription_plan"),
            "subscription_end_date": subscription_end_date,
            "feature_toggles": feature_toggles,
            "days_remaining": days_remaining,
            "expiry_warning": days_remaining <= 7 and days_remaining > 0
        }
    
    if current_user["role"] != "therapist":
        return {"is_read_only": False, "subscription_status": None, "feature_toggles": DEFAULT_FEATURE_TOGGLES}
    
    subscription_status = current_user.get("subscription_status")
    is_read_only = subscription_status not in ["trial", "active"]
    subscription = await db.subscriptions.find_one(
        {"therapist_id": current_user["id"]}, {"_id": 0}, sort=[("start_date", -1)]
    )
    subscription_end_date = subscription.get("end_date") if subscription else None
    feature_toggles = await get_feature_toggles_for_therapist(current_user["id"])
    days_remaining = calculate_days_remaining(subscription_end_date) if subscription_end_date else 0
    
    return {
        "is_read_only": is_read_only,
        "subscription_status": subscription_status,
        "subscription_plan": current_user.get("subscription_plan"),
        "subscription_end_date": subscription_end_date,
        "feature_toggles": feature_toggles,
        "days_remaining": days_remaining,
        "expiry_warning": days_remaining <= 7 and days_remaining > 0
    }


# ============= USER PREFERENCES =============

@router.get("/user/preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    prefs = await db.user_preferences.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not prefs:
        return {"theme": "calm-professional"}
    return {"theme": prefs.get("theme", "calm-professional")}


@router.put("/user/preferences")
async def update_user_preferences(prefs: UserPreferences, current_user: dict = Depends(get_current_user)):
    if prefs.theme and prefs.theme not in VALID_THEMES:
        raise HTTPException(status_code=400, detail=f"Invalid theme. Must be one of: {', '.join(VALID_THEMES)}")
    
    await db.user_preferences.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"user_id": current_user["id"], "theme": prefs.theme, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"message": "Preferences updated", "theme": prefs.theme}
