"""Creator-authored clipping permission preflight. NO downloading, YouTube API, or upload.

Passing this gate is only a candidate-source eligibility check. Public JSON flags
cannot replace genuine documented permissions or signed owner release approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

VIDEO_ID=re.compile(r"[A-Za-z0-9_-]{11}\Z")
CHANNEL_ID=re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
DIGEST=re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER=re.compile(r"[a-z0-9][a-z0-9_-]{2,80}\Z")
UTC_DATE=re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
APPROVED_PROOFS=frozenset({"direct_written_creator_grant","verified_creator_public_clipping_policy"})
REQUIRED_SCOPE=(
    "clipping_allowed","editing_allowed","youtube_shorts_allowed",
    "youtube_regular_allowed","youtube_redistribution_allowed",
    "commercial_use_allowed",
)
REGISTRY=Path(__file__).resolve().parents[1]/"branch3/creator_permissions.json"
# Category describes editorial positioning; it never grants rights to media.
CATEGORIES=frozenset({
    "gaming","livestream","comedy","entertainment","podcast_interview"
})

class ClipRightsBlocked(ValueError):
    """Insufficient explicit creator permission: no clip acquisition or upload."""

def require(ok: bool) -> None:
    if not ok:
        raise ClipRightsBlocked("DENY_CREATOR_PERMISSION_NOT_VERIFIED")

def utc(value: object) -> datetime:
    require(type(value) is str and UTC_DATE.fullmatch(value) is not None)
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:
        raise ClipRightsBlocked("DENY_CREATOR_PERMISSION_NOT_VERIFIED") from None

def https_uri(value: object) -> bool:
    if type(value) is not str or len(value)>1024:
        return False
    try:
        u=urlsplit(value)
        return (u.scheme=="https" and bool(u.hostname)
                and not u.username and not u.password
                and not u.fragment and u.port in (None,443))
    except ValueError:
        return False

def eligible_source(registry: dict, clip: dict, *, now: datetime) -> dict:
    """A *positive* result is review eligibility only, never publication consent."""
    require(type(registry) is dict and registry.get("schema_version")==1
            and registry.get("policy")=="EXPLICIT_CREATOR_GRANT_ONLY"
            and type(registry.get("creators")) is list)
    require(type(clip) is dict and type(now) is datetime and now.tzinfo is not None)
    require(clip.get("content_category") in CATEGORIES)
    # All game footage requires separate publisher commercial-use clearance;
    # streaming creator permissions cover only the rights the creator owns.
    require(type(clip.get("contains_video_game_footage")) is bool
            and type(clip.get("pre_release_or_leaked_game_footage")) is bool
            and type(clip.get("isolated_game_spoiler_or_in_game_show")) is bool
            and clip["pre_release_or_leaked_game_footage"] is False
            and clip["isolated_game_spoiler_or_in_game_show"] is False)
    if clip["content_category"]=="gaming":
        require(clip["contains_video_game_footage"] is True)
    if clip["contains_video_game_footage"]:
        require(clip.get("game_publisher_commercial_use_manually_verified") is True)
    require(clip.get("video_format") in ("short","long")
            and type(clip.get("creator_id")) is str
            and IDENTIFIER.fullmatch(clip["creator_id"]) is not None
            and type(clip.get("source_video_id")) is str
            and VIDEO_ID.fullmatch(clip["source_video_id"]) is not None
            and type(clip.get("source_channel_id")) is str
            and CHANNEL_ID.fullmatch(clip["source_channel_id"]) is not None)
    require(type(clip.get("source_url")) is str
            and clip["source_url"]==f"https://www.youtube.com/watch?v={clip['source_video_id']}")
    require(clip.get("third_party_embedded_media_cleared") is True
            and clip.get("source_content_context_reviewed") is True)
    creators=registry["creators"]
    require(len(creators)<=200 and all(type(c) is dict for c in creators)
            and len({c.get("creator_id") for c in creators})==len(creators))
    candidates=[c for c in creators if c.get("creator_id")==clip["creator_id"]]
    require(len(candidates)==1)
    creator=candidates[0]
    require(creator.get("source_channel_id")==clip["source_channel_id"]
            and CHANNEL_ID.fullmatch(creator["source_channel_id"]) is not None
            and creator.get("proof_kind") in APPROVED_PROOFS
            and https_uri(creator.get("permission_proof_url"))
            and type(creator.get("permission_evidence_sha256")) is str
            and DIGEST.fullmatch(creator["permission_evidence_sha256"]) is not None)
    require(creator.get("creator_identity_manually_verified") is True
            and creator.get("permission_scope_manually_verified") is True
            and creator.get("permission_currently_active") is True
            and creator.get("rights_holder_has_necessary_underlying_rights") is True
            and creator.get("permission_revoked") is False)
    scope=creator.get("scope")
    require(type(scope) is dict
            and all(scope.get(k) is True for k in REQUIRED_SCOPE)
            and scope.get("all_territories_allowed") is True)
    require(type(creator.get("source_video_ids")) is list
            and clip["source_video_id"] in creator["source_video_ids"]
            and len(creator["source_video_ids"])<=1000)
    require(utc(creator.get("verified_at_utc"))<=now.astimezone(timezone.utc)
            <utc(creator.get("expires_at_utc")))
    # A public policy may be changed or revoked after review; this structural
    # gate deliberately cannot authenticate websites or provide legal signoff.
    return {
        "status":"SOURCE_ELIGIBLE_FOR_MANUAL_EDITORIAL_AND_SIGNED_OWNER_REVIEW_ONLY",
        "creator_id":creator["creator_id"],
        "source_video_id":clip["source_video_id"],
        "content_category":clip["content_category"],
        "copyright_risk_eliminated":False,
        "rights_legal_verification_performed_by_this_script":False,
        "signed_release_authorized":False,
        "youtube_upload_authorized":False,
        "youtube_scheduled":False,
    }

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",type=Path,required=True)
    args=p.parse_args()
    try:
        registry=json.loads(REGISTRY.read_text("utf8"))
        clip=json.loads(args.candidate.read_text("utf8"))
        report=eligible_source(registry,clip,now=datetime.now(timezone.utc))
    except (ClipRightsBlocked,OSError,ValueError,TypeError,KeyError):
        raise SystemExit("DENIED: creator-granted clipping permission not verified; no upload") from None
    print(report["status"]+"; NO_YOUTUBE_UPLOAD_OR_PUBLISH")

if __name__=="__main__":
    main()
