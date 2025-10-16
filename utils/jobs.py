from typing import Dict, Any
from datetime import datetime

JOBS: Dict[str, Dict[str, Any]] = {}

def set_job(job_id: str, payload: Dict[str, Any]) -> None:
    payload.setdefault("updated_at", datetime.utcnow().isoformat())
    JOBS[job_id] = payload

def get_job(job_id: str) -> Dict[str, Any]:
    return JOBS.get(job_id, {"error": "not_found"})
