"""
Assessment System Tests - TheraGenie Clinical Assessment Feature
Tests for: Assessment Library, Assignment, Client Taking Flow, Scoring, Sharing
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_CREDS = {"identifier": "9999999999", "password": "password"}
CLIENT_CREDS = {"identifier": "8888888888", "password": "testpass123"}


class TestAssessmentLibrary:
    """Test Assessment Library API - should return all 12 assessments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login as therapist
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        self.therapist_token = response.json()["token"]
        self.therapist_headers = {"Authorization": f"Bearer {self.therapist_token}"}
    
    def test_get_assessment_library(self):
        """Test GET /api/assessments/library returns all 12 assessments"""
        response = requests.get(f"{BASE_URL}/api/assessments/library", headers=self.therapist_headers)
        assert response.status_code == 200, f"Failed to get library: {response.text}"
        
        library = response.json()
        expected_assessments = [
            "PHQ-9", "GAD-7", "DASS-21", "WHO-5", "ASRS-v1.1", 
            "Y-BOCS", "HAM-A", "BDI-II", "BPRS", "ISI", "AUDIT", "RSES"
        ]
        
        for assessment_type in expected_assessments:
            assert assessment_type in library, f"Missing assessment: {assessment_type}"
            assert "name" in library[assessment_type], f"{assessment_type} missing name"
            assert "questions" in library[assessment_type], f"{assessment_type} missing questions"
            assert "severity_bands" in library[assessment_type], f"{assessment_type} missing severity_bands"
        
        print(f"✓ Assessment library contains all {len(expected_assessments)} assessments")
    
    def test_assessment_library_structure(self):
        """Test that each assessment has proper structure"""
        response = requests.get(f"{BASE_URL}/api/assessments/library", headers=self.therapist_headers)
        library = response.json()
        
        # Check PHQ-9 structure as example
        phq9 = library.get("PHQ-9")
        assert phq9 is not None, "PHQ-9 not found"
        assert phq9["name"] == "Patient Health Questionnaire-9"
        assert phq9["category"] == "Depression"
        assert len(phq9["questions"]) == 9, f"PHQ-9 should have 9 questions, got {len(phq9['questions'])}"
        assert phq9["max_score"] == 27
        
        # Check question structure
        q1 = phq9["questions"][0]
        assert "text" in q1
        assert "options" in q1
        assert len(q1["options"]) >= 2
        
        print("✓ Assessment structure is correct")


class TestAssessmentAssignment:
    """Test therapist assigning assessments to clients"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login as therapist
        response = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        self.therapist_token = response.json()["token"]
        self.therapist_headers = {"Authorization": f"Bearer {self.therapist_token}"}
        
        # Get clients
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers=self.therapist_headers)
        assert clients_res.status_code == 200
        self.clients = clients_res.data if hasattr(clients_res, 'data') else clients_res.json()
        
        # Get library
        lib_res = requests.get(f"{BASE_URL}/api/assessments/library", headers=self.therapist_headers)
        self.library = lib_res.json()
    
    def test_assign_assessment_to_client(self):
        """Test POST /api/assessments - assign assessment with optional due date"""
        # Get first client
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers=self.therapist_headers)
        clients = clients_res.json()
        
        if not clients:
            pytest.skip("No clients available for testing")
        
        client_id = clients[0]["id"]
        
        # Get PHQ-9 questions from library
        phq9 = self.library.get("PHQ-9")
        
        # Assign assessment
        assignment_data = {
            "client_id": client_id,
            "assessment_type": "PHQ-9",
            "questions": phq9["questions"],
            "is_custom": False,
            "due_date": "2025-12-31"
        }
        
        response = requests.post(f"{BASE_URL}/api/assessments", json=assignment_data, headers=self.therapist_headers)
        assert response.status_code == 200, f"Failed to assign assessment: {response.text}"
        
        result = response.json()
        assert result["status"] == "assigned"
        assert result["assessment_type"] == "PHQ-9"
        assert result["client_id"] == client_id
        assert result["due_date"] == "2025-12-31"
        
        self.assessment_id = result["id"]
        print(f"✓ Assessment assigned successfully: {self.assessment_id}")
        
        return result["id"]
    
    def test_get_therapist_assessments(self):
        """Test GET /api/assessments - therapist view"""
        response = requests.get(f"{BASE_URL}/api/assessments", headers=self.therapist_headers)
        assert response.status_code == 200
        
        assessments = response.json()
        assert isinstance(assessments, list)
        print(f"✓ Therapist can view {len(assessments)} assessments")


class TestClientAssessmentFlow:
    """Test client assessment taking flow - one question per screen, auto-save, submit"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login as therapist first to assign assessment
        therapist_res = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert therapist_res.status_code == 200
        self.therapist_token = therapist_res.json()["token"]
        self.therapist_headers = {"Authorization": f"Bearer {self.therapist_token}"}
        
        # Login as client
        client_res = requests.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
        assert client_res.status_code == 200, f"Client login failed: {client_res.text}"
        self.client_token = client_res.json()["token"]
        self.client_headers = {"Authorization": f"Bearer {self.client_token}"}
        self.client_id = client_res.json()["user"]["id"]
    
    def _assign_assessment_for_client(self, assessment_type="PHQ-9"):
        """Helper to assign an assessment to the test client"""
        # Get library
        lib_res = requests.get(f"{BASE_URL}/api/assessments/library", headers=self.therapist_headers)
        library = lib_res.json()
        assessment = library.get(assessment_type)
        
        assignment_data = {
            "client_id": self.client_id,
            "assessment_type": assessment_type,
            "questions": assessment["questions"],
            "is_custom": False
        }
        
        response = requests.post(f"{BASE_URL}/api/assessments", json=assignment_data, headers=self.therapist_headers)
        assert response.status_code == 200, f"Failed to assign: {response.text}"
        return response.json()["id"]
    
    def test_client_view_assigned_assessment(self):
        """Test GET /api/assessments/{id}/client-view - client-friendly format"""
        # Assign assessment
        assessment_id = self._assign_assessment_for_client("GAD-7")
        
        # Get client view
        response = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/client-view", headers=self.client_headers)
        assert response.status_code == 200, f"Failed to get client view: {response.text}"
        
        data = response.json()
        
        # Check client-friendly fields
        assert "friendly_name" in data, "Missing friendly_name"
        assert "purpose" in data, "Missing purpose"
        assert "instruction" in data, "Missing instruction"
        assert "questions" in data, "Missing questions"
        assert data["status"] == "assigned"
        
        # GAD-7 should have friendly name "Worry & Anxiety Check-In"
        assert data["friendly_name"] == "Worry & Anxiety Check-In", f"Wrong friendly name: {data['friendly_name']}"
        
        print(f"✓ Client sees friendly name: {data['friendly_name']}")
        print(f"✓ Purpose: {data['purpose']}")
        
        return assessment_id
    
    def test_client_save_progress(self):
        """Test POST /api/assessments/{id}/save-progress - auto-save"""
        assessment_id = self._assign_assessment_for_client("WHO-5")
        
        # Save partial progress
        progress_data = {
            "answers": [
                {"question_id": 1, "value": 3, "label": "More than half of the time"},
                {"question_id": 2, "value": 4, "label": "Most of the time"}
            ],
            "current_index": 2
        }
        
        response = requests.post(
            f"{BASE_URL}/api/assessments/{assessment_id}/save-progress",
            json=progress_data,
            headers=self.client_headers
        )
        assert response.status_code == 200, f"Failed to save progress: {response.text}"
        
        result = response.json()
        assert result["success"] == True
        
        # Verify progress was saved by getting client view
        view_res = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/client-view", headers=self.client_headers)
        view_data = view_res.json()
        
        assert len(view_data["saved_answers"]) == 2, "Saved answers not persisted"
        assert view_data["current_question_index"] == 2, "Current index not persisted"
        
        print("✓ Auto-save progress working correctly")
        
        return assessment_id
    
    def test_client_submit_assessment(self):
        """Test POST /api/assessments/{id}/submit-with-scoring - submit and score"""
        assessment_id = self._assign_assessment_for_client("PHQ-9")
        
        # Get questions to know how many answers needed
        view_res = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/client-view", headers=self.client_headers)
        questions = view_res.json()["questions"]
        
        # Create answers for all questions (PHQ-9 has 9 questions)
        answers = []
        for i, q in enumerate(questions):
            answers.append({
                "question_id": q["id"],
                "value": 1,  # "Several days" for all
                "label": "Several days"
            })
        
        # Submit
        response = requests.post(
            f"{BASE_URL}/api/assessments/{assessment_id}/submit-with-scoring",
            json={"answers": answers},
            headers=self.client_headers
        )
        assert response.status_code == 200, f"Failed to submit: {response.text}"
        
        result = response.json()
        assert result["success"] == True
        # Client should NOT see score
        assert "score" not in result or result.get("score") is None, "Score should not be shown to client"
        
        print("✓ Assessment submitted successfully")
        print(f"✓ Client sees: {result.get('message', 'Thank you message')}")
        
        return assessment_id
    
    def test_client_cannot_see_unshared_results(self):
        """Test that client cannot view results until therapist shares"""
        # Submit an assessment first
        assessment_id = self._assign_assessment_for_client("ISI")
        
        # Get questions
        view_res = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/client-view", headers=self.client_headers)
        questions = view_res.json()["questions"]
        
        # Submit with answers
        answers = [{"question_id": q["id"], "value": 2, "label": "Moderate"} for q in questions]
        requests.post(
            f"{BASE_URL}/api/assessments/{assessment_id}/submit-with-scoring",
            json={"answers": answers},
            headers=self.client_headers
        )
        
        # Try to view results as client (should fail - not shared)
        response = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/results", headers=self.client_headers)
        assert response.status_code == 403, f"Client should not see unshared results: {response.text}"
        
        print("✓ Client correctly blocked from viewing unshared results")
        
        return assessment_id


class TestTherapistResultsAndSharing:
    """Test therapist viewing results, adding notes, sharing/unsharing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login as therapist
        therapist_res = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert therapist_res.status_code == 200
        self.therapist_token = therapist_res.json()["token"]
        self.therapist_headers = {"Authorization": f"Bearer {self.therapist_token}"}
        
        # Login as client
        client_res = requests.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
        assert client_res.status_code == 200
        self.client_token = client_res.json()["token"]
        self.client_headers = {"Authorization": f"Bearer {self.client_token}"}
        self.client_id = client_res.json()["user"]["id"]
    
    def _create_completed_assessment(self, assessment_type="BDI-II"):
        """Helper to create and complete an assessment"""
        # Get library
        lib_res = requests.get(f"{BASE_URL}/api/assessments/library", headers=self.therapist_headers)
        library = lib_res.json()
        assessment = library.get(assessment_type)
        
        # Assign
        assignment_data = {
            "client_id": self.client_id,
            "assessment_type": assessment_type,
            "questions": assessment["questions"],
            "is_custom": False
        }
        assign_res = requests.post(f"{BASE_URL}/api/assessments", json=assignment_data, headers=self.therapist_headers)
        assessment_id = assign_res.json()["id"]
        
        # Submit as client
        answers = [{"question_id": q["id"], "value": 1, "label": "Mild"} for q in assessment["questions"]]
        requests.post(
            f"{BASE_URL}/api/assessments/{assessment_id}/submit-with-scoring",
            json={"answers": answers},
            headers=self.client_headers
        )
        
        return assessment_id
    
    def test_therapist_view_results(self):
        """Test GET /api/assessments/{id}/results - therapist sees full details"""
        assessment_id = self._create_completed_assessment("HAM-A")
        
        response = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/results", headers=self.therapist_headers)
        assert response.status_code == 200, f"Failed to get results: {response.text}"
        
        results = response.json()
        
        # Therapist should see full details
        assert "score" in results, "Missing score"
        assert "score_details" in results, "Missing score_details"
        assert "answers" in results, "Missing answers"
        assert "questions" in results, "Missing questions"
        assert "severity" in results.get("score_details", {}), "Missing severity in score_details"
        
        print(f"✓ Therapist sees score: {results['score']}")
        print(f"✓ Severity: {results['score_details'].get('severity', {}).get('label', 'N/A')}")
        
        return assessment_id
    
    def test_therapist_add_notes(self):
        """Test PUT /api/assessments/{id}/therapist-notes"""
        assessment_id = self._create_completed_assessment("AUDIT")
        
        notes_data = {"notes": "Client shows moderate symptoms. Recommend follow-up in 2 weeks."}
        
        response = requests.put(
            f"{BASE_URL}/api/assessments/{assessment_id}/therapist-notes",
            json=notes_data,
            headers=self.therapist_headers
        )
        assert response.status_code == 200, f"Failed to save notes: {response.text}"
        
        # Verify notes saved
        results_res = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/results", headers=self.therapist_headers)
        results = results_res.json()
        assert results.get("therapist_notes") == notes_data["notes"]
        
        print("✓ Therapist notes saved successfully")
        
        return assessment_id
    
    def test_share_and_unshare_report(self):
        """Test POST /api/assessments/{id}/share-report and unshare-report"""
        assessment_id = self._create_completed_assessment("RSES")
        
        # Share report
        share_res = requests.post(f"{BASE_URL}/api/assessments/{assessment_id}/share-report", headers=self.therapist_headers)
        assert share_res.status_code == 200, f"Failed to share: {share_res.text}"
        
        # Client should now be able to view
        client_results = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/results", headers=self.client_headers)
        assert client_results.status_code == 200, "Client should see shared results"
        
        client_data = client_results.json()
        assert "score" in client_data
        print(f"✓ Client can view shared report, score: {client_data['score']}")
        
        # Unshare report
        unshare_res = requests.post(f"{BASE_URL}/api/assessments/{assessment_id}/unshare-report", headers=self.therapist_headers)
        assert unshare_res.status_code == 200, f"Failed to unshare: {unshare_res.text}"
        
        # Client should no longer be able to view
        client_blocked = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/results", headers=self.client_headers)
        assert client_blocked.status_code == 403, "Client should be blocked after unshare"
        
        print("✓ Share/unshare working correctly")


class TestAssessmentScoring:
    """Test that scoring works correctly for different assessment types"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login as therapist
        therapist_res = requests.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        self.therapist_token = therapist_res.json()["token"]
        self.therapist_headers = {"Authorization": f"Bearer {self.therapist_token}"}
        
        # Login as client
        client_res = requests.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
        self.client_token = client_res.json()["token"]
        self.client_headers = {"Authorization": f"Bearer {self.client_token}"}
        self.client_id = client_res.json()["user"]["id"]
        
        # Get library
        lib_res = requests.get(f"{BASE_URL}/api/assessments/library", headers=self.therapist_headers)
        self.library = lib_res.json()
    
    def test_phq9_scoring(self):
        """Test PHQ-9 scoring - sum method"""
        assessment = self.library["PHQ-9"]
        
        # Assign
        assign_res = requests.post(f"{BASE_URL}/api/assessments", json={
            "client_id": self.client_id,
            "assessment_type": "PHQ-9",
            "questions": assessment["questions"],
            "is_custom": False
        }, headers=self.therapist_headers)
        assessment_id = assign_res.json()["id"]
        
        # Submit with all 2s (score = 18, Moderately Severe)
        answers = [{"question_id": q["id"], "value": 2, "label": "More than half the days"} for q in assessment["questions"]]
        requests.post(
            f"{BASE_URL}/api/assessments/{assessment_id}/submit-with-scoring",
            json={"answers": answers},
            headers=self.client_headers
        )
        
        # Check results
        results = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/results", headers=self.therapist_headers)
        data = results.json()
        
        assert data["score"] == 18, f"Expected score 18, got {data['score']}"
        assert data["score_details"]["severity"]["label"] == "Moderately Severe"
        
        print(f"✓ PHQ-9 scoring correct: {data['score']} = {data['score_details']['severity']['label']}")
    
    def test_dass21_subscale_scoring(self):
        """Test DASS-21 subscale scoring"""
        assessment = self.library["DASS-21"]
        
        # Assign
        assign_res = requests.post(f"{BASE_URL}/api/assessments", json={
            "client_id": self.client_id,
            "assessment_type": "DASS-21",
            "questions": assessment["questions"],
            "is_custom": False
        }, headers=self.therapist_headers)
        assessment_id = assign_res.json()["id"]
        
        # Submit with all 1s
        answers = [{"question_id": q["id"], "value": 1, "label": "Applied to me to some degree"} for q in assessment["questions"]]
        requests.post(
            f"{BASE_URL}/api/assessments/{assessment_id}/submit-with-scoring",
            json={"answers": answers},
            headers=self.client_headers
        )
        
        # Check results
        results = requests.get(f"{BASE_URL}/api/assessments/{assessment_id}/results", headers=self.therapist_headers)
        data = results.json()
        
        # DASS-21 should have subscores
        assert "subscores" in data["score_details"], "DASS-21 should have subscores"
        subscores = data["score_details"]["subscores"]
        
        assert "depression" in subscores, "Missing depression subscore"
        assert "anxiety" in subscores, "Missing anxiety subscore"
        assert "stress" in subscores, "Missing stress subscore"
        
        print(f"✓ DASS-21 subscores: Depression={subscores['depression']['score']}, Anxiety={subscores['anxiety']['score']}, Stress={subscores['stress']['score']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
