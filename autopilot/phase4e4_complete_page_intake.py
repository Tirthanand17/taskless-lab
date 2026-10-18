"""Phase 4E.4: assemble COMPLETE, ordered, UNAUTHENTICATED YouTube pages.

NO network, YouTube account, OAuth, Google connection, database, publishing or
secret storage. This ONLY normalizes already-supplied raw provider-shaped
response fixtures and blocks truncated/cyclic page-token handoffs.

The caller's claim that the response came from Google is NOT validated.
Completeness here means supplied pages form a consistent declared chain,
not that the actual channel inventory was retrieved or is exhaustive.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .phase4b_readonly_audit import AuditBlocked
from .phase4e_readonly_import import parse_youtube_channel_video_observation

_MAX_PAGES = 12
_MAX_VIDEOS = 500
_MAX_PER_PAGE = 50
_TOKEN = re.compile(r"[A-Za-z0-9._~+\-=/]{1,256}\Z")


def assemble_untrusted_youtube_pages(
    *, channel_response: Mapping, pages: Sequence[Mapping],
) -> dict:
    """Sanitize and join a claimed YouTube nextPageToken chain.

    Each supplied page is exactly
      {"requested_page_token": None | str, "response": {"items": ...,
          "nextPageToken": ... optional}}
    Token text is never included in returned data.
    """
    if (not isinstance(pages,(list,tuple))
            or not 1<=len(pages)<=_MAX_PAGES):
        raise AuditBlocked("Bounded complete offline YouTube page chain required")
    required_token=None
    seen_requests=set()
    seen_video_ids=set()
    sanitized_videos=[]
    for pos,page in enumerate(pages):
        if not isinstance(page,dict) or set(page)!={"requested_page_token","response"}:
            raise AuditBlocked("Page must have only request token and response")
        supplied=page["requested_page_token"]
        if supplied != required_token:
            raise AuditBlocked("Missing, reordered, duplicated or mismatched page request")
        if pos>0:
            if (not isinstance(supplied,str)
                    or _TOKEN.fullmatch(supplied) is None
                    or supplied in seen_requests):
                raise AuditBlocked("Invalid or reused continuation token")
            seen_requests.add(supplied)
        response=page["response"]
        if not isinstance(response,dict):
            raise AuditBlocked("Provider-shaped page response mapping required")
        items=response.get("items")
        if not isinstance(items,list) or len(items)>_MAX_PER_PAGE:
            raise AuditBlocked("Video page exceeds supported YouTube page size")
        next_token=response.get("nextPageToken")
        if next_token is not None and (
                not isinstance(next_token,str)
                or _TOKEN.fullmatch(next_token) is None
                or next_token==supplied
                or next_token in seen_requests):
            raise AuditBlocked("Malformed or cyclic next page token")
        normalized=parse_youtube_channel_video_observation(
            channel_response=channel_response,video_response=response,
        )
        for video in normalized["videos"]:
            video_id=video["youtube_id"]
            if video_id in seen_video_ids:
                raise AuditBlocked("Duplicate channel video across pages")
            seen_video_ids.add(video_id)
            sanitized_videos.append(video)
            if len(sanitized_videos)>_MAX_VIDEOS:
                raise AuditBlocked("Offline readback cap reached, not exhaustive")
        if next_token is None and pos!=len(pages)-1:
            raise AuditBlocked("Extra page after a terminal response")
        required_token=next_token
    if required_token is not None:
        raise AuditBlocked("Missing final page; cannot mark inventory complete")
    sanitized_videos.sort(key=lambda v:v["youtube_id"])
    uncertain=any(v["uncertain_metadata"] for v in sanitized_videos)
    # Exact field shape intentionally matches existing Phase 4E.2 verifier;
    # it can then be hashed/signed externally but still NOT provider attested.
    return {
        "origin":"UNAUTHENTICATED_YOUTUBE_SHAPED_METADATA",
        "channel_id":normalized["channel_id"],
        "video_count":len(sanitized_videos),
        "videos":sanitized_videos,
        "pagination_complete":True,
        "has_conflicting_state":uncertain,
        "contains_titles_or_descriptions":False,
        "saw_authenticated_provider_request":False,
        "migration_authorized":False,
        "publication_authorized":False,
        "network_calls":0,
        "production_writes":0,
        "blockers":[
            "AUTHENTICATED_YOUTUBE_OAUTH_OWNER_BINDING_NOT_ESTABLISHED",
            "INPUTS_ARE_UNTRUSTED_PROVIDER_SHAPED_CLAIMS",
        ],
    }
