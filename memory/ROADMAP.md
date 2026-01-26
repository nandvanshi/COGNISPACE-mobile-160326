# COGNISPACE - Product Roadmap

## Current Status: MVP Complete ✅

---

## 🔴 P0 - Critical / In Progress
*Nothing critical pending*

---

## 🟠 P1 - High Priority (Next Sprint)

### 1. Client Profile Photo Upload
- **Backend**: File upload API, storage
- **Frontend**: Photo upload UI in client profile
- **Status**: Not started

### 2. Forgot Password Feature
- **Backend**: Password reset flow with email
- **Frontend**: "Forgot Password" link on login page
- **Status**: Not started

---

## 🟡 P2 - Medium Priority (Future Sprints)

### 3. AI-Powered SOAP/DAP Note Generation
- Generate session notes from session context
- Support for SOAP, DAP, and other formats
- Integration with TheraGenie

### 4. Usage Tracking for AI Features
- Track AI feature usage per therapist
- Rate limiting implementation
- Usage analytics dashboard

### 5. Note Templates Sharing
- Therapists can create and share note templates
- Template library feature
- Import/export functionality

### 6. Coupon Code Management
- Backend CRUD for coupon codes
- Apply coupon during subscription
- Admin dashboard for coupon management

---

## 🟢 P3 - Low Priority (Backlog)

### 7. Client Portal Enhancements
- Self-service appointment booking
- Homework submission
- Resource download tracking

### 8. Advanced Reporting
- Therapist productivity reports
- Client progress dashboards
- Revenue forecasting

### 9. Multi-Clinic Support
- Organization hierarchy
- Cross-clinic client transfers
- Consolidated admin dashboard

### 10. Mobile App (Future)
- React Native app
- Push notifications
- Offline session notes

---

## ✅ Recently Completed

- [x] AIClinicalSupport.js component breakdown (Jan 26, 2026)
- [x] About page creation (Jan 26, 2026)
- [x] Login page footer fix (Jan 26, 2026)
- [x] Backend route refactoring (Jan 25, 2026)
- [x] Payment reporting feature (Jan 25, 2026)
- [x] Therapist deletion & orphan management (Jan 25, 2026)
- [x] Legal pages (Privacy, Terms, Disclaimer, Contact)
- [x] Handover documentation

---

## Technical Debt / Refactoring

### Completed
- [x] server.py route extraction (50% reduction)
- [x] AIClinicalSupport.js breakdown

### Pending
- [ ] PRD.md split into PRD, CHANGELOG, ROADMAP ← Current task
- [ ] Test file creation for regression testing
- [ ] API documentation (Swagger/OpenAPI)

---

## Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| Korean text "가능한" in AI response | Low | Parked (rare occurrence) |
| Large component files | Low | Partially addressed |

---

## Feature Requests (User Feedback)
*Add user-requested features here for prioritization*

1. _None pending_

---

## Notes
- All AI features use Claude Sonnet 4 via Emergent LLM Key
- WhatsApp notifications require explicit user opt-in
- Client self-registration is disabled (therapist creates accounts)
