"""B4d1: retain *sanitized* GitHub-hosted tomorrow research-plan receipts.

This is REAL cloud-operational evidence packaging, not a model/mock of an
uploader. It consumes the existing daily GitHub scout -> source-observation ->
48-agent draft planner and emits ONE tiny public-metadata-only JSON manifest.

This public repo must not store raw source bodies, headlines, article URLs,
personal data, paid provider content, raw media, credentials, or signed
human/owner approvals in Actions artifacts. SHA256 is integrity, NOT signature.
Every content/release authorization remains false.
"""
from __future__ import annotations

import argparse
import datetime as dt
from hashlib import sha256
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from autopilot.core import CHANNEL_ID, slot_utc
from autopilot.daily_cloud_plan import (
    PLAN_VERSION, PUBLISH_SLOTS, APPROVED_RESEARCH_ORIGINS,
)
from autopilot.evidence_probe import PROBE_STATUS, verify_public_source_url, EvidenceError
from autopilot.daily_editorial_board import _subject_hash
from autopilot.reconcile_daily_editorial_plan import RECONCILIATION_STATUS

UTC=dt.timezone.utc
IST=ZoneInfo("Asia/Kolkata")
# Static public export allowlist intentionally mirrors the exact publisher
# origin policy. If a new publisher is added, review this boundary explicitly.
ALLOWED_PUBLISHERS=frozenset({"OpenAI","Google DeepMind","The Verge","arXiv AI"})
STATUS="GITHUB_RETAINED_RESEARCH_DRAFT_EVIDENCE_ONLY"
MAX_INPUT_BYTES=512_000
MAX_OUTPUT_BYTES=12_000


class DailyEvidenceRefused(ValueError):
    """Unknown, released or forged planner reports may not be archived."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,sort_keys=True,separators=(",",":"),ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _aware_timestamp(value: object) -> dt.datetime:
    if not isinstance(value,str) or len(value)>40:
        raise DailyEvidenceRefused("Missing planner clock")
    try:
        clock=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    except (ValueError,OverflowError) as exc:
        raise DailyEvidenceRefused("Invalid planner clock") from exc
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise DailyEvidenceRefused("Timezone-aware planner clock required")
    return clock.astimezone(UTC)


def _disabled_plan(plan: dict) -> None:
    expected={
        "approved_provider_credentials_connected":False,
        "cloud_media_renderer_connected":False,
        "production_release_ledger_connected":False,
        "cloud_publisher_connected":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "any_content_verified":False,
        "new_billable_resources_enabled":False,
    }
    for key, value in expected.items():
        if plan.get(key) is not value:
            raise DailyEvidenceRefused("Any real provider or release state blocks public archive")
    if (type(plan.get("maximum_incremental_spend_inr")) is not int
        or plan["maximum_incremental_spend_inr"]!=0):
        raise DailyEvidenceRefused("Any planned paid production work blocks public archive")


def _validate_source_report(evidence: dict) -> None:
    if (type(evidence) is not dict or evidence.get("schema_version")!=1
        or evidence.get("status")!=PROBE_STATUS
        or type(evidence.get("source_probes_attempted")) is not int
        or type(evidence.get("sources_fetched")) is not int
        or type(evidence.get("feed_entries_observed_only")) is not int
        or type(evidence.get("sources_failed")) is not int
        or type(evidence.get("sources_observed_total")) is not int
        or type(evidence.get("distinct_publishers_fetched")) is not int):
        raise DailyEvidenceRefused("Unknown unverified source observation report")
    n=evidence["source_probes_attempted"]
    if (not 0<=n<=3
        or any(not 0<=evidence[key]<=n for key in (
            "sources_fetched","feed_entries_observed_only","sources_failed",
            "sources_observed_total","distinct_publishers_fetched"))
        or evidence["sources_fetched"]+evidence["feed_entries_observed_only"]
            +evidence["sources_failed"]!=n
        or evidence["sources_observed_total"]!=(
            evidence["sources_fetched"]+evidence["feed_entries_observed_only"])
        or evidence["distinct_publishers_fetched"]>evidence["sources_observed_total"]):
        raise DailyEvidenceRefused("Inconsistent source counts")
    for k,want in (
        ("claims_verified",0),("scripts_generated",0),
        ("billed_provider_calls",0),
        ("semantic_corroboration_performed",False),
        ("source_body_persisted",False),
        ("audio_or_video_generated",False),
        ("youtube_upload_enabled",False),
        ("youtube_schedule_enabled",False),
        ("production_credentials_used",False),
    ):
        if type(evidence.get(k)) is not type(want) or evidence[k]!=want:
            raise DailyEvidenceRefused("Observation made unreviewed release/expense claim")
    if type(evidence.get("sources")) is not list or type(evidence.get("failures")) is not list:
        raise DailyEvidenceRefused("Malformed source observations")
    if len(evidence["sources"])!=evidence["sources_observed_total"] or len(evidence["failures"])!=n-evidence["sources_observed_total"]:
        raise DailyEvidenceRefused("Source observations must match aggregate counts")
    _aware_timestamp(evidence.get("generated_at_utc"))


def _validate_sanitized_editorial_alignment(plan:dict, receipt:object)->str:
    """Prevent mismatched old first-three RSS assignments from public export."""
    if (type(receipt) is not dict
        or receipt.get("status") != "B4D2_SANITIZED_DAILY_EDITORIAL_RECEIPT_NO_CONTENT"
        or receipt.get("plan_date_ist") != plan.get("plan_date_ist")
        or receipt.get("release_authorized") is not False
        or receipt.get("real_youtube_uploads") != 0
        or receipt.get("fresh_original_scripts_completed") != 0
        or receipt.get("headlines_urls_source_bodies_and_scripts_included") is not False
        or type(receipt.get("slots")) is not list
        or len(receipt["slots"]) != 3
        or plan.get("editorial_reconciliation_status") != RECONCILIATION_STATUS
        or plan.get("editorial_research_origin_verified_not_claims") is not True
        or plan.get("editorial_factual_script_count") != 0
        or plan.get("editorial_media_count") != 0
        or type(plan.get("editorial_board_sha256")) is not str
        or len(plan["editorial_board_sha256"]) != 64):
        raise DailyEvidenceRefused("Unaligned or promoted editorial research receipt")
    expected_count=0
    for original, item in zip(plan["slots"],receipt["slots"]):
        if (type(item) is not dict
            or original["episode_id"] != item.get("episode_id")
            or item.get("release_authorized") is not False
            or item.get("youtube_uploaded") is not False
            or original.get("research_assignment_reconciled_unverified") is not True
            or original.get("editorial_research_angle_id") != item.get("angle_id")):
            raise DailyEvidenceRefused("Editorial slot and plan do not match")
        lead=original.get("research_lead")
        if lead is None:
            if (item.get("subject_sha256") is not None
                or item.get("source_id") is not None
                or item.get("article_bytes_observed") is not False):
                raise DailyEvidenceRefused("Unassigned research slot forged source")
        else:
            expected_count+=1
            url=lead["url"]
            if (item.get("subject_sha256") != _subject_hash(lead["title"])
                or item.get("source_id") != sha256(url.encode("utf8")).hexdigest()[:24]
                or item.get("research_status") not in (
                    "EVIDENCE_OBSERVED_PENDING_FACT_AND_RIGHTS_REVIEW",
                    "HEADLINE_ONLY_NEEDS_SOURCE_RESEARCH")):
                raise DailyEvidenceRefused("Cross-receipt source identity mismatch")
    if (expected_count != receipt.get("selected_distinct_topics")
        or expected_count != plan.get("editorial_selected_unverified_topics")):
        raise DailyEvidenceRefused("Research plan and editorial selected counts differ")
    data=dict(receipt)
    digest=data.pop("receipt_sha256",None)
    expected_hash=sha256(json.dumps(
        data,sort_keys=True,separators=(",",":"),ensure_ascii=False
    ).encode("utf8")).hexdigest()
    if digest != expected_hash:
        raise DailyEvidenceRefused("Unverified public editorial receipt digest")
    return expected_hash


def build_retained_draft_receipt(
    plan: dict,evidence: dict, *, editorial_receipt:object=None
) -> dict:
    """Content-address public run status, never copy headlines URLs or sources."""
    _validate_source_report(evidence)
    if ALLOWED_PUBLISHERS != frozenset(APPROVED_RESEARCH_ORIGINS):
        raise DailyEvidenceRefused("Research source/export publisher allowlists drifted")
    if (type(plan) is not dict or plan.get("schema_version")!=PLAN_VERSION
        or plan.get("plan_kind")!="UNPRIVILEGED_RESEARCH_DRAFT_ONLY"
        or plan.get("delivery_track")!="cloud_autonomous_agents"
        or plan.get("channel_id")!=CHANNEL_ID
        or plan.get("all_three_release_slots") is not True
        or plan.get("specialist_roles")!=48
        or plan.get("departments")!=8
        or plan.get("task_contracts")!=54):
        raise DailyEvidenceRefused("Unexpected daily autonomous draft provenance")
    _disabled_plan(plan)
    matched_editorial_sha = (_validate_sanitized_editorial_alignment(
        plan, editorial_receipt) if editorial_receipt is not None else None)
    planned_at=_aware_timestamp(plan.get("generated_at_utc"))
    observed_at=_aware_timestamp(evidence["generated_at_utc"])
    if abs((planned_at-observed_at).total_seconds())>3600:
        raise DailyEvidenceRefused("Observation and plan clocks too far apart")
    day=plan.get("plan_date_ist")
    try:
        target=dt.date.fromisoformat(day)
    except (TypeError,ValueError,OverflowError) as exc:
        raise DailyEvidenceRefused("Invalid target IST day") from exc
    if (day!=target.isoformat()
        or target!=planned_at.astimezone(IST).date()+dt.timedelta(days=1)):
        raise DailyEvidenceRefused("Only tomorrow's IST research draft may be archived")
    slots=plan.get("slots")
    if type(slots) is not list or len(slots)!=3:
        raise DailyEvidenceRefused("Expected exactly 2 Shorts and 1 long")
    output_slots=[]
    for entry,spec in zip(slots,PUBLISH_SLOTS):
        slot,kind,local,label=spec
        if (type(entry) is not dict
            or entry.get("release_slot")!=slot
            or entry.get("format")!=kind
            or entry.get("local_ist")!=local
            or entry.get("release_utc")!=slot_utc(day,slot)
            or entry.get("episode_id")!=f"fm_{target.strftime('%Y%m%d')}_{slot}"
            or entry.get("episode_label")!=label
            or entry.get("agent_handoffs_completed")!=0
            or type(entry.get("required_handoffs")) is not list
            or len(entry["required_handoffs"])!=18
            or any(not isinstance(x,str) or not x.startswith(entry["episode_id"]+":")
                   for x in entry["required_handoffs"])
            or entry.get("editorial_state") not in (
                "UNVERIFIED_LEAD_ONLY","RESEARCH_REQUIRED")
            or entry.get("status")!="BLOCKED_PENDING_RESEARCH_FACT_CHECK_AND_REAL_MEDIA"):
            raise DailyEvidenceRefused("Wrong format/time, fake progress or altered episode identity")
        for key in ("real_script_exists","real_narration_exists","real_media_exists",
                    "rights_approved","real_media_qa_passed","youtube_uploaded",
                    "youtube_scheduled","release_authorized"):
            if entry.get(key) is not False:
                raise DailyEvidenceRefused("Forged approval in a research-only draft")
        lead=entry.get("research_lead")
        if lead is not None:
            if (type(lead) is not dict
                or lead.get("publisher") not in ALLOWED_PUBLISHERS
                or lead.get("status")!="unverified_lead"
                or lead.get("fact_checked") is not False
                or lead.get("video_ready") is not False
                or entry["editorial_state"]!="UNVERIFIED_LEAD_ONLY"):
                raise DailyEvidenceRefused("Unexpected unverified research lead")
            try:
                verify_public_source_url(lead.get("url"), lead["publisher"])
            except EvidenceError:
                raise DailyEvidenceRefused("Unapproved public research lead URL") from None
        elif entry["editorial_state"]!="RESEARCH_REQUIRED":
            raise DailyEvidenceRefused("Research lead absent but status claims otherwise")
        output_slots.append({
            "episode_id":entry["episode_id"],
            "format":kind,
            "slot":slot,
            "release_local_ist":local,
            "planned_utc":entry["release_utc"],
            "research_lead_present":lead is not None,
            "lead_publisher_public_only":None if lead is None else lead["publisher"],
            "factual_content_approved":False,
            "real_media_rendered":False,
            "youtube_uploaded":False,
            "youtube_scheduled":False,
            "release_authorized":False,
        })
    result={
        "schema_version":1,
        "status":STATUS,
        "plan_day_ist":day,
        "generated_at_utc":planned_at.isoformat(),
        "observation_at_utc":observed_at.isoformat(),
        "plan_content_sha256":sha256(_canonical(plan)).hexdigest(),
        "source_observation_sha256":sha256(_canonical(evidence)).hexdigest(),
        "source_observations":{
            "attempted":evidence["source_probes_attempted"],
            "direct_pages_seen_not_fact_checked":evidence["sources_fetched"],
            "rss_entries_seen_not_article_fetched":evidence["feed_entries_observed_only"],
            "failed":evidence["sources_failed"],
        },
        "slots":output_slots,
        "raw_source_headlines_urls_and_bodies_retained":False,
        "real_fact_or_rights_review_performed":False,
        "real_media_or_credentials_retained":False,
        "paid_model_or_provider_calls":False,
        "private_cloud_or_vault_deployed":False,
        "youtube_publishing_enabled":False,
        "independently_verified_unattended_youtube_releases":0,
        "release_authorized":False,
        "sha256_is_content_integrity_only_not_owner_signature":True,
        "editorial_and_plan_reconciled": matched_editorial_sha is not None,
        "sanitized_editorial_receipt_sha256":matched_editorial_sha,
        "selected_distinct_research_topics": (
            plan["editorial_selected_unverified_topics"]
            if matched_editorial_sha is not None else None),
    }
    result["receipt_sha256"]=sha256(_canonical(result)).hexdigest()
    if len(_canonical(result))>MAX_OUTPUT_BYTES:
        raise DailyEvidenceRefused("Unbounded public receipt")
    return result


def _read_bounded(path: Path) -> dict:
    if not path.is_file() or path.is_symlink() or not 2<=path.stat().st_size<=MAX_INPUT_BYTES:
        raise DailyEvidenceRefused("Missing/unbounded/non-regular source input")
    try:
        obj=json.loads(path.read_text(encoding="utf8"),
                       parse_constant=lambda _: (_ for _ in ()).throw(
                           DailyEvidenceRefused("Nonfinite public input")))
    except (json.JSONDecodeError,UnicodeError) as exc:
        raise DailyEvidenceRefused("Unparseable source input") from exc
    if type(obj) is not dict:
        raise DailyEvidenceRefused("Expected JSON object")
    return obj


def main():
    cli=argparse.ArgumentParser(description="Sanitized public draft receipt; never publish")
    cli.add_argument("--plan",required=True)
    cli.add_argument("--evidence",required=True)
    cli.add_argument("--output",required=True)
    cli.add_argument("--editorial-receipt",required=False)
    args=cli.parse_args()
    output=Path(args.output)
    if output.is_symlink() or output.exists():
        raise DailyEvidenceRefused("Refusing to overwrite a previous public receipt")
    result=build_retained_draft_receipt(
        _read_bounded(Path(args.plan)),_read_bounded(Path(args.evidence)),
        editorial_receipt=(
            _read_bounded(Path(args.editorial_receipt))
            if args.editorial_receipt else None))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=True)+"\n",encoding="utf8")
    print(json.dumps({
        "status":STATUS,"day_ist":result["plan_day_ist"],
        "three_unapproved_slots":len(result["slots"]),
        "receipt_sha256":result["receipt_sha256"],
        "actual_uploads":0,"production_release_authorized":False,
    }))


if __name__=="__main__":
    main()
