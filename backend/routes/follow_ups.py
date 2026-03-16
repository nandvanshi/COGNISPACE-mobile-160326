"""
Follow-Up Intelligence System
Tracks recommended next sessions, detects overdue clients, and improves therapy continuity.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import uuid

from database import db
from dependencies import get_current_user

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])

IST = ZoneInfo("Asia/Kolkata")


# ============= AUTH HELPERS =============

def get_effective_therapist_id(user):
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    raise HTTPException(status_code=403, detail="Access denied")


async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Therapist or assistant access required")
    return current_user


# ============= MODELS =============

class RecommendSessionRequest(BaseModel):
    client_id: str
    recommended_date: str  # ISO date string e.g., "2026-03-20"
    notes: Optional[str] = ""
    session_id: Optional[str] = None  # The appointment that triggered this recommendation


# ============= FOLLOW-UP STATUS LOGIC =============

async def get_client_follow_up_status(client_id: str, therapist_id: str):
    """
    Determine follow-up status for a client:
    - booked: has upcoming appointment
    - recommended: has recommendation but no appointment booked
    - overdue: recommended date passed, no appointment
    - dropout_risk: no session for 30 days AND no upcoming appointment
    """
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%dT%H:%M:%S")

    # Check for upcoming scheduled appointment
    upcoming = await db.appointments.find_one({
        "client_id": client_id,
        "therapist_id": therapist_id,
        "status": {"$in": ["scheduled", "in_progress"]},
        "start_time": {"$gte": now_str}
    }, {"_id": 0, "id": 1, "start_time": 1})

    # Get latest recommendation
    recommendation = await db.follow_up_recommendations.find_one(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )

    # Get last completed session
    last_session = await db.appointments.find_one(
        {"client_id": client_id, "therapist_id": therapist_id, "status": "completed"},
        {"_id": 0, "id": 1, "start_time": 1, "actual_end_time": 1},
        sort=[("start_time", -1)]
    )

    # Calculate days since last session
    days_since_last = None
    if last_session:
        last_time_str = last_session.get("actual_end_time") or last_session.get("start_time", "")
        try:
            last_dt = datetime.fromisoformat(last_time_str.replace("Z", "+00:00"))
            days_since_last = (now_utc - last_dt).days
        except (ValueError, AttributeError):
            pass

    # Determine status
    if upcoming:
        status = "booked"
    elif recommendation:
        rec_date_str = recommendation.get("recommended_date", "")
        try:
            rec_date = datetime.fromisoformat(rec_date_str + "T23:59:59+00:00") if "T" not in rec_date_str else datetime.fromisoformat(rec_date_str.replace("Z", "+00:00"))
            if now_utc > rec_date:
                status = "overdue"
            else:
                status = "recommended"
        except (ValueError, AttributeError):
            status = "recommended"
    elif days_since_last is not None and days_since_last >= 30:
        status = "dropout_risk"
    elif days_since_last is not None and days_since_last >= 14 and not upcoming:
        status = "overdue"
    else:
        status = "no_recommendation"

    # Dropout risk override: 30 days no session + no upcoming
    is_dropout_risk = (days_since_last is not None and days_since_last >= 30 and not upcoming)

    return {
        "status": status,
        "is_dropout_risk": is_dropout_risk,
        "days_since_last_session": days_since_last,
        "upcoming_appointment": upcoming,
        "recommendation": recommendation,
        "last_session": last_session
    }


# ============= ENDPOINTS =============

@router.post("/recommend")
async def recommend_next_session(req: RecommendSessionRequest, current_user: dict = Depends(require_therapist_or_assistant)):
    """Set recommended next session date for a client"""
    therapist_id = get_effective_therapist_id(current_user)

    # Verify client belongs to therapist via client_profiles
    profile = await db.client_profiles.find_one(
        {"user_id": req.client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")

    doc = {
        "id": str(uuid.uuid4()),
        "client_id": req.client_id,
        "therapist_id": therapist_id,
        "recommended_date": req.recommended_date,
        "notes": req.notes or "",
        "recommended_by_session_id": req.session_id,
        "recommended_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }

    await db.follow_up_recommendations.insert_one(doc)
    doc.pop("_id", None)

    return doc


@router.get("/summary")
async def get_follow_up_summary(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get follow-up overview stats for therapist dashboard"""
    therapist_id = get_effective_therapist_id(current_user)

    # Get all active clients via client_profiles
    profiles = await db.client_profiles.find(
        {"therapist_id": therapist_id},
        {"_id": 0, "user_id": 1}
    ).to_list(500)

    stats = {"recommended": 0, "overdue": 0, "dropout_risk": 0, "booked": 0, "total_clients": len(profiles)}

    for profile in profiles:
        fu = await get_client_follow_up_status(profile["user_id"], therapist_id)
        if fu["is_dropout_risk"]:
            stats["dropout_risk"] += 1
        if fu["status"] == "recommended":
            stats["recommended"] += 1
        elif fu["status"] == "overdue":
            stats["overdue"] += 1
        elif fu["status"] == "booked":
            stats["booked"] += 1

    return stats


@router.get("/clients")
async def get_follow_up_clients(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get detailed follow-up list for all clients, sorted by priority"""
    therapist_id = get_effective_therapist_id(current_user)

    # Get clients via client_profiles and join with user data
    profiles = await db.client_profiles.find(
        {"therapist_id": therapist_id},
        {"_id": 0, "user_id": 1}
    ).to_list(500)

    result = []
    for profile in profiles:
        cid = profile["user_id"]
        fu = await get_client_follow_up_status(cid, therapist_id)

        # Skip clients with no data
        if fu["status"] == "no_recommendation" and fu["days_since_last_session"] is None:
            continue

        user = await db.users.find_one({"id": cid}, {"_id": 0, "full_name": 1, "mobile": 1, "email": 1})
        if not user:
            continue

        result.append({
            "client_id": cid,
            "client_name": user.get("full_name", "Unknown"),
            "client_mobile": user.get("mobile", ""),
            "client_email": user.get("email", ""),
            "status": fu["status"],
            "is_dropout_risk": fu["is_dropout_risk"],
            "days_since_last_session": fu["days_since_last_session"],
            "last_session_date": fu["last_session"].get("start_time") if fu["last_session"] else None,
            "recommended_date": fu["recommendation"].get("recommended_date") if fu["recommendation"] else None,
            "recommendation_notes": fu["recommendation"].get("notes") if fu["recommendation"] else None,
            "upcoming_appointment": fu["upcoming_appointment"].get("start_time") if fu["upcoming_appointment"] else None,
        })

    # Sort: overdue > dropout_risk > recommended > booked > no_recommendation
    priority = {"overdue": 0, "dropout_risk": 1, "recommended": 2, "booked": 3, "no_recommendation": 4}
    result.sort(key=lambda x: (priority.get(x["status"], 5), -(x["days_since_last_session"] or 0)))

    return result


@router.get("/retention-analytics")
async def get_retention_analytics(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get retention metrics for the therapist"""
    therapist_id = get_effective_therapist_id(current_user)
    now_utc = datetime.now(timezone.utc)

    # Total clients via client_profiles
    total_clients = await db.client_profiles.count_documents({"therapist_id": therapist_id})

    # Clients with follow-up sessions (had more than 1 completed session)
    profiles = await db.client_profiles.find(
        {"therapist_id": therapist_id},
        {"_id": 0, "user_id": 1}
    ).to_list(500)

    clients_with_followup = 0
    overdue_count = 0
    dropout_count = 0
    active_count = 0

    for profile in profiles:
        cid = profile["user_id"]
        session_count = await db.appointments.count_documents({
            "client_id": cid, "therapist_id": therapist_id, "status": "completed"
        })
        if session_count > 1:
            clients_with_followup += 1

        fu = await get_client_follow_up_status(cid, therapist_id)
        if fu["is_dropout_risk"]:
            dropout_count += 1
        if fu["status"] == "overdue":
            overdue_count += 1
        if fu["status"] in ["booked", "recommended"]:
            active_count += 1

    retention_rate = round((clients_with_followup / total_clients * 100), 1) if total_clients > 0 else 0

    # Monthly breakdown (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = (now_utc - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = (now_utc - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month_end = now_utc

        month_sessions = await db.appointments.count_documents({
            "therapist_id": therapist_id,
            "status": "completed",
            "start_time": {
                "$gte": month_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "$lt": month_end.strftime("%Y-%m-%dT%H:%M:%S")
            }
        })

        monthly_data.append({
            "month": month_start.strftime("%b %Y"),
            "sessions": month_sessions
        })

    return {
        "total_clients": total_clients,
        "clients_with_followup": clients_with_followup,
        "overdue_clients": overdue_count,
        "dropout_risk_clients": dropout_count,
        "active_clients": active_count,
        "retention_rate": retention_rate,
        "monthly_sessions": monthly_data
    }


# ============= CLIENT ENDPOINT =============

@router.get("/my-recommendation")
async def get_my_recommendation(current_user: dict = Depends(get_current_user)):
    """Get the client's latest follow-up recommendation"""
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Client access only")

    recommendation = await db.follow_up_recommendations.find_one(
        {"client_id": current_user["id"], "status": "active"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )

    if not recommendation:
        return {"has_recommendation": False}

    # Check if overdue
    now_utc = datetime.now(timezone.utc)
    rec_date_str = recommendation.get("recommended_date", "")
    is_overdue = False
    try:
        rec_date = datetime.fromisoformat(rec_date_str + "T23:59:59+00:00") if "T" not in rec_date_str else datetime.fromisoformat(rec_date_str.replace("Z", "+00:00"))
        is_overdue = now_utc > rec_date
    except (ValueError, AttributeError):
        pass

    return {
        "has_recommendation": True,
        "recommended_date": recommendation.get("recommended_date"),
        "notes": recommendation.get("notes", ""),
        "is_overdue": is_overdue,
        "created_at": recommendation.get("created_at")
    }



# ============= CLIENT JOURNEY TIMELINE =============

@router.get("/journey/{client_id}")
async def get_client_journey(client_id: str, current_user: dict = Depends(require_therapist_or_assistant)):
    """Get the complete journey timeline for a client"""
    therapist_id = get_effective_therapist_id(current_user)

    # Verify client belongs to therapist
    profile = await db.client_profiles.find_one(
        {"user_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")

    timeline = []

    # 1. Get all sessions (completed + cancelled + no_show)
    sessions = await db.appointments.find(
        {"client_id": client_id, "therapist_id": therapist_id, "status": {"$in": ["completed", "cancelled", "no_show"]}},
        {"_id": 0, "id": 1, "start_time": 1, "end_time": 1, "status": 1, "session_type": 1, "actual_duration_minutes": 1}
    ).to_list(500)

    for s in sessions:
        timeline.append({
            "type": "session",
            "date": s.get("start_time", ""),
            "status": s.get("status"),
            "session_type": s.get("session_type", ""),
            "duration_minutes": s.get("actual_duration_minutes"),
            "id": s.get("id")
        })

    # 2. Get all follow-up recommendations
    recommendations = await db.follow_up_recommendations.find(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0, "id": 1, "recommended_date": 1, "notes": 1, "created_at": 1, "status": 1}
    ).to_list(100)

    for r in recommendations:
        timeline.append({
            "type": "recommendation",
            "date": r.get("created_at", ""),
            "recommended_date": r.get("recommended_date"),
            "notes": r.get("notes", ""),
            "status": r.get("status"),
            "id": r.get("id")
        })

    # 3. Get session notes (just metadata)
    notes = await db.session_notes.find(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0, "id": 1, "created_at": 1, "note_type": 1, "appointment_id": 1}
    ).to_list(500)

    for n in notes:
        timeline.append({
            "type": "note",
            "date": n.get("created_at", ""),
            "note_type": n.get("note_type", "general"),
            "appointment_id": n.get("appointment_id"),
            "id": n.get("id")
        })

    # 4. Get assessments assigned
    assessments = await db.assessments.find(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0, "id": 1, "created_at": 1, "title": 1, "status": 1, "assessment_type": 1}
    ).to_list(100)

    for a in assessments:
        timeline.append({
            "type": "assessment",
            "date": a.get("created_at", ""),
            "title": a.get("title", ""),
            "status": a.get("status"),
            "assessment_type": a.get("assessment_type", ""),
            "id": a.get("id")
        })

    # 5. Get reminder log
    reminders = await db.follow_up_reminder_log.find(
        {"client_id": client_id, "therapist_id": therapist_id},
        {"_id": 0}
    ).to_list(100)

    for rem in reminders:
        timeline.append({
            "type": "reminder_sent",
            "date": rem.get("sent_at", ""),
            "reminder_type": rem.get("reminder_type"),
            "channel": rem.get("channel", "email")
        })

    # Sort by date descending
    def sort_key(item):
        d = item.get("date", "")
        try:
            return datetime.fromisoformat(d.replace("Z", "+00:00"))
        except (ValueError, TypeError, AttributeError):
            try:
                return datetime.strptime(d[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return datetime.min.replace(tzinfo=timezone.utc)

    timeline.sort(key=sort_key, reverse=True)

    # Calculate stats
    completed_sessions = len([s for s in sessions if s["status"] == "completed"])
    cancelled_sessions = len([s for s in sessions if s["status"] == "cancelled"])
    no_shows = len([s for s in sessions if s["status"] == "no_show"])

    # Average gap between sessions
    min_date = datetime.min.replace(tzinfo=timezone.utc)
    completed_dates = sorted([
        d for d in [sort_key(s) for s in sessions if s["status"] == "completed"]
        if d > min_date
    ])
    avg_gap_days = None
    if len(completed_dates) > 1:
        gaps = [(completed_dates[i+1] - completed_dates[i]).days for i in range(len(completed_dates) - 1)]
        avg_gap_days = round(sum(gaps) / len(gaps), 1)

    # First session date
    first_session = min(completed_dates) if completed_dates else None

    return {
        "client_id": client_id,
        "timeline": timeline[:100],  # Limit to 100 events
        "stats": {
            "total_sessions": completed_sessions,
            "cancelled_sessions": cancelled_sessions,
            "no_shows": no_shows,
            "total_recommendations": len(recommendations),
            "total_assessments": len(assessments),
            "avg_gap_days": avg_gap_days,
            "first_session_date": first_session.isoformat() if first_session else None,
            "journey_duration_days": (datetime.now(timezone.utc) - first_session).days if first_session else 0
        }
    }


# ============= ENHANCED RETENTION ANALYTICS =============

@router.get("/retention-analytics/detailed")
async def get_detailed_retention_analytics(current_user: dict = Depends(require_therapist_or_assistant)):
    """Enhanced retention analytics with deeper insights"""
    therapist_id = get_effective_therapist_id(current_user)
    now_utc = datetime.now(timezone.utc)

    profiles = await db.client_profiles.find(
        {"therapist_id": therapist_id},
        {"_id": 0, "user_id": 1}
    ).to_list(500)

    total_clients = len(profiles)
    client_analytics = []

    for profile in profiles:
        cid = profile["user_id"]
        user = await db.users.find_one({"id": cid}, {"_id": 0, "full_name": 1})
        if not user:
            continue

        sessions = await db.appointments.find(
            {"client_id": cid, "therapist_id": therapist_id, "status": "completed"},
            {"_id": 0, "start_time": 1}
        ).sort("start_time", 1).to_list(500)

        session_count = len(sessions)
        if session_count == 0:
            continue

        # Calculate avg gap
        dates = []
        for s in sessions:
            try:
                dates.append(datetime.fromisoformat(s["start_time"].replace("Z", "+00:00")))
            except (ValueError, TypeError):
                pass

        avg_gap = None
        if len(dates) > 1:
            gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates) - 1)]
            avg_gap = round(sum(gaps) / len(gaps), 1)

        days_since_last = (now_utc - dates[-1]).days if dates else None

        client_analytics.append({
            "client_id": cid,
            "client_name": user.get("full_name", "Unknown"),
            "session_count": session_count,
            "avg_gap_days": avg_gap,
            "days_since_last_session": days_since_last,
            "first_session": dates[0].isoformat() if dates else None,
            "last_session": dates[-1].isoformat() if dates else None,
        })

    # Sort by risk (most days since last session first)
    client_analytics.sort(key=lambda x: x.get("days_since_last_session") or 0, reverse=True)

    # Calculate global averages
    all_gaps = [c["avg_gap_days"] for c in client_analytics if c["avg_gap_days"] is not None]
    all_sessions = [c["session_count"] for c in client_analytics]

    return {
        "total_clients": total_clients,
        "clients_with_sessions": len(client_analytics),
        "avg_sessions_per_client": round(sum(all_sessions) / len(all_sessions), 1) if all_sessions else 0,
        "avg_gap_between_sessions": round(sum(all_gaps) / len(all_gaps), 1) if all_gaps else None,
        "client_details": client_analytics[:50],
    }


# ============= THERAPIST SETTINGS =============

class FollowUpSettingsRequest(BaseModel):
    followup_email_enabled: Optional[bool] = None
    followup_whatsapp_enabled: Optional[bool] = None


@router.get("/settings")
async def get_followup_settings(current_user: dict = Depends(require_therapist_or_assistant)):
    """Get therapist's follow-up reminder settings"""
    therapist_id = get_effective_therapist_id(current_user)

    settings = await db.therapist_settings.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0}
    )

    return {
        "followup_email_enabled": settings.get("followup_email_enabled", True) if settings else True,
        "followup_whatsapp_enabled": settings.get("followup_whatsapp_enabled", False) if settings else False,
    }


@router.put("/settings")
async def update_followup_settings(
    req: FollowUpSettingsRequest,
    current_user: dict = Depends(require_therapist_or_assistant)
):
    """Update therapist's follow-up reminder settings"""
    therapist_id = get_effective_therapist_id(current_user)

    update_data = {}
    if req.followup_email_enabled is not None:
        update_data["followup_email_enabled"] = req.followup_email_enabled
    if req.followup_whatsapp_enabled is not None:
        update_data["followup_whatsapp_enabled"] = req.followup_whatsapp_enabled

    if not update_data:
        raise HTTPException(status_code=400, detail="No settings to update")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.therapist_settings.update_one(
        {"therapist_id": therapist_id},
        {"$set": update_data, "$setOnInsert": {"therapist_id": therapist_id}},
        upsert=True
    )

    return {"message": "Settings updated", **update_data}
