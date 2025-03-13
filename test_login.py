import requests
import json

# Test login with testuser3
login_url = 'http://127.0.0.1:8000/api/accounts/login/'
data = {
    'username': 'testuser3',
    'password': 'testpassword123'
}

print("Testing login with testuser3...")
response = requests.post(login_url, json=data)
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

# If login is successful, print the tokens
if response.status_code == 200:
    response_data = response.json()
    print("Login successful!")
    print(f"Access token: {response_data.get('access')[:20]}...")
    print(f"Refresh token: {response_data.get('refresh')[:20]}...")
    print(f"User: {response_data.get('user')}") 