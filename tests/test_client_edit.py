"""
Backend API Tests for Client Edit Functionality
Tests:
- PUT /api/clients/{id} - Update client profile (full_name, mobile, email, age, guardian, address, emergency contact, intake summary, profile_photo)
- POST /api/clients/{id}/reset-password - Reset client password by therapist
- GET /api/clients - Returns profile_photo field
- GET /api/clients/{id} - Returns profile_photo field
- client_id field remains immutable after updates
- Mobile validation (10 digits)
- Email uniqueness check
"""
import pytest
import requests
import os
import uuid
import random

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from previous iterations
THERAPIST_MOBILE = "1234567890"
THERAPIST_PASSWORD = "TestPass123"
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "admin123"


class TestClientEditSetup:
    """Setup fixtures for client edit tests"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token for testing"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Could not login as therapist: {response.text}")
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def test_client(self, therapist_token):
        """Create a test client for edit tests"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        unique_mobile = f"99{random.randint(10000000, 99999999)}"
        unique_email = f"test_edit_{uuid.uuid4().hex[:8]}@example.com"
        
        client_data = {
            "mobile": unique_mobile,
            "full_name": "Test Edit Client",
            "password": "TestClientPass123",
            "email": unique_email,
            "age": 30,
            "guardian_name": "Original Guardian",
            "address": "123 Original Street",
            "referred_by": "Dr. Original",
            "intake_summary": "Original intake summary",
            "emergency_contact_name": "Original Emergency Contact",
            "emergency_contact_phone": "1112223333"
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=headers)
        if response.status_code != 200:
            pytest.skip(f"Could not create test client: {response.text}")
        
        data = response.json()
        return {
            "id": data["id"],
            "client_id": data["client_id"],
            "original_mobile": unique_mobile,
            "original_email": unique_email
        }


class TestClientUpdateFullName(TestClientEditSetup):
    """Test PUT /api/clients/{id} updates full_name"""
    
    def test_update_full_name(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update full_name"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_name = f"Updated Name {uuid.uuid4().hex[:6]}"
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"full_name": new_name},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["full_name"] == new_name, f"Expected full_name to be '{new_name}', got '{data['full_name']}'"
        print(f"✓ full_name updated successfully to '{new_name}'")
        
        # Verify with GET
        get_response = requests.get(f"{BASE_URL}/api/clients/{test_client['id']}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["full_name"] == new_name, "GET should return updated full_name"
        print(f"✓ GET confirms full_name update persisted")


class TestClientUpdateMobile(TestClientEditSetup):
    """Test PUT /api/clients/{id} updates mobile with validation"""
    
    def test_update_mobile_valid_10_digits(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update mobile with valid 10-digit number"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_mobile = f"88{random.randint(10000000, 99999999)}"
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"mobile": new_mobile},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["mobile"] == new_mobile, f"Expected mobile to be '{new_mobile}', got '{data['mobile']}'"
        print(f"✓ mobile updated successfully to '{new_mobile}'")
    
    def test_update_mobile_invalid_format_short(self, therapist_token, test_client):
        """PUT /api/clients/{id} should reject mobile with less than 10 digits"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        invalid_mobile = "12345"  # Only 5 digits
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"mobile": invalid_mobile},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid mobile, got {response.status_code}: {response.text}"
        assert "10 digits" in response.json().get("detail", "").lower(), "Error should mention 10 digits"
        print(f"✓ Invalid mobile (short) correctly rejected with 400")
    
    def test_update_mobile_invalid_format_long(self, therapist_token, test_client):
        """PUT /api/clients/{id} should reject mobile with more than 10 digits"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        invalid_mobile = "12345678901234"  # 14 digits
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"mobile": invalid_mobile},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid mobile, got {response.status_code}: {response.text}"
        print(f"✓ Invalid mobile (long) correctly rejected with 400")
    
    def test_update_mobile_invalid_format_letters(self, therapist_token, test_client):
        """PUT /api/clients/{id} should reject mobile with non-digit characters"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        invalid_mobile = "123abc7890"  # Contains letters
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"mobile": invalid_mobile},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid mobile, got {response.status_code}: {response.text}"
        print(f"✓ Invalid mobile (letters) correctly rejected with 400")


class TestClientUpdateEmail(TestClientEditSetup):
    """Test PUT /api/clients/{id} updates email with uniqueness check"""
    
    def test_update_email_valid(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update email"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_email = f"updated_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"email": new_email},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["email"] == new_email, f"Expected email to be '{new_email}', got '{data['email']}'"
        print(f"✓ email updated successfully to '{new_email}'")
    
    def test_update_email_uniqueness_check(self, therapist_token, test_client):
        """PUT /api/clients/{id} should reject duplicate email"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Create another client with a specific email
        other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
        other_mobile = f"77{random.randint(10000000, 99999999)}"
        
        create_response = requests.post(f"{BASE_URL}/api/clients", json={
            "mobile": other_mobile,
            "full_name": "Other Client",
            "password": "OtherPass123",
            "email": other_email
        }, headers=headers)
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create other client: {create_response.text}")
        
        # Try to update test_client with the other client's email
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"email": other_email},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}: {response.text}"
        assert "already in use" in response.json().get("detail", "").lower() or "already" in response.json().get("detail", "").lower(), "Error should mention email already in use"
        print(f"✓ Duplicate email correctly rejected with 400")


class TestClientUpdateProfileFields(TestClientEditSetup):
    """Test PUT /api/clients/{id} updates profile fields (age, guardian, address, etc.)"""
    
    def test_update_age(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update age"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_age = 35
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"age": new_age},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["age"] == new_age, f"Expected age to be {new_age}"
        print(f"✓ age updated successfully to {new_age}")
    
    def test_update_guardian_name(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update guardian_name"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_guardian = "Updated Guardian Name"
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"guardian_name": new_guardian},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["guardian_name"] == new_guardian, f"Expected guardian_name to be '{new_guardian}'"
        print(f"✓ guardian_name updated successfully")
    
    def test_update_address(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update address"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_address = "456 Updated Street, New City, NC 12345"
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"address": new_address},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["address"] == new_address, f"Expected address to be '{new_address}'"
        print(f"✓ address updated successfully")
    
    def test_update_emergency_contact(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update emergency_contact_name and emergency_contact_phone"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_contact_name = "Updated Emergency Contact"
        new_contact_phone = "9998887777"
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={
                "emergency_contact_name": new_contact_name,
                "emergency_contact_phone": new_contact_phone
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["emergency_contact_name"] == new_contact_name, f"Expected emergency_contact_name to be '{new_contact_name}'"
        assert data["emergency_contact_phone"] == new_contact_phone, f"Expected emergency_contact_phone to be '{new_contact_phone}'"
        print(f"✓ emergency contact updated successfully")
    
    def test_update_intake_summary(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update intake_summary"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_summary = "Updated intake summary with detailed notes about the client's history and treatment goals."
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"intake_summary": new_summary},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["intake_summary"] == new_summary, f"Expected intake_summary to be updated"
        print(f"✓ intake_summary updated successfully")


class TestClientUpdateProfilePhoto(TestClientEditSetup):
    """Test PUT /api/clients/{id} updates profile_photo URL"""
    
    def test_update_profile_photo(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update profile_photo URL"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_photo_url = "https://example.com/photos/client123.jpg"
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"profile_photo": new_photo_url},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["profile_photo"] == new_photo_url, f"Expected profile_photo to be '{new_photo_url}'"
        print(f"✓ profile_photo updated successfully")


class TestClientPasswordReset(TestClientEditSetup):
    """Test POST /api/clients/{id}/reset-password"""
    
    def test_reset_client_password(self, therapist_token, test_client):
        """POST /api/clients/{id}/reset-password should reset client password"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        new_password = "NewResetPassword123"
        
        response = requests.post(
            f"{BASE_URL}/api/clients/{test_client['id']}/reset-password",
            json={"new_password": new_password},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "success" in response.json().get("message", "").lower(), "Response should indicate success"
        print(f"✓ Client password reset successfully")


class TestClientGetEndpoints(TestClientEditSetup):
    """Test GET endpoints return profile_photo field"""
    
    def test_get_clients_returns_profile_photo(self, therapist_token, test_client):
        """GET /api/clients should return profile_photo field"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # First update profile_photo
        photo_url = "https://example.com/test_photo.jpg"
        requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json={"profile_photo": photo_url},
            headers=headers
        )
        
        # Get all clients
        response = requests.get(f"{BASE_URL}/api/clients", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        clients = response.json()
        # Find our test client
        test_client_data = next((c for c in clients if c["id"] == test_client["id"]), None)
        
        assert test_client_data is not None, "Test client should be in the list"
        assert "profile_photo" in test_client_data, "profile_photo field should be present in GET /api/clients response"
        print(f"✓ GET /api/clients returns profile_photo field")
    
    def test_get_client_by_id_returns_profile_photo(self, therapist_token, test_client):
        """GET /api/clients/{id} should return profile_photo field"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        response = requests.get(f"{BASE_URL}/api/clients/{test_client['id']}", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "profile_photo" in data, "profile_photo field should be present in GET /api/clients/{id} response"
        print(f"✓ GET /api/clients/{{id}} returns profile_photo field")


class TestClientIdImmutable(TestClientEditSetup):
    """Test that client_id remains immutable after updates"""
    
    def test_client_id_unchanged_after_update(self, therapist_token, test_client):
        """client_id should remain unchanged after profile updates"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        original_client_id = test_client["client_id"]
        
        # Perform multiple updates
        updates = [
            {"full_name": "Name Change 1"},
            {"age": 40},
            {"address": "New Address"},
            {"intake_summary": "New summary"}
        ]
        
        for update in updates:
            response = requests.put(
                f"{BASE_URL}/api/clients/{test_client['id']}",
                json=update,
                headers=headers
            )
            assert response.status_code == 200, f"Update failed: {response.text}"
            
            data = response.json()
            assert data["client_id"] == original_client_id, f"client_id changed from '{original_client_id}' to '{data['client_id']}' after update"
        
        # Final verification with GET
        get_response = requests.get(f"{BASE_URL}/api/clients/{test_client['id']}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["client_id"] == original_client_id, "client_id should remain unchanged"
        print(f"✓ client_id remains immutable: '{original_client_id}'")


class TestClientUpdateMultipleFields(TestClientEditSetup):
    """Test updating multiple fields at once"""
    
    def test_update_multiple_fields_at_once(self, therapist_token, test_client):
        """PUT /api/clients/{id} should update multiple fields in one request"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        update_data = {
            "full_name": "Multi Update Client",
            "age": 45,
            "guardian_name": "Multi Guardian",
            "address": "789 Multi Street",
            "emergency_contact_name": "Multi Emergency",
            "emergency_contact_phone": "5554443333",
            "intake_summary": "Multi update intake summary"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        for key, value in update_data.items():
            assert data[key] == value, f"Expected {key} to be '{value}', got '{data[key]}'"
        
        print(f"✓ Multiple fields updated successfully in one request")


class TestClientUpdateNotFound:
    """Test update for non-existent client"""
    
    @pytest.fixture
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Could not login as therapist: {response.text}")
        return response.json()["token"]
    
    def test_update_nonexistent_client(self, therapist_token):
        """PUT /api/clients/{id} should return 404 for non-existent client"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        fake_id = str(uuid.uuid4())
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{fake_id}",
            json={"full_name": "Test"},
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Non-existent client correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
