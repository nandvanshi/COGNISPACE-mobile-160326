"""All Pydantic models for the API"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime

# ============= AUTH MODELS =============
class UserRegister(BaseModel):
    mobile: str
    email: str
    password: str
    full_name: str
    role: Literal["therapist", "client"] = "client"

class TherapistApplication(BaseModel):
    mobile: str
    email: str
    password: str
    full_name: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None

class SuperAdminLogin(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    identifier: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    full_name: str
    role: str
    status: Optional[str] = None
    therapist_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    token: str
    user: User

# ============= ASSISTANT MODELS =============
class AssistantCreate(BaseModel):
    email: str
    password: str
    full_name: str
    mobile: Optional[str] = None

class AssistantUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None

class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    full_name: str
    mobile: Optional[str] = None
    therapist_id: str
    therapist_name: Optional[str] = None
    status: str
    role: str = "assistant"
    created_at: str

# ============= CLIENT MODELS =============
class ClientProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    client_id: str
    therapist_id: str
    full_name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: str
    updated_at: str

class ClientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None

class ClientPasswordReset(BaseModel):
    new_password: str

# ============= APPOINTMENT MODELS =============
class AppointmentCreate(BaseModel):
    client_id: str
    date: str
    start_time: str
    duration: int = 60

class AppointmentUpdate(BaseModel):
    date: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    status: Optional[str] = None

class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    date: str
    start_time: str
    end_time: str
    duration: int
    status: str
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    actual_duration: Optional[int] = None
    recurring_pattern_id: Optional[str] = None
    created_at: str

class CheckInRequest(BaseModel):
    appointment_id: str

class CheckOutRequest(BaseModel):
    appointment_id: str
    session_note_id: Optional[str] = None
    payment_id: Optional[str] = None
    actual_duration: Optional[int] = None

# ============= AVAILABILITY MODELS =============
class TimeBlock(BaseModel):
    start: str
    end: str

class DayAvailability(BaseModel):
    enabled: bool = False
    blocks: List[TimeBlock] = []

class TherapistAvailabilityUpdate(BaseModel):
    monday: Optional[DayAvailability] = None
    tuesday: Optional[DayAvailability] = None
    wednesday: Optional[DayAvailability] = None
    thursday: Optional[DayAvailability] = None
    friday: Optional[DayAvailability] = None
    saturday: Optional[DayAvailability] = None
    sunday: Optional[DayAvailability] = None
    session_duration: Optional[int] = 60
    buffer_time: Optional[int] = 10

class TherapistAvailability(BaseModel):
    model_config = ConfigDict(extra="ignore")
    therapist_id: str
    monday: Optional[DayAvailability] = None
    tuesday: Optional[DayAvailability] = None
    wednesday: Optional[DayAvailability] = None
    thursday: Optional[DayAvailability] = None
    friday: Optional[DayAvailability] = None
    saturday: Optional[DayAvailability] = None
    sunday: Optional[DayAvailability] = None
    session_duration: int = 60
    buffer_time: int = 10
    updated_at: Optional[str] = None

class BlockedTimeCreate(BaseModel):
    date: str
    start_time: str
    end_time: str
    reason: Optional[str] = None

class BlockedTime(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    date: str
    start_time: str
    end_time: str
    reason: Optional[str] = None
    created_at: str

class AvailableSlot(BaseModel):
    start_time: str
    end_time: str
    duration: int

# ============= SESSION NOTE MODELS =============
class SessionNoteCreate(BaseModel):
    client_id: str
    appointment_id: Optional[str] = None
    note_type: Literal["soap", "dap"] = "soap"
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None

class SessionNoteUpdate(BaseModel):
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
    note_type: str
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None
    session_number: int
    created_at: str
    updated_at: str

# ============= RECURRING APPOINTMENT MODELS =============
class RecurringPatternCreate(BaseModel):
    client_id: str
    day_of_week: int
    start_time: str
    duration: int = 60
    end_date: Optional[str] = None

class RecurringPattern(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    day_of_week: int
    start_time: str
    duration: int
    end_date: Optional[str] = None
    is_active: bool = True
    created_at: str
    last_generated: Optional[str] = None

# ============= TEMPLATE MODELS =============
class NoteTemplateCreate(BaseModel):
    name: str
    note_type: Literal["soap", "dap"] = "soap"
    content: dict

class NoteTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[dict] = None

class NoteTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    name: str
    note_type: str
    content: dict
    use_count: int = 0
    created_at: str
    updated_at: str

# ============= MESSAGING MODELS =============
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
    is_read: bool = False
    created_at: str

class ClientMessagingSettings(BaseModel):
    messaging_enabled: bool = True

# ============= ASSESSMENT MODELS =============
class CustomAssessmentCreate(BaseModel):
    name: str
    questions: List[dict]
    scoring_guide: Optional[str] = None

class CustomAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    name: str
    questions: List[dict]
    scoring_guide: Optional[str] = None
    created_at: str

class AssessmentCreate(BaseModel):
    client_id: str
    assessment_type: str
    custom_assessment_id: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[str] = None

class Assessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    assessment_type: str
    custom_assessment_id: Optional[str] = None
    status: str
    instructions: Optional[str] = None
    answers: Optional[dict] = None
    score: Optional[int] = None
    interpretation: Optional[str] = None
    therapist_notes: Optional[str] = None
    due_date: Optional[str] = None
    shared_with_client: bool = False
    created_at: str
    completed_at: Optional[str] = None

class AssessmentSubmit(BaseModel):
    answers: dict

# ============= PROTOCOL MODELS =============
class ProtocolCreate(BaseModel):
    client_id: str
    name: str
    description: Optional[str] = None
    sessions: List[dict]

class Protocol(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    name: str
    description: Optional[str] = None
    sessions: List[dict]
    current_session: int = 0
    status: str = "active"
    created_at: str
    updated_at: str

# ============= HOMEWORK MODELS =============
class HomeworkCreate(BaseModel):
    client_id: str
    title: str
    description: str
    due_date: Optional[str] = None
    protocol_id: Optional[str] = None
    session_number: Optional[int] = None

class Homework(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: str
    title: str
    description: str
    due_date: Optional[str] = None
    status: str = "assigned"
    completed_at: Optional[str] = None
    completion_notes: Optional[str] = None
    protocol_id: Optional[str] = None
    session_number: Optional[int] = None
    created_at: str

class HomeworkComplete(BaseModel):
    completion_notes: Optional[str] = None

# ============= AI MODELS =============
class AIAssessmentSuggestionRequest(BaseModel):
    client_id: str
    presenting_problem: str
    additional_context: Optional[str] = None
    previous_assessments: Optional[List[str]] = None

class AIAssessmentSuggestion(BaseModel):
    assessment_type: str
    rationale: str
    priority: Literal["high", "medium", "low"]

class AIAssessmentSuggestionResponse(BaseModel):
    suggestions: List[AIAssessmentSuggestion]
    clinical_reasoning: str

class AIProtocolRequest(BaseModel):
    client_id: str
    treatment_approach: str
    presenting_problem: str
    treatment_goals: List[str]
    session_count: int = 8

class AIProtocolSession(BaseModel):
    session_number: int
    title: str
    objectives: List[str]
    activities: List[str]
    homework: Optional[str] = None

class AIProtocolResponse(BaseModel):
    protocol_name: str
    description: str
    sessions: List[AIProtocolSession]
    clinical_considerations: str
    outcome_measures: List[str]

class AIHomeworkRequest(BaseModel):
    client_id: str
    session_content: str
    treatment_goals: List[str]
    homework_type: Literal["worksheet", "behavioral", "cognitive", "mindfulness", "journaling"]

class AIHomeworkResponse(BaseModel):
    title: str
    description: str
    instructions: List[str]
    expected_duration: str
    therapeutic_rationale: str

# ============= RESOURCE MODELS =============
class ResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    resource_type: Literal["pdf", "video", "link", "worksheet"]
    url: str
    category: Optional[str] = None

class Resource(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    title: str
    description: Optional[str] = None
    resource_type: str
    url: str
    category: Optional[str] = None
    created_at: str

class ResourceAssignment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    resource_id: str
    resource_title: str
    resource_type: str
    resource_url: str
    client_id: str
    client_name: str
    therapist_id: str
    assigned_at: str
    viewed_at: Optional[str] = None
    completed_at: Optional[str] = None

# ============= PAYMENT MODELS =============
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
    bill_number: str
    therapist_id: str
    therapist_name: Optional[str] = None
    client_id: str
    client_name: str
    client_code: Optional[str] = None
    amount: float
    payment_method: str
    payment_status: str = "paid"
    payment_date: Optional[str] = None
    appointment_id: Optional[str] = None
    session_note_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

class PaymentReceipt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bill_number: str
    receipt_date: str
    therapist_name: str
    therapist_qualification: Optional[str] = None
    therapist_email: Optional[str] = None
    therapist_mobile: Optional[str] = None
    client_name: str
    client_id: str
    amount: float
    amount_in_words: str
    payment_method: str
    payment_status: str
    notes: Optional[str] = None
    session_date: Optional[str] = None

# ============= CASH SETTLEMENT MODELS =============
class CashSettlementCreate(BaseModel):
    note: Optional[str] = None

class CashSettlementDispute(BaseModel):
    reason: str

class CashSettlement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    date: str
    therapist_id: str
    therapist_name: str
    assistant_id: Optional[str] = None
    assistant_name: Optional[str] = None
    cash_amount: float
    online_amount: float
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

# ============= SUPPORT TICKET MODELS =============
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

# ============= SUBSCRIPTION MODELS =============
class SubscriptionPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: Optional[str] = None
    price: float
    duration_days: int
    features: List[str] = []
    feature_toggles: Optional[dict] = None
    is_active: bool = True
    created_at: str

class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    plan_id: str
    plan_name: str
    status: Literal["trial", "active", "expired", "cancelled"]
    start_date: str
    end_date: str
    created_at: str

class CouponCode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    code: str
    discount_percent: int
    valid_from: str
    valid_until: str
    max_uses: Optional[int] = None
    current_uses: int = 0
    is_active: bool = True
    created_at: str

# ============= THERAPIST MODELS =============
class TherapistProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    full_name: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_end_date: Optional[str] = None
    created_at: str

class ManualTherapistCreate(BaseModel):
    mobile: str
    email: str
    password: str
    full_name: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None

class TherapistUpdate(BaseModel):
    full_name: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

class ClientDetailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    client_id: str
    full_name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    therapist_id: str
    therapist_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    created_at: str
    last_session: Optional[str] = None
    total_sessions: int = 0

# ============= AUDIT LOG MODEL =============
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
