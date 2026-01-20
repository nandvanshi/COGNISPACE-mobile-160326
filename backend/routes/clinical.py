"""
Clinical routes - Case History, Consent, Homework
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user, log_audit, check_feature_enabled

router = APIRouter(tags=["clinical"])


# ============= MODELS =============

class CaseHistoryUpdate(BaseModel):
    section: str
    data: dict


class CaseHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    therapist_id: str
    sections: dict = {}
    is_complete: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConsentUpdate(BaseModel):
    is_signed: bool = False
    signature_date: Optional[str] = None
    witnessed_by: Optional[str] = None


class ConsentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    therapist_id: str
    is_signed: bool = False
    signature_date: Optional[str] = None
    witnessed_by: Optional[str] = None
    created_at: Optional[str] = None


class HomeworkCreate(BaseModel):
    client_id: str
    title: str
    description: str
    due_date: Optional[datetime] = None
    priority: str = "medium"


class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None


class HomeworkComplete(BaseModel):
    client_notes: str


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


# ============= DEPENDENCIES =============

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


# ============= CASE HISTORY ENDPOINTS =============

@router.get("/case-history/{client_id}", response_model=CaseHistoryResponse)
async def get_case_history(client_id: str, current_user: dict = Depends(require_therapist)):
    """Get case history for a client"""
    case_history = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not case_history:
        ch_id = str(uuid.uuid4())
        case_history = {
            "id": ch_id,
            "client_id": client_id,
            "therapist_id": current_user["id"],
            "sections": {},
            "is_complete": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None
        }
        await db.case_histories.insert_one(case_history)
    
    return CaseHistoryResponse(**case_history)


@router.put("/case-history/{client_id}")
async def update_case_history(client_id: str, data: CaseHistoryUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update a section of case history"""
    case_history = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not case_history:
        ch_id = str(uuid.uuid4())
        case_history = {
            "id": ch_id,
            "client_id": client_id,
            "therapist_id": current_user["id"],
            "sections": {},
            "is_complete": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.case_histories.insert_one(case_history)
    
    sections = case_history.get("sections", {})
    sections[data.section] = data.data
    
    required_sections = ["identification", "presenting_problem", "history", "mental_status"]
    is_complete = all(s in sections and sections[s] for s in required_sections)
    
    await db.case_histories.update_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"$set": {
            f"sections.{data.section}": data.data,
            "is_complete": is_complete,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_audit(current_user["id"], "therapist", "update", "case_history", case_history.get("id", ""))
    
    updated = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    return CaseHistoryResponse(**updated)


@router.post("/case-history/{client_id}/complete")
async def mark_case_history_complete(client_id: str, current_user: dict = Depends(require_active_therapist)):
    """Mark case history as complete"""
    result = await db.case_histories.update_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"$set": {"is_complete": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Case history not found")
    
    return {"message": "Case history marked as complete"}


# ============= THERAPY CONSENT ENDPOINTS =============

@router.get("/consent/{client_id}", response_model=ConsentResponse)
async def get_consent(client_id: str, current_user: dict = Depends(require_therapist)):
    """Get therapy consent for a client"""
    consent = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not consent:
        consent_id = str(uuid.uuid4())
        consent = {
            "id": consent_id,
            "client_id": client_id,
            "therapist_id": current_user["id"],
            "is_signed": False,
            "signature_date": None,
            "witnessed_by": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.therapy_consents.insert_one(consent)
    
    return ConsentResponse(**consent)


@router.put("/consent/{client_id}")
async def update_consent(client_id: str, data: ConsentUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update consent status"""
    consent = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not consent:
        consent_id = str(uuid.uuid4())
        consent = {
            "id": consent_id,
            "client_id": client_id,
            "therapist_id": current_user["id"],
            "is_signed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.therapy_consents.insert_one(consent)
    
    update_data = {"is_signed": data.is_signed}
    if data.signature_date:
        update_data["signature_date"] = data.signature_date
    if data.witnessed_by:
        update_data["witnessed_by"] = data.witnessed_by
    
    await db.therapy_consents.update_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"$set": update_data}
    )
    
    await log_audit(current_user["id"], "therapist", "update", "consent", consent.get("id", ""))
    
    updated = await db.therapy_consents.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    return ConsentResponse(**updated)


# ============= HOMEWORK ENDPOINTS =============

@router.post("/homework", response_model=Homework)
async def assign_homework(hw_data: HomeworkCreate, current_user: dict = Depends(require_active_therapist)):
    """Assign homework to a client"""
    client = await db.users.find_one({"id": hw_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if hw_data.priority not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Priority must be low, medium, or high")
    
    hw_id = str(uuid.uuid4())
    hw_doc = {
        "id": hw_id,
        "therapist_id": current_user["id"],
        "client_id": hw_data.client_id,
        "client_name": client["full_name"],
        "title": hw_data.title,
        "description": hw_data.description,
        "due_date": hw_data.due_date.isoformat() if hw_data.due_date else None,
        "priority": hw_data.priority,
        "status": "assigned",
        "client_notes": None,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.homework.insert_one(hw_doc)
    await log_audit(current_user["id"], "therapist", "assign", "homework", hw_id)
    
    return Homework(**{k: parse_datetime(v) if k in ["due_date", "completed_at", "created_at"] else v for k, v in hw_doc.items()})


@router.get("/homework", response_model=List[Homework])
async def get_homework(
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get homework - therapist sees all, client sees their own"""
    if current_user["role"] == "therapist":
        query = {"therapist_id": current_user["id"]}
        if client_id:
            query["client_id"] = client_id
    elif current_user["role"] == "client":
        query = {"client_id": current_user["id"]}
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    homework = await db.homework.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return [Homework(**{k: parse_datetime(v) if k in ["due_date", "completed_at", "created_at"] else v for k, v in hw.items()}) for hw in homework]


@router.put("/homework/{homework_id}", response_model=Homework)
async def update_homework(homework_id: str, hw_data: HomeworkUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update homework"""
    hw = await db.homework.find_one({"id": homework_id, "therapist_id": current_user["id"]}, {"_id": 0})
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    update_data = {}
    if hw_data.title is not None:
        update_data["title"] = hw_data.title
    if hw_data.description is not None:
        update_data["description"] = hw_data.description
    if hw_data.due_date is not None:
        update_data["due_date"] = hw_data.due_date.isoformat()
    if hw_data.priority is not None:
        if hw_data.priority not in ["low", "medium", "high"]:
            raise HTTPException(status_code=400, detail="Priority must be low, medium, or high")
        update_data["priority"] = hw_data.priority
    
    if update_data:
        await db.homework.update_one({"id": homework_id}, {"$set": update_data})
        await log_audit(current_user["id"], "therapist", "update", "homework", homework_id)
    
    updated_hw = await db.homework.find_one({"id": homework_id}, {"_id": 0})
    return Homework(**{k: parse_datetime(v) if k in ["due_date", "completed_at", "created_at"] else v for k, v in updated_hw.items()})


@router.delete("/homework/{homework_id}")
async def delete_homework(homework_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete homework"""
    hw = await db.homework.find_one({"id": homework_id, "therapist_id": current_user["id"]}, {"_id": 0})
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    await db.homework.delete_one({"id": homework_id})
    await log_audit(current_user["id"], "therapist", "delete", "homework", homework_id)
    
    return {"success": True, "message": "Homework deleted"}


@router.post("/homework/{homework_id}/complete")
async def complete_homework(homework_id: str, data: HomeworkComplete, current_user: dict = Depends(get_current_user)):
    """Client completes homework"""
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can complete homework")
    
    hw = await db.homework.find_one({"id": homework_id, "client_id": current_user["id"]}, {"_id": 0})
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    await db.homework.update_one(
        {"id": homework_id},
        {"$set": {
            "status": "completed",
            "client_notes": data.client_notes,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_audit(current_user["id"], "client", "complete", "homework", homework_id)
    return {"success": True}
