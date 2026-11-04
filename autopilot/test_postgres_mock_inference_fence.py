"""Actual GitHub-hosted PostgreSQL service tests; no external Gemini or private DB.

Without FLOWMINUTE_TEST_PG_DSN this suite is skipped by the repository-wide
quality gate. The dedicated GitHub-hosted service job MUST set that env var,
run this suite, and verify NO skipped tests.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest

from autopilot.atomic_mock_inference_fence import (
    ACCEPTED, REJECTED, RESERVED, InferenceFenceError,
)
from autopilot.postgres_mock_inference_fence import (
    CI_DB, CI_DB_USER, PostgresMockInferenceFence, PgReservation, STATUS,
    evaluate_synthetic_pg_mock,
)
from autopilot.test_owner_provider_lease_gate import NOW, EXCLUDED, make, resign
from autopilot.test_atomic_mock_inference_fence import kwargs_for
from autopilot.test_script_draft_agent import short_proposal
from autopilot.owner_provider_lease_gate import ModelLeaseError

TEST_ENV = "FLOWMINUTE_TEST_PG_DSN"


def _connect():
    import psycopg
    return psycopg.connect(os.environ[TEST_ENV], connect_timeout=5)


def _worker_reserve(index: int) -> str:
    """Separate Python process and independent DB connection, not a fake lock."""
    try:
        fence = PostgresMockInferenceFence(_connect)
        obj = make(index)
        fence.reserve_synthetic_owner_lease(**kwargs_for(obj))
        return "BURNED"
    except InferenceFenceError:
        return "BLOCKED"


@unittest.skipUnless(os.environ.get(TEST_ENV), "Requires dedicated ephemeral Postgres Actions service")
class PostgreSQLSignedInferenceFenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute("SELECT current_database(), current_user")
                if tuple(cur.fetchone()) != (CI_DB,CI_DB_USER):
                    raise AssertionError("Refusing non-fixture PostgreSQL database/user")
                script = (
                    Path(__file__).parent / "sql" /
                    "001_postgres_ci_inference_fence.sql"
                ).read_text(encoding="utf-8")
                for command in script.split(";"):
                    if command.strip():
                        cur.execute(command)
        cls.fence = PostgresMockInferenceFence(_connect)

    def setUp(self):
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute(
                    "TRUNCATE fm_owner_inference_burns, fm_owner_inference_days"
                )

    def test_one_durable_burn_and_reopen_from_different_client(self):
        item=make()
        reserved=self.fence.reserve_synthetic_owner_lease(**kwargs_for(item))
        self.assertEqual(self.fence.inspect(reserved.lease_id)["status"],RESERVED)
        reopened=PostgresMockInferenceFence(_connect)
        self.assertEqual(reopened.inspect(reserved.lease_id)["status"],RESERVED)
        self.assertFalse(reopened.inspect(reserved.lease_id)["safe_to_retry"])
        with self.assertRaises(InferenceFenceError):
            reopened.reserve_synthetic_owner_lease(**kwargs_for(item))

    def test_many_independent_processes_can_only_burn_one_request(self):
        with ProcessPoolExecutor(max_workers=8) as pool:
            result=list(pool.map(_worker_reserve,[0]*20))
        self.assertEqual(result.count("BURNED"),1, result)
        self.assertEqual(result.count("BLOCKED"),19, result)
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM fm_owner_inference_burns")
                self.assertEqual(cur.fetchone()[0],1)
                cur.execute("SELECT burned_count FROM fm_owner_inference_days")
                self.assertEqual(cur.fetchone()[0],1)

    def test_simultaneous_three_slots_lock_day_guard(self):
        with ProcessPoolExecutor(max_workers=6) as pool:
            result=list(pool.map(_worker_reserve, [0,1,2,0,1,2]*4))
        self.assertEqual(result.count("BURNED"),3,result)
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute("SELECT burned_count FROM fm_owner_inference_days")
                self.assertEqual(cur.fetchone()[0],3)
                cur.execute("SELECT COUNT(DISTINCT episode_id) FROM fm_owner_inference_burns")
                self.assertEqual(cur.fetchone()[0],3)

    def test_same_episode_other_valid_lease_never_reopens(self):
        obj=make(0)
        self.fence.reserve_synthetic_owner_lease(**kwargs_for(obj))
        second=make(0)
        resign(second,lease_id="another_lease_same_episode")
        with self.assertRaises(InferenceFenceError):
            self.fence.reserve_synthetic_owner_lease(**kwargs_for(second))

    def test_same_lease_id_other_episode_blocked(self):
        first=make(0)
        self.fence.reserve_synthetic_owner_lease(**kwargs_for(first))
        other=make(1)
        resign(other,lease_id=first["terms"].lease_id)
        with self.assertRaises(InferenceFenceError):
            self.fence.reserve_synthetic_owner_lease(**kwargs_for(other))

    def test_changed_project_or_owner_scope_rejected(self):
        self.fence.reserve_synthetic_owner_lease(**kwargs_for(make(0)))
        alternate=make(1)
        resign(alternate,free_tier_billing_project_fingerprint_sha256="f"*64)
        with self.assertRaises(InferenceFenceError):
            self.fence.reserve_synthetic_owner_lease(**kwargs_for(alternate))
        alternate=make(2)
        owner=alternate["registry"]["enrolled_owner"]
        alternate["registry"]={"different_owner":replace(owner,owner_id="different_owner")}
        resign(alternate,owner_id="different_owner")
        with self.assertRaises(InferenceFenceError):
            self.fence.reserve_synthetic_owner_lease(**kwargs_for(alternate))
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute("SELECT burned_count FROM fm_owner_inference_days")
                self.assertEqual(cur.fetchone()[0],1)

    def test_crash_or_uncertain_db_response_stays_permanently_burned(self):
        item=make()
        self.fence.reserve_synthetic_owner_lease(**kwargs_for(item))
        # No close call; process may disappear after sending mock request.
        second=PostgresMockInferenceFence(_connect)
        state=second.inspect(item["terms"].lease_id)
        self.assertEqual(state["status"],RESERVED)
        self.assertFalse(state["safe_to_retry"])
        with self.assertRaises(InferenceFenceError):
            second.reserve_synthetic_owner_lease(**kwargs_for(item))

    def test_stale_or_tampered_owner_signature_blocks_before_transaction(self):
        item=make()
        item["observations"]["sources"][0]["title"]+=" evil changed headline"
        with self.assertRaises(ModelLeaseError):
            self.fence.reserve_synthetic_owner_lease(**kwargs_for(item))
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM fm_owner_inference_burns")
                self.assertEqual(cur.fetchone()[0],0)

    def test_wrong_fence_token_cannot_close_and_real_one_is_single_use(self):
        item=make()
        ticket=self.fence.reserve_synthetic_owner_lease(**kwargs_for(item))
        forged=replace(ticket, token="f"*64)
        with self.assertRaises(InferenceFenceError):
            self.fence.close_mock(
                forged,mock_response_sha256="a"*64,structurally_valid=True,now=NOW
            )
        state=self.fence.inspect(ticket.lease_id)
        self.assertEqual(state["status"],RESERVED)
        closed=self.fence.close_mock(
            ticket,mock_response_sha256="a"*64,structurally_valid=True,now=NOW
        )
        self.assertEqual(closed["status"],ACCEPTED)
        self.assertFalse(closed["live_provider_call_made"])
        with self.assertRaises(InferenceFenceError):
            self.fence.close_mock(
                ticket,mock_response_sha256="a"*64,structurally_valid=True,now=NOW
            )

    def test_parallel_mock_completion_only_one_worker_wins(self):
        obj=make()
        ticket=self.fence.reserve_synthetic_owner_lease(**kwargs_for(obj))
        def attempt(_):
            try:
                return self.fence.close_mock(
                    ticket,mock_response_sha256="b"*64,
                    structurally_valid=True,now=NOW,
                )["status"]
            except InferenceFenceError:
                return "BLOCKED"
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses=list(pool.map(attempt,range(12)))
        self.assertEqual(responses.count(ACCEPTED),1,responses)
        self.assertEqual(responses.count("BLOCKED"),11,responses)

    def test_mock_structural_success_is_not_real_approved_script(self):
        obj=make(0)
        result=evaluate_synthetic_pg_mock(
            self.fence,**kwargs_for(obj),raw_proposal=short_proposal(),
        )
        self.assertEqual(result["status"],STATUS)
        self.assertEqual(result["receipt"]["status"],ACCEPTED)
        self.assertFalse(result["live_provider_request_sent"])
        self.assertFalse(result["external_claim_fact_checked"])
        self.assertFalse(result["private_spend_cap_enforced"])
        self.assertFalse(result["release_authorized"])

    def test_mock_incomplete_script_still_burns_request(self):
        obj=make(0)
        raw=dict(short_proposal())
        raw["narration"]="Not enough words."
        with self.assertRaises(InferenceFenceError):
            evaluate_synthetic_pg_mock(
                self.fence,**kwargs_for(obj),raw_proposal=raw,
            )
        state=self.fence.inspect(obj["terms"].lease_id)
        self.assertEqual(state["status"],REJECTED)
        self.assertFalse(state["safe_to_retry"])

    def test_tampered_scope_after_owner_signature_has_no_burn(self):
        item=make(0)
        item["anchor"]="a"*64
        with self.assertRaises(ModelLeaseError):
            self.fence.reserve_synthetic_owner_lease(**kwargs_for(item))
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM fm_owner_inference_burns")
                self.assertEqual(cur.fetchone()[0],0)

    def test_no_plain_api_key_or_full_script_or_token_in_db_rows(self):
        obj=make(0)
        ticket=self.fence.reserve_synthetic_owner_lease(**kwargs_for(obj))
        with _connect() as db:
            with db.cursor() as cur:
                cur.execute(
                    "SELECT lease_id, episode_id, context_sha256, token_sha256 "
                    "FROM fm_owner_inference_burns"
                )
                body=json.dumps(cur.fetchall())
                self.assertNotIn(ticket.token,body)
                self.assertNotIn("x-goog-api-key",body)
                self.assertNotIn("One setting can change",body)
                self.assertNotIn("source_url",body)

    def test_owner_billing_validation_and_private_vault_are_still_missing(self):
        obj=make(0)
        ticket=self.fence.reserve_synthetic_owner_lease(**kwargs_for(obj))
        result=self.fence.inspect(ticket.lease_id)
        self.assertFalse(result["production_ledger_deployed"])
        self.assertFalse(result["owner_real_consent_verified"])
        self.assertFalse(result["provider_inference_performed"])
        self.assertFalse(result["youtube_upload_enabled"])
        self.assertFalse(result["release_authorized"])

    def test_invalid_conn_factory_cannot_connect_to_arbitrary_database(self):
        def wrong():
            class Cursor:
                def __enter__(self): return self
                def __exit__(self,*_): return False
                def execute(self,*_): pass
                def fetchone(self): return ("customer_prod","owner_admin")
            class Fake:
                def __enter__(self): return self
                def __exit__(self,*_): return False
                def cursor(self): return Cursor()
            return Fake()
        with self.assertRaises(InferenceFenceError):
            PostgresMockInferenceFence(wrong)


if __name__=="__main__":
    unittest.main()
