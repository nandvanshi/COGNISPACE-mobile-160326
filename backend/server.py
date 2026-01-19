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
from zoneinfo import ZoneInfo
from passlib.context import CryptContext
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

# IST timezone for India Standard Time
IST = ZoneInfo("Asia/Kolkata")
import jwt
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AI/LLM Configuration
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

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
    therapist_id: Optional[str] = None  # Only for assistants - linked therapist
    mobile: str
    email: Optional[str] = None
    full_name: str
    role: str
    status: Optional[str] = None  # For therapists: pending_approval, approved, suspended, rejected; For assistants: active, suspended
    subscription_status: Optional[str] = None  # For therapists: trial, active, expired, cancelled
    subscription_plan: Optional[str] = None
    created_at: datetime

class TokenResponse(BaseModel):
    token: str
    user: User

# Assistant Models
class AssistantCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class AssistantUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime

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

# Note Template Models
class NoteTemplateCreate(BaseModel):
    name: str
    category: Literal["subjective", "objective", "assessment", "plan", "data", "general"]
    content: str

class NoteTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[Literal["subjective", "objective", "assessment", "plan", "data", "general"]] = None
    content: Optional[str] = None

class NoteTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    name: str
    category: str
    content: str
    usage_count: int = 0
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

class ClientMessagingSettings(BaseModel):
    messaging_enabled: bool

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

# AI Clinical Support Models
class AIAssessmentSuggestionRequest(BaseModel):
    client_id: Optional[str] = None  # If provided, uses client's data
    query: Optional[str] = None  # Manual query from therapist
    include_intake: bool = True
    include_notes: bool = True

class AIAssessmentSuggestion(BaseModel):
    assessment_name: str
    assessment_type: str  # PHQ-9, GAD-7, etc.
    reason: str
    priority: str  # high, medium, low
    relevant_symptoms: List[str]

class AIAssessmentSuggestionResponse(BaseModel):
    suggestions: List[AIAssessmentSuggestion]
    analysis_summary: str
    data_sources_used: List[str]

class AIProtocolRequest(BaseModel):
    client_id: Optional[str] = None
    assessment_ids: Optional[List[str]] = None  # Based on completed assessments
    query: Optional[str] = None  # Manual description
    modality_preference: Optional[str] = None  # CBT, DBT, ACT, etc.

class AIProtocolSession(BaseModel):
    session_number: int
    title: str
    objectives: List[str]
    interventions: List[str]
    homework: Optional[str] = None
    duration_minutes: int = 60

class AIProtocolResponse(BaseModel):
    protocol_name: str
    target_condition: str
    recommended_modality: str
    rationale: str
    estimated_sessions: int
    sessions: List[AIProtocolSession]
    contraindications: Optional[List[str]] = None
    progress_markers: List[str]

class AIHomeworkRequest(BaseModel):
    client_id: str
    context: Optional[str] = None  # What was discussed in session
    homework_type: Optional[str] = None  # worksheet, exercise, reading, reflection
    protocol_id: Optional[str] = None  # If following a protocol

class AIHomeworkResponse(BaseModel):
    title: str
    description: str
    instructions: str
    exercises: List[dict]  # [{name, description, steps}]
    estimated_time_minutes: int
    therapeutic_rationale: str

# Resource Library Models
class ResourceCreate(BaseModel):
    title: str
    category: str  # worksheet, exercise, psychoeducation, reading, meditation
    content: str
    tags: List[str] = []
    is_downloadable: bool = True

class Resource(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    title: str
    category: str
    content: str
    tags: List[str]
    is_downloadable: bool
    usage_count: int = 0
    created_at: datetime

class ResourceAssignment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    resource_id: str
    resource_title: str
    notes: Optional[str] = None
    status: str = "assigned"  # assigned, viewed, completed
    assigned_at: datetime
    viewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# ============= CASE HISTORY MODELS (MMS-Style) =============

class BasicIdentification(BaseModel):
    """Section 1: Basic Identification"""
    name: str
    age: Optional[int] = None
    dob: Optional[str] = None
    gender: Optional[str] = None  # Male, Female, Other, Prefer not to say
    marital_status: Optional[str] = None  # Single, Married, Divorced, Widowed, Separated
    education: Optional[str] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    contact: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    referred_by: Optional[str] = None

class PresentingComplaints(BaseModel):
    """Section 2: Presenting Complaints"""
    main_problems: str  # Client's main problems in their own words
    duration: Optional[str] = None  # How long the problem has persisted
    severity: Optional[str] = None  # Mild, Moderate, Severe
    frequency: Optional[str] = None  # Daily, Weekly, Occasionally, etc.
    triggers: Optional[str] = None  # What triggers or worsens the problem

class HistoryOfPresentIllness(BaseModel):
    """Section 3: History of Present Illness"""
    onset: Optional[str] = None  # When did it start
    course: Optional[str] = None  # How has it progressed
    previous_episodes: Optional[str] = None  # Any previous similar episodes
    factors_improving: Optional[str] = None  # What makes it better
    factors_worsening: Optional[str] = None  # What makes it worse
    prior_therapy: Optional[str] = None  # Previous therapy taken
    prior_medication: Optional[str] = None  # Previous medications

class PastPsychiatricHistory(BaseModel):
    """Section 4: Past Psychiatric History"""
    previous_therapy: Optional[str] = None
    previous_diagnosis: Optional[str] = None
    hospitalizations: Optional[str] = None
    past_medications: Optional[str] = None
    current_medications: Optional[str] = None

class MedicalHistory(BaseModel):
    """Section 5: Medical History"""
    chronic_illnesses: Optional[str] = None
    current_medications: Optional[str] = None
    sleep_pattern: Optional[str] = None  # Good, Poor, Insomnia, Hypersomnia
    appetite: Optional[str] = None  # Normal, Increased, Decreased
    substance_use: Optional[str] = None  # None, Alcohol, Tobacco, Others

class FamilyHistory(BaseModel):
    """Section 6: Family History"""
    family_structure: Optional[str] = None  # Description of family
    mental_illness_in_family: Optional[str] = None  # Yes/No with details
    relationship_dynamics: Optional[str] = None  # Quality of family relationships

class PersonalDevelopmentalHistory(BaseModel):
    """Section 7: Personal & Developmental History"""
    childhood: Optional[str] = None
    education_history: Optional[str] = None
    work_history: Optional[str] = None
    major_life_events: Optional[str] = None  # Optional, sensitive
    trauma_history: Optional[str] = None  # Optional, sensitive

class MentalStatusExamination(BaseModel):
    """Section 8: Mental Status Examination (MSE)"""
    appearance: Optional[str] = None  # Well-groomed, Disheveled, etc.
    behavior: Optional[str] = None  # Cooperative, Agitated, Withdrawn, etc.
    speech: Optional[str] = None  # Normal, Pressured, Slow, etc.
    mood: Optional[str] = None  # Euthymic, Depressed, Anxious, Irritable, etc.
    affect: Optional[str] = None  # Appropriate, Flat, Labile, etc.
    thought_process: Optional[str] = None  # Logical, Tangential, Circumstantial, etc.
    thought_content: Optional[str] = None  # Normal, Delusions, Obsessions, etc.
    perception: Optional[str] = None  # Normal, Hallucinations, etc.
    cognition: Optional[str] = None  # Intact, Impaired
    insight: Optional[str] = None  # Good, Partial, Poor
    judgment: Optional[str] = None  # Good, Fair, Poor

class ProvisionalFormulation(BaseModel):
    """Section 9: Provisional Formulation"""
    clinical_formulation: str  # Working clinical formulation
    stressors: Optional[str] = None  # Current stressors
    strengths: Optional[str] = None  # Client's strengths
    risk_indicators: Optional[str] = None  # Any risk factors (self-harm, etc.)

class InitialTherapyPlan(BaseModel):
    """Section 10: Initial Therapy Plan"""
    therapy_modality: Optional[str] = None  # CBT, DBT, ACT, etc.
    session_frequency: Optional[str] = None  # Weekly, Bi-weekly, etc.
    initial_goals: Optional[str] = None
    homework: Optional[str] = None

class ConsentDisclaimer(BaseModel):
    """Section 11: Consent & Disclaimer"""
    informed_consent_taken: bool = False
    confidentiality_explained: bool = False
    consent_date: Optional[str] = None
    additional_notes: Optional[str] = None

class CaseHistoryCreate(BaseModel):
    """Create Case History - All sections"""
    client_id: str
    basic_identification: BasicIdentification
    presenting_complaints: PresentingComplaints
    history_of_present_illness: Optional[HistoryOfPresentIllness] = None
    past_psychiatric_history: Optional[PastPsychiatricHistory] = None
    medical_history: Optional[MedicalHistory] = None
    family_history: Optional[FamilyHistory] = None
    personal_developmental_history: Optional[PersonalDevelopmentalHistory] = None
    mental_status_examination: Optional[MentalStatusExamination] = None
    provisional_formulation: Optional[ProvisionalFormulation] = None
    initial_therapy_plan: Optional[InitialTherapyPlan] = None
    consent_disclaimer: Optional[ConsentDisclaimer] = None
    is_complete: bool = False

class CaseHistory(BaseModel):
    """Full Case History Model"""
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    therapist_id: str
    basic_identification: dict
    presenting_complaints: dict
    history_of_present_illness: Optional[dict] = None
    past_psychiatric_history: Optional[dict] = None
    medical_history: Optional[dict] = None
    family_history: Optional[dict] = None
    personal_developmental_history: Optional[dict] = None
    mental_status_examination: Optional[dict] = None
    provisional_formulation: Optional[dict] = None
    initial_therapy_plan: Optional[dict] = None
    consent_disclaimer: Optional[dict] = None
    is_complete: bool = False
    created_at: datetime
    updated_at: datetime

# ============= THERAPY CONSENT MODELS =============

class TherapyConsentCreate(BaseModel):
    """Create therapy consent"""
    client_id: str
    consent_text_version: str = "1.0"

class TherapyConsent(BaseModel):
    """Therapy Consent with Signature"""
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    therapist_id: str
    therapist_name: str
    client_name: str
    consent_text: str
    consent_text_version: str
    signature_method: Optional[str] = None  # "digital" or "paper"
    signed_at: Optional[datetime] = None
    is_signed: bool = False
    case_history_id: str
    created_at: datetime
    updated_at: datetime

# Standard consent text template
CONSENT_TEXT_TEMPLATE = """
INFORMED CONSENT FOR PSYCHOTHERAPY

Client Name: {client_name}
Therapist Name: {therapist_name}
Date: {date}

1. Purpose of Therapy
I understand that psychotherapy involves discussing my thoughts, emotions, behaviors, and personal experiences with a qualified therapist for the purpose of improving my mental and emotional well-being.

2. Nature of Therapy
I understand that:
• Therapy is a collaborative process.
• Results cannot be guaranteed.
• Therapy may involve discussing difficult or uncomfortable topics.
• I have the right to ask questions at any time.

3. Confidentiality
I understand that:
• All information shared during therapy is confidential.
• Confidentiality may be legally breached only in situations such as:
  - Risk of serious harm to self or others
  - Court orders or legal requirements
  - Suspected abuse (as required by law)

4. Records & Documentation
I understand that:
• The therapist will maintain clinical notes for professional purposes.
• These notes are not accessible to me unless required by law.
• My personal and clinical data is stored securely in this application.

5. Consent for Services
I confirm that:
• I am voluntarily seeking therapy services.
• I have had the opportunity to ask questions.
• I understand the scope and limitations of therapy.

6. Right to Withdraw
I understand that:
• I may discontinue therapy at any time.
• I may withdraw my consent by informing my therapist.
"""

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
    
    # Check assistant account status
    if user["role"] == "assistant":
        if user.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Your account has been suspended")
        if user.get("status") == "deleted":
            raise HTTPException(status_code=403, detail="Your account has been deleted")
        # Verify linked therapist exists and is active
        therapist = await db.users.find_one({"id": user.get("therapist_id"), "role": "therapist"}, {"_id": 0})
        if not therapist:
            raise HTTPException(status_code=403, detail="Your linked therapist account no longer exists")
        if therapist.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="The therapist account you're linked to has been suspended")
    
    await log_audit(user["id"], user["role"], "login", "user", user["id"])
    
    token = create_token(user["id"], user.get("mobile", user.get("email", "")), user["role"])
    user_obj = User(
        id=user["id"],
        client_id=user.get("client_id"),
        therapist_id=user.get("therapist_id"),  # For assistants
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
        therapist_id=current_user.get("therapist_id"),
        mobile=current_user.get("mobile", ""),
        email=current_user.get("email"),
        full_name=current_user["full_name"],
        role=current_user["role"],
        status=current_user.get("status"),
        subscription_status=current_user.get("subscription_status"),
        subscription_plan=current_user.get("subscription_plan"),
        created_at=datetime.fromisoformat(current_user["created_at"])
    )

@api_router.get("/auth/subscription-status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status (for therapists and assistants)"""
    if current_user["role"] == "assistant":
        # For assistants, get the linked therapist's subscription status
        therapist = await db.users.find_one({"id": current_user.get("therapist_id")}, {"_id": 0})
        if not therapist:
            return {"is_read_only": True, "subscription_status": None, "subscription_end_date": None}
        subscription_status = therapist.get("subscription_status")
        is_read_only = subscription_status not in ["trial", "active"]
        subscription = await db.subscriptions.find_one(
            {"therapist_id": therapist["id"]},
            {"_id": 0},
            sort=[("start_date", -1)]
        )
        subscription_end_date = subscription.get("end_date") if subscription else None
        return {
            "is_read_only": is_read_only,
            "subscription_status": subscription_status,
            "subscription_plan": therapist.get("subscription_plan"),
            "subscription_end_date": subscription_end_date
        }
    
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

def get_effective_therapist_id(user: dict) -> str:
    """Get the therapist_id for the current user (self if therapist, linked therapist if assistant)"""
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None

async def get_linked_therapist(user: dict) -> dict:
    """Get the therapist object for an assistant's linked therapist"""
    if user["role"] == "therapist":
        return user
    elif user["role"] == "assistant":
        therapist = await db.users.find_one({"id": user.get("therapist_id"), "role": "therapist"}, {"_id": 0})
        return therapist
    return None

async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    """Allows therapist or their assistant to access (for read operations on non-clinical data)"""
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Therapist or assistant access required")
    
    if current_user["role"] == "therapist":
        status = current_user.get("status")
        if status == "suspended":
            raise HTTPException(status_code=403, detail="Your account has been suspended")
        if status == "rejected":
            raise HTTPException(status_code=403, detail="Your application was rejected")
    elif current_user["role"] == "assistant":
        if current_user.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Your account has been suspended")
        # Check if linked therapist is still valid
        therapist = await get_linked_therapist(current_user)
        if not therapist:
            raise HTTPException(status_code=403, detail="Linked therapist not found")
        if therapist.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="The therapist account you're linked to has been suspended")
    
    return current_user

async def require_active_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    """Allows therapist with active subscription or their assistant (for write operations on non-clinical data)"""
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Therapist or assistant access required")
    
    if current_user["role"] == "therapist":
        status = current_user.get("status")
        if status == "suspended":
            raise HTTPException(status_code=403, detail="Your account has been suspended")
        if status == "rejected":
            raise HTTPException(status_code=403, detail="Your application was rejected")
        subscription_status = current_user.get("subscription_status")
        if subscription_status not in ["trial", "active"]:
            raise HTTPException(
                status_code=403, 
                detail="Your subscription has expired. You are in read-only mode. Please renew to make changes."
            )
    elif current_user["role"] == "assistant":
        if current_user.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="Your account has been suspended")
        # Check linked therapist's subscription
        therapist = await get_linked_therapist(current_user)
        if not therapist:
            raise HTTPException(status_code=403, detail="Linked therapist not found")
        if therapist.get("status") == "suspended":
            raise HTTPException(status_code=403, detail="The therapist account you're linked to has been suspended")
        subscription_status = therapist.get("subscription_status")
        if subscription_status not in ["trial", "active"]:
            raise HTTPException(
                status_code=403, 
                detail="The therapist's subscription has expired. Read-only mode is active."
            )
    
    return current_user

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

# ============= ASSISTANT ENDPOINTS =============

@api_router.post("/assistants", response_model=AssistantResponse)
async def create_assistant(assistant_data: AssistantCreate, current_user: dict = Depends(require_active_therapist)):
    """Therapist creates an assistant linked to their account"""
    # Check if email already exists
    existing = await db.users.find_one({"email": assistant_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    assistant_id = str(uuid.uuid4())
    assistant_doc = {
        "id": assistant_id,
        "therapist_id": current_user["id"],
        "email": assistant_data.email,
        "password_hash": hash_password(assistant_data.password),
        "full_name": assistant_data.full_name,
        "role": "assistant",
        "status": "active",
        "mobile": "",  # Assistants login via email
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(assistant_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "assistant", assistant_id, 
                   {"assistant_email": assistant_data.email})
    
    return AssistantResponse(
        id=assistant_id,
        therapist_id=current_user["id"],
        email=assistant_data.email,
        full_name=assistant_data.full_name,
        role="assistant",
        status="active",
        created_at=datetime.fromisoformat(assistant_doc["created_at"])
    )

@api_router.get("/assistants", response_model=List[AssistantResponse])
async def get_assistants(current_user: dict = Depends(require_therapist)):
    """Therapist gets list of their assistants"""
    assistants = await db.users.find(
        {"therapist_id": current_user["id"], "role": "assistant", "status": {"$ne": "deleted"}},
        {"_id": 0}
    ).to_list(100)
    
    return [AssistantResponse(
        id=a["id"],
        therapist_id=a["therapist_id"],
        email=a["email"],
        full_name=a["full_name"],
        role=a["role"],
        status=a["status"],
        created_at=datetime.fromisoformat(a["created_at"])
    ) for a in assistants]

@api_router.get("/assistants/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Get a specific assistant"""
    assistant = await db.users.find_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"_id": 0}
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return AssistantResponse(
        id=assistant["id"],
        therapist_id=assistant["therapist_id"],
        email=assistant["email"],
        full_name=assistant["full_name"],
        role=assistant["role"],
        status=assistant["status"],
        created_at=datetime.fromisoformat(assistant["created_at"])
    )

@api_router.put("/assistants/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(assistant_id: str, update_data: AssistantUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update assistant details"""
    assistant = await db.users.find_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"_id": 0}
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    update_fields = {}
    if update_data.email is not None:
        # Check email uniqueness
        existing = await db.users.find_one({"email": update_data.email, "id": {"$ne": assistant_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_fields["email"] = update_data.email
    if update_data.full_name is not None:
        update_fields["full_name"] = update_data.full_name
    
    if update_fields:
        await db.users.update_one({"id": assistant_id}, {"$set": update_fields})
        await log_audit(current_user["id"], current_user["role"], "update", "assistant", assistant_id, update_fields)
    
    # Fetch updated assistant
    assistant = await db.users.find_one({"id": assistant_id}, {"_id": 0})
    return AssistantResponse(
        id=assistant["id"],
        therapist_id=assistant["therapist_id"],
        email=assistant["email"],
        full_name=assistant["full_name"],
        role=assistant["role"],
        status=assistant["status"],
        created_at=datetime.fromisoformat(assistant["created_at"])
    )

@api_router.put("/assistants/{assistant_id}/suspend")
async def suspend_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Suspend an assistant"""
    assistant = await db.users.find_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"_id": 0}
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    await db.users.update_one({"id": assistant_id}, {"$set": {"status": "suspended"}})
    await log_audit(current_user["id"], current_user["role"], "suspend", "assistant", assistant_id)
    
    return {"message": f"Assistant {assistant['full_name']} has been suspended"}

@api_router.put("/assistants/{assistant_id}/activate")
async def activate_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Activate a suspended assistant"""
    assistant = await db.users.find_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"_id": 0}
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    await db.users.update_one({"id": assistant_id}, {"$set": {"status": "active"}})
    await log_audit(current_user["id"], current_user["role"], "activate", "assistant", assistant_id)
    
    return {"message": f"Assistant {assistant['full_name']} has been activated"}

@api_router.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Soft delete an assistant"""
    assistant = await db.users.find_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"_id": 0}
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    # Soft delete - mark as deleted
    await db.users.update_one({"id": assistant_id}, {"$set": {"status": "deleted"}})
    await log_audit(current_user["id"], current_user["role"], "delete", "assistant", assistant_id)
    
    return {"message": f"Assistant {assistant['full_name']} has been deleted"}

@api_router.put("/assistants/{assistant_id}/reset-password")
async def reset_assistant_password(assistant_id: str, new_password: str, current_user: dict = Depends(require_therapist)):
    """Reset assistant password"""
    assistant = await db.users.find_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"_id": 0}
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    await db.users.update_one({"id": assistant_id}, {"$set": {"password_hash": hash_password(new_password)}})
    await log_audit(current_user["id"], current_user["role"], "reset_password", "assistant", assistant_id)
    
    return {"message": f"Password reset for {assistant['full_name']}"}

# Super Admin can also manage assistants
@api_router.get("/admin/assistants", response_model=List[AssistantResponse])
async def admin_get_all_assistants(therapist_id: Optional[str] = None, current_user: dict = Depends(require_super_admin)):
    """Super Admin gets all assistants, optionally filtered by therapist"""
    query = {"role": "assistant"}
    if therapist_id:
        query["therapist_id"] = therapist_id
    
    assistants = await db.users.find(query, {"_id": 0}).to_list(1000)
    
    return [AssistantResponse(
        id=a["id"],
        therapist_id=a["therapist_id"],
        email=a["email"],
        full_name=a["full_name"],
        role=a["role"],
        status=a["status"],
        created_at=datetime.fromisoformat(a["created_at"])
    ) for a in assistants]

@api_router.post("/admin/assistants", response_model=AssistantResponse)
async def admin_create_assistant(assistant_data: AssistantCreate, therapist_id: str, current_user: dict = Depends(require_super_admin)):
    """Super Admin creates an assistant for a therapist"""
    # Verify therapist exists
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Check if email already exists
    existing = await db.users.find_one({"email": assistant_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    assistant_id = str(uuid.uuid4())
    assistant_doc = {
        "id": assistant_id,
        "therapist_id": therapist_id,
        "email": assistant_data.email,
        "password_hash": hash_password(assistant_data.password),
        "full_name": assistant_data.full_name,
        "role": "assistant",
        "status": "active",
        "mobile": "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(assistant_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "assistant", assistant_id,
                   {"therapist_id": therapist_id, "assistant_email": assistant_data.email})
    
    return AssistantResponse(
        id=assistant_id,
        therapist_id=therapist_id,
        email=assistant_data.email,
        full_name=assistant_data.full_name,
        role="assistant",
        status="active",
        created_at=datetime.fromisoformat(assistant_doc["created_at"])
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
async def create_client(client_data: ClientCreate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Create a client - therapist or assistant can create"""
    # Get effective therapist_id (for assistants, it's their linked therapist)
    therapist_id = get_effective_therapist_id(current_user)
    
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
    
    # Create client profile - linked to the therapist (not assistant)
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
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.client_profiles.insert_one(profile_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "client", client_id,
                   {"created_by_assistant": current_user["role"] == "assistant"})
    
    return ClientProfile(
        id=client_id,
        client_id=unique_client_id,
        therapist_id=therapist_id,
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
async def get_clients(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get only clients assigned to the therapist (or assistant's linked therapist)"""
    therapist_id = get_effective_therapist_id(current_user)
    
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
async def get_client(client_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Get a specific client - must be assigned to therapist (or assistant's linked therapist)"""
    therapist_id = get_effective_therapist_id(current_user)
    
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
async def update_client(client_id: str, update_data: ClientProfileUpdate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Update client - assistant can update non-clinical data but cannot reassign to another therapist"""
    therapist_id = get_effective_therapist_id(current_user)
    
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
    
    # Assistants cannot change therapist assignment (reassign clients)
    if current_user["role"] == "assistant" and "therapist_id" in update_dict:
        raise HTTPException(status_code=403, detail="Assistants cannot reassign clients to another therapist")
    
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
async def create_appointment(appt_data: AppointmentCreate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Create a new appointment - assistants can create appointments for their linked therapist"""
    therapist_id = get_effective_therapist_id(current_user)
    
    # Validate times
    if appt_data.start_time >= appt_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    # Check for double-booking (exclude cancelled appointments)
    existing = await db.appointments.find_one({
        "therapist_id": therapist_id,
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
    client_profile = await db.client_profiles.find_one({"user_id": appt_data.client_id}, {"_id": 0})
    if client_profile and client_profile.get("therapist_id") != therapist_id:
        raise HTTPException(status_code=403, detail="Client is not assigned to this therapist")
    
    appt_id = str(uuid.uuid4())
    appt_doc = {
        "id": appt_id,
        "therapist_id": therapist_id,
        "client_id": appt_data.client_id,
        "client_name": client["full_name"],
        "start_time": appt_data.start_time.isoformat(),
        "end_time": appt_data.end_time.isoformat(),
        "notes": appt_data.notes,
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["id"]
    }
    
    await db.appointments.insert_one(appt_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "appointment", appt_id,
                   {"created_by_assistant": current_user["role"] == "assistant"})
    
    return Appointment(**{k: datetime.fromisoformat(v) if k in ["start_time", "end_time", "created_at"] else v for k, v in appt_doc.items()})

@api_router.get("/appointments", response_model=List[Appointment])
async def get_appointments(current_user: dict = Depends(get_current_user)):
    """Get appointments - therapists/assistants see therapist's appointments, clients see theirs"""
    query = {}
    if current_user["role"] == "therapist":
        query["therapist_id"] = current_user["id"]
    elif current_user["role"] == "assistant":
        query["therapist_id"] = current_user.get("therapist_id")
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
async def update_appointment(appointment_id: str, update_data: AppointmentUpdate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Update an appointment - assistants can reschedule appointments"""
    therapist_id = get_effective_therapist_id(current_user)
    
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify ownership
    if appointment["therapist_id"] != therapist_id:
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
            "therapist_id": therapist_id,
            "id": {"$ne": appointment_id},
            "status": {"$ne": "cancelled"},
            "$or": [
                {"start_time": {"$lt": new_end}, "end_time": {"$gt": new_start}}
            ]
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Time slot already booked. Please choose a different time.")
    
    await db.appointments.update_one({"id": appointment_id}, {"$set": update_fields})
    await log_audit(current_user["id"], current_user["role"], "update", "appointment", appointment_id,
                   {"updated_by_assistant": current_user["role"] == "assistant"})
    
    # Get updated appointment
    updated = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    return Appointment(**{k: datetime.fromisoformat(v) if k in ["start_time", "end_time", "created_at"] else v for k, v in updated.items()})

@api_router.post("/appointments/{appointment_id}/complete")
async def complete_appointment(appointment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Mark an appointment as completed - ONLY therapists can complete (clinical action)"""
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
async def cancel_appointment(appointment_id: str, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Cancel an appointment - assistants can cancel appointments"""
    therapist_id = get_effective_therapist_id(current_user)
    
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment["therapist_id"] != therapist_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if appointment["status"] == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed appointment")
    
    await db.appointments.update_one({"id": appointment_id}, {"$set": {"status": "cancelled"}})
    await log_audit(current_user["id"], current_user["role"], "cancel", "appointment", appointment_id,
                   {"cancelled_by_assistant": current_user["role"] == "assistant"})
    
    return {"message": "Appointment cancelled"}

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete an appointment - ONLY therapists can permanently delete"""
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
async def create_blocked_time(block_data: BlockedTimeCreate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Block a time range (e.g., vacation, personal time) - assistants can block calendar time"""
    therapist_id = get_effective_therapist_id(current_user)
    
    if block_data.start_datetime >= block_data.end_datetime:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    block_id = str(uuid.uuid4())
    block_doc = {
        "id": block_id,
        "therapist_id": therapist_id,
        "start_datetime": block_data.start_datetime.isoformat(),
        "end_datetime": block_data.end_datetime.isoformat(),
        "reason": block_data.reason,
        "is_all_day": block_data.is_all_day,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["id"]
    }
    
    await db.blocked_times.insert_one(block_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "blocked_time", block_id,
                   {"created_by_assistant": current_user["role"] == "assistant"})
    
    return BlockedTime(**{k: datetime.fromisoformat(v) if k in ["start_datetime", "end_datetime", "created_at"] else v for k, v in block_doc.items()})

@api_router.get("/blocked-times", response_model=List[BlockedTime])
async def get_blocked_times(current_user: dict = Depends(get_current_user)):
    """Get all blocked times for the therapist - assistants can view their therapist's blocked times"""
    if current_user["role"] == "therapist":
        therapist_id = current_user["id"]
    elif current_user["role"] == "assistant":
        therapist_id = current_user.get("therapist_id")
    else:
        raise HTTPException(status_code=403, detail="Only therapists and assistants can access blocked times")
    
    blocked = await db.blocked_times.find({"therapist_id": therapist_id}, {"_id": 0}).to_list(1000)
    
    return [BlockedTime(**{k: datetime.fromisoformat(v) if k in ["start_datetime", "end_datetime", "created_at"] else v for k, v in b.items()}) for b in blocked]

@api_router.delete("/blocked-times/{block_id}")
async def delete_blocked_time(block_id: str, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Delete a blocked time - assistants can delete blocked times they or the therapist created"""
    therapist_id = get_effective_therapist_id(current_user)
    
    block = await db.blocked_times.find_one({"id": block_id}, {"_id": 0})
    if not block:
        raise HTTPException(status_code=404, detail="Blocked time not found")
    
    if block["therapist_id"] != therapist_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.blocked_times.delete_one({"id": block_id})
    await log_audit(current_user["id"], current_user["role"], "delete", "blocked_time", block_id,
                   {"deleted_by_assistant": current_user["role"] == "assistant"})
    
    return {"message": "Blocked time deleted"}

# ============= AVAILABLE SLOTS ENDPOINT =============

@api_router.get("/available-slots/{therapist_id}", response_model=List[AvailableSlot])
async def get_available_slots(therapist_id: str, date: str, current_user: dict = Depends(get_current_user)):
    """Get available appointment slots for a specific date.
    This is the public-facing endpoint for clients to see available times.
    
    IMPORTANT: All availability times are in IST (India Standard Time).
    The therapist sets times in IST, slots are generated in IST, and returned in IST.
    """
    # Parse the date
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Don't allow booking in the past (compare in IST)
    now_ist = datetime.now(IST)
    if target_date < now_ist.date():
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
    
    # Create IST day boundaries for querying existing appointments/blocks
    # We query with a wide range to catch all relevant appointments
    start_of_day_ist = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=IST)
    end_of_day_ist = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=IST)
    # Convert to UTC for database query (appointments stored in UTC)
    start_of_day_utc = start_of_day_ist.astimezone(timezone.utc)
    end_of_day_utc = end_of_day_ist.astimezone(timezone.utc)
    
    existing_appointments = await db.appointments.find({
        "therapist_id": therapist_id,
        "status": {"$ne": "cancelled"},
        "start_time": {"$gte": start_of_day_utc.isoformat(), "$lt": end_of_day_utc.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    # Get blocked times for this date
    blocked_times = await db.blocked_times.find({
        "therapist_id": therapist_id,
        "$or": [
            {"start_datetime": {"$gte": start_of_day_utc.isoformat(), "$lt": end_of_day_utc.isoformat()}},
            {"end_datetime": {"$gt": start_of_day_utc.isoformat(), "$lte": end_of_day_utc.isoformat()}},
            {"start_datetime": {"$lte": start_of_day_utc.isoformat()}, "end_datetime": {"$gte": end_of_day_utc.isoformat()}}
        ]
    }, {"_id": 0}).to_list(100)
    
    # Generate slots - time blocks are in IST
    available_slots = []
    
    for block in time_blocks:
        block_start = datetime.strptime(block["start_time"], "%H:%M").time()
        block_end = datetime.strptime(block["end_time"], "%H:%M").time()
        
        # Create datetime in IST (availability is configured in IST)
        current_start_ist = datetime.combine(target_date, block_start).replace(tzinfo=IST)
        block_end_ist = datetime.combine(target_date, block_end).replace(tzinfo=IST)
        
        while current_start_ist + timedelta(minutes=session_duration) <= block_end_ist:
            slot_end_ist = current_start_ist + timedelta(minutes=session_duration)
            
            # Convert to UTC for comparison with stored appointments/blocks
            current_start_utc = current_start_ist.astimezone(timezone.utc)
            slot_end_utc = slot_end_ist.astimezone(timezone.utc)
            
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
                
                if current_start_utc < appt_end and slot_end_utc > appt_start:
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
                
                if current_start_utc < bt_end and slot_end_utc > bt_start:
                    is_blocked = True
                    break
            
            # Don't show slots that have already passed today (compare in IST)
            is_past = current_start_ist <= now_ist
            
            if not is_booked and not is_blocked and not is_past:
                # Return slots in UTC (frontend will convert to IST for display)
                available_slots.append(AvailableSlot(
                    start_time=current_start_utc,
                    end_time=slot_end_utc,
                    duration_minutes=session_duration
                ))
            
            # Move to next slot (session + buffer) in IST
            current_start_ist = slot_end_ist + timedelta(minutes=buffer_time)
    
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

# ============= CASE HISTORY ENDPOINTS =============

@api_router.post("/case-history", response_model=CaseHistory)
async def create_case_history(case_data: CaseHistoryCreate, current_user: dict = Depends(require_active_therapist)):
    """Create case history for a client - First session mandatory"""
    therapist_id = current_user["id"]
    
    # Verify client belongs to this therapist
    client_profile = await db.client_profiles.find_one(
        {"user_id": case_data.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found or not assigned to you")
    
    # Check if case history already exists
    existing = await db.case_histories.find_one(
        {"client_id": case_data.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Case history already exists for this client. Use PUT to update.")
    
    now = datetime.now(timezone.utc).isoformat()
    
    case_doc = {
        "id": str(uuid.uuid4()),
        "client_id": case_data.client_id,
        "therapist_id": therapist_id,
        "basic_identification": case_data.basic_identification.model_dump() if case_data.basic_identification else {},
        "presenting_complaints": case_data.presenting_complaints.model_dump() if case_data.presenting_complaints else {},
        "history_of_present_illness": case_data.history_of_present_illness.model_dump() if case_data.history_of_present_illness else None,
        "past_psychiatric_history": case_data.past_psychiatric_history.model_dump() if case_data.past_psychiatric_history else None,
        "medical_history": case_data.medical_history.model_dump() if case_data.medical_history else None,
        "family_history": case_data.family_history.model_dump() if case_data.family_history else None,
        "personal_developmental_history": case_data.personal_developmental_history.model_dump() if case_data.personal_developmental_history else None,
        "mental_status_examination": case_data.mental_status_examination.model_dump() if case_data.mental_status_examination else None,
        "provisional_formulation": case_data.provisional_formulation.model_dump() if case_data.provisional_formulation else None,
        "initial_therapy_plan": case_data.initial_therapy_plan.model_dump() if case_data.initial_therapy_plan else None,
        "consent_disclaimer": case_data.consent_disclaimer.model_dump() if case_data.consent_disclaimer else None,
        "is_complete": case_data.is_complete,
        "created_at": now,
        "updated_at": now
    }
    
    await db.case_histories.insert_one(case_doc)
    
    return CaseHistory(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in case_doc.items()})

@api_router.get("/case-history/{client_id}", response_model=CaseHistory)
async def get_case_history(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get case history for a client - Therapist only"""
    # Only therapists can view case history
    if current_user["role"] not in ["therapist"]:
        raise HTTPException(status_code=403, detail="Only therapists can view case history")
    
    therapist_id = current_user["id"]
    
    case_history = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not case_history:
        raise HTTPException(status_code=404, detail="Case history not found")
    
    return CaseHistory(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in case_history.items()})

@api_router.get("/case-history/check/{client_id}")
async def check_case_history_exists(client_id: str, current_user: dict = Depends(get_current_user)):
    """Check if case history exists for a client"""
    if current_user["role"] not in ["therapist"]:
        raise HTTPException(status_code=403, detail="Only therapists can check case history")
    
    therapist_id = current_user["id"]
    
    case_history = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0, "id": 1, "is_complete": 1}
    )
    
    return {
        "exists": case_history is not None,
        "is_complete": case_history.get("is_complete", False) if case_history else False,
        "case_history_id": case_history.get("id") if case_history else None
    }

@api_router.put("/case-history/{client_id}", response_model=CaseHistory)
async def update_case_history(client_id: str, case_data: CaseHistoryCreate, current_user: dict = Depends(require_active_therapist)):
    """Update case history - Therapist only, editable anytime"""
    therapist_id = current_user["id"]
    
    # Check if case history exists
    existing = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Case history not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    update_doc = {
        "basic_identification": case_data.basic_identification.model_dump() if case_data.basic_identification else existing.get("basic_identification", {}),
        "presenting_complaints": case_data.presenting_complaints.model_dump() if case_data.presenting_complaints else existing.get("presenting_complaints", {}),
        "history_of_present_illness": case_data.history_of_present_illness.model_dump() if case_data.history_of_present_illness else existing.get("history_of_present_illness"),
        "past_psychiatric_history": case_data.past_psychiatric_history.model_dump() if case_data.past_psychiatric_history else existing.get("past_psychiatric_history"),
        "medical_history": case_data.medical_history.model_dump() if case_data.medical_history else existing.get("medical_history"),
        "family_history": case_data.family_history.model_dump() if case_data.family_history else existing.get("family_history"),
        "personal_developmental_history": case_data.personal_developmental_history.model_dump() if case_data.personal_developmental_history else existing.get("personal_developmental_history"),
        "mental_status_examination": case_data.mental_status_examination.model_dump() if case_data.mental_status_examination else existing.get("mental_status_examination"),
        "provisional_formulation": case_data.provisional_formulation.model_dump() if case_data.provisional_formulation else existing.get("provisional_formulation"),
        "initial_therapy_plan": case_data.initial_therapy_plan.model_dump() if case_data.initial_therapy_plan else existing.get("initial_therapy_plan"),
        "consent_disclaimer": case_data.consent_disclaimer.model_dump() if case_data.consent_disclaimer else existing.get("consent_disclaimer"),
        "is_complete": case_data.is_complete,
        "updated_at": now
    }
    
    await db.case_histories.update_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"$set": update_doc}
    )
    
    updated = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    return CaseHistory(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in updated.items()})

@api_router.patch("/case-history/{client_id}/section")
async def update_case_history_section(client_id: str, section: str, data: dict, current_user: dict = Depends(require_active_therapist)):
    """Update a specific section of case history - For auto-save"""
    therapist_id = current_user["id"]
    
    valid_sections = [
        "basic_identification", "presenting_complaints", "history_of_present_illness",
        "past_psychiatric_history", "medical_history", "family_history",
        "personal_developmental_history", "mental_status_examination",
        "provisional_formulation", "initial_therapy_plan", "consent_disclaimer"
    ]
    
    if section not in valid_sections:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of: {valid_sections}")
    
    # Check if case history exists
    existing = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    now = datetime.now(timezone.utc).isoformat()
    
    if not existing:
        # Create new case history with just this section
        case_doc = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "therapist_id": therapist_id,
            section: data,
            "is_complete": False,
            "created_at": now,
            "updated_at": now
        }
        await db.case_histories.insert_one(case_doc)
    else:
        # Update existing
        await db.case_histories.update_one(
            {"client_id": client_id, "therapist_id": therapist_id},
            {"$set": {section: data, "updated_at": now}}
        )
    
    return {"message": f"Section '{section}' updated successfully", "updated_at": now}

@api_router.patch("/case-history/{client_id}/complete")
async def mark_case_history_complete(client_id: str, current_user: dict = Depends(require_active_therapist)):
    """Mark case history as complete - Required before session notes"""
    therapist_id = current_user["id"]
    
    existing = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Case history not found")
    
    # Validate required fields are present
    if not existing.get("basic_identification") or not existing.get("basic_identification", {}).get("name"):
        raise HTTPException(status_code=400, detail="Basic Identification (name) is required")
    
    if not existing.get("presenting_complaints") or not existing.get("presenting_complaints", {}).get("main_problems"):
        raise HTTPException(status_code=400, detail="Presenting Complaints (main problems) is required")
    
    if not existing.get("consent_disclaimer") or not existing.get("consent_disclaimer", {}).get("informed_consent_taken"):
        raise HTTPException(status_code=400, detail="Informed consent must be taken")
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db.case_histories.update_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"$set": {"is_complete": True, "updated_at": now}}
    )
    
    # Auto-generate therapy consent when case history is completed
    # Check if consent already exists
    existing_consent = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not existing_consent:
        # Get client and therapist names
        client_user = await db.users.find_one({"id": client_id}, {"_id": 0, "full_name": 1})
        therapist_user = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
        
        client_name = client_user.get("full_name", "Client") if client_user else "Client"
        therapist_name = therapist_user.get("full_name", "Therapist") if therapist_user else "Therapist"
        
        # Generate consent text
        consent_text = CONSENT_TEXT_TEMPLATE.format(
            client_name=client_name,
            therapist_name=therapist_name,
            date=datetime.now(IST).strftime("%d/%m/%Y")
        )
        
        consent_doc = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "therapist_id": therapist_id,
            "therapist_name": therapist_name,
            "client_name": client_name,
            "consent_text": consent_text,
            "consent_text_version": "1.0",
            "signature_method": None,
            "signed_at": None,
            "is_signed": False,
            "case_history_id": existing["id"],
            "created_at": now,
            "updated_at": now
        }
        
        await db.therapy_consents.insert_one(consent_doc)
    
    return {"message": "Case history marked as complete", "is_complete": True}

@api_router.get("/case-history/{client_id}/seed-from-profile")
async def seed_case_history_from_profile(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get client profile data to seed Basic Identification in Case History"""
    if current_user["role"] not in ["therapist"]:
        raise HTTPException(status_code=403, detail="Only therapists can access this")
    
    therapist_id = current_user["id"]
    
    # Get client from users collection
    client_user = await db.users.find_one({"id": client_id}, {"_id": 0})
    if not client_user:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client profile
    client_profile = await db.client_profiles.find_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    # Build basic identification from available data
    basic_info = {
        "name": client_user.get("full_name", ""),
        "contact": client_user.get("mobile", ""),
        "dob": client_profile.get("dob") if client_profile else None,
        "gender": client_profile.get("gender") if client_profile else None,
        "address": client_profile.get("address") if client_profile else None,
        "city": client_profile.get("city") if client_profile else None,
        "emergency_contact": client_profile.get("emergency_contact") if client_profile else None,
        "emergency_contact_relation": client_profile.get("emergency_contact_relation") if client_profile else None,
        "referred_by": client_profile.get("referred_by") if client_profile else None,
        "occupation": client_profile.get("occupation") if client_profile else None,
        "education": client_profile.get("education") if client_profile else None,
        "marital_status": client_profile.get("marital_status") if client_profile else None,
    }
    
    # Filter out None values
    basic_info = {k: v for k, v in basic_info.items() if v is not None}
    
    return {"basic_identification": basic_info}

@api_router.post("/case-history/{client_id}/sync-to-profile")
async def sync_case_history_to_profile(client_id: str, current_user: dict = Depends(require_active_therapist)):
    """Sync Basic Identification from Case History back to Client Profile"""
    therapist_id = current_user["id"]
    
    # Get case history
    case_history = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0, "basic_identification": 1}
    )
    
    if not case_history:
        raise HTTPException(status_code=404, detail="Case history not found")
    
    basic_info = case_history.get("basic_identification", {})
    
    # Update client profile with relevant fields
    profile_updates = {}
    
    if basic_info.get("dob"):
        profile_updates["dob"] = basic_info["dob"]
    if basic_info.get("gender"):
        profile_updates["gender"] = basic_info["gender"]
    if basic_info.get("address"):
        profile_updates["address"] = basic_info["address"]
    if basic_info.get("city"):
        profile_updates["city"] = basic_info["city"]
    if basic_info.get("emergency_contact"):
        profile_updates["emergency_contact"] = basic_info["emergency_contact"]
    if basic_info.get("emergency_contact_relation"):
        profile_updates["emergency_contact_relation"] = basic_info["emergency_contact_relation"]
    if basic_info.get("referred_by"):
        profile_updates["referred_by"] = basic_info["referred_by"]
    if basic_info.get("occupation"):
        profile_updates["occupation"] = basic_info["occupation"]
    if basic_info.get("education"):
        profile_updates["education"] = basic_info["education"]
    if basic_info.get("marital_status"):
        profile_updates["marital_status"] = basic_info["marital_status"]
    
    if profile_updates:
        profile_updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.client_profiles.update_one(
            {"user_id": client_id, "therapist_id": therapist_id},
            {"$set": profile_updates}
        )
    
    # Also update user's full_name if changed
    if basic_info.get("name"):
        await db.users.update_one(
            {"id": client_id},
            {"$set": {"full_name": basic_info["name"]}}
        )
    
    return {"message": "Client profile synced successfully", "updated_fields": list(profile_updates.keys())}

# ============= THERAPY CONSENT ENDPOINTS =============

@api_router.get("/therapy-consent/{client_id}", response_model=TherapyConsent)
async def get_therapy_consent(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get therapy consent for a client - Therapist or Client can view"""
    if current_user["role"] == "therapist":
        therapist_id = current_user["id"]
    elif current_user["role"] == "client":
        # Client can only view their own consent
        if current_user["id"] != client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        # Get therapist_id from client_profile
        profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0, "therapist_id": 1})
        if not profile:
            raise HTTPException(status_code=404, detail="Client profile not found")
        therapist_id = profile["therapist_id"]
    else:
        raise HTTPException(status_code=403, detail="Only therapists and clients can view consent")
    
    consent = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not consent:
        raise HTTPException(status_code=404, detail="Therapy consent not found. Case history may not be complete.")
    
    return TherapyConsent(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at", "signed_at"] and v else v for k, v in consent.items()})

@api_router.get("/therapy-consent/check/{client_id}")
async def check_therapy_consent(client_id: str, current_user: dict = Depends(get_current_user)):
    """Check if therapy consent exists and is signed"""
    if current_user["role"] == "therapist":
        therapist_id = current_user["id"]
    elif current_user["role"] == "client":
        if current_user["id"] != client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0, "therapist_id": 1})
        if not profile:
            return {"exists": False, "is_signed": False}
        therapist_id = profile["therapist_id"]
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    consent = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0, "id": 1, "is_signed": 1, "signature_method": 1}
    )
    
    return {
        "exists": consent is not None,
        "is_signed": consent.get("is_signed", False) if consent else False,
        "signature_method": consent.get("signature_method") if consent else None,
        "consent_id": consent.get("id") if consent else None
    }

@api_router.post("/therapy-consent/{client_id}/sign")
async def sign_therapy_consent(client_id: str, signature_method: str, current_user: dict = Depends(get_current_user)):
    """Sign therapy consent - Client signs digitally or Therapist marks as signed offline"""
    if signature_method not in ["digital", "paper"]:
        raise HTTPException(status_code=400, detail="Signature method must be 'digital' or 'paper'")
    
    if current_user["role"] == "client":
        # Client can only sign their own consent digitally
        if current_user["id"] != client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if signature_method != "digital":
            raise HTTPException(status_code=400, detail="Clients can only sign digitally")
        
        profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0, "therapist_id": 1})
        if not profile:
            raise HTTPException(status_code=404, detail="Client profile not found")
        therapist_id = profile["therapist_id"]
    elif current_user["role"] == "therapist":
        # Therapist can mark as signed (paper) for their clients
        therapist_id = current_user["id"]
    else:
        raise HTTPException(status_code=403, detail="Only therapists and clients can sign consent")
    
    consent = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not consent:
        raise HTTPException(status_code=404, detail="Therapy consent not found")
    
    if consent.get("is_signed"):
        raise HTTPException(status_code=400, detail="Consent is already signed")
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db.therapy_consents.update_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"$set": {
            "is_signed": True,
            "signature_method": signature_method,
            "signed_at": now,
            "updated_at": now
        }}
    )
    
    return {
        "message": "Consent signed successfully",
        "signature_method": signature_method,
        "signed_at": now
    }

@api_router.post("/therapy-consent/{client_id}/regenerate")
async def regenerate_therapy_consent(client_id: str, current_user: dict = Depends(require_active_therapist)):
    """Regenerate consent text (only if not yet signed)"""
    therapist_id = current_user["id"]
    
    consent = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not consent:
        raise HTTPException(status_code=404, detail="Therapy consent not found")
    
    if consent.get("is_signed"):
        raise HTTPException(status_code=400, detail="Cannot regenerate consent that is already signed")
    
    # Get names
    client_user = await db.users.find_one({"id": client_id}, {"_id": 0, "full_name": 1})
    therapist_user = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
    
    client_name = client_user.get("full_name", "Client") if client_user else "Client"
    therapist_name = therapist_user.get("full_name", "Therapist") if therapist_user else "Therapist"
    
    # Regenerate consent text
    consent_text = CONSENT_TEXT_TEMPLATE.format(
        client_name=client_name,
        therapist_name=therapist_name,
        date=datetime.now(IST).strftime("%d/%m/%Y")
    )
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db.therapy_consents.update_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"$set": {
            "consent_text": consent_text,
            "client_name": client_name,
            "therapist_name": therapist_name,
            "updated_at": now
        }}
    )
    
    return {"message": "Consent text regenerated", "updated_at": now}

# ============= SESSION NOTES ENDPOINTS =============

@api_router.post("/session-notes", response_model=SessionNote)
async def create_session_note(note_data: SessionNoteCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a new session note - Requires completed case history and signed consent"""
    # Check if case history exists and is complete
    case_history = await db.case_histories.find_one(
        {"client_id": note_data.client_id, "therapist_id": current_user["id"]},
        {"_id": 0, "is_complete": 1}
    )
    
    if not case_history:
        raise HTTPException(
            status_code=400, 
            detail="Case history must be completed before creating session notes. Please complete the initial case history first."
        )
    
    if not case_history.get("is_complete", False):
        raise HTTPException(
            status_code=400, 
            detail="Case history is incomplete. Please complete all required sections and mark it as complete before creating session notes."
        )
    
    # Check if therapy consent is signed
    consent = await db.therapy_consents.find_one(
        {"client_id": note_data.client_id, "therapist_id": current_user["id"]},
        {"_id": 0, "is_signed": 1}
    )
    
    if not consent or not consent.get("is_signed", False):
        raise HTTPException(
            status_code=400,
            detail="Therapy consent must be signed before creating session notes. Please ensure the client has signed the consent form."
        )
    
    # Find client in clients collection first, then users
    client = await db.clients.find_one({"id": note_data.client_id}, {"_id": 0})
    if not client:
        client = await db.users.find_one({"id": note_data.client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify client belongs to this therapist
    if client.get("therapist_id") and client["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Client is not assigned to you")
    
    # If linked to appointment, verify appointment exists and belongs to therapist
    appointment_date = None
    if note_data.appointment_id:
        appointment = await db.appointments.find_one({"id": note_data.appointment_id}, {"_id": 0})
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if appointment["therapist_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Appointment does not belong to you")
        if appointment["client_id"] != note_data.client_id:
            raise HTTPException(status_code=400, detail="Appointment client does not match selected client")
        appointment_date = appointment["start_time"]
    
    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    note_doc = {
        "id": note_id,
        "therapist_id": current_user["id"],
        "client_id": note_data.client_id,
        "client_name": client["full_name"],
        "appointment_id": note_data.appointment_id,
        "appointment_date": appointment_date,
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
async def get_session_notes(client_id: Optional[str] = None, appointment_id: Optional[str] = None, current_user: dict = Depends(require_therapist)):
    """Get session notes - therapists only see their own notes"""
    query = {"therapist_id": current_user["id"]}
    if client_id:
        query["client_id"] = client_id
    if appointment_id:
        query["appointment_id"] = appointment_id
    
    notes = await db.session_notes.find(query, {"_id": 0}).to_list(1000)
    return [SessionNote(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in note.items()}) for note in notes]

@api_router.get("/session-notes/{note_id}", response_model=SessionNote)
async def get_session_note(note_id: str, current_user: dict = Depends(require_therapist)):
    """Get a single session note by ID"""
    note = await db.session_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    # Verify ownership
    if note["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return SessionNote(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in note.items()})

@api_router.put("/session-notes/{note_id}", response_model=SessionNote)
async def update_session_note(note_id: str, update_data: SessionNoteUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update a session note - respects subscription read-only mode"""
    note = await db.session_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    # Verify ownership - only the therapist who created the note can edit
    if note["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied - only the note creator can edit")
    
    # Build update fields
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if update_data.template_type is not None:
        update_fields["template_type"] = update_data.template_type
    if update_data.subjective is not None:
        update_fields["subjective"] = update_data.subjective
    if update_data.objective is not None:
        update_fields["objective"] = update_data.objective
    if update_data.assessment is not None:
        update_fields["assessment"] = update_data.assessment
    if update_data.plan is not None:
        update_fields["plan"] = update_data.plan
    if update_data.data is not None:
        update_fields["data"] = update_data.data
    
    await db.session_notes.update_one({"id": note_id}, {"$set": update_fields})
    await log_audit(current_user["id"], current_user["role"], "update", "session_note", note_id)
    
    updated = await db.session_notes.find_one({"id": note_id}, {"_id": 0})
    return SessionNote(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in updated.items()})

@api_router.delete("/session-notes/{note_id}")
async def delete_session_note(note_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a session note - respects subscription read-only mode"""
    note = await db.session_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    # Verify ownership
    if note["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.session_notes.delete_one({"id": note_id})
    await log_audit(current_user["id"], current_user["role"], "delete", "session_note", note_id)
    
    return {"message": "Session note deleted"}

# ============= NOTE TEMPLATES ENDPOINTS =============

@api_router.post("/note-templates", response_model=NoteTemplate)
async def create_note_template(template_data: NoteTemplateCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a new note template (quick-insert phrase)"""
    if not template_data.name or not template_data.content:
        raise HTTPException(status_code=400, detail="Name and content are required")
    
    template_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    template_doc = {
        "id": template_id,
        "therapist_id": current_user["id"],
        "name": template_data.name,
        "category": template_data.category,
        "content": template_data.content,
        "usage_count": 0,
        "created_at": now,
        "updated_at": now
    }
    
    await db.note_templates.insert_one(template_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "note_template", template_id)
    
    return NoteTemplate(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in template_doc.items()})

@api_router.get("/note-templates", response_model=List[NoteTemplate])
async def get_note_templates(category: Optional[str] = None, current_user: dict = Depends(require_therapist)):
    """Get all note templates for the therapist"""
    query = {"therapist_id": current_user["id"]}
    if category:
        query["category"] = category
    
    templates = await db.note_templates.find(query, {"_id": 0}).sort("usage_count", -1).to_list(100)
    
    return [NoteTemplate(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in t.items()}) for t in templates]

@api_router.put("/note-templates/{template_id}", response_model=NoteTemplate)
async def update_note_template(template_id: str, update_data: NoteTemplateUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update a note template"""
    template = await db.note_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if update_data.name is not None:
        update_fields["name"] = update_data.name
    if update_data.category is not None:
        update_fields["category"] = update_data.category
    if update_data.content is not None:
        update_fields["content"] = update_data.content
    
    await db.note_templates.update_one({"id": template_id}, {"$set": update_fields})
    
    updated = await db.note_templates.find_one({"id": template_id}, {"_id": 0})
    return NoteTemplate(**{k: datetime.fromisoformat(v) if k in ["created_at", "updated_at"] else v for k, v in updated.items()})

@api_router.delete("/note-templates/{template_id}")
async def delete_note_template(template_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a note template"""
    template = await db.note_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.note_templates.delete_one({"id": template_id})
    await log_audit(current_user["id"], current_user["role"], "delete", "note_template", template_id)
    
    return {"message": "Template deleted"}

@api_router.post("/note-templates/{template_id}/use")
async def use_note_template(template_id: str, current_user: dict = Depends(require_therapist)):
    """Increment usage count when a template is used"""
    template = await db.note_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.note_templates.update_one(
        {"id": template_id},
        {"$inc": {"usage_count": 1}}
    )
    
    return {"message": "Template usage recorded", "content": template["content"]}

# ============= RECURRING APPOINTMENTS ENDPOINTS =============

@api_router.post("/recurring-appointments", response_model=RecurringPattern)
async def create_recurring_pattern(pattern_data: RecurringPatternCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a recurring appointment pattern"""
    # Validate day of week
    if pattern_data.day_of_week < 0 or pattern_data.day_of_week > 6:
        raise HTTPException(status_code=400, detail="day_of_week must be 0-6 (Monday-Sunday)")
    
    # Find client
    client = await db.clients.find_one({"id": pattern_data.client_id}, {"_id": 0})
    if not client:
        client = await db.users.find_one({"id": pattern_data.client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify client belongs to therapist
    if client.get("therapist_id") and client["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Client is not assigned to you")
    
    pattern_id = str(uuid.uuid4())
    pattern_doc = {
        "id": pattern_id,
        "therapist_id": current_user["id"],
        "client_id": pattern_data.client_id,
        "client_name": client["full_name"],
        "day_of_week": pattern_data.day_of_week,
        "start_time": pattern_data.start_time,
        "end_time": pattern_data.end_time,
        "notes": pattern_data.notes,
        "start_date": pattern_data.start_date,
        "end_date": pattern_data.end_date,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.recurring_patterns.insert_one(pattern_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "recurring_pattern", pattern_id)
    
    return RecurringPattern(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in pattern_doc.items()})

@api_router.get("/recurring-appointments", response_model=List[RecurringPattern])
async def get_recurring_patterns(current_user: dict = Depends(require_therapist)):
    """Get all recurring appointment patterns for the therapist"""
    patterns = await db.recurring_patterns.find(
        {"therapist_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    return [RecurringPattern(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in p.items()}) for p in patterns]

@api_router.delete("/recurring-appointments/{pattern_id}")
async def delete_recurring_pattern(pattern_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a recurring appointment pattern"""
    pattern = await db.recurring_patterns.find_one({"id": pattern_id}, {"_id": 0})
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    
    if pattern["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.recurring_patterns.delete_one({"id": pattern_id})
    await log_audit(current_user["id"], current_user["role"], "delete", "recurring_pattern", pattern_id)
    
    return {"message": "Recurring pattern deleted"}

@api_router.post("/recurring-appointments/{pattern_id}/generate")
async def generate_recurring_appointments(
    pattern_id: str,
    weeks_ahead: int = 4,
    current_user: dict = Depends(require_active_therapist)
):
    """Generate appointments from a recurring pattern for the next N weeks"""
    pattern = await db.recurring_patterns.find_one({"id": pattern_id}, {"_id": 0})
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    
    if pattern["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not pattern.get("is_active", True):
        raise HTTPException(status_code=400, detail="Pattern is not active")
    
    # Find client
    client = await db.clients.find_one({"id": pattern["client_id"]}, {"_id": 0})
    if not client:
        client = await db.users.find_one({"id": pattern["client_id"]}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Generate appointments
    created_appointments = []
    today = datetime.now(timezone.utc).date()
    start_date = datetime.strptime(pattern["start_date"], "%Y-%m-%d").date()
    end_date = None
    if pattern.get("end_date"):
        end_date = datetime.strptime(pattern["end_date"], "%Y-%m-%d").date()
    
    # Start from today or start_date, whichever is later
    current_date = max(today, start_date)
    
    # Find the next occurrence of the target day
    days_ahead = (pattern["day_of_week"] - current_date.weekday()) % 7
    if days_ahead == 0 and current_date == today:
        days_ahead = 7  # Skip today, start next week
    current_date = current_date + timedelta(days=days_ahead)
    
    for week in range(weeks_ahead):
        if end_date and current_date > end_date:
            break
        
        # Parse times
        start_time_parts = pattern["start_time"].split(":")
        end_time_parts = pattern["end_time"].split(":")
        
        appt_start = datetime.combine(
            current_date,
            datetime.strptime(pattern["start_time"], "%H:%M").time()
        ).replace(tzinfo=timezone.utc)
        
        appt_end = datetime.combine(
            current_date,
            datetime.strptime(pattern["end_time"], "%H:%M").time()
        ).replace(tzinfo=timezone.utc)
        
        # Check for existing appointment at this time
        existing = await db.appointments.find_one({
            "therapist_id": current_user["id"],
            "status": {"$ne": "cancelled"},
            "start_time": appt_start.isoformat()
        })
        
        if not existing:
            appt_id = str(uuid.uuid4())
            appt_doc = {
                "id": appt_id,
                "therapist_id": current_user["id"],
                "client_id": pattern["client_id"],
                "client_name": client["full_name"],
                "start_time": appt_start.isoformat(),
                "end_time": appt_end.isoformat(),
                "notes": pattern.get("notes", ""),
                "status": "scheduled",
                "recurring_pattern_id": pattern_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.appointments.insert_one(appt_doc)
            created_appointments.append(appt_doc)
        
        current_date = current_date + timedelta(days=7)
    
    return {
        "message": f"Generated {len(created_appointments)} appointments",
        "appointments_created": len(created_appointments)
    }

@api_router.put("/recurring-appointments/{pattern_id}/toggle")
async def toggle_recurring_pattern(pattern_id: str, current_user: dict = Depends(require_active_therapist)):
    """Toggle a recurring pattern active/inactive"""
    pattern = await db.recurring_patterns.find_one({"id": pattern_id}, {"_id": 0})
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    
    if pattern["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    new_status = not pattern.get("is_active", True)
    await db.recurring_patterns.update_one(
        {"id": pattern_id},
        {"$set": {"is_active": new_status}}
    )
    
    return {"message": f"Pattern {'activated' if new_status else 'deactivated'}", "is_active": new_status}

# ============= MESSAGING ENDPOINTS =============

async def verify_messaging_allowed(sender_id: str, sender_role: str, recipient_id: str) -> tuple:
    """Verify that messaging is allowed between two users.
    Returns (is_allowed, error_message, recipient_doc)
    """
    # Find recipient in users collection
    recipient = await db.users.find_one({"id": recipient_id}, {"_id": 0})
    
    if not recipient:
        return False, "Recipient not found", None
    
    recipient_role = recipient.get("role", "client")
    
    # Therapists can only message their assigned clients
    if sender_role == "therapist":
        if recipient_role != "client":
            return False, "Therapists can only message their assigned clients", None
        
        # Check if client is assigned to this therapist via client_profiles
        profile = await db.client_profiles.find_one({"user_id": recipient_id, "therapist_id": sender_id}, {"_id": 0})
        if not profile:
            return False, "This client is not assigned to you", None
        
        # Check if messaging is enabled for this client
        if not profile.get("messaging_enabled", True):
            return False, "Messaging is disabled for this client", None
    
    # Clients can only message their assigned therapist
    if sender_role == "client":
        # Get client's profile to find their therapist
        sender_profile = await db.client_profiles.find_one({"user_id": sender_id}, {"_id": 0})
        
        if not sender_profile:
            return False, "Client profile not found", None
        
        if recipient_id != sender_profile.get("therapist_id"):
            return False, "You can only message your assigned therapist", None
        
        # Check if messaging is enabled for this client
        if not sender_profile.get("messaging_enabled", True):
            return False, "Messaging has been disabled by your therapist", None
    
    return True, None, recipient

@api_router.post("/messages", response_model=Message)
async def send_message(msg_data: MessageCreate, current_user: dict = Depends(get_current_user)):
    """Send a message - enforces therapist-client relationship"""
    # Therapists need active subscription to send messages
    if current_user["role"] == "therapist" and not is_subscription_active(current_user):
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. You are in read-only mode. Please renew to send messages."
        )
    
    # Verify messaging is allowed
    is_allowed, error_msg, recipient = await verify_messaging_allowed(
        current_user["id"], 
        current_user["role"], 
        msg_data.recipient_id
    )
    
    if not is_allowed:
        raise HTTPException(status_code=403, detail=error_msg)
    
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
    """Get messages with a specific user"""
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
    """Get all conversations for the current user"""
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

@api_router.get("/messaging-contacts")
async def get_messaging_contacts(current_user: dict = Depends(get_current_user)):
    """Get list of users the current user can message"""
    # Assistants cannot access messaging
    if current_user["role"] == "assistant":
        raise HTTPException(status_code=403, detail="Assistants cannot access messaging")
    
    contacts = []
    
    if current_user["role"] == "therapist":
        # Get all client profiles assigned to this therapist
        client_profiles = await db.client_profiles.find(
            {"therapist_id": current_user["id"], "messaging_enabled": {"$ne": False}},
            {"_id": 0}
        ).to_list(1000)
        
        for profile in client_profiles:
            # Get user data for each client
            client_user = await db.users.find_one(
                {"id": profile["user_id"], "role": "client"},
                {"_id": 0, "id": 1, "full_name": 1, "client_id": 1}
            )
            if client_user:
                contacts.append({
                    "id": client_user["id"],
                    "name": client_user["full_name"],
                    "display_id": client_user.get("client_id", ""),
                    "photo": profile.get("profile_photo"),
                    "type": "client"
                })
    
    elif current_user["role"] == "client":
        # Get client profile to find therapist
        client_profile = await db.client_profiles.find_one({"user_id": current_user["id"]}, {"_id": 0})
        
        if client_profile and client_profile.get("therapist_id"):
            therapist = await db.users.find_one(
                {"id": client_profile["therapist_id"]},
                {"_id": 0, "id": 1, "full_name": 1, "credentials": 1, "profile_photo": 1}
            )
            if therapist:
                contacts.append({
                    "id": therapist["id"],
                    "name": therapist["full_name"],
                    "display_id": therapist.get("credentials", ""),
                    "photo": therapist.get("profile_photo"),
                    "type": "therapist"
                })
    
    return contacts

@api_router.put("/clients/{client_id}/messaging")
async def toggle_client_messaging(
    client_id: str, 
    settings: ClientMessagingSettings, 
    current_user: dict = Depends(require_active_therapist)
):
    """Enable or disable messaging for a specific client"""
    # Find client profile
    profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify client is assigned to this therapist
    if profile.get("therapist_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="This client is not assigned to you")
    
    # Get client user for name
    client_user = await db.users.find_one({"id": client_id}, {"_id": 0, "full_name": 1})
    
    await db.client_profiles.update_one(
        {"user_id": client_id},
        {"$set": {"messaging_enabled": settings.messaging_enabled}}
    )
    
    status = "enabled" if settings.messaging_enabled else "disabled"
    await log_audit(current_user["id"], current_user["role"], f"messaging_{status}", "client", client_id)
    
    return {"message": f"Messaging {status} for {client_user['full_name'] if client_user else 'client'}"}

@api_router.get("/clients/{client_id}/messaging-status")
async def get_client_messaging_status(client_id: str, current_user: dict = Depends(require_therapist)):
    """Get messaging status for a specific client"""
    profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0, "messaging_enabled": 1})
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {
        "client_id": client_id,
        "messaging_enabled": profile.get("messaging_enabled", True)
    }

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
async def get_assessments(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    # Assistants cannot access clinical data
    if current_user["role"] == "assistant":
        raise HTTPException(status_code=403, detail="Assistants cannot access assessments")
    
    query = {}
    if current_user["role"] == "therapist":
        query["therapist_id"] = current_user["id"]
        if client_id:
            query["client_id"] = client_id
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
async def get_homework(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "therapist":
        query["therapist_id"] = current_user["id"]
        if client_id:
            query["client_id"] = client_id
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

# ============= AI CLINICAL SUPPORT ENDPOINTS =============

# Standard assessments for reference
STANDARD_ASSESSMENTS = {
    "PHQ-9": {"name": "Patient Health Questionnaire-9", "conditions": ["depression", "mood disorders"]},
    "GAD-7": {"name": "Generalized Anxiety Disorder-7", "conditions": ["anxiety", "worry", "nervousness"]},
    "PCL-5": {"name": "PTSD Checklist for DSM-5", "conditions": ["trauma", "PTSD", "flashbacks"]},
    "ASRS": {"name": "Adult ADHD Self-Report Scale", "conditions": ["ADHD", "attention", "focus"]},
    "BDI-II": {"name": "Beck Depression Inventory-II", "conditions": ["depression", "hopelessness"]},
    "DASS-21": {"name": "Depression Anxiety Stress Scales", "conditions": ["depression", "anxiety", "stress"]},
    "YBOCS": {"name": "Yale-Brown Obsessive Compulsive Scale", "conditions": ["OCD", "obsessions", "compulsions"]},
    "PSS": {"name": "Perceived Stress Scale", "conditions": ["stress", "overwhelm", "coping"]}
}

async def get_ai_chat(session_id: str, system_message: str):
    """Initialize AI chat with Gemini 3 Flash"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message
    ).with_model("gemini", "gemini-3-flash-preview")
    
    return chat

@api_router.post("/ai/suggest-assessments", response_model=AIAssessmentSuggestionResponse)
async def ai_suggest_assessments(request: AIAssessmentSuggestionRequest, current_user: dict = Depends(require_active_therapist)):
    """AI-powered assessment suggestion based on client data and/or therapist query"""
    therapist_id = current_user["id"]
    data_sources = []
    client_context = ""
    
    # Gather client data if client_id provided
    if request.client_id:
        # Get client profile - client_id is the user_id from users collection
        client_profile = await db.client_profiles.find_one(
            {"user_id": request.client_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
        if not client_profile:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get client user info for name
        client_user = await db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1})
        client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
        
        client_context += f"Client: {client_name}\n"
        
        if request.include_intake and client_profile.get("intake_summary"):
            client_context += f"Intake Summary: {client_profile['intake_summary']}\n"
            data_sources.append("intake_summary")
        
        # Get recent session notes
        if request.include_notes:
            notes = await db.session_notes.find(
                {"therapist_id": therapist_id, "client_id": request.client_id},
                {"_id": 0, "subjective": 1, "objective": 1, "assessment": 1, "data": 1, "created_at": 1}
            ).sort("created_at", -1).to_list(5)
            
            if notes:
                client_context += "\nRecent Session Notes:\n"
                for i, note in enumerate(notes):
                    note_text = ""
                    if note.get("subjective"):
                        note_text += f"Subjective: {note['subjective'][:500]}\n"
                    if note.get("assessment"):
                        note_text += f"Assessment: {note['assessment'][:500]}\n"
                    if note.get("data"):
                        note_text += f"Data: {note['data'][:500]}\n"
                    if note_text:
                        client_context += f"Note {i+1}: {note_text}\n"
                data_sources.append("session_notes")
        
        # Get completed assessments
        completed_assessments = await db.assessments.find(
            {"therapist_id": therapist_id, "client_id": request.client_id, "status": "completed"},
            {"_id": 0, "assessment_type": 1, "score": 1}
        ).to_list(20)
        
        if completed_assessments:
            client_context += "\nPreviously Completed Assessments:\n"
            for a in completed_assessments:
                client_context += f"- {a['assessment_type']}: Score {a.get('score', 'N/A')}\n"
            data_sources.append("previous_assessments")
    
    # Add therapist's manual query
    if request.query:
        client_context += f"\nTherapist's Observation/Query: {request.query}\n"
        data_sources.append("therapist_query")
    
    if not client_context.strip():
        raise HTTPException(status_code=400, detail="Please provide client_id or a query")
    
    # Prepare AI prompt
    assessments_list = "\n".join([f"- {k}: {v['name']} (for {', '.join(v['conditions'])})" for k, v in STANDARD_ASSESSMENTS.items()])
    
    system_prompt = f"""You are a clinical psychology assessment consultant. Your role is to suggest appropriate standardized assessments based on client information.

Available Assessments:
{assessments_list}

Important Guidelines:
1. Suggest assessments that would provide valuable clinical information
2. Prioritize based on presenting concerns
3. Consider what assessments have already been completed
4. Provide clear rationale for each suggestion
5. Be specific about which symptoms/concerns each assessment would address

Respond in valid JSON format only with this structure:
{{
    "analysis_summary": "Brief summary of clinical observations",
    "suggestions": [
        {{
            "assessment_name": "Full assessment name",
            "assessment_type": "Assessment code (e.g., PHQ-9)",
            "reason": "Why this assessment is recommended",
            "priority": "high/medium/low",
            "relevant_symptoms": ["symptom1", "symptom2"]
        }}
    ]
}}"""

    try:
        chat = await get_ai_chat(f"assessment-{therapist_id}-{uuid.uuid4()}", system_prompt)
        user_message = UserMessage(text=f"Based on the following client information, suggest appropriate clinical assessments:\n\n{client_context}")
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        
        return AIAssessmentSuggestionResponse(
            suggestions=[AIAssessmentSuggestion(**s) for s in result.get("suggestions", [])],
            analysis_summary=result.get("analysis_summary", ""),
            data_sources_used=data_sources
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI response parsing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@api_router.post("/ai/generate-protocol", response_model=AIProtocolResponse)
async def ai_generate_protocol(request: AIProtocolRequest, current_user: dict = Depends(require_active_therapist)):
    """AI-powered therapy protocol generation"""
    therapist_id = current_user["id"]
    context = ""
    
    # Gather client information
    if request.client_id:
        client_profile = await db.client_profiles.find_one(
            {"user_id": request.client_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
        if not client_profile:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get client user info for name
        client_user = await db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1})
        client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
        
        context += f"Client: {client_name}\n"
        if client_profile.get("intake_summary"):
            context += f"Intake: {client_profile['intake_summary']}\n"
    
    # Get assessment results if provided
    if request.assessment_ids:
        assessments = await db.assessments.find(
            {"id": {"$in": request.assessment_ids}, "therapist_id": therapist_id, "status": "completed"},
            {"_id": 0}
        ).to_list(10)
        
        if assessments:
            context += "\nAssessment Results:\n"
            for a in assessments:
                context += f"- {a['assessment_type']}: Score {a.get('score', 'N/A')}\n"
    
    # Add therapist's description
    if request.query:
        context += f"\nTherapist's Description: {request.query}\n"
    
    if request.modality_preference:
        context += f"\nPreferred Modality: {request.modality_preference}\n"
    
    if not context.strip():
        raise HTTPException(status_code=400, detail="Please provide client_id, assessment_ids, or a query")
    
    system_prompt = """You are an expert clinical psychologist specializing in treatment planning. Generate evidence-based therapy protocols.

Modalities you can recommend: CBT (Cognitive Behavioral Therapy), DBT (Dialectical Behavior Therapy), ACT (Acceptance and Commitment Therapy), EMDR, Psychodynamic, Interpersonal Therapy, Mindfulness-Based.

Important Guidelines:
1. Create structured, session-by-session treatment plans
2. Include specific interventions and techniques
3. Provide homework assignments for each session
4. Note any contraindications or special considerations
5. Include measurable progress markers

Respond in valid JSON format only:
{
    "protocol_name": "Name of the protocol",
    "target_condition": "Primary condition being addressed",
    "recommended_modality": "CBT/DBT/ACT/etc",
    "rationale": "Why this approach is recommended",
    "estimated_sessions": 8,
    "sessions": [
        {
            "session_number": 1,
            "title": "Session title",
            "objectives": ["objective1", "objective2"],
            "interventions": ["intervention1", "intervention2"],
            "homework": "Homework assignment",
            "duration_minutes": 60
        }
    ],
    "contraindications": ["If any"],
    "progress_markers": ["marker1", "marker2"]
}"""

    try:
        chat = await get_ai_chat(f"protocol-{therapist_id}-{uuid.uuid4()}", system_prompt)
        user_message = UserMessage(text=f"Generate a therapy protocol based on:\n\n{context}")
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        
        return AIProtocolResponse(
            protocol_name=result.get("protocol_name", ""),
            target_condition=result.get("target_condition", ""),
            recommended_modality=result.get("recommended_modality", ""),
            rationale=result.get("rationale", ""),
            estimated_sessions=result.get("estimated_sessions", 8),
            sessions=[AIProtocolSession(**s) for s in result.get("sessions", [])],
            contraindications=result.get("contraindications"),
            progress_markers=result.get("progress_markers", [])
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI response parsing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@api_router.post("/ai/generate-homework", response_model=AIHomeworkResponse)
async def ai_generate_homework(request: AIHomeworkRequest, current_user: dict = Depends(require_active_therapist)):
    """AI-powered homework/worksheet generation"""
    therapist_id = current_user["id"]
    
    # Get client info - client_id is the user_id from users collection
    client_profile = await db.client_profiles.find_one(
        {"user_id": request.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client user info for name
    client_user = await db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
    
    context = f"Client: {client_name}\n"
    
    # Get recent session notes for context
    recent_note = await db.session_notes.find_one(
        {"therapist_id": therapist_id, "client_id": request.client_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if recent_note:
        if recent_note.get("plan"):
            context += f"Recent Session Plan: {recent_note['plan'][:500]}\n"
        if recent_note.get("assessment"):
            context += f"Recent Assessment: {recent_note['assessment'][:500]}\n"
    
    # Get protocol if provided
    if request.protocol_id:
        protocol = await db.protocols.find_one(
            {"id": request.protocol_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
        if protocol:
            context += f"Current Protocol: {protocol.get('modality', '')} for {protocol.get('condition', '')}\n"
    
    if request.context:
        context += f"Session Context: {request.context}\n"
    
    homework_type = request.homework_type or "exercise"
    
    system_prompt = f"""You are a clinical psychologist creating therapeutic homework assignments. 
The homework type requested is: {homework_type}

Types of homework:
- worksheet: Structured forms with questions for self-reflection
- exercise: Behavioral or cognitive exercises to practice
- reading: Psychoeducational material to read
- reflection: Journaling or reflection prompts
- meditation: Mindfulness or relaxation exercises

Guidelines:
1. Make it specific and actionable
2. Include clear step-by-step instructions
3. Keep it achievable (15-30 minutes typically)
4. Explain the therapeutic purpose
5. Make it relevant to the client's concerns

Respond in valid JSON format only:
{{
    "title": "Homework title",
    "description": "Brief description",
    "instructions": "Detailed instructions for the client",
    "exercises": [
        {{
            "name": "Exercise name",
            "description": "What to do",
            "steps": ["step1", "step2", "step3"]
        }}
    ],
    "estimated_time_minutes": 20,
    "therapeutic_rationale": "Why this homework will help"
}}"""

    try:
        chat = await get_ai_chat(f"homework-{therapist_id}-{uuid.uuid4()}", system_prompt)
        user_message = UserMessage(text=f"Generate therapeutic homework based on:\n\n{context}")
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        
        return AIHomeworkResponse(
            title=result.get("title", ""),
            description=result.get("description", ""),
            instructions=result.get("instructions", ""),
            exercises=result.get("exercises", []),
            estimated_time_minutes=result.get("estimated_time_minutes", 20),
            therapeutic_rationale=result.get("therapeutic_rationale", "")
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI response parsing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

# ============= RESOURCE LIBRARY ENDPOINTS =============

@api_router.post("/resources", response_model=Resource)
async def create_resource(resource: ResourceCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a new resource in the library"""
    resource_doc = {
        "id": str(uuid.uuid4()),
        "therapist_id": current_user["id"],
        "title": resource.title,
        "category": resource.category,
        "content": resource.content,
        "tags": resource.tags,
        "is_downloadable": resource.is_downloadable,
        "usage_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.resources.insert_one(resource_doc)
    
    return Resource(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in resource_doc.items()})

@api_router.get("/resources", response_model=List[Resource])
async def get_resources(category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all resources (therapist's own + system resources)"""
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    therapist_id = current_user["id"] if current_user["role"] == "therapist" else current_user.get("therapist_id")
    
    query = {"$or": [{"therapist_id": therapist_id}, {"therapist_id": "system"}]}
    if category:
        query["category"] = category
    
    resources = await db.resources.find(query, {"_id": 0}).sort("usage_count", -1).to_list(500)
    return [Resource(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in r.items()}) for r in resources]

@api_router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a resource"""
    result = await db.resources.delete_one({"id": resource_id, "therapist_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found or you don't have permission")
    return {"message": "Resource deleted"}

@api_router.post("/resources/{resource_id}/assign")
async def assign_resource(resource_id: str, client_id: str, notes: Optional[str] = None, current_user: dict = Depends(require_active_therapist)):
    """Assign a resource to a client"""
    therapist_id = current_user["id"]
    
    # Verify resource exists
    resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Verify client belongs to therapist - client_id is the user_id from users collection
    client_profile = await db.client_profiles.find_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client user info for name
    client_user = await db.users.find_one({"id": client_id}, {"_id": 0, "full_name": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
    
    assignment_doc = {
        "id": str(uuid.uuid4()),
        "therapist_id": therapist_id,
        "client_id": client_id,
        "client_name": client_name,
        "resource_id": resource_id,
        "resource_title": resource["title"],
        "notes": notes,
        "status": "assigned",
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "viewed_at": None,
        "completed_at": None
    }
    
    await db.resource_assignments.insert_one(assignment_doc)
    
    # Increment usage count
    await db.resources.update_one({"id": resource_id}, {"$inc": {"usage_count": 1}})
    
    return {"message": "Resource assigned", "assignment_id": assignment_doc["id"]}

@api_router.get("/resources/assignments", response_model=List[ResourceAssignment])
async def get_resource_assignments(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get resource assignments"""
    if current_user["role"] == "therapist":
        query = {"therapist_id": current_user["id"]}
    elif current_user["role"] == "assistant":
        query = {"therapist_id": current_user.get("therapist_id")}
    elif current_user["role"] == "client":
        query = {"client_id": current_user["id"]}
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if client_id and current_user["role"] in ["therapist", "assistant"]:
        query["client_id"] = client_id
    
    assignments = await db.resource_assignments.find(query, {"_id": 0}).sort("assigned_at", -1).to_list(500)
    
    def parse_assignment(a):
        for k in ["assigned_at", "viewed_at", "completed_at"]:
            if a.get(k):
                a[k] = datetime.fromisoformat(a[k])
        return ResourceAssignment(**a)
    
    return [parse_assignment(a) for a in assignments]

@api_router.post("/resources/assignments/{assignment_id}/view")
async def mark_resource_viewed(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a resource assignment as viewed (for clients)"""
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can mark resources as viewed")
    
    result = await db.resource_assignments.update_one(
        {"id": assignment_id, "client_id": current_user["id"]},
        {"$set": {"status": "viewed", "viewed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"message": "Marked as viewed"}

@api_router.post("/resources/assignments/{assignment_id}/complete")
async def mark_resource_completed(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a resource assignment as completed"""
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can mark resources as completed")
    
    result = await db.resource_assignments.update_one(
        {"id": assignment_id, "client_id": current_user["id"]},
        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"message": "Marked as completed"}

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
