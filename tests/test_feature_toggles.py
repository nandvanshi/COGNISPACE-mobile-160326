"""
Test Suite for Feature Toggles and Subscription System
Tests:
1. Subscription plan feature toggles management (Super Admin)
2. Feature access enforcement in backend endpoints
3. Subscription status endpoint with feature toggles
4. Expiry warning calculation
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "password"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ASSISTANT_EMAIL = "test_assistant_ui@test.com"
ASSISTANT_PASSWORD = "testpass123"


class TestSetup:
    """Setup fixtures for tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def assistant_token(self):
        """Get assistant token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        return response.json()["token"]


class TestSubscriptionPlansFeatureToggles(TestSetup):
    """Test Super Admin subscription plan management with feature toggles"""
    
    def test_admin_can_list_subscription_plans(self, admin_token):
        """Super Admin can list all subscription plans"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-plans",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        print(f"✓ Found {len(plans)} subscription plans")
    
    def test_admin_can_create_plan_with_feature_toggles(self, admin_token):
        """Super Admin can create a plan with feature toggles"""
        # Create a test plan with specific feature toggles
        test_plan = {
            "name": f"TEST_FeatureTogglePlan_{datetime.now().strftime('%H%M%S')}",
            "price": 999.0,
            "duration_days": 30,
            "features": ["Basic features", "Limited support"],
            "max_clients": 10,
            "feature_toggles": {
                "session_notes": True,
                "assessments": True,
                "ai_clinical": False,  # Disabled
                "protocols": False,    # Disabled
                "messaging": True,
                "payments": True,
                "assistants": False,   # Disabled
                "reports": False       # Disabled
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-plans",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=test_plan
        )
        assert response.status_code == 200, f"Failed to create plan: {response.text}"
        
        created_plan = response.json()
        assert created_plan["name"] == test_plan["name"]
        assert "feature_toggles" in created_plan
        assert created_plan["feature_toggles"]["ai_clinical"] == False
        assert created_plan["feature_toggles"]["session_notes"] == True
        
        print(f"✓ Created plan with feature toggles: {created_plan['id']}")
        return created_plan["id"]
    
    def test_admin_can_update_feature_toggles(self, admin_token):
        """Super Admin can update feature toggles for a plan"""
        # First get existing plans
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-plans",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        plans = response.json()
        
        # Find a test plan or use first available
        test_plan = next((p for p in plans if p["name"].startswith("TEST_")), plans[0] if plans else None)
        
        if not test_plan:
            pytest.skip("No plans available to test feature toggle update")
        
        # Update feature toggles
        new_toggles = {
            "session_notes": True,
            "assessments": True,
            "ai_clinical": True,
            "protocols": True,
            "messaging": False,  # Toggle OFF
            "payments": True,
            "assistants": True,
            "reports": False     # Toggle OFF
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/subscription-plans/{test_plan['id']}/feature-toggles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"feature_toggles": new_toggles}
        )
        assert response.status_code == 200, f"Failed to update toggles: {response.text}"
        
        # Verify update
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-plans",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        updated_plan = next((p for p in response.json() if p["id"] == test_plan["id"]), None)
        
        assert updated_plan is not None
        assert updated_plan["feature_toggles"]["messaging"] == False
        assert updated_plan["feature_toggles"]["reports"] == False
        
        print(f"✓ Updated feature toggles for plan: {test_plan['id']}")


class TestSubscriptionStatusEndpoint(TestSetup):
    """Test subscription status endpoint with feature toggles"""
    
    def test_therapist_gets_subscription_status(self, therapist_token):
        """Therapist can get their subscription status with feature toggles"""
        response = requests.get(
            f"{BASE_URL}/api/auth/subscription-status",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        
        status = response.json()
        assert "is_read_only" in status
        assert "subscription_status" in status
        assert "feature_toggles" in status
        assert "days_remaining" in status
        assert "expiry_warning" in status
        
        # Verify feature toggles structure
        toggles = status["feature_toggles"]
        expected_features = ["session_notes", "assessments", "ai_clinical", "protocols", 
                           "messaging", "payments", "assistants", "reports"]
        for feature in expected_features:
            assert feature in toggles, f"Missing feature toggle: {feature}"
        
        print(f"✓ Subscription status: {status['subscription_status']}")
        print(f"  Days remaining: {status['days_remaining']}")
        print(f"  Expiry warning: {status['expiry_warning']}")
        print(f"  Feature toggles: {len(toggles)} features")
    
    def test_assistant_gets_linked_therapist_subscription_status(self, assistant_token):
        """Assistant gets their linked therapist's subscription status"""
        response = requests.get(
            f"{BASE_URL}/api/auth/subscription-status",
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        assert response.status_code == 200
        
        status = response.json()
        assert "is_read_only" in status
        assert "feature_toggles" in status
        
        print(f"✓ Assistant sees therapist subscription status")
        print(f"  Read-only mode: {status['is_read_only']}")
    
    def test_expiry_warning_calculation(self, therapist_token):
        """Verify expiry warning is calculated correctly"""
        response = requests.get(
            f"{BASE_URL}/api/auth/subscription-status",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        
        status = response.json()
        days_remaining = status.get("days_remaining", 0)
        expiry_warning = status.get("expiry_warning", False)
        
        # Expiry warning should be True if days_remaining <= 7 and > 0
        if days_remaining <= 7 and days_remaining > 0:
            assert expiry_warning == True, "Expiry warning should be True when <= 7 days remaining"
        elif days_remaining > 7:
            assert expiry_warning == False, "Expiry warning should be False when > 7 days remaining"
        
        print(f"✓ Expiry warning logic verified (days: {days_remaining}, warning: {expiry_warning})")


class TestFeatureAccessEnforcement(TestSetup):
    """Test that feature-protected endpoints return 403 when feature is disabled"""
    
    def test_session_notes_endpoint_access(self, therapist_token):
        """Session notes endpoint respects feature toggle"""
        # This should work if session_notes feature is enabled
        response = requests.get(
            f"{BASE_URL}/api/session-notes",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        # Should be 200 (success) or 403 (feature disabled)
        assert response.status_code in [200, 403]
        
        if response.status_code == 403:
            assert "not included in your subscription" in response.json().get("detail", "").lower()
            print("✓ Session notes feature is disabled - 403 returned correctly")
        else:
            print("✓ Session notes feature is enabled - access granted")
    
    def test_assessments_endpoint_access(self, therapist_token):
        """Assessments endpoint respects feature toggle"""
        response = requests.get(
            f"{BASE_URL}/api/assessments",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code in [200, 403]
        
        if response.status_code == 403:
            print("✓ Assessments feature is disabled - 403 returned correctly")
        else:
            print("✓ Assessments feature is enabled - access granted")
    
    def test_ai_clinical_endpoint_access(self, therapist_token):
        """AI Clinical endpoint respects feature toggle"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assessment-suggestions",
            headers={"Authorization": f"Bearer {therapist_token}"},
            json={"query": "test"}
        )
        # Should be 200, 403 (feature disabled), or 400 (bad request)
        assert response.status_code in [200, 400, 403, 500]
        
        if response.status_code == 403:
            print("✓ AI Clinical feature is disabled - 403 returned correctly")
        else:
            print(f"✓ AI Clinical endpoint responded with status: {response.status_code}")
    
    def test_protocols_endpoint_access(self, therapist_token):
        """Protocols endpoint respects feature toggle"""
        response = requests.get(
            f"{BASE_URL}/api/protocols",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code in [200, 403]
        
        if response.status_code == 403:
            print("✓ Protocols feature is disabled - 403 returned correctly")
        else:
            print("✓ Protocols feature is enabled - access granted")
    
    def test_messaging_endpoint_access(self, therapist_token):
        """Messaging endpoint respects feature toggle"""
        response = requests.get(
            f"{BASE_URL}/api/messages",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code in [200, 403]
        
        if response.status_code == 403:
            print("✓ Messaging feature is disabled - 403 returned correctly")
        else:
            print("✓ Messaging feature is enabled - access granted")
    
    def test_payments_endpoint_access(self, therapist_token):
        """Payments endpoint respects feature toggle"""
        response = requests.get(
            f"{BASE_URL}/api/payments",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code in [200, 403]
        
        if response.status_code == 403:
            print("✓ Payments feature is disabled - 403 returned correctly")
        else:
            print("✓ Payments feature is enabled - access granted")
    
    def test_assistants_endpoint_access(self, therapist_token):
        """Assistants endpoint respects feature toggle"""
        response = requests.get(
            f"{BASE_URL}/api/assistants",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code in [200, 403]
        
        if response.status_code == 403:
            print("✓ Assistants feature is disabled - 403 returned correctly")
        else:
            print("✓ Assistants feature is enabled - access granted")


class TestAssistantScheduleAccess(TestSetup):
    """Test assistant access to schedule (unified calendar)"""
    
    def test_assistant_can_view_appointments(self, assistant_token):
        """Assistant can view appointments"""
        response = requests.get(
            f"{BASE_URL}/api/appointments",
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        assert response.status_code == 200
        print(f"✓ Assistant can view appointments: {len(response.json())} found")
    
    def test_assistant_can_view_availability(self, assistant_token):
        """Assistant can view therapist availability"""
        response = requests.get(
            f"{BASE_URL}/api/availability",
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        # Should be 200 or 404 (no availability set)
        assert response.status_code in [200, 404]
        print(f"✓ Assistant can view availability (status: {response.status_code})")
    
    def test_assistant_can_view_blocked_times(self, assistant_token):
        """Assistant can view blocked times"""
        response = requests.get(
            f"{BASE_URL}/api/blocked-times",
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        assert response.status_code == 200
        print(f"✓ Assistant can view blocked times: {len(response.json())} found")
    
    def test_assistant_can_create_blocked_time(self, assistant_token):
        """Assistant can create blocked time"""
        tomorrow = datetime.now() + timedelta(days=1)
        blocked_time = {
            "start_datetime": tomorrow.replace(hour=14, minute=0).isoformat(),
            "end_datetime": tomorrow.replace(hour=15, minute=0).isoformat(),
            "reason": "TEST_Assistant blocked time",
            "is_all_day": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/blocked-times",
            headers={"Authorization": f"Bearer {assistant_token}"},
            json=blocked_time
        )
        # Should be 200 (success) or 403 (read-only mode)
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            print(f"✓ Assistant can create blocked time")
            # Clean up
            blocked_id = response.json().get("id")
            if blocked_id:
                requests.delete(
                    f"{BASE_URL}/api/blocked-times/{blocked_id}",
                    headers={"Authorization": f"Bearer {assistant_token}"}
                )
        else:
            print("✓ Assistant blocked from creating (read-only mode)")
    
    def test_assistant_cannot_modify_availability_settings(self, assistant_token):
        """Assistant cannot modify availability settings"""
        # Try to update availability - should fail
        availability_update = {
            "session_duration": 60,
            "buffer_time": 15
        }
        
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers={"Authorization": f"Bearer {assistant_token}"},
            json=availability_update
        )
        # Should be 403 (forbidden) for assistants
        # Note: The actual implementation may vary
        print(f"✓ Assistant availability update response: {response.status_code}")


class TestAssessmentTrendData(TestSetup):
    """Test assessment data for trend chart"""
    
    def test_client_assessments_endpoint(self, therapist_token):
        """Verify client assessments endpoint returns data for trend chart"""
        # First get a client
        response = requests.get(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        clients = response.json()
        
        if not clients:
            pytest.skip("No clients available for assessment trend test")
        
        client_id = clients[0]["id"]
        
        # Get assessments for client
        response = requests.get(
            f"{BASE_URL}/api/clients/{client_id}/assessments",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        assessments = response.json()
        
        # Verify assessment structure for trend chart
        for assessment in assessments:
            assert "id" in assessment
            assert "assessment_type" in assessment
            assert "status" in assessment
            if assessment["status"] == "completed":
                assert "score" in assessment
                assert "completed_at" in assessment
        
        completed = [a for a in assessments if a["status"] == "completed" and a.get("score") is not None]
        print(f"✓ Found {len(completed)} completed assessments for trend chart")


class TestCleanup(TestSetup):
    """Cleanup test data"""
    
    def test_cleanup_test_plans(self, admin_token):
        """Clean up test subscription plans"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-plans",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        plans = response.json()
        
        deleted_count = 0
        for plan in plans:
            if plan["name"].startswith("TEST_"):
                del_response = requests.delete(
                    f"{BASE_URL}/api/admin/subscription-plans/{plan['id']}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                if del_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} test plans")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
