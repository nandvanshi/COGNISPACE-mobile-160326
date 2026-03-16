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


# ============= AI GENERATION =============

class AIGenerateRequest(BaseModel):
    type: str
    topic: str
    language: str = "hindi"  # default Hindi for this app
    additional_instructions: str = ""


AI_PROMPTS = {
    "homework_template": """You are a clinical psychologist creating homework assignments for therapy clients.
Create a homework template on the topic: "{topic}"
{extra}

Respond in JSON format:
{{
  "title": "Short title",
  "description": "Clear instructions for the client (2-3 paragraphs). Write in {language}.",
  "category": "one of: mindfulness, cbt, relaxation, journaling, behavioral, custom",
  "tags": ["tag1", "tag2", "tag3"]
}}""",

    "protocol_template": """You are a clinical psychologist creating a treatment protocol.
Create a structured treatment protocol on: "{topic}"
{extra}

Respond in JSON format:
{{
  "title": "Protocol name",
  "description": "Brief overview of the protocol",
  "category": "Therapy modality (CBT, DBT, ACT, EMDR, etc.)",
  "tags": ["tag1", "tag2"],
  "content": {{
    "modality": "Therapy modality",
    "condition": "Target condition",
    "sessions": [
      {{"session_number": 1, "title": "Session title", "goals": ["goal1", "goal2"]}},
      {{"session_number": 2, "title": "Session title", "goals": ["goal1", "goal2"]}},
      {{"session_number": 3, "title": "Session title", "goals": ["goal1", "goal2"]}},
      {{"session_number": 4, "title": "Session title", "goals": ["goal1", "goal2"]}}
    ]
  }}
}}""",

    "resource": """You are a clinical psychologist creating psychoeducational resources for clients.
Create a resource on: "{topic}"
{extra}

Respond in JSON format:
{{
  "title": "Resource title",
  "description": "Detailed educational content (3-5 paragraphs) for clients. Write in {language}. Include practical tips.",
  "category": "one of: worksheet, exercise, psychoeducation, reading, meditation, custom",
  "tags": ["tag1", "tag2", "tag3"]
}}""",

    "assessment": """You are a clinical psychologist creating a clinical assessment tool.
Create an assessment questionnaire on: "{topic}"
{extra}

Respond in JSON format:
{{
  "title": "Assessment name",
  "description": "Brief description of what this assessment measures",
  "category": "one of: anxiety, depression, trauma, personality, general, custom",
  "tags": ["tag1", "tag2"],
  "content": {{
    "questions": [
      {{"text": "Question 1 text", "options": [0, 1, 2, 3]}},
      {{"text": "Question 2 text", "options": [0, 1, 2, 3]}},
      {{"text": "Question 3 text", "options": [0, 1, 2, 3]}},
      {{"text": "Question 4 text", "options": [0, 1, 2, 3]}},
      {{"text": "Question 5 text", "options": [0, 1, 2, 3]}}
    ],
    "scoring": {{
      "scale": "0-3 (Not at all - Nearly every day)",
      "interpretation": {{
        "0-5": "Minimal",
        "6-10": "Mild",
        "11-15": "Moderate",
        "16-20": "Severe"
      }}
    }}
  }}
}}""",

    "note_template": """You are a clinical psychologist creating a session note template.
Create a note template structure for: "{topic}"
{extra}

Respond in JSON format:
{{
  "title": "Template name",
  "description": "When to use this template",
  "category": "one of: SOAP, DAP, BIRP, progress, intake, custom",
  "tags": ["tag1", "tag2"],
  "content": {{
    "sections": [
      {{"heading": "Section 1 heading", "placeholder": "What to write here..."}},
      {{"heading": "Section 2 heading", "placeholder": "What to write here..."}},
      {{"heading": "Section 3 heading", "placeholder": "What to write here..."}},
      {{"heading": "Section 4 heading", "placeholder": "What to write here..."}}
    ]
  }}
}}"""
}


@router.post("/{content_type}/ai-generate")
async def ai_generate_content(content_type: str, req: AIGenerateRequest, current_user: dict = Depends(require_super_admin)):
    """Use AI to generate content for a specific type"""
    import os
    import json
    
    if content_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {VALID_TYPES}")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI not configured. ANTHROPIC_API_KEY missing.")
    
    prompt_template = AI_PROMPTS.get(content_type)
    if not prompt_template:
        raise HTTPException(status_code=400, detail="AI generation not supported for this type")
    
    prompt = prompt_template.format(
        topic=req.topic,
        language=req.language,
        extra=f"Additional instructions: {req.additional_instructions}" if req.additional_instructions else ""
    )
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        generated = json.loads(response_text)
        
        # Return generated content (not saved yet - admin will review and save)
        return {
            "generated": True,
            "data": generated
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI response parse error. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
