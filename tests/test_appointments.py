"""
Appointment Calendar Feature Tests
Tests for: Create, Update, Complete, Cancel, Delete appointments
Double-booking prevention, Status filtering, Read-only mode
"""
import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "TestPass123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Known test client ID from context
TEST_CLIENT_ID = "c283749c-2c50-48d7-94bf-e4588247883d"


class TestAppointmentSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get super admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def therapist_headers(self, therapist_token):
        """Headers with therapist auth token"""
        return {
            "Authorization": f"Bearer {therapist_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Headers with admin auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_therapist_login(self, therapist_token):
        """Verify therapist can login"""
        assert therapist_token is not None
        assert len(therapist_token) > 0
        print(f"✓ Therapist login successful")
    
    def test_get_clients_list(self, therapist_headers):
        """Verify therapist can get clients list"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=therapist_headers)
        assert response.status_code == 200
        clients = response.json()
        assert isinstance(clients, list)
        print(f"✓ Found {len(clients)} clients")
        # Store first client ID for tests
        if clients:
            return clients[0]["id"]
        return None


class TestAppointmentCRUD:
    """Test Create, Read, Update, Delete operations for appointments"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_headers(self, therapist_token):
        return {
            "Authorization": f"Bearer {therapist_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def client_id(self, therapist_headers):
        """Get a valid client ID for testing"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=therapist_headers)
        assert response.status_code == 200
        clients = response.json()
        if clients:
            return clients[0]["id"]
        pytest.skip("No clients available for testing")
    
    def test_create_appointment(self, therapist_headers, client_id):
        """Test creating a new appointment"""
        # Schedule appointment far in the future with unique time to avoid conflicts
        future_date = datetime.now() + timedelta(days=50)
        start_time = future_date.replace(hour=8, minute=30, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        payload = {
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Appointment - Initial session"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=payload, headers=therapist_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["client_id"] == client_id
        assert data["status"] == "scheduled"
        assert data["notes"] == "TEST_Appointment - Initial session"
        
        print(f"✓ Created appointment: {data['id']}")
        return data["id"]
    
    def test_get_appointments_list(self, therapist_headers):
        """Test getting list of appointments"""
        response = requests.get(f"{BASE_URL}/api/appointments", headers=therapist_headers)
        assert response.status_code == 200
        
        appointments = response.json()
        assert isinstance(appointments, list)
        print(f"✓ Retrieved {len(appointments)} appointments")
    
    def test_get_single_appointment(self, therapist_headers, client_id):
        """Test getting a single appointment by ID"""
        # First create an appointment
        tomorrow = datetime.now() + timedelta(days=2)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Single appointment test"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Get the appointment
        response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == appt_id
        assert data["client_id"] == client_id
        print(f"✓ Retrieved single appointment: {appt_id}")
    
    def test_update_appointment_reschedule(self, therapist_headers, client_id):
        """Test updating appointment time (reschedule)"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=3)
        start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Reschedule test"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Reschedule to different time
        new_start = start_time + timedelta(hours=2)
        new_end = new_start + timedelta(hours=1)
        
        update_response = requests.put(f"{BASE_URL}/api/appointments/{appt_id}", json={
            "start_time": new_start.isoformat(),
            "end_time": new_end.isoformat()
        }, headers=therapist_headers)
        assert update_response.status_code == 200
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 200
        updated_data = get_response.json()
        
        # Parse and compare times
        updated_start = datetime.fromisoformat(updated_data["start_time"].replace("Z", "+00:00"))
        expected_start = new_start.replace(tzinfo=updated_start.tzinfo)
        assert updated_start.hour == expected_start.hour
        print(f"✓ Rescheduled appointment: {appt_id}")
    
    def test_update_appointment_notes(self, therapist_headers, client_id):
        """Test updating appointment notes"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=4)
        start_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Original notes"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Update notes
        update_response = requests.put(f"{BASE_URL}/api/appointments/{appt_id}", json={
            "notes": "TEST_Updated notes - focus on anxiety management"
        }, headers=therapist_headers)
        assert update_response.status_code == 200
        
        # Verify update persisted
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 200
        assert get_response.json()["notes"] == "TEST_Updated notes - focus on anxiety management"
        print(f"✓ Updated appointment notes: {appt_id}")
    
    def test_delete_appointment(self, therapist_headers, client_id):
        """Test deleting an appointment"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=5)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Delete test"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Delete appointment
        delete_response = requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 404
        print(f"✓ Deleted appointment: {appt_id}")


class TestAppointmentStatus:
    """Test appointment status changes: complete, cancel"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_headers(self, therapist_token):
        return {
            "Authorization": f"Bearer {therapist_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def client_id(self, therapist_headers):
        response = requests.get(f"{BASE_URL}/api/clients", headers=therapist_headers)
        assert response.status_code == 200
        clients = response.json()
        if clients:
            return clients[0]["id"]
        pytest.skip("No clients available for testing")
    
    def test_complete_appointment(self, therapist_headers, client_id):
        """Test marking appointment as completed via POST endpoint"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=6)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Complete test"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Complete appointment via POST endpoint
        complete_response = requests.post(f"{BASE_URL}/api/appointments/{appt_id}/complete", headers=therapist_headers)
        assert complete_response.status_code == 200
        
        # Verify status changed
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "completed"
        print(f"✓ Completed appointment: {appt_id}")
    
    def test_cancel_appointment(self, therapist_headers, client_id):
        """Test cancelling appointment via POST endpoint"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=7)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Cancel test"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Cancel appointment via POST endpoint
        cancel_response = requests.post(f"{BASE_URL}/api/appointments/{appt_id}/cancel", headers=therapist_headers)
        assert cancel_response.status_code == 200
        
        # Verify status changed
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "cancelled"
        print(f"✓ Cancelled appointment: {appt_id}")
    
    def test_cannot_complete_cancelled_appointment(self, therapist_headers, client_id):
        """Test that cancelled appointments cannot be completed"""
        # Create and cancel appointment
        tomorrow = datetime.now() + timedelta(days=8)
        start_time = tomorrow.replace(hour=16, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Cannot complete cancelled"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Cancel it
        requests.post(f"{BASE_URL}/api/appointments/{appt_id}/cancel", headers=therapist_headers)
        
        # Try to complete - should fail
        complete_response = requests.post(f"{BASE_URL}/api/appointments/{appt_id}/complete", headers=therapist_headers)
        assert complete_response.status_code == 400
        print(f"✓ Correctly rejected completing cancelled appointment")
    
    def test_cannot_cancel_completed_appointment(self, therapist_headers, client_id):
        """Test that completed appointments cannot be cancelled"""
        # Create and complete appointment
        tomorrow = datetime.now() + timedelta(days=9)
        start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Cannot cancel completed"
        }, headers=therapist_headers)
        assert create_response.status_code == 200
        appt_id = create_response.json()["id"]
        
        # Complete it
        requests.post(f"{BASE_URL}/api/appointments/{appt_id}/complete", headers=therapist_headers)
        
        # Try to cancel - should fail
        cancel_response = requests.post(f"{BASE_URL}/api/appointments/{appt_id}/cancel", headers=therapist_headers)
        assert cancel_response.status_code == 400
        print(f"✓ Correctly rejected cancelling completed appointment")


class TestDoubleBookingPrevention:
    """Test double-booking prevention logic"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_headers(self, therapist_token):
        return {
            "Authorization": f"Bearer {therapist_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def client_id(self, therapist_headers):
        response = requests.get(f"{BASE_URL}/api/clients", headers=therapist_headers)
        assert response.status_code == 200
        clients = response.json()
        if clients:
            return clients[0]["id"]
        pytest.skip("No clients available for testing")
    
    def test_double_booking_exact_overlap(self, therapist_headers, client_id):
        """Test that exact time overlap is rejected"""
        # Use a unique time slot far in the future
        future_date = datetime.now() + timedelta(days=30)
        start_time = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        # Create first appointment
        first_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Double booking - first"
        }, headers=therapist_headers)
        assert first_response.status_code == 200
        first_appt_id = first_response.json()["id"]
        
        # Try to create second appointment at same time - should fail
        second_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Double booking - second (should fail)"
        }, headers=therapist_headers)
        assert second_response.status_code == 400
        assert "already booked" in second_response.json()["detail"].lower()
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{first_appt_id}", headers=therapist_headers)
        print(f"✓ Double booking (exact overlap) correctly rejected")
    
    def test_double_booking_partial_overlap(self, therapist_headers, client_id):
        """Test that partial time overlap is rejected"""
        future_date = datetime.now() + timedelta(days=31)
        start_time = future_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        # Create first appointment 14:00-15:00
        first_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Partial overlap - first"
        }, headers=therapist_headers)
        assert first_response.status_code == 200
        first_appt_id = first_response.json()["id"]
        
        # Try to create overlapping appointment 14:30-15:30 - should fail
        overlap_start = start_time + timedelta(minutes=30)
        overlap_end = overlap_start + timedelta(hours=1)
        
        second_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": overlap_start.isoformat(),
            "end_time": overlap_end.isoformat(),
            "notes": "TEST_Partial overlap - second (should fail)"
        }, headers=therapist_headers)
        assert second_response.status_code == 400
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{first_appt_id}", headers=therapist_headers)
        print(f"✓ Double booking (partial overlap) correctly rejected")
    
    def test_cancelled_appointments_allow_rebooking(self, therapist_headers, client_id):
        """Test that cancelled appointments don't block new bookings"""
        future_date = datetime.now() + timedelta(days=32)
        start_time = future_date.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        # Create and cancel first appointment
        first_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Cancelled slot - first"
        }, headers=therapist_headers)
        assert first_response.status_code == 200
        first_appt_id = first_response.json()["id"]
        
        # Cancel it
        cancel_response = requests.post(f"{BASE_URL}/api/appointments/{first_appt_id}/cancel", headers=therapist_headers)
        assert cancel_response.status_code == 200
        
        # Create new appointment at same time - should succeed
        second_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Cancelled slot - rebooking"
        }, headers=therapist_headers)
        assert second_response.status_code == 200
        second_appt_id = second_response.json()["id"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{second_appt_id}", headers=therapist_headers)
        print(f"✓ Rebooking cancelled slot works correctly")
    
    def test_adjacent_appointments_allowed(self, therapist_headers, client_id):
        """Test that back-to-back appointments are allowed"""
        future_date = datetime.now() + timedelta(days=33)
        start_time1 = future_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time1 = start_time1 + timedelta(hours=1)
        
        # Create first appointment 9:00-10:00
        first_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time1.isoformat(),
            "end_time": end_time1.isoformat(),
            "notes": "TEST_Adjacent - first"
        }, headers=therapist_headers)
        assert first_response.status_code == 200
        first_appt_id = first_response.json()["id"]
        
        # Create adjacent appointment 10:00-11:00 - should succeed
        start_time2 = end_time1
        end_time2 = start_time2 + timedelta(hours=1)
        
        second_response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time2.isoformat(),
            "end_time": end_time2.isoformat(),
            "notes": "TEST_Adjacent - second"
        }, headers=therapist_headers)
        assert second_response.status_code == 200
        second_appt_id = second_response.json()["id"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{first_appt_id}", headers=therapist_headers)
        requests.delete(f"{BASE_URL}/api/appointments/{second_appt_id}", headers=therapist_headers)
        print(f"✓ Adjacent (back-to-back) appointments allowed")


class TestReadOnlyMode:
    """Test that expired subscription therapists cannot create/update appointments"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_active_therapist_can_create_appointments(self):
        """Verify active subscription therapist can create appointments"""
        # Login as active therapist
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Check subscription status
        status_response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Should not be read-only
        assert status_data["is_read_only"] == False, "Active therapist should not be in read-only mode"
        print(f"✓ Active therapist subscription status: {status_data['subscription_status']}")
        print(f"✓ Active therapist is_read_only: {status_data['is_read_only']}")


class TestAppointmentValidation:
    """Test input validation for appointments"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_headers(self, therapist_token):
        return {
            "Authorization": f"Bearer {therapist_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def client_id(self, therapist_headers):
        response = requests.get(f"{BASE_URL}/api/clients", headers=therapist_headers)
        assert response.status_code == 200
        clients = response.json()
        if clients:
            return clients[0]["id"]
        pytest.skip("No clients available for testing")
    
    def test_end_time_must_be_after_start_time(self, therapist_headers, client_id):
        """Test that end time must be after start time"""
        tomorrow = datetime.now() + timedelta(days=40)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time - timedelta(hours=1)  # End before start
        
        response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Invalid times"
        }, headers=therapist_headers)
        assert response.status_code == 400
        print(f"✓ Invalid time range correctly rejected")
    
    def test_invalid_client_id_rejected(self, therapist_headers):
        """Test that invalid client ID is rejected"""
        tomorrow = datetime.now() + timedelta(days=41)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        response = requests.post(f"{BASE_URL}/api/appointments", json={
            "client_id": "invalid-client-id-12345",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Invalid client"
        }, headers=therapist_headers)
        assert response.status_code == 404
        print(f"✓ Invalid client ID correctly rejected")
    
    def test_appointment_not_found(self, therapist_headers):
        """Test 404 for non-existent appointment"""
        response = requests.get(f"{BASE_URL}/api/appointments/non-existent-id-12345", headers=therapist_headers)
        assert response.status_code == 404
        print(f"✓ Non-existent appointment returns 404")


# Cleanup fixture to remove test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_appointments():
    """Cleanup TEST_ prefixed appointments after all tests"""
    yield
    # Cleanup after tests
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        if login_response.status_code == 200:
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            # Get all appointments
            appts_response = requests.get(f"{BASE_URL}/api/appointments", headers=headers)
            if appts_response.status_code == 200:
                appointments = appts_response.json()
                for appt in appointments:
                    if appt.get("notes", "").startswith("TEST_"):
                        requests.delete(f"{BASE_URL}/api/appointments/{appt['id']}", headers=headers)
                print("✓ Cleaned up test appointments")
    except Exception as e:
        print(f"Cleanup warning: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
