"""Authentication utilities and dependencies"""
import os
import re
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from database import db

# JWT Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

def validate_mobile(mobile: str) -> bool:
    """Validate Indian mobile number format"""
    return bool(re.match(r'^[6-9]\d{9}$', mobile))

def generate_client_id() -> str:
    """Generate unique client ID in format CL-XXXXXX"""
    return f"CL-{uuid.uuid4().hex[:6].upper()}"

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def create_token(user_id: str, email: str, role: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        
        if role == "super_admin":
            return {
                "id": user_id,
                "email": payload.get("email"),
                "role": "super_admin",
                "full_name": "Super Admin"
            }
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require super admin role"""
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user

async def require_therapist(current_user: dict = Depends(get_current_user)) -> dict:
    """Require therapist role"""
    if current_user.get("role") != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    if current_user.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Account not approved")
    return current_user

def get_effective_therapist_id(user: dict) -> str:
    """Get therapist ID for either therapist or assistant"""
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None

async def get_linked_therapist(user: dict) -> dict:
    """Get linked therapist for assistant"""
    if user["role"] != "assistant":
        raise HTTPException(status_code=403, detail="Not an assistant account")
    
    therapist_id = user.get("therapist_id")
    if not therapist_id:
        raise HTTPException(status_code=403, detail="No therapist linked to this assistant")
    
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Linked therapist not found")
    if therapist.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="The therapist account you're linked to has been suspended")
    
    return therapist

async def require_active_therapist_or_assistant(current_user: dict = Depends(get_current_user)) -> dict:
    """Require active therapist or assistant"""
    if current_user["role"] == "therapist":
        if current_user.get("status") != "approved":
            raise HTTPException(status_code=403, detail="Account not approved")
        # Check subscription
        sub_status = current_user.get("subscription_status", "none")
        if sub_status == "expired":
            raise HTTPException(status_code=403, detail="Your subscription has expired. Read-only mode is active.")
        return current_user
    elif current_user["role"] == "assistant":
        therapist = await get_linked_therapist(current_user)
        sub_status = therapist.get("subscription_status", "none")
        if sub_status == "expired":
            raise HTTPException(status_code=403, detail="Therapist subscription has expired. Read-only mode is active.")
        return current_user
    else:
        raise HTTPException(status_code=403, detail="Access denied")

# Default feature toggles
DEFAULT_FEATURE_TOGGLES = {
    "session_notes": True,
    "assessments": True,
    "ai_clinical": True,
    "protocols": True,
    "messaging": True,
    "payments": True,
    "assistants": True,
    "reports": True
}

async def get_feature_toggles_for_therapist(therapist_id: str):
    """Get feature toggles for a therapist based on their subscription plan"""
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
    if not therapist:
        return DEFAULT_FEATURE_TOGGLES
    
    plan_id = therapist.get("subscription_plan")
    if not plan_id:
        return DEFAULT_FEATURE_TOGGLES
    
    plan = await db.subscription_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        return DEFAULT_FEATURE_TOGGLES
    
    return {**DEFAULT_FEATURE_TOGGLES, **(plan.get("feature_toggles") or {})}

async def check_feature_enabled(therapist_id: str, feature: str):
    """Check if a feature is enabled for the therapist"""
    toggles = await get_feature_toggles_for_therapist(therapist_id)
    if not toggles.get(feature, True):
        raise HTTPException(status_code=403, detail=f"Feature '{feature}' not included in your subscription plan")

def require_feature(feature: str):
    """Dependency factory for feature checking"""
    async def check(current_user: dict = Depends(get_current_user)):
        therapist_id = get_effective_therapist_id(current_user)
        if therapist_id:
            await check_feature_enabled(therapist_id, feature)
        return current_user
    return check

async def log_audit(user_id: str, user_role: str, action: str, resource_type: str, resource_id: str, details: dict = None):
    """Log audit entry"""
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_role": user_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
        "created_at": datetime.now(timezone.utc)
    })
