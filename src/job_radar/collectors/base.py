from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from job_radar.models import Job, SourceConfig


class Collector(ABC):
    @abstractmethod
    def url(self, source: SourceConfig) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse(self, source: SourceConfig, payload: object, collected_at: str) -> list[Job]:
        raise NotImplementedError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def make_job_id(source: SourceConfig, external_id: str, url: str) -> str:
    raw = f"{source.type}\n{source.name}\n{external_id}\n{url}".encode("utf-8")
    return sha256(raw).hexdigest()[:24]
