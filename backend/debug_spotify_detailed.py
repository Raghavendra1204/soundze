"""
Detailed Spotify Token Debugger
"""
import sqlite3
import requests
import json

# Get the Spotify token from database
conn = sqlite3.connect('music_app.db')
cursor = conn.cursor()

cursor.execute("SELECT access_token, spotify_user_id FROM spotify_accounts ORDER BY id DESC LIMIT 1")
result = cursor.fetchone()
conn.close()

if not result:
    print("❌ No Spotify account found in database!")
    print("Run test_auth.py and connect Spotify first.")
    exit()

access_token, spotify_id = result

print("=" * 70)
print("🔍 SPOTIFY TOKEN DEBUG")
print("=" * 70)
print(f"\nSpotify User ID: {spotify_id}")
print(f"Token: {access_token[:30]}...")

headers = {"Authorization": f"Bearer {access_token}"}

# Test 1: Get user profile (should always work)
print("\n" + "=" * 70)
print("TEST 1: Get User Profile")
print("=" * 70)
r = requests.get("https://api.spotify.com/v1/me", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ Token is valid!")
else:
    print(f"❌ Error: {r.json()}")
    print("\n🔄 Your token expired. Run: python test_auth.py")
    exit()

# Test 2: Get top tracks
print("\n" + "=" * 70)
print("TEST 2: Get Top Tracks")
print("=" * 70)
r = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=3", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    tracks = r.json().get("items", [])
    print(f"✅ Got {len(tracks)} tracks")
    for t in tracks:
        print(f"  - {t['name']}")
    
    # Save track IDs for next test
    track_ids = [t["id"] for t in tracks]
else:
    print(f"❌ Error: {r.json()}")
    exit()

# Test 3: Get audio features
print("\n" + "=" * 70)
print("TEST 3: Get Audio Features")
print("=" * 70)
ids_string = ",".join(track_ids)
url = f"https://api.spotify.com/v1/audio-features?ids={ids_string}"
print(f"URL: {url}")
r = requests.get(url, headers=headers)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    print("✅ Audio features working!")
    features = r.json().get("audio_features", [])
    for i, f in enumerate(features):
        if f:
            print(f"\n  Track {i+1}:")
            print(f"    Energy: {f.get('energy')}")
            print(f"    Valence: {f.get('valence')}")
            print(f"    Tempo: {f.get('tempo')}")
else:
    print(f"❌ Error getting audio features!")
    print(f"Response: {r.text}")
    error_data = r.json()
    print(f"\nFull error:")
    print(json.dumps(error_data, indent=2))
    
    if r.status_code == 403:
        print("\n💡 403 Forbidden means:")
        print("  - Your Spotify account might not have permission")
        print("  - OR the token scope is missing")
        print("\n🔄 Try reconnecting: python test_auth.py")

print("\n" + "=" * 70)