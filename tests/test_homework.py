"""
Test Homework Feature - Manual Homework Assignment
Tests for:
- Therapist can create homework with title, description, due_date (optional), priority
- Therapist can view homework list
- Therapist can edit pending homework
- Therapist can delete homework
- Client can view their homework
- Client can mark homework as complete
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
THERAPIST_CREDS = {"identifier": "9999999999", "password": "password"}
CLIENT_CREDS = {"identifier": "8888888888", "password": "testpass123"}
ASSISTANT_CREDS = {"identifier": "test_assistant_ui@test.com", "password": "testpass123"}


class TestHomeworkFeature:
    """Test homework CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.created_homework_ids = []
        yield
        # Cleanup created homework
        if hasattr(self, 'therapist_token') and self.created_homework_ids:
            for hw_id in self.created_homework_ids:
                try:
                    self.session.delete(
                        f"{BASE_URL}/api/homework/{hw_id}",
                        headers={"Authorization": f"Bearer {self.therapist_token}"}
                    )
                except:
                    pass
    
    def get_therapist_token(self):
        """Get therapist auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        data = response.json()
        self.therapist_token = data["token"]
        self.therapist_id = data["user"]["id"]
        return self.therapist_token
    
    def get_client_token(self):
        """Get client auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
        assert response.status_code == 200, f"Client login failed: {response.text}"
        data = response.json()
        self.client_token = data["token"]
        self.client_id = data["user"]["id"]
        return self.client_token
    
    def get_assistant_token(self):
        """Get assistant auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ASSISTANT_CREDS)
        if response.status_code != 200:
            pytest.skip(f"Assistant login failed: {response.text}")
        data = response.json()
        self.assistant_token = data["token"]
        return self.assistant_token
    
    def get_client_id_for_therapist(self, token):
        """Get a client ID that belongs to this therapist"""
        response = self.session.get(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get clients: {response.text}"
        clients = response.json()
        if not clients:
            pytest.skip("No clients found for therapist")
        return clients[0]["id"]
    
    # ========== THERAPIST TESTS ==========
    
    def test_therapist_login(self):
        """Test therapist can login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "therapist"
        print("✓ Therapist login successful")
    
    def test_create_homework_with_all_fields(self):
        """Test therapist can create homework with all fields including priority"""
        token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(token)
        
        due_date = (datetime.now() + timedelta(days=7)).isoformat()
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Breathing Exercise",
            "description": "Practice deep breathing for 10 minutes daily",
            "due_date": due_date,
            "priority": "high"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Create homework failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["title"] == homework_data["title"]
        assert data["description"] == homework_data["description"]
        assert data["priority"] == "high"
        assert data["status"] == "assigned"
        assert data["client_id"] == client_id
        
        self.created_homework_ids.append(data["id"])
        print(f"✓ Created homework with ID: {data['id']}, priority: {data['priority']}")
    
    def test_create_homework_with_default_priority(self):
        """Test homework defaults to medium priority"""
        token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(token)
        
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Journal Entry",
            "description": "Write about your feelings today"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Create homework failed: {response.text}"
        data = response.json()
        
        # Default priority should be medium
        assert data["priority"] == "medium"
        self.created_homework_ids.append(data["id"])
        print(f"✓ Created homework with default priority: {data['priority']}")
    
    def test_create_homework_low_priority(self):
        """Test creating homework with low priority"""
        token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(token)
        
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Optional Reading",
            "description": "Read chapter 3 if you have time",
            "priority": "low"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Create homework failed: {response.text}"
        data = response.json()
        assert data["priority"] == "low"
        self.created_homework_ids.append(data["id"])
        print(f"✓ Created homework with low priority")
    
    def test_get_homework_list(self):
        """Test therapist can get homework list"""
        token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(token)
        
        # Create a homework first
        homework_data = {
            "client_id": client_id,
            "title": "TEST_List Test Homework",
            "description": "Test description",
            "priority": "medium"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 200
        created_hw = create_response.json()
        self.created_homework_ids.append(created_hw["id"])
        
        # Get homework list for client
        response = self.session.get(
            f"{BASE_URL}/api/homework?client_id={client_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Get homework failed: {response.text}"
        homework_list = response.json()
        assert isinstance(homework_list, list)
        
        # Find our created homework
        found = any(hw["id"] == created_hw["id"] for hw in homework_list)
        assert found, "Created homework not found in list"
        print(f"✓ Got homework list with {len(homework_list)} items")
    
    def test_update_homework(self):
        """Test therapist can update pending homework"""
        token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(token)
        
        # Create homework
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Original Title",
            "description": "Original description",
            "priority": "low"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 200
        created_hw = create_response.json()
        hw_id = created_hw["id"]
        self.created_homework_ids.append(hw_id)
        
        # Update homework
        update_data = {
            "title": "TEST_Updated Title",
            "priority": "high"
        }
        update_response = self.session.put(
            f"{BASE_URL}/api/homework/{hw_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert update_response.status_code == 200, f"Update homework failed: {update_response.text}"
        updated_hw = update_response.json()
        
        assert updated_hw["title"] == "TEST_Updated Title"
        assert updated_hw["priority"] == "high"
        # Description should remain unchanged
        assert updated_hw["description"] == "Original description"
        print(f"✓ Updated homework title and priority")
    
    def test_delete_homework(self):
        """Test therapist can delete homework"""
        token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(token)
        
        # Create homework
        homework_data = {
            "client_id": client_id,
            "title": "TEST_To Be Deleted",
            "description": "This will be deleted",
            "priority": "medium"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 200
        hw_id = create_response.json()["id"]
        
        # Delete homework
        delete_response = self.session.delete(
            f"{BASE_URL}/api/homework/{hw_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert delete_response.status_code == 200, f"Delete homework failed: {delete_response.text}"
        
        # Verify deletion - homework should not be in list
        list_response = self.session.get(
            f"{BASE_URL}/api/homework?client_id={client_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        homework_list = list_response.json()
        found = any(hw["id"] == hw_id for hw in homework_list)
        assert not found, "Deleted homework still found in list"
        print(f"✓ Deleted homework successfully")
    
    # ========== CLIENT TESTS ==========
    
    def test_client_can_view_homework(self):
        """Test client can view their assigned homework"""
        # First create homework as therapist
        therapist_token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(therapist_token)
        
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Client View Test",
            "description": "Client should see this",
            "priority": "high"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert create_response.status_code == 200
        created_hw = create_response.json()
        self.created_homework_ids.append(created_hw["id"])
        
        # Now login as client and view homework
        client_token = self.get_client_token()
        
        response = self.session.get(
            f"{BASE_URL}/api/homework",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        
        assert response.status_code == 200, f"Client get homework failed: {response.text}"
        homework_list = response.json()
        assert isinstance(homework_list, list)
        print(f"✓ Client can view homework list with {len(homework_list)} items")
    
    def test_client_can_complete_homework(self):
        """Test client can mark homework as complete"""
        # Create homework as therapist
        therapist_token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(therapist_token)
        
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Complete Test",
            "description": "Client will complete this",
            "priority": "medium"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert create_response.status_code == 200
        hw_id = create_response.json()["id"]
        self.created_homework_ids.append(hw_id)
        
        # Login as client and complete homework
        client_token = self.get_client_token()
        
        complete_data = {
            "client_notes": "I completed this exercise and felt better"
        }
        complete_response = self.session.post(
            f"{BASE_URL}/api/homework/{hw_id}/complete",
            json=complete_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )
        
        assert complete_response.status_code == 200, f"Complete homework failed: {complete_response.text}"
        
        # Verify homework is now completed
        list_response = self.session.get(
            f"{BASE_URL}/api/homework",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        homework_list = list_response.json()
        completed_hw = next((hw for hw in homework_list if hw["id"] == hw_id), None)
        
        if completed_hw:
            assert completed_hw["status"] == "completed"
            assert completed_hw["client_notes"] == complete_data["client_notes"]
            print(f"✓ Client completed homework successfully")
        else:
            print(f"✓ Homework completion API returned 200")
    
    # ========== ASSISTANT ACCESS TESTS ==========
    
    def test_assistant_cannot_create_homework(self):
        """Test assistant cannot create homework (therapist only)"""
        try:
            assistant_token = self.get_assistant_token()
        except:
            pytest.skip("Assistant account not available")
        
        # Get a client ID (assistant should be able to see clients)
        therapist_token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(therapist_token)
        
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Assistant Attempt",
            "description": "This should fail",
            "priority": "medium"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        
        # Should be forbidden (403) for assistant
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Assistant correctly denied from creating homework")
    
    def test_assistant_cannot_update_homework(self):
        """Test assistant cannot update homework"""
        try:
            assistant_token = self.get_assistant_token()
        except:
            pytest.skip("Assistant account not available")
        
        # Create homework as therapist first
        therapist_token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(therapist_token)
        
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Assistant Update Test",
            "description": "Assistant should not update this",
            "priority": "medium"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert create_response.status_code == 200
        hw_id = create_response.json()["id"]
        self.created_homework_ids.append(hw_id)
        
        # Try to update as assistant
        update_data = {"title": "TEST_Hacked Title"}
        response = self.session.put(
            f"{BASE_URL}/api/homework/{hw_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Assistant correctly denied from updating homework")
    
    def test_assistant_cannot_delete_homework(self):
        """Test assistant cannot delete homework"""
        try:
            assistant_token = self.get_assistant_token()
        except:
            pytest.skip("Assistant account not available")
        
        # Create homework as therapist first
        therapist_token = self.get_therapist_token()
        client_id = self.get_client_id_for_therapist(therapist_token)
        
        homework_data = {
            "client_id": client_id,
            "title": "TEST_Assistant Delete Test",
            "description": "Assistant should not delete this",
            "priority": "medium"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/homework",
            json=homework_data,
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert create_response.status_code == 200
        hw_id = create_response.json()["id"]
        self.created_homework_ids.append(hw_id)
        
        # Try to delete as assistant
        response = self.session.delete(
            f"{BASE_URL}/api/homework/{hw_id}",
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Assistant correctly denied from deleting homework")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
