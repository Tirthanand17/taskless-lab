"""No-network B3d4b tests for exact signed TTS and video storyboard contracts.

Keys and scripts here are disposable technical fixtures. These tests do NOT
authorize human/rights/fact approval, a provider account or YouTube publishing.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import unittest

from autopilot.test_script_to_preview_bridge import staged_plan
from autopilot.test_script_continuity_gate import signed_fixture
from autopilot.script_to_preview_bridge import build_signed_preview_plan
from autopilot.signed_narrated_cloud_pack import (
    NarratedPackError, STATUS, VOICE_FOR_SLOT, validate_plan,
    produce_signed_narrated_demo,
)


class SignedNarratedCloudPackTests(unittest.TestCase):
    def setUp(self):
        self.plan=staged_plan(0)

    def test_three_distinct_voice_styles_and_no_real_approval(self):
        self.assertEqual(len(set(VOICE_FOR_SLOT.values())),3)
        seen=set()
        for index, kind in enumerate(("short","long","short")):
            with self.subTest(index=index):
                plan=staged_plan(index)
                prepared=validate_plan(plan)
                self.assertEqual(prepared.episode.kind,kind)
                self.assertEqual(prepared.episode.voice,VOICE_FOR_SLOT[plan["release_slot"]])
                self.assertEqual(len(prepared.episode.scenes),plan["scene_count"])
                self.assertEqual(
                    "".join(x.narration for x in prepared.episode.scenes),
                    "".join(row["raw_narration"] for row in plan["scene_plan"]),
                )
                self.assertEqual(prepared.script_manifest_sha256,plan["script_manifest_sha256"])
                self.assertEqual(prepared.original_script_sha256,plan["full_spoken_narration_sha256"])
                self.assertTrue(len(set(prepared.scene_ids))==plan["scene_count"])
                seen.add(prepared.script_manifest_sha256)
                self.assertFalse(plan["rights_approved"])
                self.assertFalse(plan["release_authorized"])
                self.assertFalse(plan["youtube_upload_enabled"])
        self.assertEqual(len(seen),3)

    def test_duplicate_or_reordered_scenes_denied(self):
        for mutation in ("duplicate","reverse","misindexed"):
            with self.subTest(mutation=mutation):
                plan=deepcopy(self.plan)
                if mutation=="duplicate":
                    plan["scene_plan"][1]=deepcopy(plan["scene_plan"][0])
                elif mutation=="reverse":
                    plan["scene_plan"].reverse()
                else:
                    plan["scene_plan"][2]["scene_index"]=4
                with self.assertRaises(NarratedPackError):
                    validate_plan(plan)

    def test_mutated_original_spoken_text_denied(self):
        for field,value in (
            ("raw_narration","Injected fake statement."),
            ("narration_sha256","a"*64),
            ("narration_start_char",True),
            ("narration_end_char",-100),
        ):
            plan=deepcopy(self.plan)
            plan["scene_plan"][0][field]=value
            with self.subTest(field=field),self.assertRaises(NarratedPackError):
                validate_plan(plan)

    def test_model_beat_mutation_or_fake_report_denied(self):
        for field,value in (
            ("visual_direction_unverified","The company earned 200 billion in 2026"),
            ("visual_direction_sha256","b"*64),
            ("scene_id","z"*24),
            ("source_assertions_fact_checked",True),
            ("caption_accuracy_verified",True),
            ("actual_visual_production_matches_direction",True),
        ):
            plan=deepcopy(self.plan)
            plan["scene_plan"][0][field]=value
            with self.subTest(field=field), self.assertRaises(NarratedPackError):
                validate_plan(plan)

    def test_all_privilege_escalation_attempts_denied(self):
        for flag in (
            "release_authorized","youtube_upload_enabled","youtube_schedule_enabled",
            "source_fact_review_complete","human_creative_review_complete",
            "rights_approved","model_provider_live_inference_used",
            "external_review_ledger_connected","full_length_final_narration_or_video_exists",
        ):
            plan=dict(self.plan)
            plan[flag]=True
            with self.subTest(flag=flag),self.assertRaises(NarratedPackError):
                validate_plan(plan)

    def test_short_can_never_be_used_as_long_or_different_slot(self):
        for field,value in (
            ("format","long"),("release_slot","short_pm"),
            ("episode_id","fm_20261105_long"),
            ("episode_id","fm_20261105_short_pm"),
            ("episode_id","untrusted_script_without_date"),
        ):
            plan=deepcopy(self.plan)
            plan[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(NarratedPackError):
                validate_plan(plan)

    def test_episode_count_and_hash_checks(self):
        for field,value in (
            ("scene_count",50),("script_manifest_sha256","a"),
            ("full_spoken_narration_sha256","a"*64),
            ("status","APPROVED_FOR_PUBLISHING"),
        ):
            plan=deepcopy(self.plan)
            plan[field]=value
            with self.subTest(field=field),self.assertRaises(NarratedPackError):
                validate_plan(plan)

    def test_production_requires_empty_ephemeral_directory_before_media(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        plan=staged_plan(0)
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"preexisting.mp4").write_bytes(b"do not overwrite")
            with self.assertRaises(NarratedPackError):
                produce_signed_narrated_demo(plan,object(),folder)
            self.assertEqual((folder/"preexisting.mp4").read_bytes(),b"do not overwrite")

    def test_real_script_must_be_externally_signed_before_previews(self):
        item=list(signed_fixture(0))
        item[0]["visual_beats"][0]="A forged fact and invented visual milestone."
        with self.assertRaises(ValueError):
            build_signed_preview_plan(
                item[0],item[1],item[2],
                seal=item[5],anchor_manifest_sha256=item[3],registry=item[4],
                excluded_creator_and_publisher_ids=frozenset(("creator_agent","publisher_service")),
            )

    def test_fixed_source_approved_content_flags_absent(self):
        plan=self.plan
        self.assertNotIn("human_editorial_approved",plan)
        self.assertEqual(STATUS,"REAL_KOKORO_SIGNED_SCRIPT_TECHNICAL_DEMO_UNREVIEWED_NO_PUBLISH")
        self.assertFalse(plan["source_fact_review_complete"])
        self.assertFalse(plan["rights_approved"])


if __name__=="__main__":
    unittest.main()
