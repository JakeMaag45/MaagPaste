"""
Firebase client for MaagPaste - handles authentication and real-time database operations.
"""

import requests
import json
import time
from datetime import datetime

class FirebaseError(Exception):
    pass

class Session:
    def __init__(self, id_token, refresh_token, local_id, email, username=None):
        self.id_token = id_token
        self.refresh_token = refresh_token
        self.local_id = local_id
        self.email = email
        self.username = username
        self._expires_at = time.time() + 3600  # tokens expire in 1 hour

    def refresh_if_needed(self):
        if time.time() > self._expires_at:
            refresh_id_token(self)
            self._expires_at = time.time() + 3600

def refresh_id_token(session):
    """Refresh the Firebase ID token using the refresh token."""
    url = "https://securetoken.googleapis.com/v1/token?key=AIzaSyCnDgLCSegRmRF4cDYMEkTVAfIQUrm9XWE"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": session.refresh_token
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise FirebaseError("Failed to refresh token")
    data = response.json()
    session.id_token = data["id_token"]
    session.refresh_token = data.get("refresh_token", session.refresh_token)

def sign_in(email, password):
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCnDgLCSegRmRF4cDYMEkTVAfIQUrm9XWE"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        error = response.json().get("error", {})
        raise FirebaseError(error.get("message", "Sign in failed"))
    data = response.json()
    
    # Get username from database
    username = get_username(data["localId"], data["idToken"])
    
    return Session(
        id_token=data["idToken"],
        refresh_token=data["refreshToken"],
        local_id=data["localId"],
        email=data["email"],
        username=username
    )

def sign_up(email, password, username):
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyCnDgLCSegRmRF4cDYMEkTVAfIQUrm9XWE"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        error = response.json().get("error", {})
        raise FirebaseError(error.get("message", "Sign up failed"))
    data = response.json()
    
    # Save username to database
    set_username(data["localId"], data["idToken"], username)
    
    # Set default settings - screen sharing ON by default
    set_settings(data["localId"], data["idToken"], {
        "allow_delete": True,
        "show_all_screens": False,
        "screen_on_by_default": True
    })
    
    return Session(
        id_token=data["idToken"],
        refresh_token=data["refreshToken"],
        local_id=data["localId"],
        email=data["email"],
        username=username
    )

def get_username(local_id, id_token):
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/users/{local_id}/username.json?auth={id_token}"
    response = requests.get(url)
    if response.status_code == 200 and response.text:
        return response.json()
    return None

def set_username(local_id, id_token, username):
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/users/{local_id}/username.json?auth={id_token}"
    response = requests.put(url, json=username)
    if response.status_code != 200:
        raise FirebaseError("Failed to save username")

def verify_password(email, password):
    """Verify the user's password without signing in."""
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyCnDgLCSegRmRF4cDYMEkTVAfIQUrm9XWE"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise FirebaseError("Incorrect password")

def push_entry(session, entry_id, content, created_at):
    session.refresh_if_needed()
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/users/{session.local_id}/history/{entry_id}.json?auth={session.id_token}"
    payload = {
        "content": content,
        "created_at": created_at
    }
    response = requests.put(url, json=payload)
    if response.status_code != 200:
        raise FirebaseError("Failed to push entry")

def fetch_all(session):
    session.refresh_if_needed()
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/users/{session.local_id}/history.json?auth={session.id_token}"
    response = requests.get(url)
    if response.status_code != 200:
        return {}
    return response.json() or {}

def delete_entry(session, entry_id):
    session.refresh_if_needed()
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/users/{session.local_id}/history/{entry_id}.json?auth={session.id_token}"
    response = requests.delete(url)
    return response.status_code == 200

def get_settings(session):
    session.refresh_if_needed()
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/users/{session.local_id}/settings.json?auth={session.id_token}"
    response = requests.get(url)
    if response.status_code != 200:
        return {}
    return response.json() or {}

def set_settings(session, settings):
    session.refresh_if_needed()
    # Get existing settings
    existing = get_settings(session)
    existing.update(settings)
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/users/{session.local_id}/settings.json?auth={session.id_token}"
    response = requests.put(url, json=existing)
    if response.status_code != 200:
        raise FirebaseError("Failed to save settings")

def set_screen_frame(session, frame_base64):
    session.refresh_if_needed()
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/screens/{session.local_id}.json?auth={session.id_token}"
    payload = {
        "active": True,
        "frame": frame_base64,
        "username": session.username,
        "email": session.email,
        "updated_at": datetime.now().isoformat()
    }
    response = requests.put(url, json=payload)
    if response.status_code != 200:
        raise FirebaseError("Failed to push screen frame")

def set_screen_inactive(session):
    session.refresh_if_needed()
    url = f"https://servicechat-f49d3-default-rtdb.firebaseio.com/screens/{session.local_id}.json?auth={session.id_token}"
    payload = {
        "active": False,
        "frame": "",
        "username": session.username,
        "email": session.email,
        "updated_at": datetime.now().isoformat()
    }
    response = requests.put(url, json=payload)
    return response.status_code == 200

def push_screen_frame(session, frame_base64):
    """Push a screen frame to Firebase."""
    set_screen_frame(session, frame_base64)
