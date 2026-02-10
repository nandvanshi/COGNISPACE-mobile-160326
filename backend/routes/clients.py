"""
Client management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import (
    get_current_user, hash_password, log_audit, validate_mobile, generate_client_id
)

router = APIRouter(prefix="/clients", tags=["clients"])


# ============= CLIENT MODELS =============

class ClientCreate(BaseModel):
    mobile: str
    full_name: str
    password: str
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    intake_summary: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    intake_summary: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class ClientProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: Optional[str] = None
    therapist_id: Optional[str] = None
    mobile: str
    email: Optional[str] = None
    full_name: str
    role: str = "client"
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    intake_summary: Optional[str] = None
    profile_photo: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    created_at: datetime


# ============= DEPENDENCIES =============

def get_effective_therapist_id(user: dict) -> str:
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None


async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Therapist or Assistant access required")
    if current_user["role"] == "assistant":
        therapist = await db.users.find_one({"id": current_user.get("therapist_id"), "role": "therapist"}, {"_id": 0})
        if not therapist:
            raise HTTPException(status_code=403, detail="Linked therapist account not found")
        if therapist.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Linked therapist account is suspended")
    return current_user


async def require_active_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "therapist":
        subscription_status = current_user.get("subscription_status")
        if subscription_status not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Subscription expired")
        return current_user
    elif current_user["role"] == "assistant":
        therapist = await db.users.find_one({"id": current_user.get("therapist_id"), "role": "therapist"}, {"_id": 0})
        if not therapist:
            raise HTTPException(status_code=403, detail="Linked therapist not found")
        if therapist.get("subscription_status") not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Therapist subscription expired")
        return current_user
    raise HTTPException(status_code=403, detail="Access denied")


# ============= CLIENT ENDPOINTS =============

@router.post("", response_model=ClientProfile)
async def create_client(client_data: ClientCreate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Create a client - therapist or assistant can create"""
    therapist_id = get_effective_therapist_id(current_user)
    
    if not validate_mobile(client_data.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    existing_mobile = await db.users.find_one({"mobile": client_data.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    if client_data.email:
        existing_email = await db.users.find_one({"email": client_data.email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
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
    
    profile_doc = {
        "user_id": client_id,
        "therapist_id": therapist_id,
        "age": client_data.age,
        "guardian_name": client_data.guardian_name,
        "address": client_data.address,
        "referred_by": client_data.referred_by,
        "intake_summary": client_data.intake_summary,
        "emergency_contact_name": client_data.emergency_contact_name,
        "emergency_contact_phone": client_data.emergency_contact_phone,
        "profile_photo": None
    }
    
    await db.client_profiles.insert_one(profile_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "client", client_id)
    
    return ClientProfile(
        id=client_id,
        client_id=unique_client_id,
        therapist_id=therapist_id,
        mobile=client_data.mobile,
        email=client_data.email,
        full_name=client_data.full_name,
        role="client",
        age=client_data.age,
        guardian_name=client_data.guardian_name,
        address=client_data.address,
        referred_by=client_data.referred_by,
        intake_summary=client_data.intake_summary,
        emergency_contact_name=client_data.emergency_contact_name,
        emergency_contact_phone=client_data.emergency_contact_phone,
        created_at=datetime.fromisoformat(user_doc["created_at"])
    )


@router.get("", response_model=List[ClientProfile])
async def get_clients(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get all clients for the therapist"""
    therapist_id = get_effective_therapist_id(current_user)
    
    profiles = await db.client_profiles.find({"therapist_id": therapist_id}, {"_id": 0}).to_list(1000)
    
    result = []
    for profile in profiles:
        user = await db.users.find_one({"id": profile["user_id"]}, {"_id": 0, "password_hash": 0})
        if user:
            result.append(ClientProfile(
                id=user["id"],
                client_id=user.get("client_id"),
                therapist_id=profile.get("therapist_id"),
                mobile=user.get("mobile", ""),
                email=user.get("email"),
                full_name=user["full_name"],
                role="client",
                age=profile.get("age"),
                guardian_name=profile.get("guardian_name"),
                address=profile.get("address"),
                referred_by=profile.get("referred_by"),
                intake_summary=profile.get("intake_summary"),
                profile_photo=profile.get("profile_photo"),
                emergency_contact_name=profile.get("emergency_contact_name"),
                emergency_contact_phone=profile.get("emergency_contact_phone"),
                created_at=datetime.fromisoformat(user["created_at"])
            ))
    
    return result


# ============= NEW CLIENT NOTIFICATIONS =============

@router.get("/new-registrations/count")
async def get_new_registration_count(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get count of self-registered clients not yet acknowledged"""
    therapist_id = get_effective_therapist_id(current_user)
    
    # Find self-registered clients that haven't been acknowledged
    count = await db.client_profiles.count_documents({
        "therapist_id": therapist_id,
        "self_registered": True,
        "registration_acknowledged": {"$ne": True}
    })
    
    return {"count": count}


@router.get("/new-registrations")
async def get_new_registrations(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get list of self-registered clients not yet acknowledged"""
    therapist_id = get_effective_therapist_id(current_user)
    
    profiles = await db.client_profiles.find({
        "therapist_id": therapist_id,
        "self_registered": True,
        "registration_acknowledged": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    result = []
    for profile in profiles:
        user = await db.users.find_one({"id": profile["user_id"]}, {"_id": 0, "password_hash": 0})
        if user:
            result.append({
                "id": user["id"],
                "client_id": user.get("client_id"),
                "full_name": user["full_name"],
                "mobile": user.get("mobile"),
                "registered_at": profile.get("registered_at"),
                "age": profile.get("age")
            })
    
    return result


@router.post("/new-registrations/acknowledge")
async def acknowledge_new_registrations(current_user: dict = Depends(require_therapist_or_assistant)):
    """Mark all new self-registered clients as acknowledged"""
    therapist_id = get_effective_therapist_id(current_user)
    
    result = await db.client_profiles.update_many(
        {
            "therapist_id": therapist_id,
            "self_registered": True,
            "registration_acknowledged": {"$ne": True}
        },
        {"$set": {"registration_acknowledged": True}}
    )
    
    return {"acknowledged": result.modified_count}


@router.get("/{client_id}", response_model=ClientProfile)
async def get_client(client_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Get single client details"""
    therapist_id = get_effective_therapist_id(current_user)
    
    profile = await db.client_profiles.find_one({"user_id": client_id, "therapist_id": therapist_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    user = await db.users.find_one({"id": client_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Client user not found")
    
    return ClientProfile(
        id=user["id"],
        client_id=user.get("client_id"),
        therapist_id=profile.get("therapist_id"),
        mobile=user.get("mobile", ""),
        email=user.get("email"),
        full_name=user["full_name"],
        role="client",
        age=profile.get("age"),
        guardian_name=profile.get("guardian_name"),
        address=profile.get("address"),
        referred_by=profile.get("referred_by"),
        intake_summary=profile.get("intake_summary"),
        profile_photo=profile.get("profile_photo"),
        emergency_contact_name=profile.get("emergency_contact_name"),
        emergency_contact_phone=profile.get("emergency_contact_phone"),
        created_at=datetime.fromisoformat(user["created_at"])
    )


@router.put("/{client_id}", response_model=ClientProfile)
async def update_client(client_id: str, data: ClientUpdate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Update client details"""
    therapist_id = get_effective_therapist_id(current_user)
    
    profile = await db.client_profiles.find_one({"user_id": client_id, "therapist_id": therapist_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    user_update = {}
    profile_update = {}
    
    if data.full_name:
        user_update["full_name"] = data.full_name
    if data.email is not None:
        if data.email:
            existing = await db.users.find_one({"email": data.email, "id": {"$ne": client_id}})
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
        user_update["email"] = data.email
    if data.mobile:
        if not validate_mobile(data.mobile):
            raise HTTPException(status_code=400, detail="Mobile must be 10 digits")
        existing = await db.users.find_one({"mobile": data.mobile, "id": {"$ne": client_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Mobile already in use")
        user_update["mobile"] = data.mobile
    
    if data.age is not None:
        profile_update["age"] = data.age
    if data.guardian_name is not None:
        profile_update["guardian_name"] = data.guardian_name
    if data.address is not None:
        profile_update["address"] = data.address
    if data.referred_by is not None:
        profile_update["referred_by"] = data.referred_by
    if data.intake_summary is not None:
        profile_update["intake_summary"] = data.intake_summary
    if data.emergency_contact_name is not None:
        profile_update["emergency_contact_name"] = data.emergency_contact_name
    if data.emergency_contact_phone is not None:
        profile_update["emergency_contact_phone"] = data.emergency_contact_phone
    
    if user_update:
        await db.users.update_one({"id": client_id}, {"$set": user_update})
    if profile_update:
        await db.client_profiles.update_one({"user_id": client_id}, {"$set": profile_update})
    
    await log_audit(current_user["id"], current_user["role"], "update", "client", client_id)
    
    updated_user = await db.users.find_one({"id": client_id}, {"_id": 0, "password_hash": 0})
    updated_profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    
    return ClientProfile(
        id=updated_user["id"],
        client_id=updated_user.get("client_id"),
        therapist_id=updated_profile.get("therapist_id"),
        mobile=updated_user.get("mobile", ""),
        email=updated_user.get("email"),
        full_name=updated_user["full_name"],
        role="client",
        age=updated_profile.get("age"),
        guardian_name=updated_profile.get("guardian_name"),
        address=updated_profile.get("address"),
        referred_by=updated_profile.get("referred_by"),
        intake_summary=updated_profile.get("intake_summary"),
        profile_photo=updated_profile.get("profile_photo"),
        emergency_contact_name=updated_profile.get("emergency_contact_name"),
        emergency_contact_phone=updated_profile.get("emergency_contact_phone"),
        created_at=datetime.fromisoformat(updated_user["created_at"])
    )


class PasswordResetRequest(BaseModel):
    new_password: str


@router.post("/{client_id}/reset-password")
async def reset_client_password(client_id: str, request: PasswordResetRequest, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Reset client password"""
    therapist_id = get_effective_therapist_id(current_user)
    
    profile = await db.client_profiles.find_one({"user_id": client_id, "therapist_id": therapist_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    await db.users.update_one(
        {"id": client_id},
        {"$set": {"password_hash": hash_password(request.new_password)}}
    )
    
    await log_audit(current_user["id"], current_user["role"], "reset_password", "client", client_id)
    return {"message": "Password reset successfully"}


@router.post("/{client_id}/photo")
async def update_client_photo(client_id: str, photo_url: str, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Update client profile photo"""
    therapist_id = get_effective_therapist_id(current_user)
    
    result = await db.client_profiles.update_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"$set": {"profile_photo": photo_url}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {"message": "Photo updated"}
