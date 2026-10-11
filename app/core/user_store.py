import os
import json
import hashlib
import hmac
from typing import Optional, Dict

USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "users.json")
SALT = "copilot_salt_2026_xyz"


def _hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode("utf-8")).hexdigest()


def _ensure_store_dir():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        # Create default demo users if not present
        initial_users = {
            "admin": {
                "password_hash": _hash_password("admin123"),
                "role": "admin",
                "department": "general"
            },
            "user": {
                "password_hash": _hash_password("user123"),
                "role": "editor",
                "department": "engineering"
            }
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_users, f, indent=2)


def _load_users() -> Dict[str, dict]:
    _ensure_store_dir()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(users: Dict[str, dict]):
    _ensure_store_dir()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def register_user(username: str, password: str, role: str = "editor", department: str = "general") -> bool:
    """Registers a new user. Returns False if user already exists."""
    username = username.strip().lower()
    if not username or not password:
        return False
    users = _load_users()
    if username in users:
        return False
    users[username] = {
        "password_hash": _hash_password(password),
        "role": role,
        "department": department
    }
    _save_users(users)
    return True


def verify_user(username: str, password: str) -> Optional[dict]:
    """Verifies username and password. Returns user dict or None."""
    username = username.strip().lower()
    users = _load_users()
    user_info = users.get(username)
    if not user_info:
        return None
    hashed = _hash_password(password)
    if hmac.compare_digest(hashed, user_info["password_hash"]):
        return {
            "username": username,
            "role": user_info.get("role", "editor"),
            "department": user_info.get("department", "general")
        }
    return None
