"""B4d2: real daily *research triage*, not a fabricated news script.

The existing scout returns 0-24 live RSS leads, while the planner assigned the
first three to 2 Shorts + 1 long even when titles are duplicates and evidence
probe read other URLs. This board ranks *actual structural* observed sources,
avoids repeated subject/claim themes, and prepares DIFFERENT research questions.

It never claims the source headline is true, that independent corroboration
occurred, or that a narration script or original licensed video exists.
All raw source headlines/URLs remain ephemeral in daily GitHub Actions; only
a sanitized hash-only receipt may be retained in a public artifact.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

from autopilot.daily_cloud_plan import (
    PlanError, candidate_leads, parse_day_ist, PUBLISH_SLOTS,
    UNVERIFIED_SCOUT_STATUS,
)
from autopilot.evidence_probe import (
    PROBE_STATUS, verify_public_source_url, EvidenceError,
)

STATUS = "B4D2_SOURCE_LINKED_DIVERSE_RESEARCH_BRIEFS_NO_FACT_APPROVAL"
OBSERVED = frozenset((
    "SOURCE_FETCHED_NOT_FACT_CHECKED",
    "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED",
))
MAX_CANDIDATES = 24
MAX_EVIDENCE_SOURCES = 6
MAX_HISTORY_HASHES = 500
TOKENS = re.compile(r"[a-z0-9]+")
FAMILIES = (
    ("agents", frozenset(("agent", "agents", "workflow", "workflows", "automation",
                          "automate", "autonomous", "assistant", "assistants"))),
    ("models", frozenset(("model", "models", "gemini", "gpt", "llm", "llms",
                          "reasoning", "benchmark", "benchmarks", "inference"))),
    ("data", frozenset(("data", "analytics", "dataset", "datasets", "database",
                        "databases", "spreadsheet", "spreadsheets", "sql"))),
    ("security", frozenset(("security", "privacy", "risk", "risks", "safety",
                            "attack", "attacks", "authentication"))),
    ("developer_tools", frozenset(("code", "coding", "programming", "developer",
                                   "developers", "software", "api", "apis"))),
)
NOT_SUBJECT = frozenset((
    "a","an","the","with","for","and","in","of","on","to","by","from",
    "new","latest","today","this","year","week","ai","what","how",
    "why","can","are","is","an","now","about","more","than","into",
))
ANGLE = {
    "short_am": ("WHAT_TO_TEST_FIRST",
                 "What does the source actually announce, and what must be verified?",
                 "One original side-by-side fact-vs-question illustration"),
    "long": ("EXPLAIN_AND_DEMONSTRATE",
             "How might this work? Require a reproducible example before writing narration.",
             "Source diagram, method, limitations, measured example, counterexample"),
    "short_pm": ("MYTH_VS_LIMITATION",
                 "What common interpretation might be misleading, and how could it be checked independently?",
                 "One precise before/after visual with a visible limitation"),
}


class EditorialTriageRefused(ValueError):
    """Inconsistent, forged, or overprivileged daily research input."""


def _iso(value: object) -> datetime:
    if type(value) is not str or len(value) > 48:
        raise EditorialTriageRefused("Missing bounded timestamp")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if t.tzinfo is None or t.utcoffset() is None:
            raise ValueError("naive")
        return t.astimezone(timezone.utc)
    except (ValueError, OverflowError, TypeError):
        raise EditorialTriageRefused("Invalid timezone-aware timestamp") from None


def _subject_tokens(title: str) -> set[str]:
    return set(TOKENS.findall(title.casefold())) - NOT_SUBJECT


def _family(title: str) -> str:
    tokens = _subject_tokens(title)
    for name, keys in FAMILIES:
        if tokens & keys:
            return name
    return "general"


def _subject_hash(title: str) -> str:
    words = sorted(_subject_tokens(title))
    if not words:
        raise EditorialTriageRefused("No meaningful editorial subject")
    return sha256(" ".join(words).encode("utf-8")).hexdigest()


def _check_history(history: object) -> set[str]:
    if history is None:
        return set()
    if (type(history) is not list or len(history) > MAX_HISTORY_HASHES
        or any(type(x) is not str or re.fullmatch("[0-9a-f]{64}", x) is None
               for x in history)):
        raise EditorialTriageRefused("Invalid prior subject-hash history")
    return set(history)


def _validate_plan(plan: object) -> tuple[str, datetime]:
    if (type(plan) is not dict or plan.get("plan_kind") != "UNPRIVILEGED_RESEARCH_DRAFT_ONLY"
        or plan.get("delivery_track") != "cloud_autonomous_agents"
        or plan.get("youtube_upload_enabled") is not False
        or plan.get("youtube_schedule_enabled") is not False
        or plan.get("any_content_verified") is not False
        or plan.get("new_billable_resources_enabled") is not False
        or plan.get("maximum_incremental_spend_inr") != 0
        or plan.get("approved_provider_credentials_connected") is not False
        or plan.get("cloud_publisher_connected") is not False
        or plan.get("all_three_release_slots") is not True
        or type(plan.get("slots")) is not list
        or len(plan["slots"]) != 3):
        raise EditorialTriageRefused("Unsafe or incomplete daily plan")
    try:
        day = parse_day_ist(plan.get("plan_date_ist")).isoformat()
    except PlanError:
        raise EditorialTriageRefused("Bad daily plan date") from None
    for entry, (slot, kind, local, _) in zip(plan["slots"], PUBLISH_SLOTS):
        if (type(entry) is not dict
            or entry.get("episode_id") != f"fm_{day.replace('-', '')}_{slot}"
            or entry.get("format") != kind
            or entry.get("release_slot") != slot
            or entry.get("local_ist") != local
            or entry.get("release_authorized") is not False
            or entry.get("real_script_exists") is not False
            or entry.get("real_narration_exists") is not False
            or entry.get("real_media_exists") is not False
            or entry.get("real_media_qa_passed") is not False
            or entry.get("agent_handoffs_completed") != 0
            or entry.get("rights_approved") is not False
            or entry.get("youtube_uploaded") is not False
            or entry.get("youtube_scheduled") is not False):
            raise EditorialTriageRefused("Plan slot attempted unauthorized media")
    return day, _iso(plan.get("generated_at_utc"))


def _validate_observations(report: object, clock: datetime) -> dict[str, dict]:
    if (type(report) is not dict or report.get("schema_version") != 1
        or report.get("status") != PROBE_STATUS
        or report.get("claims_verified") != 0
        or report.get("scripts_generated") != 0
        or report.get("audio_or_video_generated") is not False
        or report.get("semantic_corroboration_performed") is not False
        or report.get("source_body_persisted") is not False
        or report.get("youtube_upload_enabled") is not False
        or report.get("youtube_schedule_enabled") is not False
        or report.get("production_credentials_used") is not False
        or report.get("billed_provider_calls") != 0
        or type(report.get("sources")) is not list
        or len(report["sources"]) > MAX_EVIDENCE_SOURCES):
        raise EditorialTriageRefused("Unsafe source observation batch")
    if abs((clock - _iso(report.get("generated_at_utc"))).total_seconds()) > 86400:
        raise EditorialTriageRefused("Scout and source observation clocks differ")
    count = report.get("source_probes_attempted")
    if type(count) is not int or not 0 <= count <= MAX_EVIDENCE_SOURCES:
        raise EditorialTriageRefused("Inconsistent observation attempt limit")
    if (report.get("sources_observed_total") != len(report["sources"])
        or count != len(report["sources"]) + report.get("sources_failed", -1)
        or report.get("sources_fetched", -1) != sum(
            v.get("status") == "SOURCE_FETCHED_NOT_FACT_CHECKED"
            for v in report["sources"] if type(v) is dict)
        or report.get("feed_entries_observed_only", -1) != sum(
            v.get("status") == "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED"
            for v in report["sources"] if type(v) is dict)):
        raise EditorialTriageRefused("Invented source observation counters")
    records = {}
    for item in report["sources"]:
        if type(item) is not dict or item.get("status") not in OBSERVED:
            raise EditorialTriageRefused("Unknown observed-source status")
        publisher, url = item.get("publisher"), item.get("source_url")
        try:
            url = verify_public_source_url(url, publisher)
        except EvidenceError:
            raise EditorialTriageRefused("Unapproved source origin") from None
        sid = sha256(url.encode("utf-8")).hexdigest()[:24]
        body_digest = item.get("response_sha256")
        if (item.get("source_id") != sid
            or type(body_digest) is not str
            or re.fullmatch("[0-9a-f]{64}", body_digest) is None
            or type(item.get("title")) is not str
            or not 12 <= len(item["title"]) <= 200
            or item.get("facts_verified") is not False
            or item.get("rights_verified") is not False
            or item.get("youtube_release_authorized") is not False
            or item.get("source_text_or_image_stored") is not False):
            raise EditorialTriageRefused("Forged observed source evidence")
        observed = _iso(item.get("observed_at_utc"))
        if abs((observed - clock).total_seconds()) > 86400:
            raise EditorialTriageRefused("Stale source observation")
        if item["status"] == "SOURCE_FETCHED_NOT_FACT_CHECKED":
            if (item.get("http_status") != 200
                or item.get("body_bytes_hashed", -1) < 96
                or item.get("claim_level_evidence_extracted") is not False):
                raise EditorialTriageRefused("Direct article bytes not observed")
        else:
            if (item.get("source_article_fetched") is not False
                or type(item.get("feed_entry_sha256")) is not str
                or re.fullmatch("[0-9a-f]{64}", item["feed_entry_sha256"]) is None):
                raise EditorialTriageRefused("RSS entry falsely promoted to article")
        if sid in records:
            raise EditorialTriageRefused("Repeated source ID")
        records[sid] = item
    return records


def _scout_candidates(scout: object, observed: dict, now: datetime) -> list[dict]:
    if (type(scout) is not dict or scout.get("status") != UNVERIFIED_SCOUT_STATUS
        or type(scout.get("leads")) is not list):
        raise EditorialTriageRefused("Unexpected unverified scout input")
    if abs((now - _iso(scout.get("generated_at_utc"))).total_seconds()) > 86400:
        raise EditorialTriageRefused("Plan and live scout clocks differ")
    candidates = candidate_leads(scout, limit=MAX_CANDIDATES)
    pub_dates = {}
    for raw in scout["leads"]:
        if type(raw) is not dict:
            continue
        original_title = raw.get("title")
        if type(original_title) is not str:
            continue
        safe_title = " ".join(original_title.split())[:200]
        key = (raw.get("publisher"), safe_title, raw.get("url"))
        pub_dates[key] = raw.get("published_utc")
    result = []
    seen_urls = set()
    for lead in candidates:
        try:
            url = verify_public_source_url(lead["url"], lead["publisher"])
        except EvidenceError:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        raw_date = pub_dates.get((lead["publisher"], lead["title"], url))
        # RSS scout already enforces 96h; independently reject stale and
        # future titles when the timestamp is supplied. Never guess a date.
        if raw_date is not None:
            try:
                published = _iso(raw_date)
            except EditorialTriageRefused:
                continue
            age = (now - published).total_seconds()
            if age < 0 or age > 96*3600:
                continue
        try:
            topic_hash = _subject_hash(lead["title"])
        except EditorialTriageRefused:
            continue
        sid = sha256(url.encode("utf-8")).hexdigest()[:24]
        evidence = observed.get(sid)
        if evidence is not None and (
            evidence.get("publisher") != lead["publisher"]
            or evidence.get("title") != lead["title"]):
            raise EditorialTriageRefused("Article observed with mismatched headline")
        result.append({
            "lead": lead, "family": _family(lead["title"]),
            "subject_hash": topic_hash,
            "source_id": sid,
            "observation": evidence,
            "tokens": _subject_tokens(lead["title"]),
        })
    return result


def _freshness_order(rows: list[dict]) -> list[dict]:
    # Stable, pre-ranked scout RSS order; observed pages before RSS fallback
    # before unobserved headlines. No synthetic "truth" weighting.
    weight = { "SOURCE_FETCHED_NOT_FACT_CHECKED": 0,
               "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED": 1 }
    return sorted(
        rows, key=lambda x: weight.get(
            (x["observation"] or {}).get("status"), 2))


def _related(first: dict, other: dict) -> bool:
    if first["subject_hash"] == other["subject_hash"]:
        return True
    x,y = first["tokens"], other["tokens"]
    j = len(x & y) / len(x | y) if x | y else 0
    return j >= 0.48


def build_editorial_board(
    plan: object, scout_report: object, evidence_report: object,
    *, previous_subject_hashes: object = None,
) -> dict:
    """Three distinct nonassertive research briefs, without promoting facts.

    A story without an observed original source can be an unverified RESEARCH
    TASK, not a ready-to-write source-backed narrated script.
    """
    day, now = _validate_plan(plan)
    observed = _validate_observations(evidence_report, now)
    candidates = _freshness_order(_scout_candidates(scout_report, observed, now))
    recent = _check_history(previous_subject_hashes)
    candidates = [c for c in candidates if c["subject_hash"] not in recent]
    selected: list[dict] = []
    board = []
    for index, (slot,kind,local,_) in enumerate(PUBLISH_SLOTS):
        # Prefer a new family AND a distinct independent publisher; fall
        # back to different subject with same family only if necessary.
        available = [x for x in candidates if x not in selected
                     and not any(_related(x,y) for y in selected)]
        if available:
            scored = sorted(enumerate(available), key=lambda item: (
                item[1]["family"] in {v["family"] for v in selected},
                item[1]["lead"]["publisher"] in {
                    v["lead"]["publisher"] for v in selected},
                # Long: prioritize actually fetched explainer/article metadata.
                0 if item[1]["observation"] and
                     item[1]["observation"]["status"] == "SOURCE_FETCHED_NOT_FACT_CHECKED"
                   else 1,
                item[0],
            ))
            pick = scored[0][1]
            selected.append(pick)
            src = pick["observation"]
            evidence_level = (
                "ARTICLE_BYTES_OBSERVED_NO_FACT_APPROVAL" if src and
                src["status"] == "SOURCE_FETCHED_NOT_FACT_CHECKED"
                else "RSS_ENTRY_OBSERVED_ARTICLE_NOT_READ" if src
                else "SCOUT_HEADLINE_ONLY_UNOBSERVED"
            )
            preview = {
                "publisher": pick["lead"]["publisher"],
                "unverified_title": pick["lead"]["title"],
                "unverified_url": pick["lead"]["url"],
                "source_id": pick["source_id"],
                "subject_sha256": pick["subject_hash"],
                "topic_family": pick["family"],
                "source_evidence_level": evidence_level,
                "article_bytes_observed": evidence_level.startswith("ARTICLE_BYTES"),
                "source_digest": src["response_sha256"] if src else None,
                "source_fact_claims_semantically_verified": False,
            }
        else:
            preview = None
        angle,question,visual = ANGLE[slot]
        board.append({
            "episode_id": plan["slots"][index]["episode_id"],
            "release_slot": slot,
            "format": kind,
            "local_ist": local,
            "research_lead": preview,
            "angle_id": angle,
            "research_question_not_factual_claim": question,
            "proposed_original_visual_to_research": visual,
            "editorial_status": (
                "EVIDENCE_OBSERVED_PENDING_FACT_AND_RIGHTS_REVIEW"
                if preview and preview["article_bytes_observed"] else
                "HEADLINE_ONLY_NEEDS_SOURCE_RESEARCH" if preview else
                "NO_DISTINCT_CURRENT_TOPIC_FOUND_RESEARCH_REQUIRED"
            ),
            "factual_narration_draft_exists": False,
            "real_script_exists": False,
            "rights_approved": False,
            "human_final_watch_approved": False,
            "real_media_exists": False,
            "youtube_uploaded": False,
            "youtube_scheduled": False,
            "release_authorized": False,
        })
    return {
        "schema_version": 1, "status": STATUS,
        "plan_date_ist": day, "generated_at_utc": now.isoformat(),
        "episode_count": 3, "candidate_count": len(candidates),
        "distinct_topics_selected": len(selected),
        "article_bytes_observed_selected": sum(
            x["research_lead"] is not None and
            x["research_lead"]["article_bytes_observed"] for x in board),
        "rss_entries_only_selected": sum(
            x["research_lead"] is not None and
            x["research_lead"]["source_evidence_level"] ==
                "RSS_ENTRY_OBSERVED_ARTICLE_NOT_READ" for x in board),
        "distinct_publishers_selected": len({
            x["lead"]["publisher"] for x in selected}),
        "distinct_subject_hashes": len({x["subject_hash"] for x in selected}),
        "data_is_not_live_fact_corroboration": True,
        "scripts_generated": 0,
        "billable_api_calls": 0, "model_inference_performed": False,
        "rights_approved": False, "fresh_source_corroboration_performed": False,
        "youtube_upload_enabled": False, "youtube_schedule_enabled": False,
        "release_authorized": False, "slots": board,
    }


def sanitized_public_receipt(board: object) -> dict:
    """Safe hash-only tiny public metadata; no headlines or article URLs."""
    if (type(board) is not dict or board.get("status") != STATUS
        or board.get("release_authorized") is not False
        or board.get("youtube_upload_enabled") is not False
        or board.get("youtube_schedule_enabled") is not False
        or board.get("scripts_generated") != 0
        or type(board.get("slots")) is not list or len(board["slots"]) != 3):
        raise EditorialTriageRefused("Cannot make receipt from unsafe board")
    slots = []
    for item in board["slots"]:
        if (type(item) is not dict or item.get("release_authorized") is not False
            or item.get("real_script_exists") is not False
            or item.get("real_media_exists") is not False):
            raise EditorialTriageRefused("Unsafe editorial slot")
        lead=item.get("research_lead")
        slots.append({
            "episode_id": item["episode_id"],
            "angle_id": item["angle_id"],
            "research_status": item["editorial_status"],
            "subject_sha256": lead["subject_sha256"] if lead else None,
            "source_id": lead["source_id"] if lead else None,
            "article_bytes_observed": bool(lead and lead["article_bytes_observed"]),
            "youtube_uploaded": False, "release_authorized": False,
        })
    body = {
        "status": "B4D2_SANITIZED_DAILY_EDITORIAL_RECEIPT_NO_CONTENT",
        "plan_date_ist": board["plan_date_ist"],
        "selected_distinct_topics": board["distinct_topics_selected"],
        "direct_sources_observed": board["article_bytes_observed_selected"],
        "headlines_urls_source_bodies_and_scripts_included": False,
        "fresh_original_scripts_completed": 0,
        "real_youtube_uploads": 0, "release_authorized": False,
        "slots": slots,
    }
    body["receipt_sha256"]=sha256(json.dumps(
        body,sort_keys=True,separators=(",",":"),ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    return body


def main() -> None:
    p=argparse.ArgumentParser(description="Daily original source triage; no scripts or publish")
    p.add_argument("--plan",required=True,type=Path)
    p.add_argument("--scout-report",required=True,type=Path)
    p.add_argument("--evidence",required=True,type=Path)
    p.add_argument("--board-output",required=True,type=Path)
    p.add_argument("--public-receipt-output",required=True,type=Path)
    args=p.parse_args()
    def read_small(path: Path):
        if not path.is_file() or path.stat().st_size>512_000:
            raise EditorialTriageRefused("Missing or oversized local draft input")
        return json.loads(path.read_text(encoding="utf-8"))
    board=build_editorial_board(
        read_small(args.plan),read_small(args.scout_report),
        read_small(args.evidence))
    receipt=sanitized_public_receipt(board)
    for dest,data in (
        (args.board_output,board),(args.public_receipt_output,receipt),
    ):
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(data,indent=2,sort_keys=True,
                                   ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":STATUS,"episode_count":3,
        "distinct_topics_selected":board["distinct_topics_selected"],
        "direct_sources_observed":board["article_bytes_observed_selected"],
        "scripts_generated":0,"billable_api_calls":0,
        "youtube_uploaded_or_scheduled":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
