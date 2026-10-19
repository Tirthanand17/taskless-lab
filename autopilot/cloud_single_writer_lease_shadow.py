"""Phase 4H: NON-PRODUCTION, purely in-memory SQLite lease fencing model.

Two SQLite connections share one disposable *named in-memory* database. The
rehearsal demonstrates that only the current owner/fencing epoch may proceed
inside this miniature local model. It does NOT deploy a distributed lock,
Cloudflare D1 transaction, durable lease, exclusive cloud writer, real publish
transaction or a solution to exactly-once YouTube uploads.

No persistent files, network, D1/YouTube calls or background schedule.
"""
from __future__ import annotations

import sqlite3
import uuid

from .agent_org import WorkflowError

_CREATE="""CREATE TABLE shadow_lease (
 id INTEGER PRIMARY KEY CHECK(id=1),
 owner TEXT NOT NULL, fence INTEGER NOT NULL,
 expires_tick INTEGER NOT NULL
)"""
_INITIAL="INSERT INTO shadow_lease(id,owner,fence,expires_tick) VALUES (1,'',0,0)"
_SELECT="SELECT owner,fence,expires_tick FROM shadow_lease WHERE id=1"


def _clock(tick:int,ttl:int|None=None)->None:
    if type(tick) is not int or not 0<=tick<=10**12:
        raise WorkflowError("Shadow logical clock invalid")
    if ttl is not None and (
            type(ttl) is not int or not 1<=ttl<=3600
            or tick+ttl>10**12):
        raise WorkflowError("Bounded shadow lease duration invalid")


def _owner(name:str)->None:
    if name not in ("shadow_writer_one","shadow_writer_two"):
        raise WorkflowError("Unknown shadow lease owner")


def _claim(conn:sqlite3.Connection,owner:str,now:int,ttl:int)->int:
    """Serialized CAS-like state change in disposable SQLite only."""
    _owner(owner)
    _clock(now,ttl)
    try:
        conn.execute("BEGIN IMMEDIATE")
        current=conn.execute(_SELECT).fetchone()
        if current is None:
            raise WorkflowError("Missing shadow lease state")
        current_owner,epoch,expiry=current
        if current_owner and expiry>now:
            raise WorkflowError("Conflicting shadow writer already holds lease")
        epoch+=1
        if epoch>2**62:
            raise WorkflowError("Shadow fence epoch overflow")
        conn.execute(
            "UPDATE shadow_lease SET owner=?,fence=?,expires_tick=? WHERE id=1",
            (owner,epoch,now+ttl),
        )
        conn.execute("COMMIT")
        return epoch
    except BaseException as ex:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        if isinstance(ex,sqlite3.Error):
            raise WorkflowError("Shadow lease database operation denied") from None
        raise


def _fence(conn:sqlite3.Connection,owner:str,epoch:int,now:int)->None:
    """Check owner, strictly increasing epoch and expiration in transaction."""
    _owner(owner)
    _clock(now)
    if type(epoch) is not int or epoch<=0:
        raise WorkflowError("Shadow writer requires positive fence epoch")
    try:
        conn.execute("BEGIN IMMEDIATE")
        current=conn.execute(_SELECT).fetchone()
        if current is None or current!=(owner,epoch,current[2]) or current[2]<=now:
            raise WorkflowError("Shadow writer lost lease, stale epoch denied")
        conn.execute("COMMIT")
    except BaseException as ex:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        if isinstance(ex,sqlite3.Error):
            raise WorkflowError("Shadow fence check database failure") from None
        raise


def _open_pair()->tuple[sqlite3.Connection,sqlite3.Connection]:
    # Explicit mode=memory means no database file, even though the two local
    # sqlite connections share the same ephemeral cache by name.
    uri="file:fm-lease-"+uuid.uuid4().hex+"?mode=memory&cache=shared"
    first=sqlite3.connect(uri,uri=True,isolation_level=None,timeout=0.0)
    try:
        second=sqlite3.connect(uri,uri=True,isolation_level=None,timeout=0.0)
        first.execute(_CREATE)
        first.execute(_INITIAL)
        return first,second
    except BaseException:
        first.close()
        if "second" in locals():
            second.close()
        raise


def rehearse_in_memory_writer_fencing()->dict:
    """Demonstrate conflict refusal and stale-owner fencing after takeover."""
    first,second=_open_pair()
    try:
        epoch_one=_claim(first,"shadow_writer_one",100,10)
        first_writer_live=True
        _fence(first,"shadow_writer_one",epoch_one,105)
        rejected_overlap=False
        try:
            _claim(second,"shadow_writer_two",105,10)
        except WorkflowError:
            rejected_overlap=True
        if not rejected_overlap:
            raise WorkflowError("Shadow overlapping writer was not rejected")

        epoch_two=_claim(second,"shadow_writer_two",111,10)
        if epoch_two<=epoch_one:
            raise WorkflowError("Shadow epoch did not monotonically increase")
        stale_fenced=False
        try:
            _fence(first,"shadow_writer_one",epoch_one,112)
        except WorkflowError:
            stale_fenced=True
        if not stale_fenced:
            raise WorkflowError("Shadow old epoch was accepted after takeover")
        _fence(second,"shadow_writer_two",epoch_two,112)
        expired_fenced=False
        try:
            _fence(second,"shadow_writer_two",epoch_two,121)
        except WorkflowError:
            expired_fenced=True
        if not expired_fenced:
            raise WorkflowError("Expired shadow owner was not fenced")
        return {
            "status":"SQLITE_MEMORY_LEASE_FENCING_SIMULATION_ONLY",
            "different_sqlite_connections":2,
            "synthetic_writer_conflict_denied":rejected_overlap,
            "synthetic_epoch_takeover_monotonic":epoch_two>epoch_one,
            "synthetic_stale_worker_fenced":stale_fenced,
            "synthetic_expired_worker_fenced":expired_fenced,
            "local_shadow_write_performed":True,
            "real_D1_writer_or_lease_deployed":False,
            "real_cloud_lease_atomicity_verified":False,
            "network_partition_or_clock_skew_safety_proven":False,
            "external_publisher_fencing_integrated":False,
            "cloud_backup_restore_verified":False,
            "upload_retry_authorized":False,
            "youtube_upload_or_publish_authorized":False,
            "cloud_database_writes":0,
            "external_api_requests":0,
            "recurring_infrastructure_inr":0,
        }
    finally:
        first.close()
        second.close()
