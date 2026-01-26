# COGNISPACE - Practice Management & Clinical Decision Support

## Original Problem Statement
Build a secure, therapist-first web application for practice management and clinical decision support with AI-powered diagnostic tools.

## Core Features (Implemented)
- ✅ JWT-based authentication (Therapist, Client, Super Admin, Assistant)
- ✅ Client management with self-registration via unique therapist links
- ✅ Appointment scheduling with recurring appointments
- ✅ Session notes (SOAP format)
- ✅ Assessments with scoring
- ✅ TheraGenie AI (Claude Sonnet 4) - Assessment suggestions, Protocol generation, Homework, Diagnostic reports
- ✅ CogniVision - AI-powered psychodiagnostic report generation with PDF export
- ✅ In-app notification system (bell icon, dropdown)
- ✅ Email notifications (Resend)
- ✅ WhatsApp notifications (Twilio)
- ✅ Time-based scheduler (apscheduler)
- ✅ Payment tracking with receipts
- ✅ **Payment Reporting with analytics (NEW)**

## What's Been Implemented (Latest Session - Jan 26, 2026)

### Backend Refactoring (Completed)
1. **AI Clinical Routes** → `/app/backend/routes/ai_clinical.py`
   - `/ai/suggest-assessments`
   - `/ai/generate-protocol`
   - `/ai/generate-homework`
   - `/ai/generate-diagnostic-report`

2. **Diagnostic Reports Routes** → `/app/backend/routes/diagnostic_reports.py`
   - CRUD operations for diagnostic reports
   - Approve and share functionality

3. **Resources Routes** → `/app/backend/routes/resources.py`
   - Resource library management
   - Client assignments

4. **server.py reduction**: 2570 → 1287 lines (~50% reduction)

### Bug Fixes
- ✅ AI response parsing error (empty JSON handling)
- ✅ subscription_end_date not showing in Admin panel
- ✅ Login Page Footer Desktop Layout Fix (Jan 26, 2026)
  - Fixed footer alignment issue on desktop view
  - Changed layout structure: outer flex-col with inner flex-row for two-column layout
  - Footer now spans full width and stays centered at bottom on all screen sizes

### New Pages Added (Jan 26, 2026)
- ✅ **About Page** (`/about`) - Public-facing page with:
  - Hero section with tagline
  - "What is COGNISPACE?" section
  - "Who is it for?" cards (Therapists, Clinics, Clients)
  - Philosophy section with clinical disclaimer
  - Privacy, Ethics & Safety points
  - Compliance & Standards (IST, ₹, DD/MM/YYYY)
  - CTA buttons for Registration & Support
  - Footer with legal links

### Payment Reporting (NEW - P1 Complete)
**Backend APIs:**
- `GET /payments/stats/summary` - Basic stats
- `GET /payments/reports/detailed` - Detailed report with filters
- `GET /payments/reports/monthly-trend` - Monthly trends & growth
- `GET /payments/reports/client-wise` - Client-wise breakdown
- `GET /payments/reports/daily-summary` - Daily summary
- `GET /payments/reports/export` - CSV/JSON export

**Frontend Component:**
- `PaymentReports.js` with tabs (Overview, Transactions, By Client)
- Date range filtering
- Summary cards (Revenue, Collected, Pending, Growth)
- Monthly trend chart
- Payment method breakdown
- Export functionality

## Tech Stack
- **Frontend**: React 18, Tailwind CSS, Shadcn/UI
- **Backend**: FastAPI, Motor (async MongoDB)
- **Database**: MongoDB
- **AI**: Claude Sonnet 4 via Emergent LLM Key
- **Notifications**: Resend (Email), Twilio (WhatsApp)
- **Scheduler**: APScheduler

## Key API Endpoints
- `/api/auth/*` - Authentication
- `/api/admin/*` - Admin management
- `/api/clients/*` - Client management
- `/api/appointments/*` - Scheduling
- `/api/payments/*` - Payment tracking
- `/api/payments/reports/*` - Payment analytics (NEW)
- `/api/ai/*` - AI clinical support
- `/api/diagnostic-reports/*` - Report management

## Credentials
| Role | Login | Password | URL |
|------|-------|----------|-----|
| Super Admin | admin | admin123 | /admin-login |
| Therapist 1 | 9807306444 | Abcd@1234 | /login |
| Therapist 2 | 7275005007 | newpassword | /login |
| Client | 8299683186 | Abcd@1234 | /login |

## Upcoming Tasks (P1)
1. Profile Photo Upload backend

## Future/Backlog
- AI-powered SOAP/DAP note generation
- Usage tracking/rate limiting for CI features
- Note templates sharing
- Coupon code management
