"""CLIVOX V2 P2: public-business-page creator research and UNSENT proposal drafts.

Never contacts a creator or accepts an agreement, uses YouTube API data, downloads
source footage, accesses private pages, signs permissions or publishes media.
This module validates a bounded, source-referenced *research* watchlist and
writes a non-authorizing owner-review packet to temporary local output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

CHANNEL = "UCfPEvy0SefE_5nNlYlY_CyQ"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = (PROJECT_ROOT / "branch3/clipping_v2/prospects/"
        "public-business-pages-2026-11-14.json")
MAX_BYTES = 40_000
MAX_PROSPECTS = 10
MAX_PUBLIC_AGE_DAYS = 30
ALLOWED_HOSTS = frozenset({
    "ankitt.com", "eggmilk.carrd.co", "mrjdgaming.com",
    "www.mandarriaxl.com", "caseoh.com",
})
TOP_KEYS = frozenset({
    "schema_version", "channel_id", "research_date_utc", "research_scope",
    "state", "creator_identity_authenticated", "creator_rights_verified",
    "human_owner_shortlist_approved", "public_creator_business_contacts_only",
    "third_party_media_acquisition_allowed", "youtube_upload_authorized",
    "prospects",
})
ROW_KEYS = frozenset({
    "id", "display_name", "lane", "priority_group", "public_creator_page",
    "public_business_page", "self_described_content",
    "observed_public_business_route", "evidence_note", "outreach_state",
    "rights_state",
})
PRIORITIES = {"POTENTIAL_CREATOR_PARTNER", "FAMOUS_FORMAT_RESEARCH"}
ROUTES = {"SITE_CONTACT_FORM", "BUSINESS_INQUIRY_WEBPAGE"}
LANES = {"gaming_livestream", "comedy", "vlog", "podcast_interview"}
P2_BLOCKED_FIELDS = ("media_acquisition_authorized", "source_download_allowed",
                     "license_granted", "permission_verified", "contact_sent",
                     "email_sent", "owner_approved", "upload_allowed",
                     "publish_authorized", "subscriber_count", "view_count",
                     "research_score", "virality_score", "youtube_api_stats")
EMAIL = re.compile(r"(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
PHONE = re.compile(r"(?:\+?\d[\d() .-]{7,}\d)")
ID = re.compile(r"[a-z][a-z0-9_]{3,39}\Z")


class ProspectDenied(ValueError):
    """No side effects on rejected data or non-review output destinations."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ProspectDenied("CLIVOX_V2_P2_DENIED_" + code)


def clean_string(value: object, length: int = 200) -> str:
    require(type(value) is str and 1 <= len(value) <= length
            and value == value.strip()
            and all(32 <= ord(c) <= 126 for c in value),
            "INVALID_PUBLIC_TEXT")
    require(EMAIL.search(value) is None and PHONE.search(value) is None,
            "PRIVATE_CONTACT_INFO_FORBIDDEN")
    require(not any(v in value.lower() for v in (
        "access_token=", "refresh_token=", "api_key=", "password=",
        "bearer ", "BEGIN PRIVATE KEY",
    )), "SECRET_LIKE_TEXT")
    return value


def public_page(url: object) -> str:
    clean_string(url, 250)
    parsed = urlsplit(url)
    require(
        parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS
        and parsed.netloc == parsed.hostname
        and parsed.username is None and parsed.password is None
        and parsed.port is None and parsed.query == "" and parsed.fragment == ""
        and parsed.path.startswith("/") and "//" not in parsed.path
        and ".." not in parsed.path and "\\" not in parsed.path
        and not parsed.path.lower().endswith((
            ".mp4", ".mov", ".mkv", ".webm", ".zip", ".pdf", ".csv"
        )),
        "UNTRUSTED_PUBLIC_WEBPAGE"
    )
    return url


def instant(value: object) -> datetime:
    require(type(value) is str and re.fullmatch(
        r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ", value
    ) is not None, "UTC_TIMESTAMP")
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ProspectDenied("CLIVOX_V2_P2_DENIED_BAD_DATE") from None
    return out


def validate_watchlist(payload: object, *, now: datetime) -> dict:
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "AWARE_NOW_REQUIRED")
    require(type(payload) is dict and set(payload) == TOP_KEYS,
            "EXACT_PUBLIC_SCHEMA")
    require(payload["schema_version"] == 1
            and payload["channel_id"] == CHANNEL
            and payload["research_scope"] ==
                "PUBLIC_CREATOR_BRANDED_BUSINESS_PAGES_ONLY"
            and payload["state"] == "P2_RESEARCH_PROSPECTS_NOT_CONTACTED",
            "RESEARCH_ONLY_STATE")
    for k, expected in {
        "creator_identity_authenticated": False,
        "creator_rights_verified": False,
        "human_owner_shortlist_approved": False,
        "public_creator_business_contacts_only": True,
        "third_party_media_acquisition_allowed": False,
        "youtube_upload_authorized": False,
    }.items():
        require(type(payload[k]) is bool and payload[k] is expected,
                "FORGED_RESEARCH_RIGHTS_" + k.upper())
    observed = instant(payload["research_date_utc"])
    age = now.astimezone(timezone.utc) - observed
    require(timedelta(0) <= age <= timedelta(days=MAX_PUBLIC_AGE_DAYS),
            "STALE_OR_FUTURE_RESEARCH")
    candidates = payload["prospects"]
    require(type(candidates) is list
            and 3 <= len(candidates) <= MAX_PROSPECTS,
            "PROSPECT_COUNT")
    ids, urls = set(), set()
    checked = []
    for c in candidates:
        require(type(c) is dict and set(c) == ROW_KEYS,
                "EXACT_PROSPECT_SCHEMA")
        require(not any(k in c for k in P2_BLOCKED_FIELDS),
                "PRIVATE_OR_FORGED_RANK")
        key = clean_string(c["id"], 40)
        require(ID.fullmatch(key) is not None and key not in ids,
                "PROSPECT_ID_OR_DUPLICATE")
        ids.add(key)
        name = clean_string(c["display_name"], 80)
        content = clean_string(c["self_described_content"], 180)
        note = clean_string(c["evidence_note"], 340)
        creator = public_page(c["public_creator_page"])
        business = public_page(c["public_business_page"])
        require(urlsplit(creator).hostname == urlsplit(business).hostname,
                "BUSINESS_PAGE_MUST_MATCH_BRANDED_DOMAIN")
        require(creator not in urls, "DUPLICATE_BRANDED_CREATOR_PAGE")
        urls.add(creator)
        require(c["lane"] in LANES and c["priority_group"] in PRIORITIES
                and c["observed_public_business_route"] in ROUTES
                and c["outreach_state"] == "NOT_CONTACTED"
                and c["rights_state"] == "UNVERIFIED",
                "NO_CONTACT_OR_LICENSE_INFERENCE")
        checked.append({
            "id": key, "name": name, "lane": c["lane"],
            "priority_group": c["priority_group"],
            "creator_page": creator, "business_reference_page": business,
            "observed_public_business_route": c["observed_public_business_route"],
            "creator_description_self_asserted": content,
            "evidence_note": note,
            "actual_creator_authority_verified": False,
            "actual_business_route_deliverability_verified": False,
            "actual_creator_contacted": False,
            "creator_replied_or_agreed": False,
            "commercial_redistribution_and_monetization_granted": False,
            "game_music_guest_rights_verified": False,
            "source_file_delivered": False,
            "youtube_upload_authorized": False,
            "owner_shortlist_review_state": "PENDING_REAL_HUMAN_REVIEW",
        })
    require(3 <= sum(x["priority_group"] == "POTENTIAL_CREATOR_PARTNER"
                     for x in checked) <= MAX_PROSPECTS,
            "NOT_ENOUGH_POTENTIAL_PARTNERS")
    return {
        "source_research_date_utc": payload["research_date_utc"],
        "candidates": sorted(checked, key=lambda x: x["id"]),
    }


def proposal(name: str, *, lane: str) -> dict:
    name = clean_string(name, 80)
    require(lane in LANES, "LANE")
    focus = {
        "gaming_livestream": "complete gameplay turns, reactions and humorous stream moments",
        "comedy": "self-contained humorous moments and original commentary",
        "vlog": "challenge reversals and contextual storytelling",
        "podcast_interview": "accurate interview context and critical commentary",
    }[lane]
    return {
        "subject": f"CLIVOX: licensed three-Short editing pilot for {name}",
        "recipient_address": None,
        "state": "UNSENT_DRAFT_FOR_OWNER_APPROVAL_ONLY",
        "body": (
            f"Hello {name} team,\n\n"
            "CLIVOX is planning a small, permission-first YouTube Shorts "
            "editing partnership. We would like to explore a privately "
            "reviewed pilot of up to three Shorts based on your long-form "
            f"content, especially {focus}.\n\n"
            "Before requesting or editing any footage, we would need to "
            "agree in writing on your authorized source delivery method, "
            "commercial YouTube redistribution and monetization, clip edit "
            "and commentary permissions, game/music/guest rights, credit, "
            "territories, duration, withdrawal and claim handling, any "
            "fees or revenue share, and ownership of the new edits.\n\n"
            "Nothing would be published or scheduled without the verified "
            "license and your agreed approval process. We would share "
            "private review copies and original commentary/storytelling "
            "proposals for discussion. Would you be open to reviewing "
            "the partnership scope?\n\nCLIVOX team"
        ),
        "sent": False,
        "actual_creator_consent_received": False,
        "license_verified": False,
        "media_download_authorized": False,
        "publishing_authorized": False,
    }


def compile_owner_research_packet(payload: object, *, now: datetime) -> dict:
    validated = validate_watchlist(payload, now=now)
    # Digest the exact public input. This is provenance, not identity or rights.
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    source_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    queue = []
    for record in validated["candidates"]:
        queue.append({
            **record,
            "proposed_outreach": proposal(record["name"], lane=record["lane"]),
            "next_action": "OWNER_VERIFY_CREATOR_IDENTITY_AND_BUSINESS_ROUTE",
            "rights_review_case_state": "NOT_STARTED_NO_CREATOR_GRANT",
        })
    return {
        "schema_version": 1,
        "stage": "CLIVOX_V2_P2_PUBLIC_PROSPECT_REVIEW_AND_UNSENT_OUTREACH",
        "channel_id": CHANNEL,
        "research_input_sha256": source_sha,
        "research_observed_utc": validated["source_research_date_utc"],
        "created_at_utc": now.astimezone(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "prospect_count": len(queue),
        "potential_partner_count": sum(
            x["priority_group"] == "POTENTIAL_CREATOR_PARTNER" for x in queue
        ),
        "famous_format_research_only_count": sum(
            x["priority_group"] == "FAMOUS_FORMAT_RESEARCH" for x in queue
        ),
        "all_proposals_unsent": True,
        "all_creator_identity_and_licensing_unverified": True,
        "human_shortlist_approved": False,
        "real_creator_contacts_sent": 0,
        "real_creator_replies_received": 0,
        "creator_grants_verified": 0,
        "private_media_sources_delivered": 0,
        "licensed_source_media_access_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "google_or_youtube_api_calls": 0,
        "no_third_party_media_download": True,
        "ranking_is_not_based_on_api_views_or_likes": True,
        "review_queue": queue,
    }


def load_watchlist(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= MAX_BYTES, "INPUT_FILE")
    try:
        return json.loads(path.read_text("utf-8"))
    except (ValueError, UnicodeError):
        raise ProspectDenied("CLIVOX_V2_P2_DENIED_INPUT_JSON") from None


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        # Never treat the public repo itself as a durable outreach inbox.
        output = args.output.absolute()
        require(output.suffix == ".json"
                and output.name == "clivox-p2-owner-review-UNSENT.json"
                and output.parent.is_dir()
                and not output.is_symlink()
                and not output.exists()
                and PROJECT_ROOT not in output.parents,
                "NEW_PRIVATE_OR_EPHEMERAL_REPORT_ONLY")
        data = load_watchlist(args.input)
        result = compile_owner_research_packet(
            data, now=datetime.now(timezone.utc)
        )
        # Synthetic/private owner review packet may be retained in explicitly
        # private owner vault later. Current CI must not upload this artifact.
        output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        try:
            output.chmod(0o600)
        except OSError:
            pass
        print("CLIVOX_V2_P2_PUBLIC_PROSPECTS=" + str(result["prospect_count"])
              + " potential_partners=" + str(result["potential_partner_count"])
              + " creator_contacts=0 grants=0 media=0 youtube_writes=0")
    except (ProspectDenied, OSError, ValueError, TypeError, KeyError):
        raise SystemExit(
            "CLIVOX_V2_P2_DENIED_NO_CONTACT_NO_RIGHTS_NO_MEDIA_NO_UPLOAD"
        ) from None


if __name__ == "__main__":
    run()
