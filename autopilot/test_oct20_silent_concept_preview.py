"""Original 20-Oct concept visualization: actual PNG + silent H264 smoke.

No human speech, media originality clearance, cinematic photoreal footage,
rights, remote cloud, OAuth, uploading or public YouTube action.
"""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import tempfile
import unittest

from PIL import Image

from autopilot.agent_org import WorkflowError
from autopilot.oct20_silent_concept_preview import (
    HEADLINES,load_preview_plan,preview_spec,
    render_storyboard_keyframe,render_silent_preview_excerpt,
)


class October20OfflineOriginalVisualTests(unittest.TestCase):
    def test_all_three_authored_episode_lanes_have_matching_scenes(self):
        data=load_preview_plan()
        actual={}
        for ep in sorted(HEADLINES):
            spec=preview_spec(data,ep)
            actual[ep]=(spec.scenes,spec.duration_seconds,spec.language)
            self.assertEqual(spec.scenes,len(HEADLINES[ep]))
        self.assertEqual(actual,{
            "fm_20261020_short_en":(7,42,"en"),
            "fm_20261020_short_hi":(7,44,"hi"),
            "fm_20261020_long_hi":(11,480,"hi"),
        })

    def test_actual_hindi_english_original_png_keyframes_render_and_redact(self):
        source=load_preview_plan()
        with tempfile.TemporaryDirectory() as tmp:
            for ep in ("fm_20261020_short_en","fm_20261020_short_hi"):
                name=Path(tmp)/(ep+".png")
                with self.subTest(ep=ep):
                    report=render_storyboard_keyframe(
                        plan=source,episode_id=ep,scene_number=0,
                        output_path=name)
                    self.assertTrue(name.exists())
                    with Image.open(name) as img:
                        self.assertEqual(img.size,(540,960))
                        self.assertEqual(img.mode,"RGB")
                    self.assertFalse(report["human_narration_verified"])
                    self.assertFalse(report["youtube_upload_or_publish_authorized"])
                    self.assertFalse(report["phoneme_or_word_alignment_verified"])
                    self.assertEqual(report["monthly_recurring_infrastructure_inr"],0)

    def test_no_overwrite_of_existing_media_asset_or_unsafe_geometry(self):
        source=load_preview_plan()
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"owner.png"
            target.write_bytes(b"DO_NOT_REPLACE")
            for width,height in ((200,500),(540,1024),(1080,1080)):
                with self.subTest(geometry=(width,height)),self.assertRaises(WorkflowError):
                    render_storyboard_keyframe(
                        plan=source,episode_id="fm_20261020_short_hi",
                        scene_number=0,output_path=Path(tmp)/"new.png",
                        width=width,height=height)
            with self.assertRaises(WorkflowError):
                render_storyboard_keyframe(
                    plan=source,episode_id="fm_20261020_short_en",
                    scene_number=0,output_path=target)
            self.assertEqual(target.read_bytes(),b"DO_NOT_REPLACE")

    def test_forced_publishing_claim_or_fake_audio_is_not_a_preview(self):
        for key in ("prerecorded_voice_exists","actual_media_encoded",
                    "private_upload_authorized","public_publish_authorized"):
            bad=deepcopy(load_preview_plan())
            bad["content_release_policy"][key]=True
            with self.subTest(flag=key),self.assertRaises(WorkflowError):
                preview_spec(bad,"fm_20261020_short_en")

    def test_missing_or_broken_original_scene_timeline_fails_closed(self):
        for mistake in ("unknown","repeat","gap","duration","wrong_lane"):
            source=deepcopy(load_preview_plan())
            if mistake=="unknown":
                ep="missing_unknown"
            else:
                ep="fm_20261020_short_hi"
                record=next(x for x in source["episodes"] if x["episode_id"]==ep)
                if mistake=="repeat":source["episodes"].append(deepcopy(record))
                if mistake=="gap":record["segments"][1]["start_second"]+=1
                if mistake=="duration":record["segments"][-1]["end_second"]-=1
                if mistake=="wrong_lane":record["original_spoken_language"]="en"
            with self.subTest(mistake=mistake),self.assertRaises(WorkflowError):
                preview_spec(source,ep)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real installed FFmpeg and FFprobe required")
    def test_real_one_second_h264_excerpt_has_no_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"english_silent_excerpt.mp4"
            result=render_silent_preview_excerpt(
                episode_id="fm_20261020_short_en",output_path=target,
                scenes=1,seconds_per_scene=1)
            self.assertEqual(result["frames"],24)
            self.assertEqual(result["audio_tracks"],0)
            self.assertFalse(result["full_video_complete"])
            self.assertFalse(result["licensed_voice_observed"])
            self.assertFalse(result["publishing_authorized"])
            self.assertGreater(target.stat().st_size,2048)

    def test_long_480_seconds_cannot_be_spoofed_as_short_excerpt(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(WorkflowError):
                render_silent_preview_excerpt(
                    episode_id="fm_20261020_long_hi",
                    output_path=Path(tmp)/"do_not_render.mp4",
                    scenes=1,seconds_per_scene=1)
            self.assertFalse((Path(tmp)/"do_not_render.mp4").exists())


if __name__=="__main__":
    unittest.main()
