# Job Opportunity Radar

Daily, explainable job discovery and application-preparation pipeline for Jocelyn Grosjean.

This repository is designed as the second real JOSS project. It is deliberately **manual-first**:

- GET-only collection from public ATS job boards;
- deterministic normalization and deduplication;
- explicit eligibility gates;
- explainable 0–100 fit scoring;
- persona/CV recommendation;
- compact daily HTML report;
- local tracker and auditable JSON/JSONL artifacts;
- no automatic application submission;
- no paid API dependency;
- no credentials required for the V0 collectors.

## Supported V0 sources

- Greenhouse public Job Board API
- Lever public Postings API, global and EU instances
- Ashby public Job Postings API

The collector list is company-board based. Add or enable boards in `config/sources.toml`.

## Fast start

```bash
cd job-opportunity-radar

# Offline deterministic demo + tests
./scripts/bootstrap_local.sh

# Open the generated report
open .demo-runtime/runs/latest/report.html
```

## Real daily run

1. Copy `config/sources.example.toml` to `config/sources.toml`.
2. Add target company board slugs and set `enabled = true`.
3. Run:

```bash
./scripts/job-radar \
  --profile config/profile.toml \
  --sources config/sources.toml \
  run --allow-network
```

Runtime data defaults to:

```text
~/.local/share/joss-orchestrator/projects/job-opportunity-radar/
```

Nothing under that runtime root should be committed.

## Core commands

```bash
./scripts/job-radar --sources config/sources.toml doctor
./scripts/job-radar --sources tests/fixtures/sources.toml --runtime-root .demo-runtime run --fixture-dir tests/fixtures
./scripts/job-radar --sources config/sources.toml run --allow-network
./scripts/job-radar --runtime-root ~/.local/share/joss-orchestrator/projects/job-opportunity-radar list --limit 20
./scripts/job-radar --runtime-root ~/.local/share/joss-orchestrator/projects/job-opportunity-radar status
```

## Output contract

Each run creates:

```text
runs/<run_id>/
├── raw/                 # raw source payloads
├── jobs.jsonl           # normalized, authoritative jobs
├── ranked.jsonl         # scored jobs + reasons/gaps
├── report.json          # compact machine-readable digest
├── report.html          # compact daily dashboard
├── events.jsonl         # audit events
└── manifest.json        # hashes, counts, timings, source outcomes
```

SQLite is only an index/tracker. JSON/JSONL artifacts remain authoritative and auditable.

## Safety boundaries

V0 never:

- submits an application;
- stores ATS credentials;
- performs browser automation;
- scrapes authenticated LinkedIn pages;
- uses a paid API;
- sends email or Telegram messages;
- merges or publishes through JOSS automatically.

See `docs/JOSS_BOOTSTRAP_PROMPT.md` for the exact bounded ZCode mission.
