"""Small persistent job store; no network access."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, updated TEXT, body TEXT)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, job):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO jobs VALUES (?, ?, ?)",
                       (job["id"], job["updated"], json.dumps(job, ensure_ascii=False)))

    def get(self, job_id):
        with self.connect() as db:
            row = db.execute("SELECT body FROM jobs WHERE id=?", (job_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def recent(self, limit=50):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM jobs ORDER BY updated DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def interrupt_old_jobs(self):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM jobs").fetchall()
        for row in rows:
            job = json.loads(row[0])
            if job["status"] in {"running", "cancelling"}:
                job["status"] = "interrupted"
                job["log"].append("Server restarted: assessment incomplete; no automatic resume.")
                for phase in job["phases"]:
                    if phase["status"] in {"running", "pending"}:
                        phase["status"] = "interrupted"
                self.save(job)
