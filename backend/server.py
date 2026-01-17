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
    client_id: str
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
    created_at: datetime

class ClientProfileUpdate(BaseModel):
    age: Optional[int] = None
    guardian_name: Optional[str] = None
    address: Optional[str] = None
    referred_by: Optional[str] = None
    intake_summary: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

# Appointment Models
class AppointmentCreate(BaseModel):
    client_id: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None

class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    status: str = "scheduled"
    created_at: datetime

# Session Note Models
class SessionNoteCreate(BaseModel):
    client_id: str
    template_type: Literal["SOAP", "DAP"]
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
    template_type: str
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None
    created_at: datetime
    updated_at: datetime

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
    # Validate mobile number
    if not validate_mobile(user_data.mobile):
        raise HTTPException(status_code=400, detail="Mobile number must be exactly 10 digits")
    
    # Check if mobile already exists
    existing_mobile = await db.users.find_one({"mobile": user_data.mobile})
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    
    # Check if email exists (if provided)
    if user_data.email:
        existing_email = await db.users.find_one({"email": user_data.email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    client_id = generate_client_id() if user_data.role == "client" else None
    
    user_doc = {
        "id": user_id,
        "client_id": client_id,
        "mobile": user_data.mobile,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    await log_audit(user_id, user_data.role, "register", "user", user_id)
    
    token = create_token(user_id, user_data.mobile, user_data.role)
    user = User(
        id=user_id,
        client_id=client_id,
        mobile=user_data.mobile,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        created_at=datetime.fromisoformat(user_doc["created_at"])
    )
    
    return TokenResponse(token=token, user=user)

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
    
    await log_audit(user["id"], user["role"], "login", "user", user["id"])
    
    token = create_token(user["id"], user["mobile"], user["role"])
    user_obj = User(
        id=user["id"],
        client_id=user.get("client_id"),
        mobile=user["mobile"],
        email=user.get("email"),
        full_name=user["full_name"],
        role=user["role"],
        created_at=datetime.fromisoformat(user["created_at"])
    )
    
    return TokenResponse(token=token, user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return User(
        id=current_user["id"],
        client_id=current_user.get("client_id"),
        mobile=current_user["mobile"],
        email=current_user.get("email"),
        full_name=current_user["full_name"],
        role=current_user["role"],
        created_at=datetime.fromisoformat(current_user["created_at"])
    )

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
async def create_client(client_data: ClientCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can create clients")
    
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
async def get_clients(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access this")
    
    clients = await db.users.find(
        {"role": "client"},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    result = []
    for client in clients:
        profile = await db.client_profiles.find_one({"user_id": client["id"]}, {"_id": 0})
        result.append(ClientProfile(
            id=client["id"],
            client_id=client.get("client_id", ""),
            therapist_id=profile.get("therapist_id", "") if profile else "",
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
            created_at=datetime.fromisoformat(client["created_at"])
        ))
    
    return result

@api_router.get("/clients/{client_id}", response_model=ClientProfile)
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access this")
    
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    
    return ClientProfile(
        id=client["id"],
        client_id=client.get("client_id", ""),
        therapist_id=profile.get("therapist_id", "") if profile else "",
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
        created_at=datetime.fromisoformat(client["created_at"])
    )

@api_router.put("/clients/{client_id}", response_model=ClientProfile)
async def update_client(client_id: str, update_data: ClientProfileUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access this")
    
    client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    profile_data = update_data.model_dump(exclude_unset=True)
    profile_data["therapist_id"] = current_user["id"]
    profile_data["user_id"] = client_id
    profile_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.client_profiles.update_one(
        {"user_id": client_id},
        {"$set": profile_data},
        upsert=True
    )
    
    await log_audit(current_user["id"], current_user["role"], "update", "client_profile", client_id, profile_data)
    
    return await get_client(client_id, current_user)

# ============= APPOINTMENT ENDPOINTS =============

@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appt_data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can create appointments")
    
    # Check for double-booking
    existing = await db.appointments.find_one({
        "therapist_id": current_user["id"],
        "$or": [
            {"start_time": {"$lt": appt_data.end_time.isoformat()}, "end_time": {"$gt": appt_data.start_time.isoformat()}}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Time slot already booked")
    
    client = await db.users.find_one({"id": appt_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
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
    query = {}
    if current_user["role"] == "therapist":
        query["therapist_id"] = current_user["id"]
    else:
        query["client_id"] = current_user["id"]
    
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(1000)
    
    return [Appointment(**{k: datetime.fromisoformat(v) if k in ["start_time", "end_time", "created_at"] else v for k, v in appt.items()}) for appt in appointments]

# ============= SESSION NOTES ENDPOINTS =============

@api_router.post("/session-notes", response_model=SessionNote)
async def create_session_note(note_data: SessionNoteCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can create session notes")
    
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
async def get_session_notes(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can view session notes")
    
    query = {"therapist_id": current_user["id"]}
    if client_id:
        query["client_id"] = client_id
    
    notes = await db.session_notes.find(query, {"_id": 0}).to_list(1000)
    return [SessionNote(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in note.items()}) for note in notes]

# ============= MESSAGING ENDPOINTS =============

@api_router.post("/messages", response_model=Message)
async def send_message(msg_data: MessageCreate, current_user: dict = Depends(get_current_user)):
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
async def create_custom_assessment(assessment_data: CustomAssessmentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can create custom assessments")
    
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
async def get_custom_assessments(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access this")
    
    assessments = await db.custom_assessments.find({"therapist_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return [CustomAssessment(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in assess.items()}) for assess in assessments]

@api_router.post("/assessments", response_model=Assessment)
async def assign_assessment(assessment_data: AssessmentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can assign assessments")
    
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
async def create_protocol(protocol_data: ProtocolCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can create protocols")
    
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
async def get_protocols(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can access protocols")
    
    protocols = await db.protocols.find({"therapist_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return [Protocol(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in proto.items()}) for proto in protocols]

# ============= HOMEWORK ENDPOINTS =============

@api_router.post("/homework", response_model=Homework)
async def assign_homework(hw_data: HomeworkCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can assign homework")
    
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
