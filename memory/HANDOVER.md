# COGNISPACE - Complete System Handover Document
**Last Updated**: January 26, 2026

---

## 🏗️ 1. System Architecture Overview

### Tech Stack
| Component | Technology | Details |
|-----------|------------|---------|
| **Frontend** | React 18 + Tailwind CSS | Shadcn/UI components, Sonner toasts |
| **Backend** | FastAPI (Python) | Async with Motor (MongoDB driver) |
| **Database** | MongoDB | Collections for all entities |
| **AI** | Claude Sonnet 4 | Via Emergent LLM Key |
| **Email** | Resend | HTML templates |
| **WhatsApp** | Twilio | Template-based messages |
| **Scheduler** | APScheduler | Background jobs for reminders |
| **PDF** | jsPDF + html2canvas | Frontend-side generation |

### Service Ports
- **Frontend**: Port 3000 (auto-hot-reload)
- **Backend**: Port 8001 (auto-hot-reload via supervisor)
- **All API routes**: Prefixed with `/api`

---

## 📁 2. Directory Structure

```
/app/
├── backend/
│   ├── server.py              # Main FastAPI app (~1300 lines)
│   ├── database.py            # MongoDB connection
│   ├── dependencies.py        # Auth dependencies
│   ├── routes/                # API route modules
│   │   ├── admin.py           # Super admin operations
│   │   ├── ai_clinical.py     # TheraGenie AI features
│   │   ├── appointments.py    # Scheduling
│   │   ├── assessments.py     # Assessment management
│   │   ├── assistant.py       # Assistant role APIs
│   │   ├── auth.py            # Login/register
│   │   ├── availability.py    # Therapist availability
│   │   ├── clients.py         # Client management
│   │   ├── diagnostic_reports.py  # CogniVision reports
│   │   ├── notification_settings.py
│   │   ├── notifications.py   # In-app notifications
│   │   ├── payments.py        # Payment tracking + reports
│   │   ├── protocols.py       # Treatment protocols
│   │   ├── resources.py       # Resource library
│   │   ├── sessions.py        # Session notes
│   │   ├── subscriptions.py   # Subscription management
│   │   └── therapist_profile.py  # Therapist profile + photo
│   ├── services/
│   │   ├── email/             # Email service (Resend)
│   │   ├── whatsapp/          # WhatsApp service (Twilio)
│   │   └── scheduler/         # APScheduler jobs
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── App.js             # Main app + routing
│       ├── pages/             # Page components
│       │   └── AboutPage.js   # NEW - Public about page
│       └── components/
│           ├── ui/            # Shadcn components
│           ├── AIClinicalSupport.js  # Re-exports from ai-clinical/
│           └── ai-clinical/   # NEW - Modular AI components
│               ├── index.js           # Main wrapper
│               ├── AssessmentsTab.js
│               ├── DiagnosticTab.js
│               ├── ProtocolsTab.js
│               ├── HomeworkTab.js
│               ├── ResourcesTab.js
│               ├── hooks/useAIClinical.js
│               └── dialogs/           # 5 dialog components
│
└── memory/
    ├── PRD.md                 # Product requirements (static)
    ├── CHANGELOG.md           # Implementation history
    ├── ROADMAP.md             # Priorities & backlog
    └── HANDOVER.md            # This document
```

---

## ✅ 3. Feature Status

### 🟢 COMPLETED Features

| Feature | Backend | Frontend | Notes |
|---------|---------|----------|-------|
| **Authentication** | ✅ | ✅ | JWT-based, 4 roles |
| **Therapist Dashboard** | ✅ | ✅ | Full CRUD |
| **Client Dashboard** | ✅ | ✅ | View appointments, reports |
| **Assistant Dashboard** | ✅ | ✅ | Limited access |
| **Super Admin Dashboard** | ✅ | ✅ | Full control |
| **Client Management** | ✅ | ✅ | Create, edit, archive |
| **Client Self-Registration** | ✅ | ✅ | Via therapist unique link |
| **Appointments** | ✅ | ✅ | Create, reschedule, cancel |
| **Recurring Appointments** | ✅ | ✅ | Weekly/biweekly patterns |
| **Session Notes (SOAP)** | ✅ | ✅ | Create, edit, PDF export |
| **Assessments** | ✅ | ✅ | Administer, score |
| **Payment Tracking** | ✅ | ✅ | Record, receipts, history |
| **Payment Reports** | ✅ | ✅ | Analytics dashboard |
| **TheraGenie AI** | ✅ | ✅ | Assessment suggestions, protocols, homework |
| **CogniVision Reports** | ✅ | ✅ | AI diagnostic reports, PDF export |
| **In-App Notifications** | ✅ | ✅ | Bell icon, dropdown |
| **Email Notifications** | ✅ | ✅ | Via Resend |
| **WhatsApp Notifications** | ✅ | ✅ | Via Twilio (opt-in required) |
| **Scheduler (Reminders)** | ✅ | - | 60/30 min appointment reminders |
| **Subscription Management** | ✅ | ✅ | Plans, expiry tracking |
| **Therapist Profile + Photo** | ✅ | ✅ | Upload & display |
| **Resource Library** | ✅ | ✅ | Assign to clients |
| **Therapist Deletion (Admin)** | ✅ | ✅ | Clients become orphaned |
| **Orphaned Client Management** | ✅ | ✅ | Re-link to new therapist |
| **Legal Pages** | - | ✅ | Privacy, Terms, Disclaimer, Contact |
| **About Page** | - | ✅ | Public-facing |

### 🟡 PARTIAL / In Progress

| Feature | Status | Notes |
|---------|--------|-------|
| Client Profile Photo | ❌ Backend, ❌ Frontend | Not implemented |

### 🔴 NOT IMPLEMENTED (Future)

- AI-powered SOAP/DAP note generation
- Usage tracking/rate limiting for CI features
- Note templates sharing
- Coupon code management
- Forgot Password feature

---

## 🔧 4. Configuration & Environment Variables

### Backend `.env` (`/app/backend/.env`)

```env
# Database
MONGO_URL=mongodb://...
DB_NAME=cognispace

# Auth
JWT_SECRET=your_secret
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=admin123

# AI (Emergent LLM Key)
EMERGENT_LLM_KEY=your_key

# Email (Resend)
RESEND_API_KEY=re_xxxxx
SENDER_EMAIL=notifications@yourdomain.com

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# CORS
CORS_ORIGINS=*
```

### Frontend `.env` (`/app/frontend/.env`)

```env
REACT_APP_BACKEND_URL=https://your-preview-url
```

---

## 📧 5. Email Configuration

### Provider: Resend

**Files to Edit:**
- `/app/backend/services/email/resend_provider.py` - Provider implementation
- `/app/backend/services/email/templates.py` - **HTML templates (EDIT HERE)**
- `/app/backend/services/email/service.py` - Service logic

### Available Email Templates (`templates.py`)

| Template Key | Event | Data Required |
|--------------|-------|---------------|
| `welcome_credentials` | New user created | `login_id`, `password`, `therapist_name`, `login_url` |
| `password_changed` | Password updated | `login_id`, `changed_at` |
| `appointment_confirmation` | Appointment booked | `therapist_name`, `appointment_time`, `duration` |
| `appointment_reminder` | Before appointment | `therapist_name`, `appointment_time`, `time_until` |
| `payment_receipt` | Payment recorded | `amount`, `payment_date`, `receipt_number`, `payment_method` |
| `subscription_expiry` | Subscription ending | `plan_name`, `expiry_date`, `days_remaining` |

### How to Add/Edit Email Template:

```python
# In /app/backend/services/email/templates.py

def template_your_event(data: Dict[str, Any]) -> Dict[str, str]:
    content = f"""
    <p class="greeting">Your Title</p>
    <p class="message">{data.get('your_field')}</p>
    """
    return {
        "subject": "Your Subject Line",
        "html_body": get_base_template(content, "Title"),
        "text_body": "Plain text version"
    }

# Add to registry at bottom:
EMAIL_TEMPLATES = {
    ...
    "your_event": template_your_event,
}
```

---

## 📱 6. WhatsApp Configuration

### Provider: Twilio

**Files to Edit:**
- `/app/backend/services/whatsapp/twilio_provider.py` - Twilio implementation
- `/app/backend/services/whatsapp/registry.py` - Template mapping
- `/app/backend/services/whatsapp/service.py` - Business logic

### Template Configuration

WhatsApp templates are stored in MongoDB collection: `whatsapp_templates`

**Schema:**
```json
{
  "event": "appointment_confirmation",
  "provider": "twilio",
  "template_id": "HXxxxxx",  // Twilio Content SID
  "language": "en",
  "is_active": true
}
```

### How to Add WhatsApp Template:

1. **Create template in Twilio Console** → Get Content SID
2. **Add to database:**
```python
# Via API or direct DB insert
await db.whatsapp_templates.insert_one({
    "event": "new_event",
    "provider": "twilio",
    "template_id": "HXyour_content_sid",
    "language": "en",
    "is_active": True
})
```

### WhatsApp Business Rules:
- **Requires explicit opt-in** from user (`notification_opt_in.whatsapp = true`)
- **Subscription must allow** WhatsApp (`features.whatsapp_notifications = true`)
- **No clinical data** sent via WhatsApp (only reminders, confirmations)

---

## 👤 7. Role-Based Access Control

### Roles & Permissions

| Role | Can Access | Cannot Access |
|------|------------|---------------|
| **super_admin** | Everything, all therapists, all clients | - |
| **therapist** | Own clients, appointments, notes, reports | Other therapists' data |
| **assistant** | Assigned therapist's clients (non-clinical) | Session notes, AI features |
| **client** | Own appointments, shared reports | Other clients, therapist tools |

### Admin-Controlled Settings (Super Admin Only)
- Therapist approval/rejection
- Subscription plan assignment
- Therapist deletion
- Orphaned client re-linking
- System-wide settings

### Therapist-Controlled Settings
- Own profile (name, photo, specializations)
- Client creation & management
- Appointment scheduling
- Session notes
- Payment recording
- Notification preferences

---

## ⚠️ 8. Known Issues & Areas to Avoid

### Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Korean text "가능한" | Low | Rare AI response anomaly, ignore for now |
| Large `AIClinicalSupport.js` | Low | 800+ lines, needs decomposition |
| Large `PRD.md` | Low | 2000+ lines, needs splitting |

### Areas to Avoid Touching

1. **Auth Flow** (`/app/backend/routes/auth.py`) - Stable, many dependencies
2. **Database Connection** (`/app/backend/database.py`) - Critical
3. **Subscription Logic** - Complex billing rules
4. **WhatsApp Opt-in Logic** - Legal compliance requirement

### Code Patterns to Follow

```python
# Always exclude _id from MongoDB responses
user = await db.users.find_one({"id": user_id}, {"_id": 0})

# Always use timezone-aware datetime
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# Always validate ObjectId before using
from bson import ObjectId
if ObjectId.is_valid(some_id):
    # proceed
```

---

## 🚀 9. Run & Deploy Notes

### Local Development

```bash
# Backend (auto-restarts on code change)
sudo supervisorctl status backend

# Frontend (auto-restarts on code change)
sudo supervisorctl status frontend

# Restart services (only for .env or dependency changes)
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# View logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
```

### API Testing

```bash
# Get backend URL
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

# Test login
curl -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"identifier":"9807306444","password":"Abcd@1234"}'
```

### Scheduler Jobs (APScheduler)

| Job | Frequency | Purpose |
|-----|-----------|---------|
| `check_appointment_reminders` | Every 5 min | Send 60/30 min reminders |
| `check_pending_session_notes` | Every 15 min | Remind therapists |
| `check_subscription_expiry` | Daily 9 AM IST | Warn before expiry |

---

## 🔐 10. Test Credentials

| Role | Login ID | Password | URL |
|------|----------|----------|-----|
| **Super Admin** | `admin` | `admin123` | `/admin-login` |
| **Therapist 1 (Dr. Kavita)** | `9807306444` | `Abcd@1234` | `/login` |
| **Therapist 2 (Deepak)** | `7275005007` | `newpassword` | `/login` |
| **Assistant** | `support@mindlabs.co.in` | `Abcd@1234` | `/login` |
| **Client (Divya Sharma)** | `8299683186` | `Abcd@1234` | `/login` |

---

## 📊 11. Key Database Collections

| Collection | Purpose |
|------------|---------|
| `users` | All user accounts (all roles) |
| `therapists` | Therapist profiles |
| `client_profiles` | Client data linked to therapists |
| `appointments` | All appointments |
| `session_notes` | SOAP notes |
| `assessments` | Assessment records |
| `payments` | Payment transactions |
| `notifications` | In-app notifications |
| `diagnostic_reports` | AI-generated reports |
| `subscription_plans` | Available plans |
| `therapist_subscriptions` | Active subscriptions |
| `whatsapp_templates` | WhatsApp template mappings |
| `notification_logs` | Email/WhatsApp send logs |

---

## 📞 Quick Reference - Key API Endpoints

### Auth
- `POST /api/auth/login` - Login
- `POST /api/auth/register-therapist` - Therapist application

### Clients
- `GET /api/clients` - List therapist's clients
- `POST /api/clients` - Create client
- `GET /api/clients/{id}` - Get client details

### Appointments
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Create appointment
- `PUT /api/appointments/{id}/reschedule` - Reschedule

### AI (TheraGenie)
- `POST /api/ai/suggest-assessments` - Get assessment suggestions
- `POST /api/ai/generate-protocol` - Generate treatment protocol
- `POST /api/ai/generate-homework` - Generate homework
- `POST /api/ai/generate-diagnostic-report` - Generate diagnostic report

### Admin
- `GET /api/admin/therapists` - List all therapists
- `DELETE /api/admin/therapists/{id}` - Delete therapist
- `GET /api/admin/clients/orphaned` - Get orphaned clients
- `POST /api/admin/clients/{id}/relink` - Re-link client

### Payments
- `GET /api/payments/stats/summary` - Payment stats
- `GET /api/payments/reports/monthly-trend` - Monthly trends
- `GET /api/payments/reports/client-wise` - By client breakdown

---

**End of Handover Document**
