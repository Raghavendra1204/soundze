import os
from dotenv import load_dotenv
from fastapi import APIRouter
from urllib.parse import urlencode

load_dotenv()

router = APIRouter()

CLIENT_ID = os.getenv("a065ed95808f4926acc7b0c88733bc22")
CLIENT_SECRET = os.getenv("d2b89c98a79c44ccb3f888463507cd58")
REDIRECT_URI = os.getenv("http://127.0.0.1:5173/callback")
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"

print("CLIENT_ID =", CLIENT_ID)
print("REDIRECT_URI =", REDIRECT_URI)

SCOPES = " ".join([
    "user-read-private",
    "user-read-recently-played",
    "user-top-read",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-modify-playback-state"
])

@router.get("/test")
def test():
    return {"msg": "spotify auth router works"}

@router.get("/login")
def spotify_login():
    
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES
    }
    url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return {"url": url}
