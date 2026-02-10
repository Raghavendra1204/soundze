"""
Debug script to check tokens in database
"""
import sqlite3
import requests
from datetime import datetime

# Check database
conn = sqlite3.connect('music_app.db')
cursor = conn.cursor()

print("=" * 70)
print("🔍 CHECKING DATABASE")
print("=" * 70)

# Get all users
cursor.execute("SELECT id, email FROM users")
users = cursor.fetchall()
print(f"\n📋 Users in database: {len(users)}")
for user_id, email in users:
    print(f"  - User {user_id}: {email}")

# Get Spotify connections
cursor.execute("""
    SELECT user_id, spotify_user_id, access_token, token_expires_at 
    FROM spotify_accounts
""")
spotify_accounts = cursor.fetchall()

print(f"\n🎵 Spotify connections: {len(spotify_accounts)}")
for user_id, spotify_id, token, expires in spotify_accounts:
    print(f"\n  User {user_id}:")
    print(f"    Spotify ID: {spotify_id}")
    print(f"    Token: {token[:30]}...")
    print(f"    Expires: {expires}")
    
    # Test the token
    print(f"\n    Testing token...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test basic endpoint
    r1 = requests.get("https://api.spotify.com/v1/me", headers=headers)
    print(f"    /me endpoint: {r1.status_code}")
    
    # Test audio features endpoint
    r2 = requests.get("https://api.spotify.com/v1/audio-features?ids=11dFghVXANMlKmJXsNCbNl", headers=headers)
    print(f"    /audio-features endpoint: {r2.status_code}")
    
    if r2.status_code != 200:
        print(f"    Error: {r2.json()}")

conn.close()

print("\n" + "=" * 70)
print("💡 If token test failed, you need to reconnect Spotify!")
print("=" * 70)