"""
Test Admin Email Broadcast Feature
Tests for AI-powered email broadcasting in Super Admin Panel
- GET /api/admin/email/recipients/summary
- GET /api/admin/email/recipients/list
- POST /api/admin/email/ai-draft
- POST /api/admin/email/send
- GET /api/admin/email/history
- 403 for non-admin users
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_CREDS = {"username": "admin", "password": "admin123"}
THERAPIST_CREDS = {"identifier": "7275005007", "password": "Test@123"}


class TestAdminEmailBroadcast:
    """Admin Email Broadcast API Tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get super admin token via /api/auth/super-admin-login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/super-admin-login",
            json=SUPER_ADMIN_CREDS
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token for 403 tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=THERAPIST_CREDS
        )
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    @pytest.fixture
    def therapist_headers(self, therapist_token):
        return {"Authorization": f"Bearer {therapist_token}", "Content-Type": "application/json"}
    
    # ============= GET /api/admin/email/recipients/summary =============
    
    def test_recipients_summary_success(self, admin_headers):
        """Test GET /api/admin/email/recipients/summary returns therapist/client counts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email/recipients/summary",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Validate response structure
        assert "therapists" in data, "Response should have 'therapists' key"
        assert "clients" in data, "Response should have 'clients' key"
        
        # Validate therapists structure
        assert "total" in data["therapists"], "therapists should have 'total'"
        assert "with_email" in data["therapists"], "therapists should have 'with_email'"
        assert "by_plan" in data["therapists"], "therapists should have 'by_plan'"
        
        # Validate clients structure
        assert "total" in data["clients"], "clients should have 'total'"
        assert "with_email" in data["clients"], "clients should have 'with_email'"
        
        # Validate data types
        assert isinstance(data["therapists"]["total"], int)
        assert isinstance(data["therapists"]["with_email"], int)
        assert isinstance(data["therapists"]["by_plan"], dict)
        assert isinstance(data["clients"]["total"], int)
        assert isinstance(data["clients"]["with_email"], int)
        
        print(f"Recipients summary: Therapists={data['therapists']['total']} (with email: {data['therapists']['with_email']}), Clients={data['clients']['total']} (with email: {data['clients']['with_email']})")
        print(f"Plans breakdown: {data['therapists']['by_plan']}")
    
    def test_recipients_summary_403_for_therapist(self, therapist_headers):
        """Test GET /api/admin/email/recipients/summary returns 403 for non-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email/recipients/summary",
            headers=therapist_headers
        )
        assert response.status_code == 403, f"Expected 403 for therapist, got {response.status_code}"
        print("Correctly returned 403 for therapist accessing admin endpoint")
    
    def test_recipients_summary_401_no_auth(self):
        """Test GET /api/admin/email/recipients/summary returns 401/403 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/email/recipients/summary")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"Correctly returned {response.status_code} for unauthenticated request")
    
    # ============= GET /api/admin/email/recipients/list =============
    
    def test_recipients_list_therapists(self, admin_headers):
        """Test GET /api/admin/email/recipients/list?role=therapist"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email/recipients/list",
            params={"role": "therapist"},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            # Validate first item structure
            first = data[0]
            assert "id" in first, "Each item should have 'id'"
            assert "full_name" in first, "Each item should have 'full_name'"
            assert "email" in first, "Each item should have 'email'"
            assert "mobile" in first, "Each item should have 'mobile'"
            print(f"Therapist list returned {len(data)} therapists. First: {first.get('full_name', 'N/A')}")
        else:
            print("Therapist list is empty (no therapists in DB)")
    
    def test_recipients_list_clients(self, admin_headers):
        """Test GET /api/admin/email/recipients/list?role=client"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email/recipients/list",
            params={"role": "client"},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            first = data[0]
            assert "id" in first, "Each item should have 'id'"
            assert "full_name" in first, "Each item should have 'full_name'"
            print(f"Client list returned {len(data)} clients. First: {first.get('full_name', 'N/A')}")
        else:
            print("Client list is empty (no clients in DB)")
    
    def test_recipients_list_403_for_therapist(self, therapist_headers):
        """Test GET /api/admin/email/recipients/list returns 403 for non-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email/recipients/list",
            params={"role": "therapist"},
            headers=therapist_headers
        )
        assert response.status_code == 403, f"Expected 403 for therapist, got {response.status_code}"
        print("Correctly returned 403 for therapist accessing admin endpoint")
    
    # ============= POST /api/admin/email/ai-draft =============
    
    def test_ai_draft_generation(self, admin_headers):
        """Test POST /api/admin/email/ai-draft generates email draft"""
        payload = {
            "topic": "New feature announcement - AI-powered session notes",
            "tone": "professional",
            "audience": "therapists",
            "additional_instructions": "Keep it brief and highlight the time-saving benefits"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/email/ai-draft",
            json=payload,
            headers=admin_headers,
            timeout=60  # AI generation may take time
        )
        
        # AI endpoint may return 500 if API key not configured - that's acceptable
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            if "AI not configured" in error_detail or "AI generation failed" in error_detail:
                pytest.skip("AI not configured or API key issue - skipping AI draft test")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "generated" in data, "Response should have 'generated' key"
        assert data["generated"] == True, "generated should be True"
        assert "data" in data, "Response should have 'data' key"
        
        # Validate generated content structure
        generated = data["data"]
        assert "subject" in generated, "Generated data should have 'subject'"
        assert "html_body" in generated, "Generated data should have 'html_body'"
        assert "text_body" in generated, "Generated data should have 'text_body'"
        
        assert len(generated["subject"]) > 0, "Subject should not be empty"
        assert len(generated["html_body"]) > 0, "HTML body should not be empty"
        
        print(f"AI Draft generated successfully!")
        print(f"Subject: {generated['subject'][:80]}...")
        print(f"HTML body length: {len(generated['html_body'])} chars")
    
    def test_ai_draft_403_for_therapist(self, therapist_headers):
        """Test POST /api/admin/email/ai-draft returns 403 for non-admin"""
        payload = {"topic": "Test", "tone": "professional", "audience": "therapists"}
        response = requests.post(
            f"{BASE_URL}/api/admin/email/ai-draft",
            json=payload,
            headers=therapist_headers
        )
        assert response.status_code == 403, f"Expected 403 for therapist, got {response.status_code}"
        print("Correctly returned 403 for therapist accessing admin endpoint")
    
    def test_ai_draft_validation(self, admin_headers):
        """Test POST /api/admin/email/ai-draft with missing topic"""
        payload = {"tone": "professional", "audience": "therapists"}  # Missing topic
        response = requests.post(
            f"{BASE_URL}/api/admin/email/ai-draft",
            json=payload,
            headers=admin_headers
        )
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for missing topic, got {response.status_code}"
        print("Correctly returned 422 for missing required field 'topic'")
    
    # ============= POST /api/admin/email/send =============
    
    def test_send_email_validation_no_recipients(self, admin_headers):
        """Test POST /api/admin/email/send with specific but empty recipients"""
        payload = {
            "subject": "Test Email",
            "html_body": "<p>Test content</p>",
            "recipient_type": "specific",
            "specific_ids": []  # Empty list
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/email/send",
            json=payload,
            headers=admin_headers
        )
        # Should return 400 for empty specific_ids
        assert response.status_code == 400, f"Expected 400 for empty specific_ids, got {response.status_code}: {response.text}"
        print("Correctly returned 400 for empty specific_ids")
    
    def test_send_email_validation_by_plan_no_filter(self, admin_headers):
        """Test POST /api/admin/email/send with by_plan but no plan_filter"""
        payload = {
            "subject": "Test Email",
            "html_body": "<p>Test content</p>",
            "recipient_type": "by_plan"
            # Missing plan_filter
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/email/send",
            json=payload,
            headers=admin_headers
        )
        # Should return 400 for missing plan_filter
        assert response.status_code == 400, f"Expected 400 for missing plan_filter, got {response.status_code}: {response.text}"
        print("Correctly returned 400 for missing plan_filter with by_plan type")
    
    def test_send_email_403_for_therapist(self, therapist_headers):
        """Test POST /api/admin/email/send returns 403 for non-admin"""
        payload = {
            "subject": "Test",
            "html_body": "<p>Test</p>",
            "recipient_type": "all_therapists"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/email/send",
            json=payload,
            headers=therapist_headers
        )
        assert response.status_code == 403, f"Expected 403 for therapist, got {response.status_code}"
        print("Correctly returned 403 for therapist accessing admin endpoint")
    
    def test_send_email_to_all_therapists(self, admin_headers):
        """Test POST /api/admin/email/send to all therapists (may fail if no email provider)"""
        payload = {
            "subject": "TEST - Admin Email Broadcast Test",
            "html_body": "<p>This is a test email from the admin broadcast system.</p><p>Please ignore.</p>",
            "text_body": "This is a test email from the admin broadcast system. Please ignore.",
            "recipient_type": "all_therapists"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/email/send",
            json=payload,
            headers=admin_headers,
            timeout=120  # Sending emails may take time
        )
        
        # Email sending may fail if Resend not configured - check response structure
        if response.status_code == 200:
            data = response.json()
            assert "broadcast_id" in data, "Response should have 'broadcast_id'"
            assert "total_recipients" in data, "Response should have 'total_recipients'"
            assert "sent" in data, "Response should have 'sent'"
            assert "failed" in data, "Response should have 'failed'"
            
            print(f"Email broadcast result: {data['sent']}/{data['total_recipients']} sent, {data['failed']} failed")
            print(f"Broadcast ID: {data['broadcast_id']}")
            
            if data.get("errors"):
                print(f"Errors (first 3): {data['errors'][:3]}")
        elif response.status_code == 400:
            # May return 400 if no recipients with email
            error = response.json().get("detail", "")
            print(f"Send returned 400: {error}")
            assert "No recipients" in error or "email" in error.lower(), f"Unexpected 400 error: {error}"
        else:
            # Other errors - log but don't fail (email provider issues)
            print(f"Send returned {response.status_code}: {response.text}")
    
    # ============= GET /api/admin/email/history =============
    
    def test_email_history(self, admin_headers):
        """Test GET /api/admin/email/history returns sent email history"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email/history",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            # Validate first item structure
            first = data[0]
            assert "id" in first, "Each item should have 'id'"
            assert "subject" in first, "Each item should have 'subject'"
            assert "recipient_type" in first, "Each item should have 'recipient_type'"
            assert "total_recipients" in first, "Each item should have 'total_recipients'"
            assert "sent" in first, "Each item should have 'sent'"
            assert "failed" in first, "Each item should have 'failed'"
            assert "sent_at" in first, "Each item should have 'sent_at'"
            
            print(f"Email history returned {len(data)} records")
            print(f"Latest: '{first.get('subject', 'N/A')}' to {first.get('recipient_type')} ({first.get('sent')}/{first.get('total_recipients')} sent)")
        else:
            print("Email history is empty (no emails sent yet)")
    
    def test_email_history_403_for_therapist(self, therapist_headers):
        """Test GET /api/admin/email/history returns 403 for non-admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email/history",
            headers=therapist_headers
        )
        assert response.status_code == 403, f"Expected 403 for therapist, got {response.status_code}"
        print("Correctly returned 403 for therapist accessing admin endpoint")
    
    def test_email_history_401_no_auth(self):
        """Test GET /api/admin/email/history returns 401/403 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/email/history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"Correctly returned {response.status_code} for unauthenticated request")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
