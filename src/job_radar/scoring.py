from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import re

from .models import Job, RankedJob
from .text import fold


SENIOR_TERMS = ["senior", "lead", "head", "director", "manager", "principal", "vp", "vice president"]


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _matches(text: str, terms: list[str]) -> list[str]:
    value = fold(text)
    return [term for term in terms if fold(term) in value]


def _gate(job: Job, prefs: dict) -> tuple[bool, list[str]]:
    blob = " ".join([job.title, job.location, job.workplace_type, job.employment_type, job.description])
    gates: list[str] = []
    blocked_job = _matches(blob, prefs.get("blocked_job_terms", []))
    if blocked_job:
        gates.append(f"Blocked job term: {blocked_job[0]}")
    blocked_location = _matches(" ".join([job.location, job.description]), prefs.get("blocked_location_terms", []))
    if blocked_location:
        gates.append(f"Blocked location: {blocked_location[0]}")
    workplace = fold(job.workplace_type)
    location = fold(job.location)
    if "hybrid" in workplace and not _matches(location, prefs.get("allowed_location_terms", [])):
        gates.append("Hybrid role outside the allowed geography")
    return not gates, gates


def _persona_score(job: Job, persona: dict) -> tuple[float, list[str], list[str]]:
    title_blob = job.title
    body_blob = " ".join([job.title, job.description, job.department, job.team])
    title_hits = _matches(title_blob, persona.get("title_terms", []))
    skill_hits = _matches(body_blob, persona.get("skill_terms", []))
    title_score = min(18.0, len(title_hits) * 6.0)
    skill_score = min(12.0, len(skill_hits) * 2.0)
    reasons = []
    gaps = []
    if title_hits:
        reasons.append("Title match: " + ", ".join(title_hits[:3]))
    else:
        gaps.append("Title is not a direct persona match")
    if skill_hits:
        reasons.append("Relevant skills: " + ", ".join(skill_hits[:5]))
    else:
        gaps.append("Few explicit matching skills in the description")
    return title_score + skill_score, reasons, gaps


def score_job(job: Job, profile: dict, *, now: datetime | None = None) -> RankedJob:
    now = now or datetime.now(timezone.utc)
    prefs = profile["preferences"]
    eligible, gates = _gate(job, prefs)

    best_key = ""
    best_persona = None
    best_role = -1.0
    best_reasons: list[str] = []
    best_gaps: list[str] = []
    for key, persona in profile["personas"].items():
        role_score, reasons, gaps = _persona_score(job, persona)
        if role_score > best_role:
            best_key = key
            best_persona = persona
            best_role = role_score
            best_reasons = reasons
            best_gaps = gaps
    assert best_persona is not None

    blob = " ".join([job.title, job.location, job.workplace_type, job.employment_type, job.description])
    components: dict[str, float] = {"role": round(best_role, 1)}
    reasons = list(best_reasons)
    gaps = list(best_gaps)

    senior_hits = _matches(job.title, SENIOR_TERMS)
    junior_hits = _matches(job.title, prefs.get("strong_penalty_terms", []))
    if senior_hits:
        seniority = 20.0
        reasons.append(f"Seniority match: {senior_hits[0]}")
    elif junior_hits:
        seniority = 2.0
        gaps.append(f"Seniority mismatch: {junior_hits[0]}")
    else:
        seniority = 11.0
        gaps.append("Seniority is not explicit")
    components["seniority"] = seniority

    allowed_locations = _matches(" ".join([job.location, job.workplace_type, job.description]), prefs.get("allowed_location_terms", []))
    if allowed_locations:
        location_score = 15.0
        reasons.append(f"Geography/workplace match: {allowed_locations[0]}")
    elif "remote" in fold(job.workplace_type):
        location_score = 12.0
        reasons.append("Remote workplace")
    else:
        location_score = 4.0
        gaps.append("Location eligibility needs manual verification")
    components["location"] = location_score

    contract_hits = _matches(blob, prefs.get("preferred_contract_terms", []))
    contract_score = 10.0 if contract_hits else 6.0
    if contract_hits:
        reasons.append(f"Contract match: {contract_hits[0]}")
    else:
        gaps.append("Contract type is not explicit")
    components["contract"] = contract_score

    industry_hits = _matches(blob, prefs.get("preferred_industry_terms", []))
    industry_score = min(10.0, 3.0 + len(industry_hits) * 2.0) if industry_hits else 2.0
    if industry_hits:
        reasons.append("Preferred sector: " + ", ".join(industry_hits[:3]))
    else:
        gaps.append("Sector is not a priority match")
    components["industry"] = industry_score

    persona_skill_hits = _matches(blob, best_persona.get("skill_terms", []))
    evidence_score = min(10.0, len(persona_skill_hits) * 1.5)
    components["evidence"] = round(evidence_score, 1)

    posted = _parse_date(job.posted_at) or _parse_date(job.updated_at)
    freshness_days = int(prefs.get("freshness_days", 21))
    if posted:
        age_days = max(0, (now - posted).days)
        if age_days <= 2:
            freshness = 5.0
        elif age_days <= 7:
            freshness = 4.0
        elif age_days <= freshness_days:
            freshness = 2.5
        else:
            freshness = 0.5
            gaps.append(f"Posting may be stale ({age_days} days)")
        reasons.append(f"Posting age: {age_days} day(s)")
    else:
        freshness = 1.0
        gaps.append("Publication date unavailable")
    components["freshness"] = freshness

    score = round(sum(components.values()), 1)
    if junior_hits:
        score = max(0.0, score - 18.0)
    if not eligible:
        score = min(score, 25.0)

    fp_raw = f"{job.job_id}|{best_key}|{score}|{eligible}".encode("utf-8")
    return RankedJob(
        job=job,
        eligible=eligible,
        score=score,
        persona_key=best_key,
        persona_label=str(best_persona.get("label", best_key)),
        cv=str(best_persona.get("cv", "")),
        components=components,
        reasons=reasons[:8],
        gaps=gaps[:6],
        gates=gates,
        fingerprint=sha256(fp_raw).hexdigest()[:24],
    )


def rank_jobs(jobs: list[Job], profile: dict, *, now: datetime | None = None) -> list[RankedJob]:
    ranked = [score_job(job, profile, now=now) for job in jobs]
    ranked.sort(key=lambda item: (item.eligible, item.score, item.job.posted_at, item.job.title), reverse=True)
    return ranked
