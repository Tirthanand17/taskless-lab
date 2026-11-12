"""Clivox A2 rights cases: enforce no creator grant or release from JSON claims."""
from __future__ import annotations
import copy
import json
import unittest

from scripts.branch3_rights_case_review import (
    CASES,RightsCaseDenied,audit_folder,check_dossier,
)

def fixture():
    return json.loads((CASES/"clivox_ymh_ep347_case.json").read_text("utf-8"))

class A2RightsCaseTests(unittest.TestCase):
    def test_case_report_is_hold_not_approved(self):
        r=check_dossier(fixture())
        self.assertEqual(r["review_state"],"HOLD_FOR_HUMAN_RIGHTS_AND_CONTRACT_REVIEW")
        self.assertFalse(r["creator_license_verified_by_software"])
        self.assertFalse(r["media_download_allowed"])
        self.assertFalse(r["youtube_upload_allowed"])
        self.assertIn("creator_issued_grant_missing",r["missing_gates"])
        self.assertIn("public_invitation_is_not_a_license",r["missing_gates"])
        self.assertGreaterEqual(len(r["missing_gates"]),12)

    def test_repository_cases_are_all_held(self):
        r=audit_folder(CASES)
        self.assertGreaterEqual(r["cases_checked"],1)
        self.assertEqual(r["verified_licenses"],0)
        self.assertEqual(r["source_media_downloads"],0)
        self.assertEqual(r["youtube_writes"],0)
        self.assertFalse(r["publishing_enabled"])

    def test_cannot_forge_approval_status(self):
        for status in ("APPROVED","RIGHTS_VERIFIED","READY_FOR_PUBLISH","PUBLISHED"):
            d=fixture()
            d["case_status"]=status
            with self.subTest(status=status),self.assertRaises(RightsCaseDenied):
                check_dossier(d)

    def test_wrong_channel_and_source_denied(self):
        for field,value in (("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),("schema_version",2)):
            d=fixture();d[field]=value
            with self.subTest(field=field),self.assertRaises(RightsCaseDenied):
                check_dossier(d)
        for source_mutation in ({"original_video_id":"bad"},
                                {"original_video_url":"https://evil.example/a"},
                                {"original_creator_channel_id":"UCbad"},
                                {"time_in_ms":1200,"time_out_ms":900}):
            d=fixture();d["source"].update(source_mutation)
            with self.subTest(source_mutation=source_mutation),self.assertRaises(RightsCaseDenied):
                check_dossier(d)

    def test_download_and_upload_controls_must_be_off(self):
        for field in fixture()["controls"]:
            d=fixture();d["controls"][field]=True
            with self.subTest(field=field),self.assertRaises(RightsCaseDenied):
                check_dossier(d)

    def test_cannot_fabricate_human_signoff(self):
        for field,value in (("human_verifier_receipt","approved by AI"),
                            ("exact_media_owner_approval",True),
                            ("human_approver_identified",True)):
            d=fixture();d["review"][field]=value
            with self.subTest(field=field),self.assertRaises(RightsCaseDenied):
                check_dossier(d)

    def test_private_urls_and_evidence_not_committed(self):
        for url in ("http://whop.com/ymhclipping/","https://a:b@whop.com/ymhclipping/",
                    "https://evil.example/secret#token", "https://whop.com/ymhclipping/?key=123"):
            d=fixture();d["permission"]["public_invitation_url"]=url
            with self.subTest(url=url),self.assertRaises(RightsCaseDenied):
                check_dossier(d)
        d=fixture();d["permission"]["actual_grant_reference"]="my-private-agreement-token"
        with self.assertRaises(RightsCaseDenied):
            check_dossier(d)

    def test_checklist_boolean_and_field_checks(self):
        d=fixture();d["review"]["checklist"]["youtube_commercial_use"]="true"
        with self.assertRaises(RightsCaseDenied):
            check_dossier(d)
        d=fixture();d["review"]["checklist"].pop("underlying_music_audio_cleared")
        with self.assertRaises(RightsCaseDenied):
            check_dossier(d)

    def test_machine_does_not_certify_even_all_flags_true(self):
        d=fixture()
        for k in d["review"]["checklist"]:
            d["review"]["checklist"][k]=True
        for k in ("issuer_identity_verified","commercial_rights_confirmed","scope_confirmed","revocation_checked"):
            d["permission"][k]=True
        for k in d["underlying_rights"]:
            d["underlying_rights"][k]=True
        report=check_dossier(d)
        self.assertFalse(report["creator_license_verified_by_software"])
        self.assertFalse(report["youtube_upload_allowed"])
        self.assertEqual(report["review_state"],"HOLD_FOR_HUMAN_RIGHTS_AND_CONTRACT_REVIEW")
        self.assertIn("creator_issued_grant_missing",report["missing_gates"])

if __name__=="__main__":
    unittest.main()
