"""Isolated, OFFLINE, strict-only transcript review IPC rehearsal.

Only an allowlisted HMAC-authenticated episode admission can cross this
Unix-socket boundary. All candidate media hashes, detached reviewer claims,
external-key registry, evidence file paths and SQLite DB are pre-provisioned
by the trusted parent; they are NEVER accepted from untrusted socket JSON.
No access to the old detached-only ledger.commit, publishing, shell, SQL,
network services, credentials or arbitrary file paths is provided.

This is a Linux synthetic/test-only isolation demonstration. Same-UID
processes may still access the test DB and filesystem directly; HMAC key
provisioning and reviewer identities lack real-world external trust.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from typing import Mapping
import hashlib
import hmac
import json
import os
import re
import socketserver
import time

from .agent_org import WorkflowError
from .cloud_transcript_replay_ledger import OfflineTranscriptReviewLedger
from .cloud_transcript_alignment_intake import CandidateWordTranscript
from .cloud_full_media_evidence import TechnicalFullHDObservation
from .cloud_muxed_audio_screen import MuxedAudioScreen
from .cloud_signed_transcript_reviews import (
    SignedTranscriptAttestation,TrustedTranscriptReviewer,SAFE_ID,
)
from .agent_staging_ipc_service import _require_socket_path

MAX_FRAME=2048
MAX_REPLY=2048
NONCE=re.compile(r"[a-z0-9_]{16,64}\Z")
SHA=re.compile(r"[0-9a-f]{64}\Z")
WIRE_KEYS=frozenset((
    "action","episode_id","expected_current_sha","nonce",
    "expires_at_epoch","mac_sha256",
))
SIGNED_KEYS=WIRE_KEYS-{"mac_sha256"}


@dataclass(frozen=True)
class OfflineReviewBundle:
    candidate:CandidateWordTranscript
    media:TechnicalFullHDObservation
    audio_screen:MuxedAudioScreen
    signed_attestations:tuple[SignedTranscriptAttestation,...]
    registry:Mapping[str,TrustedTranscriptReviewer]
    excluded_creator_publisher_ids:frozenset[str]
    evidence_files:Mapping[str,Path]


def _unique(pairs):
    obj={}
    for key,value in pairs:
        if key in obj:
            raise WorkflowError("Duplicate strict transcript command field")
        obj[key]=value
    return obj


def _reject_constant(value):
    raise WorkflowError("Non-finite transcript command field")


def canonical_signed_command(fields:dict)->bytes:
    """Deterministic bytes for offline HMAC signing by trusted caller."""
    if not isinstance(fields,dict) or set(fields)!=SIGNED_KEYS:
        raise WorkflowError("Strict transcript command fields incomplete")
    return json.dumps(fields,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


class StrictTranscriptReviewCommandBoundary:
    """No legacy review call, no admin routes, no remote content/path intake."""

    def __init__(self,ledger:OfflineTranscriptReviewLedger, *,
                 reviews:Mapping[str,OfflineReviewBundle],hmac_key:bytes):
        if (not isinstance(ledger,OfflineTranscriptReviewLedger)
                or not isinstance(reviews,Mapping)
                or not 1<=len(reviews)<=16
                or type(hmac_key) is not bytes or len(hmac_key)<32):
            raise WorkflowError("Trusted offline review boundary missing")
        for episode,bundle in reviews.items():
            if (not isinstance(episode,str) or SAFE_ID.fullmatch(episode) is None
                    or not isinstance(bundle,OfflineReviewBundle)
                    or bundle.candidate.episode_id!=episode):
                raise WorkflowError("Trusted review inventory malformed")
        self._ledger=ledger
        self._reviews=dict(reviews)
        self._hmac_key=hmac_key

    def execute(self,raw:str)->dict:
        if (type(raw) is not str or not 0<len(raw.encode("utf-8"))<=MAX_FRAME):
            raise WorkflowError("Signed review frame missing or too large")
        try:
            obj=json.loads(raw,object_pairs_hook=_unique,
                           parse_constant=_reject_constant)
        except (ValueError,TypeError,UnicodeError) as exc:
            raise WorkflowError("Invalid signed review JSON") from exc
        if not isinstance(obj,dict) or set(obj)!=WIRE_KEYS:
            raise WorkflowError("Strict review command shape denied")
        signed={k:obj[k] for k in SIGNED_KEYS}
        episode=signed["episode_id"]
        current=signed["expected_current_sha"]
        expiry=signed["expires_at_epoch"]
        nonce=signed["nonce"]
        mac=obj["mac_sha256"]
        if (signed["action"]!="review.admit"
                or type(episode) is not str
                or SAFE_ID.fullmatch(episode) is None
                or (current is not None
                    and (type(current) is not str
                         or SHA.fullmatch(current) is None))
                or type(nonce) is not str or NONCE.fullmatch(nonce) is None
                or type(expiry) is not int
                or type(mac) is not str or SHA.fullmatch(mac) is None):
            raise WorkflowError("Unapproved signed review operation")
        tick=int(time.time())
        if not tick<=expiry<=tick+300:
            raise WorkflowError("Expired or far-future local review command")
        expected=hmac.new(self._hmac_key,canonical_signed_command(signed),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(mac,expected):
            raise WorkflowError("Review command signature invalid")
        bundle=self._reviews.get(episode)
        if bundle is None:
            raise WorkflowError("Review episode not pre-provisioned")
        # The legacy detached-only commit method is NOT accessible here.
        # SQLite BEGIN IMMEDIATE, host clock, both external signed reviews,
        # actual sidecar byte digests and one-use receipt journal are enforced.
        response=self._ledger.commit_sidecar_bound(
            candidate=bundle.candidate,media=bundle.media,
            audio_screen=bundle.audio_screen,
            signed_attestations=bundle.signed_attestations,
            registry=bundle.registry,
            excluded_creator_publisher_ids=bundle.excluded_creator_publisher_ids,
            evidence_files=bundle.evidence_files,
            expected_current_sha=current,
            signed_command_nonce=nonce,
            signed_command_expires_at_epoch=expiry,
            now=None,
        )
        if (not response["signed_sidecar_digests_chained"]
                or not response["signed_command_nonce_chained"]):
            raise WorkflowError("Strict-only transcript admission invariant failed")
        # Do not return raw episode/video/transcript/review identities over IPC.
        return {
            "status":"OFFLINE_STRICT_REVIEW_JOURNALED",
            "event_number":response["event_number"],
            "two_signed_sidecar_digests_chained":True,
            "signed_command_nonce_persisted":True,
            "real_audio_verified":False,
            "real_reviewer_identity_verified":False,
            "youtube_upload_authorized":False,
            "publishing_authorized":False,
            "monthly_recurring_infrastructure_inr":0,
        }


class _ReviewHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(2)
        try:
            wire=self.rfile.readline(MAX_FRAME+2)
            if (not wire.endswith(b"\n") or len(wire)>MAX_FRAME+1):
                raise WorkflowError("Malformed bounded strict review frame")
            result=self.server.boundary.execute(wire[:-1].decode("utf-8"))
            payload={"ok":True,"result":result}
        except (WorkflowError,ValueError,TypeError,OSError,TimeoutError,
                UnicodeError):
            payload={"ok":False,"error":"STRICT_REVIEW_DENIED"}
        reply=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        if len(reply)>MAX_REPLY:
            reply=b'{"ok":false,"error":"STRICT_REVIEW_DENIED"}'
        try:
            self.wfile.write(reply+b"\n")
            self.wfile.flush()
        except (OSError,TimeoutError):
            pass


class OfflineStrictTranscriptReviewIPC(socketserver.ThreadingMixIn,
                                       socketserver.UnixStreamServer):
    """No TCP and no upload route; 0600 socket owned by the test process."""
    daemon_threads=True
    allow_reuse_address=False
    request_queue_size=4

    def __init__(self,location:Path,boundary:StrictTranscriptReviewCommandBoundary):
        if not isinstance(boundary,StrictTranscriptReviewCommandBoundary):
            raise WorkflowError("Strict transcript command boundary required")
        self.location=_require_socket_path(Path(location))
        self.boundary=boundary
        super().__init__(str(self.location),_ReviewHandler)
        os.chmod(self.location,0o600)
        node=self.location.stat()
        self._socket_identity=(node.st_dev,node.st_ino)

    def server_close(self):
        super().server_close()
        # Unlike the staging server, this is only ever a disposable fixture
        # socket. Do not delete a replacement file at the same path.
        try:
            import stat
            node=self.location.lstat()
            if (stat.S_ISSOCK(node.st_mode)
                    and (node.st_dev,node.st_ino)==self._socket_identity):
                self.location.unlink()
        except (FileNotFoundError,AttributeError):
            pass


def serve_offline_strict_review(*,db_path:Path,socket_path:Path,
                                reviews:Mapping[str,OfflineReviewBundle],
                                hmac_key:bytes,ready_pipe=None):
    """Trusted-process entrypoint, NEVER a deployed public service."""
    try:
        ledger=OfflineTranscriptReviewLedger(Path(db_path))
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=reviews,hmac_key=hmac_key,
        )
        with OfflineStrictTranscriptReviewIPC(Path(socket_path),boundary) as server:
            if ready_pipe is not None:
                ready_pipe.send(True)
                ready_pipe.close()
            server.serve_forever(poll_interval=0.05)
    except Exception:
        if ready_pipe is not None:
            try:
                ready_pipe.send(False)
                ready_pipe.close()
            except (BrokenPipeError,EOFError,OSError):
                pass
        raise
