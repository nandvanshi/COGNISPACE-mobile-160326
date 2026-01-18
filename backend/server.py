from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============= MODELS =============

# Auth Models
class UserRegister(BaseModel):
    mobile: str
    password: str
    full_name: str
    role: Literal["client"]  # Only clients can self-register
    email: Optional[EmailStr] = None

class TherapistApplication(BaseModel):
    mobile: str
    email: EmailStr
    full_name: str
    credentials: str  # License number, certification
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    
class SuperAdminLogin(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    identifier: str  # Can be mobile or email
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: Optional[str] = None  # Only for clients
    mobile: str
    email: Optional[str] = None
    full_name: str
    role: str
    status: Optional[str] = None  # For therapists: pending_approval, approved, suspended, rejected
    subscription_status: Optional[str] = None  # For therapists: trial, active, expired, cancelled
    subscription_plan: Optional[str] = None
    created_at: datetime

class TokenResponse(BaseModel):
    token: str
    user: User

# Client Profile Models
class ClientProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str  # Immutable - auto-generated
    therapist_id: str
    mobile: str
    email: Optional[str] = None
    full_name: str
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    intake_summary: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    profile_photo: Optional[str] = None
    created_at: datetime

class ClientProfileUpdate(BaseModel):
    # User fields (editable)
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    # Profile fields
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    intake_summary: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    profile_photo: Optional[str] = None

class ClientPasswordReset(BaseModel):
    new_password: str

# Appointment Models
class AppointmentCreate(BaseModel):
    client_id: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[Literal["scheduled", "completed", "cancelled"]] = None

class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    status: str = "scheduled"  # scheduled, completed, cancelled
    created_at: datetime

# Therapist Availability Models
class TimeBlock(BaseModel):
    start_time: str  # Format: "HH:MM" (24-hour)
    end_time: str    # Format: "HH:MM" (24-hour)

class DayAvailability(BaseModel):
    enabled: bool = False
    time_blocks: List[TimeBlock] = []

class TherapistAvailabilityUpdate(BaseModel):
    session_duration: Optional[int] = None  # Duration in minutes (e.g., 45, 60)
    buffer_time: Optional[int] = None  # Buffer between sessions in minutes
    monday: Optional[DayAvailability] = None
    tuesday: Optional[DayAvailability] = None
    wednesday: Optional[DayAvailability] = None
    thursday: Optional[DayAvailability] = None
    friday: Optional[DayAvailability] = None
    saturday: Optional[DayAvailability] = None
    sunday: Optional[DayAvailability] = None

class TherapistAvailability(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    session_duration: int = 60  # Default 60 minutes
    buffer_time: int = 0  # Default no buffer
    monday: DayAvailability = DayAvailability()
    tuesday: DayAvailability = DayAvailability()
    wednesday: DayAvailability = DayAvailability()
    thursday: DayAvailability = DayAvailability()
    friday: DayAvailability = DayAvailability()
    saturday: DayAvailability = DayAvailability()
    sunday: DayAvailability = DayAvailability()
    updated_at: datetime

class BlockedTimeCreate(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = None
    is_all_day: bool = False

class BlockedTime(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = None
    is_all_day: bool = False
    created_at: datetime

class AvailableSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_minutes: int

# Session Note Models
class SessionNoteCreate(BaseModel):
    client_id: str
    template_type: Literal["SOAP", "DAP"]
    appointment_id: Optional[str] = None  # Link to appointment
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None

class SessionNoteUpdate(BaseModel):
    template_type: Optional[Literal["SOAP", "DAP"]] = None
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None

class SessionNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    appointment_id: Optional[str] = None
    appointment_date: Optional[str] = None
    template_type: str
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Recurring Appointment Models
class RecurringPatternCreate(BaseModel):
    client_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # "HH:MM" format
    end_time: str    # "HH:MM" format
    notes: Optional[str] = None
    start_date: str  # YYYY-MM-DD - when to start generating
    end_date: Optional[str] = None  # YYYY-MM-DD - when to stop (None = indefinite)

class RecurringPattern(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    day_of_week: int
    start_time: str
    end_time: str
    notes: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    is_active: bool = True
    created_at: datetime

# Message Models
class MessageCreate(BaseModel):
    recipient_id: str
    content: str

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    sender_id: str
    sender_name: str
    recipient_id: str
    recipient_name: str
    content: str
    read: bool = False
    created_at: datetime

# Assessment Models
class CustomAssessmentCreate(BaseModel):
    name: str
    description: str
    questions: List[dict]  # [{"q": "question", "options": ["opt1", "opt2"]}]

class CustomAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    name: str
    description: str
    questions: List[dict]
    created_at: datetime

class AssessmentCreate(BaseModel):
    client_id: str
    assessment_type: str
    questions: List[dict]
    is_custom: bool = False
    custom_assessment_id: Optional[str] = None

class Assessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    assessment_type: str
    questions: List[dict]
    answers: Optional[List[dict]] = None
    score: Optional[int] = None
    status: str = "assigned"
    created_at: datetime
    completed_at: Optional[datetime] = None

class AssessmentSubmit(BaseModel):
    answers: List[dict]

# Protocol Models
class ProtocolCreate(BaseModel):
    client_id: str
    modality: str
    condition: str
    sessions: List[dict]

class Protocol(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    modality: str
    condition: str
    sessions: List[dict]
    is_template: bool = False
    created_at: datetime
    updated_at: datetime

# Homework Models
class HomeworkCreate(BaseModel):
    client_id: str
    title: str
    description: str
    due_date: Optional[datetime] = None

class Homework(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    title: str
    description: str
    due_date: Optional[datetime] = None
    status: str = "assigned"
    client_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

class HomeworkComplete(BaseModel):
    client_notes: str

# Payment Models
class PaymentCreate(BaseModel):
    client_id: str
    amount: float
    payment_method: str
    notes: Optional[str] = None

class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    amount: float
    payment_method: str
    notes: Optional[str] = None
    created_at: datetime

# Audit Log
class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    user_role: str
    action: str
    resource_type: str
    resource_id: str
    details: Optional[dict] = None
    created_at: datetime

# Subscription Models
class SubscriptionPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    price: float
    duration_days: int
    features: List[str]
    max_clients: Optional[int] = None
    created_at: datetime

class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    plan_id: str
    plan_name: str
    status: str  # trial, active, expired, cancelled
    start_date: datetime
    end_date: datetime
    coupon_code: Optional[str] = None

class CouponCode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    code: str
    discount_percent: float
    valid_until: datetime
    max_uses: Optional[int] = None
    used_count: int
    created_by: str
    created_at: datetime

# Therapist Management Models
class TherapistProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    mobile: str
    email: Optional[str] = None
    full_name: str
    credentials: str
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    status: str  # pending_approval, approved, suspended, rejected
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_end_date: Optional[datetime] = None
    profile_photo: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None

class ManualTherapistCreate(BaseModel):
    mobile: str
    email: EmailStr
    full_name: str
    password: str
    credentials: str
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None

class TherapistUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    credentials: Optional[str] = None
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    profile_photo: Optional[str] = None

class ClientDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    mobile: str
    email: Optional[str] = None
    full_name: str
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    intake_summary: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    therapist_id: Optional[str] = None
    therapist_name: Optional[str] = None
    created_at: datetime

# ============= UTILITY FUNCTIONS =============

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

# ============= AUTH ENDPOINTS =============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """
    Client self-registration is DISABLED for security and data isolation.
    Clients must be created by their assigned therapist or Super Admin.
    """
    raise HTTPException(
        status_code=403, 
        detail="Client self-registration is disabled. Please contact your therapist to create an account for you."
    )

@api_router.post("/auth/therapist-application")
async def apply_as_therapist(application: TherapistApplication):
    # Validate mobile number
    if not validate_mobile(application.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    # Check if mobile or email already exists
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
    
    return {"message": "Application submitted successfully. You will be notified once approved.", "application_id": application_id}

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    # Try to find user by mobile or email
    user = None
    if validate_mobile(login_data.identifier):
        # Login with mobile
        user = await db.users.find_one({"mobile": login_data.identifier}, {"_id": 0})
    else:
        # Login with email
        user = await db.users.find_one({"email": login_data.identifier}, {"_id": 0})
    
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check therapist account status (but allow login - will be read-only if expired)
    if user["role"] == "therapist":
        if user.get("status") != "approved":
            status = user.get("status", "pending_approval")
            if status == "pending_approval":
                raise HTTPException(status_code=403, detail="Your account is pending approval")
            elif status == "suspended":
                raise HTTPException(status_code=403, detail="Your account has been suspended")
            elif status == "rejected":
                raise HTTPException(status_code=403, detail="Your application was rejected")
        
        # Note: We no longer block login for expired subscriptions
        # Expired therapists can login but will be in read-only mode
    
    await log_audit(user["id"], user["role"], "login", "user", user["id"])
    
    token = create_token(user["id"], user.get("mobile", user.get("email", "")), user["role"])
    user_obj = User(
        id=user["id"],
        client_id=user.get("client_id"),
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

@api_router.post("/auth/super-admin-login", response_model=TokenResponse)
async def super_admin_login(login_data: SuperAdminLogin):
    # Check against environment variable or database
    super_admin_username = os.environ.get('SUPER_ADMIN_USERNAME', 'admin')
    super_admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', 'admin123')
    
    if login_data.username != super_admin_username or login_data.password != super_admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    # Create a virtual super admin user
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

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(
        id=current_user["id"],
        client_id=current_user.get("client_id"),
        mobile=current_user.get("mobile", ""),
        email=current_user.get("email"),
        full_name=current_user["full_name"],
        role=current_user["role"],
        created_at=datetime.fromisoformat(current_user["created_at"])
    )

@api_router.get("/auth/subscription-status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status (for therapists)"""
    if current_user["role"] != "therapist":
        return {"is_read_only": False, "subscription_status": None, "subscription_end_date": None}
    
    subscription_status = current_user.get("subscription_status")
    is_read_only = subscription_status not in ["trial", "active"]
    
    # Get subscription end date
    subscription = await db.subscriptions.find_one(
        {"therapist_id": current_user["id"]},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    subscription_end_date = subscription.get("end_date") if subscription else None
    
    return {
        "is_read_only": is_read_only,
        "subscription_status": subscription_status,
        "subscription_plan": current_user.get("subscription_plan"),
        "subscription_end_date": subscription_end_date
    }

# ============= SUPER ADMIN ENDPOINTS =============

async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user

async def require_therapist(current_user: dict = Depends(get_current_user)):
    """Allows any therapist to access (for read operations)"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    # Check if suspended or rejected
    status = current_user.get("status")
    if status == "suspended":
        raise HTTPException(status_code=403, detail="Your account has been suspended")
    if status == "rejected":
        raise HTTPException(status_code=403, detail="Your application was rejected")
    return current_user

async def require_active_therapist(current_user: dict = Depends(get_current_user)):
    """Requires therapist with active/trial subscription (for write operations)"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    # Check account status
    status = current_user.get("status")
    if status == "suspended":
        raise HTTPException(status_code=403, detail="Your account has been suspended")
    if status == "rejected":
        raise HTTPException(status_code=403, detail="Your application was rejected")
    # Check subscription status
    subscription_status = current_user.get("subscription_status")
    if subscription_status not in ["trial", "active"]:
        raise HTTPException(
            status_code=403, 
            detail="Your subscription has expired. You are in read-only mode. Please renew to make changes."
        )
    return current_user

def is_subscription_active(user: dict) -> bool:
    """Helper to check if subscription is active"""
    subscription_status = user.get("subscription_status")
    return subscription_status in ["trial", "active"]

@api_router.get("/admin/therapist-applications", response_model=List[TherapistProfile])
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

@api_router.post("/admin/therapist-applications/{application_id}/approve")
async def approve_therapist(application_id: str, password: str, current_user: dict = Depends(require_super_admin)):
    application = await db.therapist_applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application["status"] != "pending_approval":
        raise HTTPException(status_code=400, detail="Application already processed")
    
    # Create therapist user account
    therapist_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    user_doc = {
        "id": therapist_id,
        "mobile": application["mobile"],
        "email": application.get("email"),
        "password_hash": hash_password(password),
        "full_name": application["full_name"],
        "role": "therapist",
        "status": "approved",
        "subscription_status": "trial",  # Start with free trial
        "subscription_plan": "free_trial",
        "created_at": now.isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create trial subscription (30 days)
    subscription_doc = {
        "id": str(uuid.uuid4()),
        "therapist_id": therapist_id,
        "plan_id": "free_trial",
        "plan_name": "Free Trial",
        "status": "trial",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=30)).isoformat(),
        "coupon_code": None
    }
    
    await db.subscriptions.insert_one(subscription_doc)
    
    # Update application status
    await db.therapist_applications.update_one(
        {"id": application_id},
        {"$set": {"status": "approved", "approved_at": now.isoformat()}}
    )
    
    await log_audit(current_user["id"], current_user["role"], "approve", "therapist", therapist_id)
    
    return {"message": "Therapist approved successfully", "therapist_id": therapist_id, "password": password}

@api_router.post("/admin/therapist-applications/{application_id}/reject")
async def reject_therapist(application_id: str, current_user: dict = Depends(require_super_admin)):
    application = await db.therapist_applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    await db.therapist_applications.update_one(
        {"id": application_id},
        {"$set": {"status": "rejected"}}
    )
    
    await log_audit(current_user["id"], current_user["role"], "reject", "therapist_application", application_id)
    
    return {"message": "Application rejected"}

@api_router.get("/admin/therapists", response_model=List[TherapistProfile])
async def get_all_therapists(current_user: dict = Depends(require_super_admin)):
    therapists = await db.users.find({"role": "therapist"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    result = []
    for therapist in therapists:
        # Get application details if exists
        therapist_mobile = therapist.get("mobile", "")
        app = await db.therapist_applications.find_one({"mobile": therapist_mobile}, {"_id": 0}) if therapist_mobile else None
        
        # Get subscription end date
        subscription = await db.subscriptions.find_one(
            {"therapist_id": therapist["id"]},
            {"_id": 0},
            sort=[("start_date", -1)]
        )
        subscription_end_date = None
        if subscription and subscription.get("end_date"):
            subscription_end_date = datetime.fromisoformat(subscription["end_date"])
        
        result.append(TherapistProfile(
            id=therapist["id"],
            mobile=therapist_mobile,
            email=therapist.get("email"),
            full_name=therapist["full_name"],
            credentials=therapist.get("credentials") or (app.get("credentials", "N/A") if app else "N/A"),
            specialization=therapist.get("specialization") or (app.get("specialization") if app else None),
            years_of_experience=therapist.get("years_of_experience") or (app.get("years_of_experience") if app else None),
            status=therapist.get("status", "approved"),
            subscription_status=therapist.get("subscription_status"),
            subscription_plan=therapist.get("subscription_plan"),
            subscription_end_date=subscription_end_date,
            profile_photo=therapist.get("profile_photo"),
            created_at=datetime.fromisoformat(therapist["created_at"]),
            approved_at=datetime.fromisoformat(app["approved_at"]) if app and app.get("approved_at") else None
        ))
    return result

@api_router.post("/admin/therapists/{therapist_id}/suspend")
async def suspend_therapist(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"status": "suspended"}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    await log_audit(current_user["id"], current_user["role"], "suspend", "therapist", therapist_id)
    
    return {"message": "Therapist suspended"}

@api_router.post("/admin/therapists/{therapist_id}/activate")
async def activate_therapist(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"status": "approved"}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    await log_audit(current_user["id"], current_user["role"], "activate", "therapist", therapist_id)
    
    return {"message": "Therapist activated"}

@api_router.post("/admin/therapists/{therapist_id}/reset-password")
async def reset_therapist_password(therapist_id: str, new_password: str, current_user: dict = Depends(require_super_admin)):
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    await log_audit(current_user["id"], current_user["role"], "reset_password", "therapist", therapist_id)
    
    return {"message": "Password reset successfully", "new_password": new_password}

@api_router.post("/admin/therapists/create")
async def create_therapist_manually(therapist_data: ManualTherapistCreate, current_user: dict = Depends(require_super_admin)):
    """Manually create a therapist account without application process"""
    # Validate mobile
    if not validate_mobile(therapist_data.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    # Check if mobile or email already exists
    existing_mobile = await db.users.find_one({"mobile": therapist_data.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    existing_email = await db.users.find_one({"email": therapist_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    therapist_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    user_doc = {
        "id": therapist_id,
        "mobile": therapist_data.mobile,
        "email": therapist_data.email,
        "password_hash": hash_password(therapist_data.password),
        "full_name": therapist_data.full_name,
        "credentials": therapist_data.credentials,
        "specialization": therapist_data.specialization,
        "years_of_experience": therapist_data.years_of_experience,
        "role": "therapist",
        "status": "approved",
        "subscription_status": "trial",
        "subscription_plan": "free_trial",
        "profile_photo": None,
        "created_at": now.isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create trial subscription (30 days)
    subscription_doc = {
        "id": str(uuid.uuid4()),
        "therapist_id": therapist_id,
        "plan_id": "free_trial",
        "plan_name": "Free Trial",
        "status": "trial",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=30)).isoformat(),
        "coupon_code": None
    }
    await db.subscriptions.insert_one(subscription_doc)
    
    await log_audit(current_user["id"], current_user["role"], "create_manual", "therapist", therapist_id)
    
    return {"message": "Therapist created successfully", "therapist_id": therapist_id}

@api_router.put("/admin/therapists/{therapist_id}")
async def update_therapist(therapist_id: str, update_data: TherapistUpdate, current_user: dict = Depends(require_super_admin)):
    """Update therapist details"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    update_fields = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Check email uniqueness if being updated
    if "email" in update_fields:
        existing = await db.users.find_one({"email": update_fields["email"], "id": {"$ne": therapist_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    await db.users.update_one({"id": therapist_id}, {"$set": update_fields})
    
    await log_audit(current_user["id"], current_user["role"], "update", "therapist", therapist_id, update_fields)
    
    return {"message": "Therapist updated successfully"}

@api_router.post("/admin/therapists/{therapist_id}/photo")
async def upload_therapist_photo(therapist_id: str, photo_url: str, current_user: dict = Depends(require_super_admin)):
    """Update therapist profile photo URL"""
    result = await db.users.update_one(
        {"id": therapist_id, "role": "therapist"},
        {"$set": {"profile_photo": photo_url}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    await log_audit(current_user["id"], current_user["role"], "update_photo", "therapist", therapist_id)
    
    return {"message": "Photo updated successfully"}

@api_router.get("/admin/therapists/{therapist_id}")
async def get_therapist_detail(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    """Get detailed therapist profile including subscription info"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0, "password_hash": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Get subscription details
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    # Get application details
    app = await db.therapist_applications.find_one({"mobile": therapist.get("mobile", "")}, {"_id": 0})
    
    # Get client count
    client_count = await db.client_profiles.count_documents({"therapist_id": therapist_id})
    
    return {
        "id": therapist["id"],
        "mobile": therapist.get("mobile", ""),
        "email": therapist.get("email"),
        "full_name": therapist["full_name"],
        "credentials": therapist.get("credentials") or (app.get("credentials", "N/A") if app else "N/A"),
        "specialization": therapist.get("specialization") or (app.get("specialization") if app else None),
        "years_of_experience": therapist.get("years_of_experience") or (app.get("years_of_experience") if app else None),
        "status": therapist.get("status", "approved"),
        "profile_photo": therapist.get("profile_photo"),
        "subscription_status": therapist.get("subscription_status"),
        "subscription_plan": therapist.get("subscription_plan"),
        "subscription_end_date": subscription.get("end_date") if subscription else None,
        "client_count": client_count,
        "created_at": therapist["created_at"],
        "approved_at": app.get("approved_at") if app else None
    }

@api_router.get("/admin/therapists/{therapist_id}/clients")
async def get_therapist_clients(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    """Get all clients assigned to a therapist"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Find all client profiles for this therapist
    client_profiles = await db.client_profiles.find({"therapist_id": therapist_id}, {"_id": 0}).to_list(1000)
    
    clients = []
    for profile in client_profiles:
        client = await db.users.find_one({"id": profile["user_id"]}, {"_id": 0, "password_hash": 0})
        if client:
            clients.append({
                "id": client["id"],
                "client_id": client.get("client_id", ""),
                "mobile": client.get("mobile", "N/A"),
                "email": client.get("email"),
                "full_name": client["full_name"],
                "age": profile.get("age"),
                "created_at": client["created_at"]
            })
    
    return clients

@api_router.get("/admin/clients", response_model=List[ClientDetailResponse])
async def get_all_clients(current_user: dict = Depends(require_super_admin)):
    """Get all clients with full details including assigned therapist"""
    clients = await db.users.find({"role": "client"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    result = []
    for client in clients:
        # Get client profile
        profile = await db.client_profiles.find_one({"user_id": client["id"]}, {"_id": 0})
        
        # Get therapist info
        therapist_name = None
        therapist_id = None
        if profile and profile.get("therapist_id"):
            therapist_id = profile["therapist_id"]
            therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
            if therapist:
                therapist_name = therapist["full_name"]
        
        result.append(ClientDetailResponse(
            id=client["id"],
            client_id=client.get("client_id", ""),
            mobile=client.get("mobile", "N/A"),
            email=client.get("email"),
            full_name=client["full_name"],
            age=profile.get("age") if profile else None,
            guardian_name=profile.get("guardian_name") if profile else None,
            address=profile.get("address") if profile else None,
            referred_by=profile.get("referred_by") if profile else None,
            intake_summary=profile.get("intake_summary") if profile else None,
            emergency_contact_name=profile.get("emergency_contact_name") if profile else None,
            emergency_contact_phone=profile.get("emergency_contact_phone") if profile else None,
            therapist_id=therapist_id,
            therapist_name=therapist_name,
            created_at=datetime.fromisoformat(client["created_at"])
        ))
    
    return result

@api_router.get("/admin/clients/{client_id}")
async def get_client_detail(client_id: str, current_user: dict = Depends(require_super_admin)):
    """Get detailed client profile including assigned therapist"""
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0, "password_hash": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    
    # Get therapist info
    therapist_name = None
    therapist_id = None
    if profile and profile.get("therapist_id"):
        therapist_id = profile["therapist_id"]
        therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
        if therapist:
            therapist_name = therapist["full_name"]
    
    return {
        "id": client["id"],
        "client_id": client.get("client_id", ""),
        "mobile": client.get("mobile", "N/A"),
        "email": client.get("email"),
        "full_name": client["full_name"],
        "age": profile.get("age") if profile else None,
        "guardian_name": profile.get("guardian_name") if profile else None,
        "address": profile.get("address") if profile else None,
        "referred_by": profile.get("referred_by") if profile else None,
        "intake_summary": profile.get("intake_summary") if profile else None,
        "emergency_contact_name": profile.get("emergency_contact_name") if profile else None,
        "emergency_contact_phone": profile.get("emergency_contact_phone") if profile else None,
        "therapist_id": therapist_id,
        "therapist_name": therapist_name,
        "created_at": client["created_at"]
    }

@api_router.post("/admin/clients/{client_id}/reset-password")
async def reset_client_password(client_id: str, password_data: ClientPasswordReset, current_user: dict = Depends(require_super_admin)):
    """Admin endpoint to reset client password"""
    result = await db.users.update_one(
        {"id": client_id, "role": "client"},
        {"$set": {"password_hash": hash_password(password_data.new_password)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    await log_audit(current_user["id"], current_user["role"], "reset_password", "client", client_id)
    
    return {"message": "Password reset successfully", "new_password": password_data.new_password}

@api_router.put("/admin/clients/{client_id}")
async def admin_update_client(client_id: str, update_data: ClientProfileUpdate, current_user: dict = Depends(require_super_admin)):
    """Admin endpoint to update client details"""
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Separate user fields from profile fields
    user_fields = {}
    profile_fields = {}
    
    # User fields (stored in users collection)
    if "full_name" in update_dict:
        user_fields["full_name"] = update_dict.pop("full_name")
    if "mobile" in update_dict:
        new_mobile = update_dict.pop("mobile")
        if not validate_mobile(new_mobile):
            raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
        existing = await db.users.find_one({"mobile": new_mobile, "id": {"$ne": client_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Mobile number already in use")
        user_fields["mobile"] = new_mobile
    if "email" in update_dict:
        new_email = update_dict.pop("email")
        if new_email:
            existing = await db.users.find_one({"email": new_email, "id": {"$ne": client_id}})
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
        user_fields["email"] = new_email
    
    # Profile fields
    profile_fields = update_dict
    profile_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Update user document
    if user_fields:
        await db.users.update_one({"id": client_id}, {"$set": user_fields})
    
    # Update profile document
    if profile_fields:
        await db.client_profiles.update_one(
            {"user_id": client_id},
            {"$set": profile_fields},
            upsert=True
        )
    
    await log_audit(current_user["id"], current_user["role"], "update", "client", client_id, {**user_fields, **profile_fields})
    
    # Return updated client
    updated_client = await db.users.find_one({"id": client_id}, {"_id": 0, "password_hash": 0})
    profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    
    return {
        "id": updated_client["id"],
        "client_id": updated_client.get("client_id", ""),
        "mobile": updated_client.get("mobile", "N/A"),
        "email": updated_client.get("email"),
        "full_name": updated_client["full_name"],
        "age": profile.get("age") if profile else None,
        "guardian_name": profile.get("guardian_name") if profile else None,
        "address": profile.get("address") if profile else None,
        "referred_by": profile.get("referred_by") if profile else None,
        "intake_summary": profile.get("intake_summary") if profile else None,
        "emergency_contact_name": profile.get("emergency_contact_name") if profile else None,
        "emergency_contact_phone": profile.get("emergency_contact_phone") if profile else None,
        "profile_photo": profile.get("profile_photo") if profile else None,
        "created_at": updated_client["created_at"]
    }

# ============= SUBSCRIPTION MANAGEMENT ENDPOINTS =============

@api_router.get("/admin/subscription-plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans(current_user: dict = Depends(require_super_admin)):
    plans = await db.subscription_plans.find({}, {"_id": 0}).to_list(1000)
    return [SubscriptionPlan(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in plan.items()}) for plan in plans]

class SubscriptionPlanCreate(BaseModel):
    name: str
    price: float
    duration_days: int
    features: List[str]
    max_clients: Optional[int] = None

@api_router.post("/admin/subscription-plans", response_model=SubscriptionPlan)
async def create_subscription_plan(plan_data: SubscriptionPlanCreate, current_user: dict = Depends(require_super_admin)):
    plan_id = str(uuid.uuid4())
    plan_doc = {
        "id": plan_id,
        "name": plan_data.name,
        "price": plan_data.price,
        "duration_days": plan_data.duration_days,
        "features": plan_data.features,
        "max_clients": plan_data.max_clients,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.subscription_plans.insert_one(plan_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "subscription_plan", plan_id)
    
    return SubscriptionPlan(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in plan_doc.items()})

@api_router.delete("/admin/subscription-plans/{plan_id}")
async def delete_subscription_plan(plan_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.subscription_plans.delete_one({"id": plan_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    await log_audit(current_user["id"], current_user["role"], "delete", "subscription_plan", plan_id)
    
    return {"message": "Plan deleted"}

class AssignSubscription(BaseModel):
    plan_id: str
    coupon_code: Optional[str] = None

@api_router.post("/admin/therapists/{therapist_id}/assign-subscription")
async def assign_subscription(therapist_id: str, subscription_data: AssignSubscription, current_user: dict = Depends(require_super_admin)):
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    plan = await db.subscription_plans.find_one({"id": subscription_data.plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check coupon if provided
    discount = 0
    if subscription_data.coupon_code:
        coupon = await db.coupon_codes.find_one({"code": subscription_data.coupon_code}, {"_id": 0})
        if coupon:
            if datetime.fromisoformat(coupon["valid_until"]) > datetime.now(timezone.utc):
                if coupon.get("max_uses") is None or coupon["used_count"] < coupon["max_uses"]:
                    discount = coupon["discount_percent"]
                    # Increment usage
                    await db.coupon_codes.update_one(
                        {"code": subscription_data.coupon_code},
                        {"$inc": {"used_count": 1}}
                    )
    
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=plan["duration_days"])
    
    # Create subscription
    subscription_id = str(uuid.uuid4())
    subscription_doc = {
        "id": subscription_id,
        "therapist_id": therapist_id,
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "status": "active",
        "start_date": now.isoformat(),
        "end_date": end_date.isoformat(),
        "coupon_code": subscription_data.coupon_code
    }
    
    await db.subscriptions.insert_one(subscription_doc)
    
    # Update therapist subscription status
    await db.users.update_one(
        {"id": therapist_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_plan": plan["name"]
        }}
    )
    
    await log_audit(current_user["id"], current_user["role"], "assign_subscription", "therapist", therapist_id)
    
    return {"message": "Subscription assigned", "subscription_id": subscription_id, "discount_applied": discount}

class ExtendSubscription(BaseModel):
    additional_days: int

@api_router.post("/admin/therapists/{therapist_id}/extend-subscription")
async def extend_subscription(therapist_id: str, extend_data: ExtendSubscription, current_user: dict = Depends(require_super_admin)):
    """Extend a therapist's current subscription by additional days"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Get current subscription
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    if not subscription:
        raise HTTPException(status_code=400, detail="No subscription found. Please assign a subscription first.")
    
    # Extend end date
    current_end = datetime.fromisoformat(subscription["end_date"])
    new_end = current_end + timedelta(days=extend_data.additional_days)
    
    await db.subscriptions.update_one(
        {"id": subscription["id"]},
        {"$set": {"end_date": new_end.isoformat()}}
    )
    
    # Update status to active if it was expired
    await db.users.update_one(
        {"id": therapist_id},
        {"$set": {"subscription_status": "active"}}
    )
    
    await log_audit(current_user["id"], current_user["role"], "extend_subscription", "therapist", therapist_id, {"additional_days": extend_data.additional_days})
    
    return {"message": f"Subscription extended by {extend_data.additional_days} days", "new_end_date": new_end.isoformat()}

@api_router.post("/admin/therapists/{therapist_id}/assign-trial")
async def assign_trial_subscription(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    """Assign a default 30-day trial subscription to a therapist"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=30)
    
    # Create trial subscription
    subscription_id = str(uuid.uuid4())
    subscription_doc = {
        "id": subscription_id,
        "therapist_id": therapist_id,
        "plan_id": "free_trial",
        "plan_name": "Free Trial",
        "status": "trial",
        "start_date": now.isoformat(),
        "end_date": end_date.isoformat(),
        "coupon_code": None
    }
    
    await db.subscriptions.insert_one(subscription_doc)
    
    # Update therapist subscription status
    await db.users.update_one(
        {"id": therapist_id},
        {"$set": {
            "subscription_status": "trial",
            "subscription_plan": "free_trial"
        }}
    )
    
    await log_audit(current_user["id"], current_user["role"], "assign_trial", "therapist", therapist_id)
    
    return {"message": "30-day trial subscription assigned", "subscription_id": subscription_id, "end_date": end_date.isoformat()}

@api_router.get("/admin/therapists/{therapist_id}/subscription")
async def get_therapist_subscription(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    """Get detailed subscription info for a therapist"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    return {
        "therapist_id": therapist_id,
        "therapist_name": therapist["full_name"],
        "subscription_status": therapist.get("subscription_status"),
        "subscription_plan": therapist.get("subscription_plan"),
        "subscription": subscription
    }

@api_router.post("/admin/migrate-subscriptions")
async def migrate_subscriptions(current_user: dict = Depends(require_super_admin)):
    """Assign default trial subscriptions to all therapists without subscriptions"""
    therapists_without_subscription = await db.users.find(
        {"role": "therapist", "$or": [
            {"subscription_status": {"$exists": False}},
            {"subscription_status": None},
            {"subscription_status": ""}
        ]},
        {"_id": 0}
    ).to_list(1000)
    
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=30)
    migrated_count = 0
    
    for therapist in therapists_without_subscription:
        subscription_id = str(uuid.uuid4())
        subscription_doc = {
            "id": subscription_id,
            "therapist_id": therapist["id"],
            "plan_id": "free_trial",
            "plan_name": "Free Trial",
            "status": "trial",
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
            "coupon_code": None
        }
        
        await db.subscriptions.insert_one(subscription_doc)
        
        await db.users.update_one(
            {"id": therapist["id"]},
            {"$set": {
                "subscription_status": "trial",
                "subscription_plan": "free_trial"
            }}
        )
        migrated_count += 1
    
    await log_audit(current_user["id"], current_user["role"], "migrate_subscriptions", "system", None, {"count": migrated_count})
    
    return {"message": f"Migrated {migrated_count} therapists to trial subscription"}

@api_router.get("/admin/coupons", response_model=List[CouponCode])
async def get_coupons(current_user: dict = Depends(require_super_admin)):
    coupons = await db.coupon_codes.find({}, {"_id": 0}).to_list(1000)
    return [CouponCode(**{k: datetime.fromisoformat(v) if k in ["valid_until", "created_at"] else v for k, v in coupon.items()}) for coupon in coupons]

class CouponCreate(BaseModel):
    code: str
    discount_percent: float
    valid_until: datetime
    max_uses: Optional[int] = None

@api_router.post("/admin/coupons", response_model=CouponCode)
async def create_coupon(coupon_data: CouponCreate, current_user: dict = Depends(require_super_admin)):
    # Check if code already exists
    existing = await db.coupon_codes.find_one({"code": coupon_data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    
    coupon_id = str(uuid.uuid4())
    coupon_doc = {
        "id": coupon_id,
        "code": coupon_data.code.upper(),
        "discount_percent": coupon_data.discount_percent,
        "valid_until": coupon_data.valid_until.isoformat(),
        "max_uses": coupon_data.max_uses,
        "used_count": 0,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.coupon_codes.insert_one(coupon_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "coupon", coupon_id)
    
    return CouponCode(**{k: datetime.fromisoformat(v) if k in ["valid_until", "created_at"] else v for k, v in coupon_doc.items()})

@api_router.delete("/admin/coupons/{coupon_id}")
async def delete_coupon(coupon_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.coupon_codes.delete_one({"id": coupon_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    await log_audit(current_user["id"], current_user["role"], "delete", "coupon", coupon_id)
    
    return {"message": "Coupon deleted"}

# ============= CLIENT ENDPOINTS =============

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

@api_router.post("/clients", response_model=ClientProfile)
async def create_client(client_data: ClientCreate, current_user: dict = Depends(require_active_therapist)):
    
    # Validate mobile number
    if not validate_mobile(client_data.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    # Check if mobile already exists
    existing_mobile = await db.users.find_one({"mobile": client_data.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    # Check if email exists (if provided)
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
    
    # Create client profile
    profile_doc = {
        "user_id": client_id,
        "therapist_id": current_user["id"],
        "age": client_data.age,
        "guardian_name": client_data.guardian_name,
        "address": client_data.address,
        "referred_by": client_data.referred_by,
        "intake_summary": client_data.intake_summary,
        "emergency_contact_name": client_data.emergency_contact_name,
        "emergency_contact_phone": client_data.emergency_contact_phone,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.client_profiles.insert_one(profile_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "client", client_id)
    
    return ClientProfile(
        id=client_id,
        client_id=unique_client_id,
        therapist_id=current_user["id"],
        mobile=client_data.mobile,
        email=client_data.email,
        full_name=client_data.full_name,
        age=client_data.age,
        guardian_name=client_data.guardian_name,
        address=client_data.address,
        referred_by=client_data.referred_by,
        intake_summary=client_data.intake_summary,
        emergency_contact_name=client_data.emergency_contact_name,
        emergency_contact_phone=client_data.emergency_contact_phone,
        created_at=datetime.fromisoformat(user_doc["created_at"])
    )

@api_router.get("/clients", response_model=List[ClientProfile])
async def get_clients(current_user: dict = Depends(require_therapist)):
    """Get only clients assigned to the current therapist"""
    therapist_id = current_user["id"]
    
    # Get client profiles assigned to this therapist
    client_profiles = await db.client_profiles.find(
        {"therapist_id": therapist_id},
        {"_id": 0}
    ).to_list(1000)
    
    result = []
    for profile in client_profiles:
        client = await db.users.find_one(
            {"id": profile["user_id"], "role": "client"},
            {"_id": 0, "password_hash": 0}
        )
        if client:
            result.append(ClientProfile(
                id=client["id"],
                client_id=client.get("client_id", ""),
                therapist_id=profile.get("therapist_id", ""),
                mobile=client.get("mobile", "N/A"),
                email=client.get("email"),
                full_name=client["full_name"],
                age=profile.get("age"),
                guardian_name=profile.get("guardian_name"),
                address=profile.get("address"),
                referred_by=profile.get("referred_by"),
                intake_summary=profile.get("intake_summary"),
                emergency_contact_name=profile.get("emergency_contact_name"),
                emergency_contact_phone=profile.get("emergency_contact_phone"),
                profile_photo=profile.get("profile_photo"),
                created_at=datetime.fromisoformat(client["created_at"])
            ))
    
    return result

@api_router.get("/clients/{client_id}", response_model=ClientProfile)
async def get_client(client_id: str, current_user: dict = Depends(require_therapist)):
    """Get a specific client - must be assigned to current therapist"""
    therapist_id = current_user["id"]
    
    # Verify client is assigned to this therapist
    profile = await db.client_profiles.find_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found or not assigned to you")
    
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return ClientProfile(
        id=client["id"],
        client_id=client.get("client_id", ""),
        therapist_id=profile.get("therapist_id", ""),
        mobile=client.get("mobile", "N/A"),
        email=client.get("email"),
        full_name=client["full_name"],
        age=profile.get("age"),
        guardian_name=profile.get("guardian_name"),
        address=profile.get("address"),
        referred_by=profile.get("referred_by"),
        intake_summary=profile.get("intake_summary"),
        emergency_contact_name=profile.get("emergency_contact_name"),
        emergency_contact_phone=profile.get("emergency_contact_phone"),
        profile_photo=profile.get("profile_photo"),
        created_at=datetime.fromisoformat(client["created_at"])
    )

@api_router.put("/clients/{client_id}", response_model=ClientProfile)
async def update_client(client_id: str, update_data: ClientProfileUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update client - must be assigned to current therapist"""
    therapist_id = current_user["id"]
    
    # Verify client is assigned to this therapist
    profile = await db.client_profiles.find_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found or not assigned to you")
    
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Separate user fields from profile fields
    user_fields = {}
    profile_fields = {}
    
    # User fields (stored in users collection)
    if "full_name" in update_dict:
        user_fields["full_name"] = update_dict.pop("full_name")
    if "mobile" in update_dict:
        new_mobile = update_dict.pop("mobile")
        # Validate mobile format
        if not validate_mobile(new_mobile):
            raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
        # Check if mobile already exists (excluding current client)
        existing = await db.users.find_one({"mobile": new_mobile, "id": {"$ne": client_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Mobile number already in use by another account")
        user_fields["mobile"] = new_mobile
    if "email" in update_dict:
        new_email = update_dict.pop("email")
        if new_email:
            # Check if email already exists (excluding current client)
            existing = await db.users.find_one({"email": new_email, "id": {"$ne": client_id}})
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use by another account")
        user_fields["email"] = new_email
    
    # Profile fields (stored in client_profiles collection)
    profile_fields = update_dict
    profile_fields["therapist_id"] = current_user["id"]
    profile_fields["user_id"] = client_id
    profile_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Update user document if there are user field changes
    if user_fields:
        await db.users.update_one({"id": client_id}, {"$set": user_fields})
    
    # Update profile document
    await db.client_profiles.update_one(
        {"user_id": client_id},
        {"$set": profile_fields},
        upsert=True
    )
    
    await log_audit(current_user["id"], current_user["role"], "update", "client_profile", client_id, {**user_fields, **profile_fields})
    
    return await get_client(client_id, current_user)

@api_router.post("/clients/{client_id}/reset-password")
async def reset_client_password_by_therapist(client_id: str, password_data: ClientPasswordReset, current_user: dict = Depends(require_active_therapist)):
    """Reset client password (by their assigned therapist)"""
    therapist_id = current_user["id"]
    
    # Verify client is assigned to this therapist
    profile = await db.client_profiles.find_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=403, detail="You can only reset passwords for your own clients")
    
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    await db.users.update_one(
        {"id": client_id},
        {"$set": {"password_hash": hash_password(password_data.new_password)}}
    )
    
    await log_audit(current_user["id"], current_user["role"], "reset_password", "client", client_id)
    
    return {"message": "Password reset successfully"}

@api_router.post("/clients/{client_id}/photo")
async def update_client_photo(client_id: str, photo_url: str, current_user: dict = Depends(require_active_therapist)):
    """Update client profile photo URL - must be assigned to current therapist"""
    therapist_id = current_user["id"]
    
    # Verify client is assigned to this therapist
    profile = await db.client_profiles.find_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=403, detail="You can only update photos for your own clients")
    
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    await db.client_profiles.update_one(
        {"user_id": client_id},
        {"$set": {"profile_photo": photo_url, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    await log_audit(current_user["id"], current_user["role"], "update_photo", "client", client_id)
    
    return {"message": "Photo updated successfully"}

# ============= APPOINTMENT ENDPOINTS =============

@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appt_data: AppointmentCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a new appointment - respects subscription read-only mode"""
    # Validate times
    if appt_data.start_time >= appt_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    # Check for double-booking (exclude cancelled appointments)
    existing = await db.appointments.find_one({
        "therapist_id": current_user["id"],
        "status": {"$ne": "cancelled"},
        "$or": [
            {"start_time": {"$lt": appt_data.end_time.isoformat()}, "end_time": {"$gt": appt_data.start_time.isoformat()}}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Time slot already booked. Please choose a different time.")
    
    # Find client - check both clients collection and users collection
    client = await db.clients.find_one({"id": appt_data.client_id}, {"_id": 0})
    if not client:
        client = await db.users.find_one({"id": appt_data.client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify client belongs to this therapist
    if client.get("therapist_id") and client["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Client is not assigned to you")
    
    appt_id = str(uuid.uuid4())
    appt_doc = {
        "id": appt_id,
        "therapist_id": current_user["id"],
        "client_id": appt_data.client_id,
        "client_name": client["full_name"],
        "start_time": appt_data.start_time.isoformat(),
        "end_time": appt_data.end_time.isoformat(),
        "notes": appt_data.notes,
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.appointments.insert_one(appt_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "appointment", appt_id)
    
    return Appointment(**{k: datetime.fromisoformat(v) if k in ["start_time", "end_time", "created_at"] else v for k, v in appt_doc.items()})

@api_router.get("/appointments", response_model=List[Appointment])
async def get_appointments(current_user: dict = Depends(get_current_user)):
    """Get appointments - therapists see their appointments, clients see theirs"""
    query = {}
    if current_user["role"] == "therapist":
        query["therapist_id"] = current_user["id"]
    else:
        query["client_id"] = current_user["id"]
    
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(1000)
    
    return [Appointment(**{k: datetime.fromisoformat(v) if k in ["start_time", "end_time", "created_at"] else v for k, v in appt.items()}) for appt in appointments]

@api_router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single appointment by ID"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify ownership
    if current_user["role"] == "therapist" and appointment["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user["role"] == "client" and appointment["client_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return Appointment(**{k: datetime.fromisoformat(v) if k in ["start_time", "end_time", "created_at"] else v for k, v in appointment.items()})

@api_router.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, update_data: AppointmentUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update an appointment - respects subscription read-only mode"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify ownership
    if appointment["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build update fields
    update_fields = {}
    
    if update_data.start_time is not None:
        update_fields["start_time"] = update_data.start_time.isoformat()
    if update_data.end_time is not None:
        update_fields["end_time"] = update_data.end_time.isoformat()
    if update_data.notes is not None:
        update_fields["notes"] = update_data.notes
    if update_data.status is not None:
        update_fields["status"] = update_data.status
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Validate times if being updated
    new_start = update_fields.get("start_time", appointment["start_time"])
    new_end = update_fields.get("end_time", appointment["end_time"])
    if new_start >= new_end:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    # Check for double-booking if times are being changed (exclude current appointment and cancelled ones)
    if "start_time" in update_fields or "end_time" in update_fields:
        existing = await db.appointments.find_one({
            "therapist_id": current_user["id"],
            "id": {"$ne": appointment_id},
            "status": {"$ne": "cancelled"},
            "$or": [
                {"start_time": {"$lt": new_end}, "end_time": {"$gt": new_start}}
            ]
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Time slot already booked. Please choose a different time.")
    
    await db.appointments.update_one({"id": appointment_id}, {"$set": update_fields})
    await log_audit(current_user["id"], current_user["role"], "update", "appointment", appointment_id)
    
    # Get updated appointment
    updated = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    return Appointment(**{k: datetime.fromisoformat(v) if k in ["start_time", "end_time", "created_at"] else v for k, v in updated.items()})

@api_router.post("/appointments/{appointment_id}/complete")
async def complete_appointment(appointment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Mark an appointment as completed - respects subscription read-only mode"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if appointment["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot complete a cancelled appointment")
    
    await db.appointments.update_one({"id": appointment_id}, {"$set": {"status": "completed"}})
    await log_audit(current_user["id"], current_user["role"], "complete", "appointment", appointment_id)
    
    return {"message": "Appointment marked as completed"}

@api_router.post("/appointments/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Cancel an appointment - respects subscription read-only mode"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if appointment["status"] == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed appointment")
    
    await db.appointments.update_one({"id": appointment_id}, {"$set": {"status": "cancelled"}})
    await log_audit(current_user["id"], current_user["role"], "cancel", "appointment", appointment_id)
    
    return {"message": "Appointment cancelled"}

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete an appointment - respects subscription read-only mode"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.appointments.delete_one({"id": appointment_id})
    await log_audit(current_user["id"], current_user["role"], "delete", "appointment", appointment_id)
    
    return {"message": "Appointment deleted"}

# ============= THERAPIST AVAILABILITY ENDPOINTS =============

@api_router.get("/availability", response_model=TherapistAvailability)
async def get_availability(current_user: dict = Depends(get_current_user)):
    """Get therapist's availability settings"""
    therapist_id = current_user["id"] if current_user["role"] == "therapist" else None
    if not therapist_id:
        raise HTTPException(status_code=403, detail="Only therapists can access availability settings")
    
    availability = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    
    if not availability:
        # Create default availability
        default_availability = {
            "id": str(uuid.uuid4()),
            "therapist_id": therapist_id,
            "session_duration": 60,
            "buffer_time": 0,
            "monday": {"enabled": False, "time_blocks": []},
            "tuesday": {"enabled": False, "time_blocks": []},
            "wednesday": {"enabled": False, "time_blocks": []},
            "thursday": {"enabled": False, "time_blocks": []},
            "friday": {"enabled": False, "time_blocks": []},
            "saturday": {"enabled": False, "time_blocks": []},
            "sunday": {"enabled": False, "time_blocks": []},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.therapist_availability.insert_one(default_availability)
        availability = default_availability
    
    return TherapistAvailability(**{k: datetime.fromisoformat(v) if k == "updated_at" else v for k, v in availability.items()})

@api_router.put("/availability", response_model=TherapistAvailability)
async def update_availability(update_data: TherapistAvailabilityUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update therapist's availability settings"""
    therapist_id = current_user["id"]
    
    # Get existing or create new
    availability = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    
    if not availability:
        availability = {
            "id": str(uuid.uuid4()),
            "therapist_id": therapist_id,
            "session_duration": 60,
            "buffer_time": 0,
            "monday": {"enabled": False, "time_blocks": []},
            "tuesday": {"enabled": False, "time_blocks": []},
            "wednesday": {"enabled": False, "time_blocks": []},
            "thursday": {"enabled": False, "time_blocks": []},
            "friday": {"enabled": False, "time_blocks": []},
            "saturday": {"enabled": False, "time_blocks": []},
            "sunday": {"enabled": False, "time_blocks": []},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.therapist_availability.insert_one(availability)
    
    # Build update fields
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if update_data.session_duration is not None:
        if update_data.session_duration < 15 or update_data.session_duration > 240:
            raise HTTPException(status_code=400, detail="Session duration must be between 15 and 240 minutes")
        update_fields["session_duration"] = update_data.session_duration
    
    if update_data.buffer_time is not None:
        if update_data.buffer_time < 0 or update_data.buffer_time > 60:
            raise HTTPException(status_code=400, detail="Buffer time must be between 0 and 60 minutes")
        update_fields["buffer_time"] = update_data.buffer_time
    
    # Update each day's availability
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        day_data = getattr(update_data, day, None)
        if day_data is not None:
            update_fields[day] = day_data.model_dump()
    
    await db.therapist_availability.update_one(
        {"therapist_id": therapist_id},
        {"$set": update_fields}
    )
    
    # Get updated availability
    updated = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    await log_audit(current_user["id"], current_user["role"], "update", "availability", therapist_id)
    
    return TherapistAvailability(**{k: datetime.fromisoformat(v) if k == "updated_at" else v for k, v in updated.items()})

# ============= BLOCKED TIME ENDPOINTS =============

@api_router.post("/blocked-times", response_model=BlockedTime)
async def create_blocked_time(block_data: BlockedTimeCreate, current_user: dict = Depends(require_active_therapist)):
    """Block a time range (e.g., vacation, personal time)"""
    if block_data.start_datetime >= block_data.end_datetime:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    block_id = str(uuid.uuid4())
    block_doc = {
        "id": block_id,
        "therapist_id": current_user["id"],
        "start_datetime": block_data.start_datetime.isoformat(),
        "end_datetime": block_data.end_datetime.isoformat(),
        "reason": block_data.reason,
        "is_all_day": block_data.is_all_day,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.blocked_times.insert_one(block_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "blocked_time", block_id)
    
    return BlockedTime(**{k: datetime.fromisoformat(v) if k in ["start_datetime", "end_datetime", "created_at"] else v for k, v in block_doc.items()})

@api_router.get("/blocked-times", response_model=List[BlockedTime])
async def get_blocked_times(current_user: dict = Depends(get_current_user)):
    """Get all blocked times for the therapist"""
    therapist_id = current_user["id"] if current_user["role"] == "therapist" else None
    if not therapist_id:
        raise HTTPException(status_code=403, detail="Only therapists can access blocked times")
    
    blocked = await db.blocked_times.find({"therapist_id": therapist_id}, {"_id": 0}).to_list(1000)
    
    return [BlockedTime(**{k: datetime.fromisoformat(v) if k in ["start_datetime", "end_datetime", "created_at"] else v for k, v in b.items()}) for b in blocked]

@api_router.delete("/blocked-times/{block_id}")
async def delete_blocked_time(block_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a blocked time"""
    block = await db.blocked_times.find_one({"id": block_id}, {"_id": 0})
    if not block:
        raise HTTPException(status_code=404, detail="Blocked time not found")
    
    if block["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.blocked_times.delete_one({"id": block_id})
    await log_audit(current_user["id"], current_user["role"], "delete", "blocked_time", block_id)
    
    return {"message": "Blocked time deleted"}

# ============= AVAILABLE SLOTS ENDPOINT =============

@api_router.get("/available-slots/{therapist_id}", response_model=List[AvailableSlot])
async def get_available_slots(therapist_id: str, date: str, current_user: dict = Depends(get_current_user)):
    """Get available appointment slots for a specific date.
    This is the public-facing endpoint for clients to see available times.
    """
    # Parse the date
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Don't allow booking in the past
    if target_date < datetime.now(timezone.utc).date():
        return []
    
    # Get therapist's availability settings
    availability = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    if not availability:
        return []  # Therapist has not set up availability
    
    # Get the day of week
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_name = day_names[target_date.weekday()]
    
    day_availability = availability.get(day_name, {})
    if not day_availability.get("enabled", False):
        return []  # Therapist not available on this day
    
    time_blocks = day_availability.get("time_blocks", [])
    if not time_blocks:
        return []
    
    session_duration = availability.get("session_duration", 60)
    buffer_time = availability.get("buffer_time", 0)
    
    # Get existing appointments for this date
    start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    existing_appointments = await db.appointments.find({
        "therapist_id": therapist_id,
        "status": {"$ne": "cancelled"},
        "start_time": {"$gte": start_of_day.isoformat(), "$lt": end_of_day.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    # Get blocked times for this date
    blocked_times = await db.blocked_times.find({
        "therapist_id": therapist_id,
        "$or": [
            {"start_datetime": {"$gte": start_of_day.isoformat(), "$lt": end_of_day.isoformat()}},
            {"end_datetime": {"$gt": start_of_day.isoformat(), "$lte": end_of_day.isoformat()}},
            {"start_datetime": {"$lte": start_of_day.isoformat()}, "end_datetime": {"$gte": end_of_day.isoformat()}}
        ]
    }, {"_id": 0}).to_list(100)
    
    # Generate slots
    available_slots = []
    
    for block in time_blocks:
        block_start = datetime.strptime(block["start_time"], "%H:%M").time()
        block_end = datetime.strptime(block["end_time"], "%H:%M").time()
        
        current_start = datetime.combine(target_date, block_start).replace(tzinfo=timezone.utc)
        block_end_dt = datetime.combine(target_date, block_end).replace(tzinfo=timezone.utc)
        
        while current_start + timedelta(minutes=session_duration) <= block_end_dt:
            slot_end = current_start + timedelta(minutes=session_duration)
            
            # Check if this slot overlaps with any existing appointment
            is_booked = False
            for appt in existing_appointments:
                appt_start_str = appt["start_time"]
                appt_end_str = appt["end_time"]
                # Handle both 'Z' suffix and no timezone
                if appt_start_str.endswith('Z'):
                    appt_start = datetime.fromisoformat(appt_start_str.replace('Z', '+00:00'))
                else:
                    appt_start = datetime.fromisoformat(appt_start_str).replace(tzinfo=timezone.utc)
                if appt_end_str.endswith('Z'):
                    appt_end = datetime.fromisoformat(appt_end_str.replace('Z', '+00:00'))
                else:
                    appt_end = datetime.fromisoformat(appt_end_str).replace(tzinfo=timezone.utc)
                
                if current_start < appt_end and slot_end > appt_start:
                    is_booked = True
                    break
            
            # Check if this slot is blocked
            is_blocked = False
            for bt in blocked_times:
                bt_start_str = bt["start_datetime"]
                bt_end_str = bt["end_datetime"]
                # Handle both 'Z' suffix and no timezone
                if bt_start_str.endswith('Z'):
                    bt_start = datetime.fromisoformat(bt_start_str.replace('Z', '+00:00'))
                else:
                    bt_start = datetime.fromisoformat(bt_start_str).replace(tzinfo=timezone.utc)
                if bt_end_str.endswith('Z'):
                    bt_end = datetime.fromisoformat(bt_end_str.replace('Z', '+00:00'))
                else:
                    bt_end = datetime.fromisoformat(bt_end_str).replace(tzinfo=timezone.utc)
                
                if current_start < bt_end and slot_end > bt_start:
                    is_blocked = True
                    break
            
            # Don't show slots that have already passed today
            now = datetime.now(timezone.utc)
            is_past = current_start <= now
            
            if not is_booked and not is_blocked and not is_past:
                available_slots.append(AvailableSlot(
                    start_time=current_start,
                    end_time=slot_end,
                    duration_minutes=session_duration
                ))
            
            # Move to next slot (session + buffer)
            current_start = slot_end + timedelta(minutes=buffer_time)
    
    return available_slots

@api_router.get("/therapist/{therapist_id}/availability")
async def get_therapist_availability_public(therapist_id: str, current_user: dict = Depends(get_current_user)):
    """Get therapist's public availability settings (for clients to see)"""
    availability = await db.therapist_availability.find_one({"therapist_id": therapist_id}, {"_id": 0})
    
    if not availability:
        return {
            "session_duration": 60,
            "available_days": []
        }
    
    available_days = []
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    for day in day_names:
        day_data = availability.get(day, {})
        if day_data.get("enabled", False) and day_data.get("time_blocks"):
            available_days.append(day)
    
    return {
        "session_duration": availability.get("session_duration", 60),
        "available_days": available_days
    }

# ============= SESSION NOTES ENDPOINTS =============

@api_router.post("/session-notes", response_model=SessionNote)
async def create_session_note(note_data: SessionNoteCreate, current_user: dict = Depends(require_active_therapist)):
    
    client = await db.users.find_one({"id": note_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    note_doc = {
        "id": note_id,
        "therapist_id": current_user["id"],
        "client_id": note_data.client_id,
        "client_name": client["full_name"],
        "template_type": note_data.template_type,
        "subjective": note_data.subjective,
        "objective": note_data.objective,
        "assessment": note_data.assessment,
        "plan": note_data.plan,
        "data": note_data.data,
        "created_at": now,
        "updated_at": now
    }
    
    await db.session_notes.insert_one(note_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "session_note", note_id)
    
    return SessionNote(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in note_doc.items()})

@api_router.get("/session-notes", response_model=List[SessionNote])
async def get_session_notes(client_id: Optional[str] = None, current_user: dict = Depends(require_therapist)):
    
    query = {"therapist_id": current_user["id"]}
    if client_id:
        query["client_id"] = client_id
    
    notes = await db.session_notes.find(query, {"_id": 0}).to_list(1000)
    return [SessionNote(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in note.items()}) for note in notes]

# ============= MESSAGING ENDPOINTS =============

@api_router.post("/messages", response_model=Message)
async def send_message(msg_data: MessageCreate, current_user: dict = Depends(get_current_user)):
    # Therapists need active subscription to send messages
    if current_user["role"] == "therapist" and not is_subscription_active(current_user):
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. You are in read-only mode. Please renew to send messages."
        )
    
    recipient = await db.users.find_one({"id": msg_data.recipient_id}, {"_id": 0})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    msg_id = str(uuid.uuid4())
    msg_doc = {
        "id": msg_id,
        "sender_id": current_user["id"],
        "sender_name": current_user["full_name"],
        "recipient_id": msg_data.recipient_id,
        "recipient_name": recipient["full_name"],
        "content": msg_data.content,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(msg_doc)
    await log_audit(current_user["id"], current_user["role"], "send", "message", msg_id)
    
    return Message(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in msg_doc.items()})

@api_router.get("/messages/{other_user_id}", response_model=List[Message])
async def get_messages(other_user_id: str, current_user: dict = Depends(get_current_user)):
    messages = await db.messages.find({
        "$or": [
            {"sender_id": current_user["id"], "recipient_id": other_user_id},
            {"sender_id": other_user_id, "recipient_id": current_user["id"]}
        ]
    }, {"_id": 0}).sort("created_at", 1).to_list(1000)
    
    # Mark as read
    await db.messages.update_many(
        {"sender_id": other_user_id, "recipient_id": current_user["id"], "read": False},
        {"$set": {"read": True}}
    )
    
    return [Message(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in msg.items()}) for msg in messages]

@api_router.get("/messages", response_model=List[dict])
async def get_conversations(current_user: dict = Depends(get_current_user)):
    messages = await db.messages.find({
        "$or": [
            {"sender_id": current_user["id"]},
            {"recipient_id": current_user["id"]}
        ]
    }, {"_id": 0}).to_list(10000)
    
    conversations = {}
    for msg in messages:
        other_id = msg["recipient_id"] if msg["sender_id"] == current_user["id"] else msg["sender_id"]
        other_name = msg["recipient_name"] if msg["sender_id"] == current_user["id"] else msg["sender_name"]
        
        if other_id not in conversations:
            conversations[other_id] = {
                "user_id": other_id,
                "user_name": other_name,
                "last_message": msg["content"],
                "last_message_time": msg["created_at"],
                "unread_count": 0
            }
        else:
            if msg["created_at"] > conversations[other_id]["last_message_time"]:
                conversations[other_id]["last_message"] = msg["content"]
                conversations[other_id]["last_message_time"] = msg["created_at"]
        
        if msg["recipient_id"] == current_user["id"] and not msg["read"]:
            conversations[other_id]["unread_count"] += 1
    
    return list(conversations.values())

# ============= ASSESSMENT ENDPOINTS =============

ASSESSMENT_LIBRARY = {
    "PHQ-9": {
        "name": "Patient Health Questionnaire-9",
        "description": "Depression screening",
        "questions": [
            {"q": "Little interest or pleasure in doing things", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"q": "Feeling down, depressed, or hopeless", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"q": "Trouble falling or staying asleep, or sleeping too much", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"q": "Feeling tired or having little energy", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"q": "Poor appetite or overeating", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]}
        ]
    },
    "GAD-7": {
        "name": "Generalized Anxiety Disorder-7",
        "description": "Anxiety screening",
        "questions": [
            {"q": "Feeling nervous, anxious, or on edge", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"q": "Not being able to stop or control worrying", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"q": "Worrying too much about different things", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
            {"q": "Trouble relaxing", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]}
        ]
    },
    "PCL-5": {
        "name": "PTSD Checklist for DSM-5",
        "description": "PTSD screening",
        "questions": [
            {"q": "Repeated, disturbing memories, thoughts, or images of a stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"q": "Repeated, disturbing dreams of a stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"q": "Suddenly feeling or acting as if a stressful experience were actually happening again", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]}
        ]
    },
    "ASRS": {
        "name": "Adult ADHD Self-Report Scale",
        "description": "ADHD screening",
        "questions": [
            {"q": "How often do you have trouble wrapping up the final details of a project?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very often"]},
            {"q": "How often do you have difficulty getting things in order when you have to do a task that requires organization?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very often"]},
            {"q": "How often do you have problems remembering appointments or obligations?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very often"]}
        ]
    },
    "BDI-II": {
        "name": "Beck Depression Inventory-II",
        "description": "Depression severity assessment",
        "questions": [
            {"q": "Sadness", "options": ["I do not feel sad", "I feel sad much of the time", "I am sad all the time", "I am so sad or unhappy that I can't stand it"]},
            {"q": "Pessimism", "options": ["I am not discouraged about my future", "I feel more discouraged about my future than I used to", "I do not expect things to work out for me", "I feel my future is hopeless"]},
            {"q": "Past Failure", "options": ["I do not feel like a failure", "I have failed more than I should have", "As I look back, I see a lot of failures", "I feel I am a total failure as a person"]},
            {"q": "Loss of Pleasure", "options": ["I get as much pleasure as I ever did", "I don't enjoy things as much as I used to", "I get very little pleasure from things", "I can't get any pleasure from things"]}
        ]
    },
    "DASS-21": {
        "name": "Depression Anxiety Stress Scales-21",
        "description": "Measure depression, anxiety, and stress",
        "questions": [
            {"q": "I found it hard to wind down", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me a considerable degree", "Applied to me very much"]},
            {"q": "I was aware of dryness of my mouth", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me a considerable degree", "Applied to me very much"]},
            {"q": "I couldn't seem to experience any positive feeling at all", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me a considerable degree", "Applied to me very much"]},
            {"q": "I felt that I had nothing to look forward to", "options": ["Did not apply to me at all", "Applied to me to some degree", "Applied to me a considerable degree", "Applied to me very much"]}
        ]
    },
    "YBOCS": {
        "name": "Yale-Brown Obsessive Compulsive Scale",
        "description": "OCD symptom severity",
        "questions": [
            {"q": "Time occupied by obsessive thoughts - How much of your time is occupied by obsessive thoughts?", "options": ["None", "Less than 1 hour/day", "1-3 hours/day", "3-8 hours/day", "More than 8 hours/day"]},
            {"q": "Interference from obsessive thoughts - How much do your obsessive thoughts interfere with functioning?", "options": ["None", "Mild interference", "Moderate interference", "Severe interference", "Extreme interference"]},
            {"q": "Distress of obsessive thoughts - How much distress do your obsessive thoughts cause?", "options": ["None", "Mild distress", "Moderate distress", "Severe distress", "Extreme distress"]}
        ]
    },
    "PSS": {
        "name": "Perceived Stress Scale",
        "description": "Measure perception of stress",
        "questions": [
            {"q": "In the last month, how often have you been upset because of something that happened unexpectedly?", "options": ["Never", "Almost never", "Sometimes", "Fairly often", "Very often"]},
            {"q": "In the last month, how often have you felt that you were unable to control important things in your life?", "options": ["Never", "Almost never", "Sometimes", "Fairly often", "Very often"]},
            {"q": "In the last month, how often have you felt nervous and stressed?", "options": ["Never", "Almost never", "Sometimes", "Fairly often", "Very often"]},
            {"q": "In the last month, how often have you felt confident about your ability to handle personal problems?", "options": ["Never", "Almost never", "Sometimes", "Fairly often", "Very often"]}
        ]
    }
}

@api_router.get("/assessments/library")
async def get_assessment_library(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access this")
    return ASSESSMENT_LIBRARY

@api_router.post("/assessments/custom", response_model=CustomAssessment)
async def create_custom_assessment(assessment_data: CustomAssessmentCreate, current_user: dict = Depends(require_active_therapist)):
    
    assessment_id = str(uuid.uuid4())
    assessment_doc = {
        "id": assessment_id,
        "therapist_id": current_user["id"],
        "name": assessment_data.name,
        "description": assessment_data.description,
        "questions": assessment_data.questions,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_assessments.insert_one(assessment_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "custom_assessment", assessment_id)
    
    return CustomAssessment(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in assessment_doc.items()})

@api_router.get("/assessments/custom", response_model=List[CustomAssessment])
async def get_custom_assessments(current_user: dict = Depends(require_therapist)):
    
    assessments = await db.custom_assessments.find({"therapist_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return [CustomAssessment(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in assess.items()}) for assess in assessments]

@api_router.post("/assessments", response_model=Assessment)
async def assign_assessment(assessment_data: AssessmentCreate, current_user: dict = Depends(require_active_therapist)):
    
    client = await db.users.find_one({"id": assessment_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    assessment_id = str(uuid.uuid4())
    assessment_doc = {
        "id": assessment_id,
        "therapist_id": current_user["id"],
        "client_id": assessment_data.client_id,
        "client_name": client["full_name"],
        "assessment_type": assessment_data.assessment_type,
        "questions": assessment_data.questions,
        "is_custom": assessment_data.is_custom,
        "custom_assessment_id": assessment_data.custom_assessment_id,
        "answers": None,
        "score": None,
        "status": "assigned",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    
    await db.assessments.insert_one(assessment_doc)
    await log_audit(current_user["id"], current_user["role"], "assign", "assessment", assessment_id)
    
    result = {k: datetime.fromisoformat(v) if k == "created_at" and v else v for k, v in assessment_doc.items()}
    return Assessment(**result)

@api_router.get("/assessments", response_model=List[Assessment])
async def get_assessments(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "therapist":
        query["therapist_id"] = current_user["id"]
    else:
        query["client_id"] = current_user["id"]
    
    assessments = await db.assessments.find(query, {"_id": 0}).to_list(1000)
    result = []
    for assess in assessments:
        assess_dict = {k: datetime.fromisoformat(v) if k in ["created_at", "completed_at"] and v else v for k, v in assess.items()}
        result.append(Assessment(**assess_dict))
    return result

@api_router.post("/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id: str, submission: AssessmentSubmit, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can submit assessments")
    
    assessment = await db.assessments.find_one({"id": assessment_id, "client_id": current_user["id"]}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    score = sum([ans.get("score", 0) for ans in submission.answers])
    
    await db.assessments.update_one(
        {"id": assessment_id},
        {"$set": {
            "answers": submission.answers,
            "score": score,
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_audit(current_user["id"], current_user["role"], "submit", "assessment", assessment_id)
    
    return {"success": True, "score": score}

# ============= PROTOCOL ENDPOINTS =============

PROTOCOL_TEMPLATES = {
    "CBT-Anxiety": {
        "modality": "CBT",
        "condition": "Anxiety",
        "sessions": [
            {"number": 1, "focus": "Introduction & psychoeducation", "activities": ["Introduce CBT model", "Anxiety education", "Set goals"]},
            {"number": 2, "focus": "Identifying automatic thoughts", "activities": ["Thought records", "Cognitive distortions", "Homework assignment"]},
            {"number": 3, "focus": "Cognitive restructuring", "activities": ["Challenge negative thoughts", "Evidence gathering", "Balanced thinking"]},
            {"number": 4, "focus": "Behavioral activation", "activities": ["Activity scheduling", "Graded exposure", "Relaxation techniques"]}
        ]
    },
    "DBT-Emotion Regulation": {
        "modality": "DBT",
        "condition": "Emotion Dysregulation",
        "sessions": [
            {"number": 1, "focus": "Understanding emotions", "activities": ["Emotion identification", "Functions of emotions", "Mindfulness practice"]},
            {"number": 2, "focus": "PLEASE skills", "activities": ["Physical health", "Sleep hygiene", "Exercise planning"]},
            {"number": 3, "focus": "Opposite action", "activities": ["Identify action urges", "Practice opposite action", "Check effectiveness"]}
        ]
    },
    "ACT-Depression": {
        "modality": "ACT",
        "condition": "Depression",
        "sessions": [
            {"number": 1, "focus": "Creative hopelessness", "activities": ["Explore control strategies", "Workability assessment", "Introduce acceptance"]},
            {"number": 2, "focus": "Values clarification", "activities": ["Identify core values", "Values compass", "Committed action planning"]},
            {"number": 3, "focus": "Defusion techniques", "activities": ["Notice thoughts as thoughts", "Defusion exercises", "Observer self"]}
        ]
    }
}

@api_router.get("/protocols/templates")
async def get_protocol_templates(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access this")
    return PROTOCOL_TEMPLATES

@api_router.post("/protocols", response_model=Protocol)
async def create_protocol(protocol_data: ProtocolCreate, current_user: dict = Depends(require_active_therapist)):
    
    client = await db.users.find_one({"id": protocol_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    protocol_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    protocol_doc = {
        "id": protocol_id,
        "therapist_id": current_user["id"],
        "client_id": protocol_data.client_id,
        "client_name": client["full_name"],
        "modality": protocol_data.modality,
        "condition": protocol_data.condition,
        "sessions": protocol_data.sessions,
        "is_template": False,
        "created_at": now,
        "updated_at": now
    }
    
    await db.protocols.insert_one(protocol_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "protocol", protocol_id)
    
    return Protocol(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in protocol_doc.items()})

@api_router.get("/protocols", response_model=List[Protocol])
async def get_protocols(current_user: dict = Depends(require_therapist)):
    
    protocols = await db.protocols.find({"therapist_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return [Protocol(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in proto.items()}) for proto in protocols]

# ============= HOMEWORK ENDPOINTS =============

@api_router.post("/homework", response_model=Homework)
async def assign_homework(hw_data: HomeworkCreate, current_user: dict = Depends(require_active_therapist)):
    
    client = await db.users.find_one({"id": hw_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    hw_id = str(uuid.uuid4())
    hw_doc = {
        "id": hw_id,
        "therapist_id": current_user["id"],
        "client_id": hw_data.client_id,
        "client_name": client["full_name"],
        "title": hw_data.title,
        "description": hw_data.description,
        "due_date": hw_data.due_date.isoformat() if hw_data.due_date else None,
        "status": "assigned",
        "client_notes": None,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.homework.insert_one(hw_doc)
    await log_audit(current_user["id"], current_user["role"], "assign", "homework", hw_id)
    
    result = {}
    for k, v in hw_doc.items():
        if k in ["due_date", "completed_at"] and v:
            result[k] = datetime.fromisoformat(v)
        elif k == "created_at":
            result[k] = datetime.fromisoformat(v)
        else:
            result[k] = v
    return Homework(**result)

@api_router.get("/homework", response_model=List[Homework])
async def get_homework(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "therapist":
        query["therapist_id"] = current_user["id"]
    else:
        query["client_id"] = current_user["id"]
    
    homework = await db.homework.find(query, {"_id": 0}).to_list(1000)
    result = []
    for hw in homework:
        hw_dict = {}
        for k, v in hw.items():
            if k in ["due_date", "completed_at"] and v:
                hw_dict[k] = datetime.fromisoformat(v)
            elif k == "created_at":
                hw_dict[k] = datetime.fromisoformat(v)
            else:
                hw_dict[k] = v
        result.append(Homework(**hw_dict))
    return result

@api_router.post("/homework/{homework_id}/complete")
async def complete_homework(homework_id: str, completion: HomeworkComplete, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can complete homework")
    
    hw = await db.homework.find_one({"id": homework_id, "client_id": current_user["id"]}, {"_id": 0})
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    await db.homework.update_one(
        {"id": homework_id},
        {"$set": {
            "client_notes": completion.client_notes,
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_audit(current_user["id"], current_user["role"], "complete", "homework", homework_id)
    
    return {"success": True}

# ============= PAYMENT ENDPOINTS =============

@api_router.post("/payments", response_model=Payment)
async def record_payment(payment_data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can record payments")
    
    client = await db.users.find_one({"id": payment_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    payment_id = str(uuid.uuid4())
    payment_doc = {
        "id": payment_id,
        "therapist_id": current_user["id"],
        "client_id": payment_data.client_id,
        "client_name": client["full_name"],
        "amount": payment_data.amount,
        "payment_method": payment_data.payment_method,
        "notes": payment_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payments.insert_one(payment_doc)
    await log_audit(current_user["id"], current_user["role"], "record", "payment", payment_id)
    
    return Payment(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in payment_doc.items()})

@api_router.get("/payments", response_model=List[Payment])
async def get_payments(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can view payments")
    
    query = {"therapist_id": current_user["id"]}
    if client_id:
        query["client_id"] = client_id
    
    payments = await db.payments.find(query, {"_id": 0}).to_list(1000)
    return [Payment(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in payment.items()}) for payment in payments]

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Run on application startup - migrate therapists without subscriptions"""
    logger.info("Running startup migration for therapists without subscriptions...")
    
    # Find all therapists without subscription_status or with null/empty subscription_status
    therapists_without_subscription = await db.users.find(
        {"role": "therapist", "$or": [
            {"subscription_status": {"$exists": False}},
            {"subscription_status": None},
            {"subscription_status": ""}
        ]},
        {"_id": 0, "id": 1, "full_name": 1}
    ).to_list(1000)
    
    if not therapists_without_subscription:
        logger.info("No therapists without subscriptions found.")
        return
    
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=30)
    migrated_count = 0
    
    for therapist in therapists_without_subscription:
        # Create trial subscription
        subscription_id = str(uuid.uuid4())
        subscription_doc = {
            "id": subscription_id,
            "therapist_id": therapist["id"],
            "plan_id": "free_trial",
            "plan_name": "Free Trial",
            "status": "trial",
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
            "coupon_code": None
        }
        
        await db.subscriptions.insert_one(subscription_doc)
        
        # Update therapist
        await db.users.update_one(
            {"id": therapist["id"]},
            {"$set": {
                "subscription_status": "trial",
                "subscription_plan": "free_trial"
            }}
        )
        migrated_count += 1
        logger.info(f"Migrated therapist: {therapist.get('full_name', therapist['id'])}")
    
    logger.info(f"Startup migration complete. Migrated {migrated_count} therapists to trial subscription.")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
