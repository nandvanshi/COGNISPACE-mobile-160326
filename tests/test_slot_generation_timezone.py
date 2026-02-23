"""
Test Suite: Slot Generation Timezone Bug Fix Verification
Bug: Timing mismatch between Weekly Availability settings and available appointment slots

This test verifies that:
1. Slot generation matches availability times in IST
2. Multiple time blocks generate correct slots
3. Slot times are displayed in 24-hour format (HH:mm)
4. Booking an appointment uses correct times
5. Blocked times correctly remove slots from available slots
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://theragenie-staging.preview.emergentagent.com').rstrip('/')

# IST offset for verification
IST_OFFSET = timedelta(hours=5, minutes=30)


class TestSlotGenerationTimezone:
    """Test slot generation matches availability settings in IST timezone"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Therapist 1 credentials
        self.therapist1_mobile = "9999999999"
        self.therapist1_password = "password"
        self.therapist1_id = "74f28b81-c293-40bf-9226-28626af1ae27"
        
        # Therapist 2 credentials
        self.therapist2_mobile = "7275005007"
        self.therapist2_password = "password"
        self.therapist2_id = "95ca48f3-6715-4b72-af4d-7f0ef7d2a34d"
        
        # Test date - 2026-01-21 is a Wednesday
        self.test_date = "2026-01-21"
    
    def login(self, mobile, password):
        """Login and return token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": mobile,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def utc_to_ist(self, utc_time_str):
        """Convert UTC time string to IST datetime"""
        if utc_time_str.endswith('Z'):
            utc_time_str = utc_time_str.replace('Z', '+00:00')
        utc_dt = datetime.fromisoformat(utc_time_str)
        ist_dt = utc_dt + IST_OFFSET
        return ist_dt
    
    def get_ist_time_str(self, utc_time_str):
        """Get HH:MM format IST time from UTC string"""
        ist_dt = self.utc_to_ist(utc_time_str)
        return ist_dt.strftime("%H:%M")
    
    # ============= THERAPIST 1 TESTS =============
    
    def test_therapist1_availability_settings(self):
        """Verify Therapist 1 has Wednesday 09:00-17:00 IST with 60min sessions and 10min buffer"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login as Therapist 1"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/availability")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify session settings
        assert data["session_duration"] == 60, f"Expected 60min sessions, got {data['session_duration']}"
        assert data["buffer_time"] == 10, f"Expected 10min buffer, got {data['buffer_time']}"
        
        # Verify Wednesday availability
        wednesday = data.get("wednesday", {})
        assert wednesday.get("enabled") == True, "Wednesday should be enabled"
        
        time_blocks = wednesday.get("time_blocks", [])
        assert len(time_blocks) >= 1, "Wednesday should have at least 1 time block"
        
        # Check first block starts at 09:00
        first_block = time_blocks[0]
        assert first_block["start_time"] == "09:00", f"Expected start_time 09:00, got {first_block['start_time']}"
        
        print(f"✓ Therapist 1 availability verified: Wednesday {first_block['start_time']}-{first_block['end_time']} IST")
    
    def test_therapist1_slot_generation_starts_at_0900_ist(self):
        """Verify Therapist 1 slots for 2026-01-21 start at 09:00 IST"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login as Therapist 1"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date={self.test_date}")
        
        assert response.status_code == 200
        slots = response.json()
        
        assert len(slots) > 0, "Should have available slots for Wednesday"
        
        # First slot should start at 09:00 IST
        first_slot = slots[0]
        first_slot_ist = self.get_ist_time_str(first_slot["start_time"])
        
        assert first_slot_ist == "09:00", f"First slot should start at 09:00 IST, got {first_slot_ist}"
        
        # Verify slot duration is 60 minutes
        assert first_slot["duration_minutes"] == 60, f"Expected 60min duration, got {first_slot['duration_minutes']}"
        
        print(f"✓ Therapist 1 first slot starts at {first_slot_ist} IST (correct)")
        print(f"✓ Total slots generated: {len(slots)}")
    
    def test_therapist1_slot_times_in_24hour_format(self):
        """Verify slot times are in 24-hour format (HH:mm)"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login as Therapist 1"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date={self.test_date}")
        
        assert response.status_code == 200
        slots = response.json()
        
        for i, slot in enumerate(slots):
            start_ist = self.get_ist_time_str(slot["start_time"])
            end_ist = self.get_ist_time_str(slot["end_time"])
            
            # Verify 24-hour format (HH:MM)
            assert len(start_ist) == 5, f"Start time should be HH:MM format, got {start_ist}"
            assert len(end_ist) == 5, f"End time should be HH:MM format, got {end_ist}"
            assert ":" in start_ist, f"Start time should contain colon, got {start_ist}"
            assert ":" in end_ist, f"End time should contain colon, got {end_ist}"
            
            # Verify hours are 0-23 (24-hour format)
            start_hour = int(start_ist.split(":")[0])
            end_hour = int(end_ist.split(":")[0])
            assert 0 <= start_hour <= 23, f"Start hour should be 0-23, got {start_hour}"
            assert 0 <= end_hour <= 23, f"End hour should be 0-23, got {end_hour}"
        
        print(f"✓ All {len(slots)} slots are in 24-hour format (HH:MM)")
    
    def test_therapist1_slot_buffer_time_applied(self):
        """Verify 10-minute buffer is applied between slots"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login as Therapist 1"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date={self.test_date}")
        
        assert response.status_code == 200
        slots = response.json()
        
        # Check buffer between consecutive slots
        for i in range(len(slots) - 1):
            current_end = self.utc_to_ist(slots[i]["end_time"])
            next_start = self.utc_to_ist(slots[i + 1]["start_time"])
            
            buffer = (next_start - current_end).total_seconds() / 60
            assert buffer == 10, f"Buffer between slot {i+1} and {i+2} should be 10 min, got {buffer} min"
        
        print(f"✓ 10-minute buffer correctly applied between all {len(slots)} slots")
    
    # ============= THERAPIST 2 TESTS =============
    
    def test_therapist2_availability_settings(self):
        """Verify Therapist 2 has Wednesday blocks: 10:20-17:00, 17:30-18:10, 18:30-20:45 with 40min sessions and 5min buffer"""
        token = self.login(self.therapist2_mobile, self.therapist2_password)
        assert token, "Failed to login as Therapist 2"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/availability")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify session settings
        assert data["session_duration"] == 40, f"Expected 40min sessions, got {data['session_duration']}"
        assert data["buffer_time"] == 5, f"Expected 5min buffer, got {data['buffer_time']}"
        
        # Verify Wednesday availability
        wednesday = data.get("wednesday", {})
        assert wednesday.get("enabled") == True, "Wednesday should be enabled"
        
        time_blocks = wednesday.get("time_blocks", [])
        assert len(time_blocks) == 3, f"Wednesday should have 3 time blocks, got {len(time_blocks)}"
        
        # Verify time blocks
        expected_blocks = [
            ("10:20", "17:00"),
            ("17:30", "18:10"),
            ("18:30", "20:45")
        ]
        
        for i, (expected_start, expected_end) in enumerate(expected_blocks):
            assert time_blocks[i]["start_time"] == expected_start, f"Block {i+1} start should be {expected_start}, got {time_blocks[i]['start_time']}"
            assert time_blocks[i]["end_time"] == expected_end, f"Block {i+1} end should be {expected_end}, got {time_blocks[i]['end_time']}"
        
        print(f"✓ Therapist 2 availability verified: 3 time blocks on Wednesday")
    
    def test_therapist2_multiple_time_blocks_slot_generation(self):
        """Verify Therapist 2 generates correct slots for all 3 time blocks"""
        token = self.login(self.therapist2_mobile, self.therapist2_password)
        assert token, "Failed to login as Therapist 2"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist2_id}?date={self.test_date}")
        
        assert response.status_code == 200
        slots = response.json()
        
        # Group slots by time block
        block1_slots = []  # 10:20-17:00
        block2_slots = []  # 17:30-18:10
        block3_slots = []  # 18:30-20:45
        
        for slot in slots:
            start_ist = self.utc_to_ist(slot["start_time"])
            start_hour = start_ist.hour + start_ist.minute / 60
            
            if start_hour < 17:
                block1_slots.append(slot)
            elif start_hour < 18.5:
                block2_slots.append(slot)
            else:
                block3_slots.append(slot)
        
        # Block 1: 10:20-17:00 with 40min sessions + 5min buffer = 45min per slot
        # Duration: 6h40m = 400min, slots = 400/45 = 8.88 -> 9 slots (last one ends at 17:00)
        assert len(block1_slots) >= 8, f"Block 1 should have at least 8 slots, got {len(block1_slots)}"
        
        # Block 2: 17:30-18:10 = 40min, exactly 1 slot
        assert len(block2_slots) == 1, f"Block 2 should have exactly 1 slot, got {len(block2_slots)}"
        
        # Block 3: 18:30-20:45 = 135min, slots = 135/45 = 3 slots
        assert len(block3_slots) >= 2, f"Block 3 should have at least 2 slots, got {len(block3_slots)}"
        
        # Verify first slot of each block starts at correct time
        if block1_slots:
            first_block1 = self.get_ist_time_str(block1_slots[0]["start_time"])
            assert first_block1 == "10:20", f"Block 1 first slot should start at 10:20 IST, got {first_block1}"
        
        if block2_slots:
            first_block2 = self.get_ist_time_str(block2_slots[0]["start_time"])
            assert first_block2 == "17:30", f"Block 2 first slot should start at 17:30 IST, got {first_block2}"
        
        if block3_slots:
            first_block3 = self.get_ist_time_str(block3_slots[0]["start_time"])
            assert first_block3 == "18:30", f"Block 3 first slot should start at 18:30 IST, got {first_block3}"
        
        print(f"✓ Therapist 2 slot generation verified:")
        print(f"  Block 1 (10:20-17:00): {len(block1_slots)} slots")
        print(f"  Block 2 (17:30-18:10): {len(block2_slots)} slots")
        print(f"  Block 3 (18:30-20:45): {len(block3_slots)} slots")
        print(f"  Total: {len(slots)} slots")
    
    def test_therapist2_slot_buffer_time_applied(self):
        """Verify 5-minute buffer is applied between slots within same block"""
        token = self.login(self.therapist2_mobile, self.therapist2_password)
        assert token, "Failed to login as Therapist 2"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist2_id}?date={self.test_date}")
        
        assert response.status_code == 200
        slots = response.json()
        
        # Check buffer between consecutive slots in block 1 (10:20-17:00)
        block1_slots = [s for s in slots if self.utc_to_ist(s["start_time"]).hour < 17]
        
        for i in range(len(block1_slots) - 1):
            current_end = self.utc_to_ist(block1_slots[i]["end_time"])
            next_start = self.utc_to_ist(block1_slots[i + 1]["start_time"])
            
            buffer = (next_start - current_end).total_seconds() / 60
            assert buffer == 5, f"Buffer between slot {i+1} and {i+2} should be 5 min, got {buffer} min"
        
        print(f"✓ 5-minute buffer correctly applied between slots in block 1")
    
    # ============= BOOKING VERIFICATION TESTS =============
    
    def test_booking_appointment_uses_correct_times(self):
        """Verify booking an appointment uses correct IST times"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login as Therapist 1"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get available slots
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date={self.test_date}")
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) > 0, "Should have available slots"
        
        # Get first slot
        first_slot = slots[0]
        slot_start_ist = self.get_ist_time_str(first_slot["start_time"])
        slot_end_ist = self.get_ist_time_str(first_slot["end_time"])
        
        # Get a client to book with
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        if clients_response.status_code != 200 or not clients_response.json():
            pytest.skip("No clients available for booking test")
        
        client = clients_response.json()[0]
        
        # Book the appointment
        booking_response = self.session.post(f"{BASE_URL}/api/appointments", json={
            "client_id": client["id"],
            "start_time": first_slot["start_time"],
            "end_time": first_slot["end_time"],
            "notes": "TEST_TIMEZONE_VERIFICATION"
        })
        
        assert booking_response.status_code in [200, 201], f"Failed to book appointment: {booking_response.text}"
        
        appointment = booking_response.json()
        
        # Verify appointment times match slot times
        appt_start_ist = self.get_ist_time_str(appointment["start_time"])
        appt_end_ist = self.get_ist_time_str(appointment["end_time"])
        
        assert appt_start_ist == slot_start_ist, f"Appointment start {appt_start_ist} should match slot start {slot_start_ist}"
        assert appt_end_ist == slot_end_ist, f"Appointment end {appt_end_ist} should match slot end {slot_end_ist}"
        
        print(f"✓ Appointment booked with correct times: {appt_start_ist} - {appt_end_ist} IST")
        
        # Cleanup - delete the test appointment
        delete_response = self.session.delete(f"{BASE_URL}/api/appointments/{appointment['id']}")
        assert delete_response.status_code == 200, "Failed to cleanup test appointment"
        print(f"✓ Test appointment cleaned up")
    
    # ============= BLOCKED TIME TESTS =============
    
    def test_blocked_time_removes_slot(self):
        """Verify blocked time correctly removes slot from available slots"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login as Therapist 1"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get initial slots
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date={self.test_date}")
        assert response.status_code == 200
        initial_slots = response.json()
        initial_count = len(initial_slots)
        
        if initial_count == 0:
            pytest.skip("No slots available to test blocking")
        
        # Get first slot time
        first_slot = initial_slots[0]
        
        # Create a blocked time for the first slot
        block_response = self.session.post(f"{BASE_URL}/api/blocked-times", json={
            "start_datetime": first_slot["start_time"],
            "end_datetime": first_slot["end_time"],
            "reason": "TEST_BLOCKED_TIME",
            "is_all_day": False
        })
        
        assert block_response.status_code in [200, 201], f"Failed to create blocked time: {block_response.text}"
        blocked_time = block_response.json()
        
        # Get slots again - should have one less
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date={self.test_date}")
        assert response.status_code == 200
        new_slots = response.json()
        
        assert len(new_slots) == initial_count - 1, f"Should have {initial_count - 1} slots after blocking, got {len(new_slots)}"
        
        # Verify the blocked slot is not in the list
        blocked_start = first_slot["start_time"]
        for slot in new_slots:
            assert slot["start_time"] != blocked_start, "Blocked slot should not appear in available slots"
        
        print(f"✓ Blocked time correctly removed slot from available slots")
        print(f"  Initial slots: {initial_count}, After blocking: {len(new_slots)}")
        
        # Cleanup - delete the blocked time
        delete_response = self.session.delete(f"{BASE_URL}/api/blocked-times/{blocked_time['id']}")
        assert delete_response.status_code == 200, "Failed to cleanup blocked time"
        print(f"✓ Test blocked time cleaned up")
    
    # ============= AVAILABILITY SETTINGS UPDATE TESTS =============
    
    def test_availability_settings_page_displays_correctly(self):
        """Verify availability settings can be retrieved and updated"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login as Therapist 1"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get current availability
        response = self.session.get(f"{BASE_URL}/api/availability")
        assert response.status_code == 200
        current = response.json()
        
        # Verify all required fields are present
        required_fields = ["session_duration", "buffer_time", "monday", "tuesday", "wednesday", 
                          "thursday", "friday", "saturday", "sunday"]
        for field in required_fields:
            assert field in current, f"Missing required field: {field}"
        
        # Verify day structure
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            day_data = current.get(day, {})
            assert "enabled" in day_data, f"Missing 'enabled' in {day}"
            assert "time_blocks" in day_data, f"Missing 'time_blocks' in {day}"
        
        print(f"✓ Availability settings structure verified")
        print(f"  Session duration: {current['session_duration']} min")
        print(f"  Buffer time: {current['buffer_time']} min")
        
        # Count enabled days
        enabled_days = [d for d in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] 
                       if current.get(d, {}).get("enabled")]
        print(f"  Enabled days: {', '.join(enabled_days)}")


class TestSlotGenerationEdgeCases:
    """Test edge cases for slot generation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        self.therapist1_mobile = "9999999999"
        self.therapist1_password = "password"
        self.therapist1_id = "74f28b81-c293-40bf-9226-28626af1ae27"
    
    def login(self, mobile, password):
        """Login and return token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": mobile,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_disabled_day_returns_no_slots(self):
        """Verify disabled day returns empty slots"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # 2026-01-22 is Thursday - disabled for Therapist 1
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date=2026-01-22")
        assert response.status_code == 200
        slots = response.json()
        
        assert len(slots) == 0, f"Disabled day should return 0 slots, got {len(slots)}"
        print(f"✓ Disabled day (Thursday) correctly returns 0 slots")
    
    def test_past_date_returns_no_slots(self):
        """Verify past date returns empty slots"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Use a past date
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date=2025-01-01")
        assert response.status_code == 200
        slots = response.json()
        
        assert len(slots) == 0, f"Past date should return 0 slots, got {len(slots)}"
        print(f"✓ Past date correctly returns 0 slots")
    
    def test_invalid_date_format_returns_error(self):
        """Verify invalid date format returns error"""
        token = self.login(self.therapist1_mobile, self.therapist1_password)
        assert token, "Failed to login"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = self.session.get(f"{BASE_URL}/api/available-slots/{self.therapist1_id}?date=invalid-date")
        assert response.status_code == 400, f"Invalid date should return 400, got {response.status_code}"
        print(f"✓ Invalid date format correctly returns 400 error")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
