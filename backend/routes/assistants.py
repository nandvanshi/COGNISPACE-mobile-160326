"""
Assistant management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import (
    get_current_user, hash_password, log_audit, check_feature_enabled
)

router = APIRouter(tags=["assistants"])


# ============= ASSISTANT MODELS =============

class AssistantCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class AssistantUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class AssistantResponse(BaseModel):
    id: str
    therapist_id: str
    email: str
    full_name: str
    role: str = "assistant"
    status: str = "active"
    created_at: datetime


# ============= DEPENDENCIES =============

async def require_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    status = current_user.get("status")
    if status == "suspended":
        raise HTTPException(status_code=403, detail="Your account has been suspended")
    return current_user


async def require_active_therapist(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    subscription_status = current_user.get("subscription_status")
    if subscription_status not in ["trial", "active"]:
        raise HTTPException(status_code=403, detail="Subscription expired")
    return current_user


async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


# ============= ASSISTANT ENDPOINTS =============

@router.post("/assistants", response_model=AssistantResponse)
async def create_assistant(assistant_data: AssistantCreate, current_user: dict = Depends(require_active_therapist)):
    """Therapist creates an assistant linked to their account"""
    await check_feature_enabled(current_user["id"], "assistants")
    
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
        "mobile": "",
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


@router.get("/assistants", response_model=List[AssistantResponse])
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
        role="assistant",
        status=a.get("status", "active"),
        created_at=datetime.fromisoformat(a["created_at"])
    ) for a in assistants]


@router.get("/assistants/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Get single assistant details"""
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
        role="assistant",
        status=assistant.get("status", "active"),
        created_at=datetime.fromisoformat(assistant["created_at"])
    )


@router.put("/assistants/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(assistant_id: str, data: AssistantUpdate, current_user: dict = Depends(require_active_therapist)):
    """Update assistant details"""
    assistant = await db.users.find_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"_id": 0}
    )
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    update_data = {}
    if data.full_name:
        update_data["full_name"] = data.full_name
    if data.email:
        existing = await db.users.find_one({"email": data.email, "id": {"$ne": assistant_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = data.email
    
    if update_data:
        await db.users.update_one({"id": assistant_id}, {"$set": update_data})
        await log_audit(current_user["id"], current_user["role"], "update", "assistant", assistant_id)
    
    updated = await db.users.find_one({"id": assistant_id}, {"_id": 0})
    return AssistantResponse(
        id=updated["id"],
        therapist_id=updated["therapist_id"],
        email=updated["email"],
        full_name=updated["full_name"],
        role="assistant",
        status=updated.get("status", "active"),
        created_at=datetime.fromisoformat(updated["created_at"])
    )


@router.put("/assistants/{assistant_id}/suspend")
async def suspend_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Suspend an assistant"""
    result = await db.users.update_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"$set": {"status": "suspended"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    await log_audit(current_user["id"], current_user["role"], "suspend", "assistant", assistant_id)
    return {"message": "Assistant suspended"}


@router.put("/assistants/{assistant_id}/activate")
async def activate_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Activate a suspended assistant"""
    result = await db.users.update_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"$set": {"status": "active"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    await log_audit(current_user["id"], current_user["role"], "activate", "assistant", assistant_id)
    return {"message": "Assistant activated"}


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: str, current_user: dict = Depends(require_therapist)):
    """Soft delete an assistant"""
    result = await db.users.update_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"$set": {"status": "deleted"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    await log_audit(current_user["id"], current_user["role"], "delete", "assistant", assistant_id)
    return {"message": "Assistant deleted"}


@router.put("/assistants/{assistant_id}/reset-password")
async def reset_assistant_password(assistant_id: str, new_password: str, current_user: dict = Depends(require_therapist)):
    """Reset assistant password"""
    result = await db.users.update_one(
        {"id": assistant_id, "therapist_id": current_user["id"], "role": "assistant"},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    await log_audit(current_user["id"], current_user["role"], "reset_password", "assistant", assistant_id)
    return {"message": "Password reset successfully"}


@router.get("/admin/assistants", response_model=List[AssistantResponse])
async def get_all_assistants(current_user: dict = Depends(require_super_admin)):
    """Super Admin: Get all assistants"""
    assistants = await db.users.find(
        {"role": "assistant", "status": {"$ne": "deleted"}},
        {"_id": 0}
    ).to_list(1000)
    
    return [AssistantResponse(
        id=a["id"],
        therapist_id=a["therapist_id"],
        email=a["email"],
        full_name=a["full_name"],
        role="assistant",
        status=a.get("status", "active"),
        created_at=datetime.fromisoformat(a["created_at"])
    ) for a in assistants]


@router.post("/admin/assistants", response_model=AssistantResponse)
async def admin_create_assistant(
    therapist_id: str,
    assistant_data: AssistantCreate,
    current_user: dict = Depends(require_super_admin)
):
    """Super Admin: Create assistant for any therapist"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
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
    await log_audit(current_user["id"], "super_admin", "create", "assistant", assistant_id)
    
    return AssistantResponse(
        id=assistant_id,
        therapist_id=therapist_id,
        email=assistant_data.email,
        full_name=assistant_data.full_name,
        role="assistant",
        status="active",
        created_at=datetime.fromisoformat(assistant_doc["created_at"])
    )
