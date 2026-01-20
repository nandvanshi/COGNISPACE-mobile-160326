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
from assessment_library import CLINICAL_ASSESSMENTS, calculate_score, get_severity, get_client_friendly_assessment, ASSESSMENT_CLIENT_INFO

router = APIRouter(prefix="/assessments", tags=["assessments"])


# Use complete assessment library from assessment_library.py
ASSESSMENT_LIBRARY = CLINICAL_ASSESSMENTS


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


@router.get("/{assessment_id}/results")
async def get_assessment_results(assessment_id: str, current_user: dict = Depends(get_current_user)):
    """Get assessment results - therapist sees full results, client sees only if shared"""
    assessment = await db.assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Access control
    if current_user["role"] == "therapist":
        if assessment.get("therapist_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user["role"] == "client":
        if assessment.get("client_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        if not assessment.get("is_shared", False):
            raise HTTPException(status_code=403, detail="Results not shared yet")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get assessment library data for scoring info
    assessment_type = assessment.get("assessment_type", "")
    library_data = ASSESSMENT_LIBRARY.get(assessment_type, {})
    
    # Calculate score if responses exist
    responses = assessment.get("responses", [])
    score = None
    severity = None
    
    if responses and assessment.get("status") == "completed":
        score = calculate_score(assessment_type, responses)
        severity = get_severity(assessment_type, score)
    
    return {
        "id": assessment["id"],
        "assessment_type": assessment_type,
        "assessment_name": library_data.get("name", assessment_type),
        "client_id": assessment.get("client_id"),
        "client_name": assessment.get("client_name"),
        "status": assessment.get("status"),
        "responses": responses,
        "score": score,
        "severity": severity,
        "severity_bands": library_data.get("severity_bands", []),
        "questions": library_data.get("questions", []),
        "therapist_notes": assessment.get("therapist_notes"),
        "is_shared": assessment.get("is_shared", False),
        "assigned_at": assessment.get("assigned_at"),
        "completed_at": assessment.get("completed_at")
    }


@router.post("/{assessment_id}/share-report")
async def share_assessment_report(assessment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Share assessment results with client"""
    result = await db.assessments.update_one(
        {"id": assessment_id, "therapist_id": current_user["id"]},
        {"$set": {"is_shared": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    await log_audit(current_user["id"], "therapist", "share", "assessment_report", assessment_id)
    return {"message": "Report shared with client"}


@router.post("/{assessment_id}/unshare-report")
async def unshare_assessment_report(assessment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Remove client access to assessment results"""
    result = await db.assessments.update_one(
        {"id": assessment_id, "therapist_id": current_user["id"]},
        {"$set": {"is_shared": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    await log_audit(current_user["id"], "therapist", "unshare", "assessment_report", assessment_id)
    return {"message": "Report access removed"}


@router.put("/{assessment_id}/therapist-notes")
async def update_therapist_notes(assessment_id: str, data: dict, current_user: dict = Depends(require_active_therapist)):
    """Add or update therapist notes on assessment"""
    result = await db.assessments.update_one(
        {"id": assessment_id, "therapist_id": current_user["id"]},
        {"$set": {"therapist_notes": data.get("notes", "")}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    await log_audit(current_user["id"], "therapist", "update", "assessment_notes", assessment_id)
    return {"message": "Notes updated"}


@router.delete("/{assessment_id}")
async def delete_assessment(assessment_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete an assessment"""
    result = await db.assessments.delete_one({"id": assessment_id, "therapist_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    await log_audit(current_user["id"], "therapist", "delete", "assessment", assessment_id)
    return {"message": "Assessment deleted"}