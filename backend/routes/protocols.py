"""
Protocol management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user, log_audit

router = APIRouter(prefix="/protocols", tags=["protocols"])


# ============= MODELS =============

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


# ============= PROTOCOL TEMPLATES =============

PROTOCOL_TEMPLATES = {
    "CBT_ANXIETY": {
        "name": "CBT for Anxiety",
        "modality": "CBT",
        "condition": "Anxiety",
        "description": "Cognitive Behavioral Therapy protocol for anxiety disorders",
        "sessions": [
            {"session_number": 1, "title": "Assessment & Psychoeducation", "goals": ["Initial assessment", "Introduce CBT model", "Set treatment goals"]},
            {"session_number": 2, "title": "Cognitive Restructuring I", "goals": ["Identify automatic thoughts", "Introduce thought records", "Challenge cognitive distortions"]},
            {"session_number": 3, "title": "Cognitive Restructuring II", "goals": ["Review thought records", "Practice cognitive reframing", "Identify thinking patterns"]},
            {"session_number": 4, "title": "Behavioral Experiments", "goals": ["Plan behavioral experiments", "Gradual exposure introduction", "Test anxious predictions"]},
            {"session_number": 5, "title": "Exposure Therapy I", "goals": ["Create fear hierarchy", "Begin in-session exposure", "Assign exposure homework"]},
            {"session_number": 6, "title": "Exposure Therapy II", "goals": ["Continue exposure exercises", "Process experiences", "Build coping skills"]},
            {"session_number": 7, "title": "Relapse Prevention", "goals": ["Review progress", "Identify warning signs", "Create maintenance plan"]},
            {"session_number": 8, "title": "Termination", "goals": ["Consolidate gains", "Plan for future challenges", "Gradual session spacing"]}
        ]
    },
    "CBT_DEPRESSION": {
        "name": "CBT for Depression",
        "modality": "CBT",
        "condition": "Depression",
        "description": "Cognitive Behavioral Therapy protocol for depression",
        "sessions": [
            {"session_number": 1, "title": "Assessment & Goal Setting", "goals": ["Comprehensive assessment", "Set SMART goals", "Introduce activity monitoring"]},
            {"session_number": 2, "title": "Behavioral Activation I", "goals": ["Review activity log", "Identify mood-activity connection", "Plan pleasant activities"]},
            {"session_number": 3, "title": "Behavioral Activation II", "goals": ["Increase activity level", "Address avoidance", "Build mastery experiences"]},
            {"session_number": 4, "title": "Cognitive Work I", "goals": ["Identify negative thoughts", "Introduce thought records", "Learn cognitive distortions"]},
            {"session_number": 5, "title": "Cognitive Work II", "goals": ["Challenge negative thoughts", "Develop balanced thinking", "Core belief identification"]},
            {"session_number": 6, "title": "Problem Solving", "goals": ["Teach problem-solving skills", "Address life stressors", "Build self-efficacy"]},
            {"session_number": 7, "title": "Relapse Prevention", "goals": ["Identify vulnerability factors", "Create action plan", "Review coping strategies"]},
            {"session_number": 8, "title": "Termination", "goals": ["Review achievements", "Plan for setbacks", "Schedule booster sessions"]}
        ]
    },
    "DBT_SKILLS": {
        "name": "DBT Skills Training",
        "modality": "DBT",
        "condition": "Emotional Dysregulation",
        "description": "Dialectical Behavior Therapy skills training protocol",
        "sessions": [
            {"session_number": 1, "title": "Orientation & Mindfulness I", "goals": ["Orientation to DBT", "Introduction to mindfulness", "Wise mind concept"]},
            {"session_number": 2, "title": "Mindfulness II", "goals": ["What skills", "How skills", "Practice exercises"]},
            {"session_number": 3, "title": "Distress Tolerance I", "goals": ["TIPP skills", "Distract with ACCEPTS", "Self-soothe techniques"]},
            {"session_number": 4, "title": "Distress Tolerance II", "goals": ["IMPROVE the moment", "Pros and cons", "Radical acceptance"]},
            {"session_number": 5, "title": "Emotion Regulation I", "goals": ["Understanding emotions", "Reduce vulnerability", "Opposite action"]},
            {"session_number": 6, "title": "Emotion Regulation II", "goals": ["Check the facts", "Problem solving", "Build positive experiences"]},
            {"session_number": 7, "title": "Interpersonal Effectiveness I", "goals": ["DEAR MAN skills", "GIVE skills", "FAST skills"]},
            {"session_number": 8, "title": "Interpersonal Effectiveness II & Review", "goals": ["Practice interpersonal skills", "Review all modules", "Create maintenance plan"]}
        ]
    },
    "ACT_GENERAL": {
        "name": "ACT for General Issues",
        "modality": "ACT",
        "condition": "General",
        "description": "Acceptance and Commitment Therapy general protocol",
        "sessions": [
            {"session_number": 1, "title": "Creative Hopelessness", "goals": ["Assess control agenda", "Introduce ACT model", "Explore workability"]},
            {"session_number": 2, "title": "Cognitive Defusion", "goals": ["Identify fusion", "Defusion techniques", "Thoughts as thoughts"]},
            {"session_number": 3, "title": "Acceptance", "goals": ["Willingness concept", "Clean vs dirty discomfort", "Acceptance exercises"]},
            {"session_number": 4, "title": "Present Moment", "goals": ["Mindfulness practice", "Contact with now", "Observer self"]},
            {"session_number": 5, "title": "Values Clarification", "goals": ["Values assessment", "Life compass", "Distinguish values from goals"]},
            {"session_number": 6, "title": "Committed Action", "goals": ["Set values-based goals", "Action planning", "Barriers to action"]},
            {"session_number": 7, "title": "Integration", "goals": ["Connect all processes", "Apply to life domains", "Build flexibility"]},
            {"session_number": 8, "title": "Review & Maintenance", "goals": ["Review progress", "Plan for challenges", "Ongoing practice"]}
        ]
    },
    "TRAUMA_PROCESSING": {
        "name": "Trauma Processing",
        "modality": "Trauma-Focused",
        "condition": "PTSD/Trauma",
        "description": "Trauma-focused therapy protocol",
        "sessions": [
            {"session_number": 1, "title": "Safety & Stabilization", "goals": ["Build therapeutic alliance", "Assess trauma history", "Develop safety plan"]},
            {"session_number": 2, "title": "Psychoeducation", "goals": ["Normalize trauma responses", "Explain treatment rationale", "Introduce grounding"]},
            {"session_number": 3, "title": "Coping Skills", "goals": ["Teach relaxation", "Build emotion regulation", "Create coping toolkit"]},
            {"session_number": 4, "title": "Trauma Narrative I", "goals": ["Begin trauma narrative", "Process emotions", "Use grounding as needed"]},
            {"session_number": 5, "title": "Trauma Narrative II", "goals": ["Continue processing", "Identify stuck points", "Work through avoidance"]},
            {"session_number": 6, "title": "Cognitive Processing", "goals": ["Challenge trauma beliefs", "Address guilt/shame", "Reframe meaning"]},
            {"session_number": 7, "title": "Integration", "goals": ["Integrate trauma memories", "Build coherent narrative", "Identify growth"]},
            {"session_number": 8, "title": "Future Focus", "goals": ["Review progress", "Plan for triggers", "Build resilience"]}
        ]
    }
}


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


async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return current_user


def parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


# ============= PROTOCOL ENDPOINTS =============

@router.get("/templates")
async def get_protocol_templates(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get available protocol templates - built-in + admin (global)"""
    # Start with built-in templates
    result = dict(PROTOCOL_TEMPLATES)
    
    # Get admin-created global protocol templates
    admin_templates = await db.admin_content.find(
        {"type": "protocol_template"},
        {"_id": 0}
    ).to_list(100)
    
    # Add admin templates with a prefix to distinguish
    for at in admin_templates:
        key = f"ADMIN_{at['id'][:8].upper()}"
        content = at.get("content", {})
        result[key] = {
            "name": at.get("title", ""),
            "modality": content.get("modality", at.get("category", "General")),
            "condition": content.get("condition", ""),
            "description": at.get("description", ""),
            "sessions": content.get("sessions", []),
            "source": "admin"
        }
    
    return result


@router.post("", response_model=Protocol)
async def create_protocol(data: ProtocolCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a new treatment protocol for a client"""
    therapist_id = current_user["id"]
    
    # Validate client belongs to therapist
    client_profile = await db.client_profiles.find_one(
        {"user_id": data.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client name
    client_user = await db.users.find_one({"id": data.client_id}, {"_id": 0, "full_name": 1})
    client_name = client_user.get("full_name", "Unknown") if client_user else "Unknown"
    
    now = datetime.now(timezone.utc).isoformat()
    protocol_id = str(uuid.uuid4())
    protocol_doc = {
        "id": protocol_id,
        "therapist_id": therapist_id,
        "client_id": data.client_id,
        "client_name": client_name,
        "modality": data.modality,
        "condition": data.condition,
        "sessions": data.sessions,
        "is_template": False,
        "created_at": now,
        "updated_at": now
    }
    
    await db.protocols.insert_one(protocol_doc)
    await log_audit(current_user["id"], "therapist", "create", "protocol", protocol_id)
    
    return Protocol(
        id=protocol_doc["id"],
        therapist_id=protocol_doc["therapist_id"],
        client_id=protocol_doc["client_id"],
        client_name=protocol_doc["client_name"],
        modality=protocol_doc["modality"],
        condition=protocol_doc["condition"],
        sessions=protocol_doc["sessions"],
        is_template=protocol_doc["is_template"],
        created_at=parse_datetime(protocol_doc["created_at"]),
        updated_at=parse_datetime(protocol_doc["updated_at"])
    )


@router.get("", response_model=List[Protocol])
async def get_protocols(
    client_id: Optional[str] = None,
    current_user: dict = Depends(require_therapist_or_assistant)
):
    """Get all protocols for the therapist"""
    therapist_id = get_effective_therapist_id(current_user)
    
    query = {"therapist_id": therapist_id}
    if client_id:
        query["client_id"] = client_id
    
    protocols = await db.protocols.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return [Protocol(
        id=p["id"],
        therapist_id=p["therapist_id"],
        client_id=p["client_id"],
        client_name=p.get("client_name", "Unknown"),
        modality=p["modality"],
        condition=p["condition"],
        sessions=p["sessions"],
        is_template=p.get("is_template", False),
        created_at=parse_datetime(p["created_at"]),
        updated_at=parse_datetime(p["updated_at"])
    ) for p in protocols]


@router.get("/{protocol_id}", response_model=Protocol)
async def get_protocol(protocol_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Get a single protocol"""
    therapist_id = get_effective_therapist_id(current_user)
    
    protocol = await db.protocols.find_one(
        {"id": protocol_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    return Protocol(
        id=protocol["id"],
        therapist_id=protocol["therapist_id"],
        client_id=protocol["client_id"],
        client_name=protocol.get("client_name", "Unknown"),
        modality=protocol["modality"],
        condition=protocol["condition"],
        sessions=protocol["sessions"],
        is_template=protocol.get("is_template", False),
        created_at=parse_datetime(protocol["created_at"]),
        updated_at=parse_datetime(protocol["updated_at"])
    )


@router.put("/{protocol_id}", response_model=Protocol)
async def update_protocol(protocol_id: str, data: dict, current_user: dict = Depends(require_active_therapist)):
    """Update a protocol"""
    therapist_id = current_user["id"]
    
    protocol = await db.protocols.find_one(
        {"id": protocol_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if "modality" in data:
        update_data["modality"] = data["modality"]
    if "condition" in data:
        update_data["condition"] = data["condition"]
    if "sessions" in data:
        update_data["sessions"] = data["sessions"]
    
    await db.protocols.update_one({"id": protocol_id}, {"$set": update_data})
    await log_audit(current_user["id"], "therapist", "update", "protocol", protocol_id)
    
    updated = await db.protocols.find_one({"id": protocol_id}, {"_id": 0})
    
    return Protocol(
        id=updated["id"],
        therapist_id=updated["therapist_id"],
        client_id=updated["client_id"],
        client_name=updated.get("client_name", "Unknown"),
        modality=updated["modality"],
        condition=updated["condition"],
        sessions=updated["sessions"],
        is_template=updated.get("is_template", False),
        created_at=parse_datetime(updated["created_at"]),
        updated_at=parse_datetime(updated["updated_at"])
    )


@router.delete("/{protocol_id}")
async def delete_protocol(protocol_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a protocol"""
    therapist_id = current_user["id"]
    
    result = await db.protocols.delete_one(
        {"id": protocol_id, "therapist_id": therapist_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    await log_audit(current_user["id"], "therapist", "delete", "protocol", protocol_id)
    
    return {"message": "Protocol deleted"}
