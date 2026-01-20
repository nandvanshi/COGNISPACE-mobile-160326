# TheraGenie - Product Requirements Document

## Original Problem Statement
Build a secure, therapist-first web application for managing a therapy practice and supporting clinical decision-making.

**App Name**: TheraGenie
**Tagline**: Clinical intelligence for modern therapists

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
- **Test Therapist**: mobile: `9999999999`, password: `password123`
- **Test Assistant**: email: `assistant1@test.com`, password: `assist123`

---

## Backlog

### P1 - High Priority
- [ ] Refactor `server.py` into modular structure (routes, models, services)
- [ ] Global Standards Verification (IST timezone, DD/MM/YYYY dates, ₹ currency across app)
- [ ] Coupon Code management validation and testing

### P2 - Medium Priority  
- [x] ~~Assessment result visualization~~ (DONE - Phase 26)
- [ ] Profile photo upload (currently URL-based)
- [ ] AI-powered SOAP/DAP note generation from session transcripts
- [ ] Case History download/print functionality

### P3 - Future Enhancements
- [x] ~~Clinical Support: Assessment suggestion engine~~ (DONE - Phase 18)
- [x] ~~Clinical Support: Therapy protocol builder~~ (DONE - Phase 18)
- [ ] Template sharing between therapists
- [x] ~~Homework completion tracking~~ (DONE - Phase 18 Resource Library)
- [ ] Audit log viewer for admins
- [ ] Email notifications for approvals
- [ ] AI usage tracking/rate limiting
- [ ] Assessment trends and progress tracking over time

---

## Refactoring Needs
- Split `server.py` into modular structure (routes, models, services)
- Add database migration strategy for schema changes
- Add comprehensive error handling
