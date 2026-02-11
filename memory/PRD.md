# COGNISPACE - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application named **COGNISPACE** for practice management and clinical decision support.

## Core Features
- **Authentication**: Secure JWT-based authentication for Therapists, Clients, Super Admins, and Assistants
- **Client Management**: Full client lifecycle management
- **Appointments**: Scheduling and management with automated notifications
- **Session Notes**: Clinical documentation
- **Messaging**: In-app communication (messenger-style)
- **Payment Tracking**: Financial management with receipts
- **TheraGenie & CogniVision**: AI module for clinical intelligence
- **Notifications**: WhatsApp + Email notifications using Twilio templates

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

## WhatsApp Templates (Twilio Approved)

### 1. Welcome Message (cogni_1st)
- **SID**: HXc374601a165b80488fdc52a01a140d2b
- **Used for**: Therapist/Client approval
- **Variables**: {{1}} = Full name

### 2. Appointment Confirmation (cogni_appointment)
- **SID**: HX6d3de8806ccd2116c7a5b32fe79f825f
- **Used for**: When appointment is fixed
- **Variables**: {{1}}=Client, {{2}}=Therapist, {{3}}=Date, {{4}}=Time

### 3. Appointment Reminder (cogni_rem)
- **SID**: HX25894886d0be2d48c89f2e24ac9fff8e
- **Used for**: 1 hour before appointment
- **Variables**: {{1}}=Client, {{2}}=Therapist, {{3}}=Date, {{4}}=Time

### 4. Payment Received (cogni_pay)
- **SID**: HX34fc7c7cc70b9036ccd1c350ac8acb6f
- **Used for**: When payment is recorded
- **Variables**: {{1}}=Client, {{2}}=Amount, {{3}}=Therapist, {{4}}=Date

## What's Implemented ✅

### Feb 11, 2026 - Notification System Complete
- [x] Centralized NotificationService for WhatsApp + Email
- [x] Therapist welcome (WhatsApp template + detailed email with guide)
- [x] Client welcome (WhatsApp template + detailed email with guide)
- [x] Appointment confirmation (WhatsApp + Email to client)
- [x] Appointment reminder 1 hour before (WhatsApp + Email)
- [x] Payment received notification (WhatsApp + Email)
- [x] Mobile-responsive messaging UI

### Previous Sessions
- [x] JWT-based authentication for all roles
- [x] Admin dashboard with hash-based SPA routing
- [x] Therapist Management (View, Edit, Delete, Suspend)
- [x] Subscription Management (Assign, Extend, Trial)
- [x] Client password reset fix
- [x] Messaging UI improvements

## Architecture
```
/app/backend/
├── services/
│   ├── notification_service.py    # NEW - Centralized notifications
│   ├── whatsapp/
│   │   ├── templates.py           # NEW - WhatsApp template definitions
│   │   ├── service.py             # Updated
│   │   └── twilio_provider.py     # Updated with template support
│   ├── email/
│   │   └── templates.py           # Updated with client_welcome
│   └── scheduler/
│       └── jobs.py                # Updated for 1-hour reminder
├── routes/
│   ├── admin.py                   # Updated - uses NotificationService
│   ├── clients.py                 # Updated - sends welcome notifications
│   ├── appointments.py            # Updated - sends appointment notifications
│   └── payments.py                # Updated - sends payment notifications
```

## Notification Flow

| Event | WhatsApp | Email |
|-------|----------|-------|
| Therapist Approved | ✅ cogni_1st | ✅ Detailed welcome + guide |
| Client Created | ✅ cogni_1st | ✅ Detailed welcome + guide |
| Appointment Fixed | ✅ cogni_appointment | ✅ Confirmation |
| 1 Hour Before | ✅ cogni_rem | ✅ Reminder |
| Payment Received | ✅ cogni_pay | ✅ Receipt |

## Test Credentials
| Role | Login ID | Password | URL |
|------|----------|----------|-----|
| Super Admin | admin | admin123 | /admin-login |

## Known Issues
- None currently

## Pending Tasks
- [ ] Profile photo upload (Therapist & Client)
- [ ] Forgot Password functionality
- [ ] AI-powered SOAP/DAP note generation

---
Last Updated: February 11, 2026
