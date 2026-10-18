"""Phase 4E.5: reconcile claimed channel uploads playlist with video details.

DATA TRANSFORM ONLY, no Google/Cloudflare API, credentials, new connection,
billing, storage, D1 writes or YouTube mutation.

YouTube's channels.list(mine=true,part=contentDetails) identifies the
channel's uploads playlist; playlistItems.list lists video IDs, while
videos.list(id=...) provides processing/privacy/scheduling details. A
single fake videos.list page is NOT proof of complete upload history.

All inputs are UNAUTHENTICATED provider-shaped objects supplied by a caller.
Even a perfect offline crosswalk has zero permission or provider provenance.
Missing or deleted private video details fail closed for human reconciliation;
no inventory or release is silently classified as complete.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .core import CHANNEL_ID
from .phase4b_readonly_audit import AuditBlocked, VIDEO_ID
from .phase4e_readonly_import import parse_youtube_channel_video_observation
from .phase4e4_complete_page_intake import _TOKEN

MAX_PAGES=12
MAX_PER_PAGE=50
MAX_UPLOADS=500
_PLAYLIST = re.compile(r"[A-Za-z0-9_-]{12,160}\Z")


def _pages(values: object, *, allow_empty: bool=False) -> Sequence[dict]:
    if not isinstance(values,(list,tuple)) or len(values)>MAX_PAGES or (
            not allow_empty and not values):
        raise AuditBlocked("Expected a bounded offline provider-shaped page list")
    return values


def _channel_uploads_playlist(response: object) -> str:
    if not isinstance(response,Mapping):
        raise AuditBlocked("Sanitized channel-shaped response required")
    channels=response.get("items")
    if not isinstance(channels,list) or len(channels)!=1:
        raise AuditBlocked("Exactly one claimed owner channel required")
    ch=channels[0]
    if not isinstance(ch,Mapping) or ch.get("id")!=CHANNEL_ID:
        raise AuditBlocked("Unexpected uploads channel identity")
    details=ch.get("contentDetails")
    if not isinstance(details,Mapping):
        raise AuditBlocked("Channel uploads playlist identity missing")
    related=details.get("relatedPlaylists")
    if not isinstance(related,Mapping):
        raise AuditBlocked("Channel related uploads playlist missing")
    uploads=related.get("uploads")
    if not isinstance(uploads,str) or not _PLAYLIST.fullmatch(uploads):
        raise AuditBlocked("Invalid owner uploads playlist")
    return uploads


def _playlist_video_ids(pages: Sequence[dict], uploads_id: str)->set[str]:
    expected_token=None
    used_tokens=set()
    videos=set()
    for offset,page in enumerate(_pages(pages)):
        if not isinstance(page,dict) or set(page)!={
                "playlist_id","requested_page_token","response"}:
            raise AuditBlocked("Unexpected raw playlist page fields")
        if page["playlist_id"]!=uploads_id:
            raise AuditBlocked("Uploads page belongs to another playlist")
        requested=page["requested_page_token"]
        if requested!=expected_token:
            raise AuditBlocked("Missing or unordered uploads page")
        if offset>0:
            if (not isinstance(requested,str)
                    or _TOKEN.fullmatch(requested) is None
                    or requested in used_tokens):
                raise AuditBlocked("Invalid or replayed uploads page request")
            used_tokens.add(requested)
        raw=page["response"]
        if not isinstance(raw,dict):
            raise AuditBlocked("Malformed playlist response")
        items=raw.get("items")
        if not isinstance(items,list) or len(items)>MAX_PER_PAGE:
            raise AuditBlocked("Unbounded uploads playlist results")
        for item in items:
            if not isinstance(item,Mapping):
                raise AuditBlocked("Invalid playlist item")
            content=item.get("contentDetails")
            snippet=item.get("snippet")
            if not isinstance(content,Mapping) or not isinstance(snippet,Mapping):
                raise AuditBlocked("Missing playlist video or channel proof")
            video_id=content.get("videoId")
            if (not isinstance(video_id,str)
                    or VIDEO_ID.fullmatch(video_id) is None
                    or snippet.get("channelId")!=CHANNEL_ID
                    or video_id in videos):
                raise AuditBlocked("Wrong-channel or duplicated uploads playlist video")
            videos.add(video_id)
            if len(videos)>MAX_UPLOADS:
                raise AuditBlocked("Owner upload inventory exceeds bounded review")
        new_token=raw.get("nextPageToken")
        if new_token is not None and (
                not isinstance(new_token,str)
                or _TOKEN.fullmatch(new_token) is None
                or new_token==requested
                or new_token in used_tokens):
            raise AuditBlocked("Invalid or cyclic uploads page continuation")
        if new_token is None and offset!=len(pages)-1:
            raise AuditBlocked("Page follows uploads playlist terminal page")
        expected_token=new_token
    if expected_token is not None:
        raise AuditBlocked("Incomplete uploads playlist history")
    return videos


def assemble_untrusted_uploads_with_video_details(
    *,channel_response: Mapping,playlist_pages: Sequence[dict],
    video_detail_batches: Sequence[dict],
)->dict:
    """Match claimed uploads playlist IDs to exact, bounded videos.list IDs.

    Each detail batch: {"requested_video_ids": [id, ...],
    "response": {"items":[...]}}. All requested IDs must match response IDs,
    and union of batches must match the uploads playlist exactly.
    """
    upload_playlist=_channel_uploads_playlist(channel_response)
    uploaded=_playlist_video_ids(playlist_pages,upload_playlist)
    batches=_pages(video_detail_batches,allow_empty=True)
    requested=set()
    safe=[]
    for batch in batches:
        if not isinstance(batch,dict) or set(batch)!={
                "requested_video_ids","response"}:
            raise AuditBlocked("Unapproved raw video batch fields")
        ids=batch["requested_video_ids"]
        if not isinstance(ids,list) or not 1<=len(ids)<=MAX_PER_PAGE:
            raise AuditBlocked("Bounded videos.list ID batch required")
        if any(not isinstance(i,str) or VIDEO_ID.fullmatch(i) is None for i in ids):
            raise AuditBlocked("Invalid requested videos.list ID")
        if len(set(ids))!=len(ids) or requested.intersection(ids):
            raise AuditBlocked("Duplicate video request batch IDs")
        requested.update(ids)
        if not requested<=uploaded:
            raise AuditBlocked("Requested video ID absent from uploads playlist")
        body=batch["response"]
        if not isinstance(body,Mapping):
            raise AuditBlocked("Invalid videos.list response body")
        raw=body.get("items")
        if not isinstance(raw,list) or len(raw)>MAX_PER_PAGE:
            raise AuditBlocked("Invalid videos.list item count")
        if body.get("nextPageToken") is not None:
            raise AuditBlocked("videos.list ID batches must not have a page token")
        clean=parse_youtube_channel_video_observation(
            channel_response=channel_response,video_response=body)
        if set(x["youtube_id"] for x in clean["videos"])!=set(ids):
            raise AuditBlocked(
                "Missing, deleted, inaccessible or unexpected video details"
            )
        safe.extend(clean["videos"])
    if requested!=uploaded:
        raise AuditBlocked("Uploads playlist and video details not fully reconciled")
    if len(safe)!=len(uploaded):
        raise AuditBlocked("Video details missing or duplicated")
    safe.sort(key=lambda item:item["youtube_id"])
    uncertain=any(item["uncertain_metadata"] for item in safe)
    # This EXACTLY matches the existing Phase 4E.2 sanitization contract.
    return {
        "origin":"UNAUTHENTICATED_YOUTUBE_SHAPED_METADATA",
        "channel_id":CHANNEL_ID,
        "video_count":len(safe),
        "videos":safe,
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
