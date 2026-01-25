"""
Test Consent P0 Bug Fix - Verify consent template has 12 sections
and client dashboard works after therapist completes case history
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CLIENT_MOBILE = "8299683186"
CLIENT_PASSWORD = "Abcd@1234"
CLIENT_ID = "e07cfd87-c778-4e19-9c28-1e9ae3feba96"
THERAPIST_NAME = "Dr. Kavita Dhingra"


class TestConsentP0Fix:
    """Test consent functionality after P0 bug fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_client_token(self):
        """Login as client and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": CLIENT_MOBILE,
            "password": CLIENT_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_client_login(self):
        """Test client can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": CLIENT_MOBILE,
            "password": CLIENT_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "client"
        assert data["user"]["full_name"] == "Divya Sharma "
        print(f"✓ Client login successful: {data['user']['full_name']}")
    
    def test_consent_check_endpoint(self):
        """Test GET /api/therapy-consent/check/{client_id}"""
        token = self.get_client_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/check/{CLIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        
        assert "exists" in data
        assert "is_signed" in data
        assert data["exists"] == True, "Consent should exist"
        print(f"✓ Consent check: exists={data['exists']}, is_signed={data['is_signed']}")
    
    def test_consent_has_12_sections(self):
        """Test consent template has all 12 sections"""
        token = self.get_client_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/{CLIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        
        consent_text = data.get("consent_text", "")
        assert consent_text, "Consent text should not be empty"
        
        # Extract section headers (numbered sections like "1. Services Offered")
        sections = re.findall(r'^\d+\.\s+(.+)$', consent_text, re.MULTILINE)
        
        expected_sections = [
            "Services Offered",
            "Purpose of Therapy",
            "Nature of Therapy",
            "Role of the Therapist",
            "Confidentiality",
            "Records & Documentation",
            "Fees & Payments",
            "Appointments & Attendance",
            "Use of Digital Systems",
            "Client Responsibilities",
            "Right to Withdraw",
            "Consent Statement"
        ]
        
        assert len(sections) == 12, f"Expected 12 sections, found {len(sections)}: {sections}"
        
        for expected in expected_sections:
            assert expected in sections, f"Missing section: {expected}"
        
        print(f"✓ All 12 consent sections present: {sections}")
    
    def test_therapist_name_in_consent(self):
        """Test therapist name appears in consent"""
        token = self.get_client_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/{CLIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # Check therapist_name field
        assert data.get("therapist_name") == THERAPIST_NAME, \
            f"Expected therapist_name '{THERAPIST_NAME}', got '{data.get('therapist_name')}'"
        
        # Check therapist name in consent text
        consent_text = data.get("consent_text", "")
        assert THERAPIST_NAME in consent_text, \
            f"Therapist name '{THERAPIST_NAME}' not found in consent text"
        
        print(f"✓ Therapist name '{THERAPIST_NAME}' present in consent")
    
    def test_services_offered_section_content(self):
        """Test Services Offered section has therapist credentials"""
        token = self.get_client_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/{CLIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        
        consent_text = data.get("consent_text", "")
        
        # Check for therapist credentials in Services Offered section
        assert "PhD" in consent_text or "Masters" in consent_text, \
            "Therapist qualifications should be in consent"
        assert "psychological assessment" in consent_text.lower(), \
            "Services description should mention psychological assessment"
        
        print("✓ Services Offered section has therapist credentials")
    
    def test_consent_sign_endpoint(self):
        """Test POST /api/therapy-consent/{client_id}/sign"""
        token = self.get_client_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # First check current status
        check_response = self.session.get(f"{BASE_URL}/api/therapy-consent/check/{CLIENT_ID}")
        initial_status = check_response.json()
        
        # Sign consent
        response = self.session.post(
            f"{BASE_URL}/api/therapy-consent/{CLIENT_ID}/sign?signature_method=digital"
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("message") == "Consent signed successfully"
        
        # Verify consent is now signed
        verify_response = self.session.get(f"{BASE_URL}/api/therapy-consent/check/{CLIENT_ID}")
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["is_signed"] == True
        
        print(f"✓ Consent signed successfully (was: {initial_status['is_signed']}, now: True)")
    
    def test_dashboard_data_after_consent(self):
        """Test client can access dashboard data after consent is signed"""
        token = self.get_client_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test appointments endpoint
        appts_response = self.session.get(f"{BASE_URL}/api/appointments")
        assert appts_response.status_code == 200
        print(f"✓ Appointments endpoint accessible: {len(appts_response.json())} appointments")
        
        # Test homework endpoint
        hw_response = self.session.get(f"{BASE_URL}/api/homework")
        assert hw_response.status_code == 200
        print(f"✓ Homework endpoint accessible: {len(hw_response.json())} homework items")
        
        # Test assessments endpoint
        assess_response = self.session.get(f"{BASE_URL}/api/assessments")
        assert assess_response.status_code == 200
        print(f"✓ Assessments endpoint accessible: {len(assess_response.json())} assessments")
        
        # Test payments endpoint
        payments_response = self.session.get(f"{BASE_URL}/api/payments")
        assert payments_response.status_code == 200
        print(f"✓ Payments endpoint accessible: {len(payments_response.json())} payments")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
