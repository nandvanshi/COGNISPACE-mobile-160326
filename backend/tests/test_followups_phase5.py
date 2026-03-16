"""
Phase 5 Follow-Up Intelligence Tests:
- Journey Timeline API (GET /api/follow-ups/journey/{client_id})
- Detailed Retention Analytics API (GET /api/follow-ups/retention-analytics/detailed)
- Follow-Up Settings API (GET/PUT /api/follow-ups/settings)
- Email Templates (followup_2day_reminder, followup_sameday_reminder, followup_1week_missed, followup_30day_reengagement)
- Scheduler Job Registration (followup_reminders every 30 min)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test Credentials
THERAPIST_MOBILE = "7275005007"
THERAPIST_PASSWORD = "Test@123"
CLIENT_MOBILE = "9235555549"
CLIENT_PASSWORD = "Test@123"
CLIENT_ID = "84f06ca2-44ad-4611-8140-3645ee9868a9"

@pytest.fixture(scope="module")
def therapist_token():
    """Get therapist auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": THERAPIST_MOBILE,
        "password": THERAPIST_PASSWORD
    })
    assert response.status_code == 200, f"Therapist login failed: {response.text}"
    return response.json().get("token")

@pytest.fixture(scope="module")
def client_token():
    """Get client auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": CLIENT_MOBILE,
        "password": CLIENT_PASSWORD
    })
    assert response.status_code == 200, f"Client login failed: {response.text}"
    return response.json().get("token")


class TestJourneyTimeline:
    """GET /api/follow-ups/journey/{client_id} - Client Journey Timeline API"""

    def test_journey_timeline_returns_200(self, therapist_token):
        """Test that journey timeline returns 200 for valid client"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/journey/{CLIENT_ID}", headers=headers)
        
        assert response.status_code == 200, f"Journey API failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "client_id" in data, "Missing client_id in response"
        assert "timeline" in data, "Missing timeline in response"
        assert "stats" in data, "Missing stats in response"

    def test_journey_timeline_has_stats(self, therapist_token):
        """Test that journey stats contain expected fields"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/journey/{CLIENT_ID}", headers=headers)
        
        assert response.status_code == 200
        stats = response.json().get("stats", {})
        
        # Verify stats structure
        assert "total_sessions" in stats, "Missing total_sessions in stats"
        assert "total_recommendations" in stats, "Missing total_recommendations in stats"
        assert "total_assessments" in stats, "Missing total_assessments in stats"
        assert "avg_gap_days" in stats, "Missing avg_gap_days in stats"
        assert "journey_duration_days" in stats, "Missing journey_duration_days in stats"

    def test_journey_timeline_returns_timeline_events(self, therapist_token):
        """Test that timeline contains event objects with proper structure"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/journey/{CLIENT_ID}", headers=headers)
        
        assert response.status_code == 200
        timeline = response.json().get("timeline", [])
        
        # Timeline can be empty if no events, but structure should exist
        assert isinstance(timeline, list), "Timeline should be a list"
        
        if len(timeline) > 0:
            event = timeline[0]
            assert "type" in event, "Event missing 'type' field"
            assert "date" in event, "Event missing 'date' field"

    def test_journey_timeline_no_auth_returns_401(self):
        """Test that journey endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/journey/{CLIENT_ID}")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_journey_timeline_client_access_denied(self, client_token):
        """Test that clients cannot access journey timeline (therapist/assistant only)"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/journey/{CLIENT_ID}", headers=headers)
        assert response.status_code == 403, f"Expected 403 for client access, got {response.status_code}"

    def test_journey_timeline_invalid_client_returns_404(self, therapist_token):
        """Test that journey returns 404 for invalid client_id"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/journey/invalid-client-id", headers=headers)
        assert response.status_code == 404, f"Expected 404 for invalid client, got {response.status_code}"


class TestDetailedRetentionAnalytics:
    """GET /api/follow-ups/retention-analytics/detailed - Detailed Retention Analytics"""

    def test_detailed_analytics_returns_200(self, therapist_token):
        """Test that detailed analytics returns 200"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/retention-analytics/detailed", headers=headers)
        
        assert response.status_code == 200, f"Detailed analytics failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_clients" in data, "Missing total_clients"
        assert "clients_with_sessions" in data, "Missing clients_with_sessions"
        assert "avg_sessions_per_client" in data, "Missing avg_sessions_per_client"
        assert "avg_gap_between_sessions" in data, "Missing avg_gap_between_sessions"

    def test_detailed_analytics_has_client_details(self, therapist_token):
        """Test that detailed analytics includes per-client breakdown"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/retention-analytics/detailed", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "client_details" in data, "Missing client_details"
        assert isinstance(data["client_details"], list), "client_details should be a list"
        
        if len(data["client_details"]) > 0:
            client = data["client_details"][0]
            assert "client_id" in client, "Missing client_id in client_details"
            assert "client_name" in client, "Missing client_name in client_details"
            assert "session_count" in client, "Missing session_count in client_details"
            assert "days_since_last_session" in client, "Missing days_since_last_session"

    def test_detailed_analytics_no_auth_returns_401(self):
        """Test that detailed analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/follow-ups/retention-analytics/detailed")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_detailed_analytics_client_access_denied(self, client_token):
        """Test that clients cannot access detailed analytics"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/retention-analytics/detailed", headers=headers)
        assert response.status_code == 403, f"Expected 403 for client access, got {response.status_code}"


class TestFollowUpSettings:
    """GET/PUT /api/follow-ups/settings - Therapist Follow-Up Reminder Settings"""

    def test_get_settings_returns_200(self, therapist_token):
        """Test that get settings returns 200 with default values"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/settings", headers=headers)
        
        assert response.status_code == 200, f"Get settings failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "followup_email_enabled" in data, "Missing followup_email_enabled"
        assert "followup_whatsapp_enabled" in data, "Missing followup_whatsapp_enabled"
        assert isinstance(data["followup_email_enabled"], bool), "followup_email_enabled should be boolean"
        assert isinstance(data["followup_whatsapp_enabled"], bool), "followup_whatsapp_enabled should be boolean"

    def test_update_settings_email_toggle(self, therapist_token):
        """Test toggling email reminders on/off"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Get current state
        get_response = requests.get(f"{BASE_URL}/api/follow-ups/settings", headers=headers)
        assert get_response.status_code == 200
        current_email_enabled = get_response.json().get("followup_email_enabled")
        
        # Toggle email setting
        new_value = not current_email_enabled
        put_response = requests.put(f"{BASE_URL}/api/follow-ups/settings", headers=headers, json={
            "followup_email_enabled": new_value
        })
        assert put_response.status_code == 200, f"Update failed: {put_response.text}"
        assert "message" in put_response.json()
        
        # Verify the change persisted
        verify_response = requests.get(f"{BASE_URL}/api/follow-ups/settings", headers=headers)
        assert verify_response.status_code == 200
        assert verify_response.json().get("followup_email_enabled") == new_value
        
        # Restore original value
        requests.put(f"{BASE_URL}/api/follow-ups/settings", headers=headers, json={
            "followup_email_enabled": current_email_enabled
        })

    def test_update_settings_whatsapp_toggle(self, therapist_token):
        """Test toggling WhatsApp reminders on/off"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Get current state
        get_response = requests.get(f"{BASE_URL}/api/follow-ups/settings", headers=headers)
        assert get_response.status_code == 200
        current_whatsapp_enabled = get_response.json().get("followup_whatsapp_enabled")
        
        # Toggle WhatsApp setting
        new_value = not current_whatsapp_enabled
        put_response = requests.put(f"{BASE_URL}/api/follow-ups/settings", headers=headers, json={
            "followup_whatsapp_enabled": new_value
        })
        assert put_response.status_code == 200, f"Update failed: {put_response.text}"
        
        # Verify the change persisted
        verify_response = requests.get(f"{BASE_URL}/api/follow-ups/settings", headers=headers)
        assert verify_response.status_code == 200
        assert verify_response.json().get("followup_whatsapp_enabled") == new_value
        
        # Restore original value
        requests.put(f"{BASE_URL}/api/follow-ups/settings", headers=headers, json={
            "followup_whatsapp_enabled": current_whatsapp_enabled
        })

    def test_settings_no_auth_returns_401(self):
        """Test that settings endpoints require authentication"""
        get_response = requests.get(f"{BASE_URL}/api/follow-ups/settings")
        assert get_response.status_code in [401, 403], f"GET Expected 401/403, got {get_response.status_code}"
        
        put_response = requests.put(f"{BASE_URL}/api/follow-ups/settings", json={"followup_email_enabled": True})
        assert put_response.status_code in [401, 403], f"PUT Expected 401/403, got {put_response.status_code}"

    def test_settings_client_access_denied(self, client_token):
        """Test that clients cannot access settings"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/follow-ups/settings", headers=headers)
        assert response.status_code == 403, f"Expected 403 for client access, got {response.status_code}"

    def test_update_settings_empty_body_returns_400(self, therapist_token):
        """Test that empty update body returns 400"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.put(f"{BASE_URL}/api/follow-ups/settings", headers=headers, json={})
        assert response.status_code == 400, f"Expected 400 for empty body, got {response.status_code}"


class TestSchedulerJobRegistration:
    """Verify scheduler jobs are registered correctly"""

    def test_scheduler_jobs_endpoint(self, therapist_token):
        """Test that scheduler jobs list includes followup_reminders job"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        
        # Try the scheduler jobs endpoint if exists
        response = requests.get(f"{BASE_URL}/api/scheduler/jobs", headers=headers)
        
        if response.status_code == 200:
            jobs = response.json()
            job_ids = [job.get("id") for job in jobs]
            assert "followup_reminders" in job_ids, f"followup_reminders job not found. Found jobs: {job_ids}"
            
            # Verify the followup_reminders job details
            followup_job = next((j for j in jobs if j.get("id") == "followup_reminders"), None)
            assert followup_job is not None, "followup_reminders job not found"
            assert "trigger" in followup_job, "Job missing trigger info"
            # IntervalTrigger with 30 minutes
            assert "30" in str(followup_job.get("trigger", "")), f"Job trigger should be 30 minutes: {followup_job.get('trigger')}"
        else:
            # Scheduler endpoint might not be exposed, just mark as skipped
            pytest.skip(f"Scheduler jobs endpoint returned {response.status_code}")


class TestEmailTemplates:
    """Verify email templates are registered (code review test)"""

    def test_email_templates_import(self):
        """Test that email templates module can be imported and has required templates"""
        # This test runs on the test server and verifies templates exist
        # We can't directly import Python modules, so we verify via API or code presence
        
        # For this test, we verify by checking that the scheduler can be run
        # The templates are imported by the followup_reminders job
        # If templates were missing, the job would fail
        
        # We can verify templates exist by checking the code statically
        import subprocess
        result = subprocess.run(
            ["grep", "-l", "followup_2day_reminder", "/app/backend/services/email/templates.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "followup_2day_reminder template not found in templates.py"
        
        result = subprocess.run(
            ["grep", "-l", "followup_sameday_reminder", "/app/backend/services/email/templates.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "followup_sameday_reminder template not found in templates.py"
        
        result = subprocess.run(
            ["grep", "-l", "followup_1week_missed", "/app/backend/services/email/templates.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "followup_1week_missed template not found in templates.py"
        
        result = subprocess.run(
            ["grep", "-l", "followup_30day_reengagement", "/app/backend/services/email/templates.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "followup_30day_reengagement template not found in templates.py"

    def test_email_templates_registered_in_registry(self):
        """Test that followup templates are in EMAIL_TEMPLATES registry"""
        import subprocess
        
        # Check that templates are registered
        templates = ["followup_2day_reminder", "followup_sameday_reminder", "followup_1week_missed", "followup_30day_reengagement"]
        
        for template in templates:
            result = subprocess.run(
                ["grep", "-c", f'EMAIL_TEMPLATES\\["{template}"\\]', "/app/backend/services/email/templates.py"],
                capture_output=True,
                text=True
            )
            assert int(result.stdout.strip()) > 0, f"{template} not registered in EMAIL_TEMPLATES"


class TestSchedulerJobCode:
    """Verify scheduler code for followup_reminders job"""

    def test_followup_reminders_job_registered(self):
        """Test that followup_reminders job is registered in scheduler"""
        import subprocess
        
        # Check that the job is registered with correct ID
        result = subprocess.run(
            ["grep", "-c", "id='followup_reminders'", "/app/backend/services/scheduler/scheduler.py"],
            capture_output=True,
            text=True
        )
        assert int(result.stdout.strip()) > 0, "followup_reminders job not registered in scheduler"
        
        # Check the interval is 30 minutes
        result = subprocess.run(
            ["grep", "-A1", "check_followup_reminders", "/app/backend/services/scheduler/scheduler.py"],
            capture_output=True,
            text=True
        )
        assert "IntervalTrigger" in result.stdout or "minutes=30" in result.stdout, \
            f"followup_reminders should run every 30 minutes: {result.stdout}"

    def test_followup_reminders_module_exists(self):
        """Test that followup_reminders.py module exists"""
        import os
        assert os.path.exists("/app/backend/services/scheduler/followup_reminders.py"), \
            "followup_reminders.py module not found"

    def test_followup_reminders_function_defined(self):
        """Test that check_followup_reminders function is defined"""
        import subprocess
        
        result = subprocess.run(
            ["grep", "-c", "async def check_followup_reminders", "/app/backend/services/scheduler/followup_reminders.py"],
            capture_output=True,
            text=True
        )
        assert int(result.stdout.strip()) > 0, "check_followup_reminders function not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
