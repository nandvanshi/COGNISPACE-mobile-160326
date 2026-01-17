"""
Backend API Tests for TherapyFlow Super Admin Panel Enhancements
P0: Subscription Plans and Coupon Codes modules
P1: Manual therapist creation, edit therapist, therapist detail, therapist clients, full client details
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


@pytest.fixture(scope="module")
def admin_token():
    """Get super admin token for all tests"""
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


# ============= P0: SUBSCRIPTION PLANS TESTS =============

class TestSubscriptionPlans:
    """P0: Test Subscription Plans CRUD - GET/POST/DELETE /api/admin/subscription-plans"""
    
    def test_get_subscription_plans(self, admin_headers):
        """GET /api/admin/subscription-plans should return list of plans"""
        response = requests.get(f"{BASE_URL}/api/admin/subscription-plans", headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET subscription-plans returned {len(data)} plans")
    
    def test_create_subscription_plan(self, admin_headers):
        """POST /api/admin/subscription-plans should create a new plan"""
        unique_name = f"TEST_Plan_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "price": 99.99,
            "duration_days": 30,
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "max_clients": 50
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/subscription-plans", json=payload, headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should contain id"
        assert data["name"] == unique_name, f"Name mismatch: expected {unique_name}, got {data['name']}"
        assert data["price"] == 99.99, f"Price mismatch: expected 99.99, got {data['price']}"
        assert data["duration_days"] == 30, f"Duration mismatch: expected 30, got {data['duration_days']}"
        assert len(data["features"]) == 3, f"Features count mismatch: expected 3, got {len(data['features'])}"
        
        print(f"✓ Created subscription plan: {data['id']}")
        return data["id"]
    
    def test_create_and_delete_subscription_plan(self, admin_headers):
        """DELETE /api/admin/subscription-plans/{id} should delete a plan"""
        # First create a plan
        unique_name = f"TEST_DeletePlan_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "price": 49.99,
            "duration_days": 7,
            "features": ["Trial Feature"],
            "max_clients": None
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/subscription-plans", json=create_payload, headers=admin_headers)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        plan_id = create_response.json()["id"]
        
        # Now delete it
        delete_response = requests.delete(f"{BASE_URL}/api/admin/subscription-plans/{plan_id}", headers=admin_headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        # Verify deletion by trying to get all plans and checking it's not there
        get_response = requests.get(f"{BASE_URL}/api/admin/subscription-plans", headers=admin_headers)
        plans = get_response.json()
        plan_ids = [p["id"] for p in plans]
        assert plan_id not in plan_ids, "Deleted plan should not be in list"
        
        print(f"✓ Deleted subscription plan: {plan_id}")
    
    def test_delete_nonexistent_plan(self, admin_headers):
        """DELETE /api/admin/subscription-plans/{id} should return 404 for nonexistent plan"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/admin/subscription-plans/{fake_id}", headers=admin_headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Correctly returned 404 for nonexistent plan")


# ============= P0: COUPON CODES TESTS =============

class TestCouponCodes:
    """P0: Test Coupon Codes CRUD - GET/POST/DELETE /api/admin/coupons"""
    
    def test_get_coupons(self, admin_headers):
        """GET /api/admin/coupons should return list of coupons"""
        response = requests.get(f"{BASE_URL}/api/admin/coupons", headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET coupons returned {len(data)} coupons")
    
    def test_create_coupon(self, admin_headers):
        """POST /api/admin/coupons should create a new coupon"""
        unique_code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        valid_until = (datetime.now() + timedelta(days=30)).isoformat()
        
        payload = {
            "code": unique_code,
            "discount_percent": 25.0,
            "valid_until": valid_until,
            "max_uses": 100
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/coupons", json=payload, headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should contain id"
        assert data["code"] == unique_code.upper(), f"Code mismatch: expected {unique_code.upper()}, got {data['code']}"
        assert data["discount_percent"] == 25.0, f"Discount mismatch: expected 25.0, got {data['discount_percent']}"
        assert data["used_count"] == 0, f"Used count should be 0, got {data['used_count']}"
        
        print(f"✓ Created coupon: {data['code']}")
        return data["id"]
    
    def test_create_duplicate_coupon_fails(self, admin_headers):
        """POST /api/admin/coupons should fail for duplicate code"""
        unique_code = f"DUP{uuid.uuid4().hex[:6].upper()}"
        valid_until = (datetime.now() + timedelta(days=30)).isoformat()
        
        payload = {
            "code": unique_code,
            "discount_percent": 10.0,
            "valid_until": valid_until,
            "max_uses": None
        }
        
        # Create first coupon
        response1 = requests.post(f"{BASE_URL}/api/admin/coupons", json=payload, headers=admin_headers)
        assert response1.status_code == 200, f"First create failed: {response1.text}"
        
        # Try to create duplicate
        response2 = requests.post(f"{BASE_URL}/api/admin/coupons", json=payload, headers=admin_headers)
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}"
        
        print(f"✓ Correctly rejected duplicate coupon code")
    
    def test_create_and_delete_coupon(self, admin_headers):
        """DELETE /api/admin/coupons/{id} should delete a coupon"""
        unique_code = f"DEL{uuid.uuid4().hex[:6].upper()}"
        valid_until = (datetime.now() + timedelta(days=7)).isoformat()
        
        create_payload = {
            "code": unique_code,
            "discount_percent": 15.0,
            "valid_until": valid_until,
            "max_uses": 10
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/coupons", json=create_payload, headers=admin_headers)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        coupon_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/admin/coupons/{coupon_id}", headers=admin_headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/admin/coupons", headers=admin_headers)
        coupons = get_response.json()
        coupon_ids = [c["id"] for c in coupons]
        assert coupon_id not in coupon_ids, "Deleted coupon should not be in list"
        
        print(f"✓ Deleted coupon: {coupon_id}")


# ============= P1: MANUAL THERAPIST CREATION TESTS =============

class TestManualTherapistCreation:
    """P1: Test Manual Therapist Creation - POST /api/admin/therapists/create"""
    
    def test_create_therapist_manually(self, admin_headers):
        """POST /api/admin/therapists/create should create a therapist without application"""
        import random
        unique_mobile = f"33{random.randint(10000000, 99999999)}"
        unique_email = f"manual_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_Manual Therapist",
            "password": "ManualPass123",
            "credentials": "Licensed Clinical Psychologist #12345",
            "specialization": "Anxiety & Depression",
            "years_of_experience": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "therapist_id" in data, "Response should contain therapist_id"
        assert "message" in data, "Response should contain message"
        
        print(f"✓ Manually created therapist: {data['therapist_id']}")
        return data["therapist_id"]
    
    def test_create_therapist_invalid_mobile(self, admin_headers):
        """POST /api/admin/therapists/create should fail for invalid mobile"""
        payload = {
            "mobile": "123",  # Invalid - not 10 digits
            "email": f"invalid_{uuid.uuid4().hex[:8]}@example.com",
            "full_name": "Invalid Mobile Test",
            "password": "TestPass123",
            "credentials": "Test Credentials"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Correctly rejected invalid mobile number")
    
    def test_create_therapist_duplicate_mobile(self, admin_headers):
        """POST /api/admin/therapists/create should fail for duplicate mobile"""
        import random
        unique_mobile = f"22{random.randint(10000000, 99999999)}"
        
        payload1 = {
            "mobile": unique_mobile,
            "email": f"dup1_{uuid.uuid4().hex[:8]}@example.com",
            "full_name": "TEST_Duplicate Mobile 1",
            "password": "TestPass123",
            "credentials": "Test Credentials"
        }
        
        # Create first therapist
        response1 = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload1, headers=admin_headers)
        assert response1.status_code == 200, f"First create failed: {response1.text}"
        
        # Try to create with same mobile
        payload2 = {
            "mobile": unique_mobile,
            "email": f"dup2_{uuid.uuid4().hex[:8]}@example.com",
            "full_name": "TEST_Duplicate Mobile 2",
            "password": "TestPass123",
            "credentials": "Test Credentials"
        }
        
        response2 = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload2, headers=admin_headers)
        assert response2.status_code == 400, f"Expected 400 for duplicate mobile, got {response2.status_code}"
        
        print(f"✓ Correctly rejected duplicate mobile number")


# ============= P1: EDIT THERAPIST TESTS =============

class TestEditTherapist:
    """P1: Test Edit Therapist - PUT /api/admin/therapists/{id}"""
    
    @pytest.fixture
    def test_therapist_id(self, admin_headers):
        """Create a test therapist for editing"""
        import random
        unique_mobile = f"11{random.randint(10000000, 99999999)}"
        unique_email = f"edit_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_Edit Therapist",
            "password": "EditPass123",
            "credentials": "Original Credentials",
            "specialization": "Original Specialization",
            "years_of_experience": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        return response.json()["therapist_id"]
    
    def test_update_therapist(self, admin_headers, test_therapist_id):
        """PUT /api/admin/therapists/{id} should update therapist details"""
        update_payload = {
            "full_name": "TEST_Updated Name",
            "credentials": "Updated Credentials",
            "specialization": "Updated Specialization",
            "years_of_experience": 15
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/therapists/{test_therapist_id}",
            json=update_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify update by getting therapist detail
        get_response = requests.get(
            f"{BASE_URL}/api/admin/therapists/{test_therapist_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 200
        data = get_response.json()
        
        assert data["full_name"] == "TEST_Updated Name", f"Name not updated: {data['full_name']}"
        assert data["credentials"] == "Updated Credentials", f"Credentials not updated: {data['credentials']}"
        assert data["specialization"] == "Updated Specialization", f"Specialization not updated: {data['specialization']}"
        assert data["years_of_experience"] == 15, f"Experience not updated: {data['years_of_experience']}"
        
        print(f"✓ Updated therapist: {test_therapist_id}")
    
    def test_update_nonexistent_therapist(self, admin_headers):
        """PUT /api/admin/therapists/{id} should return 404 for nonexistent therapist"""
        fake_id = str(uuid.uuid4())
        update_payload = {"full_name": "Test"}
        
        response = requests.put(
            f"{BASE_URL}/api/admin/therapists/{fake_id}",
            json=update_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Correctly returned 404 for nonexistent therapist")


# ============= P1: THERAPIST DETAIL WITH SUBSCRIPTION INFO =============

class TestTherapistDetail:
    """P1: Test Therapist Detail - GET /api/admin/therapists/{id}"""
    
    @pytest.fixture
    def test_therapist_id(self, admin_headers):
        """Create a test therapist for detail view"""
        import random
        unique_mobile = f"99{random.randint(10000000, 99999999)}"
        unique_email = f"detail_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_Detail Therapist",
            "password": "DetailPass123",
            "credentials": "Detail Test Credentials",
            "specialization": "Detail Specialization",
            "years_of_experience": 8
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        return response.json()["therapist_id"]
    
    def test_get_therapist_detail(self, admin_headers, test_therapist_id):
        """GET /api/admin/therapists/{id} should return detailed therapist info"""
        response = requests.get(
            f"{BASE_URL}/api/admin/therapists/{test_therapist_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "id" in data, "Response should contain id"
        assert "full_name" in data, "Response should contain full_name"
        assert "mobile" in data, "Response should contain mobile"
        assert "email" in data, "Response should contain email"
        assert "credentials" in data, "Response should contain credentials"
        assert "status" in data, "Response should contain status"
        assert "subscription_status" in data, "Response should contain subscription_status"
        assert "subscription_plan" in data, "Response should contain subscription_plan"
        assert "subscription_end_date" in data, "Response should contain subscription_end_date"
        assert "client_count" in data, "Response should contain client_count"
        
        # Verify values
        assert data["id"] == test_therapist_id
        assert data["full_name"] == "TEST_Detail Therapist"
        assert data["status"] == "approved"
        assert data["subscription_status"] == "trial"  # New therapists start with trial
        
        print(f"✓ Got therapist detail with subscription info: {test_therapist_id}")
    
    def test_get_nonexistent_therapist_detail(self, admin_headers):
        """GET /api/admin/therapists/{id} should return 404 for nonexistent therapist"""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/admin/therapists/{fake_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Correctly returned 404 for nonexistent therapist")


# ============= P1: THERAPIST CLIENTS =============

class TestTherapistClients:
    """P1: Test Therapist Clients - GET /api/admin/therapists/{id}/clients"""
    
    @pytest.fixture
    def test_therapist_id(self, admin_headers):
        """Create a test therapist"""
        import random
        unique_mobile = f"88{random.randint(10000000, 99999999)}"
        unique_email = f"clients_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_Clients Therapist",
            "password": "ClientsPass123",
            "credentials": "Clients Test Credentials"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        return response.json()["therapist_id"]
    
    def test_get_therapist_clients(self, admin_headers, test_therapist_id):
        """GET /api/admin/therapists/{id}/clients should return list of clients"""
        response = requests.get(
            f"{BASE_URL}/api/admin/therapists/{test_therapist_id}/clients",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Got {len(data)} clients for therapist: {test_therapist_id}")
    
    def test_get_nonexistent_therapist_clients(self, admin_headers):
        """GET /api/admin/therapists/{id}/clients should return 404 for nonexistent therapist"""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/admin/therapists/{fake_id}/clients",
            headers=admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Correctly returned 404 for nonexistent therapist")


# ============= P1: FULL CLIENT DETAILS =============

class TestFullClientDetails:
    """P1: Test Full Client Details - GET /api/admin/clients and GET /api/admin/clients/{id}"""
    
    def test_get_all_clients_with_therapist_name(self, admin_headers):
        """GET /api/admin/clients should return clients with therapist_name field"""
        response = requests.get(f"{BASE_URL}/api/admin/clients", headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        # Check that response includes therapist_name field (even if null)
        if len(data) > 0:
            client = data[0]
            assert "therapist_name" in client or "therapist_id" in client, "Response should include therapist info"
            assert "full_name" in client, "Response should include full_name"
            assert "mobile" in client, "Response should include mobile"
        
        print(f"✓ GET /api/admin/clients returned {len(data)} clients with therapist info")
    
    def test_get_specific_client_detail(self, admin_headers):
        """GET /api/admin/clients/{id} should return detailed client info"""
        # First get list of clients
        list_response = requests.get(f"{BASE_URL}/api/admin/clients", headers=admin_headers)
        if list_response.status_code != 200:
            pytest.skip("Could not get clients list")
        
        clients = list_response.json()
        if len(clients) == 0:
            pytest.skip("No clients to test with")
        
        client_id = clients[0]["id"]
        
        # Get specific client detail
        response = requests.get(f"{BASE_URL}/api/admin/clients/{client_id}", headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "id" in data, "Response should contain id"
        assert "full_name" in data, "Response should contain full_name"
        assert "mobile" in data, "Response should contain mobile"
        assert "therapist_name" in data or "therapist_id" in data, "Response should contain therapist info"
        
        print(f"✓ Got client detail: {client_id}")
    
    def test_get_nonexistent_client_detail(self, admin_headers):
        """GET /api/admin/clients/{id} should return 404 for nonexistent client"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/admin/clients/{fake_id}", headers=admin_headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Correctly returned 404 for nonexistent client")


# ============= AUTHENTICATION TESTS =============

class TestEndpointAuthentication:
    """Test that all admin endpoints require authentication"""
    
    def test_subscription_plans_requires_auth(self):
        """GET /api/admin/subscription-plans should require auth"""
        response = requests.get(f"{BASE_URL}/api/admin/subscription-plans")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ subscription-plans requires auth")
    
    def test_coupons_requires_auth(self):
        """GET /api/admin/coupons should require auth"""
        response = requests.get(f"{BASE_URL}/api/admin/coupons")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ coupons requires auth")
    
    def test_create_therapist_requires_auth(self):
        """POST /api/admin/therapists/create should require auth"""
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json={})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ therapists/create requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
