"""B4d5: make three-slot *research* plan exactly follow the independent editorial board.

Daily source scout, article observations and B4d2 editorial selector previously
made different choices from daily_cloud_plan's first-three-raw-headlines slots.
This file creates a new, **unapproved** planner artifact with three consistent
topic assignments. It NEVER invents a real factual script, voice or video.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import argparse
import json
from pathlib import Path

from autopilot.daily_cloud_plan import (
    PLAN_VERSION, PUBLISH_SLOTS, candidate_leads,
)
from autopilot.daily_editorial_board import (
    STATUS as EDITORIAL_STATUS, build_editorial_board,
)
from autopilot.evidence_probe import verify_public_source_url, EvidenceError

RECONCILIATION_STATUS = "B4D5_EDITORIAL_PLAN_SOURCE_RECONCILED_NO_RELEASE"
MAX_INPUT_BYTES = 512_000
MAX_OUTPUT_BYTES = 512_000


class PlanReconciliationRefused(ValueError):
    """A forged, mismatched, privileged or unbounded editorial plan is refused."""


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def align_plan_to_editorial_board(
    plan: object, board: object, scout_report: object, source_observations: object,
) -> dict:
    """Recompute the actual board and never trust an arbitrary JSON handoff."""
    try:
        calculated = build_editorial_board(plan, scout_report, source_observations)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        raise PlanReconciliationRefused("Unsafe or inconsistent source plan inputs") from None
    if (type(board) is not dict
        or board.get("status") != EDITORIAL_STATUS
        or board != calculated
        or board.get("release_authorized") is not False
        or board.get("youtube_upload_enabled") is not False
        or board.get("youtube_schedule_enabled") is not False
        or board.get("scripts_generated") != 0
        or board.get("model_inference_performed") is not False
        or board.get("rights_approved") is not False
        or board.get("fresh_source_corroboration_performed") is not False
        or type(plan) is not dict or plan.get("schema_version") != PLAN_VERSION):
        raise PlanReconciliationRefused("Editorial board was not an authentic unapproved recomputation")
    try:
        eligible = candidate_leads(scout_report, limit=24)
    except ValueError:
        raise PlanReconciliationRefused("Untrusted scout candidates") from None
    if (type(board.get("slots")) is not list or len(board["slots"]) != 3
        or type(plan.get("slots")) is not list or len(plan["slots"]) != 3):
        raise PlanReconciliationRefused("Need exactly three source-scoped episodes")
    aligned = deepcopy(plan)
    seen_urls = set()
    publishers = set()
    for i, ((slot,kind,local,_), item) in enumerate(zip(PUBLISH_SLOTS,board["slots"])):
        old = plan["slots"][i]
        if (type(item) is not dict
            or item.get("episode_id") != old.get("episode_id")
            or item.get("release_slot") != slot
            or item.get("format") != kind or item.get("local_ist") != local
            or item.get("release_authorized") is not False
            or item.get("real_script_exists") is not False
            or item.get("real_media_exists") is not False
            or item.get("rights_approved") is not False
            or item.get("youtube_uploaded") is not False
            or item.get("youtube_scheduled") is not False):
            raise PlanReconciliationRefused("Editorial slot claims unauthorized media or identity")
        preview = item.get("research_lead")
        if preview is None:
            chosen = None
            if item.get("editorial_status") != "NO_DISTINCT_CURRENT_TOPIC_FOUND_RESEARCH_REQUIRED":
                raise PlanReconciliationRefused("Absent lead cannot be research-complete")
        else:
            if (type(preview) is not dict
                or preview.get("source_fact_claims_semantically_verified") is not False
                or type(preview.get("publisher")) is not str
                or type(preview.get("unverified_title")) is not str
                or type(preview.get("unverified_url")) is not str):
                raise PlanReconciliationRefused("Malformed nonassertive editorial lead")
            chosen = next((lead for lead in eligible
                if (lead["publisher"] == preview["publisher"]
                    and lead["title"] == preview["unverified_title"]
                    and lead["url"] == preview["unverified_url"])), None)
            if chosen is None:
                raise PlanReconciliationRefused("Chosen editorial story missing from real scout")
            try:
                verified_url = verify_public_source_url(chosen["url"], chosen["publisher"])
            except EvidenceError:
                raise PlanReconciliationRefused("Editorial story has an unapproved origin") from None
            if (verified_url in seen_urls
                or preview.get("source_id") != sha256(verified_url.encode()).hexdigest()[:24]):
                raise PlanReconciliationRefused("Duplicate or substituted story source")
            seen_urls.add(verified_url)
            publishers.add(chosen["publisher"])
        slot_copy = aligned["slots"][i]
        slot_copy["research_lead"] = deepcopy(chosen)
        slot_copy["editorial_state"] = (
            "UNVERIFIED_LEAD_ONLY" if chosen is not None else "RESEARCH_REQUIRED")
        # This is metadata for source research tasks, NOT a completion flag.
        slot_copy["research_assignment_reconciled_unverified"] = True
        slot_copy["editorial_research_angle_id"] = item["angle_id"]
    if (len(seen_urls) != board.get("distinct_topics_selected")
        or len(publishers) != board.get("distinct_publishers_selected")):
        raise PlanReconciliationRefused("Editorial research diversity counters mismatch")
    aligned["editorial_reconciliation_status"] = RECONCILIATION_STATUS
    aligned["editorial_board_sha256"] = sha256(_canonical(board)).hexdigest()
    aligned["editorial_selected_unverified_topics"] = len(seen_urls)
    aligned["editorial_selected_distinct_publishers"] = len(publishers)
    aligned["editorial_factual_script_count"] = 0
    aligned["editorial_media_count"] = 0
    aligned["editorial_research_origin_verified_not_claims"] = True
    if len(_canonical(aligned)) > MAX_OUTPUT_BYTES:
        raise PlanReconciliationRefused("Daily reconciled source plan is unbounded")
    return aligned


def _read(path: Path) -> object:
    if (not path.is_file() or path.is_symlink()
        or not 2 <= path.stat().st_size <= MAX_INPUT_BYTES):
        raise PlanReconciliationRefused("Missing or unbounded ephemeral source input")
    try:
        return json.loads(path.read_text(encoding="utf8"),
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              PlanReconciliationRefused("Invalid JSON constant")))
    except (json.JSONDecodeError,UnicodeError):
        raise PlanReconciliationRefused("Bad source metadata JSON") from None


def main() -> None:
    ap=argparse.ArgumentParser(description="Unapproved research-plan alignment only")
    ap.add_argument("--plan",type=Path,required=True)
    ap.add_argument("--board",type=Path,required=True)
    ap.add_argument("--scout-report",type=Path,required=True)
    ap.add_argument("--source-observations",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.output.is_symlink() or args.output.exists():
        raise PlanReconciliationRefused("Never overwrite a prior research receipt")
    result=align_plan_to_editorial_board(
        _read(args.plan),_read(args.board),_read(args.scout_report),
        _read(args.source_observations))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,
                                     ensure_ascii=True)+"\n",encoding="utf8")
    print(json.dumps({"status":RECONCILIATION_STATUS,
        "episode_count":3,"distinct_research_assignments":
        result["editorial_selected_unverified_topics"],
        "approved_scripts":0,"youtube_uploads":0,
        "release_authorized":False},sort_keys=True))


if __name__=="__main__":
    main()
