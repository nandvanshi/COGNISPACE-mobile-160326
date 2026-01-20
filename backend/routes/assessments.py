"""
Assessment management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user, log_audit, check_feature_enabled

router = APIRouter(prefix="/assessments", tags=["assessments"])


# ============= ASSESSMENT LIBRARY =============

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
            {"q": "Repeated, disturbing memories of a stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"q": "Repeated, disturbing dreams of a stressful experience", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]},
            {"q": "Suddenly feeling as if a stressful experience were happening again", "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"]}
        ]
    },
    "ASRS": {
        "name": "Adult ADHD Self-Report Scale",
        "description": "ADHD screening",
        "questions": [
            {"q": "Trouble wrapping up final details of a project?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very often"]},
            {"q": "Difficulty getting things in order for organized tasks?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very often"]},
            {"q": "Problems remembering appointments or obligations?", "options": ["Never", "Rarely", "Sometimes", "Often", "Very often"]}
        ]
    },
    "BDI-II": {
        "name": "Beck Depression Inventory-II",
        "description": "Depression severity assessment",
        "questions": [
            {"q": "Sadness", "options": ["I do not feel sad", "I feel sad much of the time", "I am sad all the time", "I can't stand it"]},
            {"q": "Pessimism", "options": ["Not discouraged", "More discouraged than before", "Don't expect things to work out", "Future is hopeless"]},
            {"q": "Past Failure", "options": ["Don't feel like a failure", "Failed more than I should", "See a lot of failures", "Total failure"]},
            {"q": "Loss of Pleasure", "options": ["Get as much pleasure as ever", "Don't enjoy as much", "Very little pleasure", "No pleasure"]}
        ]
    },
    "DASS-21": {
        "name": "Depression Anxiety Stress Scales-21",
        "description": "Measure depression, anxiety, and stress",
        "questions": [
            {"q": "I found it hard to wind down", "options": ["Did not apply", "Applied sometimes", "Applied often", "Applied most of time"]},
            {"q": "I was aware of dryness of my mouth", "options": ["Did not apply", "Applied sometimes", "Applied often", "Applied most of time"]},
            {"q": "I couldn't seem to experience any positive feeling", "options": ["Did not apply", "Applied sometimes", "Applied often", "Applied most of time"]}
        ]
    }
}


# ============= MODELS =============

class AssessmentAssign(BaseModel):
    client_id: str
    assessment_type: str
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class AssessmentSubmit(BaseModel):
    responses: List[int]
    notes: Optional[str] = None


class AssignedAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: Optional[str] = None
    assessment_type: str
    assessment_name: Optional[str] = None
    status: str
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    responses: Optional[List[int]] = None
    score: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


# ============= DEPENDENCIES =============

def get_effective_therapist_id(user: dict) -> str:
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None


async def require_active_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    if current_user.get("subscription_status") not in ["trial", "active"]:
        raise HTTPException(status_code=403, detail="Subscription expired")
    return current_user


async def require_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    return current_user


def parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


# ============= ASSESSMENT ENDPOINTS =============

# IMPORTANT: Static routes (/library, /custom) must come BEFORE dynamic routes (/{assessment_id})

@router.get("/library")
async def get_assessment_library(current_user: dict = Depends(get_current_user)):
    """Get available assessment types"""
    return ASSESSMENT_LIBRARY


@router.get("/custom")
async def get_custom_assessments(current_user: dict = Depends(require_therapist)):
    """Get therapist's custom assessments"""
    custom = await db.custom_assessments.find(
        {"therapist_id": current_user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    return custom


@router.post("/custom")
async def create_custom_assessment(data: dict, current_user: dict = Depends(require_active_therapist)):
    """Create a custom assessment"""
    assessment_id = str(uuid.uuid4())
    assessment_doc = {
        "id": assessment_id,
        "therapist_id": current_user["id"],
        "name": data.get("name"),
        "description": data.get("description"),
        "questions": data.get("questions", []),
        "is_shared": data.get("is_shared", False),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_assessments.insert_one(assessment_doc)
    await log_audit(current_user["id"], "therapist", "create", "custom_assessment", assessment_id)
    
    return assessment_doc


@router.delete("/custom/{assessment_id}")
async def delete_custom_assessment(assessment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a custom assessment"""
    result = await db.custom_assessments.delete_one({
        "id": assessment_id,
        "therapist_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Custom assessment not found")
    
    return {"message": "Custom assessment deleted"}


@router.get("/client/{client_id}/history")
async def get_client_assessment_history(client_id: str, current_user: dict = Depends(require_therapist)):
    """Get assessment history for a client"""
    assessments = await db.assessments.find(
        {"client_id": client_id, "therapist_id": current_user["id"], "status": "completed"},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(100)
    
    return assessments


@router.post("", response_model=AssignedAssessment)
async def assign_assessment(data: AssessmentAssign, current_user: dict = Depends(require_active_therapist)):
    """Assign assessment to a client"""
    await check_feature_enabled(current_user["id"], "assessments")
    
    if data.assessment_type not in ASSESSMENT_LIBRARY:
        raise HTTPException(status_code=400, detail="Invalid assessment type")
    
    client = await db.users.find_one({"id": data.client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    assessment_id = str(uuid.uuid4())
    assessment_doc = {
        "id": assessment_id,
        "therapist_id": current_user["id"],
        "client_id": data.client_id,
        "client_name": client.get("full_name"),
        "assessment_type": data.assessment_type,
        "assessment_name": ASSESSMENT_LIBRARY[data.assessment_type]["name"],
        "status": "assigned",
        "due_date": data.due_date.isoformat() if data.due_date else None,
        "notes": data.notes,
        "responses": None,
        "score": None,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.assessments.insert_one(assessment_doc)
    await log_audit(current_user["id"], "therapist", "assign", "assessment", assessment_id)
    
    return AssignedAssessment(**{k: parse_datetime(v) if k in ["due_date", "completed_at", "created_at"] else v for k, v in assessment_doc.items()})


@router.get("", response_model=List[AssignedAssessment])
async def get_assessments(
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get assessments - therapist sees assigned, client sees their own"""
    if current_user["role"] == "therapist":
        query = {"therapist_id": current_user["id"]}
    elif current_user["role"] == "client":
        query = {"client_id": current_user["id"]}
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if client_id and current_user["role"] == "therapist":
        query["client_id"] = client_id
    if status:
        query["status"] = status
    
    assessments = await db.assessments.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return [AssignedAssessment(**{k: parse_datetime(v) if k in ["due_date", "completed_at", "created_at"] else v for k, v in a.items()}) for a in assessments]


@router.get("/{assessment_id}")
async def get_assessment(assessment_id: str, current_user: dict = Depends(get_current_user)):
    """Get single assessment with questions"""
    assessment = await db.assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if current_user["role"] == "therapist" and assessment["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user["role"] == "client" and assessment["client_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    assessment_type = assessment.get("assessment_type")
    questions = ASSESSMENT_LIBRARY.get(assessment_type, {}).get("questions", [])
    
    return {**assessment, "questions": questions}


@router.post("/{assessment_id}/submit")
async def submit_assessment(assessment_id: str, data: AssessmentSubmit, current_user: dict = Depends(get_current_user)):
    """Client submits assessment responses"""
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can submit assessments")
    
    assessment = await db.assessments.find_one({"id": assessment_id, "client_id": current_user["id"]}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if assessment.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Assessment already completed")
    
    score = sum(data.responses)
    
    await db.assessments.update_one(
        {"id": assessment_id},
        {"$set": {
            "responses": data.responses,
            "score": score,
            "status": "completed",
            "client_notes": data.notes,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_audit(current_user["id"], "client", "submit", "assessment", assessment_id)
    
    return {"message": "Assessment submitted", "score": score}


@router.delete("/{assessment_id}")
async def delete_assessment(assessment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete an assessment"""
    result = await db.assessments.delete_one({"id": assessment_id, "therapist_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    await log_audit(current_user["id"], "therapist", "delete", "assessment", assessment_id)
    return {"message": "Assessment deleted"}


 