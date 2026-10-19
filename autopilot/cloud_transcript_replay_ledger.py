"""Bounded OFFLINE SQLite audit and anti-replay for signed transcript reviews.

This is a rehearsal of admission receipts, never speech verification or
permission to upload. A single BEGIN IMMEDIATE covers verified signatures,
cross-episode one-time receipt IDs, optimistic episode-head replacement and
the durable digest-chain append. Local filesystem/clock/admin access remain
untrusted production boundaries. No secret/private key/media is persisted.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Mapping
import json
import re
import sqlite3

from .agent_org import WorkflowError
from .cloud_full_media_evidence import TechnicalFullHDObservation
from .cloud_muxed_audio_screen import MuxedAudioScreen
from .cloud_transcript_alignment_intake import CandidateWordTranscript
from .cloud_signed_transcript_reviews import (
    SignedTranscriptAttestation,TrustedTranscriptReviewer,
    transcript_digest,verify_signed_transcript_attestations,
)

MAX_REVIEW_EVENTS=4096
GENESIS_SHA="0"*64
SHA=re.compile(r"[0-9a-f]{64}\Z")
SCHEMA=(
    "CREATE TABLE IF NOT EXISTS transcript_review_events("
    "seq INTEGER PRIMARY KEY AUTOINCREMENT,"
    "event_sha TEXT NOT NULL UNIQUE, prev_sha TEXT NOT NULL,"
    "episode TEXT NOT NULL, lane TEXT NOT NULL,"
    "media_sha TEXT NOT NULL UNIQUE, transcript_sha TEXT NOT NULL,"
    "srt_sha TEXT NOT NULL, transcriber_receipt TEXT NOT NULL,"
    "listener_receipt TEXT NOT NULL, supersedes_sha TEXT,"
    "accepted_at_utc TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS transcript_review_heads("
    "episode TEXT PRIMARY KEY, event_sha TEXT NOT NULL,"
    "FOREIGN KEY(event_sha) REFERENCES transcript_review_events(event_sha))",
    "CREATE TABLE IF NOT EXISTS transcript_review_consumed("
    "receipt_id TEXT PRIMARY KEY, event_sha TEXT NOT NULL,"
    "role TEXT NOT NULL CHECK(role IN ('transcriber','independent_listener')),"
    "FOREIGN KEY(event_sha) REFERENCES transcript_review_events(event_sha))",
)


def _hash_event(payload:dict)->str:
    return sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,
                             separators=(",",":"),allow_nan=False).encode()).hexdigest()


def _event(row:tuple)->dict:
    (seq,event_sha,prev_sha,episode,lane,media_sha,transcript_sha,
     srt_sha,transcriber_receipt,listener_receipt,supersedes_sha,
     accepted_at_utc)=row
    return {
        "seq":seq,"prev_sha":prev_sha,"episode":episode,"lane":lane,
        "media_sha":media_sha,"transcript_sha":transcript_sha,
        "srt_sha":srt_sha,"transcriber_receipt":transcriber_receipt,
        "listener_receipt":listener_receipt,"supersedes_sha":supersedes_sha,
        "accepted_at_utc":accepted_at_utc,
    }


class OfflineTranscriptReviewLedger:
    """Local trusted-process journal; NOT the Phase 4 publishing ledger."""

    def __init__(self,path:Path):
        self.path=Path(path)
        if (not self.path.is_absolute() or not self.path.parent.is_dir()
                or self.path.parent.is_symlink() or self.path.is_symlink()):
            raise WorkflowError("Offline transcript audit needs safe absolute path")
        with self._transaction() as db:
            for statement in SCHEMA:
                db.execute(statement)
            self._audit(db)

    @contextmanager
    def _transaction(self):
        try:
            with sqlite3.connect(self.path,timeout=5,isolation_level=None) as db:
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("PRAGMA busy_timeout=5000")
                db.execute("BEGIN IMMEDIATE")
                try:
                    yield db
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
        except sqlite3.Error as exc:
            raise WorkflowError("Offline transcript SQLite audit unavailable") from exc

    def _audit(self,db:sqlite3.Connection)->tuple[int,str,dict[str,str]]:
        if db.execute("PRAGMA quick_check(1)").fetchall()!=[("ok",)]:
            raise WorkflowError("Transcript audit database failed integrity check")
        rows=db.execute(
            "SELECT seq,event_sha,prev_sha,episode,lane,media_sha,"
            "transcript_sha,srt_sha,transcriber_receipt,listener_receipt,"
            "supersedes_sha,accepted_at_utc "
            "FROM transcript_review_events ORDER BY seq"
        ).fetchall()
        if len(rows)>MAX_REVIEW_EVENTS:
            raise WorkflowError("Transcript audit reached bounded event cap")
        last=GENESIS_SHA
        heads={}
        receipts={}
        seen_media=set()
        for pos,row in enumerate(rows,1):
            detail=_event(row)
            if (type(detail["seq"]) is not int or detail["seq"]!=pos
                    or row[2]!=last
                    or not isinstance(row[1],str) or SHA.fullmatch(row[1]) is None
                    or _hash_event(detail)!=row[1]
                    or not all(isinstance(detail[k],str) and
                               SHA.fullmatch(detail[k]) is not None
                               for k in ("media_sha","transcript_sha","srt_sha"))
                    or detail["media_sha"] in seen_media
                    or (detail["supersedes_sha"]!=heads.get(detail["episode"])
                        if detail["episode"] in heads
                        else detail["supersedes_sha"] is not None)
                    or detail["transcriber_receipt"]==detail["listener_receipt"]):
                raise WorkflowError("Transcript review audit chain corrupted")
            seen_media.add(detail["media_sha"])
            for role,key in (
                ("transcriber","transcriber_receipt"),
                ("independent_listener","listener_receipt"),
            ):
                receipt=detail[key]
                if (not isinstance(receipt,str)
                        or receipt in receipts or not 3<=len(receipt)<=64):
                    raise WorkflowError("Duplicate/corrupt transcript review receipt")
                receipts[receipt]=(last,role)
            last=row[1]
            heads[detail["episode"]]=last
        actual=db.execute(
            "SELECT episode,event_sha FROM transcript_review_heads"
        ).fetchall()
        if dict(actual)!=heads or len(actual)!=len(heads):
            raise WorkflowError("Transcript review current-head index corrupted")
        actual_receipts=db.execute(
            "SELECT receipt_id,event_sha,role FROM transcript_review_consumed"
        ).fetchall()
        expected={}
        for row in rows:
            for receipt,role in ((row[8],"transcriber"),
                                 (row[9],"independent_listener")):
                expected[receipt]=(row[1],role)
        if (len(actual_receipts)!=len(expected)
                or {x[0]:(x[1],x[2]) for x in actual_receipts}!=expected):
            raise WorkflowError("Transcript review consumed-receipt index corrupted")
        return len(rows),last,heads

    def commit(self,*,candidate:CandidateWordTranscript,
               media:TechnicalFullHDObservation,
               audio_screen:MuxedAudioScreen,
               signed_attestations:tuple[SignedTranscriptAttestation,...],
               registry:Mapping[str,TrustedTranscriptReviewer],
               excluded_creator_publisher_ids:frozenset[str],
               now:datetime,
               expected_current_sha:str|None)->dict:
        """One signed-review batch per immutable MP4; replacement needs CAS.

        Reused receipt IDs are rejected even if their signatures remain valid.
        No idempotent replay path: caller must query current_status() after
        a lost ACK, then explicitly begin a new signed review for new media.
        """
        if (expected_current_sha is not None and
                (not isinstance(expected_current_sha,str)
                 or SHA.fullmatch(expected_current_sha) is None)):
            raise WorkflowError("Malformed expected transcript audit head")
        with self._transaction() as db:
            count,last,heads=self._audit(db)
            if count>=MAX_REVIEW_EVENTS:
                raise WorkflowError("Transcript audit full; fail closed")
            verified=verify_signed_transcript_attestations(
                candidate=candidate,media=media,audio_screen=audio_screen,
                signed_attestations=signed_attestations,registry=registry,
                excluded_creator_publisher_ids=excluded_creator_publisher_ids,
                now=now,
            )
            if verified["blocking_reasons"]:
                raise WorkflowError("No accepted two-role transcript signatures")
            if heads.get(candidate.episode_id)!=expected_current_sha:
                raise WorkflowError("Transcript current-head changed; revision denied")
            receipts={}
            for record in signed_attestations:
                role=record.claim.role
                if role in receipts or record.claim.decision!="ACCEPT":
                    raise WorkflowError("Signed transcript role unavailable")
                receipts[role]=record.claim.receipt_id
            if (set(receipts)!={"transcriber","independent_listener"}
                    or len(set(receipts.values()))!=2):
                raise WorkflowError("Exactly two unique signed receipts required")
            for receipt in receipts.values():
                if db.execute(
                    "SELECT 1 FROM transcript_review_consumed WHERE receipt_id=?",
                    (receipt,),
                ).fetchone():
                    raise WorkflowError("Transcript signed review receipt replayed")
            if db.execute(
                "SELECT 1 FROM transcript_review_events WHERE media_sha=?",
                (media.video_sha256,),
            ).fetchone():
                raise WorkflowError("Original video already assigned a review")
            row={
                "seq":count+1,
                "prev_sha":last,
                "episode":candidate.episode_id,
                "lane":candidate.lane,
                "media_sha":media.video_sha256,
                "transcript_sha":transcript_digest(candidate),
                "srt_sha":candidate.authored_draft_srt_sha256,
                "transcriber_receipt":receipts["transcriber"],
                "listener_receipt":receipts["independent_listener"],
                "supersedes_sha":expected_current_sha,
                "accepted_at_utc":now.isoformat(),
            }
            event_sha=_hash_event(row)
            db.execute(
                "INSERT INTO transcript_review_events("
                "seq,event_sha,prev_sha,episode,lane,media_sha,"
                "transcript_sha,srt_sha,transcriber_receipt,listener_receipt,"
                "supersedes_sha,accepted_at_utc) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (row["seq"],event_sha,*tuple(row[k] for k in (
                    "prev_sha","episode","lane","media_sha","transcript_sha",
                    "srt_sha","transcriber_receipt","listener_receipt",
                    "supersedes_sha","accepted_at_utc",
                ))),
            )
            for role,receipt in receipts.items():
                db.execute(
                    "INSERT INTO transcript_review_consumed VALUES(?,?,?)",
                    (receipt,event_sha,role),
                )
            db.execute(
                "INSERT INTO transcript_review_heads VALUES(?,?) "
                "ON CONFLICT(episode) DO UPDATE SET event_sha=excluded.event_sha",
                (candidate.episode_id,event_sha),
            )
            self._audit(db)
            return {
                "status":"OFFLINE_SIGNED_TRANSCRIPT_REVIEW_JOURNALED_ONLY",
                "event_sha256":event_sha,
                "event_number":count+1,
                "episode_id":candidate.episode_id,
                "media_sha256":media.video_sha256,
                "transcript_sha256":row["transcript_sha"],
                "supersedes_sha256":expected_current_sha,
                "actual_audio_content_independently_verified":False,
                "reviewer_identity_independently_verified":False,
                "youtube_publishing_authorized":False,
                "monthly_recurring_infrastructure_inr":0,
            }

    def current_status(self,episode_id:str)->dict:
        if not isinstance(episode_id,str) or not 3<=len(episode_id)<=64:
            raise WorkflowError("Expected bounded episode ID")
        with self._transaction() as db:
            count,last,heads=self._audit(db)
            return {
                "episode_id":episode_id,
                "current_event_sha256":heads.get(episode_id),
                "total_accepted_review_batches":count,
                "audit_tip_sha256":last,
                "source_signed_record_only":True,
                "actual_audio_content_independently_verified":False,
                "youtube_publishing_authorized":False,
            }
