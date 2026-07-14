# Architecture

## Purpose

The Job Opportunity Radar is a bounded, auditable daily pipeline. It finds public job postings and prepares a reviewable shortlist. It is not an autonomous applicant.

## Pipeline

```text
public ATS boards
  → GET-only collectors
  → raw payload preservation
  → canonical normalization
  → deterministic deduplication
  → eligibility gates
  → persona + fit scoring
  → HTML/JSON daily digest
  → local tracker index
```

## Sources of truth

Authoritative:

- raw JSON payloads;
- normalized `jobs.jsonl`;
- scored `ranked.jsonl`;
- `events.jsonl`;
- run `manifest.json` and hashes.

Derived/index only:

- SQLite job/tracker index;
- `runs/latest` convenience pointer.

## Boundaries

- Network is denied by default and enabled only with `--allow-network`.
- HTTP is GET-only and restricted to an explicit host allowlist.
- Retries, timeouts and maximum response size are bounded.
- There is no ATS POST/application code in V0.
- There are no credentials, paid APIs, headless browsers or package dependencies.
- Runtime defaults outside the repository.
- A failed source is recorded; it does not erase other successful source results.
- A run with zero collected jobs fails closed.

## Scoring

The score is explainable and componentized:

- role/persona match: 30;
- seniority: 20;
- geography/workplace: 15;
- contract: 10;
- preferred industry: 10;
- explicit evidence/skills: 10;
- freshness: 5.

Hard gates cap a role at 25 and mark it ineligible. Examples: US-only, unsupported hybrid geography, unpaid/internship, commission-only.

## Next product layers

1. Company-board discovery and curated target lists.
2. Gmail ingestion for LinkedIn job alerts, read-only.
3. Application preparation artifacts: CV selection, tailored top section, short cover note and recruiter message.
4. Human-approved tracker status updates and follow-up reminders.
5. Dashboard and scheduled delivery.
6. Form prefill only after enough reviewed applications, with confirmation before submission.
