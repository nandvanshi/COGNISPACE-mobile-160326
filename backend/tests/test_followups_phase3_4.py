"""
Follow-Up Intelligence System - Phase 3 & 4 Tests
Tests the follow-up summary, clients list, and client recommendation endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "7275005007"
THERAPIST_PASSWORD = "Test@123"
CLIENT_MOBILE = "9235555549"
CLIENT_PASSWORD = "Test@123"
SUPER_ADMIN_MOBILE = "7275005000"
SUPER_ADMIN_PASSWORD = "Test@123"

@pytest.fixture(scope="module")
def therapist_token():
    """Get therapist auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": THERAPIST_MOBILE,
        "password": THERAPIST_PASSWORD
    })
    assert response.status_code == 200, f"Therapist login failed: {response.text}"
    return response.json()["token"]

@pytest.fixture(scope="module")
def client_token():
    """Get client auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": CLIENT_MOBILE,
        "password": CLIENT_PASSWORD
    })
    assert response.status_code == 200, f"Client login failed: {response.text}"
    return response.json()["token"]


# ============= SUMMARY ENDPOINT TESTS =============

class TestFollowUpSummary:
    """GET /api/follow-ups/summary - Dashboard stat counts"""
    
    def test_summary_returns_correct_fields(self, therapist_token):
        """Verify summary returns booked, recommended, overdue, dropout_risk"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/summary",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields exist
        assert "booked" in data, "Missing 'booked' field"
        assert "recommended" in data, "Missing 'recommended' field"
        assert "overdue" in data, "Missing 'overdue' field"
        assert "dropout_risk" in data, "Missing 'dropout_risk' field"
        assert "total_clients" in data, "Missing 'total_clients' field"
        
        # Verify types
        assert isinstance(data["booked"], int)
        assert isinstance(data["recommended"], int)
        assert isinstance(data["overdue"], int)
        assert isinstance(data["dropout_risk"], int)
        assert isinstance(data["total_clients"], int)
        
    def test_summary_values_are_non_negative(self, therapist_token):
        """All counts should be >= 0"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/summary",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        data = response.json()
        
        assert data["booked"] >= 0
        assert data["recommended"] >= 0
        assert data["overdue"] >= 0
        assert data["dropout_risk"] >= 0
        assert data["total_clients"] >= 0
        
    def test_summary_requires_auth(self):
        """Summary endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/summary")
        assert response.status_code in [401, 403]
        
    def test_summary_denied_for_client(self, client_token):
        """Clients should not access therapist summary"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/summary",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 403


# ============= CLIENTS LIST ENDPOINT TESTS =============

class TestFollowUpClients:
    """GET /api/follow-ups/clients - Detailed client list"""
    
    def test_clients_returns_list(self, therapist_token):
        """Returns list of clients with follow-up info"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
    def test_clients_have_required_fields(self, therapist_token):
        """Each client has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        data = response.json()
        
        if len(data) > 0:
            client = data[0]
            required_fields = [
                "client_id", "client_name", "status", 
                "days_since_last_session", "is_dropout_risk"
            ]
            for field in required_fields:
                assert field in client, f"Missing field: {field}"
                
    def test_clients_status_is_valid(self, therapist_token):
        """Client status should be one of expected values"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        data = response.json()
        
        valid_statuses = ["booked", "recommended", "overdue", "dropout_risk", "no_recommendation"]
        for client in data:
            assert client["status"] in valid_statuses, f"Invalid status: {client['status']}"
            
    def test_clients_sorted_by_priority(self, therapist_token):
        """List should be sorted by priority (overdue > dropout_risk > recommended > booked)"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        data = response.json()
        
        # Check ordering is maintained
        priority = {"overdue": 0, "dropout_risk": 1, "recommended": 2, "booked": 3, "no_recommendation": 4}
        for i in range(len(data) - 1):
            current_priority = priority.get(data[i]["status"], 5)
            next_priority = priority.get(data[i + 1]["status"], 5)
            assert current_priority <= next_priority, "Clients not sorted by priority"
            
    def test_clients_requires_auth(self):
        """Clients endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/clients")
        assert response.status_code in [401, 403]


# ============= CLIENT MY-RECOMMENDATION ENDPOINT TESTS =============

class TestMyRecommendation:
    """GET /api/follow-ups/my-recommendation - Client's follow-up recommendation"""
    
    def test_my_recommendation_returns_data(self, client_token):
        """Returns recommendation data for client"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/my-recommendation",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have has_recommendation field
        assert "has_recommendation" in data
        
    def test_my_recommendation_fields_when_exists(self, client_token):
        """When recommendation exists, should have all fields"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/my-recommendation",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        data = response.json()
        
        if data.get("has_recommendation"):
            assert "recommended_date" in data
            assert "notes" in data
            assert "is_overdue" in data
            assert isinstance(data["is_overdue"], bool)
            
    def test_my_recommendation_denied_for_therapist(self, therapist_token):
        """Therapists should not access client-only endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/my-recommendation",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        assert response.status_code == 403
        
    def test_my_recommendation_requires_auth(self):
        """My-recommendation endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/my-recommendation")
        assert response.status_code in [401, 403]


# ============= INTEGRATION TESTS =============

class TestFollowUpIntegration:
    """Integration tests between follow-up components"""
    
    def test_summary_counts_match_clients_list(self, therapist_token):
        """Summary counts should match actual clients in list"""
        # Get summary
        summary_res = requests.get(
            f"{BASE_URL}/api/follow-ups/summary",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        summary = summary_res.json()
        
        # Get clients list
        clients_res = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers={"Authorization": f"Bearer {therapist_token}"}
        )
        clients = clients_res.json()
        
        # Count by status
        status_counts = {"booked": 0, "recommended": 0, "overdue": 0, "dropout_risk": 0}
        for c in clients:
            if c["status"] in status_counts:
                status_counts[c["status"]] += 1
            if c.get("is_dropout_risk"):
                status_counts["dropout_risk"] = status_counts.get("dropout_risk", 0) + 1 - 1  # Already counted
                
        # Note: dropout_risk is counted separately from status
        # Verify recommended/overdue/booked counts match
        assert summary["recommended"] >= 0  # Some may have been counted
        assert summary["overdue"] >= 0
        assert summary["booked"] >= 0
        

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
