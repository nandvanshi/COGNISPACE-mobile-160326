"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import os

from database import db
from dependencies import (
    validate_mobile, hash_password, verify_password, create_token,
    get_current_user, log_audit, get_feature_toggles_for_therapist,
    calculate_days_remaining, DEFAULT_FEATURE_TOGGLES, generate_client_id,
    generate_registration_code
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
    qualifications: str
    specializations: List[str] = []
    years_of_experience: Optional[int] = None
    clinic_name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    google_maps_link: Optional[str] = None


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


class ForgotPasswordRequest(BaseModel):
    identifier: str  # email or mobile


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyResetTokenRequest(BaseModel):
    token: str


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
    
    # Check for existing pending application
    existing_application = await db.therapist_applications.find_one({
        "$or": [
            {"mobile": application.mobile},
            {"email": application.email}
        ],
        "status": "pending_approval"
    })
    if existing_application:
        raise HTTPException(status_code=400, detail="An application with this mobile/email is already pending approval")
    
    # Validate password
    if len(application.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Hash password for storage
    hashed_password = hash_password(application.password)
    
    application_id = str(uuid.uuid4())
    application_doc = {
        "id": application_id,
        "mobile": application.mobile,
        "email": application.email,
        "full_name": application.full_name,
        "password_hash": hashed_password,
        "qualifications": application.qualifications,
        "specializations": application.specializations or [],
        "years_of_experience": application.years_of_experience,
        "clinic_name": application.clinic_name,
        "address_line_1": application.address_line_1,
        "address_line_2": application.address_line_2,
        "pincode": application.pincode,
        "city": application.city,
        "state": application.state,
        "district": application.district,
        "google_maps_link": application.google_maps_link,
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None
    }
    
    await db.therapist_applications.insert_one(application_doc)
    
    return {"message": "Application submitted successfully. You will be notified once approved.", "application_id": application_id}


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


# ============= CLIENT SELF-REGISTRATION VIA THERAPIST LINK =============

class ClientSelfRegister(BaseModel):
    mobile: str
    password: str
    full_name: str
    email: Optional[str] = None
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


@router.get("/therapist-registration-link")
async def get_therapist_registration_link(current_user: dict = Depends(get_current_user)):
    """Get or generate therapist's unique client registration link"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access registration links")
    
    therapist_id = current_user["id"]
    
    # Check if therapist already has a registration code
    therapist_profile = await db.therapist_profiles.find_one({"therapist_id": therapist_id}, {"_id": 0})
    
    if not therapist_profile:
        # Create profile if doesn't exist
        therapist_profile = {"therapist_id": therapist_id}
        await db.therapist_profiles.insert_one(therapist_profile)
    
    registration_code = therapist_profile.get("registration_code")
    
    if not registration_code:
        # Generate new registration code
        registration_code = generate_registration_code()
        # Ensure uniqueness
        while await db.therapist_profiles.find_one({"registration_code": registration_code}):
            registration_code = generate_registration_code()
        
        await db.therapist_profiles.update_one(
            {"therapist_id": therapist_id},
            {"$set": {"registration_code": registration_code}}
        )
    
    return {
        "registration_code": registration_code,
        "therapist_name": current_user["full_name"]
    }


@router.post("/therapist-registration-link/regenerate")
async def regenerate_registration_link(current_user: dict = Depends(get_current_user)):
    """Regenerate therapist's client registration link (invalidates old link)"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can regenerate registration links")
    
    therapist_id = current_user["id"]
    
    # Generate new unique code
    new_code = generate_registration_code()
    while await db.therapist_profiles.find_one({"registration_code": new_code}):
        new_code = generate_registration_code()
    
    await db.therapist_profiles.update_one(
        {"therapist_id": therapist_id},
        {"$set": {"registration_code": new_code}},
        upsert=True
    )
    
    return {
        "registration_code": new_code,
        "message": "Registration link regenerated. Old link is now invalid."
    }


@router.get("/verify-registration-code/{code}")
async def verify_registration_code(code: str):
    """Verify if a registration code is valid (public endpoint)"""
    therapist_profile = await db.therapist_profiles.find_one({"registration_code": code}, {"_id": 0})
    
    if not therapist_profile:
        raise HTTPException(status_code=404, detail="Invalid registration link")
    
    therapist_id = therapist_profile.get("therapist_id")
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0, "password_hash": 0})
    
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    if therapist.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Therapist account is not active")
    
    return {
        "valid": True,
        "therapist_name": therapist["full_name"],
        "therapist_id": therapist_id
    }


@router.post("/client-self-register/{code}")
async def client_self_register(code: str, client_data: ClientSelfRegister):
    """Client self-registration via therapist's unique link (public endpoint)"""
    # Verify the registration code
    therapist_profile = await db.therapist_profiles.find_one({"registration_code": code}, {"_id": 0})
    
    if not therapist_profile:
        raise HTTPException(status_code=404, detail="Invalid registration link")
    
    therapist_id = therapist_profile.get("therapist_id")
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    if therapist.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Therapist account is not active")
    
    # Validate mobile
    if not validate_mobile(client_data.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    # Check for existing mobile
    existing_mobile = await db.users.find_one({"mobile": client_data.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    # Check for existing email
    if client_data.email:
        existing_email = await db.users.find_one({"email": client_data.email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create client
    client_id = str(uuid.uuid4())
    unique_client_id = generate_client_id()
    
    user_doc = {
        "id": client_id,
        "client_id": unique_client_id,
        "mobile": client_data.mobile,
        "email": client_data.email,
        "password_hash": hash_password(client_data.password),
        "full_name": client_data.full_name,
        "role": "client",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create client profile linked to therapist
    profile_doc = {
        "user_id": client_id,
        "therapist_id": therapist_id,
        "age": client_data.age,
        "guardian_name": client_data.guardian_name,
        "address": client_data.address,
        "referred_by": client_data.referred_by,
        "emergency_contact_name": client_data.emergency_contact_name,
        "emergency_contact_phone": client_data.emergency_contact_phone,
        "profile_photo": None,
        "self_registered": True,  # Flag to indicate self-registration
        "registered_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.client_profiles.insert_one(profile_doc)
    await log_audit(client_id, "client", "self_register", "client", client_id, {"therapist_id": therapist_id})
    
    # Send notification to therapist (in-app)
    from routes.notifications import notify_therapist_new_client
    await notify_therapist_new_client(therapist_id, client_data.full_name, client_id)
    
    # Get assistant email if exists
    assistant_email = None
    assistant = await db.users.find_one(
        {"therapist_id": therapist_id, "role": "assistant"},
        {"_id": 0, "email": 1}
    )
    if assistant:
        assistant_email = assistant.get("email")
    
    # Send email notification to therapist and assistant about new client registration
    try:
        from services.notification_service import NotificationService
        await NotificationService.send_client_self_registration_notification(
            client_name=client_data.full_name,
            client_mobile=client_data.mobile,
            client_email=client_data.email,
            therapist_email=therapist.get("email"),
            assistant_email=assistant_email,
            registration_time=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        print(f"Failed to send registration notification: {e}")
    
    # Send welcome email to client (if email provided)
    if client_data.email:
        try:
            from services.notification_service import NotificationService
            await NotificationService.send_client_welcome(
                client_name=client_data.full_name,
                mobile=client_data.mobile,
                email=client_data.email,
                username=client_data.mobile,
                password=client_data.password,
                therapist_name=therapist["full_name"]
            )
        except Exception as e:
            print(f"Failed to send welcome notification: {e}")
    
    return {
        "message": "Registration successful! You can now login.",
        "client_id": unique_client_id,
        "therapist_name": therapist["full_name"]
    }


# ============= FORGOT PASSWORD ENDPOINTS =============

import secrets
from datetime import timedelta
from services.email.registry import EmailProviderRegistry
from services.email.base import EmailMessage
from services.email.templates import get_email_template


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send password reset link to user's email.
    Works for therapists and clients.
    """
    identifier = request.identifier.strip()
    
    # Find user by email or mobile
    user = await db.users.find_one(
        {"$or": [{"email": identifier}, {"mobile": identifier}]},
        {"_id": 0}
    )
    
    if not user:
        # Don't reveal if user exists - security best practice
        return {"message": "If an account exists with this email/mobile, you will receive a password reset link."}
    
    if not user.get("email"):
        raise HTTPException(
            status_code=400, 
            detail="No email associated with this account. Please contact support."
        )
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token in database
    await db.password_reset_tokens.delete_many({"user_id": user["id"]})  # Remove old tokens
    await db.password_reset_tokens.insert_one({
        "user_id": user["id"],
        "token": reset_token,
        "email": user["email"],
        "expires_at": token_expiry.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "used": False
    })
    
    # Get frontend URL from environment (required for password reset links)
    frontend_url = os.environ.get("FRONTEND_URL") or os.environ.get("REACT_APP_BACKEND_URL", "").replace("/api", "").rstrip("/")
    if not frontend_url:
        frontend_url = "https://cognispace.in"  # Production fallback
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    
    # Send email
    try:
        email_content = get_email_template("password_reset", {
            "user_name": user.get("full_name", "User"),
            "reset_link": reset_link,
            "expiry_hours": 1
        })
        
        message = EmailMessage(
            to=user["email"],
            subject=email_content["subject"],
            html_body=email_content["html_body"],
            text_body=email_content["text_body"]
        )
        
        result = await EmailProviderRegistry.send_email(message)
        if not result.success:
            raise Exception(result.error)
            
    except Exception as e:
        print(f"Failed to send reset email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email. Please try again.")
    
    await log_audit(user["id"], user["role"], "request_password_reset", "user", user["id"])
    
    return {"message": "If an account exists with this email/mobile, you will receive a password reset link."}


@router.post("/verify-reset-token")
async def verify_reset_token(request: VerifyResetTokenRequest):
    """Verify if reset token is valid"""
    token_doc = await db.password_reset_tokens.find_one(
        {"token": request.token, "used": False},
        {"_id": 0}
    )
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    # Check expiry
    expiry = datetime.fromisoformat(token_doc["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    
    return {"valid": True, "email": token_doc["email"]}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using token"""
    # Find and validate token
    token_doc = await db.password_reset_tokens.find_one(
        {"token": request.token, "used": False},
        {"_id": 0}
    )
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    # Check expiry
    expiry = datetime.fromisoformat(token_doc["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expiry:
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Update password
    await db.users.update_one(
        {"id": token_doc["user_id"]},
        {"$set": {"password_hash": hash_password(request.new_password)}}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one(
        {"token": request.token},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Get user for logging
    user = await db.users.find_one({"id": token_doc["user_id"]}, {"_id": 0, "role": 1})
    await log_audit(token_doc["user_id"], user.get("role", "unknown"), "reset_password", "user", token_doc["user_id"])
    
    return {"message": "Password reset successful! You can now login with your new password."}

