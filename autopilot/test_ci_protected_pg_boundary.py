"""Real Postgres 16 service privileges test; no real vault or owner/provider.

Requires dedicated FLOWMINUTE_B3D4C2B3A_ADMIN_DSN and synthetic role
passwords. Other repository CI skips these integration cases deliberately.
The dedicated workflow must run them and fail on ANY skip.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest

from autopilot.atomic_mock_inference_fence import (
    InferenceFenceError, RESERVED, ACCEPTED, REJECTED,
)
from autopilot.ci_protected_pg_boundary import (
    ProtectedMockGateway, LimitedMockLedgerObserver,
    MockCiTicket, GATEWAY_ROLE, WORKER_ROLE, AUDITOR_ROLE,
)
from autopilot.owner_provider_lease_gate import ModelLeaseError
from autopilot.test_atomic_mock_inference_fence import kwargs_for
from autopilot.test_owner_provider_lease_gate import NOW, make, resign

PREFIX = "FLOWMINUTE_B3D4C2B3A_"
ADMIN_DSN = PREFIX+"ADMIN_DSN"
TEST_PASSWORDS = {
    GATEWAY_ROLE: PREFIX+"GATEWAY_TEST_PASSWORD",
    WORKER_ROLE: PREFIX+"WORKER_TEST_PASSWORD",
    AUDITOR_ROLE: PREFIX+"AUDITOR_TEST_PASSWORD",
}


def connect_admin():
    import psycopg
    return psycopg.connect(os.environ[ADMIN_DSN],connect_timeout=4)


def _test_role_connection(role: str):
    import psycopg
    if role not in TEST_PASSWORDS:
        raise InferenceFenceError("CI roles only")
    return psycopg.connect(
        host="127.0.0.1",port=5432,dbname="flowminute_fence_ci",
        user=role,password=os.environ[TEST_PASSWORDS[role]],
        connect_timeout=4,
    )


def connect_gateway():
    return _test_role_connection(GATEWAY_ROLE)


def connect_worker():
    return _test_role_connection(WORKER_ROLE)


def connect_auditor():
    return _test_role_connection(AUDITOR_ROLE)


@unittest.skipUnless(os.environ.get(ADMIN_DSN), "Dedicated read-only hosted Postgres service required")
class PostgresLeastPrivilegeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import psycopg
        from psycopg import sql
        with psycopg.connect(os.environ[ADMIN_DSN],autocommit=True,connect_timeout=4) as admin:
            with admin.cursor() as cur:
                cur.execute("SELECT current_database(), current_user, usesuper "
                            "FROM pg_catalog.pg_user WHERE usename=current_user")
                row=cur.fetchone()
                if tuple(row)!=( "flowminute_fence_ci","flowminute_test",True):
                    raise AssertionError("CI migration refuses production or unprivileged DB")
                migration=(Path(__file__).parent/"sql"/"002_ci_least_privilege_ledger.sql").read_text(encoding="utf-8")
                cur.execute(migration)
                for role,env_var in TEST_PASSWORDS.items():
                    password=os.environ[env_var]
                    if not isinstance(password,str) or not 15<=len(password)<=90:
                        raise AssertionError("Invalid disposable CI role password")
                    cur.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                        sql.Identifier(role),sql.Literal(password),
                    ))
        cls.gateway=ProtectedMockGateway(connect_gateway)
        cls.worker=LimitedMockLedgerObserver(connect_worker,role=WORKER_ROLE)
        cls.auditor=LimitedMockLedgerObserver(connect_auditor,role=AUDITOR_ROLE)

    def setUp(self):
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute(
                    "TRUNCATE fm_private_ci.audit_events, fm_private_ci.burns, "
                    "fm_private_ci.day_ledger RESTART IDENTITY CASCADE"
                )

    def test_actual_role_flags_and_direct_table_denials(self):
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute("""
                    SELECT rolname,rolsuper,rolcreatedb,rolcreaterole,
                           rolbypassrls,rolinherit
                      FROM pg_catalog.pg_roles
                     WHERE rolname IN (
                         'fm_ci_gateway','fm_ci_worker','fm_ci_auditor','fm_ci_owner'
                     ) ORDER BY rolname
                """)
                rows=cur.fetchall()
                self.assertEqual(len(rows),4)
                for row in rows:
                    self.assertEqual(tuple(row[1:]),(False,False,False,False,False))
                for role in TEST_PASSWORDS:
                    for privilege in ("SELECT","INSERT","UPDATE","DELETE","TRUNCATE"):
                        cur.execute(
                            "SELECT has_table_privilege(%s,'fm_private_ci.burns',%s)",
                            (role,privilege),
                        )
                        self.assertFalse(cur.fetchone()[0],(role,privilege))
                    cur.execute(
                        "SELECT has_schema_privilege(%s,'fm_private_ci','CREATE')",
                        (role,),
                    )
                    self.assertFalse(cur.fetchone()[0],role)

    def test_separate_gateway_can_burn_but_worker_and_auditor_cannot(self):
        obj=make(0)
        ticket=self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        self.assertIsInstance(ticket,MockCiTicket)
        for connect in (connect_worker,connect_auditor):
            with self.subTest(role=connect.__name__), connect() as db:
                with db.cursor() as cur:
                    with self.assertRaises(Exception):
                        cur.execute(
                            "SELECT fm_private_ci.burn_mock_once("
                            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            ("a"*3,)*9+(NOW,),
                        )
        for observer in (self.worker,self.auditor):
            state=observer.inspect(ticket.lease_id)
            self.assertEqual(state["status"],RESERVED)
            self.assertEqual(state["audit_event_count"],1)
            self.assertFalse(state["contains_fence_secret"])
            self.assertFalse(state["provider_inference_performed"])
            self.assertFalse(state["release_authorized"])

    def test_worker_cannot_insert_delete_update_truncate_or_create(self):
        obj=make(0)
        ticket=self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        queries=[
            "INSERT INTO fm_private_ci.audit_events(lease_id,event_action,event_at) "
            "VALUES ('fake','BURN',now())",
            "DELETE FROM fm_private_ci.burns",
            "UPDATE fm_private_ci.burns SET status='MOCK_DRAFT_VALIDATED_NO_RELEASE'",
            "TRUNCATE fm_private_ci.burns",
            "CREATE TABLE fm_private_ci.secret_leak (credential TEXT)",
            "ALTER TABLE fm_private_ci.burns ADD COLUMN fake BOOL",
        ]
        for connect in (connect_worker,connect_auditor,connect_gateway):
            for query in queries:
                with self.subTest(role=connect.__name__,query=query):
                    with connect() as db:
                        with db.cursor() as cur:
                            with self.assertRaises(Exception):
                                cur.execute(query)
        self.assertEqual(self.auditor.inspect(ticket.lease_id)["status"],RESERVED)
        self.assertEqual(self.auditor.inspect(ticket.lease_id)["audit_event_count"],1)

    def test_nobody_can_assume_owner_role(self):
        for connect in (connect_worker,connect_gateway,connect_auditor):
            with self.subTest(role=connect.__name__):
                with connect() as db:
                    with db.cursor() as cur:
                        with self.assertRaises(Exception):
                            cur.execute("SET ROLE fm_ci_owner")

    def test_one_time_mock_close_is_recorded_without_audit_rewrite(self):
        obj=make(0)
        ticket=self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        receipt=self.gateway.close_mock(
            ticket,mock_output_sha256="d"*64,structurally_valid=True,now=NOW
        )
        self.assertEqual(receipt["status"],ACCEPTED)
        self.assertFalse(receipt["provider_call_enabled"])
        self.assertFalse(receipt["production_cloud_database_deployed"])
        observed=self.auditor.inspect(ticket.lease_id)
        self.assertEqual(observed["status"],ACCEPTED)
        self.assertEqual(observed["audit_event_count"],2)
        self.assertFalse(observed["admin_or_backup_tampering_excluded"])
        with self.assertRaises(InferenceFenceError):
            self.gateway.close_mock(
                ticket,mock_output_sha256="d"*64,structurally_valid=True,now=NOW
            )
        self.assertEqual(self.worker.inspect(ticket.lease_id)["audit_event_count"],2)

    def test_wrong_ephemeral_closure_token_cannot_close(self):
        obj=make(0)
        ticket=self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        forged=replace(ticket,ephemeral_fence_token="a"*64)
        with self.assertRaises(InferenceFenceError):
            self.gateway.close_mock(
                forged,mock_output_sha256="c"*64,structurally_valid=False,now=NOW
            )
        self.assertEqual(self.worker.inspect(ticket.lease_id)["status"],RESERVED)
        receipt=self.gateway.close_mock(
            ticket,mock_output_sha256="c"*64,structurally_valid=False,now=NOW
        )
        self.assertEqual(receipt["status"],REJECTED)
        self.assertEqual(self.auditor.inspect(ticket.lease_id)["audit_event_count"],2)

    def test_many_separate_gateway_sessions_cannot_duplicate_same_episode(self):
        obj=make(0)
        def attempt(_):
            try:
                return self.gateway.reserve_synthetic_signed_intent(
                    **kwargs_for(obj)
                )
            except InferenceFenceError:
                return None
        with ThreadPoolExecutor(max_workers=12) as pool:
            tickets=list(pool.map(attempt,range(22)))
        self.assertEqual(sum(isinstance(t,MockCiTicket) for t in tickets),1)
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute("SELECT burns FROM fm_private_ci.day_ledger")
                self.assertEqual(cur.fetchone()[0],1)
                cur.execute("SELECT count(*) FROM fm_private_ci.audit_events")
                self.assertEqual(cur.fetchone()[0],1)

    def test_three_daily_slots_are_bounded_to_same_mock_owner_project(self):
        obj=[make(i) for i in range(3)]
        results=[
            self.gateway.reserve_synthetic_signed_intent(**kwargs_for(row))
            for row in obj
        ]
        self.assertEqual(len({t.episode_id for t in results}),3)
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute("SELECT burns FROM fm_private_ci.day_ledger")
                self.assertEqual(cur.fetchone()[0],3)
        fourth=make(0)
        resign(fourth,lease_id="fourth_replayed_ci_lease")
        with self.assertRaises(InferenceFenceError):
            self.gateway.reserve_synthetic_signed_intent(**kwargs_for(fourth))
        self.assertEqual(self.auditor.inspect(results[0].lease_id)["status"],RESERVED)

    def test_changed_mock_project_scope_cannot_use_same_day_guard(self):
        first=make(0)
        self.gateway.reserve_synthetic_signed_intent(**kwargs_for(first))
        other=make(1)
        resign(other,free_tier_billing_project_fingerprint_sha256="f"*64)
        with self.assertRaises(InferenceFenceError):
            self.gateway.reserve_synthetic_signed_intent(**kwargs_for(other))

    def test_forged_owner_signature_is_rejected_before_privileged_procedure(self):
        obj=make(0)
        obj["anchor"]="f"*64
        with self.assertRaises(ModelLeaseError):
            self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute("SELECT count(*) FROM fm_private_ci.burns")
                self.assertEqual(cur.fetchone()[0],0)

    def test_search_path_is_fixed_and_public_function_execution_denied(self):
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute("""
                    SELECT proconfig
                      FROM pg_catalog.pg_proc
                     WHERE pronamespace='fm_private_ci'::regnamespace
                       AND proname='burn_mock_once'
                """)
                config=cur.fetchone()[0]
                self.assertIn(
                    "search_path=pg_catalog, fm_private_ci, pg_temp",config
                )
                cur.execute("""
                    SELECT has_function_privilege(
                        'fm_ci_worker',
                        'fm_private_ci.burn_mock_once(text,text,text,text,text,text,text,text,text,timestamptz)',
                        'EXECUTE'
                    )
                """)
                self.assertFalse(cur.fetchone()[0])
                cur.execute("""
                    SELECT has_function_privilege(
                        'fm_ci_gateway',
                        'fm_private_ci.burn_mock_once(text,text,text,text,text,text,text,text,text,timestamptz)',
                        'EXECUTE'
                    )
                """)
                self.assertTrue(cur.fetchone()[0])

    def test_client_changes_search_path_or_creates_temp_table_cannot_spoof_burn(self):
        obj=make(0)
        with connect_gateway() as db:
            with db.cursor() as cur:
                cur.execute("SET search_path TO pg_temp, public")
                cur.execute("CREATE TEMP TABLE burns(lease_id TEXT)")
        ticket=self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        self.assertEqual(self.worker.inspect(ticket.lease_id)["status"],RESERVED)

    def test_no_plaintext_mock_fence_token_in_privileged_db_rows(self):
        obj=make(0)
        ticket=self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        self.assertNotIn(ticket.ephemeral_fence_token,repr(ticket))
        self.assertNotIn(ticket.ephemeral_fence_token,
                         json.dumps(self.worker.inspect(ticket.lease_id)))
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute(
                    "SELECT lease_id,episode_id,token_sha256,"
                    "external_anchor_sha256 FROM fm_private_ci.burns"
                )
                self.assertNotIn(ticket.ephemeral_fence_token,
                                 json.dumps(cur.fetchall()))

    def test_untrusted_readonly_role_factory_cannot_impersonate_gateway(self):
        with self.assertRaises(InferenceFenceError):
            ProtectedMockGateway(connect_worker)
        with self.assertRaises(InferenceFenceError):
            LimitedMockLedgerObserver(connect_gateway,role=WORKER_ROLE)

    def test_non_privileged_status_does_not_mean_real_production_approval(self):
        obj=make(0)
        ticket=self.gateway.reserve_synthetic_signed_intent(**kwargs_for(obj))
        status=self.auditor.inspect(ticket.lease_id)
        self.assertFalse(status["production_secret_vault_verified"])
        self.assertFalse(status["admin_or_backup_tampering_excluded"])
        self.assertFalse(status["provider_inference_performed"])
        self.assertFalse(status["youtube_upload_enabled"])
        self.assertFalse(status["release_authorized"])


if __name__=="__main__":
    unittest.main()
