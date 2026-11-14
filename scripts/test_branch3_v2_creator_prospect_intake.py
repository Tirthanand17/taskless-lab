"""Adversarial zero-network tests of CLIVOX V2 P2 creator prospect research.

No contact sent, rights granted, source footage, API key, YouTube operations
or private contact details are present in the fixture or generated packet.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from scripts.branch3_v2_creator_prospect_intake import (
    CHANNEL, DATA, PROJECT_ROOT, ProspectDenied, compile_owner_research_packet,
    load_watchlist, proposal, public_page, validate_watchlist
)

NOW = datetime(2026, 11, 14, 14, 32, tzinfo=timezone.utc)


class CreatorProspectTests(unittest.TestCase):
    def setUp(self):
        self.payload = load_watchlist(DATA)

    def test_real_public_leads_are_only_research_with_unsent_drafts(self):
        report = compile_owner_research_packet(self.payload, now=NOW)
        self.assertEqual(report["channel_id"], CHANNEL)
        self.assertEqual(report["prospect_count"], 5)
        self.assertEqual(report["potential_partner_count"], 4)
        self.assertEqual(report["famous_format_research_only_count"], 1)
        self.assertEqual(report["real_creator_contacts_sent"], 0)
        self.assertEqual(report["real_creator_replies_received"], 0)
        self.assertEqual(report["creator_grants_verified"], 0)
        self.assertEqual(report["private_media_sources_delivered"], 0)
        self.assertEqual(report["google_or_youtube_api_calls"], 0)
        self.assertTrue(report["all_proposals_unsent"])
        self.assertTrue(report["all_creator_identity_and_licensing_unverified"])
        self.assertTrue(report["no_third_party_media_download"])
        self.assertTrue(report["ranking_is_not_based_on_api_views_or_likes"])
        for flag in ("human_shortlist_approved",
                     "licensed_source_media_access_authorized",
                     "youtube_upload_authorized", "youtube_schedule_authorized",
                     "youtube_publish_authorized"):
            self.assertIs(report[flag], False, flag)
        self.assertRegex(report["research_input_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(len(report["review_queue"]), 5)
        self.assertEqual([x["id"] for x in report["review_queue"]],
                         sorted(x["id"] for x in report["review_queue"]))
        for p in report["review_queue"]:
            self.assertFalse(p["actual_creator_authority_verified"])
            self.assertFalse(p["actual_business_route_deliverability_verified"])
            self.assertFalse(p["actual_creator_contacted"])
            self.assertFalse(p["creator_replied_or_agreed"])
            self.assertFalse(p["commercial_redistribution_and_monetization_granted"])
            self.assertFalse(p["game_music_guest_rights_verified"])
            self.assertFalse(p["source_file_delivered"])
            self.assertFalse(p["youtube_upload_authorized"])
            self.assertEqual(p["owner_shortlist_review_state"],
                             "PENDING_REAL_HUMAN_REVIEW")
            self.assertEqual(p["next_action"],
                             "OWNER_VERIFY_CREATOR_IDENTITY_AND_BUSINESS_ROUTE")
            q=p["proposed_outreach"]
            self.assertTrue(q["subject"].startswith("CLIVOX: licensed"))
            self.assertIn("Nothing would be published", q["body"])
            self.assertIn("commercial YouTube redistribution", q["body"])
            self.assertIsNone(q["recipient_address"])
            self.assertEqual(q["state"],
                             "UNSENT_DRAFT_FOR_OWNER_APPROVAL_ONLY")
            self.assertFalse(q["sent"])
            self.assertFalse(q["license_verified"])
            self.assertFalse(q["publishing_authorized"])
            self.assertFalse(q["media_download_authorized"])
        self.assertNotIn("research_priority_score_0_to_100",
                         json.dumps(report))
        self.assertNotIn("source_score", json.dumps(report))

    def test_determinism_and_pure_function_no_mutation(self):
        data = deepcopy(self.payload)
        one = compile_owner_research_packet(data, now=NOW)
        two = compile_owner_research_packet(deepcopy(data), now=NOW)
        self.assertEqual(one, two)
        self.assertEqual(data, self.payload)
        self.assertEqual(one["research_input_sha256"],
                         two["research_input_sha256"])

    def test_tampered_source_evidence_changes_sha_without_grant(self):
        one=compile_owner_research_packet(self.payload, now=NOW)
        d=deepcopy(self.payload)
        d["prospects"][0]["evidence_note"]+=" Human re-check still required."
        two=compile_owner_research_packet(d, now=NOW)
        self.assertNotEqual(one["research_input_sha256"],
                            two["research_input_sha256"])
        self.assertEqual(two["creator_grants_verified"], 0)

    def test_schema_rejects_approval_forgery_and_wrong_channel(self):
        scenarios = (
            ("channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("state", "RIGHTS_VERIFIED"),
            ("creator_identity_authenticated", True),
            ("creator_rights_verified", True),
            ("human_owner_shortlist_approved", True),
            ("public_creator_business_contacts_only", False),
            ("third_party_media_acquisition_allowed", True),
            ("youtube_upload_authorized", True),
            ("creator_contacts_sent", 1),
            ("api_key", "SECRET"),
        )
        for key, value in scenarios:
            d=deepcopy(self.payload)
            d[key]=value
            with self.subTest(field=key),self.assertRaises(ProspectDenied):
                validate_watchlist(d,now=NOW)

    def test_reject_any_row_level_untrusted_approval_or_metric(self):
        changes = (
            ("license_granted", True),
            ("owner_approved", True),
            ("contact_sent", True),
            ("media_acquisition_authorized", True),
            ("youtube_api_stats", {"views": 111}),
            ("virality_score", 90),
            ("subscriber_count", 100),
            ("outreach_state", "CONTACTED"),
            ("rights_state", "VERIFIED"),
            ("priority_group", "RIGHTS_APPROVED"),
            ("lane", "restricted_footage"),
            ("observed_public_business_route", "VERIFIED_CONTRACT"),
        )
        for k,v in changes:
            d=deepcopy(self.payload)
            d["prospects"][0][k]=v
            with self.subTest(field=k),self.assertRaises(ProspectDenied):
                compile_owner_research_packet(d,now=NOW)

    def test_reject_contact_private_data_anywhere(self):
        cases=(
            ("evidence_note","Direct contact person@example.org"),
            ("self_described_content","Private number +1 415 555 1212"),
            ("display_name","access_token=SECRET"),
            ("public_business_page","https://ankitt.com/?email=private"),
            ("public_business_page","https://ankitt.com/contact#inbox"),
            ("public_business_page","https://user:password@ankitt.com/"),
            ("public_business_page","http://ankitt.com/"),
            ("public_creator_page","https://ankitt.com.secrets.example/"),
            ("public_creator_page","https://ankitt.com/video.mp4"),
            ("public_creator_page","https://ankitt.com/../secrets"),
        )
        for k,v in cases:
            d=deepcopy(self.payload)
            d["prospects"][0][k]=v
            with self.subTest(field=k),self.assertRaises(ProspectDenied):
                validate_watchlist(d,now=NOW)

    def test_creator_and_business_page_must_match_domain(self):
        d=deepcopy(self.payload)
        d["prospects"][0]["public_business_page"]="https://caseoh.com/pages/about-me"
        with self.assertRaises(ProspectDenied):
            validate_watchlist(d,now=NOW)

    def test_reject_duplicate_source_or_ids(self):
        cases = ("id", "public_creator_page")
        for key in cases:
            d=deepcopy(self.payload)
            d["prospects"][1][key]=d["prospects"][0][key]
            with self.subTest(key=key),self.assertRaises(ProspectDenied):
                validate_watchlist(d,now=NOW)

    def test_reject_bad_counts_and_input_dates(self):
        cases=(
            ("2026-11-15T00:00:00Z", NOW),
            ("2026-10-01T00:00:00Z", NOW),
            ("2026-11-14T00:00:00+00:00", NOW),
        )
        for date, now in cases:
            d=deepcopy(self.payload)
            d["research_date_utc"]=date
            with self.subTest(date=date),self.assertRaises(ProspectDenied):
                validate_watchlist(d,now=now)
        for count in (0,2,11):
            d=deepcopy(self.payload)
            d["prospects"]=d["prospects"][:count]
            if count == 11:
                d["prospects"] = d["prospects"] * 6
            with self.subTest(count=count),self.assertRaises(ProspectDenied):
                validate_watchlist(d,now=NOW)

    def test_no_hidden_download_or_network_in_public_page_validation(self):
        self.assertEqual(public_page("https://ankitt.com/"),
                         "https://ankitt.com/")
        for url in ("ftp://ankitt.com/", "https://127.0.0.1/",
                    "https://example.org/", "https://ankitt.com:443/",
                    "https://ankitt.com/f.mp4", "https://ankitt.com/?token=x",
                    "https://ankitt.com\\@evil.test/"):
            with self.subTest(url=url),self.assertRaises(ProspectDenied):
                public_page(url)

    def test_no_outreach_from_generator(self):
        message=proposal("Eggmilk",lane="gaming_livestream")
        self.assertEqual(message["sent"],False)
        self.assertIsNone(message["recipient_address"])
        self.assertIn("rights",message["body"])
        self.assertIn("private review copies",message["body"])
        self.assertFalse(message["actual_creator_consent_received"])
        for kind in ("unknown","copyright_bypass"):
            with self.assertRaises(ProspectDenied):
                proposal("Test",lane=kind)

    def test_input_rejects_symlinks_and_non_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            data=root/"p2.json"
            data.write_text("not-json",encoding="utf-8")
            with self.assertRaises(ProspectDenied):
                load_watchlist(data)
            self.assertEqual(load_watchlist(DATA),self.payload)
            alias=root/"alias.json"
            alias.symlink_to(DATA)
            with self.assertRaises(ProspectDenied):
                load_watchlist(alias)


if __name__ == "__main__":
    unittest.main()
