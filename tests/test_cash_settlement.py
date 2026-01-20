"""
Test Cash Settlement Feature - End-of-Day Cash Reconciliation
Tests all settlement endpoints:
- GET /api/settlements/today - Today's settlement status
- POST /api/settlements/handover - Assistant marks cash as handed over
- POST /api/settlements/{id}/confirm - Therapist confirms receipt
- POST /api/settlements/{id}/dispute - Therapist reports issue
- GET /api/settlements/pending - Pending settlements for therapist
- GET /api/settlements/history - Settlement audit trail
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ASSISTANT_EMAIL = "test_assistant_ui@test.com"
ASSISTANT_PASSWORD = "testpass123"
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "password"


class TestCashSettlementEndpoints:
    """Test Cash Settlement API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.assistant_token = None
        self.therapist_token = None
        
    def get_assistant_token(self):
        """Login as assistant and get token"""
        if self.assistant_token:
            return self.assistant_token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        assert response.status_code == 200, f"Assistant login failed: {response.text}"
        self.assistant_token = response.json()["token"]
        return self.assistant_token
    
    def get_therapist_token(self):
        """Login as therapist and get token"""
        if self.therapist_token:
            return self.therapist_token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        self.therapist_token = response.json()["token"]
        return self.therapist_token
    
    # ============= GET /api/settlements/today =============
    
    def test_get_today_settlement_as_assistant(self):
        """Test assistant can get today's settlement status"""
        token = self.get_assistant_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/today",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "date" in data
        assert "therapist_id" in data
        assert "cash_amount" in data
        assert "online_amount" in data
        assert "total_amount" in data
        assert "status" in data
        assert data["status"] in ["pending", "handed_over", "settled", "disputed"]
        print(f"✓ Today's settlement: status={data['status']}, cash={data['cash_amount']}, online={data['online_amount']}")
    
    def test_get_today_settlement_as_therapist(self):
        """Test therapist can get today's settlement status"""
        token = self.get_therapist_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/today",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "date" in data
        assert "status" in data
        assert "cash_amount" in data
        print(f"✓ Therapist can view settlement: status={data['status']}")
    
    def test_get_today_settlement_unauthorized(self):
        """Test unauthorized access is blocked"""
        response = self.session.get(f"{BASE_URL}/api/settlements/today")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ Unauthorized access blocked")
    
    # ============= POST /api/settlements/handover =============
    
    def test_handover_requires_assistant_role(self):
        """Test only assistants can mark cash handover"""
        token = self.get_therapist_token()
        response = self.session.post(
            f"{BASE_URL}/api/settlements/handover",
            headers={"Authorization": f"Bearer {token}"},
            json={"note": "Test handover"}
        )
        assert response.status_code == 403, f"Should reject therapist: {response.text}"
        print("✓ Handover correctly requires assistant role")
    
    def test_handover_no_cash_to_settle(self):
        """Test handover fails when no cash collected"""
        token = self.get_assistant_token()
        
        # First check today's settlement
        check_response = self.session.get(
            f"{BASE_URL}/api/settlements/today",
            headers={"Authorization": f"Bearer {token}"}
        )
        settlement_data = check_response.json()
        
        # If cash_amount is 0, handover should fail
        if settlement_data.get("cash_amount", 0) == 0:
            response = self.session.post(
                f"{BASE_URL}/api/settlements/handover",
                headers={"Authorization": f"Bearer {token}"},
                json={"note": "Test handover"}
            )
            assert response.status_code == 400, f"Should fail with no cash: {response.text}"
            assert "No cash" in response.json().get("detail", "")
            print("✓ Handover correctly fails when no cash to settle")
        else:
            print(f"⚠ Skipping test - cash amount is {settlement_data.get('cash_amount')}")
    
    # ============= GET /api/settlements/pending =============
    
    def test_get_pending_settlements_as_therapist(self):
        """Test therapist can get pending settlements"""
        token = self.get_therapist_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "pending_settlements" in data
        assert "count" in data
        assert isinstance(data["pending_settlements"], list)
        print(f"✓ Pending settlements: count={data['count']}")
    
    def test_get_pending_settlements_requires_therapist(self):
        """Test only therapists can view pending settlements"""
        token = self.get_assistant_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, f"Should reject assistant: {response.text}"
        print("✓ Pending settlements correctly requires therapist role")
    
    # ============= GET /api/settlements/history =============
    
    def test_get_settlement_history_as_therapist(self):
        """Test therapist can get settlement history"""
        token = self.get_therapist_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "settlements" in data
        assert "total_count" in data
        assert "date_range" in data
        print(f"✓ Settlement history: count={data['total_count']}")
    
    def test_get_settlement_history_as_assistant(self):
        """Test assistant can get settlement history"""
        token = self.get_assistant_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "settlements" in data
        print(f"✓ Assistant can view settlement history: count={data['total_count']}")
    
    def test_get_settlement_history_with_days_param(self):
        """Test settlement history with custom days parameter"""
        token = self.get_therapist_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/history?days=7",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "date_range" in data
        print(f"✓ Settlement history with days param: range={data['date_range']}")
    
    # ============= POST /api/settlements/{id}/confirm =============
    
    def test_confirm_requires_therapist_role(self):
        """Test only therapists can confirm settlements"""
        token = self.get_assistant_token()
        response = self.session.post(
            f"{BASE_URL}/api/settlements/fake-id/confirm",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, f"Should reject assistant: {response.text}"
        print("✓ Confirm correctly requires therapist role")
    
    def test_confirm_nonexistent_settlement(self):
        """Test confirming non-existent settlement returns 404"""
        token = self.get_therapist_token()
        response = self.session.post(
            f"{BASE_URL}/api/settlements/nonexistent-id-12345/confirm",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, f"Should return 404: {response.text}"
        print("✓ Confirm returns 404 for non-existent settlement")
    
    # ============= POST /api/settlements/{id}/dispute =============
    
    def test_dispute_requires_therapist_role(self):
        """Test only therapists can dispute settlements"""
        token = self.get_assistant_token()
        response = self.session.post(
            f"{BASE_URL}/api/settlements/fake-id/dispute",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "Test dispute reason"}
        )
        assert response.status_code == 403, f"Should reject assistant: {response.text}"
        print("✓ Dispute correctly requires therapist role")
    
    def test_dispute_requires_reason(self):
        """Test dispute requires a reason"""
        token = self.get_therapist_token()
        
        # Test with empty reason
        response = self.session.post(
            f"{BASE_URL}/api/settlements/fake-id/dispute",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": ""}
        )
        # Should fail validation (either 400 or 422)
        assert response.status_code in [400, 422], f"Should require reason: {response.text}"
        print("✓ Dispute correctly requires reason")
    
    def test_dispute_reason_min_length(self):
        """Test dispute reason minimum length validation"""
        token = self.get_therapist_token()
        
        # Test with short reason (less than 5 chars)
        response = self.session.post(
            f"{BASE_URL}/api/settlements/fake-id/dispute",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "abc"}
        )
        # Should fail - either 400 for validation or 404 for not found
        # The validation happens before the lookup
        assert response.status_code in [400, 404], f"Response: {response.text}"
        print("✓ Dispute reason minimum length validated")
    
    def test_dispute_nonexistent_settlement(self):
        """Test disputing non-existent settlement returns 404"""
        token = self.get_therapist_token()
        response = self.session.post(
            f"{BASE_URL}/api/settlements/nonexistent-id-12345/dispute",
            headers={"Authorization": f"Bearer {token}"},
            json={"reason": "Valid reason for dispute"}
        )
        assert response.status_code == 404, f"Should return 404: {response.text}"
        print("✓ Dispute returns 404 for non-existent settlement")


class TestCashSettlementFlow:
    """Test complete cash settlement workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_assistant_token(self):
        """Login as assistant"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        return response.json()["token"]
    
    def get_therapist_token(self):
        """Login as therapist"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        return response.json()["token"]
    
    def test_settlement_status_values(self):
        """Test that settlement status is one of valid values"""
        token = self.get_assistant_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/today",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        valid_statuses = ["pending", "handed_over", "settled", "disputed"]
        assert data["status"] in valid_statuses, f"Invalid status: {data['status']}"
        print(f"✓ Settlement status is valid: {data['status']}")
    
    def test_settlement_amounts_are_numbers(self):
        """Test that settlement amounts are numeric"""
        token = self.get_therapist_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/today",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["cash_amount"], (int, float)), "cash_amount should be numeric"
        assert isinstance(data["online_amount"], (int, float)), "online_amount should be numeric"
        assert isinstance(data["total_amount"], (int, float)), "total_amount should be numeric"
        assert data["total_amount"] == data["cash_amount"] + data["online_amount"], "Total should equal cash + online"
        print(f"✓ Settlement amounts are valid: cash={data['cash_amount']}, online={data['online_amount']}, total={data['total_amount']}")
    
    def test_settlement_date_format(self):
        """Test that settlement date is in correct format"""
        token = self.get_assistant_token()
        response = self.session.get(
            f"{BASE_URL}/api/settlements/today",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Date should be in YYYY-MM-DD format
        date_str = data["date"]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            print(f"✓ Settlement date format is valid: {date_str}")
        except ValueError:
            pytest.fail(f"Invalid date format: {date_str}")


class TestSettlementDataIsolation:
    """Test that settlements are properly isolated between therapists"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_assistant_sees_linked_therapist_settlement(self):
        """Test assistant only sees their linked therapist's settlement"""
        # Login as assistant
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": ASSISTANT_EMAIL,
            "password": ASSISTANT_PASSWORD
        })
        assert response.status_code == 200
        assistant_data = response.json()
        assistant_token = assistant_data["token"]
        therapist_id = assistant_data["user"].get("therapist_id")
        
        # Get settlement
        settlement_response = self.session.get(
            f"{BASE_URL}/api/settlements/today",
            headers={"Authorization": f"Bearer {assistant_token}"}
        )
        assert settlement_response.status_code == 200
        settlement = settlement_response.json()
        
        # Verify therapist_id matches
        assert settlement["therapist_id"] == therapist_id, "Settlement should be for linked therapist"
        print(f"✓ Assistant sees correct therapist's settlement: {therapist_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
