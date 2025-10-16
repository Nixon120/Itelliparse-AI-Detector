import os, json
from typing import Dict, List

WATCHLIST_PATH = "data/watchlist.json"

def _load() -> Dict[str, Dict]:
    if not os.path.exists(WATCHLIST_PATH):
        return {}
    with open(WATCHLIST_PATH, "r") as f:
        return json.load(f)

def _save(db: Dict[str, Dict]) -> None:
    os.makedirs(os.path.dirname(WATCHLIST_PATH), exist_ok=True)
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(db, f)

def enroll(profile_id: str, typ: str, vector: List[float]) -> None:
    db = _load()
    db[profile_id] = {"type": typ, "vector": vector}
    _save(db)

def delete(profile_id: str) -> None:
    db = _load()
    if profile_id in db:
        del db[profile_id]
        _save(db)

def cosine(a: List[float], b: List[float]) -> float:
    num = sum(x*y for x,y in zip(a,b))
    den = (sum(x*x for x in a)**0.5) * (sum(y*y for y in b)**0.5)
    if den == 0: return 0.0
    return max(0.0, min(1.0, num/den))

def match_face(query: List[float], allow: List[str] | None) -> List[Dict]:
    db = _load()
    out = []
    for pid, rec in db.items():
        if rec.get("type") != "face": continue
        if allow and pid not in allow: continue
        sim = cosine(query, rec.get("vector", []))
        if sim >= 0.85:
            out.append({"profile_id": pid, "similarity": sim})
    return out

def match_voice(query: List[float], allow: List[str] | None) -> List[Dict]:
    db = _load()
    out = []
    for pid, rec in db.items():
        if rec.get("type") != "voice": continue
        if allow and pid not in allow: continue
        sim = cosine(query, rec.get("vector", []))
        if sim >= 0.85:
            out.append({"profile_id": pid, "similarity": sim})
    return out
