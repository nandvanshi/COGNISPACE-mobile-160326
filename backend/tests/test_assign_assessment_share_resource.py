"""
Tests for Assign Assessment and Share Resource functionality
- POST /api/assessments with client_id and assessment_type to assign assessment
- POST /api/resources/{resource_id}/assign?client_id={client_id} to share resource
- GET /api/assessments/library to get assessment types (PHQ-9, GAD-7, etc.)
- GET /api/resources to get available resources
- GET /api/assessments?client_id={client_id} to show assigned assessments for client
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
THERAPIST_CREDS = {"identifier": "7275005007", "password": "Test@123"}
CLIENT_ID = "84f06ca2-44ad-4611-8140-3645ee9868a9"  # Client Suman

class TestAssignAssessmentShareResource:
    """Tests for Assign Assessment and Share Resource endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test - get therapist auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        
        data = response.json()
        self.token = data.get("token")
        self.therapist_id = data.get("user", {}).get("id")
        assert self.token, "No token received from login"
        
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        # Cleanup - delete any test-created assessments
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Remove test-created assessments"""
        try:
            # Get assessments for the client
            response = self.session.get(f"{BASE_URL}/api/assessments?client_id={CLIENT_ID}")
            if response.status_code == 200:
                assessments = response.json()
                for a in assessments:
                    if a.get("notes") and "TEST_" in str(a.get("notes", "")):
                        self.session.delete(f"{BASE_URL}/api/assessments/{a['id']}")
        except Exception:
            pass  # Ignore cleanup errors
    
    # ============= ASSESSMENT LIBRARY TESTS =============
    
    def test_get_assessment_library(self):
        """GET /api/assessments/library should return assessment types (PHQ-9, GAD-7, etc.)"""
        response = self.session.get(f"{BASE_URL}/api/assessments/library")
        
        assert response.status_code == 200, f"Failed to get assessment library: {response.text}"
        
        library = response.json()
        assert isinstance(library, dict), "Assessment library should be a dictionary"
        
        # Check for common assessment types
        expected_types = ["PHQ-9", "GAD-7"]
        found_types = []
        for key in library.keys():
            if "PHQ" in key or "GAD" in key:
                found_types.append(key)
        
        print(f"Assessment library contains {len(library)} assessment types")
        print(f"Found types: {list(library.keys())[:10]}...")  # First 10
        
        # Verify structure of assessment entries
        for key, val in list(library.items())[:3]:
            assert "name" in val, f"Assessment {key} missing 'name' field"
            print(f"  - {key}: {val.get('name')}")
    
    # ============= ASSIGN ASSESSMENT TESTS =============
    
    def test_assign_assessment_phq9(self):
        """POST /api/assessments with PHQ-9 assessment type should create assignment"""
        test_notes = f"TEST_{uuid.uuid4().hex[:8]}"
        payload = {
            "client_id": CLIENT_ID,
            "assessment_type": "PHQ-9",
            "notes": test_notes
        }
        
        response = self.session.post(f"{BASE_URL}/api/assessments", json=payload)
        
        assert response.status_code == 200, f"Failed to assign assessment: {response.text}"
        
        data = response.json()
        assert data.get("client_id") == CLIENT_ID
        assert data.get("assessment_type") == "PHQ-9"
        assert data.get("status") == "assigned"
        assert "id" in data
        
        print(f"Successfully assigned PHQ-9 assessment with ID: {data.get('id')}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/assessments/{data['id']}")
    
    def test_assign_assessment_gad7(self):
        """POST /api/assessments with GAD-7 assessment type should create assignment"""
        test_notes = f"TEST_{uuid.uuid4().hex[:8]}"
        payload = {
            "client_id": CLIENT_ID,
            "assessment_type": "GAD-7",
            "notes": test_notes
        }
        
        response = self.session.post(f"{BASE_URL}/api/assessments", json=payload)
        
        assert response.status_code == 200, f"Failed to assign GAD-7: {response.text}"
        
        data = response.json()
        assert data.get("client_id") == CLIENT_ID
        assert data.get("assessment_type") == "GAD-7"
        assert data.get("status") == "assigned"
        
        print(f"Successfully assigned GAD-7 assessment with ID: {data.get('id')}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/assessments/{data['id']}")
    
    def test_assign_assessment_invalid_type(self):
        """POST /api/assessments with invalid assessment type should fail"""
        payload = {
            "client_id": CLIENT_ID,
            "assessment_type": "INVALID-ASSESSMENT-TYPE"
        }
        
        response = self.session.post(f"{BASE_URL}/api/assessments", json=payload)
        
        # Should fail with 400 for invalid assessment type
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("Correctly rejected invalid assessment type")
    
    def test_assign_assessment_invalid_client(self):
        """POST /api/assessments with invalid client_id should fail"""
        payload = {
            "client_id": "invalid-client-id-12345",
            "assessment_type": "PHQ-9"
        }
        
        response = self.session.post(f"{BASE_URL}/api/assessments", json=payload)
        
        # Should fail with 404 for client not found
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("Correctly rejected invalid client ID")
    
    # ============= GET ASSESSMENTS BY CLIENT TESTS =============
    
    def test_get_assessments_by_client(self):
        """GET /api/assessments?client_id={client_id} should return assessments for client"""
        # First assign an assessment
        test_notes = f"TEST_{uuid.uuid4().hex[:8]}"
        assign_response = self.session.post(f"{BASE_URL}/api/assessments", json={
            "client_id": CLIENT_ID,
            "assessment_type": "PHQ-9",
            "notes": test_notes
        })
        assert assign_response.status_code == 200
        created_id = assign_response.json().get("id")
        
        # Now get assessments for the client
        response = self.session.get(f"{BASE_URL}/api/assessments?client_id={CLIENT_ID}")
        
        assert response.status_code == 200, f"Failed to get client assessments: {response.text}"
        
        assessments = response.json()
        assert isinstance(assessments, list)
        
        # Find our created assessment
        found = any(a.get("id") == created_id for a in assessments)
        assert found, "Created assessment not found in client's assessments list"
        
        print(f"Client {CLIENT_ID} has {len(assessments)} assessment(s)")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/assessments/{created_id}")
    
    # ============= RESOURCES TESTS =============
    
    def test_get_resources(self):
        """GET /api/resources should return available resources"""
        response = self.session.get(f"{BASE_URL}/api/resources")
        
        assert response.status_code == 200, f"Failed to get resources: {response.text}"
        
        resources = response.json()
        assert isinstance(resources, list)
        
        print(f"Available resources: {len(resources)}")
        for r in resources[:5]:
            print(f"  - {r.get('title')} (ID: {r.get('id')}, Category: {r.get('category')})")
        
        # Store first resource ID for sharing test
        self.first_resource_id = resources[0].get("id") if resources else None
        
        return resources
    
    # ============= SHARE RESOURCE TESTS =============
    
    def test_share_resource_to_client(self):
        """POST /api/resources/{resource_id}/assign?client_id={client_id} should share resource"""
        # First get available resources
        resources_response = self.session.get(f"{BASE_URL}/api/resources")
        assert resources_response.status_code == 200
        resources = resources_response.json()
        
        if not resources:
            # Create a test resource first
            create_response = self.session.post(f"{BASE_URL}/api/resources", json={
                "title": "TEST Resource for Share",
                "category": "worksheet",
                "content": "Test content for sharing",
                "tags": ["test"]
            })
            if create_response.status_code == 200:
                resource_id = create_response.json().get("id")
            else:
                pytest.skip("No resources available and couldn't create test resource")
        else:
            resource_id = resources[0].get("id")
        
        # Share resource with client
        response = self.session.post(
            f"{BASE_URL}/api/resources/{resource_id}/assign?client_id={CLIENT_ID}",
            json={"notes": f"TEST_{uuid.uuid4().hex[:8]}"}
        )
        
        assert response.status_code == 200, f"Failed to share resource: {response.text}"
        
        data = response.json()
        assert "assignment_id" in data or "message" in data
        
        print(f"Successfully shared resource {resource_id} with client {CLIENT_ID}")
        print(f"Response: {data}")
    
    def test_share_invalid_resource(self):
        """POST /api/resources/{invalid_id}/assign should fail with 404"""
        invalid_resource_id = f"invalid-resource-{uuid.uuid4().hex[:8]}"
        
        response = self.session.post(
            f"{BASE_URL}/api/resources/{invalid_resource_id}/assign?client_id={CLIENT_ID}"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("Correctly rejected invalid resource ID")
    
    def test_share_resource_invalid_client(self):
        """POST /api/resources/{id}/assign with invalid client should fail"""
        # Get a valid resource first
        resources_response = self.session.get(f"{BASE_URL}/api/resources")
        assert resources_response.status_code == 200
        resources = resources_response.json()
        
        if not resources:
            pytest.skip("No resources available")
        
        resource_id = resources[0].get("id")
        invalid_client_id = f"invalid-client-{uuid.uuid4().hex[:8]}"
        
        response = self.session.post(
            f"{BASE_URL}/api/resources/{resource_id}/assign?client_id={invalid_client_id}"
        )
        
        # Should fail with 404 for client not found
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("Correctly rejected invalid client ID for resource sharing")
    
    # ============= RESOURCE ASSIGNMENTS TESTS =============
    
    def test_get_resource_assignments_by_client(self):
        """GET /api/resources/assignments?client_id={client_id} should return shared resources"""
        response = self.session.get(f"{BASE_URL}/api/resources/assignments?client_id={CLIENT_ID}")
        
        assert response.status_code == 200, f"Failed to get resource assignments: {response.text}"
        
        assignments = response.json()
        assert isinstance(assignments, list)
        
        print(f"Client {CLIENT_ID} has {len(assignments)} resource assignment(s)")
        for a in assignments[:3]:
            print(f"  - {a.get('resource_title')} (Status: {a.get('status')})")


class TestTherapistLogin:
    """Basic authentication test"""
    
    def test_therapist_login(self):
        """POST /api/auth/login should authenticate therapist"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"].get("role") == "therapist"
        
        print(f"Therapist login successful: {data['user'].get('full_name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
