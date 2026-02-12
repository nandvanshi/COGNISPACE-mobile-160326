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


def template_therapist_welcome(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for therapist account approval with login credentials and platform guide"""
    password_section = ""
    if data.get('password'):
        password_section = f"""
        <div class="credential-item">
            <strong>Password:</strong> {data.get('password')}
        </div>
        <p class="message" style="color: #d32f2f; font-size: 14px;">
            <strong>⚠️ Important:</strong> Please change your password after your first login for security.
        </p>
        """
    else:
        password_section = """
        <p class="message" style="color: #0d5c4d; font-size: 14px;">
            <strong>✓</strong> You set your password during registration. Use that to login.
        </p>
        """
    
    content = f"""
    <p class="greeting">🎉 Welcome to COGNISPACE, {data.get('therapist_name', '')}!</p>
    <p class="message">
        Your COGNISPACE therapist account has been <strong>approved</strong>. You now have access to our comprehensive practice management platform designed specifically for mental health professionals.
    </p>
    
    <div class="credentials-box">
        <h3>🔐 Your Login Credentials</h3>
        <div class="credential-item">
            <strong>Login ID (Mobile):</strong> {data.get('mobile', 'N/A')}
        </div>
        {password_section}
    </div>
    
    <div class="info-box">
        <h4>📅 Your Free Trial</h4>
        <p><strong>Trial Period:</strong> 14 Days</p>
        <p><strong>Trial Ends:</strong> {data.get('trial_end_date', 'N/A')}</p>
        <p>Explore all premium features during your trial period.</p>
    </div>
    
    <div class="divider"></div>
    
    <h3 style="color: #0d5c4d;">📖 Quick Start Guide</h3>
    
    <div class="info-box" style="background: #e3f2fd; border-color: #2196f3;">
        <h4 style="color: #1565c0;">1️⃣ Client Management</h4>
        <ul style="margin: 10px 0; padding-left: 20px; color: #333;">
            <li>Add clients manually or share your unique registration link</li>
            <li>Maintain complete client profiles with case history</li>
            <li>Track progress and manage treatment plans</li>
        </ul>
    </div>
    
    <div class="info-box" style="background: #f3e5f5; border-color: #9c27b0;">
        <h4 style="color: #7b1fa2;">2️⃣ Appointments & Sessions</h4>
        <ul style="margin: 10px 0; padding-left: 20px; color: #333;">
            <li>Schedule appointments with automated reminders</li>
            <li>Create detailed session notes (SOAP format supported)</li>
            <li>Use quick session templates for efficiency</li>
        </ul>
    </div>
    
    <div class="info-box" style="background: #fff3e0; border-color: #ff9800;">
        <h4 style="color: #ef6c00;">3️⃣ TheraGenie AI Assistant</h4>
        <ul style="margin: 10px 0; padding-left: 20px; color: #333;">
            <li>Get AI-powered clinical insights and suggestions</li>
            <li>Generate comprehensive psychodiagnostic reports</li>
            <li>Use CogniVision for symptom analysis</li>
        </ul>
    </div>
    
    <div class="info-box" style="background: #e8f5e9; border-color: #4caf50;">
        <h4 style="color: #2e7d32;">4️⃣ Payments & Reports</h4>
        <ul style="margin: 10px 0; padding-left: 20px; color: #333;">
            <li>Track session payments and generate receipts</li>
            <li>View revenue reports and analytics</li>
            <li>Export data for accounting purposes</li>
        </ul>
    </div>
    
    <div class="info-box" style="background: #fce4ec; border-color: #e91e63;">
        <h4 style="color: #c2185b;">5️⃣ Secure Messaging</h4>
        <ul style="margin: 10px 0; padding-left: 20px; color: #333;">
            <li>Communicate securely with clients</li>
            <li>Enable/disable messaging per client</li>
            <li>All messages are encrypted</li>
        </ul>
    </div>
    
    <div class="divider"></div>
    
    <a href="{data.get('login_url', 'https://cognispace.in/login')}" class="button" style="display: block; text-align: center;">🚀 Login to COGNISPACE</a>
    
    <div class="divider"></div>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 20px;">
        <h4 style="margin: 0 0 10px 0; color: #0d5c4d;">Need Help?</h4>
        <p style="margin: 5px 0; font-size: 14px;">📧 Email: <a href="mailto:care@cognispace.in">care@cognispace.in</a></p>
        <p style="margin: 5px 0; font-size: 14px;">📱 WhatsApp: <a href="https://wa.me/917348700555">+91 7348700555</a></p>
        <p style="margin: 5px 0; font-size: 14px; color: #666;">We're here to help you get started!</p>
    </div>
    """
    
    return {
        "subject": "🎉 Welcome to COGNISPACE - Your Account is Approved!",
        "html_body": get_base_template(content, "Welcome to COGNISPACE"),
        "text_body": f"Welcome {data.get('therapist_name')}! Your COGNISPACE account is approved. Login ID: {data.get('mobile')}. Trial Period: 14 days. Login at {data.get('login_url', 'https://cognispace.in/login')}"
    }


def template_client_welcome(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for client account creation with login credentials and platform guide"""
    content = f"""
    <p class="greeting">🌟 Welcome to COGNISPACE, {data.get('client_name', '')}!</p>
    <p class="message">
        Your COGNISPACE client account has been created by <strong>{data.get('therapist_name', 'your therapist')}</strong>. You now have access to a secure platform to connect with your therapist and manage your therapy journey.
    </p>
    
    <div class="credentials-box">
        <h3>🔐 Your Login Credentials</h3>
        <div class="credential-item">
            <strong>Username:</strong> {data.get('username', data.get('mobile', 'N/A'))}
        </div>
        <div class="credential-item">
            <strong>Password:</strong> {data.get('password', 'N/A')}
        </div>
    </div>
    
    <p class="message" style="color: #d32f2f; font-size: 14px;">
        <strong>⚠️ Important:</strong> Please change your password after your first login for security.
    </p>
    
    <div class="info-box">
        <h4>👤 Your Therapist</h4>
        <p><strong>Name:</strong> {data.get('therapist_name', 'N/A')}</p>
    </div>
    
    <div class="divider"></div>
    
    <h3 style="color: #0d5c4d;">📱 How to Use the Portal</h3>
    
    <div class="info-box" style="background: #e3f2fd; border-color: #2196f3;">
        <h4 style="color: #1565c0;">📅 View Appointments</h4>
        <p style="margin: 5px 0; color: #333;">See your scheduled sessions and upcoming appointments on your dashboard.</p>
    </div>
    
    <div class="info-box" style="background: #f3e5f5; border-color: #9c27b0;">
        <h4 style="color: #7b1fa2;">💬 Message Your Therapist</h4>
        <p style="margin: 5px 0; color: #333;">Use secure in-app messaging to communicate with your therapist between sessions.</p>
    </div>
    
    <div class="info-box" style="background: #e8f5e9; border-color: #4caf50;">
        <h4 style="color: #2e7d32;">📊 Track Your Progress</h4>
        <p style="margin: 5px 0; color: #333;">View your session history and any shared reports or assessments.</p>
    </div>
    
    <div class="info-box" style="background: #fff3e0; border-color: #ff9800;">
        <h4 style="color: #ef6c00;">💳 View Payments</h4>
        <p style="margin: 5px 0; color: #333;">Track your payment history and view receipts for sessions.</p>
    </div>
    
    <div class="divider"></div>
    
    <a href="{data.get('login_url', 'https://cognispace.in/login')}" class="button" style="display: block; text-align: center;">🚀 Login to Your Account</a>
    
    <div class="divider"></div>
    
    <div style="background: #fce4ec; padding: 15px; border-radius: 8px; margin-top: 20px;">
        <p style="margin: 0; font-size: 14px; color: #c2185b;">
            <strong>🔒 Privacy First:</strong> All your information is secure and confidential. Only you and your therapist can access your data.
        </p>
    </div>
    
    <p class="message" style="margin-top: 20px; font-size: 14px;">
        For any questions, please contact your therapist directly through the portal.
    </p>
    """
    
    return {
        "subject": f"🌟 Welcome to COGNISPACE - Your Client Account",
        "html_body": get_base_template(content, "Welcome to COGNISPACE"),
        "text_body": f"Welcome {data.get('client_name')}! Your COGNISPACE account has been created by {data.get('therapist_name')}. Username: {data.get('username', data.get('mobile'))}. Password: {data.get('password')}. Login at {data.get('login_url', 'https://cognispace.in/login')}"
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
    """Template for appointment confirmation - Client receives this"""
    # Parse date and time for display
    appt_time = data.get('appointment_time', '')
    therapist_name = data.get('therapist_name', 'Your Therapist')
    client_name = data.get('client_name', 'Dear Client')
    date_display = format_ist_datetime(appt_time).split(' ')[0] if appt_time else 'N/A'
    time_display = format_ist_datetime(appt_time).split(' ')[1] if appt_time and len(format_ist_datetime(appt_time).split(' ')) > 1 else 'N/A'
    
    content = f"""
    <p class="greeting">Dear {client_name},</p>
    
    <p class="message">
        We are pleased to confirm your appointment with <strong>{therapist_name}</strong> on:
    </p>
    
    <div class="info-box" style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 16px;"><strong>📅 Date:</strong> {date_display}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>⏰ Time:</strong> {time_display}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>⏱️ Duration:</strong> {data.get('duration', '50')} minutes</p>
    </div>
    
    <p class="message">
        We look forward to supporting you during this session. Your commitment to your well-being is important, and we are here to ensure a smooth and meaningful experience.
    </p>
    
    <div class="info-box" style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0;">
        <p style="margin: 0; font-size: 14px; color: #1565c0;">
            <strong>💡 For online sessions:</strong> We recommend joining a few minutes early and ensuring a stable internet connection for an uninterrupted experience.
        </p>
    </div>
    
    <p class="message">
        You may review your appointment details anytime through your client portal:
    </p>
    
    <a href="{data.get('dashboard_url', 'https://cognispace.in/login')}" class="button" style="display: block; text-align: center; margin: 20px 0;">View Appointment</a>
    
    <p class="message" style="font-size: 14px; color: #666;">
        If you need to make any changes or have questions regarding your session, please contact your therapist directly.
    </p>
    
    <div class="divider" style="border-top: 1px solid #eee; margin: 20px 0;"></div>
    
    <p class="message">
        We look forward to connecting with you.
    </p>
    
    <p class="message" style="margin-top: 20px;">
        <strong>Warm regards,</strong><br>
        Team CogniSpace
    </p>
    """
    
    # Subject format: Appointment Confirmed - DD/MM/YYYY HH:MM
    subject_date = format_ist_datetime(appt_time) if appt_time else ''
    
    return {
        "subject": f"Appointment Confirmed - {subject_date}",
        "html_body": get_base_template(content, "Appointment Confirmed"),
        "text_body": f"Dear {client_name}, Your appointment with {therapist_name} is confirmed for {format_ist_datetime(appt_time)}. We look forward to connecting with you. - Team CogniSpace"
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


def template_password_reset(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for password reset email"""
    content = f"""
    <p class="greeting">Password Reset Request</p>
    <p class="message">
        Hi {data.get('user_name', 'User')},
    </p>
    <p class="message">
        We received a request to reset your COGNISPACE account password. Click the button below to set a new password:
    </p>
    
    <a href="{data.get('reset_link', '#')}" class="button" style="display: block; text-align: center; margin: 30px 0;">Reset My Password</a>
    
    <div class="info-box" style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0;">
        <p style="margin: 0; font-size: 14px; color: #e65100;">
            <strong>⏰ This link will expire in {data.get('expiry_hours', 1)} hour(s).</strong>
        </p>
    </div>
    
    <p class="message" style="font-size: 14px; color: #666;">
        If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.
    </p>
    
    <div class="divider" style="border-top: 1px solid #eee; margin: 20px 0;"></div>
    
    <p class="message" style="font-size: 12px; color: #999;">
        If the button above doesn't work, copy and paste this link into your browser:<br>
        <span style="word-break: break-all; color: #0d5c4d;">{data.get('reset_link', '#')}</span>
    </p>
    
    <p class="message" style="margin-top: 20px;">
        <strong>Warm regards,</strong><br>
        Team CogniSpace
    </p>
    """
    
    return {
        "subject": "Reset Your COGNISPACE Password",
        "html_body": get_base_template(content, "Password Reset"),
        "text_body": f"Hi {data.get('user_name')}, Click this link to reset your password: {data.get('reset_link')}. This link expires in {data.get('expiry_hours', 1)} hour(s)."
    }


def template_appointment_cancellation(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for appointment cancellation notification"""
    content = f"""
    <p class="greeting">Appointment Cancelled</p>
    <p class="message">
        The following appointment has been cancelled:
    </p>
    
    <div class="info-box" style="background: #ffebee; border-left: 4px solid #f44336; padding: 20px; margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 16px;"><strong>👤 Client:</strong> {data.get('client_name', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>👨‍⚕️ Therapist:</strong> {data.get('therapist_name', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>📅 Date:</strong> {format_ist_datetime(data.get('appointment_time', ''))}</p>
    </div>
    
    <p class="message" style="font-size: 14px; color: #666;">
        <strong>Cancelled by:</strong> {data.get('cancelled_by', 'N/A')}<br>
        <strong>Reason:</strong> {data.get('cancellation_reason', 'No reason provided')}
    </p>
    
    <p class="message" style="margin-top: 20px;">
        <strong>Warm regards,</strong><br>
        Team CogniSpace
    </p>
    """
    
    return {
        "subject": f"Appointment Cancelled - {data.get('client_name', 'Client')} ({format_ist_datetime(data.get('appointment_time', ''))})",
        "html_body": get_base_template(content, "Appointment Cancelled"),
        "text_body": f"Appointment cancelled for {data.get('client_name')} on {format_ist_datetime(data.get('appointment_time'))}. Cancelled by: {data.get('cancelled_by')}."
    }


def template_client_self_registration(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for notifying therapist/assistant when client self-registers"""
    content = f"""
    <p class="greeting">🎉 New Client Registration!</p>
    <p class="message">
        A new client has registered through your referral link.
    </p>
    
    <div class="info-box" style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 16px;"><strong>👤 Name:</strong> {data.get('client_name', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>📱 Mobile:</strong> {data.get('client_mobile', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>📧 Email:</strong> {data.get('client_email', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>📅 Registered:</strong> {format_ist_datetime(data.get('registration_time', ''))}</p>
    </div>
    
    <p class="message">
        You can now view this client in your dashboard and schedule their first appointment.
    </p>
    
    <a href="{data.get('dashboard_url', 'https://cognispace.in/login')}" class="button" style="display: block; text-align: center; margin: 20px 0;">View Client</a>
    
    <p class="message" style="margin-top: 20px;">
        <strong>Warm regards,</strong><br>
        Team CogniSpace
    </p>
    """
    
    return {
        "subject": f"New Client Registration - {data.get('client_name', 'New Client')}",
        "html_body": get_base_template(content, "New Client Registration"),
        "text_body": f"New client {data.get('client_name')} ({data.get('client_mobile')}) has registered through your referral link."
    }


def template_payment_received_therapist(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for notifying therapist/assistant when payment is received"""
    content = f"""
    <p class="greeting">💰 Payment Received!</p>
    <p class="message">
        A payment has been recorded for one of your clients.
    </p>
    
    <div class="info-box" style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 16px;"><strong>👤 Client:</strong> {data.get('client_name', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>💵 Amount:</strong> ₹{data.get('amount', 0):,.0f}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>💳 Method:</strong> {data.get('payment_method', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>🧾 Receipt:</strong> {data.get('receipt_number', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>📅 Date:</strong> {format_ist_datetime(data.get('payment_date', ''))}</p>
    </div>
    
    <a href="{data.get('dashboard_url', 'https://cognispace.in/login')}" class="button" style="display: block; text-align: center; margin: 20px 0;">View Payment Details</a>
    
    <p class="message" style="margin-top: 20px;">
        <strong>Warm regards,</strong><br>
        Team CogniSpace
    </p>
    """
    
    return {
        "subject": f"Payment Received - ₹{data.get('amount', 0):,.0f} from {data.get('client_name', 'Client')}",
        "html_body": get_base_template(content, "Payment Received"),
        "text_body": f"Payment of ₹{data.get('amount', 0):,.0f} received from {data.get('client_name')} via {data.get('payment_method')}."
    }


def template_consent_accepted(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for notifying therapist/assistant when client accepts consent"""
    content = f"""
    <p class="greeting">✅ Consent Form Accepted!</p>
    <p class="message">
        A client has signed and accepted their therapy consent form.
    </p>
    
    <div class="info-box" style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 16px;"><strong>👤 Client:</strong> {data.get('client_name', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>👨‍⚕️ Therapist:</strong> {data.get('therapist_name', 'N/A')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>📅 Signed On:</strong> {format_ist_datetime(data.get('signature_date', ''))}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>✍️ Method:</strong> {data.get('signature_method', 'Digital').title()}</p>
    </div>
    
    <div class="info-box" style="background: #f5f5f5; border-left: 4px solid #0d5c4d; padding: 15px; margin: 20px 0;">
        <p style="margin: 0; font-size: 14px; color: #333;">
            <strong>📋 Consent Summary:</strong><br>
            {data.get('consent_summary', 'Informed Consent for Psychological Services')}
        </p>
    </div>
    
    <p class="message">
        You can now proceed with scheduling sessions and creating session notes for this client.
    </p>
    
    <a href="{data.get('dashboard_url', 'https://cognispace.in/login')}" class="button" style="display: block; text-align: center; margin: 20px 0;">View Client Profile</a>
    
    <p class="message" style="margin-top: 20px;">
        <strong>Warm regards,</strong><br>
        Team CogniSpace
    </p>
    """
    
    return {
        "subject": f"✅ Consent Accepted - {data.get('client_name', 'Client')}",
        "html_body": get_base_template(content, "Consent Accepted"),
        "text_body": f"Client {data.get('client_name')} has signed the therapy consent form on {format_ist_datetime(data.get('signature_date'))}."
    }


def template_consent_confirmation_client(data: Dict[str, Any]) -> Dict[str, str]:
    """Template for confirming consent signing to the client"""
    content = f"""
    <p class="greeting">Consent Form Signed Successfully! ✅</p>
    <p class="message">
        Dear <strong>{data.get('client_name', 'Client')}</strong>,
    </p>
    <p class="message">
        Thank you for signing the Informed Consent for Psychological Services. Your consent has been recorded successfully.
    </p>
    
    <div class="info-box" style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 16px;"><strong>📋 Document:</strong> Informed Consent for Psychological Services</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>👨‍⚕️ Therapist:</strong> {data.get('therapist_name', 'Your Therapist')}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>📅 Signed On:</strong> {format_ist_datetime(data.get('signature_date', ''))}</p>
        <p style="margin: 10px 0; font-size: 16px;"><strong>✍️ Method:</strong> {data.get('signature_method', 'Digital').title()} Signature</p>
    </div>
    
    <div class="info-box" style="background: #f5f5f5; border-left: 4px solid #0d5c4d; padding: 15px; margin: 20px 0;">
        <p style="margin: 0 0 10px 0; font-size: 14px; color: #333;">
            <strong>What's Next?</strong>
        </p>
        <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #555;">
            <li>Your therapist can now schedule sessions with you</li>
            <li>You can view your appointments in your dashboard</li>
            <li>All your session records will be maintained securely</li>
        </ul>
    </div>
    
    <a href="{data.get('dashboard_url', 'https://cognispace.in/login')}" class="button" style="display: block; text-align: center; margin: 20px 0;">Go to My Dashboard</a>
    
    <p class="message" style="margin-top: 20px; font-size: 14px; color: #666;">
        If you have any questions about the consent or your therapy sessions, please reach out to your therapist directly.
    </p>
    
    <p class="message" style="margin-top: 20px;">
        <strong>Warm regards,</strong><br>
        Team CogniSpace
    </p>
    """
    
    return {
        "subject": f"✅ Your Consent Has Been Recorded - {data.get('therapist_name', 'CogniSpace')}",
        "html_body": get_base_template(content, "Consent Confirmation"),
        "text_body": f"Dear {data.get('client_name')}, your consent form has been signed successfully on {format_ist_datetime(data.get('signature_date'))}. You can now proceed with therapy sessions with {data.get('therapist_name')}."
    }


def template_daily_summary(data: Dict[str, Any]) -> Dict[str, str]:
    """Enhanced daily summary template with appointments, pending payments, and pending notes"""
    appointments = data.get('appointments', [])
    pending_payments = data.get('pending_payments', [])
    pending_notes = data.get('pending_notes', [])
    is_assistant = data.get('is_assistant', False)
    
    total_appointments = len(appointments)
    total_pending_amount = sum(p.get('amount', 0) for p in pending_payments)
    total_pending_notes = len(pending_notes)
    
    # Appointments section
    if total_appointments == 0:
        appointments_html = """
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <p style="color: #2e7d32; margin: 0;">✨ No appointments scheduled for today.</p>
        </div>
        """
    else:
        appt_items = ""
        for appt in appointments:
            appt_items += f"""
            <div style="background: #fff; padding: 12px 15px; margin: 8px 0; border-radius: 6px; border-left: 4px solid #0d5c4d;">
                <p style="margin: 0 0 5px 0;"><strong>{appt.get('time', 'N/A')}</strong> - {appt.get('client_name', 'N/A')}</p>
                <p style="margin: 0; font-size: 13px; color: #666;">{appt.get('type', 'Session')} • {appt.get('duration', '50')} mins</p>
            </div>
            """
        appointments_html = f"""
        <div style="margin-bottom: 20px;">
            <h4 style="color: #0d5c4d; margin: 0 0 10px 0;">📅 Today's Appointments ({total_appointments})</h4>
            {appt_items}
        </div>
        """
    
    # Pending Payments section
    if len(pending_payments) == 0:
        payments_html = """
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <p style="color: #2e7d32; margin: 0;">✨ No pending payments.</p>
        </div>
        """
    else:
        payment_items = ""
        for pmt in pending_payments[:5]:  # Show max 5
            payment_items += f"""
            <div style="background: #fff; padding: 10px 15px; margin: 6px 0; border-radius: 6px; border-left: 4px solid #ff9800;">
                <p style="margin: 0;"><strong>{pmt.get('client_name', 'N/A')}</strong> - ₹{pmt.get('amount', 0):,.0f}</p>
            </div>
            """
        more_text = f"<p style='font-size: 12px; color: #666;'>...and {len(pending_payments) - 5} more</p>" if len(pending_payments) > 5 else ""
        payments_html = f"""
        <div style="margin-bottom: 20px;">
            <h4 style="color: #ff9800; margin: 0 0 10px 0;">💰 Pending Payments (₹{total_pending_amount:,.0f})</h4>
            {payment_items}
            {more_text}
        </div>
        """
    
    # Pending Notes section (only for therapists)
    notes_html = ""
    if not is_assistant and total_pending_notes > 0:
        note_items = ""
        for note in pending_notes[:5]:  # Show max 5
            note_items += f"""
            <div style="background: #fff; padding: 10px 15px; margin: 6px 0; border-radius: 6px; border-left: 4px solid #9c27b0;">
                <p style="margin: 0;"><strong>{note.get('client_name', 'N/A')}</strong> - {note.get('session_date', 'N/A')}</p>
            </div>
            """
        more_text = f"<p style='font-size: 12px; color: #666;'>...and {len(pending_notes) - 5} more</p>" if len(pending_notes) > 5 else ""
        notes_html = f"""
        <div style="margin-bottom: 20px;">
            <h4 style="color: #9c27b0; margin: 0 0 10px 0;">📝 Pending Session Notes ({total_pending_notes})</h4>
            {note_items}
            {more_text}
        </div>
        """
    elif not is_assistant:
        notes_html = """
        <div style="margin-bottom: 20px;">
            <h4 style="color: #9c27b0; margin: 0 0 10px 0;">📝 Pending Session Notes</h4>
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <p style="color: #2e7d32; margin: 0;">✨ All session notes are up to date!</p>
            </div>
        </div>
        """
    
    content = f"""
    <p class="greeting">Good Morning! ☀️</p>
    <p class="message">
        Here's your daily summary for <strong>{data.get('date', 'today')}</strong>:
    </p>
    
    <div class="info-box" style="background: #f0f9f7; border-color: #0d5c4d; padding: 20px;">
        <div style="display: flex; justify-content: space-around; text-align: center;">
            <div>
                <p style="font-size: 28px; color: #0d5c4d; margin: 0;"><strong>{total_appointments}</strong></p>
                <p style="font-size: 12px; color: #666; margin: 5px 0 0 0;">Appointments</p>
            </div>
            <div>
                <p style="font-size: 28px; color: #ff9800; margin: 0;"><strong>₹{total_pending_amount:,.0f}</strong></p>
                <p style="font-size: 12px; color: #666; margin: 5px 0 0 0;">Pending</p>
            </div>
            {f'<div><p style="font-size: 28px; color: #9c27b0; margin: 0;"><strong>{total_pending_notes}</strong></p><p style="font-size: 12px; color: #666; margin: 5px 0 0 0;">Notes Due</p></div>' if not is_assistant else ''}
        </div>
    </div>
    
    {appointments_html}
    {payments_html}
    {notes_html}
    
    <a href="{data.get('dashboard_url', '#')}" class="button" style="display: block; text-align: center;">Open Dashboard</a>
    """
    
    role_text = "Assistant" if is_assistant else "Therapist"
    return {
        "subject": f"📅 Daily Summary - {data.get('date', 'Today')} | {total_appointments} Appointments, ₹{total_pending_amount:,.0f} Pending",
        "html_body": get_base_template(content, f"Daily Summary - {role_text}"),
        "text_body": f"Good Morning! Today ({data.get('date')}): {total_appointments} appointments, ₹{total_pending_amount:,.0f} pending payments{f', {total_pending_notes} notes due' if not is_assistant else ''}."
    }


# Template registry
EMAIL_TEMPLATES = {
    "welcome_credentials": template_welcome_credentials,
    "therapist_welcome": template_therapist_welcome,
    "client_welcome": template_client_welcome,
    "password_changed": template_password_changed,
    "password_reset": template_password_reset,
    "appointment_confirmation": template_appointment_confirmation,
    "appointment_confirmation_therapist": template_appointment_confirmation_therapist,
    "appointment_reminder": template_appointment_reminder,
    "appointment_cancellation": template_appointment_cancellation,
    "client_self_registration": template_client_self_registration,
    "payment_receipt": template_payment_receipt,
    "payment_received_therapist": template_payment_received_therapist,
    "consent_accepted": template_consent_accepted,
    "consent_confirmation_client": template_consent_confirmation_client,
    "subscription_expiry": template_subscription_expiry,
    "daily_schedule_briefing": template_daily_schedule_briefing,
    "daily_payment_statement": template_daily_payment_statement,
    "daily_summary": template_daily_summary,
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
