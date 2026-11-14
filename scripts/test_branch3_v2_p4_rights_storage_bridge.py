"""P2/P3->P4 creator-license/private-storage bridge must always fail closed."""
import copy
import unittest

from scripts.test_branch3_v2_p2p3_pilot_owner_review import NOW, inputs
from scripts.branch3_v2_p2p3_pilot_owner_review import compile_owner_pilot_packet
from scripts.branch3_v2_p2p3_owner_decision_matrix import build_matrix
from scripts.branch3_v2_p4_synthetic_handoff_preflight import actual_closed_boundary
from scripts.branch3_a3_private_vault_readback import fixture_report
from scripts.branch3_v2_p4_rights_storage_bridge import (
    STAGE, HOLD, HandoffDenied, build_handoff_hold,
    actual_source_free_readiness, production_media_ingest,
)


def fixture():
    w, audit, policy, registry = inputs()
    packet = compile_owner_pilot_packet(
        watchlist=w, public_audit=audit, policy=policy, registry=registry, now=NOW)
    matrix = build_matrix(packet, watchlist=w, public_audit=audit,
                          policy=policy, registry=registry, now=NOW)
    return dict(owner_matrix=matrix, storage_gate=actual_closed_boundary(),
                vault_fixture=fixture_report())


class RightsStorageBridgeTests(unittest.TestCase):
    def test_real_closed_state_from_three_existing_modules(self):
        report = actual_source_free_readiness(now=NOW)
        self.assertEqual(report["stage"], STAGE)
        self.assertEqual(report["status"], HOLD)
        self.assertEqual(report["public_creator_research_count"], 5)
        self.assertEqual(report["suggested_review_first_not_owner_selected"], 3)
        self.assertEqual(report["creator_rightsholder_grants_verified"], 0)
        self.assertEqual(report["creator_original_masters_received"], 0)
        self.assertFalse(report["authenticated_private_media_vault_approved"])
        self.assertFalse(report["github_private_metadata_readback_performed"])
        self.assertFalse(report["source_ingestion_enabled"])
        self.assertFalse(report["media_render_enabled"])
        self.assertFalse(report["youtube_upload_enabled"])
        self.assertFalse(report["youtube_publish_enabled"])
        self.assertFalse(report["real_p4_milestone_complete"])
        self.assertEqual(len(report["missing_real_world_dependencies"]), 7)
        self.assertNotIn("recipient_address", str(report))
        self.assertNotIn("private_repo_name", str(report))

    def test_forged_rights_or_creator_action_never_unlocks_ingest(self):
        for field, value in (
            ("license_received", True), ("owner_approval_received", True),
            ("creator_outreach_sent", 1), ("licensed_media_delivered", 1),
            ("all_actions_blocked", False), ("youtube_uploads", 1),
        ):
            d = fixture()
            d["owner_matrix"][field] = value
            with self.subTest(field=field), self.assertRaises(HandoffDenied):
                build_handoff_hold(**d)

    def test_forged_individual_rights_row_never_unlocks_ingest(self):
        for field in (
            "owner_selection_recorded", "legal_signatory_authenticated",
            "commercial_youtube_short_license_verified",
            "specific_source_media_rights_cleared",
            "private_source_handoff_authorized", "youtube_publish_authorized",
        ):
            d = fixture()
            d["owner_matrix"]["rows"][4][field] = True
            with self.subTest(field=field), self.assertRaises(HandoffDenied):
                build_handoff_hold(**d)

    def test_forged_vault_or_p4_policy_never_unlocks_ingest(self):
        for field, value in (
            ("private_vault_activated", True),
            ("rights_grants_verified", 1),
            ("rights_grants_verified", True),
            ("creator_media_fetch_enabled", True),
            ("creator_media_write_enabled", True),
            ("youtube_upload_enabled", True),
            ("p4_milestone_complete", True),
        ):
            d = fixture()
            d["storage_gate"][field] = value
            with self.subTest(field=field), self.assertRaises(HandoffDenied):
                build_handoff_hold(**d)

    def test_a3_vault_fixture_cannot_pretend_live_readback(self):
        d = fixture()
        d["vault_fixture"]["live_github_private_metadata_readback"] = True
        with self.assertRaises(HandoffDenied):
            build_handoff_hold(**d)
        d = fixture()
        d["vault_fixture"]["readback_passed"] = True
        with self.assertRaises(HandoffDenied):
            build_handoff_hold(**d)

    def test_media_ingest_entrypoint_not_available(self):
        for kwargs in ({}, {"creator_approved": True},
                       {"source_path": "/tmp/creator-stream.mp4", "grant": True},
                       {"youtube_upload": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(HandoffDenied):
                production_media_ingest(**kwargs)


if __name__ == "__main__":
    unittest.main()
