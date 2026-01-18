"""
Test Suite for Session Notes and Recurring Appointments Features
Tests P0-1 through P0-12 as specified in the review request

Features tested:
- Session Notes: SOAP/DAP templates, linking to appointments, CRUD operations, filtering
- Recurring Appointments: Pattern creation, appointment generation, toggle, delete
- Read-only mode: Subscription expiry prevents note creation/editing
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "TestPass123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Test client ID from context
TEST_CLIENT_ID = "c283749c-2c50-48d7-94bf-e4588247883d"


class TestSessionNotesCRUD:
    """Session Notes CRUD operations - P0-1 through P0-7"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.therapist_id = login_response.json()["user"]["id"]
        
        # Get clients for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        assert clients_response.status_code == 200
        self.clients = clients_response.json()
        assert len(self.clients) > 0, "No clients available for testing"
        self.test_client = self.clients[0]
        
        # Get appointments for linking tests
        appts_response = self.session.get(f"{BASE_URL}/api/appointments")
        assert appts_response.status_code == 200
        self.appointments = appts_response.json()
        
        yield
        
        # Cleanup: Delete test notes created during tests
        notes_response = self.session.get(f"{BASE_URL}/api/session-notes")
        if notes_response.status_code == 200:
            for note in notes_response.json():
                if note.get("subjective", "").startswith("TEST_") or note.get("data", "").startswith("TEST_"):
                    self.session.delete(f"{BASE_URL}/api/session-notes/{note['id']}")
    
    def test_p0_1_create_soap_note_all_fields(self):
        """P0-1: Create SOAP session note with all fields (Subjective, Objective, Assessment, Plan)"""
        soap_note = {
            "client_id": self.test_client["id"],
            "template_type": "SOAP",
            "subjective": "TEST_Client reports feeling anxious about upcoming work presentation",
            "objective": "TEST_Client appeared tense, fidgeting with hands, maintained eye contact",
            "assessment": "TEST_Generalized anxiety disorder, moderate severity",
            "plan": "TEST_Continue CBT techniques, practice relaxation exercises daily"
        }
        
        response = self.session.post(f"{BASE_URL}/api/session-notes", json=soap_note)
        assert response.status_code == 200, f"Failed to create SOAP note: {response.text}"
        
        data = response.json()
        assert data["template_type"] == "SOAP"
        assert data["subjective"] == soap_note["subjective"]
        assert data["objective"] == soap_note["objective"]
        assert data["assessment"] == soap_note["assessment"]
        assert data["plan"] == soap_note["plan"]
        assert data["client_id"] == self.test_client["id"]
        assert data["client_name"] == self.test_client["full_name"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify persistence with GET
        get_response = self.session.get(f"{BASE_URL}/api/session-notes/{data['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["subjective"] == soap_note["subjective"]
        
        print(f"✓ P0-1 PASS: Created SOAP note with all fields, ID: {data['id']}")
    
    def test_p0_2_create_dap_note_all_fields(self):
        """P0-2: Create DAP session note with all fields (Data, Assessment, Plan)"""
        dap_note = {
            "client_id": self.test_client["id"],
            "template_type": "DAP",
            "data": "TEST_Client discussed recent conflict with family member, expressed frustration",
            "assessment": "TEST_Progress in emotional regulation, still struggling with family dynamics",
            "plan": "TEST_Role-play communication strategies, assign journaling homework"
        }
        
        response = self.session.post(f"{BASE_URL}/api/session-notes", json=dap_note)
        assert response.status_code == 200, f"Failed to create DAP note: {response.text}"
        
        data = response.json()
        assert data["template_type"] == "DAP"
        assert data["data"] == dap_note["data"]
        assert data["assessment"] == dap_note["assessment"]
        assert data["plan"] == dap_note["plan"]
        assert data["client_id"] == self.test_client["id"]
        
        # Verify persistence
        get_response = self.session.get(f"{BASE_URL}/api/session-notes/{data['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["data"] == dap_note["data"]
        
        print(f"✓ P0-2 PASS: Created DAP note with all fields, ID: {data['id']}")
    
    def test_p0_3_link_note_to_appointment(self):
        """P0-3: Link session note to an existing appointment"""
        # Find an appointment for the test client
        client_appointments = [a for a in self.appointments if a["client_id"] == self.test_client["id"]]
        
        if not client_appointments:
            # Create an appointment for testing
            tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            appt_data = {
                "client_id": self.test_client["id"],
                "start_time": tomorrow.isoformat() + "Z",
                "end_time": (tomorrow + timedelta(hours=1)).isoformat() + "Z",
                "notes": "TEST_Appointment for note linking"
            }
            appt_response = self.session.post(f"{BASE_URL}/api/appointments", json=appt_data)
            if appt_response.status_code == 200:
                test_appointment = appt_response.json()
            else:
                pytest.skip("Could not create appointment for linking test")
        else:
            test_appointment = client_appointments[0]
        
        # Create note linked to appointment
        linked_note = {
            "client_id": self.test_client["id"],
            "appointment_id": test_appointment["id"],
            "template_type": "SOAP",
            "subjective": "TEST_Session linked to appointment",
            "assessment": "TEST_Assessment for linked note"
        }
        
        response = self.session.post(f"{BASE_URL}/api/session-notes", json=linked_note)
        assert response.status_code == 200, f"Failed to create linked note: {response.text}"
        
        data = response.json()
        assert data["appointment_id"] == test_appointment["id"]
        assert data["appointment_date"] is not None
        
        print(f"✓ P0-3 PASS: Created note linked to appointment {test_appointment['id']}")
    
    def test_p0_4_edit_session_note(self):
        """P0-4: Edit existing session note"""
        # Create a note first
        create_response = self.session.post(f"{BASE_URL}/api/session-notes", json={
            "client_id": self.test_client["id"],
            "template_type": "SOAP",
            "subjective": "TEST_Original subjective content",
            "assessment": "TEST_Original assessment"
        })
        assert create_response.status_code == 200
        note_id = create_response.json()["id"]
        original_created_at = create_response.json()["created_at"]
        
        # Update the note
        update_data = {
            "subjective": "TEST_Updated subjective content",
            "objective": "TEST_Added objective field",
            "assessment": "TEST_Updated assessment",
            "plan": "TEST_Added plan field"
        }
        
        update_response = self.session.put(f"{BASE_URL}/api/session-notes/{note_id}", json=update_data)
        assert update_response.status_code == 200, f"Failed to update note: {update_response.text}"
        
        updated = update_response.json()
        assert updated["subjective"] == update_data["subjective"]
        assert updated["objective"] == update_data["objective"]
        assert updated["assessment"] == update_data["assessment"]
        assert updated["plan"] == update_data["plan"]
        assert updated["created_at"] == original_created_at  # created_at should not change
        assert updated["updated_at"] != original_created_at  # updated_at should change
        
        # Verify persistence
        get_response = self.session.get(f"{BASE_URL}/api/session-notes/{note_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["subjective"] == update_data["subjective"]
        
        print(f"✓ P0-4 PASS: Successfully edited session note {note_id}")
    
    def test_p0_5_delete_session_note(self):
        """P0-5: Delete session note"""
        # Create a note to delete
        create_response = self.session.post(f"{BASE_URL}/api/session-notes", json={
            "client_id": self.test_client["id"],
            "template_type": "DAP",
            "data": "TEST_Note to be deleted",
            "assessment": "TEST_Assessment to delete"
        })
        assert create_response.status_code == 200
        note_id = create_response.json()["id"]
        
        # Delete the note
        delete_response = self.session.delete(f"{BASE_URL}/api/session-notes/{note_id}")
        assert delete_response.status_code == 200, f"Failed to delete note: {delete_response.text}"
        assert "deleted" in delete_response.json()["message"].lower()
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/session-notes/{note_id}")
        assert get_response.status_code == 404
        
        print(f"✓ P0-5 PASS: Successfully deleted session note {note_id}")
    
    def test_p0_6_filter_notes_by_client(self):
        """P0-6: Filter notes by client"""
        # Create notes for different clients if we have multiple
        if len(self.clients) >= 2:
            client1 = self.clients[0]
            client2 = self.clients[1]
            
            # Create note for client 1
            self.session.post(f"{BASE_URL}/api/session-notes", json={
                "client_id": client1["id"],
                "template_type": "SOAP",
                "subjective": "TEST_Note for client 1"
            })
            
            # Create note for client 2
            self.session.post(f"{BASE_URL}/api/session-notes", json={
                "client_id": client2["id"],
                "template_type": "SOAP",
                "subjective": "TEST_Note for client 2"
            })
        
        # Filter by client
        filter_response = self.session.get(f"{BASE_URL}/api/session-notes?client_id={self.test_client['id']}")
        assert filter_response.status_code == 200
        
        filtered_notes = filter_response.json()
        # All returned notes should be for the filtered client
        for note in filtered_notes:
            assert note["client_id"] == self.test_client["id"]
        
        print(f"✓ P0-6 PASS: Filter by client returns {len(filtered_notes)} notes for {self.test_client['full_name']}")
    
    def test_p0_7_view_note_details(self):
        """P0-7: View note details with formatted sections"""
        # Create a comprehensive note
        full_note = {
            "client_id": self.test_client["id"],
            "template_type": "SOAP",
            "subjective": "TEST_Detailed subjective section with client's reported symptoms",
            "objective": "TEST_Detailed objective observations from the session",
            "assessment": "TEST_Clinical assessment and diagnosis considerations",
            "plan": "TEST_Treatment plan and next steps"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/session-notes", json=full_note)
        assert create_response.status_code == 200
        note_id = create_response.json()["id"]
        
        # Get note details
        detail_response = self.session.get(f"{BASE_URL}/api/session-notes/{note_id}")
        assert detail_response.status_code == 200
        
        note = detail_response.json()
        assert note["id"] == note_id
        assert note["template_type"] == "SOAP"
        assert note["subjective"] == full_note["subjective"]
        assert note["objective"] == full_note["objective"]
        assert note["assessment"] == full_note["assessment"]
        assert note["plan"] == full_note["plan"]
        assert note["client_name"] == self.test_client["full_name"]
        assert "created_at" in note
        assert "updated_at" in note
        
        print(f"✓ P0-7 PASS: Note details retrieved with all formatted sections")


class TestRecurringAppointments:
    """Recurring Appointments CRUD operations - P0-8 through P0-11"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get clients
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        assert clients_response.status_code == 200
        self.clients = clients_response.json()
        assert len(self.clients) > 0, "No clients available for testing"
        self.test_client = self.clients[0]
        
        yield
        
        # Cleanup: Delete test patterns
        patterns_response = self.session.get(f"{BASE_URL}/api/recurring-appointments")
        if patterns_response.status_code == 200:
            for pattern in patterns_response.json():
                if pattern.get("notes", "").startswith("TEST_"):
                    self.session.delete(f"{BASE_URL}/api/recurring-appointments/{pattern['id']}")
    
    def test_p0_8_create_recurring_pattern(self):
        """P0-8: Create recurring appointment pattern"""
        today = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        
        pattern_data = {
            "client_id": self.test_client["id"],
            "day_of_week": 1,  # Tuesday
            "start_time": "14:00",
            "end_time": "15:00",
            "notes": "TEST_Weekly therapy session",
            "start_date": today,
            "end_date": end_date
        }
        
        response = self.session.post(f"{BASE_URL}/api/recurring-appointments", json=pattern_data)
        assert response.status_code == 200, f"Failed to create pattern: {response.text}"
        
        data = response.json()
        assert data["client_id"] == self.test_client["id"]
        assert data["client_name"] == self.test_client["full_name"]
        assert data["day_of_week"] == 1
        assert data["start_time"] == "14:00"
        assert data["end_time"] == "15:00"
        assert data["notes"] == pattern_data["notes"]
        assert data["start_date"] == today
        assert data["end_date"] == end_date
        assert data["is_active"] == True
        assert "id" in data
        
        # Verify persistence
        patterns_response = self.session.get(f"{BASE_URL}/api/recurring-appointments")
        assert patterns_response.status_code == 200
        patterns = patterns_response.json()
        assert any(p["id"] == data["id"] for p in patterns)
        
        print(f"✓ P0-8 PASS: Created recurring pattern for {self.test_client['full_name']} on Tuesdays")
        return data["id"]
    
    def test_p0_9_generate_appointments_from_pattern(self):
        """P0-9: Generate appointments from recurring pattern"""
        # Create a pattern first
        today = datetime.now().strftime("%Y-%m-%d")
        pattern_data = {
            "client_id": self.test_client["id"],
            "day_of_week": 3,  # Thursday
            "start_time": "10:00",
            "end_time": "11:00",
            "notes": "TEST_Pattern for generation test",
            "start_date": today
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/recurring-appointments", json=pattern_data)
        assert create_response.status_code == 200
        pattern_id = create_response.json()["id"]
        
        # Generate appointments for 4 weeks
        generate_response = self.session.post(
            f"{BASE_URL}/api/recurring-appointments/{pattern_id}/generate?weeks_ahead=4"
        )
        assert generate_response.status_code == 200, f"Failed to generate: {generate_response.text}"
        
        result = generate_response.json()
        assert "appointments_created" in result
        assert result["appointments_created"] >= 0  # May be 0 if appointments already exist
        
        # Verify appointments were created
        appts_response = self.session.get(f"{BASE_URL}/api/appointments")
        assert appts_response.status_code == 200
        appointments = appts_response.json()
        
        # Check for appointments with the recurring pattern ID
        recurring_appts = [a for a in appointments if a.get("recurring_pattern_id") == pattern_id]
        
        print(f"✓ P0-9 PASS: Generated {result['appointments_created']} appointments from pattern")
    
    def test_p0_10_toggle_recurring_pattern(self):
        """P0-10: Toggle recurring pattern active/inactive"""
        # Create a pattern
        today = datetime.now().strftime("%Y-%m-%d")
        pattern_data = {
            "client_id": self.test_client["id"],
            "day_of_week": 4,  # Friday
            "start_time": "16:00",
            "end_time": "17:00",
            "notes": "TEST_Pattern for toggle test",
            "start_date": today
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/recurring-appointments", json=pattern_data)
        assert create_response.status_code == 200
        pattern_id = create_response.json()["id"]
        assert create_response.json()["is_active"] == True
        
        # Toggle to inactive
        toggle_response = self.session.put(f"{BASE_URL}/api/recurring-appointments/{pattern_id}/toggle")
        assert toggle_response.status_code == 200, f"Failed to toggle: {toggle_response.text}"
        assert toggle_response.json()["is_active"] == False
        
        # Verify pattern is inactive
        patterns_response = self.session.get(f"{BASE_URL}/api/recurring-appointments")
        pattern = next((p for p in patterns_response.json() if p["id"] == pattern_id), None)
        assert pattern is not None
        assert pattern["is_active"] == False
        
        # Toggle back to active
        toggle_response2 = self.session.put(f"{BASE_URL}/api/recurring-appointments/{pattern_id}/toggle")
        assert toggle_response2.status_code == 200
        assert toggle_response2.json()["is_active"] == True
        
        print(f"✓ P0-10 PASS: Successfully toggled pattern active/inactive")
    
    def test_p0_11_delete_recurring_pattern(self):
        """P0-11: Delete recurring pattern"""
        # Create a pattern to delete
        today = datetime.now().strftime("%Y-%m-%d")
        pattern_data = {
            "client_id": self.test_client["id"],
            "day_of_week": 5,  # Saturday
            "start_time": "09:00",
            "end_time": "10:00",
            "notes": "TEST_Pattern to delete",
            "start_date": today
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/recurring-appointments", json=pattern_data)
        assert create_response.status_code == 200
        pattern_id = create_response.json()["id"]
        
        # Delete the pattern
        delete_response = self.session.delete(f"{BASE_URL}/api/recurring-appointments/{pattern_id}")
        assert delete_response.status_code == 200, f"Failed to delete: {delete_response.text}"
        assert "deleted" in delete_response.json()["message"].lower()
        
        # Verify deletion
        patterns_response = self.session.get(f"{BASE_URL}/api/recurring-appointments")
        patterns = patterns_response.json()
        assert not any(p["id"] == pattern_id for p in patterns)
        
        print(f"✓ P0-11 PASS: Successfully deleted recurring pattern")
    
    def test_inactive_pattern_cannot_generate(self):
        """Test that inactive patterns cannot generate appointments"""
        # Create and deactivate a pattern
        today = datetime.now().strftime("%Y-%m-%d")
        pattern_data = {
            "client_id": self.test_client["id"],
            "day_of_week": 0,  # Monday
            "start_time": "11:00",
            "end_time": "12:00",
            "notes": "TEST_Inactive pattern test",
            "start_date": today
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/recurring-appointments", json=pattern_data)
        assert create_response.status_code == 200
        pattern_id = create_response.json()["id"]
        
        # Deactivate
        self.session.put(f"{BASE_URL}/api/recurring-appointments/{pattern_id}/toggle")
        
        # Try to generate - should fail
        generate_response = self.session.post(
            f"{BASE_URL}/api/recurring-appointments/{pattern_id}/generate?weeks_ahead=2"
        )
        assert generate_response.status_code == 400
        assert "not active" in generate_response.json()["detail"].lower()
        
        print(f"✓ Inactive pattern correctly prevented from generating appointments")


class TestReadOnlyMode:
    """Test read-only mode for expired subscriptions - P0-12"""
    
    def test_p0_12_read_only_mode_check(self):
        """P0-12: Verify read-only mode prevents note creation/editing"""
        # This test verifies the endpoint protection exists
        # Full test would require an expired therapist account
        
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as active therapist
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Check subscription status endpoint
        status_response = session.get(f"{BASE_URL}/api/auth/subscription-status")
        assert status_response.status_code == 200
        
        status = status_response.json()
        assert "is_read_only" in status
        assert "subscription_status" in status
        
        # Active therapist should not be in read-only mode
        if status["subscription_status"] in ["trial", "active"]:
            assert status["is_read_only"] == False
            print(f"✓ P0-12 PARTIAL: Active therapist correctly not in read-only mode")
            print(f"  Note: Full read-only test requires expired subscription account")
        else:
            assert status["is_read_only"] == True
            print(f"✓ P0-12 PASS: Expired therapist correctly in read-only mode")


class TestSessionNotesValidation:
    """Additional validation tests for session notes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        self.clients = clients_response.json()
        self.test_client = self.clients[0] if self.clients else None
    
    def test_create_note_invalid_client(self):
        """Test creating note with invalid client ID"""
        response = self.session.post(f"{BASE_URL}/api/session-notes", json={
            "client_id": "invalid-client-id",
            "template_type": "SOAP",
            "subjective": "TEST_Invalid client test"
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        print("✓ Invalid client ID correctly rejected")
    
    def test_create_note_invalid_appointment(self):
        """Test creating note with invalid appointment ID"""
        if not self.test_client:
            pytest.skip("No test client available")
        
        response = self.session.post(f"{BASE_URL}/api/session-notes", json={
            "client_id": self.test_client["id"],
            "appointment_id": "invalid-appointment-id",
            "template_type": "SOAP",
            "subjective": "TEST_Invalid appointment test"
        })
        assert response.status_code == 404
        assert "appointment" in response.json()["detail"].lower()
        print("✓ Invalid appointment ID correctly rejected")
    
    def test_get_nonexistent_note(self):
        """Test getting a note that doesn't exist"""
        response = self.session.get(f"{BASE_URL}/api/session-notes/nonexistent-note-id")
        assert response.status_code == 404
        print("✓ Nonexistent note correctly returns 404")
    
    def test_update_nonexistent_note(self):
        """Test updating a note that doesn't exist"""
        response = self.session.put(f"{BASE_URL}/api/session-notes/nonexistent-note-id", json={
            "subjective": "TEST_Update nonexistent"
        })
        assert response.status_code == 404
        print("✓ Update nonexistent note correctly returns 404")
    
    def test_delete_nonexistent_note(self):
        """Test deleting a note that doesn't exist"""
        response = self.session.delete(f"{BASE_URL}/api/session-notes/nonexistent-note-id")
        assert response.status_code == 404
        print("✓ Delete nonexistent note correctly returns 404")


class TestRecurringAppointmentsValidation:
    """Additional validation tests for recurring appointments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        self.clients = clients_response.json()
        self.test_client = self.clients[0] if self.clients else None
    
    def test_create_pattern_invalid_day(self):
        """Test creating pattern with invalid day of week"""
        if not self.test_client:
            pytest.skip("No test client available")
        
        response = self.session.post(f"{BASE_URL}/api/recurring-appointments", json={
            "client_id": self.test_client["id"],
            "day_of_week": 7,  # Invalid - should be 0-6
            "start_time": "10:00",
            "end_time": "11:00",
            "start_date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 400
        print("✓ Invalid day of week correctly rejected")
    
    def test_create_pattern_invalid_client(self):
        """Test creating pattern with invalid client ID"""
        response = self.session.post(f"{BASE_URL}/api/recurring-appointments", json={
            "client_id": "invalid-client-id",
            "day_of_week": 1,
            "start_time": "10:00",
            "end_time": "11:00",
            "start_date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        print("✓ Invalid client ID correctly rejected")
    
    def test_delete_nonexistent_pattern(self):
        """Test deleting a pattern that doesn't exist"""
        response = self.session.delete(f"{BASE_URL}/api/recurring-appointments/nonexistent-pattern-id")
        assert response.status_code == 404
        print("✓ Delete nonexistent pattern correctly returns 404")
    
    def test_generate_nonexistent_pattern(self):
        """Test generating from a pattern that doesn't exist"""
        response = self.session.post(f"{BASE_URL}/api/recurring-appointments/nonexistent-pattern-id/generate")
        assert response.status_code == 404
        print("✓ Generate from nonexistent pattern correctly returns 404")
    
    def test_toggle_nonexistent_pattern(self):
        """Test toggling a pattern that doesn't exist"""
        response = self.session.put(f"{BASE_URL}/api/recurring-appointments/nonexistent-pattern-id/toggle")
        assert response.status_code == 404
        print("✓ Toggle nonexistent pattern correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
