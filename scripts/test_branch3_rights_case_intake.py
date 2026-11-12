"""Clivox A2 rights-case intake adversarial tests: no self-approval."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import unittest

from scripts.branch3_discovery import build_report, mock_fixture
from scripts.branch3_rights_case_intake import (
    build_rights_cases, RightsIntakeBlocked, PENDING_CHECKS
)

NOW = datetime(2026,11,12,12,0,tzinfo=timezone.utc)
REVIEWED_AT = "2026-11-12T12:00:00Z"

def report():
    return build_report(
        mock_fixture(), category="gaming", mode="fixture",
        query="", now=NOW, fixture=True,
    )

class RightsIntakeTests(unittest.TestCase):
    def test_fixture_creates_only_pending_rights_cases(self):
        result=build_rights_cases(report(),generated_at_utc=REVIEWED_AT)
        self.assertEqual(result["stage"],"A2_RIGHTS_REVIEW_INTAKE_ONLY")
        self.assertEqual(result["pending_case_count"],2)
        self.assertTrue(result["is_synthetic_fixture"])
        self.assertTrue(result["cases_all_unverified"])
        self.assertEqual(result["creator_permission_grants_issued_by_this_workflow"],0)
        self.assertEqual(result["youtube_writes"],0)
        self.assertEqual(result["media_downloads"],0)
        self.assertFalse(result["release_enabled"])
        for c in result["cases"]:
            self.assertTrue(c["case_is_synthetic"])
            self.assertEqual(c["case_state"],"AWAITING_REAL_RIGHTS_HOLDER_VERIFICATION")
            self.assertTrue(all(x=="PENDING_HUMAN_VERIFICATION" for x in c["required_checks"].values()))
            self.assertEqual(len(c["required_checks"]),len(PENDING_CHECKS))
            for field in (
                "actual_grant_document_available","verified_creator_published_policy",
                "creator_permissions_registry_updated","contract_acceptance_done",
                "contract_assignment_reviewed_by_owner","media_acquisition_authorized",
                "edit_authorized","owner_clip_release_signed",
                "youtube_upload_authorized","youtube_publish_authorized"
            ):
                self.assertFalse(c[field])

    def test_case_ids_unique_source_integrity(self):
        r=report()
        out=build_rights_cases(r,generated_at_utc=REVIEWED_AT)
        self.assertEqual(len({c["case_id"] for c in out["cases"]}),2)
        self.assertEqual(len(out["source_report_sha256"]),64)
        changed=copy.deepcopy(r)
        changed["candidates"][0]["source_title"]="Changed after review"
        out2=build_rights_cases(changed,generated_at_utc=REVIEWED_AT)
        self.assertNotEqual(out["source_report_sha256"],out2["source_report_sha256"])

    def test_never_promote_discovery_flags_to_permission(self):
        bad={
            "permission_state":"VERIFIED",
            "rights_holder_identity_verified":True,
            "clivox_commercial_clipping_rights_verified":True,
            "underlying_game_music_guest_rights_cleared":True,
            "source_media_download_allowed":True,
            "segment_selected":True,
            "quote_verified":True,
            "ready_to_publish":True,
            "youtube_upload_authorized":True,
        }
        for key,val in bad.items():
            r=report();r["candidates"][0][key]=val
            with self.subTest(key=key),self.assertRaises(RightsIntakeBlocked):
                build_rights_cases(r,generated_at_utc=REVIEWED_AT)

    def test_reject_false_source_report_credentials(self):
        changes=[
            ("stage","A2_RIGHTS_VERIFIED"),
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("all_candidates_permission_unverified",False),
            ("release_or_media_acquisition_allowed",True),
            ("youtube_api_write_calls",1),
            ("mode","ids"),
            ("source_of_numbers","youtube_data_api_v3_public_statistics"),
        ]
        for key,val in changes:
            r=report();r[key]=val
            with self.subTest(key=key),self.assertRaises(RightsIntakeBlocked):
                build_rights_cases(r,generated_at_utc=REVIEWED_AT)

    def test_reject_tampered_video_id_and_url(self):
        for field,val in (
            ("source_video_id","NOT_AN_ID"),
            ("source_channel_id","NOT_A_CHANNEL"),
            ("source_url","https://attacker.example/a"),
            ("research_priority_score_0_to_100",101),
            ("source_title",""),
            ("sourcing_status","APPROVED_TO_CLIP"),
        ):
            r=report();r["candidates"][0][field]=val
            with self.subTest(field=field),self.assertRaises(RightsIntakeBlocked):
                build_rights_cases(r,generated_at_utc=REVIEWED_AT)

    def test_reject_duplicate_and_expansion(self):
        r=report()
        r["candidates"].append(copy.deepcopy(r["candidates"][0]))
        with self.assertRaises(RightsIntakeBlocked):
            build_rights_cases(r,generated_at_utc=REVIEWED_AT)
        r=report()
        r["candidates"]=r["candidates"]*20
        with self.assertRaises(RightsIntakeBlocked):
            build_rights_cases(r,generated_at_utc=REVIEWED_AT)

    def test_source_video_in_real_mode_remains_unverified(self):
        r=report()
        r["mode"]="ids"
        r["is_synthetic_fixture"]=False
        r["source_of_numbers"]="youtube_data_api_v3_public_statistics"
        out=build_rights_cases(r,generated_at_utc=REVIEWED_AT)
        self.assertFalse(out["is_synthetic_fixture"])
        self.assertTrue(out["cases_all_unverified"])
        self.assertTrue(all(not c["youtube_upload_authorized"] for c in out["cases"]))

if __name__=="__main__":
    unittest.main()
