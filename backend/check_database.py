"""
Check what's actually in the database
"""
import sqlite3
import os

# Check if database exists
if not os.path.exists('music_app.db'):
    print("❌ Database file doesn't exist!")
    print("Run: python setup_database.py")
    exit()

print("✅ Database file exists")

conn = sqlite3.connect('music_app.db')
cursor = conn.cursor()

# Check users table
print("\n" + "=" * 70)
print("👥 USERS TABLE")
print("=" * 70)
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
print(f"Total users: {len(users)}")
for row in users:
    print(f"  {row}")

# Check spotify_accounts table
print("\n" + "=" * 70)
print("🎵 SPOTIFY_ACCOUNTS TABLE")
print("=" * 70)
cursor.execute("SELECT * FROM spotify_accounts")
spotify = cursor.fetchall()
print(f"Total Spotify connections: {len(spotify)}")
for row in spotify:
    print(f"  {row}")

conn.close()

if len(users) > 0 and len(spotify) == 0:
    print("\n" + "=" * 70)
    print("⚠️  PROBLEM FOUND!")
    print("=" * 70)
    print("You have users but NO Spotify connections!")
    print("This means the /callback endpoint has a bug.")
    print("\nLet me check your main.py callback code...")
    