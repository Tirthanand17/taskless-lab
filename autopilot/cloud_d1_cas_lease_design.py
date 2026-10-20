"""Phase 4J: CLOUDFLARE-D1-SHAPED conditional CAS lease *design*, offline only.

D1 Workers supports parameterized statements, single-statement atomic SQL,
and reports D1Result.meta.changes. This file models that ONE-statement
boundary using disposable shared-memory SQLite connections, NOT Cloudflare.

DO NOT run SQL against a real D1 database without a separate schema review,
backup, quota verification, deployment design and explicit owner approval.
This local model uses caller-supplied integer clock ticks: clock skew,
worker restarts, multi-region read replicas, partitions and provider side
effects are UNPROVEN. A fenced upload_started reservation does not make
Youtube videos.insert exactly once. LOST ACK => NO AUTOMATIC RETRY.
"""
from __future__ import annotations

import re
import sqlite3
import uuid

from .agent_org import WorkflowError

# MODEL ONLY; not a migration and not wired to the private D1 collector.
LEASE_SCHEMA = """CREATE TABLE fm_release_lease_shadow (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 owner_nonce TEXT NOT NULL DEFAULT '',
 fence_epoch INTEGER NOT NULL DEFAULT 0 CHECK(fence_epoch>=0),
 expires_at_tick INTEGER NOT NULL DEFAULT 0 CHECK(expires_at_tick>=0),
 last_tick INTEGER NOT NULL DEFAULT 0 CHECK(last_tick>=0)
)"""
LEASE_INITIAL = """INSERT INTO fm_release_lease_shadow
(singleton,owner_nonce,fence_epoch,expires_at_tick,last_tick)
VALUES (1,'',0,0,0)"""
RELEASE_SCHEMA = """CREATE TABLE fm_releases_shadow (
 release_date TEXT NOT NULL, episode_id TEXT NOT NULL,
 media_sha256 TEXT NOT NULL, stage TEXT NOT NULL,
 updated_at TEXT NOT NULL, youtube_id TEXT,
 PRIMARY KEY(release_date,episode_id), UNIQUE(youtube_id)
)"""
# A single conditional UPDATE is the claim's indivisible D1 SQL statement;
# a prior SELECT + unguarded UPDATE is an unsafe distributed lock pattern.
CLAIM_SQL = """UPDATE fm_release_lease_shadow
SET owner_nonce=?,fence_epoch=fence_epoch+1,expires_at_tick=?,last_tick=?
WHERE singleton=1 AND fence_epoch=? AND expires_at_tick<=? AND last_tick<=?"""
RENEW_SQL = """UPDATE fm_release_lease_shadow
SET expires_at_tick=?,last_tick=?
WHERE singleton=1 AND owner_nonce=? AND fence_epoch=?
AND expires_at_tick>? AND last_tick<=? AND ?>expires_at_tick"""
# This fenced state write only RESERVES an upload attempt locally. It neither
# calls YouTube nor fences an HTTP request after the DB statement commits.
RESERVE_UPLOAD_SQL = """UPDATE fm_releases_shadow
SET stage='upload_started',updated_at=?
WHERE release_date=? AND episode_id=? AND media_sha256=?
AND stage='media_qa_passed'
AND EXISTS (
 SELECT 1 FROM fm_release_lease_shadow
 WHERE singleton=1 AND owner_nonce=? AND fence_epoch=?
 AND expires_at_tick>? AND last_tick<=?
)"""

NONCE=re.compile(r"[A-Za-z0-9_-]{32,64}\Z")
SHA=re.compile(r"[a-f0-9]{64}\Z")
IDENTITY=re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
MAX_TICK=10**12
MAX_FENCE=2**62


def _valid_fence(nonce:str,epoch:int,tick:int,ttl:int|None=None)->None:
    if not isinstance(nonce,str) or NONCE.fullmatch(nonce) is None:
        raise WorkflowError("Shadow D1 nonce does not meet fenced token shape")
    if type(epoch) is not int or not 0<=epoch<MAX_FENCE:
        raise WorkflowError("Shadow D1 CAS epoch is malformed")
    if type(tick) is not int or not 0<=tick<=MAX_TICK:
        raise WorkflowError("Shadow D1 CAS clock tick is malformed")
    if ttl is not None and (
        type(ttl) is not int or not 1<=ttl<=3600 or tick+ttl>MAX_TICK
    ):
        raise WorkflowError("Shadow D1 bounded lease duration is invalid")


def _write_one(conn:sqlite3.Connection,statement:str,parameters:tuple)->bool:
    try:
        # In SQLite autocommit mode, each UPDATE is an atomic statement.
        # In production D1, require .run().success True AND meta.changes==1.
        cursor=conn.execute(statement,parameters)
        changed=cursor.rowcount
        if changed not in (0,1):
            raise WorkflowError("Shadow D1 CAS modified an unexpected row count")
        return changed==1
    except sqlite3.Error:
        raise WorkflowError("Shadow D1 CAS statement failed closed") from None


def claim_shadow_d1_lease(
    conn:sqlite3.Connection,*,nonce:str,expected_epoch:int,
    now_tick:int,ttl_seconds:int,
)->int:
    _valid_fence(nonce,expected_epoch,now_tick,ttl_seconds)
    if not _write_one(conn,CLAIM_SQL,(
        nonce,now_tick+ttl_seconds,now_tick,expected_epoch,now_tick,now_tick,
    )):
        raise WorkflowError("Conditional D1-shaped lease claim refused")
    return expected_epoch+1


def renew_shadow_d1_lease(
    conn:sqlite3.Connection,*,nonce:str,epoch:int,
    now_tick:int,ttl_seconds:int,
)->None:
    _valid_fence(nonce,epoch,now_tick,ttl_seconds)
    if epoch==0 or not _write_one(conn,RENEW_SQL,(
        now_tick+ttl_seconds,now_tick,nonce,epoch,
        now_tick,now_tick,now_tick+ttl_seconds,
    )):
        raise WorkflowError("Expired/stale/unowned D1-shaped lease renewal denied")


def reserve_shadow_upload_once(
    conn:sqlite3.Connection,*,nonce:str,epoch:int,now_tick:int,
    release_date:str,episode_id:str,media_sha256:str,
)->None:
    _valid_fence(nonce,epoch,now_tick)
    if (epoch==0 or not isinstance(release_date,str)
            or len(release_date)!=10
            or not isinstance(episode_id,str)
            or IDENTITY.fullmatch(episode_id) is None
            or not isinstance(media_sha256,str)
            or SHA.fullmatch(media_sha256) is None):
        raise WorkflowError("Shadow reserve release identity invalid")
    if not _write_one(conn,RESERVE_UPLOAD_SQL,(
        "shadow-synthetic-event",release_date,episode_id,media_sha256,
        nonce,epoch,now_tick,now_tick,
    )):
        raise WorkflowError("Shadow upload reservation rejected; never auto-retry")


def open_disposable_d1_cas_model()->tuple[sqlite3.Connection,sqlite3.Connection]:
    """Two actual SQLite connections, ONE purely RAM-backed database."""
    name="file:flowminute-d1-cas-"+uuid.uuid4().hex+"?mode=memory&cache=shared"
    a=sqlite3.connect(name,uri=True,isolation_level=None,timeout=0.0)
    try:
        b=sqlite3.connect(name,uri=True,isolation_level=None,timeout=0.0)
        a.execute(LEASE_SCHEMA)
        a.execute(LEASE_INITIAL)
        a.execute(RELEASE_SCHEMA)
        a.execute(
            "INSERT INTO fm_releases_shadow VALUES (?,?,?,?,?,?)",
            ("2026-10-20","tutorial_short_en","a"*64,
             "media_qa_passed","synthetic-before-upload",None)
        )
        return a,b
    except BaseException:
        a.close()
        if "b" in locals():
            b.close()
        raise


def rehearse_d1_conditional_lease_and_upload_reservation()->dict:
    """No real upload and no production SQL/database calls."""
    a,b=open_disposable_d1_cas_model()
    try:
        first_epoch=claim_shadow_d1_lease(
            a,nonce="A"*32,expected_epoch=0,now_tick=100,ttl_seconds=10,
        )
        rival_blocked=False
        try:
            claim_shadow_d1_lease(
                b,nonce="B"*32,expected_epoch=0,now_tick=101,ttl_seconds=10,
            )
        except WorkflowError:
            rival_blocked=True
        if not rival_blocked:
            raise WorkflowError("D1-shaped overlap was not fenced")
        renew_shadow_d1_lease(
            a,nonce="A"*32,epoch=first_epoch,now_tick=105,ttl_seconds=10,
        )
        second_epoch=claim_shadow_d1_lease(
            b,nonce="B"*32,expected_epoch=first_epoch,
            now_tick=116,ttl_seconds=10,
        )
        stale_blocked=False
        try:
            reserve_shadow_upload_once(
                a,nonce="A"*32,epoch=first_epoch,now_tick=117,
                release_date="2026-10-20",episode_id="tutorial_short_en",
                media_sha256="a"*64,
            )
        except WorkflowError:
            stale_blocked=True
        if not stale_blocked:
            raise WorkflowError("Stale D1-shaped writer reserved an upload")
        reserve_shadow_upload_once(
            b,nonce="B"*32,epoch=second_epoch,now_tick=117,
            release_date="2026-10-20",episode_id="tutorial_short_en",
            media_sha256="a"*64,
        )
        second_attempt_blocked=False
        try:
            reserve_shadow_upload_once(
                b,nonce="B"*32,epoch=second_epoch,now_tick=118,
                release_date="2026-10-20",episode_id="tutorial_short_en",
                media_sha256="a"*64,
            )
        except WorkflowError:
            second_attempt_blocked=True
        if not second_attempt_blocked:
            raise WorkflowError("Duplicate shadow upload reserve was accepted")
        if a.execute(
            "SELECT stage FROM fm_releases_shadow WHERE episode_id=?",
            ("tutorial_short_en",),
        ).fetchone()!=("upload_started",):
            raise WorkflowError("Shadow CAS release state was not reserved")
        return {
            "status":"D1_CONDITIONAL_SQL_SQLITE_SHADOW_ONLY",
            "simulated_distinct_sqlite_connections":2,
            "single_statement_claim_conflict_rejected":rival_blocked,
            "monotonic_epoch_takeover_rehearsed":second_epoch>first_epoch,
            "same_owner_live_lease_renewal_rehearsed":True,
            "stale_epoch_release_reservation_rejected":stale_blocked,
            "duplicate_upload_reservation_rejected":second_attempt_blocked,
            "shadow_final_release_state":"upload_started",
            "real_d1_schema_migrated":False,
            "real_d1_statement_execution_verified":False,
            "real_cloud_consistency_or_clock_proven":False,
            "durable_exclusive_cloud_publisher_verified":False,
            "actual_youtube_upload_attempted":False,
            "external_http_side_effect_fenced":False,
            "lost_youtube_ack_safe_to_retry":False,
            "publishing_authorized":False,
            "cloud_database_writes":0,
            "external_api_requests":0,
            "recurring_infrastructure_inr":0,
        }
    finally:
        a.close()
        b.close()
