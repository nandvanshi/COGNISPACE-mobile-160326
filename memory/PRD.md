# TherapyFlow - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application for managing a therapy practice and supporting clinical decision-making.

## Core Requirements

### User Roles
- **Therapist**: Primary user - manages clients, sessions, assessments, protocols, and payments
- **Client**: Secondary user - receives therapy, completes assessments and homework
- **Super Admin**: Platform administrator - approves therapists, manages subscriptions and coupons

### Authentication
- Secure email/password auth with JWT
- Mobile-first authentication for clients (mobile number as primary identifier)
- Super Admin has separate login portal at `/admin-login`
- Therapist self-registration disabled - must apply and be approved by Super Admin

### Practice Management (MVP)
- Client profiles with extended fields (guardian name, age, address, etc.)
- Appointment scheduling (double-booking prevention)
- Session notes (SOAP & DAP templates)
- Secure messaging between therapist and client
- Basic payment tracking

### Clinical Support
- Assessment library (PHQ-9, GAD-7, PCL-5, ASRS, BDI-II, DASS-21, YBOCS, PSS)
- Custom assessment creation by therapists
- Therapy protocol builder with templates (CBT-Anxiety, DBT-Emotion Regulation, ACT-Depression)
- Homework/resource sharing

### Super Admin Features
- Therapist application approval workflow
- **Manual therapist creation** (without application)
- **Edit therapist details**
- **Profile photo support for therapists**
- Therapist management (suspend/activate/reset password)
- **Subscription details with remaining validity**
- **View therapist's assigned clients**
- Client management with full details
- **Assigned therapist name in client profiles**
- **Navigation: Client → Therapist profile, Therapist → Clients list**
- Subscription plan management (CRUD)
- Coupon code management (CRUD)

### Key Exclusions
- No teletherapy/video calls
- No insurance billing integration
- No automated AI diagnosis

---

## What's Been Implemented

### Phase 1: Core Infrastructure (COMPLETED)
- [x] FastAPI backend with MongoDB
- [x] React frontend with Tailwind CSS + Shadcn UI
- [x] JWT-based authentication with role-based access control
- [x] User registration and login for clients

### Phase 2: Therapist Features (COMPLETED)
- [x] Client management (create, view, update profiles)
- [x] Expanded client profiles (guardian name, age, address, etc.)
- [x] Clinical assessment library (8 standard assessments)
- [x] Custom assessment creation
- [x] Assessment assignment and completion
- [x] Therapy protocol templates
- [x] Homework assignment

### Phase 3: Super Admin & Onboarding (COMPLETED - Jan 17, 2026)
- [x] Super Admin login portal (`/admin-login`)
- [x] Super Admin dashboard with navigation
- [x] Therapist application workflow (apply, approve, reject)
- [x] Therapist management (suspend/activate/reset password)
- [x] Client management for admins
- [x] Subscription plan CRUD
- [x] Coupon code management

### Phase 4: Admin Panel Enhancements (COMPLETED - Jan 17, 2026)
- [x] **P0 Fixed**: Subscription Plans module (was double /api prefix)
- [x] **P0 Fixed**: Coupon Codes module (was double /api prefix)
- [x] **Manual therapist creation** - Add therapist directly without application
- [x] **Edit therapist details** - Update name, email, credentials, specialization
- [x] **Profile photo support** - Photo URL storage and display
- [x] **Subscription details** - Show plan, status, and remaining validity days
- [x] **View therapist's clients** - List all assigned clients per therapist
- [x] **Full client details** - Age, guardian, address, emergency contact, intake summary
- [x] **Therapist name in client profiles** - Shows assigned therapist
- [x] **Navigation** - Client → Therapist, Therapist → Clients list

### Phase 5: Subscription Read-Only Mode (COMPLETED - Jan 17, 2026)
- [x] **Read-only mode for expired/cancelled subscriptions**:
  - Allowed: View clients, profiles, session notes, assessments, protocols, homework
  - Blocked: Create/update clients, appointments, notes, assignments, messages
- [x] **Backend enforcements**:
  - `require_therapist` - allows any approved therapist (read operations)
  - `require_active_therapist` - requires trial/active subscription (write operations)
  - `is_subscription_active()` helper function
  - `GET /api/auth/subscription-status` endpoint
- [x] **Frontend banner**: Persistent warning when subscription expired
  - "Your subscription has expired. You are currently in read-only mode."
  - Shows on all therapist pages
  - "Contact Support" button

### Phase 6: Client Edit Functionality (COMPLETED - Jan 17, 2026)
- [x] **Edit client profile details**:
  - Full name, mobile, email (with validation)
  - Age, guardian name, address, referred by
  - Emergency contact name and phone
  - Intake summary
- [x] **Edit client credentials**:
  - Mobile update with 10-digit validation
  - Email update with uniqueness check
  - Password reset by therapist (`POST /api/clients/{id}/reset-password`)
- [x] **Client profile photo/avatar**:
  - URL-based photo storage (`profile_photo` field)
  - Initials fallback in UI
- [x] **Client ID immutability**:
  - `client_id` (e.g., CL-XXXXXX) remains unchanged
  - Shown as "(immutable)" in edit dialog

### Phase 7: Data Isolation Security Fix (COMPLETED - Jan 18, 2026)
- [x] **Client self-registration DISABLED**:
  - `POST /api/auth/register` returns 403
  - Login page shows message: "Clients: Please contact your therapist to create an account for you"
  - No registration tab on login page
- [x] **Therapist data isolation**:
  - `GET /api/clients` returns ONLY clients assigned to current therapist
  - `GET /api/clients/{id}` returns 404 for unassigned clients
  - `PUT /api/clients/{id}` returns 404 for unassigned clients
  - `POST /api/clients/{id}/reset-password` returns 403 for unassigned clients
- [x] **Super Admin access preserved**:
  - `GET /api/admin/clients` returns ALL clients
  - `PUT /api/admin/clients/{id}` works for any client
  - Admin can view and edit any client details

### Phase 8: Super Admin UX Improvements (COMPLETED - Jan 18, 2026)
- [x] **Search functionality in Therapist Management**:
  - Search input with magnifying glass icon
  - Client-side filtering by name, email, mobile, credentials
  - Real-time result count (e.g., "Showing 1 of 20 therapists")
  - Clear button (X) to reset search
  - Empty state message when no results match

### Phase 9: P0 Subscription Management (COMPLETED - Jan 18, 2026)
- [x] **Automatic trial subscription for new therapists**:
  - Manual creation via `POST /api/admin/therapists/create` assigns 30-day trial
  - Approved applications via `POST /api/admin/therapist-applications/{id}/approve` assigns 30-day trial
  - UI shows info message: "New therapists automatically receive a 30-day trial subscription"
- [x] **Startup migration for existing therapists**:
  - Backend `@app.on_event("startup")` automatically migrates therapists without subscriptions
  - Assigns 30-day free trial to any therapist missing subscription_status
- [x] **Super Admin subscription management UI**:
  - Subscription dialog accessible via "Subscription" button on each therapist card
  - **Assign Free Trial**: One-click 30-day trial assignment
  - **Assign Subscription Plan**: Dropdown with all available plans (Basic, Silver, etc.)
  - **Extend Subscription**: Add extra days to current subscription end date
- [x] **Subscription changes persist immediately**:
  - Therapist profiles update instantly after subscription changes
  - Subscription badges show status (trial/active/expired) and plan name
  - Days remaining displayed with color coding (green/warning/expired)
- [x] **Fix Missing Subscriptions button**:
  - `POST /api/admin/migrate-subscriptions` endpoint
  - Bulk assigns trial subscriptions to all therapists without one
- [x] **Backend endpoints verified**:
  - `POST /api/admin/therapists/{id}/assign-subscription` - Assign plan
  - `POST /api/admin/therapists/{id}/extend-subscription` - Extend by days
  - `POST /api/admin/therapists/{id}/assign-trial` - Assign 30-day trial
  - `GET /api/admin/therapists/{id}/subscription` - Get subscription details

### Phase 10: Appointment Calendar (COMPLETED - Jan 18, 2026)
- [x] **Therapist-wise scheduling**:
  - Each therapist has their own appointment calendar
  - Appointments filtered by logged-in therapist's ID
- [x] **Client association**:
  - Appointments linked to specific clients via client dropdown
  - Client name displayed on appointment cards
- [x] **Double-booking prevention**:
  - Backend validates no overlapping appointments for same therapist
  - Cancelled appointments free up time slots for rebooking
  - Adjacent (back-to-back) appointments are allowed
- [x] **Appointment status management**:
  - Status options: `scheduled`, `completed`, `cancelled`
  - Complete appointment via checkmark button or `POST /api/appointments/{id}/complete`
  - Cancel appointment via X button or `POST /api/appointments/{id}/cancel`
  - Status badges with color coding (blue=scheduled, green=completed, red=cancelled)
- [x] **Full CRUD operations**:
  - Create: `POST /api/appointments` with client_id, start_time, end_time, notes
  - Read: `GET /api/appointments` (list) and `GET /api/appointments/{id}` (single)
  - Update: `PUT /api/appointments/{id}` to reschedule time or update notes
  - Delete: `DELETE /api/appointments/{id}`
- [x] **Subscription read-only mode respected**:
  - All write endpoints use `require_active_therapist` dependency
  - Expired subscription therapists cannot create/update/delete appointments
  - UI hides action buttons when in read-only mode
- [x] **UI Features**:
  - Stats cards: Today's Sessions, Completed, Upcoming counts
  - Filter by status dropdown (All/Scheduled/Completed/Cancelled)
  - Appointments grouped by date with date headers
  - Create/Edit dialogs with datetime-local inputs
  - Action buttons: Edit (pencil), Complete (checkmark), Cancel (X), Delete (trash)

---

## Technical Architecture

```
/app/
├── backend/
│   ├── server.py          # Main API (FastAPI)
│   └── tests/             # Pytest tests
├── frontend/
│   └── src/
│       ├── App.js         # Router + API config
│       ├── pages/         # Page components
│       └── components/
│           ├── admin/     # Super Admin components
│           └── ui/        # Shadcn UI components
└── test_reports/          # Test results
```

### API Endpoints (Key)
- `POST /api/auth/login` - User login (mobile or email)
- `POST /api/auth/super-admin-login` - Admin login
- `POST /api/auth/therapist-application` - Submit application
- `GET /api/admin/therapist-applications` - List applications
- `POST /api/admin/therapist-applications/{id}/approve` - Approve therapist
- `POST /api/admin/therapists/create` - **Manual therapist creation**
- `PUT /api/admin/therapists/{id}` - **Edit therapist**
- `GET /api/admin/therapists/{id}` - **Therapist detail with subscription**
- `GET /api/admin/therapists/{id}/clients` - **Therapist's clients**
- `POST /api/admin/therapists/{id}/suspend` - Suspend therapist
- `GET /api/admin/clients` - **Full client details with therapist name**
- `GET /api/admin/clients/{id}` - **Single client detail**
- `GET /api/admin/subscription-plans` - List subscription plans
- `POST /api/admin/subscription-plans` - Create subscription plan
- `DELETE /api/admin/subscription-plans/{id}` - Delete plan
- `GET /api/admin/coupons` - List coupons
- `POST /api/admin/coupons` - Create coupon
- `DELETE /api/admin/coupons/{id}` - Delete coupon

### Test Credentials
- **Super Admin**: username: `admin`, password: `admin123` (at `/admin-login`)
- **Test Therapist**: mobile: `9999999999`, password: `TestPass123`

---

## Backlog

### P1 - High Priority
- [ ] Appointment Calendar with double-booking prevention
- [ ] Session Notes with SOAP/DAP templates
- [ ] Secure therapist-client messaging interface

### P2 - Medium Priority  
- [ ] Payment tracking for therapists
- [ ] Assessment result visualization
- [ ] Profile photo upload (currently URL-based)

### P3 - Future Enhancements
- [ ] Therapy protocol builder UI
- [ ] Homework completion tracking
- [ ] Audit log viewer for admins
- [ ] Email notifications for approvals

---

## Refactoring Needs
- Split `server.py` into modular structure (routes, models, services)
- Add database migration strategy for schema changes
- Add comprehensive error handling
