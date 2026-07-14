from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from .base import Collector, canonical_hash, make_job_id
from job_radar.models import Job, SourceConfig
from job_radar.text import html_to_text, normalize_space


def _epoch_ms(value: object) -> str:
    try:
        number = int(value)
        return datetime.fromtimestamp(number / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OSError):
        return ""


class LeverCollector(Collector):
    def url(self, source: SourceConfig) -> str:
        host = "api.eu.lever.co" if source.instance == "eu" else "api.lever.co"
        board = quote(source.board, safe="")
        return f"https://{host}/v0/postings/{board}?mode=json"

    def parse(self, source: SourceConfig, payload: object, collected_at: str) -> list[Job]:
        if not isinstance(payload, list):
            raise ValueError(f"Invalid Lever payload for {source.name}")
        jobs: list[Job] = []
        for raw in payload:
            if not isinstance(raw, dict):
                continue
            external_id = str(raw.get("id", ""))
            title = normalize_space(raw.get("text"))
            url = normalize_space(raw.get("hostedUrl"))
            if not external_id or not title or not url:
                continue
            categories = raw.get("categories") or {}
            if not isinstance(categories, dict):
                categories = {}
            lists = raw.get("lists") or []
            list_text = " ".join(
                html_to_text(item.get("content")) for item in lists
                if isinstance(item, dict)
            )
            description = " ".join(filter(None, [
                normalize_space(raw.get("descriptionPlain")),
                list_text,
                normalize_space(raw.get("additionalPlain")),
            ]))
            salary = raw.get("salaryRange") or {}
            if isinstance(salary, dict) and salary:
                compensation = " ".join(str(salary.get(k, "")) for k in ("currency", "min", "max", "interval")).strip()
            else:
                compensation = normalize_space(raw.get("salaryDescriptionPlain"))
            raw_hash = canonical_hash(raw)
            jobs.append(Job(
                job_id=make_job_id(source, external_id, url),
                source="lever",
                source_name=source.name,
                company=source.company,
                external_id=external_id,
                title=title,
                location=normalize_space(categories.get("location")),
                workplace_type=normalize_space(raw.get("workplaceType")) or "unspecified",
                employment_type=normalize_space(categories.get("commitment")),
                url=url,
                apply_url=normalize_space(raw.get("applyUrl")) or url,
                description=description,
                department=normalize_space(categories.get("department")),
                team=normalize_space(categories.get("team")),
                posted_at=_epoch_ms(raw.get("createdAt")),
                updated_at=_epoch_ms(raw.get("updatedAt")),
                collected_at=collected_at,
                compensation=compensation,
                date_confidence="created_at" if raw.get("createdAt") else "unknown",
                provenance={"endpoint": self.url(source), "source_name": source.name},
                raw_hash=raw_hash,
            ))
        return jobs
