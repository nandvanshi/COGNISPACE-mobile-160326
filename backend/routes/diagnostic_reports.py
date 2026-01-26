"""
Diagnostic Reports Routes
Contains endpoints for managing psychodiagnostic reports:
- Create, Read, Update, Delete reports
- Approve and Share reports with clients
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import jwt

# Router setup
router = APIRouter(tags=["Diagnostic Reports"])

# Module-level variables (set via setup function)
_db = None
_JWT_SECRET = None
_JWT_ALGORITHM = "HS256"

security = HTTPBearer()


def setup_diagnostic_reports(database, jwt_secret, jwt_algorithm="HS256"):
    """Setup function to inject dependencies from server.py"""
    global _db, _JWT_SECRET, _JWT_ALGORITHM
    _db = database
    _JWT_SECRET = jwt_secret
    _JWT_ALGORITHM = jwt_algorithm


# ============= MODELS =============

class DiagnosticReportCreate(BaseModel):
    client_id: str
    assessment_ids: List[str]
    report_content: str
    status: str = "draft"
    therapist_signature: Optional[str] = None
    therapist_reg_no: Optional[str] = None


class DiagnosticReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    therapist_id: str
    client_id: str
    assessment_ids: List[str]
    report_content: str
    status: str
    therapist_signature: Optional[str] = None
    therapist_reg_no: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    shared_at: Optional[datetime] = None


# ============= AUTH HELPERS =============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        user = await _db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_active_therapist(current_user: dict = Depends(get_current_user)):
    """Requires therapist with active/trial subscription"""
    if current_user["role"] != "therapist":
        raise HTTPException(status_code=403, detail="Therapist access required")
    status = current_user.get("status")
    if status == "suspended":
        raise HTTPException(status_code=403, detail="Your account has been suspended")
    if status == "rejected":
        raise HTTPException(status_code=403, detail="Your application was rejected")
    subscription_status = current_user.get("subscription_status")
    if subscription_status not in ["trial", "active"]:
        raise HTTPException(
            status_code=403, 
            detail="Your subscription has expired. You are in read-only mode."
        )
    return current_user


# ============= DIAGNOSTIC REPORT ENDPOINTS =============

@router.post("/diagnostic-reports", response_model=DiagnosticReport)
async def save_diagnostic_report(report: DiagnosticReportCreate, current_user: dict = Depends(require_active_therapist)):
    """Save a diagnostic report (draft or final)"""
    report_doc = {
        "id": str(uuid.uuid4()),
        "therapist_id": current_user["id"],
        "client_id": report.client_id,
        "assessment_ids": report.assessment_ids,
        "report_content": report.report_content,
        "status": report.status,
        "therapist_signature": report.therapist_signature,
        "therapist_reg_no": report.therapist_reg_no,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "approved_at": None,
        "shared_at": None
    }
    
    await _db.diagnostic_reports.insert_one(report_doc)
    report_doc.pop("_id", None)
    return DiagnosticReport(**report_doc)


@router.get("/diagnostic-reports")
async def get_diagnostic_reports(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get diagnostic reports - therapist sees all, client sees only shared"""
    query = {}
    
    if current_user["role"] == "client":
        query = {"client_id": current_user["id"], "status": "shared"}
    else:
        query = {"therapist_id": current_user["id"]}
        if client_id:
            query["client_id"] = client_id
    
    reports = await _db.diagnostic_reports.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return reports


@router.get("/diagnostic-reports/{report_id}")
async def get_diagnostic_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific diagnostic report"""
    report = await _db.diagnostic_reports.find_one({"id": report_id}, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Client can only see shared reports
    if current_user["role"] == "client":
        if report["client_id"] != current_user["id"] or report["status"] != "shared":
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if report["therapist_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return report


@router.put("/diagnostic-reports/{report_id}")
async def update_diagnostic_report(report_id: str, update_data: dict, current_user: dict = Depends(require_active_therapist)):
    """Update a diagnostic report"""
    report = await _db.diagnostic_reports.find_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    update_fields = {"updated_at": datetime.now(timezone.utc)}
    
    if "report_content" in update_data:
        update_fields["report_content"] = update_data["report_content"]
    if "therapist_signature" in update_data:
        update_fields["therapist_signature"] = update_data["therapist_signature"]
    if "therapist_reg_no" in update_data:
        update_fields["therapist_reg_no"] = update_data["therapist_reg_no"]
    
    await _db.diagnostic_reports.update_one({"id": report_id}, {"$set": update_fields})
    
    updated_report = await _db.diagnostic_reports.find_one({"id": report_id}, {"_id": 0})
    return updated_report


@router.post("/diagnostic-reports/{report_id}/approve")
async def approve_diagnostic_report(report_id: str, current_user: dict = Depends(require_active_therapist)):
    """Approve a diagnostic report (still not shared with client)"""
    report = await _db.diagnostic_reports.find_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    await _db.diagnostic_reports.update_one(
        {"id": report_id},
        {"$set": {"status": "approved", "approved_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Report approved successfully"}


@router.post("/diagnostic-reports/{report_id}/share")
async def share_diagnostic_report(report_id: str, current_user: dict = Depends(require_active_therapist)):
    """Share diagnostic report with client"""
    report = await _db.diagnostic_reports.find_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report["status"] not in ["approved", "shared"]:
        raise HTTPException(status_code=400, detail="Report must be approved before sharing")
    
    await _db.diagnostic_reports.update_one(
        {"id": report_id},
        {"$set": {"status": "shared", "shared_at": datetime.now(timezone.utc)}}
    )
    
    # Send notification to client about shared report
    try:
        from routes.notifications import notify_client_report_shared
        await notify_client_report_shared(report["client_id"], report.get("title", "Diagnostic Report"))
    except Exception as e:
        print(f"Failed to send report notification: {e}")
    
    return {"message": "Report shared with client successfully"}


@router.delete("/diagnostic-reports/{report_id}")
async def delete_diagnostic_report(report_id: str, current_user: dict = Depends(require_active_therapist)):
    """Delete a diagnostic report"""
    result = await _db.diagnostic_reports.delete_one({"id": report_id, "therapist_id": current_user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted successfully"}
