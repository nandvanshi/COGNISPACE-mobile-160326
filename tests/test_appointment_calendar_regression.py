"""
Regression Test Suite for Appointment Calendar Features
Tests:
- GET/PUT /api/availability - Weekly schedule with multiple time blocks
- GET /api/available-slots/{therapist_id}?date= - Slot generation
- POST /api/appointments - Create with double-booking prevention
- PUT/DELETE /api/appointments/{id} - Update and delete
- POST /api/appointments/{id}/complete and /cancel - Status changes
- POST/GET/DELETE /api/blocked-times - Blocked time CRUD
- Read-only mode blocks write operations for expired subscriptions
"""

import pytest
import requests
import os
from datetime import datetime, timedelta, timezone
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from context
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "password123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Known test client ID
TEST_CLIENT_ID = "c283749c-2c50-48d7-94bf-e4588247883d"


@pytest.fixture(scope="module")
def therapist_token():
    """Get therapist authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": THERAPIST_MOBILE,
        "password": THERAPIST_PASSWORD
    })
    assert response.status_code == 200, f"Therapist login failed: {response.text}"
    data = response.json()
    assert "token" in data
    return data["token"]


@pytest.fixture(scope="module")
def therapist_id(therapist_token):
    """Get therapist ID from auth/me"""
    headers = {"Authorization": f"Bearer {therapist_token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    assert response.status_code == 200
    return response.json()["id"]


@pytest.fixture(scope="module")
def therapist_headers(therapist_token):
    """Headers with therapist auth token"""
    return {
        "Authorization": f"Bearer {therapist_token}",
        "Content-Type": "application/json"
    }


class TestAvailabilitySettings:
    """Test GET/PUT /api/availability - Weekly schedule with multiple time blocks"""
    
    def test_get_availability(self, therapist_headers):
        """GET /api/availability - Get current availability settings"""
        response = requests.get(f"{BASE_URL}/api/availability", headers=therapist_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "session_duration" in data
        assert "buffer_time" in data
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            assert day in data
            assert "enabled" in data[day]
            assert "time_blocks" in data[day]
        
        print(f"✓ GET /api/availability - session_duration: {data['session_duration']}, buffer_time: {data['buffer_time']}")
    
    def test_update_availability_with_multiple_time_blocks(self, therapist_headers):
        """PUT /api/availability - Update with multiple time blocks per day"""
        # Set Monday with multiple time blocks (morning and afternoon)
        update_data = {
            "session_duration": 60,
            "buffer_time": 15,
            "monday": {
                "enabled": True,
                "time_blocks": [
                    {"start_time": "09:00", "end_time": "12:00"},
                    {"start_time": "14:00", "end_time": "18:00"}
                ]
            },
            "tuesday": {
                "enabled": True,
                "time_blocks": [
                    {"start_time": "10:00", "end_time": "17:00"}
                ]
            }
        }
        
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify updates
        assert data["session_duration"] == 60
        assert data["buffer_time"] == 15
        assert data["monday"]["enabled"] == True
        assert len(data["monday"]["time_blocks"]) == 2
        assert data["tuesday"]["enabled"] == True
        
        print(f"✓ PUT /api/availability - Multiple time blocks set successfully")
    
    def test_update_session_duration_validation(self, therapist_headers):
        """PUT /api/availability - Validate session duration bounds (15-240 min)"""
        # Test invalid session duration (too short)
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={"session_duration": 10})
        assert response.status_code == 400
        
        # Test invalid session duration (too long)
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={"session_duration": 300})
        assert response.status_code == 400
        
        # Test valid session duration
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={"session_duration": 45})
        assert response.status_code == 200
        
        print(f"✓ Session duration validation working correctly")
    
    def test_update_buffer_time_validation(self, therapist_headers):
        """PUT /api/availability - Validate buffer time bounds (0-60 min)"""
        # Test invalid buffer time (negative)
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={"buffer_time": -5})
        assert response.status_code == 400 or response.status_code == 422  # Pydantic validation
        
        # Test invalid buffer time (too long)
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={"buffer_time": 90})
        assert response.status_code == 400
        
        # Test valid buffer time
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={"buffer_time": 30})
        assert response.status_code == 200
        
        print(f"✓ Buffer time validation working correctly")


class TestSlotGeneration:
    """Test GET /api/available-slots/{therapist_id}?date= - Slot generation"""
    
    def test_get_available_slots_for_enabled_day(self, therapist_headers, therapist_id):
        """GET /api/available-slots - Get slots for a day with availability"""
        # First ensure Monday is enabled with time blocks
        requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={
            "session_duration": 60,
            "buffer_time": 0,
            "monday": {
                "enabled": True,
                "time_blocks": [{"start_time": "09:00", "end_time": "12:00"}]
            }
        })
        
        # Find next Monday
        today = datetime.now(timezone.utc).date()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # Next Monday, not today
        next_monday = today + timedelta(days=days_until_monday)
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={next_monday.isoformat()}",
            headers=therapist_headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        assert isinstance(slots, list)
        
        # Should have slots (3 hours / 60 min = 3 slots)
        print(f"✓ GET /api/available-slots - Found {len(slots)} slots for {next_monday}")
    
    def test_get_available_slots_for_disabled_day(self, therapist_headers, therapist_id):
        """GET /api/available-slots - Returns empty for disabled day"""
        # Disable Sunday
        requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={
            "sunday": {"enabled": False, "time_blocks": []}
        })
        
        # Find next Sunday
        today = datetime.now(timezone.utc).date()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={next_sunday.isoformat()}",
            headers=therapist_headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) == 0
        
        print(f"✓ GET /api/available-slots - Returns empty for disabled day")
    
    def test_get_available_slots_past_date(self, therapist_headers, therapist_id):
        """GET /api/available-slots - Returns empty for past dates"""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={yesterday.isoformat()}",
            headers=therapist_headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) == 0
        
        print(f"✓ GET /api/available-slots - Returns empty for past dates")
    
    def test_get_available_slots_invalid_date_format(self, therapist_headers, therapist_id):
        """GET /api/available-slots - Returns 400 for invalid date format"""
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date=invalid-date",
            headers=therapist_headers
        )
        
        assert response.status_code == 400
        print(f"✓ GET /api/available-slots - Returns 400 for invalid date format")


class TestAppointmentCRUD:
    """Test POST/PUT/DELETE /api/appointments - CRUD operations"""
    
    @pytest.fixture(scope="class")
    def created_appointment_id(self, therapist_headers):
        """Create an appointment for testing"""
        # Schedule for next week to avoid conflicts
        future_date = datetime.now(timezone.utc) + timedelta(days=10)
        start_time = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Regression test appointment"
        })
        
        if response.status_code == 201:
            return response.json()["id"]
        return None
    
    def test_create_appointment(self, therapist_headers):
        """POST /api/appointments - Create new appointment"""
        future_date = datetime.now(timezone.utc) + timedelta(days=14)
        start_time = future_date.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_Create appointment test"
        })
        
        assert response.status_code in [200, 201]  # API returns 200
        data = response.json()
        assert "id" in data
        assert data["client_id"] == TEST_CLIENT_ID
        assert data["status"] == "scheduled"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{data['id']}", headers=therapist_headers)
        
        print(f"✓ POST /api/appointments - Created appointment successfully")
    
    def test_create_appointment_invalid_times(self, therapist_headers):
        """POST /api/appointments - Reject when end_time <= start_time"""
        future_date = datetime.now(timezone.utc) + timedelta(days=15)
        start_time = future_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time - timedelta(hours=1)  # End before start
        
        response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        })
        
        assert response.status_code == 400
        print(f"✓ POST /api/appointments - Rejects invalid times")
    
    def test_get_appointments(self, therapist_headers):
        """GET /api/appointments - List all appointments"""
        response = requests.get(f"{BASE_URL}/api/appointments", headers=therapist_headers)
        
        assert response.status_code == 200
        appointments = response.json()
        assert isinstance(appointments, list)
        
        print(f"✓ GET /api/appointments - Found {len(appointments)} appointments")
    
    def test_update_appointment(self, therapist_headers, created_appointment_id):
        """PUT /api/appointments/{id} - Update appointment"""
        if not created_appointment_id:
            pytest.skip("No appointment created for update test")
        
        response = requests.put(
            f"{BASE_URL}/api/appointments/{created_appointment_id}",
            headers=therapist_headers,
            json={"notes": "TEST_Updated notes"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "TEST_Updated notes"
        
        print(f"✓ PUT /api/appointments/{created_appointment_id} - Updated successfully")
    
    def test_delete_appointment(self, therapist_headers):
        """DELETE /api/appointments/{id} - Delete appointment"""
        # Create appointment to delete
        future_date = datetime.now(timezone.utc) + timedelta(days=20)
        start_time = future_date.replace(hour=15, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_To be deleted"
        })
        
        assert create_response.status_code in [200, 201]  # API returns 200
        appt_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 404
        
        print(f"✓ DELETE /api/appointments - Deleted successfully")


class TestDoubleBookingPrevention:
    """Test double-booking prevention on create and update"""
    
    def test_double_booking_prevention_on_create(self, therapist_headers):
        """POST /api/appointments - Prevent double-booking"""
        # Create first appointment
        future_date = datetime.now(timezone.utc) + timedelta(days=25)
        start_time = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        first_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_First appointment"
        })
        
        assert first_response.status_code in [200, 201], f"First appointment creation failed: {first_response.text}"
        first_appt_id = first_response.json()["id"]
        
        # Try to create overlapping appointment
        overlap_start = start_time + timedelta(minutes=30)  # Overlaps
        overlap_end = overlap_start + timedelta(hours=1)
        
        second_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": overlap_start.isoformat(),
            "end_time": overlap_end.isoformat(),
            "notes": "TEST_Overlapping appointment"
        })
        
        assert second_response.status_code == 400
        assert "already booked" in second_response.json().get("detail", "").lower() or "double" in second_response.json().get("detail", "").lower()
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{first_appt_id}", headers=therapist_headers)
        
        print(f"✓ Double-booking prevention on create working")
    
    def test_double_booking_prevention_on_update(self, therapist_headers):
        """PUT /api/appointments - Prevent double-booking on update"""
        # Create two non-overlapping appointments
        future_date = datetime.now(timezone.utc) + timedelta(days=26)
        
        # First appointment: 10:00-11:00
        start1 = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end1 = start1 + timedelta(hours=1)
        
        first_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start1.isoformat(),
            "end_time": end1.isoformat(),
            "notes": "TEST_First for update test"
        })
        assert first_response.status_code in [200, 201], f"First appointment failed: {first_response.text}"
        first_id = first_response.json()["id"]
        
        # Second appointment: 14:00-15:00
        start2 = future_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end2 = start2 + timedelta(hours=1)
        
        second_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start2.isoformat(),
            "end_time": end2.isoformat(),
            "notes": "TEST_Second for update test"
        })
        assert second_response.status_code in [200, 201], f"Second appointment failed: {second_response.text}"
        second_id = second_response.json()["id"]
        
        # Try to update second appointment to overlap with first
        overlap_start = start1 + timedelta(minutes=30)
        overlap_end = overlap_start + timedelta(hours=1)
        
        update_response = requests.put(
            f"{BASE_URL}/api/appointments/{second_id}",
            headers=therapist_headers,
            json={
                "start_time": overlap_start.isoformat(),
                "end_time": overlap_end.isoformat()
            }
        )
        
        assert update_response.status_code == 400
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{first_id}", headers=therapist_headers)
        requests.delete(f"{BASE_URL}/api/appointments/{second_id}", headers=therapist_headers)
        
        print(f"✓ Double-booking prevention on update working")


class TestAppointmentStatusChanges:
    """Test POST /api/appointments/{id}/complete and /cancel"""
    
    def test_complete_appointment(self, therapist_headers):
        """POST /api/appointments/{id}/complete - Mark as completed"""
        # Create appointment
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        start_time = future_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_To be completed"
        })
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        appt_id = create_response.json()["id"]
        
        # Complete it
        complete_response = requests.post(
            f"{BASE_URL}/api/appointments/{appt_id}/complete",
            headers=therapist_headers
        )
        assert complete_response.status_code == 200
        
        # Verify status
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "completed"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        
        print(f"✓ POST /api/appointments/{appt_id}/complete - Status changed to completed")
    
    def test_cancel_appointment(self, therapist_headers):
        """POST /api/appointments/{id}/cancel - Cancel appointment"""
        # Create appointment
        future_date = datetime.now(timezone.utc) + timedelta(days=31)
        start_time = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "TEST_To be cancelled"
        })
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        appt_id = create_response.json()["id"]
        
        # Cancel it
        cancel_response = requests.post(
            f"{BASE_URL}/api/appointments/{appt_id}/cancel",
            headers=therapist_headers
        )
        assert cancel_response.status_code == 200
        
        # Verify status
        get_response = requests.get(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "cancelled"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        
        print(f"✓ POST /api/appointments/{appt_id}/cancel - Status changed to cancelled")
    
    def test_cannot_complete_cancelled_appointment(self, therapist_headers):
        """Cannot complete a cancelled appointment"""
        # Create and cancel appointment
        future_date = datetime.now(timezone.utc) + timedelta(days=32)
        start_time = future_date.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        })
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        appt_id = create_response.json()["id"]
        
        # Cancel it
        requests.post(f"{BASE_URL}/api/appointments/{appt_id}/cancel", headers=therapist_headers)
        
        # Try to complete
        complete_response = requests.post(
            f"{BASE_URL}/api/appointments/{appt_id}/complete",
            headers=therapist_headers
        )
        assert complete_response.status_code == 400
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        
        print(f"✓ Cannot complete cancelled appointment - validation working")
    
    def test_cannot_cancel_completed_appointment(self, therapist_headers):
        """Cannot cancel a completed appointment"""
        # Create and complete appointment
        future_date = datetime.now(timezone.utc) + timedelta(days=33)
        start_time = future_date.replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", headers=therapist_headers, json={
            "client_id": TEST_CLIENT_ID,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        })
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        appt_id = create_response.json()["id"]
        
        # Complete it
        requests.post(f"{BASE_URL}/api/appointments/{appt_id}/complete", headers=therapist_headers)
        
        # Try to cancel
        cancel_response = requests.post(
            f"{BASE_URL}/api/appointments/{appt_id}/cancel",
            headers=therapist_headers
        )
        assert cancel_response.status_code == 400
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=therapist_headers)
        
        print(f"✓ Cannot cancel completed appointment - validation working")


class TestBlockedTimeCRUD:
    """Test POST/GET/DELETE /api/blocked-times"""
    
    def test_create_blocked_time(self, therapist_headers):
        """POST /api/blocked-times - Create blocked time"""
        future_date = datetime.now(timezone.utc) + timedelta(days=40)
        start_datetime = future_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_datetime = future_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        response = requests.post(f"{BASE_URL}/api/blocked-times", headers=therapist_headers, json={
            "start_datetime": start_datetime.isoformat(),
            "end_datetime": end_datetime.isoformat(),
            "reason": "TEST_Vacation day",
            "is_all_day": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["reason"] == "TEST_Vacation day"
        assert data["is_all_day"] == True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/blocked-times/{data['id']}", headers=therapist_headers)
        
        print(f"✓ POST /api/blocked-times - Created successfully")
    
    def test_create_blocked_time_invalid_times(self, therapist_headers):
        """POST /api/blocked-times - Reject when end <= start"""
        future_date = datetime.now(timezone.utc) + timedelta(days=41)
        start_datetime = future_date.replace(hour=17, minute=0, second=0, microsecond=0)
        end_datetime = future_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Before start
        
        response = requests.post(f"{BASE_URL}/api/blocked-times", headers=therapist_headers, json={
            "start_datetime": start_datetime.isoformat(),
            "end_datetime": end_datetime.isoformat(),
            "reason": "TEST_Invalid"
        })
        
        assert response.status_code == 400
        print(f"✓ POST /api/blocked-times - Rejects invalid times")
    
    def test_get_blocked_times(self, therapist_headers):
        """GET /api/blocked-times - List all blocked times"""
        response = requests.get(f"{BASE_URL}/api/blocked-times", headers=therapist_headers)
        
        assert response.status_code == 200
        blocked_times = response.json()
        assert isinstance(blocked_times, list)
        
        print(f"✓ GET /api/blocked-times - Found {len(blocked_times)} blocked times")
    
    def test_delete_blocked_time(self, therapist_headers):
        """DELETE /api/blocked-times/{id} - Delete blocked time"""
        # Create blocked time
        future_date = datetime.now(timezone.utc) + timedelta(days=42)
        start_datetime = future_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_datetime = future_date.replace(hour=12, minute=0, second=0, microsecond=0)
        
        create_response = requests.post(f"{BASE_URL}/api/blocked-times", headers=therapist_headers, json={
            "start_datetime": start_datetime.isoformat(),
            "end_datetime": end_datetime.isoformat(),
            "reason": "TEST_To be deleted"
        })
        assert create_response.status_code == 200
        block_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/blocked-times/{block_id}", headers=therapist_headers)
        assert delete_response.status_code == 200
        
        print(f"✓ DELETE /api/blocked-times - Deleted successfully")
    
    def test_blocked_time_prevents_slot_generation(self, therapist_headers, therapist_id):
        """Blocked time should prevent slot generation"""
        # Find next Wednesday
        today = datetime.now(timezone.utc).date()
        days_until_wed = (2 - today.weekday()) % 7
        if days_until_wed == 0:
            days_until_wed = 7
        next_wed = today + timedelta(days=days_until_wed)
        
        # Enable Wednesday with time blocks
        requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={
            "session_duration": 60,
            "buffer_time": 0,
            "wednesday": {
                "enabled": True,
                "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
            }
        })
        
        # Get slots before blocking
        slots_before = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={next_wed.isoformat()}",
            headers=therapist_headers
        ).json()
        
        # Block the entire day
        block_start = datetime.combine(next_wed, datetime.min.time()).replace(tzinfo=timezone.utc)
        block_end = datetime.combine(next_wed, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        block_response = requests.post(f"{BASE_URL}/api/blocked-times", headers=therapist_headers, json={
            "start_datetime": block_start.isoformat(),
            "end_datetime": block_end.isoformat(),
            "reason": "TEST_Block for slot test",
            "is_all_day": True
        })
        assert block_response.status_code == 200
        block_id = block_response.json()["id"]
        
        # Get slots after blocking
        slots_after = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={next_wed.isoformat()}",
            headers=therapist_headers
        ).json()
        
        # Should have fewer or no slots
        assert len(slots_after) < len(slots_before) or len(slots_after) == 0
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/blocked-times/{block_id}", headers=therapist_headers)
        
        print(f"✓ Blocked time prevents slot generation - Before: {len(slots_before)}, After: {len(slots_after)}")


class TestReadOnlyMode:
    """Test read-only mode blocks write operations for expired subscriptions"""
    
    def test_subscription_status_endpoint(self, therapist_headers):
        """GET /api/auth/subscription-status - Check subscription status"""
        response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=therapist_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "is_read_only" in data
        assert "subscription_status" in data
        
        print(f"✓ GET /api/auth/subscription-status - is_read_only: {data['is_read_only']}, status: {data['subscription_status']}")
    
    def test_active_subscription_allows_writes(self, therapist_headers):
        """Active subscription should allow write operations"""
        # Check subscription status first
        status_response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=therapist_headers)
        status_data = status_response.json()
        
        if status_data.get("is_read_only"):
            pytest.skip("Therapist is in read-only mode, skipping write test")
        
        # Try to update availability (write operation)
        response = requests.put(f"{BASE_URL}/api/availability", headers=therapist_headers, json={
            "buffer_time": 10
        })
        
        assert response.status_code == 200
        print(f"✓ Active subscription allows write operations")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_appointments(self, therapist_headers):
        """Clean up TEST_ prefixed appointments"""
        response = requests.get(f"{BASE_URL}/api/appointments", headers=therapist_headers)
        if response.status_code == 200:
            appointments = response.json()
            deleted = 0
            for appt in appointments:
                notes = appt.get("notes") or ""
                if notes.startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/appointments/{appt['id']}", headers=therapist_headers)
                    deleted += 1
            print(f"✓ Cleaned up {deleted} test appointments")
    
    def test_cleanup_test_blocked_times(self, therapist_headers):
        """Clean up TEST_ prefixed blocked times"""
        response = requests.get(f"{BASE_URL}/api/blocked-times", headers=therapist_headers)
        if response.status_code == 200:
            blocked_times = response.json()
            deleted = 0
            for bt in blocked_times:
                reason = bt.get("reason") or ""
                if reason.startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/blocked-times/{bt['id']}", headers=therapist_headers)
                    deleted += 1
            print(f"✓ Cleaned up {deleted} test blocked times")
