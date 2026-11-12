"""Clivox integrated-rehearsal adversarial tests without rendering/video upload."""
from __future__ import annotations
import copy
import hashlib
import json
import tempfile
from pathlib import Path
import unittest

from scripts.branch3_a4_editorial import check_script, EditorialHold
from scripts.branch3_a5_render_original_demo import visual_script_srt
from scripts.branch3_a5_media_qa import check_metadata, MediaQARejected
from scripts.branch3_a6_signed_release import FIXTURE as RELEASE, POLICY as RELEASE_POLICY, ReleaseBlocked
from scripts.branch3_a8_private_first_dryrun import PLAN, LEDGER, DryRunBlocked
from scripts.test_branch3_a5_media import fixture, baseline_manifest, baseline_probe
from scripts.branch3_integrated_rehearsal import (
    RehearsalDenied, validate_handoff, inspect_directory
)

def valid_inputs():
    blueprint=fixture()
    with tempfile.TemporaryDirectory() as temp:
        text=Path(temp)/"captions.srt"
        visual_script_srt(blueprint["beats"],text)
        srt=text.read_text("utf-8")
    manifest=baseline_manifest()
    manifest.update({
        "video_name":"clivox-original-only-a5-demo.mp4",
        "srt_name":"on-screen-editorial-script-not-dialogue.srt",
        "concept_id":blueprint["proposal_id"],
        "source_blueprint_sha256":check_script(blueprint)["editorial_plan_sha256"],
        "scene_card_names":[f"scene-{n:02}.png" for n in range(5)],
        "video_sha256":hashlib.sha256(b"fake-test-only-bytes").hexdigest(),
        "srt_sha256":hashlib.sha256(srt.encode()).hexdigest(),
        "video_size_bytes":123456,
    })
    probe=baseline_probe()
    qa=check_metadata(probe,manifest,srt)
    return {
        "blueprint":blueprint,"manifest":manifest,"qa":qa,
        "video_hash":manifest["video_sha256"],
        "video_bytes":manifest["video_size_bytes"],
        "srt_hash":manifest["srt_sha256"],
        "probe":probe,"srt_text":srt,
        "release":json.loads(RELEASE.read_text("utf-8")),
        "release_policy":json.loads(RELEASE_POLICY.read_text("utf-8")),
        "schedule":json.loads(PLAN.read_text("utf-8")),
        "ledger":json.loads(LEDGER.read_text("utf-8")),
    }

class IntegratedRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.inputs=valid_inputs()

    def test_valid_synthetic_all_handoffs_still_quarantined(self):
        r=validate_handoff(**self.inputs)
        self.assertEqual(len(r["stages_verified"]),4)
        self.assertEqual(r["channel_id"],"UCfPEvy0SefE_5nNlYlY_CyQ")
        self.assertTrue(r["synthetic_tones_not_voiceover"])
        self.assertEqual(r["result"],"TECHNICALLY_CHECKED_ORIGINAL_DEMO_QUARANTINED")
        self.assertFalse(r["creator_license_verified"])
        self.assertFalse(r["real_licensed_pilot_completed"])
        self.assertFalse(r["real_owner_video_signature_present"])
        self.assertFalse(r["youtube_upload_authorized"])
        self.assertFalse(r["youtube_schedule_authorized"])
        self.assertFalse(r["youtube_publish_authorized"])
        self.assertEqual(r["google_oauth_or_youtube_network_calls"],0)

    def test_no_forged_source_quote_or_license(self):
        for field in ("creator_grant_verified","source_context_checked","exact_asset_signed"):
            data=valid_inputs()
            data["blueprint"]["release_locks"][field]=True
            with self.subTest(field=field),self.assertRaises(EditorialHold):
                validate_handoff(**data)
        data=valid_inputs()
        data["blueprint"]["beats"][2]["source_quotation"]="Never verified"
        with self.assertRaises(EditorialHold):
            validate_handoff(**data)

    def test_exact_media_and_caption_hashes_and_size_must_match(self):
        for key,change in (
            ("video_hash","0"*64),("srt_hash","1"*64),
            ("video_bytes",123457),
        ):
            data=valid_inputs()
            data[key]=change
            with self.subTest(key=key),self.assertRaises(RehearsalDenied):
                validate_handoff(**data)

    def test_changed_blueprint_or_manifest_provenance_denied(self):
        for field,value in (
            ("source_blueprint_sha256","a"*64),
            ("concept_id","clivox_wrong_video"),
            ("video_name","../../stolen-source.mp4"),
            ("scene_card_names",["scene-00.png"]),
        ):
            data=valid_inputs()
            data["manifest"][field]=value
            with self.subTest(field=field),self.assertRaises(RehearsalDenied):
                validate_handoff(**data)
        data=valid_inputs()
        data["blueprint"]["creative_intent"]["story_thesis"]="New unrelated draft"
        with self.assertRaises(RehearsalDenied):
            validate_handoff(**data)

    def test_forged_technical_qa_or_youtube_release_denied(self):
        for key,value in (
            ("synthetic_video_technical_checks_passed",False),
            ("ready_to_publish",True),
            ("youtube_upload_authorized",True),
            ("resolution","1080x1920"),
        ):
            data=valid_inputs()
            data["qa"][key]=value
            with self.subTest(key=key),self.assertRaises(RehearsalDenied):
                validate_handoff(**data)
        data=valid_inputs()
        data["manifest"]["ready_to_upload"]=True
        with self.assertRaises(MediaQARejected):
            validate_handoff(**data)

    def test_a6_quarantine_and_a8_no_upload_must_hold(self):
        data=valid_inputs()
        data["release"]["signature"]["owner_signed"]=True
        with self.assertRaises(ReleaseBlocked):
            validate_handoff(**data)
        data=valid_inputs()
        data["release_policy"]["youtube_write_enabled"]=True
        with self.assertRaises(ReleaseBlocked):
            validate_handoff(**data)
        data=valid_inputs()
        data["schedule"]["production_actions"]["video_insert"]=True
        with self.assertRaises(DryRunBlocked):
            validate_handoff(**data)
        data=valid_inputs()
        data["ledger"]["remote_video_ids"]=["ABCDEFGHIJK"]
        with self.assertRaises(DryRunBlocked):
            validate_handoff(**data)

    def test_mismatched_release_and_schedule_denied(self):
        data=valid_inputs()
        data["schedule"]["source_release_id"]="clivox_wrong_synthetic_demo"
        with self.assertRaises(RehearsalDenied):
            validate_handoff(**data)

    def test_demo_media_directory_must_be_real_not_repo_or_symlink(self):
        with self.assertRaises(RehearsalDenied):
            inspect_directory(Path("relative/path"))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RehearsalDenied):
                inspect_directory(Path(tmp))  # no manifest / MP4
            fake=Path(tmp)/"dirlink"
            fake.symlink_to(Path(tmp),target_is_directory=True)
            with self.assertRaises(RehearsalDenied):
                inspect_directory(fake)

if __name__=="__main__":
    unittest.main()
