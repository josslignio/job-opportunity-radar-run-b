from __future__ import annotations

from urllib.parse import quote

from .base import Collector, canonical_hash, make_job_id
from job_radar.models import Job, SourceConfig
from job_radar.text import html_to_text, normalize_space


class GreenhouseCollector(Collector):
    def url(self, source: SourceConfig) -> str:
        board = quote(source.board, safe="")
        return f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"

    def parse(self, source: SourceConfig, payload: object, collected_at: str) -> list[Job]:
        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise ValueError(f"Invalid Greenhouse payload for {source.name}")
        jobs: list[Job] = []
        for raw in payload["jobs"]:
            if not isinstance(raw, dict):
                continue
            external_id = str(raw.get("id", ""))
            url = normalize_space(raw.get("absolute_url"))
            title = normalize_space(raw.get("title"))
            if not external_id or not title or not url:
                continue
            departments = raw.get("departments") or []
            offices = raw.get("offices") or []
            department = ", ".join(
                normalize_space(item.get("name")) for item in departments
                if isinstance(item, dict) and item.get("name")
            )
            office_text = ", ".join(
                normalize_space(item.get("location") or item.get("name")) for item in offices
                if isinstance(item, dict) and (item.get("location") or item.get("name"))
            )
            location = normalize_space((raw.get("location") or {}).get("name")) or office_text
            raw_hash = canonical_hash(raw)
            jobs.append(Job(
                job_id=make_job_id(source, external_id, url),
                source="greenhouse",
                source_name=source.name,
                company=source.company,
                external_id=external_id,
                title=title,
                location=location,
                workplace_type="remote" if "remote" in location.lower() else "unspecified",
                employment_type="",
                url=url,
                apply_url=url,
                description=html_to_text(raw.get("content")),
                department=department,
                team="",
                posted_at=normalize_space(raw.get("first_published")),
                updated_at=normalize_space(raw.get("updated_at")),
                collected_at=collected_at,
                compensation="",
                date_confidence="first_published" if raw.get("first_published") else "updated_at",
                provenance={"endpoint": self.url(source), "source_name": source.name},
                raw_hash=raw_hash,
            ))
        return jobs
