"""
WhatsApp Templates - Twilio Content Template SIDs and helper functions
"""

# ============= TWILIO WHATSAPP TEMPLATES =============

# 1. Welcome Message - For new therapist/client approval
TEMPLATE_WELCOME = {
    "name": "cogni_1st",
    "sid": "HXc374601a165b80488fdc52a01a140d2b",
    "variables": ["name"],  # {{1}} -> Full name (without auto Dr. prefix)
}

# 2. Appointment Confirmation - When appointment is fixed
TEMPLATE_APPOINTMENT_CONFIRMED = {
    "name": "cogni_appointment",
    "sid": "HX6d3de8806ccd2116c7a5b32fe79f825",
    "variables": ["client_name", "therapist_name", "date", "time"],
}

# 3. Appointment Reminder - 1 hour before
TEMPLATE_APPOINTMENT_REMINDER = {
    "name": "cogni_rem",
    "sid": "HX25894886d0be2d48c89f2e24ac9fff8e",
    "variables": ["client_name", "therapist_name", "date", "time"],
}

# 4. Payment Received - When payment is recorded
TEMPLATE_PAYMENT_RECEIVED = {
    "name": "cogni_pay",
    "sid": "HX34fc7c7cc70b9036ccd1c350ac8acb6f",
    "variables": ["client_name", "amount", "therapist_name", "date"],
}


def get_welcome_variables(name: str) -> dict:
    """
    Get variables for welcome template.
    Don't add Dr. prefix - use name as-is from profile.
    """
    return {"1": name}


def get_appointment_confirmed_variables(
    client_name: str,
    therapist_name: str,
    date: str,
    time: str
) -> dict:
    """Get variables for appointment confirmation template."""
    return {
        "1": client_name,
        "2": therapist_name,
        "3": date,
        "4": time,
    }


def get_appointment_reminder_variables(
    client_name: str,
    therapist_name: str,
    date: str,
    time: str
) -> dict:
    """Get variables for appointment reminder template."""
    return {
        "1": client_name,
        "2": therapist_name,
        "3": date,
        "4": time,
    }


def get_payment_received_variables(
    client_name: str,
    amount: str,
    therapist_name: str,
    date: str
) -> dict:
    """Get variables for payment received template."""
    return {
        "1": client_name,
        "2": amount,
        "3": therapist_name,
        "4": date,
    }
