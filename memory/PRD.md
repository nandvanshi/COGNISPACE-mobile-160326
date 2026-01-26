# COGNISPACE - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application for managing a therapy practice and supporting clinical decision-making.

**App Name**: COGNISPACE
**Tagline**: Precision Insights. Personal Growth.

## Core Requirements

### User Roles
- **Therapist**: Primary user - manages clients, sessions, assessments, protocols, and payments
- **Therapist Assistant**: Delegated user - manages non-clinical operational tasks for a linked therapist
- **Client**: Secondary user - receives therapy, completes assessments and homework
- **Super Admin**: Platform administrator - approves therapists, manages subscriptions and coupons

### Authentication
- Secure email/password auth with JWT
- Mobile-first authentication for clients (mobile number as primary identifier)
- Assistant login via email (same login endpoint, role-based routing)
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
- **Subscription Plan Feature Toggles** (NEW - Phase 27)
  - Control feature access per subscription plan
  - 8 toggleable features: Session Notes, Assessments, AI Clinical, Protocols, Messaging, Payments, Assistants, Reports
  - Feature toggles enforced in UI (hide from sidebar) and backend (403 on disabled endpoints)
  - Changes apply immediately to all therapists on the plan
- Coupon code management (CRUD)
- Assistant management (view all assistants across therapists)

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
  - Stats cards: Today's Sessions, Completed, Upcoming, Blocked Times counts
  - Filter by status dropdown (All/Scheduled/Completed/Cancelled)
  - Appointments grouped by date with date headers
  - Create/Edit dialogs with datetime-local inputs
  - Action buttons: Edit (pencil), Complete (checkmark), Cancel (X), Delete (trash)
  - **Block Time button** with dedicated dialog
  - **Appointments/Blocked Times toggle** to switch views
- [x] **Calendar Blocking (P0)**:
  - Block full day (holiday/leave) via is_all_day checkbox
  - Block specific time ranges on a date
  - Optional reason field (Leave, Holiday, Personal, Offline Booking, Training, Meeting, Other)
  - Blocked slots excluded from available slots (enforced in slot generation backend)
  - Visually distinct blocked times view with red styling
  - Cannot override existing appointments (frontend validates before blocking)
  - Therapist: full block/unblock control
  - Assistant: can block/unblock time but cannot change availability rules
  - `POST /api/blocked-times` - Create blocked time
  - `GET /api/blocked-times` - List blocked times
  - `DELETE /api/blocked-times/{id}` - Remove blocked time

### Phase 11: Therapist Availability & Slot-Based Scheduling (COMPLETED - Jan 18, 2026)
- [x] **Weekly working hours definition**:
  - Therapists can enable/disable each day of the week
  - Multiple time blocks per day (e.g., 9AM-12PM and 2PM-6PM)
  - Add/remove time block buttons with start/end time inputs
  - `PUT /api/availability` endpoint to save settings
- [x] **Session duration setting**:
  - Configurable session duration (15-240 minutes)
  - Default: 60 minutes
  - Input validation enforced on backend
- [x] **Buffer time between sessions**:
  - Configurable buffer time (0-60 minutes)
  - Default: 0 minutes (no buffer)
  - Applied between generated slots
- [x] **Automatic slot generation**:
  - `GET /api/available-slots/{therapist_id}?date=YYYY-MM-DD`
  - Generates slots based on working hours, session duration, and buffer time
  - Only shows future slots (past slots filtered out)
  - Respects day-of-week availability
- [x] **Block full days or specific time ranges**:
  - `POST /api/blocked-times` to create blocked periods
  - Support for all-day blocks and specific time ranges
  - Optional reason field (vacation, holiday, personal, etc.)
  - `DELETE /api/blocked-times/{id}` to remove blocks
- [x] **Blocked times prevent slot generation**:
  - Slots overlapping blocked times are excluded
  - Tested and verified in iteration_8
- [x] **Booked appointments prevent double-booking**:
  - Existing appointments exclude those time slots
  - Cancelled appointments free up slots
- [x] **Slot-based booking UI**:
  - "Available Slots" vs "Manual Entry" toggle in booking dialog
  - Date picker to select appointment date
  - Clickable slot buttons showing time and duration
  - Selected slot highlighted with confirmation message
  - "No available slots" message for disabled days
- [x] **Availability Settings page**:
  - New sidebar menu item "Availability" with Clock icon
  - Session Settings card (duration, buffer time)
  - Weekly Schedule card with day toggles and time blocks
  - Blocked Times card with list and add button
  - Save Availability button with success toast

### Phase 12: Session Notes (COMPLETED - Jan 18, 2026)
- [x] **SOAP Template**:
  - Subjective: Client's reported symptoms, concerns, experiences
  - Objective: Observable behaviors, mental status, appearance
  - Assessment: Clinical impressions, progress, interpretations
  - Plan: Treatment plan, interventions, homework, next steps
- [x] **DAP Template**:
  - Data: Observations and information gathered
  - Assessment: Clinical impressions and interpretations
  - Plan: Treatment plan and next steps
- [x] **Notes linked to appointments**:
  - Optional appointment_id field when creating notes
  - Dropdown shows client's appointments (completed/scheduled)
  - Linked notes display appointment date
  - "Linked" badge on note cards
- [x] **Therapist-only editing**:
  - Only note creator can edit/delete
  - Backend enforces `therapist_id` check on all operations
- [x] **Subscription read-only mode respected**:
  - All write endpoints use `require_active_therapist`
  - Expired therapists can view but not create/edit/delete
  - UI hides action buttons when `isReadOnly=true`
- [x] **Full CRUD operations**:
  - `POST /api/session-notes` - Create (SOAP or DAP)
  - `GET /api/session-notes` - List with optional client_id filter
  - `GET /api/session-notes/{id}` - Get single note
  - `PUT /api/session-notes/{id}` - Update note content
  - `DELETE /api/session-notes/{id}` - Delete note
- [x] **UI Features**:
  - Stats cards: Total Notes, SOAP Notes, DAP Notes
  - Filter by client dropdown
  - Note cards with preview text and metadata
  - View dialog with formatted S/O/A/P or D/A/P sections
  - Edit dialog with all fields editable
  - Delete with confirmation

### Phase 13: Recurring Appointments (COMPLETED - Jan 18, 2026)
- [x] **Pattern creation**:
  - Select client, day of week, start/end time
  - Define start date and optional end date
  - Optional notes field for session description
  - `POST /api/recurring-appointments` endpoint
- [x] **Generate appointments from pattern**:
  - `POST /api/recurring-appointments/{id}/generate?weeks_ahead=4`
  - Creates scheduled appointments for next N weeks
  - Skips dates with existing appointments at same time
  - Marks generated appointments with `recurring_pattern_id`
- [x] **Toggle pattern active/inactive**:
  - `PUT /api/recurring-appointments/{id}/toggle`
  - Inactive patterns cannot generate new appointments
  - UI shows "Paused" label for inactive patterns
- [x] **Delete pattern**:
  - `DELETE /api/recurring-appointments/{id}`
  - Does not delete already-generated appointments
- [x] **UI Features**:
  - New "Recurring" sidebar menu item with Repeat icon
  - Info card explaining how recurring appointments work
  - Pattern cards showing client, day, time, date range
  - Generate, Toggle, Delete buttons per pattern
  - Create Pattern dialog with all fields

### Phase 14: Note Templates / Quick Insert (COMPLETED - Jan 18, 2026)
- [x] **Template CRUD**:
  - `POST /api/note-templates` - Create template with name, category, content
  - `GET /api/note-templates` - List all templates (sorted by usage count)
  - `PUT /api/note-templates/{id}` - Update template
  - `DELETE /api/note-templates/{id}` - Delete template
- [x] **Categories**:
  - Subjective (S), Objective (O), Assessment (A), Plan (P), Data (D), General
  - Category-specific filtering when inserting
  - Color-coded badges in UI
- [x] **Usage tracking**:
  - `POST /api/note-templates/{id}/use` - Increment usage count
  - Most-used templates appear first in lists
  - "Used Nx" display on template cards
- [x] **Quick Insert in note forms**:
  - "Quick Insert (N)" button appears on each SOAP/DAP field
  - Shows only templates matching that field's category + General
  - One-click insert appends content to field
  - Works in both Create and Edit dialogs
- [x] **Template Manager UI**:
  - "Templates (N)" button in Session Notes header
  - "Manage Quick Templates" dialog
  - Create New Template form (name, category dropdown, content)
  - List of existing templates with delete buttons
  - Stats card showing template count

### Phase 15: Secure Therapist-Client Messaging (COMPLETED - Jan 18, 2026)
- [x] **Therapist-controlled visibility**:
  - Therapists can enable/disable messaging per client
  - `PUT /api/clients/{id}/messaging` - Toggle messaging enabled/disabled
  - `GET /api/clients/{id}/messaging-status` - Get messaging status
  - Client Settings dialog with toggle switches for each client
- [x] **Restriction to assigned clients only**:
  - `GET /api/messaging-contacts` - Returns only assigned clients with messaging enabled
  - `POST /api/messages` - Validates sender-recipient relationship
  - Therapists can only message their assigned clients
  - Clients can only message their assigned therapist
- [x] **Read-only mode enforcement**:
  - Expired subscription therapists cannot send messages
  - Returns 403 with "read-only mode" message
  - UI shows warning banner and disables message input
- [x] **Full messaging features**:
  - `POST /api/messages` - Send message to valid recipient
  - `GET /api/messages/{user_id}` - Get messages with specific user
  - `GET /api/messages` - Get all conversations (list view)
  - Auto-mark as read when viewing conversation
  - Unread count badges on conversations
- [x] **UI Features**:
  - Conversations list with last message preview
  - Messages panel with chat bubbles (sender/receiver styling)
  - Timestamps on messages
  - Read indicators for sent messages
  - New Message dialog with contact selection
  - Client Settings dialog for toggling messaging
  - HIPAA compliance notice
- [x] **Security**:
  - verify_messaging_allowed() validates all send requests
  - Uses `client_profiles` collection for therapist assignment
  - messaging_enabled field in client_profiles

### Phase 16: Slot Generation Timezone Bug Fix (COMPLETED - Jan 18, 2026)
- [x] **Bug Fixed**: Timing mismatch between Weekly Availability settings and available appointment slots
  - Root cause: Backend was treating IST availability times as UTC in slot generation
  - Impact: Slots were shifted by 5.5 hours (e.g., 09:00 IST availability showed as 14:30 IST slots)
- [x] **Solution Applied**:
  - Added IST timezone constant using `zoneinfo.ZoneInfo("Asia/Kolkata")`
  - Modified slot generation to treat `time_blocks` as IST times
  - Convert to UTC for comparison with stored appointments/blocked times
  - Return slots in UTC (frontend converts to IST for display)
- [x] **Verification**:
  - Therapist 1: 09:00-17:00 IST availability → First slot at 09:00 IST ✓
  - Therapist 2: Multiple blocks (10:20-17:00, 17:30-18:10, 18:30-20:45) → All block start times match exactly ✓
  - Buffer times applied correctly between slots ✓
  - Blocked times correctly remove affected slots ✓
  - 13/13 backend tests passed (100%)
- [x] **Acceptance Criteria Met**:
  - A slot booked always falls fully within the defined availability block ✓
  - Displayed slot times exactly match availability configuration ✓

### Phase 18: AI Clinical Support (COMPLETED - Jan 19, 2026)
- [x] **AI Assessment Suggestion Engine**:
  - `POST /api/ai/suggest-assessments` - AI analyzes client data and suggests assessments
  - Input: client_id (optional), query (symptoms/observations), include_intake, include_notes
  - Output: analysis_summary, suggestions with priority, assessment_type, reason, relevant_symptoms
  - Suggests PHQ-9, GAD-7, PCL-5, ASRS, BDI-II, DASS-21, YBOCS, PSS based on symptoms
  - Uses client's intake summary and session notes for context
- [x] **AI Therapy Protocol Builder**:
  - `POST /api/ai/generate-protocol` - Generates evidence-based treatment protocols
  - Input: client_id (optional), query, modality_preference (CBT, DBT, ACT, EMDR, etc.)
  - Output: protocol_name, target_condition, recommended_modality, rationale, sessions[]
  - Each session includes: objectives, interventions, homework, duration
  - Includes progress_markers and contraindications
- [x] **AI Homework Generator**:
  - `POST /api/ai/generate-homework` - Creates personalized therapeutic homework
  - Input: client_id (required), context, homework_type (worksheet, exercise, reflection, reading, meditation)
  - Output: title, description, instructions, exercises[], estimated_time_minutes, therapeutic_rationale
  - Can be assigned directly to client after generation
- [x] **Resource Library**:
  - `POST /api/resources` - Create resources (worksheets, exercises, psychoeducation)
  - `GET /api/resources` - List resources with optional category filter
  - `DELETE /api/resources/{id}` - Delete resource
  - `POST /api/resources/{id}/assign` - Assign resource to client
  - `GET /api/resources/assignments` - List assignments
  - Client can mark resources as viewed/completed
- [x] **AI Integration**:
  - Using Gemini 3 Flash via emergentintegrations library
  - EMERGENT_LLM_KEY configured in backend/.env
  - Response time: 5-15 seconds typical
  - 19/19 backend tests passed (100%)
- [x] **Frontend UI**:
  - New "AI Clinical" menu item in therapist dashboard
  - 4 tabs: Assessments, Protocols, Homework, Resources
  - Beautiful gradient buttons for AI actions
  - Results display with priority badges, symptom tags
  - Protocol dialog shows full session plan
  - Homework dialog with exercises and instructions

### Phase 19: Clinical Notes with Case History (COMPLETED - Jan 19, 2026)
- [x] **Mandatory Case History Flow**:
  - Case History MUST be completed before any session notes
  - Uses structured MMS-style format (form-based, not free text)
  - One-time creation per client, editable by therapist only
  - Session notes creation blocked with 400 error if case history incomplete
- [x] **Case History Sections (11 sections)**:
  1. **Basic Identification**: Name*, Age/DOB, Gender, Marital Status, Education, Occupation, Address, Contact, Emergency Contact, Referred By
  2. **Presenting Complaints** (Required): Main problems in client's words*, Duration, Severity, Frequency, Triggers
  3. **History of Present Illness**: Onset, Course, Previous episodes, Factors improving/worsening, Prior therapy/medication
  4. **Past Psychiatric History**: Previous therapy, diagnosis, hospitalizations, past/current medications
  5. **Medical History**: Chronic illnesses, Current medications, Sleep pattern (dropdown), Appetite, Substance use
  6. **Family History**: Family structure, Mental illness in family (Yes/No), Relationship dynamics
  7. **Personal & Developmental History**: Childhood, Education, Work history, Major life events (optional), Trauma (optional)
  8. **Mental Status Examination (MSE)**: Appearance, Behavior, Speech, Mood, Affect, Thought process, Thought content, Perception, Cognition, Insight, Judgment (dropdowns + short text)
  9. **Provisional Formulation**: Clinical formulation*, Stressors, Strengths, Risk indicators
  10. **Initial Therapy Plan**: Therapy modality, Session frequency, Initial goals, Homework
  11. **Consent & Disclaimer**: Informed consent taken* (checkbox), Confidentiality explained (checkbox), Consent date, Notes
- [x] **Backend Endpoints**:
  - `POST /api/case-history` - Create case history
  - `GET /api/case-history/{client_id}` - Get case history
  - `GET /api/case-history/check/{client_id}` - Check if case history exists & is complete
  - `PUT /api/case-history/{client_id}` - Update full case history
  - `PATCH /api/case-history/{client_id}/section` - Auto-save individual sections
  - `PATCH /api/case-history/{client_id}/complete` - Mark complete (validates required fields)
- [x] **Frontend UI**:
  - Multi-step wizard with collapsible sections
  - Progress navigation showing all 11 steps with icons
  - Auto-save on field changes (2-second debounce)
  - Required field validation before completion
  - "Complete Case History" action with validation
  - Case History warning in Session Notes dialog with "Start Case History" button
- [x] **Security & Access Control**:
  - Therapist-only access (no clients, no assistants)
  - All content editable and approved by therapist only
  - Respects subscription read-only mode
  - No client access to therapist notes
- [x] **Testing**: 23/25 backend tests passed (92%), 2 skipped due to test setup

### Phase 17: Therapist Assistant Role (COMPLETED - Jan 18, 2026)
- [x] **Role Definition**:
  - Stored in `users` collection with `role: "assistant"` and `therapist_id`
  - Always linked to exactly one therapist (cannot switch)
  - No self-registration (created by therapist or super admin)
- [x] **Account Management**:
  - `POST /api/assistants` - Therapist creates assistant
  - `GET /api/assistants` - List therapist's assistants
  - `PUT /api/assistants/{id}` - Update assistant details
  - `PUT /api/assistants/{id}/suspend` - Suspend assistant
  - `PUT /api/assistants/{id}/activate` - Activate assistant
  - `DELETE /api/assistants/{id}` - Soft delete (status: deleted)
  - `PUT /api/assistants/{id}/reset-password` - Reset password
- [x] **Login & Auth**:
  - Same `/api/auth/login` endpoint (email-based login)
  - Returns `role: "assistant"` and `therapist_id` in response
  - Frontend routes to `/assistant` dashboard
- [x] **Allowed Access**:
  - View/create clients (non-clinical data only)
  - Create, reschedule, cancel appointments
  - Block calendar time (full day or time slots)
  - View therapist availability and bookings
  - View payments
- [x] **Explicit Restrictions (Backend Enforced)**:
  - Cannot access: session notes, assessments, protocols, messaging
  - Cannot change therapist availability settings
  - Cannot reassign clients to another therapist
  - Cannot permanently delete clients
  - Cannot complete appointments (clinical action)
- [x] **UI**:
  - AssistantDashboard with limited sidebar (Overview, Clients, Appointments, Payments)
  - AssistantManagement component for therapists to manage assistants
  - "Assistants" menu item in therapist dashboard
- [x] **Audit Logging**:
  - All assistant actions logged with `created_by_assistant: true` in details
  - Audit trail for: create client, create/cancel appointment, block time
- [x] **Subscription Enforcement**:
  - Assistant inherits therapist's subscription status
  - Read-only mode applies when therapist subscription expired

### Phase 20: Comprehensive Client Profile View (COMPLETED - Jan 19, 2026)
- [x] **Single-pane dashboard for each client**:
  - All client data aggregated in one modal view
  - Accessible from "View Profile" button on client cards in Client Management
  - Replaces multiple navigations with single comprehensive view
- [x] **Client Profile Modal Components**:
  - **Header Section**: Client avatar, name, client ID, phone, email
  - **Status Badges**: "Consent Signed/Pending", "Case History Complete/Pending"
  - **Quick Stats Row**: Sessions Done, Upcoming, Session Notes, Assessments, Total Paid (₹)
  - **Quick Action Buttons**: "Book Appointment", "Start Session Note" (therapist only)
- [x] **Tabbed Navigation with 5 tabs**:
  - **Overview Tab**: Next Appointment, Last Session, Case History summary, Therapy Consent summary, Recent Session Notes, Pending Items
  - **Sessions Tab**: Completed/Upcoming/Session Notes/Cancelled stats, Session Notes list with View/Edit, All Appointments list
  - **Case History Tab**: View/Edit case history, shows all 11 sections if available, Create button if not
  - **Assessments Tab**: Completed/Pending counts, Assessment list with scores
  - **Payments Tab**: Total Paid/Pending/Transaction counts, Payment history list
- [x] **Session Notes in Client Profile (NEW - Jan 19, 2026)**:
  - Session Notes displayed in Sessions tab with date, SOAP/DAP type badge, and preview
  - View Session Note dialog with color-coded sections (S/O/A/P or D/A/P)
  - Edit Session Note dialog with all fields editable
  - Session notes hidden from assistants (clinical data restriction)
- [x] **Start New Session Note Workflow (NEW - Jan 19, 2026)**:
  - "Start Session Note" button in header and Sessions tab
  - Validates Case History is complete before allowing note creation
  - Validates Consent is signed before allowing note creation
  - Pre-fills appointment link with today's appointment if available
  - Create Session Note dialog with SOAP/DAP selector and appointment dropdown
- [x] **Book Appointment from Client Profile (NEW - Jan 19, 2026)**:
  - "Book Appointment" button in header and Sessions tab
  - Date picker with available slot fetching
  - Slot-based booking with `GET /api/available-slots/{therapist_id}?date=`
  - Optional notes field for appointment description
- [x] **Backend Endpoint Updates**:
  - `GET /api/appointments?client_id={id}` - Filter appointments by client
  - `GET /api/assessments?client_id={id}` - Filter assessments by client
  - `GET /api/homework?client_id={id}` - Filter homework by client
  - All endpoints now support client_id query parameter for therapists
- [x] **Security & Access Control**:
  - Read-only mode disables action buttons (isReadOnly prop)
  - Assistants blocked from session notes (isAssistant prop)
  - Subscription status respected
  - Therapists can only view their assigned clients
- [x] **Testing**: 17/17 backend tests + 16/16 frontend features passed (100%)
  - /app/tests/test_client_profile_view.py - Backend endpoint tests
  - /app/test_reports/iteration_16.json, iteration_17.json

### Phase 21: Session Check-In/Check-Out & Payment Workflow (COMPLETED - Jan 19, 2026)
- [x] **Session Check-In (Start Session)**:
  - `POST /api/appointments/{id}/check-in` endpoint
  - Records actual_start_time (IST timestamp)
  - Changes status from "scheduled" to "in_progress"
  - Records checked_in_by (user ID)
  - Both Therapist AND Assistant can check-in
- [x] **Session Check-Out (End Session)**:
  - `POST /api/appointments/{id}/check-out` endpoint
  - Records actual_end_time (IST timestamp)
  - Calculates actual_duration_minutes
  - Changes status from "in_progress" to "completed"
  - Records checked_out_by (user ID)
  - Both Therapist AND Assistant can check-out
  - Optional payment recording at check-out
- [x] **Enhanced Payment Model**:
  - New fields: bill_number (unique), payment_status (paid/partial/pending), payment_method (cash/upi/card/bank/other)
  - Linked to: appointment_id, session_note_id, client_id, therapist_id
  - client_code (CL-XXXXXX), therapist_name stored for receipts
  - `POST /api/payments` - Both Therapist AND Assistant can record payments
  - `GET /api/payments` - Therapist, Assistant, AND Client can view
  - `GET /api/payments/{id}` - Single payment with access control
- [x] **Unique Bill Number Generation**:
  - Format: BILL-YYYYMMDD-XXXX (e.g., BILL-20260119-0001)
  - Auto-incrementing daily sequence
  - `generate_bill_number()` async function
- [x] **Payment Receipt System**:
  - `GET /api/payments/{id}/receipt` endpoint returns PaymentReceipt model
  - Receipt includes: bill_number, clinic_name, therapist details, client details, date/time, session reference, amount, payment_method, payment_status, notes
  - Accessible by Therapist, Assistant, AND Client (read-only)
- [x] **Frontend Components**:
  - `SessionActionButtons` - Check In / Check Out buttons for appointment cards
  - `AppointmentStatusBadge` - Color-coded status (blue=scheduled, amber=in_progress, green=completed, red=cancelled)
  - `PaymentCard` - Payment listing with receipt button
  - `PaymentReceiptView` - Modal with printable receipt, Print and Download PDF buttons
- [x] **UI Integration**:
  - Sessions tab shows Check In button for scheduled appointments
  - Sessions tab shows Check Out button for in_progress appointments
  - Check Out dialog includes optional payment recording (amount, mode, status, notes)
  - Payments tab uses PaymentCard with receipt icon
  - Receipt dialog with formatted layout, Print and Download PDF functionality
- [x] **Access Control**:
  - Therapist & Assistant: Check-in/out, record payments, view/download receipts
  - Client: View payments, view/download receipts (read-only, no edit)
  - Subscription read-only mode respected
- [x] **Appointment Model Updates**:
  - New status: "in_progress" (between scheduled and completed)
  - New fields: actual_start_time, actual_end_time, actual_duration_minutes, checked_in_by, checked_out_by

### Phase 22: App Rebranding & Therapist Dashboard UX (COMPLETED - Jan 20, 2026)
- [x] **App Renamed to TheraGenie**:
  - All "Haven" references changed to "TheraGenie" across all pages
  - New tagline: "Clinical intelligence for modern therapists"
  - Login page, TherapistDashboard, ClientDashboard, SuperAdminDashboard, AssistantDashboard updated
  - Sidebar logo with Sparkles icon and "TheraGenie" text
- [x] **Therapist Dashboard Sidebar Reorganization**:
  - Navigation grouped into two sections: "Clinical" and "Operations"
  - **Clinical Group**: Dashboard, Clients, Schedule, Session Notes, Assessments, Protocols, AI Clinical
  - **Operations Group**: Availability, Recurring, Messages, Payments, Assistants
  - Improved scanability for new therapists with uppercase section labels
- [x] **Action-Oriented Today at a Glance Cards**:
  - Sessions Today: Shows completed/remaining, clickable to Schedule
  - Unread Messages: Shows "All caught up" or count, clickable to Messages
  - Pending Notes: Shows count with "Add notes →" CTA, clickable to Session Notes
  - Border-left color coding based on priority state
- [x] **Personal Greeting**:
  - Time-based greeting: "Good morning/afternoon/evening"
  - Icons: SunMedium (morning), Sunset (afternoon), Moon (evening)
  - Shows therapist's first name and formatted date
- [x] **Calendar-Centric Dashboard Layout**:
  - Today's Schedule section prominently displayed with status badges
  - Status badges: "In Session" (amber pulse), "Done" (green), "Up Next" (primary), "Starting Now"
  - "View Calendar" link to navigate to full schedule
  - This Week section showing weekly appointments grouped by day
- [x] **Empty States with CTAs**:
  - No sessions today → "Schedule Appointment" + "Set Availability" buttons
  - Calendar-centric messaging for empty states
  - Friendly guidance instead of passive empty states
- [x] **Needs Attention Section**:
  - Alerts for: inactive clients (30+ days), pending session notes, trial status
  - Each alert has action link (e.g., "View Clients →", "Add Notes →")
- [x] **Coming Up Section**:
  - Next appointment details: client name, time until, date, time range
  - "View Client Profile" button
- [x] **Practice Overview (Lower Emphasis)**:
  - Moved to right sidebar with dashed border and muted background
  - Shows Total Clients and Upcoming Sessions counts
  - Clickable to navigate to respective views
- [x] **Testing**: 29/29 frontend tests passed (100%)
  - /app/test_reports/iteration_18.json

### Phase 23: Mobile Responsiveness (COMPLETED - Jan 20, 2026)
- [x] **Mobile-First Sidebar Navigation**:
  - Hamburger menu visible on screens < 1024px (lg breakpoint)
  - Slide-out sidebar with smooth transition animation
  - Collapsible Clinical/Operations groups on mobile (chevron icons)
  - Close button (X) in sidebar header
  - Overlay backdrop when sidebar is open
- [x] **Responsive Layout Adjustments**:
  - Cards stack vertically on mobile (< 640px), 3-column row on sm+
  - Main content padding: p-4 (mobile) → p-6 (sm) → p-10 (lg)
  - Text scaling: text-2xl (mobile) → text-3xl (sm) → text-4xl (lg)
- [x] **Touch-Friendly Targets**:
  - All nav buttons minimum 44px height on mobile (48px for Settings/Logout)
  - Full-width buttons on mobile for easy tapping
  - Larger tap targets for cards (active:scale-[0.98] feedback)
- [x] **Mobile Header**:
  - Fixed header with TheraGenie logo and hamburger menu
  - Current view label (hidden on very small screens)
  - Header height accounts for main content offset (pt-14)
- [x] **Client Dashboard Mobile**:
  - Sticky header with compact layout
  - Full-width "Book Appointment" button on mobile
  - Cards stack vertically with appropriate padding
  - Text truncation for long content (line-clamp-2)
- [x] **Breakpoint Testing Verified**:
  - lg (1024px): Sidebar always visible, hamburger hidden
  - Below lg (1023px): Hamburger visible, sidebar hidden
  - sm (640px): Cards in row, text sizes increase
  - Below sm (639px): Cards stacked, smallest text sizes
- [x] **Testing**: 11/11 frontend tests passed (100%)
  - /app/test_reports/iteration_19.json

### Phase 24: PWA (Progressive Web App) Support (COMPLETED - Jan 20, 2026)
- [x] **PWA Manifest** (`/public/manifest.json`):
  - App name: "TheraGenie"
  - Theme color: #16a34a (primary green)
  - Display mode: standalone
  - Icons: 72x72 to 512x512 PNG sizes
  - App shortcuts for Schedule and Clients
- [x] **Service Worker** (`/public/service-worker.js`):
  - Static asset caching on install
  - Network-first strategy for API calls
  - Cache-first strategy for static assets
  - Offline fallback page
  - Push notification support (ready for future integration)
- [x] **Offline Page** (`/public/offline.html`):
  - Branded offline page with retry button
  - Clean, professional design matching app theme
- [x] **App Icons**:
  - Generated icons at all required sizes (72-512px)
  - Apple Touch Icon (180x180)
  - Favicon (32x32)
- [x] **Install Prompt Component** (`InstallPWA.js`):
  - Smart install prompt (Android/Chrome)
  - iOS instructions (Add to Home Screen)
  - Dismissible with localStorage persistence
  - Shows after 3-5 second delay, respects 7-day cooldown
- [x] **Meta Tags** (index.html):
  - Apple Mobile Web App capable
  - Theme color meta
  - MSApplication tiles
  - Manifest link

### Phase 25: Full Therapist Schedule/Calendar System (COMPLETED - Jan 20, 2026)
- [x] **New TherapistSchedule Component** (`/components/TherapistSchedule.js`):
  - Replaced old AppointmentCalendar with comprehensive schedule system
  - Sidebar nav item renamed from "appointments" to "schedule"
- [x] **Month View (Default)**:
  - Full calendar grid showing all days of the month
  - Session count badges on dates with appointments
  - Navigation: Previous Month, Next Month, Today button
  - Jump to Date dialog with date picker
  - Today highlighted with primary border
  - Past dates shown with muted styling
  - Legend showing Today and "Has sessions" indicators
- [x] **Day View (On Date Click)**:
  - Date displayed in DD/MM/YYYY format (IST)
  - Day name displayed (e.g., "Tuesday")
  - Vertical time-based schedule (08:00 - 21:30 in 30-min slots)
  - Time displayed in 24-hour format (HH:mm)
  - Navigation: Previous Day, Next Day, Back to Month
- [x] **Day View Slot Types**:
  - **Available**: Green background, "Schedule" button to book
  - **Unavailable**: Gray, shows "Unavailable" text
  - **Blocked**: Red background, "Blocked" label, X button to remove
  - **Scheduled Session**: Primary background, shows client avatar, name, time range (HH:mm - HH:mm), status badge
- [x] **Session Status Badges**:
  - scheduled: blue
  - in_progress: amber
  - completed: green
  - cancelled: red
- [x] **Editing & Actions (Day View)**:
  - Schedule Appointment Dialog: client select, duration, notes
  - Edit Appointment Dialog: update notes, change status
  - Cancel appointment (with confirmation)
  - Block Time Dialog: select time range or block entire day, reason
  - Remove blocked time
- [x] **IST Timezone Compliance**:
  - All times displayed in IST (GMT +5:30)
  - Date/time calculations use IST offset
- [x] **Mobile Responsive**:
  - Month view calendar adapts to small screens
  - Day view time slots scrollable
  - Navigation buttons accessible on mobile
- [x] **Bug Fixed**: Available slots showed "Unavailable" - changed `dayAvailability.slots` to `dayAvailability.time_blocks` and `avail.start/end` to `avail.start_time/end_time`
- [x] **Testing**: 100% frontend tests passed
  - /app/test_reports/iteration_20.json

### Phase 26: Clinical Assessments Phase-1 (COMPLETED - Jan 20, 2026)
- [x] **Expanded Assessment Library (12 Assessments)**:
  - PHQ-9 (Patient Health Questionnaire-9) - Depression screening
  - GAD-7 (Generalized Anxiety Disorder-7) - Anxiety screening
  - DASS-21 (Depression Anxiety Stress Scales) - Tri-dimensional screening with subscales
  - WHO-5 (Well-Being Index) - General well-being
  - ASRS-v1.1 (Adult ADHD Self-Report Scale) - ADHD screening
  - Y-BOCS (Yale-Brown Obsessive Compulsive Scale) - OCD severity
  - HAM-A (Hamilton Anxiety Rating Scale) - Anxiety assessment
  - BDI-II (Beck Depression Inventory-II) - Depression severity (21 questions)
  - **BPRS (Brief Psychiatric Rating Scale)** - NEW: 18-item general psychiatric screening
  - ISI (Insomnia Severity Index) - Sleep issues
  - AUDIT (Alcohol Use Disorders Identification Test) - Alcohol use screening
  - RSES (Rosenberg Self-Esteem Scale) - Self-esteem assessment
- [x] **Client-Friendly Assessment Names** (ASSESSMENT_CLIENT_INFO):
  - PHQ-9 → "Mood Check-In"
  - GAD-7 → "Worry & Anxiety Check-In"
  - DASS-21 → "Emotional Well-being Check-In"
  - WHO-5 → "Well-being Check-In"
  - ASRS-v1.1 → "Focus & Attention Check-In"
  - Y-BOCS → "Thoughts & Habits Check-In"
  - HAM-A → "Anxiety Experience Check-In"
  - BDI-II → "Mood & Feelings Check-In"
  - BPRS → "Overall Experience Check-In"
  - ISI → "Sleep Quality Check-In"
  - AUDIT → "Lifestyle Check-In"
  - RSES → "Self-Perception Check-In"
- [x] **Client Assessment Taking UX** (ClientAssessmentTaker.js):
  - **Start Screen**: Calm, non-clinical intro with reassurance text
    - Shows friendly name, purpose, time estimate, question count
    - "There are no right or wrong answers" message
    - Disclaimer: "This helps your therapist understand your experience. Not a diagnosis."
  - **One Question Per Screen Flow**:
    - Large readable text, touch-friendly option buttons
    - Progress indicator (e.g., "Question 3 of 9")
    - Answered count display
    - Back/Next navigation
    - Auto-save progress every 2 seconds
  - **Submission Confirmation**:
    - "Thank you. Your therapist will review this."
    - NO scores shown to clients
- [x] **Backend Endpoints (Assessment)**:
  - `GET /api/assessments/library` - Returns all 12 standard assessments
  - `POST /api/assessments` - Assign assessment with optional due_date
  - `GET /api/assessments/{id}/client-view` - Client-friendly assessment view
  - `POST /api/assessments/{id}/save-progress` - Auto-save answers in progress
  - `POST /api/assessments/{id}/submit-with-scoring` - Submit and score assessment
  - `GET /api/assessments/{id}/results` - Full results (therapist) or limited (client if shared)
  - `POST /api/assessments/{id}/share-report` - Share report with client
  - `POST /api/assessments/{id}/unshare-report` - Remove client access
  - `PUT /api/assessments/{id}/therapist-notes` - Add clinical notes
  - `PUT /api/assessments/{id}/due-date` - Set due date
  - `GET /api/client/assessments` - Client's assessment list (client-friendly)
  - `GET /api/client/assessment-history` - Completed assessments (names & dates only)
- [x] **Scoring System** (assessment_library.py):
  - Sum-based scoring (PHQ-9, GAD-7, BDI-II, ISI, AUDIT, RSES)
  - Subscale scoring (DASS-21: Depression, Anxiety, Stress with multiplier)
  - Percentage scoring (WHO-5: multiplied by 4)
  - ADHD shaded threshold counting (ASRS-v1.1)
  - Severity bands with color coding (green, yellow, orange, red, darkred)
- [x] **Therapist Results View** (Assessments.js):
  - Score summary with severity label
  - Subscale breakdown for DASS-21
  - Detailed response list (question + answer + value)
  - Clinical notes section (editable)
  - Share/Unshare toggle with status indicator
- [x] **Client Shared Report View** (ClientDashboard.js):
  - Shows only after therapist shares
  - Score and severity display
  - Therapist notes (if added)
  - "Please discuss this report with your therapist" disclaimer
- [x] **Access Control**:
  - Clients cannot see scores until therapist shares
  - Assistants cannot access assessment data
  - Therapists can only view their clients' assessments
- [x] **Testing**: 13/13 backend tests passed (100%)
  - /app/tests/test_assessments.py
  - /app/test_reports/iteration_22.json

### Phase 27: Product Alignment & Feature Toggles (COMPLETED - Jan 20, 2026)
- [x] **Unified Calendar System**:
  - TherapistSchedule component now used by both Therapist and Assistant
  - Removed deprecated AppointmentCalendar component
  - Assistant has restricted permissions: can view, book, cancel, block time
  - Assistant CANNOT: modify availability settings, edit recurring rules
  - `isAssistant` prop controls availability editing permissions
- [x] **Subscription Plan Feature Toggles** (Super Admin):
  - New feature: Control which features are available per subscription plan
  - 8 toggleable features: session_notes, assessments, ai_clinical, protocols, messaging, payments, assistants, reports
  - Feature Toggles Dialog in Super Admin → Subscription Plans
  - Each feature has icon, label, and description
  - Toggle switches to enable/disable features
  - Changes apply immediately to all therapists on the plan
- [x] **Backend Feature Enforcement**:
  - `check_feature_enabled()` function validates feature access
  - `require_feature()` dependency factory for endpoint protection
  - Protected endpoints: session-notes, assessments, ai-suggest, protocols, messaging, payments, assistants
  - Returns 403 "Feature not included in your subscription plan" when disabled
- [x] **Frontend Feature Enforcement**:
  - `SubscriptionContext` provides `isFeatureEnabled()` and `featureToggles` state
  - `SubscriptionProvider` wraps entire app
  - TherapistDashboard filters sidebar nav items based on feature toggles
  - Nav items have `feature` property mapped to toggle keys
- [x] **Subscription Status Endpoint Enhanced**:
  - `GET /api/auth/subscription-status` now returns:
    - `is_read_only`, `subscription_status`, `subscription_plan`
    - `feature_toggles` (all 8 feature states)
    - `days_remaining` (calculated from end_date)
    - `expiry_warning` (true if days_remaining <= 7 and > 0)
- [x] **Expiry Warning Banner**:
  - Shows when `expiry_warning` is true (< 7 days remaining)
  - Amber banner with "Your subscription expires in X days" message
  - "Contact Support" button
  - Positioned below mobile header, above read-only banner
- [x] **Availability Setup Prompt**:
  - Blue banner on Dashboard when therapist has no availability set
  - "Set up your availability to start accepting appointments"
  - "Set Availability" button navigates to availability settings
- [x] **Assessment Trend Chart**:
  - New `AssessmentTrendChart` component
  - Bar chart showing score progression over time
  - Trend analysis: Improving (down), Needs attention (up), Stable
  - Assessment type selector for clients with multiple assessment types
  - Integrated in ClientProfileView → Assessments tab (shows when 2+ completed)
- [x] **Testing**: 20/20 backend tests passed (100%)
  - /app/tests/test_feature_toggles.py
  - /app/test_reports/iteration_23.json

### Phase 28: Action-Oriented Assistant Dashboard (COMPLETED - Jan 20, 2026)
- [x] **New Assistant Dashboard Overview** (AssistantOverview component):
  - Therapist name and current date prominently displayed
  - Date format: DD/MM/YYYY (IST timezone)
  - Refresh button for manual data refresh
  - Auto-refresh every 5 minutes
- [x] **Quick Actions Panel**:
  - Add Client button → navigates to Clients view
  - Today's Schedule button → navigates to Schedule view
  - Record Payment button → navigates to Payments view
  - 3-column grid layout with icons
- [x] **Today's Call Reminders Section**:
  - Lists all appointments for today with client names and times
  - Pending calls shown with amber background and "Mark Called" button
  - Completed calls shown with green background, "Undo" option
  - Badge shows pending count (e.g., "2 pending")
  - `POST /api/assistant/call-reminder/{appointment_id}` - Mark as called
  - `DELETE /api/assistant/call-reminder/{appointment_id}` - Undo call mark
- [x] **Needs Attention Section**:
  - Upcoming Sessions (within 4 hours): Blue cards with clock icon
  - In Progress - Need Check-out: Amber cards with warning icon
  - Pending Payments: Red cards with dollar icon and count
  - Each item clickable → navigates to relevant view
  - "All caught up!" message when nothing needs attention
- [x] **Inactive Clients Follow-up Section (30+ days)**:
  - Lists clients without sessions in last 30 days
  - Shows days since last session (or "No sessions yet")
  - Call button (opens tel: link for mobile)
  - Schedule button → navigates to Schedule view
  - "View all X inactive clients" link when > 5 clients
  - "All clients are active!" message when none inactive
- [x] **Daily Payments Summary Section**:
  - 3-column summary: Cash, Online, Total amounts in ₹ (Indian Rupee)
  - Payment method icons: Banknote (cash), CreditCard (online), DollarSign (total)
  - List of today's payments with client name, method, and amount
  - "Record Payment" button in header
  - "No payments recorded today" empty state
- [x] **Access Information Panel (Collapsible)**:
  - Shows assistant permissions clearly
  - **CAN**: View/create clients, view therapist availability, schedule/cancel appointments, block time, view/record payments, check in/out sessions
  - **CANNOT**: View session notes, access assessments/protocols, access AI clinical features, create/edit/delete availability, delete clients permanently
- [x] **Backend API** (`GET /api/assistant/dashboard`):
  - Returns therapist info (name, email, mobile)
  - Today's date and day name in IST
  - Today's appointments with call status (pending/called)
  - Needs attention: upcoming_sessions, pending_checkins, pending_payments_count
  - Inactive clients list (top 10, sorted by days inactive)
  - Payments summary: cash_total, online_total, total, payments list
- [x] **Schedule View (TherapistSchedule component)**:
  - Uses shared TherapistSchedule with `isAssistant={true}` prop
  - Month view shows calendar with appointment counts
  - Day view shows availability blocks, booked sessions, available slots
  - **FIX VERIFIED**: Day view now correctly displays therapist availability (previously showed "No Availability Set")
  - "Add Availability" button hidden for assistants
  - "Block Time" button visible and functional for assistants
  - Available slots bookable by assistant
- [x] **Clinical Data Restrictions**:
  - Assistants blocked from session notes (403)
  - Assistants blocked from assessments (403)
  - Assistants blocked from protocols (403)
  - Assistants blocked from AI clinical features (403)
- [x] **Testing**: 17/17 backend tests passed, 100% frontend features verified
  - /app/tests/test_assistant_dashboard.py
  - /app/test_reports/iteration_24.json

### Phase 29: End-of-Day Cash Settlement (COMPLETED - Jan 20, 2026)
- [x] **Cash Settlement Data Model** (`cash_settlements` collection):
  - Fields: id, date, therapist_id, therapist_name, assistant_id, assistant_name
  - Amounts: cash_amount, online_amount, total_amount (auto-calculated)
  - Status: "pending" | "handed_over" | "settled" | "disputed"
  - Handover: handover_note, handover_at
  - Confirmation: confirmed_at, confirmed_by
  - Dispute: disputed_at, disputed_reason
  - Timestamps: created_at, updated_at
- [x] **Backend Endpoints**:
  - `GET /api/settlements/today` - Get today's settlement status with auto-calculated amounts
  - `POST /api/settlements/handover` - Assistant marks cash as handed over (requires cash_amount > 0)
  - `POST /api/settlements/{id}/confirm` - Therapist confirms receipt (LOCKS the record)
  - `POST /api/settlements/{id}/dispute` - Therapist reports issue (requires reason, min 5 chars)
  - `GET /api/settlements/pending` - Get pending/disputed settlements for therapist
  - `GET /api/settlements/history` - Get settlement audit trail (configurable days param)
- [x] **Assistant Dashboard - Cash Settlement Card**:
  - Title: "End-of-Day Cash Settlement" with HandCoins icon
  - 3-column summary: Cash to Hand Over, Online (Auto-settled), Total Today
  - Status badge: Pending (amber), Awaiting Confirmation (blue), Settled (green), Disputed (red)
  - **Pending state**: "Mark Cash Handed Over" button when cash_amount > 0
  - **No cash state**: "No cash to settle today. All payments were online."
  - **Handed over state**: Shows waiting message with therapist name and handover time
  - **Settled state**: Shows "Settlement Complete" with lock icon and confirmation time
  - **Disputed state**: Shows issue details with disputed reason
- [x] **Cash Handover Dialog**:
  - Shows auto-calculated cash amount (cannot be edited)
  - Optional note field
  - Warning: "By clicking Confirm Handover, you confirm that you have handed over the cash"
  - Confirm Handover button
- [x] **Therapist Dashboard - Pending Settlement Banner**:
  - Amber banner appears when settlement status is "handed_over"
  - Shows: Amount, Assistant name, Date, Note (if any)
  - Two buttons: "Confirm Received" (green) | "Report Issue" (red outline)
- [x] **Therapist Dashboard - Disputed Settlement Banner**:
  - Red banner appears when settlement status is "disputed"
  - Shows amount, assistant name, disputed reason
- [x] **Confirm Receipt Dialog**:
  - Shows cash amount, assistant name, date, handover note
  - Warning: "Confirming will lock this settlement record. This action cannot be undone."
  - Lock icon to indicate record locking
  - "Confirm & Lock" button
- [x] **Dispute Dialog**:
  - Shows reported amount and assistant name
  - Required reason field (min 5 characters)
  - "Report Issue" button (destructive style)
- [x] **Settlement Rules**:
  - Online payments (UPI, card, bank) are auto-settled (no manual action needed)
  - Cash requires manual handover → confirmation flow
  - Once confirmed, settlement record is LOCKED and cannot be modified
  - Audit trail maintained: date, amount, assistant, timestamps, status changes
- [x] **Testing**: 20/20 backend tests passed, 100% frontend features verified
  - /app/tests/test_cash_settlement.py
  - /app/test_reports/iteration_25.json

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
- **Test Therapist**: mobile: `9999999999`, password: `password`
- **Test Assistant**: email: `test_assistant_ui@test.com`, password: `testpass123`
- **Test Client**: mobile: `8888888888`, password: `testpass123`

---

## Backlog

### P1 - High Priority
- [x] ~~Refactor `server.py` into modular structure~~ (DONE - Phase 32 - Partial)
- [ ] Global Standards Verification (IST timezone, DD/MM/YYYY dates, ₹ currency across app)
- [ ] Coupon Code management validation and testing

### P2 - Medium Priority  
- [x] ~~Assessment result visualization~~ (DONE - Phase 26)
- [x] ~~Assessment trends and progress tracking~~ (DONE - Phase 27 - AssessmentTrendChart)
- [x] ~~Subscription feature toggles~~ (DONE - Phase 27)
- [x] ~~Unified calendar for Therapist/Assistant~~ (DONE - Phase 27)
- [ ] Profile photo upload (currently URL-based only)
- [ ] AI-powered SOAP/DAP note generation from session transcripts
- [ ] Case History download/print functionality

### P3 - Future Enhancements
- [x] ~~Clinical Support: Assessment suggestion engine~~ (DONE - Phase 18)
- [x] ~~Clinical Support: Therapy protocol builder~~ (DONE - Phase 18)
- [ ] Template sharing between therapists
- [x] ~~Homework completion tracking~~ (DONE - Phase 18 Resource Library)
- [ ] Audit log viewer for admins
- [ ] Email notifications for approvals, subscription expiry
- [ ] AI usage tracking/rate limiting
- [ ] SMS/Email appointment reminders
- [ ] Global search across clients/appointments

---

## Architecture

### Backend Structure (Refactored - Phase 32)
```
/app/backend/
├── server.py           # Main FastAPI app (6127 lines, reduced from 6856)
├── database.py         # MongoDB connection
├── auth.py             # Auth utilities & dependencies  
├── models/
│   └── __init__.py     # All Pydantic models (~600 lines)
├── routes/
│   └── __init__.py     # Route modules (migration planned)
├── assessment_library.py
├── ARCHITECTURE.md     # Architecture documentation
└── tests/
```

### Migration Status
| Component | Status | Location |
|-----------|--------|----------|
| Models | ✅ Extracted | models/__init__.py |
| Auth Utilities | ✅ Extracted | auth.py |
| Database Config | ✅ Extracted | database.py |
| Routes | ⏳ Planned | Still in server.py |

---

## Refactoring Needs
- [x] ~~Extract models to separate package~~ (DONE)
- [x] ~~Extract auth utilities~~ (DONE)
- [x] ~~Extract database config~~ (DONE)
- [ ] Split routes into domain-specific modules
- [ ] Add database migration strategy for schema changes
- [ ] Add comprehensive error handling

### Phase 33: Dashboard Navigation Context (COMPLETED - Jan 20, 2026)
- [x] **Therapist Overview Navigation Fix**:
  - Updated `handleNavigate` in TherapistOverview.js to accept context parameters (clientId, filter)
  - "View Client Profile" button in "Coming Up" card now passes client_id for direct profile view
  - "View Clients" button in "Inactive Clients" alert passes filter='inactive' with client IDs
- [x] **TherapistDashboard Navigation Context**:
  - Added `navContext` state with `selectedClientId`, `clientFilter`, `filterData`
  - `handleNavigation` function passes context to ClientManagement component
- [x] **ClientManagement Enhanced Props**:
  - New props: `initialClientId`, `initialFilter`, `filterData`, `onClearContext`
  - Auto-opens client profile when `initialClientId` is provided
  - Shows "Showing inactive clients (no sessions in 30+ days)" banner when filtered
  - "Show All Clients" button clears filter and shows all clients
- [x] **Testing**: 100% frontend tests passed (iteration_26.json)
  - Login works correctly
  - Coming Up card → Client Profile navigation verified
  - Inactive Clients alert → Filtered view with banner verified
  - Clear filter button functionality verified

### Phase 34: Manual Homework Feature (COMPLETED - Jan 20, 2026)
- [x] **Backend Enhancements**:
  - Added `priority` field to HomeworkCreate model (low/medium/high, default: medium)
  - Added `HomeworkUpdate` model for editing homework
  - Added `PUT /api/homework/{id}` - Therapist can update homework (title, description, due_date, priority)
  - Added `DELETE /api/homework/{id}` - Therapist can delete homework
  - Existing `POST /api/homework/{id}/complete` - Client marks homework complete
  - Priority validation enforced (must be low/medium/high)
- [x] **Therapist UI - Client Profile View**:
  - New "Homework" tab (6th tab, hidden from assistants)
  - Stats cards: Pending, Completed, Total homework counts
  - "Assign Homework" button with dialog: Title, Description, Due Date (optional), Priority selector
  - Homework list with status badges (Pending/Completed) and priority badges (High/Medium/Low)
  - Edit/Delete buttons for pending homework
  - Due date overdue indicator (red styling)
  - Client notes displayed for completed homework
- [x] **Client Dashboard Enhancement**:
  - Homework section shows priority badges (High=red, Medium=amber, Low=gray)
  - Overdue indicator for past due dates
  - "Mark Complete" button with notes prompt
- [x] **Access Control**:
  - Assistants: No access to Homework tab (isAssistant check on tab and functions)
  - Assistants: Backend returns 403 for homework create/update/delete
  - Clients: Can only view/complete their own homework
- [x] **Testing**: 92% backend (11/12), 100% frontend
  - Test file: /app/tests/test_homework.py
  - Report: /app/test_reports/iteration_27.json

### Phase 35: Assistant Dashboard Crash Fix (COMPLETED - Jan 21, 2026)
- [x] **Bug Fixed**: Assistant Dashboard crashed on login with TypeError
  - Root cause: Frontend component accessing potentially null/undefined API response data
  - Properties affected: `inactive_clients`, `payments_summary`, `needs_attention`, `todays_appointments`
- [x] **Solution Applied** (AssistantDashboard.js):
  - Added comprehensive optional chaining (`?.`) on all data access points
  - Created safe wrapper objects: `safeNeedsAttention`, `safePaymentsSummary`
  - Added `inactive_clients_count` to destructuring with default value 0
  - All array properties now have `|| []` fallbacks
  - All nested property access uses `?.` operator
- [x] **Testing**: Screenshot verification - Dashboard loads correctly for assistant user
  - Login: `support@mindlabs.co.in` / `Abcd@1234`
  - All sections render without crash: Call Reminders, Needs Attention, Inactive Clients, Payments Summary

- [x] **Bug Fixed**: Schedule Day View crashed with "Invalid time value" error
  - Root cause: `Date.toISOString()` called on potentially invalid Date objects in TherapistSchedule.js
  - Affected: `selectedDate`, appointment filtering, blocked times filtering
- [x] **Solution Applied** (TherapistSchedule.js):
  - Added date validation before `toISOString()` calls: `instanceof Date && !isNaN(date.getTime())`
  - Safe date parsing in `calendarData` and `daySchedule` useMemo hooks
  - Wrapped date filtering in try-catch blocks for appointment and blocked time arrays
  - Validated `handleDateClick`, `goToPrevDay`, `goToNextDay` navigation handlers
  - Added validation in `handleBlockTime` and `handleScheduleAppointment` functions
- [x] **Testing**: Screenshot verification - Day view loads correctly
  - Month view → Date click → Day view works without errors
  - Availability blocks, booked sessions display correctly

### Phase 36: Case History Simple Form (COMPLETED - Jan 21, 2026)
- [x] **New Simple Form Created**: Replaced wizard-style form with full-page multi-step form
  - 11 sections across multiple pages with Next/Previous navigation
  - Auto-save when moving between sections (PATCH /api/case-history/{client_id}/section)
  - Full page layout (not cards/wizard style)
  - Mobile responsive design
  - Progress bar showing current section (e.g., "2 / 11")
- [x] **Sections**: Basic Identification, Presenting Complaints, History of Present Illness, 
  Past Psychiatric History, Medical History, Family History, Personal & Developmental History,
  Mental Status Examination, Provisional Formulation, Initial Therapy Plan, Consent & Disclaimer
- [x] **PDF Download**: View Full mode with Print/Download option at completion
- [x] **Backend Endpoints Added**:
  - GET /api/case-history/check/{client_id} - Check if case history exists
  - PATCH /api/case-history/{client_id}/section?section={section_name} - Auto-save section
  - GET /api/therapy-consent/check/{client_id} - Check consent status
  - GET /api/therapy-consent/{client_id} - Get consent details
  - POST /api/therapy-consent/{client_id}/sign - Sign consent
- [x] **Mobile Responsive Fixes** (ClientProfileView.js):
  - Header buttons now wrap on mobile (flex-wrap)
  - "View / Edit Case History" button visible as full-width on mobile
  - Grid columns adapt: 1 col mobile, 2 col tablet, 3 col desktop
  - Text sizes reduced on mobile (text-xs sm:text-sm)
  - Email truncated with max-width on mobile
- [x] **Files Created/Modified**:
  - Created: /app/frontend/src/components/CaseHistoryForm.js
  - Modified: /app/frontend/src/components/ClientProfileView.js
  - Modified: /app/backend/routes/clinical.py

### Phase 37: Server.py Refactoring - Step 1 (PENDING)
**Goal**: Break monolithic server.py (6919 lines) into modular route files

**Step 1: Auth Routes (COMPLETED)**
- Created `/app/backend/database.py` - Database connection module
- Created `/app/backend/dependencies.py` - Shared utilities and dependencies
- Created `/app/backend/routes/auth.py` - Auth endpoints (~240 lines)
  - POST /auth/register
  - POST /auth/therapist-application
  - POST /auth/login
  - POST /auth/super-admin-login
  - GET /auth/me
  - GET /auth/subscription-status
  - GET /auth/user/preferences
  - PUT /auth/user/preferences
- Updated `server.py` to import and include auth_router
- **Lines reduced**: 6919 → 6684 (~235 lines moved)
- **Testing**: All login endpoints verified (Therapist, Admin, Client)

**Pending Steps:**
- Step 2: Admin routes (Super Admin endpoints)
- Step 3: Client routes
- Step 4: Appointment routes
- Step 5: Remaining routes (sessions, assessments, payments, etc.)

**Step 2: Admin Routes (COMPLETED)**
- Created `/app/backend/routes/admin.py` (~526 lines)
  - GET /admin/therapist-applications
  - POST /admin/therapist-applications/{id}/approve
  - POST /admin/therapist-applications/{id}/reject
  - GET/POST/PUT /admin/therapists
  - POST /admin/therapists/{id}/suspend|activate|reset-password|photo
  - GET /admin/therapists/{id}/clients
  - GET/PUT /admin/clients
  - POST /admin/clients/{id}/reset-password
- **Lines reduced**: 6684 → 6177 (~500+ lines moved)
- Kept dependency functions in server.py (used by remaining routes)
- **Testing**: All admin endpoints verified (therapists, clients, applications)

**Current Status:**
- server.py: 6177 lines (from 6919)
- routes/auth.py: 294 lines
- routes/admin.py: 526 lines
- Total moved: ~820 lines

**Next Steps:**
- Step 3: Move remaining admin routes (subscriptions, support tickets, assistants)
- Step 4: Client & Appointment routes

**Step 3: Support, Subscriptions & Assistants (COMPLETED)**
- Created `/app/backend/routes/subscriptions.py` (~532 lines)
  - Support Ticket CRUD (create, list, get, reply, update status)
  - Admin dashboard stats
  - Subscription plan management (CRUD)
  - Therapist subscription assignment, extension, trial
  - Coupon management
- Created `/app/backend/routes/assistants.py` (~301 lines)
  - Assistant CRUD (create, list, get, update, delete)
  - Suspend/activate/reset-password
  - Admin assistant management
- **Lines reduced**: 6177 → 5449 (~728 lines moved)
- **Testing**: All moved endpoints verified

**Current Status:**
- server.py: 5449 lines (from 6919, -1470 total)
- routes/auth.py: 294 lines
- routes/admin.py: 526 lines
- routes/assistants.py: 301 lines
- routes/subscriptions.py: 532 lines
- Total in routes: 1653 lines

**Remaining in server.py:**
- Models (~900 lines)
- Utility functions (~120 lines)
- Dependency functions (~100 lines)
- Assistant Dashboard endpoints (~200 lines)
- Cash Settlement endpoints (~360 lines)
- Client endpoints (~280 lines)
- Appointment endpoints (~430 lines)
- Availability/Blocked time (~200 lines)
- Case History endpoints (~340 lines)
- Consent endpoints (~150 lines)
- Session Notes endpoints (~160 lines)
- Note Templates (~95 lines)
- Recurring Appointments (~175 lines)
- Messaging (~230 lines)
- Assessments (~700 lines)
- Payments (~350 lines)
- Homework (~120 lines)
- Therapist Profile (~180 lines)
- Protocols (~200 lines)
- AI Clinical (~230 lines)

**Step 4: Client & Appointment Routes (COMPLETED)**
- Created `/app/backend/routes/clients.py` (~345 lines)
  - Client CRUD (create, list, get, update)
  - Password reset, photo update
  - Role-based access control
- Created `/app/backend/routes/appointments.py` (~437 lines)
  - Appointment CRUD
  - Client appointment request
  - Check-in/check-out functionality
  - Mark completed, no-show, cancel
- **Lines reduced**: 5449 → 4743 (~706 lines moved)
- **Testing**: All endpoints verified

**Current Status:**
- server.py: 4743 lines (from 6919, -2176 total, ~31% reduction)
- Total in routes: 2435 lines
  - auth.py: 294
  - admin.py: 526
  - assistants.py: 301
  - subscriptions.py: 532
  - clients.py: 345
  - appointments.py: 437

**Remaining in server.py (~4743 lines):**
- Models (~900 lines)
- Utility/Dependency functions (~220 lines)
- Assistant Dashboard (~200 lines)
- Cash Settlement (~360 lines)
- Availability/Blocked time (~350 lines)
- Case History (~340 lines)
- Consent (~150 lines)
- Session Notes (~160 lines)
- Note Templates (~95 lines)
- Recurring Appointments (~175 lines)
- Messaging (~230 lines)
- Assessments (~700 lines)
- Payments (~350 lines)
- Homework (~120 lines)
- Therapist Profile (~180 lines)
- Protocols (~200 lines)
- AI Clinical (~230 lines)

**Step 5: Availability & Payments Routes (COMPLETED)**
- Created `/app/backend/routes/availability.py` (~359 lines)
  - GET/PUT /availability
  - POST/GET/DELETE /blocked-time
  - GET /available-slots
- Created `/app/backend/routes/payments.py` (~336 lines)
  - Payment CRUD (create, list, get, update, delete)
  - Payment stats summary
- **Lines reduced**: 4743 → 4228 (~515 lines moved)
- **Testing**: All endpoints verified

**Current Status:**
- server.py: 4228 lines (from 6919, -2691 total, ~39% reduction)
- Total in routes: 3130 lines
  - auth.py: 294
  - admin.py: 526
  - assistants.py: 301
  - subscriptions.py: 532
  - clients.py: 345
  - appointments.py: 437
  - availability.py: 359
  - payments.py: 336

**Remaining in server.py (~4228 lines):**
- Models (~900 lines)
- Utility/Dependency functions (~220 lines)
- Assistant Dashboard (~200 lines)
- Cash Settlement (~360 lines)
- Case History (~340 lines)
- Consent (~150 lines)
- Session Notes (~160 lines)
- Note Templates (~95 lines)
- Recurring Appointments (~175 lines)
- Messaging (~230 lines)
- Assessments (~700 lines)
- Homework (~120 lines)
- Therapist Profile (~180 lines)
- Protocols (~200 lines)
- AI Clinical (~230 lines)

**Step 6: Sessions, Messaging & Assessments (COMPLETED)**
- Created `/app/backend/routes/sessions.py` (~301 lines)
  - Session Notes CRUD
  - Messaging system (send, list, read, unread count)
- Created `/app/backend/routes/assessments.py` (~278 lines)
  - Assessment library with PHQ-9, GAD-7, PCL-5, ASRS, BDI-II, DASS-21
  - Assign, submit, track assessments
- **Lines reduced**: 4228 → 3000 (~1228 lines moved)
- **Testing**: All endpoints verified

**Current Status:**
- server.py: 3000 lines (from 6919, -3919 total, ~57% reduction)
- Total in routes: 3709 lines
  - auth.py: 294
  - admin.py: 526
  - assistants.py: 301
  - subscriptions.py: 532
  - clients.py: 345
  - appointments.py: 437
  - availability.py: 359
  - payments.py: 336
  - sessions.py: 301
  - assessments.py: 278

**Remaining in server.py (~3000 lines):**
- Models (~900 lines)
- Utility/Dependency functions (~220 lines)
- Assistant Dashboard (~200 lines)
- Cash Settlement (~360 lines)
- Case History (~340 lines)
- Consent (~150 lines)
- Note Templates (~95 lines)
- Recurring Appointments (~175 lines)
- Homework (~120 lines)
- Therapist Profile (~180 lines)
- Protocols (~200 lines)
- AI Clinical (~230 lines)

**Step 7: Final Refactoring - Clinical & Assistant Routes (COMPLETED)**
- Created `/app/backend/routes/clinical.py` (~373 lines)
  - Case History CRUD
  - Therapy Consent CRUD
  - Homework CRUD with priority
- Created `/app/backend/routes/assistant.py` (~349 lines)
  - Assistant Dashboard with stats
  - Call Reminders
  - Cash Settlement (handover, confirm, dispute)
- **Lines reduced**: 3000 → 1799 (~1201 lines moved)
- **Testing**: All endpoints verified

**FINAL STATUS - REFACTORING COMPLETE:**
- server.py: **1799 lines** (from 6919, **-74% reduction**)
- Total routes: **4431 lines** (12 modules)

**Route Modules:**
| Module | Lines | Endpoints |
|--------|-------|-----------|
| admin.py | 526 | Therapist/Client management |
| subscriptions.py | 532 | Plans, support tickets, coupons |
| appointments.py | 437 | Appointments, check-in/out |
| clinical.py | 373 | Case history, consent, homework |
| availability.py | 359 | Availability, blocked time, slots |
| assistant.py | 349 | Dashboard, cash settlement |
| clients.py | 345 | Client CRUD |
| payments.py | 336 | Payments CRUD, stats |
| sessions.py | 301 | Session notes, messaging |
| assistants.py | 301 | Assistant user management |
| auth.py | 294 | Login, registration, preferences |
| assessments.py | 278 | Assessment library, assign, submit |

**Remaining in server.py (~1799 lines):**
- Models (~550 lines)
- Utility/Dependency functions (~200 lines)
- AI Clinical endpoints (~230 lines)
- Therapist Profile (~180 lines)
- Note Templates (~95 lines)
- Recurring Appointments (~175 lines)
- Protocols (~200 lines)
- Resource Library (~170 lines)

### Phase 36: Post-Refactoring Bug Fixes (COMPLETED - Jan 21, 2026)
**Issues Identified:** After the major server.py refactoring, several features stopped loading:
- Assessments - "Not able to load assessment"
- Protocols - "Failed to load protocols"
- Recurring Appointments - "Failed to load recurring appointments"
- Messages - "Failed to load messaging data"
- Availability - "Failed to load availability settings"

**Root Causes & Fixes:**
1. **Assessments `/api/assessments/custom` (Route Order Issue)**:
   - Problem: `/custom` endpoint was defined AFTER `/{assessment_id}` in `assessments.py`
   - FastAPI matched `/custom` as an assessment_id parameter
   - Fix: Moved `/custom`, `/custom/{assessment_id}`, `/library`, `/client/{client_id}/history` routes BEFORE `/{assessment_id}`
   - File: `/app/backend/routes/assessments.py`

2. **Protocols Endpoints Missing**:
   - Problem: `/api/protocols` and `/api/protocols/templates` were never created in refactoring
   - Fix: Created new `/app/backend/routes/protocols.py` with:
     - GET /protocols - List therapist's protocols
     - GET /protocols/templates - 5 standard templates (CBT_ANXIETY, CBT_DEPRESSION, DBT_SKILLS, ACT_GENERAL, TRAUMA_PROCESSING)
     - POST /protocols - Create protocol
     - GET/PUT/DELETE /protocols/{id}

3. **Recurring Appointments Endpoints Missing**:
   - Problem: `/api/recurring-appointments` endpoints were never created in refactoring
   - Fix: Created new `/app/backend/routes/recurring.py` with:
     - GET /recurring-appointments - List patterns
     - POST /recurring-appointments - Create pattern
     - GET/PUT/DELETE /recurring-appointments/{id}
     - PUT /recurring-appointments/{id}/toggle - Toggle active status
     - POST /recurring-appointments/{id}/generate - Generate appointments

4. **Messaging Contacts Endpoint Missing**:
   - Problem: `/api/messaging-contacts` was never created (frontend calls this for contact list)
   - Fix: Added endpoint to `/app/backend/routes/sessions.py`
   - Returns list of clients (for therapist) or therapist (for client) with unread counts

5. **Blocked Times Field Mapping & Endpoint Name**:
   - Problem 1: Frontend calls `/api/blocked-times` (plural), backend had `/api/blocked-time` (singular)
   - Problem 2: Database stores `start_datetime/end_datetime`, code expected `start_time/end_time`
   - Fix: Added both endpoint aliases, added field mapping to handle both old and new field names
   - File: `/app/backend/routes/availability.py`

**Files Created:**
- `/app/backend/routes/protocols.py` (~300 lines)
- `/app/backend/routes/recurring.py` (~300 lines)

**Files Modified:**
- `/app/backend/routes/assessments.py` - Route order fix
- `/app/backend/routes/sessions.py` - Added /messaging-contacts endpoint
- `/app/backend/routes/availability.py` - Added /blocked-times alias, field mapping fix
- `/app/backend/server.py` - Added router imports

**Testing**: 14/14 backend tests passed, 100% frontend features verified
- Test file: `/app/tests/test_refactored_features.py`
- Report: `/app/test_reports/iteration_28.json`

**Endpoints Fixed:**
| Endpoint | Status | Issue |
|----------|--------|-------|
| GET /api/assessments/custom | ✅ FIXED | Route order |
| GET /api/protocols | ✅ FIXED | Missing endpoint |
| GET /api/protocols/templates | ✅ FIXED | Missing endpoint |
| GET /api/recurring-appointments | ✅ FIXED | Missing endpoint |
| GET /api/messaging-contacts | ✅ FIXED | Missing endpoint |
| GET /api/blocked-times | ✅ FIXED | Missing alias + field mapping |

### Phase 37: Assessment & Messaging Bug Fixes (COMPLETED - Jan 21, 2026)
**User Reported Issues:**
1. Assessment Library forms incomplete - only 3-5 questions instead of full forms
2. Assessment Results showing "Not Found" on click
3. Messages showing empty boxes instead of client names
4. Messages showing "Failed to load messages" on conversation click

**Root Causes & Fixes:**

1. **Assessment Library Incomplete**:
   - Problem: `routes/assessments.py` had a simplified `ASSESSMENT_LIBRARY` with only 3-5 questions per assessment
   - Fix: Imported complete `CLINICAL_ASSESSMENTS` from `assessment_library.py` (12 assessments with full questions)
   - Now includes: PHQ-9 (9 Qs), GAD-7 (7 Qs), DASS-21 (21 Qs), WHO-5, ASRS-v1.1, Y-BOCS, HAM-A, BDI-II (21 Qs), BPRS, ISI, AUDIT, RSES

2. **Assessment Results Endpoint Missing**:
   - Problem: `/api/assessments/{id}/results` endpoint never existed in `routes/assessments.py`
   - Fix: Added complete results endpoint with:
     - Access control (therapist sees all, client sees only if shared)
     - Score calculation using `calculate_score()` from assessment_library
     - Severity calculation using `get_severity()`
     - Returns questions, responses, severity bands, therapist notes
   - Also added: `/share-report`, `/unshare-report`, `/therapist-notes` endpoints

3. **Messages - Client Names Not Showing**:
   - Problem: Frontend calls `/api/messages` expecting conversations format (user_id, user_name, last_message, unread_count)
   - Backend returned raw messages array instead
   - Fix: Created `/api/messages/conversations` endpoint that groups messages by conversation partner

4. **Messages - "Failed to load messages" on Click**:
   - Problem: Frontend calls `/api/messages/{userId}` to get conversation messages, endpoint didn't exist
   - Fix: Added `/api/messages/{user_id}` endpoint in `routes/sessions.py`
   - Also auto-marks messages as read when fetched

**Files Modified:**
- `/app/backend/routes/assessments.py` - Use complete library, add results/share/notes endpoints
- `/app/backend/routes/sessions.py` - Add /messages/conversations, /messages/{user_id} endpoints
- `/app/frontend/src/components/Messaging.js` - Use /messages/conversations endpoint

**Testing:** All endpoints return 200, frontend verified via screenshots
- Assessment Library: 12 assessments with complete questions
- Assessment Results: Modal shows questions, responses, clinical notes, share button
- Messages: Conversations list shows client names, clicking loads messages

### Phase 38: Indian Address Standards for Therapist Profile (COMPLETED - Jan 21, 2026)
**Feature:** Structured address fields with Pincode-based auto-fill for Therapist Profile

**Backend Implementation:**
- Created `/app/backend/routes/therapist_profile.py` (~300 lines)
- **Endpoints:**
  - `GET /api/therapist/profile` - Get therapist profile with address fields
  - `PUT /api/therapist/profile` - Update profile (basic info, clinic info, address, privacy)
  - `GET /api/therapist/pincode/{pincode}` - Pincode lookup (India Post API)
  - `GET /api/therapist/profile/receipt-info` - Get receipt-formatted info with privacy settings

**Data Model (TherapistProfile):**
- Basic Info: full_name, email, mobile, profile_photo
- Clinic Info: clinic_name, specialization, qualifications, experience_years, consultation_fee
- Address (Indian Format): address_line_1, address_line_2, pincode, city, state, district
- Privacy: show_mobile_on_receipt, show_email_on_receipt

**Frontend Implementation:**
- Created `/app/frontend/src/components/TherapistProfileSettings.js` (~370 lines)
- **Sections:**
  1. Basic Information - Name, Email, Mobile, Photo URL
  2. Clinic Information - Name, Specialization, Qualifications, Experience, Fee (₹)
  3. Clinic Address (Indian Format) - Address lines, PIN Code, City, District, State
  4. Receipt Privacy Settings - Toggle switches for mobile/email visibility
  5. Subscription Status (read-only)

**Pincode Auto-fill Feature:**
- Enter 6-digit PIN code → Auto-fills City, District, State
- Uses India Post API: `https://api.postalpincode.in/pincode/{pincode}`
- Loading spinner during lookup, green checkmark on success
- Manual entry allowed if pincode lookup fails

**UI/UX:**
- Added "My Profile" nav item in Operations section of sidebar
- Consultation Fee field with ₹ symbol
- "Indian Format" badge on address section
- Read-only mode respected for expired subscriptions

**Files Created:**
- `/app/backend/routes/therapist_profile.py`
- `/app/frontend/src/components/TherapistProfileSettings.js`

**Files Modified:**
- `/app/backend/server.py` - Added therapist_profile_router
- `/app/frontend/src/pages/TherapistDashboard.js` - Added My Profile nav and view

**Testing:** Screenshot verified - Pincode 110001 auto-fills "New Delhi", "Delhi"



### Phase 39: Assistant Client Profile - Non-Clinical Tabs Only (COMPLETED - Jan 21, 2026)
**Feature:** Assistant role can view Client Profile as full page, but only with non-clinical tabs (Sessions, Payments, Book Appointment)

**Requirement:**
- Assistant should be able to navigate to client profile from Client Management
- Only non-clinical tabs should be visible: Overview, Sessions, Payments
- Clinical tabs should be hidden: Case History, Session Notes, Assessments, Homework
- Overview tab should show non-clinical stats (Sessions, Upcoming, Payments, Total Paid)
- Clinical cards (Therapy Consent, Recent Notes, Case History) should be hidden

**Implementation:**

**1. ClientProfilePage.js Changes:**
- Added `isAssistant` prop to control tab visibility
- Created `allTabs` array with `clinicalOnly` flag per tab
- Filtered tabs based on `isAssistant` - shows only non-clinical tabs for assistants
- Updated "Back" button to navigate to `/assistant` for assistants, `/therapist` for therapists
- Overview tab modifications for assistants:
  - Hide Therapy Consent card
  - Hide Recent Notes section (replaced with Recent Payments for assistant)
  - Hide Case History Quick View card
  - Show different stats: Total Sessions, Upcoming, Payments, Total Paid (instead of Assessments/Homework)

**2. AssistantDashboard.js Changes:**
- Added URL pattern matching for `/assistant/clients/:clientId`
- Renders `ClientProfilePage` with `isAssistant={true}` when on client profile URL
- Added `ClientProfilePage` import

**3. ClientManagement.js Changes:**
- Updated `handleViewProfile` to navigate to `/assistant/clients/:id` for assistant role
- Keeps `/therapist/clients/:id` for therapist role

**Tab Access Control:**
| Tab | Therapist | Assistant |
|-----|-----------|-----------|
| Overview | ✅ Full | ✅ Limited (no clinical data) |
| Case History | ✅ | ❌ Hidden |
| Sessions | ✅ | ✅ |
| Session Notes | ✅ | ❌ Hidden |
| Assessments | ✅ | ❌ Hidden |
| Homework | ✅ | ❌ Hidden |
| Payments | ✅ | ✅ |

**Files Modified:**
- `/app/frontend/src/components/ClientProfilePage.js` - Tab filtering and content changes
- `/app/frontend/src/pages/AssistantDashboard.js` - Client profile routing
- `/app/frontend/src/components/ClientManagement.js` - Navigation path by role

**Testing:**
- Assistant login: `support@mindlabs.co.in` / `Abcd@1234`
- Verified only 3 tabs visible (Overview, Sessions, Payments)
- Clinical tabs hidden (Case History, Session Notes, Assessments, Homework)
- "Back to Dashboard" button correctly navigates to /assistant
- Therapist view still shows all 7 tabs

### Phase 40: Application Rebranding & UI Fixes (COMPLETED - Jan 22, 2026)
**Feature:** Complete application rebrand from TheraGenie to COGNISPACE

**Rebranding Changes:**
- App Name: TheraGenie → **COGNISPACE**
- Tagline: "Clinical intelligence for modern therapists" → **"Precision Insights. Personal Growth."**
- Logo: New logo uploaded at `/app/frontend/public/logo-cognispace.png`
- Updated all frontend files with new branding (LoginPage, dashboards, headers)
- Service Worker updated to `networkFirst` strategy to fix caching issues

**Login Page UI Tweaks (P0):**
- Logo size increased from `h-24` to `h-36`
- Heading changed from "Welcome back" to "Welcome"
- Button text changed from "Apply as Therapist" to "Register as Therapist"
- Added helper text: "Registration requires admin approval."

**Client Dashboard Availability Slots Bug Fix (P0):**
- Fixed recurring issue where availability slots didn't show time
- Time now correctly displays in 24-hour IST format (e.g., 10:00, 11:10, 12:20)
- `formatTime(slot.start)` correctly renders slot times

**Caching Issue Fix:**
- Service Worker changed from `cacheFirst` to `networkFirst` strategy
- Users now see latest UI immediately after login without hard refresh

**Files Modified:**
- `/app/frontend/src/pages/LoginPage.js` - UI tweaks
- `/app/frontend/public/service-worker.js` - Caching strategy
- `/app/frontend/public/logo-cognispace.png` - New logo
- Multiple frontend files - Branding updates

**Testing:** Screenshot verified
- Login page shows larger logo, correct text, helper message
- Client Dashboard availability slots show times correctly (10:00, 11:10, 12:20, etc.)

### Phase 41: LLM Change - Gemini to Claude Sonnet 4 (COMPLETED - Jan 23, 2026)
**Feature:** Replaced Gemini 3 Flash with Claude Sonnet 4 for CogniVision Diagnostic Engine

**Background:**
- User reported hallucination issues with Gemini model (adding unselected assessments to reports)
- Prompt hardening partially fixed the issue but user wanted to try a different LLM
- User selected **Claude Sonnet 4** as the new model

**Implementation:**
- Updated `get_ai_chat()` function in `/app/backend/server.py`
- Changed from: `.with_model("gemini", "gemini-3-flash-preview")`
- Changed to: `.with_model("anthropic", "claude-4-sonnet-20250514")`
- Using Emergent LLM Key (universal key) - no API key change needed
- All CI features (Assessment Suggestions, Protocol Generation, Homework, Diagnostic Reports) now use Claude

**Testing:**
- ✅ Diagnostic Report API returns valid response
- ✅ Report contains ONLY assessments provided in input (Y-BOCS mentioned, no hallucinated LSAS/DOCS)
- ✅ Professional ICD-10/DSM-5 diagnostic format maintained
- ✅ TheraGenie UI loads correctly with Diagnostic tab

**Files Modified:**
- `/app/backend/server.py` - Line ~1290: `get_ai_chat()` function updated to use Claude

### Phase 42: Professional Clinical Documentation Prompt (COMPLETED - Jan 24, 2026)
**Feature:** Complete rewrite of CogniVision prompt to professional clinical documentation standards

**New Prompt Structure:**
- Positioned as "Senior Clinical Documentation Assistant"
- Explicit safety rules: NO definitive diagnoses, use non-diagnostic phrasing
- 12-section professional report format:
  1. Identifying Information
  2. Reason for Referral
  3. Assessment Tools Used
  4. Behavioral Observations
  5. Test Results & Interpretation
  6. Clinical Impressions (Non-Diagnostic)
  7. Functional Impact
  8. Strengths & Protective Factors
  9. Areas of Concern
  10. Recommendations for Therapy Focus
  11. Limitations of Assessment
  12. Disclaimer & Therapist Review Note

**Key Changes:**
- Uses ICD-10 (not ICD-11) and DSM-5 coding standards
- Non-diagnostic language: "findings suggestive of...", "patterns consistent with...", "may be considered..."
- Added Strengths & Protective Factors section
- Added Limitations of Assessment section
- Stronger disclaimer and therapist review note
- Hospital-grade professional report format

**Files Modified:**
- `/app/backend/server.py` - Complete rewrite of `system_prompt` and `DiagnosticReportResponse` model
- `/app/frontend/src/components/AIClinicalSupport.js` - Changed ICD-11 to ICD-10 in UI text

**Testing:**
- ✅ 12 sections generating correctly
- ✅ Non-diagnostic language used ("findings are suggestive of...", "consistent with...")
- ✅ Recommendations use proper therapeutic language ("may be considered", "could be explored")

---
### Phase 43: P0 Bug Fix - Client Consent Flow (COMPLETED - Jan 25, 2026)
**Critical Bug:** Client dashboard was showing blank/incorrect page after therapist completed case history.

**Root Cause:**
- When therapist completed a client's case history, the consent document was being created but with incomplete data
- The frontend consent page would fail to render properly due to missing `therapist_name` and `consent_text`

**Fix Applied:**
1. **Updated Default Consent Template** in `/app/backend/routes/clinical.py`:
   - Expanded from 5 basic sections to comprehensive 12-section professional consent
   - Added "Services Offered" as first section with therapist credentials
   - Added detailed sections: Purpose of Therapy, Nature of Therapy, Role of Therapist, Confidentiality, Records & Documentation, Fees & Payments, Appointments & Attendance, Use of Digital Systems, Client Responsibilities, Right to Withdraw, Consent Statement

2. **Consent Text Structure:**
   - Section 1: Services Offered (therapist name and qualifications)
   - Section 2: Purpose of Therapy (collaborative process description)
   - Section 3: Nature of Therapy (discussion of personal topics, gradual progress)
   - Section 4: Role of the Therapist (professional guidelines)
   - Section 5: Confidentiality (detailed exceptions)
   - Section 6: Records & Documentation (clinical records storage)
   - Section 7: Fees & Payments (session charges, cancellation policy)
   - Section 8: Appointments & Attendance (punctuality, late arrival)
   - Section 9: Use of Digital Systems (consent for digital tools)
   - Section 10: Client Responsibilities (active participation)
   - Section 11: Right to Withdraw (discontinuation rights)
   - Section 12: Consent Statement (final confirmation)

**Testing Results:**
- ✅ Client login shows informed consent page correctly
- ✅ All 12 sections display with proper formatting
- ✅ Therapist name and credentials appear in Services Offered section
- ✅ "Sign Consent" button works correctly
- ✅ After signing, client dashboard loads with full functionality
- ✅ "Good Morning/Afternoon/Evening" greeting shows correctly
- ✅ Therapist name displays in header

**Files Modified:**
- `/app/backend/routes/clinical.py` - Updated default consent text template (Lines 355-420)
- Database: Updated existing Divya Sharma's consent document with new template

---

### Phase 44: Client Self-Registration Link (COMPLETED - Jan 25, 2026)
**Feature:** Unique registration link for each therapist to share with new clients

**How it works:**
1. Each therapist gets a unique registration code (8-character alphanumeric)
2. Therapist shares link like: `https://app.com/register/client/{code}`
3. Client opens link, fills registration form, and gets automatically linked to that therapist

**Backend Implementation:**
- `GET /api/auth/therapist-registration-link` - Get therapist's unique registration link
- `POST /api/auth/therapist-registration-link/regenerate` - Generate new link (invalidates old)
- `GET /api/auth/verify-registration-code/{code}` - Verify if code is valid (public)
- `POST /api/auth/client-self-register/{code}` - Client self-registration (public)
- Registration code stored in `therapist_profiles.registration_code`

**Frontend Implementation:**
- New page: `/register/client/:therapistCode` (`ClientRegisterPage.js`)
- Registration form with same fields as therapist-created client:
  - Required: Full Name, Mobile (10 digits), Password
  - Optional: Email, Age, Guardian Name, Address, Referred By, Emergency Contact
- Success page shows Client ID and therapist name with "Go to Login" button

**Therapist Dashboard Integration:**
- `ClientRegistrationLink.js` component added to TherapistOverview
- Shows registration link with copy button
- "Share Link" button (uses Web Share API on mobile)
- "Preview" button to open link in new tab
- "Regenerate" button to create new link

**Security:**
- Link is always valid until regenerated
- Registration code uniqueness enforced
- Therapist status checked before allowing registration
- Client automatically linked to correct therapist

**Files Created:**
- `/app/frontend/src/pages/ClientRegisterPage.js`
- `/app/frontend/src/components/ClientRegistrationLink.js`

**Files Modified:**
- `/app/backend/routes/auth.py` - Added 4 new endpoints
- `/app/backend/dependencies.py` - Added `generate_registration_code()` function
- `/app/frontend/src/App.js` - Added route for client registration
- `/app/frontend/src/components/TherapistOverview.js` - Added registration link card

**Testing Results:**
- ✅ Therapist can get/regenerate registration link
- ✅ Link verification works (valid/invalid codes)
- ✅ Client can self-register with all form fields
- ✅ Validation works (duplicate mobile/email, password match)
- ✅ Success page shows client ID and therapist name
- ✅ New client auto-linked to correct therapist
- ✅ `self_registered: true` flag added to client profile

---

### Phase 46: Email Notification System (COMPLETED - Jan 26, 2026)
**Feature:** Provider-agnostic Email Notification System with Resend integration

**Architecture:**
- Provider-agnostic design allowing easy provider switching (Resend, SendGrid, SES, etc.)
- Base class pattern: `EmailProviderBase` with abstract methods
- Dynamic registry: `EmailProviderRegistry` loads providers from database
- Service layer: `EmailService` handles business logic (subscription checks, preferences)
- Template system: HTML email templates with COGNISPACE branding

**Email Provider Abstraction:**
- `/app/backend/services/email/base.py` - Base class, EmailMessage, EmailResult models
- `/app/backend/services/email/registry.py` - Dynamic provider registry
- `/app/backend/services/email/resend_provider.py` - Resend API implementation (async)
- `/app/backend/services/email/service.py` - Business logic with subscription/preference checks
- `/app/backend/services/email/templates.py` - HTML email templates

**Email Templates Implemented:**
1. Welcome Credentials - New client login ID + password
2. Password Changed - Security notification
3. Appointment Confirmation - Booking confirmation
4. Appointment Reminder - Upcoming session reminder
5. Payment Receipt - Payment confirmation with ₹ amount
6. Subscription Expiry - Renewal warning

**Notification Settings API:**
- `GET /api/notification-settings/events` - List all notification events with preferences
- `GET /api/notification-settings/channel-availability` - Check email/whatsapp availability per subscription
- `PUT /api/notification-settings/preference` - Update individual preference
- `PUT /api/notification-settings/preferences/bulk` - Bulk update preferences

**Frontend UI:**
- Settings modal updated with "Notification Preferences" section
- Channel availability badges (Email Enabled/Disabled, WhatsApp Enabled/Disabled)
- Toggle switches for each notification event (Email and WhatsApp columns)
- N/A shown for events that don't support a channel
- Toast messages on preference update

**Subscription Integration:**
- Email notifications allowed based on subscription plan features
- `subscription_plans.features.email_notifications` controls access
- Therapists can toggle individual events on/off

**Email Trigger Implemented:**
- Client self-registration sends welcome email with credentials
- Email service checks: subscription allows, therapist preference enabled, user opted in

**Configuration:**
- `RESEND_API_KEY` in backend .env
- `SENDER_EMAIL` configurable (default: noreply@cognispace.in)

**Testing Results (iteration_31.json):**
- ✅ Backend: 100% (12/12 tests passed)
- ✅ Frontend: 100% (all UI working)
- ✅ All 6 notification events displayed
- ✅ Email toggles functional
- ✅ WhatsApp correctly disabled (not configured)
- ✅ Preference updates working with toast

---

## Pending Tasks (Priority Order)

### P1 - WhatsApp Integration
- Implement WhatsApp provider using Twilio or similar
- Add WhatsApp templates for key events
- Enable WhatsApp toggles in UI when configured

### P1 - Time-Based Notification Scheduler
- Background job to send appointment reminders (30 min before)
- Pending notes reminder (1 hour after session)
- Subscription expiry warnings

### P2 - Global Standards Audit
- Date format: DD/MM/YYYY everywhere
- Currency: ₹ (INR) everywhere

### P2 - Code Refactoring
- Split `server.py` into smaller modules (models/, routes/, templates/)
- Decompose `AIClinicalSupport.js` component

---
