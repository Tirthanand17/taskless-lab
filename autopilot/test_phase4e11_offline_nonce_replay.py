"""Phase 4E.11 in-memory replay rehearsal; fake Ed25519 keys, no APIs."""
import sqlite3
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import base64
import unittest

import autopilot.test_phase4e2_signed_snapshot_bridge as fixtures
from autopilot.phase4d_signed_observations import (
    ObservationBlocked, SignedObservation, _canonical,
)
from autopilot.phase4e11_offline_nonce_replay import (
    initialize_offline_nonce_fixture, verify_and_reserve_once_offline,
)

TABLE = "phase4e11_offline_seen_nonce_hashes"


class OfflineOneUseNonceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.OfflineSignedSnapshotBridgeTests(
            "test_exact_bounded_verified_signatures_do_not_prove_remote_access"
        )
        self.fixture.setUp()
        self.conn = sqlite3.connect(":memory:", isolation_level=None)
        initialize_offline_nonce_fixture(self.conn)

    def tearDown(self):
        self.conn.close()

    def args(self, conn=None, nonce=fixtures.NONCE, signed=None):
        return {
            "conn": self.conn if conn is None else conn,
            "d1_snapshot": self.fixture.d1,
            "youtube_snapshot": self.fixture.youtube,
            "signed_observations": (
                self.fixture.signed if signed is None else signed
            ),
            "trusted_registry": self.fixture.registry,
            "request_nonce": nonce,
            "now": fixtures.NOW,
        }

    def count(self, conn=None):
        c = self.conn if conn is None else conn
        return c.execute("SELECT count(*) FROM " + TABLE).fetchone()[0]

    def signed_with_nonce(self, nonce):
        records = []
        for old in self.fixture.signed:
            claim = replace(old.claim, request_nonce=nonce)
            key = self.fixture.keys[claim.kind]
            records.append(SignedObservation(
                claim, base64.b64encode(key.sign(_canonical(claim))).decode()
            ))
        return records

    def test_atomic_first_use_then_replay_denial(self):
        result = verify_and_reserve_once_offline(**self.args())
        self.assertEqual(self.count(), 1)
        self.assertTrue(result["signed_integrity_for_exact_sanitized_snapshot_bytes"])
        self.assertFalse(result["live_authenticated_d1_access_verified"])
        self.assertFalse(result["migration_authorized"])
        self.assertFalse(result["public_publishing_authorized"])
        with self.assertRaises(ObservationBlocked):
            verify_and_reserve_once_offline(**self.args())
        self.assertEqual(self.count(), 1)

    def test_bad_signature_does_not_consume_nonce(self):
        bad = list(self.fixture.signed)
        bad[0] = replace(bad[0], signature_b64=base64.b64encode(b"0"*64).decode())
        with self.assertRaises(ObservationBlocked):
            verify_and_reserve_once_offline(**self.args(signed=bad))
        self.assertEqual(self.count(), 0)
        verify_and_reserve_once_offline(**self.args())
        self.assertEqual(self.count(), 1)

    def test_bad_metadata_does_not_consume_nonce(self):
        args = self.args()
        args["youtube_snapshot"] = deepcopy(args["youtube_snapshot"])
        args["youtube_snapshot"]["oauth_secret"] = "DO_NOT_ECHO"
        with self.assertRaises(ObservationBlocked) as error:
            verify_and_reserve_once_offline(**args)
        self.assertNotIn("DO_NOT_ECHO", str(error.exception))
        self.assertEqual(self.count(), 0)
        verify_and_reserve_once_offline(**self.args())
        self.assertEqual(self.count(), 1)

    def test_distinct_signed_nonce_is_separately_usable(self):
        verify_and_reserve_once_offline(**self.args())
        nonce = "nonce_second_21"
        result = verify_and_reserve_once_offline(
            **self.args(nonce=nonce, signed=self.signed_with_nonce(nonce))
        )
        self.assertTrue(result["signed_integrity_for_exact_sanitized_snapshot_bytes"])
        self.assertEqual(self.count(), 2)
        with self.assertRaises(ObservationBlocked):
            verify_and_reserve_once_offline(
                **self.args(nonce=nonce, signed=self.signed_with_nonce(nonce))
            )
        self.assertEqual(self.count(), 2)

    def test_same_nonce_stays_denied_across_shared_memory_connections(self):
        uri = "file:flowminute_phase4e11_synthetic?mode=memory&cache=shared"
        first = sqlite3.connect(uri, uri=True, isolation_level=None)
        second = sqlite3.connect(uri, uri=True, isolation_level=None)
        try:
            initialize_offline_nonce_fixture(first)
            verify_and_reserve_once_offline(**self.args(conn=first))
            with self.assertRaises(ObservationBlocked):
                verify_and_reserve_once_offline(**self.args(conn=second))
            self.assertEqual(self.count(first), 1)
        finally:
            first.close()
            second.close()

    def test_open_transaction_and_attached_database_denied(self):
        self.conn.execute("BEGIN")
        with self.assertRaises(ObservationBlocked):
            verify_and_reserve_once_offline(**self.args())
        self.conn.rollback()
        self.conn.execute("ATTACH DATABASE ':memory:' AS extra")
        with self.assertRaises(ObservationBlocked):
            verify_and_reserve_once_offline(**self.args())
        with self.assertRaises(ObservationBlocked):
            initialize_offline_nonce_fixture(self.conn)
        self.conn.execute("DETACH DATABASE extra")
        self.assertEqual(self.count(), 0)

    def test_unknown_and_noncanonical_nonce_denied_without_secret_echo(self):
        for nonce in ("", "UPPER_CASE", "a", "unsafe;DROP", 42, None):
            with self.subTest(nonce_type=type(nonce).__name__):
                with self.assertRaises(ObservationBlocked) as error:
                    verify_and_reserve_once_offline(**self.args(nonce=nonce))
                self.assertNotIn("DROP",str(error.exception))
        self.assertEqual(self.count(), 0)

    def test_insert_trigger_failure_rolls_back_without_replay_consumption(self):
        self.conn.execute(
            "CREATE TRIGGER offline_rehearsal_fault BEFORE INSERT ON "
            + TABLE + " BEGIN SELECT RAISE(ABORT, 'fake failure'); END"
        )
        with self.assertRaises(sqlite3.Error):
            verify_and_reserve_once_offline(**self.args())
        self.assertEqual(self.count(), 0)
        self.conn.execute("DROP TRIGGER offline_rehearsal_fault")
        verify_and_reserve_once_offline(**self.args())
        self.assertEqual(self.count(), 1)

    def test_fixture_is_not_durable_across_connection_restart(self):
        verify_and_reserve_once_offline(**self.args())
        self.conn.close()
        self.conn = sqlite3.connect(":memory:", isolation_level=None)
        initialize_offline_nonce_fixture(self.conn)
        # Expected vulnerability of an ephemeral research fixture:
        # same receipt can be presented after memory reset.
        verify_and_reserve_once_offline(**self.args())
        self.assertEqual(self.count(), 1)

    def test_no_provider_origin_or_write_authority_from_fixture(self):
        result = verify_and_reserve_once_offline(**self.args())
        self.assertFalse(result["live_authenticated_youtube_channel_owner_verified"])
        self.assertFalse(result["production_ledger_writer_deployed"])
        self.assertFalse(result["migration_authorized"])
        self.assertFalse(result["private_upload_or_scheduling_authorized"])
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(result["database_writes"], 0)  # *provider* writes only
        self.assertNotIn(fixtures.VID, str(result))
        self.assertNotIn("releases", str(result))


if __name__ == "__main__":
    unittest.main()
