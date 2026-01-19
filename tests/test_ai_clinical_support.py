"""
Test AI Clinical Support Features
- AI Assessment Suggestions (POST /api/ai/suggest-assessments)
- AI Protocol Builder (POST /api/ai/generate-protocol)
- AI Homework Generator (POST /api/ai/generate-homework)
- Resource Library CRUD (POST/GET /api/resources, POST /api/resources/{id}/assign)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "password"


class TestAIClinicalSupport:
    """Test AI Clinical Support endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as therapist and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.therapist_id = data["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a client for testing
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        if clients_response.status_code == 200 and clients_response.json():
            self.client_id = clients_response.json()[0]["id"]
            self.client_name = clients_response.json()[0]["full_name"]
        else:
            self.client_id = None
            self.client_name = None
    
    # ============= AI ASSESSMENT SUGGESTIONS =============
    
    def test_ai_suggest_assessments_with_query(self):
        """Test AI assessment suggestions with a symptom query"""
        response = requests.post(
            f"{BASE_URL}/api/ai/suggest-assessments",
            headers=self.headers,
            json={
                "query": "Client reports feeling sad, hopeless, and has difficulty sleeping for the past 2 weeks. Also experiencing excessive worry about work and family.",
                "include_intake": True,
                "include_notes": True
            },
            timeout=60  # AI may take time
        )
        
        assert response.status_code == 200, f"AI suggest assessments failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "suggestions" in data, "Response should contain suggestions"
        assert "analysis_summary" in data, "Response should contain analysis_summary"
        assert "data_sources_used" in data, "Response should contain data_sources_used"
        
        # Validate suggestions structure
        if data["suggestions"]:
            suggestion = data["suggestions"][0]
            assert "assessment_name" in suggestion
            assert "assessment_type" in suggestion
            assert "reason" in suggestion
            assert "priority" in suggestion
            assert "relevant_symptoms" in suggestion
            
            # Check priority is valid
            assert suggestion["priority"] in ["high", "medium", "low"]
        
        print(f"AI Assessment Suggestions: {len(data['suggestions'])} suggestions returned")
        print(f"Analysis Summary: {data['analysis_summary'][:200]}...")
    
    def test_ai_suggest_assessments_with_client(self):
        """Test AI assessment suggestions with client ID"""
        if not self.client_id:
            pytest.skip("No client available for testing")
        
        response = requests.post(
            f"{BASE_URL}/api/ai/suggest-assessments",
            headers=self.headers,
            json={
                "client_id": self.client_id,
                "query": "Client showing signs of anxiety and panic attacks",
                "include_intake": True,
                "include_notes": True
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"AI suggest assessments with client failed: {response.text}"
        data = response.json()
        assert "suggestions" in data
        print(f"AI Assessment Suggestions for client: {len(data['suggestions'])} suggestions")
    
    def test_ai_suggest_assessments_no_input(self):
        """Test AI assessment suggestions without any input - should fail"""
        response = requests.post(
            f"{BASE_URL}/api/ai/suggest-assessments",
            headers=self.headers,
            json={
                "include_intake": True,
                "include_notes": True
            },
            timeout=30
        )
        
        assert response.status_code == 400, "Should fail without client_id or query"
    
    # ============= AI PROTOCOL BUILDER =============
    
    def test_ai_generate_protocol_with_query(self):
        """Test AI protocol generation with a condition description"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-protocol",
            headers=self.headers,
            json={
                "query": "Client diagnosed with moderate depression and social anxiety. Has difficulty with negative thought patterns and avoids social situations.",
                "modality_preference": "CBT"
            },
            timeout=90  # Protocol generation may take longer
        )
        
        assert response.status_code == 200, f"AI generate protocol failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "protocol_name" in data, "Response should contain protocol_name"
        assert "target_condition" in data, "Response should contain target_condition"
        assert "recommended_modality" in data, "Response should contain recommended_modality"
        assert "rationale" in data, "Response should contain rationale"
        assert "estimated_sessions" in data, "Response should contain estimated_sessions"
        assert "sessions" in data, "Response should contain sessions"
        assert "progress_markers" in data, "Response should contain progress_markers"
        
        # Validate sessions structure
        assert len(data["sessions"]) > 0, "Should have at least one session"
        session = data["sessions"][0]
        assert "session_number" in session
        assert "title" in session
        assert "objectives" in session
        assert "interventions" in session
        assert "duration_minutes" in session
        
        print(f"Protocol Generated: {data['protocol_name']}")
        print(f"Modality: {data['recommended_modality']}")
        print(f"Sessions: {len(data['sessions'])}")
    
    def test_ai_generate_protocol_with_client(self):
        """Test AI protocol generation with client ID"""
        if not self.client_id:
            pytest.skip("No client available for testing")
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-protocol",
            headers=self.headers,
            json={
                "client_id": self.client_id,
                "query": "Generalized anxiety disorder with panic symptoms"
            },
            timeout=90
        )
        
        assert response.status_code == 200, f"AI generate protocol with client failed: {response.text}"
        data = response.json()
        assert "sessions" in data
        print(f"Protocol for client: {data['protocol_name']} with {len(data['sessions'])} sessions")
    
    def test_ai_generate_protocol_no_input(self):
        """Test AI protocol generation without any input - should fail"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-protocol",
            headers=self.headers,
            json={},
            timeout=30
        )
        
        assert response.status_code == 400, "Should fail without client_id, assessment_ids, or query"
    
    # ============= AI HOMEWORK GENERATOR =============
    
    def test_ai_generate_homework(self):
        """Test AI homework generation"""
        if not self.client_id:
            pytest.skip("No client available for testing")
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-homework",
            headers=self.headers,
            json={
                "client_id": self.client_id,
                "context": "Discussed cognitive distortions and negative thought patterns. Client identified catastrophizing as a common pattern.",
                "homework_type": "worksheet"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"AI generate homework failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "title" in data, "Response should contain title"
        assert "description" in data, "Response should contain description"
        assert "instructions" in data, "Response should contain instructions"
        assert "exercises" in data, "Response should contain exercises"
        assert "estimated_time_minutes" in data, "Response should contain estimated_time_minutes"
        assert "therapeutic_rationale" in data, "Response should contain therapeutic_rationale"
        
        # Validate exercises structure
        if data["exercises"]:
            exercise = data["exercises"][0]
            assert "name" in exercise
            assert "description" in exercise
        
        print(f"Homework Generated: {data['title']}")
        print(f"Estimated Time: {data['estimated_time_minutes']} minutes")
        print(f"Exercises: {len(data['exercises'])}")
    
    def test_ai_generate_homework_different_types(self):
        """Test AI homework generation with different types"""
        if not self.client_id:
            pytest.skip("No client available for testing")
        
        homework_types = ["exercise", "reflection", "meditation"]
        
        for hw_type in homework_types:
            response = requests.post(
                f"{BASE_URL}/api/ai/generate-homework",
                headers=self.headers,
                json={
                    "client_id": self.client_id,
                    "context": "Working on stress management",
                    "homework_type": hw_type
                },
                timeout=60
            )
            
            assert response.status_code == 200, f"AI generate homework ({hw_type}) failed: {response.text}"
            data = response.json()
            assert "title" in data
            print(f"Homework type '{hw_type}': {data['title']}")
    
    def test_ai_generate_homework_no_client(self):
        """Test AI homework generation without client - should fail"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-homework",
            headers=self.headers,
            json={
                "context": "Some context"
            },
            timeout=30
        )
        
        # Should fail with 422 (validation error) or 404 (client not found)
        assert response.status_code in [404, 422], f"Should fail without client_id: {response.status_code}"


class TestResourceLibrary:
    """Test Resource Library CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.therapist_id = data["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a client for testing
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        if clients_response.status_code == 200 and clients_response.json():
            self.client_id = clients_response.json()[0]["id"]
        else:
            self.client_id = None
    
    def test_create_resource(self):
        """Test creating a new resource"""
        resource_data = {
            "title": "TEST_Anxiety Thought Record Worksheet",
            "category": "worksheet",
            "content": "This worksheet helps you identify and challenge anxious thoughts.\n\n1. Situation: What happened?\n2. Automatic Thought: What went through your mind?\n3. Emotion: How did you feel? (0-100%)\n4. Evidence For: What supports this thought?\n5. Evidence Against: What contradicts this thought?\n6. Balanced Thought: What's a more balanced perspective?\n7. New Emotion: How do you feel now? (0-100%)",
            "tags": ["anxiety", "CBT", "thought record"],
            "is_downloadable": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/resources",
            headers=self.headers,
            json=resource_data
        )
        
        assert response.status_code == 200, f"Create resource failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert data["title"] == resource_data["title"]
        assert data["category"] == resource_data["category"]
        assert data["content"] == resource_data["content"]
        assert "id" in data
        assert data["usage_count"] == 0
        
        self.created_resource_id = data["id"]
        print(f"Resource created: {data['id']}")
        
        return data["id"]
    
    def test_get_resources(self):
        """Test getting all resources"""
        response = requests.get(
            f"{BASE_URL}/api/resources",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Get resources failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"Total resources: {len(data)}")
        
        # Validate resource structure if any exist
        if data:
            resource = data[0]
            assert "id" in resource
            assert "title" in resource
            assert "category" in resource
            assert "content" in resource
    
    def test_get_resources_by_category(self):
        """Test getting resources filtered by category"""
        response = requests.get(
            f"{BASE_URL}/api/resources?category=worksheet",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Get resources by category failed: {response.text}"
        data = response.json()
        
        # All returned resources should be worksheets
        for resource in data:
            assert resource["category"] == "worksheet"
        
        print(f"Worksheet resources: {len(data)}")
    
    def test_assign_resource_to_client(self):
        """Test assigning a resource to a client"""
        if not self.client_id:
            pytest.skip("No client available for testing")
        
        # First create a resource
        resource_data = {
            "title": "TEST_Mindfulness Exercise",
            "category": "meditation",
            "content": "A simple 5-minute breathing exercise for stress relief.",
            "tags": ["mindfulness", "breathing"],
            "is_downloadable": True
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/resources",
            headers=self.headers,
            json=resource_data
        )
        assert create_response.status_code == 200
        resource_id = create_response.json()["id"]
        
        # Assign to client
        assign_response = requests.post(
            f"{BASE_URL}/api/resources/{resource_id}/assign?client_id={self.client_id}",
            headers=self.headers
        )
        
        assert assign_response.status_code == 200, f"Assign resource failed: {assign_response.text}"
        data = assign_response.json()
        
        assert "assignment_id" in data
        assert data["message"] == "Resource assigned"
        
        print(f"Resource assigned: {data['assignment_id']}")
        
        # Verify usage count increased
        get_response = requests.get(f"{BASE_URL}/api/resources", headers=self.headers)
        resources = get_response.json()
        assigned_resource = next((r for r in resources if r["id"] == resource_id), None)
        assert assigned_resource is not None
        assert assigned_resource["usage_count"] >= 1
    
    def test_get_resource_assignments(self):
        """Test getting resource assignments"""
        response = requests.get(
            f"{BASE_URL}/api/resources/assignments",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Get assignments failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"Total assignments: {len(data)}")
        
        # Validate assignment structure if any exist
        if data:
            assignment = data[0]
            assert "id" in assignment
            assert "client_id" in assignment
            assert "resource_id" in assignment
            assert "status" in assignment
    
    def test_delete_resource(self):
        """Test deleting a resource"""
        # First create a resource to delete
        resource_data = {
            "title": "TEST_Resource to Delete",
            "category": "exercise",
            "content": "This resource will be deleted.",
            "tags": ["test"],
            "is_downloadable": False
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/resources",
            headers=self.headers,
            json=resource_data
        )
        assert create_response.status_code == 200
        resource_id = create_response.json()["id"]
        
        # Delete the resource
        delete_response = requests.delete(
            f"{BASE_URL}/api/resources/{resource_id}",
            headers=self.headers
        )
        
        assert delete_response.status_code == 200, f"Delete resource failed: {delete_response.text}"
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/resources", headers=self.headers)
        resources = get_response.json()
        deleted_resource = next((r for r in resources if r["id"] == resource_id), None)
        assert deleted_resource is None, "Resource should be deleted"
        
        print(f"Resource deleted: {resource_id}")


class TestAIEndpointsAuth:
    """Test AI endpoints require authentication"""
    
    def test_ai_suggest_assessments_no_auth(self):
        """Test AI suggest assessments without auth - should fail"""
        response = requests.post(
            f"{BASE_URL}/api/ai/suggest-assessments",
            json={"query": "test"}
        )
        assert response.status_code == 403, "Should require authentication"
    
    def test_ai_generate_protocol_no_auth(self):
        """Test AI generate protocol without auth - should fail"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-protocol",
            json={"query": "test"}
        )
        assert response.status_code == 403, "Should require authentication"
    
    def test_ai_generate_homework_no_auth(self):
        """Test AI generate homework without auth - should fail"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-homework",
            json={"client_id": "test"}
        )
        assert response.status_code == 403, "Should require authentication"
    
    def test_resources_no_auth(self):
        """Test resources endpoint without auth - should fail"""
        response = requests.get(f"{BASE_URL}/api/resources")
        assert response.status_code == 403, "Should require authentication"


# Cleanup test data
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_resources():
    """Cleanup TEST_ prefixed resources after all tests"""
    yield
    
    # Login and cleanup
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": THERAPIST_MOBILE,
        "password": THERAPIST_PASSWORD
    })
    if response.status_code == 200:
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all resources
        resources_response = requests.get(f"{BASE_URL}/api/resources", headers=headers)
        if resources_response.status_code == 200:
            for resource in resources_response.json():
                if resource["title"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/resources/{resource['id']}", headers=headers)
                    print(f"Cleaned up resource: {resource['title']}")
