#!/usr/bin/env python3
"""Remove legacy synthetic history only, with exclusive access to the data store."""
import argparse
import json
from pathlib import Path
import re
import shutil
from echo_recon.locking import InstanceLock
from echo_recon.storage import Store


def remove_demos(data):
    data = Path(data).resolve()
    db_path = data / "history.sqlite3"
    if not db_path.exists():
        return 0
    lock = InstanceLock(data / "server.lock").acquire()
    try:
        scratch = data / "scratch"
        # Refuse a redirected root, including Windows junctions. Never treat an
        # external directory as the boundary merely because scratch points to it.
        if scratch.resolve() != scratch:
            raise RuntimeError("Scratch directory is redirected outside its expected location; cleanup refused.")
        store = Store(db_path)
        # Keep the exact serialized non-demo rows unchanged, not just their count.
        with store.connect() as db:
            before = {key: body for key, body in db.execute("SELECT id,body FROM jobs")
                      if json.loads(body).get("demo") is not True}
        deleted = store.remove_legacy_demos()
        for job_id in deleted:
            if not re.fullmatch(r"[a-f0-9]{32}", job_id):
                continue
            folder = scratch / job_id
            if folder.is_symlink():
                folder.unlink()
            elif folder.is_dir() and folder.resolve().is_relative_to(scratch):
                shutil.rmtree(folder)
        with store.connect() as db:
            after = {key: body for key, body in db.execute("SELECT id,body FROM jobs")}
        if before != after:
            raise RuntimeError("Non-demo data changed unexpectedly; stop and inspect the database.")
        return len(deleted)
    finally:
        lock.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["remove-demo"])
    parser.parse_args()
    folder = Path(__file__).resolve().parent / "data"
    try:
        count = remove_demos(folder)
    except RuntimeError as exc:
        raise SystemExit(str(exc) + " Stop the dashboard before maintenance.")
    print(f"Removed {count} legacy demo records. Non-demo history is unchanged.")
