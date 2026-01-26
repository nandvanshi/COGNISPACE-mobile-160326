"""
Notification Settings API Tests
Tests for email/whatsapp notification preferences management
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_CREDENTIALS = {
    "identifier": "9807306444",
    "password": "Abcd@1234"
}


@pytest.fixture(scope="module")
def therapist_token():
    """Get therapist authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=THERAPIST_CREDENTIALS
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "token" in data
    assert data["user"]["role"] == "therapist"
    return data["token"]


@pytest.fixture
def auth_headers(therapist_token):
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {therapist_token}",
        "Content-Type": "application/json"
    }


class TestNotificationSettingsChannelAvailability:
    """Tests for GET /api/notification-settings/channel-availability"""
    
    def test_get_channel_availability_success(self, auth_headers):
        """Test getting channel availability returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/channel-availability",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "email_allowed" in data
        assert "whatsapp_allowed" in data
        assert "whatsapp_configured" in data
        
        # Email should be allowed, WhatsApp should not be
        assert data["email_allowed"] is True
        assert data["whatsapp_allowed"] is False
        assert data["whatsapp_configured"] is False
    
    def test_channel_availability_requires_auth(self):
        """Test that channel availability requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/channel-availability"
        )
        assert response.status_code == 401


class TestNotificationSettingsEvents:
    """Tests for GET /api/notification-settings/events"""
    
    def test_get_events_success(self, auth_headers):
        """Test getting notification events returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/events",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 6  # At least 6 notification events
        
        # Check first event structure
        event = data[0]
        assert "event_key" in event
        assert "event_name" in event
        assert "supports_email" in event
        assert "supports_whatsapp" in event
        assert "send_email" in event
        assert "send_whatsapp" in event
        assert "email_allowed" in event
        assert "whatsapp_allowed" in event
    
    def test_events_contain_expected_types(self, auth_headers):
        """Test that all expected notification event types are present"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/events",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        event_keys = [e["event_key"] for e in data]
        
        expected_events = [
            "welcome_credentials",
            "password_changed",
            "appointment_confirmation",
            "appointment_reminder",
            "payment_receipt",
            "subscription_expiry"
        ]
        
        for expected in expected_events:
            assert expected in event_keys, f"Missing event: {expected}"
    
    def test_email_allowed_whatsapp_disabled(self, auth_headers):
        """Test that email is allowed and whatsapp is disabled for all events"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/events",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for event in data:
            # Email should be allowed for events that support it
            if event["supports_email"]:
                assert event["email_allowed"] is True
            # WhatsApp should be disabled for all events
            assert event["whatsapp_allowed"] is False
    
    def test_events_requires_auth(self):
        """Test that events endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/notification-settings/events"
        )
        assert response.status_code == 401


class TestNotificationSettingsPreferenceUpdate:
    """Tests for PUT /api/notification-settings/preference"""
    
    def test_update_email_preference_disable(self, auth_headers):
        """Test disabling email for a notification event"""
        # Disable email for appointment_confirmation
        response = requests.put(
            f"{BASE_URL}/api/notification-settings/preference",
            headers=auth_headers,
            json={
                "event_key": "appointment_confirmation",
                "send_email": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Preference updated successfully"
        
        # Verify the change persisted
        events_response = requests.get(
            f"{BASE_URL}/api/notification-settings/events",
            headers=auth_headers
        )
        events = events_response.json()
        appointment_event = next(e for e in events if e["event_key"] == "appointment_confirmation")
        assert appointment_event["send_email"] is False
    
    def test_update_email_preference_enable(self, auth_headers):
        """Test enabling email for a notification event"""
        # Re-enable email for appointment_confirmation
        response = requests.put(
            f"{BASE_URL}/api/notification-settings/preference",
            headers=auth_headers,
            json={
                "event_key": "appointment_confirmation",
                "send_email": True
            }
        )
        assert response.status_code == 200
        
        # Verify the change persisted
        events_response = requests.get(
            f"{BASE_URL}/api/notification-settings/events",
            headers=auth_headers
        )
        events = events_response.json()
        appointment_event = next(e for e in events if e["event_key"] == "appointment_confirmation")
        assert appointment_event["send_email"] is True
    
    def test_update_invalid_event_key(self, auth_headers):
        """Test updating with invalid event key returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/notification-settings/preference",
            headers=auth_headers,
            json={
                "event_key": "invalid_event_key",
                "send_email": True
            }
        )
        assert response.status_code == 400
        assert "Invalid event key" in response.json()["detail"]
    
    def test_enable_whatsapp_when_not_allowed(self, auth_headers):
        """Test enabling WhatsApp when not allowed by subscription returns 403"""
        response = requests.put(
            f"{BASE_URL}/api/notification-settings/preference",
            headers=auth_headers,
            json={
                "event_key": "appointment_confirmation",
                "send_whatsapp": True
            }
        )
        assert response.status_code == 403
        assert "WhatsApp notifications not allowed" in response.json()["detail"]
    
    def test_preference_update_requires_auth(self):
        """Test that preference update requires authentication"""
        response = requests.put(
            f"{BASE_URL}/api/notification-settings/preference",
            json={
                "event_key": "appointment_confirmation",
                "send_email": True
            }
        )
        assert response.status_code == 401


class TestNotificationSettingsBulkUpdate:
    """Tests for PUT /api/notification-settings/preferences/bulk"""
    
    def test_bulk_update_preferences(self, auth_headers):
        """Test bulk updating multiple notification preferences"""
        response = requests.put(
            f"{BASE_URL}/api/notification-settings/preferences/bulk",
            headers=auth_headers,
            json=[
                {"event_key": "welcome_credentials", "send_email": True},
                {"event_key": "payment_receipt", "send_email": True}
            ]
        )
        assert response.status_code == 200
        data = response.json()
        assert "Updated 2 preferences" in data["message"]
