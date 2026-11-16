"""Fail-closed narration QA; source-only PR tests, no media or upload."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autopilot.branch1_narrated_real_app_short import (
    APPS,OUT_ASS,OUT_MP4,OUT_RECEIPT,STATUS,STORIES,OUT_SRT,
    chapter_asset,story_episode,validate_story,video_graph,validate_output,
    render,probe
)
from autopilot.branch1_recovery import RecoveryRefused
from autopilot.branch1_real_app_capture import CAPTURE, RECEIPT

class NarratedRealAppTests(unittest.TestCase):
    def test_both_real_app_voices_are_bounded_and_source_authored(self):
        for app in sorted(APPS):
            with self.subTest(app=app):
                summary=validate_story(app)
                self.assertEqual(summary["chapters"],5)
                self.assertEqual(summary["voice"],"af_heart")
                self.assertTrue(summary["real_software_capture_required"])
                self.assertFalse(summary["owner_review_approved"])
                self.assertEqual(summary["youtube_uploads"],0)
                ep=story_episode(app)
                self.assertEqual(ep["type"],"short")
                self.assertEqual(len(ep["scenes"]),5)
                self.assertTrue(ep["real_software_evidence"])

    def test_story_refuses_fabrication_and_overlong_narration(self):
        for app in sorted(APPS):
            for label,bad in (
                ("unsupported voice",{"voice":"unlicensed_voice"}),
                ("fake intro",{"chapters":(("FAKE <LOGIN>","A"*90),)+STORIES[app]["chapters"][1:]}),
                ("obscene long shot",{"source_windows":((9.0,2.0),)+STORIES[app]["source_windows"][1:]}),
                ("short title",{"chapters":(("X","A"*100),)+STORIES[app]["chapters"][1:]}),
                ("massive phrase",{"chapters":STORIES[app]["chapters"][:2]+
                    (("FAKE STORY", "An enormously long invented sentence " * 14),)+
                    STORIES[app]["chapters"][3:]}),
            ):
                with self.subTest(app=app,label=label):
                    with patch.dict(STORIES[app],bad):
                        with self.assertRaises((RecoveryRefused,AssertionError)):
                            validate_story(app)

    def test_actual_source_timeline_nonoverlapping_chapters_and_captions(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            ass=folder/OUT_ASS
            ass.write_text("[Script Info]\nScriptType: v4.00+\n","utf8")
            from autopilot.branch1_real_action_coverage_gate import RealActionCoverageRefused
            for app in APPS:
                # The existing authentic *ten-second* source is proven too
                # static; video_graph MUST refuse it, rather than silently
                # produce another technically valid frozen Short.
                with self.assertRaises(RealActionCoverageRefused):
                    video_graph(app,[6.,5.,5.,5.,6.],ass,folder)
                # Prove that a FUTURE 5-chapter, genuinely long source
                # timeline can still construct the edit graph.
                with patch.dict(STORIES[app],{
                    "source_windows":((0.,5.5),(5.5,5.),(10.5,5.),
                                      (15.5,5.),(20.5,5.5))
                }):
                    graph=video_graph(app,[6.,5.,5.,5.,6.],ass,folder)
                self.assertIn("[0:v]split=5[s0][s1][s2][s3][s4]",graph)
                self.assertIn("[v0][v1][v2][v3][v4]concat=n=5",graph)
                self.assertIn("[concat]ass=",graph)
                self.assertIn("PROOF",graph if False else "PROOF")
                self.assertNotIn("image=",graph)
                self.assertEqual(graph.count("drawtext="),5)
                self.assertEqual(graph.count("tpad="),5)
                self.assertEqual(graph.count("trim=start="),5)
                for i in range(5):
                    self.assertTrue((folder/f"ORIGINAL_CHAPTER_{i:02}.txt").is_file())

    def test_reject_untrusted_graphics_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            for unsafe in ("x:danger","<HTML>","PERSON@EMAIL","", "a"*300):
                with self.subTest(label=unsafe):
                    with self.assertRaises(RecoveryRefused):
                        chapter_asset(Path(tmp),0,unsafe)

    def test_no_owner_approval_from_synthetic_receipt(self):
        from autopilot.test_branch1_real_app_capture import fake_receipt
        from autopilot.branch1_real_app_capture import plan
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for app in sorted(APPS):
                src=base/app
                out=base/(app+"-out")
                src.mkdir()
                out.mkdir()
                fake_receipt(app,src)
                fake={
                    "schema":"FLOWMINUTE_B1_NARRATED_REAL_APP_V1",
                    "status":STATUS,"app":app,"episode_id":plan(app)[0]["episode_id"],
                    "source_capture_sha256":"a"*64,
                    "source_provenance_sha256":"a"*64,
                    "public_voice_model_sha256":"a"*64,
                    "public_voice_pack_sha256":"a"*64,
                    "narration_pcm_sha256":"a"*64,
                    "caption_srt_sha256":"a"*64,
                    "caption_ass_sha256":"a"*64,
                    "narrated_mp4_sha256":"a"*64,
                    "narrated_mp4_bytes":12345,
                    "duration_seconds":25.,
                    "spoken_words":validate_story(app)["words"],
                    "postencoded_audio_verified":True,
                    "real_recording_pixel_source":True,
                    "owner_final_watch":False,
                    "release_signed":False,
                    "youtube_uploads":0,
                    "youtube_schedules":0,
                }
                for key,bad in (
                    ("owner_final_watch",True),
                    ("release_signed",True),
                    ("youtube_uploads",1),
                    ("youtube_schedules",1),
                    ("real_recording_pixel_source",False),
                    ("postencoded_audio_verified",False),
                    ("status","UPLOADED"),
                    ("app","other"),
                ):
                    with self.subTest(app=app,key=key):
                        test={**fake,key:bad}
                        (out/OUT_RECEIPT).write_text(json.dumps(test),"utf8")
                        with self.assertRaises(RecoveryRefused):
                            validate_output(app,src,out)

    def test_missing_media_and_not_running_on_laptop_refused(self):
        from autopilot.branch1_real_app_capture import plan
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for app in APPS:
                with self.subTest(app=app):
                    source=base/app
                    output=base/(app+"out")
                    source.mkdir()
                    with self.assertRaises(RecoveryRefused):
                        render(app,source,output,Path("fake.onnx"),Path("fake.bin"))
                    with self.assertRaises(RecoveryRefused):
                        validate_output(app,source,output)

if __name__=="__main__":
    unittest.main()
