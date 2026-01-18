"""
Test Data Isolation Security Fix - P0 Security
Tests that:
1. GET /api/clients returns only clients assigned to current therapist
2. GET /api/clients/{id} returns 404 for clients not assigned to current therapist
3. PUT /api/clients/{id} returns 403/404 for clients not assigned to current therapist
4. POST /api/clients/{id}/reset-password returns 403 for clients not assigned to current therapist
5. POST /api/auth/register returns 403 (client self-registration disabled)
6. Super Admin GET /api/admin/clients still returns ALL clients
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_1_MOBILE = "1234567890"
THERAPIST_1_PASSWORD = "TestPass123"

SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "admin123"


class TestDataIsolation:
    """Test data isolation between therapists"""
    
    @pytest.fixture(scope="class")
    def therapist_1_token(self):
        """Get token for therapist 1"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_1_MOBILE,
            "password": THERAPIST_1_PASSWORD
        })
        assert response.status_code == 200, f"Therapist 1 login failed: {response.text}"
        data = response.json()
        return data["token"], data["user"]["id"]
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get token for super admin"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": SUPER_ADMIN_USERNAME,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_2_token(self, super_admin_token):
        """Create a second therapist and get their token"""
        # Create therapist 2 via admin
        import random
        unique_mobile = f"9876{random.randint(100000, 999999)}"
        unique_email = f"therapist2_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/therapists/create",
            json={
                "mobile": unique_mobile,
                "email": unique_email,
                "full_name": "Test Therapist 2",
                "password": "TestPass456",
                "credentials": "PhD Psychology"
            },
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        if response.status_code != 200:
            pytest.skip(f"Could not create therapist 2: {response.text}")
        
        # Login as therapist 2
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": unique_mobile,
            "password": "TestPass456"
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Could not login as therapist 2: {login_response.text}")
        
        data = login_response.json()
        return data["token"], data["user"]["id"], unique_mobile
    
    @pytest.fixture(scope="class")
    def therapist_1_client(self, therapist_1_token):
        """Create a client assigned to therapist 1"""
        token, therapist_id = therapist_1_token
        import random
        unique_mobile = f"5555{random.randint(100000, 999999)}"
        
        response = requests.post(
            f"{BASE_URL}/api/clients",
            json={
                "mobile": unique_mobile,
                "full_name": "TEST_Client_For_Therapist_1",
                "password": "ClientPass123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            pytest.skip(f"Could not create client for therapist 1: {response.text}")
        
        return response.json()["id"], unique_mobile
    
    # ============= TEST: Client Self-Registration Disabled =============
    
    def test_client_self_registration_disabled(self):
        """POST /api/auth/register should return 403"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "mobile": "9999999999",
            "password": "TestPass123",
            "full_name": "Self Register Client",
            "role": "client"
        })
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert "disabled" in data.get("detail", "").lower() or "contact" in data.get("detail", "").lower(), \
            f"Expected message about registration being disabled, got: {data}"
    
    # ============= TEST: GET /api/clients returns only assigned clients =============
    
    def test_get_clients_returns_only_assigned_clients(self, therapist_1_token, therapist_2_token, therapist_1_client):
        """Therapist 1 should only see their own clients, not therapist 2's clients"""
        token_1, therapist_1_id = therapist_1_token
        token_2, therapist_2_id, _ = therapist_2_token
        client_id, _ = therapist_1_client
        
        # Therapist 1 should see their client
        response_1 = requests.get(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {token_1}"}
        )
        assert response_1.status_code == 200
        clients_1 = response_1.json()
        client_ids_1 = [c["id"] for c in clients_1]
        assert client_id in client_ids_1, "Therapist 1 should see their own client"
        
        # Therapist 2 should NOT see therapist 1's client
        response_2 = requests.get(
            f"{BASE_URL}/api/clients",
            headers={"Authorization": f"Bearer {token_2}"}
        )
        assert response_2.status_code == 200
        clients_2 = response_2.json()
        client_ids_2 = [c["id"] for c in clients_2]
        assert client_id not in client_ids_2, "Therapist 2 should NOT see therapist 1's client"
    
    # ============= TEST: GET /api/clients/{id} returns 404 for unassigned client =============
    
    def test_get_client_by_id_returns_404_for_unassigned(self, therapist_2_token, therapist_1_client):
        """Therapist 2 should get 404 when trying to access therapist 1's client"""
        token_2, _, _ = therapist_2_token
        client_id, _ = therapist_1_client
        
        response = requests.get(
            f"{BASE_URL}/api/clients/{client_id}",
            headers={"Authorization": f"Bearer {token_2}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    
    def test_get_client_by_id_works_for_assigned(self, therapist_1_token, therapist_1_client):
        """Therapist 1 should be able to access their own client"""
        token_1, _ = therapist_1_token
        client_id, _ = therapist_1_client
        
        response = requests.get(
            f"{BASE_URL}/api/clients/{client_id}",
            headers={"Authorization": f"Bearer {token_1}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == client_id
    
    # ============= TEST: PUT /api/clients/{id} returns 403/404 for unassigned client =============
    
    def test_update_client_returns_404_for_unassigned(self, therapist_2_token, therapist_1_client):
        """Therapist 2 should get 404 when trying to update therapist 1's client"""
        token_2, _, _ = therapist_2_token
        client_id, _ = therapist_1_client
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{client_id}",
            json={"full_name": "Hacked Name"},
            headers={"Authorization": f"Bearer {token_2}"}
        )
        
        # Should be 404 (not found or not assigned) or 403 (forbidden)
        assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}: {response.text}"
    
    def test_update_client_works_for_assigned(self, therapist_1_token, therapist_1_client):
        """Therapist 1 should be able to update their own client"""
        token_1, _ = therapist_1_token
        client_id, _ = therapist_1_client
        
        new_name = f"Updated_Name_{uuid.uuid4().hex[:6]}"
        response = requests.put(
            f"{BASE_URL}/api/clients/{client_id}",
            json={"full_name": new_name},
            headers={"Authorization": f"Bearer {token_1}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["full_name"] == new_name
    
    # ============= TEST: POST /api/clients/{id}/reset-password returns 403 for unassigned =============
    
    def test_reset_password_returns_403_for_unassigned(self, therapist_2_token, therapist_1_client):
        """Therapist 2 should get 403 when trying to reset password for therapist 1's client"""
        token_2, _, _ = therapist_2_token
        client_id, _ = therapist_1_client
        
        response = requests.post(
            f"{BASE_URL}/api/clients/{client_id}/reset-password",
            json={"new_password": "HackedPassword123"},
            headers={"Authorization": f"Bearer {token_2}"}
        )
        
        # Should be 403 (forbidden) or 404 (not found)
        assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}: {response.text}"
    
    def test_reset_password_works_for_assigned(self, therapist_1_token, therapist_1_client):
        """Therapist 1 should be able to reset password for their own client"""
        token_1, _ = therapist_1_token
        client_id, _ = therapist_1_client
        
        response = requests.post(
            f"{BASE_URL}/api/clients/{client_id}/reset-password",
            json={"new_password": "NewPassword123"},
            headers={"Authorization": f"Bearer {token_1}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    # ============= TEST: Super Admin can see ALL clients =============
    
    def test_super_admin_sees_all_clients(self, super_admin_token, therapist_1_client):
        """Super Admin should see all clients via /api/admin/clients"""
        client_id, _ = therapist_1_client
        
        response = requests.get(
            f"{BASE_URL}/api/admin/clients",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        clients = response.json()
        client_ids = [c["id"] for c in clients]
        assert client_id in client_ids, "Super Admin should see all clients including therapist 1's client"
    
    def test_super_admin_can_access_any_client_detail(self, super_admin_token, therapist_1_client):
        """Super Admin should be able to access any client's details"""
        client_id, _ = therapist_1_client
        
        response = requests.get(
            f"{BASE_URL}/api/admin/clients/{client_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == client_id


class TestClientIsolationEdgeCases:
    """Edge case tests for data isolation"""
    
    @pytest.fixture(scope="class")
    def therapist_1_token(self):
        """Get token for therapist 1"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_1_MOBILE,
            "password": THERAPIST_1_PASSWORD
        })
        assert response.status_code == 200, f"Therapist 1 login failed: {response.text}"
        data = response.json()
        return data["token"], data["user"]["id"]
    
    def test_get_nonexistent_client_returns_404(self, therapist_1_token):
        """Accessing a non-existent client should return 404"""
        token, _ = therapist_1_token
        fake_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{BASE_URL}/api/clients/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_update_nonexistent_client_returns_404(self, therapist_1_token):
        """Updating a non-existent client should return 404"""
        token, _ = therapist_1_token
        fake_id = str(uuid.uuid4())
        
        response = requests.put(
            f"{BASE_URL}/api/clients/{fake_id}",
            json={"full_name": "Test"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_reset_password_nonexistent_client_returns_404(self, therapist_1_token):
        """Resetting password for non-existent client should return 404"""
        token, _ = therapist_1_token
        fake_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/clients/{fake_id}/reset-password",
            json={"new_password": "Test123"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be 403 or 404
        assert response.status_code in [403, 404]


class TestRegistrationDisabled:
    """Tests specifically for registration being disabled"""
    
    def test_register_endpoint_returns_403(self):
        """POST /api/auth/register should return 403 with helpful message"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "mobile": "1111111111",
            "password": "TestPass123",
            "full_name": "Test Client",
            "role": "client"
        })
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        detail = data.get("detail", "")
        # Should mention that registration is disabled and to contact therapist
        assert "disabled" in detail.lower() or "contact" in detail.lower() or "therapist" in detail.lower(), \
            f"Expected helpful message about contacting therapist, got: {detail}"
    
    def test_register_with_different_data_still_403(self):
        """Registration should be disabled regardless of data provided"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "mobile": "2222222222",
            "password": "AnotherPass123",
            "full_name": "Another Client",
            "role": "client",
            "email": "test@example.com"
        })
        
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
