"""Clivox public campaign discovery is NOT a creator license. Fail closed.

No network, credentials, clip downloads, uploads or account actions.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
WATCHLIST=ROOT/"branch3/clip_source_watchlist_2026-11-12.json"
ALLOWED_HOSTS={"b4e0vdqv6zgqeqj4pfgm.apps.whop.com","dev-b4e0vdqv6zgqeqj4pfgm.apps.whop.com","contentrewards.com"}

class ResearchOnlyError(ValueError):
    pass

def require(value: bool, reason: str) -> None:
    if not value: raise ResearchOnlyError(reason)

def validate_watchlist(w: object) -> int:
    require(type(w) is dict,"not a JSON object")
    require(w.get("schema_version")==1,"incorrect version")
    require(w.get("channel_id")=="UCfPEvy0SefE_5nNlYlY_CyQ","wrong channel")
    require(w.get("policy")=="RESEARCH_ONLY_NOT_CREATOR_PERMISSION","permission shortcut")
    require(w.get("creator_allowlist_empty") is True,"claims creator approval")
    require(w.get("automatic_download_enabled") is False,"download enabled")
    require(w.get("automatic_publish_enabled") is False,"publish enabled")
    require(w.get("all_candidates")=="RESEARCH_ONLY","claims publication approval")
    candidates=w.get("candidates")
    require(type(candidates) is list and len(candidates)>=3,"no candidates")
    ids=set()
    for c in candidates:
        require(type(c) is dict,"invalid candidate")
        cid=c.get("id")
        require(type(cid) is str and cid and cid not in ids,"duplicate/missing id")
        ids.add(cid)
        require(c.get("pillar") in {"gaming","livestream","comedy","entertainment","podcast_interview"},"unknown pillar")
        require(c.get("status")=="RESEARCH_ONLY_UNVERIFIED","claim of cleared source")
        for flag in ("rights_verified","clipping_authorized_for_clivox","allowlist_approved","media_download_authorized","upload_authorized"):
            require(c.get(flag) is False,f"unsafe clearance claim: {flag}")
        raw=c.get("campaign_url")
        require(type(raw) is str and len(raw)<2048,"invalid campaign URL")
        url=urlparse(raw)
        require(url.scheme=="https" and url.hostname in ALLOWED_HOSTS
                and url.username is None and url.password is None
                and url.fragment=="" and url.path.startswith("/c/campaigns/"),"untrusted campaign origin")
        require(type(c.get("special_conditions")) is list and len(c["special_conditions"])>0,"missing terms")
        require(type(c.get("youtube_listed")) is bool,"unknown YouTube platform")
        if not c["youtube_listed"]:
            require(c.get("initial_priority")=="EXCLUDED_YOUTUBE","cross-platform leak")
        if c.get("public_listing_status_at_research")=="paused":
            require(c.get("initial_priority")=="EXCLUDED_PAUSED","paused campaign")
        require(c.get("initial_priority")!="APPROVED","bogus approved priority")
    require(all(x is False for x in w.get("required_review_fields",{}).values()),"falsely finished reviews")
    return len(ids)

def main() -> None:
    w=json.loads(WATCHLIST.read_text("utf8"))
    count=validate_watchlist(w)
    real=json.loads((ROOT/"branch3/creator_permissions.json").read_text("utf8"))
    require(real.get("creators")==[],"creator allowlist modified while onboarding research")
    state=json.loads((ROOT/"branch3/channel_state.json").read_text("utf8"))
    require(state["release_gates"]["verified_creator_permissions_count"]==0,"state says verified rights")
    require(state["channel_settings"]["automatic_publishing_enabled"] is False,"publishing turned on")
    print(f"BRANCH3_DISCOVERY_RESEARCH_ONLY_{count}_UNVERIFIED_CANDIDATES_ZERO_RELEASES")

if __name__=="__main__":
    main()
