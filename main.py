import os, json, tempfile, uuid, asyncio
from typing import Optional

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field

from utils.storage import save_upload
from utils.jobs import set_job, get_job
from utils.scoring import fuse
from utils.identity import enroll as id_enroll, delete as id_delete, match_face, match_voice
from utils.auth import create_user, verify_user, get_user
from utils.webhook import post_webhook
from detectors.provenance import check_c2pa
from detectors.watermark import scan_watermarks
from detectors.visual import analyze_video
from detectors.imagegen import analyze_image
from detectors.audio import analyze_audio
from ml.models import pseudo_image_score, pseudo_audio_score, pseudo_video_score, metrics_stub

APP_SECRET = os.environ.get("IP_SESSION_SECRET", "dev_session_secret")

app = FastAPI(title="intelliparse API", version="1.1.0")
app.add_middleware(SessionMiddleware, secret_key=APP_SECRET)

# Serve SPA assets if built
if os.path.isdir("web/dist"):
    app.mount("/assets", StaticFiles(directory="web/dist/assets"), name="assets")

def spa_index() -> HTMLResponse:
    path = os.path.join("web", "dist", "index.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>intelliparse</h1><p>Build the frontend to see the UI.</p>")

class AnalyzeOptions(BaseModel):
    check_provenance: bool = True
    check_watermarks: bool = True
    check_audio: bool = True
    check_visual: bool = True
    face_watchlist: list[str] | None = None
    voice_watchlist: list[str] | None = None
    callback_url: str | None = None

# -------- Auth Stub --------
class AuthReq(BaseModel):
    email: str
    password: str

def current_user(request: Request) -> Optional[dict]:
    email = request.session.get("email")
    if not email: return None
    return get_user(email)

@app.post("/auth/register")
def register(req: AuthReq, request: Request):
    try:
        user = create_user(req.email, req.password)
        request.session["email"] = user["email"]
        return {"email": user["email"], "api_key": user["api_key"]}
    except ValueError:
        raise HTTPException(409, "User already exists")

@app.post("/auth/login")
def login(req: AuthReq, request: Request):
    user = verify_user(req.email, req.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    request.session["email"] = user["email"]
    return {"email": user["email"], "api_key": user["api_key"]}

@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}

@app.get("/me")
def me(user = Depends(current_user)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return {"email": user["email"], "api_key": user["api_key"]}

# -------- ML Metrics --------
@app.get("/v1/metrics")
def metrics():
    return metrics_stub()

# -------- Pipeline --------
async def _pipeline(job_id: str, modality: str, file_path: str, opts: AnalyzeOptions, callback_url: Optional[str] = None):
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

    # ML/DL/NN pseudo-scores (deterministic) + existing stubs
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

    # Sidecar embeddings matching
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

    # Webhook callback
    if callback_url:
        try:
            await post_webhook(callback_url, result)
        except Exception:
            # don't crash job if webhook fails
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

@app.post("/v1/watchlist:enroll")
def enroll(req: EnrollRequest):
    id_enroll(profile_id=req.profile_id, typ=req.type, vector=req.vector)
    return {"profile_id": req.profile_id, "type": req.type}

@app.delete("/v1/watchlist/{profile_id}", status_code=204)
def delete_profile(profile_id: str):
    id_delete(profile_id)
    return JSONResponse(status_code=204, content=None)

@app.post("/v1/images:analyze", status_code=202)
async def analyze_image_endpoint(background_tasks: BackgroundTasks,
                                 file: UploadFile = File(...),
                                 options: str | None = None):
    try:
        opts = AnalyzeOptions.model_validate_json(options or "{}")
    except Exception as e:
        raise HTTPException(400, f"Invalid options JSON: {e}")
    tmp = _save_temp_upload(file)
    key, stored_path = save_upload(tmp, file.filename or "image")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    set_job(job_id, {"status": "queued"})
    background_tasks.add_task(_pipeline, job_id, "image", stored_path, opts, opts.callback_url)
    return {"job_id": job_id, "status": "queued"}

@app.post("/v1/audio:analyze", status_code=202)
async def analyze_audio_endpoint(background_tasks: BackgroundTasks,
                                 file: UploadFile = File(...),
                                 options: str | None = None):
    try:
        opts = AnalyzeOptions.model_validate_json(options or "{}")
    except Exception as e:
        raise HTTPException(400, f"Invalid options JSON: {e}")
    tmp = _save_temp_upload(file)
    key, stored_path = save_upload(tmp, file.filename or "audio")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    set_job(job_id, {"status": "queued"})
    background_tasks.add_task(_pipeline, job_id, "audio", stored_path, opts, opts.callback_url)
    return {"job_id": job_id, "status": "queued"}

@app.post("/v1/videos:analyze", status_code=202)
async def analyze_video_endpoint(background_tasks: BackgroundTasks,
                                 file: UploadFile = File(...),
                                 options: str | None = None):
    try:
        opts = AnalyzeOptions.model_validate_json(options or "{}")
    except Exception as e:
        raise HTTPException(400, f"Invalid options JSON: {e}")
    tmp = _save_temp_upload(file)
    key, stored_path = save_upload(tmp, file.filename or "video")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    set_job(job_id, {"status": "queued"})
    background_tasks.add_task(_pipeline, job_id, "video", stored_path, opts, opts.callback_url)
    return {"job_id": job_id, "status": "queued"}

@app.get("/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    job = get_job(job_id)
    if "error" in job:
        raise HTTPException(404, "Job not found")
    return job

@app.get("/", response_class=HTMLResponse)
def index():
    return spa_index()

@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa_routes(full_path: str):
    if full_path.startswith("v1/") or full_path.startswith("assets/"):
        return JSONResponse({"error": "Not Found"}, status_code=404)
    return spa_index()
