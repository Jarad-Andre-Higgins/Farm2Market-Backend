#!/usr/bin/env python
"""
Test the enhanced chat APIs
"""
import requests
import json

def test_chat_apis():
    """Test chat functionality"""
    base_url = "http://localhost:8000/api"
    
    print("💬 TESTING ENHANCED CHAT APIS")
    print("=" * 50)
    
    # First login to get token
    print("\n1. Logging in to get token...")
    login_data = {
        "email": "testbuyer@buyer.com",
        "password": "buyer123"
    }
    
    response = requests.post(f"{base_url}/buyer/login/", json=login_data)
    if response.status_code == 200:
        token = response.json()['token']
        headers = {'Authorization': f'Token {token}'}
        print(f"✅ Login successful! Token: {token[:20]}...")
    else:
        print(f"❌ Login failed: {response.text}")
        return
    
    # Test 1: Get conversations
    print("\n2. Testing get conversations...")
    try:
        response = requests.get(f"{base_url}/messages/conversations/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('conversations', []))} conversations")
        else:
            print(f"❌ Failed to get conversations")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Start a conversation
    print("\n3. Testing start conversation...")
    try:
        # Get farmer ID from test data (farmer ID should be 8 based on our test data)
        conversation_data = {
            "recipient_id": 8,  # Test farmer ID
            "initial_message": "Hello! I'm interested in your products.",
            "conversation_type": "product_inquiry"
        }
        
        response = requests.post(f"{base_url}/messages/conversations/start/", 
                               json=conversation_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            conversation_id = data.get('conversation_id')
            print(f"✅ Conversation started! ID: {conversation_id}")
            
            # Test 3: Send a message
            if conversation_id:
                print("\n4. Testing send message...")
                message_data = {
                    "conversation_id": conversation_id,
                    "message_text": "Can you tell me more about your tomatoes?"
                }
                
                response = requests.post(f"{base_url}/messages/send/", 
                                       json=message_data, headers=headers)
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    print(f"✅ Message sent successfully!")
                else:
                    print(f"❌ Failed to send message")
                
                # Test 4: Get conversation messages
                print("\n5. Testing get conversation messages...")
                response = requests.get(f"{base_url}/messages/conversation/{conversation_id}/", 
                                      headers=headers)
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get('messages', [])
                    print(f"✅ Found {len(messages)} messages in conversation")
                else:
                    print(f"❌ Failed to get conversation messages")
        else:
            print(f"❌ Failed to start conversation")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Chat API testing completed!")

if __name__ == '__main__':
    test_chat_apis()
