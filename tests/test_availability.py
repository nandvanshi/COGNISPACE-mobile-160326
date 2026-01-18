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
        
        # Get current value
        current = requests.get(f"{BASE_URL}/api/availability", headers=headers).json()
        original_duration = current["session_duration"]
        
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
        
        # Reset to original
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={"session_duration": original_duration})
    
    def test_update_buffer_time(self, therapist_token):
        """P0-3: Therapist can set buffer time between appointments"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Get current value
        current = requests.get(f"{BASE_URL}/api/availability", headers=headers).json()
        original_buffer = current["buffer_time"]
        
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
        
        # Reset to original
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={"buffer_time": original_buffer})
    
    def test_enable_day_with_time_blocks(self, therapist_token):
        """P0-1: Therapist can define weekly working hours with multiple time blocks per day"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Enable Thursday with two time blocks (morning and afternoon)
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "thursday": {
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
        assert data["thursday"]["enabled"] == True
        assert len(data["thursday"]["time_blocks"]) == 2
        assert data["thursday"]["time_blocks"][0]["start_time"] == "09:00"
        assert data["thursday"]["time_blocks"][0]["end_time"] == "12:00"
        assert data["thursday"]["time_blocks"][1]["start_time"] == "14:00"
        assert data["thursday"]["time_blocks"][1]["end_time"] == "18:00"
        
        # Cleanup - disable Thursday
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={
            "thursday": {"enabled": False, "time_blocks": []}
        })
    
    def test_update_multiple_days(self, therapist_token):
        """P0-1: Update multiple days at once"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Save original state
        original = requests.get(f"{BASE_URL}/api/availability", headers=headers).json()
        
        response = requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "friday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "10:00", "end_time": "16:00"}]
                },
                "saturday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "08:00", "end_time": "14:00"}]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["friday"]["enabled"] == True
        assert data["saturday"]["enabled"] == True
        
        # Cleanup - restore original
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={
            "friday": original["friday"],
            "saturday": original["saturday"]
        })
    
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
        future_date = datetime.now() + timedelta(days=60)
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
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/blocked-times/{data['id']}", headers=headers)
    
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
        future_date = datetime.now() + timedelta(days=65)
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
    
    def test_generate_slots_for_enabled_day(self, therapist_token, therapist_id):
        """P0-4: System generates available slots based on availability settings"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Use a far future date to avoid conflicts with existing appointments
        # Find a Monday 8 weeks from now
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        future_monday = today + timedelta(days=days_until_monday + 56)  # 8 weeks out
        date_str = future_monday.strftime("%Y-%m-%d")
        
        # First set up clean availability for Monday
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
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # With 9AM-5PM (8 hours) and 60-min sessions, should have 8 slots
        assert len(slots) == 8, f"Expected 8 slots, got {len(slots)} for date {date_str}"
        
        # Verify slot structure
        for slot in slots:
            assert "start_time" in slot
            assert "end_time" in slot
            assert "duration_minutes" in slot
            assert slot["duration_minutes"] == 60
    
    def test_no_slots_for_disabled_day(self, therapist_token, therapist_id):
        """P0-4: No slots generated for disabled days"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Ensure Sunday is disabled
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "sunday": {"enabled": False, "time_blocks": []}
            }
        )
        
        # Find a Sunday 8 weeks from now
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        future_sunday = today + timedelta(days=days_until_sunday + 56)
        date_str = future_sunday.strftime("%Y-%m-%d")
        
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
        
        # Find a Tuesday 8 weeks from now
        today = datetime.now()
        days_until_tuesday = (1 - today.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        future_tuesday = today + timedelta(days=days_until_tuesday + 56)
        date_str = future_tuesday.strftime("%Y-%m-%d")
        
        # Set 60-min sessions with 15-min buffer on Tuesday
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 15,
                "tuesday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # With 8 hours, 60-min sessions + 15-min buffer (75 min total), should have 6 slots
        # 9:00-10:00, 10:15-11:15, 11:30-12:30, 12:45-13:45, 14:00-15:00, 15:15-16:15
        assert len(slots) == 6, f"Expected 6 slots with buffer, got {len(slots)}"
        
        # Reset buffer
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={"buffer_time": 0})
    
    def test_slots_with_different_session_duration(self, therapist_token, therapist_id):
        """P0-2: Different session durations generate different number of slots"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Find a Wednesday 8 weeks from now
        today = datetime.now()
        days_until_wednesday = (2 - today.weekday()) % 7
        if days_until_wednesday == 0:
            days_until_wednesday = 7
        future_wednesday = today + timedelta(days=days_until_wednesday + 56)
        date_str = future_wednesday.strftime("%Y-%m-%d")
        
        # Set 45-min sessions on Wednesday
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 45,
                "buffer_time": 0,
                "wednesday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # With 8 hours (480 min) and 45-min sessions, should have 10 slots (480/45 = 10.67)
        assert len(slots) == 10, f"Expected 10 slots with 45-min duration, got {len(slots)}"
        
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
        
        # Find a Thursday 8 weeks from now
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        future_thursday = today + timedelta(days=days_until_thursday + 56)
        date_str = future_thursday.strftime("%Y-%m-%d")
        
        # Setup Thursday availability
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "thursday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Get initial slots count
        initial_response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        assert initial_response.status_code == 200
        initial_slots = len(initial_response.json())
        assert initial_slots == 8, f"Expected 8 initial slots, got {initial_slots}"
        
        # Block 10AM-12PM on that Thursday
        block_start = future_thursday.replace(hour=10, minute=0, second=0, microsecond=0)
        block_end = future_thursday.replace(hour=12, minute=0, second=0, microsecond=0)
        
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
        assert after_response.status_code == 200
        after_slots = len(after_response.json())
        
        # Should have 2 fewer slots (10AM and 11AM blocked)
        assert after_slots < initial_slots, f"Expected fewer slots after blocking, got {after_slots} vs {initial_slots}"
        assert after_slots == initial_slots - 2, f"Expected {initial_slots - 2} slots, got {after_slots}"
        
        # Cleanup - delete the blocked time and disable Thursday
        requests.delete(f"{BASE_URL}/api/blocked-times/{block_id}", headers=headers)
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={
            "thursday": {"enabled": False, "time_blocks": []}
        })


class TestBookedAppointmentsPreventSlots:
    """Test that booked appointments prevent double-booking"""
    
    def test_booked_appointment_removes_slot(self, therapist_token, therapist_id):
        """P0-7: Booked appointments prevent double-booking on slot generation"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Find a Friday 8 weeks from now
        today = datetime.now()
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        future_friday = today + timedelta(days=days_until_friday + 56)
        date_str = future_friday.strftime("%Y-%m-%d")
        
        # Setup Friday availability
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "friday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
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
        assert initial_response.status_code == 200
        initial_slots = len(initial_response.json())
        assert initial_slots == 8, f"Expected 8 initial slots, got {initial_slots}"
        
        # Book an appointment at 10AM
        appt_start = future_friday.replace(hour=10, minute=0, second=0, microsecond=0)
        appt_end = future_friday.replace(hour=11, minute=0, second=0, microsecond=0)
        
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
        assert after_response.status_code == 200
        after_slots = len(after_response.json())
        
        # Should have 1 fewer slot (10AM booked)
        assert after_slots == initial_slots - 1, f"Expected {initial_slots - 1} slots, got {after_slots}"
        
        # Cleanup - delete the appointment and disable Friday
        requests.delete(f"{BASE_URL}/api/appointments/{appt_id}", headers=headers)
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={
            "friday": {"enabled": False, "time_blocks": []}
        })


class TestSlotBasedBooking:
    """Test end-to-end slot-based booking"""
    
    def test_book_from_available_slot(self, therapist_token, therapist_id):
        """P0-8: Slot-based booking works end-to-end"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Find a Saturday 8 weeks from now
        today = datetime.now()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        future_saturday = today + timedelta(days=days_until_saturday + 56)
        date_str = future_saturday.strftime("%Y-%m-%d")
        
        # Setup Saturday availability
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "saturday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Get available slots
        slots_response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        assert slots_response.status_code == 200
        slots = slots_response.json()
        assert len(slots) > 0, "No slots available for booking test"
        
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
        assert first_slot["start_time"] not in slot_times, "Booked slot should not be available"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appt_data['id']}", headers=headers)
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={
            "saturday": {"enabled": False, "time_blocks": []}
        })


class TestMultipleTimeBlocks:
    """Test multiple time blocks per day"""
    
    def test_multiple_time_blocks_generate_slots(self, therapist_token, therapist_id):
        """P0-1: Multiple time blocks per day generate correct slots"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Find a Sunday 8 weeks from now
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        future_sunday = today + timedelta(days=days_until_sunday + 56)
        date_str = future_sunday.strftime("%Y-%m-%d")
        
        # Setup Sunday with morning and afternoon blocks
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "buffer_time": 0,
                "sunday": {
                    "enabled": True,
                    "time_blocks": [
                        {"start_time": "09:00", "end_time": "12:00"},  # 3 hours = 3 slots
                        {"start_time": "14:00", "end_time": "17:00"}   # 3 hours = 3 slots
                    ]
                }
            }
        )
        
        response = requests.get(
            f"{BASE_URL}/api/available-slots/{therapist_id}?date={date_str}",
            headers=headers
        )
        
        assert response.status_code == 200
        slots = response.json()
        
        # Should have 6 slots total (3 morning + 3 afternoon)
        assert len(slots) == 6, f"Expected 6 slots for multiple time blocks, got {len(slots)}"
        
        # Verify no slots during lunch break (12:00-14:00)
        for slot in slots:
            slot_hour = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00')).hour
            assert slot_hour not in [12, 13], f"Found slot during lunch break at hour {slot_hour}"
        
        # Cleanup - disable Sunday
        requests.put(f"{BASE_URL}/api/availability", headers=headers, json={
            "sunday": {"enabled": False, "time_blocks": []}
        })


class TestPublicAvailability:
    """Test public availability endpoint"""
    
    def test_get_therapist_public_availability(self, therapist_token, therapist_id):
        """Test public availability endpoint returns correct data"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # First set up some availability
        requests.put(
            f"{BASE_URL}/api/availability",
            headers=headers,
            json={
                "session_duration": 60,
                "monday": {
                    "enabled": True,
                    "time_blocks": [{"start_time": "09:00", "end_time": "17:00"}]
                }
            }
        )
        
        # Get public availability
        response = requests.get(
            f"{BASE_URL}/api/therapist/{therapist_id}/availability",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_duration" in data
        assert "available_days" in data
        assert "monday" in data["available_days"]


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
    
    headers = {"Authorization": f"Bearer {therapist_token}"}
    
    # Cleanup blocked times with TEST_ prefix
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
    
    # Reset availability to original state (Monday enabled with 9-12, 14-17)
    requests.put(
        f"{BASE_URL}/api/availability",
        headers=headers,
        json={
            "session_duration": 60,
            "buffer_time": 0,
            "monday": {
                "enabled": True,
                "time_blocks": [
                    {"start_time": "09:00", "end_time": "12:00"},
                    {"start_time": "14:00", "end_time": "17:00"}
                ]
            },
            "tuesday": {
                "enabled": True,
                "time_blocks": [{"start_time": "10:00", "end_time": "16:00"}]
            },
            "wednesday": {
                "enabled": True,
                "time_blocks": [{"start_time": "08:00", "end_time": "14:00"}]
            },
            "thursday": {"enabled": False, "time_blocks": []},
            "friday": {"enabled": False, "time_blocks": []},
            "saturday": {"enabled": False, "time_blocks": []},
            "sunday": {"enabled": False, "time_blocks": []}
        }
    )
