"""
Backend API Tests for Subscription Expiry Read-Only Mode
Tests the feature: When subscription is expired/cancelled:
- Allow read operations (GET)
- Block write operations (POST/PUT/DELETE) with 403 error
- GET /api/auth/subscription-status returns is_read_only: true for expired
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "admin123"
TEST_THERAPIST_MOBILE = "1234567890"
TEST_THERAPIST_PASSWORD = "TestPass123"


@pytest.fixture(scope="module")
def admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
        "username": SUPER_ADMIN_USERNAME,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Could not get admin token: {response.text}")
    return response.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


def set_subscription_status(status: str):
    """Helper to set subscription status via mongosh"""
    import subprocess
    cmd = f'mongosh mongodb://localhost:27017/haven_therapy --eval "db.users.updateOne({{mobile: \'{TEST_THERAPIST_MOBILE}\'}}, {{\\$set: {{subscription_status: \'{status}\'}}}});" --quiet'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0


def get_therapist_token():
    """Get therapist token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": TEST_THERAPIST_MOBILE,
        "password": TEST_THERAPIST_PASSWORD
    })
    if response.status_code != 200:
        return None
    return response.json()["token"]


# ============= LOGIN TESTS =============

class TestExpiredTherapistLogin:
    """Test that expired subscription therapist can still login"""
    
    def test_login_works_for_expired_subscription(self):
        """Expired subscription therapist should be able to login"""
        # Set subscription to expired
        assert set_subscription_status("expired"), "Failed to set subscription status"
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": TEST_THERAPIST_MOBILE,
            "password": TEST_THERAPIST_PASSWORD
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["role"] == "therapist", "User role should be therapist"
        
        print(f"✓ Expired subscription therapist can login successfully")
        
        # Reset to trial for other tests
        set_subscription_status("trial")
    
    def test_login_works_for_trial_subscription(self):
        """Trial subscription therapist should be able to login"""
        set_subscription_status("trial")
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": TEST_THERAPIST_MOBILE,
            "password": TEST_THERAPIST_PASSWORD
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Trial subscription therapist can login successfully")
    
    def test_login_works_for_active_subscription(self):
        """Active subscription therapist should be able to login"""
        set_subscription_status("active")
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": TEST_THERAPIST_MOBILE,
            "password": TEST_THERAPIST_PASSWORD
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Active subscription therapist can login successfully")
        
        # Reset to trial
        set_subscription_status("trial")


# ============= SUBSCRIPTION STATUS ENDPOINT TESTS =============

class TestSubscriptionStatusEndpoint:
    """Test GET /api/auth/subscription-status endpoint"""
    
    def test_subscription_status_returns_read_only_true_for_expired(self):
        """GET /api/auth/subscription-status should return is_read_only: true for expired"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "is_read_only" in data, "Response should contain is_read_only"
        assert data["is_read_only"] == True, f"is_read_only should be True for expired, got {data['is_read_only']}"
        assert data["subscription_status"] == "expired", f"subscription_status should be 'expired', got {data['subscription_status']}"
        
        print(f"✓ Subscription status returns is_read_only: true for expired")
        
        # Reset
        set_subscription_status("trial")
    
    def test_subscription_status_returns_read_only_true_for_cancelled(self):
        """GET /api/auth/subscription-status should return is_read_only: true for cancelled"""
        set_subscription_status("cancelled")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["is_read_only"] == True, f"is_read_only should be True for cancelled, got {data['is_read_only']}"
        
        print(f"✓ Subscription status returns is_read_only: true for cancelled")
        
        # Reset
        set_subscription_status("trial")
    
    def test_subscription_status_returns_read_only_false_for_trial(self):
        """GET /api/auth/subscription-status should return is_read_only: false for trial"""
        set_subscription_status("trial")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["is_read_only"] == False, f"is_read_only should be False for trial, got {data['is_read_only']}"
        
        print(f"✓ Subscription status returns is_read_only: false for trial")
    
    def test_subscription_status_returns_read_only_false_for_active(self):
        """GET /api/auth/subscription-status should return is_read_only: false for active"""
        set_subscription_status("active")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["is_read_only"] == False, f"is_read_only should be False for active, got {data['is_read_only']}"
        
        print(f"✓ Subscription status returns is_read_only: false for active")
        
        # Reset
        set_subscription_status("trial")


# ============= READ OPERATIONS FOR EXPIRED THERAPIST =============

class TestReadOperationsForExpiredTherapist:
    """Test that READ operations work for expired subscription therapist"""
    
    def test_get_clients_works_for_expired(self):
        """GET /api/clients should work for expired subscription therapist"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/clients works for expired therapist (returned {len(data)} clients)")
        
        # Reset
        set_subscription_status("trial")
    
    def test_get_session_notes_works_for_expired(self):
        """GET /api/session-notes should work for expired subscription therapist"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/session-notes", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/session-notes works for expired therapist")
        
        # Reset
        set_subscription_status("trial")
    
    def test_get_appointments_works_for_expired(self):
        """GET /api/appointments should work for expired subscription therapist"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/appointments", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/appointments works for expired therapist")
        
        # Reset
        set_subscription_status("trial")


# ============= WRITE OPERATIONS BLOCKED FOR EXPIRED THERAPIST =============

class TestWriteOperationsBlockedForExpiredTherapist:
    """Test that WRITE operations are blocked with 403 for expired subscription therapist"""
    
    def test_post_clients_blocked_for_expired(self):
        """POST /api/clients should return 403 for expired subscription therapist"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "mobile": "9876543210",
            "full_name": "Test Client",
            "password": "TestPass123"
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        # Verify error message mentions subscription/read-only
        data = response.json()
        assert "detail" in data, "Response should contain detail"
        assert "subscription" in data["detail"].lower() or "read-only" in data["detail"].lower() or "expired" in data["detail"].lower(), \
            f"Error message should mention subscription/read-only/expired: {data['detail']}"
        
        print(f"✓ POST /api/clients blocked with 403 for expired therapist")
        
        # Reset
        set_subscription_status("trial")
    
    def test_post_appointments_blocked_for_expired(self):
        """POST /api/appointments should return 403 for expired subscription therapist"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "client_id": "test-client-id",
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
            "notes": "Test appointment"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=payload, headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        print(f"✓ POST /api/appointments blocked with 403 for expired therapist")
        
        # Reset
        set_subscription_status("trial")
    
    def test_post_session_notes_blocked_for_expired(self):
        """POST /api/session-notes should return 403 for expired subscription therapist"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "client_id": "test-client-id",
            "template_type": "SOAP",
            "subjective": "Test subjective",
            "objective": "Test objective",
            "assessment": "Test assessment",
            "plan": "Test plan"
        }
        
        response = requests.post(f"{BASE_URL}/api/session-notes", json=payload, headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        print(f"✓ POST /api/session-notes blocked with 403 for expired therapist")
        
        # Reset
        set_subscription_status("trial")
    
    def test_post_messages_blocked_for_expired(self):
        """POST /api/messages should return 403 for expired subscription therapist"""
        set_subscription_status("expired")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "recipient_id": "test-recipient-id",
            "content": "Test message"
        }
        
        response = requests.post(f"{BASE_URL}/api/messages", json=payload, headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        print(f"✓ POST /api/messages blocked with 403 for expired therapist")
        
        # Reset
        set_subscription_status("trial")


# ============= WRITE OPERATIONS WORK FOR ACTIVE/TRIAL THERAPIST =============

class TestWriteOperationsWorkForActiveTherapist:
    """Test that WRITE operations work for active/trial subscription therapist"""
    
    def test_post_clients_works_for_trial(self):
        """POST /api/clients should work for trial subscription therapist"""
        set_subscription_status("trial")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        import random
        unique_mobile = f"98{random.randint(10000000, 99999999)}"
        
        payload = {
            "mobile": unique_mobile,
            "full_name": f"TEST_Trial Client {uuid.uuid4().hex[:6]}",
            "password": "TestPass123"
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=headers)
        
        # Should be 200 (success) or 400 (validation error like duplicate mobile) - NOT 403
        assert response.status_code != 403, f"Should not get 403 for trial therapist: {response.text}"
        
        if response.status_code == 200:
            print(f"✓ POST /api/clients works for trial therapist (created client)")
        else:
            print(f"✓ POST /api/clients accessible for trial therapist (status: {response.status_code})")
    
    def test_post_clients_works_for_active(self):
        """POST /api/clients should work for active subscription therapist"""
        set_subscription_status("active")
        
        token = get_therapist_token()
        assert token, "Failed to get therapist token"
        
        headers = {"Authorization": f"Bearer {token}"}
        import random
        unique_mobile = f"97{random.randint(10000000, 99999999)}"
        
        payload = {
            "mobile": unique_mobile,
            "full_name": f"TEST_Active Client {uuid.uuid4().hex[:6]}",
            "password": "TestPass123"
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=payload, headers=headers)
        
        # Should be 200 (success) or 400 (validation error) - NOT 403
        assert response.status_code != 403, f"Should not get 403 for active therapist: {response.text}"
        
        if response.status_code == 200:
            print(f"✓ POST /api/clients works for active therapist (created client)")
        else:
            print(f"✓ POST /api/clients accessible for active therapist (status: {response.status_code})")
        
        # Reset
        set_subscription_status("trial")


# ============= CLEANUP =============

@pytest.fixture(scope="module", autouse=True)
def cleanup(request):
    """Ensure subscription status is reset after all tests"""
    def reset_status():
        set_subscription_status("trial")
        print("\n✓ Reset subscription status to 'trial'")
    
    request.addfinalizer(reset_status)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
