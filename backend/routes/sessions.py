"""
Session Notes and Messaging routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user, log_audit, check_feature_enabled

router = APIRouter(tags=["sessions"])


# ============= MODELS =============

class SessionNoteCreate(BaseModel):
    client_id: str
    appointment_id: Optional[str] = None
    template_type: str = "SOAP"
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None
    intervention: Optional[str] = None
    response: Optional[str] = None
    session_duration: Optional[int] = None
    next_session_goals: Optional[str] = None


class SessionNoteUpdate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None
    intervention: Optional[str] = None
    response: Optional[str] = None
    session_duration: Optional[int] = None
    next_session_goals: Optional[str] = None


class SessionNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    client_name: Optional[str] = None
    appointment_id: Optional[str] = None
    appointment_date: Optional[str] = None
    template_type: str
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    data: Optional[str] = None
    intervention: Optional[str] = None
    response: Optional[str] = None
    session_duration: Optional[int] = None
    next_session_goals: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class MessageCreate(BaseModel):
    recipient_id: str
    content: str


class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    sender_id: str
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None
    recipient_id: str
    recipient_name: Optional[str] = None
    content: str
    is_read: bool = False
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


# ============= SESSION NOTES ENDPOINTS =============

@router.post("/session-notes", response_model=SessionNote)
async def create_session_note(note_data: SessionNoteCreate, current_user: dict = Depends(require_active_therapist)):
    """Create a new session note - Requires completed case history and signed consent"""
    await check_feature_enabled(current_user["id"], "session_notes")
    
    case_history = await db.case_histories.find_one(
        {"client_id": note_data.client_id, "therapist_id": current_user["id"]},
        {"_id": 0, "is_complete": 1}
    )
    
    if not case_history:
        raise HTTPException(status_code=400, detail="Case history must be completed before creating session notes.")
    
    if not case_history.get("is_complete", False):
        raise HTTPException(status_code=400, detail="Case history is incomplete. Please complete all required sections.")
    
    consent = await db.therapy_consents.find_one(
        {"client_id": note_data.client_id, "therapist_id": current_user["id"]},
        {"_id": 0, "is_signed": 1}
    )
    
    if not consent or not consent.get("is_signed", False):
        raise HTTPException(status_code=400, detail="Therapy consent must be signed before creating session notes.")
    
    client = await db.clients.find_one({"id": note_data.client_id}, {"_id": 0})
    if not client:
        client = await db.users.find_one({"id": note_data.client_id, "role": "client"}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    appointment_date = None
    if note_data.appointment_id:
        appointment = await db.appointments.find_one({"id": note_data.appointment_id}, {"_id": 0})
        if appointment:
            appointment_date = appointment.get("start_time", "").split("T")[0] if appointment.get("start_time") else None
    
    note_id = str(uuid.uuid4())
    note_doc = {
        "id": note_id,
        "therapist_id": current_user["id"],
        "client_id": note_data.client_id,
        "client_name": client.get("full_name"),
        "appointment_id": note_data.appointment_id,
        "appointment_date": appointment_date,
        "template_type": note_data.template_type,
        "subjective": note_data.subjective,
        "objective": note_data.objective,
        "assessment": note_data.assessment,
        "plan": note_data.plan,
        "data": note_data.data,
        "intervention": note_data.intervention,
        "response": note_data.response,
        "session_duration": note_data.session_duration,
        "next_session_goals": note_data.next_session_goals,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    
    await db.session_notes.insert_one(note_doc)
    await log_audit(current_user["id"], "therapist", "create", "session_note", note_id)
    
    return SessionNote(**{k: parse_datetime(v) if k in ["created_at", "updated_at"] else v for k, v in note_doc.items()})


@router.get("/session-notes", response_model=List[SessionNote])
async def get_session_notes(
    client_id: Optional[str] = None,
    current_user: dict = Depends(require_therapist)
):
    """Get session notes"""
    query = {"therapist_id": current_user["id"]}
    if client_id:
        query["client_id"] = client_id
    
    notes = await db.session_notes.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return [SessionNote(**{k: parse_datetime(v) if k in ["created_at", "updated_at"] else v for k, v in note.items()}) for note in notes]


@router.get("/session-notes/{note_id}", response_model=SessionNote)
async def get_session_note(note_id: str, current_user: dict = Depends(require_therapist)):
    """Get single session note"""
    note = await db.session_notes.find_one({"id": note_id, "therapist_id": current_user["id"]}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    return SessionNote(**{k: parse_datetime(v) if k in ["created_at", "updated_at"] else v for k, v in note.items()})


@router.put("/session-notes/{note_id}", response_model=SessionNote)
async def update_session_note(note_id: str, data: SessionNoteUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update session note"""
    note = await db.session_notes.find_one({"id": note_id, "therapist_id": current_user["id"]}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    for field in ["subjective", "objective", "assessment", "plan", "data", "intervention", "response", "session_duration", "next_session_goals"]:
        value = getattr(data, field)
        if value is not None:
            update_data[field] = value
    
    await db.session_notes.update_one({"id": note_id}, {"$set": update_data})
    await log_audit(current_user["id"], "therapist", "update", "session_note", note_id)
    
    updated = await db.session_notes.find_one({"id": note_id}, {"_id": 0})
    return SessionNote(**{k: parse_datetime(v) if k in ["created_at", "updated_at"] else v for k, v in updated.items()})


@router.delete("/session-notes/{note_id}")
async def delete_session_note(note_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete session note"""
    result = await db.session_notes.delete_one({"id": note_id, "therapist_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session note not found")
    
    await log_audit(current_user["id"], "therapist", "delete", "session_note", note_id)
    return {"message": "Session note deleted"}


# ============= MESSAGING ENDPOINTS =============

@router.post("/messages", response_model=Message)
async def send_message(msg_data: MessageCreate, current_user: dict = Depends(get_current_user)):
    """Send a message"""
    if current_user["role"] == "therapist":
        await check_feature_enabled(current_user["id"], "messaging")
    
    recipient = await db.users.find_one({"id": msg_data.recipient_id}, {"_id": 0})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    message_id = str(uuid.uuid4())
    message_doc = {
        "id": message_id,
        "sender_id": current_user["id"],
        "sender_name": current_user.get("full_name", "Unknown"),
        "sender_role": current_user["role"],
        "recipient_id": msg_data.recipient_id,
        "recipient_name": recipient.get("full_name", "Unknown"),
        "content": msg_data.content,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message_doc)
    
    return Message(**{k: parse_datetime(v) if k == "created_at" else v for k, v in message_doc.items()})


@router.get("/messages", response_model=List[Message])
async def get_messages(
    with_user: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get messages for current user"""
    query = {"$or": [{"sender_id": current_user["id"]}, {"recipient_id": current_user["id"]}]}
    
    if with_user:
        query = {
            "$or": [
                {"sender_id": current_user["id"], "recipient_id": with_user},
                {"sender_id": with_user, "recipient_id": current_user["id"]}
            ]
        }
    
    messages = await db.messages.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return [Message(**{k: parse_datetime(v) if k == "created_at" else v for k, v in msg.items()}) for msg in messages]


@router.put("/messages/{message_id}/read")
async def mark_message_read(message_id: str, current_user: dict = Depends(get_current_user)):
    """Mark message as read"""
    result = await db.messages.update_one(
        {"id": message_id, "recipient_id": current_user["id"]},
        {"$set": {"is_read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {"message": "Message marked as read"}


@router.get("/messages/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread messages"""
    count = await db.messages.count_documents({"recipient_id": current_user["id"], "is_read": False})
    return {"unread_count": count}
