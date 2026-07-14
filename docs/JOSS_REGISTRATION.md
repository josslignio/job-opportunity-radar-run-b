# JOSS registration notes

Do not invent a `.agent/project.toml` schema in this repository.

When registering this as the second JOSS project, ZCode must first inspect the canonical project profile currently used by `weekly-trading-radar`, then create the new profile using that exact schema.

Required logical values:

```text
project_id: job-opportunity-radar
repository: separate Git repository
runtime namespace: job-opportunity-radar
max_incremental_cost_usd: 0
publication: disabled
auto_merge: disabled
deployment: disabled
network: denied by default; explicit bounded GET-only run command allowed
credentials: none for V0
runtime state: outside repository
allowed write paths: src/, tests/, config/, docs/, scripts/
forbidden write paths: runtime root, other JOSS projects, weekly-trading-radar repo
```

Deterministic commands:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
./scripts/job-radar --profile config/profile.toml --sources tests/fixtures/sources.toml --runtime-root .demo-runtime run --fixture-dir tests/fixtures
```

Real network command, human-triggered only at first:

```bash
./scripts/job-radar --profile config/profile.toml --sources config/sources.toml run --allow-network
```
