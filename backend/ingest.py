import sqlite3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_valid_token(user_id):
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT access_token, refresh_token FROM spotify_accounts WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        print(f"❌ No Spotify account found for user {user_id}")
        return None

    access_token, refresh_token = result

    # Refresh the token (Spotify tokens expire in 1hr, always refresh to be safe)
    response = requests.post("https://accounts.spotify.com/api/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    })

    if response.status_code != 200:
        print(f"❌ Token refresh failed: {response.text}")
        return access_token  # fallback to old token

    new_token = response.json().get("access_token")

    # Save new token to DB
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE spotify_accounts SET access_token = ? WHERE user_id = ?",
        (new_token, user_id)
    )
    conn.commit()
    conn.close()

    return new_token


def run_ml_pipeline(user_id: int):
    print(f"🚀 Starting ingestion for user {user_id}...")

    token = get_valid_token(user_id)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Get top 50 tracks
    url = "https://api.spotify.com/v1/me/top/tracks?time_range=medium_term&limit=50"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch top tracks: {response.status_code} {response.text}")
        return

    items = response.json().get("items", [])
    if not items:
        print("❌ No tracks returned.")
        return

    track_ids = [item["id"] for item in items if item.get("id")]
    track_info = {}
    for item in items:
        tid = item.get("id")
        if not tid:
            continue
        artist = "Unknown"
        if item.get("artists"):
            artist = item["artists"][0].get("name", "Unknown")
        track_info[tid] = {
            "name": item.get("name", "Unknown"),
            "artist": artist,
            "popularity": item.get("popularity", 0),
            "duration_ms": item.get("duration_ms", 0),
            "explicit": item.get("explicit", False)
        }

    # Step 2: Fetch full track details (replaces broken audio-features)
    ids_string = ",".join(track_ids[:50])
    tracks_url = f"https://api.spotify.com/v1/tracks?ids={ids_string}"
    tracks_response = requests.get(tracks_url, headers=headers)

    if tracks_response.status_code != 200:
        print(f"❌ Failed to fetch track details: {tracks_response.status_code}")
        return

    tracks_data = tracks_response.json().get("tracks", [])

    # Step 3: Save to DB
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()

    saved = 0
    for track in tracks_data:
        if not track:
            continue
        tid = track.get("id")
        info = track_info.get(tid, {})
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tracks
                (track_id, user_id, name, artist, popularity, duration_ms, explicit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tid,
                user_id,
                info.get("name"),
                info.get("artist"),
                info.get("popularity", 0),
                info.get("duration_ms", 0),
                info.get("explicit", False)
            ))
            saved += 1
        except Exception as e:
            print(f"Error saving {tid}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Saved {saved} tracks for user {user_id}")

if __name__ == "__main__":
 run_ml_pipeline(user_id=1)  # change 1 to your actual user_id