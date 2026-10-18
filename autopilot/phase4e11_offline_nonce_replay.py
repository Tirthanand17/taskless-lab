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
# SQLite removes IF NOT EXISTS in sqlite_master's stored CREATE statement.
# Requiring the exact fixture SQL also rejects a preexisting weakened
# lookalike table. This check is for synthetic CI state, NOT provider D1.
_STORED_SCHEMA = _CREATE.replace(" IF NOT EXISTS", "", 1)


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


def _require_fixture_schema(conn: sqlite3.Connection) -> None:
    """Refuse weakened tables, schema drift and INSERT/DELETE trigger bypasses.

    Called on setup AND inside each replay transaction so a table that was
    modified after initialization cannot turn a successful report into a
    non-persisted nonce reservation.
    """
    schema = conn.execute(
        "SELECT type, sql FROM sqlite_master WHERE name = ?", (_TABLE,)
    ).fetchone()
    columns = conn.execute("PRAGMA table_info(" + _TABLE + ")").fetchall()
    triggers = conn.execute(
        "SELECT count(*) FROM sqlite_master "
        "WHERE type='trigger' AND tbl_name = ?", (_TABLE,)
    ).fetchone()[0]
    if (schema is None or schema[0] != "table"
            or schema[1] != _STORED_SCHEMA
            or len(columns) != 1
            or columns[0][1:6] != ("nonce_sha256", "TEXT", 1, None, 1)
            or triggers != 0):
        raise ObservationBlocked("Offline nonce fixture schema or triggers invalid")


def initialize_offline_nonce_fixture(conn: sqlite3.Connection) -> None:
    """Explicit setup; only creates an ephemeral in-memory fixture table."""
    _memory_connection(conn)
    if conn.in_transaction:
        raise ObservationBlocked("Offline nonce fixture requires no active transaction")
    try:
        conn.execute(_CREATE)
        _require_fixture_schema(conn)
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
        _require_fixture_schema(conn)
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
        inserted = conn.execute(
            "INSERT INTO " + _TABLE + " (nonce_sha256) VALUES (?)", (digest,)
        )
        # SQLite RAISE(IGNORE) or a delete-after-insert trigger must NEVER
        # produce a successful verification without retaining the nonce.
        present = conn.execute(
            "SELECT 1 FROM " + _TABLE + " WHERE nonce_sha256 = ?", (digest,)
        ).fetchone()
        new_count = conn.execute("SELECT count(*) FROM " + _TABLE).fetchone()[0]
        if inserted.rowcount != 1 or present is None or new_count != number + 1:
            raise ObservationBlocked("Offline nonce reservation not persisted")
        conn.commit()
        # Preserve the exact underlying validation report shape.
        return report
    except sqlite3.Error:
        try:
            if conn.in_transaction:
                conn.rollback()
        except sqlite3.Error:
            pass
        # Neither SQLite lock states nor attacker-defined trigger errors can
        # reveal SQL text, raw fixture metadata or invented secret markers.
        raise ObservationBlocked("Offline nonce fixture transaction unavailable") from None
    except BaseException:
        if conn.in_transaction:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        raise
