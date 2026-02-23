"""
Public Booking Feature - Backend API Tests
Tests for public booking calendar functionality including:
- Public therapist profile endpoint
- Available slots endpoint
- Public booking creation
- Pending approval endpoint
- Approve/Decline endpoints
"""
import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
THERAPIST_ID = "8210bdef-7566-4f48-a640-eb6ce5d98f6b"


class TestPublicBookingEndpoints:
    """Public Booking APIs - No Auth Required"""
    
    def test_get_public_therapist_profile(self):
        """GET /api/public/therapist/{therapist_id} - returns therapist public info"""
        response = requests.get(f"{BASE_URL}/api/public/therapist/{THERAPIST_ID}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain id"
        assert "name" in data, "Response should contain name"
        assert data["id"] == THERAPIST_ID
        assert "session_duration" in data
        print(f"✓ Public therapist profile: {data['name']}, session: {data['session_duration']}min")
    
    def test_get_public_therapist_not_found(self):
        """GET /api/public/therapist/{invalid_id} - returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/public/therapist/{fake_id}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid therapist ID returns 404")
    
    def test_get_available_slots(self):
        """GET /api/public/therapist/{therapist_id}/slots - returns available time slots"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/public/therapist/{THERAPIST_ID}/slots?date={today}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "slots" in data, "Response should contain slots array"
        assert isinstance(data["slots"], list)
        
        if len(data["slots"]) > 0:
            slot = data["slots"][0]
            assert "start" in slot, "Slot should have start time"
            assert "end" in slot, "Slot should have end time"
            assert "display" in slot, "Slot should have display format"
        
        print(f"✓ Available slots endpoint returned {len(data['slots'])} slots")
    
    def test_create_public_booking_new_client(self):
        """POST /api/public/book - creates booking and client account"""
        # Get an available slot
        today = datetime.now().strftime("%Y-%m-%d")
        slots_response = requests.get(f"{BASE_URL}/api/public/therapist/{THERAPIST_ID}/slots?date={today}")
        assert slots_response.status_code == 200
        
        slots = slots_response.json()["slots"]
        if not slots:
            pytest.skip("No available slots for testing")
        
        # Use a slot from the future
        selected_slot = slots[-1]  # Use last available slot
        
        # Create booking with unique email
        unique_id = str(uuid.uuid4())[:8]
        booking_data = {
            "therapist_id": THERAPIST_ID,
            "slot_start": selected_slot["start"],
            "slot_end": selected_slot["end"],
            "full_name": f"TEST_PublicBooking_{unique_id}",
            "email": f"test_{unique_id}@publicbooking.com",
            "mobile": f"999{uuid.uuid4().int % 10000000:07d}",
            "gender": "male",
            "notes": "Test booking from automated tests"
        }
        
        response = requests.post(f"{BASE_URL}/api/public/book", json=booking_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Booking should be successful"
        assert "appointment_id" in data, "Response should contain appointment_id"
        assert "is_new_client" in data, "Response should indicate if new client"
        
        print(f"✓ Public booking created: {data['appointment_id']}, new_client={data['is_new_client']}")
        
        # Store for cleanup
        return data["appointment_id"]
    
    def test_create_booking_missing_required_fields(self):
        """POST /api/public/book - validates required fields"""
        incomplete_data = {
            "therapist_id": THERAPIST_ID,
            # Missing other required fields
        }
        
        response = requests.post(f"{BASE_URL}/api/public/book", json=incomplete_data)
        
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
        print("✓ Missing fields return validation error")
    
    def test_booking_link_info(self):
        """GET /api/public/booking-link/{therapist_id} - returns booking enabled status"""
        response = requests.get(f"{BASE_URL}/api/public/booking-link/{THERAPIST_ID}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "enabled" in data
        assert data["enabled"] == True, "Public booking should be enabled for this therapist"
        print(f"✓ Booking link info: enabled={data['enabled']}")


class TestAuthenticatedBookingApproval:
    """Authenticated endpoints for approve/decline bookings"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Login as therapist to get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "7275005007",
            "password": "Test@123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Cannot login as therapist")
        
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_pending_approval_appointments(self):
        """GET /api/appointments/pending-approval - returns pending bookings"""
        response = requests.get(f"{BASE_URL}/api/appointments/pending-approval", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "pending_appointments" in data
        assert isinstance(data["pending_appointments"], list)
        
        if len(data["pending_appointments"]) > 0:
            appt = data["pending_appointments"][0]
            assert "id" in appt
            assert "client_name" in appt
            assert "start_time" in appt
            assert appt.get("status") == "pending_approval"
        
        print(f"✓ Pending approvals: {len(data['pending_appointments'])} appointments")
    
    def test_approve_booking_creates_scheduled_appointment(self):
        """POST /api/appointments/{id}/approve - approves pending booking"""
        # First create a new booking to approve
        today = datetime.now().strftime("%Y-%m-%d")
        slots_response = requests.get(f"{BASE_URL}/api/public/therapist/{THERAPIST_ID}/slots?date={today}")
        slots = slots_response.json().get("slots", [])
        
        if not slots:
            pytest.skip("No available slots")
        
        # Create booking
        unique_id = str(uuid.uuid4())[:8]
        booking_data = {
            "therapist_id": THERAPIST_ID,
            "slot_start": slots[0]["start"],
            "slot_end": slots[0]["end"],
            "full_name": f"TEST_Approve_{unique_id}",
            "email": f"approve_{unique_id}@test.com",
            "mobile": f"888{uuid.uuid4().int % 10000000:07d}",
            "notes": "Test for approval"
        }
        
        book_response = requests.post(f"{BASE_URL}/api/public/book", json=booking_data)
        if book_response.status_code != 200:
            pytest.skip("Could not create booking for approval test")
        
        appointment_id = book_response.json()["appointment_id"]
        
        # Approve the booking
        approve_response = requests.post(
            f"{BASE_URL}/api/appointments/{appointment_id}/approve",
            headers=self.headers
        )
        
        assert approve_response.status_code == 200, f"Expected 200, got {approve_response.status_code}: {approve_response.text}"
        
        data = approve_response.json()
        assert data.get("status") == "scheduled", "Approved booking should have 'scheduled' status"
        print(f"✓ Booking approved: {appointment_id}")
        
        # Verify appointment status changed
        appt_response = requests.get(f"{BASE_URL}/api/appointments/{appointment_id}", headers=self.headers)
        assert appt_response.status_code == 200
        assert appt_response.json()["status"] == "scheduled"
        print("✓ Appointment status verified as 'scheduled'")
    
    def test_decline_booking_changes_status(self):
        """POST /api/appointments/{id}/decline - declines pending booking"""
        # First create a new booking to decline
        today = datetime.now().strftime("%Y-%m-%d")
        slots_response = requests.get(f"{BASE_URL}/api/public/therapist/{THERAPIST_ID}/slots?date={today}")
        slots = slots_response.json().get("slots", [])
        
        if len(slots) < 2:
            pytest.skip("Not enough available slots")
        
        # Create booking (use different slot than approve test)
        unique_id = str(uuid.uuid4())[:8]
        booking_data = {
            "therapist_id": THERAPIST_ID,
            "slot_start": slots[1]["start"],  # Use second slot
            "slot_end": slots[1]["end"],
            "full_name": f"TEST_Decline_{unique_id}",
            "email": f"decline_{unique_id}@test.com",
            "mobile": f"777{uuid.uuid4().int % 10000000:07d}",
            "notes": "Test for decline"
        }
        
        book_response = requests.post(f"{BASE_URL}/api/public/book", json=booking_data)
        if book_response.status_code != 200:
            pytest.skip("Could not create booking for decline test")
        
        appointment_id = book_response.json()["appointment_id"]
        
        # Decline the booking
        decline_response = requests.post(
            f"{BASE_URL}/api/appointments/{appointment_id}/decline?reason=Test%20decline",
            headers=self.headers
        )
        
        assert decline_response.status_code == 200, f"Expected 200, got {decline_response.status_code}: {decline_response.text}"
        
        data = decline_response.json()
        assert data.get("status") == "declined", "Declined booking should have 'declined' status"
        print(f"✓ Booking declined: {appointment_id}")
    
    def test_approve_nonexistent_appointment(self):
        """POST /api/appointments/{invalid_id}/approve - returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/appointments/{fake_id}/approve", headers=self.headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Approve invalid appointment returns 404")
    
    def test_decline_nonexistent_appointment(self):
        """POST /api/appointments/{invalid_id}/decline - returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/appointments/{fake_id}/decline", headers=self.headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Decline invalid appointment returns 404")


class TestTherapistProfilePublicBookingSettings:
    """Test therapist profile settings for public booking"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Login as therapist"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "7275005007",
            "password": "Test@123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Cannot login as therapist")
        
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_therapist_profile_has_public_booking_setting(self):
        """GET /api/therapist/profile - includes public_booking_enabled field"""
        response = requests.get(f"{BASE_URL}/api/therapist/profile", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "public_booking_enabled" in data, "Profile should include public_booking_enabled field"
        assert "session_duration" in data, "Profile should include session_duration field"
        
        print(f"✓ Profile has public_booking_enabled={data['public_booking_enabled']}, session_duration={data.get('session_duration')}")
    
    def test_update_public_booking_setting(self):
        """PUT /api/therapist/profile - can toggle public_booking_enabled"""
        # Get current setting
        get_response = requests.get(f"{BASE_URL}/api/therapist/profile", headers=self.headers)
        current_setting = get_response.json().get("public_booking_enabled", False)
        
        # Toggle setting
        update_data = {
            "public_booking_enabled": not current_setting,
            "session_duration": 60
        }
        
        update_response = requests.put(f"{BASE_URL}/api/therapist/profile", headers=self.headers, json=update_data)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        # Verify change
        verify_response = requests.get(f"{BASE_URL}/api/therapist/profile", headers=self.headers)
        new_setting = verify_response.json().get("public_booking_enabled")
        assert new_setting == (not current_setting), "Setting should have been toggled"
        
        # Restore original setting
        restore_data = {"public_booking_enabled": current_setting, "session_duration": 60}
        requests.put(f"{BASE_URL}/api/therapist/profile", headers=self.headers, json=restore_data)
        
        print("✓ Public booking setting can be toggled")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
