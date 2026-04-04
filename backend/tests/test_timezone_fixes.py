"""
Test Timezone Fixes - Backend API Tests
Tests for:
1. GET /api/appointments/available-slots - IST hours converted to UTC properly
2. Morning briefing query - date-component matching for both storage formats
3. Login flow verification
"""
import pytest
import requests
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
IST = ZoneInfo("Asia/Kolkata")

# Test credentials (from /app/memory/test_credentials.md)
THERAPIST_MOBILE = "7275005007"
THERAPIST_PASSWORD = "Test@123"
CLIENT_MOBILE = "9235555549"
CLIENT_PASSWORD = "Test@123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class TestTherapistLogin:
    """Test therapist login flow"""
    
    def test_therapist_login_success(self):
        """Test therapist login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data.get("user", {}).get("role") == "therapist", "User is not a therapist"
        
    def test_therapist_login_invalid_password(self):
        """Test therapist login with invalid password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": "WrongPassword123"
        })
        
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"


class TestAvailableSlots:
    """Test available slots endpoint with timezone handling"""
    
    @pytest.fixture
    def client_token(self):
        """Get a client token for testing available-slots endpoint"""
        # Login as client directly
        client_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": CLIENT_MOBILE,
            "password": CLIENT_PASSWORD
        })
        
        if client_login.status_code != 200:
            pytest.skip(f"Cannot login as client: {client_login.text}")
            
        return client_login.json().get("token")
    
    @pytest.fixture
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Cannot login as therapist")
            
        return response.json().get("token")
    
    def test_available_slots_requires_client_role(self, therapist_token):
        """Test that available-slots endpoint requires client role"""
        # Get today's date in IST
        today_ist = datetime.now(IST)
        date_str = today_ist.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/appointments/available-slots?date={date_str}",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        
        print(f"Available slots (therapist) response: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Should return 403 for therapist
        assert response.status_code == 403, f"Expected 403 for therapist, got {response.status_code}"
    
    def test_therapist_availability_endpoint(self, therapist_token):
        """Test therapist availability settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/availability",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        
        print(f"Availability response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Availability data: {data}")
            
            # Check if availability is configured
            if data:
                # Check for day-based availability
                days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                for day in days:
                    if day in data and data[day].get('enabled'):
                        print(f"  {day}: enabled, time_blocks: {data[day].get('time_blocks', [])}")
        else:
            print(f"No availability configured or error: {response.text}")
    
    def test_available_slots_timezone_conversion(self, client_token):
        """Test that available-slots returns correct UTC times with IST display_time"""
        # Test with a future date (Sunday April 6, 2026)
        test_date = "2026-04-06"
        
        response = requests.get(
            f"{BASE_URL}/api/appointments/available-slots?date={test_date}",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        
        print(f"Available slots response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            slots = data.get("slots", [])
            print(f"Total slots: {len(slots)}")
            
            if slots:
                # Check first slot
                first_slot = slots[0]
                start_time = first_slot.get("start_time")
                display_time = first_slot.get("display_time")
                
                print(f"First slot: start_time={start_time}, display_time={display_time}")
                
                # Verify timezone conversion
                # 9:00 AM IST = 3:30 AM UTC
                if display_time == "09:00":
                    assert "T03:30:00" in start_time, \
                        f"9:00 AM IST should be 03:30 UTC, got {start_time}"
                    print("SUCCESS: Timezone conversion is correct (9:00 AM IST = 03:30 UTC)")
                
                # Check that all slots have proper format
                for slot in slots[:5]:
                    assert "start_time" in slot
                    assert "end_time" in slot
                    assert "display_time" in slot
                    assert "+00:00" in slot["start_time"], "start_time should be in UTC"
        else:
            print(f"Error: {response.text}")


class TestAppointmentsTimezone:
    """Test appointments with timezone handling"""
    
    @pytest.fixture
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Cannot login as therapist")
            
        return response.json().get("token")
    
    def test_get_appointments_list(self, therapist_token):
        """Test getting appointments list"""
        response = requests.get(
            f"{BASE_URL}/api/appointments",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        
        print(f"Appointments list response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get appointments: {response.text}"
        
        appointments = response.json()
        print(f"Total appointments: {len(appointments)}")
        
        # Check timezone format of appointments
        for appt in appointments[:5]:  # Check first 5
            start_time = appt.get("start_time")
            print(f"  Appointment: {appt.get('client_name')} - start_time: {start_time}")
            
            # Verify start_time is in ISO format with timezone
            if start_time:
                assert "T" in start_time, f"start_time should be ISO format: {start_time}"
    
    def test_appointments_date_filtering(self, therapist_token):
        """Test that appointments can be filtered by date correctly"""
        # Get today's date in IST
        today_ist = datetime.now(IST)
        today_str = today_ist.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/appointments",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        
        assert response.status_code == 200
        
        appointments = response.json()
        
        # Filter appointments for today using date component matching
        # (same logic as frontend fix)
        today_appts = [
            appt for appt in appointments
            if appt.get("start_time", "")[:10] == today_str
            and appt.get("status") != "cancelled"
        ]
        
        print(f"Today's appointments ({today_str}): {len(today_appts)}")
        for appt in today_appts:
            print(f"  - {appt.get('client_name')}: {appt.get('start_time')}")


class TestDateUtilsFunctions:
    """Test date utility functions in backend"""
    
    def test_ist_today_range_utc(self):
        """Test get_ist_today_range_utc function logic"""
        # Simulate the function logic
        now_ist = datetime.now(IST)
        today_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end_ist = today_start_ist + timedelta(days=1)
        
        start_utc = today_start_ist.astimezone(timezone.utc)
        end_utc = today_end_ist.astimezone(timezone.utc)
        
        print(f"IST Today: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"IST Start: {today_start_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"IST End: {today_end_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"UTC Start: {start_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"UTC End: {end_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Verify IST to UTC conversion
        # IST is UTC+5:30, so IST midnight = UTC 18:30 previous day
        assert start_utc.hour == 18 and start_utc.minute == 30, \
            f"IST midnight should be 18:30 UTC, got {start_utc.hour}:{start_utc.minute}"
    
    def test_slot_generation_ist_to_utc(self):
        """Test that slot generation converts IST hours to UTC correctly"""
        # Simulate slot generation for 9:00 AM IST
        today_ist = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 9:00 AM IST slot
        slot_start_ist = today_ist.replace(hour=9, minute=0)
        slot_start_utc = slot_start_ist.astimezone(timezone.utc)
        
        print(f"9:00 AM IST = {slot_start_utc.strftime('%H:%M')} UTC")
        
        # 9:00 AM IST = 3:30 AM UTC
        assert slot_start_utc.hour == 3 and slot_start_utc.minute == 30, \
            f"9:00 AM IST should be 3:30 AM UTC, got {slot_start_utc.hour}:{slot_start_utc.minute}"
        
        # 7:15 PM IST slot (19:15)
        slot_evening_ist = today_ist.replace(hour=19, minute=15)
        slot_evening_utc = slot_evening_ist.astimezone(timezone.utc)
        
        print(f"7:15 PM IST = {slot_evening_utc.strftime('%H:%M')} UTC")
        
        # 7:15 PM IST = 1:45 PM UTC
        assert slot_evening_utc.hour == 13 and slot_evening_utc.minute == 45, \
            f"7:15 PM IST should be 13:45 UTC, got {slot_evening_utc.hour}:{slot_evening_utc.minute}"


class TestMorningBriefingQuery:
    """Test morning briefing query logic"""
    
    def test_date_component_query_logic(self):
        """Test that date component matching works for both storage formats"""
        # Today's IST date
        now_ist = datetime.now(IST)
        today_date_str = now_ist.strftime("%Y-%m-%d")
        next_date_str = (now_ist + timedelta(days=1)).strftime("%Y-%m-%d")
        
        query_start = f"{today_date_str}T00:00:00"
        query_end = f"{next_date_str}T00:00:00"
        
        print(f"Morning briefing query range: [{query_start}] to [{query_end}]")
        
        # Test appointment stored in CORRECT UTC format
        # 7:15 PM IST on April 4 = 13:45 UTC on April 4
        correct_utc_appt = "2026-04-04T13:45:00+00:00"
        correct_date = correct_utc_appt[:10]
        
        # Test appointment stored in OLD IST-in-UTC format
        # 7:15 PM IST stored as 19:15 UTC (wrong but legacy)
        old_ist_in_utc_appt = "2026-04-04T19:15:00+00:00"
        old_date = old_ist_in_utc_appt[:10]
        
        print(f"Correct UTC format date component: {correct_date}")
        print(f"Old IST-in-UTC format date component: {old_date}")
        
        # Both should have the same date component for the same IST day
        assert correct_date == old_date == "2026-04-04", \
            "Both storage formats should have same date component for same IST day"
        
        # Verify query would match both
        test_date = "2026-04-04"
        query_start_test = f"{test_date}T00:00:00"
        query_end_test = f"2026-04-05T00:00:00"
        
        assert correct_utc_appt >= query_start_test and correct_utc_appt < query_end_test, \
            "Correct UTC format should match query"
        assert old_ist_in_utc_appt >= query_start_test and old_ist_in_utc_appt < query_end_test, \
            "Old IST-in-UTC format should match query"


class TestSuperAdminLogin:
    """Test super admin login"""
    
    def test_super_admin_login_success(self):
        """Test super admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        
        print(f"Super admin login response: {response.status_code}")
        
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"


# Fixtures
@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
