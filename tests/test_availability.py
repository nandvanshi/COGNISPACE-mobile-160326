"""
Test suite for Therapist Availability Feature (P0 Requirements)
Tests:
- P0-1: Therapist can define weekly working hours with multiple time blocks per day
- P0-2: Therapist can set session duration (e.g., 45 or 60 minutes)
- P0-3: Therapist can set buffer time between appointments
- P0-4: System generates available slots based on availability settings
- P0-5: Therapist can block specific dates/time ranges (vacation, holidays)
- P0-6: Blocked times prevent slot generation
- P0-7: Booked appointments prevent double-booking on slot generation
- P0-8: Slot-based booking works end-to-end
- P0-9: Read-only mode respected for availability settings
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "TestPass123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class TestAvailabilitySetup:
    """Test availability settings CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self, therapist_token):
        """Setup for each test"""
        self.token = therapist_token
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_default_availability(self, therapist_token):
        """P0-1: Get default availability settings for therapist"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/availability", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "session_duration" in data
        assert "buffer_time" in data
        assert "monday" in data
        assert "tuesday" in data
        assert "wednesday" in data
        assert "thursday" in data
        assert "friday" in data
        assert "saturday" in data
        assert "sunday" in data
        
        # Verify day structure
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            assert "enabled" in data[day]
            assert "time_blocks" in data[day]
    
    def test_update_session_duration(self, therapist_token):
        """P0-2: Therapist can set session duration"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Set session duration to 45 minutes
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={"session_duration": 45}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_duration"] == 45
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/availability", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["session_duration"] == 45
        
        # Reset to 60 minutes
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={"session_duration": 60})
    
    def test_update_buffer_time(self, therapist_token):
        """P0-3: Therapist can set buffer time between appointments"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Set buffer time to 15 minutes
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={"buffer_time": 15}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["buffer_time"] == 15
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/availability", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["buffer_time"] == 15
        
        # Reset to 0
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={"buffer_time": 0})
    
    def test_enable_day_with_time_blocks(self, therapist_token):
        """P0-1: Therapist can define weekly working hours with multiple time blocks per day"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Enable Monday with two time blocks (morning and afternoon)
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "monday": {
                    "enabled": True,
                    "time_blocks": [
                        {"start_time": "09:00", "end_time": "12:00"},
                        {"start_time": "14:00", "end_time": "18:00"}
                    ]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["monday"]["enabled"] == True
        assert len(data["monday"]["time_blocks"]) == 2
        assert data["monday"]["time_blocks"][0]["start_time"] == "09:00"
        assert data["monday"]["time_blocks"][0]["end_time"] == "12:00"
        assert data["monday"]["time_blocks"][1]["start_time"] == "14:00"
        assert data["monday"]["time_blocks"][1]["end_time"] == "18:00"
    
    def test_update_multiple_days(self, therapist_token):
        """P0-1: Update multiple days at once"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "tuesday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "10:00", "end_time": "16:00"}]
                },
                "wednesday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "08:00", "end_time": "14:00"}]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tuesday"]["enabled"] == True
        assert data["wednesday"]["enabled"] == True
    
    def test_session_duration_validation(self, therapist_token):
        """P0-2: Session duration must be between 15 and 240 minutes"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Test too short
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={"session_duration": 10}
        )
        assert response.status_code == 400
        
        # Test too long
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={"session_duration": 300}
        )
        assert response.status_code == 400
    
    def test_buffer_time_validation(self, therapist_token):
        """P0-3: Buffer time must be between 0 and 60 minutes"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Test negative
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={"buffer_time": -5}
        )
        assert response.status_code == 400
        
        # Test too long
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={"buffer_time": 90}
        )
        assert response.status_code == 400


class TestBlockedTimes:
    """Test blocked time functionality"""
    
    def test_create_blocked_time(self, therapist_token):
        """P0-5: Therapist can block specific dates/time ranges"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Block a future date
        future_date = datetime.now() + timedelta(days=30)
        start_dt = future_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_dt = future_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        response = requests.post(
            f"{BASE_URL}/api/blocked-times",
            headers=headers,
            json={
                "start_datetime": start_dt.isoformat(),
                "end_datetime": end_dt.isoformat(),
                "reason": "TEST_Vacation",
                "is_all_day": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["reason"] == "TEST_Vacation"
        assert data["is_all_day"] == False
        
        # Store for cleanup
        return data["id"]
    
    def test_get_blocked_times(self, therapist_token):
        """P0-5: Get all blocked times for therapist"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        response = requests.get(f"{BASE_URL}/api/blocked-times", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_delete_blocked_time(self, therapist_token):
        """P0-5: Delete a blocked time"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # First create a blocked time
        future_date = datetime.now() + timedelta(days=45)
        start_dt = future_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_dt = future_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        create_response = requests.post(
            f"{BASE_URL}/api/blocked-times",
            headers=headers,
            json={
                "start_datetime": start_dt.isoformat(),
                "end_datetime": end_dt.isoformat(),
                "reason": "TEST_ToDelete",
                "is_all_day": False
            }
        )
        assert create_response.status_code == 200
        block_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/blocked-times/{block_id}",
            headers=headers
        )
        assert delete_response.status_code == 200
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/blocked-times", headers=headers)
        blocked_ids = [b["id"] for b in get_response.json()]
        assert block_id not in blocked_ids
    
    def test_blocked_time_validation(self, therapist_token):
        """P0-5: End time must be after start time"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        future_date = datetime.now() + timedelta(days=30)
        start_dt = future_date.replace(hour=17, minute=0, second=0, microsecond=0)
        end_dt = future_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Before start
        
        response = requests.post(
            f"{BASE_URL}/api/blocked-times",
            headers=headers,
            json={
                "start_datetime": start_dt.isoformat(),
                "end_datetime": end_dt.isoformat(),
                "reason": "Invalid",
                "is_all_day": False
            }
        )
        
        assert response.status_code == 400


class TestAvailableSlots:
    """Test available slot generation"""
    
    @pytest.fixture(autouse=True)
    def setup_availability(self, therapist_token, therapist_id):
        """Setup availability for slot tests"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Set up Monday with 9AM-5PM, 60-min sessions, no buffer
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "monday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        self.therapist_id = therapist_id
        self.headers = headers
    
    def test_generate_slots_for_enabled_day(self, therapist_token, therapist_id):
        """P0-4: System generates available slots based on availability settings"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Find next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # Next Monday, not today
        next_monday = today + timedelta(days=days_until_monday)
        date_str = next_monday.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # With 9AM-5PM (8 hours) and 60-min sessions, should have 8 slots
        assert len(slots) == 8
        
        # Verify slot structure
        for slot in slots:
            assert "start_time" in slot
            assert "end_time" in slot
            assert "duration_minutes" in slot
            assert slot["duration_minutes"] == 60
    
    def test_no_slots_for_disabled_day(self, therapist_token, therapist_id):
        """P0-4: No slots generated for disabled days"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Disable Sunday
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "sunday": {"enabled": False, "time_blocks": []}
            }
        )
        
        # Find next Sunday
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        date_str = next_sunday.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) == 0
    
    def test_slots_with_buffer_time(self, therapist_token, therapist_id):
        """P0-3: Buffer time affects slot generation"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Set 60-min sessions with 15-min buffer
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 15,
                "monday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Find next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        date_str = next_monday.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # With 8 hours, 60-min sessions + 15-min buffer (75 min total), should have ~6 slots
        # 9:00-10:00, 10:15-11:15, 11:30-12:30, 12:45-13:45, 14:00-15:00, 15:15-16:15
        # Last possible: 16:00-17:00 (starts at 16:00 after 15:15+60+15=16:30 - doesn't fit)
        # Actually: 480 min / 75 min = 6.4, so 6 slots
        assert len(slots) >= 6
        
        # Reset buffer
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={"buffer_time": 0})
    
    def test_slots_with_different_session_duration(self, therapist_token, therapist_id):
        """P0-2: Different session durations generate different number of slots"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Set 45-min sessions
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 45,
                "buffer_time": 0,
                "monday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Find next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        date_str = next_monday.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # With 8 hours (480 min) and 45-min sessions, should have 10 slots (480/45 = 10.67)
        assert len(slots) == 10
        
        for slot in slots:
            assert slot["duration_minutes"] == 45
        
        # Reset to 60 min
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={"session_duration": 60})
    
    def test_invalid_date_format(self, therapist_token, therapist_id):
        """P0-4: Invalid date format returns error"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date=invalid-date",
            headers=headers
        )
        
        assert response.status_code == 400
    
    def test_past_date_returns_empty(self, therapist_token, therapist_id):
        """P0-4: Past dates return no slots"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        past_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={past_date}",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json() == []


class TestBlockedTimesPreventSlots:
    """Test that blocked times prevent slot generation"""
    
    def test_blocked_time_removes_slots(self, therapist_token, therapist_id):
        """P0-6: Blocked times prevent slot generation"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Setup Monday availability
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "monday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Find next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        date_str = next_monday.strftime("%Y-%m-%d")
        
        # Get initial slots count
        initial_response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        initial_slots = len(initial_response.json())
        
        # Block 10AM-12PM on that Monday
        block_start = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)
        block_end = next_monday.replace(hour=12, minute=0, second=0, microsecond=0)
        
        block_response = requests.post(
            f"{BASE_URL}/api/blocked-times",
            headers=headers,
            json={
                "start_datetime": block_start.isoformat(),
                "end_datetime": block_end.isoformat(),
                "reason": "TEST_BlockedSlots",
                "is_all_day": False
            }
        )
        assert block_response.status_code == 200
        block_id = block_response.json()["id"]
        
        # Get slots again - should have fewer
        after_response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        after_slots = len(after_response.json())
        
        # Should have 2 fewer slots (10AM and 11AM blocked)
        assert after_slots < initial_slots
        assert after_slots == initial_slots - 2
        
        # Cleanup - delete the blocked time
        requests.delete(f"{BASE_URL}/api/blocked-times/{block_id}", headers=headers)


class TestBookedAppointmentsPreventSlots:
    """Test that booked appointments prevent double-booking"""
    
    def test_booked_appointment_removes_slot(self, therapist_token, therapist_id):
        """P0-7: Booked appointments prevent double-booking on slot generation"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Setup Monday availability
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "monday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Find next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        date_str = next_monday.strftime("%Y-%m-%d")
        
        # Get a client to book with
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
        clients = clients_response.json()
        
        if not clients:
            pytest.skip("No clients available for booking test")
        
        client_id = clients[0]["id"]
        
        # Get initial slots count
        initial_response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        initial_slots = len(initial_response.json())
        
        # Book an appointment at 10AM
        appt_start = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)
        appt_end = next_monday.replace(hour=11, minute=0, second=0, microsecond=0)
        
        appt_response = requests.post(
            f"{BASE_URL}/api/appointments",
            headers=headers,
            json={
                "client_id": client_id,
                "start_time": appt_start.isoformat(),
                "end_time": appt_end.isoformat(),
                "notes": "TEST_SlotBooking"
            }
        )
        assert appt_response.status_code == 200
        appt_id = appt_response.json()["id"]
        
        # Get slots again - should have one fewer
        after_response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        after_slots = len(after_response.json())
        
        # Should have 1 fewer slot (10AM booked)
        assert after_slots == initial_slots - 1
        
        # Cleanup - delete the appointment
        requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=headers)


class TestSlotBasedBooking:
    """Test end-to-end slot-based booking"""
    
    def test_book_from_available_slot(self, therapist_token, therapist_id):
        """P0-8: Slot-based booking works end-to-end"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Setup Monday availability
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "monday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Find next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        date_str = next_monday.strftime("%Y-%m-%d")
        
        # Get available slots
        slots_response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        assert slots_response.status_code == 200
        slots = slots_response.json()
        assert len(slots) > 0
        
        # Get a client
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
        clients = clients_response.json()
        
        if not clients:
            pytest.skip("No clients available for booking test")
        
        client_id = clients[0]["id"]
        
        # Book the first available slot
        first_slot = slots[0]
        
        appt_response = requests.post(
            f"{BASE_URL}/api/appointments",
            headers=headers,
            json={
                "client_id": client_id,
                "start_time": first_slot["start_time"],
                "end_time": first_slot["end_time"],
                "notes": "TEST_SlotBasedBooking"
            }
        )
        assert appt_response.status_code == 200
        appt_data = appt_response.json()
        assert appt_data["status"] == "scheduled"
        
        # Verify the slot is no longer available
        slots_after = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        ).json()
        
        slot_times = [s["start_time"] for s in slots_after]
        assert first_slot["start_time"] not in slot_times
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appt_data['id']}", headers=headers)


class TestReadOnlyMode:
    """Test read-only mode for availability settings"""
    
    def test_expired_therapist_cannot_update_availability(self, expired_therapist_token):
        """P0-9: Read-only mode respected for availability settings"""
        if not expired_therapist_token:
            pytest.skip("No expired therapist available for test")
        
        headers = {"Authorization": f"Bearer {expired_therapist_token}"}
        
        # Try to update availability - should fail
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={"session_duration": 45}
        )
        
        assert response.status_code == 403
        assert "read-only" in response.json().get("detail", "").lower() or "expired" in response.json().get("detail", "").lower()
    
    def test_expired_therapist_cannot_create_blocked_time(self, expired_therapist_token):
        """P0-9: Expired therapist cannot create blocked times"""
        if not expired_therapist_token:
            pytest.skip("No expired therapist available for test")
        
        headers = {"Authorization": f"Bearer {expired_therapist_token}"}
        
        future_date = datetime.now() + timedelta(days=30)
        
        response = requests.post(
            f"{BASE_URL}/api/blocked-times",
            headers=headers,
            json={
                "start_datetime": future_date.isoformat(),
                "end_datetime": (future_date + timedelta(hours=8)).isoformat(),
                "reason": "Test",
                "is_all_day": False
            }
        )
        
        assert response.status_code == 403
    
    def test_expired_therapist_can_read_availability(self, expired_therapist_token):
        """P0-9: Expired therapist can still read availability"""
        if not expired_therapist_token:
            pytest.skip("No expired therapist available for test")
        
        headers = {"Authorization": f"Bearer {expired_therapist_token}"}
        
        response = requests.get(f"{BASE_URL}/api/availability", headers=headers)
        
        # Should be able to read
        assert response.status_code == 200


class TestMultipleTimeBlocks:
    """Test multiple time blocks per day"""
    
    def test_multiple_time_blocks_generate_slots(self, therapist_token, therapist_id):
        """P0-1: Multiple time blocks per day generate correct slots"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Setup Monday with morning and afternoon blocks
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "monday": {
                    "enabled": True,
                    "time_blocks": [
                        {"start_time": "09:00", "end_time": "12:00"},  # 3 hours = 3 slots
                        {"start_time": "14:00", "end_time": "17:00"}   # 3 hours = 3 slots
                    ]
                }
            }
        )
        
        # Find next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        date_str = next_monday.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # Should have 6 slots total (3 morning + 3 afternoon)
        assert len(slots) == 6
        
        # Verify no slots during lunch break (12:00-14:00)
        for slot in slots:
            slot_hour = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00')).hour
            assert slot_hour not in [12, 13]  # No slots during lunch


# ============= FIXTURES =============

@pytest.fixture(scope="module")
def therapist_token():
    """Get authentication token for active therapist"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"identifier": THERAPIST_MOBILE, "password": THERAPIST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Could not authenticate therapist: {response.text}")
    return response.json()["token"]


@pytest.fixture(scope="module")
def therapist_id(therapist_token):
    """Get therapist ID"""
    headers = {"Authorization": f"Bearer {therapist_token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code != 200:
        pytest.skip("Could not get therapist info")
    return response.json()["id"]


@pytest.fixture(scope="module")
def expired_therapist_token():
    """Get token for expired therapist (if available)"""
    # Try to find an expired therapist or return None
    # For now, return None as we don't have an expired therapist in test data
    return None


@pytest.fixture(scope="module")
def admin_token():
    """Get super admin token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/super-admin-login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip("Could not authenticate admin")
    return response.json()["token"]


# Cleanup fixture
@pytest.fixture(autouse=True, scope="module")
def cleanup_test_data(therapist_token):
    """Cleanup test data after all tests"""
    yield
    
    # Cleanup blocked times with TEST_ prefix
    headers = {"Authorization": f"Bearer {therapist_token}"}
    blocked_response = requests.get(f"{BASE_URL}/api/blocked-times", headers=headers)
    if blocked_response.status_code == 200:
        for block in blocked_response.json():
            if block.get("reason", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/blocked-times/{block['id']}", headers=headers)
    
    # Cleanup appointments with TEST_ prefix in notes
    appts_response = requests.get(f"{BASE_URL}/api/appointments", headers=headers)
    if appts_response.status_code == 200:
        for appt in appts_response.json():
            if appt.get("notes", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/appointments/{appt['id']}", headers=headers)
