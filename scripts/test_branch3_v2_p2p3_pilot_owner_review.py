"""Owner-decision-only P2/P3 fresh public route and unsigned pilot tests."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_v2_creator_prospect_intake import (
    DATA, load_watchlist,
)
from scripts.branch3_v2_p3_licensing_scope_quarantine import (
    CHECKS, request_terms,
)
from scripts.branch3_a2_review_receipt import (
    POLICY, REGISTRY, read_json as a2_read_json,
)
from scripts.branch3_v2_p2p3_pilot_owner_review import (
    AUDIT_FILE, CHANNEL, FIRST, ID_ORDER, OUT_NAME,
    PilotDenied, STAGE, compile_owner_pilot_packet,
    load_public_route_audit, production_contact_license_or_clip,
    validate_owner_packet, validate_public_route_audit,
)


NOW = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


def inputs():
    return (
        load_watchlist(DATA),
        load_public_route_audit(),
        a2_read_json(POLICY),
        a2_read_json(REGISTRY),
    )


def draft():
    w, a, p, r = inputs()
    return compile_owner_pilot_packet(
        watchlist=w, public_audit=a, policy=p, registry=r, now=NOW)


class OwnerPilotReviewTests(unittest.TestCase):
    def test_five_public_route_observations_not_verified_creator_grants(self):
        watch, audit, _, _ = inputs()
        validate_public_route_audit(audit, watch, now=NOW)
        self.assertEqual(audit["channel_id"], CHANNEL)
        self.assertEqual(audit["public_creator_contact_routes_observed"], 5)
        self.assertEqual([r["prospect_id"] for r in audit["options"]],
                         list(ID_ORDER))
        self.assertEqual(audit["route_review_expires_after_days"], 30)
        self.assertFalse(audit["owner_shortlist_approved"])
        self.assertFalse(audit["legal_identity_authenticated"])
        self.assertEqual(audit["creator_outreach_sent"], 0)
        self.assertEqual(audit["authenticated_commercial_rights_grants"], 0)
        self.assertEqual(audit["authorized_media_files"], 0)
        self.assertEqual(audit["youtube_uploads"], 0)
        for row in audit["options"]:
            self.assertTrue(row["route_publicly_observed"])
            for key in (
                "independent_creator_identity_authenticated",
                "current_rightsholder_signatory_authenticated",
                "source_media_verified_owned",
                "commercial_clipping_license_granted",
                "revenue_share_terms_agreed", "human_owner_approved_outreach",
                "outreach_sent",
            ):
                self.assertFalse(row[key])

    def test_owner_review_three_options_and_two_hold_not_a_final_shortlist(self):
        d = draft()
        self.assertEqual(d["stage"], STAGE)
        self.assertEqual(d["channel_id"], CHANNEL)
        self.assertEqual(d["owner_review_first_count"], 3)
        self.assertEqual([x["prospect_id"]
                          for x in d["owner_review_first_options"]],
                         list(FIRST))
        self.assertEqual([x["prospect_id"]
                          for x in d["deferred_or_format_only_options"]],
                         ["mrjd_gaming", "caseoh_format"])
        self.assertTrue(d["all_proposals_unsent"])
        self.assertTrue(d["all_owner_shortlist_selections_unapproved"])
        self.assertTrue(d["all_creators_rightsholder_permissions_unverified"])
        self.assertTrue(d["all_source_rights_and_guest_music_game_not_cleared"])
        self.assertEqual(d["proposed_private_pilot_clips_per_creator"], 3)
        self.assertEqual(d["license_scope_questions_each"], len(CHECKS))
        self.assertGreaterEqual(len(CHECKS), 25)
        self.assertEqual(d["unsigned_negotiation_terms"], request_terms())
        self.assertTrue(d["unsigned_negotiation_terms"]["request_only_not_agreement"])
        self.assertTrue(d["unsigned_negotiation_terms"]["no_license_granted"])

    def test_unsent_specific_creator_drafts_have_no_destination(self):
        d = draft()
        for item in d["owner_review_first_options"] + d["deferred_or_format_only_options"]:
            self.assertIsNone(item["recipient_address"])
            self.assertIn("CLIVOX:", item["unsent_subject"])
            self.assertIn(item["display_name"], item["unsent_subject"])
            self.assertIn("Hello", item["unsent_message"])
            self.assertIn("Nothing would be published", item["unsent_message"])
            self.assertEqual(item["rights_checklist_pending_count"], len(CHECKS))
            for flag in (
                "actual_owner_shortlist_selected",
                "business_route_independently_authenticated",
                "actual_signatory_authorized", "source_video_grant_verified",
                "human_originality_editorial_approved",
                "commercial_youtube_license_granted",
                "allow_contact", "allow_source_download", "allow_upload",
            ):
                self.assertFalse(item[flag])
        self.assertEqual(d["creator_messages_sent"], 0)
        self.assertEqual(d["creator_replies_received"], 0)
        self.assertEqual(d["authenticated_licenses_received"], 0)
        self.assertEqual(d["creator_source_files_delivered"], 0)
        self.assertEqual(d["youtube_uploads"], 0)
        self.assertEqual(d["real_youtube_api_requests"], 0)
        self.assertFalse(d["revenue_predictions_generated"])
        self.assertFalse(d["licensing_authorized"])
        self.assertFalse(d["owner_release_signed"])
        self.assertFalse(d["media_download_authorized"])
        self.assertFalse(d["video_editing_authorized"])
        self.assertFalse(d["youtube_upload_authorized"])
        self.assertFalse(d["youtube_publish_authorized"])

    def test_no_creator_email_phone_contract_source_video_or_secret_in_output(self):
        result = json.dumps(draft())
        for string in (
            "@", "phone_number", "personal_email",
            "access_token", "refresh_token", "BEGIN PRIVATE KEY",
            "creator_contract_text", "creator_signed_grant",
            "source_video_id", "source_media_download_url",
            "youtube.com/watch?", "predicted_viral_views",
        ):
            self.assertNotIn(string, result)
        self.assertIn("https://ankitt.com/", result)
        self.assertIn("https://eggmilk.carrd.co/", result)
        self.assertIn("https://www.mandarriaxl.com/", result)

    def test_audit_stale_after_thirty_days_or_future_dated_denied(self):
        watch, audit, _, _ = inputs()
        with self.assertRaises(ValueError):
            validate_public_route_audit(
                audit, watch, now=NOW+timedelta(days=31))
        with self.assertRaises(ValueError):
            validate_public_route_audit(
                audit, watch, now=NOW-timedelta(days=1))

    def test_audit_flags_can_never_self_certify_owner_licensor_or_consents(self):
        watch, baseline, _, _ = inputs()
        for key, value in (
            ("owner_shortlist_approved", True),
            ("legal_identity_authenticated", True),
            ("creator_to_specific_media_ownership_authenticated", True),
            ("human_creator_consent_for_each_source", True),
            ("creator_outreach_sent", 1), ("creator_outreach_sent", True),
            ("creator_replies_received", 1),
            ("authenticated_commercial_rights_grants", 1),
            ("authorized_media_files", 1), ("youtube_uploads", 1),
            ("no_media_download_or_contact_tool_called", False),
            ("research_only", False),
            ("no_personal_email_or_phone_saved", False),
            ("no_youtube_api_derived_creator_ranking", False),
            ("observed_at_utc", "2028-01-01T00:00:00Z"),
            ("public_creator_contact_routes_observed", 30),
            ("route_review_expires_after_days", 365),
            ("channel_id", "UNKNOWNCHANNEL"),
        ):
            doc = copy.deepcopy(baseline)
            doc[key] = value
            with self.subTest(key=key), self.assertRaises(PilotDenied):
                validate_public_route_audit(doc, watch, now=NOW)

    def test_external_forged_public_routes_private_contact_source_link_denied(self):
        watch, baseline, _, _ = inputs()
        for key, value in (
            ("public_evidence_url", "https://fake-permission.example.invalid"),
            ("observed_route_type", "SIGNATORY_VERIFIED"),
            ("owner_review_group", "OWNER_APPROVED_CONTACT"),
            ("route_publicly_observed", False),
            ("independent_creator_identity_authenticated", True),
            ("current_rightsholder_signatory_authenticated", True),
            ("source_media_verified_owned", True),
            ("commercial_clipping_license_granted", True),
            ("revenue_share_terms_agreed", True),
            ("human_owner_approved_outreach", True),
            ("outreach_sent", True),
            ("observed_fit", "Contact person at name@example.com"),
            ("key_human_verification", "Call +12345678910 for rights"),
        ):
            doc = copy.deepcopy(baseline)
            doc["options"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_public_route_audit(doc, watch, now=NOW)
        doc = copy.deepcopy(baseline)
        doc["options"][0]["actual_legal_owner_approved"] = True
        with self.assertRaises(PilotDenied):
            validate_public_route_audit(doc, watch, now=NOW)
        doc = copy.deepcopy(baseline)
        doc["options"].reverse()
        with self.assertRaises(PilotDenied):
            validate_public_route_audit(doc, watch, now=NOW)

    def test_human_shortlist_cannot_be_replaced_with_draft_recommendation(self):
        w, a, p, r = inputs()
        baseline = draft()
        for key, value in (
            ("actual_owner_shortlist_selected", True),
            ("business_route_independently_authenticated", True),
            ("actual_signatory_authorized", True),
            ("source_video_grant_verified", True),
            ("human_originality_editorial_approved", True),
            ("commercial_youtube_license_granted", True),
            ("allow_contact", True), ("allow_source_download", True),
            ("allow_upload", True), ("recipient_address", "test@example.com"),
            ("rights_checklist_pending_count", 0),
            ("unsent_message", "We already signed!"),
        ):
            doc = copy.deepcopy(baseline)
            doc["owner_review_first_options"][0][key] = value
            with self.subTest(key=key), self.assertRaises(PilotDenied):
                validate_owner_packet(doc, public_audit=a, watchlist=w,
                                      policy=p, registry=r, now=NOW)

    def test_commercial_terms_are_negotiation_only_and_cannot_flip(self):
        w, a, p, r = inputs()
        d = draft()
        for key, value in (
            ("no_license_granted", False),
            ("no_terms_accepted", False),
            ("request_only_not_agreement", False),
            ("number_of_private_pilot_clips", 200),
            ("requested_channel_id", "WRONG"),
        ):
            doc = copy.deepcopy(d)
            doc["unsigned_negotiation_terms"][key] = value
            with self.subTest(key=key), self.assertRaises(PilotDenied):
                validate_owner_packet(doc, public_audit=a, watchlist=w,
                                      policy=p, registry=r, now=NOW)

    def test_report_laundering_disallowed(self):
        w, a, p, r = inputs()
        for key, value in (
            ("creator_messages_sent", 1),
            ("creator_replies_received", 1),
            ("authenticated_licenses_received", 1),
            ("owner_release_signed", True),
            ("licensing_authorized", True),
            ("media_download_authorized", True),
            ("video_editing_authorized", True),
            ("youtube_upload_authorized", True),
            ("youtube_publish_authorized", True),
            ("youtube_uploads", 1),
            ("real_youtube_api_requests", 1),
            ("all_proposals_unsent", False),
            ("all_owner_shortlist_selections_unapproved", False),
            ("all_creators_rightsholder_permissions_unverified", False),
            ("revenue_predictions_generated", True),
        ):
            doc = draft()
            doc[key] = value
            with self.subTest(key=key), self.assertRaises(PilotDenied):
                validate_owner_packet(doc, public_audit=a, watchlist=w,
                                      policy=p, registry=r, now=NOW)

    def test_a2_or_p3_policy_cannot_approve_prospect_by_waiver(self):
        w, a, p, r = inputs()
        p["creator_grants"] = "FORGED"
        with self.assertRaises((PilotDenied, ValueError)):
            compile_owner_pilot_packet(watchlist=w, public_audit=a,
                                      policy=p, registry=r, now=NOW)

    def test_fixed_public_audit_file_only_not_caller_injected_contract(self):
        audit = load_public_route_audit(AUDIT_FILE)
        self.assertEqual(audit["observed_at_utc"], "2026-11-14T00:00:00Z")
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "other.json"
            path.write_text(json.dumps(audit), encoding="utf-8")
            with self.assertRaises(PilotDenied):
                load_public_route_audit(path)
        with self.assertRaises(PilotDenied):
            load_public_route_audit(Path("/etc/passwd"))

    def test_closed_real_contact_action_never_sends(self):
        with self.assertRaises(PilotDenied):
            production_contact_license_or_clip()
        with self.assertRaises(PilotDenied):
            production_contact_license_or_clip(
                api_token="secret", requested_creator="ankitt_ps5",
                approve=True, upload=True
            )

    def test_deterministic_identity_provenance_not_legal_authentication(self):
        one, two = draft(), draft()
        self.assertEqual(one, two)
        self.assertEqual(len(one["source_watchlist_sha256"]), 64)
        self.assertEqual(len(one["public_route_audit_sha256"]), 64)
        self.assertFalse(one["owner_release_signed"])
        self.assertEqual(one["research_observed_utc"], "2026-11-14T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
