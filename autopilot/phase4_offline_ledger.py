"""Phase 4 OFFLINE SQLite/D1 protocol simulation -- not a production writer.

No Cloudflare API, OAuth, YouTube calls, provisioning or actual publishing.
The credentialed D1 adapter must implement equivalent atomic predicates and
independently verify remote receipts before any real migration is considered.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .core import CHANNEL_ID

UTC = dt.timezone.utc
STAGES = (
    "planned", "research_verified", "script_verified", "media_qa_passed",
    "upload_uncertain", "remote_private_verified", "schedule_uncertain",
    "scheduled_verified", "public_verified", "quarantined",
)
LOCAL_NEXT = {
    "planned": "research_verified",
    "research_verified": "script_verified",
    "script_verified": "media_qa_passed",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
EPISODE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")
VIDEO = re.compile(r"[A-Za-z0-9_-]{11}\Z")
OWNER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")


class ProtocolBlocked(ValueError):
    """The simulated single-writer ledger rejects an unsafe state change."""


def _instant(value: str) -> dt.datetime:
    try:
        item = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ProtocolBlocked("Valid canonical UTC timestamp required") from exc
    if item.tzinfo is None or item.utcoffset() != dt.timedelta(0):
        raise ProtocolBlocked("Timestamp must be UTC")
    if value != item.astimezone(UTC).isoformat(timespec="seconds"):
        raise ProtocolBlocked("Timestamp must be exact canonical seconds UTC")
    return item


def _sha(value: str) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


class OfflineLedger:
    """A SQLite reference simulator only; explicit opt-in avoids accidental use.

    Claims such as authenticated=True are synthetic caller-supplied facts.
    They MUST NOT be used as production proof or upload authorization.
    """
    def __init__(self, db: str | Path = ":memory:", *, offline_test_only: bool = False):
        if not offline_test_only:
            raise ProtocolBlocked("Only offline test simulations are permitted")
        self.db = sqlite3.connect(str(db), isolation_level=None, timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout = 5000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS phase4_releases (
                channel_id TEXT NOT NULL, episode_id TEXT NOT NULL,
                planned_utc TEXT NOT NULL, media_sha256 TEXT NOT NULL,
                stage TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0,
                review_digest TEXT, youtube_id TEXT UNIQUE, intent_id TEXT UNIQUE,
                fence INTEGER NOT NULL DEFAULT 0, lease_owner TEXT,
                lease_until TEXT,
                PRIMARY KEY (channel_id,episode_id),
                UNIQUE (channel_id,planned_utc),
                UNIQUE (channel_id,media_sha256)
            );
            CREATE TABLE IF NOT EXISTS phase4_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL, episode_id TEXT NOT NULL,
                version INTEGER NOT NULL, action TEXT NOT NULL,
                at_utc TEXT NOT NULL, detail_json TEXT NOT NULL,
                UNIQUE (channel_id,episode_id,version)
            );
            CREATE TRIGGER IF NOT EXISTS phase4_events_no_update
            BEFORE UPDATE ON phase4_events BEGIN
                SELECT RAISE(ABORT, 'Append-only events cannot be updated');
            END;
            CREATE TRIGGER IF NOT EXISTS phase4_events_no_delete
            BEFORE DELETE ON phase4_events BEGIN
                SELECT RAISE(ABORT, 'Append-only events cannot be deleted');
            END;
        """)

    @contextmanager
    def _atomic(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _row(self, episode: str):
        return self.db.execute(
            "SELECT * FROM phase4_releases WHERE channel_id=? AND episode_id=?",
            (CHANNEL_ID, episode),
        ).fetchone()

    def get(self, episode: str) -> dict | None:
        row = self._row(episode)
        return dict(row) if row else None

    def events(self, episode: str) -> list[dict]:
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM phase4_events WHERE channel_id=? AND episode_id=? ORDER BY event_id",
            (CHANNEL_ID, episode),
        )]

    def _log(self, episode: str, version: int, action: str, at: str, detail: dict):
        self.db.execute(
            "INSERT INTO phase4_events(channel_id,episode_id,version,action,at_utc,detail_json) "
            "VALUES (?,?,?,?,?,?)",
            (CHANNEL_ID, episode, version, action, at,
             json.dumps(detail, sort_keys=True, separators=(",", ":"))),
        )

    def reserve(self, *, channel: str, episode: str, planned_utc: str,
                media_sha256: str, now_utc: str) -> bool:
        if channel != CHANNEL_ID or not isinstance(episode, str) or not EPISODE.fullmatch(episode):
            raise ProtocolBlocked("Expected channel and safe episode ID required")
        _instant(planned_utc)
        _instant(now_utc)
        if not _sha(media_sha256):
            raise ProtocolBlocked("Immutable lowercase media SHA256 required")
        with self._atomic():
            old = self._row(episode)
            if old:
                if (old["planned_utc"], old["media_sha256"]) != (planned_utc, media_sha256):
                    raise ProtocolBlocked("Episode already bound to another slot or media")
                return False
            try:
                self.db.execute(
                    "INSERT INTO phase4_releases(channel_id,episode_id,planned_utc,media_sha256,stage) "
                    "VALUES (?,?,?,?,?)", (channel,episode,planned_utc,media_sha256,"planned"),
                )
            except sqlite3.IntegrityError as exc:
                raise ProtocolBlocked("Slot or media already reserved") from exc
            self._log(episode, 0, "reserved", now_utc,
                      {"slot_utc": planned_utc, "media_sha256": media_sha256})
            return True

    def claim(self, episode: str, *, expected_version: int, owner: str,
              now_utc: str, ttl_seconds: int = 120) -> tuple[int,int]:
        now = _instant(now_utc)
        if not isinstance(owner,str) or not OWNER.fullmatch(owner):
            raise ProtocolBlocked("Safe worker ID required")
        if not isinstance(ttl_seconds,int) or not 1 <= ttl_seconds <= 300:
            raise ProtocolBlocked("Short bounded lease TTL required")
        until = (now+dt.timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds")
        with self._atomic():
            r=self._row(episode)
            if not r or r["version"] != expected_version:
                raise ProtocolBlocked("Stale release version")
            if r["stage"] in ("public_verified","quarantined"):
                raise ProtocolBlocked("Terminal release is immutable")
            if r["lease_until"] is not None and _instant(r["lease_until"]) > now:
                raise ProtocolBlocked("Active lease cannot be stolen even by same worker")
            version, fence = expected_version+1, r["fence"]+1
            changed=self.db.execute(
                "UPDATE phase4_releases SET version=?,fence=?,lease_owner=?,lease_until=? "
                "WHERE channel_id=? AND episode_id=? AND version=?",
                (version,fence,owner,until,CHANNEL_ID,episode,expected_version),
            ).rowcount
            if changed!=1:
                raise ProtocolBlocked("Concurrent version change")
            self._log(episode,version,"lease_claimed",now_utc,
                      {"worker":owner,"fence":fence,"expires_utc":until})
            return version,fence

    def _check(self, episode: str, *, stage: str, version: int, owner: str,
               fence: int, now_utc: str):
        now=_instant(now_utc)
        r=self._row(episode)
        if not r or r["stage"] != stage or r["version"] != version:
            raise ProtocolBlocked("Release stage/version changed: reconcile")
        if (r["lease_owner"] != owner or r["fence"] != fence or
                r["lease_until"] is None or _instant(r["lease_until"]) <= now):
            raise ProtocolBlocked("Missing, expired or superseded fencing lease")
        return r

    def _move(self, episode: str, stage: str, version: int, now_utc: str,
              *, updates: dict | None = None, action: str | None = None,
              detail: dict | None = None) -> int:
        next_version=version+1
        values={"stage":stage,"version":next_version,**(updates or {})}
        fields=", ".join(f"{k}=?" for k in values)
        changed=self.db.execute(
            f"UPDATE phase4_releases SET {fields} WHERE channel_id=? AND episode_id=? AND version=?",
            (*values.values(),CHANNEL_ID,episode,version),
        ).rowcount
        if changed!=1:
            raise ProtocolBlocked("Conditional writer conflict")
        self._log(episode,next_version,action or stage,now_utc,detail or {})
        return next_version

    def local_step(self, episode: str, *, target: str, expected_version: int,
                   owner: str, fence: int, now_utc: str,
                   review_digest: str | None = None) -> int:
        with self._atomic():
            r=self._row(episode)
            if not r or LOCAL_NEXT.get(r["stage"]) != target:
                raise ProtocolBlocked("Local stage skipping or reversal forbidden")
            self._check(episode,stage=r["stage"],version=expected_version,
                        owner=owner,fence=fence,now_utc=now_utc)
            if target=="media_qa_passed" and not _sha(review_digest):
                raise ProtocolBlocked("Separate review evidence digest required; not approval")
            if target!="media_qa_passed" and review_digest is not None:
                raise ProtocolBlocked("Review digest only accepted at media step")
            return self._move(episode,target,expected_version,now_utc,
                              updates={"review_digest":review_digest} if review_digest else None)

    def begin_upload_once(self, episode: str, *, expected_version: int,owner: str,
                          fence: int, media_sha256: str, intent_id: str,
                          now_utc: str) -> int:
        if not isinstance(intent_id,str) or not OWNER.fullmatch(intent_id):
            raise ProtocolBlocked("Non-empty unique upload intent ID required")
        with self._atomic():
            r=self._check(episode,stage="media_qa_passed",version=expected_version,
                          owner=owner,fence=fence,now_utc=now_utc)
            if media_sha256!=r["media_sha256"] or not r["review_digest"]:
                raise ProtocolBlocked("Media hash or review record mismatch")
            try:
                return self._move(episode,"upload_uncertain",expected_version,now_utc,
                                  updates={"intent_id":intent_id},
                                  action="UPLOAD_INTENT_RESERVED_NO_NETWORK",
                                  detail={"intent_id":intent_id})
            except sqlite3.IntegrityError as exc:
                raise ProtocolBlocked("Upload intent already reserved") from exc

    def bind_private_readback(self, episode: str, *, expected_version: int,
                              owner: str, fence: int, now_utc: str,
                              remote_channel: str, youtube_id: str,
                              processed: bool, privacy: str, authenticated: bool) -> int:
        if (remote_channel!=CHANNEL_ID or not isinstance(youtube_id,str) or
            not VIDEO.fullmatch(youtube_id) or processed is not True or
            privacy!="private" or authenticated is not True):
            raise ProtocolBlocked("Exact authenticated private processed readback required")
        with self._atomic():
            self._check(episode,stage="upload_uncertain",version=expected_version,
                        owner=owner,fence=fence,now_utc=now_utc)
            try:
                return self._move(episode,"remote_private_verified",expected_version,
                                  now_utc,updates={"youtube_id":youtube_id},
                                  detail={"youtube_id":youtube_id})
            except sqlite3.IntegrityError as exc:
                raise ProtocolBlocked("Video ID already belongs to another release") from exc

    def begin_schedule_once(self, episode: str, *, expected_version: int,
                            owner: str, fence: int, now_utc: str) -> int:
        with self._atomic():
            self._check(episode,stage="remote_private_verified",version=expected_version,
                        owner=owner,fence=fence,now_utc=now_utc)
            return self._move(episode,"schedule_uncertain",expected_version,now_utc,
                              action="SCHEDULE_INTENT_RESERVED_NO_NETWORK")

    def bind_schedule_readback(self, episode: str, *, expected_version: int,
                               owner: str, fence: int, now_utc: str,
                               youtube_id: str, publish_at_utc: str,
                               authenticated: bool, privacy: str) -> int:
        _instant(publish_at_utc)
        with self._atomic():
            r=self._check(episode,stage="schedule_uncertain",version=expected_version,
                          owner=owner,fence=fence,now_utc=now_utc)
            if (authenticated is not True or privacy!="private" or
                youtube_id!=r["youtube_id"] or publish_at_utc!=r["planned_utc"]):
                raise ProtocolBlocked("Exact ID, private state and UTC schedule readback required")
            return self._move(episode,"scheduled_verified",expected_version,now_utc,
                              detail={"youtube_id":youtube_id,"publish_at_utc":publish_at_utc})

    def bind_public_readback(self, episode: str, *, expected_version: int,
                             owner: str, fence: int, now_utc: str,
                             youtube_id: str, authenticated: bool,
                             playable: bool, privacy: str) -> int:
        with self._atomic():
            r=self._check(episode,stage="scheduled_verified",version=expected_version,
                          owner=owner,fence=fence,now_utc=now_utc)
            if (youtube_id != r["youtube_id"] or authenticated is not True or
                playable is not True or privacy!="public"):
                raise ProtocolBlocked("Actual authenticated matching public readback required")
            return self._move(episode,"public_verified",expected_version,now_utc,
                              detail={"youtube_id":youtube_id})

    def quarantine(self, episode: str, *, expected_version: int,owner: str,
                   fence: int, now_utc: str, reason: str) -> int:
        if not isinstance(reason,str) or not 8 <= len(reason.strip()) <= 160:
            raise ProtocolBlocked("Specific bounded quarantine reason required")
        with self._atomic():
            r=self._row(episode)
            if not r or r["stage"] in ("public_verified","quarantined"):
                raise ProtocolBlocked("Cannot quarantine terminal release")
            self._check(episode,stage=r["stage"],version=expected_version,
                        owner=owner,fence=fence,now_utc=now_utc)
            return self._move(episode,"quarantined",expected_version,now_utc,
                              detail={"reason":reason.strip()})

    def close(self) -> None:
        self.db.close()
