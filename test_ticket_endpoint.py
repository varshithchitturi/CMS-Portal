import sys
import os
sys.path.append('.')

import json
from app import app

def test_create_ticket_endpoint():
    """Test the /create_ticket endpoint that was failing"""
    
    with app.test_client() as client:
        # First, let's simulate a login to get a session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'test_user'
            sess['full_name'] = 'Test User'
            sess['chat_session_id'] = 'test-session-123'
        
        # Now test the create_ticket endpoint
        response = client.post('/create_ticket', 
                             json={'message': 'I cannot log into my account'},
                             content_type='application/json')
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_json()}")
        
        if response.status_code == 200:
            data = response.get_json()
            if data.get('success'):
                print("✅ Ticket creation successful!")
                print(f"Ticket ID: {data.get('ticket_id')}")
                print(f"Category: {data.get('category')}")
                print(f"Priority: {data.get('priority')}")
            else:
                print(f"❌ Ticket creation failed: {data.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            try:
                error_data = response.get_json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.get_data(as_text=True)}")

if __name__ == "__main__":
    test_create_ticket_endpoint()
