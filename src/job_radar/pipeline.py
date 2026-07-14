from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time
from typing import Any

from .collectors import COLLECTORS
from .collectors.base import utc_now
from .config import load_profile, load_sources
from .dedupe import deduplicate
from .http import get_json
from .report import build_report_payload, render_html
from .scoring import rank_jobs
from .storage import (
    file_sha256, init_index, update_latest, upsert_ranked,
    write_json, write_jsonl,
)


def _run_id(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_pipeline(*, profile_path: str, sources_path: str, runtime_root: str,
                 fixture_dir: str | None = None, allow_network: bool = False,
                 now: datetime | None = None) -> dict[str, Any]:
    started = time.monotonic()
    now = now or datetime.now(timezone.utc)
    run_id = _run_id(now)
    root = Path(runtime_root).expanduser().resolve()
    run_dir = root / "runs" / run_id
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)

    profile = load_profile(profile_path)
    sources = load_sources(sources_path)
    enabled = [source for source in sources if source.enabled]
    if not enabled:
        raise ValueError("No enabled sources. Enable a source or use the fixture source configuration.")

    collected_at = now.isoformat().replace("+00:00", "Z")
    all_jobs = []
    source_results: list[dict] = []
    events: list[dict] = [{"at": collected_at, "event": "run_started", "run_id": run_id}]

    fixture_root = Path(fixture_dir).resolve() if fixture_dir else None
    for source in enabled:
        collector = COLLECTORS[source.type]
        result = {"source": source.name, "type": source.type, "status": "failed", "jobs": 0, "error": ""}
        try:
            fixture = fixture_root / f"{source.name}.json" if fixture_root else None
            if fixture and fixture.exists():
                payload = json.loads(fixture.read_text(encoding="utf-8"))
                mode = "fixture"
            else:
                payload = get_json(collector.url(source), allow_network=allow_network)
                mode = "network"
            raw_path = raw_dir / f"{source.name}.json"
            write_json(raw_path, payload)
            jobs = collector.parse(source, payload, collected_at)
            all_jobs.extend(jobs)
            result.update({"status": "ok", "jobs": len(jobs), "mode": mode, "endpoint": collector.url(source)})
            events.append({"at": utc_now(), "event": "source_collected", "source": source.name, "jobs": len(jobs), "mode": mode})
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            events.append({"at": utc_now(), "event": "source_failed", "source": source.name, "error": result["error"]})
        source_results.append(result)

    if not all_jobs:
        write_jsonl(run_dir / "events.jsonl", events)
        write_json(run_dir / "manifest.json", {
            "run_id": run_id, "status": "failed", "reason": "No jobs collected",
            "source_results": source_results,
        })
        raise RuntimeError("No jobs were collected from any source")

    jobs, duplicates = deduplicate(all_jobs)
    ranked_objects = rank_jobs(jobs, profile, now=now)
    jobs_rows = [job.to_dict() for job in jobs]
    ranked_rows = [item.to_dict() for item in ranked_objects]

    write_jsonl(run_dir / "jobs.jsonl", jobs_rows)
    write_jsonl(run_dir / "ranked.jsonl", ranked_rows)
    write_json(run_dir / "duplicates.json", duplicates)
    report_payload = build_report_payload(run_id, ranked_rows, profile, source_results)
    write_json(run_dir / "report.json", report_payload)
    (run_dir / "report.html").write_text(render_html(report_payload, profile), encoding="utf-8")
    events.append({"at": utc_now(), "event": "run_completed", "run_id": run_id, "jobs": len(jobs_rows)})
    write_jsonl(run_dir / "events.jsonl", events)

    hashes = {}
    for filename in ("jobs.jsonl", "ranked.jsonl", "duplicates.json", "report.json", "report.html", "events.jsonl"):
        hashes[filename] = file_sha256(run_dir / filename)
    completed_at = utc_now()
    manifest = {
        "run_id": run_id,
        "status": "completed",
        "started_at": collected_at,
        "completed_at": completed_at,
        "duration_ms": round((time.monotonic() - started) * 1000, 1),
        "runtime_root": str(root),
        "source_results": source_results,
        "counts": {
            "raw_jobs": len(all_jobs),
            "deduplicated_jobs": len(jobs),
            "duplicates": len(duplicates),
            "eligible": sum(1 for row in ranked_rows if row["eligible"]),
            "shortlisted": report_payload["counts"]["shortlisted"],
        },
        "hashes": hashes,
        "network_allowed": allow_network,
        "fixture_dir": str(fixture_root) if fixture_root else "",
        "automatic_application": False,
        "incremental_api_cost_usd": 0,
    }
    write_json(run_dir / "manifest.json", manifest)

    db = init_index(root)
    try:
        db.execute("INSERT OR REPLACE INTO runs(run_id, started_at, completed_at, status, jobs_count, eligible_count, report_path) VALUES(?,?,?,?,?,?,?)",
                   (run_id, collected_at, completed_at, "completed", len(jobs), manifest["counts"]["eligible"], str(run_dir / "report.html")))
        upsert_ranked(db, ranked_rows, completed_at)
        db.commit()
    finally:
        db.close()
    update_latest(root, run_dir)
    return manifest
