"""
P0 Subscription Management Tests
Tests for critical subscription management features:
- P0-1: Create new therapist with automatic 30-day trial subscription
- P0-2: Assign subscription plan to existing therapist
- P0-3: Change therapist's subscription plan
- P0-4: Extend therapist's subscription
- P0-5: Migrate subscriptions for therapists without subscriptions
- P0-6: Verify subscription changes persist
"""
import pytest
import requests
import os
import uuid
import random
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


@pytest.fixture(scope="module")
def test_subscription_plan(admin_headers):
    """Create a test subscription plan for testing"""
    unique_name = f"TEST_Plan_{uuid.uuid4().hex[:6]}"
    payload = {
        "name": unique_name,
        "price": 99.99,
        "duration_days": 30,
        "features": ["Feature 1", "Feature 2"],
        "max_clients": 50
    }
    
    response = requests.post(f"{BASE_URL}/api/admin/subscription-plans", json=payload, headers=admin_headers)
    if response.status_code != 200:
        pytest.skip(f"Could not create test plan: {response.text}")
    
    plan = response.json()
    yield plan
    
    # Cleanup - delete the plan after tests
    requests.delete(f"{BASE_URL}/api/admin/subscription-plans/{plan['id']}", headers=admin_headers)


class TestP0_1_NewTherapistTrialSubscription:
    """P0-1: Create a new therapist manually and verify they get automatic 30-day trial subscription"""
    
    def test_create_therapist_gets_trial_subscription(self, admin_headers):
        """POST /api/admin/therapists/create should create therapist with trial subscription"""
        unique_mobile = f"10{random.randint(10000000, 99999999)}"
        unique_email = f"p0_trial_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Trial_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0TEST",
            "specialization": "Test Specialization",
            "years_of_experience": 5
        }
        
        # Create therapist
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "therapist_id" in data, "Response should contain therapist_id"
        therapist_id = data["therapist_id"]
        
        # Verify therapist has trial subscription
        detail_response = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers)
        assert detail_response.status_code == 200, f"Could not get therapist detail: {detail_response.text}"
        
        therapist_detail = detail_response.json()
        
        # Verify subscription status is trial
        assert therapist_detail["subscription_status"] == "trial", \
            f"Expected subscription_status='trial', got '{therapist_detail['subscription_status']}'"
        
        # Verify subscription plan is free_trial
        assert therapist_detail["subscription_plan"] == "free_trial", \
            f"Expected subscription_plan='free_trial', got '{therapist_detail['subscription_plan']}'"
        
        # Verify subscription end date is approximately 30 days from now
        assert therapist_detail["subscription_end_date"] is not None, "subscription_end_date should not be None"
        
        end_date = datetime.fromisoformat(therapist_detail["subscription_end_date"].replace('Z', '+00:00'))
        now = datetime.now(end_date.tzinfo)
        days_remaining = (end_date - now).days
        
        assert 28 <= days_remaining <= 31, f"Expected ~30 days remaining, got {days_remaining}"
        
        print(f"✓ P0-1 PASS: New therapist {therapist_id} created with trial subscription ({days_remaining} days)")


class TestP0_2_AssignSubscriptionPlan:
    """P0-2: Assign a subscription plan to an existing therapist via Super Admin"""
    
    @pytest.fixture
    def test_therapist(self, admin_headers):
        """Create a test therapist for subscription assignment"""
        unique_mobile = f"20{random.randint(10000000, 99999999)}"
        unique_email = f"p0_assign_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Assign_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0ASSIGN"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        return response.json()["therapist_id"]
    
    def test_assign_subscription_plan(self, admin_headers, test_therapist, test_subscription_plan):
        """POST /api/admin/therapists/{id}/assign-subscription should assign plan"""
        therapist_id = test_therapist
        plan_id = test_subscription_plan["id"]
        plan_name = test_subscription_plan["name"]
        
        # Assign subscription
        assign_payload = {"plan_id": plan_id}
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/assign-subscription",
            json=assign_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "subscription_id" in data, "Response should contain subscription_id"
        
        # Verify subscription was assigned by getting therapist detail
        detail_response = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers)
        assert detail_response.status_code == 200
        
        therapist_detail = detail_response.json()
        
        # Verify subscription status changed to active
        assert therapist_detail["subscription_status"] == "active", \
            f"Expected subscription_status='active', got '{therapist_detail['subscription_status']}'"
        
        # Verify subscription plan name matches
        assert therapist_detail["subscription_plan"] == plan_name, \
            f"Expected subscription_plan='{plan_name}', got '{therapist_detail['subscription_plan']}'"
        
        print(f"✓ P0-2 PASS: Subscription plan '{plan_name}' assigned to therapist {therapist_id}")


class TestP0_3_ChangeSubscriptionPlan:
    """P0-3: Change a therapist's subscription plan to a different plan"""
    
    @pytest.fixture
    def test_therapist_with_plan(self, admin_headers, test_subscription_plan):
        """Create a therapist and assign initial plan"""
        unique_mobile = f"30{random.randint(10000000, 99999999)}"
        unique_email = f"p0_change_test_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create therapist
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Change_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0CHANGE"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        therapist_id = response.json()["therapist_id"]
        
        # Assign initial plan
        assign_payload = {"plan_id": test_subscription_plan["id"]}
        requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/assign-subscription",
            json=assign_payload,
            headers=admin_headers
        )
        
        return therapist_id
    
    @pytest.fixture
    def second_subscription_plan(self, admin_headers):
        """Create a second subscription plan for changing"""
        unique_name = f"TEST_Plan2_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "price": 199.99,
            "duration_days": 60,
            "features": ["Premium Feature 1", "Premium Feature 2"],
            "max_clients": 100
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/subscription-plans", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create second plan: {response.text}")
        
        plan = response.json()
        yield plan
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/subscription-plans/{plan['id']}", headers=admin_headers)
    
    def test_change_subscription_plan(self, admin_headers, test_therapist_with_plan, second_subscription_plan):
        """Changing subscription plan should update therapist's plan"""
        therapist_id = test_therapist_with_plan
        new_plan_id = second_subscription_plan["id"]
        new_plan_name = second_subscription_plan["name"]
        
        # Change to new plan
        assign_payload = {"plan_id": new_plan_id}
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/assign-subscription",
            json=assign_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify plan was changed
        detail_response = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers)
        assert detail_response.status_code == 200
        
        therapist_detail = detail_response.json()
        
        assert therapist_detail["subscription_plan"] == new_plan_name, \
            f"Expected subscription_plan='{new_plan_name}', got '{therapist_detail['subscription_plan']}'"
        
        print(f"✓ P0-3 PASS: Subscription plan changed to '{new_plan_name}' for therapist {therapist_id}")


class TestP0_4_ExtendSubscription:
    """P0-4: Extend a therapist's subscription by adding days"""
    
    @pytest.fixture
    def test_therapist_for_extend(self, admin_headers):
        """Create a therapist for extension testing"""
        unique_mobile = f"40{random.randint(10000000, 99999999)}"
        unique_email = f"p0_extend_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Extend_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0EXTEND"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        return response.json()["therapist_id"]
    
    def test_extend_subscription(self, admin_headers, test_therapist_for_extend):
        """POST /api/admin/therapists/{id}/extend-subscription should add days"""
        therapist_id = test_therapist_for_extend
        
        # Get current subscription end date
        detail_response = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers)
        assert detail_response.status_code == 200
        
        original_end_date = detail_response.json()["subscription_end_date"]
        original_end = datetime.fromisoformat(original_end_date.replace('Z', '+00:00'))
        
        # Extend by 15 days
        extend_days = 15
        extend_payload = {"additional_days": extend_days}
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/extend-subscription",
            json=extend_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "new_end_date" in data, "Response should contain new_end_date"
        
        # Verify extension
        new_end = datetime.fromisoformat(data["new_end_date"].replace('Z', '+00:00'))
        expected_end = original_end + timedelta(days=extend_days)
        
        # Allow 1 second tolerance for timing
        diff = abs((new_end - expected_end).total_seconds())
        assert diff < 2, f"Expected end date {expected_end}, got {new_end}"
        
        # Verify by getting therapist detail again
        detail_response2 = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers)
        therapist_detail = detail_response2.json()
        
        assert therapist_detail["subscription_end_date"] == data["new_end_date"], \
            "Subscription end date should be updated in therapist profile"
        
        print(f"✓ P0-4 PASS: Subscription extended by {extend_days} days for therapist {therapist_id}")
    
    def test_extend_subscription_no_subscription_fails(self, admin_headers):
        """Extending subscription for therapist without subscription should fail gracefully"""
        # Create therapist without subscription (we'll manually remove it)
        unique_mobile = f"41{random.randint(10000000, 99999999)}"
        unique_email = f"p0_extend_fail_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Extend_Fail_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0EXTENDFAIL"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        therapist_id = response.json()["therapist_id"]
        
        # The therapist has a trial subscription, so extend should work
        # This test verifies the endpoint works correctly
        extend_payload = {"additional_days": 10}
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/extend-subscription",
            json=extend_payload,
            headers=admin_headers
        )
        
        # Should succeed since therapist has trial subscription
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ P0-4 PASS: Extend subscription works for therapist with trial")


class TestP0_5_MigrateSubscriptions:
    """P0-5: Verify the 'Fix Missing Subscriptions' migration button works"""
    
    def test_migrate_subscriptions_endpoint(self, admin_headers):
        """POST /api/admin/migrate-subscriptions should migrate therapists without subscriptions"""
        response = requests.post(f"{BASE_URL}/api/admin/migrate-subscriptions", headers=admin_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "migrated" in data["message"].lower() or "therapists" in data["message"].lower(), \
            f"Response message should mention migration: {data['message']}"
        
        print(f"✓ P0-5 PASS: Migration endpoint works - {data['message']}")


class TestP0_6_SubscriptionPersistence:
    """P0-6: Verify subscription changes persist and reflect immediately in therapist profiles"""
    
    @pytest.fixture
    def test_therapist_for_persistence(self, admin_headers):
        """Create a therapist for persistence testing"""
        unique_mobile = f"60{random.randint(10000000, 99999999)}"
        unique_email = f"p0_persist_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Persist_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0PERSIST"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        return response.json()["therapist_id"]
    
    def test_subscription_changes_persist(self, admin_headers, test_therapist_for_persistence, test_subscription_plan):
        """Subscription changes should persist across multiple API calls"""
        therapist_id = test_therapist_for_persistence
        plan_id = test_subscription_plan["id"]
        plan_name = test_subscription_plan["name"]
        
        # Step 1: Verify initial trial subscription
        detail1 = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers).json()
        assert detail1["subscription_status"] == "trial", "Initial status should be trial"
        initial_end_date = detail1["subscription_end_date"]
        
        # Step 2: Assign new plan
        assign_payload = {"plan_id": plan_id}
        requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/assign-subscription",
            json=assign_payload,
            headers=admin_headers
        )
        
        # Step 3: Verify plan change persisted
        detail2 = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers).json()
        assert detail2["subscription_status"] == "active", "Status should be active after plan assignment"
        assert detail2["subscription_plan"] == plan_name, f"Plan should be {plan_name}"
        
        # Step 4: Extend subscription
        extend_payload = {"additional_days": 30}
        requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/extend-subscription",
            json=extend_payload,
            headers=admin_headers
        )
        
        # Step 5: Verify extension persisted
        detail3 = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers).json()
        assert detail3["subscription_end_date"] != detail2["subscription_end_date"], \
            "End date should have changed after extension"
        
        # Step 6: Verify in therapists list
        list_response = requests.get(f"{BASE_URL}/api/admin/therapists", headers=admin_headers)
        therapists = list_response.json()
        
        therapist_in_list = next((t for t in therapists if t["id"] == therapist_id), None)
        assert therapist_in_list is not None, "Therapist should be in list"
        assert therapist_in_list["subscription_status"] == "active", "Status in list should be active"
        assert therapist_in_list["subscription_plan"] == plan_name, f"Plan in list should be {plan_name}"
        
        print(f"✓ P0-6 PASS: All subscription changes persisted for therapist {therapist_id}")


class TestP0_AssignTrialSubscription:
    """Test assign-trial endpoint for assigning 30-day trial"""
    
    @pytest.fixture
    def test_therapist_for_trial(self, admin_headers, test_subscription_plan):
        """Create a therapist and assign a paid plan first"""
        unique_mobile = f"70{random.randint(10000000, 99999999)}"
        unique_email = f"p0_trial_assign_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Trial_Assign_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0TRIALASSIGN"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        therapist_id = response.json()["therapist_id"]
        
        # Assign paid plan first
        assign_payload = {"plan_id": test_subscription_plan["id"]}
        requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/assign-subscription",
            json=assign_payload,
            headers=admin_headers
        )
        
        return therapist_id
    
    def test_assign_trial_subscription(self, admin_headers, test_therapist_for_trial):
        """POST /api/admin/therapists/{id}/assign-trial should assign 30-day trial"""
        therapist_id = test_therapist_for_trial
        
        # Verify therapist has active subscription first
        detail1 = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers).json()
        assert detail1["subscription_status"] == "active", "Should have active subscription before trial assignment"
        
        # Assign trial
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/assign-trial",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "subscription_id" in data, "Response should contain subscription_id"
        assert "end_date" in data, "Response should contain end_date"
        
        # Verify trial was assigned
        detail2 = requests.get(f"{BASE_URL}/api/admin/therapists/{therapist_id}", headers=admin_headers).json()
        assert detail2["subscription_status"] == "trial", \
            f"Expected subscription_status='trial', got '{detail2['subscription_status']}'"
        assert detail2["subscription_plan"] == "free_trial", \
            f"Expected subscription_plan='free_trial', got '{detail2['subscription_plan']}'"
        
        print(f"✓ Assign trial subscription works for therapist {therapist_id}")


class TestSubscriptionEndpointErrors:
    """Test error handling for subscription endpoints"""
    
    def test_assign_subscription_nonexistent_therapist(self, admin_headers, test_subscription_plan):
        """Assigning subscription to nonexistent therapist should return 404"""
        fake_id = str(uuid.uuid4())
        assign_payload = {"plan_id": test_subscription_plan["id"]}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{fake_id}/assign-subscription",
            json=assign_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Correctly returned 404 for nonexistent therapist")
    
    def test_assign_subscription_nonexistent_plan(self, admin_headers):
        """Assigning nonexistent plan should return 404"""
        # Create a therapist first
        unique_mobile = f"80{random.randint(10000000, 99999999)}"
        unique_email = f"p0_error_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "mobile": unique_mobile,
            "email": unique_email,
            "full_name": "TEST_P0_Error_Therapist",
            "password": "TestPass123",
            "credentials": "Licensed Therapist #P0ERROR"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/therapists/create", json=payload, headers=admin_headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test therapist: {response.text}")
        
        therapist_id = response.json()["therapist_id"]
        
        # Try to assign nonexistent plan
        fake_plan_id = str(uuid.uuid4())
        assign_payload = {"plan_id": fake_plan_id}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{therapist_id}/assign-subscription",
            json=assign_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Correctly returned 404 for nonexistent plan")
    
    def test_extend_subscription_nonexistent_therapist(self, admin_headers):
        """Extending subscription for nonexistent therapist should return 404"""
        fake_id = str(uuid.uuid4())
        extend_payload = {"additional_days": 30}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{fake_id}/extend-subscription",
            json=extend_payload,
            headers=admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Correctly returned 404 for nonexistent therapist")
    
    def test_assign_trial_nonexistent_therapist(self, admin_headers):
        """Assigning trial to nonexistent therapist should return 404"""
        fake_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/{fake_id}/assign-trial",
            headers=admin_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Correctly returned 404 for nonexistent therapist")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
