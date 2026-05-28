# COGNISPACE - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application named **COGNISPACE** for practice management and clinical decision support.

## User's Preferred Language
Hindi/Hinglish

## Tech Stack
- Frontend: React 18 + Shadcn/UI + Tailwind CSS
- Backend: FastAPI (Python)
- Database: MongoDB (Atlas / Local)
- AI: Anthropic Claude (Emergent LLM Key)
- Email: Resend API
- WhatsApp: Twilio API
- Scheduling: APScheduler

## What's Implemented (Complete Feature List)

### Authentication & Users
- [x] JWT auth for all 4 roles (Therapist, Client, Assistant, Super Admin)
- [x] Therapist application + admin approval flow
- [x] Client self-registration via unique link
- [x] Forgot/reset password (email-based)

### Client Management
- [x] Full CRUD with demographics
- [x] Case history form (multi-section)
- [x] Therapy consent with e-signature
- [x] Client journey timeline

### Appointments & Scheduling
- [x] Availability settings (weekly hours, duration, buffer)
- [x] Auto slot generation
- [x] Calendar view (month/week)
- [x] Check-in/check-out with actual duration
- [x] Recurring appointments
- [x] Client appointment requests (approve/decline)
- [x] Public booking page with slug URL
- [x] Blocked time management

### Session & Clinical
- [x] Session notes with voice input (Web Speech API)
- [x] 35+ assessment library + custom assessments
- [x] Protocol templates
- [x] Homework assignments + templates
- [x] Resource library + assignments
- [x] Diagnostic reports (AI-generated)

### AI (TheraGenie)
- [x] Assessment suggestions
- [x] Protocol generation
- [x] Homework generation
- [x] Diagnostic report generation
- [x] Admin content AI generation
- [x] Email broadcast AI drafting

### Payments & Billing
- [x] Credit/debit payment recording
- [x] Auto bill numbering
- [x] Printable PDF receipts
- [x] Payment reports (summary, monthly, client-wise, daily, export)
- [x] Cash settlement flow (assistant → therapist)

### Follow-Up Intelligence
- [x] Recommend next session at checkout
- [x] Follow-up dashboard with stats
- [x] Retention analytics
- [x] Automated email reminders (4 templates)
- [x] Client self-view of recommendations

### Messaging & Notifications
- [x] In-app messenger (therapist ↔ client)
- [x] Notification bell with types
- [x] PWA badge + sound
- [x] Email notifications (Resend)
- [x] WhatsApp notifications (Twilio)
- [x] Per-event notification preferences

### Admin Panel
- [x] Dashboard with stats
- [x] Therapist management (full CRUD)
- [x] Client management + orphaned linking
- [x] Subscription plans with feature toggles
- [x] Coupon codes
- [x] Content library (5 types + AI generation)
- [x] Email broadcast
- [x] Support tickets
- [x] All Users view (filters, search, pagination)
- [x] System Config (.env viewer)
- [x] Update Log (timeline of code changes)
- [x] Build timestamp (auto-update on restart)
- [x] Timezone migration tool

### Mobile & PWA
- [x] Mobile-first therapist view (<1024px)
- [x] PWA install prompt
- [x] Notification badge + sound

### Bug Fixes (Latest Session - May 2026)
- [x] Declined appointments filtered from all schedule/calendar views
- [x] Notification Clear All + Mark All Read route ordering fix
- [x] Build timestamp auto-update on server start
- [x] Delete Payment Record option for therapist/assistant (with confirmation dialog) — Feb 2026

## Pending Tasks

### P1 - High Priority
- [ ] Profile Photo Upload (actual file upload, currently mocked)
- [ ] AI-Powered SOAP/DAP Notes

### P2 - Medium Priority
- [ ] WhatsApp follow-up templates (Twilio approval pending)
- [ ] AI usage tracking/rate limiting
- [ ] Coupon code redemption flow (client-side)

### Future
- [ ] Google Calendar Integration
- [ ] Video Consultation
- [ ] Multi-Language Support
- [ ] Online Payment Gateway (Razorpay/Stripe)
- [ ] Two-Factor Authentication

## Key Technical Notes
- Timezone: All dates stored as UTC ISO strings. Use `date_utils.py` for IST conversion.
- Date queries: Use DATE COMPONENT matching (`start_time[:10]`) for both old and new formats.
- Notification routes: Static routes (`/clear-all`, `/mark-all-read`) MUST come before `/{notification_id}`.
- MongoDB: Always exclude `_id` from responses.

## Test Credentials
- Therapist: mobile=7275005007, password=Test@123
- Client: mobile=9235555549, password=Test@123
- Super Admin: username=admin, password=admin123

## Key Files
- `/app/COGNISPACE_DOCUMENTATION.md` - Complete app documentation
- `/app/backend/services/date_utils.py` - Centralized timezone utilities
- `/app/backend/services/scheduler/jobs.py` - Background cron jobs
- `/app/backend/build_info.txt` - Auto-updated build timestamp
- `/app/backend/update_log.txt` - Manual update log entries
- `/app/VPS_DEPLOYMENT_GUIDE.md` - VPS deployment instructions

---
Last Updated: May 15, 2026
