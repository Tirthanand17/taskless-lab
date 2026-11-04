"""B3d4c2b1 adversarial concurrency and crash safety (100% mock/no network).

All signed leases are disposable B3d4c2a synthetic owner fixtures. The SQLite
database is in GitHub-hosted TemporaryDirectory only; never a real private
cloud ledger or a provider billing guarantee.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import sqlite3
import unittest

from autopilot.atomic_mock_inference_fence import (
    EphemeralOneUseLedger, InferenceFenceError, Reservation,
    RESERVED, ACCEPTED, REJECTED, MOCK_STATUS,
    evaluate_one_synthetic_mock_script,
)
from autopilot.owner_provider_lease_gate import ModelLeaseError
from autopilot.test_owner_provider_lease_gate import (
    NOW, EXCLUDED, make, resign,
)
from autopilot.test_script_draft_agent import short_proposal


def kwargs_for(item):
    return {
        "slot": item["slot"],
        "observations": item["observations"],
        "signed_lease": item["lease"],
        "external_lease_anchor_sha256": item["anchor"],
        "owner_registry": item["registry"],
        "excluded_automated_agent_ids": EXCLUDED,
        "now": NOW,
    }


class AtomicMockInferenceFenceTests(unittest.TestCase):
    def setUp(self):
        self.dir = TemporaryDirectory(prefix="flowminute-b3d4c2b1-ephemeral-")
        self.addCleanup(self.dir.cleanup)
        self.path = Path(self.dir.name) / "private_mock_lease.sqlite3"
        self.ledger = EphemeralOneUseLedger(self.path)

    def test_single_owner_signed_lease_burned_before_any_response(self):
        item = make(0)
        record = self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))
        self.assertIsInstance(record, Reservation)
        status = self.ledger.inspect(item["terms"].lease_id)
        self.assertEqual(status["state"], RESERVED)
        self.assertFalse(status["safely_retryable"])
        self.assertFalse(status["provider_inference_executed"])
        self.assertFalse(status["real_project_billing_guaranteed"])
        self.assertNotIn("fence_token", json.dumps(status))
        self.assertNotIn("api_key", json.dumps(status))
        with self.assertRaises(InferenceFenceError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))

    def test_one_shot_structurally_validated_synthetic_response_is_not_real_ai(self):
        item=make(0)
        report = evaluate_one_synthetic_mock_script(
            self.ledger, **kwargs_for(item), raw_synthetic_proposal=short_proposal(),
        )
        self.assertEqual(report["status"],MOCK_STATUS)
        self.assertEqual(report["receipt"]["status"],ACCEPTED)
        self.assertFalse(report["actual_generative_model_output_created"])
        self.assertFalse(report["full_original_content_reviewed"])
        self.assertFalse(report["factual_claims_verified"])
        self.assertFalse(report["durable_private_cloud_ledger_connected"])
        self.assertFalse(report["release_authorized"])
        self.assertEqual(self.ledger.inspect(item["terms"].lease_id)["state"],ACCEPTED)
        with self.assertRaises(InferenceFenceError):
            evaluate_one_synthetic_mock_script(
                self.ledger,**kwargs_for(item),raw_synthetic_proposal=short_proposal(),
            )

    def test_invalid_mock_draft_consumes_lease_no_retry(self):
        item=make(0)
        broken=dict(short_proposal())
        broken["narration"]="Insufficient sample words"
        with self.assertRaisesRegex(InferenceFenceError,"after lease burned"):
            evaluate_one_synthetic_mock_script(
                self.ledger,**kwargs_for(item),raw_synthetic_proposal=broken,
            )
        self.assertEqual(self.ledger.inspect(item["terms"].lease_id)["state"],REJECTED)
        with self.assertRaises(InferenceFenceError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))

    def test_simulated_worker_crash_and_reopen_stays_burned(self):
        item=make(0)
        self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))
        # Reopen same filesystem database as a fresh worker after an outage.
        reopened=EphemeralOneUseLedger(self.path)
        status=reopened.inspect(item["terms"].lease_id)
        self.assertEqual(status["state"],RESERVED)
        self.assertFalse(status["safely_retryable"])
        with self.assertRaises(InferenceFenceError):
            reopened.reserve_synthetic_owner_lease(**kwargs_for(item))

    def test_two_workers_can_never_reserve_one_lease_twice(self):
        item=make(0)
        args=kwargs_for(item)
        def attempt(_):
            try:
                return self.ledger.reserve_synthetic_owner_lease(**args)
            except InferenceFenceError:
                return None
        with ThreadPoolExecutor(max_workers=12) as pool:
            results=list(pool.map(attempt, range(24)))
        self.assertEqual(sum(isinstance(x,Reservation) for x in results),1)
        self.assertEqual(self.ledger.inspect(item["terms"].lease_id)["state"],RESERVED)

    def test_new_signed_lease_cannot_reuse_same_episode(self):
        first=make(0)
        self.ledger.reserve_synthetic_owner_lease(**kwargs_for(first))
        another=make(0)
        resign(another,lease_id="separate_second_attempt")
        with self.assertRaises(InferenceFenceError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(another))

    def test_other_episode_cannot_reuse_first_lease_identity(self):
        first=make(0)
        self.ledger.reserve_synthetic_owner_lease(**kwargs_for(first))
        other=make(1)
        resign(other,lease_id=first["terms"].lease_id)
        with self.assertRaises(InferenceFenceError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(other))

    def test_three_correct_daily_slots_can_reserve_once_each(self):
        objects=[make(i) for i in range(3)]
        reservations=[
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(o))
            for o in objects
        ]
        self.assertEqual(len(set(x.episode_id for x in reservations)),3)
        self.assertEqual(len(set(x.lease_id for x in reservations)),3)
        self.assertTrue(all(
            self.ledger.inspect(x.lease_id)["state"]==RESERVED for x in reservations
        ))
        # A fourth attempt for the same day, even a valid extra key/lease,
        # cannot evade the per-episode UNIQUE constraint or 3/day quota.
        extra=make(1)
        resign(extra,lease_id="fourth_lease_attempt")
        with self.assertRaises(InferenceFenceError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(extra))

    def test_mix_different_private_project_fingerprint_is_denied(self):
        first=make(0)
        self.ledger.reserve_synthetic_owner_lease(**kwargs_for(first))
        other=make(1)
        resign(other,free_tier_billing_project_fingerprint_sha256="f"*64)
        with self.assertRaises(InferenceFenceError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(other))

    def test_mix_independent_owner_identifiers_is_denied(self):
        first=make(0)
        self.ledger.reserve_synthetic_owner_lease(**kwargs_for(first))
        second=make(1)
        # Make an unrelated valid synthetic signing identity.
        original=second["registry"]["enrolled_owner"]
        second["registry"]={"other_owner":replace(original,owner_id="other_owner")}
        resign(second,owner_id="other_owner")
        with self.assertRaises(InferenceFenceError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(second))

    def test_tampered_owner_lease_external_anchor_denied_before_reserve(self):
        item=make(0)
        item["anchor"]="a"*64
        with self.assertRaises(ModelLeaseError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))
        fresh=make(0)
        self.ledger.reserve_synthetic_owner_lease(**kwargs_for(fresh))

    def test_forged_source_headline_denied_before_reserve(self):
        item=make(0)
        item["observations"]["sources"][0]["title"]="New source title injected after owner signature."
        with self.assertRaises(ModelLeaseError):
            self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))
        fresh=make(0)
        self.ledger.reserve_synthetic_owner_lease(**kwargs_for(fresh))

    def test_bad_private_parent_or_db_path_denied(self):
        with self.assertRaises(InferenceFenceError):
            EphemeralOneUseLedger(Path(":memory:"))
        with self.assertRaises(InferenceFenceError):
            EphemeralOneUseLedger(Path(self.dir.name)/"not_db.txt")
        target=Path(self.dir.name)/"real.sqlite3"
        target.write_bytes(b"")
        link=Path(self.dir.name)/"linked.sqlite3"
        link.symlink_to(target)
        with self.assertRaises(InferenceFenceError):
            EphemeralOneUseLedger(link)

    def test_forged_fence_token_cannot_close_reservation(self):
        item=make(0)
        reserved=self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))
        forged=replace(reserved,fence_token="c"*64)
        with self.assertRaises(InferenceFenceError):
            self.ledger.close_mock(
                forged,mock_result_sha256="a"*64,
                valid_structured_draft=True,now=NOW,
            )
        self.assertEqual(self.ledger.inspect(reserved.lease_id)["state"],RESERVED)
        good=self.ledger.close_mock(
            reserved,mock_result_sha256="b"*64,
            valid_structured_draft=True,now=NOW,
        )
        self.assertEqual(good["status"],ACCEPTED)
        with self.assertRaises(InferenceFenceError):
            self.ledger.close_mock(
                reserved,mock_result_sha256="b"*64,
                valid_structured_draft=True,now=NOW,
            )

    def test_bools_are_not_allowed_as_closure_outcomes(self):
        item=make(0)
        ticket=self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))
        for input in (1,"PASS",None):
            with self.subTest(input=input),self.assertRaises(InferenceFenceError):
                self.ledger.close_mock(
                    ticket,mock_result_sha256="b"*64,
                    valid_structured_draft=input,now=NOW,
                )
        self.assertEqual(self.ledger.inspect(ticket.lease_id)["state"],RESERVED)

    def test_output_has_no_api_key_full_prompt_or_fence_secret(self):
        item=make(0)
        ticket=self.ledger.reserve_synthetic_owner_lease(**kwargs_for(item))
        report=self.ledger.close_mock(
            ticket,mock_result_sha256="f"*64,
            valid_structured_draft=True,now=NOW,
        )
        stored=self.path.read_bytes()
        self.assertNotIn(ticket.fence_token.encode(),stored)
        self.assertNotIn(b"generativelanguage.googleapis.com",stored)
        self.assertNotIn(b"One setting can change",stored)
        self.assertNotIn(b"Private API Key",stored)
        self.assertNotIn("fence_token",json.dumps(report))
        self.assertFalse(report["release_authorized"])

    def test_no_real_live_inference_wrapper_is_exported(self):
        import autopilot.atomic_mock_inference_fence as module
        self.assertFalse(hasattr(module,"send_gemini_request"))
        self.assertFalse(hasattr(module,"enable_provider"))
        self.assertFalse(hasattr(module,"youtube_upload"))
        self.assertEqual(module.MOCK_STATUS,MOCK_STATUS)


if __name__=="__main__":
    unittest.main()
