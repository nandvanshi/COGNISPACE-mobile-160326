"""
Scheduler API Tests - Time-Based Notification Scheduler using APScheduler
Tests for:
- Scheduler Status API (GET /api/scheduler/status)
- Manual Job Trigger API (POST /api/scheduler/run/{job_id})
- Job registration verification (3 jobs with correct intervals)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSchedulerAuth:
    """Test authentication requirements for scheduler endpoints"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "9807306444",
            "password": "Abcd@1234"
        })
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        return response.json()["token"]
    
    def test_scheduler_status_requires_auth(self):
        """Test that scheduler status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 401, "Should require authentication"
    
    def test_scheduler_run_requires_auth(self):
        """Test that manual job trigger requires authentication"""
        response = requests.post(f"{BASE_URL}/api/scheduler/run/appointment_reminders")
        assert response.status_code == 401, "Should require authentication"


class TestSchedulerStatus:
    """Test GET /api/scheduler/status endpoint"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "9807306444",
            "password": "Abcd@1234"
        })
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        return response.json()["token"]
    
    def test_scheduler_status_super_admin(self, super_admin_token):
        """Test scheduler status as super admin - should return is_running=true and 3 jobs"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/status", headers=headers)
        
        assert response.status_code == 200, f"Failed to get scheduler status: {response.text}"
        data = response.json()
        
        # Verify is_running is true
        assert "is_running" in data, "Response should contain is_running field"
        assert data["is_running"] == True, "Scheduler should be running"
        
        # Verify jobs list
        assert "jobs" in data, "Response should contain jobs field"
        assert isinstance(data["jobs"], list), "Jobs should be a list"
        assert len(data["jobs"]) == 3, f"Should have 3 jobs, got {len(data['jobs'])}"
        
        # Verify checked_at timestamp
        assert "checked_at" in data, "Response should contain checked_at field"
    
    def test_scheduler_status_therapist(self, therapist_token):
        """Test scheduler status as therapist - should be allowed"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/status", headers=headers)
        
        assert response.status_code == 200, f"Therapist should be able to view scheduler status: {response.text}"
        data = response.json()
        assert "is_running" in data
        assert "jobs" in data
    
    def test_scheduler_jobs_details(self, super_admin_token):
        """Test that all 3 jobs are registered with correct details"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        jobs = data["jobs"]
        
        # Create a dict of jobs by id for easier verification
        jobs_by_id = {job["id"]: job for job in jobs}
        
        # Verify appointment_reminders job (5 min interval)
        assert "appointment_reminders" in jobs_by_id, "appointment_reminders job should exist"
        appt_job = jobs_by_id["appointment_reminders"]
        assert appt_job["name"] == "Check Appointment Reminders"
        assert "interval" in appt_job["trigger"].lower(), "Should be interval trigger"
        assert "5" in appt_job["trigger"] or "0:05:00" in appt_job["trigger"], "Should be 5 minute interval"
        assert appt_job["next_run"] is not None, "Should have next_run time"
        
        # Verify pending_session_notes job (15 min interval)
        assert "pending_session_notes" in jobs_by_id, "pending_session_notes job should exist"
        notes_job = jobs_by_id["pending_session_notes"]
        assert notes_job["name"] == "Check Pending Session Notes"
        assert "interval" in notes_job["trigger"].lower(), "Should be interval trigger"
        assert "15" in notes_job["trigger"] or "0:15:00" in notes_job["trigger"], "Should be 15 minute interval"
        assert notes_job["next_run"] is not None, "Should have next_run time"
        
        # Verify subscription_expiry job (daily at 9 AM)
        assert "subscription_expiry" in jobs_by_id, "subscription_expiry job should exist"
        sub_job = jobs_by_id["subscription_expiry"]
        assert sub_job["name"] == "Check Subscription Expiry"
        assert "cron" in sub_job["trigger"].lower(), "Should be cron trigger"
        assert sub_job["next_run"] is not None, "Should have next_run time"


class TestManualJobTrigger:
    """Test POST /api/scheduler/run/{job_id} endpoint"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "9807306444",
            "password": "Abcd@1234"
        })
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        return response.json()["token"]
    
    def test_manual_trigger_super_admin_only(self, therapist_token):
        """Test that only super admin can manually trigger jobs"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.post(
            f"{BASE_URL}/api/scheduler/run/appointment_reminders",
            headers=headers
        )
        
        assert response.status_code == 403, "Therapist should not be able to trigger jobs"
        assert "super admin" in response.json().get("detail", "").lower()
    
    def test_manual_trigger_appointment_reminders(self, super_admin_token):
        """Test manually triggering appointment_reminders job"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/scheduler/run/appointment_reminders",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to trigger job: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "appointment_reminders" in data["message"]
    
    def test_manual_trigger_pending_session_notes(self, super_admin_token):
        """Test manually triggering pending_session_notes job"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/scheduler/run/pending_session_notes",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to trigger job: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "pending_session_notes" in data["message"]
    
    def test_manual_trigger_subscription_expiry(self, super_admin_token):
        """Test manually triggering subscription_expiry job"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/scheduler/run/subscription_expiry",
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to trigger job: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "subscription_expiry" in data["message"]
    
    def test_manual_trigger_invalid_job(self, super_admin_token):
        """Test triggering a non-existent job returns error"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/scheduler/run/invalid_job_id",
            headers=headers
        )
        
        assert response.status_code == 400, "Should return 400 for invalid job"
        assert "not found" in response.json().get("detail", "").lower()


class TestSchedulerLogs:
    """Test GET /api/scheduler/logs endpoint"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": "9807306444",
            "password": "Abcd@1234"
        })
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        return response.json()["token"]
    
    def test_scheduler_logs_super_admin_only(self, therapist_token):
        """Test that only super admin can view scheduler logs"""
        headers = {"Authorization": f"Bearer {therapist_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/logs", headers=headers)
        
        assert response.status_code == 403, "Therapist should not be able to view logs"
    
    def test_scheduler_logs_super_admin(self, super_admin_token):
        """Test super admin can view scheduler logs"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/logs", headers=headers)
        
        assert response.status_code == 200, f"Failed to get logs: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Logs should be a list"
    
    def test_scheduler_logs_with_limit(self, super_admin_token):
        """Test scheduler logs with limit parameter"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/scheduler/logs?limit=10",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_scheduler_logs_filter_by_job(self, super_admin_token):
        """Test scheduler logs filtered by job_id"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/scheduler/logs?job_id=appointment_reminders",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestJobIntervals:
    """Verify job intervals are configured correctly"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_appointment_reminders_5min_interval(self, super_admin_token):
        """Verify appointment_reminders runs every 5 minutes"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/status", headers=headers)
        
        assert response.status_code == 200
        jobs = response.json()["jobs"]
        
        appt_job = next((j for j in jobs if j["id"] == "appointment_reminders"), None)
        assert appt_job is not None
        
        # Check trigger contains 5 minute interval
        trigger = appt_job["trigger"].lower()
        assert "interval" in trigger
        # APScheduler formats interval as "interval[0:05:00]" or similar
        assert "5" in trigger or "0:05:00" in trigger
    
    def test_pending_notes_15min_interval(self, super_admin_token):
        """Verify pending_session_notes runs every 15 minutes"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/status", headers=headers)
        
        assert response.status_code == 200
        jobs = response.json()["jobs"]
        
        notes_job = next((j for j in jobs if j["id"] == "pending_session_notes"), None)
        assert notes_job is not None
        
        trigger = notes_job["trigger"].lower()
        assert "interval" in trigger
        assert "15" in trigger or "0:15:00" in trigger
    
    def test_subscription_expiry_daily_9am(self, super_admin_token):
        """Verify subscription_expiry runs daily at 9 AM IST"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/scheduler/status", headers=headers)
        
        assert response.status_code == 200
        jobs = response.json()["jobs"]
        
        sub_job = next((j for j in jobs if j["id"] == "subscription_expiry"), None)
        assert sub_job is not None
        
        trigger = sub_job["trigger"].lower()
        assert "cron" in trigger
        # Cron trigger should contain hour=9
        assert "9" in trigger


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
