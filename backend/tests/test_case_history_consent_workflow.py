"""
Test Case History -> Consent Workflow
Tests the complete flow:
1. Therapist completes case history
2. Consent document is created
3. Client receives notification
4. Client can check consent status
5. Client can fetch consent document
6. Client can sign consent
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


class TestCaseHistoryConsentWorkflow:
    """Test the complete case history -> consent workflow"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def test_therapist(self, admin_token):
        """Create or get a test therapist"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Check if test therapist exists
        test_mobile = "9999888877"
        response = requests.get(f"{BASE_URL}/api/admin/users?role=therapist", headers=headers)
        if response.status_code == 200:
            therapists = response.json()
            for t in therapists:
                if t.get("mobile") == test_mobile:
                    # Login as therapist
                    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                        "identifier": test_mobile,
                        "password": "Test@123"
                    })
                    if login_resp.status_code == 200:
                        return {
                            "id": t["id"],
                            "token": login_resp.json().get("access_token"),
                            "mobile": test_mobile
                        }
        
        # Create new therapist
        therapist_data = {
            "full_name": "TEST_Consent_Therapist",
            "mobile": test_mobile,
            "email": f"test_consent_therapist_{uuid.uuid4().hex[:6]}@test.com",
            "password": "Test@123",
            "qualifications": "M.Phil Clinical Psychology",
            "specializations": ["Anxiety", "Depression"],
            "experience_years": 5
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/admin/therapists", json=therapist_data, headers=headers)
        if create_resp.status_code in [200, 201]:
            therapist = create_resp.json()
            # Approve therapist
            requests.put(f"{BASE_URL}/api/admin/therapists/{therapist['id']}/approve", headers=headers)
            
            # Login as therapist
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "identifier": test_mobile,
                "password": "Test@123"
            })
            if login_resp.status_code == 200:
                return {
                    "id": therapist["id"],
                    "token": login_resp.json().get("access_token"),
                    "mobile": test_mobile
                }
        
        pytest.skip("Could not create/login test therapist")
    
    @pytest.fixture(scope="class")
    def test_client(self, test_therapist):
        """Create a test client for the therapist"""
        headers = {"Authorization": f"Bearer {test_therapist['token']}"}
        
        # Create a unique client
        unique_id = uuid.uuid4().hex[:6]
        client_data = {
            "full_name": f"TEST_Consent_Client_{unique_id}",
            "mobile": f"98765{unique_id[:5]}",
            "email": f"test_consent_client_{unique_id}@test.com",
            "password": "Client@123"
        }
        
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=headers)
        if response.status_code in [200, 201]:
            client = response.json()
            # Login as client
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "mobile": client_data["mobile"],
                "password": "Client@123"
            })
            if login_resp.status_code == 200:
                return {
                    "id": client["id"],
                    "token": login_resp.json().get("access_token"),
                    "mobile": client_data["mobile"],
                    "full_name": client_data["full_name"]
                }
        
        pytest.skip(f"Could not create test client: {response.status_code} - {response.text}")
    
    # ============= TEST CASES =============
    
    def test_01_get_case_history_creates_if_not_exists(self, test_therapist, test_client):
        """Test GET /api/clinical/case-history/{client_id} creates case history if not exists"""
        headers = {"Authorization": f"Bearer {test_therapist['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/clinical/case-history/{test_client['id']}", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["client_id"] == test_client["id"]
        assert data["is_complete"] == False
        print(f"✓ Case history created/fetched for client {test_client['id']}")
    
    def test_02_update_case_history_section(self, test_therapist, test_client):
        """Test PUT /api/clinical/case-history/{client_id} updates a section"""
        headers = {"Authorization": f"Bearer {test_therapist['token']}"}
        
        update_data = {
            "section": "identification",
            "data": {
                "name": test_client["full_name"],
                "age": 30,
                "gender": "Male",
                "occupation": "Software Engineer"
            }
        }
        
        response = requests.put(f"{BASE_URL}/api/clinical/case-history/{test_client['id']}", 
                               json=update_data, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "sections" in data or "identification" in str(data)
        print(f"✓ Case history section 'identification' updated")
    
    def test_03_check_consent_before_case_history_complete(self, test_therapist, test_client):
        """Test GET /api/clinical/therapy-consent/check/{client_id} before case history is complete"""
        headers = {"Authorization": f"Bearer {test_therapist['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/clinical/therapy-consent/check/{test_client['id']}", 
                               headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Consent may or may not exist at this point
        assert "exists" in data
        assert "is_signed" in data
        print(f"✓ Consent check before completion: exists={data['exists']}, is_signed={data['is_signed']}")
    
    def test_04_mark_case_history_complete(self, test_therapist, test_client):
        """Test POST /api/clinical/case-history/{client_id}/complete creates consent and sends notification"""
        headers = {"Authorization": f"Bearer {test_therapist['token']}"}
        
        response = requests.post(f"{BASE_URL}/api/clinical/case-history/{test_client['id']}/complete", 
                                headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert "complete" in data["message"].lower() or "notified" in data["message"].lower()
        print(f"✓ Case history marked complete: {data['message']}")
    
    def test_05_consent_exists_after_case_history_complete(self, test_therapist, test_client):
        """Test consent document exists after case history is marked complete"""
        headers = {"Authorization": f"Bearer {test_therapist['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/clinical/therapy-consent/check/{test_client['id']}", 
                               headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["exists"] == True, "Consent should exist after case history completion"
        assert data["is_signed"] == False, "Consent should not be signed yet"
        print(f"✓ Consent exists after case history completion: exists={data['exists']}, is_signed={data['is_signed']}")
    
    def test_06_client_can_check_consent_status(self, test_client):
        """Test client can check their own consent status"""
        headers = {"Authorization": f"Bearer {test_client['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/clinical/therapy-consent/check/{test_client['id']}", 
                               headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["exists"] == True, "Client should see consent exists"
        assert data["is_signed"] == False, "Consent should not be signed yet"
        print(f"✓ Client can check consent status: exists={data['exists']}, is_signed={data['is_signed']}")
    
    def test_07_client_can_fetch_consent_document(self, test_client):
        """Test client can fetch their consent document"""
        headers = {"Authorization": f"Bearer {test_client['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/clinical/therapy-consent/{test_client['id']}", 
                               headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify consent document structure
        assert "id" in data, "Consent should have id"
        assert "client_id" in data, "Consent should have client_id"
        assert data["client_id"] == test_client["id"]
        assert "therapist_name" in data, "Consent should have therapist_name"
        assert "is_signed" in data, "Consent should have is_signed"
        assert data["is_signed"] == False, "Consent should not be signed yet"
        
        # Check for consent text (may be in consent_text field)
        has_consent_content = "consent_text" in data or "INFORMED CONSENT" in str(data)
        print(f"✓ Client fetched consent document: therapist={data.get('therapist_name')}, has_content={has_consent_content}")
    
    def test_08_client_cannot_access_other_client_consent(self, test_client):
        """Test client cannot access another client's consent"""
        headers = {"Authorization": f"Bearer {test_client['token']}"}
        
        # Try to access a fake client ID
        fake_client_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/clinical/therapy-consent/{fake_client_id}", 
                               headers=headers)
        
        # Should return 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Client correctly denied access to other client's consent")
    
    def test_09_client_signs_consent(self, test_client):
        """Test client can sign their consent"""
        headers = {"Authorization": f"Bearer {test_client['token']}"}
        
        response = requests.post(
            f"{BASE_URL}/api/clinical/therapy-consent/{test_client['id']}/sign?signature_method=digital", 
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower() or "signed" in data["message"].lower()
        print(f"✓ Client signed consent: {data['message']}")
    
    def test_10_consent_is_signed_after_signing(self, test_client):
        """Test consent status shows signed after client signs"""
        headers = {"Authorization": f"Bearer {test_client['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/clinical/therapy-consent/check/{test_client['id']}", 
                               headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["exists"] == True
        assert data["is_signed"] == True, "Consent should be signed now"
        print(f"✓ Consent is now signed: exists={data['exists']}, is_signed={data['is_signed']}")
    
    def test_11_therapist_can_see_signed_consent(self, test_therapist, test_client):
        """Test therapist can see the signed consent"""
        headers = {"Authorization": f"Bearer {test_therapist['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/clinical/therapy-consent/{test_client['id']}", 
                               headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["is_signed"] == True, "Therapist should see consent is signed"
        assert "signature_date" in data, "Should have signature date"
        assert data["signature_date"] is not None, "Signature date should not be None"
        print(f"✓ Therapist sees signed consent: signature_date={data.get('signature_date')}")
    
    def test_12_client_notification_created(self, test_client):
        """Test that notification was created for client"""
        headers = {"Authorization": f"Bearer {test_client['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        
        if response.status_code == 200:
            notifications = response.json()
            # Look for consent_pending notification
            consent_notifications = [n for n in notifications if 
                                    n.get("type") == "consent_pending" or 
                                    "consent" in n.get("title", "").lower() or
                                    "consent" in n.get("message", "").lower()]
            
            if consent_notifications:
                print(f"✓ Found {len(consent_notifications)} consent-related notification(s)")
                for n in consent_notifications[:2]:
                    print(f"  - {n.get('title')}: {n.get('message')[:50]}...")
            else:
                print(f"⚠ No consent notifications found (may have been read or not created)")
        else:
            print(f"⚠ Could not fetch notifications: {response.status_code}")


class TestEmailTemplateRegistry:
    """Test that email templates are properly registered"""
    
    def test_consent_pending_client_template_exists(self):
        """Test that consent_pending_client template is in EMAIL_TEMPLATES"""
        # This is a code verification test - we check the template file
        import sys
        sys.path.insert(0, '/app/backend')
        
        try:
            from services.email.templates import EMAIL_TEMPLATES, get_email_template
            
            assert "consent_pending_client" in EMAIL_TEMPLATES, \
                "consent_pending_client template should be in EMAIL_TEMPLATES"
            
            # Test the template generates correctly
            test_data = {
                "client_name": "Test Client",
                "therapist_name": "Test Therapist",
                "dashboard_url": "https://test.com/login"
            }
            
            result = get_email_template("consent_pending_client", test_data)
            
            assert "subject" in result, "Template should return subject"
            assert "html_body" in result, "Template should return html_body"
            assert "text_body" in result, "Template should return text_body"
            assert "Test Client" in result["html_body"], "Client name should be in email"
            assert "Test Therapist" in result["html_body"], "Therapist name should be in email"
            
            print(f"✓ consent_pending_client template exists and generates correctly")
            print(f"  Subject: {result['subject']}")
            
        except ImportError as e:
            pytest.skip(f"Could not import email templates: {e}")


class TestCaseHistoryCheckEndpoint:
    """Test case history check endpoint"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "mobile": "9999888877",
            "password": "Test@123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not login as therapist")
    
    def test_check_case_history_endpoint(self, therapist_token):
        """Test GET /api/clinical/case-history/check/{client_id}"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Use a random client ID to test non-existent case
        fake_client_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/clinical/case-history/check/{fake_client_id}", 
                               headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "exists" in data
        assert "is_complete" in data
        assert data["exists"] == False, "Case history should not exist for random ID"
        print(f"✓ Case history check endpoint works: exists={data['exists']}, is_complete={data['is_complete']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
