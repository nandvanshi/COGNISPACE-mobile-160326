"""
Test suite for refactored features after backend refactoring:
- Assessments (list, custom assessments)
- Protocols (list, templates)
- Recurring Appointments (list)
- Messages (contacts, conversations)
- Availability (settings, blocked times)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_CREDS = {"identifier": "9999999999", "password": "password"}
CLIENT_CREDS = {"identifier": "8888888888", "password": "testpass123"}


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
        if response.status_code != 200:
            pytest.skip(f"Client login failed: {response.text}")
        data = response.json()
        return data.get("token")
    
    def test_therapist_login(self):
        """Test therapist can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "therapist"
        print(f"✓ Therapist login successful: {data['user']['full_name']}")


class TestAssessments:
    """Assessment feature tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_assessments_list(self, auth_headers):
        """Test GET /api/assessments - load assessments list"""
        response = requests.get(f"{BASE_URL}/api/assessments", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get assessments: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Assessments list loaded: {len(data)} assessments")
    
    def test_get_assessment_library(self, auth_headers):
        """Test GET /api/assessments/library - get assessment types"""
        response = requests.get(f"{BASE_URL}/api/assessments/library", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get assessment library: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        # Check for standard assessments
        expected_types = ["PHQ-9", "GAD-7", "PCL-5", "ASRS", "BDI-II", "DASS-21"]
        for assessment_type in expected_types:
            assert assessment_type in data, f"Missing assessment type: {assessment_type}"
        print(f"✓ Assessment library loaded: {list(data.keys())}")
    
    def test_get_custom_assessments(self, auth_headers):
        """Test GET /api/assessments/custom - get custom assessments"""
        response = requests.get(f"{BASE_URL}/api/assessments/custom", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get custom assessments: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Custom assessments loaded: {len(data)} custom assessments")


class TestProtocols:
    """Protocol feature tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_protocols_list(self, auth_headers):
        """Test GET /api/protocols - load protocols list"""
        response = requests.get(f"{BASE_URL}/api/protocols", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get protocols: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Protocols list loaded: {len(data)} protocols")
    
    def test_get_protocol_templates(self, auth_headers):
        """Test GET /api/protocols/templates - get protocol templates"""
        response = requests.get(f"{BASE_URL}/api/protocols/templates", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get protocol templates: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        # Check for expected templates
        expected_templates = ["CBT_ANXIETY", "CBT_DEPRESSION", "DBT_SKILLS", "ACT_GENERAL", "TRAUMA_PROCESSING"]
        for template in expected_templates:
            assert template in data, f"Missing protocol template: {template}"
        print(f"✓ Protocol templates loaded: {list(data.keys())}")


class TestRecurringAppointments:
    """Recurring appointments feature tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_recurring_patterns_list(self, auth_headers):
        """Test GET /api/recurring-appointments - load recurring patterns list"""
        response = requests.get(f"{BASE_URL}/api/recurring-appointments", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get recurring appointments: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Recurring appointments list loaded: {len(data)} patterns")


class TestMessaging:
    """Messaging feature tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_messaging_contacts(self, auth_headers):
        """Test GET /api/messaging-contacts - load messaging contacts"""
        response = requests.get(f"{BASE_URL}/api/messaging-contacts", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get messaging contacts: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Messaging contacts loaded: {len(data)} contacts")
        # Verify contact structure if any contacts exist
        if data:
            contact = data[0]
            assert "id" in contact, "Contact should have id"
            assert "name" in contact, "Contact should have name"
            print(f"  First contact: {contact.get('name', 'Unknown')}")
    
    def test_get_messages(self, auth_headers):
        """Test GET /api/messages - load messages"""
        response = requests.get(f"{BASE_URL}/api/messages", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get messages: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Messages loaded: {len(data)} messages")
    
    def test_get_unread_count(self, auth_headers):
        """Test GET /api/messages/unread-count - get unread message count"""
        response = requests.get(f"{BASE_URL}/api/messages/unread-count", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get unread count: {response.text}"
        data = response.json()
        assert "unread_count" in data, "Response should have unread_count"
        print(f"✓ Unread count: {data['unread_count']}")


class TestAvailability:
    """Availability settings feature tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_availability(self, auth_headers):
        """Test GET /api/availability - load availability settings"""
        response = requests.get(f"{BASE_URL}/api/availability", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get availability: {response.text}"
        data = response.json()
        # Verify availability structure
        assert "therapist_id" in data, "Response should have therapist_id"
        assert "session_duration" in data, "Response should have session_duration"
        # Check day fields
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            assert day in data, f"Response should have {day}"
        print(f"✓ Availability settings loaded: session_duration={data.get('session_duration')}min")
    
    def test_get_blocked_times(self, auth_headers):
        """Test GET /api/blocked-times - load blocked time slots"""
        response = requests.get(f"{BASE_URL}/api/blocked-times", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get blocked times: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Blocked times loaded: {len(data)} blocked slots")
        # Verify blocked time structure if any exist
        if data:
            bt = data[0]
            assert "id" in bt, "Blocked time should have id"
            assert "start_time" in bt, "Blocked time should have start_time"
            assert "end_time" in bt, "Blocked time should have end_time"
    
    def test_get_blocked_time_alternate_endpoint(self, auth_headers):
        """Test GET /api/blocked-time (singular) - alternate endpoint"""
        response = requests.get(f"{BASE_URL}/api/blocked-time", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get blocked time: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Blocked time (singular endpoint) loaded: {len(data)} blocked slots")


class TestSessionNotes:
    """Session notes feature tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_session_notes(self, auth_headers):
        """Test GET /api/session-notes - load session notes"""
        response = requests.get(f"{BASE_URL}/api/session-notes", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get session notes: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Session notes loaded: {len(data)} notes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
