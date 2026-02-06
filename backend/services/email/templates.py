"""
Email Templates - HTML templates for different notification events
"""
from typing import Dict, Any
from datetime import datetime


def format_ist_datetime(dt_str: str) -> str:
    """Format datetime string to IST DD/MM/YYYY HH:mm"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        # Add 5:30 hours for IST
        from datetime import timedelta
        ist_dt = dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime("%d/%m/%Y %H:%M")
    except:
        return dt_str


def get_base_template(content: str, title: str = "COGNISPACE") -> str:
    """Base HTML email template with branding"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #0d5c4d 0%, #1a7a6a 100%);
            color: #fff;
            padding: 25px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
            letter-spacing: 1px;
        }}
        .header p {{
            margin: 5px 0 0;
            font-size: 12px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #0d5c4d;
            margin-bottom: 20px;
        }}
        .message {{
            font-size: 15px;
            color: #555;
            margin-bottom: 25px;
        }}
        .info-box {{
            background: #f0f9f7;
            border-left: 4px solid #0d5c4d;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .info-box p {{
            margin: 5px 0;
        }}
        .info-box strong {{
            color: #0d5c4d;
        }}
        .button {{
            display: inline-block;
            background: #0d5c4d;
            color: #fff !important;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 15px 0;
        }}
        .button:hover {{
            background: #1a7a6a;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            font-size: 12px;
            color: #888;
            border-top: 1px solid #eee;
        }}
        .footer a {{
            color: #0d5c4d;
            text-decoration: none;
        }}
        .divider {{
            height: 1px;
            background: #eee;
            margin: 20px 0;
        }}
        .credentials-box {{
            background: #fff8e1;
            border: 1px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .credentials-box h3 {{
            color: #f57c00;
            margin: 0 0 15px 0;
        }}
        .credential-item {{
            background: #fff;
            padding: 10px 15px;
            margin: 8px 0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>COGNISPACE</h1>
            <p>Precision Insights. Personal Growth.</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>This is an automated message from COGNISPACE.</p>
            <p>Please do not reply to this email.</p>
            <div class="divider"></div>
            <p>&copy; {datetime.now().year} COGNISPACE. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


# ============= EMAIL TEMPLATES =============

def template_welcome_credentials(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for new user credentials (login ID + password)"""
    content = f"""
    <p class="greeting">Welcome to COGNISPACE!</p>
    <p class="message">
        Your account has been created successfully. Below are your login credentials:
    </p>
    
    <div class="credentials-box">
        <h3>🔐 Your Login Credentials</h3>
        <div class="credential-item">
            <strong>Login ID:</strong> {data.get('login_id', 'N/A')}
        </div>
        <div class="credential-item">
            <strong>Password:</strong> {data.get('password', 'N/A')}
        </div>
    </div>
    
    <p class="message">
        <strong>Important:</strong> Please change your password after your first login for security.
    </p>
    
    <div class="info-box">
        <p><strong>Your Therapist:</strong> {data.get('therapist_name', 'N/A')}</p>
    </div>
    
    <a href="{data.get('login_url', '#')}" class="button">Login to COGNISPACE</a>
    """
    
    return {
        "subject": "Welcome to COGNISPACE - Your Login Credentials",
        "html_body": get_base_template(content, "Welcome to COGNISPACE"),
        "text_body": f"Welcome to COGNISPACE! Your Login ID: {data.get('login_id')}, Password: {data.get('password')}. Please login at {data.get('login_url')} and change your password."
    }


def template_password_changed(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for password change notification"""
    content = f"""
    <p class="greeting">Password Changed Successfully</p>
    <p class="message">
        Your COGNISPACE password has been changed successfully.
    </p>
    
    <div class="info-box">
        <p><strong>Changed at:</strong> {format_ist_datetime(data.get('changed_at', ''))}</p>
        <p><strong>Account:</strong> {data.get('login_id', 'N/A')}</p>
    </div>
    
    <p class="message" style="color: #d32f2f;">
        <strong>⚠️ If you did not make this change, please contact your therapist or support immediately.</strong>
    </p>
    """
    
    return {
        "subject": "COGNISPACE - Password Changed",
        "html_body": get_base_template(content, "Password Changed"),
        "text_body": f"Your COGNISPACE password was changed at {format_ist_datetime(data.get('changed_at'))}. If you did not make this change, please contact support."
    }


def template_appointment_confirmation(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for appointment confirmation"""
    content = f"""
    <p class="greeting">Appointment Confirmed!</p>
    <p class="message">
        Your appointment has been successfully scheduled.
    </p>
    
    <div class="info-box">
        <p><strong>📅 Date & Time:</strong> {format_ist_datetime(data.get('appointment_time', ''))}</p>
        <p><strong>👤 With:</strong> {data.get('therapist_name', 'Your Therapist')}</p>
        <p><strong>⏱️ Duration:</strong> {data.get('duration', '50')} minutes</p>
    </div>
    
    <p class="message">
        Please arrive 5-10 minutes before your scheduled time.
    </p>
    
    <a href="{data.get('dashboard_url', '#')}" class="button">View Appointment</a>
    """
    
    return {
        "subject": f"Appointment Confirmed - {format_ist_datetime(data.get('appointment_time', ''))}",
        "html_body": get_base_template(content, "Appointment Confirmed"),
        "text_body": f"Your appointment with {data.get('therapist_name')} is confirmed for {format_ist_datetime(data.get('appointment_time'))}."
    }


def template_appointment_reminder(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for appointment reminder"""
    content = f"""
    <p class="greeting">Appointment Reminder</p>
    <p class="message">
        This is a reminder for your upcoming appointment.
    </p>
    
    <div class="info-box">
        <p><strong>📅 Date & Time:</strong> {format_ist_datetime(data.get('appointment_time', ''))}</p>
        <p><strong>👤 With:</strong> {data.get('therapist_name', 'Your Therapist')}</p>
        <p><strong>⏰ Time Until:</strong> {data.get('time_until', 'Soon')}</p>
    </div>
    
    <p class="message">
        Please ensure you're ready for your session.
    </p>
    """
    
    return {
        "subject": f"Reminder: Appointment in {data.get('time_until', 'soon')}",
        "html_body": get_base_template(content, "Appointment Reminder"),
        "text_body": f"Reminder: Your appointment with {data.get('therapist_name')} is {data.get('time_until')} at {format_ist_datetime(data.get('appointment_time'))}."
    }


def template_payment_receipt(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for payment receipt"""
    content = f"""
    <p class="greeting">Payment Receipt</p>
    <p class="message">
        Thank you for your payment. Here are your receipt details:
    </p>
    
    <div class="info-box">
        <p><strong>💰 Amount Paid:</strong> ₹{data.get('amount', 0):,.0f}</p>
        <p><strong>📅 Payment Date:</strong> {format_ist_datetime(data.get('payment_date', ''))}</p>
        <p><strong>🧾 Receipt No:</strong> {data.get('receipt_number', 'N/A')}</p>
        <p><strong>💳 Payment Method:</strong> {data.get('payment_method', 'N/A')}</p>
    </div>
    
    <p class="message">
        {data.get('therapist_name', 'Your Therapist')}
    </p>
    
    <a href="{data.get('receipt_url', '#')}" class="button">View Full Receipt</a>
    """
    
    return {
        "subject": f"Payment Receipt - ₹{data.get('amount', 0):,.0f}",
        "html_body": get_base_template(content, "Payment Receipt"),
        "text_body": f"Payment of ₹{data.get('amount', 0):,.0f} received on {format_ist_datetime(data.get('payment_date'))}. Receipt No: {data.get('receipt_number')}."
    }


def template_subscription_expiry(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for subscription expiry warning"""
    content = f"""
    <p class="greeting">Subscription Expiring Soon</p>
    <p class="message">
        Your COGNISPACE subscription is expiring soon. Please renew to continue uninterrupted services.
    </p>
    
    <div class="info-box">
        <p><strong>📅 Expiry Date:</strong> {format_ist_datetime(data.get('expiry_date', ''))}</p>
        <p><strong>⏰ Days Remaining:</strong> {data.get('days_remaining', 0)} days</p>
        <p><strong>📦 Current Plan:</strong> {data.get('plan_name', 'N/A')}</p>
    </div>
    
    <p class="message">
        Renew now to avoid any disruption in your practice management.
    </p>
    
    <a href="{data.get('renewal_url', '#')}" class="button">Renew Subscription</a>
    """
    
    return {
        "subject": f"Subscription Expiring in {data.get('days_remaining', 0)} Days",
        "html_body": get_base_template(content, "Subscription Expiring"),
        "text_body": f"Your COGNISPACE subscription expires on {format_ist_datetime(data.get('expiry_date'))}. {data.get('days_remaining')} days remaining. Please renew."
    }


def template_appointment_confirmation_therapist(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for appointment confirmation sent to therapist/assistant"""
    content = f"""
    <p class="greeting">New Appointment Scheduled</p>
    <p class="message">
        A new appointment has been booked.
    </p>
    
    <div class="info-box">
        <p><strong>👤 Client:</strong> {data.get('client_name', 'N/A')}</p>
        <p><strong>📅 Date & Time:</strong> {format_ist_datetime(data.get('appointment_time', ''))}</p>
        <p><strong>⏱️ Duration:</strong> {data.get('duration', '50')} minutes</p>
        <p><strong>📝 Type:</strong> {data.get('appointment_type', 'Session')}</p>
    </div>
    
    <a href="{data.get('dashboard_url', '#')}" class="button">View Schedule</a>
    """
    
    return {
        "subject": f"New Appointment: {data.get('client_name', 'Client')} - {format_ist_datetime(data.get('appointment_time', ''))}",
        "html_body": get_base_template(content, "New Appointment"),
        "text_body": f"New appointment with {data.get('client_name')} on {format_ist_datetime(data.get('appointment_time'))}."
    }


def template_daily_schedule_briefing(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for morning daily schedule briefing"""
    appointments = data.get('appointments', [])
    total_count = len(appointments)
    
    if total_count == 0:
        schedule_html = """
        <div class="info-box" style="background: #e8f5e9; border-color: #4caf50;">
            <p style="color: #2e7d32; margin: 0;">✨ No appointments scheduled for today. Enjoy your day!</p>
        </div>
        """
    else:
        schedule_items = ""
        for appt in appointments:
            schedule_items += f"""
            <div style="background: #fff; padding: 12px 15px; margin: 8px 0; border-radius: 6px; border-left: 4px solid #0d5c4d;">
                <p style="margin: 0 0 5px 0;"><strong>{appt.get('time', 'N/A')}</strong> - {appt.get('client_name', 'N/A')}</p>
                <p style="margin: 0; font-size: 13px; color: #666;">{appt.get('type', 'Session')} • {appt.get('duration', '50')} mins</p>
            </div>
            """
        schedule_html = f"""
        <div class="info-box">
            <p><strong>📊 Total Appointments:</strong> {total_count}</p>
        </div>
        <div style="margin-top: 15px;">
            <h3 style="color: #0d5c4d; margin: 0 0 10px 0;">Today's Schedule</h3>
            {schedule_items}
        </div>
        """
    
    content = f"""
    <p class="greeting">Good Morning! ☀️</p>
    <p class="message">
        Here's your schedule for <strong>{data.get('date', 'today')}</strong>:
    </p>
    
    {schedule_html}
    
    <a href="{data.get('dashboard_url', '#')}" class="button">Open Dashboard</a>
    """
    
    return {
        "subject": f"📅 Daily Schedule - {data.get('date', 'Today')} ({total_count} appointments)",
        "html_body": get_base_template(content, "Daily Schedule"),
        "text_body": f"Good Morning! You have {total_count} appointments today ({data.get('date')}). Login to view details."
    }


def template_daily_payment_statement(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for end-of-day payment statement"""
    payments = data.get('payments', [])
    total_amount = data.get('total_amount', 0)
    payment_count = len(payments)
    
    if payment_count == 0:
        payments_html = """
        <div class="info-box" style="background: #fff3e0; border-color: #ff9800;">
            <p style="color: #e65100; margin: 0;">No payments recorded today.</p>
        </div>
        """
    else:
        payment_items = ""
        for pmt in payments:
            status_color = "#4caf50" if pmt.get('status') == 'paid' else "#ff9800"
            payment_items += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{pmt.get('client_name', 'N/A')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{pmt.get('amount', 0):,.0f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{pmt.get('method', 'N/A')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><span style="color: {status_color};">{pmt.get('status', 'N/A').title()}</span></td>
            </tr>
            """
        payments_html = f"""
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
            <thead>
                <tr style="background: #f5f5f5;">
                    <th style="padding: 10px; text-align: left;">Client</th>
                    <th style="padding: 10px; text-align: left;">Amount</th>
                    <th style="padding: 10px; text-align: left;">Method</th>
                    <th style="padding: 10px; text-align: left;">Status</th>
                </tr>
            </thead>
            <tbody>
                {payment_items}
            </tbody>
        </table>
        """
    
    content = f"""
    <p class="greeting">Daily Payment Statement 💰</p>
    <p class="message">
        Here's your payment summary for <strong>{data.get('date', 'today')}</strong>:
    </p>
    
    <div class="info-box" style="background: #e8f5e9; border-color: #4caf50;">
        <p style="font-size: 24px; color: #2e7d32; margin: 0 0 5px 0;"><strong>₹{total_amount:,.0f}</strong></p>
        <p style="margin: 0; color: #666;">Total from {payment_count} payment(s)</p>
    </div>
    
    {payments_html}
    
    <a href="{data.get('reports_url', '#')}" class="button">View Full Report</a>
    """
    
    return {
        "subject": f"💰 Daily Payment Statement - {data.get('date', 'Today')} (₹{total_amount:,.0f})",
        "html_body": get_base_template(content, "Daily Payment Statement"),
        "text_body": f"Daily Payment Statement for {data.get('date')}: Total ₹{total_amount:,.0f} from {payment_count} payments."
    }


# Template registry
EMAIL_TEMPLATES = {
    "welcome_credentials": template_welcome_credentials,
    "password_changed": template_password_changed,
    "appointment_confirmation": template_appointment_confirmation,
    "appointment_confirmation_therapist": template_appointment_confirmation_therapist,
    "appointment_reminder": template_appointment_reminder,
    "payment_receipt": template_payment_receipt,
    "subscription_expiry": template_subscription_expiry,
    "daily_schedule_briefing": template_daily_schedule_briefing,
    "daily_payment_statement": template_daily_payment_statement,
}


def get_email_template(event: str, data: Dict[str, Any]) -> Dict[str, str]:
    """
    Get email template for an event.
    
    Args:
        event: Event name (e.g., 'appointment_confirmation')
        data: Template data
        
    Returns:
        Dict with 'subject', 'html_body', 'text_body'
    """
    if event in EMAIL_TEMPLATES:
        return EMAIL_TEMPLATES[event](data)
    
    # Default template
    return {
        "subject": f"COGNISPACE Notification",
        "html_body": get_base_template(f"<p>{data.get('message', 'You have a new notification.')}</p>"),
        "text_body": data.get('message', 'You have a new notification.')
    }
