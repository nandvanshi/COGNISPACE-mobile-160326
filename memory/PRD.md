# COGNISPACE - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application named **COGNISPACE** for practice management and clinical decision support.

## Core Features
- **Authentication**: Secure JWT-based authentication for Therapists, Clients, Super Admins, and Assistants
- **Client Management**: Full client lifecycle management
- **Appointments**: Scheduling and management
- **Session Notes**: Clinical documentation
- **Messaging**: In-app communication
- **Payment Tracking**: Financial management
- **TheraGenie & CogniVision**: AI module for clinical intelligence, editable/exportable psychodiagnostic reports (PDF)
- **Client Self-Registration**: Unique, permanent therapist links for client self-onboarding
- **Client-Facing Reports**: Clients can view shared diagnostic reports
- **In-App Notifications**: Role-aware, real-time notifications including morning briefings and daily payment summaries
- **Admin Features**: Therapist management, deletion with orphan client handling
- **Payment Reporting**: Comprehensive revenue analysis dashboard
- **Legal Pages**: About, Privacy Policy, Terms, Clinical Disclaimer, Refund Policy, Contact/Support

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

## Architecture
```
/app/
├── backend/
│   ├── routes/
│   │   ├── admin.py
│   │   ├── subscriptions.py
│   │   └── ai_clinical.py
│   ├── services/
│   │   ├── email/
│   │   └── whatsapp/
└── frontend/
    └── src/
        ├── components/
        │   ├── admin/
        │   │   ├── TherapistApplications.js
        │   │   ├── SubscriptionManagement.js
        │   │   └── TherapistManagement.js
        ├── pages/
        │   ├── SuperAdminDashboard.js (hash-based routing)
        │   ├── TherapistDashboard.js
        │   └── AssistantDashboard.js
        └── utils/
            └── constants.js (centralized)
```

## What's Implemented ✅
- [x] JWT-based authentication for all roles
- [x] Admin dashboard with hash-based SPA routing
- [x] Therapist Management (View, Edit, Delete, Suspend)
- [x] Subscription Management (Assign, Extend, Trial)
- [x] Therapist Applications approval workflow
- [x] Welcome email notifications on approval
- [x] Centralized specialization options
- [x] Browser back button support (hash routing)
- [x] Client management
- [x] Basic AI clinical features

## Current Session (Feb 7, 2026)
### Verified Working:
- ✅ Admin -> Therapist Management -> Subscription assignment
  - Dialog opens correctly
  - Plans load in dropdown
  - Assignment succeeds with toast notification

## Known Issues
1. **WhatsApp Messages** (P2) - Twilio Error 63016, needs pre-approved Message Template
   - **Status**: BLOCKED - Awaiting user decision on template creation approach
2. **Korean text in AI content** (P2) - May appear in AI-generated content
   - **Status**: NOT STARTED

## Pending/Upcoming Tasks
- [ ] Profile photo upload (Therapist & Client) - **MOCKED**
- [ ] Forgot Password functionality
- [ ] AI-powered SOAP/DAP note generation
- [ ] Usage tracking/rate limiting for AI features
- [ ] Therapist note templates sharing
- [ ] Coupon code management backend logic
- [ ] `/api/clients` N+1 query optimization

## Test Credentials
| Role | Login ID | Password | URL |
|------|----------|----------|-----|
| Super Admin | admin | admin123 | /admin-login |

## Deployment
- Target domain: `cognispace.in`
- No hardcoded URLs in codebase
- See `/app/memory/DEPLOYMENT.md` for setup guide

---
Last Updated: February 7, 2026
