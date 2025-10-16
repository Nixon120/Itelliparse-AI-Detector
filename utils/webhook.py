import os, hmac, hashlib, httpx, json
from typing import Dict

SECRET = os.environ.get("IP_SECRET_KEY", "dev_secret")

def sign_payload(payload: Dict) -> str:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    mac = hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={mac}"

async def post_webhook(url: str, payload: Dict) -> Dict:
    sig = sign_payload(payload)
    headers = {
        "Content-Type": "application/json",
        "X-Intelliparse-Signature": sig,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload, headers=headers)
        return {"status_code": r.status_code, "text": r.text}
