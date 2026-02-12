"""
Test suite for PWA Sound & Badge Notification Preferences
Tests GET/PUT /api/notifications/preferences endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestNotificationPreferences:
    """Tests for notification preferences (sound & badge) endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get auth token"""
        # Login as super admin
        login_response = requests.post(
            f"{BASE_URL}/api/auth/super-admin-login",
            json={"username": "admin", "password": "admin123"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        yield
        # Cleanup - restore defaults
        requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": True, "badge_enabled": True}
        )
    
    def test_get_preferences_returns_defaults(self):
        """GET /api/notifications/preferences returns sound_enabled and badge_enabled defaults (true)"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "sound_enabled" in data, "Response missing sound_enabled field"
        assert "badge_enabled" in data, "Response missing badge_enabled field"
        
        # Verify types
        assert isinstance(data["sound_enabled"], bool), "sound_enabled should be boolean"
        assert isinstance(data["badge_enabled"], bool), "badge_enabled should be boolean"
    
    def test_get_preferences_without_auth_fails(self):
        """GET /api/notifications/preferences without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/notifications/preferences")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_update_sound_preference_to_false(self):
        """PUT /api/notifications/preferences updates sound_enabled to false"""
        # Update sound to false
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": False, "badge_enabled": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert data.get("sound_enabled") == False, "sound_enabled should be False"
        assert data.get("badge_enabled") == True, "badge_enabled should be True"
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["sound_enabled"] == False, "sound_enabled not persisted"
    
    def test_update_badge_preference_to_false(self):
        """PUT /api/notifications/preferences updates badge_enabled to false"""
        # Update badge to false
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": True, "badge_enabled": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert data.get("sound_enabled") == True, "sound_enabled should be True"
        assert data.get("badge_enabled") == False, "badge_enabled should be False"
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["badge_enabled"] == False, "badge_enabled not persisted"
    
    def test_update_both_preferences_to_false(self):
        """PUT /api/notifications/preferences updates both sound and badge to false"""
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": False, "badge_enabled": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("sound_enabled") == False
        assert data.get("badge_enabled") == False
        
        # Verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers
        )
        get_data = get_response.json()
        assert get_data["sound_enabled"] == False
        assert get_data["badge_enabled"] == False
    
    def test_update_preferences_to_true(self):
        """PUT /api/notifications/preferences updates both to true"""
        # First set to false
        requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": False, "badge_enabled": False}
        )
        
        # Then set to true
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": True, "badge_enabled": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("sound_enabled") == True
        assert data.get("badge_enabled") == True
    
    def test_update_preferences_without_auth_fails(self):
        """PUT /api/notifications/preferences without auth returns 401/403"""
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            json={"sound_enabled": False, "badge_enabled": False}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_update_preferences_partial_update(self):
        """PUT /api/notifications/preferences with partial data works"""
        # Update only sound_enabled
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("sound_enabled") == False
    
    def test_preferences_response_has_message(self):
        """PUT /api/notifications/preferences returns success message"""
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": True, "badge_enabled": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data, "Response should contain message field"
        assert "success" in data["message"].lower() or "updated" in data["message"].lower()


class TestNotificationPreferencesWithTherapist:
    """Tests for notification preferences with therapist user"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get therapist auth token"""
        # Try to login as existing therapist
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": "9807306444", "password": "Abcd@1234"}
        )
        
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            self.therapist_available = True
        else:
            self.therapist_available = False
            pytest.skip("Therapist login failed - skipping therapist-specific tests")
        
        yield
        
        # Cleanup - restore defaults
        if self.therapist_available:
            requests.put(
                f"{BASE_URL}/api/notifications/preferences",
                headers=self.headers,
                json={"sound_enabled": True, "badge_enabled": True}
            )
    
    def test_therapist_can_get_preferences(self):
        """Therapist can GET /api/notifications/preferences"""
        if not self.therapist_available:
            pytest.skip("Therapist not available")
        
        response = requests.get(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sound_enabled" in data
        assert "badge_enabled" in data
    
    def test_therapist_can_update_preferences(self):
        """Therapist can PUT /api/notifications/preferences"""
        if not self.therapist_available:
            pytest.skip("Therapist not available")
        
        response = requests.put(
            f"{BASE_URL}/api/notifications/preferences",
            headers=self.headers,
            json={"sound_enabled": False, "badge_enabled": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("sound_enabled") == False
        assert data.get("badge_enabled") == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
