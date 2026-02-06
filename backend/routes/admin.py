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
    subscription_end_date: Optional[datetime] = None
    created_at: datetime
    approved_at: Optional[datetime] = None


class TherapistUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    qualifications: Optional[str] = None
    specializations: Optional[List[str]] = None
    years_of_experience: Optional[int] = None
    profile_photo: Optional[str] = None
    clinic_name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None


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

@router.get("/therapist-applications")
async def get_therapist_applications(current_user: dict = Depends(require_super_admin)):
    applications = await db.therapist_applications.find({}, {"_id": 0}).to_list(1000)
    result = []
    for app in applications:
        app_data = {
            "id": app["id"],
            "mobile": app["mobile"],
            "email": app.get("email"),
            "full_name": app["full_name"],
            "credentials": app.get("qualifications", app.get("credentials", "")),
            "specializations": app.get("specializations", []),
            "specialization": ", ".join(app.get("specializations", [])) if isinstance(app.get("specializations"), list) else app.get("specialization", ""),
            "years_of_experience": app.get("years_of_experience"),
            "status": app["status"],
            "subscription_status": None,
            "subscription_plan": None,
            "created_at": app["created_at"],
            "approved_at": app.get("approved_at"),
            "has_password": bool(app.get("password_hash")),
            # Clinic Info
            "clinic_name": app.get("clinic_name"),
            "fee_slots": app.get("fee_slots", []),
            # Address
            "address_line_1": app.get("address_line_1"),
            "address_line_2": app.get("address_line_2"),
            "pincode": app.get("pincode"),
            "city": app.get("city"),
            "district": app.get("district"),
            "state": app.get("state"),
            "google_maps_link": app.get("google_maps_link")
        }
        result.append(app_data)
    return result


@router.post("/therapist-applications/{application_id}/approve")
async def approve_therapist(application_id: str, password: Optional[str] = None, current_user: dict = Depends(require_super_admin)):
    application = await db.therapist_applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application["status"] != "pending_approval":
        raise HTTPException(status_code=400, detail="Application already processed")
    
    therapist_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=14)
    
    # Use password from application if provided during registration, otherwise use admin-provided password
    if application.get("password_hash"):
        password_hash = application["password_hash"]
    elif password:
        password_hash = hash_password(password)
    else:
        raise HTTPException(status_code=400, detail="Password required for approval")
    
    therapist_doc = {
        "id": therapist_id,
        "mobile": application["mobile"],
        "email": application.get("email"),
        "full_name": application["full_name"],
        "password_hash": password_hash,
        "role": "therapist",
        "status": "approved",
        "qualifications": application.get("qualifications", application.get("credentials", "")),
        "specializations": application.get("specializations", []),
        "years_of_experience": application.get("years_of_experience"),
        "clinic_name": application.get("clinic_name"),
        "address_line_1": application.get("address_line_1"),
        "address_line_2": application.get("address_line_2"),
        "pincode": application.get("pincode"),
        "city": application.get("city"),
        "state": application.get("state"),
        "district": application.get("district"),
        "google_maps_link": application.get("google_maps_link"),
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
        # Get subscription end_date for this therapist
        subscription = await db.subscriptions.find_one(
            {"therapist_id": t["id"]},
            {"_id": 0, "end_date": 1},
            sort=[("start_date", -1)]
        )
        subscription_end_date = None
        if subscription and subscription.get("end_date"):
            end_date_str = subscription.get("end_date")
            if isinstance(end_date_str, str):
                subscription_end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            elif isinstance(end_date_str, datetime):
                subscription_end_date = end_date_str
        
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
            subscription_end_date=subscription_end_date,
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
        "qualifications": data.qualifications,
        "years_of_experience": data.years_of_experience,
        "clinic_name": data.clinic_name,
        "subscription_status": "trial",
        "subscription_plan": "Trial",
        "created_at": now.isoformat(),
        "approved_at": now.isoformat()
    }
    
    await db.users.insert_one(therapist_doc)
    
    # Create therapist profile with specializations, fee_slots, and address
    profile_doc = {
        "therapist_id": therapist_id,
        "clinic_name": data.clinic_name,
        "qualifications": data.qualifications,
        "specializations": data.specializations or [],
        "fee_slots": [{"amount": slot.amount, "duration_minutes": slot.duration_minutes} for slot in (data.fee_slots or [])],
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
    
    # Update user document
    user_update = {}
    if data.full_name:
        user_update["full_name"] = data.full_name
    if data.email:
        user_update["email"] = data.email
    if data.mobile:
        if not validate_mobile(data.mobile):
            raise HTTPException(status_code=400, detail="Mobile must be 10 digits")
        user_update["mobile"] = data.mobile
    if data.qualifications:
        user_update["qualifications"] = data.qualifications
    if data.years_of_experience is not None:
        user_update["years_of_experience"] = data.years_of_experience
    if data.profile_photo is not None:
        user_update["profile_photo"] = data.profile_photo
    if data.clinic_name is not None:
        user_update["clinic_name"] = data.clinic_name
    
    if user_update:
        await db.users.update_one({"id": therapist_id}, {"$set": user_update})
    
    # Update therapist_profile document
    profile_update = {}
    if data.qualifications:
        profile_update["qualifications"] = data.qualifications
    if data.specializations is not None:
        profile_update["specializations"] = data.specializations
    if data.clinic_name is not None:
        profile_update["clinic_name"] = data.clinic_name
    if data.address_line_1 is not None:
        profile_update["address_line_1"] = data.address_line_1
    if data.address_line_2 is not None:
        profile_update["address_line_2"] = data.address_line_2
    if data.pincode is not None:
        profile_update["pincode"] = data.pincode
    if data.city is not None:
        profile_update["city"] = data.city
    if data.state is not None:
        profile_update["state"] = data.state
    if data.district is not None:
        profile_update["district"] = data.district
    
    if profile_update:
        profile_update["updated_at"] = datetime.now(timezone.utc).isoformat()
        # Use upsert to create profile if it doesn't exist
        await db.therapist_profiles.update_one(
            {"therapist_id": therapist_id},
            {"$set": profile_update},
            upsert=True
        )
    
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
    
    # Fetch therapist profile for additional details (specializations, address, fee_slots)
    therapist_profile = await db.therapist_profiles.find_one({"therapist_id": therapist_id}, {"_id": 0})
    
    clients_count = await db.client_profiles.count_documents({"therapist_id": therapist_id})
    appointments_count = await db.appointments.count_documents({"therapist_id": therapist_id})
    
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    # Extract subscription_end_date for frontend compatibility
    subscription_end_date = None
    if subscription:
        subscription_end_date = subscription.get("end_date")
    
    # Merge therapist user data with profile data
    result = {
        **therapist,
        "client_count": clients_count,
        "appointments_count": appointments_count,
        "current_subscription": subscription,
        "subscription_end_date": subscription_end_date
    }
    
    # Add profile data if exists
    if therapist_profile:
        result["specializations"] = therapist_profile.get("specializations", [])
        result["fee_slots"] = therapist_profile.get("fee_slots", [])
        result["address_line_1"] = therapist_profile.get("address_line_1")
        result["address_line_2"] = therapist_profile.get("address_line_2")
        result["pincode"] = therapist_profile.get("pincode")
        result["city"] = therapist_profile.get("city")
        result["state"] = therapist_profile.get("state")
        result["district"] = therapist_profile.get("district")
        result["google_maps_link"] = therapist_profile.get("google_maps_link")
        # If qualifications is in profile, prefer that
        if therapist_profile.get("qualifications"):
            result["qualifications"] = therapist_profile.get("qualifications")
        if therapist_profile.get("clinic_name"):
            result["clinic_name"] = therapist_profile.get("clinic_name")
    
    # Also check if address data is in users collection (for therapists approved from applications)
    if not result.get("address_line_1") and therapist.get("address_line_1"):
        result["address_line_1"] = therapist.get("address_line_1")
        result["address_line_2"] = therapist.get("address_line_2")
        result["pincode"] = therapist.get("pincode")
        result["city"] = therapist.get("city")
        result["state"] = therapist.get("state")
        result["district"] = therapist.get("district")
        result["google_maps_link"] = therapist.get("google_maps_link")
    
    return result


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


@router.delete("/therapists/{therapist_id}")
async def delete_therapist(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete a therapist and all associated data - allows re-registration with same details"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    therapist_mobile = therapist.get("mobile")
    therapist_email = therapist.get("email")
    therapist_name = therapist.get("full_name")
    
    # Delete all associated data
    # 1. Delete therapist profile
    await db.therapist_profiles.delete_many({"therapist_id": therapist_id})
    await db.therapist_profiles.delete_many({"user_id": therapist_id})
    
    # 2. Delete subscriptions
    await db.subscriptions.delete_many({"therapist_id": therapist_id})
    
    # 3. Delete availability settings
    await db.availability.delete_many({"therapist_id": therapist_id})
    
    # 4. Delete fee slots
    await db.fee_slots.delete_many({"therapist_id": therapist_id})
    
    # 5. Delete appointments (or optionally keep for client records)
    await db.appointments.delete_many({"therapist_id": therapist_id})
    
    # 6. Delete session notes
    await db.session_notes.delete_many({"therapist_id": therapist_id})
    
    # 7. Delete assessments
    await db.assessments.delete_many({"therapist_id": therapist_id})
    
    # 8. Delete diagnostic reports
    await db.diagnostic_reports.delete_many({"therapist_id": therapist_id})
    
    # 9. Delete payments
    await db.payments.delete_many({"therapist_id": therapist_id})
    
    # 10. Delete protocols
    await db.protocols.delete_many({"therapist_id": therapist_id})
    
    # 11. Delete resources
    await db.resources.delete_many({"therapist_id": therapist_id})
    
    # 12. Delete resource assignments
    await db.resource_assignments.delete_many({"therapist_id": therapist_id})
    
    # 13. Delete case histories
    await db.case_histories.delete_many({"therapist_id": therapist_id})
    
    # 14. Delete messages
    await db.messages.delete_many({"therapist_id": therapist_id})
    
    # 15. Delete notifications
    await db.notifications.delete_many({"user_id": therapist_id})
    
    # 16. Delete assistants associated with this therapist
    await db.users.delete_many({"therapist_id": therapist_id, "role": "assistant"})
    
    # 17. Delete client profiles (unlink clients from this therapist)
    await db.client_profiles.delete_many({"therapist_id": therapist_id})
    
    # 18. Finally delete the therapist user
    result = await db.users.delete_one({"id": therapist_id, "role": "therapist"})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failed to delete therapist")
    
    await log_audit(current_user["id"], "super_admin", "delete", "therapist", therapist_id, {
        "deleted_mobile": therapist_mobile,
        "deleted_email": therapist_email,
        "deleted_name": therapist_name
    })
    
    return {
        "message": f"Therapist '{therapist_name}' deleted successfully",
        "deleted_mobile": therapist_mobile,
        "deleted_email": therapist_email,
        "note": "This mobile/email can now be used for new registration"
    }


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


@router.get("/clients/orphaned/list")
async def get_orphaned_clients(current_user: dict = Depends(require_super_admin)):
    """Get clients who are not linked to any therapist (orphaned after therapist deletion)"""
    # Get all client users
    all_clients = await db.users.find({"role": "client"}, {"_id": 0, "password_hash": 0}).to_list(5000)
    
    orphaned = []
    for client in all_clients:
        # Check if client has a profile linked to a therapist
        profile = await db.client_profiles.find_one({"user_id": client["id"]}, {"_id": 0})
        
        if not profile:
            # No profile at all - orphaned
            orphaned.append({
                **client,
                "profile": None,
                "therapist_id": None,
                "therapist_name": None,
                "reason": "No profile exists"
            })
        elif not profile.get("therapist_id"):
            # Profile exists but no therapist linked
            orphaned.append({
                **client,
                "profile": profile,
                "therapist_id": None,
                "therapist_name": None,
                "reason": "Profile has no therapist"
            })
        else:
            # Check if therapist still exists
            therapist = await db.users.find_one({"id": profile["therapist_id"], "role": "therapist"}, {"_id": 0})
            if not therapist:
                orphaned.append({
                    **client,
                    "profile": profile,
                    "therapist_id": profile["therapist_id"],
                    "therapist_name": None,
                    "reason": "Therapist deleted"
                })
    
    return {
        "total_orphaned": len(orphaned),
        "clients": orphaned
    }


@router.post("/clients/{client_id}/link-therapist")
async def link_client_to_therapist(
    client_id: str, 
    therapist_id: str = Query(..., description="Therapist ID to link the client to"),
    current_user: dict = Depends(require_super_admin)
):
    """Link an orphaned client to a new therapist"""
    # Verify client exists
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify therapist exists
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Check if client already has a profile
    existing_profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    
    if existing_profile:
        # Update existing profile with new therapist
        await db.client_profiles.update_one(
            {"user_id": client_id},
            {"$set": {"therapist_id": therapist_id}}
        )
    else:
        # Create new profile
        import uuid
        new_profile = {
            "id": str(uuid.uuid4()),
            "user_id": client_id,
            "therapist_id": therapist_id,
            "full_name": client.get("full_name", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.client_profiles.insert_one(new_profile)
    
    await log_audit(current_user["id"], "super_admin", "link", "client", client_id, {
        "linked_to_therapist": therapist_id,
        "therapist_name": therapist.get("full_name")
    })
    
    return {
        "message": f"Client '{client.get('full_name')}' linked to therapist '{therapist.get('full_name')}'",
        "client_id": client_id,
        "therapist_id": therapist_id
    }


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
