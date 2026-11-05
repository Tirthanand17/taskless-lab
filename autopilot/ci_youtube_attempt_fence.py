"""B4b1 CI-ONLY PostgreSQL attempt fence, never a YouTube uploader.

Demonstrates real PostgreSQL cross-connection uniqueness + privileged procedures
against *imaginary* credentials and B4a DRY RUN intents. This does not provide
a production authenticated owner, actual cloud deployment, YouTube OAuth,
remotely confirmed result or exactly-once network delivery.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import re
import secrets
from typing import Callable

from autopilot.ci_protected_pg_boundary import (
    _strict_role, GATEWAY_ROLE, AUDITOR_ROLE,
)
from autopilot.youtube_private_first_contract import (
    DryRunUploadIntent, prepare_unapproved_intent,
    ReleaseContractError,
)

HEX64 = re.compile(r"^[0-9a-f]{64}$")
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class MockUploadFenceError(ValueError):
    """Any ambiguous or rejected transition: do NOT start a new insert."""


@dataclass(frozen=True)
class MockPgUploadTicket:
    """Disposable test nonce; never log or store the raw nonce in SQL."""
    channel_id: str
    episode_id: str
    context_sha256: str
    ephemeral_token: str = field(repr=False)
    simulated_only: bool = True
    release_authorized: bool = False


def validate_mock_intent(intent: DryRunUploadIntent) -> None:
    if (type(intent) is not DryRunUploadIntent
        or intent.simulation_only is not True
        or intent.real_owner_approval is not False
        or intent.real_youtube_oauth is not False
        or intent.release_authorized is not False):
        raise MockUploadFenceError("Only B4a unapproved immutable dry-run intentions accepted")
    try:
        canonical = prepare_unapproved_intent(
            episode_id=intent.episode_id, slot=intent.slot,
            channel_id=intent.channel_id, final_mp4_sha256=intent.final_mp4_sha256,
            captions_srt_sha256=intent.captions_srt_sha256,
            thumbnail_sha256=intent.thumbnail_sha256,
            source_review_context_sha256=intent.source_review_context_sha256,
            title=intent.title, description=intent.description, language=intent.language,
            synthetic_media_disclosure=intent.synthetic_media_disclosure,
            made_for_kids=intent.made_for_kids,
            publish_at_utc=intent.publish_at_utc, now=datetime.now(timezone.utc),
        )
    except ReleaseContractError as exc:
        raise MockUploadFenceError("Mock intent invalid or expired") from exc
    if intent != canonical:
        raise MockUploadFenceError("Forged digest or unapproved attributes")


class ProtectedCiYouTubeFence:
    """Disposable PostgreSQL 16 gateway for mock-only one-shot evidence."""

    def __init__(self, connect: Callable):
        _strict_role(connect, GATEWAY_ROLE)
        self._connect = connect

    def reserve_mock(self, intent: DryRunUploadIntent) -> MockPgUploadTicket:
        validate_mock_intent(intent)
        nonce = secrets.token_hex(32)
        nonce_sha = sha256(nonce.encode("ascii")).hexdigest()
        try:
            with self._connect() as db:
                with db.transaction():
                    with db.cursor() as cur:
                        cur.execute(
                            "SELECT fm_private_ci.reserve_youtube_mock_once("
                            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (intent.channel_id, intent.episode_id, intent.slot,
                             intent.publish_at_utc, intent.context_sha256,
                             intent.final_mp4_sha256, intent.captions_srt_sha256,
                             intent.thumbnail_sha256, intent.source_review_context_sha256,
                             nonce_sha),
                        )
                        state = cur.fetchone()[0]
                        if state != "POSSIBLY_SENT_NO_RETRY":
                            raise MockUploadFenceError("Unexpected mock reservation")
        except Exception as exc:
            raise MockUploadFenceError(
                "Ambiguous/duplicate PostgreSQL reservation; never attempt remote insert"
            ) from exc
        return MockPgUploadTicket(
            intent.channel_id, intent.episode_id, intent.context_sha256, nonce,
        )

    def report_unverified_remote_id(self, ticket: MockPgUploadTicket, remote_id: str) -> str:
        if (type(ticket) is not MockPgUploadTicket
            or ticket.simulated_only is not True or ticket.release_authorized is not False
            or not isinstance(ticket.ephemeral_token, str)
            or not HEX64.fullmatch(ticket.ephemeral_token)
            or not isinstance(ticket.context_sha256, str)
            or not HEX64.fullmatch(ticket.context_sha256)
            or not isinstance(remote_id, str) or not VIDEO_ID.fullmatch(remote_id)):
            raise MockUploadFenceError("Invalid non-publishable mock remote ID ticket")
        token_sha = sha256(ticket.ephemeral_token.encode("ascii")).hexdigest()
        try:
            with self._connect() as db:
                with db.transaction():
                    with db.cursor() as cur:
                        cur.execute(
                            "SELECT fm_private_ci.note_youtube_mock_remote_id_once(%s,%s,%s,%s)",
                            (ticket.channel_id, ticket.episode_id, token_sha, remote_id),
                        )
                        state = cur.fetchone()[0]
                        if state != "REMOTE_ID_REPORTED_UNVERIFIED":
                            raise MockUploadFenceError("Mock remote ID not recorded")
            return state
        except Exception as exc:
            raise MockUploadFenceError(
                "Uncertain/invalid mock remote ID, never initiate another upload"
            ) from exc


class MockYouTubeFenceAuditor:
    """A separate no-table-access role sees redacted counters/status only."""

    def __init__(self, connect: Callable):
        _strict_role(connect, AUDITOR_ROLE)
        self._connect = connect

    def inspect(self, channel_id: str, episode_id: str) -> dict:
        if (not isinstance(channel_id,str) or
            not re.fullmatch(r"UC[A-Za-z0-9_-]{22}",channel_id)
            or not isinstance(episode_id,str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{8,100}",episode_id)):
            raise MockUploadFenceError("Invalid mock audit scope")
        try:
            with self._connect() as db:
                with db.cursor() as cur:
                    cur.execute(
                        "SELECT state,attempt_count,audit_event_count,unverified_remote_video_id "
                        "FROM fm_private_ci.inspect_youtube_mock_attempt(%s,%s)",
                        (channel_id,episode_id),
                    )
                    row = cur.fetchone()
        except Exception as exc:
            raise MockUploadFenceError("Mock audit unavailable") from exc
        if row is None:
            raise MockUploadFenceError("Unknown mock attempt: no release evidence")
        state,attempt_count,event_count,unverified_id = row
        return {
            "state":state, "attempt_count":attempt_count,
            "audit_event_count":event_count,
            "unverified_remote_video_id":unverified_id,
            "real_youtube_insert_performed":False,
            "real_owner_oauth_authenticated":False,
            "real_cloud_persistence_deployed":False,
            "real_media_or_rights_approved":False,
            "real_youtube_processing_verified":False,
            "real_youtube_scheduled":False,
            "real_youtube_published":False,
            "release_authorized":False,
        }
