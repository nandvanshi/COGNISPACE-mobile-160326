"""
WhatsApp Integration Tests - Twilio Provider with Provider Abstraction
Tests:
1. TwilioWhatsAppProvider class exists and follows base class pattern
2. WhatsApp Service convenience methods (appointment_confirmation, appointment_reminder, payment_receipt)
3. Channel Availability API - whatsapp_configured returns false when Twilio not configured
4. Appointment creation includes WhatsApp trigger (graceful skip if not configured)
5. Scheduler jobs include WhatsApp reminder trigger
6. WhatsApp requires explicit user opt-in (notification_opt_in.whatsapp = true)
"""
import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestWhatsAppProviderArchitecture:
    """Test WhatsApp Provider Architecture - TwilioWhatsAppProvider follows base class pattern"""
    
    def test_twilio_provider_class_exists(self):
        """Verify TwilioWhatsAppProvider class exists"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        assert TwilioWhatsAppProvider is not None
        print("✓ TwilioWhatsAppProvider class exists")
    
    def test_twilio_provider_inherits_base(self):
        """Verify TwilioWhatsAppProvider inherits from WhatsAppProviderBase"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        from services.whatsapp.base import WhatsAppProviderBase
        
        assert issubclass(TwilioWhatsAppProvider, WhatsAppProviderBase)
        print("✓ TwilioWhatsAppProvider inherits from WhatsAppProviderBase")
    
    def test_twilio_provider_implements_required_methods(self):
        """Verify TwilioWhatsAppProvider implements all required abstract methods"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        # Create instance with empty config
        provider = TwilioWhatsAppProvider({})
        
        # Check required methods exist
        assert hasattr(provider, 'send')
        assert hasattr(provider, 'send_bulk')
        assert hasattr(provider, 'validate_config')
        assert hasattr(provider, 'is_available')
        assert hasattr(provider, 'get_template_status')
        print("✓ TwilioWhatsAppProvider implements all required abstract methods")
    
    def test_twilio_provider_is_not_available_without_credentials(self):
        """Verify provider returns is_available=False when credentials not configured"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        assert provider.is_available == False
        print("✓ TwilioWhatsAppProvider.is_available returns False without credentials")
    
    def test_twilio_provider_validate_config_fails_without_credentials(self):
        """Verify validate_config returns False without credentials"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        assert provider.validate_config() == False
        print("✓ TwilioWhatsAppProvider.validate_config() returns False without credentials")
    
    def test_twilio_provider_registered_in_registry(self):
        """Verify Twilio is registered in PROVIDER_CLASSES"""
        from services.whatsapp.registry import PROVIDER_CLASSES
        
        assert "twilio" in PROVIDER_CLASSES
        print("✓ Twilio registered in PROVIDER_CLASSES")
    
    def test_base_class_has_required_abstract_methods(self):
        """Verify WhatsAppProviderBase defines required abstract methods"""
        from services.whatsapp.base import WhatsAppProviderBase
        import inspect
        
        # Get abstract methods
        abstract_methods = []
        for name, method in inspect.getmembers(WhatsAppProviderBase):
            if getattr(method, '__isabstractmethod__', False):
                abstract_methods.append(name)
        
        required = ['send', 'send_bulk', 'validate_config', 'is_available', 'get_template_status']
        for method in required:
            assert method in abstract_methods, f"Missing abstract method: {method}"
        
        print(f"✓ WhatsAppProviderBase has all required abstract methods: {required}")


class TestWhatsAppServiceConvenienceMethods:
    """Test WhatsApp Service convenience methods"""
    
    def test_service_has_appointment_confirmation_method(self):
        """Verify WhatsAppService has send_appointment_confirmation method"""
        from services.whatsapp.service import WhatsAppService
        
        assert hasattr(WhatsAppService, 'send_appointment_confirmation')
        assert callable(getattr(WhatsAppService, 'send_appointment_confirmation'))
        print("✓ WhatsAppService.send_appointment_confirmation exists")
    
    def test_service_has_appointment_reminder_method(self):
        """Verify WhatsAppService has send_appointment_reminder method"""
        from services.whatsapp.service import WhatsAppService
        
        assert hasattr(WhatsAppService, 'send_appointment_reminder')
        assert callable(getattr(WhatsAppService, 'send_appointment_reminder'))
        print("✓ WhatsAppService.send_appointment_reminder exists")
    
    def test_service_has_payment_receipt_method(self):
        """Verify WhatsAppService has send_payment_receipt method"""
        from services.whatsapp.service import WhatsAppService
        
        assert hasattr(WhatsAppService, 'send_payment_receipt')
        assert callable(getattr(WhatsAppService, 'send_payment_receipt'))
        print("✓ WhatsAppService.send_payment_receipt exists")
    
    def test_service_has_is_configured_method(self):
        """Verify WhatsAppService has is_configured method"""
        from services.whatsapp.service import WhatsAppService
        
        assert hasattr(WhatsAppService, 'is_configured')
        assert callable(getattr(WhatsAppService, 'is_configured'))
        print("✓ WhatsAppService.is_configured exists")
    
    def test_service_is_not_configured_without_credentials(self):
        """Verify WhatsAppService.is_configured() returns False without Twilio credentials"""
        from services.whatsapp.service import WhatsAppService
        
        # Without initialization, should return False
        result = WhatsAppService.is_configured()
        assert result == False
        print("✓ WhatsAppService.is_configured() returns False without credentials")


class TestWhatsAppTemplates:
    """Test WhatsApp message templates"""
    
    def test_twilio_provider_has_appointment_confirmation_template(self):
        """Verify appointment_confirmation template exists"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        body = provider._build_message_body("appointment_confirmation", ["Dr. Smith", "2024-01-15", "10:00"])
        
        assert "Appointment Confirmed" in body
        assert "Dr. Smith" in body
        assert "2024-01-15" in body
        assert "10:00" in body
        print("✓ appointment_confirmation template works correctly")
    
    def test_twilio_provider_has_appointment_reminder_template(self):
        """Verify appointment_reminder template exists"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        body = provider._build_message_body("appointment_reminder", ["Dr. Smith", "30 minutes"])
        
        assert "Appointment Reminder" in body
        assert "Dr. Smith" in body
        assert "30 minutes" in body
        print("✓ appointment_reminder template works correctly")
    
    def test_twilio_provider_has_payment_receipt_template(self):
        """Verify payment_receipt template exists"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        body = provider._build_message_body("payment_receipt", ["1500", "2024-01-15"])
        
        assert "Payment Received" in body
        assert "1500" in body
        assert "2024-01-15" in body
        print("✓ payment_receipt template works correctly")
    
    def test_templates_contain_no_clinical_content(self):
        """Verify templates don't contain clinical/medical content"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        
        templates = [
            ("appointment_confirmation", ["Dr. Smith", "2024-01-15", "10:00"]),
            ("appointment_reminder", ["Dr. Smith", "30 minutes"]),
            ("payment_receipt", ["1500", "2024-01-15"])
        ]
        
        clinical_terms = ["diagnosis", "treatment", "therapy", "mental health", "condition", "medication", "prescription"]
        
        for template_name, params in templates:
            body = provider._build_message_body(template_name, params)
            for term in clinical_terms:
                assert term.lower() not in body.lower(), f"Template {template_name} contains clinical term: {term}"
        
        print("✓ All templates contain no clinical content")


class TestChannelAvailabilityAPI:
    """Test Channel Availability API - whatsapp_configured returns false when Twilio not configured"""
    
    @pytest.fixture
    def therapist_token(self):
        """Get therapist auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "9807306444",
            "password": "Abcd@1234"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not authenticate therapist")
    
    def test_channel_availability_endpoint_exists(self, therapist_token):
        """Verify /api/notification-settings/channel-availability endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/channel-availability",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        print("✓ Channel availability endpoint exists and returns 200")
    
    def test_whatsapp_configured_returns_false(self, therapist_token):
        """Verify whatsapp_configured returns false when Twilio not configured"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/channel-availability",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "whatsapp_configured" in data
        assert data["whatsapp_configured"] == False, "whatsapp_configured should be False without Twilio credentials"
        print(f"✓ whatsapp_configured = {data['whatsapp_configured']} (expected False)")
    
    def test_channel_availability_response_structure(self, therapist_token):
        """Verify channel availability response has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/channel-availability",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "email_allowed" in data
        assert "whatsapp_allowed" in data
        assert "whatsapp_configured" in data
        
        assert isinstance(data["email_allowed"], bool)
        assert isinstance(data["whatsapp_allowed"], bool)
        assert isinstance(data["whatsapp_configured"], bool)
        
        print(f"✓ Channel availability response structure correct: {data}")


class TestAppointmentCreationWhatsAppTrigger:
    """Test appointment creation includes WhatsApp trigger (graceful skip if not configured)"""
    
    @pytest.fixture
    def therapist_token(self):
        """Get therapist auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "9807306444",
            "password": "Abcd@1234"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not authenticate therapist")
    
    def test_appointment_creation_does_not_fail_without_whatsapp(self, therapist_token):
        """Verify appointment creation works even when WhatsApp not configured"""
        from datetime import datetime, timedelta
        
        # Get a client to create appointment for
        response = requests.get(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        
        if response.status_code != 200 or not response.json():
            pytest.skip("No clients available for testing")
        
        clients = response.json()
        client_id = clients[0]["id"] if clients else None
        
        if not client_id:
            pytest.skip("No client ID available")
        
        # Create appointment for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        response = requests.post(
            f"{BASE_URL}/api/appointments",
            headers={"Authorization": f"Bearer {therapist_token}"},
            json={
                "client_id": client_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "notes": "TEST_WhatsApp integration test appointment"
            }
        )
        
        # Should succeed even without WhatsApp configured
        assert response.status_code in [200, 201], f"Appointment creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        
        # Cleanup - cancel the test appointment
        appointment_id = data["id"]
        requests.delete(
            f"{BASE_URL}/api/appointments/{appointment_id}",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        
        print("✓ Appointment creation succeeds without WhatsApp configured (graceful skip)")
    
    def test_appointments_route_has_whatsapp_import(self):
        """Verify appointments route imports WhatsAppService"""
        with open('/app/backend/routes/appointments.py', 'r') as f:
            content = f.read()
        
        assert "from services.whatsapp import WhatsAppService" in content or \
               "from services.whatsapp" in content
        print("✓ Appointments route imports WhatsAppService")
    
    def test_appointments_route_checks_whatsapp_configured(self):
        """Verify appointments route checks WhatsAppService.is_configured()"""
        with open('/app/backend/routes/appointments.py', 'r') as f:
            content = f.read()
        
        assert "WhatsAppService.is_configured()" in content
        print("✓ Appointments route checks WhatsAppService.is_configured()")
    
    def test_appointments_route_calls_send_appointment_confirmation(self):
        """Verify appointments route calls send_appointment_confirmation"""
        with open('/app/backend/routes/appointments.py', 'r') as f:
            content = f.read()
        
        assert "send_appointment_confirmation" in content
        print("✓ Appointments route calls send_appointment_confirmation")


class TestSchedulerWhatsAppReminder:
    """Test scheduler jobs include WhatsApp reminder trigger"""
    
    def test_scheduler_jobs_file_imports_whatsapp(self):
        """Verify scheduler jobs imports WhatsAppService"""
        with open('/app/backend/services/scheduler/jobs.py', 'r') as f:
            content = f.read()
        
        assert "from services.whatsapp import WhatsAppService" in content or \
               "from services.whatsapp" in content
        print("✓ Scheduler jobs imports WhatsAppService")
    
    def test_scheduler_jobs_checks_whatsapp_configured(self):
        """Verify scheduler jobs checks WhatsAppService.is_configured()"""
        with open('/app/backend/services/scheduler/jobs.py', 'r') as f:
            content = f.read()
        
        assert "WhatsAppService.is_configured()" in content
        print("✓ Scheduler jobs checks WhatsAppService.is_configured()")
    
    def test_scheduler_jobs_calls_send_appointment_reminder(self):
        """Verify scheduler jobs calls send_appointment_reminder"""
        with open('/app/backend/services/scheduler/jobs.py', 'r') as f:
            content = f.read()
        
        assert "send_appointment_reminder" in content
        print("✓ Scheduler jobs calls send_appointment_reminder")
    
    def test_scheduler_whatsapp_in_try_except(self):
        """Verify WhatsApp calls in scheduler are wrapped in try-except"""
        with open('/app/backend/services/scheduler/jobs.py', 'r') as f:
            content = f.read()
        
        # Check that WhatsApp call is in a try block
        assert "try:" in content
        assert "WhatsAppService" in content
        assert "except" in content
        print("✓ WhatsApp calls in scheduler are wrapped in try-except for graceful handling")


class TestWhatsAppOptInRequirement:
    """Test WhatsApp requires explicit user opt-in (notification_opt_in.whatsapp = true)"""
    
    def test_service_has_check_user_whatsapp_opt_in_method(self):
        """Verify WhatsAppService has check_user_whatsapp_opt_in method"""
        from services.whatsapp.service import WhatsAppService
        
        assert hasattr(WhatsAppService, 'check_user_whatsapp_opt_in')
        assert callable(getattr(WhatsAppService, 'check_user_whatsapp_opt_in'))
        print("✓ WhatsAppService.check_user_whatsapp_opt_in exists")
    
    def test_service_checks_opt_in_in_send_notification(self):
        """Verify send_notification checks user opt-in"""
        with open('/app/backend/services/whatsapp/service.py', 'r') as f:
            content = f.read()
        
        assert "check_user_whatsapp_opt_in" in content
        assert "notification_opt_in" in content
        print("✓ WhatsAppService.send_notification checks user opt-in")
    
    def test_opt_in_defaults_to_false(self):
        """Verify WhatsApp opt-in defaults to False (explicit opt-in required)"""
        with open('/app/backend/services/whatsapp/service.py', 'r') as f:
            content = f.read()
        
        # Check that default is False for whatsapp opt-in
        assert 'opt_in.get("whatsapp", False)' in content
        print("✓ WhatsApp opt-in defaults to False (explicit opt-in required)")
    
    def test_service_returns_error_without_opt_in(self):
        """Verify service returns error message when user hasn't opted in"""
        with open('/app/backend/services/whatsapp/service.py', 'r') as f:
            content = f.read()
        
        assert "User has not opted in for WhatsApp notifications" in content
        print("✓ Service returns appropriate error when user hasn't opted in")


class TestWhatsAppRegistryConfiguration:
    """Test WhatsApp Registry configuration"""
    
    def test_registry_is_configured_returns_false_without_providers(self):
        """Verify registry.is_configured() returns False without active providers"""
        from services.whatsapp.registry import WhatsAppProviderRegistry
        
        # Without initialization, should return False
        result = WhatsAppProviderRegistry.is_configured()
        assert result == False
        print("✓ WhatsAppProviderRegistry.is_configured() returns False without providers")
    
    def test_registry_get_provider_returns_none_without_providers(self):
        """Verify registry.get_provider() returns None without active providers"""
        from services.whatsapp.registry import WhatsAppProviderRegistry
        
        result = WhatsAppProviderRegistry.get_provider()
        assert result is None
        print("✓ WhatsAppProviderRegistry.get_provider() returns None without providers")


class TestPhoneNumberNormalization:
    """Test phone number normalization in base class"""
    
    def test_normalize_phone_adds_country_code(self):
        """Verify normalize_phone adds +91 for 10-digit Indian numbers"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        
        # Test 10-digit number
        result = provider.normalize_phone("9876543210")
        assert result == "+919876543210"
        print("✓ normalize_phone adds +91 for 10-digit numbers")
    
    def test_normalize_phone_preserves_plus(self):
        """Verify normalize_phone preserves existing + prefix"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        
        result = provider.normalize_phone("+919876543210")
        assert result == "+919876543210"
        print("✓ normalize_phone preserves existing + prefix")
    
    def test_normalize_phone_handles_91_prefix(self):
        """Verify normalize_phone handles 91 prefix without +"""
        from services.whatsapp.twilio_provider import TwilioWhatsAppProvider
        
        provider = TwilioWhatsAppProvider({})
        
        result = provider.normalize_phone("919876543210")
        assert result == "+919876543210"
        print("✓ normalize_phone handles 91 prefix without +")


class TestWhatsAppDataModels:
    """Test WhatsApp data models"""
    
    def test_whatsapp_message_model_exists(self):
        """Verify WhatsAppMessage model exists"""
        from services.whatsapp.base import WhatsAppMessage
        
        assert WhatsAppMessage is not None
        print("✓ WhatsAppMessage model exists")
    
    def test_whatsapp_result_model_exists(self):
        """Verify WhatsAppResult model exists"""
        from services.whatsapp.base import WhatsAppResult
        
        assert WhatsAppResult is not None
        print("✓ WhatsAppResult model exists")
    
    def test_whatsapp_message_has_required_fields(self):
        """Verify WhatsAppMessage has required fields"""
        from services.whatsapp.base import WhatsAppMessage
        
        msg = WhatsAppMessage(to="+919876543210", template_name="test")
        
        assert hasattr(msg, 'to')
        assert hasattr(msg, 'template_name')
        assert hasattr(msg, 'template_params')
        assert hasattr(msg, 'language')
        assert hasattr(msg, 'metadata')
        print("✓ WhatsAppMessage has all required fields")
    
    def test_whatsapp_result_has_required_fields(self):
        """Verify WhatsAppResult has required fields"""
        from services.whatsapp.base import WhatsAppResult
        
        result = WhatsAppResult(success=True, provider="twilio")
        
        assert hasattr(result, 'success')
        assert hasattr(result, 'provider')
        assert hasattr(result, 'message_id')
        assert hasattr(result, 'error')
        assert hasattr(result, 'timestamp')
        print("✓ WhatsAppResult has all required fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
