# COGNISPACE - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application named **COGNISPACE** for practice management and clinical decision support.

## Core Features
- **Authentication**: Secure JWT-based authentication for Therapists, Clients, Super Admins, and Assistants
- **Client Management**: Full client lifecycle management
- **Appointments**: Scheduling and management with automated notifications
- **Session Notes**: Clinical documentation
- **Messaging**: In-app communication (messenger-style with soft delete)
- **Payment Tracking**: Financial management with Credit/Debit support and receipts
- **TheraGenie & CogniVision**: AI module for clinical intelligence
- **Notifications**: WhatsApp + Email notifications using Twilio templates
- **PWA Sound & Badge**: Notification sounds and app icon badge count

## User's Preferred Language
Hindi (User communicates in Hindi/Hinglish)

## Tech Stack
- **Frontend**: React with Shadcn/UI components
- **Backend**: FastAPI (Python)
- **Database**: MongoDB Atlas
- **AI**: Anthropic Claude (User API Key)
- **Email**: Resend (User API Key)
- **SMS/WhatsApp**: Twilio (User API Key)
- **PDF Generation**: jsPDF & html2canvas

## What's Implemented ✅

### Feb 16, 2026 - Case History & Consent Workflow Rework ✅
- [x] **Case History -> Consent Flow**:
  - When therapist marks case history as complete → Consent document auto-created
  - In-app notification sent to client ("Please Sign Therapy Consent")
  - Email notification sent to client (template: consent_pending_client)
  - Client sees consent form on their dashboard until signed
  - After signing → Client gets full dashboard access
- [x] **Email Template Registered**: `consent_pending_client` added to EMAIL_TEMPLATES registry
- [x] **Flow Tested End-to-End**:
  - POST /api/case-history/{client_id}/complete → Creates consent + notifications
  - GET /api/therapy-consent/check/{client_id} → Client can check status
  - GET /api/therapy-consent/{client_id} → Client can fetch consent document
  - POST /api/therapy-consent/{client_id}/sign → Client can sign consent

### Feb 12, 2026 - Daily Summary, Consent Notification & Payment Debit
- [x] **Daily Summary Email (7 AM IST)**: Morning email to therapists/assistants with:
  - Today's appointments list
  - Pending payments summary
  - Pending session notes (therapist only)
- [x] **Consent Accept Notification**: Email to therapist/assistant when client signs consent form
  - Includes: client name, therapist name, consent details, signature date/time
- [x] **Payment Debit/Refund Feature**:
  - transaction_type field: "credit" (payment) or "debit" (refund)
  - Credit/Debit toggle buttons in payment form
  - Type column in payment table with colored badges
  - Summary card shows: Net Revenue, Credit total, Debit total
  - Debit amounts shown in red with minus sign

### Feb 12, 2026 - PWA Sound & Badge Notifications
- [x] Backend API for user notification preferences (GET/PUT /api/notifications/preferences)
- [x] Sound toggle in Settings - users can enable/disable notification sounds
- [x] Badge toggle in Settings - users can enable/disable app icon badge count
- [x] NotificationBell component plays sound on new notifications
- [x] NotificationBell updates app badge count (PWA mode)

### Feb 11, 2026 - Notification System Complete
- [x] Centralized NotificationService for WhatsApp + Email
- [x] Forgot Password functionality with email reset link
- [x] PWA login persistence (users stay logged in)
- [x] Messaging UI overhaul (mobile-responsive, soft delete)
- [x] Dynamic email sender names (therapist name for client emails)
- [x] Client self-registration email notifications

### Previous Sessions
- [x] JWT-based authentication for all roles
- [x] Admin dashboard with hash-based SPA routing
- [x] Therapist Management (View, Edit, Delete, Suspend)
- [x] Subscription Management (Assign, Extend, Trial)
- [x] Client password reset fix
- [x] Messaging UI improvements

## Notification System

### Email Notifications
| Event | Recipients | Template |
|-------|------------|----------|
| Therapist Approved | Therapist | therapist_welcome |
| Client Created | Client | client_welcome |
| Appointment Fixed | Client, Therapist, Assistant | appointment_confirmation |
| Appointment Reminder (1hr) | Client, Therapist, Assistant | appointment_reminder |
| Appointment Cancelled | Client, Therapist, Assistant | appointment_cancellation |
| Payment Received | Client | payment_receipt |
| Payment Received | Therapist, Assistant | payment_received_therapist |
| Consent Signed | Therapist, Assistant | consent_accepted |
| **Consent Pending** | **Client** | **consent_pending_client** (NEW) |
| Daily Summary (7 AM) | Therapist, Assistant | daily_summary |
| Client Self-Registration | Therapist, Assistant | client_self_registration |

### WhatsApp Templates (Twilio Approved)
| Template | SID | Usage |
|----------|-----|-------|
| cogni_1st | HXc374... | Welcome message |
| cogni_appointment | HX6d3de... | Appointment confirmation |
| cogni_rem | HX2589... | Appointment reminder |
| cogni_pay | HX34fc7... | Payment received |

## Architecture
```
/app/backend/
├── services/
│   ├── notification_service.py    # Centralized notifications
│   │   ├── send_consent_accepted_notification()  # NEW
│   │   └── send_daily_summary()                  # NEW
│   ├── email/
│   │   └── templates.py
│   │       ├── template_consent_accepted()       # NEW
│   │       └── template_daily_summary()          # NEW
│   └── scheduler/
│       └── jobs.py
│           └── send_morning_schedule_briefing()  # Enhanced
├── routes/
│   ├── payments.py                # Credit/Debit support
│   └── clinical.py                # Consent notification trigger

/app/frontend/src/
├── components/
│   └── Payments.js                # Credit/Debit UI
└── services/
    └── notificationService.js     # PWA sound & badge
```

## Payment System

### Transaction Types
| Type | Description | Display |
|------|-------------|---------|
| credit | Payment received | Green badge, positive amount |
| debit | Refund/cancellation | Red badge, negative amount |

### Payment Statistics API
```json
{
  "summary": {
    "total_transactions": 10,
    "total_amount": 50000,
    "paid_amount": 45000,
    "pending_amount": 5000,
    "credit_amount": 47000,
    "debit_amount": 2000,
    "net_amount": 45000
  }
}
```

## Test Credentials
| Role | Login ID | Password | URL |
|------|----------|----------|-----|
| Super Admin | admin | admin123 | /admin-login |
| Test Therapist | 7275005007 | Test@123 | /login |

## Known Issues
- None currently

## Pending Tasks (P1)
- [ ] Profile photo upload (Therapist & Client)
- [ ] AI-powered SOAP/DAP note generation
- [ ] Client-facing diagnostic reports sharing

## Future Tasks (P2)
- [ ] Usage tracking/rate limiting for AI features
- [ ] Note templates sharing feature
- [ ] Coupon code management backend
- [ ] N+1 query optimization in /api/clients
- [ ] WhatsApp "Daily Morning Briefing" notification

---
Last Updated: February 16, 2026
