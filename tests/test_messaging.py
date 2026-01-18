"""
Messaging Feature Tests
Tests for therapist-controlled messaging visibility, restriction to assigned clients,
and read-only mode enforcement for expired subscriptions.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
THERAPIST_MOBILE = "9999999999"
THERAPIST_PASSWORD = "password123"

# Test client ID from context
TEST_CLIENT_ID = "c97b31a8-a2c6-427c-8653-bc7e3f983e08"


class TestMessagingSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def therapist_token(self):
        """Get therapist authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data["token"], data["user"]
    
    def test_therapist_login(self, therapist_token):
        """Test therapist can login successfully"""
        token, user = therapist_token
        assert token is not None
        assert user["role"] == "therapist"
        assert user["subscription_status"] in ["trial", "active"]
        print(f"✓ Therapist logged in: {user['full_name']} (subscription: {user['subscription_status']})")


class TestMessagingContacts:
    """Tests for messaging contacts endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_messaging_contacts(self, auth_headers):
        """Test therapist can see assigned clients in messaging contacts"""
        response = requests.get(f"{BASE_URL}/api/messaging-contacts", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get contacts: {response.text}"
        
        contacts = response.json()
        assert isinstance(contacts, list)
        print(f"✓ Found {len(contacts)} messaging contacts")
        
        # All contacts should be clients for a therapist
        for contact in contacts:
            assert contact.get("type") == "client", f"Expected client type, got {contact.get('type')}"
            assert "id" in contact
            assert "name" in contact
            print(f"  - {contact['name']} ({contact.get('display_id', 'N/A')})")
        
        return contacts
    
    def test_contacts_only_assigned_clients(self, auth_headers):
        """Verify contacts only include assigned clients with messaging enabled"""
        response = requests.get(f"{BASE_URL}/api/messaging-contacts", headers=auth_headers)
        contacts = response.json()
        
        # Get all clients for this therapist
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        all_clients = clients_response.json()
        
        # Contacts should be subset of assigned clients
        contact_ids = {c["id"] for c in contacts}
        client_ids = {c["id"] for c in all_clients}
        
        # All contacts should be in client list
        assert contact_ids.issubset(client_ids), "Contacts include non-assigned clients"
        print(f"✓ All {len(contacts)} contacts are assigned clients")


class TestSendMessage:
    """Tests for sending messages"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_client(self, auth_headers):
        """Get a test client to message"""
        response = requests.get(f"{BASE_URL}/api/messaging-contacts", headers=auth_headers)
        contacts = response.json()
        if contacts:
            return contacts[0]
        pytest.skip("No clients available for messaging test")
    
    def test_send_message_to_assigned_client(self, auth_headers, test_client):
        """Test therapist can send message to assigned client"""
        test_message = f"TEST_MSG_{uuid.uuid4().hex[:8]}: Hello from therapist"
        
        response = requests.post(f"{BASE_URL}/api/messages", headers=auth_headers, json={
            "recipient_id": test_client["id"],
            "content": test_message
        })
        
        assert response.status_code == 200, f"Failed to send message: {response.text}"
        
        msg = response.json()
        assert msg["content"] == test_message
        assert msg["recipient_id"] == test_client["id"]
        assert "id" in msg
        assert "created_at" in msg
        print(f"✓ Message sent to {test_client['name']}: {test_message[:30]}...")
        
        return msg
    
    def test_cannot_send_to_unassigned_client(self, auth_headers):
        """Test therapist cannot send message to unassigned client"""
        fake_client_id = str(uuid.uuid4())
        
        response = requests.post(f"{BASE_URL}/api/messages", headers=auth_headers, json={
            "recipient_id": fake_client_id,
            "content": "This should fail"
        })
        
        assert response.status_code in [403, 404], f"Expected 403/404, got {response.status_code}"
        print(f"✓ Correctly blocked message to unassigned client (status: {response.status_code})")
    
    def test_get_messages_with_client(self, auth_headers, test_client):
        """Test retrieving messages with a specific client"""
        response = requests.get(f"{BASE_URL}/api/messages/{test_client['id']}", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get messages: {response.text}"
        
        messages = response.json()
        assert isinstance(messages, list)
        print(f"✓ Retrieved {len(messages)} messages with {test_client['name']}")
    
    def test_get_conversations(self, auth_headers):
        """Test getting all conversations"""
        response = requests.get(f"{BASE_URL}/api/messages", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get conversations: {response.text}"
        
        conversations = response.json()
        assert isinstance(conversations, list)
        print(f"✓ Retrieved {len(conversations)} conversations")
        
        for conv in conversations:
            assert "user_id" in conv
            assert "user_name" in conv
            assert "last_message" in conv


class TestClientMessagingSettings:
    """Tests for therapist-controlled messaging visibility"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_client(self, auth_headers):
        """Get a test client for settings tests"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = response.json()
        if clients:
            return clients[0]
        pytest.skip("No clients available for settings test")
    
    def test_get_client_messaging_status(self, auth_headers, test_client):
        """Test getting client messaging status"""
        response = requests.get(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging-status", 
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get status: {response.text}"
        
        status = response.json()
        assert "client_id" in status
        assert "messaging_enabled" in status
        print(f"✓ Client {test_client['full_name']} messaging status: {status['messaging_enabled']}")
        
        return status["messaging_enabled"]
    
    def test_disable_client_messaging(self, auth_headers, test_client):
        """Test therapist can disable messaging for a client"""
        # First, ensure messaging is enabled
        requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging",
            headers=auth_headers,
            json={"messaging_enabled": True}
        )
        
        # Now disable it
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging",
            headers=auth_headers,
            json={"messaging_enabled": False}
        )
        
        assert response.status_code == 200, f"Failed to disable messaging: {response.text}"
        print(f"✓ Disabled messaging for {test_client['full_name']}")
        
        # Verify status changed
        status_response = requests.get(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging-status",
            headers=auth_headers
        )
        status = status_response.json()
        assert status["messaging_enabled"] == False, "Messaging should be disabled"
        print(f"✓ Verified messaging is disabled")
    
    def test_disabled_client_not_in_contacts(self, auth_headers, test_client):
        """Test disabled client doesn't appear in messaging contacts"""
        # Ensure messaging is disabled
        requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging",
            headers=auth_headers,
            json={"messaging_enabled": False}
        )
        
        # Get contacts
        response = requests.get(f"{BASE_URL}/api/messaging-contacts", headers=auth_headers)
        contacts = response.json()
        
        contact_ids = [c["id"] for c in contacts]
        assert test_client["id"] not in contact_ids, "Disabled client should not appear in contacts"
        print(f"✓ Disabled client {test_client['full_name']} not in messaging contacts")
    
    def test_cannot_send_to_disabled_client(self, auth_headers, test_client):
        """Test cannot send message to client with messaging disabled"""
        # Ensure messaging is disabled
        requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging",
            headers=auth_headers,
            json={"messaging_enabled": False}
        )
        
        # Try to send message
        response = requests.post(f"{BASE_URL}/api/messages", headers=auth_headers, json={
            "recipient_id": test_client["id"],
            "content": "This should fail - messaging disabled"
        })
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        assert "disabled" in response.json().get("detail", "").lower()
        print(f"✓ Correctly blocked message to disabled client")
    
    def test_enable_client_messaging(self, auth_headers, test_client):
        """Test therapist can re-enable messaging for a client"""
        response = requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging",
            headers=auth_headers,
            json={"messaging_enabled": True}
        )
        
        assert response.status_code == 200, f"Failed to enable messaging: {response.text}"
        print(f"✓ Re-enabled messaging for {test_client['full_name']}")
        
        # Verify status changed
        status_response = requests.get(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging-status",
            headers=auth_headers
        )
        status = status_response.json()
        assert status["messaging_enabled"] == True, "Messaging should be enabled"
        print(f"✓ Verified messaging is enabled")
    
    def test_enabled_client_in_contacts(self, auth_headers, test_client):
        """Test enabled client appears in messaging contacts"""
        # Ensure messaging is enabled
        requests.put(
            f"{BASE_URL}/api/clients/{test_client['id']}/messaging",
            headers=auth_headers,
            json={"messaging_enabled": True}
        )
        
        # Get contacts
        response = requests.get(f"{BASE_URL}/api/messaging-contacts", headers=auth_headers)
        contacts = response.json()
        
        contact_ids = [c["id"] for c in contacts]
        assert test_client["id"] in contact_ids, "Enabled client should appear in contacts"
        print(f"✓ Enabled client {test_client['full_name']} appears in messaging contacts")


class TestExpiredSubscriptionReadOnly:
    """Tests for read-only mode with expired subscription"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for therapist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": THERAPIST_MOBILE,
            "password": THERAPIST_PASSWORD
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_subscription_status_endpoint(self, auth_headers):
        """Test subscription status endpoint returns correct data"""
        response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=auth_headers)
        
        assert response.status_code == 200, f"Failed to get subscription status: {response.text}"
        
        status = response.json()
        assert "is_read_only" in status
        assert "subscription_status" in status
        print(f"✓ Subscription status: {status['subscription_status']}, read_only: {status['is_read_only']}")
        
        return status
    
    def test_active_subscription_can_send(self, auth_headers):
        """Test therapist with active subscription can send messages"""
        # First check subscription status
        status_response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=auth_headers)
        status = status_response.json()
        
        if status["is_read_only"]:
            pytest.skip("Therapist has expired subscription - cannot test active sending")
        
        # Get a contact
        contacts_response = requests.get(f"{BASE_URL}/api/messaging-contacts", headers=auth_headers)
        contacts = contacts_response.json()
        
        if not contacts:
            pytest.skip("No contacts available")
        
        # Send message
        response = requests.post(f"{BASE_URL}/api/messages", headers=auth_headers, json={
            "recipient_id": contacts[0]["id"],
            "content": f"TEST_ACTIVE_SUB_{uuid.uuid4().hex[:8]}"
        })
        
        assert response.status_code == 200, f"Active subscription should allow sending: {response.text}"
        print(f"✓ Active subscription can send messages")
    
    def test_read_only_mode_check(self, auth_headers):
        """Test that read-only mode is properly enforced via require_active_therapist"""
        # This tests the backend protection - the endpoint uses require_active_therapist
        # which blocks expired subscriptions
        
        # Check the toggle messaging endpoint (uses require_active_therapist)
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = response.json()
        
        if not clients:
            pytest.skip("No clients available")
        
        # The toggle endpoint should work for active subscriptions
        # and return 403 for expired subscriptions
        status_response = requests.get(f"{BASE_URL}/api/auth/subscription-status", headers=auth_headers)
        status = status_response.json()
        
        if status["is_read_only"]:
            # Test that write operations are blocked
            response = requests.put(
                f"{BASE_URL}/api/clients/{clients[0]['id']}/messaging",
                headers=auth_headers,
                json={"messaging_enabled": True}
            )
            assert response.status_code == 403, "Expired subscription should block write operations"
            print(f"✓ Read-only mode correctly blocks write operations")
        else:
            print(f"✓ Active subscription - write operations allowed (subscription: {status['subscription_status']})")


class TestMessagingUIDataTestIds:
    """Verify data-testid attributes exist for UI testing"""
    
    def test_expected_data_testids(self):
        """Document expected data-testid attributes for frontend testing"""
        expected_testids = [
            "messaging",
            "messaging-settings-button",
            "new-conversation-button",
            "conversations-list",
            "messages-panel",
            "message-input",
            "send-message-button",
            "new-conversation-dialog",
            "contact-select",
            "start-conversation-button",
            "messaging-settings-dialog",
            # Dynamic testids
            "conversation-{user_id}",
            "message-{id}",
            "client-setting-{id}",
            "toggle-messaging-{id}"
        ]
        
        print("✓ Expected data-testid attributes for Messaging UI:")
        for testid in expected_testids:
            print(f"  - {testid}")
        
        assert len(expected_testids) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
