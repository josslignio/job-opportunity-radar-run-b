from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    name: str
    type: str
    company: str
    board: str
    enabled: bool = True
    instance: str = "global"


@dataclass
class Job:
    job_id: str
    source: str
    source_name: str
    company: str
    external_id: str
    title: str
    location: str
    workplace_type: str
    employment_type: str
    url: str
    apply_url: str
    description: str
    department: str = ""
    team: str = ""
    posted_at: str = ""
    updated_at: str = ""
    collected_at: str = ""
    compensation: str = ""
    date_confidence: str = "unknown"
    provenance: dict[str, Any] = field(default_factory=dict)
    raw_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankedJob:
    job: Job
    eligible: bool
    score: float
    persona_key: str
    persona_label: str
    cv: str
    components: dict[str, float]
    reasons: list[str]
    gaps: list[str]
    gates: list[str]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["job"] = self.job.to_dict()
        return data
