# utils/usage_sqlite.py
import time, sqlite3
from typing import Dict, Tuple
from .db import get_conn, migrate

migrate()

def _now() -> int:
    return int(time.time())

def _purge_old(conn: sqlite3.Connection, api_key: str, window_seconds: int) -> None:
    cutoff = _now() - window_seconds
    conn.execute("DELETE FROM usage_events WHERE api_key=? AND ts<?", (api_key, cutoff))

def check_limit_sqlite(api_key: str, per_minute: int, per_day: int) -> Tuple[bool, Dict]:
    conn = get_conn()
    try:
        _purge_old(conn, api_key, 60)
        _purge_old(conn, api_key, 86400)
        now = _now()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM usage_events WHERE api_key=? AND ts>=?", (api_key, now-60))
        used_min = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM usage_events WHERE api_key=? AND ts>=?", (api_key, now-86400))
        used_day = cur.fetchone()[0]
        ok = (used_min < per_minute) and (used_day < per_day)
        details = {
            "per_minute": per_minute,
            "per_day": per_day,
            "used_minute": used_min,
            "used_day": used_day,
            "retry_after_seconds": 60 if used_min >= per_minute else 1
        }
        return ok, details
    finally:
        conn.commit()
        conn.close()

def record_hit_sqlite(api_key: str) -> None:
    conn = get_conn()
    try:
        conn.execute("INSERT INTO usage_events(api_key, ts) VALUES(?,?)", (api_key, _now()))
    finally:
        conn.commit()
        conn.close()
