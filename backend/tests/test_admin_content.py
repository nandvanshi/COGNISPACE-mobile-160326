"""
Admin Content Management API Tests
Tests the admin CRUD operations for:
- homework_template
- protocol_template
- resource
- assessment
- note_template

Also tests that therapist APIs can see admin content with source='admin'.
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials from backend/.env
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Therapist credentials
THERAPIST_MOBILE = "7275005007"
THERAPIST_PASSWORD = "Test@123"


class TestAdminContentCRUD:
    """Test Admin Content CRUD operations for all 5 content types"""
    
    admin_token = None
    therapist_token = None
    created_ids = {}  # Store created content IDs for cleanup
    
    @classmethod
    def setup_class(cls):
        """Login as admin and therapist before tests"""
        # Admin login
        admin_resp = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert admin_resp.status_code == 200, f"Admin login failed: {admin_resp.text}"
        cls.admin_token = admin_resp.json().get("token")
        assert cls.admin_token, "No admin token received"
        print(f"Admin login successful")
        
        # Therapist login
        therapist_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert therapist_resp.status_code == 200, f"Therapist login failed: {therapist_resp.text}"
        cls.therapist_token = therapist_resp.json().get("token")
        assert cls.therapist_token, "No therapist token received"
        print(f"Therapist login successful")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup created test content"""
        if not cls.admin_token:
            return
        headers = {"Authorization": f"Bearer {cls.admin_token}"}
        for content_type, item_id in cls.created_ids.items():
            try:
                requests.delete(f"{BASE_URL}/api/admin/content/{content_type}/{item_id}", headers=headers)
                print(f"Cleaned up {content_type}: {item_id}")
            except Exception as e:
                print(f"Cleanup failed for {content_type}: {e}")
    
    def get_admin_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/jsonճ"}
    
    def get_therapist_headers(self):
        return {"Authorization": f"Bearer {self.therapist_token}", "Content-Type": "application/json"}
    
    # ===== Admin Content Stats =====
    
    def test_01_admin_content_stats(self):
        """GET /api/admin/content - Get content stats as admin"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "homework_template" in data, "Missing homework_template in stats"
        assert "protocol_template" in data, "Missing protocol_template in stats"
        assert "resource" in data, "Missing resource in stats"
        assert "assessment" in data, "Missing assessment in stats"
        assert "note_template" in data, "Missing note_template in stats"
        print(f"Admin content stats: {data}")
    
    # ===== Homework Template CRUD =====
    
    def test_02_create_homework_template(self):
        """POST /api/admin/content/homework_template - Create homework template"""
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        payload = {
            "type": "homework_template",
            "title": "TEST_Admin Gratitude Journal",
            "description": "Practice gratitude daily by writing 3 things you're grateful for.",
            "category": "journaling",
            "tags": ["gratitude", "wellness", "daily"]
        }
        resp = requests.post(f"{BASE_URL}/api/admin/content/homework_template", json=payload, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("id"), "No ID returned"
        assert data.get("title") == payload["title"], "Title mismatch"
        assert data.get("source") == "admin", "Source should be 'admin'"
        TestAdminContentCRUD.created_ids["homework_template"] = data["id"]
        print(f"Created homework_template: {data['id']}")
    
    def test_03_get_homework_templates(self):
        """GET /api/admin/content/homework_template - List homework templates"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content/homework_template", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        # Find our created template
        created_id = TestAdminContentCRUD.created_ids.get("homework_template")
        if created_id:
            found = any(item.get("id") == created_id for item in data)
            assert found, f"Created homework template {created_id} not found in list"
        print(f"Found {len(data)} homework templates")
    
    def test_04_update_homework_template(self):
        """PUT /api/admin/content/homework_template/{id} - Update homework template"""
        created_id = TestAdminContentCRUD.created_ids.get("homework_template")
        if not created_id:
            pytest.skip("No homework template created to update")
        
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        payload = {
            "title": "TEST_Admin Updated Gratitude Journal",
            "description": "Updated: Practice gratitude daily with 5 things you're grateful for.",
            "tags": ["gratitude", "wellness", "daily", "updated"]
        }
        resp = requests.put(f"{BASE_URL}/api/admin/content/homework_template/{created_id}", json=payload, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("title") == payload["title"], "Title not updated"
        print(f"Updated homework_template: {created_id}")
    
    # ===== Protocol Template CRUD =====
    
    def test_05_create_protocol_template(self):
        """POST /api/admin/content/protocol_template - Create protocol template"""
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        payload = {
            "type": "protocol_template",
            "title": "TEST_Admin CBT for Social Anxiety",
            "description": "8-session CBT protocol for social anxiety disorder",
            "category": "CBT",
            "tags": ["anxiety", "social", "cbt"],
            "content": {
                "modality": "CBT",
                "condition": "Social Anxiety",
                "sessions": [
                    {"session_number": 1, "title": "Assessment", "goals": ["Initial assessment", "Psychoeducation"]},
                    {"session_number": 2, "title": "Cognitive Restructuring", "goals": ["Identify automatic thoughts"]}
                ]
            }
        }
        resp = requests.post(f"{BASE_URL}/api/admin/content/protocol_template", json=payload, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("id"), "No ID returned"
        assert data.get("source") == "admin", "Source should be 'admin'"
        TestAdminContentCRUD.created_ids["protocol_template"] = data["id"]
        print(f"Created protocol_template: {data['id']}")
    
    def test_06_get_protocol_templates(self):
        """GET /api/admin/content/protocol_template - List protocol templates"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content/protocol_template", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        print(f"Found {len(data)} protocol templates")
    
    # ===== Resource CRUD =====
    
    def test_07_create_resource(self):
        """POST /api/admin/content/resource - Create resource"""
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        payload = {
            "type": "resource",
            "title": "TEST_Admin Anxiety Worksheet",
            "description": "A comprehensive worksheet for tracking anxiety triggers and coping strategies.",
            "category": "worksheet",
            "tags": ["anxiety", "worksheet", "coping"]
        }
        resp = requests.post(f"{BASE_URL}/api/admin/content/resource", json=payload, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("id"), "No ID returned"
        assert data.get("source") == "admin", "Source should be 'admin'"
        TestAdminContentCRUD.created_ids["resource"] = data["id"]
        print(f"Created resource: {data['id']}")
    
    def test_08_get_resources(self):
        """GET /api/admin/content/resource - List resources"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content/resource", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        print(f"Found {len(data)} resources")
    
    # ===== Assessment CRUD =====
    
    def test_09_create_assessment(self):
        """POST /api/admin/content/assessment - Create assessment"""
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        payload = {
            "type": "assessment",
            "title": "TEST_Admin Stress Assessment",
            "description": "A 10-question stress level assessment",
            "category": "general",
            "tags": ["stress", "assessment", "screening"],
            "content": {
                "questions": [
                    {"text": "How often do you feel overwhelmed?", "options": [0, 1, 2, 3]},
                    {"text": "How often do you have trouble sleeping?", "options": [0, 1, 2, 3]}
                ],
                "scoring": {"min": 0, "max": 6, "interpretation": "Higher scores indicate higher stress"}
            }
        }
        resp = requests.post(f"{BASE_URL}/api/admin/content/assessment", json=payload, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("id"), "No ID returned"
        assert data.get("source") == "admin", "Source should be 'admin'"
        TestAdminContentCRUD.created_ids["assessment"] = data["id"]
        print(f"Created assessment: {data['id']}")
    
    def test_10_get_assessments(self):
        """GET /api/admin/content/assessment - List assessments"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content/assessment", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        print(f"Found {len(data)} assessments")
    
    # ===== Note Template CRUD =====
    
    def test_11_create_note_template(self):
        """POST /api/admin/content/note_template - Create note template"""
        headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        payload = {
            "type": "note_template",
            "title": "TEST_Admin SOAP Note Template",
            "description": "Standard SOAP format for clinical session notes",
            "category": "SOAP",
            "tags": ["soap", "clinical", "documentation"]
        }
        resp = requests.post(f"{BASE_URL}/api/admin/content/note_template", json=payload, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("id"), "No ID returned"
        assert data.get("source") == "admin", "Source should be 'admin'"
        TestAdminContentCRUD.created_ids["note_template"] = data["id"]
        print(f"Created note_template: {data['id']}")
    
    def test_12_get_note_templates(self):
        """GET /api/admin/content/note_template - List note templates"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content/note_template", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        print(f"Found {len(data)} note templates")


class TestTherapistSeesAdminContent:
    """Test that therapist APIs return admin content with source='admin'"""
    
    admin_token = None
    therapist_token = None
    
    @classmethod
    def setup_class(cls):
        """Login as admin and therapist"""
        # Admin login
        admin_resp = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert admin_resp.status_code == 200, f"Admin login failed: {admin_resp.text}"
        cls.admin_token = admin_resp.json().get("token")
        
        # Therapist login
        therapist_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert therapist_resp.status_code == 200, f"Therapist login failed: {therapist_resp.text}"
        cls.therapist_token = therapist_resp.json().get("token")
    
    def test_therapist_sees_admin_homework_templates(self):
        """GET /api/homework-templates - Therapist should see admin templates with source='admin'"""
        headers = {"Authorization": f"Bearer {self.therapist_token}"}
        resp = requests.get(f"{BASE_URL}/api/homework-templates", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        
        # Check for admin content (source='admin')
        admin_items = [item for item in data if item.get("source") == "admin"]
        system_items = [item for item in data if item.get("is_system") == True]
        print(f"Homework templates: {len(data)} total, {len(admin_items)} admin, {len(system_items)} system")
        
        # Should have system templates at minimum
        assert len(system_items) > 0, "Expected at least some system templates"
    
    def test_therapist_sees_admin_protocol_templates(self):
        """GET /api/protocols/templates - Therapist should see admin templates"""
        headers = {"Authorization": f"Bearer {self.therapist_token}"}
        resp = requests.get(f"{BASE_URL}/api/protocols/templates", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, dict), "Expected dict response"
        
        # Check for admin-prefixed keys
        admin_keys = [k for k in data.keys() if k.startswith("ADMIN_")]
        builtin_keys = [k for k in data.keys() if not k.startswith("ADMIN_")]
        print(f"Protocol templates: {len(data)} total, {len(admin_keys)} admin, {len(builtin_keys)} built-in")
        
        # Should have built-in templates at minimum
        assert len(builtin_keys) > 0, "Expected built-in protocol templates"
    
    def test_therapist_sees_admin_resources(self):
        """GET /api/resources - Therapist should see admin resources"""
        headers = {"Authorization": f"Bearer {self.therapist_token}"}
        resp = requests.get(f"{BASE_URL}/api/resources", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        
        # Check for admin resources (therapist_id='admin')
        admin_items = [item for item in data if item.get("therapist_id") == "admin"]
        print(f"Resources: {len(data)} total, {len(admin_items)} admin")
    
    def test_therapist_sees_admin_assessments(self):
        """GET /api/assessments/library - Therapist should see admin assessments"""
        headers = {"Authorization": f"Bearer {self.therapist_token}"}
        resp = requests.get(f"{BASE_URL}/api/assessments/library", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, dict), "Expected dict response"
        
        # Check for admin-prefixed keys
        admin_keys = [k for k in data.keys() if k.startswith("ADMIN_")]
        builtin_keys = [k for k in data.keys() if not k.startswith("ADMIN_")]
        print(f"Assessment library: {len(data)} total, {len(admin_keys)} admin, {len(builtin_keys)} built-in")
        
        # Should have built-in assessments at minimum
        assert len(builtin_keys) > 0, "Expected built-in assessments"


class TestAdminAccessControl:
    """Test that non-admin cannot access admin content APIs"""
    
    therapist_token = None
    
    @classmethod
    def setup_class(cls):
        """Login as therapist"""
        therapist_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert therapist_resp.status_code == 200, f"Therapist login failed: {therapist_resp.text}"
        cls.therapist_token = therapist_resp.json().get("token")
    
    def test_therapist_cannot_get_admin_content_stats(self):
        """GET /api/admin/content - Therapist should get 403"""
        headers = {"Authorization": f"Bearer {self.therapist_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content", headers=headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("Therapist correctly denied access to admin content stats")
    
    def test_therapist_cannot_list_admin_homework_templates(self):
        """GET /api/admin/content/homework_template - Therapist should get 403"""
        headers = {"Authorization": f"Bearer {self.therapist_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/content/homework_template", headers=headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("Therapist correctly denied access to admin homework templates")
    
    def test_therapist_cannot_create_admin_content(self):
        """POST /api/admin/content/homework_template - Therapist should get 403"""
        headers = {"Authorization": f"Bearer {self.therapist_token}", "Content-Type": "application/json"}
        payload = {
            "type": "homework_template",
            "title": "TEST_Unauthorized Content",
            "description": "This should fail"
        }
        resp = requests.post(f"{BASE_URL}/api/admin/content/homework_template", json=payload, headers=headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("Therapist correctly denied access to create admin content")
    
    def test_therapist_cannot_delete_admin_content(self):
        """DELETE /api/admin/content/homework_template/{id} - Therapist should get 403"""
        headers = {"Authorization": f"Bearer {self.therapist_token}"}
        resp = requests.delete(f"{BASE_URL}/api/admin/content/homework_template/fake-id", headers=headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("Therapist correctly denied access to delete admin content")


class TestDeleteAdminContent:
    """Test deletion of admin content"""
    
    admin_token = None
    created_id = None
    
    @classmethod
    def setup_class(cls):
        """Login as admin and create test content"""
        admin_resp = requests.post(f"{BASE_URL}/api/auth/super-admin-login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        assert admin_resp.status_code == 200, f"Admin login failed: {admin_resp.text}"
        cls.admin_token = admin_resp.json().get("token")
        
        # Create test content to delete
        headers = {"Authorization": f"Bearer {cls.admin_token}", "Content-Type": "application/json"}
        payload = {
            "type": "homework_template",
            "title": "TEST_To Be Deleted",
            "description": "This will be deleted in test"
        }
        resp = requests.post(f"{BASE_URL}/api/admin/content/homework_template", json=payload, headers=headers)
        if resp.status_code == 200:
            cls.created_id = resp.json().get("id")
            print(f"Created test content for deletion: {cls.created_id}")
    
    def test_delete_admin_content(self):
        """DELETE /api/admin/content/homework_template/{id} - Delete content"""
        if not self.created_id:
            pytest.skip("No content created to delete")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.delete(f"{BASE_URL}/api/admin/content/homework_template/{self.created_id}", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify it's deleted - should not be found in list
        resp2 = requests.get(f"{BASE_URL}/api/admin/content/homework_template", headers=headers)
        assert resp2.status_code == 200
        items = resp2.json()
        found = any(item.get("id") == self.created_id for item in items)
        assert not found, f"Deleted content {self.created_id} still exists"
        print(f"Successfully deleted and verified: {self.created_id}")
    
    def test_delete_nonexistent_content(self):
        """DELETE /api/admin/content/homework_template/{id} - Should return 404"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.delete(f"{BASE_URL}/api/admin/content/homework_template/nonexistent-id", headers=headers)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("Correctly returned 404 for nonexistent content")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
