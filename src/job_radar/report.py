from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _badge(score: float, excellent: float, good: float) -> str:
    if score >= excellent:
        return "EXCELLENT"
    if score >= good:
        return "GOOD"
    return "REVIEW"


def build_report_payload(run_id: str, ranked: list[dict], profile: dict, source_results: list[dict]) -> dict:
    prefs = profile["preferences"]
    eligible = [item for item in ranked if item["eligible"]]
    minimum = float(prefs.get("minimum_score", 58))
    top = [item for item in eligible if item["score"] >= minimum]
    max_results = int(prefs.get("max_daily_results", 15))
    return {
        "run_id": run_id,
        "candidate": profile["identity"]["name"],
        "counts": {
            "collected": len(ranked),
            "eligible": len(eligible),
            "shortlisted": len(top),
            "excellent": sum(1 for item in top if item["score"] >= float(prefs.get("excellent_score", 84))),
            "good": sum(1 for item in top if float(prefs.get("good_score", 72)) <= item["score"] < float(prefs.get("excellent_score", 84))),
        },
        "source_results": source_results,
        "top_matches": top[:max_results],
        "manual_first": True,
        "automatic_application": False,
    }


def render_html(payload: dict, profile: dict) -> str:
    prefs = profile["preferences"]
    excellent = float(prefs.get("excellent_score", 84))
    good = float(prefs.get("good_score", 72))
    cards = []
    for item in payload["top_matches"]:
        job = item["job"]
        reasons = "".join(f"<li>{escape(reason)}</li>" for reason in item["reasons"][:5])
        gaps = "".join(f"<li>{escape(gap)}</li>" for gap in item["gaps"][:3])
        cards.append(f"""
        <article class="card">
          <div class="topline">
            <div>
              <h2>{escape(job['title'])}</h2>
              <div class="company">{escape(job['company'])}</div>
            </div>
            <div class="score"><strong>{item['score']:.0f}</strong><span>{_badge(item['score'], excellent, good)}</span></div>
          </div>
          <div class="meta">{escape(job['location'] or 'Location not stated')} · {escape(job['workplace_type'] or 'unspecified')} · {escape(job['employment_type'] or 'contract not stated')}</div>
          <div class="persona">{escape(item['persona_label'])} · CV: {escape(item['cv'])}</div>
          <div class="cols">
            <div><h3>Why it matches</h3><ul>{reasons}</ul></div>
            <div><h3>Verify / gaps</h3><ul>{gaps or '<li>No major gap detected by rules</li>'}</ul></div>
          </div>
          <div class="actions"><a href="{escape(job['url'], quote=True)}">View offer</a><a href="{escape(job['apply_url'], quote=True)}">Open application</a></div>
        </article>
        """)
    if not cards:
        cards.append('<div class="empty">No role passed today\'s minimum score and eligibility gates.</div>')
    counts = payload["counts"]
    source_rows = "".join(
        f"<tr><td>{escape(row['source'])}</td><td>{escape(row['status'])}</td><td>{row.get('jobs', 0)}</td><td>{escape(row.get('error', ''))}</td></tr>"
        for row in payload["source_results"]
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Job Radar — {escape(payload['run_id'])}</title>
<style>
:root{{--bg:#f4f5f7;--panel:#fff;--text:#17191d;--muted:#606773;--line:#dfe3e8;--accent:#15171a}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--text)}}
main{{max-width:980px;margin:0 auto;padding:24px 16px 48px}} header{{display:flex;justify-content:space-between;gap:20px;align-items:flex-end;margin-bottom:14px}} h1{{font-size:27px;margin:0 0 3px}} .sub{{color:var(--muted);font-size:13px}} .stats{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 18px}} .stat{{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:9px 12px;min-width:112px}} .stat strong{{display:block;font-size:20px}} .stat span{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:10px 0;box-shadow:0 1px 2px rgba(0,0,0,.03)}} .topline{{display:flex;justify-content:space-between;gap:16px}} h2{{font-size:18px;margin:0 0 3px}} .company{{font-weight:600;color:var(--muted)}} .score{{text-align:center;min-width:66px}} .score strong{{display:block;font-size:25px;line-height:1}} .score span{{font-size:9px;letter-spacing:.08em;color:var(--muted)}} .meta,.persona{{font-size:12px;color:var(--muted);margin-top:7px}} .persona{{color:#272b31;font-weight:600}}
.cols{{display:grid;grid-template-columns:1.2fr 1fr;gap:18px;margin-top:12px}} h3{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;margin:0 0 5px;color:var(--muted)}} ul{{margin:0;padding-left:18px;font-size:12px;line-height:1.45}} .actions{{display:flex;gap:8px;margin-top:13px}} .actions a{{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;border-radius:7px;padding:7px 10px;font-size:12px;font-weight:650}} .actions a+ a{{background:#fff;color:var(--text);border:1px solid var(--line)}}
section.audit{{margin-top:20px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}} table{{width:100%;border-collapse:collapse;font-size:11px}} th,td{{text-align:left;border-bottom:1px solid var(--line);padding:7px 5px}} .notice{{margin-top:14px;color:var(--muted);font-size:11px}} .empty{{background:#fff;border:1px solid var(--line);padding:20px;border-radius:10px}}
@media(max-width:700px){{header{{display:block}}.cols{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><h1>Daily Job Radar</h1><div class="sub">{escape(payload['candidate'])} · run {escape(payload['run_id'])}</div></div><div class="sub">Manual review required before every application</div></header>
<div class="stats"><div class="stat"><strong>{counts['collected']}</strong><span>collected</span></div><div class="stat"><strong>{counts['eligible']}</strong><span>eligible</span></div><div class="stat"><strong>{counts['shortlisted']}</strong><span>shortlisted</span></div><div class="stat"><strong>{counts['excellent']}</strong><span>excellent</span></div></div>
{''.join(cards)}
<section class="audit"><h3>Source audit</h3><table><thead><tr><th>Source</th><th>Status</th><th>Jobs</th><th>Error</th></tr></thead><tbody>{source_rows}</tbody></table></section>
<div class="notice">This report uses deterministic rules and public job-board data. It does not submit applications and may require manual verification of eligibility, salary, visa and location.</div>
</main></body></html>"""
