"""
Payment management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from dependencies import get_current_user, log_audit, check_feature_enabled

router = APIRouter(prefix="/payments", tags=["payments"])


# ============= MODELS =============

class PaymentCreate(BaseModel):
    client_id: str
    amount: float
    payment_method: str = "cash"
    payment_status: Optional[str] = "paid"
    appointment_id: Optional[str] = None
    session_note_id: Optional[str] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None


class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    bill_number: str
    therapist_id: str
    therapist_name: Optional[str] = None
    client_id: str
    client_name: str
    client_code: Optional[str] = None
    amount: float
    payment_method: str
    payment_status: str
    appointment_id: Optional[str] = None
    session_note_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# ============= DEPENDENCIES =============

def get_effective_therapist_id(user: dict) -> str:
    if user["role"] == "therapist":
        return user["id"]
    elif user["role"] == "assistant":
        return user.get("therapist_id")
    return None


async def require_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["therapist", "assistant"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return current_user


async def require_active_therapist_or_assistant(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "therapist":
        if current_user.get("subscription_status") not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Subscription expired")
        return current_user
    elif current_user["role"] == "assistant":
        therapist = await db.users.find_one({"id": current_user.get("therapist_id")}, {"_id": 0})
        if not therapist or therapist.get("subscription_status") not in ["trial", "active"]:
            raise HTTPException(status_code=403, detail="Therapist subscription expired")
        return current_user
    raise HTTPException(status_code=403, detail="Access denied")


def parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


async def generate_bill_number():
    """Generate unique bill number in format BILL-YYYYMMDD-XXXX"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"BILL-{today}-"
    
    last_bill = await db.payments.find_one(
        {"bill_number": {"$regex": f"^{prefix}"}},
        {"_id": 0, "bill_number": 1},
        sort=[("bill_number", -1)]
    )
    
    if last_bill:
        try:
            last_num = int(last_bill["bill_number"].split("-")[-1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    return f"{prefix}{new_num:04d}"


# ============= PAYMENT ENDPOINTS =============

@router.post("", response_model=Payment)
async def record_payment(payment_data: PaymentCreate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Record a payment - both therapists and assistants can record"""
    therapist_id = get_effective_therapist_id(current_user)
    await check_feature_enabled(therapist_id, "payments")
    
    client = await db.users.find_one({"id": payment_data.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_therapist_id = client.get("therapist_id")
    if not client_therapist_id:
        profile = await db.client_profiles.find_one({"user_id": payment_data.client_id}, {"_id": 0})
        if profile:
            client_therapist_id = profile.get("therapist_id")
    
    if client_therapist_id != therapist_id:
        raise HTTPException(status_code=403, detail="Access denied - client not assigned to you")
    
    therapist = await db.users.find_one({"id": therapist_id}, {"_id": 0})
    
    bill_number = await generate_bill_number()
    payment_id = str(uuid.uuid4())
    
    payment_doc = {
        "id": payment_id,
        "bill_number": bill_number,
        "therapist_id": therapist_id,
        "therapist_name": therapist.get("full_name") if therapist else None,
        "client_id": payment_data.client_id,
        "client_name": client["full_name"],
        "client_code": client.get("client_id"),
        "amount": payment_data.amount,
        "payment_method": payment_data.payment_method,
        "payment_status": payment_data.payment_status or "paid",
        "appointment_id": payment_data.appointment_id,
        "session_note_id": payment_data.session_note_id,
        "notes": payment_data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payments.insert_one(payment_doc)
    await log_audit(current_user["id"], current_user["role"], "create", "payment", payment_id)
    
    # Send notification to client about payment receipt
    try:
        from routes.notifications import notify_client_payment_receipt
        await notify_client_payment_receipt(
            payment_data.client_id,
            payment_data.amount,
            payment_id
        )
    except Exception as e:
        print(f"Failed to send payment notification: {e}")
    
    return Payment(
        id=payment_id,
        bill_number=bill_number,
        therapist_id=therapist_id,
        therapist_name=payment_doc["therapist_name"],
        client_id=payment_data.client_id,
        client_name=client["full_name"],
        client_code=client.get("client_id"),
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        payment_status=payment_doc["payment_status"],
        appointment_id=payment_data.appointment_id,
        session_note_id=payment_data.session_note_id,
        notes=payment_data.notes,
        created_at=parse_datetime(payment_doc["created_at"])
    )


@router.get("", response_model=List[Payment])
async def get_payments(
    client_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get payments - filtered by role"""
    if current_user["role"] == "client":
        query = {"client_id": current_user["id"]}
    elif current_user["role"] in ["therapist", "assistant"]:
        therapist_id = get_effective_therapist_id(current_user)
        query = {"therapist_id": therapist_id}
        if client_id:
            query["client_id"] = client_id
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    payments = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    return [Payment(
        id=p["id"],
        bill_number=p.get("bill_number", ""),
        therapist_id=p["therapist_id"],
        therapist_name=p.get("therapist_name"),
        client_id=p["client_id"],
        client_name=p.get("client_name", ""),
        client_code=p.get("client_code"),
        amount=p["amount"],
        payment_method=p.get("payment_method", "cash"),
        payment_status=p.get("payment_status", "paid"),
        appointment_id=p.get("appointment_id"),
        session_note_id=p.get("session_note_id"),
        notes=p.get("notes"),
        created_at=parse_datetime(p["created_at"])
    ) for p in payments]


@router.get("/{payment_id}", response_model=Payment)
async def get_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Get single payment details"""
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if current_user["role"] == "client" and payment["client_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user["role"] in ["therapist", "assistant"]:
        therapist_id = get_effective_therapist_id(current_user)
        if payment["therapist_id"] != therapist_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return Payment(
        id=payment["id"],
        bill_number=payment.get("bill_number", ""),
        therapist_id=payment["therapist_id"],
        therapist_name=payment.get("therapist_name"),
        client_id=payment["client_id"],
        client_name=payment.get("client_name", ""),
        client_code=payment.get("client_code"),
        amount=payment["amount"],
        payment_method=payment.get("payment_method", "cash"),
        payment_status=payment.get("payment_status", "paid"),
        appointment_id=payment.get("appointment_id"),
        session_note_id=payment.get("session_note_id"),
        notes=payment.get("notes"),
        created_at=parse_datetime(payment["created_at"])
    )


@router.get("/{payment_id}/receipt")
async def get_payment_receipt(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Get payment receipt data for PDF generation"""
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Access check
    if current_user["role"] == "client" and payment["client_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user["role"] in ["therapist", "assistant"]:
        therapist_id = get_effective_therapist_id(current_user)
        if payment["therapist_id"] != therapist_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get therapist profile for receipt
    therapist = await db.users.find_one({"id": payment["therapist_id"]}, {"_id": 0, "full_name": 1, "mobile": 1, "email": 1})
    profile = await db.therapist_profiles.find_one({"user_id": payment["therapist_id"]}, {"_id": 0})
    
    clinic_name = profile.get("clinic_name", "COGNISPACE") if profile else "COGNISPACE"
    clinic_address = profile.get("clinic_address", "") if profile else ""
    show_mobile = profile.get("show_mobile_on_receipt", True) if profile else True
    show_email = profile.get("show_email_on_receipt", True) if profile else True
    
    # Format date
    created_at = payment.get("created_at", "")
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = dt.strftime("%d/%m/%Y")
            formatted_time = dt.strftime("%I:%M %p")
        except:
            formatted_date = created_at[:10]
            formatted_time = ""
    else:
        formatted_date = ""
        formatted_time = ""
    
    return {
        "id": payment["id"],
        "bill_number": payment.get("bill_number", ""),
        "clinic_name": clinic_name,
        "clinic_address": clinic_address,
        "therapist_name": therapist.get("full_name", "") if therapist else payment.get("therapist_name", ""),
        "therapist_mobile": therapist.get("mobile", "") if therapist and show_mobile else "",
        "therapist_email": therapist.get("email", "") if therapist and show_email else "",
        "client_name": payment.get("client_name", ""),
        "client_code": payment.get("client_code", ""),
        "amount": payment["amount"],
        "payment_method": payment.get("payment_method", "cash"),
        "payment_status": payment.get("payment_status", "paid"),
        "notes": payment.get("notes", ""),
        "date": formatted_date,
        "time": formatted_time,
        "created_at": payment.get("created_at", "")
    }


@router.put("/{payment_id}", response_model=Payment)
async def update_payment(payment_id: str, data: PaymentUpdate, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Update payment details"""
    therapist_id = get_effective_therapist_id(current_user)
    
    payment = await db.payments.find_one({"id": payment_id, "therapist_id": therapist_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    update_data = {}
    if data.amount is not None:
        update_data["amount"] = data.amount
    if data.payment_method is not None:
        update_data["payment_method"] = data.payment_method
    if data.payment_status is not None:
        update_data["payment_status"] = data.payment_status
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    if update_data:
        await db.payments.update_one({"id": payment_id}, {"$set": update_data})
        await log_audit(current_user["id"], current_user["role"], "update", "payment", payment_id)
    
    updated = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    return Payment(
        id=updated["id"],
        bill_number=updated.get("bill_number", ""),
        therapist_id=updated["therapist_id"],
        therapist_name=updated.get("therapist_name"),
        client_id=updated["client_id"],
        client_name=updated.get("client_name", ""),
        client_code=updated.get("client_code"),
        amount=updated["amount"],
        payment_method=updated.get("payment_method", "cash"),
        payment_status=updated.get("payment_status", "paid"),
        appointment_id=updated.get("appointment_id"),
        session_note_id=updated.get("session_note_id"),
        notes=updated.get("notes"),
        created_at=parse_datetime(updated["created_at"])
    )


@router.delete("/{payment_id}")
async def delete_payment(payment_id: str, current_user: dict = Depends(require_active_therapist_or_assistant)):
    """Delete a payment record"""
    therapist_id = get_effective_therapist_id(current_user)
    
    result = await db.payments.delete_one({"id": payment_id, "therapist_id": therapist_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    await log_audit(current_user["id"], current_user["role"], "delete", "payment", payment_id)
    return {"message": "Payment deleted"}


@router.get("/stats/summary")
async def get_payment_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_therapist_or_assistant)
):
    """Get payment statistics summary"""
    therapist_id = get_effective_therapist_id(current_user)
    
    query = {"therapist_id": therapist_id}
    
    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            query["created_at"]["$gte"] = start_date
        if end_date:
            query["created_at"]["$lte"] = end_date
    
    payments = await db.payments.find(query, {"_id": 0}).to_list(10000)
    
    total_amount = sum(p.get("amount", 0) for p in payments)
    paid_amount = sum(p.get("amount", 0) for p in payments if p.get("payment_status") == "paid")
    pending_amount = sum(p.get("amount", 0) for p in payments if p.get("payment_status") == "pending")
    
    by_method = {}
    for p in payments:
        method = p.get("payment_method", "unknown")
        by_method[method] = by_method.get(method, 0) + p.get("amount", 0)
    
    return {
        "total_transactions": len(payments),
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "by_payment_method": by_method
    }
