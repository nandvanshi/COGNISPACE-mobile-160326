# COGNISPACE - Changelog

All notable changes to this project are documented in this file.

---

## [Jan 26, 2026] - Latest Session

### Frontend Refactoring
- **AIClinicalSupport.js Component Breakdown** (1721 lines → 12 modular files)
  ```
  ai-clinical/
  ├── index.js             - Main wrapper (267 lines)
  ├── AssessmentsTab.js    - Assessment suggestions UI
  ├── DiagnosticTab.js     - CogniVision reports UI
  ├── ProtocolsTab.js      - Protocol builder UI
  ├── HomeworkTab.js       - Homework generator UI
  ├── ResourcesTab.js      - Resource library UI
  ├── hooks/useAIClinical.js - All API calls & state
  └── dialogs/
      ├── ProtocolDialog.js
      ├── HomeworkDialog.js
      ├── ResourceDialog.js
      ├── ReportEditorDialog.js
      └── ReportPreviewDialog.js
  ```

### New Pages
- **About Page** (`/about`) - Public-facing informational page
  - Hero section with tagline
  - "What is COGNISPACE?" section
  - "Who is it for?" cards (Therapists, Clinics, Clients)
  - Philosophy & clinical disclaimer
  - Privacy, Ethics & Safety points
  - Compliance & Standards section
  - CTA buttons for Registration & Support

### Bug Fixes
- ✅ Login Page Footer Desktop Layout Fix
  - Fixed footer alignment issue on desktop view
  - Changed layout structure: outer flex-col with inner flex-row
  - Footer now spans full width and stays centered

### Documentation
- Created `/app/memory/HANDOVER.md` - Complete system handover document
- Split PRD.md into PRD.md, CHANGELOG.md, ROADMAP.md

---

## [Jan 25, 2026] - Backend Refactoring & Features

### Backend Refactoring (Completed)
- **AI Clinical Routes** moved to `/app/backend/routes/ai_clinical.py`
- **Diagnostic Reports Routes** moved to `/app/backend/routes/diagnostic_reports.py`
- **Resources Routes** moved to `/app/backend/routes/resources.py`
- **server.py reduction**: 2570 → 1287 lines (~50% reduction)

### Payment Reporting Feature (NEW)
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

### Admin Features
- **Therapist Deletion** with client data handling
- **Orphaned Client Management** - View and re-link unlinked clients

### Legal Pages
- Privacy Policy (`/privacy-policy`)
- Terms & Conditions (`/terms-conditions`)
- Clinical Disclaimer (`/clinical-disclaimer`)
- Contact/Support (`/contact`)

### Bug Fixes
- ✅ AI response parsing error (empty JSON handling)
- ✅ subscription_end_date not showing in Admin panel

---

## [Earlier Releases]

### Core Platform
- JWT-based authentication (4 roles)
- Client management with self-registration
- Appointment scheduling with recurring patterns
- Session notes (SOAP format)
- Assessments with auto-scoring

### TheraGenie AI
- Assessment suggestions
- Protocol generation
- Homework generation
- CogniVision diagnostic reports

### Notifications
- In-app notification system
- Email notifications (Resend)
- WhatsApp notifications (Twilio)

### Scheduler
- APScheduler for background jobs
- 60/30 minute appointment reminders
- Pending session note reminders
- Subscription expiry warnings

### Payments
- Payment tracking
- Receipt generation
- Client payment history
