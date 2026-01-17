"""
Backend API Tests for TherapyFlow Admin and Auth Features
Tests P0 Fix: Super Admin Approval Flow
Tests P1 Fix: Client records without mobile field
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "admin123"
TEST_THERAPIST_MOBILE = "9999999999"  # Test mobile
TEST_THERAPIST_PASSWORD = "TestPass123"


class TestSuperAdminLogin:
    """Test Super Admin Login at /admin-login"""
    
    def test_super_admin_login_success(self):
        """P0: Super admin should be able to login"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["role"] == "super_admin", "User role should be super_admin"
        assert data["user"]["id"] == "super_admin", "User id should be super_admin"
        print(f"✓ Super admin login successful, token received")
    
    def test_super_admin_login_invalid_credentials(self):
        """Super admin login should fail with wrong credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": "wrong",
            "password": "wrong"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Invalid credentials correctly rejected")


class TestTherapistApplicationFlow:
    """Test Therapist Application and Approval Flow"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not get admin token")
        return response.json()["token"]
    
    def test_therapist_application_submit(self):
        """Test submitting a therapist application"""
        import random
        unique_mobile = f"88{random.randint(10000000, 99999999)}"  # 10 digit mobile
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/therapist-application", json={
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "Test Therapist",
            "credentials": "Licensed Clinical Psychologist",
            "specialization": "Anxiety",
            "years_of_experience": 5
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "application_id" in data, "Response should contain application_id"
        print(f"✓ Therapist application submitted: {data['application_id']}")
        return data["application_id"]
    
    def test_get_therapist_applications(self, admin_token):
        """P0: GET /api/admin/therapist-applications should work with super admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/therapist-applications", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Got {len(data)} therapist applications")
    
    def test_get_therapist_applications_without_auth(self):
        """Applications endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/therapist-applications")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated request correctly rejected")
    
    def test_approve_therapist_application(self, admin_token):
        """P0: POST /api/admin/therapist-applications/{id}/approve should work"""
        import random
        # First submit an application
        unique_mobile = f"77{random.randint(10000000, 99999999)}"  # 10 digit mobile
        unique_email = f"approve_test_{uuid.uuid4().hex[:8]}@example.com"
        
        submit_response = requests.post(f"{BASE_URL}/api/auth/therapist-application", json={
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "Approve Test Therapist",
            "credentials": "Licensed Therapist",
            "specialization": "Depression",
            "years_of_experience": 3
        })
        
        if submit_response.status_code != 200:
            pytest.skip(f"Could not submit application: {submit_response.text}")
        
        app_id = submit_response.json()["application_id"]
        
        # Now approve it
        headers = {"Authorization": f"Bearer {admin_token}"}
        approve_response = requests.post(
            f"{BASE_URL}/api/admin/therapist-applications/{app_id}/approve?password={TEST_THERAPIST_PASSWORD}",
            headers=headers
        )
        
        assert approve_response.status_code == 200, f"Expected 200, got {approve_response.status_code}: {approve_response.text}"
        
        data = approve_response.json()
        assert "therapist_id" in data, "Response should contain therapist_id"
        print(f"✓ Therapist approved: {data['therapist_id']}")
        
        # Store for later tests
        return {"therapist_id": data["therapist_id"], "mobile": unique_mobile}


class TestTherapistManagement:
    """Test Therapist Suspend/Activate Endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not get admin token")
        return response.json()["token"]
    
    @pytest.fixture
    def test_therapist(self, admin_token):
        """Create a test therapist for suspend/activate tests"""
        import random
        unique_mobile = f"66{random.randint(10000000, 99999999)}"  # 10 digit mobile
        unique_email = f"mgmt_test_{uuid.uuid4().hex[:8]}@example.com"
        
        # Submit application
        submit_response = requests.post(f"{BASE_URL}/api/auth/therapist-application", json={
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "Management Test Therapist",
            "credentials": "Licensed Therapist",
            "specialization": "General",
            "years_of_experience": 2
        })
        
        if submit_response.status_code != 200:
            pytest.skip(f"Could not submit application: {submit_response.text}")
        
        app_id = submit_response.json()["application_id"]
        
        # Approve
        headers = {"Authorization": f"Bearer {admin_token}"}
        approve_response = requests.post(
            f"{BASE_URL}/api/admin/therapist-applications/{app_id}/approve?password=TestPass123",
            headers=headers
        )
        
        if approve_response.status_code != 200:
            pytest.skip(f"Could not approve application: {approve_response.text}")
        
        return {
            "therapist_id": approve_response.json()["therapist_id"],
            "mobile": unique_mobile
        }
    
    def test_get_all_therapists(self, admin_token):
        """GET /api/admin/therapists should return list of therapists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/therapists", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Got {len(data)} therapists")
    
    def test_suspend_therapist(self, admin_token, test_therapist):
        """POST /api/admin/therapists/{id}/suspend should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        therapist_id = test_therapist["therapist_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/suspend",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Therapist {therapist_id} suspended")
    
    def test_activate_therapist(self, admin_token, test_therapist):
        """POST /api/admin/therapists/{id}/activate should work"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        therapist_id = test_therapist["therapist_id"]
        
        # First suspend
        requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/suspend",
            headers=headers
        )
        
        # Then activate
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/activate",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Therapist {therapist_id} activated")


class TestClientEndpoint:
    """Test Client List Endpoint - P1 Fix for mobile field"""
    
    @pytest.fixture
    def therapist_token(self):
        """Get an approved therapist token"""
        # First create and approve a therapist
        admin_response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        })
        
        if admin_response.status_code != 200:
            pytest.skip("Could not get admin token")
        
        admin_token = admin_response.json()["token"]
        
        unique_mobile = f"55{uuid.uuid4().hex[:8]}"[:10]
        unique_email = f"client_test_{uuid.uuid4().hex[:8]}@example.com"
        
        # Submit application
        submit_response = requests.post(f"{BASE_URL}/api/auth/therapist-application", json={
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "Client Test Therapist",
            "credentials": "Licensed Therapist",
            "specialization": "General",
            "years_of_experience": 2
        })
        
        if submit_response.status_code != 200:
            pytest.skip(f"Could not submit application: {submit_response.text}")
        
        app_id = submit_response.json()["application_id"]
        
        # Approve
        headers = {"Authorization": f"Bearer {admin_token}"}
        approve_response = requests.post(
            f"{BASE_URL}/api/admin/therapist-applications/{app_id}/approve?password=TestPass123",
            headers=headers
        )
        
        if approve_response.status_code != 200:
            pytest.skip(f"Could not approve application: {approve_response.text}")
        
        # Login as therapist
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": unique_mobile,
            "password": "TestPass123"
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Could not login as therapist: {login_response.text}")
        
        return login_response.json()["token"]
    
    def test_get_clients_no_crash(self, therapist_token):
        """P1: GET /api/clients should not crash on old records without mobile field"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
        
        # Should not return 500 (server error)
        assert response.status_code != 500, f"Server crashed with 500: {response.text}"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/clients returned {len(data)} clients without crashing")


class TestApprovedTherapistLogin:
    """Test that approved therapist can login using mobile number"""
    
    @pytest.fixture
    def approved_therapist(self):
        """Create and approve a therapist"""
        admin_response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        })
        
        if admin_response.status_code != 200:
            pytest.skip("Could not get admin token")
        
        admin_token = admin_response.json()["token"]
        
        unique_mobile = f"44{uuid.uuid4().hex[:8]}"[:10]
        unique_email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "LoginTestPass123"
        
        # Submit application
        submit_response = requests.post(f"{BASE_URL}/api/auth/therapist-application", json={
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "Login Test Therapist",
            "credentials": "Licensed Therapist",
            "specialization": "General",
            "years_of_experience": 2
        })
        
        if submit_response.status_code != 200:
            pytest.skip(f"Could not submit application: {submit_response.text}")
        
        app_id = submit_response.json()["application_id"]
        
        # Approve
        headers = {"Authorization": f"Bearer {admin_token}"}
        approve_response = requests.post(
            f"{BASE_URL}/api/admin/therapist-applications/{app_id}/approve?password={password}",
            headers=headers
        )
        
        if approve_response.status_code != 200:
            pytest.skip(f"Could not approve application: {approve_response.text}")
        
        return {"mobile": unique_mobile, "password": password}
    
    def test_approved_therapist_login_with_mobile(self, approved_therapist):
        """Approved therapist should be able to login using mobile number"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": approved_therapist["mobile"],
            "password": approved_therapist["password"]
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["role"] == "therapist", "User role should be therapist"
        assert data["user"]["status"] == "approved", "User status should be approved"
        print(f"✓ Approved therapist logged in successfully with mobile: {approved_therapist['mobile']}")


class TestAdminClientsEndpoint:
    """Test Admin Clients Endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not get admin token")
        return response.json()["token"]
    
    def test_admin_get_all_clients(self, admin_token):
        """GET /api/admin/clients should work for super admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/clients", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Admin got {len(data)} clients")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
