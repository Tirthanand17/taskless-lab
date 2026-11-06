"""GitHub-hosted daily planning for FlowMinute's 2 Shorts + 1 long workflow.

Unprivileged and deterministic: NO LLM calls, generated scripts, rendering,
OAuth, publishing, laptop dependency, persistent credentials or paid providers.
Research leads are not verified facts. All three releases remain blocked.
The 48 actual agent roles and 18-task/episode DAG come from agent_org.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from autopilot.agent_org import EpisodeSpec, MasterOrchestrator, ROLES
from autopilot.core import CHANNEL_ID, slot_utc

IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc
PLAN_VERSION = 1
PUBLISH_SLOTS = (
    ("short_am", "short", "11:00", "Short A"),
    ("long", "long", "16:00", "Long"),
    ("short_pm", "short", "20:30", "Short B"),
)
APPROVED_RESEARCH_ORIGINS = {
    "OpenAI": {"openai.com", "www.openai.com"},
    "Google DeepMind": {"deepmind.google", "www.deepmind.google"},
    "The Verge": {"theverge.com", "www.theverge.com"},
    # Article identity is a direct /abs page; the independent RSS hostname
    # is verified as a pinned feed URL, NOT allowed as an article target.
    "arXiv AI": {"arxiv.org"},
}
UNVERIFIED_SCOUT_STATUS = "leads_only_no_publish_authorization"


class PlanError(ValueError):
    """Fail closed rather than promote a draft into a live release."""


def parse_day_ist(raw: str) -> dt.date:
    if not isinstance(raw, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raise PlanError("Date must be YYYY-MM-DD")
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:
        raise PlanError("Invalid calendar date") from exc


def next_research_day(now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(UTC)
    if now.tzinfo is None or now.utcoffset() is None:
        raise PlanError("Timezone-aware clock required")
    tomorrow = now.astimezone(IST).date() + dt.timedelta(days=1)
    return tomorrow.isoformat()


def _review_lead(raw: object) -> dict | None:
    """Sanitize a lead; no feed entry is allowed to assert factual verification."""
    if not isinstance(raw, dict) or raw.get("status") != "unverified_lead":
        return None
    publisher = raw.get("publisher")
    title = raw.get("title")
    link = raw.get("url")
    if publisher not in APPROVED_RESEARCH_ORIGINS:
        return None
    if not isinstance(title, str) or not 12 <= len(title.strip()) <= 240:
        return None
    if not isinstance(link, str) or len(link) > 512:
        return None
    try:
        parsed = urlsplit(link)
        if (parsed.scheme != "https" or parsed.username or parsed.password
            or parsed.port not in (None, 443) or parsed.fragment):
            return None
        host = (parsed.hostname or "").lower()
        if host not in APPROVED_RESEARCH_ORIGINS[publisher]:
            return None
        if publisher == "arXiv AI" and (
            re.fullmatch(r"/abs/[0-9]{4}\.[0-9]{4,5}(?:v[1-9][0-9]*)?",
                         parsed.path) is None
            or parsed.query or parsed.fragment):
            return None
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
    except ValueError:
        return None
    safe_title = " ".join(title.split())
    if not safe_title or any(ord(c) < 32 for c in safe_title):
        return None
    return {
        "publisher": publisher,
        "title": safe_title[:200],
        "url": link,
        "status": "unverified_lead",
        "fact_checked": False,
        "video_ready": False,
    }


def candidate_leads(scout_report: object, limit: int = 9) -> list[dict]:
    """Require the existing scout's no-publication marker, not a vague 'approved' flag."""
    if not isinstance(scout_report, dict):
        raise PlanError("Scout report must be a JSON object")
    if scout_report.get("status") != UNVERIFIED_SCOUT_STATUS:
        raise PlanError("Unexpected scout status or attempted authorization escalation")
    raw = scout_report.get("leads")
    if not isinstance(raw, list) or len(raw) > 1000:
        raise PlanError("Missing or unbounded lead list")
    if not 1 <= limit <= 24:
        raise PlanError("Invalid lead limit")
    seen = set()
    results = []
    for item in raw:
        clean = _review_lead(item)
        if clean is None:
            continue
        fingerprint = (clean["publisher"], clean["title"].casefold())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        results.append(clean)
        if len(results) == limit:
            break
    return results


def build_plan(day_ist: str, *, scout_report: object | None = None,
               generated_at_utc: dt.datetime | None = None,
               channel_id: str = CHANNEL_ID) -> dict:
    """Return evidence-labelled *drafts*, never real scripts/video or upload authority."""
    date = parse_day_ist(day_ist)
    if channel_id != CHANNEL_ID:
        raise PlanError("Wrong channel; never silently publish to another channel")
    clock = generated_at_utc or dt.datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise PlanError("Timezone-aware clock required")
    clock = clock.astimezone(UTC)
    candidates = candidate_leads(scout_report) if scout_report is not None else []
    specs = []
    for slot, kind, _, _ in PUBLISH_SLOTS:
        specs.append(EpisodeSpec(
            episode_id=f"fm_{date.strftime('%Y%m%d')}_{slot}",
            kind=kind,
            language="en",
            priority=80 if kind == "long" else 70,
        ))
    org = MasterOrchestrator(tuple(specs))
    if org.summary()["uploads_enabled"] or org.summary()["scheduling_enabled"]:
        raise PlanError("Draft orchestrator unexpectedly granted publishing authority")
    if len(ROLES) != 48 or org.summary()["departments"] != 8:
        raise PlanError("Agent architecture drift detected")
    slots = []
    for index, (slot, kind, local, label) in enumerate(PUBLISH_SLOTS):
        spec = specs[index]
        graph = org.workflows[spec.episode_id]
        if len(graph.order) != 18:
            raise PlanError("Incomplete task dependency graph")
        lead = candidates[index] if index < len(candidates) else None
        slots.append({
            "episode_id": spec.episode_id,
            "format": kind,
            "release_slot": slot,
            "local_ist": local,
            "release_utc": slot_utc(day_ist, slot),
            "episode_label": label,
            "research_lead": lead,
            "editorial_state": "UNVERIFIED_LEAD_ONLY" if lead else "RESEARCH_REQUIRED",
            "required_handoffs": list(graph.order),
            "agent_handoffs_completed": 0,
            "real_script_exists": False,
            "real_narration_exists": False,
            "real_media_exists": False,
            "rights_approved": False,
            "real_media_qa_passed": False,
            "youtube_uploaded": False,
            "youtube_scheduled": False,
            "release_authorized": False,
            "status": "BLOCKED_PENDING_RESEARCH_FACT_CHECK_AND_REAL_MEDIA",
        })
    return {
        "schema_version": PLAN_VERSION,
        "plan_date_ist": date.isoformat(),
        "generated_at_utc": clock.isoformat(),
        "channel_id": CHANNEL_ID,
        "delivery_track": "cloud_autonomous_agents",
        "plan_kind": "UNPRIVILEGED_RESEARCH_DRAFT_ONLY",
        "all_three_release_slots": len(slots) == 3,
        "specialist_roles": len(ROLES),
        "departments": org.summary()["departments"],
        "task_contracts": sum(len(org.workflows[x.episode_id].order) for x in specs),
        "approved_provider_credentials_connected": False,
        "cloud_media_renderer_connected": False,
        "production_release_ledger_connected": False,
        "cloud_publisher_connected": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "any_content_verified": False,
        "new_billable_resources_enabled": False,
        "maximum_incremental_spend_inr": 0,
        "reference_implementation": "autopilot.agent_org.MasterOrchestrator",
        "research_lead_count": len(candidates),
        "slots": slots,
        "next_gate": "Independent source and factual review; real provider-backed media rendering and rights/audio QA",
        "safety_note": "No content was generated or uploaded. Do not infer publishing readiness from this plan.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="No-secret cloud tomorrow planner; no YouTube writes")
    parser.add_argument("--date", default=None, help="IST date YYYY-MM-DD; default tomorrow")
    parser.add_argument("--scout-report", default=None, help="Existing scout's UNVERIFIED JSON report")
    parser.add_argument("--output", default="out/flowminute-tomorrow-draft.json")
    args = parser.parse_args()
    research = None
    if args.scout_report is not None:
        research = json.loads(Path(args.scout_report).read_text(encoding="utf-8"))
    plan = build_plan(args.date or next_research_day(), scout_report=research)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": plan["plan_kind"],
        "day_ist": plan["plan_date_ist"],
        "episode_slots": len(plan["slots"]),
        "unverified_leads": plan["research_lead_count"],
        "agent_roles": plan["specialist_roles"],
        "required_evidence_handoffs": plan["task_contracts"],
        "uploads_enabled": False,
        "cloud_publisher_connected": False,
    }))


if __name__ == "__main__":
    main()
