"""
Shared dependencies and utilities for routes
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import jwt
import os
import uuid

from database import db

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

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


def validate_mobile(mobile: str) -> bool:
    """Validate that mobile is exactly 10 digits"""
    return mobile.isdigit() and len(mobile) == 10


def generate_client_id() -> str:
    """Generate a unique client ID in format CL-XXXXXX"""
    import random
    return f"CL-{random.randint(100000, 999999)}"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(user_id: str, email: str, role: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_feature_toggles_for_therapist(therapist_id: str):
    """Get active feature toggles for a therapist based on their subscription plan"""
    if not therapist_id:
        return DEFAULT_FEATURE_TOGGLES
    
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
    if not therapist:
        return DEFAULT_FEATURE_TOGGLES
    
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    if not subscription:
        return DEFAULT_FEATURE_TOGGLES
    
    plan = await db.subscription_plans.find_one({"id": subscription.get("plan_id")}, {"_id": 0})
    if not plan or not plan.get("feature_toggles"):
        return DEFAULT_FEATURE_TOGGLES
    
    return {**DEFAULT_FEATURE_TOGGLES, **plan.get("feature_toggles", {})}


async def check_feature_enabled(therapist_id: str, feature_name: str):
    """Check if a feature is enabled for a therapist"""
    toggles = await get_feature_toggles_for_therapist(therapist_id)
    if not toggles.get(feature_name, True):
        raise HTTPException(
            status_code=403, 
            detail=f"Feature '{feature_name}' is not included in your subscription plan"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        # Handle super admin (virtual user not in DB)
        if user_id == "super_admin":
            return {
                "id": "super_admin",
                "mobile": "0000000000",
                "email": "admin@haven.com",
                "full_name": "Super Admin",
                "role": "super_admin",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_feature(feature_name: str):
    """Dependency factory to require a specific feature"""
    async def check_feature(current_user: dict = Depends(get_current_user)):
        if current_user["role"] == "therapist":
            await check_feature_enabled(current_user["id"], feature_name)
        elif current_user["role"] == "assistant":
            await check_feature_enabled(current_user.get("therapist_id"), feature_name)
        return current_user
    return check_feature


async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


async def require_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    return current_user


async def require_active_therapist(current_user: dict = Depends(get_current_user)):
    """Require an active therapist (subscription not expired)"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    
    subscription_status = current_user.get("subscription_status")
    if subscription_status not in ["trial", "active"]:
        raise HTTPException(
            status_code=403, 
            detail="Your subscription has expired. Please renew to perform this action."
        )
    return current_user


async def require_active_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    """Require an active therapist or assistant whose therapist has active subscription"""
    if current_user["role"] == "therapist":
        subscription_status = current_user.get("subscription_status")
        if subscription_status not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Subscription expired")
        return current_user
    elif current_user["role"] == "assistant":
        therapist = await db.users.find_one({"id": current_user.get("therapist_id")}, {"_id": 0})
        if not therapist:
            raise HTTPException(status_code=403, detail="Linked therapist not found")
        if therapist.get("subscription_status") not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Therapist subscription expired")
        return current_user
    else:
        raise HTTPException(status_code=403, detail="Access denied")


def get_effective_therapist_id(current_user: dict) -> str:
    """Get the effective therapist ID for a user (handles assistants)"""
    if current_user["role"] == "therapist":
        return current_user["id"]
    elif current_user["role"] == "assistant":
        return current_user.get("therapist_id")
    return None


async def log_audit(user_id: str, user_role: str, action: str, resource_type: str, resource_id: str, details: dict = None):
    audit = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_role": user_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit)


def calculate_days_remaining(end_date_str):
    """Calculate days remaining from end date string"""
    if not end_date_str:
        return 0
    try:
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = end_date - now
        return max(0, delta.days)
    except:
        return 0
