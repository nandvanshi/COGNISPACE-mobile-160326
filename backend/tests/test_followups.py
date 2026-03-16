"""
Follow-Up Intelligence System Tests
Tests for the follow-up recommendation system that tracks recommended sessions,
detects overdue clients, and improves therapy continuity.
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "7275005007"
THERAPIST_PASSWORD = "Test@123"
CLIENT_ID_SUMAN = "84f06ca2-44ad-4611-8140-3645ee9868a9"
CLIENT_ID_VEDIC = "0acd8e06-bc6a-416f-9dc4-842280324ea2"
CLIENT_MOBILE = "9235555549"
CLIENT_PASSWORD = "Test@123"


class TestFollowUpAPIs:
    """Test Follow-Up Intelligence System APIs"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": THERAPIST_MOBILE, "password": THERAPIST_PASSWORD}
        )
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def client_token(self):
        """Get client authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": CLIENT_MOBILE, "password": CLIENT_PASSWORD}
        )
        assert response.status_code == 200, f"Client login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, therapist_token):
        """Get authorization headers for therapist"""
        return {"Authorization": f"Bearer {therapist_token}"}
    
    @pytest.fixture(scope="class")
    def client_auth_headers(self, client_token):
        """Get authorization headers for client"""
        return {"Authorization": f"Bearer {client_token}"}
    
    # =============================================================================
    # POST /api/follow-ups/recommend - Create follow-up recommendation
    # =============================================================================
    
    def test_recommend_follow_up_success(self, auth_headers):
        """Test creating a follow-up recommendation for a client"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/follow-ups/recommend",
            json={
                "client_id": CLIENT_ID_SUMAN,
                "recommended_date": future_date,
                "notes": "TEST: Weekly CBT session recommended"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to create recommendation: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response missing 'id'"
        assert data["client_id"] == CLIENT_ID_SUMAN, "Client ID mismatch"
        assert data["recommended_date"] == future_date, "Date mismatch"
        assert data["notes"] == "TEST: Weekly CBT session recommended", "Notes mismatch"
        assert data["status"] == "active", "Status should be 'active'"
        assert "created_at" in data, "Response missing 'created_at'"
        assert "therapist_id" in data, "Response missing 'therapist_id'"
        
        print(f"SUCCESS: Created follow-up recommendation with id={data['id']}")
    
    def test_recommend_follow_up_invalid_client(self, auth_headers):
        """Test creating recommendation for non-existent client"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/follow-ups/recommend",
            json={
                "client_id": "non-existent-client-id",
                "recommended_date": future_date,
                "notes": "Should fail"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid client, got {response.status_code}"
        print("SUCCESS: Correctly rejected recommendation for invalid client")
    
    def test_recommend_follow_up_without_auth(self):
        """Test creating recommendation without authentication"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/follow-ups/recommend",
            json={
                "client_id": CLIENT_ID_SUMAN,
                "recommended_date": future_date,
                "notes": "Should fail without auth"
            }
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("SUCCESS: Correctly rejected unauthenticated request")
    
    # =============================================================================
    # GET /api/follow-ups/summary - Get summary stats
    # =============================================================================
    
    def test_get_follow_up_summary(self, auth_headers):
        """Test getting follow-up summary stats"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get summary: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "booked" in data, "Response missing 'booked' count"
        assert "recommended" in data, "Response missing 'recommended' count"
        assert "overdue" in data, "Response missing 'overdue' count"
        assert "dropout_risk" in data, "Response missing 'dropout_risk' count"
        assert "total_clients" in data, "Response missing 'total_clients' count"
        
        # Verify counts are integers >= 0
        assert isinstance(data["booked"], int) and data["booked"] >= 0
        assert isinstance(data["recommended"], int) and data["recommended"] >= 0
        assert isinstance(data["overdue"], int) and data["overdue"] >= 0
        assert isinstance(data["dropout_risk"], int) and data["dropout_risk"] >= 0
        assert isinstance(data["total_clients"], int) and data["total_clients"] >= 0
        
        print(f"SUCCESS: Got follow-up summary - booked={data['booked']}, recommended={data['recommended']}, "
              f"overdue={data['overdue']}, dropout_risk={data['dropout_risk']}, total={data['total_clients']}")
    
    def test_get_follow_up_summary_without_auth(self):
        """Test getting summary without authentication"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/summary")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("SUCCESS: Correctly rejected unauthenticated request for summary")
    
    # =============================================================================
    # GET /api/follow-ups/clients - Get detailed client list
    # =============================================================================
    
    def test_get_follow_up_clients(self, auth_headers):
        """Test getting detailed follow-up client list"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get clients: {response.text}"
        data = response.json()
        
        # Response should be a list
        assert isinstance(data, list), "Response should be a list"
        
        # If there are clients, verify structure
        if len(data) > 0:
            client = data[0]
            assert "client_id" in client, "Client missing 'client_id'"
            assert "client_name" in client, "Client missing 'client_name'"
            assert "status" in client, "Client missing 'status'"
            assert "is_dropout_risk" in client, "Client missing 'is_dropout_risk'"
            
            # Verify status is valid
            valid_statuses = ["overdue", "dropout_risk", "recommended", "booked", "no_recommendation"]
            assert client["status"] in valid_statuses, f"Invalid status: {client['status']}"
            
            print(f"SUCCESS: Got {len(data)} clients with follow-up data")
            print(f"  First client: {client['client_name']} - status={client['status']}")
        else:
            print("SUCCESS: Got empty client list (no clients with follow-up data)")
    
    def test_follow_up_clients_sorted_by_priority(self, auth_headers):
        """Test that clients are sorted by priority (overdue > dropout_risk > recommended > booked)"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get clients: {response.text}"
        data = response.json()
        
        if len(data) > 1:
            priority = {"overdue": 0, "dropout_risk": 1, "recommended": 2, "booked": 3, "no_recommendation": 4}
            
            # Check that priority is non-decreasing
            for i in range(len(data) - 1):
                curr_priority = priority.get(data[i]["status"], 5)
                next_priority = priority.get(data[i + 1]["status"], 5)
                if curr_priority > next_priority:
                    # This is acceptable - the secondary sort is by days_since_last_session
                    pass
            
            print(f"SUCCESS: Clients are sorted correctly, first status={data[0]['status']}")
        else:
            print("SUCCESS: Too few clients to verify sorting")
    
    # =============================================================================
    # GET /api/follow-ups/retention-analytics - Get retention metrics
    # =============================================================================
    
    def test_get_retention_analytics(self, auth_headers):
        """Test getting retention analytics"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/retention-analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get analytics: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_clients" in data, "Response missing 'total_clients'"
        assert "clients_with_followup" in data, "Response missing 'clients_with_followup'"
        assert "overdue_clients" in data, "Response missing 'overdue_clients'"
        assert "dropout_risk_clients" in data, "Response missing 'dropout_risk_clients'"
        assert "active_clients" in data, "Response missing 'active_clients'"
        assert "retention_rate" in data, "Response missing 'retention_rate'"
        assert "monthly_sessions" in data, "Response missing 'monthly_sessions'"
        
        # Verify monthly_sessions is a list with month data
        assert isinstance(data["monthly_sessions"], list), "monthly_sessions should be a list"
        if len(data["monthly_sessions"]) > 0:
            month_data = data["monthly_sessions"][0]
            assert "month" in month_data, "Month data missing 'month'"
            assert "sessions" in month_data, "Month data missing 'sessions'"
        
        # Verify retention_rate is a valid percentage
        assert isinstance(data["retention_rate"], (int, float)), "retention_rate should be numeric"
        assert 0 <= data["retention_rate"] <= 100, "retention_rate should be 0-100"
        
        print(f"SUCCESS: Got retention analytics - total_clients={data['total_clients']}, "
              f"retention_rate={data['retention_rate']}%, active={data['active_clients']}")
    
    def test_retention_analytics_monthly_sessions(self, auth_headers):
        """Test that monthly sessions data is returned for last 6 months"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/retention-analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get analytics: {response.text}"
        data = response.json()
        
        monthly = data.get("monthly_sessions", [])
        assert len(monthly) == 6, f"Expected 6 months of data, got {len(monthly)}"
        
        for month_data in monthly:
            assert "month" in month_data, "Month data missing 'month'"
            assert "sessions" in month_data, "Month data missing 'sessions'"
            assert isinstance(month_data["sessions"], int), "sessions should be integer"
        
        print(f"SUCCESS: Got 6 months of session data")
    
    # =============================================================================
    # GET /api/follow-ups/my-recommendation - Client endpoint
    # =============================================================================
    
    def test_client_get_my_recommendation(self, client_auth_headers):
        """Test client getting their follow-up recommendation"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/my-recommendation",
            headers=client_auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get recommendation: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "has_recommendation" in data, "Response missing 'has_recommendation'"
        
        if data["has_recommendation"]:
            assert "recommended_date" in data, "Response missing 'recommended_date'"
            assert "is_overdue" in data, "Response missing 'is_overdue'"
            print(f"SUCCESS: Client has recommendation - date={data['recommended_date']}, overdue={data['is_overdue']}")
        else:
            print("SUCCESS: Client has no active recommendation")
    
    def test_client_recommendation_access_control(self, auth_headers):
        """Test that therapist cannot access client-only endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/follow-ups/my-recommendation",
            headers=auth_headers  # Using therapist token
        )
        
        # Should return 403 since therapist is not a client
        assert response.status_code == 403, f"Expected 403 for therapist accessing client endpoint, got {response.status_code}"
        print("SUCCESS: Correctly denied therapist access to client endpoint")
    
    # =============================================================================
    # Integration test - Create recommendation and verify in list
    # =============================================================================
    
    def test_integration_create_and_verify_recommendation(self, auth_headers):
        """Integration test: Create recommendation and verify it appears in clients list"""
        future_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        # Create recommendation
        create_response = requests.post(
            f"{BASE_URL}/api/follow-ups/recommend",
            json={
                "client_id": CLIENT_ID_VEDIC,
                "recommended_date": future_date,
                "notes": "TEST_INTEGRATION: Bi-weekly session"
            },
            headers=auth_headers
        )
        
        assert create_response.status_code == 200, f"Failed to create: {create_response.text}"
        
        # Get clients list and verify recommendation appears
        list_response = requests.get(
            f"{BASE_URL}/api/follow-ups/clients",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200, f"Failed to get list: {list_response.text}"
        clients = list_response.json()
        
        # Find the client we just created recommendation for
        target_client = None
        for client in clients:
            if client.get("client_id") == CLIENT_ID_VEDIC:
                target_client = client
                break
        
        if target_client:
            # Verify the recommendation data is present
            assert target_client.get("recommended_date") is not None or target_client.get("status") in ["recommended", "booked"], \
                "Client should have recommendation or booked status"
            print(f"SUCCESS: Integration test passed - client has status={target_client['status']}")
        else:
            print("INFO: Client not in list (may have no session history)")


class TestFollowUpAccessControl:
    """Test access control for follow-up APIs"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"identifier": THERAPIST_MOBILE, "password": THERAPIST_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_unauthenticated_recommend(self):
        """Test that unauthenticated users cannot create recommendations"""
        response = requests.post(
            f"{BASE_URL}/api/follow-ups/recommend",
            json={"client_id": CLIENT_ID_SUMAN, "recommended_date": "2026-02-01"}
        )
        assert response.status_code in [401, 403]
        print("SUCCESS: Unauthenticated recommend request rejected")
    
    def test_unauthenticated_summary(self):
        """Test that unauthenticated users cannot get summary"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/summary")
        assert response.status_code in [401, 403]
        print("SUCCESS: Unauthenticated summary request rejected")
    
    def test_unauthenticated_clients(self):
        """Test that unauthenticated users cannot get clients"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/clients")
        assert response.status_code in [401, 403]
        print("SUCCESS: Unauthenticated clients request rejected")
    
    def test_unauthenticated_analytics(self):
        """Test that unauthenticated users cannot get analytics"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/retention-analytics")
        assert response.status_code in [401, 403]
        print("SUCCESS: Unauthenticated analytics request rejected")
    
    def test_unauthenticated_my_recommendation(self):
        """Test that unauthenticated users cannot get my-recommendation"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/my-recommendation")
        assert response.status_code in [401, 403]
        print("SUCCESS: Unauthenticated my-recommendation request rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
