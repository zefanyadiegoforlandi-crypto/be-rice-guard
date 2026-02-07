"""
Quick API Testing Script
Jalankan script ini untuk test semua endpoint API
"""

import requests
import json
import base64
import time

BASE_URL = "http://localhost:8000/api"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'='*50}")
    print(f"{title}")
    print(f"{'='*50}{RESET}\n")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def test_health():
    """Test health endpoint"""
    print_section("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health")
        if response.status_code == 200:
            print_success("Health check passed")
            print(json.dumps(response.json(), indent=2))
        else:
            print_error(f"Health check failed: {response.status_code}")
    except Exception as e:
        print_error(f"Connection error: {str(e)}")

def test_register():
    """Test user registration"""
    print_section("Testing User Registration")
    
    test_email = f"testuser_{int(time.time())}@example.com"
    test_data = {
        "email": test_email,
        "name": "Test User",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Registration successful for {test_email}")
            print(f"Token: {data['access_token'][:50]}...")
            return data['access_token'], test_email
        else:
            print_error(f"Registration failed: {response.text}")
            return None, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None, None

def test_login(email, password="testpass123"):
    """Test user login"""
    print_section("Testing User Login")
    
    test_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=test_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Login successful for {email}")
            print(f"Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print_error(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def test_get_stats(token):
    """Test get detection stats"""
    print_section("Testing Get Detection Stats")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/detection/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Stats retrieved successfully")
            print(json.dumps(data, indent=2))
        else:
            print_error(f"Failed to get stats: {response.text}")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_get_history(token):
    """Test get detection history"""
    print_section("Testing Get Detection History")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/detection/history",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"History retrieved successfully ({len(data)} records)")
            if len(data) > 0:
                print(f"First record: {json.dumps(data[0], indent=2)}")
        else:
            print_error(f"Failed to get history: {response.text}")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def main():
    print(f"\n{YELLOW}Rice Detection API - Testing Script{RESET}")
    print(f"{YELLOW}Make sure both backend and frontend are running!{RESET}\n")
    
    # Test health
    test_health()
    
    # Test registration and get token
    token, email = test_register()
    
    if token:
        # Test login
        test_login(email)
        
        # Test stats
        test_get_stats(token)
        
        # Test history
        test_get_history(token)
        
        print(f"\n{GREEN}All tests completed!{RESET}")
    else:
        print(f"\n{RED}Testing aborted due to registration failure{RESET}")

if __name__ == "__main__":
    main()
