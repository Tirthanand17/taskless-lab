"""FlowMinute Autopilot control plane (standard library only).

No network, OAuth, billing or publishing in this module. A separate privileged
adapter must supply authentic YouTube receipts. Failed/ambiguous API calls never
trigger a duplicate request here.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import json
import sqlite3

CHANNEL_ID = "UCCcL9Q_jqVq6LJmnYUSAFZA"
IST = ZoneInfo("Asia/Kolkata")
SLOTS = {"short_am": (11, 0), "long": (16, 0), "short_pm": (20, 30)}

class GateError(ValueError):
    """Release must stop rather than guess."""

class Stage(str, Enum):
    PLANNED = "planned"
    FACTS_VERIFIED = "facts_verified"
    QA_PASSED = "qa_passed"
    UPLOAD_UNRESOLVED = "upload_unresolved"
    PRIVATE_UPLOADED = "private_uploaded"
    PROCESSING_SUCCEEDED = "processing_succeeded"
    SCHEDULE_UNRESOLVED = "schedule_unresolved"
    SCHEDULED_VERIFIED = "scheduled_verified"
    PUBLIC_VERIFIED = "public_verified"
    QUARANTINED = "quarantined"

NEXT = {
    Stage.PLANNED: {Stage.FACTS_VERIFIED, Stage.QUARANTINED},
    Stage.FACTS_VERIFIED: {Stage.QA_PASSED, Stage.QUARANTINED},
    Stage.QA_PASSED: {Stage.UPLOAD_UNRESOLVED, Stage.QUARANTINED},
    Stage.UPLOAD_UNRESOLVED: {Stage.PRIVATE_UPLOADED, Stage.QUARANTINED},
    Stage.PRIVATE_UPLOADED: {Stage.PROCESSING_SUCCEEDED, Stage.QUARANTINED},
    Stage.PROCESSING_SUCCEEDED: {Stage.SCHEDULE_UNRESOLVED, Stage.QUARANTINED},
    Stage.SCHEDULE_UNRESOLVED: {Stage.SCHEDULED_VERIFIED, Stage.QUARANTINED},
    Stage.SCHEDULED_VERIFIED: {Stage.PUBLIC_VERIFIED, Stage.QUARANTINED},
    Stage.PUBLIC_VERIFIED: set(),
    Stage.QUARANTINED: set()
}

def slot_utc(day: str, kind: str) -> str:
    if kind not in SLOTS:
        raise GateError("Unknown publishing slot")
    try:
        d = date.fromisoformat(day)
    except ValueError as exc:
        raise GateError("Use YYYY-MM-DD") from exc
    hour, minute = SLOTS[kind]
    return datetime(d.year,d.month,d.day,hour,minute,tzinfo=IST).astimezone(timezone.utc).isoformat()

def require_future(utc_time: str, *, now: datetime | None = None, lead_minutes: int = 15):
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise GateError("Timezone-aware clock required")
    requested = datetime.fromisoformat(utc_time)
    if requested.tzinfo is None or requested <= clock + timedelta(minutes=lead_minutes):
        raise GateError("Never schedule a past/near-past video")

@dataclass(frozen=True)
class Topic:
    title: str
    viewer_benefit: str
    original_example: str
    source_urls: tuple[str, ...]
    editorial_score: float

    def validate(self, recent_titles: tuple[str, ...] = ()):
        if not .72 <= self.editorial_score <= 1:
            raise GateError("Topic does not meet minimum value threshold")
        if len(self.title.strip()) < 12 or len(self.viewer_benefit.strip()) < 35:
            raise GateError("Missing meaningful viewer benefit")
        if len(self.original_example.strip()) < 25:
            raise GateError("Must provide a distinct practical example")
        domains = set()
        for url in self.source_urls:
            p = urlparse(url)
            if p.scheme != "https" or not p.hostname or p.username:
                raise GateError("Attributable HTTPS research source required")
            domains.add(p.hostname)
        if len(self.source_urls) < 2 or len(domains) < 2:
            raise GateError("Require at least two independent sources")
        a = set(self.title.lower().split())
        for recent in recent_titles:
            b = set(recent.lower().split())
            if len(a & b) / max(1,len(a | b)) >= .7:
                raise GateError("Duplicate topic / little audience novelty")

@dataclass(frozen=True)
class MediaQA:
    sha256: str
    duration_s: float
    voice_duration_s: float
    width: int
    height: int
    peak_db: float
    decoded: bool
    captions_verified: bool
    rights_verified: bool
    facts_verified: bool
    thumbnail_verified: bool

    def validate(self, kind: str):
        if kind not in (*SLOTS, "short"): raise GateError("Unknown format")
        if len(self.sha256)!=64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise GateError("Missing media SHA256")
        if (self.width,self.height) != ((1920,1080) if kind=="long" else (1080,1920)):
            raise GateError("Incorrect media dimensions")
        minimum, maximum = (120,900) if kind=="long" else (20,180)
        if not minimum <= self.duration_s <= maximum or not 10 < self.voice_duration_s <= self.duration_s <= self.voice_duration_s+3:
            raise GateError("Truncated narration or incorrect duration")
        if not -60 <= self.peak_db <= -1: raise GateError("Audio peaks invalid")
        if not all((self.decoded,self.captions_verified,self.rights_verified,
                    self.facts_verified,self.thumbnail_verified)):
            raise GateError("Missing decode/caption/rights/facts/thumbnail clearance")

@dataclass
class Provider:
    name: str
    purpose: str
    approved: bool
    max_jobs_daily: int
    cost_usd: float = 0.0
    used_today: int = 0
    blocked_until: datetime | None = None
    enabled: bool = True

    def usable(self, task: str, remaining_budget: float, now: datetime) -> bool:
        return (self.purpose==task and self.approved and self.enabled and
                self.used_today < self.max_jobs_daily and
                self.cost_usd <= remaining_budget and
                (not self.blocked_until or now >= self.blocked_until))

class ProviderRouter:
    """Use authorized providers only; 401/403 disables, 429 cooldown; never evade limits."""
    def __init__(self, providers: list[Provider]):
        self.providers = providers

    def choose(self, task: str, remaining_budget: float = 0,
               now: datetime | None = None) -> Provider:
        now=now or datetime.now(timezone.utc)
        choices=[p for p in self.providers if p.usable(task,remaining_budget,now)]
        if not choices: raise GateError("No approved provider: quarantine and alert")
        return sorted(choices,key=lambda p:(p.cost_usd,p.used_today,p.name))[0]

    def record_success(self, p: Provider):
        p.used_today += 1

    def record_failure(self, p: Provider, http_status: int, now: datetime | None = None):
        if http_status in (401,403):
            p.enabled = False
        elif http_status == 429:
            p.blocked_until = (now or datetime.now(timezone.utc))+timedelta(minutes=45)
        else:
            p.blocked_until = (now or datetime.now(timezone.utc))+timedelta(minutes=10)

class ReleaseLedger:
    """Atomic immutable reservations. Only read-only-verified receipts advance releases."""
    def __init__(self, db_file: Path):
        self.path=Path(db_file)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._db() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS releases (
                episode TEXT PRIMARY KEY, kind TEXT NOT NULL, planned_utc TEXT NOT NULL,
                sha TEXT NOT NULL UNIQUE, channel TEXT NOT NULL, stage TEXT NOT NULL,
                youtube_id TEXT, receipt TEXT NOT NULL DEFAULT '{}',
                UNIQUE(kind,planned_utc))""")

    def _db(self):
        con=sqlite3.connect(self.path,timeout=30)
        con.execute("PRAGMA busy_timeout=30000")
        return con

    def reserve(self, episode: str, kind: str, day: str, sha: str,
                *, channel: str = CHANNEL_ID, now: datetime | None = None) -> bool:
        if not episode or not episode.replace("_","").isalnum():
            raise GateError("Invalid episode id")
        if channel != CHANNEL_ID: raise GateError("Unexpected YouTube channel")
        if len(sha)!=64 or any(c not in "0123456789abcdef" for c in sha):
            raise GateError("Media hash missing")
        target=slot_utc(day,kind)
        require_future(target,now=now)
        with self._db() as con:
            con.execute("BEGIN IMMEDIATE")
            old=con.execute("SELECT kind,planned_utc,sha,channel FROM releases WHERE episode=?",(episode,)).fetchone()
            if old:
                if tuple(old) != (kind,target,sha,channel):
                    raise GateError("Episode already reserved for different content")
                return False
            # Adaptive kind='short' and legacy short_am/short_pm can share
            # the same timestamp; the old UNIQUE(kind,planned_utc) index
            # is insufficient on its own to prevent a duplicate release.
            if con.execute("SELECT 1 FROM releases WHERE planned_utc=? LIMIT 1",
                           (target,)).fetchone():
                raise GateError("Existing release occupies proposed time")
            try:
                con.execute("INSERT INTO releases (episode,kind,planned_utc,sha,channel,stage) VALUES (?,?,?,?,?,?)",
                            (episode,kind,target,sha,channel,Stage.PLANNED.value))
            except sqlite3.IntegrityError as exc:
                raise GateError("Duplicate media or conflicting time slot") from exc
            return True

    def reserve_prepared_batch(self, entries: list[tuple[str,str,str,str]], *,
                               channel: str = CHANNEL_ID,
                               now: datetime | None = None) -> dict[str,bool]:
        """Atomically reserve QA-cleared adaptive calendar entries.

        Entry: (episode, 'short'|'long', exact UTC ISO time, media SHA256).
        This is a LOCAL ledger operation, not an API upload or scheduling call.
        Every row either commits or the whole batch rolls back, including when
        it conflicts with an existing legacy short_am/short_pm reservation.
        """
        if channel != CHANNEL_ID:
            raise GateError("Unexpected YouTube channel")
        if not 1 <= len(entries) <= 18:
            raise GateError("One to eighteen prepared media records required")
        seen_episodes, seen_hashes, seen_times = set(), set(), set()
        cleaned = []
        for episode, kind, utc, sha in entries:
            if not isinstance(episode, str) or not episode or not episode.replace("_","").isalnum():
                raise GateError("Invalid episode id")
            if kind not in ("short","long"):
                raise GateError("Unsupported adaptive format")
            if not isinstance(sha,str) or len(sha)!=64 or any(x not in "0123456789abcdef" for x in sha):
                raise GateError("Media SHA256 required")
            if not isinstance(utc,str):
                raise GateError("Exact timezone-aware UTC required")
            try:
                instant=datetime.fromisoformat(utc)
            except ValueError as exc:
                raise GateError("Invalid UTC timestamp") from exc
            if instant.tzinfo is None or instant.utcoffset()!=timedelta(0):
                raise GateError("UTC timezone required")
            canonical=instant.astimezone(timezone.utc).isoformat()
            if utc != canonical:
                raise GateError("Use canonical UTC timestamp")
            require_future(canonical,now=now)
            if episode in seen_episodes or sha in seen_hashes or canonical in seen_times:
                raise GateError("Duplicate episode, media hash or UTC slot in batch")
            seen_episodes.add(episode)
            seen_hashes.add(sha)
            seen_times.add(canonical)
            cleaned.append((episode,kind,canonical,sha))
        result={}
        with self._db() as con:
            con.execute("BEGIN IMMEDIATE")
            for episode, kind, utc, sha in cleaned:
                old=con.execute(
                    "SELECT kind,planned_utc,sha,channel FROM releases WHERE episode=?",
                    (episode,)).fetchone()
                if old:
                    if tuple(old) != (kind,utc,sha,channel):
                        raise GateError("Episode reserved for different content")
                    result[episode]=False
                    continue
                # The legacy UNIQUE(kind,planned_utc) index cannot catch a
                # short_am reservation colliding with new kind='short'.
                if con.execute("SELECT 1 FROM releases WHERE planned_utc=? LIMIT 1",
                               (utc,)).fetchone():
                    raise GateError("Existing video occupies proposed publishing time")
                try:
                    con.execute(
                        "INSERT INTO releases (episode,kind,planned_utc,sha,channel,stage) VALUES (?,?,?,?,?,?)",
                        (episode,kind,utc,sha,channel,Stage.PLANNED.value))
                except sqlite3.IntegrityError as exc:
                    raise GateError("Duplicate media or conflicting release") from exc
                result[episode]=True
        return result

    def get(self, episode: str) -> dict:
        with self._db() as con:
            con.row_factory=sqlite3.Row
            row=con.execute("SELECT * FROM releases WHERE episode=?",(episode,)).fetchone()
            if row is None: raise GateError("Unknown episode")
            return dict(row)

    def advance(self, episode: str, new: Stage, receipt: dict | None = None) -> bool:
        with self._db() as con:
            con.execute("BEGIN IMMEDIATE")
            row=con.execute("SELECT stage,channel,planned_utc,youtube_id FROM releases WHERE episode=?",(episode,)).fetchone()
            if not row: raise GateError("Unknown episode")
            old=Stage(row[0])
            if new==old: return False
            if new not in NEXT[old]:raise GateError("Unsafe or skipped state transition")
            receipt=receipt or {}
            if new in {Stage.PRIVATE_UPLOADED,Stage.PROCESSING_SUCCEEDED,Stage.SCHEDULED_VERIFIED,Stage.PUBLIC_VERIFIED}:
                if receipt.get("source")!="authenticated_youtube_api" or receipt.get("channel")!=row[1]:
                    raise GateError("Authenticated channel evidence required")
                if not (receipt.get("youtube_id") or row[3]):raise GateError("Remote video id required")
            if new in {Stage.SCHEDULED_VERIFIED,Stage.PUBLIC_VERIFIED} and receipt.get("publish_at_utc")!=row[2]:
                raise GateError("Exact UTC publishing time not verified")
            if row[3] and receipt.get("youtube_id") and receipt["youtube_id"]!=row[3]:
                raise GateError("Never substitute a new YouTube upload ID")
            youtube_id=receipt.get("youtube_id") or row[3]
            con.execute("UPDATE releases SET stage=?,youtube_id=?,receipt=? WHERE episode=?",
                        (new.value,youtube_id,json.dumps(receipt,sort_keys=True),episode))
            return True
