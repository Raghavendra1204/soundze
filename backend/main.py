"""
🔐 Complete Authentication System
==================================

USER FLOW:
1. User signs up (email + password)
2. User logs in → gets a session token
3. User connects their Spotify account
4. User can now use all endpoints with their data stored

TECH STACK:
- SQLite database (simple, no setup needed)
- Password hashing (secure storage)
- JWT tokens (for sessions)
- Spotify OAuth (already working!)
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os
import requests
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt

# Load environment
load_dotenv(dotenv_path=".env", override=True)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# JWT secret (generate a random one for your app)
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))

app = FastAPI()


# ============================================================
# DATABASE SETUP
# ============================================================

def init_db():
    """Create database tables if they don't exist"""
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Spotify connections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spotify_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            spotify_user_id TEXT UNIQUE NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_expires_at TIMESTAMP,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()


# ============================================================
# PYDANTIC MODELS (for request validation)
# ============================================================

class UserSignup(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_jwt_token(user_id: int, email: str) -> str:
    """Create a JWT token for user sessions"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)  # Token valid for 7 days
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: str = Header(None)):
    """
    Dependency to get current logged-in user from JWT token
    
    Usage in endpoints:
    @app.get("/protected")
    def protected_route(user = Depends(get_current_user)):
        # user contains user_id and email
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    return verify_jwt_token(token)


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.post("/signup")
def signup(user: UserSignup):
    """
    Create a new user account
    
    Request body:
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    """
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()
    
    try:
        # Hash the password
        password_hash = hash_password(user.password)
        
        # Insert user
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (user.email, password_hash)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        
        # Create JWT token
        token = create_jwt_token(user_id, user.email)
        
        return {
            "message": "Account created successfully!",
            "user_id": user_id,
            "email": user.email,
            "token": token,
            "next_step": "Use this token in Authorization header: 'Bearer <token>'"
        }
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()


@app.post("/login")
def login(user: UserLogin):
    """
    Login with existing account
    
    Request body:
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    """
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()
    
    # Find user
    cursor.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?",
        (user.email,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id, email, stored_hash = result
    
    # Verify password
    if hash_password(user.password) != stored_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token = create_jwt_token(user_id, email)
    
    return {
        "message": "Login successful!",
        "user_id": user_id,
        "email": email,
        "token": token,
        "next_step": "Use this token in Authorization header for all requests"
    }


# ============================================================
# SPOTIFY OAUTH (Updated to link with user accounts)
# ============================================================

@app.get("/connect-spotify")
def connect_spotify(user = Depends(get_current_user)):
    """
    Start Spotify OAuth flow for logged-in user
    
    Usage: Add Authorization header with your JWT token
    """
    # Store user_id in state parameter so we can link it later
    state = f"{user['user_id']}"
    
    spotify_auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=user-read-private user-read-email playlist-read-private user-top-read user-read-recently-played"
        f"&state={state}"
    )
    return RedirectResponse(spotify_auth_url)


@app.get("/callback")
def spotify_callback(code: str = None, state: str = None, error: str = None):
    """
    Spotify OAuth callback - links Spotify account to user
    """
    if error:
        return {"error": error}
    
    # Get user_id from state
    user_id = int(state)
    
    # Exchange code for access token
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    token_response = requests.post(token_url, data=data).json()
    
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in", 3600)
    
    if not access_token:
        return {"error": "Failed to get access token", "details": token_response}
    
    # Get Spotify user info
    headers = {"Authorization": f"Bearer {access_token}"}
    spotify_user = requests.get("https://api.spotify.com/v1/me", headers=headers).json()
    spotify_user_id = spotify_user.get("id")
    
    # Store in database
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()
    
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    try:
        # Insert or update Spotify connection
        cursor.execute('''
            INSERT OR REPLACE INTO spotify_accounts 
            (user_id, spotify_user_id, access_token, refresh_token, token_expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, spotify_user_id, access_token, refresh_token, token_expires_at))
        
        conn.commit()
    finally:
        conn.close()
    
    return {
        "message": "Spotify account connected successfully!",
        "spotify_user": spotify_user_id,
        "user_id": user_id
    }


# ============================================================
# PROTECTED ENDPOINTS (Require authentication)
# ============================================================

def get_spotify_token(user_id: int) -> str:
    """Helper to get Spotify access token for a user"""
    conn = sqlite3.connect('music_app.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT access_token FROM spotify_accounts WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(
            status_code=400, 
            detail="Spotify account not connected. Use /connect-spotify first"
        )
    
    return result[0]


@app.get("/me/top-tracks")
def get_my_top_tracks(
    time_range: str = "medium_term",
    limit: int = 20,
    user = Depends(get_current_user)
):
    """
    Get YOUR top tracks (authenticated endpoint)
    
    Usage: Add header: Authorization: Bearer <your_jwt_token>
    """
    access_token = get_spotify_token(user["user_id"])
    
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit={limit}"
    response = requests.get(url, headers=headers).json()
    
    tracks = []
    for item in response.get("items", []):
        tracks.append({
            "id": item["id"],
            "name": item["name"],
            "artist": item["artists"][0]["name"],
            "popularity": item["popularity"]
        })
    
    return {
        "user": user["email"],
        "time_range": time_range,
        "total": len(tracks),
        "tracks": tracks
    }


@app.get("/me/audio-features")
def get_my_audio_features(
    track_ids: str,
    user = Depends(get_current_user)
):
    """
    Get audio features for tracks (authenticated)
    
    Usage: /me/audio-features?track_ids=id1,id2,id3
    Header: Authorization: Bearer <your_jwt_token>
    """
    access_token = get_spotify_token(user["user_id"])
    
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/audio-features?ids={track_ids}"
    response = requests.get(url, headers=headers).json()
    
    return response


@app.get("/")
def root():
    return {
        "status": "Music App API running",
        "endpoints": {
            "signup": "POST /signup",
            "login": "POST /login",
            "connect_spotify": "GET /connect-spotify (requires auth)",
            "my_top_tracks": "GET /me/top-tracks (requires auth)",
            "my_audio_features": "GET /me/audio-features (requires auth)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)