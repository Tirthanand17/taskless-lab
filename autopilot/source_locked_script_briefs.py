"""B4d6 — source-LOCKED creative research handoff for each distinct daily video.

Three original storyboard RESEARCH OUTLINES are bound to the exact observed
article (if any). These are not fact-checked scripts, audio, video, citations
that prove source assertions, or YouTube release permissions.

Uses ONLY the original ephemeral GitHub scout, original article-hash metadata,
and an independently recalculated editorial board/fully reconciled plan.
Public artifacts retain neither publisher article text nor these prompts.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from autopilot.daily_cloud_plan import PUBLISH_SLOTS
from autopilot.daily_editorial_board import STATUS as BOARD_STATUS
from autopilot.evidence_probe import PROBE_STATUS
from autopilot.reconcile_daily_editorial_plan import align_plan_to_editorial_board
from autopilot.script_draft_agent import build_draft_input, ScriptDraftError

STATUS = "B4D6_EPISODE_LOCKED_CREATIVE_RESEARCH_OUTLINE_NO_FACT_APPROVAL"
MAX_BYTES = 512_000
ORIGINAL_VISUALS = {
    "agents": (
        "Draw an original task-handoff diagram with explicit entry and exit states",
        "Animate one consent checkpoint before an autonomous action can proceed",
        "Show a side-by-side original workflow timeline and clearly marked uncertainty",
    ),
    "models": (
        "Draw a reproducible baseline-versus-model comparison with empty result boxes",
        "Animate a prompt being tested while withholding unverified outcome numbers",
        "Show an original evaluation rubric with a limitations and source panel",
    ),
    "data": (
        "Illustrate a tiny original synthetic table with labeled input types",
        "Compare a before-and-after chart with no invented measurements",
        "Animate the steps for validating an illustrative sample dataset",
    ),
    "security": (
        "Draw an original threat path and checkpoint, avoiding real user secrets",
        "Compare an explicitly synthetic authorized and unauthorized request",
        "Show a schematic mitigation tree and clearly marked limitation",
    ),
    "developer_tools": (
        "Draw a reproducible sample API call diagram with placeholder results",
        "Show an original test harness timeline with unfilled measured outcomes",
        "Animate a code change and a before-versus-after review checklist",
    ),
    "general": (
        "Draw a source timeline showing only dates separately verified later",
        "Illustrate the proposed mechanism as a clearly labeled hypothesis",
        "Show what a reproducible experiment and independent check would need",
    ),
}
RESEARCH_QUESTIONS = {
    "short_am": (
        "What does the original source actually claim changed?",
        "Which measurement or reproducible check supports that claim?",
        "What is an important unresolved limitation or alternative explanation?",
    ),
    "long": (
        "Which exact method or mechanism is reported by the original source?",
        "What baseline, date, and comparison are independently observable?",
        "What original small demonstration can a viewer reproduce safely?",
        "What claim is most likely to be overstated or misinterpreted?",
        "Which second independent source would be needed for corroboration?",
        "What rights are needed for any quoted chart, screenshot or graphic?",
    ),
    "short_pm": (
        "What tempting interpretation is unsupported by the source?",
        "Which simple counterexample would test that interpretation?",
        "What remains genuinely unknown until independent review?",
    ),
}


class SourceLockedResearchRefused(ValueError):
    """Unsafe, unaligned or script-promoted source briefs must fail closed."""


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def build_episode_locked_research(
    original_plan: object, aligned_plan: object, board: object,
    scout_report: object, evidence_report: object,
) -> dict:
    try:
        recalculated = align_plan_to_editorial_board(
            original_plan, board, scout_report, evidence_report)
    except (ValueError, KeyError, TypeError):
        raise SourceLockedResearchRefused(
            "Invalid original source research or editorial board") from None
    if (type(aligned_plan) is not dict or aligned_plan != recalculated
        or type(board) is not dict or board.get("status") != BOARD_STATUS
        or type(evidence_report) is not dict
        or evidence_report.get("status") != PROBE_STATUS
        or evidence_report.get("claims_verified") != 0
        or evidence_report.get("scripts_generated") != 0
        or evidence_report.get("youtube_upload_enabled") is not False
        or evidence_report.get("youtube_schedule_enabled") is not False
        or aligned_plan.get("youtube_upload_enabled") is not False
        or aligned_plan.get("youtube_schedule_enabled") is not False):
        raise SourceLockedResearchRefused("Cannot write research on an unaligned or approved plan")
    observed_by_id = {x["source_id"]: x for x in evidence_report["sources"]}
    briefs = []
    count_direct = count_rss = count_unobserved = 0
    for i, (slot, kind, local, _) in enumerate(PUBLISH_SLOTS):
        planned = aligned_plan["slots"][i]
        editorial = board["slots"][i]
        picked = editorial["research_lead"]
        source_id = picked["source_id"] if picked is not None else None
        observation = observed_by_id.get(source_id)
        if planned["episode_id"] != editorial["episode_id"]:
            raise SourceLockedResearchRefused("Inconsistent episode identity")
        for field in ("real_script_exists", "real_narration_exists",
                      "real_media_exists", "rights_approved",
                      "youtube_uploaded", "youtube_scheduled",
                      "release_authorized"):
            if planned.get(field) is not False:
                raise SourceLockedResearchRefused("Production claim in research-only plan")
        family = picked["topic_family"] if picked is not None else "general"
        if family not in ORIGINAL_VISUALS:
            raise SourceLockedResearchRefused("Unreviewed topic taxonomy")
        evidence_tier = (
            "DIRECT_ARTICLE_BYTES_ONLY" if observation and
            observation["status"] == "SOURCE_FETCHED_NOT_FACT_CHECKED"
            else "RSS_ENTRY_ONLY" if observation else "UNOBSERVED"
        )
        locked_model_input = None
        if evidence_tier == "DIRECT_ARTICLE_BYTES_ONLY":
            count_direct += 1
            try:
                locked_model_input = build_draft_input(
                    planned, {"status": PROBE_STATUS,
                              "claims_verified": 0,
                              "youtube_upload_enabled": False,
                              "sources": [observation]})
            except (ScriptDraftError, ValueError, KeyError, TypeError):
                raise SourceLockedResearchRefused(
                    "Cannot bind fetched article to this episode") from None
            if (len(locked_model_input["untrusted_source_records"]) != 1
                or locked_model_input["untrusted_source_records"][0]["source_id"]
                    != source_id
                or locked_model_input["untrusted_source_records"][0]["evidence_type"]
                    != "SOURCE_FETCHED_NOT_FACT_CHECKED"):
                raise SourceLockedResearchRefused("Episode source escaped its scope")
        elif evidence_tier == "RSS_ENTRY_ONLY":
            count_rss += 1
            if picked["source_evidence_level"] != "RSS_ENTRY_OBSERVED_ARTICLE_NOT_READ":
                raise SourceLockedResearchRefused("RSS article-read claim forged")
        else:
            count_unobserved += 1
            if picked is not None and picked["source_evidence_level"] != (
                "SCOUT_HEADLINE_ONLY_UNOBSERVED"):
                raise SourceLockedResearchRefused("Headline claim promoted to article")
        if evidence_tier == "DIRECT_ARTICLE_BYTES_ONLY" and (
            picked["source_evidence_level"] != "ARTICLE_BYTES_OBSERVED_NO_FACT_APPROVAL"):
            raise SourceLockedResearchRefused("Direct source proof mismatched editorial status")
        # Original narrative structure is designed for research producers;
        # it is deliberately NOT usable as a finished factual narration.
        visual = ORIGINAL_VISUALS[family]
        outline = (
            ("HOOK_QUESTION", "Show a clearly posed viewer question, not a proven headline"),
            ("SOURCE_SCOPE", "Mark the publisher and unverified research question"),
            ("DEMONSTRATION", visual[0]),
            ("VERIFY_AND_LIMIT", "Keep result labels blank until independent fact review"),
        ) if kind == "short" else (
            ("HOOK_QUESTION", "Open with a falsifiable question, not an asserted result"),
            ("SOURCE_SCOPE", "Name the original source and what its article does not establish"),
            ("MECHANISM", visual[0]),
            ("BASELINE", "Explain the experimental baseline only after source claim review"),
            ("EXAMPLE_1", visual[1]),
            ("EXAMPLE_2", visual[2]),
            ("COUNTEREXAMPLE", "Investigate alternative hypotheses and reproducible limits"),
            ("FACT_AND_RIGHTS_GATE", "Block narration until claims and licensing are reviewed"),
            ("NEXT_VIEWER_ACTION", "Offer a safe viewer-controlled mini experiment"),
        )
        briefs.append({
            "episode_id": planned["episode_id"],
            "slot": slot, "format": kind, "time_ist": local,
            "angle_id": editorial["angle_id"],
            "source_id": source_id,
            "subject_sha256": picked["subject_sha256"] if picked else None,
            "unverified_topic_title": picked["unverified_title"] if picked else None,
            "evidence_tier": evidence_tier,
            "source_observation_sha256": (
                observation["response_sha256"] if observation else None),
            "research_source_count": 1 if observation else 0,
            "research_questions_needing_review": list(RESEARCH_QUESTIONS[slot]),
            "proposed_original_visuals": list(visual),
            "narrative_structure_not_written_script": [
                {"beat":a,"research_direction":b} for a,b in outline],
            "unverified_one_source_model_proposal_input": locked_model_input,
            "model_permission_granted": False,
            "model_calls_made": 0,
            "draft_ready_for_provider_call": False,
            "factual_script_drafted": False,
            "claims_verified": False,
            "source_rights_approved": False,
            "recorded_voice_exists": False,
            "rendered_media_exists": False,
            "owner_final_watch_approved": False,
            "youtube_uploaded": False,
            "youtube_scheduled": False,
            "release_authorized": False,
        })
    if count_direct + count_rss + count_unobserved != 3:
        raise SourceLockedResearchRefused("Daily creative research slot count mismatch")
    result = {
        "status": STATUS,
        "plan_day_ist": aligned_plan["plan_date_ist"],
        "daily_slots": 3,
        "direct_article_episode_briefs": count_direct,
        "rss_only_episode_briefs": count_rss,
        "unobserved_episode_briefs": count_unobserved,
        "eligible_for_external_model_calls": 0,
        "actual_factual_scripts_generated": 0,
        "actual_media_generated": 0,
        "paid_requests": 0,
        "youtube_uploads": 0,
        "release_authorized": False,
        "canonical_editorial_board_sha256": aligned_plan["editorial_board_sha256"],
        "episodes": briefs,
    }
    if len(_canonical(result)) > MAX_BYTES:
        raise SourceLockedResearchRefused("Unbounded research episode handoff")
    return result


def _read(path: Path) -> object:
    if (not path.is_file() or path.is_symlink()
        or not 2 <= path.stat().st_size <= MAX_BYTES):
        raise SourceLockedResearchRefused("Missing or unbounded ephemeral source file")
    try:
        return json.loads(path.read_text(encoding="utf8"),
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              SourceLockedResearchRefused("Nonfinite source input")))
    except (UnicodeError,json.JSONDecodeError):
        raise SourceLockedResearchRefused("Malformed ephemeral source JSON") from None


def main() -> None:
    ap = argparse.ArgumentParser(description="Three original research outlines, NO FACTS/UPLOAD")
    ap.add_argument("--raw-plan", required=True, type=Path)
    ap.add_argument("--aligned-plan", required=True, type=Path)
    ap.add_argument("--board", required=True, type=Path)
    ap.add_argument("--scout", required=True, type=Path)
    ap.add_argument("--evidence", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise SourceLockedResearchRefused("Do not overwrite previous source research")
    result = build_episode_locked_research(
        _read(args.raw_plan),_read(args.aligned_plan),_read(args.board),
        _read(args.scout),_read(args.evidence))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=True,
                                      indent=2)+"\n",encoding="utf8")
    print(json.dumps({
        "status":STATUS,
        "creative_research_outlines":3,
        "observed_article_bound_briefs":result["direct_article_episode_briefs"],
        "rss_only_briefs":result["rss_only_episode_briefs"],
        "unobserved_briefs":result["unobserved_episode_briefs"],
        "model_calls_made":0,"factual_scripts_created":0,
        "uploads":0,"release_authorized":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
