import requests
import json
import webbrowser
import os
import time

print("=== ESPA Authentication Test ===")
print("This script will test your authentication in the browser")

# Open login page in browser
login_url = 'http://127.0.0.1:8000/login/'
print(f"Opening login page in browser: {login_url}")
webbrowser.open(login_url)

# Wait for user to login
input("Press Enter after you have logged in through the browser...")

# Now check if authentication worked by making a request to API
try:
    # First make a simple request to get the cookies/session
    session = requests.Session()
    home_response = session.get('http://127.0.0.1:8000/')
    cookies = session.cookies.get_dict()
    
    print("\nSession cookies obtained:")
    for name, value in cookies.items():
        print(f"- {name}: {value[:10]}..." if len(str(value)) > 10 else f"- {name}: {value}")
    
    # Try to access profile API which requires authentication
    profile_url = 'http://127.0.0.1:8000/api/accounts/profile/'
    headers = {}
    
    # Check if we have localStorage tokens from browser
    access_token = input("\nEnter the access token from localStorage (if available, or press Enter to skip): ")
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    
    print(f"\nMaking authenticated request to: {profile_url}")
    print(f"Headers: {headers}")
    profile_response = session.get(profile_url, headers=headers)
    
    print(f"\nProfile API Response Status: {profile_response.status_code}")
    if profile_response.status_code == 200:
        print("Authentication successful! Profile data:")
        try:
            profile_data = profile_response.json()
            print(json.dumps(profile_data, indent=2))
        except:
            print(f"Raw response: {profile_response.text[:500]}")
    else:
        print(f"Authentication failed. Response: {profile_response.text[:500]}")
        
except Exception as e:
    print(f"Error during test: {str(e)}")

print("\nTest completed.") 