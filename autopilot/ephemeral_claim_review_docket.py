"""B4d7 source-anchored unverified claim-REVIEW docket, never a factual script.

Recomputes the previously source-locked three-episode research outline
to prevent swapping a third-party excerpt into a different episode.

Two short literal passages/source can help a later reviewer locate claim
candidates. They are NOT model-approved, fact-checked, independent evidence,
licensed reuse, narration, or a production authorization. Dockets are deleted
after this GitHub job, never part of the public artifact.
"""
from __future__ import annotations

from hashlib import sha256
import argparse
import json
from pathlib import Path

from autopilot.public_article_passages import (
    PASSAGE_STATUS, MAX_PASSAGES_PER_SOURCE, MAX_CHARS_PER_PASSAGE,
)
from autopilot.source_locked_script_briefs import (
    build_episode_locked_research, SourceLockedResearchRefused,
)

DOCKET_STATUS = "EPHEMERAL_EPISODE_CLAIM_REVIEW_QUESTIONS_UNVERIFIED"
MAX_INPUT_BYTES = 512_000
MAX_OUTPUT_BYTES = 18_000
QUESTION = (
    "What independently testable claim, if any, does this literal "
    "passage support, and what second primary source corroborates it?"
)


class ClaimDocketRefused(ValueError):
    """Refuse source swaps, forged fact reviews and unbounded literal passages."""


def _sha(data: str) -> str:
    return sha256(data.encode("utf8")).hexdigest()


def build_claim_review_docket(
    original: object, aligned: object, board: object, scout: object,
    evidence: object, briefs: object, ephemeral_passages: object,
) -> dict:
    try:
        expected = build_episode_locked_research(
            original,aligned,board,scout,evidence)
    except (SourceLockedResearchRefused,TypeError,ValueError,KeyError):
        raise ClaimDocketRefused("Cannot establish real source-locked episode research") from None
    if type(briefs) is not dict or briefs != expected:
        raise ClaimDocketRefused("Research episode storyboard was changed")
    if (type(ephemeral_passages) is not dict
        or ephemeral_passages.get("status") != PASSAGE_STATUS
        or ephemeral_passages.get("source_observation_generated_at_utc")
             != evidence["generated_at_utc"]
        or ephemeral_passages.get("not_a_fact_check") is not True
        or ephemeral_passages.get("not_a_rights_clearance") is not True
        or ephemeral_passages.get("not_for_public_artifacts") is not True
        or type(ephemeral_passages.get("sources")) is not list
        or len(ephemeral_passages["sources"]) > 3):
        raise ClaimDocketRefused("Untrusted temporary publisher source passage batch")
    source_by_id = {
        x["source_id"]: x for x in evidence["sources"]
        if x["status"] == "SOURCE_FETCHED_NOT_FACT_CHECKED"
    }
    provided = {}
    for item in ephemeral_passages["sources"]:
        if (type(item) is not dict or
            type(item.get("source_id")) is not str
            or item["source_id"] in provided
            or item["source_id"] not in source_by_id
            or item.get("status") != PASSAGE_STATUS
            or item.get("facts_verified") is not False
            or item.get("rights_approved") is not False
            or item.get("observed_article_sha256") != source_by_id[
                item["source_id"]]["response_sha256"]
            or type(item.get("passages")) is not list
            or len(item["passages"]) > MAX_PASSAGES_PER_SOURCE):
            raise ClaimDocketRefused("Passage batch is not bound to a read publisher page")
        taken=set()
        for p in item["passages"]:
            if (type(p) is not dict
                or set(p) != {
                    "passage_index","literal_excerpt_unverified",
                    "literal_excerpt_sha256",
                    "not_a_semantic_claim_or_fact_review",
                    "not_licensed_for_narration_or_public_reuse"}
                or type(p["passage_index"]) is not int
                or not 0 <= p["passage_index"] < 80
                or p["passage_index"] in taken
                or type(p["literal_excerpt_unverified"]) is not str
                or not 60 <= len(p["literal_excerpt_unverified"]) <= MAX_CHARS_PER_PASSAGE
                or p["literal_excerpt_sha256"] != _sha(
                    p["literal_excerpt_unverified"])
                or p["not_a_semantic_claim_or_fact_review"] is not True
                or p["not_licensed_for_narration_or_public_reuse"] is not True):
                raise ClaimDocketRefused("Untrusted, duplicated or oversized literal passage")
            taken.add(p["passage_index"])
        provided[item["source_id"]] = item
    docket = []
    total_passages = 0
    direct_with_literal = 0
    no_literal = 0
    for brief in briefs["episodes"]:
        src=brief["source_id"]
        if (brief["release_authorized"] is not False
            or brief["factual_script_drafted"] is not False
            or brief["model_calls_made"] != 0):
            raise ClaimDocketRefused("Episode already in production is not a research docket")
        result = provided.get(src)
        if brief["evidence_tier"] != "DIRECT_ARTICLE_BYTES_ONLY":
            if result is not None:
                raise ClaimDocketRefused("Cannot fabricate excerpts for unread RSS/news")
            state="PRIMARY_SOURCE_ARTICLE_NOT_OBSERVED"
        elif result is None or not result["passages"]:
            state="DIRECT_SOURCE_OBSERVED_NO_REVIEWABLE_LITERAL_TEXT"
            no_literal += 1
        else:
            state="SMALL_LITERAL_EXCERPTS_LOCATED_NOT_FACT_CHECKED"
            direct_with_literal += 1
        snippets = [] if result is None else result["passages"]
        total_passages += len(snippets)
        questions = []
        for excerpt in snippets:
            questions.append({
                "source_id": src,
                "source_observation_sha256": brief["source_observation_sha256"],
                "passage_index": excerpt["passage_index"],
                "literal_excerpt_unverified": excerpt["literal_excerpt_unverified"],
                "literal_excerpt_sha256": excerpt["literal_excerpt_sha256"],
                "open_claim_investigation_question": QUESTION,
                "independent_primary_corroboration_present": False,
                "reviewer_claim_supported": False,
                "rights_cleared": False,
                "may_be_read_aloud_or_quoted_in_video": False,
            })
        docket.append({
            "episode_id": brief["episode_id"],
            "format": brief["format"],
            "research_source_id": src,
            "research_evidence_tier": brief["evidence_tier"],
            "claim_investigation_status": state,
            "literal_passage_questions_needing_human_review": questions,
            "factual_script_exists": False,
            "rights_approved": False,
            "youtube_upload_enabled": False,
            "release_authorized": False,
        })
    result = {
        "status": DOCKET_STATUS,
        "plan_day_ist": briefs["plan_day_ist"],
        "three_video_episodes": 3,
        "direct_article_episodes": briefs["direct_article_episode_briefs"],
        "direct_article_episodes_with_short_literal_review_passages": direct_with_literal,
        "direct_article_episodes_without_literal_review_passages": no_literal,
        "short_literal_passage_review_questions": total_passages,
        "unreviewed_quote_reuse_forbidden": True,
        "semantic_claims_verified": 0,
        "independent_primary_corrobations": 0,
        "factual_scripts_generated": 0,
        "rights_approvals": 0,
        "external_ai_calls": 0,
        "youtube_uploads": 0,
        "release_authorized": False,
        "dockets": docket,
    }
    size = len(json.dumps(result,separators=(",",":"),ensure_ascii=True).encode())
    if size > MAX_OUTPUT_BYTES:
        raise ClaimDocketRefused("Research claim docket too large")
    return result


def _read(path: Path) -> object:
    if (not path.is_file() or path.is_symlink()
        or not 2 <= path.stat().st_size <= MAX_INPUT_BYTES):
        raise ClaimDocketRefused("Missing or oversized ephemeral claim input")
    try:
        return json.loads(path.read_text(encoding="utf8"),
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ClaimDocketRefused("Invalid source input constant")))
    except (UnicodeError,json.JSONDecodeError):
        raise ClaimDocketRefused("Bad source-bound input") from None


def main() -> None:
    ap=argparse.ArgumentParser(description="Ephemeral bounded article passage claim questions only")
    for name in ("original-plan","aligned-plan","board","scout",
                 "evidence","briefs","passages"):
        ap.add_argument("--"+name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args=ap.parse_args()
    if (args.output.exists() or args.output.is_symlink()
        or args.output.parent.name != "out"
        or not args.output.name.startswith("flowminute-ephemeral-")):
        raise ClaimDocketRefused("Only new temporary GitHub research dockets allowed")
    report=build_claim_review_docket(*[
        _read(getattr(args,name.replace("-","_")))
        for name in ("original-plan","aligned-plan","board","scout",
                     "evidence","briefs","passages")])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=True,
                                       indent=2)+"\n",encoding="utf8")
    # Only safe numeric counters to public Actions logs, never third-party text.
    print(json.dumps({
        "status": DOCKET_STATUS,
        "three_video_episodes": report["three_video_episodes"],
        "direct_article_episodes": report["direct_article_episodes"],
        "reviewable_direct_article_episodes": report[
            "direct_article_episodes_with_short_literal_review_passages"],
        "unverified_literal_passage_question_count": report[
            "short_literal_passage_review_questions"],
        "semantically_verified_claims": 0,
        "scripts_created": 0,
        "rights_approvals": 0,
        "youtube_uploads": 0,
        "release_authorized": False,
    },sort_keys=True))


if __name__=="__main__":
    main()
