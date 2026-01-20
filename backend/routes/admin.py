"""
Super Admin routes - Therapist and Client management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from dependencies import (
    get_current_user, hash_password, log_audit, validate_mobile,
    DEFAULT_FEATURE_TOGGLES
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============= ADMIN MODELS =============

class TherapistProfile(BaseModel):
    id: str
    mobile: str
    email: Optional[str] = None
    full_name: str
    credentials: str
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    status: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None


class TherapistUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    credentials: Optional[str] = None
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None


class FeeSlotCreate(BaseModel):
    amount: float
    duration_minutes: int


class TherapistCreate(BaseModel):
    mobile: str
    email: EmailStr
    full_name: str
    password: str
    qualifications: str
    specializations: Optional[List[str]] = None
    years_of_experience: Optional[int] = None
    # Clinic Info
    clinic_name: Optional[str] = None
    fee_slots: Optional[List[FeeSlotCreate]] = None
    # Address (Indian Format)
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None


class ClientDetailResponse(BaseModel):
    id: str
    client_id: Optional[str] = None
    mobile: str
    email: Optional[str] = None
    full_name: str
    role: str = "client"
    therapist_id: Optional[str] = None
    therapist_name: Optional[str] = None
    age: Optional[int] = None
    profile_photo: Optional[str] = None
    created_at: str


class ClientAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None


# ============= DEPENDENCIES =============

async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


# ============= THERAPIST APPLICATION ENDPOINTS =============

@router.get("/therapist-applications", response_model=List[TherapistProfile])
async def get_therapist_applications(current_user: dict = Depends(require_super_admin)):
    applications = await db.therapist_applications.find({}, {"_id": 0}).to_list(1000)
    result = []
    for app in applications:
        result.append(TherapistProfile(
            id=app["id"],
            mobile=app["mobile"],
            email=app.get("email"),
            full_name=app["full_name"],
            credentials=app["credentials"],
            specialization=app.get("specialization"),
            years_of_experience=app.get("years_of_experience"),
            status=app["status"],
            subscription_status=None,
            subscription_plan=None,
            created_at=datetime.fromisoformat(app["created_at"]),
            approved_at=datetime.fromisoformat(app["approved_at"]) if app.get("approved_at") else None
        ))
    return result


@router.post("/therapist-applications/{application_id}/approve")
async def approve_therapist(application_id: str, password: str, current_user: dict = Depends(require_super_admin)):
    application = await db.therapist_applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application["status"] != "pending_approval":
        raise HTTPException(status_code=400, detail="Application already processed")
    
    therapist_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=14)
    
    therapist_doc = {
        "id": therapist_id,
        "mobile": application["mobile"],
        "email": application.get("email"),
        "full_name": application["full_name"],
        "password_hash": hash_password(password),
        "role": "therapist",
        "status": "approved",
        "credentials": application["credentials"],
        "specialization": application.get("specialization"),
        "years_of_experience": application.get("years_of_experience"),
        "subscription_status": "trial",
        "subscription_plan": "Trial",
        "created_at": now.isoformat(),
        "approved_at": now.isoformat()
    }
    
    await db.users.insert_one(therapist_doc)
    
    subscription_id = str(uuid.uuid4())
    subscription_doc = {
        "id": subscription_id,
        "therapist_id": therapist_id,
        "plan_id": None,
        "plan_name": "Trial",
        "start_date": now.isoformat(),
        "end_date": trial_end.isoformat(),
        "status": "active",
        "payment_amount": 0,
        "payment_method": "trial",
        "created_at": now.isoformat()
    }
    await db.subscriptions.insert_one(subscription_doc)
    
    await db.therapist_applications.update_one(
        {"id": application_id},
        {"$set": {"status": "approved", "approved_at": now.isoformat()}}
    )
    
    await log_audit(current_user["id"], "super_admin", "approve", "therapist_application", application_id, 
                   {"therapist_id": therapist_id})
    
    return {"message": "Therapist approved successfully", "therapist_id": therapist_id}


@router.post("/therapist-applications/{application_id}/reject")
async def reject_therapist(application_id: str, reason: str = "", current_user: dict = Depends(require_super_admin)):
    application = await db.therapist_applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    await db.therapist_applications.update_one(
        {"id": application_id},
        {"$set": {"status": "rejected", "rejection_reason": reason}}
    )
    
    await log_audit(current_user["id"], "super_admin", "reject", "therapist_application", application_id)
    
    return {"message": "Application rejected"}


# ============= THERAPIST MANAGEMENT ENDPOINTS =============

@router.get("/therapists", response_model=List[TherapistProfile])
async def get_all_therapists(
    status: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin)
):
    query = {"role": "therapist"}
    if status:
        query["status"] = status
    
    therapists = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    result = []
    for t in therapists:
        result.append(TherapistProfile(
            id=t["id"],
            mobile=t.get("mobile", ""),
            email=t.get("email"),
            full_name=t.get("full_name", "Unknown"),
            credentials=t.get("credentials", ""),
            specialization=t.get("specialization"),
            years_of_experience=t.get("years_of_experience"),
            status=t.get("status"),
            subscription_status=t.get("subscription_status"),
            subscription_plan=t.get("subscription_plan"),
            created_at=datetime.fromisoformat(t["created_at"]) if t.get("created_at") else datetime.now(timezone.utc),
            approved_at=datetime.fromisoformat(t["approved_at"]) if t.get("approved_at") else None
        ))
    return result


@router.post("/therapists/{therapist_id}/suspend")
async def suspend_therapist(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"status": "suspended"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    await log_audit(current_user["id"], "super_admin", "suspend", "therapist", therapist_id)
    return {"message": "Therapist suspended"}


@router.post("/therapists/{therapist_id}/activate")
async def activate_therapist(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"status": "approved"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    await log_audit(current_user["id"], "super_admin", "activate", "therapist", therapist_id)
    return {"message": "Therapist activated"}


@router.post("/therapists/{therapist_id}/reset-password")
async def reset_therapist_password(therapist_id: str, new_password: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    await log_audit(current_user["id"], "super_admin", "reset_password", "therapist", therapist_id)
    return {"message": "Password reset successfully"}


@router.post("/therapists/create")
async def create_therapist(data: TherapistCreate, current_user: dict = Depends(require_super_admin)):
    if not validate_mobile(data.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    existing_mobile = await db.users.find_one({"mobile": data.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    existing_email = await db.users.find_one({"email": data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    therapist_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=14)
    
    therapist_doc = {
        "id": therapist_id,
        "mobile": data.mobile,
        "email": data.email,
        "full_name": data.full_name,
        "password_hash": hash_password(data.password),
        "role": "therapist",
        "status": "approved",
        "credentials": data.credentials,
        "specialization": data.specialization,
        "years_of_experience": data.years_of_experience,
        "clinic_name": data.clinic_name,
        "subscription_status": "trial",
        "subscription_plan": "Trial",
        "created_at": now.isoformat(),
        "approved_at": now.isoformat()
    }
    
    await db.users.insert_one(therapist_doc)
    
    # Create therapist profile with address if provided
    if any([data.address_line_1, data.address_line_2, data.pincode, data.city, data.state, data.consultation_fee]):
        profile_doc = {
            "therapist_id": therapist_id,
            "clinic_name": data.clinic_name,
            "consultation_fee": data.consultation_fee,
            "address_line_1": data.address_line_1,
            "address_line_2": data.address_line_2,
            "pincode": data.pincode,
            "city": data.city,
            "state": data.state,
            "district": data.district,
            "show_mobile_on_receipt": True,
            "show_email_on_receipt": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.therapist_profiles.insert_one(profile_doc)
    
    subscription_id = str(uuid.uuid4())
    subscription_doc = {
        "id": subscription_id,
        "therapist_id": therapist_id,
        "plan_id": None,
        "plan_name": "Trial",
        "start_date": now.isoformat(),
        "end_date": trial_end.isoformat(),
        "status": "active",
        "payment_amount": 0,
        "payment_method": "trial",
        "created_at": now.isoformat()
    }
    await db.subscriptions.insert_one(subscription_doc)
    
    await log_audit(current_user["id"], "super_admin", "create", "therapist", therapist_id)
    
    return {"message": "Therapist created successfully", "therapist_id": therapist_id}


@router.put("/therapists/{therapist_id}")
async def update_therapist(therapist_id: str, data: TherapistUpdate, current_user: dict = Depends(require_super_admin)):
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    update_data = {}
    if data.full_name:
        update_data["full_name"] = data.full_name
    if data.email:
        update_data["email"] = data.email
    if data.mobile:
        if not validate_mobile(data.mobile):
            raise HTTPException(status_code=400, detail="Mobile must be 10 digits")
        update_data["mobile"] = data.mobile
    if data.credentials:
        update_data["credentials"] = data.credentials
    if data.specialization:
        update_data["specialization"] = data.specialization
    if data.years_of_experience is not None:
        update_data["years_of_experience"] = data.years_of_experience
    
    if update_data:
        await db.users.update_one({"id": therapist_id}, {"$set": update_data})
        await log_audit(current_user["id"], "super_admin", "update", "therapist", therapist_id)
    
    return {"message": "Therapist updated"}


@router.post("/therapists/{therapist_id}/photo")
async def update_therapist_photo(therapist_id: str, photo_url: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"profile_photo": photo_url}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    return {"message": "Photo updated"}


@router.get("/therapists/{therapist_id}")
async def get_therapist_detail(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0, "password_hash": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    clients_count = await db.client_profiles.count_documents({"therapist_id": therapist_id})
    appointments_count = await db.appointments.count_documents({"therapist_id": therapist_id})
    
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    return {
        **therapist,
        "clients_count": clients_count,
        "appointments_count": appointments_count,
        "current_subscription": subscription
    }


@router.get("/therapists/{therapist_id}/clients")
async def get_therapist_clients(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    profiles = await db.client_profiles.find({"therapist_id": therapist_id}, {"_id": 0}).to_list(1000)
    
    result = []
    for profile in profiles:
        user = await db.users.find_one({"id": profile["user_id"]}, {"_id": 0, "password_hash": 0})
        if user:
            result.append({
                "id": user["id"],
                "client_id": user.get("client_id"),
                "mobile": user.get("mobile"),
                "email": user.get("email"),
                "full_name": user["full_name"],
                "age": profile.get("age"),
                "created_at": user["created_at"]
            })
    
    return result


# ============= CLIENT MANAGEMENT ENDPOINTS =============

@router.get("/clients", response_model=List[ClientDetailResponse])
async def get_all_clients(
    therapist_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin)
):
    query = {"role": "client"}
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(5000)
    
    result = []
    for u in users:
        profile = await db.client_profiles.find_one({"user_id": u["id"]}, {"_id": 0})
        
        if therapist_id and profile and profile.get("therapist_id") != therapist_id:
            continue
        
        therapist_name = None
        if profile and profile.get("therapist_id"):
            therapist = await db.users.find_one({"id": profile["therapist_id"]}, {"_id": 0})
            if therapist:
                therapist_name = therapist.get("full_name")
        
        result.append(ClientDetailResponse(
            id=u["id"],
            client_id=u.get("client_id"),
            mobile=u.get("mobile", ""),
            email=u.get("email"),
            full_name=u["full_name"],
            therapist_id=profile.get("therapist_id") if profile else None,
            therapist_name=therapist_name,
            age=profile.get("age") if profile else None,
            profile_photo=profile.get("profile_photo") if profile else None,
            created_at=u["created_at"]
        ))
    
    return result


@router.get("/clients/{client_id}")
async def get_client_detail(client_id: str, current_user: dict = Depends(require_super_admin)):
    user = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Client not found")
    
    profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    
    therapist_name = None
    if profile and profile.get("therapist_id"):
        therapist = await db.users.find_one({"id": profile["therapist_id"]}, {"_id": 0})
        if therapist:
            therapist_name = therapist.get("full_name")
    
    appointments_count = await db.appointments.count_documents({"client_id": client_id})
    sessions_count = await db.session_notes.count_documents({"client_id": client_id})
    
    return {
        **user,
        "profile": profile,
        "therapist_name": therapist_name,
        "appointments_count": appointments_count,
        "sessions_count": sessions_count
    }


@router.post("/clients/{client_id}/reset-password")
async def reset_client_password(client_id: str, new_password: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": client_id, "role": "client"},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    await log_audit(current_user["id"], "super_admin", "reset_password", "client", client_id)
    return {"message": "Password reset successfully"}


@router.put("/clients/{client_id}")
async def update_client_admin(client_id: str, data: ClientAdminUpdate, current_user: dict = Depends(require_super_admin)):
    user = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Client not found")
    
    user_update = {}
    profile_update = {}
    
    if data.full_name:
        user_update["full_name"] = data.full_name
    if data.email:
        user_update["email"] = data.email
    if data.mobile:
        if not validate_mobile(data.mobile):
            raise HTTPException(status_code=400, detail="Mobile must be 10 digits")
        user_update["mobile"] = data.mobile
    
    if data.age is not None:
        profile_update["age"] = data.age
    if data.guardian_name:
        profile_update["guardian_name"] = data.guardian_name
    if data.address:
        profile_update["address"] = data.address
    
    if user_update:
        await db.users.update_one({"id": client_id}, {"$set": user_update})
    
    if profile_update:
        await db.client_profiles.update_one(
            {"user_id": client_id},
            {"$set": profile_update}
        )
    
    await log_audit(current_user["id"], "super_admin", "update", "client", client_id)
    
    updated_user = await db.users.find_one({"id": client_id}, {"_id": 0, "password_hash": 0})
    profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    
    return {
        "id": updated_user["id"],
        "client_id": updated_user.get("client_id"),
        "mobile": updated_user.get("mobile", ""),
        "email": updated_user.get("email"),
        "full_name": updated_user["full_name"],
        "therapist_id": profile.get("therapist_id") if profile else None,
        "age": profile.get("age") if profile else None,
        "profile_photo": profile.get("profile_photo") if profile else None,
        "created_at": updated_user["created_at"]
    }
