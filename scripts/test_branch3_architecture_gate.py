"""Adversarial tests for the Clivox architecture design-only safety contract."""
from __future__ import annotations
import copy
from datetime import datetime,timezone,timedelta
import json
import unittest

from scripts.branch3_architecture_gate import (
    ARCH,GRAPH,SCHEMA,EXAMPLE,CHANNEL,PERMS,ArchitectureBlocked,
    data,validate_architecture,preview_schedule,preview_state_transition,
    assert_no_api_write_allowed,
)

NOW=datetime(2026,11,12,8,0,0,tzinfo=timezone.utc)

class ClivoxArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.c=data(ARCH)
        self.g=data(GRAPH)
        self.sch=data(SCHEMA)
        self.j=data(EXAMPLE)
        self.ch=data(CHANNEL)
        self.perms=data(PERMS)

    def valid(self):
        validate_architecture(self.c,self.g,self.sch,self.j,self.ch,self.perms)

    def test_valid_design_while_no_rights_granted(self):
        self.valid()
        self.assertEqual(self.c["architecture_state"],"DESIGN_ONLY")

    def test_wrong_account_and_paused_branch_changes(self):
        for field,value in (
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("handle","@FlowMinuteLab"),
        ):
            self.c=data(ARCH)
            self.c[field]=value
            with self.subTest(field=field),self.assertRaises(ArchitectureBlocked):
                self.valid()
        self.c=data(ARCH)
        self.c["isolation"]["branch1_paused"]=False
        with self.assertRaises(ArchitectureBlocked):
            self.valid()

    def test_fail_closed_if_any_write_or_source_download_enabled(self):
        for field in (
            "auto_download_enabled","auto_publish_enabled","api_write_calls_enabled",
            "global_upload_enabled","owner_signing_implemented",
            "github_environment_protection_configured",
        ):
            self.c=data(ARCH)
            self.c["safety"][field]=True
            with self.subTest(field=field),self.assertRaises(ArchitectureBlocked):
                self.valid()

    def test_reject_media_in_public_repo(self):
        for field in ("public_repo_contains_copyrighted_raw_video","raw_license_documents_public","private_media_escrow_enabled"):
            self.c=data(ARCH)
            self.c["storage"][field]=True
            with self.subTest(field=field),self.assertRaises(ArchitectureBlocked):
                self.valid()

    def test_approval_forgery_in_example_job(self):
        mutations=[
            ("rights","permission_state","verified"),
            ("rights","commercial_youtube_licensed",True),
            ("rights","evidence_digest_sha256","a"*64),
            ("release","owner_signed",True),
            ("release","release_enabled",True),
            ("media","qa_passed",True),
            ("media","file_in_public_repo",True),
            ("youtube","privacy","public"),
            ("youtube","video_id","ABCDEFGHIJK"),
            ("youtube","readback_verified",True),
            ("editorial","original_story_approved",True),
            ("analytics","engaged_views",1000000),
        ]
        for section,field,value in mutations:
            self.j=data(EXAMPLE)
            self.j[section][field]=value
            with self.subTest(section=section,field=field),self.assertRaises(ArchitectureBlocked):
                self.valid()

    def test_missing_creator_rights(self):
        self.perms["creators"]=[{"creator_id":"unsupported"}]
        with self.assertRaises(ArchitectureBlocked):
            self.valid()

    def test_state_graph_and_protected_transition(self):
        self.valid()
        plan=preview_state_transition(self.g,"DISCOVERED","RIGHTS_PENDING")
        self.assertEqual(plan["mode"],"PLAN_ONLY_NO_SIDE_EFFECTS")
        self.assertFalse(plan["release_authorized"])
        for target in ("RIGHTS_VERIFIED","OWNER_SIGNED","PRIVATE_UPLOADED","SCHEDULED","PUBLISHED"):
            with self.subTest(target=target),self.assertRaises(ArchitectureBlocked):
                preview_state_transition(self.g,"RIGHTS_PENDING" if target=="RIGHTS_VERIFIED" else {
                    "OWNER_SIGNED":"QA_PASSED","PRIVATE_UPLOADED":"OWNER_SIGNED",
                    "SCHEDULED":"PRIVATE_UPLOADED","PUBLISHED":"SCHEDULED"
                }[target],target)
        with self.assertRaises(ArchitectureBlocked):
            preview_state_transition(self.g,"DISCOVERED","SCHEDULED")

    def test_protected_graph_must_not_allow_self_loop(self):
        self.g["transitions"]["DISCOVERED"].append("DISCOVERED")
        with self.assertRaises(ArchitectureBlocked):
            self.valid()

    def test_future_utc_preview_not_publication_permission(self):
        report=preview_schedule("2026-11-12T09:00:00Z",now=NOW,
                                privacy="private",channel_id="UCfPEvy0SefE_5nNlYlY_CyQ")
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["youtube_upload_authorized"])
        self.assertEqual(report["mode"],"PLAN_ONLY_NO_YOUTUBE_CALL")

    def test_reject_past_timestamps_and_non_utc_time(self):
        for time_s in (
            "2026-11-12T07:59:59Z","2026-11-12T08:20:00Z",
            "2026-11-12T08:00:00Z",
            "2026-11-12T13:40:00+05:30",
            "2026-11-12T08:59:00",
            "not-a-date",
        ):
            with self.subTest(time_s=time_s),self.assertRaises(ArchitectureBlocked):
                preview_schedule(time_s,now=NOW,privacy="private",channel_id="UCfPEvy0SefE_5nNlYlY_CyQ")
        with self.assertRaises(ArchitectureBlocked):
            preview_schedule("2026-11-12T09:00:00Z",now=NOW,privacy="public",
                             channel_id="UCfPEvy0SefE_5nNlYlY_CyQ")
        with self.assertRaises(ArchitectureBlocked):
            preview_schedule("2026-11-12T09:00:00Z",now=NOW,privacy="private",
                             channel_id="UCCcL9Q_jqVq6LJmnYUSAFZA")
        with self.assertRaises(ArchitectureBlocked):
            preview_schedule("2026-11-12T09:00:00Z",now=datetime(2026,11,12,8,0),
                             privacy="private",channel_id="UCfPEvy0SefE_5nNlYlY_CyQ")

    def test_real_api_write_never_implemented(self):
        with self.assertRaises(ArchitectureBlocked):
            assert_no_api_write_allowed(self.c)

    def test_no_fabricated_youtube_data(self):
        self.j["youtube"]["publish_at_utc"]="2026-11-12T09:00:00Z"
        with self.assertRaises(ArchitectureBlocked):
            self.valid()

if __name__=="__main__":
    unittest.main()

