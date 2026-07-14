from __future__ import annotations

from hashlib import sha256
import re

from .models import Job
from .text import fold


COMPANY_SUFFIXES = re.compile(r"\b(inc|ltd|limited|llc|gmbh|sas|sa|plc)\b")


def fingerprint(job: Job) -> str:
    company = COMPANY_SUFFIXES.sub("", fold(job.company))
    title = fold(job.title)
    location = fold(job.location).replace("remote", "")
    base = "|".join([company.strip(), title.strip(), location.strip()])
    return sha256(base.encode("utf-8")).hexdigest()[:24]


def deduplicate(jobs: list[Job]) -> tuple[list[Job], list[dict]]:
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    seen_fingerprints: dict[str, Job] = {}
    kept: list[Job] = []
    duplicates: list[dict] = []
    for job in jobs:
        fp = fingerprint(job)
        duplicate_of = None
        reason = ""
        if job.job_id in seen_ids:
            duplicate_of, reason = job.job_id, "job_id"
        elif job.url and job.url in seen_urls:
            duplicate_of, reason = job.url, "url"
        elif fp in seen_fingerprints:
            duplicate_of, reason = seen_fingerprints[fp].job_id, "normalized_fingerprint"
        if duplicate_of:
            duplicates.append({"job_id": job.job_id, "duplicate_of": duplicate_of, "reason": reason})
            continue
        seen_ids.add(job.job_id)
        if job.url:
            seen_urls.add(job.url)
        seen_fingerprints[fp] = job
        kept.append(job)
    return kept, duplicates
