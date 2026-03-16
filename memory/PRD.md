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
- **Mobile-First Therapist View**: Separate mobile UI with bottom navigation

## User's Preferred Language
Hindi (User communicates in Hindi/Hinglish)

## Tech Stack
- **Frontend**: React with Shadcn/UI components
- **Backend**: FastAPI (Python)
- **Database**: MongoDB Atlas
- **AI**: Anthropic Claude (User API Key)
- **Email**: Resend (User API Key)
- **SMS/WhatsApp**: Twilio (User API Key)
- **PDF Generation**: iframe-based print approach

## What's Implemented

### March 6, 2026 - Mobile Therapist View P0 Fixes
- [x] **Client Context Navigation Fix**: When navigating from client profile to Notes/Messages/TheraGenie in mobile view, the client context (selectedClientId) is now properly maintained via React Router state and navContext prop
- [x] **All Secondary Views in Mobile**: Added messages, protocols, assessments, payment-reports, homework-templates, resource-library views to mobile rendering
- [x] **Mobile Back Button**: Back button in secondary views navigates to client profile if came from there, otherwise goes to dashboard home
- [x] **More Tab Navigation**: All More menu items (homework-templates, resource-library, availability, recurring, assistants, profile, settings, support) now properly navigate to correct views
- [x] **Settings from More Tab**: Settings item from More tab opens the settings modal correctly

### March 6, 2026 - Messaging Typing Bug Fix
- [x] **Extracted MessageInput component**: Created a React.memo-wrapped MessageInput component with its own local state, preventing parent re-renders from causing typing lag
- [x] **useCallback on handleSendMessage**: Wrapped send handler with useCallback to prevent unnecessary re-renders

### March 6, 2026 - Client PDF Download Improvement
- [x] **Iframe-based approach**: Replaced window.open with hidden iframe for PDF print dialog to avoid popup blockers
- [x] **Fallback mechanism**: Falls back to window.open if iframe approach fails
- [x] **Better cleanup**: Iframe removed from DOM after use

### March 6, 2026 - Resource Creation Safeguard
- [x] **Null-safe content rendering**: Fixed potential crash in ResourcesTab when resource.content is null/undefined

### March 16, 2026 - Admin Content Library
- [x] **Admin Panel**: New "Content Library" section in Super Admin Dashboard
- [x] **5 Content Types**: homework_template, protocol_template, resource, assessment, note_template - all CRUD operational
- [x] **Therapist Integration**: Admin content automatically appears in therapist's existing tabs (Homework Templates, Protocol Templates, Resources, Assessment Library)
- [x] **Access Control**: Only super_admin can create/edit/delete admin content; therapists can only view/use
- [x] **Backward Compatible**: All existing therapist functionality untouched; admin content is additive only
- [x] **Testing**: 22/22 backend tests passed, frontend UI verified

### March 8, 2026 - Scheduler Timezone & UTC Date Fix
- [x] **Root Cause 1**: All CronTrigger jobs were running on UTC instead of IST because `timezone` param was only on scheduler, not on individual CronTriggers
- [x] **Root Cause 2**: All date range queries in scheduled jobs used IST `.isoformat()` (e.g., `2026-03-07T00:00:00+05:30`) but database stores dates in UTC format (e.g., `2026-03-07T18:30:00Z`), causing MongoDB string comparisons to fail
- [x] **Fix**: Explicitly passed `timezone=IST_TZ` to each CronTrigger in scheduler.py
- [x] **Fix**: Converted all date range queries in jobs.py to UTC format using `.astimezone(timezone.utc).strftime()` before querying
- [x] **Fix**: Also fixed `timedelta(hours=5, minutes=30)` manual IST conversion to use proper `.astimezone(IST)`
- [x] **Jobs fixed**: `send_daily_payment_statement`, `send_morning_schedule_briefing`, `check_appointment_reminders`, `check_pending_session_notes`, `check_subscription_expiry`
- Client Appointment Request Feature
- WhatsApp Template Integration (cogni_t_apreq, cogni_t_daysh)
- Payment Calculation Fixes
- Slug-Based Public Booking URL
- Availability Logic Fix
- Therapist Mobile View Scaffolding
- Mobile Home Tab Backend (/api/therapist/dashboard-stats)
- Consent separated from Case History
- Case History UI Consistency
- Subscription & Feature Toggle System
- Cash Settlement Flow
- Payment Reports Dashboard
- Client Self-Registration
- Public Booking Calendar
- Mobile-First Client UI
- Shared Resources Feature
- Homework Templates
- In-App Notifications

### March 16, 2026 - Follow-Up Intelligence System (Phase 1-2)
- [x] Backend: 5 API endpoints for follow-up recommendations, summary, client list, retention analytics, client self-view
- [x] Frontend: Checkout dialog "Recommend Next Session" checkbox with date picker
- [x] Frontend: Follow-Up Dashboard with summary cards, client list, retention analytics
- [x] Frontend: Therapist & Assistant sidebar nav integration
- [x] Frontend: Client home tab follow-up reminder card
- [x] Fixed: Client-therapist mapping to use client_profiles collection
- [x] Testing: 17/17 backend tests pass

### March 16, 2026 - Follow-Up Intelligence System (Phase 3-4)
- [x] TherapistOverview (desktop): Follow-Up Intelligence card with Booked/Recommended/Overdue/Dropout Risk + urgent clients list
- [x] MobileTherapistView: Follow-Up strip with 4 status counts in HomeTab
- [x] AssistantOverview: Follow-Up Intelligence card with stats + urgent client tags
- [x] ClientDashboard: Enhanced follow-up reminder with "Book Your Session" CTA button, overdue/recommended differentiation
- [x] Testing: 14/14 backend tests pass, all frontend code verified

### March 16, 2026 - Follow-Up Intelligence System (Phase 5) + Automated Reminders
- [x] Client Journey Timeline: API returns complete history (sessions, assessments, recommendations, reminders), new tab in Client Profile
- [x] Deep Retention Analytics: Per-client metrics (session count, avg gap, days since last visit) + global averages
- [x] Follow-Up Reminder Settings: Therapist can toggle Email/WhatsApp reminders on/off via Settings
- [x] 4 Email Templates: 2-day before, same day, 1-week missed, 30-day re-engagement (warm, positive tone)
- [x] Automated Scheduler Job: Runs every 30 min, sends Email reminders based on recommendation dates
- [x] WhatsApp reminder structure ready (pending Twilio template approval)
- [x] Testing: 21/22 backend tests pass, all frontend code verified

## Pending Tasks

### P0 - Critical
- [ ] Production deployment login fix (blocked - platform issue)

### P1 - High Priority
- [ ] Profile photo upload (Therapist & Client)
- [ ] AI-powered SOAP/DAP note generation
- [ ] N+1 Query in /api/clients - FIXED (batch $in query)

### P2 - Medium Priority
- [ ] WhatsApp follow-up templates (awaiting Twilio approval from user)
- [ ] Usage tracking/rate limiting for AI features
- [ ] Homework Templates & Resource Library management (Global templates)
- [ ] Coupon code management backend

### Future Tasks
- [ ] Google Calendar integration for automatic event creation (user deferred)
- [ ] Voice input (Speech-to-Text) for session notes
- [ ] Note templates sharing feature
- [ ] Automated follow-up reminders (WhatsApp/Email)

## Key Technical Architecture

### Mobile View Pattern
- `useIsMobile` hook detects viewport < 1024px
- Mobile: renders `MobileTherapistView` with bottom navigation (Home, Clients, Schedule, Payments, More)
- Desktop: renders traditional sidebar + content layout
- Client profiles: Full-page at `/therapist/clients/:id`
- Secondary views: Rendered in mobile wrapper with back button
- Client context: Passed via `navContext` prop through `location.state`

### Key Files
- `/app/frontend/src/pages/TherapistDashboard.js` - Main dashboard with mobile/desktop switching
- `/app/frontend/src/components/therapist/MobileTherapistView.js` - Mobile view container
- `/app/frontend/src/components/ClientProfilePage.js` - Client profile with tabs
- `/app/frontend/src/components/SessionNotes.js` - Session notes (accepts navContext)
- `/app/frontend/src/components/Messaging.js` - Messaging with isolated MessageInput
- `/app/frontend/src/components/ai-clinical/index.js` - TheraGenie AI (accepts navContext)
- `/app/frontend/src/components/FollowUpDashboard.js` - Follow-up dashboard with analytics
- `/app/backend/routes/follow_ups.py` - Follow-up Intelligence System APIs

### Test Credentials
- Therapist: mobile=7275005007, password=Test@123
- Client: mobile=9235555549, password=Test@123
- Super Admin: mobile=7275005000, password=Test@123

---
Last Updated: March 16, 2026
