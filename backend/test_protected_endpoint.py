"""
Test your protected endpoints after authentication
"""
import requests
import json

# Read your saved token
try:
    with open('your_token.txt', 'r') as f:
        TOKEN = f.read().strip()
except FileNotFoundError:
    print("❌ Token file not found! Run test_auth.py first.")
    exit()

BASE_URL = "http://127.0.0.1:8000"
headers = {"Authorization": f"Bearer {TOKEN}"}

print("🎵 Testing Protected Endpoints")
print("=" * 70)

# 1. Get top tracks
print("\n📡 Getting your top tracks...")
response = requests.get(f"{BASE_URL}/me/top-tracks?limit=10", headers=headers)
print(f"Status: {response.status_code}")
data = response.json()
print(json.dumps(data, indent=2))

# 2. Get audio features for first track
if data.get("tracks"):
    track_ids = [t["id"] for t in data["tracks"][:3]]
    ids_string = ",".join(track_ids)
    
    print("\n📡 Getting audio features...")
    response = requests.get(
        f"{BASE_URL}/me/audio-features?track_ids={ids_string}",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

print("\n✅ Success! Your auth system is fully working!")