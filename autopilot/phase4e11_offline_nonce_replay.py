"""Phase 4E.11 — OFFLINE, MEMORY-ONLY signed receipt nonce-use rehearsal.

This is a deterministic simulator around the existing Phase 4E.2 validator,
NOT a production nonce store, trusted signing service, provider connector or
release authority. The SQLite database MUST be memory-only and is lost on
connection shutdown. Never pass a real production database or provider data.
"""
from __future__ import annotations

from hashlib import sha256
import sqlite3

from .phase4d_signed_observations import IDENTITY, ObservationBlocked
from .phase4e2_signed_snapshot_bridge import inspect_signed_sanitized_phase4e_snapshots

_TABLE = "phase4e11_offline_seen_nonce_hashes"
_CAP = 256
_CREATE = (
    "CREATE TABLE IF NOT EXISTS " + _TABLE
    + " (nonce_sha256 TEXT PRIMARY KEY NOT NULL "
    + "CHECK(length(nonce_sha256) = 64)) WITHOUT ROWID"
)
_PURPOSE = b"FlowMinute/4E11/offline-nonce-rehearsal/v1\x00"


def _memory_connection(conn: sqlite3.Connection) -> None:
    """Deny file-backed or attached SQLite DBs: synthetic evidence only."""
    if type(conn) is not sqlite3.Connection:
        raise ObservationBlocked("Offline nonce fixture requires a SQLite connection")
    try:
        databases = conn.execute("PRAGMA database_list").fetchall()
    except sqlite3.Error:
        raise ObservationBlocked("Offline nonce fixture cannot inspect storage") from None
    if (len(databases) != 1 or databases[0][1] != "main"
            or databases[0][2] != ""):
        raise ObservationBlocked("Offline nonce fixture requires memory-only storage")


def initialize_offline_nonce_fixture(conn: sqlite3.Connection) -> None:
    """Explicit setup; only creates an ephemeral in-memory fixture table."""
    _memory_connection(conn)
    if conn.in_transaction:
        raise ObservationBlocked("Offline nonce fixture requires no active transaction")
    try:
        conn.execute(_CREATE)
        schema = conn.execute(
            "SELECT type, sql FROM sqlite_master WHERE name = ?", (_TABLE,)
        ).fetchone()
        columns = conn.execute("PRAGMA table_info(" + _TABLE + ")").fetchall()
        # A preexisting caller-shaped table is not acceptable. This is a
        # testing invariant, not an authenticated production schema audit.
        if (schema is None or schema[0] != "table" or len(columns) != 1
                or columns[0][1] != "nonce_sha256"
                or columns[0][5] != 1
                or "WITHOUT ROWID" not in schema[1].upper()):
            raise ObservationBlocked("Offline nonce fixture schema invalid")
    except sqlite3.Error:
        raise ObservationBlocked("Offline nonce fixture initialization denied") from None


def verify_and_reserve_once_offline(
    *, conn: sqlite3.Connection, d1_snapshot: dict, youtube_snapshot: dict,
    signed_observations, trusted_registry, request_nonce: str, now,
) -> dict:
    """Atomically verify signed *claims* and record a one-use nonce digest.

    Only for a single in-memory SQLite fixture session. Caller-supplied now,
    trust roots, source data and signatures do not prove real API access.
    No D1/Google API, file access, migration, scheduling or upload.
    """
    _memory_connection(conn)
    if conn.in_transaction:
        raise ObservationBlocked("Offline verifier requires no active transaction")
    if not isinstance(request_nonce, str) or not IDENTITY.fullmatch(request_nonce):
        raise ObservationBlocked("Malformed offline nonce")
    digest = sha256(_PURPOSE + request_nonce.encode("ascii")).hexdigest()
    try:
        # Claim uniqueness check + cryptographic validation + reservation
        # happen under the SAME SQLite write transaction. Failed validation
        # rolls back and does not consume the nonce.
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT 1 FROM " + _TABLE + " WHERE nonce_sha256 = ?", (digest,)
        ).fetchone()
        if row is not None:
            raise ObservationBlocked("Previously used offline nonce")
        number = conn.execute("SELECT count(*) FROM " + _TABLE).fetchone()[0]
        if number >= _CAP:
            raise ObservationBlocked("Bounded offline nonce fixture capacity reached")
        report = inspect_signed_sanitized_phase4e_snapshots(
            d1_snapshot=d1_snapshot,
            youtube_snapshot=youtube_snapshot,
            signed_observations=signed_observations,
            trusted_registry=trusted_registry,
            request_nonce=request_nonce,
            already_seen_nonces=frozenset(),
            now=now,
        )
        if (report.get("signed_integrity_for_exact_sanitized_snapshot_bytes") is not True
                or report.get("live_authenticated_d1_access_verified") is not False
                or report.get("live_authenticated_youtube_channel_owner_verified") is not False
                or report.get("migration_authorized") is not False
                or report.get("private_upload_or_scheduling_authorized") is not False
                or report.get("public_publishing_authorized") is not False):
            raise ObservationBlocked("Untrusted report claimed release authority")
        conn.execute(
            "INSERT INTO " + _TABLE + " (nonce_sha256) VALUES (?)", (digest,)
        )
        conn.commit()
        # Preserve the exact underlying validation report shape.
        return report
    except BaseException:
        if conn.in_transaction:
            conn.rollback()
        raise
