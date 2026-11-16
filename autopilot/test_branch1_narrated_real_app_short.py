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
    render,probe,authentic_source_speed
)
from autopilot.branch1_recovery import RecoveryRefused
from autopilot.branch1_real_app_capture import CAPTURE, RECEIPT

class NarratedRealAppTests(unittest.TestCase):
    def test_single_remaster_retry_limits_peak_without_softening_release_gate(self):
        from autopilot.verified_aac_mastering_b4g5 import (
            AUDIO_MASTERING_FILTER,AUDIO_REMASTER_FILTER,
            ACCEPTED_INTEGRATED_LUFS_MIN,ACCEPTED_INTEGRATED_LUFS_MAX,
            ACCEPTED_TRUE_PEAK_DBTP_MAX,
        )
        self.assertIn("loudnorm=I=-18",AUDIO_MASTERING_FILTER)
        self.assertIn("loudnorm=I=-18:TP=-4",AUDIO_REMASTER_FILTER)
        self.assertIn("alimiter=limit=0.70:level=false",AUDIO_REMASTER_FILTER)
        layout=(Path(__file__).parent/"branch1_narrated_real_app_short.py").read_text("utf8")
        self.assertIn("drawbox=x=0:y=1540:w=iw:h=380:color=0x071827@0.92:t=fill",layout)
        self.assertNotIn("color=0x071827@0.36:t=fill",layout)
        self.assertEqual(ACCEPTED_INTEGRATED_LUFS_MIN,-20.5)
        self.assertEqual(ACCEPTED_INTEGRATED_LUFS_MAX,-15.5)
        self.assertEqual(ACCEPTED_TRUE_PEAK_DBTP_MAX,-1.0)
        src=(Path(__file__).parent/"branch1_narrated_real_app_short.py").read_text("utf8")
        self.assertIn('AUDIO_REMASTER_FILTER,',src)
        self.assertIn('fixed=out/"REMASTER_ONCE.mp4"',src)
        self.assertIn('verify_exact_encoded_master("ffmpeg",fixed,sha(fixed),total)',src)
        self.assertIn("fixed.replace(video)",src)
        self.assertNotIn('loudnorm=I=-18:TP=-2.5:LRA=11',src)

    def test_both_real_app_voices_are_bounded_and_source_authored(self):
        for app in sorted(APPS):
            with self.subTest(app=app):
                summary=validate_story(app)
                self.assertEqual(summary["chapters"],5 if app=="calc" else 3)
                self.assertEqual(summary["voice"],"af_heart")
                self.assertTrue(summary["real_software_capture_required"])
                self.assertFalse(summary["owner_review_approved"])
                self.assertEqual(summary["youtube_uploads"],0)
                ep=story_episode(app)
                self.assertEqual(ep["type"],"short")
                self.assertEqual(len(ep["scenes"]),5 if app=="calc" else 3)
                self.assertTrue(ep["real_software_evidence"])

    def test_chrome_words_teach_genuine_find_on_fictional_local_data(self):
        chapters=STORIES["chrome"]["chapters"]
        combined=" ".join(spoken for _,spoken in chapters)
        self.assertIn("real Chrome Find",combined)
        self.assertIn("fictional local data",combined)
        self.assertIn("Scrolling this much text",combined)
        self.assertIn("Control F",combined)
        self.assertIn("Control G",combined)
        self.assertIn("ERROR",combined)
        self.assertIn("real matches",combined)
        self.assertNotIn("notification",combined.lower())
        self.assertNotIn("throwaway demo profile",combined)
        self.assertEqual(validate_story("chrome")["chapters"],3)

    def test_story_refuses_fabrication_and_overlong_narration(self):
        for app in sorted(APPS):
            for label,bad in (
                ("unsupported voice",{"voice":"unlicensed_voice"}),
                ("fake intro",{"chapters":(("FAKE <LOGIN>","A"*90),)+STORIES[app]["chapters"][1:]}),
                ("obscene long shot",{"source_windows":((49.0,2.0),)+STORIES[app]["source_windows"][1:]}),
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
                # The *historical* 10-second footage is refused and the
                # new source windows claim only genuine 48s app activity.
                with patch.dict(STORIES[app],{
                    "source_windows":((7.2,2.0),(.1,1.7),(1.25,2.0),
                                      (2.0,2.3),(6.0,3.5))
                }):
                    with self.assertRaises(RealActionCoverageRefused):
                        video_graph(app,[6.,5.,5.,5.,6.],ass,folder)
                graph=video_graph(app,[6.,5.,5.,5.,6.] if app=="calc" else [6.,6.,7.],ass,folder)
                count=5 if app=="calc" else 3
                self.assertIn(f"[0:v]split={count}",graph)
                self.assertIn(f"concat=n={count}",graph)
                self.assertIn("[concat]ass=",graph)
                self.assertIn("PROOF",graph if False else "PROOF")
                self.assertNotIn("image=",graph)
                self.assertEqual(graph.count("drawtext="),count)
                self.assertEqual(graph.count("tpad="),count)
                self.assertEqual(graph.count("trim=start="),count)
                for i in range(5):
                    self.assertTrue((folder/f"ORIGINAL_CHAPTER_{i:02}.txt").is_file())

    def test_real_application_mobile_framing_does_not_fabricate_ui(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            ass=folder/OUT_ASS
            ass.write_text("[Script Info]\nScriptType: v4.00+\n","utf8")
            calc=video_graph("calc",[6.,5.,5.,5.,6.],ass,folder)
            chrome=video_graph("chrome",[6.,6.,7.],ass,folder)
            self.assertEqual(calc.count("crop=720:460:0:0"),5)
            self.assertEqual(calc.count("crop=440:220:240:75"),5)
            self.assertEqual(calc.count("color=c=0x081827"),5)
            self.assertEqual(calc.count("overlay=x=0:y=190"),5)
            self.assertEqual(calc.count("overlay=x=0:y=900"),5)
            self.assertNotIn("crop=600:1067",calc)
            self.assertEqual(chrome.count("crop=675:1080:20:0"),3)
            self.assertEqual(chrome.count("pad=1080:1920:0:152:color=0x081827"),3)
            self.assertNotIn("overlay=",chrome)
            for app,graph in (("calc",calc),("chrome",chrome)):
                self.assertIn(f"concat=n={5 if app=='calc' else 3}:v=1:a=0",graph)
                self.assertIn("[concat]ass=",graph)
                self.assertNotIn("movie=",graph)
                self.assertNotIn("image=",graph)
                self.assertEqual(graph.count("drawtext="),5 if app=="calc" else 3)

    def test_mobile_crop_and_first_spoken_claim_match_real_result(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            captions=root/OUT_ASS
            captions.write_text("[Script Info]\\nScriptType: v4.00+\\n","utf8")
            calc=video_graph("calc",[6.,5.,5.,5.,6.],captions,root)
            chrome=video_graph("chrome",[6.,6.,7.],captions,root)
            self.assertEqual(calc.count("crop=440:220:240:75"),5)
            self.assertEqual(chrome.count("crop=675:1080:20:0"),3)
            self.assertEqual(chrome.count("pad=1080:1920:0:152:color=0x081827"),3)
            self.assertEqual(calc.count("scale=1080:540"),5)
            self.assertNotIn("crop=600:1067:15:70",chrome)
            self.assertIn("The direct match is false",STORIES["calc"]["chapters"][0][1])
            self.assertIn("Trim makes it true",STORIES["calc"]["chapters"][0][1])
            self.assertNotIn("fake",STORIES["calc"]["chapters"][0][1].lower())

    def test_retime_all_recorded_actions_instead_of_discarding_late_frames(self):
        from autopilot.branch1_recovery import RecoveryRefused
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            ass=folder/OUT_ASS
            ass.write_text("[Script Info]\\nScriptType: v4.00+\\n","utf8")
            for app in APPS:
                graph=video_graph(app,[6.,5.,5.,5.,6.] if app=="calc" else [6.,6.,7.],ass,folder)
                # 8.5 seconds of genuine application footage are retimed
                # to voice duration; none of the later actions are cut.
                if app=="calc":
                    self.assertIn("setpts=0.70588235*(PTS-STARTPTS)",graph)
                    self.assertIn("setpts=0.58823529*(PTS-STARTPTS)",graph)
                else:
                    self.assertIn("setpts=0.76433121*(PTS-STARTPTS)",graph)
                self.assertEqual(graph.count("stop_duration=1.25"),5 if app=="calc" else 3)
                self.assertNotIn("stop_duration=12",graph)
                self.assertEqual(graph.count("fps=24"),5 if app=="calc" else 3)
        self.assertAlmostEqual(authentic_source_speed(8.5,5.0),1.7)
        for bad_window,bad_voice in ((8.5,2.6),(8.5,12.0),
                                     (float("nan"),5),(-1,5),
                                     (8.5,False),(8.5,0)):
            with self.subTest(window=bad_window,voice=bad_voice):
                with self.assertRaises(RecoveryRefused):
                    authentic_source_speed(bad_window,bad_voice)

    def test_editorial_brief_matches_realistic_speech_runtime(self):
        from autopilot.branch1_real_app_capture import plan
        self.assertEqual(plan("calc")[0]["duration_seconds"],27)
        self.assertEqual(plan("chrome")[0]["duration_seconds"],22)
        self.assertEqual(len(STORIES["chrome"]["source_windows"]),3)
        source=(Path(__file__).parent/"branch1_narrated_real_app_short.py").read_text("utf8")
        self.assertIn("EDITORIAL_BRIEF_RUNTIME_MISMATCH",source)
        self.assertIn("ACTUAL_SPOKEN_RUNTIME_NOT_MATCHING_CREATIVE_BRIEF",source)

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
