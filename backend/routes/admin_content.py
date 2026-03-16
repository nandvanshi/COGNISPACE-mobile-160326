"""
Admin Content Management Routes
Allows super_admin to create global content (assessments, protocols, 
homework templates, resources, note templates) that appear in therapist views.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user

router = APIRouter(prefix="/admin/content", tags=["admin-content"])


# ============= AUTH =============

async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


# ============= MODELS =============

class AdminContentCreate(BaseModel):
    type: str  # homework_template, protocol_template, resource, assessment, note_template
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "general"
    content: Optional[Dict[str, Any]] = {}
    tags: List[str] = []


class AdminContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


VALID_TYPES = ["homework_template", "protocol_template", "resource", "assessment", "note_template"]


# ============= CRUD ENDPOINTS =============

@router.get("/{content_type}")
async def list_admin_content(content_type: str, current_user: dict = Depends(require_super_admin)):
    """List all admin-created content of a specific type"""
    if content_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {VALID_TYPES}")
    
    items = await db.admin_content.find(
        {"type": content_type},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    return items


@router.post("/{content_type}")
async def create_admin_content(content_type: str, data: AdminContentCreate, current_user: dict = Depends(require_super_admin)):
    """Create new admin content"""
    if content_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {VALID_TYPES}")
    
    doc = {
        "id": str(uuid.uuid4()),
        "type": content_type,
        "title": data.title,
        "description": data.description or "",
        "category": data.category or "general",
        "content": data.content or {},
        "tags": data.tags,
        "source": "admin",
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.admin_content.insert_one(doc)
    doc.pop("_id", None)
    
    return doc


@router.put("/{content_type}/{item_id}")
async def update_admin_content(content_type: str, item_id: str, data: AdminContentUpdate, current_user: dict = Depends(require_super_admin)):
    """Update admin content"""
    update_fields = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.admin_content.update_one(
        {"id": item_id, "type": content_type},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    
    updated = await db.admin_content.find_one({"id": item_id}, {"_id": 0})
    return updated


@router.delete("/{content_type}/{item_id}")
async def delete_admin_content(content_type: str, item_id: str, current_user: dict = Depends(require_super_admin)):
    """Delete admin content"""
    result = await db.admin_content.delete_one({"id": item_id, "type": content_type})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": "Content deleted"}


# ============= BULK STATS =============

@router.get("")
async def get_content_stats(current_user: dict = Depends(require_super_admin)):
    """Get count of admin content by type"""
    stats = {}
    for t in VALID_TYPES:
        count = await db.admin_content.count_documents({"type": t})
        stats[t] = count
    return stats
