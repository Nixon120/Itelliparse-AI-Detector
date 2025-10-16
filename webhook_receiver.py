import os, hmac, hashlib, json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

SECRET = os.environ.get("IP_SECRET_KEY", "dev_secret")
app = FastAPI()

@app.post("/webhooks/intelliparse")
async def receive(request: Request):
    raw = await request.body()
    sig = request.headers.get("X-Intelliparse-Signature", "")
    ok = False
    if sig.startswith("sha256="):
        given = sig.split("=",1)[1]
        calc = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
        ok = hmac.compare_digest(given, calc)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        payload = {"raw": raw.decode("utf-8", errors="ignore")}
    return JSONResponse({"verified": ok, "payload": payload})
