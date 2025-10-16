# utils/usage.py
import time
from typing import Dict, List, Tuple

# In-memory usage store: api_key -> {"min": [ts...], "day": [ts...]}
_USAGE: Dict[str, Dict[str, List[float]]] = {}

def _now() -> float:
    return time.time()

def _window_cut(ts_list: List[float], window_seconds: int) -> List[float]:
    cutoff = _now() - window_seconds
    # keep only timestamps inside window
    return [t for t in ts_list if t >= cutoff]

def _ensure(api_key: str):
    if api_key not in _USAGE:
        _USAGE[api_key] = {"min": [], "day": []}
    return _USAGE[api_key]

def check_limit(
    api_key: str,
    per_minute: int = 60,
    per_day: int = 5000
) -> Tuple[bool, Dict]:
    """
    Returns (ok, details). ok=False means limit exceeded.
    """
    bucket = _ensure(api_key)
    bucket["min"] = _window_cut(bucket["min"], 60)
    bucket["day"] = _window_cut(bucket["day"], 86400)

    used_min = len(bucket["min"])
    used_day = len(bucket["day"])

    ok = (used_min < per_minute) and (used_day < per_day)
    details = {
        "per_minute": per_minute,
        "per_day": per_day,
        "used_minute": used_min,
        "used_day": used_day,
        "retry_after_seconds": 60 if used_min >= per_minute else 1
    }
    return ok, details

def record_hit(api_key: str) -> None:
    bucket = _ensure(api_key)
    now = _now()
    bucket["min"].append(now)
    bucket["day"].append(now)
