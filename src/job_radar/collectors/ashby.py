from __future__ import annotations

from urllib.parse import quote

from .base import Collector, canonical_hash, make_job_id
from job_radar.models import Job, SourceConfig
from job_radar.text import html_to_text, normalize_space


class AshbyCollector(Collector):
    def url(self, source: SourceConfig) -> str:
        board = quote(source.board, safe="")
        return f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true"

    def parse(self, source: SourceConfig, payload: object, collected_at: str) -> list[Job]:
        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise ValueError(f"Invalid Ashby payload for {source.name}")
        jobs: list[Job] = []
        for raw in payload["jobs"]:
            if not isinstance(raw, dict) or raw.get("isListed") is False:
                continue
            url = normalize_space(raw.get("jobUrl"))
            title = normalize_space(raw.get("title"))
            external_id = normalize_space(raw.get("id")) or url.rsplit("/", 1)[-1]
            if not title or not url or not external_id:
                continue
            secondary = raw.get("secondaryLocations") or []
            locations = [normalize_space(raw.get("location"))]
            locations.extend(
                normalize_space(item.get("location")) for item in secondary
                if isinstance(item, dict)
            )
            locations = [item for item in locations if item]
            compensation = raw.get("compensation") or {}
            if isinstance(compensation, dict):
                compensation_text = normalize_space(
                    compensation.get("compensationTierSummary")
                    or compensation.get("scrapeableCompensationSalarySummary")
                )
            else:
                compensation_text = ""
            raw_hash = canonical_hash(raw)
            jobs.append(Job(
                job_id=make_job_id(source, external_id, url),
                source="ashby",
                source_name=source.name,
                company=source.company,
                external_id=external_id,
                title=title,
                location="; ".join(dict.fromkeys(locations)),
                workplace_type=normalize_space(raw.get("workplaceType")) or ("remote" if raw.get("isRemote") else "unspecified"),
                employment_type=normalize_space(raw.get("employmentType")),
                url=url,
                apply_url=normalize_space(raw.get("applyUrl")) or url,
                description=normalize_space(raw.get("descriptionPlain")) or html_to_text(raw.get("descriptionHtml")),
                department=normalize_space(raw.get("department")),
                team=normalize_space(raw.get("team")),
                posted_at=normalize_space(raw.get("publishedAt")),
                updated_at=normalize_space(raw.get("updatedAt")),
                collected_at=collected_at,
                compensation=compensation_text,
                date_confidence="published_at" if raw.get("publishedAt") else "unknown",
                provenance={"endpoint": self.url(source), "source_name": source.name},
                raw_hash=raw_hash,
            ))
        return jobs
