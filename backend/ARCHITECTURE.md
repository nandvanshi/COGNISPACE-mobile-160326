"""
TheraGenie Backend - Modular Architecture

This file documents the refactored architecture of the TheraGenie backend.

## Directory Structure

```
/app/backend/
├── server.py           # Main FastAPI application (being slimmed down)
├── database.py         # MongoDB connection
├── auth.py             # Authentication utilities & dependencies
├── assessment_library.py # Clinical assessments
├── models/
│   └── __init__.py     # All Pydantic models
├── routes/
│   └── __init__.py     # Route modules (migration in progress)
├── services/           # Business logic (future)
├── utils/              # Helper functions (future)
└── tests/              # Test files
```

## Models (models/__init__.py)

All Pydantic models organized by domain:
- Auth: UserRegister, UserLogin, User, TokenResponse
- Assistant: AssistantCreate, AssistantUpdate, AssistantResponse
- Client: ClientProfile, ClientProfileUpdate
- Appointment: AppointmentCreate, Appointment, CheckInRequest, CheckOutRequest
- Availability: TimeBlock, DayAvailability, TherapistAvailability, BlockedTime
- Session Notes: SessionNoteCreate, SessionNote, NoteTemplate
- Assessments: AssessmentCreate, Assessment, CustomAssessment
- Protocols: ProtocolCreate, Protocol, Homework
- Payments: PaymentCreate, Payment, CashSettlement
- Support: SupportTicket, TicketCreate, TicketReply
- Admin: SubscriptionPlan, CouponCode, TherapistProfile

## Authentication (auth.py)

- get_current_user: JWT token validation
- require_super_admin: Admin-only routes
- require_therapist: Therapist-only routes
- require_active_therapist_or_assistant: Both roles
- check_feature_enabled: Subscription feature checks
- log_audit: Audit logging

## Database (database.py)

- MongoDB connection via Motor
- Database instance: `db`

## Migration Status

| Domain | Status | Location |
|--------|--------|----------|
| Models | ✅ Extracted | models/__init__.py |
| Auth | ✅ Extracted | auth.py |
| Database | ✅ Extracted | database.py |
| Admin Routes | ⏳ Pending | server.py |
| Client Routes | ⏳ Pending | server.py |
| Clinical Routes | ⏳ Pending | server.py |

## Usage

The main server.py still contains all route handlers but now imports:
- Models from `models/__init__.py`
- Auth utilities from `auth.py`
- Database from `database.py`

This allows gradual migration without breaking changes.
"""
