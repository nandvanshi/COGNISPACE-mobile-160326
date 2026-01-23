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
from assessment_library import CLINICAL_ASSESSMENTS, calculate_score, get_severity, get_client_friendly_assessment, ASSESSMENT_CLIENT_INFO

# IST timezone for India Standard Time
IST = ZoneInfo("Asia/Kolkata")
import jwt
from bson import ObjectId

# Import route modules
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.assistants import router as assistants_router
from routes.subscriptions import router as subscriptions_router
from routes.clients import router as clients_router
from routes.appointments import router as appointments_router
from routes.availability import router as availability_router
from routes.payments import router as payments_router
from routes.sessions import router as sessions_router
from routes.assessments import router as assessments_router
from routes.clinical import router as clinical_router
from routes.assistant import router as assistant_dashboard_router
from routes.recurring import router as recurring_router
from routes.protocols import router as protocols_router
from routes.therapist_profile import router as therapist_profile_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AI/LLM Configuration
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Default feature toggles for all subscription plans (all features enabled by default)
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

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Include route modules
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(assistants_router)
api_router.include_router(subscriptions_router)
api_router.include_router(clients_router)
api_router.include_router(appointments_router)
api_router.include_router(availability_router)
api_router.include_router(payments_router)
api_router.include_router(sessions_router)
api_router.include_router(assessments_router)
api_router.include_router(clinical_router)
api_router.include_router(assistant_dashboard_router)
api_router.include_router(recurring_router)
api_router.include_router(protocols_router)
api_router.include_router(therapist_profile_router)

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
    status: Optional[Literal["scheduled", "in_progress", "completed", "cancelled"]] = None

class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    checked_in_by: Optional[str] = None
    checked_out_by: Optional[str] = None
    created_at: datetime

class CheckInRequest(BaseModel):
    notes: Optional[str] = None

class CheckOutRequest(BaseModel):
    notes: Optional[str] = None
    record_payment: bool = False
    payment_amount: Optional[float] = None
    payment_mode: Optional[Literal["cash", "upi", "card", "bank", "other"]] = None
    payment_status: Optional[Literal["paid", "partial", "pending"]] = None
    payment_notes: Optional[str] = None

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
    due_date: Optional[str] = None  # Optional due date in ISO format

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
    due_date: Optional[str] = None
    report_shared_with_client: Optional[bool] = False

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
    priority: str = "medium"  # low, medium, high

class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None

class Homework(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    title: str
    description: str
    due_date: Optional[datetime] = None
    priority: str = "medium"
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
    include_case_history: bool = True
    include_prev_assessments: bool = True

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
    include_case_history: bool = True
    include_prev_assessments: bool = True

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
    include_case_history: bool = True
    include_prev_assessments: bool = True

class AIHomeworkResponse(BaseModel):
    title: str
    description: str
    instructions: str
    exercises: List[dict]  # [{name, description, steps}]
    estimated_time_minutes: int
    therapeutic_rationale: str

# CogniVision Diagnostic Report Models
class DiagnosticReportRequest(BaseModel):
    client_id: str
    assessment_ids: List[str]  # Selected completed assessments
    include_intake: bool = True
    include_session_history: bool = True
    include_case_history: bool = True
    therapist_notes: Optional[str] = None  # Offline assessment data / additional input

class DiagnosticReportSection(BaseModel):
    title: str
    content: str

class DiagnosticReportResponse(BaseModel):
    header: str
    patient_identification: str
    referral_context: str
    assessment_battery: str
    psychometric_findings: str
    diagnostic_impression: str
    treatment_roadmap: str
    disclaimer: str
    raw_html: str  # Full formatted report

class DiagnosticReportCreate(BaseModel):
    client_id: str
    assessment_ids: List[str]
    report_content: str  # Rich text HTML content
    status: str = "draft"  # draft, approved, shared
    therapist_signature: Optional[str] = None
    therapist_reg_no: Optional[str] = None

class DiagnosticReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    assessment_ids: List[str]
    report_content: str
    status: str  # draft, approved, shared
    therapist_signature: Optional[str] = None
    therapist_reg_no: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    shared_at: Optional[datetime] = None

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
    payment_method: Literal["cash", "upi", "card", "bank", "bank_transfer", "credit_card", "cheque", "other"]
    payment_status: Literal["paid", "partial", "pending"] = "paid"
    appointment_id: Optional[str] = None
    session_note_id: Optional[str] = None
    notes: Optional[str] = None

class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    bill_number: str  # Unique bill/receipt number
    therapist_id: str
    therapist_name: Optional[str] = None
    client_id: str
    client_name: str
    client_code: Optional[str] = None  # Client ID like CL-123456
    amount: float
    payment_method: str  # cash, upi, card, bank, bank_transfer, credit_card, cheque, other
    payment_status: str = "paid"  # paid, partial, pending
    appointment_id: Optional[str] = None
    session_note_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

class PaymentReceipt(BaseModel):
    """Receipt data for PDF generation"""
    bill_number: str
    clinic_name: str
    therapist_name: str
    therapist_phone: Optional[str] = None
    therapist_email: Optional[str] = None
    client_name: str
    client_id: str  # CL-123456 format
    date: str
    time: str
    session_date: Optional[str] = None
    session_time: Optional[str] = None
    amount: float
    payment_method: str
    payment_status: str
    notes: Optional[str] = None

# Cash Settlement Models
class CashSettlementCreate(BaseModel):
    """Request to hand over cash"""
    note: Optional[str] = None

class CashSettlementDispute(BaseModel):
    """Request to dispute a settlement"""
    reason: str  # Required for disputes

class CashSettlement(BaseModel):
    """Cash settlement record"""
    model_config = ConfigDict(extra="ignore")
    id: str
    date: str  # YYYY-MM-DD format
    therapist_id: str
    therapist_name: str
    assistant_id: Optional[str] = None
    assistant_name: Optional[str] = None
    cash_amount: float  # Auto-calculated from payments
    online_amount: float  # Auto-calculated from payments
    total_amount: float
    status: Literal["pending", "handed_over", "settled", "disputed"] = "pending"
    handover_note: Optional[str] = None
    handover_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    confirmed_by: Optional[str] = None
    disputed_at: Optional[str] = None
    disputed_reason: Optional[str] = None
    created_at: str
    updated_at: str

# Support Ticket Models
class TicketReplyCreate(BaseModel):
    message: str

class TicketReply(BaseModel):
    id: str
    ticket_id: str
    message: str
    author_id: str
    author_name: str
    author_role: Literal["therapist", "super_admin"]
    created_at: str

class TicketCreate(BaseModel):
    subject: str
    category: Literal["technical", "billing", "subscription", "other"]
    description: str
    priority: Literal["low", "medium", "high"] = "medium"

class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "closed"]

class SupportTicket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    therapist_name: str
    therapist_email: Optional[str] = None
    subject: str
    category: Literal["technical", "billing", "subscription", "other"]
    description: str
    priority: Literal["low", "medium", "high"]
    status: Literal["open", "in_progress", "closed"] = "open"
    replies: List[TicketReply] = []
    created_at: str
    updated_at: str

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
    # Feature toggles - control what features are available in this plan
    feature_toggles: Optional[dict] = None  # {"session_notes": True, "assessments": True, ...}

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
        # Free trial gets all features
        return DEFAULT_FEATURE_TOGGLES
    
    plan = await db.subscription_plans.find_one({"id": subscription.get("plan_id")}, {"_id": 0})
    if not plan or not plan.get("feature_toggles"):
        return DEFAULT_FEATURE_TOGGLES
    
    return {**DEFAULT_FEATURE_TOGGLES, **plan.get("feature_toggles", {})}

async def check_feature_enabled(therapist_id: str, feature_name: str):
    """Check if a feature is enabled for a therapist based on their subscription plan"""
    toggles = await get_feature_toggles_for_therapist(therapist_id)
    if not toggles.get(feature_name, True):
        raise HTTPException(
            status_code=403, 
            detail=f"Feature '{feature_name}' is not included in your subscription plan"
        )

def require_feature(feature_name: str):
    """Dependency factory to require a specific feature"""
    async def check_feature(current_user: dict = Depends(get_current_user)):
        if current_user["role"] == "therapist":
            await check_feature_enabled(current_user["id"], feature_name)
        elif current_user["role"] == "assistant":
            await check_feature_enabled(current_user.get("therapist_id"), feature_name)
        return current_user
    return check_feature

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

# ============= AUTH ENDPOINTS (MOVED TO routes/auth.py) =============
# The following auth endpoints are now in routes/auth.py:
# - POST /auth/register
# - POST /auth/therapist-application
# - POST /auth/login
# - POST /auth/super-admin-login
# - GET /auth/me
# - GET /auth/subscription-status
# - GET /user/preferences
# - PUT /user/preferences

# ============= USER PREFERENCES ENDPOINTS (MOVED TO routes/auth.py) =============


# ============= SUPER ADMIN ENDPOINTS (MOVED TO routes/admin.py) =============
# Moved: /admin/therapist-applications, /admin/therapists, /admin/clients

# ============= DEPENDENCY FUNCTIONS (kept for remaining routes) =============

async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user

async def require_therapist(current_user: dict = Depends(get_current_user)):
    """Allows any therapist to access (for read operations)"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
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
            raise HTTPException(
                status_code=403, 
                detail="Your subscription has expired. You are in read-only mode."
            )
        return current_user
    elif current_user["role"] == "assistant":
        therapist = await db.users.find_one({"id": current_user.get("therapist_id"), "role": "therapist"}, {"_id": 0})
        if not therapist:
            raise HTTPException(status_code=403, detail="Linked therapist account not found")
        subscription_status = therapist.get("subscription_status")
        if subscription_status not in ["trial", "active"]:
            raise HTTPException(
                status_code=403, 
                detail="The therapist's subscription has expired. Read-only mode is active."
            )
        return current_user
    
    raise HTTPException(status_code=403, detail="Access denied")


# ============= SUPPORT TICKET & SUBSCRIPTION ENDPOINTS (MOVED TO routes/subscriptions.py) =============
# ============= ASSISTANT ENDPOINTS (MOVED TO routes/assistants.py) =============


# ============= ASSISTANT DASHBOARD & CASH SETTLEMENT (MOVED TO routes/assistant.py) =============


# ============= CASE HISTORY, CONSENT, HOMEWORK (MOVED TO routes/clinical.py) =============

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
    # Check feature access
    await check_feature_enabled(current_user["id"], "ai_clinical")
    
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
        
        # Include Case History if requested
        if request.include_case_history:
            case_history = await db.case_histories.find_one(
                {"client_id": request.client_id, "therapist_id": therapist_id},
                {"_id": 0}
            )
            if case_history:
                ch_text = ""
                if case_history.get("presenting_problem"):
                    ch_text += f"Presenting Problem: {case_history['presenting_problem']}\n"
                if case_history.get("history_of_present_illness"):
                    ch_text += f"History of Present Illness: {case_history['history_of_present_illness']}\n"
                if case_history.get("past_psychiatric_history"):
                    ch_text += f"Past Psychiatric History: {case_history['past_psychiatric_history']}\n"
                if case_history.get("family_history"):
                    ch_text += f"Family History: {case_history['family_history']}\n"
                if case_history.get("medical_history"):
                    ch_text += f"Medical History: {case_history['medical_history']}\n"
                if case_history.get("mental_status_exam"):
                    ch_text += f"Mental Status Exam: {case_history['mental_status_exam']}\n"
                if case_history.get("diagnosis"):
                    ch_text += f"Diagnosis: {case_history['diagnosis']}\n"
                if ch_text:
                    client_context += f"\nCase History:\n{ch_text}"
                    data_sources.append("case_history")
        
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
        if request.include_prev_assessments:
            completed_assessments = await db.assessments.find(
                {"therapist_id": therapist_id, "client_id": request.client_id, "status": "completed"},
                {"_id": 0, "assessment_type": 1, "score": 1, "interpretation": 1}
            ).to_list(20)
            
            if completed_assessments:
                client_context += "\nPreviously Completed Assessments:\n"
                for a in completed_assessments:
                    client_context += f"- {a['assessment_type']}: Score {a.get('score', 'N/A')}"
                    if a.get('interpretation'):
                        client_context += f" ({a['interpretation'][:100]})"
                    client_context += "\n"
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
        
        # Include Case History if requested
        if request.include_case_history:
            case_history = await db.case_histories.find_one(
                {"client_id": request.client_id, "therapist_id": therapist_id},
                {"_id": 0}
            )
            if case_history:
                ch_text = ""
                if case_history.get("presenting_problem"):
                    ch_text += f"Presenting Problem: {case_history['presenting_problem']}\n"
                if case_history.get("history_of_present_illness"):
                    ch_text += f"History: {case_history['history_of_present_illness']}\n"
                if case_history.get("diagnosis"):
                    ch_text += f"Diagnosis: {case_history['diagnosis']}\n"
                if case_history.get("mental_status_exam"):
                    ch_text += f"MSE: {case_history['mental_status_exam']}\n"
                if ch_text:
                    context += f"\nCase History:\n{ch_text}"
        
        # Include Previous Assessments if requested
        if request.include_prev_assessments:
            prev_assessments = await db.assessments.find(
                {"therapist_id": therapist_id, "client_id": request.client_id, "status": "completed"},
                {"_id": 0, "assessment_type": 1, "score": 1, "interpretation": 1}
            ).to_list(10)
            
            if prev_assessments:
                context += "\nPrevious Assessment Results:\n"
                for a in prev_assessments:
                    context += f"- {a['assessment_type']}: Score {a.get('score', 'N/A')}"
                    if a.get('interpretation'):
                        context += f" ({a['interpretation'][:100]})"
                    context += "\n"
    
    # Get assessment results if provided
    if request.assessment_ids:
        assessments = await db.assessments.find(
            {"id": {"$in": request.assessment_ids}, "therapist_id": therapist_id, "status": "completed"},
            {"_id": 0}
        ).to_list(10)
        
        if assessments:
            context += "\nSelected Assessment Results:\n"
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
    
    # Include Case History if requested
    if request.include_case_history:
        case_history = await db.case_histories.find_one(
            {"client_id": request.client_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
        if case_history:
            ch_text = ""
            if case_history.get("presenting_problem"):
                ch_text += f"Presenting Problem: {case_history['presenting_problem']}\n"
            if case_history.get("diagnosis"):
                ch_text += f"Diagnosis: {case_history['diagnosis']}\n"
            if ch_text:
                context += f"\nCase History:\n{ch_text}"
    
    # Include Previous Assessments if requested
    if request.include_prev_assessments:
        prev_assessments = await db.assessments.find(
            {"therapist_id": therapist_id, "client_id": request.client_id, "status": "completed"},
            {"_id": 0, "assessment_type": 1, "score": 1, "interpretation": 1}
        ).to_list(5)
        
        if prev_assessments:
            context += "\nPrevious Assessments:\n"
            for a in prev_assessments:
                context += f"- {a['assessment_type']}: Score {a.get('score', 'N/A')}"
                if a.get('interpretation'):
                    context += f" ({a['interpretation'][:80]})"
                context += "\n"
    
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

# ============= COGNIVISION DIAGNOSTIC REPORT ENDPOINTS =============

@api_router.post("/ai/generate-diagnostic-report", response_model=DiagnosticReportResponse)
async def ai_generate_diagnostic_report(request: DiagnosticReportRequest, current_user: dict = Depends(require_active_therapist)):
    """CogniVision Diagnostic Engine - Generate comprehensive psychodiagnostic report"""
    await check_feature_enabled(current_user["id"], "ai_clinical")
    
    therapist_id = current_user["id"]
    
    # Get therapist info for header and signature
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
    therapist_name = therapist.get("full_name", "Unknown") if therapist else "Unknown"
    therapist_reg = therapist.get("registration_number", "N/A") if therapist else "N/A"
    therapist_phone = therapist.get("phone", "N/A") if therapist else "N/A"
    
    # Get therapist profile for additional details
    therapist_profile = await db.therapist_profiles.find_one({"user_id": therapist_id}, {"_id": 0})
    therapist_title = therapist_profile.get("professional_title", "Clinical Psychologist") if therapist_profile else "Clinical Psychologist"
    therapist_clinic = therapist_profile.get("clinic_name", "") if therapist_profile else ""
    therapist_address = ""
    if therapist_profile and therapist_profile.get("address"):
        addr = therapist_profile["address"]
        addr_parts = [addr.get("line1", ""), addr.get("line2", ""), addr.get("city", ""), addr.get("state", ""), addr.get("pincode", "")]
        therapist_address = ", ".join([p for p in addr_parts if p])
    
    # Get client info
    client_profile = await db.client_profiles.find_one(
        {"user_id": request.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_user = await db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1, "phone": 1, "date_of_birth": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
    client_phone = client_user.get("phone", "N/A") if client_user else "N/A"
    client_dob = client_user.get("date_of_birth", "N/A") if client_user else "N/A"
    
    context = f"""
PATIENT INFORMATION:
- Name: {client_name}
- Contact: {client_phone}
- Date of Birth: {client_dob}
- Referral Source: {client_profile.get('referral_source', 'Self-referred')}
- Primary Concerns: {client_profile.get('presenting_concerns', 'Not specified')}
"""
    
    # Include Case History
    if request.include_case_history:
        case_history = await db.case_histories.find_one(
            {"client_id": request.client_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
        if case_history:
            context += f"""
CASE HISTORY:
- Presenting Problem: {case_history.get('presenting_problem', 'N/A')}
- History of Present Illness: {case_history.get('history_of_present_illness', 'N/A')}
- Past Psychiatric History: {case_history.get('past_psychiatric_history', 'N/A')}
- Family History: {case_history.get('family_history', 'N/A')}
- Medical History: {case_history.get('medical_history', 'N/A')}
- Mental Status Exam: {case_history.get('mental_status_exam', 'N/A')}
- Previous Diagnosis: {case_history.get('diagnosis', 'N/A')}
"""
    
    # Include Intake Notes
    if request.include_intake and client_profile.get("intake_summary"):
        context += f"""
INTAKE NOTES:
{client_profile['intake_summary']}
"""
    
    # Include Session History
    if request.include_session_history:
        session_notes = await db.session_notes.find(
            {"therapist_id": therapist_id, "client_id": request.client_id},
            {"_id": 0, "subjective": 1, "objective": 1, "assessment": 1, "plan": 1, "created_at": 1}
        ).sort("created_at", -1).to_list(10)
        
        if session_notes:
            context += "\nSESSION HISTORY (Recent):\n"
            for i, note in enumerate(session_notes[:5]):
                context += f"""
Session {i+1}:
- Subjective: {note.get('subjective', 'N/A')[:300]}
- Assessment: {note.get('assessment', 'N/A')[:300]}
- Plan: {note.get('plan', 'N/A')[:200]}
"""
    
    # Get Selected Assessments - Optional now
    assessment_battery = []
    if request.assessment_ids:
        assessments = await db.assessments.find(
            {"id": {"$in": request.assessment_ids}, "therapist_id": therapist_id, "status": "completed"},
            {"_id": 0}
        ).to_list(50)
        
        if assessments:
            context += "\nASSESSMENT BATTERY & SCORES:\n"
            for a in assessments:
                assessment_info = f"""
Assessment: {a.get('assessment_type', 'Unknown')}
- Score: {a.get('score', 'N/A')}
- Interpretation: {a.get('interpretation', 'N/A')}
- Severity: {a.get('severity', 'N/A')}
- Administered: {a.get('created_at', 'N/A')}
- Responses: {json.dumps(a.get('responses', {}))[:500] if a.get('responses') else 'N/A'}
"""
                context += assessment_info
                assessment_battery.append({
                    "type": a.get('assessment_type'),
                    "score": a.get('score'),
                    "interpretation": a.get('interpretation'),
                    "severity": a.get('severity')
                })
    
    # Include Therapist Notes (offline assessment data) - Can be primary source
    if request.therapist_notes:
        context += f"""
THERAPIST'S CLINICAL OBSERVATIONS / ASSESSMENT DETAILS:
{request.therapist_notes}
"""
    
    # Validate that we have at least some data to generate report
    if not request.assessment_ids and not request.therapist_notes:
        raise HTTPException(status_code=400, detail="Please select assessments or provide clinical observations")
    
    # Current date for report
    from datetime import datetime
    report_date = datetime.now().strftime("%d/%m/%Y")
    
    system_prompt = f"""You are CogniVision Engine, a Senior Clinical Psychologist AI system integrated into COGNISPACE. 
Your task is to synthesize all provided clinical data into a Full-Scale Psychodiagnostic Evaluation Report.

IMPORTANT GUIDELINES:
1. Use objective, medical-grade terminology and formal clinical structure
2. Identify clinical correlations across different tests to create a unified diagnostic picture
3. Do NOT provide summaries - provide DEEP clinical interpretations
4. Use ICD-11 and DSM-5 diagnostic standards
5. Be evidence-based and cite which assessments support each conclusion
6. Maintain professional, formal tone throughout

REPORT STRUCTURE (Generate each section):

1. PATIENT IDENTIFICATION & REFERRAL CONTEXT
   - Demographics, referral source, presenting complaints
   
2. ASSESSMENT BATTERY
   - Complete list of all administered tests with dates
   
3. PSYCHOMETRIC FINDINGS & DATA TRIANGULATION
   - Cross-analysis of all test results
   - Identify patterns, correlations, and discrepancies
   - Clinical significance of scores
   
4. DIAGNOSTIC IMPRESSION
   - Primary diagnosis with ICD-11/DSM-5 codes
   - Differential diagnoses considered
   - Rule-outs with reasoning
   - Severity specifiers
   
5. EVIDENCE-BASED TREATMENT ROADMAP
   - Recommended interventions
   - Treatment modality suggestions
   - Prognosis indicators
   - Follow-up recommendations

Respond in valid JSON format:
{{
    "patient_identification": "Full section text...",
    "referral_context": "Full section text...",
    "assessment_battery": "Full section text with all tests listed...",
    "psychometric_findings": "Detailed cross-analysis text...",
    "diagnostic_impression": "Full diagnostic formulation with codes...",
    "treatment_roadmap": "Complete treatment recommendations..."
}}

Remember: You are CogniVision Engine providing expert-level clinical analysis."""

    try:
        chat = await get_ai_chat(f"cognivision-{therapist_id}-{uuid.uuid4()}", system_prompt)
        user_message = UserMessage(text=f"Generate a comprehensive Psychodiagnostic Evaluation Report based on:\n\n{context}")
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
        
        # Build formatted HTML report
        raw_html = f"""
<div class="diagnostic-report">
    <div class="report-header" style="text-align: center; border-bottom: 2px solid #16a34a; padding-bottom: 20px; margin-bottom: 30px;">
        <h1 style="color: #16a34a; margin: 0;">COGNISPACE</h1>
        <p style="color: #666; margin: 5px 0;">Precision Insights. Personal Growth.</p>
        <h2 style="margin-top: 20px;">PSYCHODIAGNOSTIC EVALUATION REPORT</h2>
        <p><strong>Report Date:</strong> {report_date}</p>
        <p><strong>Report ID:</strong> CR-{uuid.uuid4().hex[:8].upper()}</p>
    </div>
    
    <div class="section">
        <h3 style="color: #16a34a; border-bottom: 1px solid #e5e7eb;">1. PATIENT IDENTIFICATION & REFERRAL CONTEXT</h3>
        <p>{result.get('patient_identification', 'N/A')}</p>
        <p>{result.get('referral_context', '')}</p>
    </div>
    
    <div class="section">
        <h3 style="color: #16a34a; border-bottom: 1px solid #e5e7eb;">2. ASSESSMENT BATTERY</h3>
        <p>{result.get('assessment_battery', 'N/A')}</p>
    </div>
    
    <div class="section">
        <h3 style="color: #16a34a; border-bottom: 1px solid #e5e7eb;">3. PSYCHOMETRIC FINDINGS & DATA TRIANGULATION</h3>
        <p>{result.get('psychometric_findings', 'N/A')}</p>
    </div>
    
    <div class="section">
        <h3 style="color: #16a34a; border-bottom: 1px solid #e5e7eb;">4. DIAGNOSTIC IMPRESSION</h3>
        <p>{result.get('diagnostic_impression', 'N/A')}</p>
    </div>
    
    <div class="section">
        <h3 style="color: #16a34a; border-bottom: 1px solid #e5e7eb;">5. EVIDENCE-BASED TREATMENT ROADMAP</h3>
        <p>{result.get('treatment_roadmap', 'N/A')}</p>
    </div>
    
    <div class="report-footer" style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e5e7eb;">
        <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p style="font-size: 11px; color: #666;"><strong>CONFIDENTIALITY NOTICE:</strong> This report contains sensitive clinical information protected under applicable privacy laws. It is intended solely for the use of the named patient and their treating clinician. Unauthorized disclosure, copying, or distribution is strictly prohibited.</p>
            <p style="font-size: 11px; color: #666;"><strong>DISCLAIMER:</strong> This report is generated by CogniVision Engine as a clinical decision-support tool. All findings and recommendations require therapist review and approval. This report does not constitute a final diagnosis and should be interpreted in conjunction with comprehensive clinical evaluation.</p>
        </div>
        
        <div style="display: flex; justify-content: space-between; margin-top: 30px;">
            <div>
                <p><strong>Prepared by:</strong></p>
                <p>{therapist_name}</p>
                <p>Registration No: {therapist_reg}</p>
            </div>
            <div style="text-align: right;">
                <p><strong>Digital Signature:</strong></p>
                <p>_______________________</p>
                <p style="font-size: 11px;">Date: {report_date}</p>
            </div>
        </div>
    </div>
</div>
"""
        
        disclaimer = """This report is generated by CogniVision Engine as a clinical decision-support tool. All findings require therapist review and approval. This does not constitute a final diagnosis."""
        
        return DiagnosticReportResponse(
            header=f"COGNISPACE - Psychodiagnostic Evaluation Report - {report_date}",
            patient_identification=result.get('patient_identification', ''),
            referral_context=result.get('referral_context', ''),
            assessment_battery=result.get('assessment_battery', ''),
            psychometric_findings=result.get('psychometric_findings', ''),
            diagnostic_impression=result.get('diagnostic_impression', ''),
            treatment_roadmap=result.get('treatment_roadmap', ''),
            disclaimer=disclaimer,
            raw_html=raw_html
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CogniVision error: {str(e)}")

@api_router.post("/diagnostic-reports", response_model=DiagnosticReport)
async def save_diagnostic_report(report: DiagnosticReportCreate, current_user: dict = Depends(require_active_therapist)):
    """Save a diagnostic report (draft or final)"""
    report_doc = {
        "id": str(uuid.uuid4()),
        "therapist_id": current_user["id"],
        "client_id": report.client_id,
        "assessment_ids": report.assessment_ids,
        "report_content": report.report_content,
        "status": report.status,
        "therapist_signature": report.therapist_signature,
        "therapist_reg_no": report.therapist_reg_no,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "approved_at": None,
        "shared_at": None
    }
    
    await db.diagnostic_reports.insert_one(report_doc)
    report_doc.pop("_id", None)
    return DiagnosticReport(**report_doc)

@api_router.get("/diagnostic-reports")
async def get_diagnostic_reports(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get diagnostic reports - therapist sees all, client sees only shared"""
    query = {}
    
    if current_user["role"] == "client":
        query = {"client_id": current_user["id"], "status": "shared"}
    else:
        query = {"therapist_id": current_user["id"]}
        if client_id:
            query["client_id"] = client_id
    
    reports = await db.diagnostic_reports.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return reports

@api_router.get("/diagnostic-reports/{report_id}")
async def get_diagnostic_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific diagnostic report"""
    report = await db.diagnostic_reports.find_one({"id": report_id}, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Client can only see shared reports
    if current_user["role"] == "client":
        if report["client_id"] != current_user["id"] or report["status"] != "shared":
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if report["therapist_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return report

@api_router.put("/diagnostic-reports/{report_id}")
async def update_diagnostic_report(report_id: str, update_data: dict, current_user: dict = Depends(require_active_therapist)):
    """Update a diagnostic report"""
    report = await db.diagnostic_reports.find_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    update_fields = {"updated_at": datetime.now(timezone.utc)}
    
    if "report_content" in update_data:
        update_fields["report_content"] = update_data["report_content"]
    if "therapist_signature" in update_data:
        update_fields["therapist_signature"] = update_data["therapist_signature"]
    if "therapist_reg_no" in update_data:
        update_fields["therapist_reg_no"] = update_data["therapist_reg_no"]
    
    await db.diagnostic_reports.update_one({"id": report_id}, {"$set": update_fields})
    
    updated_report = await db.diagnostic_reports.find_one({"id": report_id}, {"_id": 0})
    return updated_report

@api_router.post("/diagnostic-reports/{report_id}/approve")
async def approve_diagnostic_report(report_id: str, current_user: dict = Depends(require_active_therapist)):
    """Approve a diagnostic report (still not shared with client)"""
    report = await db.diagnostic_reports.find_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    await db.diagnostic_reports.update_one(
        {"id": report_id},
        {"$set": {"status": "approved", "approved_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Report approved successfully"}

@api_router.post("/diagnostic-reports/{report_id}/share")
async def share_diagnostic_report(report_id: str, current_user: dict = Depends(require_active_therapist)):
    """Share diagnostic report with client"""
    report = await db.diagnostic_reports.find_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report["status"] not in ["approved", "shared"]:
        raise HTTPException(status_code=400, detail="Report must be approved before sharing")
    
    await db.diagnostic_reports.update_one(
        {"id": report_id},
        {"$set": {"status": "shared", "shared_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Report shared with client successfully"}

@api_router.delete("/diagnostic-reports/{report_id}")
async def delete_diagnostic_report(report_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a diagnostic report"""
    result = await db.diagnostic_reports.delete_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted successfully"}

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
