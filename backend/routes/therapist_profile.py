"""
Therapist Profile management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import httpx

from database import db
from dependencies import get_current_user, log_audit

router = APIRouter(prefix="/therapist", tags=["therapist-profile"])


# ============= MODELS =============

class TherapistAddress(BaseModel):
    """Indian Address Format"""
    address_line_1: Optional[str] = None  # Building/House No., Street
    address_line_2: Optional[str] = None  # Locality/Area
    pincode: Optional[str] = None         # 6-digit Indian PIN code
    city: Optional[str] = None            # Auto-filled from pincode
    state: Optional[str] = None           # Auto-filled from pincode
    district: Optional[str] = None        # Auto-filled from pincode


class FeeSlot(BaseModel):
    """Consultation fee slot with duration"""
    amount: float
    duration_minutes: int


class TherapistProfileUpdate(BaseModel):
    """Therapist profile update model"""
    # Basic Info
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    profile_photo: Optional[str] = None
    
    # Clinic Info
    clinic_name: Optional[str] = None
    specializations: Optional[List[str]] = None  # Array of specializations (1-5)
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None
    fee_slots: Optional[List[FeeSlot]] = None  # Multiple fee options with duration
    
    # Address (Indian Format)
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    
    # Privacy Settings
    show_mobile_on_receipt: Optional[bool] = None
    show_email_on_receipt: Optional[bool] = None


class TherapistProfile(BaseModel):
    """Full therapist profile"""
    model_config = ConfigDict(extra="ignore")
    
    id: str
    full_name: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    profile_photo: Optional[str] = None
    
    # Clinic Info
    clinic_name: Optional[str] = None
    specializations: Optional[List[str]] = None
    specialization: Optional[str] = None  # Legacy field
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None
    fee_slots: Optional[List[dict]] = None
    consultation_fee: Optional[float] = None  # Legacy field
    
    # Address
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    
    # Legacy address field (for backward compatibility)
    address: Optional[str] = None
    
    # Privacy Settings
    show_mobile_on_receipt: bool = True
    show_email_on_receipt: bool = True
    
    # Subscription info
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None


class PincodeResponse(BaseModel):
    """Response from pincode lookup"""
    pincode: str
    city: str
    state: str
    district: str
    country: str = "India"


# ============= DEPENDENCIES =============

async def require_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    return current_user


# ============= PINCODE LOOKUP =============

@router.get("/pincode/{pincode}", response_model=PincodeResponse)
async def lookup_pincode(pincode: str):
    """
    Lookup Indian pincode to get city, state, district
    Uses India Post API
    """
    # Validate pincode format
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode. Must be 6 digits.")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # India Post API
            response = await client.get(f"https://api.postalpincode.in/pincode/{pincode}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0 and data[0].get("Status") == "Success":
                    post_offices = data[0].get("PostOffice", [])
                    
                    if post_offices and len(post_offices) > 0:
                        po = post_offices[0]
                        return PincodeResponse(
                            pincode=pincode,
                            city=po.get("Block") or po.get("Division") or po.get("District", ""),
                            state=po.get("State", ""),
                            district=po.get("District", ""),
                            country="India"
                        )
            
            # Fallback: Try alternate API
            alt_response = await client.get(f"https://api.worldpostallocations.com/pincode?postalcode={pincode}&countrycode=IN")
            if alt_response.status_code == 200:
                alt_data = alt_response.json()
                if alt_data.get("result"):
                    result = alt_data["result"][0] if isinstance(alt_data["result"], list) else alt_data["result"]
                    return PincodeResponse(
                        pincode=pincode,
                        city=result.get("city", ""),
                        state=result.get("state", ""),
                        district=result.get("district", ""),
                        country="India"
                    )
                    
    except Exception as e:
        # Log error but don't expose internal details
        print(f"Pincode lookup error: {e}")
    
    raise HTTPException(status_code=404, detail="Pincode not found. Please enter city and state manually.")


# ============= PROFILE ENDPOINTS =============

@router.get("/profile", response_model=TherapistProfile)
async def get_therapist_profile(current_user: dict = Depends(require_therapist)):
    """Get current therapist's profile"""
    therapist = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Get therapist profile data if exists
    profile = await db.therapist_profiles.find_one({"therapist_id": current_user["id"]}, {"_id": 0})
    
    # Merge user and profile data
    return TherapistProfile(
        id=therapist["id"],
        full_name=therapist.get("full_name", ""),
        email=therapist.get("email"),
        mobile=therapist.get("mobile"),
        profile_photo=therapist.get("profile_photo") or (profile.get("profile_photo") if profile else None),
        
        # From profile collection
        clinic_name=profile.get("clinic_name") if profile else therapist.get("clinic_name"),
        specializations=profile.get("specializations") if profile else None,
        specialization=profile.get("specialization") if profile else therapist.get("specialization"),
        qualifications=profile.get("qualifications") if profile else therapist.get("qualifications"),
        experience_years=profile.get("experience_years") if profile else therapist.get("experience_years"),
        fee_slots=profile.get("fee_slots") if profile else None,
        consultation_fee=profile.get("consultation_fee") if profile else therapist.get("consultation_fee"),
        
        # Address fields
        address_line_1=profile.get("address_line_1") if profile else None,
        address_line_2=profile.get("address_line_2") if profile else None,
        pincode=profile.get("pincode") if profile else None,
        city=profile.get("city") if profile else None,
        state=profile.get("state") if profile else None,
        district=profile.get("district") if profile else None,
        address=therapist.get("address"),  # Legacy
        
        # Privacy settings
        show_mobile_on_receipt=profile.get("show_mobile_on_receipt", True) if profile else True,
        show_email_on_receipt=profile.get("show_email_on_receipt", True) if profile else True,
        
        # Subscription
        subscription_status=therapist.get("subscription_status"),
        subscription_plan=therapist.get("subscription_plan")
    )


@router.put("/profile", response_model=TherapistProfile)
async def update_therapist_profile(data: TherapistProfileUpdate, current_user: dict = Depends(require_therapist)):
    """Update therapist profile"""
    
    # Fields that go to users collection
    user_update = {}
    if data.full_name is not None:
        user_update["full_name"] = data.full_name
    if data.email is not None:
        user_update["email"] = data.email
    if data.mobile is not None:
        user_update["mobile"] = data.mobile
    if data.profile_photo is not None:
        user_update["profile_photo"] = data.profile_photo
    if data.clinic_name is not None:
        user_update["clinic_name"] = data.clinic_name
    
    # Update users collection
    if user_update:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": user_update}
        )
    
    # Fields that go to therapist_profiles collection
    profile_update = {
        "therapist_id": current_user["id"],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Clinic info
    if data.clinic_name is not None:
        profile_update["clinic_name"] = data.clinic_name
    if data.specialization is not None:
        profile_update["specialization"] = data.specialization
    if data.qualifications is not None:
        profile_update["qualifications"] = data.qualifications
    if data.experience_years is not None:
        profile_update["experience_years"] = data.experience_years
    if data.consultation_fee is not None:
        profile_update["consultation_fee"] = data.consultation_fee
    
    # Address fields
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
    
    # Privacy settings
    if data.show_mobile_on_receipt is not None:
        profile_update["show_mobile_on_receipt"] = data.show_mobile_on_receipt
    if data.show_email_on_receipt is not None:
        profile_update["show_email_on_receipt"] = data.show_email_on_receipt
    
    # Upsert therapist profile
    await db.therapist_profiles.update_one(
        {"therapist_id": current_user["id"]},
        {"$set": profile_update},
        upsert=True
    )
    
    await log_audit(current_user["id"], "therapist", "update", "profile", current_user["id"])
    
    # Return updated profile
    return await get_therapist_profile(current_user)


@router.get("/profile/receipt-info")
async def get_receipt_info(current_user: dict = Depends(require_therapist)):
    """
    Get therapist info formatted for receipts
    Respects privacy settings
    """
    therapist = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    profile = await db.therapist_profiles.find_one({"therapist_id": current_user["id"]}, {"_id": 0})
    
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Check privacy settings
    show_mobile = profile.get("show_mobile_on_receipt", True) if profile else True
    show_email = profile.get("show_email_on_receipt", True) if profile else True
    
    # Build address string
    address_parts = []
    if profile:
        if profile.get("address_line_1"):
            address_parts.append(profile["address_line_1"])
        if profile.get("address_line_2"):
            address_parts.append(profile["address_line_2"])
        if profile.get("city"):
            address_parts.append(profile["city"])
        if profile.get("district") and profile.get("district") != profile.get("city"):
            address_parts.append(profile["district"])
        if profile.get("state"):
            address_parts.append(profile["state"])
        if profile.get("pincode"):
            address_parts.append(f"PIN: {profile['pincode']}")
    
    # Fallback to legacy address
    if not address_parts and therapist.get("address"):
        address_parts = [therapist["address"]]
    
    return {
        "clinic_name": profile.get("clinic_name") if profile else therapist.get("clinic_name"),
        "therapist_name": therapist.get("full_name"),
        "qualifications": profile.get("qualifications") if profile else None,
        "mobile": therapist.get("mobile") if show_mobile else None,
        "email": therapist.get("email") if show_email else None,
        "address": ", ".join(address_parts) if address_parts else None
    }
