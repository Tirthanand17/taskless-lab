"""B4e2 regression: calibrated narration, 17 one-shot visuals and safe captions.

No live model, user laptop, paid cloud, article download or YouTube access.
Actual physical MP4 frames are tested again in trusted main cloud.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from autopilot.full_original_rehearsal_media_b4e1 import (
    VOICE_SPEED_BY_SLOT,VOICE_SPEED_PREVIOUS,VOICE_SPEED_REFERENCE_SECONDS,
    CAPTION_MAX_LINES,CAPTION_WRAP_CHARS,CAPTION_MARGIN_BOTTOM_PX,
    CAPTION_ASS_FONT_SIZE,CAPTION_ASS_SCRIPT_HEIGHT,
    _safe_pixel_calibrated_srt_filter,
    SCENE_CARD_WORDS,REVEAL_SECONDS,FullRehearsalRefused,
    _draw_original_full_scene,_encode_full,_verify_encoded_first_reveal,
    prepare_full_rehearsal_plan,split_original_voice_to_cues,
)
from autopilot.nonfactual_narration_rehearsal import (
    THEMES,_paragraphs,build_nonfactual_rehearsals,
)
from autopilot.test_nonfactual_narration_rehearsal_b4d9 import pipeline


class NonLoopingFullMediaPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_documents=pipeline()
        cls.rehearsals=build_nonfactual_rehearsals(*cls.original_documents)
        cls.plan=prepare_full_rehearsal_plan(
            *cls.original_documents,cls.rehearsals)

    def test_calibrated_three_voice_speeds_derived_from_actual_trusted_main(self):
        self.assertEqual(set(VOICE_SPEED_BY_SLOT),
                         {"short_am","long","short_pm"})
        self.assertEqual(VOICE_SPEED_BY_SLOT, {
            "short_am":0.93,"long":0.86,"short_pm":0.88})
        for ep in self.plan["episodes"]:
            slot=ep["slot"]
            self.assertTrue(.83 <= VOICE_SPEED_BY_SLOT[slot] <=1.04)
            expected=VOICE_SPEED_REFERENCE_SECONDS[slot]*(
                VOICE_SPEED_PREVIOUS[slot]/VOICE_SPEED_BY_SLOT[slot])
            target=ep["target_seconds_not_audio_verified"]
            # A planning estimate only; must verify real PCM on live main.
            self.assertLess(abs(expected-target),3.0)

    def test_all_17_illustrations_have_original_scene_specific_visual_vocabulary(self):
        ids=[s["scene_id"] for e in self.plan["episodes"]
             for s in e["scenes"]]
        self.assertEqual(len(ids),17)
        self.assertEqual(len(set(ids)),11)
        self.assertEqual(set(ids),set(SCENE_CARD_WORDS))
        for scene_id,triplet in SCENE_CARD_WORDS.items():
            self.assertEqual(len(triplet),3)
            self.assertEqual(len(set(triplet)),3)
            self.assertTrue(all(len(item)==2 for item in triplet))
            self.assertFalse(any("rotate" in word.lower()
                                 or "spinner" in word.lower()
                                 for card in triplet for word in card))
        self.assertEqual(REVEAL_SECONDS,.36)

    def test_full_caption_lines_fit_both_reserved_panels_in_all_six_script_families(self):
        self.assertEqual(CAPTION_MAX_LINES,{"short":4,"long":2})
        self.assertEqual(CAPTION_WRAP_CHARS,{"short":44,"long":76})
        self.assertGreaterEqual(CAPTION_MARGIN_BOTTOM_PX["short"],150)
        self.assertGreaterEqual(CAPTION_MARGIN_BOTTOM_PX["long"],135)
        for family,theme in THEMES.items():
            for slot in ("short_am","long","short_pm"):
                kind="long" if slot=="long" else "short"
                for paragraph in _paragraphs(slot,theme):
                    chunks=split_original_voice_to_cues(paragraph)
                    self.assertEqual(" ".join(chunks)," ".join(paragraph.split()))
                    for phrase in chunks:
                        lines=textwrap.wrap(phrase,
                            width=CAPTION_WRAP_CHARS[kind],
                            break_long_words=False,break_on_hyphens=False)
                        self.assertLessEqual(len(lines),CAPTION_MAX_LINES[kind])
                        self.assertTrue(all(len(line)<=CAPTION_WRAP_CHARS[kind]+2
                                            for line in lines))

    def test_libass_srt_uses_virtual_not_output_pixel_units(self):
        self.assertEqual(CAPTION_ASS_SCRIPT_HEIGHT,288)
        self.assertEqual(CAPTION_ASS_FONT_SIZE,{"short":7,"long":9})
        for ep in self.plan["episodes"]:
            with tempfile.TemporaryDirectory() as tmp:
                filt=_safe_pixel_calibrated_srt_filter(
                    ep,Path(tmp)/"original-captions.srt")
            expected_margin=25 if ep["kind"]=="short" else 39
            font=CAPTION_ASS_FONT_SIZE[ep["kind"]]
            self.assertIn(f"FontSize={font}",filt)
            self.assertIn(f"MarginV={expected_margin}",filt)
            self.assertNotIn("FontSize=27",filt)
            self.assertNotIn("FontSize=24",filt)
            self.assertNotIn("MarginV=168",filt)
            self.assertNotIn("MarginV=148",filt)

    @unittest.skipUnless(importlib.util.find_spec("PIL"),
                         "Pillow required to inspect physically rendered subtitles")
    def test_actual_ffmpeg_burned_subtitle_pixels_stay_inside_both_cards(self):
        ffmpeg=shutil.which("ffmpeg")
        if ffmpeg is None:
            self.skipTest("Actual FFmpeg not installed")
        from PIL import Image,ImageChops
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            cases=(
                ("short",1080,1920,
                 ("This is an original fictional lesson",
                  "with made-up inputs and a fair test",
                  "check all sources and labels first",
                  "before trusting real-world claims."),390),
                ("long",1920,1080,
                 ("An independent reviewer should verify all factual claims",
                  "before a creator can safely publish the video."),248),
            )
            for kind,w,h,lines,top_margin in cases:
                with self.subTest(kind=kind):
                    ep=next(e for e in self.plan["episodes"]
                            if e["kind"]==kind)
                    srt=root/f"{kind}-original.srt"
                    srt.write_text(
                        "1\\n00:00:00,000 --> 00:00:02,000\\n"+
                        "\\n".join(lines)+"\\n",encoding="utf8")
                    output={}
                    for style in ("base","burned"):
                        target=root/f"{kind}-{style}.png"
                        vf=("fps=24,format=yuv420p" if style=="base"
                            else _safe_pixel_calibrated_srt_filter(ep,srt))
                        cmd=[
                            ffmpeg,"-v","error","-nostdin","-y",
                            "-f","lavfi","-i",
                            f"color=c=0x142235:s={w}x{h}:r=24:d=2",
                            "-ss","0.8","-vf",vf,
                            "-frames:v","1",str(target),
                        ]
                        result=subprocess.run(
                            cmd,capture_output=True,text=True,timeout=35)
                        self.assertEqual(result.returncode,0,result.stderr[-1200:])
                        output[style]=Image.open(target).convert("RGB")
                    binary=ImageChops.difference(
                        output["base"],output["burned"]).convert("L").point(
                        lambda v:255 if v>25 else 0)
                    bounds=binary.getbbox()
                    self.assertIsNotNone(bounds,"FFmpeg emitted no burned subtitles")
                    left,top,right,bottom=bounds
                    self.assertGreaterEqual(left,82)
                    self.assertLessEqual(right,w-82)
                    self.assertGreaterEqual(top,h-top_margin+20)
                    self.assertLessEqual(bottom,h-128-10)

    def test_one_time_reveal_is_not_a_continuously_running_animation(self):
        self.assertTrue(0.15<REVEAL_SECONDS<.5)
        for ep in self.plan["episodes"]:
            for scene in ep["scenes"]:
                self.assertEqual(scene["motion_policy"],"single-entry-reveal-static")
                self.assertFalse(scene["source_quote_display_allowed"])
                self.assertFalse(scene["news_claim_fact_checked"])
        self.assertFalse(self.plan["release_authorized"])
        self.assertEqual(self.plan["paid_model_calls"],0)
        self.assertEqual(self.plan["approved_news_facts"],0)
        self.assertEqual(self.plan["youtube_uploads"],0)

    @unittest.skipUnless(importlib.util.find_spec("PIL"),
                         "Pillow only available on physical media GitHub runners")
    def test_physical_unique_two_stage_png_reveal_for_all_17_scenes(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            total=0
            for ep in self.plan["episodes"]:
                final_digests=[]
                for scene in ep["scenes"]:
                    base=Path(tmp)/ep["slot"]/f"{scene['scene']}-base.png"
                    active=Path(tmp)/ep["slot"]/f"{scene['scene']}-active.png"
                    a=_draw_original_full_scene(ep,scene,base,revealed=False)
                    b=_draw_original_full_scene(ep,scene,active,revealed=True)
                    self.assertNotEqual(a,b)
                    final_digests.append(b)
                    for p in (base,active):
                        with Image.open(p) as im:
                            im.load()
                            self.assertEqual(im.size,tuple(ep["size"]))
                            self.assertEqual(im.mode,"RGB")
                    total+=2
                self.assertEqual(len(set(final_digests)),
                                 ep["all_scene_count"])
            self.assertEqual(total,34)

    @unittest.skipUnless(importlib.util.find_spec("PIL"),
                         "Pillow only available on physical video workers")
    def test_nonexistent_episode_and_wrong_reveal_state_refused(self):
        ep=self.plan["episodes"][1]
        with tempfile.TemporaryDirectory() as tmp:
            wrong={**ep,"slot":"unknown"}
            with self.assertRaises(FullRehearsalRefused):
                _draw_original_full_scene(wrong,ep["scenes"][0],Path(tmp)/"a.png")
            wrongscene={**ep["scenes"][0],"scene_id":"FICTITIOUS_PREAPPROVED_NEWS"}
            with self.assertRaises(FullRehearsalRefused):
                _draw_original_full_scene(ep,wrongscene,Path(tmp)/"b.png")
            with self.assertRaises(FullRehearsalRefused):
                _draw_original_full_scene(ep,ep["scenes"][0],
                                          Path(tmp)/"c.png",revealed="yes")

    def test_ffmpeg_scene_concat_contains_34_one_time_visual_events_not_17_stills(self):
        ep=self.plan["episodes"][1]
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            images=[]
            durations=[13.0 for _ in ep["scenes"]]
            for i in range(ep["all_scene_count"]):
                a=folder/f"{i:02}_start.png"
                b=folder/f"{i:02}_end.png"
                a.write_bytes(b"a")
                b.write_bytes(b"b")
                images.append((a,b))
            wav=folder/"voice.wav"
            srt=folder/"captions.srt"
            wav.write_bytes(b"fake")
            srt.write_bytes(b"fake")
            with patch(
                "autopilot.full_original_rehearsal_media_b4e1._run",
                return_value="") as encoder:
                result=_encode_full("ffmpeg",ep,folder,images,durations,
                                    wav,srt,sum(durations))
            self.assertEqual(result.suffix,".mp4")
            text=(folder/"EPHEMERAL_ALL_SCENES_ONE_SHOT_REVEAL.ffconcat").read_text()
            self.assertEqual(text.count("\nfile '"),19)
            self.assertEqual(text.count("duration 0.360000"),9)
            self.assertEqual(text.count("duration 12.640000"),9)
            self.assertIn("MarginV=39",str(encoder.call_args))
            self.assertIn("FontSize=9",str(encoder.call_args))
            self.assertNotIn("MarginV=148",str(encoder.call_args))
            self.assertIn("fps=24",str(encoder.call_args))
            self.assertIn("libx264",str(encoder.call_args))
            self.assertIn("aac",str(encoder.call_args))
            self.assertNotIn("rotate",str(encoder.call_args))
            self.assertNotIn("loop",str(encoder.call_args))

    def test_video_cannot_use_missing_one_shot_stage_or_invalid_pcm_clock(self):
        ep=self.plan["episodes"][0]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            only=[(p/"missing-a.png",p/"missing-b.png")
                  for _ in ep["scenes"]]
            with self.assertRaises(FullRehearsalRefused):
                _encode_full("ffmpeg",ep,p,only,[12.0]*4,
                             p/"not-present.wav",p/"missing.srt",48.)
            for a,b in only:
                a.write_bytes(b"a")
                b.write_bytes(b"b")
            with self.assertRaises(FullRehearsalRefused):
                _encode_full("ffmpeg",ep,p,only,[1.0]*4,
                             p/"not-present.wav",p/"missing.srt",4.)

    def test_physical_encoded_frame_change_is_checked_not_assumed_from_png(self):
        fake_frame=bytes([120])*(192*108)
        moving=bytes([120])*500+bytes([185])*(192*108-500)
        class FakeFinished:
            def __init__(self,payload):
                self.returncode=0
                self.stdout=payload
                self.stderr=b""
        with patch("subprocess.run",
                   side_effect=[FakeFinished(fake_frame),
                                FakeFinished(moving)]) as mock_run:
            self.assertTrue(_verify_encoded_first_reveal("ffmpeg",Path("/tmp/preview.mp4")))
            self.assertEqual(mock_run.call_count,2)
        with patch("subprocess.run",
                   side_effect=[FakeFinished(fake_frame),
                                FakeFinished(fake_frame)]):
            with self.assertRaises(FullRehearsalRefused):
                _verify_encoded_first_reveal("ffmpeg",Path("/tmp/unchanged.mp4"))

    def test_badly_decoded_short_frame_never_passes_quality_gate(self):
        class FakeFinished:
            returncode=0
            stdout=b"\x00"*29
            stderr=b""
        with patch("subprocess.run",return_value=FakeFinished()):
            with self.assertRaises(FullRehearsalRefused):
                _verify_encoded_first_reveal("ffmpeg",Path("/tmp/broken.mp4"))


    def _physical_qa_fixture(self):
        """Small actual file plus authentic all-scenes original caption text."""
        from autopilot.full_original_rehearsal_media_b4e1 import _inspect_full
        ep=self.plan["episodes"][0]
        cues=[]
        cursor=0.
        for scene in ep["scenes"]:
            for line in scene["caption_cues"]:
                cues.append({"text":line,"start":cursor,"end":cursor+4.,
                             "scene":scene["scene"]})
                cursor+=4.1
        hashes=[sha256(f"final-{i}".encode()).hexdigest()
                for i in range(ep["all_scene_count"])]
        pairs=[(sha256(f"base-{i}".encode()).hexdigest(),digest)
               for i,digest in enumerate(hashes)]
        return ep,cues,cursor,hashes,pairs,_inspect_full

    def test_real_post_encode_caption_inspector_executes_complete_safe_path(self):
        ep,cues,total,hashes,pairs,inspect=self._physical_qa_fixture()
        class PhysicalMetadata:
            stderr=("Stream #0:0: Video: h264 (High), yuv420p, 1080x1920\n"
                    "Stream #0:1: Audio: aac (LC), 24000 Hz, mono\n")
            stdout=""
            returncode=1
        with tempfile.TemporaryDirectory() as root:
            movie=Path(root)/"rehearsal.mp4"
            movie.write_bytes(b"test-physically-bounded"*20000)
            with (patch("subprocess.run",return_value=PhysicalMetadata()),
                  patch("autopilot.full_original_rehearsal_media_b4e1._run",
                        return_value=""),
                  patch("autopilot.full_original_rehearsal_media_b4e1._verify_encoded_first_reveal",
                        return_value=True)):
                r=inspect("ffmpeg",movie,ep,cues,total,hashes,pairs)
            self.assertEqual(r["original_full_scene_count"],4)
            self.assertTrue(r["actual_full_ffmpeg_decode_passed"])
            self.assertTrue(r["first_real_encoded_one_shot_checkpoint_reveal_frame_verified"])
            self.assertTrue(r["srt_caption_baseline_inside_reserved_panel"])
            self.assertLessEqual(r["measured_actual_caption_max_visible_lines"],4)
            self.assertEqual(r["voice_speed_calibrated_from_last_real_run"],.93)
            self.assertEqual(r["original_scene_base_and_one_shot_reveal_pngs"],8)
            self.assertFalse(r["release_authorized"])
            self.assertFalse(r["human_full_audio_visual_watch_completed"])

    def test_real_post_encode_inspector_rejects_historical_lost_reveal(self):
        ep,cues,total,hashes,pairs,inspect=self._physical_qa_fixture()
        with tempfile.TemporaryDirectory() as root:
            movie=Path(root)/"rehearsal.mp4"
            movie.write_bytes(b"x"*400000)
            bad_pairs=list(pairs)
            bad_pairs[0]=(hashes[0],hashes[0])
            with self.assertRaises(FullRehearsalRefused):
                inspect("ffmpeg",movie,ep,cues,total,hashes,bad_pairs)


if __name__=="__main__":
    unittest.main()
