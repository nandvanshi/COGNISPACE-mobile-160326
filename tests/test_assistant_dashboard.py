"""
Test Assistant Dashboard Features
- Assistant login
- Dashboard overview API
- Call reminders functionality
- Schedule view with availability
- Payments view
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ASSISTANT_EMAIL = "test_assistant_ui@test.com"
ASSISTANT_PASSWORD = "testpass123"
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "password"


class TestAssistantLogin:
    """Test assistant login functionality"""
    
    def test_assistant_login_success(self):
        """Test assistant can login with email and password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["role"] == "assistant", f"Expected role 'assistant', got {data['user']['role']}"
        assert data["user"]["email"] == ASSISTANT_EMAIL, f"Email mismatch"
        assert data["user"]["therapist_id"] is not None, "therapist_id should be set for assistant"
        
        print(f"SUCCESS: Assistant login successful - {data['user']['full_name']}")
        return data["token"]
    
    def test_assistant_login_invalid_password(self):
        """Test assistant login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Invalid password correctly rejected")


class TestAssistantDashboard:
    """Test assistant dashboard API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        
        self.token = response.json()["token"]
        self.user = response.json()["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_overview_api(self):
        """Test GET /api/assistant/dashboard returns correct data structure"""
        response = requests.get(f"{BASE_URL}/api/assistant/dashboard", headers=self.headers)
        
        print(f"Dashboard response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify required fields
        assert "therapist" in data, "Missing 'therapist' field"
        assert "today_date" in data, "Missing 'today_date' field"
        assert "today_day" in data, "Missing 'today_day' field"
        assert "todays_appointments" in data, "Missing 'todays_appointments' field"
        assert "needs_attention" in data, "Missing 'needs_attention' field"
        assert "inactive_clients" in data, "Missing 'inactive_clients' field"
        assert "payments_summary" in data, "Missing 'payments_summary' field"
        
        # Verify therapist info
        assert "full_name" in data["therapist"], "Missing therapist full_name"
        
        # Verify date format (DD/MM/YYYY)
        today_date = data["today_date"]
        assert len(today_date.split("/")) == 3, f"Date format should be DD/MM/YYYY, got {today_date}"
        
        # Verify needs_attention structure
        needs_attention = data["needs_attention"]
        assert "upcoming_sessions" in needs_attention, "Missing upcoming_sessions"
        assert "pending_checkins" in needs_attention, "Missing pending_checkins"
        assert "pending_payments_count" in needs_attention, "Missing pending_payments_count"
        
        # Verify payments_summary structure
        payments = data["payments_summary"]
        assert "cash_total" in payments, "Missing cash_total"
        assert "online_total" in payments, "Missing online_total"
        assert "total" in payments, "Missing total"
        assert "payments" in payments, "Missing payments list"
        
        print(f"SUCCESS: Dashboard API returns correct structure")
        print(f"  - Therapist: {data['therapist']['full_name']}")
        print(f"  - Today: {data['today_date']} ({data['today_day']})")
        print(f"  - Appointments today: {len(data['todays_appointments'])}")
        print(f"  - Inactive clients: {data.get('inactive_clients_count', len(data['inactive_clients']))}")
    
    def test_dashboard_only_accessible_by_assistant(self):
        """Test that dashboard endpoint rejects non-assistant users"""
        # Login as therapist
        therapist_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        
        if therapist_response.status_code != 200:
            pytest.skip("Therapist login failed")
        
        therapist_token = therapist_response.json()["token"]
        therapist_headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Try to access assistant dashboard as therapist
        response = requests.get(f"{BASE_URL}/api/assistant/dashboard", headers=therapist_headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("SUCCESS: Dashboard correctly rejects non-assistant users")


class TestCallReminders:
    """Test call reminder functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_mark_called_requires_valid_appointment(self):
        """Test that mark called requires a valid appointment ID"""
        response = requests.post(
            f"{BASE_URL}/api/assistant/call-reminder/invalid-appointment-id",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Invalid appointment ID correctly rejected")
    
    def test_call_reminder_flow(self):
        """Test the full call reminder flow if there are appointments"""
        # Get dashboard to find appointments
        dashboard_response = requests.get(f"{BASE_URL}/api/assistant/dashboard", headers=self.headers)
        
        if dashboard_response.status_code != 200:
            pytest.skip("Could not get dashboard")
        
        appointments = dashboard_response.json().get("todays_appointments", [])
        
        if not appointments:
            print("INFO: No appointments today to test call reminders")
            return
        
        # Test marking first appointment as called
        appt_id = appointments[0]["id"]
        
        # Mark as called
        mark_response = requests.post(
            f"{BASE_URL}/api/assistant/call-reminder/{appt_id}",
            headers=self.headers
        )
        
        assert mark_response.status_code == 200, f"Mark called failed: {mark_response.text}"
        print(f"SUCCESS: Marked appointment {appt_id} as called")
        
        # Verify it's marked in dashboard
        dashboard_response2 = requests.get(f"{BASE_URL}/api/assistant/dashboard", headers=self.headers)
        appointments2 = dashboard_response2.json().get("todays_appointments", [])
        
        marked_appt = next((a for a in appointments2 if a["id"] == appt_id), None)
        if marked_appt:
            assert marked_appt.get("call_status") == "called", f"Expected 'called', got {marked_appt.get('call_status')}"
            print("SUCCESS: Call status updated in dashboard")
        
        # Unmark (reset)
        unmark_response = requests.delete(
            f"{BASE_URL}/api/assistant/call-reminder/{appt_id}",
            headers=self.headers
        )
        
        assert unmark_response.status_code == 200, f"Unmark failed: {unmark_response.text}"
        print("SUCCESS: Call reminder reset")


class TestAssistantScheduleAccess:
    """Test assistant access to schedule/availability"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        
        self.token = response.json()["token"]
        self.user = response.json()["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_assistant_can_view_availability(self):
        """Test assistant can view therapist's availability"""
        response = requests.get(f"{BASE_URL}/api/availability", headers=self.headers)
        
        print(f"Availability response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify availability structure
        assert "session_duration" in data, "Missing session_duration"
        assert "buffer_time" in data, "Missing buffer_time"
        
        # Check day availability
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            assert day in data, f"Missing {day} availability"
            assert "enabled" in data[day], f"Missing enabled for {day}"
            assert "time_blocks" in data[day], f"Missing time_blocks for {day}"
        
        print(f"SUCCESS: Assistant can view availability")
        print(f"  - Session duration: {data['session_duration']} min")
        print(f"  - Buffer time: {data['buffer_time']} min")
        
        # Count enabled days
        enabled_days = [d for d in days if data[d].get("enabled")]
        print(f"  - Enabled days: {len(enabled_days)} ({', '.join(enabled_days) if enabled_days else 'none'})")
        
        return data
    
    def test_assistant_cannot_update_availability(self):
        """Test assistant CANNOT update therapist's availability"""
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=self.headers,
            json={
                "session_duration": 45
            }
        )
        
        # Should be 403 Forbidden - only therapists can update availability
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("SUCCESS: Assistant correctly blocked from updating availability")
    
    def test_assistant_can_view_appointments(self):
        """Test assistant can view appointments"""
        response = requests.get(f"{BASE_URL}/api/appointments", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of appointments"
        
        print(f"SUCCESS: Assistant can view appointments ({len(data)} total)")
    
    def test_assistant_can_view_clients(self):
        """Test assistant can view clients"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of clients"
        
        print(f"SUCCESS: Assistant can view clients ({len(data)} total)")
    
    def test_assistant_can_view_blocked_times(self):
        """Test assistant can view blocked times"""
        response = requests.get(f"{BASE_URL}/api/blocked-times", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of blocked times"
        
        print(f"SUCCESS: Assistant can view blocked times ({len(data)} total)")
    
    def test_assistant_can_create_blocked_time(self):
        """Test assistant CAN create blocked time"""
        # Create a blocked time for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/blocked-times",
            headers=self.headers,
            json={
                "start_datetime": f"{tomorrow}T10:00:00",
                "end_datetime": f"{tomorrow}T11:00:00",
                "reason": "Test block by assistant",
                "is_all_day": False
            }
        )
        
        print(f"Create blocked time response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        block_id = data.get("id")
        
        print(f"SUCCESS: Assistant can create blocked time (ID: {block_id})")
        
        # Clean up - delete the blocked time
        if block_id:
            delete_response = requests.delete(
                f"{BASE_URL}/api/blocked-times/{block_id}",
                headers=self.headers
            )
            print(f"Cleanup: Deleted blocked time - {delete_response.status_code}")


class TestAssistantPaymentsAccess:
    """Test assistant access to payments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_assistant_can_view_payments(self):
        """Test assistant can view payments"""
        response = requests.get(f"{BASE_URL}/api/payments", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of payments"
        
        print(f"SUCCESS: Assistant can view payments ({len(data)} total)")


class TestAssistantClinicalRestrictions:
    """Test that assistant CANNOT access clinical data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_assistant_cannot_access_session_notes(self):
        """Test assistant cannot access session notes"""
        response = requests.get(f"{BASE_URL}/api/session-notes", headers=self.headers)
        
        # Should be 403 - clinical data restricted
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("SUCCESS: Assistant correctly blocked from session notes")
    
    def test_assistant_cannot_access_assessments(self):
        """Test assistant cannot access assessments"""
        response = requests.get(f"{BASE_URL}/api/assessments", headers=self.headers)
        
        # Should be 403 - clinical data restricted
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("SUCCESS: Assistant correctly blocked from assessments")
    
    def test_assistant_cannot_access_protocols(self):
        """Test assistant cannot access protocols"""
        response = requests.get(f"{BASE_URL}/api/protocols", headers=self.headers)
        
        # Should be 403 - clinical data restricted
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("SUCCESS: Assistant correctly blocked from protocols")


class TestSubscriptionStatus:
    """Test subscription status for assistant"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_assistant_gets_therapist_subscription_status(self):
        """Test assistant gets linked therapist's subscription status"""
        response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert "is_read_only" in data, "Missing is_read_only"
        assert "subscription_status" in data, "Missing subscription_status"
        assert "feature_toggles" in data, "Missing feature_toggles"
        
        print(f"SUCCESS: Assistant gets subscription status")
        print(f"  - Read-only: {data['is_read_only']}")
        print(f"  - Status: {data['subscription_status']}")
        print(f"  - Plan: {data.get('subscription_plan')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
