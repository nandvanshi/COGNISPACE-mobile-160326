"""
AI Clinical Support Routes
Contains AI-powered endpoints for:
- Assessment suggestions
- Protocol generation
- Homework generation
- Diagnostic report generation (CogniVision)
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json
import re
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
import jwt

from emergentintegrations.llm.chat import LlmChat, UserMessage

# Router setup
router = APIRouter(tags=["AI Clinical Support"])

# Module-level variables (set via setup_ai_clinical)
_db = None
_EMERGENT_LLM_KEY = None
_JWT_SECRET = None
_JWT_ALGORITHM = "HS256"

security = HTTPBearer()


def setup_ai_clinical(database, llm_key, jwt_secret, jwt_algorithm="HS256"):
    """Setup function to inject dependencies from server.py"""
    global _db, _EMERGENT_LLM_KEY, _JWT_SECRET, _JWT_ALGORITHM
    _db = database
    _EMERGENT_LLM_KEY = llm_key
    _JWT_SECRET = jwt_secret
    _JWT_ALGORITHM = jwt_algorithm


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        user = await _db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_active_therapist(current_user: dict = Depends(get_current_user)):
    """Requires therapist with active/trial subscription"""
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


async def get_feature_toggles_for_therapist(therapist_id: str):
    """Get active feature toggles for a therapist based on their subscription plan"""
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
    
    if not therapist_id:
        return DEFAULT_FEATURE_TOGGLES
    
    therapist = await _db.users.find_one({"id": therapist_id}, {"_id": 0})
    if not therapist:
        return DEFAULT_FEATURE_TOGGLES
    
    subscription = await _db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    if not subscription:
        return DEFAULT_FEATURE_TOGGLES
    
    plan = await _db.subscription_plans.find_one({"id": subscription.get("plan_id")}, {"_id": 0})
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


# ============= AI MODELS =============

class AIAssessmentSuggestionRequest(BaseModel):
    client_id: Optional[str] = None
    query: Optional[str] = None
    include_intake: bool = True
    include_notes: bool = True
    include_case_history: bool = True
    include_prev_assessments: bool = True

class AIAssessmentSuggestion(BaseModel):
    assessment_name: str
    assessment_type: str
    reason: str
    priority: str
    relevant_symptoms: List[str]

class AIAssessmentSuggestionResponse(BaseModel):
    suggestions: List[AIAssessmentSuggestion]
    analysis_summary: str
    data_sources_used: List[str]

class AIProtocolRequest(BaseModel):
    client_id: Optional[str] = None
    assessment_ids: Optional[List[str]] = None
    query: Optional[str] = None
    modality_preference: Optional[str] = None
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
    context: Optional[str] = None
    homework_type: Optional[str] = None
    protocol_id: Optional[str] = None
    include_case_history: bool = True
    include_prev_assessments: bool = True

class AIHomeworkResponse(BaseModel):
    title: str
    description: str
    instructions: str
    exercises: List[dict]
    estimated_time_minutes: int
    therapeutic_rationale: str

class DiagnosticReportRequest(BaseModel):
    client_id: str
    assessment_ids: List[str]
    include_intake: bool = True
    include_session_history: bool = True
    include_case_history: bool = True
    therapist_notes: Optional[str] = None

class DiagnosticReportResponse(BaseModel):
    header: str
    identifying_information: str
    reason_for_referral: str
    assessment_tools_used: str
    behavioral_observations: str
    test_results_interpretation: str
    clinical_impressions: str
    functional_impact: str
    strengths_protective_factors: str
    areas_of_concern: str
    recommendations: str
    disclaimer: str
    raw_html: str


# ============= HELPER FUNCTIONS =============

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
    """Initialize AI chat with Claude Sonnet 4"""
    if not _EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    chat = LlmChat(
        api_key=_EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message
    ).with_model("anthropic", "claude-4-sonnet-20250514")
    
    return chat


# ============= AI ENDPOINTS =============

@router.post("/ai/suggest-assessments", response_model=AIAssessmentSuggestionResponse)
async def ai_suggest_assessments(request: AIAssessmentSuggestionRequest, current_user: dict = Depends(require_active_therapist)):
    """AI-powered assessment suggestion based on client data and/or therapist query"""
    # Check feature access
    await check_feature_enabled(current_user["id"], "ai_clinical")
    
    therapist_id = current_user["id"]
    data_sources = []
    client_context = ""
    
    # Gather client data if client_id provided
    if request.client_id:
        client_profile = await _db.client_profiles.find_one(
            {"user_id": request.client_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
        if not client_profile:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_user = await _db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1})
        client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
        
        client_context += f"Client: {client_name}\n"
        
        # Include Case History if requested
        if request.include_case_history:
            case_history = await _db.case_histories.find_one(
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
            notes = await _db.session_notes.find(
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
            completed_assessments = await _db.assessments.find(
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
        
        # Handle response - could be string or object
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Extract JSON from response - find the JSON block
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group()
        else:
            # No JSON found - AI gave a text response, provide default suggestions
            return AIAssessmentSuggestionResponse(
                suggestions=[
                    AIAssessmentSuggestion(
                        assessment_name="Patient Health Questionnaire-9",
                        assessment_type="PHQ-9",
                        reason="Recommended as a baseline screening for depression - insufficient client data available for more specific recommendations",
                        priority="medium",
                        relevant_symptoms=["general screening"]
                    ),
                    AIAssessmentSuggestion(
                        assessment_name="Generalized Anxiety Disorder-7",
                        assessment_type="GAD-7",
                        reason="Recommended as a baseline screening for anxiety - insufficient client data available for more specific recommendations",
                        priority="medium",
                        relevant_symptoms=["general screening"]
                    )
                ],
                analysis_summary="Limited client data available. General baseline assessments recommended. Please add case history or clinical observations for more targeted suggestions.",
                data_sources_used=data_sources
            )
        
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


@router.post("/ai/generate-protocol", response_model=AIProtocolResponse)
async def ai_generate_protocol(request: AIProtocolRequest, current_user: dict = Depends(require_active_therapist)):
    """AI-powered therapy protocol generation"""
    therapist_id = current_user["id"]
    context = ""
    
    # Gather client information
    if request.client_id:
        client_profile = await _db.client_profiles.find_one(
            {"user_id": request.client_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
        if not client_profile:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_user = await _db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1})
        client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
        
        context += f"Client: {client_name}\n"
        if client_profile.get("intake_summary"):
            context += f"Intake: {client_profile['intake_summary']}\n"
        
        # Include Case History if requested
        if request.include_case_history:
            case_history = await _db.case_histories.find_one(
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
            prev_assessments = await _db.assessments.find(
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
        assessments = await _db.assessments.find(
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
        
        # Handle response type
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)
        
        response_text = response_text.strip()
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group()
        else:
            raise HTTPException(status_code=500, detail="Unable to generate protocol - please provide more clinical details")
        
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


@router.post("/ai/generate-homework", response_model=AIHomeworkResponse)
async def ai_generate_homework(request: AIHomeworkRequest, current_user: dict = Depends(require_active_therapist)):
    """AI-powered homework/worksheet generation"""
    therapist_id = current_user["id"]
    
    # Get client info
    client_profile = await _db.client_profiles.find_one(
        {"user_id": request.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_user = await _db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
    
    context = f"Client: {client_name}\n"
    
    # Include Case History if requested
    if request.include_case_history:
        case_history = await _db.case_histories.find_one(
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
        prev_assessments = await _db.assessments.find(
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
    recent_note = await _db.session_notes.find_one(
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
        protocol = await _db.protocols.find_one(
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
        
        # Handle response type
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)
        
        response_text = response_text.strip()
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group()
        else:
            raise HTTPException(status_code=500, detail="Unable to generate homework - please provide more clinical context")
        
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


@router.post("/ai/generate-diagnostic-report", response_model=DiagnosticReportResponse)
async def ai_generate_diagnostic_report(request: DiagnosticReportRequest, current_user: dict = Depends(require_active_therapist)):
    """CogniVision Diagnostic Engine - Generate comprehensive psychodiagnostic report"""
    await check_feature_enabled(current_user["id"], "ai_clinical")
    
    therapist_id = current_user["id"]
    
    # Get therapist info for header and signature
    therapist = await _db.users.find_one({"id": therapist_id}, {"_id": 0})
    therapist_name = therapist.get("full_name", "Unknown") if therapist else "Unknown"
    therapist_phone = therapist.get("mobile", "") or therapist.get("phone", "") if therapist else ""
    
    # Get therapist profile for additional details
    therapist_profile = await _db.therapist_profiles.find_one({"therapist_id": therapist_id}, {"_id": 0})
    if not therapist_profile:
        therapist_profile = await _db.therapist_profiles.find_one({"user_id": therapist_id}, {"_id": 0})
    
    therapist_qualifications = therapist_profile.get("qualifications", "") if therapist_profile else ""
    
    # Build therapist address from profile
    therapist_address_lines = []
    if therapist_profile:
        line1 = therapist_profile.get("address_line_1", "")
        line2 = therapist_profile.get("address_line_2", "")
        city = therapist_profile.get("city", "")
        state = therapist_profile.get("state", "")
        pincode = therapist_profile.get("pincode", "")
        
        if line1:
            therapist_address_lines.append(line1.strip().rstrip(','))
        if line2:
            therapist_address_lines.append(line2.strip().rstrip(','))
        
        city_state = []
        if city:
            city_state.append(city.strip())
        if state:
            city_state.append(state.strip())
        if pincode:
            city_state.append(pincode.strip())
        if city_state:
            therapist_address_lines.append(", ".join(city_state))
    
    # Get client info from client_profiles
    client_profile = await _db.client_profiles.find_one(
        {"user_id": request.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client name from users table
    client_user = await _db.users.find_one({"id": request.client_id}, {"_id": 0, "full_name": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else client_profile.get("full_name", "Unknown")
    
    # Get age and referred_by from client_profiles
    client_age = client_profile.get("age", "N/A")
    if client_age and client_age != "N/A":
        client_age = f"{client_age} years"
    client_referred_by = client_profile.get("referred_by", "Self-referred") or "Self-referred"
    
    context = f"""
PATIENT INFORMATION:
- Name: {client_name}
- Age: {client_age}
- Referred By: {client_referred_by}
"""
    
    # Include Case History
    if request.include_case_history:
        case_history = await _db.case_histories.find_one(
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
        session_notes = await _db.session_notes.find(
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
        assessments = await _db.assessments.find(
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
    
    # Include Therapist Notes
    if request.therapist_notes:
        context += f"""
THERAPIST'S CLINICAL OBSERVATIONS / ASSESSMENT DETAILS:
{request.therapist_notes}
"""
    
    # Validate that we have at least some data
    if not request.assessment_ids and not request.therapist_notes:
        raise HTTPException(status_code=400, detail="Please select assessments or provide clinical observations")
    
    # Current date for report
    report_date = datetime.now().strftime("%d/%m/%Y")
    
    system_prompt = """You are a Senior Clinical Psychological Report Writer.

You generate FULL, PROFESSIONAL psychological assessment reports
used by psychologists and psychiatrists for clinical understanding,
referrals, and treatment planning.

--------------------------------------------------
CORE PRINCIPLES
--------------------------------------------------

1. Use formal, professional clinical language.
2. Write for a clinical audience (psychologists, psychiatrists).
3. Be precise, structured, and neutral in tone.
4. Do NOT use casual or conversational language.
5. Reduce therapist documentation workload while preserving clinical control.

--------------------------------------------------
STRICT FORMATTING RULES (MANDATORY)
--------------------------------------------------

1️⃣ PATIENT NAME REPETITION RULE:
   - Mention patient name ONLY ONCE in Identifying Information section
   - Do NOT repeat the name anywhere else in the report
   - Use neutral terms like "the client" or "the individual" in all other sections

2️⃣ ASSESSMENT SCORE FORMATTING:
   - Do NOT use tables with pipes (|---|) or markdown tables
   - Do NOT use confusing formats like 16/21, 7/18
   - Write each assessment in clear text format:
     
     [Assessment Name]
     Raw Score: [X] (Scale Range: 0–[Max]) – [Severity Level]
     [Clinical interpretation and functional meaning]
     
   ✅ Example:
     Y-BOCS (Yale-Brown Obsessive Compulsive Scale)
     Raw Score: 19 (Scale Range: 0–40) – Moderate Severity
     Indicates clinically significant obsessive-compulsive symptoms with notable functional impairment in daily activities.
     
     GAD-7 (Generalized Anxiety Disorder Scale)
     Raw Score: 12 (Scale Range: 0–21) – Moderate Anxiety
     Reflects persistent generalized anxiety symptoms requiring clinical attention.

3️⃣ RECOMMENDATIONS FORMATTING:
   - Do NOT write recommendations in one paragraph
   - Each recommendation must be on a separate line with clear heading
   - Use professional clinical tone
   
   ✅ Format:
     Therapeutic Approach
     Cognitive Behavioral Therapy (CBT) with Exposure and Response Prevention (ERP) for OCD symptoms.
     
     Session Frequency
     Weekly 60-minute sessions for 16–20 weeks initially.
     
     Adjunct Interventions
     Sleep hygiene psychoeducation and relaxation training.
     
     Psychiatric Referral
     Consider consultation for SSRI augmentation if psychotherapy response is suboptimal.
     
     Follow-up Schedule
     Re-assessment after 8 weeks to evaluate treatment progress.

--------------------------------------------------
SAFETY & ETHICAL RULES
--------------------------------------------------

- Always requires therapist review before finalization.
- Use ICD-10 and DSM-5 coding standards for diagnosis.

--------------------------------------------------
INPUT HANDLING RULES
--------------------------------------------------

- You may receive:
  • One or more completed psychological assessments (if selected)
  • Case history data (if selected)
  • Intake notes (if provided)
  • Session notes (if selected)

- When MULTIPLE assessments are selected:
  → Generate ONE integrated report
  → Include ONLY the selected assessments
  → Do NOT mention unselected tools

--------------------------------------------------
REQUIRED OUTPUT
--------------------------------------------------

Generate a COMPLETE Psychological Assessment Report. Output must look like a formal psychological testing report suitable for professional review and clinical records — NOT a summary.

Respond in valid JSON format:
{
    "identifying_information": "Patient demographics - mention name ONLY here",
    "reason_for_referral": "Why the assessment was requested, presenting concerns - use 'the client' not name",
    "assessment_tools_used": "List ONLY the assessments explicitly mentioned in input",
    "behavioral_observations": "Observations during assessment - use 'the client' not name",
    "test_results_interpretation": "IMPORTANT: Use double newlines (blank line) between each assessment. Format each assessment as:\\n\\nAssessment Name\\nRaw Score: X (Scale Range: 0–Max) – Severity Level\\nClinical interpretation sentence.\\n\\nNext Assessment Name\\nRaw Score: Y (Scale Range: 0–Max) – Severity Level\\nClinical interpretation sentence.",
    "clinical_impressions": "Provide clinical diagnosis with ICD-10 and DSM-5 codes. Primary diagnosis, differential diagnoses, severity specifiers. Use 'the client' not name.",
    "functional_impact": "How symptoms affect daily functioning - use 'the client' not name",
    "strengths_protective_factors": "Strengths, support systems, resilience factors - use 'the client' not name",
    "areas_of_concern": "Key clinical concerns - use 'the client' not name",
    "recommendations": "IMPORTANT: Use double newlines (blank line) between each recommendation. Format each as:\\n\\nHeading Name\\nRecommendation description text.\\n\\nSTRICTLY DO NOT mention session duration or time (like 60-minute, 45-minute sessions). Only mention frequency (weekly, bi-weekly) without specifying session length."
}

--------------------------------------------------
GOAL
--------------------------------------------------

Produce a hospital-grade psychological assessment report that:
- Can be reviewed by another professional
- Significantly reduces therapist report-writing burden
- Maintains clinical safety, clarity, and professionalism
- Looks like a formal psychological testing report, NOT a summary"""

    try:
        chat = await get_ai_chat(f"cognivision-{therapist_id}-{uuid.uuid4()}", system_prompt)
        user_message = UserMessage(text=f"Generate a comprehensive Psychological Assessment Report based on:\n\n{context}")
        response = await chat.send_message(user_message)
        
        # Handle response type
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)
        
        response_text = response_text.strip()
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group()
        else:
            raise HTTPException(status_code=500, detail="Unable to generate diagnostic report - please ensure sufficient clinical data is provided")
        
        result = json.loads(response_text.strip())
        
        # Helper function to format Test Results
        def format_test_results(text):
            if not text:
                return "N/A"
            import re
            lines = text.split('\n\n')
            if len(lines) <= 1:
                text = re.sub(r'(?<=[.)])\s*([A-Z][A-Za-z\s\-()]+(?:Domain|Scale|Inventory|Questionnaire|Checklist|Assessment|Test))', r'</p><p class="assessment-item"><strong>\1</strong>', text)
                text = re.sub(r'Raw Score:', r'<br/><em>Raw Score:</em>', text)
                text = re.sub(r'(Scale Range:[^–-]+[–-][^)]+\))\s*[–-]\s*', r'<br/>\1 – <strong>', text)
                text = re.sub(r'(Clinically Significant|Moderate|Mild|Severe|Within Normal Limits|Moderately High|Moderately Elevated|High|Low|Normal)', r'\1</strong><br/>', text)
                return f'<p class="assessment-item">{text}</p>'
            
            formatted = []
            for block in lines:
                block = block.strip()
                if not block:
                    continue
                parts = block.split('\n')
                if parts:
                    assessment_name = parts[0]
                    rest = '<br/>'.join(parts[1:]) if len(parts) > 1 else ''
                    formatted.append(f'<p class="assessment-item"><strong>{assessment_name}</strong><br/>{rest}</p>')
            return ''.join(formatted) if formatted else f'<p>{text}</p>'
        
        # Helper function to format Recommendations
        def format_recommendations(text):
            if not text:
                return "N/A"
            import re
            lines = text.split('\n\n')
            if len(lines) <= 1:
                text = re.sub(r'([A-Z][A-Za-z\s/\-]+(?:Therapy|Consultation|Evaluation|Training|Assessment|Referral|Monitoring|Accommodations|Psychoeducation|Management|Intervention|Support|Schedule|Approach|Treatment))\s+([A-Z])', r'<p class="recommendation-item"><strong>\1</strong><br/>\2', text)
                if '<p class="recommendation-item">' in text:
                    text = text + '</p>'
                    return text
                return f'<p>{text}</p>'
            
            formatted = []
            for block in lines:
                block = block.strip()
                if not block:
                    continue
                parts = block.split('\n')
                if parts:
                    heading = parts[0]
                    description = ' '.join(parts[1:]) if len(parts) > 1 else ''
                    formatted.append(f'<p class="recommendation-item"><strong>{heading}</strong><br/>{description}</p>')
            return ''.join(formatted) if formatted else f'<p>{text}</p>'
        
        # Format special sections
        test_results_html = format_test_results(result.get('test_results_interpretation', ''))
        recommendations_html = format_recommendations(result.get('recommendations', ''))
        
        # Build address HTML
        address_html = ""
        for line in therapist_address_lines:
            address_html += f"<p>{line}</p>"
        
        # Build clean HTML report
        raw_html = f"""
<div class="clinical-report">
    
    <!-- Therapist Header -->
    <div class="therapist-header">
        <h1>{therapist_name}</h1>
        {f'<p>{therapist_qualifications}</p>' if therapist_qualifications else ''}
        {address_html}
        {f'<p>{therapist_phone}</p>' if therapist_phone else ''}
    </div>
    
    <!-- Report Title -->
    <div class="report-title">PSYCHOLOGICAL ASSESSMENT REPORT</div>
    <div class="report-meta">
        <p>Report Date: {report_date}</p>
        <p>Report ID: CR-{uuid.uuid4().hex[:8].upper()}</p>
    </div>
    
    <!-- Section 1: Identifying Information -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">1. Identifying Information</div>
        <div class="patient-info">
            <p><strong>Patient Name:</strong> {client_name}</p>
            <p><strong>Age:</strong> {client_age}</p>
            <p><strong>Referred By:</strong> {client_referred_by}</p>
        </div>
        <div class="report-content">
            <p>{result.get('identifying_information', '')}</p>
        </div>
    </div>
    
    <!-- Section 2: Reason for Referral -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">2. Reason for Referral</div>
        <div class="report-content">
            <p>{result.get('reason_for_referral', 'Self-referred for psychological assessment.')}</p>
        </div>
    </div>
    
    <!-- Section 3: Assessment Tools Used -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">3. Assessment Tools Used</div>
        <div class="report-content">
            <p>{result.get('assessment_tools_used', 'Clinical interview and behavioral observation.')}</p>
        </div>
    </div>
    
    <!-- Section 4: Behavioral Observations -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">4. Behavioral Observations</div>
        <div class="report-content">
            <p>{result.get('behavioral_observations', 'Not available for this assessment.')}</p>
        </div>
    </div>
    
    <!-- Section 5: Test Results & Interpretation -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">5. Test Results & Interpretation</div>
        <div class="report-content test-results">
            {test_results_html}
        </div>
    </div>
    
    <!-- Section 6: Clinical Impressions -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">6. Clinical Impressions</div>
        <div class="report-content">
            <p>{result.get('clinical_impressions', 'N/A')}</p>
        </div>
    </div>
    
    <!-- Section 7: Functional Impact -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">7. Functional Impact</div>
        <div class="report-content">
            <p>{result.get('functional_impact', 'N/A')}</p>
        </div>
    </div>
    
    <!-- Section 8: Strengths & Protective Factors -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">8. Strengths & Protective Factors</div>
        <div class="report-content">
            <p>{result.get('strengths_protective_factors', 'N/A')}</p>
        </div>
    </div>
    
    <!-- Section 9: Areas of Concern -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">9. Areas of Concern</div>
        <div class="report-content">
            <p>{result.get('areas_of_concern', 'N/A')}</p>
        </div>
    </div>
    
    <!-- Section 10: Recommendations -->
    <hr class="section-divider">
    <div class="report-section">
        <div class="section-heading">10. Recommendations</div>
        <div class="report-content recommendations">
            {recommendations_html}
        </div>
    </div>
    
    <!-- Disclaimer & Confidentiality Notice -->
    <div class="disclaimer-box">
        <p><strong>DISCLAIMER:</strong> This report is generated as a clinical documentation aid. It does NOT constitute a final diagnosis or treatment recommendation. All findings require review and approval by the treating clinician.</p>
        <p><strong>Confidentiality Notice:</strong> This document is strictly Confidential and intended solely for the use of the named recipient, their treating clinician, or authorized medical personnel. Unauthorized reproduction, distribution, or disclosure of this report is strictly prohibited under the Personal Data Protection laws and clinical ethics guidelines.</p>
    </div>
    
    <!-- Signature Block -->
    <div class="signature-section">
        <p class="signature-label">Prepared by:</p>
        <div class="signature-space"></div>
        <p class="signature-name">{therapist_name}</p>
        <p class="signature-details">{therapist_qualifications}</p>
        <p class="signature-details" style="margin-top: 10px;">Date: {report_date}</p>
    </div>
</div>
"""
        
        disclaimer = """This report is generated as a clinical documentation aid. It does NOT constitute a final diagnosis or treatment recommendation. All findings require review and approval by the treating clinician."""
        
        return DiagnosticReportResponse(
            header=f"COGNISPACE - Psychological Assessment Report - {report_date}",
            identifying_information=result.get('identifying_information', ''),
            reason_for_referral=result.get('reason_for_referral', ''),
            assessment_tools_used=result.get('assessment_tools_used', ''),
            behavioral_observations=result.get('behavioral_observations', ''),
            test_results_interpretation=result.get('test_results_interpretation', ''),
            clinical_impressions=result.get('clinical_impressions', ''),
            functional_impact=result.get('functional_impact', ''),
            strengths_protective_factors=result.get('strengths_protective_factors', ''),
            areas_of_concern=result.get('areas_of_concern', ''),
            recommendations=result.get('recommendations', ''),
            disclaimer=disclaimer,
            raw_html=raw_html
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CogniVision error: {str(e)}")
