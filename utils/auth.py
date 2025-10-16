from typing import Dict, Optional
from passlib.hash import bcrypt
from datetime import datetime

# In-memory user store (email -> record). Replace with DB in production.
USERS: Dict[str, Dict] = {}

def create_user(email: str, password: str) -> Dict:
    if email in USERS:
        raise ValueError("user_exists")
    hashed = bcrypt.hash(password)
    USERS[email] = {
        "email": email,
        "password_hash": hashed,
        "api_key": f"sk_{abs(hash(email)) & 0xfffffff:07x}",
        "created_at": datetime.utcnow().isoformat()
    }
    return USERS[email]

def verify_user(email: str, password: str) -> Optional[Dict]:
    user = USERS.get(email)
    if not user: return None
    if bcrypt.verify(password, user["password_hash"]):
        return user
    return None

def get_user(email: str) -> Optional[Dict]:
    return USERS.get(email)
