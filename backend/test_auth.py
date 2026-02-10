"""
🧪 Test Script for Authentication System
========================================

This script helps you test all the auth features easily!
Run this to signup, login, and test protected endpoints.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_response(title, response):
    """Pretty print API responses"""
    print("\n" + "=" * 70)
    print(f"📡 {title}")
    print("=" * 70)
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("=" * 70)


def test_signup():
    """Test user signup"""
    print("\n🔹 STEP 1: Creating a new account...")
    
    data = {
        "email": "test@example.com",  # Change this to your email
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/signup", json=data)
    print_response("SIGNUP RESPONSE", response)
    
    if response.status_code == 200:
        return response.json().get("token")
    return None


def test_login():
    """Test user login"""
    print("\n🔹 STEP 2: Logging in...")
    
    data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    print_response("LOGIN RESPONSE", response)
    
    if response.status_code == 200:
        return response.json().get("token")
    return None


def test_protected_endpoint(token):
    """Test accessing a protected endpoint"""
    print("\n🔹 STEP 3: Testing protected endpoint (without Spotify)...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # This will fail because we haven't connected Spotify yet
    # But it shows the auth is working!
    response = requests.get(f"{BASE_URL}/me/top-tracks", headers=headers)
    print_response("PROTECTED ENDPOINT (Expected to fail)", response)


def get_spotify_auth_url(token):
    """Get Spotify authorization URL"""
    print("\n🔹 STEP 4: Getting Spotify connection URL...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # We can't use RedirectResponse in requests, so we'll check the response
    response = requests.get(
        f"{BASE_URL}/connect-spotify", 
        headers=headers,
        allow_redirects=False  # Don't follow the redirect
    )
    
    if response.status_code == 307:
        spotify_url = response.headers.get("location")
        print("\n" + "=" * 70)
        print("✅ SPOTIFY AUTH URL GENERATED")
        print("=" * 70)
        print(f"\n🔗 Copy this URL and paste it in your browser:\n")
        print(spotify_url)
        print("\n" + "=" * 70)
        print("\n📝 After authorizing on Spotify:")
        print("1. You'll be redirected back")
        print("2. Your Spotify account will be connected")
        print("3. Then you can use /me/top-tracks and other endpoints!")
        print("=" * 70)
        return spotify_url
    else:
        print_response("ERROR GETTING SPOTIFY URL", response)
        return None


def main():
    """Main test flow"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║        🎵 AUTHENTICATION SYSTEM TEST SCRIPT 🎵              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    This script will:
    1. ✅ Create a test account (or login if exists)
    2. ✅ Get a JWT token
    3. ✅ Test protected endpoints
    4. ✅ Generate Spotify connection link
    
    Make sure your server is running on port 8000!
    """)
    
    input("Press ENTER to start...")
    
    # Try signup first
    token = test_signup()
    
    # If signup fails (user exists), try login
    if not token:
        print("\n⚠️  Signup failed (user might exist), trying login...")
        token = test_login()
    
    if not token:
        print("\n❌ Failed to get token. Check your server and try again.")
        return
    
    print("\n✅ Successfully got JWT token!")
    print(f"Your token: {token[:50]}...")
    
    # Test protected endpoint (will fail without Spotify)
    test_protected_endpoint(token)
    
    # Get Spotify auth URL
    spotify_url = get_spotify_auth_url(token)
    
    if spotify_url:
        print("\n🎉 SUCCESS! Follow the instructions above to complete Spotify connection.")
        
        # Save token to file for easy access
        with open("your_token.txt", "w") as f:
            f.write(token)
        print("\n💾 Your token has been saved to 'your_token.txt'")
        print("   Use this token for future API requests!")


if __name__ == "__main__":
    main()