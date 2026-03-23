"""
Admin Email Broadcasting - AI-powered email composer for Super Admin
Allows sending freeform emails to therapists, clients, or specific users.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user

router = APIRouter(prefix="/admin/email", tags=["admin-email"])


async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


class AIEmailDraftRequest(BaseModel):
    topic: str
    tone: Optional[str] = "professional"
    audience: Optional[str] = "therapists"
    additional_instructions: Optional[str] = None


class SendEmailRequest(BaseModel):
    subject: str
    html_body: str
    text_body: Optional[str] = None
    recipient_type: str  # all_therapists, all_clients, by_plan, specific
    plan_filter: Optional[str] = None  # for by_plan: free, basic, premium, etc.
    specific_ids: Optional[List[str]] = None  # for specific recipients


@router.get("/recipients/summary")
async def get_recipient_summary(current_user: dict = Depends(require_super_admin)):
    """Get summary of available recipients grouped by type"""
    therapists = await db.users.find(
        {"role": "therapist", "status": {"$ne": "deleted"}},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "mobile": 1}
    ).to_list(1000)

    clients = await db.users.find(
        {"role": "client", "status": {"$ne": "deleted"}},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "mobile": 1}
    ).to_list(5000)

    # Get subscription plans for therapists
    plan_counts = {}
    for t in therapists:
        sub = await db.subscriptions.find_one(
            {"therapist_id": t["id"], "status": "active"},
            {"_id": 0, "plan_name": 1}
        )
        plan = sub.get("plan_name", "No Plan") if sub else "No Plan"
        plan_counts[plan] = plan_counts.get(plan, 0) + 1

    therapists_with_email = [t for t in therapists if t.get("email")]
    clients_with_email = [c for c in clients if c.get("email")]

    return {
        "therapists": {
            "total": len(therapists),
            "with_email": len(therapists_with_email),
            "by_plan": plan_counts
        },
        "clients": {
            "total": len(clients),
            "with_email": len(clients_with_email)
        }
    }


@router.get("/recipients/list")
async def get_recipients_list(
    role: str = "therapist",
    plan: Optional[str] = None,
    current_user: dict = Depends(require_super_admin)
):
    """Get list of recipients for selection"""
    query = {"role": role, "status": {"$ne": "deleted"}}
    users = await db.users.find(query, {"_id": 0, "id": 1, "full_name": 1, "email": 1, "mobile": 1}).to_list(5000)

    result = []
    for u in users:
        entry = {
            "id": u["id"],
            "full_name": u.get("full_name", ""),
            "email": u.get("email", ""),
            "mobile": u.get("mobile", ""),
        }

        if role == "therapist" and plan:
            sub = await db.subscriptions.find_one(
                {"therapist_id": u["id"], "status": "active"},
                {"_id": 0, "plan_name": 1}
            )
            user_plan = sub.get("plan_name", "No Plan") if sub else "No Plan"
            if plan != user_plan:
                continue
            entry["plan"] = user_plan

        result.append(entry)

    return result


@router.post("/ai-draft")
async def ai_generate_email_draft(req: AIEmailDraftRequest, current_user: dict = Depends(require_super_admin)):
    """Use AI to generate an email draft"""
    import os
    import json

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI not configured")

    prompt = f"""You are an email copywriter for COGNISPACE, a therapy practice management platform. 
Write a professional email for the following:

Topic: {req.topic}
Tone: {req.tone}
Audience: {req.audience}
{f'Additional notes: {req.additional_instructions}' if req.additional_instructions else ''}

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "subject": "Email subject line",
  "html_body": "<p>HTML formatted email body. Use <p>, <strong>, <em>, <ul>, <li> tags. Keep it concise and impactful. Sign off as Team CogniSpace.</p>",
  "text_body": "Plain text version of the email"
}}"""

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        generated = json.loads(response_text)
        return {"generated": True, "data": generated}

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI response parse error. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/send")
async def send_bulk_email(req: SendEmailRequest, current_user: dict = Depends(require_super_admin)):
    """Send email to selected recipients"""
    from services.email.registry import EmailProviderRegistry
    from services.email.base import EmailMessage

    # Build recipient list
    recipients = []

    if req.recipient_type == "all_therapists":
        users = await db.users.find(
            {"role": "therapist", "status": {"$ne": "deleted"}, "email": {"$exists": True, "$ne": ""}},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1}
        ).to_list(1000)
        recipients = users

    elif req.recipient_type == "all_clients":
        users = await db.users.find(
            {"role": "client", "status": {"$ne": "deleted"}, "email": {"$exists": True, "$ne": ""}},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1}
        ).to_list(5000)
        recipients = users

    elif req.recipient_type == "by_plan":
        if not req.plan_filter:
            raise HTTPException(status_code=400, detail="plan_filter required for by_plan type")
        therapists = await db.users.find(
            {"role": "therapist", "status": {"$ne": "deleted"}, "email": {"$exists": True, "$ne": ""}},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1}
        ).to_list(1000)
        for t in therapists:
            sub = await db.subscriptions.find_one(
                {"therapist_id": t["id"], "status": "active"},
                {"_id": 0, "plan_name": 1}
            )
            plan = sub.get("plan_name", "No Plan") if sub else "No Plan"
            if plan == req.plan_filter:
                recipients.append(t)

    elif req.recipient_type == "specific":
        if not req.specific_ids:
            raise HTTPException(status_code=400, detail="specific_ids required")
        users = await db.users.find(
            {"id": {"$in": req.specific_ids}, "email": {"$exists": True, "$ne": ""}},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1}
        ).to_list(5000)
        recipients = users

    if not recipients:
        raise HTTPException(status_code=400, detail="No recipients with email addresses found")

    # Wrap body in base template
    from services.email.templates import get_base_template
    styled_html = get_base_template(req.html_body, req.subject)

    # Send emails
    sent = 0
    failed = 0
    errors = []

    for recipient in recipients:
        email = recipient.get("email")
        if not email:
            continue
        try:
            message = EmailMessage(
                to=email,
                subject=req.subject,
                html_body=styled_html,
                text_body=req.text_body or ""
            )
            result = await EmailProviderRegistry.send_email(message)
            if result.success:
                sent += 1
            else:
                failed += 1
                errors.append(f"{email}: {result.error}")
        except Exception as e:
            failed += 1
            errors.append(f"{email}: {str(e)}")

    # Log the broadcast
    broadcast_id = str(uuid.uuid4())
    await db.admin_email_broadcasts.insert_one({
        "id": broadcast_id,
        "subject": req.subject,
        "recipient_type": req.recipient_type,
        "plan_filter": req.plan_filter,
        "total_recipients": len(recipients),
        "sent": sent,
        "failed": failed,
        "sent_by": current_user["id"],
        "sent_at": datetime.now(timezone.utc).isoformat()
    })

    return {
        "broadcast_id": broadcast_id,
        "total_recipients": len(recipients),
        "sent": sent,
        "failed": failed,
        "errors": errors[:10] if errors else []
    }


@router.get("/history")
async def get_email_history(current_user: dict = Depends(require_super_admin)):
    """Get history of sent email broadcasts"""
    broadcasts = await db.admin_email_broadcasts.find(
        {},
        {"_id": 0}
    ).sort("sent_at", -1).to_list(50)
    return broadcasts
