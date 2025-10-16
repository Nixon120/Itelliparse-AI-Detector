import os, json, tempfile, uuid, stripe
from typing import Optional

from fastapi import (
    FastAPI, UploadFile, File, BackgroundTasks, HTTPException,
    Request, Depends, Header
)
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field

from utils.storage import save_upload
from utils.jobs import set_job, get_job
from utils.scoring import fuse
from utils.identity import enroll as id_enroll, delete as id_delete, match_face, match_voice
from utils.auth import (
    create_user, verify_user, get_user,
    get_user_by_api_key, set_user_plan
)
from utils.webhook import post_webhook
from detectors.provenance import check_c2pa
from detectors.watermark import scan_watermarks
from detectors.visual import analyze_video
from detectors.imagegen import analyze_image
from detectors.audio import analyze_audio
from ml.models import pseudo_image_score, pseudo_audio_score, pseudo_video_score, metrics_stub

APP_NAME = "PowerAI"
APP_VERSION = "1.3.0"

APP_SECRET = os.environ.get("IP_SESSION_SECRET", "dev_session_secret")
REQUIRE_AUTH = os.environ.get("IP_REQUIRE_AUTH", "0") == "1"

# Stripe
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PRICE_PRO_MONTH = os.environ.get("STRIPE_PRICE_PRO_MONTH")  # optional, can pass from body
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.add_middleware(SessionMiddleware, secret_key=APP_SECRET)

# Serve frontend (Vite dist)
if os.path.isdir("web/dist"):
    app.mount("/assets", StaticFiles(directory="web/dist/assets"), name="assets")

def spa_index() -> HTMLResponse:
    index_path = os.path.join("web", "dist", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse(f"<h1>{APP_NAME}</h1><p>Build the frontend to see the UI.</p>")

# ---------- Auth: sessions & API Keys ----------
class AuthReq(BaseModel):
    email: str
    password: str

def current_user(request: Request) -> Optional[dict]:
    email = request.session.get("email")
    return get_user(email) if email else None

def api_key_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> Optional[dict]:
    token = None
    # Authorization: Bearer sk_xxx
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    # Or X-API-Key: sk_xxx
    if not token and x_api_key:
        token = x_api_key.strip()
    if not token:
        return None
    return get_user_by_api_key(token)

def require_auth_or_api_key(
    session_user = Depends(current_user),
    header_user = Depends(api_key_user)
):
    if not REQUIRE_AUTH:
        # In dev mode, allow no auth
        return session_user or header_user
    # In prod mode, require either a valid session OR a valid API key user
    user = session_user or header_user
    if not user:
        raise HTTPException(401, "Authentication required (session or API key).")
    return user

@app.post("/auth/register")
def register(req: AuthReq, request: Request):
    try:
        user = create_user(req.email, req.password)
        request.session["email"] = user["email"]
        return {"email": user["email"], "api_key": user["api_key"], "plan": user["plan"]}
    except ValueError:
        raise HTTPException(409, "User already exists")

@app.post("/auth/login")
def login(req: AuthReq, request: Request):
    user = verify_user(req.email, req.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    request.session["email"] = user["email"]
    return {"email": user["email"], "api_key": user["api_key"], "plan": user["plan"]}

@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}

@app.get("/me")
def me(user = Depends(current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return {"email": user["email"], "api_key": user["api_key"], "plan": user.get("plan", "free")}

# ---------- Metrics ----------
@app.get("/v1/metrics")
def metrics():
    return metrics_stub()

# ---------- Analyze pipeline ----------
class AnalyzeOptions(BaseModel):
    check_provenance: bool = True
    check_watermarks: bool = True
    check_audio: bool = True
    check_visual: bool = True
    face_watchlist: list[str] | None = None
    voice_watchlist: list[str] | None = None
    callback_url: str | None = None

async def _pipeline(job_id: str, modality: str, file_path: str, opts: AnalyzeOptions):
    result = {
        "job_id": job_id,
        "status": "running",
        "modality": modality,
        "provenance": {},
        "watermarks": [],
        "video_deepfake": {},
        "image_gen": {},
        "audio_spoof": {},
        "identity": {"face_matches": [], "voice_matches": []},
        "artifacts": {"metadata_flags": [], "hashes": {}},
        "model_versions": {"vision":"v0", "audio":"v0", "provenance":"v0"},
        "limitations": []
    }
    set_job(job_id, result)

    if opts.check_provenance:
        result["provenance"] = check_c2pa(file_path)
        if not result["provenance"].get("c2pa_present"):
            result["limitations"].append("no_c2pa_credentials_found")
    if opts.check_watermarks:
        result["watermarks"] = scan_watermarks(file_path, modality)

    if modality == "image" and opts.check_visual:
        result["image_gen"] = analyze_image(file_path)
        result["image_gen"]["nn_score"] = pseudo_image_score(file_path)
    if modality == "video":
        if opts.check_visual:
            result["video_deepfake"] = analyze_video(file_path)
            result["video_deepfake"]["nn_score"] = pseudo_video_score(file_path)
        if opts.check_audio:
            result["audio_spoof"] = analyze_audio(file_path)
    if modality == "audio" and opts.check_audio:
        result["audio_spoof"] = analyze_audio(file_path)
        result["audio_spoof"]["nn_score"] = pseudo_audio_score(file_path)

    # optional identity sidecar
    sidecar = file_path + ".vector.json"
    if os.path.exists(sidecar):
        try:
            data = json.load(open(sidecar))
            face_vec = data.get("face_vector")
            voice_vec = data.get("voice_vector")
            if face_vec:
                result["identity"]["face_matches"] = match_face(face_vec, opts.face_watchlist)
            if voice_vec:
                result["identity"]["voice_matches"] = match_voice(voice_vec, opts.voice_watchlist)
        except Exception:
            result["limitations"].append("invalid_sidecar_vector")

    fused = fuse(modality, result)
    result.update(fused)
    result["status"] = "completed"
    set_job(job_id, result)

    if opts.callback_url:
        try:
            await post_webhook(opts.callback_url, result)
        except Exception:
            pass

def _save_temp_upload(upload: UploadFile) -> str:
    suffix = os.path.splitext(upload.filename or "")[1] or ""
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(upload.file.read())
    return tmp_path

class EnrollRequest(BaseModel):
    type: str = Field(pattern="^(face|voice)$")
    profile_id: str
    vector: list[float]

# ---- Protected routes (session or API key) ----
@app.post("/v1/watchlist:enroll")
def enroll(req: EnrollRequest, user = Depends(require_auth_or_api_key)):
    id_enroll(profile_id=req.profile_id, typ=req.type, vector=req.vector)
    return {"profile_id": req.profile_id, "type": req.type}

@app.delete("/v1/watchlist/{profile_id}", status_code=204)
def delete_profile(profile_id: str, user = Depends(require_auth_or_api_key)):
    id_delete(profile_id)
    return JSONResponse(status_code=204, content=None)

@app.post("/v1/images:analyze", status_code=202)
async def analyze_image_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: str | None = None,
    user = Depends(require_auth_or_api_key)
):
    try:
        opts = AnalyzeOptions.model_validate_json(options or "{}")
    except Exception as e:
        raise HTTPException(400, f"Invalid options JSON: {e}")
    tmp = _save_temp_upload(file)
    _, stored_path = save_upload(tmp, file.filename or "image")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    set_job(job_id, {"status": "queued"})
    background_tasks.add_task(_pipeline, job_id, "image", stored_path, opts)
    return {"job_id": job_id, "status": "queued"}

@app.post("/v1/audio:analyze", status_code=202)
async def analyze_audio_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: str | None = None,
    user = Depends(require_auth_or_api_key)
):
    try:
        opts = AnalyzeOptions.model_validate_json(options or "{}")
    except Exception as e:
        raise HTTPException(400, f"Invalid options JSON: {e}")
    tmp = _save_temp_upload(file)
    _, stored_path = save_upload(tmp, file.filename or "audio")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    set_job(job_id, {"status": "queued"})
    background_tasks.add_task(_pipeline, job_id, "audio", stored_path, opts)
    return {"job_id": job_id, "status": "queued"}

@app.post("/v1/videos:analyze", status_code=202)
async def analyze_video_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: str | None = None,
    user = Depends(require_auth_or_api_key)
):
    try:
        opts = AnalyzeOptions.model_validate_json(options or "{}")
    except Exception as e:
        raise HTTPException(400, f"Invalid options JSON: {e}")
    tmp = _save_temp_upload(file)
    _, stored_path = save_upload(tmp, file.filename or "video")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    set_job(job_id, {"status": "queued"})
    background_tasks.add_task(_pipeline, job_id, "video", stored_path, opts)
    return {"job_id": job_id, "status": "queued"}

@app.get("/v1/jobs/{job_id}")
def get_job_status(job_id: str, user = Depends(require_auth_or_api_key)):
    job = get_job(job_id)
    if "error" in job:
        raise HTTPException(404, "Job not found")
    return job

# ---------- Stripe: create checkout + webhook ----------
class CheckoutReq(BaseModel):
    # optional: pass a price if you don't set STRIPE_PRICE_PRO_MONTH
    price_id: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    customer_email: Optional[str] = None  # fallback if no session user

@app.post("/billing/create-checkout-session")
def create_checkout_session(
    req: CheckoutReq,
    request: Request,
    user = Depends(current_user)
):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(501, "Billing is not configured on this deployment.")
    price_id = req.price_id or STRIPE_PRICE_PRO_MONTH
    if not price_id:
        raise HTTPException(400, "Missing Stripe price (set STRIPE_PRICE_PRO_MONTH or provide price_id).")

    success_url = req.success_url or (str(request.url_for("index")) + "?billing=success")
    cancel_url = req.cancel_url or (str(request.url_for("pricing_page")) if "pricing_page" in app.router.routes else str(request.base_url) )

    email = (user or {}).get("email") if user else req.customer_email
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=email,
    )
    return {"checkout_url": session.url}

@app.post("/billing/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(501, "No STRIPE_WEBHOOK_SECRET configured.")
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(400, "Invalid webhook signature")

    # Handle a couple common events
    if event["type"] == "checkout.session.completed":
        cs = event["data"]["object"]
        email = cs.get("customer_email")
        if email:
            set_user_plan(email, "pro")

    return {"ok": True}

# A named route for success redirect (optional)
@app.get("/pricing", name="pricing_page", response_class=HTMLResponse)
def pricing_page():
    return spa_index()

# ---------- Webhooks tester ----------
@app.post("/webhooks/test")
async def webhook_test(request: Request):
    sig = request.headers.get("X-Intelliparse-Signature", "")
    body = await request.body()
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except Exception:
        payload = {"raw": body.decode("utf-8", errors="ignore")}
    return {"received": payload, "signature": sig, "length": len(body)}

# ---------- SPA routes ----------
@app.get("/", response_class=HTMLResponse)
def index():
    return spa_index()

@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa_routes(full_path: str):
    if full_path.startswith(("v1/", "assets/", "webhooks/", "billing/")):
        return JSONResponse({"error": "Not Found"}, status_code=404)
    return spa_index()
