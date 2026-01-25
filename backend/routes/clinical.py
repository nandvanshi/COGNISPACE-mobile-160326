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

router = APIRouter(tags=["clinical"], prefix="")


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
    # Flattened sections for frontend compatibility
    basic_identification: dict = {}
    presenting_complaints: dict = {}
    history_of_present_illness: dict = {}
    past_psychiatric_history: dict = {}
    medical_history: dict = {}
    family_history: dict = {}
    personal_developmental_history: dict = {}
    mental_status_examination: dict = {}
    provisional_formulation: dict = {}
    initial_therapy_plan: dict = {}
    consent_disclaimer: dict = {}


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

@router.get("/case-history/{client_id}")
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
    
    # Flatten sections for frontend compatibility
    sections = case_history.get("sections", {})
    response = {
        "id": case_history.get("id"),
        "client_id": case_history.get("client_id"),
        "therapist_id": case_history.get("therapist_id"),
        "sections": sections,
        "is_complete": case_history.get("is_complete", False),
        "created_at": case_history.get("created_at"),
        "updated_at": case_history.get("updated_at"),
        # Flattened sections
        "basic_identification": sections.get("basic_identification", {}),
        "presenting_complaints": sections.get("presenting_complaints", {}),
        "history_of_present_illness": sections.get("history_of_present_illness", {}),
        "past_psychiatric_history": sections.get("past_psychiatric_history", {}),
        "medical_history": sections.get("medical_history", {}),
        "family_history": sections.get("family_history", {}),
        "personal_developmental_history": sections.get("personal_developmental_history", {}),
        "mental_status_examination": sections.get("mental_status_examination", {}),
        "provisional_formulation": sections.get("provisional_formulation", {}),
        "initial_therapy_plan": sections.get("initial_therapy_plan", {}),
        "consent_disclaimer": sections.get("consent_disclaimer", {})
    }
    
    return response


@router.get("/case-history/check/{client_id}")
async def check_case_history(client_id: str, current_user: dict = Depends(require_therapist)):
    """Check if case history exists and is complete for a client"""
    case_history = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not case_history:
        return {"exists": False, "is_complete": False}
    
    return {
        "exists": True,
        "is_complete": case_history.get("is_complete", False)
    }


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


@router.patch("/case-history/{client_id}/section")
async def update_case_history_section(
    client_id: str, 
    section: str,
    data: dict,
    current_user: dict = Depends(require_active_therapist)
):
    """Update a specific section of case history (auto-save)"""
    case_history = await db.case_histories.find_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not case_history:
        # Create new case history
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
    
    # Update the specific section
    await db.case_histories.update_one(
        {"client_id": client_id, "therapist_id": current_user["id"]},
        {"$set": {
            f"sections.{section}": data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Section saved", "section": section}


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

@router.get("/therapy-consent/check/{client_id}")
async def check_therapy_consent(client_id: str, current_user: dict = Depends(get_current_user)):
    """Check if therapy consent exists and is signed for a client"""
    # Allow both therapist and client to check consent
    consent = None
    
    if current_user["role"] == "therapist":
        consent = await db.therapy_consents.find_one(
            {"client_id": client_id, "therapist_id": current_user["id"]},
            {"_id": 0}
        )
    elif current_user["role"] == "client":
        # Client can check their own consent
        if client_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        consent = await db.therapy_consents.find_one(
            {"client_id": client_id},
            {"_id": 0}
        )
    
    if not consent:
        return {"exists": False, "is_signed": False}
    
    return {
        "exists": True,
        "is_signed": consent.get("is_signed", False)
    }


@router.get("/therapy-consent/{client_id}")
async def get_therapy_consent(client_id: str, current_user: dict = Depends(get_current_user)):
    """Get therapy consent for a client"""
    consent = None
    therapist_id = None
    
    if current_user["role"] == "therapist":
        therapist_id = current_user["id"]
        consent = await db.therapy_consents.find_one(
            {"client_id": client_id, "therapist_id": therapist_id},
            {"_id": 0}
        )
    elif current_user["role"] == "client":
        # Client can view their own consent
        if client_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        consent = await db.therapy_consents.find_one(
            {"client_id": client_id},
            {"_id": 0}
        )
        if consent:
            therapist_id = consent.get("therapist_id")
    
    if not consent:
        if not therapist_id:
            # For clients without consent yet, get their assigned therapist
            client_profile = await db.client_profiles.find_one({"user_id": client_id}, {"_id": 0})
            if client_profile:
                therapist_id = client_profile.get("therapist_id")
        
        if therapist_id:
            # Get therapist details
            therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
            therapist_name = therapist.get("full_name", "Your Therapist") if therapist else "Your Therapist"
            
            # Get therapist profile for qualifications
            therapist_profile = await db.therapist_profiles.find_one({"therapist_id": therapist_id}, {"_id": 0})
            qualifications = therapist_profile.get("qualifications", "") if therapist_profile else ""
            
            # Default consent text - Professional Informed Consent for Psychological Services
            consent_text = f"""INFORMED CONSENT FOR PSYCHOLOGICAL SERVICES

1. Services Offered
{therapist_name} ({qualifications}) will provide psychological assessment, counseling, and therapeutic services.

2. Purpose of Therapy
Psychological therapy is a collaborative process aimed at understanding thoughts, emotions, behaviours, and experiences in order to support mental well-being and personal growth.
The nature, goals, and duration of therapy may vary depending on individual needs and will be discussed with the therapist.

3. Nature of Therapy
I understand that:
• Therapy may involve discussion of personal, emotional, or distressing topics.
• Progress may be gradual and not always linear.
• There may be times when therapy feels uncomfortable as difficult issues are explored.
• No specific outcomes or guarantees can be promised.

4. Role of the Therapist
I understand that the therapist:
• Will provide professional psychological services based on training, experience, and ethical guidelines.
• Will not provide medical advice or prescribe medication.
• Will not make decisions on my behalf.
• Will encourage my active participation in the therapeutic process.

5. Confidentiality
I understand that all information shared during therapy is confidential and will not be disclosed without my consent, except in the following circumstances:
• If there is a risk of serious harm to myself or others
• If there is disclosure of abuse of a child, elderly person, or vulnerable individual
• If required by a court of law or other legal authority
• If disclosure is required for professional supervision, where identity will be protected as far as possible

6. Records & Documentation
I understand that:
• The therapist may maintain session notes and clinical records for professional and legal purposes.
• These records are stored securely and access is restricted.
• I may request access to my records as per applicable laws and ethical guidelines.

7. Fees & Payments
I understand that:
• Therapy sessions are chargeable as per the fee structure communicated by the therapist.
• Payment is due during or after each session unless otherwise agreed.
• Missed or late-cancelled sessions may be chargeable as per the therapist's cancellation policy.

8. Appointments & Attendance
I understand that:
• Sessions are scheduled in advance.
• Punctuality is important to make effective use of session time.
• Late arrival may result in a shorter session without fee adjustment.

9. Use of Digital Systems
I consent to the use of secure digital systems for:
• Appointment scheduling
• Session documentation
• Billing and receipts
• Storage of consent and case history information
I understand that reasonable measures are taken to protect my data and privacy.

10. Client Responsibilities
I understand that:
• Therapy is most effective when I actively participate.
• I am responsible for sharing relevant information honestly.
• I may ask questions or seek clarification at any time during therapy.

11. Right to Withdraw
I understand that:
• I may discontinue therapy at any time.
• The therapist may recommend termination or referral if therapy is no longer appropriate or effective.

12. Consent Statement
I confirm that:
• I have read and understood the information provided above.
• I have had the opportunity to ask questions.
• I voluntarily consent to participate in psychological therapy."""

            consent_id = str(uuid.uuid4())
            consent = {
                "id": consent_id,
                "client_id": client_id,
                "therapist_id": therapist_id,
                "therapist_name": therapist_name,
                "consent_text": consent_text,
                "is_signed": False,
                "signature_date": None,
                "witnessed_by": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.therapy_consents.insert_one(consent)
        else:
            return {"exists": False, "is_signed": False}
    
    # Add therapist_name if missing
    if consent and not consent.get("therapist_name"):
        therapist_id = consent.get("therapist_id")
        if therapist_id:
            therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0, "full_name": 1})
            consent["therapist_name"] = therapist.get("full_name", "Your Therapist") if therapist else "Your Therapist"
    
    return consent


@router.post("/therapy-consent/{client_id}/sign")
async def sign_therapy_consent(client_id: str, signature_method: str = "digital", current_user: dict = Depends(get_current_user)):
    """Sign therapy consent - can be done by client"""
    if current_user["role"] == "client" and client_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    consent = await db.therapy_consents.find_one({"client_id": client_id}, {"_id": 0})
    
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    await db.therapy_consents.update_one(
        {"client_id": client_id},
        {"$set": {
            "is_signed": True,
            "signature_date": datetime.now(timezone.utc).isoformat(),
            "signature_method": signature_method
        }}
    )
    
    return {"message": "Consent signed successfully"}


@router.get("/consent/{client_id}", response_model=ConsentResponse)
async def get_consent(client_id: str, current_user: dict = Depends(require_therapist)):
    """Get therapy consent for a client (legacy endpoint)"""
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
    
    # Send notification to client about homework
    try:
        from routes.notifications import notify_client_homework_assigned
        await notify_client_homework_assigned(hw_data.client_id, hw_data.title)
    except Exception as e:
        print(f"Failed to send homework notification: {e}")
    
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
