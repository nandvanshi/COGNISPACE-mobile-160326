# COGNISPACE - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application for practice management and clinical decision support with AI-powered diagnostic tools.

---

## Product Vision
COGNISPACE is a therapist-first clinical platform designed to help mental health professionals manage clients, sessions, documentation, and practice operations — all in one secure place.

---

## Target Users

### 1. Therapists
- Private practitioners
- Clinical psychologists
- Counselors
- Psychiatrists

### 2. Clinics & Teams
- Multi-practitioner clinics
- Mental health centers
- Assistants handling non-clinical tasks

### 3. Clients
- Individuals seeking therapy
- Patients of registered therapists

---

## Core Features

### Authentication & Access Control
- JWT-based authentication
- 4 roles: Super Admin, Therapist, Assistant, Client
- Role-based access control (RBAC)

### Client Management
- Client profiles with demographics
- Self-registration via unique therapist links
- Case history documentation
- Intake notes

### Appointments
- Create, reschedule, cancel
- Recurring appointments (weekly/biweekly)
- 60/30 minute reminders

### Session Notes
- SOAP format documentation
- Linked to appointments
- PDF export

### Assessments
- Assessment library (30+ standardized tools)
- Online administration
- Auto-scoring
- Progress tracking

### TheraGenie AI (Clinical Intelligence)
- Assessment suggestions based on client data
- Treatment protocol generation
- Homework/exercise generation
- **CogniVision**: AI-powered psychodiagnostic reports

### Payments
- Payment tracking
- Receipt generation
- Comprehensive analytics dashboard

### Notifications
- In-app notifications (bell icon)
- Email (Resend)
- WhatsApp (Twilio) - opt-in required

### Admin Features
- Therapist approval/rejection
- Subscription management
- Therapist deletion with client re-linking
- System-wide settings

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18, Tailwind CSS, Shadcn/UI |
| Backend | FastAPI (Python), Motor (async MongoDB) |
| Database | MongoDB |
| AI | Claude Sonnet 4 via Emergent LLM Key |
| Email | Resend |
| WhatsApp | Twilio |
| Scheduler | APScheduler |
| PDF | jsPDF + html2canvas |

---

## API Structure

```
/api/
├── auth/           # Authentication
├── admin/          # Super admin operations
├── clients/        # Client management
├── appointments/   # Scheduling
├── sessions/       # Session notes
├── assessments/    # Assessment management
├── payments/       # Payment tracking + reports
├── ai/             # TheraGenie AI features
├── diagnostic-reports/  # CogniVision reports
├── notifications/  # In-app notifications
├── resources/      # Resource library
└── protocols/      # Treatment protocols
```

---

## Test Credentials

| Role | Login | Password | URL |
|------|-------|----------|-----|
| Super Admin | admin | admin123 | /admin-login |
| Therapist 1 | 9807306444 | Abcd@1234 | /login |
| Therapist 2 | 7275005007 | newpassword | /login |
| Assistant | support@mindlabs.co.in | Abcd@1234 | /login |
| Client | 8299683186 | Abcd@1234 | /login |

---

## Compliance & Standards

- India Standard Time (IST)
- DD/MM/YYYY date format
- Indian Rupee (₹)
- HIPAA-minded security practices
- Consent-driven data handling
- No clinical data via WhatsApp

---

## Legal Pages
- Privacy Policy (`/privacy-policy`)
- Terms & Conditions (`/terms-conditions`)
- Clinical Disclaimer (`/clinical-disclaimer`)
- Contact/Support (`/contact`)
- About Page (`/about`)

---

## Brand
**COGNISPACE** by Vedic Wellness Solutions
*Precision Insights. Personal Growth.*
