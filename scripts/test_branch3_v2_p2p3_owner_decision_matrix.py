"""No creator permission can be inferred from a source-free owner matrix."""
import copy
from datetime import datetime, timezone
import unittest

from scripts.test_branch3_v2_p2p3_pilot_owner_review import inputs, NOW
from scripts.branch3_v2_p2p3_pilot_owner_review import (
    compile_owner_pilot_packet, PilotDenied,
)
from scripts.branch3_v2_p2p3_owner_decision_matrix import build_matrix, BLOCKED


def fixture():
    watch, audit, policy, registry = inputs()
    packet = compile_owner_pilot_packet(
        watchlist=watch, public_audit=audit,
        policy=policy, registry=registry, now=NOW)
    return watch, audit, policy, registry, packet


class SourceFreeOwnerMatrixTests(unittest.TestCase):
    def test_five_unapproved_rows_and_three_only_research_priorities(self):
        w, a, p, r, packet = fixture()
        result = build_matrix(packet, watchlist=w, public_audit=a,
                              policy=p, registry=r, now=NOW)
        self.assertEqual(result["prospects_total"], 5)
        self.assertEqual(len(result["rows"]), 5)
        self.assertEqual(len(result["research_first_only"]), 3)
        self.assertTrue(result["all_actions_blocked"])
        self.assertFalse(result["owner_approval_received"])
        self.assertFalse(result["license_received"])
        self.assertEqual(result["creator_outreach_sent"], 0)
        self.assertEqual(result["licensed_media_delivered"], 0)
        self.assertEqual(result["youtube_uploads"], 0)
        for row in result["rows"]:
            self.assertEqual(row["status"], BLOCKED)
            self.assertEqual(row["pending_rights_questions"], 30)
            for key in (
                "owner_selection_recorded", "identity_authentication_complete",
                "legal_signatory_authenticated", "specific_source_media_rights_cleared",
                "commercial_youtube_short_license_verified",
                "underlying_music_guests_and_game_rights_cleared",
                "private_source_handoff_authorized",
                "owner_exact_media_release_signed", "outreach_authorized",
                "clip_generation_authorized", "youtube_upload_authorized",
                "youtube_publish_authorized"
            ):
                self.assertIs(row[key], False)

    def test_forged_first_creator_permission_cannot_enter_matrix(self):
        w, a, p, r, packet = fixture()
        for field, value in (
            ("allow_contact", True),
            ("allow_source_download", True),
            ("commercial_youtube_license_granted", True),
            ("actual_owner_shortlist_selected", True),
        ):
            modified = copy.deepcopy(packet)
            modified["owner_review_first_options"][0][field] = value
            with self.subTest(field=field), self.assertRaises(PilotDenied):
                build_matrix(modified, watchlist=w, public_audit=a,
                             policy=p, registry=r, now=NOW)

    def test_forged_global_rights_provenance_cannot_enter_matrix(self):
        w, a, p, r, packet = fixture()
        for field, value in (
            ("owner_release_signed", True),
            ("creator_messages_sent", 1),
            ("authenticated_licenses_received", 1),
            ("source_watchlist_sha256", "0"*64),
            ("youtube_publish_authorized", True),
        ):
            modified = copy.deepcopy(packet)
            modified[field] = value
            with self.subTest(field=field), self.assertRaises(PilotDenied):
                build_matrix(modified, watchlist=w, public_audit=a,
                             policy=p, registry=r, now=NOW)


if __name__ == "__main__":
    unittest.main()
