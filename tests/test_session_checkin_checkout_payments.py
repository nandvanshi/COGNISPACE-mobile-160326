"""
Test Session Check-In/Check-Out workflow with payment capture and PDF receipt generation.

Features tested:
1. POST /api/appointments/{id}/check-in - Changes status to 'in_progress', records actual_start_time
2. POST /api/appointments/{id}/check-out - Changes status to 'completed', records actual_end_time, calculates duration
3. POST /api/appointments/{id}/check-out with record_payment=true - Creates linked payment with bill_number
4. POST /api/payments - Therapist can record payment with all new fields
5. POST /api/payments - Assistant can record payment (not just therapist)
6. GET /api/payments - Client can view their own payments
7. GET /api/payments/{id}/receipt - Returns PaymentReceipt with all fields
8. GET /api/payments/{id}/receipt - Client can access their own receipt
9. Bill number format BILL-YYYYMMDD-XXXX is generated correctly
"""

import pytest
import requests
import os
import re
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_CREDS = {"identifier": "9999999999", "password": "password"}
CLIENT_CREDS = {"identifier": "8888888888", "password": "testpass123"}


class TestSessionCheckInCheckOut:
    """Test Check-In/Check-Out workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        data = response.json()
        self.therapist_token = data["token"]
        self.therapist_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.therapist_token}"})
        
        # Get a client for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        assert clients_response.status_code == 200
        clients = clients_response.json()
        assert len(clients) > 0, "No clients found for testing"
        self.test_client = clients[0]
        self.test_client_id = self.test_client["id"]
        
        yield
        
        # Cleanup - no specific cleanup needed as we create new appointments
    
    def create_test_appointment(self):
        """Helper to create a new scheduled appointment for testing"""
        # Create appointment for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        appointment_data = {
            "client_id": self.test_client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": f"Test appointment for check-in/check-out testing - {uuid.uuid4()}"
        }
        
        response = self.session.post(f"{BASE_URL}/api/appointments", json=appointment_data)
        assert response.status_code == 200, f"Failed to create appointment: {response.text}"
        return response.json()
    
    def test_check_in_changes_status_to_in_progress(self):
        """POST /api/appointments/{id}/check-in - Changes status to 'in_progress'"""
        # Create a new appointment
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Verify initial status is scheduled
        assert appointment["status"] == "scheduled", f"Expected scheduled, got {appointment['status']}"
        
        # Check in
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={
            "notes": "Test check-in notes"
        })
        assert response.status_code == 200, f"Check-in failed: {response.text}"
        
        result = response.json()
        assert result["status"] == "in_progress", f"Expected in_progress, got {result['status']}"
        print(f"✓ Check-in changed status to in_progress")
    
    def test_check_in_records_actual_start_time(self):
        """POST /api/appointments/{id}/check-in - Records actual_start_time"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Check in
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        assert response.status_code == 200
        
        result = response.json()
        assert result.get("actual_start_time") is not None, "actual_start_time not recorded"
        
        # Verify it's a valid datetime
        actual_start = result["actual_start_time"]
        assert isinstance(actual_start, str), "actual_start_time should be a string"
        print(f"✓ Check-in recorded actual_start_time: {actual_start}")
    
    def test_check_in_records_checked_in_by(self):
        """POST /api/appointments/{id}/check-in - Records who checked in"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        assert response.status_code == 200
        
        result = response.json()
        assert result.get("checked_in_by") == self.therapist_id, "checked_in_by not recorded correctly"
        print(f"✓ Check-in recorded checked_in_by: {result['checked_in_by']}")
    
    def test_cannot_check_in_cancelled_appointment(self):
        """Cannot check-in to a cancelled appointment"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Cancel the appointment
        cancel_response = self.session.put(f"{BASE_URL}/api/appointments/{appointment_id}", json={
            "status": "cancelled"
        })
        assert cancel_response.status_code == 200
        
        # Try to check in
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "cancelled" in response.json().get("detail", "").lower()
        print(f"✓ Cannot check-in to cancelled appointment")
    
    def test_check_out_changes_status_to_completed(self):
        """POST /api/appointments/{id}/check-out - Changes status to 'completed'"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Check in first
        self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        
        # Check out
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={
            "notes": "Test check-out notes"
        })
        assert response.status_code == 200, f"Check-out failed: {response.text}"
        
        result = response.json()
        assert result["status"] == "completed", f"Expected completed, got {result['status']}"
        print(f"✓ Check-out changed status to completed")
    
    def test_check_out_records_actual_end_time(self):
        """POST /api/appointments/{id}/check-out - Records actual_end_time"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Check in first
        self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        
        # Check out
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={})
        assert response.status_code == 200
        
        result = response.json()
        assert result.get("actual_end_time") is not None, "actual_end_time not recorded"
        print(f"✓ Check-out recorded actual_end_time: {result['actual_end_time']}")
    
    def test_check_out_calculates_duration(self):
        """POST /api/appointments/{id}/check-out - Calculates duration"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Check in first
        self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        
        # Wait a moment then check out
        import time
        time.sleep(1)
        
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={})
        assert response.status_code == 200
        
        result = response.json()
        assert result.get("actual_duration_minutes") is not None, "actual_duration_minutes not calculated"
        assert isinstance(result["actual_duration_minutes"], int), "Duration should be an integer"
        print(f"✓ Check-out calculated duration: {result['actual_duration_minutes']} minutes")
    
    def test_cannot_check_out_without_check_in(self):
        """Cannot check-out without checking in first"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Try to check out without checking in
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={})
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "check-in" in response.json().get("detail", "").lower()
        print(f"✓ Cannot check-out without check-in first")
    
    def test_check_out_with_payment_creates_payment(self):
        """POST /api/appointments/{id}/check-out with record_payment=true - Creates linked payment"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Check in first
        self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        
        # Check out with payment
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={
            "notes": "Session completed",
            "record_payment": True,
            "payment_amount": 1500.00,
            "payment_mode": "upi",
            "payment_status": "paid",
            "payment_notes": "Payment via UPI"
        })
        assert response.status_code == 200, f"Check-out with payment failed: {response.text}"
        
        result = response.json()
        assert result.get("payment") is not None, "Payment not created"
        
        payment = result["payment"]
        assert payment.get("amount") == 1500.00, f"Expected amount 1500, got {payment.get('amount')}"
        assert payment.get("payment_method") == "upi", f"Expected upi, got {payment.get('payment_method')}"
        assert payment.get("payment_status") == "paid", f"Expected paid, got {payment.get('payment_status')}"
        assert payment.get("bill_number") is not None, "bill_number not generated"
        assert payment.get("appointment_id") == appointment_id, "Payment not linked to appointment"
        print(f"✓ Check-out with payment created payment with bill_number: {payment['bill_number']}")
    
    def test_bill_number_format(self):
        """Bill number format BILL-YYYYMMDD-XXXX is generated correctly"""
        appointment = self.create_test_appointment()
        appointment_id = appointment["id"]
        
        # Check in and out with payment
        self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={
            "record_payment": True,
            "payment_amount": 1000.00,
            "payment_mode": "cash",
            "payment_status": "paid"
        })
        assert response.status_code == 200
        
        result = response.json()
        bill_number = result["payment"]["bill_number"]
        
        # Verify format: BILL-YYYYMMDD-XXXX
        pattern = r"^BILL-\d{8}-\d{4}$"
        assert re.match(pattern, bill_number), f"Bill number format incorrect: {bill_number}"
        
        # Verify date part is today
        today = datetime.now().strftime("%Y%m%d")
        assert today in bill_number, f"Bill number should contain today's date: {bill_number}"
        print(f"✓ Bill number format correct: {bill_number}")


class TestPaymentEndpoints:
    """Test Payment CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200, f"Therapist login failed: {response.text}"
        data = response.json()
        self.therapist_token = data["token"]
        self.therapist_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.therapist_token}"})
        
        # Get a client for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        assert clients_response.status_code == 200
        clients = clients_response.json()
        assert len(clients) > 0, "No clients found for testing"
        self.test_client = clients[0]
        self.test_client_id = self.test_client["id"]
        
        yield
    
    def test_therapist_can_record_payment(self):
        """POST /api/payments - Therapist can record payment with all new fields"""
        payment_data = {
            "client_id": self.test_client_id,
            "amount": 2000.00,
            "payment_method": "card",
            "payment_status": "paid",
            "notes": "Test payment by therapist"
        }
        
        response = self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
        assert response.status_code == 200, f"Failed to record payment: {response.text}"
        
        result = response.json()
        assert result.get("amount") == 2000.00
        assert result.get("payment_method") == "card"
        assert result.get("payment_status") == "paid"
        assert result.get("bill_number") is not None
        assert result.get("therapist_id") == self.therapist_id
        assert result.get("client_id") == self.test_client_id
        print(f"✓ Therapist recorded payment: {result['bill_number']}")
        
        return result["id"]
    
    def test_payment_modes(self):
        """Test all payment modes: cash, upi, card, bank, other"""
        modes = ["cash", "upi", "card", "bank", "other"]
        
        for mode in modes:
            payment_data = {
                "client_id": self.test_client_id,
                "amount": 500.00,
                "payment_method": mode,
                "payment_status": "paid"
            }
            
            response = self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
            assert response.status_code == 200, f"Failed to record {mode} payment: {response.text}"
            
            result = response.json()
            assert result.get("payment_method") == mode
            print(f"✓ Payment mode '{mode}' works correctly")
    
    def test_payment_statuses(self):
        """Test all payment statuses: paid, partial, pending"""
        statuses = ["paid", "partial", "pending"]
        
        for status in statuses:
            payment_data = {
                "client_id": self.test_client_id,
                "amount": 500.00,
                "payment_method": "cash",
                "payment_status": status
            }
            
            response = self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
            assert response.status_code == 200, f"Failed to record {status} payment: {response.text}"
            
            result = response.json()
            assert result.get("payment_status") == status
            print(f"✓ Payment status '{status}' works correctly")
    
    def test_get_payments_by_client(self):
        """GET /api/payments?client_id= - Get payments for a specific client"""
        # First create a payment
        payment_data = {
            "client_id": self.test_client_id,
            "amount": 1000.00,
            "payment_method": "cash",
            "payment_status": "paid"
        }
        self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
        
        # Get payments for client
        response = self.session.get(f"{BASE_URL}/api/payments?client_id={self.test_client_id}")
        assert response.status_code == 200
        
        payments = response.json()
        assert isinstance(payments, list)
        assert len(payments) > 0, "No payments found for client"
        
        # Verify all payments belong to the client
        for payment in payments:
            assert payment.get("client_id") == self.test_client_id
        
        print(f"✓ Retrieved {len(payments)} payments for client")


class TestAssistantPaymentAccess:
    """Test that assistants can record payments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist first to create assistant if needed
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        data = response.json()
        self.therapist_token = data["token"]
        self.therapist_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.therapist_token}"})
        
        # Get a client for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        assert clients_response.status_code == 200
        clients = clients_response.json()
        assert len(clients) > 0, "No clients found for testing"
        self.test_client = clients[0]
        self.test_client_id = self.test_client["id"]
        
        # Check if test assistant exists, create if not
        self.assistant_email = "test_assistant_payments@test.com"
        self.assistant_password = "testpass123"
        
        # Try to get existing assistants
        assistants_response = self.session.get(f"{BASE_URL}/api/assistants")
        if assistants_response.status_code == 200:
            assistants = assistants_response.json()
            existing = [a for a in assistants if a.get("email") == self.assistant_email]
            if existing:
                self.assistant_id = existing[0]["id"]
            else:
                # Create assistant
                create_response = self.session.post(f"{BASE_URL}/api/assistants", json={
                    "email": self.assistant_email,
                    "password": self.assistant_password,
                    "full_name": "Test Assistant Payments"
                })
                if create_response.status_code == 200:
                    self.assistant_id = create_response.json()["id"]
                else:
                    pytest.skip("Could not create assistant for testing")
        
        yield
    
    def test_assistant_can_record_payment(self):
        """POST /api/payments - Assistant can record payment"""
        # Login as assistant
        assistant_session = requests.Session()
        assistant_session.headers.update({"Content-Type": "application/json"})
        
        login_response = assistant_session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": self.assistant_email,
            "password": self.assistant_password
        })
        
        if login_response.status_code != 200:
            pytest.skip("Assistant login failed - may not exist")
        
        assistant_token = login_response.json()["token"]
        assistant_session.headers.update({"Authorization": f"Bearer {assistant_token}"})
        
        # Record payment as assistant
        payment_data = {
            "client_id": self.test_client_id,
            "amount": 1500.00,
            "payment_method": "upi",
            "payment_status": "paid",
            "notes": "Payment recorded by assistant"
        }
        
        response = assistant_session.post(f"{BASE_URL}/api/payments", json=payment_data)
        assert response.status_code == 200, f"Assistant failed to record payment: {response.text}"
        
        result = response.json()
        assert result.get("amount") == 1500.00
        assert result.get("bill_number") is not None
        print(f"✓ Assistant recorded payment: {result['bill_number']}")
    
    def test_assistant_can_check_in_appointment(self):
        """POST /api/appointments/{id}/check-in - Assistant can check-in"""
        # Login as assistant
        assistant_session = requests.Session()
        assistant_session.headers.update({"Content-Type": "application/json"})
        
        login_response = assistant_session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": self.assistant_email,
            "password": self.assistant_password
        })
        
        if login_response.status_code != 200:
            pytest.skip("Assistant login failed - may not exist")
        
        assistant_token = login_response.json()["token"]
        assistant_session.headers.update({"Authorization": f"Bearer {assistant_token}"})
        
        # Create appointment as therapist
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        self.session.headers.update({"Authorization": f"Bearer {self.therapist_token}"})
        create_response = self.session.post(f"{BASE_URL}/api/appointments", json={
            "client_id": self.test_client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "Test appointment for assistant check-in"
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create appointment")
        
        appointment_id = create_response.json()["id"]
        
        # Check in as assistant
        response = assistant_session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        assert response.status_code == 200, f"Assistant check-in failed: {response.text}"
        
        result = response.json()
        assert result["status"] == "in_progress"
        print(f"✓ Assistant checked in appointment")
    
    def test_assistant_can_check_out_with_payment(self):
        """POST /api/appointments/{id}/check-out - Assistant can check-out with payment"""
        # Login as assistant
        assistant_session = requests.Session()
        assistant_session.headers.update({"Content-Type": "application/json"})
        
        login_response = assistant_session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": self.assistant_email,
            "password": self.assistant_password
        })
        
        if login_response.status_code != 200:
            pytest.skip("Assistant login failed - may not exist")
        
        assistant_token = login_response.json()["token"]
        assistant_session.headers.update({"Authorization": f"Bearer {assistant_token}"})
        
        # Create and check-in appointment as therapist
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        self.session.headers.update({"Authorization": f"Bearer {self.therapist_token}"})
        create_response = self.session.post(f"{BASE_URL}/api/appointments", json={
            "client_id": self.test_client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "Test appointment for assistant check-out"
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create appointment")
        
        appointment_id = create_response.json()["id"]
        
        # Check in as assistant
        assistant_session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        
        # Check out with payment as assistant
        response = assistant_session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={
            "record_payment": True,
            "payment_amount": 2000.00,
            "payment_mode": "card",
            "payment_status": "paid",
            "payment_notes": "Payment recorded by assistant at checkout"
        })
        assert response.status_code == 200, f"Assistant check-out failed: {response.text}"
        
        result = response.json()
        assert result["status"] == "completed"
        assert result.get("payment") is not None
        assert result["payment"]["amount"] == 2000.00
        print(f"✓ Assistant checked out with payment: {result['payment']['bill_number']}")


class TestClientPaymentAccess:
    """Test that clients can view their own payments and receipts"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist first to create a payment
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        data = response.json()
        self.therapist_token = data["token"]
        self.therapist_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.therapist_token}"})
        
        # Get the test client's user ID
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        assert clients_response.status_code == 200
        clients = clients_response.json()
        
        # Find client with mobile 8888888888
        self.test_client = None
        for client in clients:
            if client.get("mobile") == "8888888888":
                self.test_client = client
                break
        
        if not self.test_client:
            pytest.skip("Test client 8888888888 not found")
        
        self.test_client_id = self.test_client["id"]
        
        # Create a payment for the client
        payment_data = {
            "client_id": self.test_client_id,
            "amount": 3000.00,
            "payment_method": "bank",
            "payment_status": "paid",
            "notes": "Test payment for client access testing"
        }
        
        payment_response = self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
        if payment_response.status_code == 200:
            self.test_payment_id = payment_response.json()["id"]
        else:
            self.test_payment_id = None
        
        yield
    
    def test_client_can_view_own_payments(self):
        """GET /api/payments - Client can view their own payments"""
        # Login as client
        client_session = requests.Session()
        client_session.headers.update({"Content-Type": "application/json"})
        
        login_response = client_session.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
        
        if login_response.status_code != 200:
            pytest.skip("Client login failed")
        
        client_token = login_response.json()["token"]
        client_session.headers.update({"Authorization": f"Bearer {client_token}"})
        
        # Get payments
        response = client_session.get(f"{BASE_URL}/api/payments")
        assert response.status_code == 200, f"Client failed to get payments: {response.text}"
        
        payments = response.json()
        assert isinstance(payments, list)
        print(f"✓ Client can view {len(payments)} payments")
    
    def test_client_can_access_own_receipt(self):
        """GET /api/payments/{id}/receipt - Client can access their own receipt"""
        if not self.test_payment_id:
            pytest.skip("No test payment created")
        
        # Login as client
        client_session = requests.Session()
        client_session.headers.update({"Content-Type": "application/json"})
        
        login_response = client_session.post(f"{BASE_URL}/api/auth/login", json=CLIENT_CREDS)
        
        if login_response.status_code != 200:
            pytest.skip("Client login failed")
        
        client_token = login_response.json()["token"]
        client_session.headers.update({"Authorization": f"Bearer {client_token}"})
        
        # Get receipt
        response = client_session.get(f"{BASE_URL}/api/payments/{self.test_payment_id}/receipt")
        assert response.status_code == 200, f"Client failed to get receipt: {response.text}"
        
        receipt = response.json()
        assert receipt.get("bill_number") is not None
        assert receipt.get("client_name") is not None
        assert receipt.get("amount") == 3000.00
        print(f"✓ Client can access receipt: {receipt['bill_number']}")


class TestPaymentReceipt:
    """Test Payment Receipt endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as therapist
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=THERAPIST_CREDS)
        assert response.status_code == 200
        data = response.json()
        self.therapist_token = data["token"]
        self.therapist_id = data["user"]["id"]
        self.session.headers.update({"Authorization": f"Bearer {self.therapist_token}"})
        
        # Get a client for testing
        clients_response = self.session.get(f"{BASE_URL}/api/clients")
        assert clients_response.status_code == 200
        clients = clients_response.json()
        assert len(clients) > 0
        self.test_client = clients[0]
        self.test_client_id = self.test_client["id"]
        
        yield
    
    def test_receipt_contains_all_required_fields(self):
        """GET /api/payments/{id}/receipt - Returns PaymentReceipt with all fields"""
        # Create a payment
        payment_data = {
            "client_id": self.test_client_id,
            "amount": 2500.00,
            "payment_method": "upi",
            "payment_status": "paid",
            "notes": "Test payment for receipt testing"
        }
        
        payment_response = self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
        assert payment_response.status_code == 200
        payment_id = payment_response.json()["id"]
        
        # Get receipt
        response = self.session.get(f"{BASE_URL}/api/payments/{payment_id}/receipt")
        assert response.status_code == 200, f"Failed to get receipt: {response.text}"
        
        receipt = response.json()
        
        # Verify all required fields
        required_fields = [
            "bill_number", "clinic_name", "therapist_name", 
            "client_name", "client_id", "date", "time",
            "amount", "payment_method", "payment_status"
        ]
        
        for field in required_fields:
            assert field in receipt, f"Missing required field: {field}"
            assert receipt[field] is not None, f"Field {field} is None"
        
        # Verify values
        assert receipt["amount"] == 2500.00
        assert receipt["payment_method"] == "UPI"  # Should be uppercase
        assert receipt["payment_status"] == "PAID"  # Should be uppercase
        
        print(f"✓ Receipt contains all required fields:")
        for field in required_fields:
            print(f"  - {field}: {receipt[field]}")
    
    def test_receipt_with_linked_appointment(self):
        """Receipt shows session date/time when linked to appointment"""
        # Create appointment
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        appt_response = self.session.post(f"{BASE_URL}/api/appointments", json={
            "client_id": self.test_client_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        })
        assert appt_response.status_code == 200
        appointment_id = appt_response.json()["id"]
        
        # Check in and out with payment
        self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-in", json={})
        checkout_response = self.session.post(f"{BASE_URL}/api/appointments/{appointment_id}/check-out", json={
            "record_payment": True,
            "payment_amount": 1800.00,
            "payment_mode": "cash",
            "payment_status": "paid"
        })
        assert checkout_response.status_code == 200
        payment_id = checkout_response.json()["payment"]["id"]
        
        # Get receipt
        response = self.session.get(f"{BASE_URL}/api/payments/{payment_id}/receipt")
        assert response.status_code == 200
        
        receipt = response.json()
        assert receipt.get("session_date") is not None, "session_date should be present for linked appointment"
        assert receipt.get("session_time") is not None, "session_time should be present for linked appointment"
        print(f"✓ Receipt shows session date: {receipt['session_date']} at {receipt['session_time']}")
    
    def test_receipt_not_found(self):
        """GET /api/payments/{id}/receipt - Returns 404 for non-existent payment"""
        response = self.session.get(f"{BASE_URL}/api/payments/non-existent-id/receipt")
        assert response.status_code == 404
        print(f"✓ Receipt returns 404 for non-existent payment")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
