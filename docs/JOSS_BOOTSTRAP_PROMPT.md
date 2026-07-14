# Prompt ZCode — bootstrap bounded JOSS project

```text
JOB OPPORTUNITY RADAR — SECOND JOSS PROJECT — BOUNDED V0 BUILD

Important current-state constraint:
- Do not touch, interrupt, enqueue into, or modify the currently running Weekly Trading Radar canonical technical shadow run.
- Treat weekly-trading-radar as read-only except for inspecting the canonical JOSS project-profile schema and project registry format.
- Build this project in a separate repository and a separate JOSS runtime namespace.

Starter bundle:
- Use the provided job-opportunity-radar repository as the V0 baseline.
- Do not rewrite it from scratch before running its offline tests and demo.

Mission:
1. Create a new local Git repository at:
   /Users/jocelyngrosjean/job-opportunity-radar
2. Copy/import the starter bundle there.
3. Initialize Git on main and make one clean baseline commit.
4. Run the offline test suite with the Python interpreter already available locally. Do not install packages.
5. Run the fixture demo and inspect the manifest, JSONL outputs and HTML report.
6. Inspect the canonical project profile and registry schema from the existing JOSS repository read-only.
7. Register project_id job-opportunity-radar using the exact existing schema, with strict project isolation.
8. Add a verified initial source list for Jocelyn's three personas:
   - AI / Automation Project Manager
   - Growth / Marketing Automation
   - Crypto Affiliate / KOL / Business Development
9. Verify every ATS board slug before enabling it. Prefer public Greenhouse, Lever and Ashby endpoints.
10. Execute one bounded network shadow run only after doctor passes.

Hard constraints:
- max_incremental_cost_usd = 0;
- no paid API and no uncertain-cost fallback;
- no package installation;
- no authenticated LinkedIn scraping;
- no browser automation;
- no ATS POST/application submission;
- no automatic email/Telegram send in V0;
- no publication, deployment, push, merge or auto-merge without explicit human instruction;
- no credential persistence;
- GET-only network access to the explicit ATS host allowlist;
- bounded timeouts, retries and response size;
- runtime state outside both repositories;
- JSON/JSONL artifacts authoritative, SQLite index-only;
- no cross-project queues, caches, lessons or worktrees;
- fail closed if zero jobs are collected or config integrity fails.

Candidate constraints already defined in config/profile.toml:
- senior/lead/head/manager/director roles;
- remote Europe, worldwide or compatible EMEA geography;
- French native, fluent English, immediately available;
- prioritize AI/automation, growth automation, fintech, crypto/Web3/exchanges;
- reject US-only without compatibility, unsupported hybrid geography, internship/unpaid and commission-only;
- recommend exactly one persona and CV per role;
- never invent skills, work authorization, salary, visa status or experience.

Required verification:
- offline tests pass;
- fixture run is deterministic and creates raw JSON, jobs.jsonl, ranked.jsonl, report.json, report.html, events.jsonl and manifest.json;
- all run artifacts are outside the managed repo for real runs;
- source failures are audited;
- no duplicate jobs in the shortlist;
- hard-gated jobs cannot appear as eligible;
- HTML links point only to the original offer/application URLs;
- repository remains clean after real run;
- JOSS registry has a unique project key;
- no contamination with weekly-trading-radar.

Final delivery:
1. Exact Git state and commit.
2. Test output and fixture-demo verdict.
3. JOSS registry/profile paths and isolation proof.
4. Enabled source list with verified endpoint per company.
5. First network shadow-run counts and report path.
6. P0/P1/P2/P3 findings.
7. Concise continuation handoff.
8. Stop. Do not start auto-application, dashboard or Learning A–D in this run.
```
