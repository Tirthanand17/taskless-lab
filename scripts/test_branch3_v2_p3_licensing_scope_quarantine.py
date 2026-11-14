"""CLIVOX V2 P3 legal-scope quarantine: only synthetic fixtures, zero grants.

Covers actual cross-module A1→A2 signed-review pending cases and P2
public-prospect data, without forging rights-holder crosslinks or contact.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import unittest

from scripts.branch3_discovery import build_report, mock_fixture
from scripts.branch3_rights_case_intake import build_rights_cases
from scripts.branch3_a2_review_receipt import POLICY, REGISTRY, read_json
from scripts.branch3_v2_creator_prospect_intake import DATA, load_watchlist
from scripts.branch3_v2_p3_licensing_scope_quarantine import (
    CHANNEL, CHECKS, LicensingScopeDenied, TERMS,
    build_p3_offline_handoff, compile_a2_synthetic_source_examples,
    compile_scope_packet, request_terms, review_checklist,
    source_case_reference, validate_unsigned_request
)

NOW = datetime(2026, 11, 14, 14, 32, tzinfo=timezone.utc)


def args() -> dict:
    return dict(
        watchlist=load_watchlist(DATA),
        policy=read_json(POLICY), registry=read_json(REGISTRY),
        now=NOW,
    )


def synthetic_a2() -> dict:
    discovery = build_report(
        mock_fixture(), category="gaming", mode="fixture",
        query="", now=NOW, fixture=True
    )
    return build_rights_cases(
        discovery, generated_at_utc="2026-11-14T14:32:00Z"
    )


class P3ScopeQuarantineTests(unittest.TestCase):
    def test_complete_p2_and_a2_synthetic_handoff_has_zero_rights(self):
        packet = build_p3_offline_handoff(**args())
        self.assertEqual(packet["channel_id"], CHANNEL)
        self.assertEqual(
            packet["stage"], "CLIVOX_V2_P3_CONTRACT_SCOPE_INTAKE_QUARANTINED"
        )
        self.assertEqual(packet["research_prospects_count"], 5)
        self.assertEqual(packet["unsigned_requests_generated"], 5)
        self.assertEqual(packet["rights_scope_checks_per_prospect"], len(CHECKS))
        self.assertGreaterEqual(len(CHECKS), 25)
        self.assertTrue(packet["questions_are_for_negotiation_only"])
        self.assertEqual(packet["actually_signed_contracts_received"], 0)
        self.assertEqual(packet["actual_creator_grants_verified"], 0)
        self.assertFalse(packet["creator_legal_identity_authenticated"])
        self.assertFalse(packet["creator_to_source_ownership_authenticated"])
        self.assertFalse(packet["real_reviewer_key_enrolled"])
        self.assertFalse(packet["real_revocation_head_pinned"])
        self.assertFalse(packet["private_legal_vault_approved"])
        self.assertFalse(packet["source_footage_delivered"])
        for flag in ("media_acquisition_authorized",
                     "clivox_youtube_upload_authorized",
                     "clivox_youtube_publish_authorized",
                     "owner_review_completed"):
            self.assertFalse(packet[flag])
        self.assertEqual(packet["youtube_api_calls"], 0)
        self.assertEqual(packet["creator_outreach_calls"], 0)
        self.assertEqual(packet["source_media_downloads"], 0)
        self.assertFalse(packet["public_output_contains_private_contracts"])
        self.assertRegex(packet["research_only_packet_sha256"],
                         r"^[0-9a-f]{64}$")
        for row in packet["prospect_scope_review_queue"]:
            self.assertIsNone(row["source_video_id"])
            self.assertIsNone(row["a2_pending_source_case_id"])
            self.assertIsNone(row["a2_pending_source_case_sha256"])
            self.assertFalse(row["source_video_rightsholder_link_verified"])
            self.assertFalse(row["creator_signed_grant_received"])
            self.assertFalse(row["creator_has_been_contacted"])
            self.assertFalse(row["creator_has_replied"])
            self.assertFalse(row["licensing_authorized"])
            self.assertFalse(row["source_media_acquisition_authorized"])
            self.assertFalse(row["editing_authorized"])
            self.assertFalse(row["youtube_upload_authorized"])
            self.assertFalse(row["youtube_publish_authorized"])
            self.assertEqual(
                row["rights_review_state"],
                "P3_SCOPE_QUESTIONS_ONLY_NOT_A_LICENSE"
            )
            self.assertEqual(row["unsigned_scope_request"], TERMS)
            self.assertEqual(set(row["checklist"]), set(CHECKS))
            self.assertTrue(all(
                v == "PENDING_HUMAN_AUTHENTICATION_NO_GRANT"
                for v in row["checklist"].values()
            ))
        cases = packet["separate_unlinked_synthetic_a2_cases"]
        self.assertEqual(cases["source_case_count"], 2)
        self.assertEqual(cases["real_source_licenses"], 0)
        self.assertTrue(cases["a1_synthetic"])
        self.assertEqual(
            cases["status"],
            "SYNTHETIC_A2_PENDING_CASES_UNLINKED_TO_ANY_REAL_CREATOR"
        )
        for case in cases["synthetic_cases_only"]:
            self.assertTrue(case["synthetic_fixture"])
            self.assertIsNone(case["potential_creator_prospect_id"])
            self.assertFalse(case["actual_source_to_prospect_ownership_verified"])
            self.assertFalse(case["source_license_exists"])
            self.assertFalse(case["ready_for_media_acquisition"])
            self.assertRegex(case["a2_pending_case_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("contact_email", json.dumps(packet))
        self.assertNotIn("creator_contract_text", json.dumps(packet))
        self.assertNotIn("research_priority_score_0_to_100", json.dumps(packet))

    def test_determinism_and_no_input_mutation(self):
        first = args()
        untouched = copy.deepcopy(first)
        a = build_p3_offline_handoff(**first)
        b = build_p3_offline_handoff(**args())
        self.assertEqual(a, b)
        self.assertEqual(first, untouched)
        self.assertEqual(len(a["research_only_packet_sha256"]), 64)

    def test_request_is_a_request_and_cannot_be_fake_agreement(self):
        base=request_terms()
        self.assertEqual(validate_unsigned_request(base), TERMS)
        for k, v in (
            ("ads_monetization_requested", False),
            ("commercial_youtube_redistribution_requested", False),
            ("number_of_private_pilot_clips", True),
            ("number_of_private_pilot_clips", 200),
            ("requested_term_days", 0),
            ("requested_channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("request_only_not_agreement", False),
            ("no_terms_accepted", False),
            ("no_license_granted", False),
            ("requested_source_delivery_route", "UNRESTRICTED_YOUTUBE_DOWNLOAD"),
            ("creator_grant_evidence_sha256", "a"*64),
            ("owner_approved", True),
            ("contact_email", "private@example.org"),
        ):
            draft=copy.deepcopy(base)
            draft[k]=v
            with self.subTest(key=k,value=v),self.assertRaises(LicensingScopeDenied):
                validate_unsigned_request(draft)
        draft=copy.deepcopy(base)
        del draft["requested_creator_final_review"]
        with self.assertRaises(LicensingScopeDenied):
            validate_unsigned_request(draft)

    def test_upstream_a2_real_policy_and_registry_cannot_be_overridden(self):
        cases=[
            ("policy","real_human_reviewer_key_enrolled",True),
            ("policy","durable_revocation_ledger",True),
            ("policy","actual_contract_storage_approved",True),
            ("policy","source_media_download_enabled",True),
            ("policy","real_authentic_creator_grants",1),
            ("registry","creators",[{"creator_id":"fake_creator"}]),
        ]
        for kind, field, value in cases:
            params=args()
            params[kind][field]=value
            with self.subTest(kind=kind,field=field),self.assertRaises(LicensingScopeDenied):
                compile_scope_packet(**params)

    def test_p2_forged_identity_contact_or_rights_fails_closed(self):
        cases=(
            ("creator_identity_authenticated",True),
            ("creator_rights_verified",True),
            ("human_owner_shortlist_approved",True),
            ("third_party_media_acquisition_allowed",True),
            ("youtube_upload_authorized",True),
            ("creator_contacts_sent",1),
        )
        for field,value in cases:
            params=args()
            params["watchlist"][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                compile_scope_packet(**params)
        params=args()
        params["watchlist"]["prospects"][0]["outreach_state"]="CONTACTED"
        with self.assertRaises(ValueError):
            compile_scope_packet(**params)
        params=args()
        params["watchlist"]["prospects"][0]["rights_state"]="VERIFIED"
        with self.assertRaises(ValueError):
            compile_scope_packet(**params)

    def test_wrong_channel_stale_watchlist_or_bad_clock_is_denied(self):
        params=args()
        params["watchlist"]["channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
        with self.assertRaises(ValueError):
            compile_scope_packet(**params)
        params=args()
        params["watchlist"]["research_date_utc"]="2026-09-01T00:00:00Z"
        with self.assertRaises(ValueError):
            compile_scope_packet(**params)
        params=args()
        params["now"]=datetime(2026,11,14,14,32)
        with self.assertRaises(LicensingScopeDenied):
            compile_scope_packet(**params)

    def test_legal_scope_unsigned_term_mutations_cannot_authorize(self):
        params=args()
        terms=request_terms()
        terms["requested_channel_id"]="UC"+"z"*22
        params["unsigned_terms"]=terms
        with self.assertRaises(LicensingScopeDenied):
            compile_scope_packet(**params)
        params=args()
        params["unsigned_terms"]={**request_terms(),
                                  "license_granted":True}
        with self.assertRaises(LicensingScopeDenied):
            compile_scope_packet(**params)

    def test_a2_case_exact_digest_and_missing_or_forged_review_block(self):
        fixture=synthetic_a2()
        item=fixture["cases"][0]
        safe=source_case_reference(item)
        self.assertEqual(safe["a2_case_id"], item["case_id"])
        self.assertIsNone(safe["potential_creator_prospect_id"])
        for key,val in (
            ("case_state","RIGHTS_VERIFIED"),
            ("source_video_id","INVALID"),
            ("source_url","https://fake.example/"),
            ("case_is_synthetic","false"),
            ("human_rights_reviewer_assigned",True),
            ("media_acquisition_authorized",True),
            ("youtube_publish_authorized",True),
            ("permission_evidence_sha256","a"*64),
        ):
            tampered=copy.deepcopy(item)
            tampered[key]=val
            with self.subTest(field=key),self.assertRaises(LicensingScopeDenied):
                source_case_reference(tampered)
        self.assertNotIn("creator",safe["source_video_id"].lower())

    def test_real_license_still_zero_even_with_valid_pending_case(self):
        refs=compile_a2_synthetic_source_examples(now=NOW)
        self.assertEqual(refs["real_source_licenses"],0)
        self.assertEqual(refs["source_case_count"],2)
        for row in refs["synthetic_cases_only"]:
            self.assertFalse(row["ready_for_media_acquisition"])
            self.assertFalse(row["source_authority_document_verified"])
            self.assertIsNone(row["potential_creator_prospect_id"])


if __name__ == "__main__":
    unittest.main()
