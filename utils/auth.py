from typing import Dict, Optional
from passlib.hash import bcrypt
from datetime import datetime

USERS: Dict[str, Dict] = {}

def create_user(email: str, password: str) -> Dict:
    if email in USERS:
        raise ValueError("user_exists")
    hashed = bcrypt.hash(password)
    USERS[email] = {
        "email": email,
        "password_hash": hashed,
        "api_key": f"sk_{abs(hash(email)) & 0xfffffff:07x}",  # simple demo key
        "plan": "free",
        "created_at": datetime.utcnow().isoformat()
    }
    return USERS[email]

def verify_user(email: str, password: str) -> Optional[Dict]:
    user = USERS.get(email)
    if not user: 
        return None
    if bcrypt.verify(password, user["password_hash"]):
        return user
    return None

def get_user(email: str) -> Optional[Dict]:
    return USERS.get(email)

def get_user_by_api_key(api_key: str) -> Optional[Dict]:
    for user in USERS.values():
        if user.get("api_key") == api_key:
            return user
    return None

def set_user_plan(email: str, plan: str) -> None:
    if email in USERS:
        USERS[email]["plan"] = plan
