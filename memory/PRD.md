# COGNISPACE - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application named **COGNISPACE** for practice management and clinical decision support.

## Core Features
- **Authentication**: Secure JWT-based authentication for Therapists, Clients, Super Admins, and Assistants
- **Client Management**: Full client lifecycle management
- **Appointments**: Scheduling and management with automated notifications
- **Session Notes**: Clinical documentation
- **Messaging**: In-app communication (messenger-style with soft delete)
- **Payment Tracking**: Financial management with receipts
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

### Feb 12, 2026 - PWA Sound & Badge Notifications
- [x] Backend API for user notification preferences (GET/PUT /api/notifications/preferences)
- [x] Sound toggle in Settings - users can enable/disable notification sounds
- [x] Badge toggle in Settings - users can enable/disable app icon badge count
- [x] NotificationBell component plays sound on new notifications
- [x] NotificationBell updates app badge count (PWA mode)
- [x] notificationService.js manages sound/badge with localStorage fallback
- [x] Fixed linting errors (E722 bare except) in payments.py and scheduler/jobs.py

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

## Architecture
```
/app/backend/
├── services/
│   ├── notification_service.py    # Centralized notifications
│   ├── whatsapp/
│   │   ├── templates.py           # WhatsApp template definitions
│   │   ├── service.py             # WhatsApp service
│   │   └── twilio_provider.py     # Twilio integration
│   ├── email/
│   │   └── templates.py           # Email templates
│   └── scheduler/
│       └── jobs.py                # Scheduled jobs
├── routes/
│   ├── notifications.py           # Notification API + User preferences
│   ├── auth.py                    # Auth + Forgot Password
│   ├── clients.py                 # Client management
│   ├── appointments.py            # Appointment management
│   └── payments.py                # Payment management

/app/frontend/src/
├── services/
│   └── notificationService.js     # PWA sound & badge service
├── components/
│   ├── NotificationBell.js        # Notification bell with badge
│   ├── NotificationSettings.js    # Sound/Badge settings UI
│   └── Settings.js                # Main settings dialog
└── public/
    └── notification-sound.mp3     # Notification sound file
```

## Notification Flow

| Event | WhatsApp | Email | PWA |
|-------|----------|-------|-----|
| Therapist Approved | ✅ cogni_1st | ✅ Detailed welcome | - |
| Client Created | ✅ cogni_1st | ✅ Detailed welcome | - |
| Appointment Fixed | ✅ cogni_appointment | ✅ Confirmation | 🔔 Sound + Badge |
| 1 Hour Before | ✅ cogni_rem | ✅ Reminder | 🔔 Sound + Badge |
| Payment Received | ✅ cogni_pay | ✅ Receipt | 🔔 Sound + Badge |
| New Message | - | - | 🔔 Sound + Badge |

## Test Credentials
| Role | Login ID | Password | URL |
|------|----------|----------|-----|
| Super Admin | admin | admin123 | /admin-login |

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
Last Updated: February 12, 2026
