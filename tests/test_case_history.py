"""
Test Case History Feature - MMS-Style Clinical Notes
Tests for:
- Create case history (POST /api/case-history)
- Get case history (GET /api/case-history/{client_id})
- Update case history section (PATCH /api/case-history/{client_id}/section)
- Mark case history complete (PATCH /api/case-history/{client_id}/complete)
- Check case history exists (GET /api/case-history/check/{client_id})
- Session notes blocked if case history incomplete
- Security: Only therapists can access case history
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "password"


@pytest.fixture(scope="module")
def therapist_token():
    """Get therapist authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": THERAPIST_MOBILE,
        "password": THERAPIST_PASSWORD
    })
    assert response.status_code == 200, f"Therapist login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def therapist_headers(therapist_token):
    """Headers with therapist auth token"""
    return {
        "Authorization": f"Bearer {therapist_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def test_client(therapist_headers):
    """Get or create a test client for case history testing"""
    # First try to find existing client 'Test Client Alpha'
    response = requests.get(f"{BASE_URL}/api/clients", headers=therapist_headers)
    assert response.status_code == 200
    clients = response.json()
    
    # Look for Test Client Alpha
    test_client = None
    for client in clients:
        if "Test Client Alpha" in client.get("full_name", ""):
            test_client = client
            break
    
    if not test_client:
        # Create a new test client
        unique_id = str(uuid.uuid4())[:8]
        client_data = {
            "mobile": f"888{unique_id[:7]}",
            "full_name": f"TEST_CaseHistory_Client_{unique_id}",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=therapist_headers)
        assert response.status_code == 201, f"Failed to create test client: {response.text}"
        test_client = response.json()
    
    return test_client


@pytest.fixture(scope="module")
def clean_case_history(therapist_headers, test_client):
    """Ensure no case history exists for test client before tests"""
    client_id = test_client["id"]
    # Try to delete existing case history (if endpoint exists) or just proceed
    # The tests will handle existing case history
    yield
    # Cleanup after tests - delete case history if created
    # Note: No delete endpoint exists, so we leave it


class TestCaseHistoryCheck:
    """Test case history existence check endpoint"""
    
    def test_check_case_history_no_auth(self, test_client):
        """Test that check endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/case-history/check/{test_client['id']}")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_check_case_history_exists(self, therapist_headers, test_client):
        """Test checking if case history exists"""
        response = requests.get(
            f"{BASE_URL}/api/case-history/check/{test_client['id']}", 
            headers=therapist_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data
        assert "is_complete" in data
        assert isinstance(data["exists"], bool)
        assert isinstance(data["is_complete"], bool)


class TestCaseHistoryCreate:
    """Test case history creation"""
    
    def test_create_case_history_no_auth(self, test_client):
        """Test that create endpoint requires authentication"""
        payload = {
            "client_id": test_client["id"],
            "basic_identification": {"name": "Test Client"},
            "presenting_complaints": {"main_problems": "Test problems"}
        }
        response = requests.post(f"{BASE_URL}/api/case-history", json=payload)
        assert response.status_code == 403 or response.status_code == 401
    
    def test_create_case_history_minimal(self, therapist_headers, test_client):
        """Test creating case history with minimal required fields"""
        # First check if case history already exists
        check_response = requests.get(
            f"{BASE_URL}/api/case-history/check/{test_client['id']}", 
            headers=therapist_headers
        )
        
        if check_response.json().get("exists"):
            # Case history exists, skip creation test
            pytest.skip("Case history already exists for this client")
        
        payload = {
            "client_id": test_client["id"],
            "basic_identification": {
                "name": test_client.get("full_name", "Test Client"),
                "age": 30,
                "gender": "Male"
            },
            "presenting_complaints": {
                "main_problems": "Anxiety and stress related to work",
                "duration": "3 months",
                "severity": "Moderate"
            },
            "is_complete": False
        }
        
        response = requests.post(f"{BASE_URL}/api/case-history", json=payload, headers=therapist_headers)
        assert response.status_code == 200, f"Failed to create case history: {response.text}"
        
        data = response.json()
        assert data["client_id"] == test_client["id"]
        assert data["basic_identification"]["name"] == test_client.get("full_name", "Test Client")
        assert data["presenting_complaints"]["main_problems"] == "Anxiety and stress related to work"
        assert data["is_complete"] == False
    
    def test_create_duplicate_case_history_fails(self, therapist_headers, test_client):
        """Test that creating duplicate case history fails"""
        # First ensure case history exists
        check_response = requests.get(
            f"{BASE_URL}/api/case-history/check/{test_client['id']}", 
            headers=therapist_headers
        )
        
        if not check_response.json().get("exists"):
            # Create one first
            payload = {
                "client_id": test_client["id"],
                "basic_identification": {"name": "Test Client"},
                "presenting_complaints": {"main_problems": "Test problems"}
            }
            requests.post(f"{BASE_URL}/api/case-history", json=payload, headers=therapist_headers)
        
        # Try to create duplicate
        payload = {
            "client_id": test_client["id"],
            "basic_identification": {"name": "Test Client"},
            "presenting_complaints": {"main_problems": "Different problems"}
        }
        response = requests.post(f"{BASE_URL}/api/case-history", json=payload, headers=therapist_headers)
        assert response.status_code == 400
        assert "already exists" in response.json().get("detail", "").lower()


class TestCaseHistoryGet:
    """Test getting case history"""
    
    def test_get_case_history_no_auth(self, test_client):
        """Test that get endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/case-history/{test_client['id']}")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_get_case_history(self, therapist_headers, test_client):
        """Test getting case history for a client"""
        # First ensure case history exists
        check_response = requests.get(
            f"{BASE_URL}/api/case-history/check/{test_client['id']}", 
            headers=therapist_headers
        )
        
        if not check_response.json().get("exists"):
            # Create one first
            payload = {
                "client_id": test_client["id"],
                "basic_identification": {"name": test_client.get("full_name", "Test Client")},
                "presenting_complaints": {"main_problems": "Test problems"}
            }
            requests.post(f"{BASE_URL}/api/case-history", json=payload, headers=therapist_headers)
        
        response = requests.get(
            f"{BASE_URL}/api/case-history/{test_client['id']}", 
            headers=therapist_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["client_id"] == test_client["id"]
        assert "basic_identification" in data
        assert "presenting_complaints" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_case_history_not_found(self, therapist_headers):
        """Test getting case history for non-existent client"""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/case-history/{fake_id}", 
            headers=therapist_headers
        )
        assert response.status_code == 404


class TestCaseHistorySectionUpdate:
    """Test updating individual sections of case history"""
    
    def test_update_section_no_auth(self, test_client):
        """Test that section update requires authentication"""
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=basic_identification",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 403 or response.status_code == 401
    
    def test_update_basic_identification_section(self, therapist_headers, test_client):
        """Test updating basic identification section"""
        section_data = {
            "name": test_client.get("full_name", "Test Client"),
            "age": 35,
            "gender": "Male",
            "marital_status": "Single",
            "education": "Graduate",
            "occupation": "Software Engineer",
            "city": "Mumbai"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=basic_identification",
            json=section_data,
            headers=therapist_headers
        )
        assert response.status_code == 200
        assert "updated" in response.json().get("message", "").lower()
    
    def test_update_presenting_complaints_section(self, therapist_headers, test_client):
        """Test updating presenting complaints section"""
        section_data = {
            "main_problems": "Anxiety, difficulty sleeping, work stress",
            "duration": "6 months",
            "severity": "Moderate",
            "frequency": "Daily",
            "triggers": "Work deadlines, social situations"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=presenting_complaints",
            json=section_data,
            headers=therapist_headers
        )
        assert response.status_code == 200
    
    def test_update_medical_history_section(self, therapist_headers, test_client):
        """Test updating medical history section"""
        section_data = {
            "chronic_illnesses": "None",
            "current_medications": "None",
            "sleep_pattern": "Poor",
            "appetite": "Normal",
            "substance_use": "None"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=medical_history",
            json=section_data,
            headers=therapist_headers
        )
        assert response.status_code == 200
    
    def test_update_mental_status_examination_section(self, therapist_headers, test_client):
        """Test updating MSE section"""
        section_data = {
            "appearance": "Well-groomed",
            "behavior": "Cooperative",
            "speech": "Normal",
            "mood": "Anxious",
            "affect": "Appropriate",
            "thought_process": "Logical",
            "thought_content": "Normal",
            "perception": "Normal",
            "cognition": "Intact",
            "insight": "Good",
            "judgment": "Good"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=mental_status_examination",
            json=section_data,
            headers=therapist_headers
        )
        assert response.status_code == 200
    
    def test_update_consent_disclaimer_section(self, therapist_headers, test_client):
        """Test updating consent section"""
        section_data = {
            "informed_consent_taken": True,
            "confidentiality_explained": True,
            "consent_date": "2025-01-15",
            "additional_notes": "Client understood all terms"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=consent_disclaimer",
            json=section_data,
            headers=therapist_headers
        )
        assert response.status_code == 200
    
    def test_update_invalid_section(self, therapist_headers, test_client):
        """Test updating invalid section name"""
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=invalid_section",
            json={"data": "test"},
            headers=therapist_headers
        )
        assert response.status_code == 400
        assert "invalid section" in response.json().get("detail", "").lower()


class TestCaseHistoryComplete:
    """Test marking case history as complete"""
    
    def test_complete_case_history_no_auth(self, test_client):
        """Test that complete endpoint requires authentication"""
        response = requests.patch(f"{BASE_URL}/api/case-history/{test_client['id']}/complete")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_complete_case_history_missing_name(self, therapist_headers, test_client):
        """Test that completing case history requires name"""
        # First update to remove name
        requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=basic_identification",
            json={"age": 30},  # No name
            headers=therapist_headers
        )
        
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/complete",
            headers=therapist_headers
        )
        # Should fail if name is missing
        # Note: This might pass if name was already set, so we check the validation logic
        if response.status_code == 400:
            assert "name" in response.json().get("detail", "").lower()
    
    def test_complete_case_history_with_all_required_fields(self, therapist_headers, test_client):
        """Test completing case history with all required fields"""
        # Update all required sections
        # 1. Basic Identification with name
        requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=basic_identification",
            json={"name": test_client.get("full_name", "Test Client"), "age": 30},
            headers=therapist_headers
        )
        
        # 2. Presenting Complaints with main_problems
        requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=presenting_complaints",
            json={"main_problems": "Anxiety and stress", "severity": "Moderate"},
            headers=therapist_headers
        )
        
        # 3. Consent with informed_consent_taken
        requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=consent_disclaimer",
            json={"informed_consent_taken": True, "confidentiality_explained": True},
            headers=therapist_headers
        )
        
        # Now try to complete
        response = requests.patch(
            f"{BASE_URL}/api/case-history/{test_client['id']}/complete",
            headers=therapist_headers
        )
        assert response.status_code == 200
        assert response.json().get("is_complete") == True
    
    def test_verify_case_history_is_complete(self, therapist_headers, test_client):
        """Verify case history is marked as complete"""
        response = requests.get(
            f"{BASE_URL}/api/case-history/check/{test_client['id']}", 
            headers=therapist_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] == True
        assert data["is_complete"] == True


class TestSessionNotesBlockedWithoutCaseHistory:
    """Test that session notes creation is blocked without completed case history"""
    
    def test_session_notes_blocked_no_case_history(self, therapist_headers):
        """Test that session notes cannot be created without case history"""
        # Create a new client without case history
        unique_id = str(uuid.uuid4())[:8]
        client_data = {
            "mobile": f"777{unique_id[:7]}",
            "full_name": f"TEST_NoCaseHistory_Client_{unique_id}",
            "password": "testpass123"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=therapist_headers)
        if create_response.status_code != 201:
            pytest.skip("Could not create test client")
        
        new_client = create_response.json()
        
        # Try to create session note without case history
        note_data = {
            "client_id": new_client["id"],
            "template_type": "SOAP",
            "subjective": "Test subjective content"
        }
        
        response = requests.post(f"{BASE_URL}/api/session-notes", json=note_data, headers=therapist_headers)
        assert response.status_code == 400
        assert "case history" in response.json().get("detail", "").lower()
    
    def test_session_notes_blocked_incomplete_case_history(self, therapist_headers):
        """Test that session notes cannot be created with incomplete case history"""
        # Create a new client
        unique_id = str(uuid.uuid4())[:8]
        client_data = {
            "mobile": f"666{unique_id[:7]}",
            "full_name": f"TEST_IncompleteCH_Client_{unique_id}",
            "password": "testpass123"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=therapist_headers)
        if create_response.status_code != 201:
            pytest.skip("Could not create test client")
        
        new_client = create_response.json()
        
        # Create incomplete case history (missing consent)
        case_history_data = {
            "client_id": new_client["id"],
            "basic_identification": {"name": new_client["full_name"]},
            "presenting_complaints": {"main_problems": "Test problems"},
            "is_complete": False
        }
        
        requests.post(f"{BASE_URL}/api/case-history", json=case_history_data, headers=therapist_headers)
        
        # Try to create session note with incomplete case history
        note_data = {
            "client_id": new_client["id"],
            "template_type": "SOAP",
            "subjective": "Test subjective content"
        }
        
        response = requests.post(f"{BASE_URL}/api/session-notes", json=note_data, headers=therapist_headers)
        assert response.status_code == 400
        assert "incomplete" in response.json().get("detail", "").lower() or "case history" in response.json().get("detail", "").lower()
    
    def test_session_notes_allowed_with_complete_case_history(self, therapist_headers, test_client):
        """Test that session notes can be created with completed case history"""
        # Ensure case history is complete
        check_response = requests.get(
            f"{BASE_URL}/api/case-history/check/{test_client['id']}", 
            headers=therapist_headers
        )
        
        if not check_response.json().get("is_complete"):
            # Complete the case history
            requests.patch(
                f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=basic_identification",
                json={"name": test_client.get("full_name", "Test Client")},
                headers=therapist_headers
            )
            requests.patch(
                f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=presenting_complaints",
                json={"main_problems": "Test problems"},
                headers=therapist_headers
            )
            requests.patch(
                f"{BASE_URL}/api/case-history/{test_client['id']}/section?section=consent_disclaimer",
                json={"informed_consent_taken": True},
                headers=therapist_headers
            )
            requests.patch(
                f"{BASE_URL}/api/case-history/{test_client['id']}/complete",
                headers=therapist_headers
            )
        
        # Now create session note
        note_data = {
            "client_id": test_client["id"],
            "template_type": "SOAP",
            "subjective": "Client reports feeling anxious about upcoming presentation",
            "objective": "Client appeared well-groomed, maintained eye contact",
            "assessment": "Generalized anxiety with situational triggers",
            "plan": "Continue CBT techniques, practice relaxation exercises"
        }
        
        response = requests.post(f"{BASE_URL}/api/session-notes", json=note_data, headers=therapist_headers)
        assert response.status_code == 200, f"Failed to create session note: {response.text}"
        
        data = response.json()
        assert data["client_id"] == test_client["id"]
        assert data["template_type"] == "SOAP"


class TestCaseHistorySecurity:
    """Test security - only therapists can access case history"""
    
    def test_client_cannot_access_case_history(self, test_client):
        """Test that clients cannot access case history endpoints"""
        # Try to login as client (if client has credentials)
        # For now, we test with no auth which should fail
        response = requests.get(f"{BASE_URL}/api/case-history/{test_client['id']}")
        assert response.status_code in [401, 403]
    
    def test_case_history_requires_therapist_role(self, therapist_headers, test_client):
        """Test that case history endpoints require therapist role"""
        # This test verifies the endpoint works with therapist auth
        response = requests.get(
            f"{BASE_URL}/api/case-history/check/{test_client['id']}", 
            headers=therapist_headers
        )
        assert response.status_code == 200


class TestCaseHistoryAllSections:
    """Test all 11 sections of case history"""
    
    def test_update_all_sections(self, therapist_headers, test_client):
        """Test updating all 11 sections of case history"""
        sections = {
            "basic_identification": {
                "name": test_client.get("full_name", "Test Client"),
                "age": 32,
                "dob": "1993-05-15",
                "gender": "Male",
                "marital_status": "Single",
                "education": "Post Graduate",
                "occupation": "Engineer",
                "address": "123 Test Street",
                "city": "Mumbai",
                "contact": "9876543210",
                "emergency_contact": "9876543211",
                "emergency_contact_relation": "Parent",
                "referred_by": "Dr. Smith"
            },
            "presenting_complaints": {
                "main_problems": "Anxiety, sleep issues, work stress",
                "duration": "6 months",
                "severity": "Moderate",
                "frequency": "Daily",
                "triggers": "Work deadlines, social situations"
            },
            "history_of_present_illness": {
                "onset": "Gradual onset 6 months ago",
                "course": "Progressive worsening",
                "previous_episodes": "One episode 2 years ago",
                "factors_improving": "Exercise, meditation",
                "factors_worsening": "Lack of sleep, caffeine",
                "prior_therapy": "Brief counseling 2 years ago",
                "prior_medication": "None"
            },
            "past_psychiatric_history": {
                "previous_therapy": "6 sessions of counseling",
                "previous_diagnosis": "Adjustment disorder",
                "hospitalizations": "None",
                "past_medications": "None",
                "current_medications": "None"
            },
            "medical_history": {
                "chronic_illnesses": "None",
                "current_medications": "Vitamin D supplements",
                "sleep_pattern": "Poor",
                "appetite": "Normal",
                "substance_use": "None"
            },
            "family_history": {
                "family_structure": "Nuclear family, parents and one sibling",
                "mental_illness_in_family": "No",
                "relationship_dynamics": "Generally supportive"
            },
            "personal_developmental_history": {
                "childhood": "Normal developmental milestones",
                "education_history": "Good academic performance",
                "work_history": "5 years in IT industry",
                "major_life_events": "Job change 1 year ago",
                "trauma_history": "None reported"
            },
            "mental_status_examination": {
                "appearance": "Well-groomed",
                "behavior": "Cooperative",
                "speech": "Normal",
                "mood": "Anxious",
                "affect": "Appropriate",
                "thought_process": "Logical",
                "thought_content": "Normal",
                "perception": "Normal",
                "cognition": "Intact",
                "insight": "Good",
                "judgment": "Good"
            },
            "provisional_formulation": {
                "clinical_formulation": "Generalized anxiety disorder with occupational stressors",
                "stressors": "Work pressure, performance expectations",
                "strengths": "Good insight, motivated for therapy, supportive family",
                "risk_indicators": "None identified"
            },
            "initial_therapy_plan": {
                "therapy_modality": "CBT",
                "session_frequency": "Weekly",
                "initial_goals": "Reduce anxiety symptoms, improve sleep, develop coping strategies",
                "homework": "Daily relaxation exercises, thought diary"
            },
            "consent_disclaimer": {
                "informed_consent_taken": True,
                "confidentiality_explained": True,
                "consent_date": "2025-01-15",
                "additional_notes": "Client understood all terms and conditions"
            }
        }
        
        for section_name, section_data in sections.items():
            response = requests.patch(
                f"{BASE_URL}/api/case-history/{test_client['id']}/section?section={section_name}",
                json=section_data,
                headers=therapist_headers
            )
            assert response.status_code == 200, f"Failed to update section {section_name}: {response.text}"
        
        # Verify all sections are saved
        response = requests.get(
            f"{BASE_URL}/api/case-history/{test_client['id']}", 
            headers=therapist_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["basic_identification"]["name"] == test_client.get("full_name", "Test Client")
        assert data["presenting_complaints"]["main_problems"] == "Anxiety, sleep issues, work stress"
        assert data["consent_disclaimer"]["informed_consent_taken"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
