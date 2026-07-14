from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

from .config import ConfigError, load_profile, load_sources
from .pipeline import run_pipeline
from .storage import init_index, list_jobs


DEFAULT_RUNTIME = "~/.local/share/joss-orchestrator/projects/job-opportunity-radar"


def _base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-radar", description="Daily explainable job opportunity radar")
    parser.add_argument("--profile", default="config/profile.toml")
    parser.add_argument("--sources", default="config/sources.toml")
    parser.add_argument("--runtime-root", default=DEFAULT_RUNTIME)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Validate configuration and runtime boundaries")
    doctor.add_argument("--fixture-dir")

    run = sub.add_parser("run", help="Run collection, normalization, ranking and reporting")
    run.add_argument("--fixture-dir")
    run.add_argument("--allow-network", action="store_true")

    list_cmd = sub.add_parser("list", help="List indexed jobs")
    list_cmd.add_argument("--limit", type=int, default=20)

    sub.add_parser("status", help="Show latest run manifest")
    return parser


def _doctor(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    sources = load_sources(args.sources)
    enabled = [source for source in sources if source.enabled]
    runtime = Path(args.runtime_root).expanduser().resolve()
    repo = Path.cwd().resolve()
    issues = []
    try:
        runtime.relative_to(repo)
        issues.append("Runtime root is inside the repository")
    except ValueError:
        pass
    if not enabled:
        issues.append("No enabled sources")
    fixture_dir = Path(args.fixture_dir).resolve() if args.fixture_dir else None
    if fixture_dir:
        missing = [source.name for source in enabled if not (fixture_dir / f"{source.name}.json").exists()]
        if missing:
            issues.append("Missing fixtures: " + ", ".join(missing))
    result = {
        "status": "ok" if not issues else "blocked",
        "candidate": profile["identity"]["name"],
        "personas": list(profile["personas"]),
        "enabled_sources": [source.name for source in enabled],
        "runtime_root": str(runtime),
        "runtime_outside_repo": "Runtime root is inside the repository" not in issues,
        "network_default": "disabled",
        "automatic_application": False,
        "incremental_api_cost_usd": 0,
        "issues": issues,
    }
    print(json.dumps(result, indent=2))
    return 0 if not issues else 2


def _status(args: argparse.Namespace) -> int:
    manifest = Path(args.runtime_root).expanduser() / "runs" / "latest" / "manifest.json"
    if not manifest.exists():
        print("No completed run found", file=sys.stderr)
        return 1
    print(manifest.read_text(encoding="utf-8"), end="")
    return 0


def _list(args: argparse.Namespace) -> int:
    db = init_index(Path(args.runtime_root).expanduser())
    try:
        rows = list_jobs(db, args.limit)
    finally:
        db.close()
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _base_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return _doctor(args)
        if args.command == "run":
            manifest = run_pipeline(
                profile_path=args.profile,
                sources_path=args.sources,
                runtime_root=args.runtime_root,
                fixture_dir=args.fixture_dir,
                allow_network=args.allow_network,
            )
            print(json.dumps(manifest, indent=2))
            return 0
        if args.command == "list":
            return _list(args)
        if args.command == "status":
            return _status(args)
        parser.error(f"Unknown command: {args.command}")
    except (ConfigError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0
