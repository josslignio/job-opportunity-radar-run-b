from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import shutil
import sqlite3
from typing import Iterable, Any


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    atomic_write(path, content)


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_latest(runtime_root: Path, run_dir: Path) -> None:
    latest_dir = runtime_root / "runs" / "latest"
    temp_link = runtime_root / "runs" / ".latest.tmp"
    try:
        if temp_link.exists() or temp_link.is_symlink():
            temp_link.unlink()
        temp_link.symlink_to(run_dir.name, target_is_directory=True)
        os.replace(temp_link, latest_dir)
    except OSError:
        if latest_dir.exists() or latest_dir.is_symlink():
            if latest_dir.is_dir() and not latest_dir.is_symlink():
                shutil.rmtree(latest_dir)
            else:
                latest_dir.unlink()
        shutil.copytree(run_dir, latest_dir)


def init_index(runtime_root: Path) -> sqlite3.Connection:
    runtime_root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(runtime_root / "index.sqlite3")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        company TEXT NOT NULL,
        title TEXT NOT NULL,
        location TEXT NOT NULL,
        url TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        latest_score REAL NOT NULL,
        persona_key TEXT NOT NULL,
        eligible INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'found'
    );
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        status TEXT NOT NULL,
        jobs_count INTEGER NOT NULL DEFAULT 0,
        eligible_count INTEGER NOT NULL DEFAULT 0,
        report_path TEXT
    );
    CREATE TABLE IF NOT EXISTS application_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT ''
    );
    """)
    db.commit()
    return db


def upsert_ranked(db: sqlite3.Connection, ranked_rows: list[dict], seen_at: str) -> None:
    for item in ranked_rows:
        job = item["job"]
        db.execute("""
        INSERT INTO jobs(job_id, company, title, location, url, first_seen, last_seen,
                         latest_score, persona_key, eligible, status)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'found')
        ON CONFLICT(job_id) DO UPDATE SET
            last_seen=excluded.last_seen,
            latest_score=excluded.latest_score,
            persona_key=excluded.persona_key,
            eligible=excluded.eligible,
            company=excluded.company,
            title=excluded.title,
            location=excluded.location,
            url=excluded.url
        """, (
            job["job_id"], job["company"], job["title"], job["location"], job["url"],
            seen_at, seen_at, item["score"], item["persona_key"], int(item["eligible"]),
        ))
    db.commit()


def list_jobs(db: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = db.execute("""
      SELECT job_id, company, title, location, latest_score, persona_key, eligible, status, url, last_seen
      FROM jobs
      ORDER BY eligible DESC, latest_score DESC, last_seen DESC
      LIMIT ?
    """, (limit,)).fetchall()
    keys = ["job_id", "company", "title", "location", "score", "persona", "eligible", "status", "url", "last_seen"]
    return [dict(zip(keys, row)) for row in rows]
