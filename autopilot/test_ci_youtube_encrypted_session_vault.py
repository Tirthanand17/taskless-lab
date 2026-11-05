"""B4b3 real disposable PostgreSQL 16 + AES-256-GCM mock session tests.

Dedicated hosted CI must first initialize SQL 002 and 003 in independent test
commands; these cases apply 004 only to isolated flowminute_fence_ci.
No real resumable URL, OAuth, KMS, YT request, or owner information is present.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import unittest

from autopilot.ci_youtube_attempt_fence import (
    ProtectedCiYouTubeFence,MockPgUploadTicket
)
from autopilot.ci_youtube_encrypted_session_vault import (
    ProtectedCiMockSessionVault,CiMockSessionAuditor,MockCiEnvelopeKey,
    SealedSessionRefused
)
from autopilot.ci_protected_pg_boundary import (
    GATEWAY_ROLE,AUDITOR_ROLE,WORKER_ROLE
)
from autopilot.test_ci_protected_pg_boundary import (
    ADMIN_DSN,connect_admin,connect_gateway,connect_auditor,connect_worker
)
from autopilot.test_ci_youtube_attempt_fence import mock_intent,REMOTE_ID

FAKE_REF="fake-session:CI_Synthetic_Unique_001__"
OTHER_REF="fake-session:CI_Synthetic_Unique_002__"


class PureEnvelopeFlagTests(unittest.TestCase):
    def test_default_key_and_flag_types_are_mock_only(self):
        key=MockCiEnvelopeKey("ci_v1",b"x"*32)
        self.assertNotIn("xxxxxxxx",repr(key))
        self.assertTrue(key.fake_only)

    def test_real_url_never_accepted_in_schema_or_public_api(self):
        import re
        from autopilot.ci_youtube_encrypted_session_vault import FAKE_HANDLE
        self.assertIsNone(FAKE_HANDLE.fullmatch(
            "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=credential"))
        self.assertIsNotNone(FAKE_HANDLE.fullmatch(FAKE_REF))


@unittest.skipUnless(os.environ.get(ADMIN_DSN),
                     "Requires isolated real PostgreSQL 16 CI service")
class DisposablePgEncryptedYouTubeSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connect_admin() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(),current_user")
                if tuple(cur.fetchone())!=("flowminute_fence_ci","flowminute_test"):
                    raise AssertionError("NEVER apply CI migration outside isolated fake DB")
                cur.execute("SELECT 1 FROM pg_catalog.pg_tables WHERE "
                            "schemaname='fm_private_ci' AND tablename='youtube_mock_attempts'")
                if cur.fetchone()!=(1,):
                    raise AssertionError("003 one-shot mock upload migration not initialized")
                script=(Path(__file__).parent/"sql"/"004_ci_youtube_encrypted_session.sql")
                cur.execute(script.read_text(encoding="utf-8"))
        cls.fence=ProtectedCiYouTubeFence(connect_gateway)
        cls.vault=ProtectedCiMockSessionVault(connect_gateway)
        cls.auditor=CiMockSessionAuditor(connect_auditor)
        cls.key=MockCiEnvelopeKey.generate()

    def setUp(self):
        with connect_admin() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "TRUNCATE fm_private_ci.youtube_mock_session_audit, "
                    "fm_private_ci.youtube_mock_session_envelopes, "
                    "fm_private_ci.youtube_mock_audit, "
                    "fm_private_ci.youtube_mock_attempts "
                    "RESTART IDENTITY CASCADE"
                )

    def _reserve(self):
        intent=mock_intent()
        return intent,self.fence.reserve_mock(intent)

    def _seal(self,intent,ticket,*,handle=FAKE_REF,key=None):
        return self.vault.seal_before_any_transfer(
            intent=intent,ticket=ticket,fake_handle=handle,
            total_bytes=3000000,key=self.key if key is None else key)

    def test_real_encryption_at_rest_and_new_client_process_like_restart(self):
        intent,ticket=self._reserve()
        receipt=self._seal(intent,ticket)
        self.assertFalse(receipt.release_authorized)
        self.assertFalse(receipt.real_encrypted_owner_vault_deployed)
        with connect_admin() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT nonce,ciphertext,key_version,octet_length(ciphertext),"
                    "mock_handle_sha256,encRYPTION_version "
                    "FROM fm_private_ci.youtube_mock_session_envelopes "
                    "WHERE channel_id=%s AND episode_id=%s",
                    (intent.channel_id,intent.episode_id))
                nonce,ciphertext,version,size,fingerprint,algorithm=cur.fetchone()
        self.assertEqual(len(nonce),12)
        self.assertGreater(size,len(FAKE_REF))
        self.assertNotIn(FAKE_REF.encode(),bytes(ciphertext))
        self.assertEqual(version,"ci_v1")
        self.assertEqual(algorithm,1)
        self.assertEqual(fingerprint,sha256(FAKE_REF.encode()).hexdigest())
        self.assertNotIn(FAKE_REF,repr(receipt))
        audit=self.auditor.inspect(intent.channel_id,intent.episode_id)
        self.assertEqual(audit["audit_event_count"],1)
        self.assertTrue(audit["sealed_in_disposable_postgres"])
        self.assertFalse(audit["contains_session_handle"])
        self.assertFalse(audit["real_cloud_persistence"])
        # A fresh gateway opens NEW independent real PG connections.
        recovered=ProtectedCiMockSessionVault(connect_gateway).load_after_simulated_restart(
            intent=intent,ticket=ticket,key=self.key)
        self.assertEqual(recovered.fake_handle,FAKE_REF)
        self.assertNotIn(FAKE_REF,repr(recovered))
        self.assertEqual(recovered.instruction.action,"QUERY_EXISTING_SESSION_ONLY")
        self.assertEqual(recovered.instruction.headers["Content-Range"],
                         "bytes */3000000")
        self.assertFalse(recovered.instruction.actual_http_executed)
        self.assertFalse(recovered.real_youtube_session)
        self.assertFalse(recovered.release_authorized)
        self.assertEqual(self.auditor.inspect(intent.channel_id,intent.episode_id)
                         ["audit_event_count"],2)

    def test_fence_without_sealed_session_cannot_resume_or_restart_upload(self):
        intent,ticket=self._reserve()
        audit=self.auditor.inspect(intent.channel_id,intent.episode_id)
        self.assertFalse(audit["sealed_in_disposable_postgres"])
        with self.assertRaises(SealedSessionRefused):
            self.vault.load_after_simulated_restart(
                intent=intent,ticket=ticket,key=self.key)

    def test_same_episode_simultaneous_encrypt_seal_at_most_once(self):
        intent,ticket=self._reserve()
        def attempt(n):
            try:
                return self._seal(intent,ticket,handle=FAKE_REF if n%2 else OTHER_REF)
            except SealedSessionRefused:
                return None
        with ThreadPoolExecutor(max_workers=12) as pool:
            out=list(pool.map(attempt,range(24)))
        self.assertEqual(sum(x is not None for x in out),1)
        audit=self.auditor.inspect(intent.channel_id,intent.episode_id)
        self.assertEqual(audit["audit_event_count"],1)
        self.assertFalse(audit["release_authorized"])

    def test_wrong_channel_context_token_and_release_forgery_rejected(self):
        intent,ticket=self._reserve()
        for altered in (
            replace(ticket,channel_id="UC"+"Y"*22),
            replace(ticket,episode_id="another_episode_abc"),
            replace(ticket,context_sha256="a"*64),
            replace(ticket,ephemeral_token="f"*64),
            replace(ticket,release_authorized=True),
            replace(ticket,simulated_only=False),
        ):
            with self.subTest(altered=altered.episode_id),self.assertRaises(
                    SealedSessionRefused):
                self._seal(intent,altered)
        self.assertFalse(self.auditor.inspect(
            intent.channel_id,intent.episode_id)["sealed_in_disposable_postgres"])
        self._seal(intent,ticket)
        with self.assertRaises(SealedSessionRefused):
            self.vault.load_after_simulated_restart(
                intent=intent,ticket=replace(ticket,ephemeral_token="f"*64),key=self.key)

    def test_no_real_youtube_session_uri_or_forged_envelope_key(self):
        intent,ticket=self._reserve()
        for reference in (
            "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=xxx",
            "fake-session:short", "", "http://example.com/real", "fake-session:xxx hello",
        ):
            with self.subTest(reference=reference),self.assertRaises(SealedSessionRefused):
                self._seal(intent,ticket,handle=reference)
        for key in (
            MockCiEnvelopeKey("prod_v1",b"x"*32),
            MockCiEnvelopeKey("ci_v1",b"short"),
            MockCiEnvelopeKey("ci_v1",b"x"*32, fake_only=False),
        ):
            with self.subTest(key=key.version),self.assertRaises(SealedSessionRefused):
                self._seal(intent,ticket,key=key)
        self.assertFalse(self.auditor.inspect(
            intent.channel_id,intent.episode_id)["sealed_in_disposable_postgres"])

    def test_unauthorized_gateway_worker_or_auditor_no_table_or_functions(self):
        with connect_admin() as conn:
            with conn.cursor() as cur:
                for role in (GATEWAY_ROLE,WORKER_ROLE,AUDITOR_ROLE):
                    for table in ("youtube_mock_session_envelopes",
                                  "youtube_mock_session_audit"):
                        for privilege in ("SELECT","INSERT","UPDATE","DELETE","TRUNCATE"):
                            cur.execute(
                                "SELECT pg_catalog.has_table_privilege(%s,%s,%s)",
                                (role,"fm_private_ci."+table,privilege))
                            self.assertFalse(cur.fetchone()[0],
                                             (role,table,privilege))
                for role in (WORKER_ROLE,AUDITOR_ROLE):
                    for function in (
                        "fm_private_ci.seal_youtube_mock_session_once("
                        "text,text,text,text,text,bigint,text,bytea,bytea,text,text)",
                        "fm_private_ci.retrieve_youtube_mock_session("
                        "text,text,text,text,text)",
                    ):
                        cur.execute(
                            "SELECT pg_catalog.has_function_privilege(%s,%s,'EXECUTE')",
                            (role,function))
                        self.assertFalse(cur.fetchone()[0],(role,function))
                cur.execute("SELECT pg_catalog.has_function_privilege(%s,%s,'EXECUTE')",
                            (WORKER_ROLE,
                             "fm_private_ci.inspect_youtube_mock_session(text,text)"))
                self.assertFalse(cur.fetchone()[0])
        with self.assertRaises(Exception):
            ProtectedCiMockSessionVault(connect_worker)
        with self.assertRaises(Exception):
            CiMockSessionAuditor(connect_gateway)
        with connect_auditor() as conn:
            with conn.cursor() as cur:
                with self.assertRaises(Exception):
                    cur.execute("SELECT nonce FROM "
                                "fm_private_ci.youtube_mock_session_envelopes")

    def test_ciphertext_tamper_detected_and_never_reissues_new_upload(self):
        intent,ticket=self._reserve()
        self._seal(intent,ticket)
        with connect_admin() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE fm_private_ci.youtube_mock_session_envelopes "
                    "SET ciphertext=set_byte(ciphertext,5,"
                    "(get_byte(ciphertext,5) # 1)) "
                    "WHERE channel_id=%s AND episode_id=%s",
                    (intent.channel_id,intent.episode_id))
        with self.assertRaises(SealedSessionRefused):
            self.vault.load_after_simulated_restart(
                intent=intent,ticket=ticket,key=self.key)
        with self.assertRaises(SealedSessionRefused):
            self._seal(intent,ticket)

    def test_nonce_tamper_fails_authenticated_decryption(self):
        intent,ticket=self._reserve()
        self._seal(intent,ticket)
        with connect_admin() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE fm_private_ci.youtube_mock_session_envelopes "
                    "SET nonce=set_byte(nonce,0,(get_byte(nonce,0) # 1)) "
                    "WHERE channel_id=%s AND episode_id=%s",
                    (intent.channel_id,intent.episode_id))
        with self.assertRaises(SealedSessionRefused):
            self.vault.load_after_simulated_restart(
                intent=intent,ticket=ticket,key=self.key)

    def test_wrong_in_memory_key_rejected_even_same_key_version(self):
        intent,ticket=self._reserve()
        self._seal(intent,ticket)
        wrong=MockCiEnvelopeKey.generate()
        self.assertEqual(wrong.version,self.key.version)
        with self.assertRaises(SealedSessionRefused):
            ProtectedCiMockSessionVault(connect_gateway).load_after_simulated_restart(
                intent=intent,ticket=ticket,key=wrong)

    def test_sql_forged_seal_cannot_bypass_ticket_binding(self):
        intent,ticket=self._reserve()
        with connect_gateway() as conn:
            with conn.cursor() as cur:
                with self.assertRaises(Exception):
                    cur.execute(
                        "SELECT fm_private_ci.seal_youtube_mock_session_once("
                        "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            intent.channel_id,intent.episode_id,"0"*64,
                            intent.context_sha256,intent.final_mp4_sha256,
                            3000000,"ci_v1",b"n"*12,b"x"*48,
                            "a"*64,"b"*64,
                        ),
                    )
        self.assertFalse(self.auditor.inspect(
            intent.channel_id,intent.episode_id)["sealed_in_disposable_postgres"])

    def test_terminal_reported_id_cannot_decrypt_session_again(self):
        intent,ticket=self._reserve()
        self._seal(intent,ticket)
        self.fence.report_unverified_remote_id(ticket,REMOTE_ID)
        with self.assertRaises(SealedSessionRefused):
            self.vault.load_after_simulated_restart(
                intent=intent,ticket=ticket,key=self.key)
        self.assertFalse(self.auditor.inspect(
            intent.channel_id,intent.episode_id)["real_youtube_upload"])


if __name__=="__main__":
    unittest.main()
