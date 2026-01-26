"""
Subscription and Support Ticket management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Union
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from dependencies import (
    get_current_user, log_audit, DEFAULT_FEATURE_TOGGLES
)

router = APIRouter(tags=["subscriptions"])


# ============= MODELS =============

class SubscriptionPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    price: float
    duration_days: int
    features: Union[List[str], dict]  # Support both list (legacy) and dict (new)
    max_clients: Optional[int] = None
    feature_toggles: Optional[dict] = None
    created_at: datetime


class SubscriptionPlanCreate(BaseModel):
    name: str
    price: float
    duration_days: int
    features: Union[List[str], dict] = []  # Support both formats
    max_clients: Optional[int] = None
    feature_toggles: Optional[dict] = None


class TicketCreate(BaseModel):
    subject: str
    category: str
    description: str
    priority: str = "normal"


class TicketReply(BaseModel):
    message: str


class TicketStatusUpdate(BaseModel):
    status: str


class SupportTicket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    therapist_name: Optional[str] = None
    therapist_email: Optional[str] = None
    subject: str
    category: str
    description: str
    priority: str
    status: str
    replies: List[dict] = []
    created_at: str
    updated_at: str


class CouponCode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    code: str
    discount_percent: int
    valid_until: Optional[str] = None
    max_uses: Optional[int] = None
    current_uses: int = 0
    is_active: bool = True
    created_at: str


class CouponCreate(BaseModel):
    code: str
    discount_percent: int
    valid_until: Optional[str] = None
    max_uses: Optional[int] = None


# ============= DEPENDENCIES =============

async def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


# ============= SUPPORT TICKET ENDPOINTS =============

@router.post("/support/tickets", response_model=SupportTicket)
async def create_support_ticket(ticket_data: TicketCreate, current_user: dict = Depends(get_current_user)):
    """Create a support ticket - therapists only"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Only therapists can create support tickets")
    
    now_utc = datetime.now(timezone.utc).isoformat()
    ticket_id = str(uuid.uuid4())
    
    ticket_doc = {
        "id": ticket_id,
        "therapist_id": current_user["id"],
        "therapist_name": current_user.get("full_name", "Unknown"),
        "therapist_email": current_user.get("email"),
        "subject": ticket_data.subject,
        "category": ticket_data.category,
        "description": ticket_data.description,
        "priority": ticket_data.priority,
        "status": "open",
        "replies": [],
        "created_at": now_utc,
        "updated_at": now_utc
    }
    
    await db.support_tickets.insert_one(ticket_doc)
    await log_audit(current_user["id"], "therapist", "create", "support_ticket", ticket_id)
    
    return SupportTicket(**ticket_doc)


@router.get("/support/tickets")
async def get_support_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get support tickets - therapists see own, super_admin sees all"""
    if current_user["role"] == "therapist":
        query = {"therapist_id": current_user["id"]}
    elif current_user["role"] == "super_admin":
        query = {}
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    
    tickets = await db.support_tickets.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return tickets


@router.get("/support/tickets/{ticket_id}")
async def get_support_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    """Get single ticket details"""
    ticket = await db.support_tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user["role"] == "therapist" and ticket["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ticket


@router.post("/support/tickets/{ticket_id}/reply")
async def reply_to_ticket(ticket_id: str, reply_data: TicketReply, current_user: dict = Depends(get_current_user)):
    """Reply to a support ticket"""
    ticket = await db.support_tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user["role"] == "therapist" and ticket["therapist_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    reply = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_role": current_user["role"],
        "user_name": current_user.get("full_name", "Unknown"),
        "message": reply_data.message,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.support_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"replies": reply},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Reply added", "reply": reply}


@router.put("/support/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, status_data: TicketStatusUpdate, current_user: dict = Depends(require_super_admin)):
    """Update ticket status - admin only"""
    valid_statuses = ["open", "in_progress", "closed"]
    if status_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")
    
    result = await db.support_tickets.update_one(
        {"id": ticket_id},
        {"$set": {"status": status_data.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return {"message": "Status updated"}


@router.get("/admin/support/stats")
async def get_support_stats(current_user: dict = Depends(require_super_admin)):
    """Get support ticket statistics for admin dashboard"""
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    stats = await db.support_tickets.aggregate(pipeline).to_list(10)
    
    result = {"open": 0, "in_progress": 0, "closed": 0, "total": 0}
    for s in stats:
        result[s["_id"]] = s["count"]
        result["total"] += s["count"]
    
    return result


@router.get("/admin/dashboard-stats")
async def get_admin_dashboard_stats(current_user: dict = Depends(require_super_admin)):
    """Get comprehensive admin dashboard statistics"""
    now_utc = datetime.now(timezone.utc)
    
    total_therapists = await db.users.count_documents({"role": "therapist", "status": "approved"})
    pending_applications = await db.therapist_applications.count_documents({"status": "pending_approval"})
    suspended_therapists = await db.users.count_documents({"role": "therapist", "status": "suspended"})
    total_clients = await db.users.count_documents({"role": "client"})
    
    active_subscriptions = await db.users.count_documents({
        "role": "therapist", 
        "status": "approved",
        "subscription_status": {"$in": ["active", "trial"]}
    })
    expired_subscriptions = await db.users.count_documents({
        "role": "therapist",
        "status": "approved", 
        "subscription_status": "expired"
    })
    
    seven_days_later = (now_utc + timedelta(days=7)).isoformat()
    trial_ending_soon = await db.subscriptions.count_documents({
        "status": "active",
        "plan_name": "Trial",
        "end_date": {"$lte": seven_days_later, "$gte": now_utc.isoformat()}
    })
    
    open_tickets = await db.support_tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    total_assistants = await db.users.count_documents({"role": "assistant", "status": {"$ne": "deleted"}})
    
    return {
        "therapists": {
            "total": total_therapists,
            "pending_approval": pending_applications,
            "suspended": suspended_therapists
        },
        "clients": {
            "total": total_clients
        },
        "subscriptions": {
            "active": active_subscriptions,
            "expired": expired_subscriptions,
            "trial_ending_soon": trial_ending_soon
        },
        "support": {
            "open_tickets": open_tickets
        },
        "assistants": {
            "total": total_assistants
        }
    }


# ============= SUBSCRIPTION PLAN ENDPOINTS =============

@router.get("/admin/subscription-plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans(current_user: dict = Depends(require_super_admin)):
    plans = await db.subscription_plans.find({}, {"_id": 0}).to_list(1000)
    return [SubscriptionPlan(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in plan.items()}) for plan in plans]


@router.post("/admin/subscription-plans", response_model=SubscriptionPlan)
async def create_subscription_plan(plan_data: SubscriptionPlanCreate, current_user: dict = Depends(require_super_admin)):
    plan_id = str(uuid.uuid4())
    toggles = {**DEFAULT_FEATURE_TOGGLES, **(plan_data.feature_toggles or {})}
    plan_doc = {
        "id": plan_id,
        "name": plan_data.name,
        "price": plan_data.price,
        "duration_days": plan_data.duration_days,
        "features": plan_data.features,
        "max_clients": plan_data.max_clients,
        "feature_toggles": toggles,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.subscription_plans.insert_one(plan_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "subscription_plan", plan_id)
    
    return SubscriptionPlan(**{k: datetime.fromisoformat(v) if k == "created_at" else v for k, v in plan_doc.items()})


@router.delete("/admin/subscription-plans/{plan_id}")
async def delete_subscription_plan(plan_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.subscription_plans.delete_one({"id": plan_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    await log_audit(current_user["id"], current_user["role"], "delete", "subscription_plan", plan_id)
    return {"message": "Plan deleted"}


@router.put("/admin/subscription-plans/{plan_id}/feature-toggles")
async def update_plan_feature_toggles(plan_id: str, feature_toggles: dict, current_user: dict = Depends(require_super_admin)):
    plan = await db.subscription_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    merged_toggles = {**DEFAULT_FEATURE_TOGGLES, **plan.get("feature_toggles", {}), **feature_toggles}
    
    await db.subscription_plans.update_one(
        {"id": plan_id},
        {"$set": {"feature_toggles": merged_toggles}}
    )
    
    await log_audit(current_user["id"], current_user["role"], "update_toggles", "subscription_plan", plan_id)
    return {"message": "Feature toggles updated", "feature_toggles": merged_toggles}


@router.get("/admin/subscription-plans/{plan_id}")
async def get_subscription_plan(plan_id: str, current_user: dict = Depends(require_super_admin)):
    plan = await db.subscription_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/admin/therapists/{therapist_id}/assign-subscription")
async def assign_subscription(
    therapist_id: str,
    plan_id: str,
    payment_amount: float = 0,
    payment_method: str = "admin_assigned",
    current_user: dict = Depends(require_super_admin)
):
    """Assign a subscription plan to a therapist"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    plan = await db.subscription_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=plan["duration_days"])
    
    subscription_id = str(uuid.uuid4())
    subscription_doc = {
        "id": subscription_id,
        "therapist_id": therapist_id,
        "plan_id": plan_id,
        "plan_name": plan["name"],
        "start_date": now.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active",
        "payment_amount": payment_amount,
        "payment_method": payment_method,
        "created_at": now.isoformat(),
        "assigned_by": current_user["id"]
    }
    
    await db.subscriptions.insert_one(subscription_doc)
    
    await db.users.update_one(
        {"id": therapist_id},
        {"$set": {
            "subscription_status": "active",
            "subscription_plan": plan["name"]
        }}
    )
    
    await log_audit(current_user["id"], "super_admin", "assign_subscription", "therapist", therapist_id,
                   {"plan_id": plan_id, "subscription_id": subscription_id})
    
    return {"message": "Subscription assigned", "subscription_id": subscription_id, "end_date": end_date.isoformat()}


@router.post("/admin/therapists/{therapist_id}/extend-subscription")
async def extend_subscription(
    therapist_id: str,
    days: int,
    current_user: dict = Depends(require_super_admin)
):
    """Extend a therapist's current subscription"""
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    current_end = datetime.fromisoformat(subscription["end_date"].replace('Z', '+00:00'))
    new_end = current_end + timedelta(days=days)
    
    await db.subscriptions.update_one(
        {"id": subscription["id"]},
        {"$set": {"end_date": new_end.isoformat()}}
    )
    
    await db.users.update_one(
        {"id": therapist_id},
        {"$set": {"subscription_status": "active"}}
    )
    
    await log_audit(current_user["id"], "super_admin", "extend_subscription", "therapist", therapist_id,
                   {"days": days, "new_end_date": new_end.isoformat()})
    
    return {"message": f"Subscription extended by {days} days", "new_end_date": new_end.isoformat()}


@router.post("/admin/therapists/{therapist_id}/assign-trial")
async def assign_trial(therapist_id: str, days: int = 14, current_user: dict = Depends(require_super_admin)):
    """Assign a trial period to a therapist"""
    therapist = await db.users.find_one({"id": therapist_id, "role": "therapist"}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=days)
    
    subscription_id = str(uuid.uuid4())
    subscription_doc = {
        "id": subscription_id,
        "therapist_id": therapist_id,
        "plan_id": None,
        "plan_name": "Trial",
        "start_date": now.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active",
        "payment_amount": 0,
        "payment_method": "trial",
        "created_at": now.isoformat(),
        "assigned_by": current_user["id"]
    }
    
    await db.subscriptions.insert_one(subscription_doc)
    
    await db.users.update_one(
        {"id": therapist_id},
        {"$set": {
            "subscription_status": "trial",
            "subscription_plan": "Trial"
        }}
    )
    
    await log_audit(current_user["id"], "super_admin", "assign_trial", "therapist", therapist_id,
                   {"days": days, "subscription_id": subscription_id})
    
    return {"message": f"Trial assigned for {days} days", "end_date": end_date.isoformat()}


@router.get("/admin/therapists/{therapist_id}/subscription")
async def get_therapist_subscription(therapist_id: str, current_user: dict = Depends(require_super_admin)):
    """Get therapist's subscription details"""
    subscription = await db.subscriptions.find_one(
        {"therapist_id": therapist_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    if not subscription:
        return {"subscription": None}
    
    return {"subscription": subscription}


# ============= COUPON ENDPOINTS =============

@router.get("/admin/coupons", response_model=List[CouponCode])
async def get_coupons(current_user: dict = Depends(require_super_admin)):
    coupons = await db.coupons.find({}, {"_id": 0}).to_list(1000)
    return [CouponCode(**c) for c in coupons]


@router.post("/admin/coupons", response_model=CouponCode)
async def create_coupon(coupon_data: CouponCreate, current_user: dict = Depends(require_super_admin)):
    existing = await db.coupons.find_one({"code": coupon_data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    
    coupon_id = str(uuid.uuid4())
    coupon_doc = {
        "id": coupon_id,
        "code": coupon_data.code.upper(),
        "discount_percent": coupon_data.discount_percent,
        "valid_until": coupon_data.valid_until,
        "max_uses": coupon_data.max_uses,
        "current_uses": 0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.coupons.insert_one(coupon_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "coupon", coupon_id)
    
    return CouponCode(**coupon_doc)


@router.delete("/admin/coupons/{coupon_id}")
async def delete_coupon(coupon_id: str, current_user: dict = Depends(require_super_admin)):
    result = await db.coupons.delete_one({"id": coupon_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    await log_audit(current_user["id"], current_user["role"], "delete", "coupon", coupon_id)
    return {"message": "Coupon deleted"}
