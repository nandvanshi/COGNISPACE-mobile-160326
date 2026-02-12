"""
Test Payment Debit/Refund Feature and Notification Services
Tests:
1. POST /api/payments with transaction_type='credit' - creates credit payment
2. POST /api/payments with transaction_type='debit' - creates debit/refund entry
3. GET /api/payments - returns transaction_type field
4. GET /api/payments/reports/detailed - returns credit_amount, debit_amount, net_amount
5. Email templates exist: consent_accepted, daily_summary
6. NotificationService methods exist: send_consent_accepted_notification, send_daily_summary
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPaymentDebitFeature:
    """Test payment debit/refund feature"""
    
    @pytest.fixture(scope="class")
    def therapist_auth(self):
        """Get therapist authentication token"""
        # First login as admin to get list of therapists
        admin_response = requests.post(
            f"{BASE_URL}/api/auth/super-admin-login",
            json={"username": "admin", "password": "admin123"}
        )
        if admin_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = admin_response.json()["token"]
        
        # Get therapists (approved status, not active)
        therapists_response = requests.get(
            f"{BASE_URL}/api/admin/therapists",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if therapists_response.status_code != 200:
            pytest.skip("Failed to get therapists")
        
        therapists = therapists_response.json()
        # Filter for approved therapists with active subscription
        active_therapists = [t for t in therapists if t.get("status") == "approved" and t.get("subscription_status") == "active"]
        
        if not active_therapists:
            pytest.skip("No active therapists found")
        
        therapist = active_therapists[0]
        therapist_mobile = therapist.get("mobile")
        
        # Login as therapist (uses identifier field, not mobile)
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": therapist_mobile, "password": "Test@123"}
        )
        
        if login_response.status_code != 200:
            # Try default password
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"identifier": therapist_mobile, "password": "password123"}
            )
        
        if login_response.status_code != 200:
            pytest.skip(f"Therapist login failed: {login_response.text}")
        
        return {
            "token": login_response.json()["token"],
            "therapist_id": therapist["id"],
            "therapist_mobile": therapist_mobile
        }
    
    @pytest.fixture(scope="class")
    def test_client_id(self, therapist_auth):
        """Get or create a test client"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        # Get existing clients
        clients_response = requests.get(
            f"{BASE_URL}/api/clients",
            headers=headers
        )
        
        if clients_response.status_code == 200 and clients_response.json():
            return clients_response.json()[0]["id"]
        
        # Create a test client if none exist
        unique_id = str(uuid.uuid4())[:8]
        client_data = {
            "full_name": f"TEST_PaymentClient_{unique_id}",
            "mobile": f"99999{unique_id[:5]}",
            "email": f"test_payment_{unique_id}@test.com"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/clients",
            json=client_data,
            headers=headers
        )
        
        if create_response.status_code in [200, 201]:
            return create_response.json()["id"]
        
        pytest.skip("Could not get or create test client")
    
    def test_create_credit_payment(self, therapist_auth, test_client_id):
        """Test creating a credit payment"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        payment_data = {
            "client_id": test_client_id,
            "amount": 1000.00,
            "payment_method": "cash",
            "transaction_type": "credit",
            "notes": "TEST_Credit payment for testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments",
            json=payment_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["amount"] == 1000.00
        assert data["transaction_type"] == "credit", f"Expected 'credit', got {data.get('transaction_type')}"
        assert "id" in data
        assert "bill_number" in data
        
        # Store payment ID for cleanup
        self.__class__.credit_payment_id = data["id"]
    
    def test_create_debit_payment(self, therapist_auth, test_client_id):
        """Test creating a debit/refund payment"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        payment_data = {
            "client_id": test_client_id,
            "amount": 500.00,
            "payment_method": "upi",
            "transaction_type": "debit",
            "notes": "TEST_Refund for cancelled session"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments",
            json=payment_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["amount"] == 500.00
        assert data["transaction_type"] == "debit", f"Expected 'debit', got {data.get('transaction_type')}"
        assert "id" in data
        
        # Store payment ID for cleanup
        self.__class__.debit_payment_id = data["id"]
    
    def test_get_payments_includes_transaction_type(self, therapist_auth):
        """Test that GET /api/payments returns transaction_type field"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/payments",
            headers=headers
        )
        
        assert response.status_code == 200
        
        payments = response.json()
        assert len(payments) > 0, "No payments found"
        
        # Check that transaction_type is present in response
        for payment in payments:
            assert "transaction_type" in payment, f"transaction_type missing in payment {payment.get('id')}"
            assert payment["transaction_type"] in ["credit", "debit"], f"Invalid transaction_type: {payment['transaction_type']}"
    
    def test_detailed_report_includes_credit_debit_amounts(self, therapist_auth):
        """Test that /api/payments/reports/detailed returns credit_amount, debit_amount, net_amount"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/payments/reports/detailed",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "summary" in data, "Missing 'summary' in response"
        
        summary = data["summary"]
        assert "credit_amount" in summary, "Missing 'credit_amount' in summary"
        assert "debit_amount" in summary, "Missing 'debit_amount' in summary"
        assert "net_amount" in summary, "Missing 'net_amount' in summary"
        
        # Verify net_amount calculation
        expected_net = summary["credit_amount"] - summary["debit_amount"]
        assert summary["net_amount"] == expected_net, f"Net amount mismatch: {summary['net_amount']} != {expected_net}"
    
    def test_payment_default_transaction_type_is_credit(self, therapist_auth, test_client_id):
        """Test that payment without transaction_type defaults to credit"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        payment_data = {
            "client_id": test_client_id,
            "amount": 200.00,
            "payment_method": "cash",
            # No transaction_type specified
            "notes": "TEST_Default transaction type test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments",
            json=payment_data,
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["transaction_type"] == "credit", f"Default should be 'credit', got {data.get('transaction_type')}"
        
        # Store for cleanup
        self.__class__.default_payment_id = data["id"]
    
    def test_get_single_payment_includes_transaction_type(self, therapist_auth):
        """Test that GET /api/payments/{id} returns transaction_type"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        # Use the credit payment we created
        payment_id = getattr(self.__class__, 'credit_payment_id', None)
        if not payment_id:
            pytest.skip("No credit payment created")
        
        response = requests.get(
            f"{BASE_URL}/api/payments/{payment_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "transaction_type" in data
        assert data["transaction_type"] == "credit"


class TestEmailTemplates:
    """Test that required email templates exist"""
    
    def test_consent_accepted_template_exists(self):
        """Verify consent_accepted template is registered"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from services.email.templates import EMAIL_TEMPLATES, get_email_template
        
        assert "consent_accepted" in EMAIL_TEMPLATES, "consent_accepted template not in registry"
        
        # Test template generation
        test_data = {
            "client_name": "Test Client",
            "therapist_name": "Dr. Test",
            "signature_date": "2026-01-15T10:00:00Z",
            "signature_method": "digital",
            "consent_summary": "Informed Consent",
            "dashboard_url": "https://test.com"
        }
        
        result = get_email_template("consent_accepted", test_data)
        assert "subject" in result
        assert "html_body" in result
        assert "text_body" in result
        assert "Consent" in result["subject"] or "consent" in result["subject"].lower()
    
    def test_daily_summary_template_exists(self):
        """Verify daily_summary template is registered"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from services.email.templates import EMAIL_TEMPLATES, get_email_template
        
        assert "daily_summary" in EMAIL_TEMPLATES, "daily_summary template not in registry"
        
        # Test template generation
        test_data = {
            "date": "2026-01-15",
            "appointments": [
                {"client_name": "Client 1", "time": "10:00 AM"},
                {"client_name": "Client 2", "time": "2:00 PM"}
            ],
            "pending_payments": [
                {"client_name": "Client 3", "amount": 1000}
            ],
            "pending_notes": [
                {"client_name": "Client 4", "appointment_date": "2026-01-14"}
            ],
            "is_assistant": False,
            "dashboard_url": "https://test.com"
        }
        
        result = get_email_template("daily_summary", test_data)
        assert "subject" in result
        assert "html_body" in result
        assert "text_body" in result


class TestNotificationServiceMethods:
    """Test that NotificationService has required methods"""
    
    def test_send_consent_accepted_notification_exists(self):
        """Verify send_consent_accepted_notification method exists"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from services.notification_service import NotificationService
        
        assert hasattr(NotificationService, 'send_consent_accepted_notification'), \
            "NotificationService missing send_consent_accepted_notification method"
        
        # Verify it's a callable
        method = getattr(NotificationService, 'send_consent_accepted_notification')
        assert callable(method), "send_consent_accepted_notification is not callable"
    
    def test_send_daily_summary_exists(self):
        """Verify send_daily_summary method exists"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from services.notification_service import NotificationService
        
        assert hasattr(NotificationService, 'send_daily_summary'), \
            "NotificationService missing send_daily_summary method"
        
        # Verify it's a callable
        method = getattr(NotificationService, 'send_daily_summary')
        assert callable(method), "send_daily_summary is not callable"


class TestPaymentReportsWithTransactionType:
    """Test payment reports include transaction type data"""
    
    @pytest.fixture(scope="class")
    def therapist_auth(self):
        """Get therapist authentication token"""
        admin_response = requests.post(
            f"{BASE_URL}/api/auth/super-admin-login",
            json={"username": "admin", "password": "admin123"}
        )
        if admin_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = admin_response.json()["token"]
        
        # Get therapists (approved status, not active)
        therapists_response = requests.get(
            f"{BASE_URL}/api/admin/therapists",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if therapists_response.status_code != 200:
            pytest.skip("Failed to get therapists")
        
        therapists = therapists_response.json()
        # Filter for approved therapists with active subscription
        active_therapists = [t for t in therapists if t.get("status") == "approved" and t.get("subscription_status") == "active"]
        
        if not active_therapists:
            pytest.skip("No active therapists found")
        
        therapist = active_therapists[0]
        therapist_mobile = therapist.get("mobile")
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": therapist_mobile, "password": "Test@123"}
        )
        
        if login_response.status_code != 200:
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"identifier": therapist_mobile, "password": "password123"}
            )
        
        if login_response.status_code != 200:
            pytest.skip(f"Therapist login failed")
        
        return {"token": login_response.json()["token"]}
    
    def test_detailed_report_payments_include_transaction_type(self, therapist_auth):
        """Test that payments in detailed report include transaction_type"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/payments/reports/detailed",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        payments = data.get("payments", [])
        
        for payment in payments:
            assert "transaction_type" in payment, f"transaction_type missing in payment {payment.get('id')}"
    
    def test_by_payment_method_includes_credit_debit(self, therapist_auth):
        """Test that by_payment_method breakdown includes credit/debit"""
        headers = {"Authorization": f"Bearer {therapist_auth['token']}"}
        
        response = requests.get(
            f"{BASE_URL}/api/payments/reports/detailed",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        by_method = data.get("by_payment_method", {})
        
        # Each method should have credit and debit breakdown
        for method, stats in by_method.items():
            assert "credit" in stats, f"Missing 'credit' in {method} stats"
            assert "debit" in stats, f"Missing 'debit' in {method} stats"


# Cleanup test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_payments():
    """Cleanup test payments after all tests"""
    yield
    
    # Cleanup would happen here if needed
    # For now, test payments are left for manual review
