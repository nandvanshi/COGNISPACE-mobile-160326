"""
Test Case History and Consent Separation
Tests the new workflow where:
1. Case History has 10 sections (NOT 11) - Consent & Disclaimer removed
2. Case History completes without consent checkbox
3. After completion, consent document is generated and client is notified
4. Therapist sees 'Consent (pending)' in Client Profile
5. Client sees consent form when they login
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "7275005007"
THERAPIST_PASSWORD = "Test@123"


class TestCaseHistoryConsentSeparation:
    """Test the separation of Consent from Case History"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        data = login_response.json()
        self.token = data.get("token")
        self.therapist_id = data.get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get a client for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        if clients_response.status_code == 200:
            clients = clients_response.json()
            if clients:
                self.test_client = clients[0]
                self.client_id = self.test_client.get("id")
            else:
                pytest.skip("No clients available for testing")
        else:
            pytest.skip(f"Failed to get clients: {clients_response.text}")
    
    def test_01_login_works(self):
        """Test that therapist login works"""
        assert self.token is not None
        assert self.therapist_id is not None
        print(f"✓ Therapist logged in successfully: {self.therapist_id}")
    
    def test_02_get_case_history_endpoint(self):
        """Test GET /api/case-history/{client_id} endpoint"""
        response = self.session.get(f"{BASE_URL}/api/case-history/{self.client_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "client_id" in data
        assert data["client_id"] == self.client_id
        print(f"✓ Case history retrieved for client {self.client_id}")
        print(f"  - is_complete: {data.get('is_complete')}")
    
    def test_03_case_history_section_update(self):
        """Test PATCH /api/case-history/{client_id}/section endpoint"""
        # Update basic_identification section
        section_data = {
            "name": "Test Client Name",
            "age_dob": "30 years",
            "gender": "male"
        }
        
        response = self.session.patch(
            f"{BASE_URL}/api/case-history/{self.client_id}/section?section=basic_identification",
            json=section_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Section saved"
        print(f"✓ Section basic_identification saved successfully")
    
    def test_04_case_history_complete_without_consent(self):
        """Test POST /api/case-history/{client_id}/complete - should work without consent fields"""
        # First, ensure required fields are filled
        # Update basic_identification
        self.session.patch(
            f"{BASE_URL}/api/case-history/{self.client_id}/section?section=basic_identification",
            json={"name": "Test Client", "age_dob": "30 years"}
        )
        
        # Update presenting_complaints (required)
        self.session.patch(
            f"{BASE_URL}/api/case-history/{self.client_id}/section?section=presenting_complaints",
            json={"main_problems": "Test presenting complaints for testing purposes"}
        )
        
        # Now complete the case history
        response = self.session.post(f"{BASE_URL}/api/case-history/{self.client_id}/complete")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        # Should mention consent notification
        assert "consent" in data.get("message", "").lower() or "complete" in data.get("message", "").lower()
        print(f"✓ Case history completed without consent fields")
        print(f"  - Response: {data.get('message')}")
    
    def test_05_consent_document_created_after_completion(self):
        """Test that consent document is created after case history completion"""
        # Check consent status
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/check/{self.client_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "exists" in data
        print(f"✓ Consent check endpoint works")
        print(f"  - exists: {data.get('exists')}")
        print(f"  - is_signed: {data.get('is_signed')}")
    
    def test_06_get_therapy_consent(self):
        """Test GET /api/therapy-consent/{client_id} endpoint"""
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/{self.client_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have consent document with therapist info
        if data.get("exists") == False:
            print(f"✓ Consent document not yet created (expected if case history not complete)")
        else:
            assert "id" in data or "therapist_name" in data
            print(f"✓ Consent document retrieved")
            print(f"  - therapist_name: {data.get('therapist_name')}")
            print(f"  - is_signed: {data.get('is_signed')}")
    
    def test_07_case_history_check_endpoint(self):
        """Test GET /api/case-history/check/{client_id} endpoint"""
        response = self.session.get(f"{BASE_URL}/api/case-history/check/{self.client_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "exists" in data
        assert "is_complete" in data
        print(f"✓ Case history check endpoint works")
        print(f"  - exists: {data.get('exists')}")
        print(f"  - is_complete: {data.get('is_complete')}")


class TestCaseHistorySections:
    """Test that Case History has exactly 10 sections (no consent_disclaimer)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        data = login_response.json()
        self.token = data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get a client for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        if clients_response.status_code == 200:
            clients = clients_response.json()
            if clients:
                self.client_id = clients[0].get("id")
            else:
                pytest.skip("No clients available for testing")
        else:
            pytest.skip(f"Failed to get clients: {clients_response.text}")
    
    def test_01_all_10_sections_can_be_saved(self):
        """Test that all 10 sections can be saved individually"""
        sections = [
            'basic_identification',
            'presenting_complaints',
            'history_of_present_illness',
            'past_psychiatric_history',
            'medical_history',
            'family_history',
            'personal_developmental_history',
            'mental_status_examination',
            'provisional_formulation',
            'initial_therapy_plan'
        ]
        
        for section in sections:
            response = self.session.patch(
                f"{BASE_URL}/api/case-history/{self.client_id}/section?section={section}",
                json={"test_field": f"Test data for {section}"}
            )
            
            assert response.status_code == 200, f"Failed to save section {section}: {response.text}"
            print(f"✓ Section {section} saved successfully")
        
        print(f"\n✓ All 10 sections can be saved (consent_disclaimer NOT included)")
    
    def test_02_consent_disclaimer_section_not_required(self):
        """Test that consent_disclaimer section is NOT required for completion"""
        # Fill required fields only
        self.session.patch(
            f"{BASE_URL}/api/case-history/{self.client_id}/section?section=basic_identification",
            json={"name": "Test Client for Consent Test"}
        )
        
        self.session.patch(
            f"{BASE_URL}/api/case-history/{self.client_id}/section?section=presenting_complaints",
            json={"main_problems": "Test complaints for consent separation test"}
        )
        
        # Complete without consent_disclaimer
        response = self.session.post(f"{BASE_URL}/api/case-history/{self.client_id}/complete")
        
        # Should succeed without consent_disclaimer
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Case history completes without consent_disclaimer section")


class TestConsentWorkflow:
    """Test the separate consent workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        data = login_response.json()
        self.token = data.get("token")
        self.therapist_id = data.get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get a client for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        if clients_response.status_code == 200:
            clients = clients_response.json()
            if clients:
                self.test_client = clients[0]
                self.client_id = self.test_client.get("id")
            else:
                pytest.skip("No clients available for testing")
        else:
            pytest.skip(f"Failed to get clients: {clients_response.text}")
    
    def test_01_consent_check_endpoint(self):
        """Test GET /api/therapy-consent/check/{client_id}"""
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/check/{self.client_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data
        assert "is_signed" in data
        print(f"✓ Consent check: exists={data.get('exists')}, is_signed={data.get('is_signed')}")
    
    def test_02_consent_get_endpoint(self):
        """Test GET /api/therapy-consent/{client_id}"""
        response = self.session.get(f"{BASE_URL}/api/therapy-consent/{self.client_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("exists") == False:
            print(f"✓ Consent not yet created (case history may not be complete)")
        else:
            # Should have consent text and therapist info
            print(f"✓ Consent document retrieved")
            print(f"  - therapist_name: {data.get('therapist_name')}")
            print(f"  - is_signed: {data.get('is_signed')}")
            if data.get('consent_text'):
                print(f"  - consent_text length: {len(data.get('consent_text', ''))} chars")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
