# utils/db.py
import os, sqlite3, threading

_DB_PATH = os.environ.get("POWERAI_DB_PATH", "data/powerai.db")
_lock = threading.RLock()

def get_conn():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def migrate():
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        # Fixed-window events
        cur.execute(
            """CREATE TABLE IF NOT EXISTS usage_events (
                api_key TEXT NOT NULL,
                ts INTEGER NOT NULL
            )"""
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_events_key_ts ON usage_events(api_key, ts);")
        # Token-bucket table (shared with Option B)
        cur.execute(
            """CREATE TABLE IF NOT EXISTS usage_buckets (
                api_key TEXT PRIMARY KEY,
                tokens REAL NOT NULL,
                last_refill INTEGER NOT NULL,
                capacity REAL NOT NULL,
                refill_rate REAL NOT NULL
            )"""
        )
        conn.commit()
        conn.close()
