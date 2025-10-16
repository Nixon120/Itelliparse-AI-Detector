# utils/usage_bucket.py
import time, sqlite3
from typing import Dict, Tuple
from .db import get_conn, migrate

migrate()

def _now() -> int:
    return int(time.time())

def init_bucket(api_key: str, capacity: float, refill_rate: float) -> None:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT api_key FROM usage_buckets WHERE api_key=?", (api_key,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO usage_buckets(api_key, tokens, last_refill, capacity, refill_rate) VALUES(?,?,?,?,?)",
                (api_key, capacity, _now(), capacity, refill_rate)
            )
    finally:
        conn.commit()
        conn.close()

def _refill(tokens: float, last_refill: int, capacity: float, refill_rate: float) -> float:
    elapsed = max(0, _now() - last_refill)
    return min(capacity, tokens + elapsed * refill_rate)

def take(api_key: str, cost: float, capacity: float, refill_rate: float) -> Tuple[bool, Dict]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT tokens, last_refill, capacity, refill_rate FROM usage_buckets WHERE api_key=?", (api_key,))
        row = cur.fetchone()
        now = _now()
        if row is None:
            tokens = capacity
            last_refill = now
            cur.execute(
                "INSERT INTO usage_buckets(api_key, tokens, last_refill, capacity, refill_rate) VALUES(?,?,?,?,?)",
                (api_key, tokens, last_refill, capacity, refill_rate)
            )
        else:
            tokens, last_refill, capacity_db, refill_rate_db = row
            if capacity_db and capacity_db != capacity:
                capacity = capacity_db
            if refill_rate_db and refill_rate_db != refill_rate:
                refill_rate = refill_rate_db

        cur.execute("SELECT tokens, last_refill, capacity, refill_rate FROM usage_buckets WHERE api_key=?", (api_key,))
        tokens, last_refill, capacity, refill_rate = cur.fetchone()

        tokens = _refill(tokens, last_refill, capacity, refill_rate)
        if tokens >= cost:
            tokens -= cost
            cur.execute("UPDATE usage_buckets SET tokens=?, last_refill=? WHERE api_key=?", (tokens, now, api_key))
            ok = True
            retry_after = 0
        else:
            deficit = cost - tokens
            retry_after = int(deficit / refill_rate) if refill_rate > 0 else 60
            ok = False

        details = {
            "capacity": capacity,
            "refill_rate_per_sec": refill_rate,
            "tokens_remaining": tokens,
            "retry_after_seconds": retry_after
        }
        return ok, details
    finally:
        conn.commit()
        conn.close()
