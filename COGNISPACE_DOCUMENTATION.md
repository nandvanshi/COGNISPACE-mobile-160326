# COGNISPACE - Complete Application Documentation
### Master Reference Document
**Last Updated:** May 15, 2026

---

## 1. APP OVERVIEW

### App Name: **COGNISPACE**
### Purpose:
COGNISPACE is a secure, therapist-first web application for **practice management and clinical decision support**. It helps mental health professionals (psychologists, counselors, therapists) manage their entire practice digitally - from client intake to session documentation, billing, AI-powered clinical tools, and automated follow-ups.

### Who Is It Designed For?
| Role | Description |
|------|-------------|
| **Therapist** | Primary user - manages clients, appointments, sessions, payments, clinical tools |
| **Client (Patient)** | Books appointments, fills assessments, views homework/resources, communicates with therapist |
| **Assistant (Receptionist)** | Handles front-desk operations - check-ins, payment collection, call reminders, cash settlements |
| **Super Admin** | Platform administrator - manages therapists, subscription plans, content library, system config |

### Tech Stack:
| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Shadcn/UI Components + Tailwind CSS |
| **Backend** | FastAPI (Python) |
| **Database** | MongoDB (Atlas Cloud / Local) |
| **AI Engine** | Anthropic Claude (via Emergent LLM Key + emergentintegrations) |
| **Email** | Resend API |
| **WhatsApp** | Twilio API |
| **PDF** | Browser iframe-based print |
| **PWA** | Progressive Web App with notification badges & sounds |
| **Scheduling** | APScheduler (background cron jobs) |

---

## 2. ALL FEATURES LIST

### A. Authentication & User Management
| Feature | What It Does | Location |
|---------|-------------|----------|
| Therapist Login | Login via mobile number + password | `/login` |
| Client Login | Login via mobile number + password | `/login` |
| Super Admin Login | Login via username + password | `/admin-login` |
| Assistant Login | Login via mobile + password | `/login` |
| Therapist Application | New therapists apply with qualifications, experience, clinic details | `/therapist-application` |
| Application Approval | Admin approves/rejects therapist applications | Admin > Therapist Applications |
| Client Self-Registration | Clients register via therapist's unique link | `/register/client/:code` |
| Forgot/Reset Password | Email-based password reset with token verification | `/forgot-password` |
| JWT Token Authentication | Secure API access with role-based token | All protected routes |

### B. Client Management
| Feature | What It Does | Location |
|---------|-------------|----------|
| Add Client | Therapist creates new client with demographics | Therapist > Clients > Add |
| Client Profile | Full profile with age, guardian, emergency contact, address, referral | Therapist > Clients > Profile |
| Client List | Searchable, filterable list of all clients | Therapist > Clients |
| Case History Form | Detailed clinical intake form with multiple sections | Client Profile > Case History |
| Therapy Consent | Digital consent form with signature capture | Client Profile > Consent |
| Client Registration Link | Auto-generated unique URL for client self-registration | Therapist > Settings |
| New Registration Alerts | Badge notification when new clients self-register | Therapist > Clients |
| Client Profile Photo | Profile picture upload/display | Client Profile |
| Orphaned Client Management | Admin can link unassigned clients to therapists | Admin > Client Management |

### C. Appointments & Scheduling
| Feature | What It Does | Location |
|---------|-------------|----------|
| Create Appointment | Book appointment for a client with date/time slot | Therapist > Schedule |
| Available Slots | Auto-generated time slots based on therapist availability settings | Slot picker in booking |
| Availability Settings | Set working hours per day of week, session duration, buffer time | Therapist > Availability |
| Blocked Time | Block specific dates/times (holidays, personal time) | Therapist > Availability |
| Calendar View | Month/week calendar showing all appointments | Therapist > Schedule |
| Appointment Status | Track: pending, scheduled, completed, cancelled, declined, no-show | Schedule view |
| Check-In/Check-Out | Record actual session start and end times | Schedule > Appointment card |
| Mark Completed | Mark session as done (auto or manual) | Appointment actions |
| No-Show | Mark client as no-show | Appointment actions |
| Recurring Appointments | Create weekly/biweekly/monthly recurring patterns | Therapist > Recurring |
| Client Appointment Request | Clients can request appointments (therapist approves/declines) | Client Dashboard |
| Approve/Decline | Therapist approves or declines client-requested appointments | Schedule > Pending |
| Public Booking Page | Shareable URL for clients to book appointments | `/book/:therapistSlug` |
| Booking Link Management | Enable/disable public booking, set slug URL | Therapist > Profile |
| Appointment Reminders | WhatsApp reminders for upcoming appointments (via Twilio) | Automated |
| Morning Schedule Briefing | Daily email at 7 AM IST with day's appointments summary | Automated |

### D. Session & Therapy Management
| Feature | What It Does | Location |
|---------|-------------|----------|
| Session Notes | Create/edit clinical session notes per appointment | Therapist > Session Notes |
| Voice Input | Native Web Speech API for dictating notes | Session Notes textarea |
| Protocol Templates | Create therapy protocol plans (modality, condition, sessions) | Therapist > Protocols |
| Assessments | Assign standardized assessments (PHQ-9, GAD-7, etc.) to clients | Therapist > Assessments |
| Assessment Library | 35+ built-in validated assessments + custom assessments | Assessments > Library |
| Client Assessment Taking | Clients fill assessments on their dashboard | Client Dashboard > Tasks |
| Assessment Scoring | Auto-scoring with severity interpretation | Assessment results |
| Assessment Report Sharing | Share/unshare assessment reports with clients | Assessment actions |
| Homework Assignment | Assign homework tasks to clients with due dates | Client Profile > Homework |
| Homework Templates | Reusable homework templates library | Therapist > Homework Templates |
| Resource Library | Create & share educational resources/handouts | Therapist > Resource Library |
| Resource Assignment | Assign specific resources to clients | Client Profile > Resources |
| Diagnostic Reports | AI-generated diagnostic reports from assessments | Client Profile > Reports |
| Therapy Consent | Digital therapy consent form with e-signature | Client Profile > Consent |
| Client Journey Timeline | Complete chronological history: sessions, assessments, recommendations | Client Profile > Journey |

### E. AI Clinical Intelligence (TheraGenie)
| Feature | What It Does | Location |
|---------|-------------|----------|
| AI Assessment Suggestions | AI recommends assessments based on client presentation | TheraGenie > Suggest Assessments |
| AI Protocol Generation | AI generates therapy protocol based on diagnosis & modality | TheraGenie > Generate Protocol |
| AI Homework Generation | AI creates personalized homework assignments | TheraGenie > Generate Homework |
| AI Diagnostic Report | AI generates comprehensive diagnostic report from assessment data | TheraGenie > Diagnostic Report |
| AI Content Generation | Admin generates content (homework, protocols, resources) via AI | Admin > Content Library > AI Generate |
| AI Email Drafting | AI drafts broadcast emails for admin | Admin > Email Broadcast > AI Draft |
| CogniVision | AI-powered clinical decision support engine | Part of TheraGenie |

### F. Payments & Billing
| Feature | What It Does | Location |
|---------|-------------|----------|
| Record Payment | Log payment (cash/UPI/card/bank transfer) with amount | Therapist > Payments |
| Credit/Debit System | Support for both credit (received) and debit (refund/expense) entries | Payment form |
| Auto Bill Number | Sequential bill numbers per therapist | Auto-generated |
| Payment Receipt | Printable PDF receipt with therapist clinic details | Payment > Receipt icon |
| Payment Status | Track: pending, received, partially_paid | Payment list |
| Session-Linked Payment | Auto-create payment entry on session checkout | Session checkout flow |
| Payment Reports Dashboard | Summary stats, monthly trends, client-wise breakdown | Therapist > Reports |
| Daily Payment Summary Email | Automated daily email with payment summary | Automated at 8 PM IST |
| Cash Settlement Flow | Assistant collects cash, creates settlement, therapist confirms | Assistant > Settlements |
| Export Reports | Export payment data to CSV | Reports > Export |

### G. Follow-Up Intelligence System
| Feature | What It Does | Location |
|---------|-------------|----------|
| Recommend Next Session | At checkout, recommend next session date | Session checkout dialog |
| Follow-Up Dashboard | Summary of booked, recommended, overdue, dropout risk clients | Therapist > Follow-Ups |
| Client Follow-Up List | Filterable list of clients by follow-up status | Follow-Up Dashboard |
| Retention Analytics | Session counts, avg gaps, days since last visit, global averages | Follow-Up Dashboard > Analytics |
| Client Self-View | Clients see their follow-up recommendation on their dashboard | Client Dashboard |
| Automated Email Reminders | 4 templates: 2-day before, same day, 1-week missed, 30-day re-engagement | Automated scheduler |
| Reminder Settings | Therapist toggles email/WhatsApp reminders on/off | Settings > Follow-up Reminders |
| Reminder Log | System tracks all sent reminders with timestamps | Internal logging |

### H. Messaging
| Feature | What It Does | Location |
|---------|-------------|----------|
| In-App Messaging | Messenger-style chat between therapist and client | Therapist > Messages |
| Contact List | All clients with last message preview & unread count | Messages sidebar |
| Real-Time Messages | Polling-based message refresh | Messages view |
| Soft Delete | Users can delete messages for themselves only | Message actions |
| Unread Count Badge | Badge showing unread message count | Sidebar + Notification bell |

### I. Notifications
| Feature | What It Does | Location |
|---------|-------------|----------|
| In-App Notifications | Bell icon with dropdown showing all notifications | Top navigation bar |
| Notification Types | Appointment, payment, message, follow-up, system alerts | Notification dropdown |
| Mark Read/Unread | Mark individual or all notifications as read | Notification actions |
| Clear All | Delete all notifications at once | Notification dropdown |
| PWA Badge | App icon badge count on mobile/desktop | PWA feature |
| Notification Sound | Audio alert for new notifications | PWA feature |
| Email Notifications | Transactional emails (appointment confirm, payment receipt, etc.) | Automated via Resend |
| WhatsApp Notifications | WhatsApp messages for reminders and alerts | Automated via Twilio |
| Notification Preferences | Per-event toggle for WhatsApp notifications | Therapist > Settings |

### J. Assistant (Receptionist) Features
| Feature | What It Does | Location |
|---------|-------------|----------|
| Assistant Dashboard | Overview with today's appointments, stats, urgent items | Assistant > Dashboard |
| Client Check-In | Mark clients as checked in for their appointment | Assistant > Schedule |
| Call Reminder | Log phone call reminders to clients | Assistant > Actions |
| Cash Collection | Record cash payments from clients | Assistant > Payments |
| Cash Settlement | Create cash handover settlement to therapist | Assistant > Settlements |
| Settlement Confirmation | Therapist confirms/disputes cash settlements | Therapist > Settlements |
| Follow-Up View | View follow-up stats and urgent client list | Assistant > Follow-Ups |

### K. Super Admin Features
| Feature | What It Does | Location |
|---------|-------------|----------|
| Admin Dashboard | Overview stats: therapists, clients, revenue, tickets | Admin > Dashboard |
| Therapist Applications | View, approve, reject new therapist applications | Admin > Applications |
| Therapist Management | Edit, suspend, activate, delete, reset password for therapists | Admin > Therapists |
| Client Management | View all clients, link orphaned clients to therapists | Admin > Clients |
| Subscription Plans | Create/edit/delete subscription plans with feature toggles | Admin > Subscriptions |
| Assign Subscription | Assign/extend plans to therapists | Admin > Therapist detail |
| Coupon Codes | Create/manage discount coupons | Admin > Coupons |
| Content Library | Create global homework, protocols, resources, assessments, note templates | Admin > Content Library |
| AI Content Generation | Use AI to generate content for the library | Content Library > AI Generate |
| Email Broadcast | Send mass emails to therapists/clients with AI drafting | Admin > Email Broadcast |
| Support Tickets | View & respond to therapist support tickets | Admin > Support |
| All Users View | See all registered users with role filters, search, pagination | Admin > All Users |
| System Config | View all backend .env variables (secrets) with reveal/copy | Admin > System Config |
| Update Log | Timeline of all code updates with timestamps | Admin > Update Log |
| Build Timestamp | Auto-updated server start timestamp in sidebar | Admin sidebar footer |
| Timezone Migration Tool | Fix old appointment timezone issues (dry-run + apply) | Admin > Dashboard card |

### L. Mobile & PWA
| Feature | What It Does | Location |
|---------|-------------|----------|
| Mobile-First Therapist View | Bottom navigation UI for mobile (Home, Clients, Schedule, Payments, More) | Auto-detects < 1024px |
| PWA Install | "Install App" prompt for adding to home screen | Settings |
| Notification Badge | App icon shows unread count | Mobile/Desktop |
| Notification Sound | Audio chime on new notifications | Mobile/Desktop |

### M. Public Pages
| Feature | What It Does | Location |
|---------|-------------|----------|
| Public Booking Page | Anyone can book appointment with therapist via slug URL | `/book/:slug` |
| About Page | Information about the platform | `/about` |
| Privacy Policy | GDPR/legal privacy policy | `/privacy-policy` |
| Terms & Conditions | Legal terms of use | `/terms-conditions` |
| Clinical Disclaimer | Clinical services disclaimer | `/clinical-disclaimer` |
| Refund Policy | Payment refund terms | `/refund-policy` |
| Contact Support | Support contact page | `/contact` |

---

## 3. ALL PAGES & SCREENS

### Public Routes (No Login Required)
| Page | URL | Description |
|------|-----|-------------|
| Login | `/login` | Therapist, Client, Assistant login with mobile + password |
| Admin Login | `/admin-login` | Super Admin login with username + password |
| Therapist Application | `/therapist-application` | New therapist application form |
| Client Registration | `/register/client/:code` | Client self-registration via therapist's unique link |
| Public Booking | `/book/:slug` or `/booking/:therapistId` | Public appointment booking page |
| Forgot Password | `/forgot-password` | Password reset request |
| Reset Password | `/reset-password` | Password reset form with token |
| Privacy Policy | `/privacy-policy` | Legal privacy policy |
| Terms & Conditions | `/terms-conditions` | Legal terms |
| Clinical Disclaimer | `/clinical-disclaimer` | Clinical disclaimer |
| Refund Policy | `/refund-policy` | Refund policy |
| Contact Support | `/contact` | Support contact |
| About | `/about` | About the platform |

### Therapist Dashboard (`/therapist/*`)
| View | Sidebar Item | Description |
|------|-------------|-------------|
| Dashboard (Overview) | Dashboard | Today's stats, upcoming appointments, follow-up alerts, subscription info |
| Clients | Clients | Client list, add new client, search/filter |
| Client Profile | Clients > [Click client] | Full client page with tabs: Overview, Appointments, Notes, Assessments, Homework, Resources, Protocols, Journey, Consent, Case History |
| Schedule | Schedule | Calendar with month/week view, book appointment, manage bookings |
| Session Notes | Session Notes | Create/edit session notes, voice input, link to appointments |
| Assessments | Assessments | Assign assessments, view results, assessment library |
| Protocols | Protocols | Create/manage therapy protocols from templates |
| Messages | Messages | Chat with clients (messenger-style) |
| TheraGenie | TheraGenie | AI tools: assessment suggestions, protocol generation, homework generation, diagnostic reports |
| Follow-Ups | Follow-Ups | Follow-up dashboard with stats, client list, retention analytics |
| Availability | Availability | Set weekly working hours, session duration, blocked times |
| Recurring | Recurring | Create recurring appointment patterns |
| Payments | Payments | Record/view payments, generate receipts |
| Reports | Reports | Payment analytics: summary, monthly trend, client-wise, daily, export |
| Assistants | Assistants | Manage front-desk assistants |
| My Profile | My Profile | Edit personal, clinic details, public booking settings, receipt info |
| Subscription | Subscription Info | View current plan, feature access, expiry |
| Support | Support | Create/track support tickets |
| Settings | Settings (modal) | Notification preferences, follow-up reminders, theme, PWA install |

### Client Dashboard (`/client/*`)
| Tab | Description |
|-----|-------------|
| Home | Welcome card, upcoming appointments, follow-up reminders, pending tasks |
| Appointments | View all appointments (upcoming, past), request new appointment |
| Tasks | Pending assessments, homework assignments, shared resources |
| Messages | Chat with therapist |
| Profile | Personal details, assessment history |

### Assistant Dashboard (`/assistant/*`)
| View | Description |
|------|-------------|
| Overview | Today's stats, appointments, pending settlements, follow-up alerts |
| Clients | View therapist's client list |
| Schedule | Today's appointments, check-in/check-out actions |
| Payments | Record payments, manage cash settlements |
| Follow-Ups | View follow-up stats for therapist's clients |

### Super Admin Dashboard (`/admin/*`)
| View | Sidebar Item | Description |
|------|-------------|-------------|
| Dashboard | Dashboard | Platform stats, therapist/client counts, revenue overview |
| Therapist Applications | Therapist Applications | Approve/reject new therapist applications |
| Therapist Management | Therapist Management | Full CRUD: edit, suspend, activate, reset password, assign plans |
| Client Management | Client Management | View all clients, link orphaned clients |
| Subscription Plans | Subscription Plans | Create/edit/delete plans with feature toggles |
| Coupon Codes | Coupon Codes | Create/manage discount coupons |
| Support Tickets | Support Tickets | View/respond to therapist tickets |
| Content Library | Content Library | Create global content (5 types) + AI generation |
| Email Broadcast | Email Broadcast | Mass email with recipient filters + AI drafting |
| All Users | All Users | View all users with role filters, search, pagination, copy |
| System Config | System Config | View all backend .env secrets with reveal/copy |
| Update Log | Update Log | Timeline of code updates with timestamps |
| Settings | Settings (modal) | Admin preferences |

---

## 4. DATABASE STRUCTURE

### Collections & Fields

#### `users` - All user accounts
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| mobile | string | Mobile number (login identifier) |
| email | string | Email address |
| full_name | string | Full name |
| password_hash | string | bcrypt hashed password |
| role | string | `therapist`, `client`, `assistant`, `super_admin` |
| status | string | `active`, `approved`, `suspended`, `pending` |
| qualifications | string | Professional qualifications (therapist) |
| specializations | array | List of specializations (therapist) |
| years_of_experience | number | Years of practice (therapist) |
| clinic_name | string | Clinic/practice name |
| address, pincode, city, state, district | string | Location details |
| google_maps_link | string | Clinic Google Maps URL |
| subscription_status | string | `active`, `expired`, `trial` |
| subscription_plan | string | Current plan name |
| profile_photo | string | Photo URL |
| created_at | string (ISO) | Registration timestamp |

#### `appointments` - All appointments
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| therapist_id | string | Therapist user ID |
| client_id | string | Client user ID |
| client_name | string | Client display name |
| start_time | string (ISO) | Scheduled start (UTC) |
| end_time | string (ISO) | Scheduled end (UTC) |
| status | string | `pending`, `scheduled`, `completed`, `cancelled`, `declined`, `no_show` |
| actual_start_time | string (ISO) | Check-in time |
| actual_end_time | string (ISO) | Check-out time |
| actual_duration_minutes | number | Real session duration |
| checked_in_by | string | Who checked in (therapist/assistant ID) |
| notes | string | Appointment notes |
| confirmation_email_sent | boolean | Email sent flag |
| created_at | string (ISO) | Creation timestamp |

#### `payments` - Payment records
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| bill_number | string | Sequential bill number (e.g., BILL-001) |
| therapist_id | string | Therapist user ID |
| client_id | string | Client user ID |
| client_name, client_code | string | Client display info |
| amount | number | Payment amount (positive=credit, negative=debit) |
| payment_method | string | `cash`, `upi`, `card`, `bank_transfer`, `other` |
| payment_status | string | `pending`, `received`, `partially_paid` |
| appointment_id | string | Linked appointment (optional) |
| session_note_id | string | Linked session note (optional) |
| notes | string | Payment notes |
| created_at | string (ISO) | Payment date |

#### `session_notes` - Clinical session notes
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| therapist_id | string | Author therapist ID |
| client_id | string | Client user ID |
| appointment_id | string | Linked appointment |
| content | string | Note content (rich text) |
| session_type | string | Session type |
| mood | string | Client mood assessment |
| progress | string | Progress notes |
| plan | string | Next session plan |
| created_at, updated_at | string (ISO) | Timestamps |

#### `client_profiles` - Extended client info
| Field | Type | Description |
|-------|------|-------------|
| user_id | string | Client user ID (FK to users) |
| therapist_id | string | Linked therapist ID |
| age | number | Client age |
| guardian_name | string | Guardian/parent name |
| address | string | Client address |
| referred_by | string | Referral source |
| intake_summary | string | Initial intake notes |
| emergency_contact_name, phone | string | Emergency contact |
| profile_photo | string | Photo URL |

#### `case_histories` - Clinical case history forms
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| client_id | string | Client user ID |
| therapist_id | string | Therapist who created |
| sections | object | Multi-section form data (family history, medical, presenting concerns, etc.) |
| is_complete | boolean | Completion status |
| created_at, updated_at | string (ISO) | Timestamps |

#### `therapy_consents` - Signed consent forms
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| client_id | string | Client user ID |
| therapist_id | string | Therapist user ID |
| consent_text | string | Full consent text |
| is_signed | boolean | Whether signed |
| signature_date | string | Date of signature |
| signature_method | string | How signed |
| witnessed_by | string | Witness name |

#### `assessments` - Assigned/completed assessments
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| therapist_id, client_id | string | User references |
| assessment_type | string | Assessment type key (e.g., `phq9`, `gad7`) |
| assessment_name | string | Display name |
| status | string | `assigned`, `in_progress`, `completed` |
| responses | array | Client's answers |
| score | number | Calculated score |
| is_shared | boolean | Shared with client |
| due_date | string | Assignment due date |

#### `protocols` - Therapy protocols
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| therapist_id, client_id | string | User references |
| modality | string | Therapy modality (CBT, DBT, etc.) |
| condition | string | Clinical condition |
| sessions | array | Session-by-session plan |
| is_template | boolean | Template or client-specific |

#### `resources` - Therapist-created resources
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| therapist_id | string | Creator therapist |
| title | string | Resource title |
| category | string | Category |
| content | string | Content body |
| tags | array | Tags for filtering |

#### `resource_assignments` - Resources assigned to clients
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| resource_id | string | Resource reference |
| client_id, therapist_id | string | User references |
| status | string | `assigned`, `viewed`, `completed` |

#### `homework` - Homework assignments
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| therapist_id, client_id | string | User references |
| title, description | string | Homework details |
| due_date | string | Due date |
| priority | string | `low`, `medium`, `high` |
| status | string | `assigned`, `completed` |

#### `messages` - In-app messages
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| sender_id, recipient_id | string | User references |
| content | string | Message body |
| is_read | boolean | Read status |

#### `notifications` - In-app notifications
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| user_id | string | Target user |
| type | string | Notification type |
| title, message | string | Notification content |
| link | string | Navigation link |
| is_read | boolean | Read status |

#### `follow_up_recommendations` - Session follow-up tracking
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| client_id, therapist_id | string | User references |
| recommended_date | string | Suggested next visit date |
| status | string | `active`, `booked`, `completed` |

#### `therapist_availability` - Weekly schedule settings
| Field | Type | Description |
|-------|------|-------------|
| therapist_id | string | Therapist reference |
| session_duration | number | Minutes per session |
| buffer_time | number | Minutes between sessions |
| monday-sunday | object | Each day: `{ enabled, start, end }` |

#### `therapist_profiles` - Extended therapist settings
| Field | Type | Description |
|-------|------|-------------|
| therapist_id | string | User reference |
| registration_code | string | Unique client registration code |
| public_booking_enabled | boolean | Public booking toggle |
| public_booking_slug | string | Custom booking URL slug |
| fee_slots | array | Fee structure |
| receipt display settings | various | What to show on payment receipts |

#### `subscription_plans` - SaaS plans
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| name | string | Plan name (Core, Pro, etc.) |
| price | number | Monthly price |
| duration_days | number | Plan duration |
| features | array | Feature list |
| max_clients | number | Client limit |
| feature_toggles | object | Feature on/off flags |

#### `subscriptions` - Therapist subscriptions
| Field | Type | Description |
|-------|------|-------------|
| therapist_id, plan_id | string | References |
| start_date, end_date | string | Active period |
| status | string | `active`, `expired`, `trial` |

#### `admin_content` - Global content library
| Field | Type | Description |
|-------|------|-------------|
| type | string | `homework_template`, `protocol_template`, `resource`, `assessment`, `note_template` |
| title, description, content | string | Content data |
| tags | array | Tags for categorization |
| source | string | `admin` or `ai_generated` |

#### `therapist_applications` - New therapist applications
#### `audit_logs` - System audit trail
#### `diagnostic_reports` - AI-generated clinical reports
#### `follow_up_reminder_log` - Automated reminder history
#### `notification_preferences` - Per-event notification toggles
#### `password_reset_tokens` - Password reset tokens
#### `email_providers` - Email service configuration
#### `therapist_settings` - Therapist-specific settings (follow-up reminders)

### Key Relationships
```
users (1) ──── (N) appointments
users (1) ──── (N) payments
users (1) ──── (1) client_profiles (for clients)
users (1) ──── (1) therapist_profiles (for therapists)
users (1) ──── (1) therapist_availability (for therapists)
client_profiles.therapist_id ──── users.id (therapist)
appointments ──── session_notes (via appointment_id)
appointments ──── payments (via appointment_id)
assessments.client_id ──── users.id
resources ──── resource_assignments (via resource_id)
subscription_plans ──── subscriptions (via plan_id)
```

---

## 5. USER ROLES & ACCESS

### Role Matrix
| Feature | Super Admin | Therapist | Assistant | Client |
|---------|:-----------:|:---------:|:---------:|:------:|
| Platform management | Full | - | - | - |
| Therapist approval | Full | - | - | - |
| Subscription management | Full | View own | - | - |
| Client CRUD | View all | Own clients | View assigned | Own profile |
| Appointments | View all | Own schedule | Therapist's schedule | Own appointments |
| Session notes | - | Full CRUD | - | - |
| Payments | - | Full CRUD | Record/collect | - |
| AI Tools (TheraGenie) | - | Full access | - | - |
| Assessments | - | Assign/view | - | Fill/submit |
| Messaging | - | With own clients | - | With therapist |
| Follow-ups | - | Full dashboard | View stats | View own |
| Cash settlements | - | Confirm/dispute | Create/handover | - |
| Content library | Create global | View & use | - | - |
| System config | View .env | - | - | - |

### Authentication Flow
1. User enters mobile (or username for admin) + password
2. Backend verifies credentials against bcrypt hash in MongoDB
3. JWT token generated with user_id, role, expiry
4. Token sent to frontend, stored in memory
5. All subsequent API calls include `Authorization: Bearer <token>` header
6. Backend middleware validates token and extracts user context
7. Role-based route guards prevent unauthorized access

---

## 6. WORKFLOWS

### 1. Adding a New Client
```
Therapist logs in → Clients tab → "Add Client" button
→ Fill form: Name, Mobile, Email, Age, Gender, Address, Guardian, Emergency Contact
→ Submit → Client created with auto-generated password
→ Client gets login credentials (mobile + password)
→ Optional: Share self-registration link instead (client fills own details)
```

### 2. Booking an Appointment
```
Therapist → Schedule tab → "Book Appointment" button
→ Select Client from dropdown
→ Select Date → Available time slots shown (based on availability settings)
→ Select slot → Add notes (optional)
→ Confirm → Appointment created with status "scheduled"
→ Email confirmation sent to client (if configured)
→ WhatsApp reminder sent before appointment (automated)
```

**Client-Initiated Booking:**
```
Client visits public booking URL (/book/:slug)
→ Sees therapist info + calendar
→ Selects date & time slot → Fills details
→ Submits request → Status: "pending"
→ Therapist receives notification → Approves/Declines
→ Client notified of decision
```

### 3. Recording a Therapy Session
```
Appointment time arrives → Therapist/Assistant clicks "Check In"
→ Session in progress (actual_start_time recorded)
→ Session ends → Click "Check Out"
→ actual_end_time and duration recorded
→ Popup: "Recommend Next Session?" → Set follow-up date (optional)
→ Popup: "Create Payment?" → Record payment (optional)
→ Appointment status → "completed"
→ Go to Session Notes → Create note with voice input or typing
→ Link note to appointment
```

### 4. Generating a Bill/Invoice
```
Therapist → Payments tab → "Add Payment"
→ Select Client → Enter amount, method (Cash/UPI/Card/Transfer)
→ Select type: Credit (received) or Debit (refund)
→ Link to appointment (optional) → Add notes
→ Save → Bill number auto-generated (BILL-001, BILL-002...)
→ Click receipt icon → Printable PDF with clinic logo, client details, amount
→ PDF opens in print dialog (iframe-based, no popup blocker issues)
```

### 5. Viewing Reports
```
Therapist → Reports tab
→ Summary: Total revenue, pending, received, payment method breakdown
→ Monthly Trend: Line chart showing monthly revenue
→ Client-Wise: Revenue per client with session count
→ Daily Summary: Day-by-day payment log
→ Export: Download complete payment data as CSV
→ Date range filter available on all views
```

### 6. AI Clinical Workflow
```
Therapist → TheraGenie tab → Select client
→ Option 1: "Suggest Assessments" → AI analyzes case history → Recommends assessments
→ Option 2: "Generate Protocol" → Select modality → AI creates full therapy plan
→ Option 3: "Generate Homework" → AI creates personalized homework assignment
→ Option 4: "Generate Report" → AI creates diagnostic report from assessment data
→ All AI outputs can be reviewed, edited, saved, or assigned to client
```

---

## 7. WHAT IS NOT BUILT YET

### Pending / Not Yet Implemented
| Feature | Priority | Status |
|---------|----------|--------|
| Profile Photo Upload (actual upload) | P1 | MOCKED (placeholder, no actual file upload) |
| AI-Powered SOAP/DAP Notes | P1 | Not started |
| Google Calendar Integration | P2 | Not started |
| AI Usage Tracking / Rate Limiting | P2 | Not started |
| Full Coupon Code Redemption Flow | P2 | Backend exists, client-side redemption not built |
| WhatsApp Follow-Up Templates | P2 | Code ready, awaiting Twilio template approval |
| Video Consultation | Future | Not started |
| Multi-Language Support | Future | Not started |
| Analytics Dashboard for Admin | Future | Basic stats only |
| Automated Backup System | Future | Not started |
| Two-Factor Authentication | Future | Not started |

### Known Limitations
1. **Production Deployment Login**: Emergent platform deployed app returns 400 on login (platform-level issue, not code bug)
2. **Real-Time Messaging**: Uses polling, not WebSockets (slight delay in message delivery)
3. **File Uploads**: No actual file/image upload to cloud storage yet (profile photos are placeholder)
4. **Offline Mode**: PWA caches pages but no offline data sync
5. **Multi-Therapist Practice**: Each therapist manages independently; no shared practice/clinic view
6. **Payment Gateway**: No online payment processing (Razorpay/Stripe) - only manual recording

---

## 8. HOW TO USE / GET STARTED

### First-Time Setup Flow
1. **Super Admin** logs in at `/admin-login` (username: `admin`, password: `admin123`)
2. Admin creates **Subscription Plans** (Admin > Subscription Plans)
3. A new **Therapist applies** at `/therapist-application`
4. Admin **approves** the application (Admin > Therapist Applications)
5. Therapist **logs in** at `/login` with mobile number + password
6. Therapist sets **Availability** (working hours, session duration)
7. Therapist **adds Clients** (manually or via self-registration link)
8. Therapist **books Appointments**, records sessions, manages practice

### Default Login Credentials
| Role | Identifier | Password | Login Page |
|------|-----------|----------|------------|
| **Super Admin** | `admin` | `admin123` | `/admin-login` |
| **Therapist** | `7275005007` | `Test@123` | `/login` |
| **Client** | `9235555549` | `Test@123` | `/login` |

### Sample Data
The application has sample data including:
- 1 Therapist (Dr. Deepak Nandvanshi)
- Multiple test clients
- Sample appointments, payments, assessments, session notes
- Follow-up recommendations

### Quick Start Checklist
- [ ] Login as Super Admin → Create at least one Subscription Plan
- [ ] Login as Therapist → Set Availability (Availability tab)
- [ ] Add a Client (Clients tab > Add Client)
- [ ] Book an Appointment (Schedule tab > Book)
- [ ] Check In/Out the session
- [ ] Create a Session Note
- [ ] Record a Payment
- [ ] Try TheraGenie AI (TheraGenie tab)
- [ ] Check Follow-Up Dashboard
- [ ] Explore Payment Reports

### Environment Variables Required
| Variable | Purpose |
|----------|---------|
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | Database name |
| `JWT_SECRET` | JWT token signing key |
| `SUPER_ADMIN_USERNAME` | Admin login username |
| `SUPER_ADMIN_PASSWORD` | Admin login password |
| `FRONTEND_URL` | Frontend domain URL |
| `CORS_ORIGINS` | Allowed CORS origins |
| `EMERGENT_LLM_KEY` | AI features (Claude) API key |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `RESEND_API_KEY` | Email service key |
| `SENDER_EMAIL` | From email address |
| `TWILIO_ACCOUNT_SID` | Twilio account ID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | WhatsApp sender number |

---

## APPENDIX: Automated Background Jobs

| Job | Schedule | What It Does |
|-----|----------|-------------|
| Morning Schedule Briefing | 7:00 AM IST daily | Emails today's appointments to therapist |
| Daily Payment Summary | 8:00 PM IST daily | Emails day's payment summary |
| Appointment Reminders | Every 30 min | WhatsApp reminders for upcoming appointments |
| Pending Session Notes Check | 9:00 PM IST daily | Reminds therapist of incomplete notes |
| Follow-Up Reminders | Every 30 min | Email reminders for recommended follow-up dates |
| Subscription Expiry Check | 6:00 AM IST daily | Alerts for expiring subscriptions |

---

*This document is the complete master reference for COGNISPACE. For code-level details, refer to `/app/memory/PRD.md`.*
