"""Genuine Hindi glyph-render and landscape-vs-portrait MP4 regression tests.

All outputs are intentionally silent and editorially unapproved. These tests
use installed OFL/OS font packages only, never a network TTS provider.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_hindi_visual_preview import (
    _authored_profile, _shown_cue, _font,
    render_hindi_frame, render_hindi_visual_preview,
)

class HindiRealVisualTests(unittest.TestCase):
    def test_exact_two_authored_episode_profiles(self):
        h=_authored_profile("csv_tutorial_short_hi")
        l=_authored_profile("csv_tutorial_long_hi")
        self.assertEqual((h[0],h[1],len(h[2])),("short",42,4))
        self.assertEqual((l[0],l[1],len(l[2])),("long",432,24))
        self.assertEqual(h[3][0][0],0)
        self.assertEqual(l[3][-1][1],432000)

    def test_short_and_long_use_actual_hindi_cues(self):
        for episode in ("csv_tutorial_short_hi","csv_tutorial_long_hi"):
            with self.subTest(episode=episode):
                profile=_authored_profile(episode)
                cue=_shown_cue(profile,800)
                self.assertTrue(any("\u0900"<=x<="\u097f" for x in cue))
                self.assertNotIn("<",cue)

    def test_portrait_and_landscape_are_correct_aspect_ratios(self):
        s=render_hindi_frame("csv_tutorial_short_hi",1,width=360)
        l=render_hindi_frame("csv_tutorial_long_hi",1,width=640)
        self.assertEqual(s.size,(360,640))
        self.assertEqual(l.size,(640,360))
        self.assertEqual(s.mode,"RGB")

    def test_real_full_hd_frames_use_correct_portrait_and_landscape(self):
        portrait=render_hindi_frame("csv_tutorial_short_hi",1,width=1080)
        landscape=render_hindi_frame("csv_tutorial_long_hi",1,width=1920)
        self.assertEqual(portrait.size,(1080,1920))
        self.assertEqual(landscape.size,(1920,1080))
        self.assertNotEqual(portrait.getpixel((10,10)),portrait.getpixel((10,1000)))
        self.assertNotEqual(landscape.getpixel((10,10)),landscape.getpixel((10,1000)))

    def test_full_hd_preview_is_hard_capped_to_36_frames(self):
        with tempfile.TemporaryDirectory() as root:
            for episode,width in (
                ("csv_tutorial_short_hi",1080),
                ("csv_tutorial_long_hi",1920),
            ):
                with self.subTest(episode=episode),self.assertRaises(WorkflowError):
                    render_hindi_visual_preview(
                        episode,Path(root)/(episode+".mp4"),
                        width=width,fps=24,duration_s=2)
                self.assertFalse((Path(root)/(episode+".mp4")).exists())

    def test_animated_pixels_change_in_same_scene(self):
        x=render_hindi_frame("csv_tutorial_short_hi",1,width=360)
        y=render_hindi_frame("csv_tutorial_short_hi",1.25,width=360)
        self.assertNotEqual(x.tobytes(),y.tobytes())

    def test_24_long_scenes_use_accurate_source_specific_storyboard(self):
        from autopilot.phase3_hindi_visual_preview import (
            LONG_SCENE_STORYBOARD, LONG_CODE_SNIPPETS, LONG_ROW_CALLOUTS,
        )
        self.assertEqual(len(LONG_SCENE_STORYBOARD),24)
        self.assertEqual(len({label for _,label in LONG_SCENE_STORYBOARD}),24)
        self.assertEqual(set(mode for mode,_ in LONG_SCENE_STORYBOARD),
                         {0,1,2,3,4,5})
        # No generic position%4 cycling: actual narrative flow is
        # intro -> privacy -> CSV concepts -> writer/reader -> math ->
        # CSV edge cases -> privacy -> recap.
        for index,mode in {
            0:0,1:4,2:0,5:2,6:2,7:2,8:2,9:2,10:5,
            11:1,12:1,13:1,14:3,16:2,17:2,18:4,19:5,
            20:5,21:2,22:5,23:3,
        }.items():
            with self.subTest(scene=index):
                self.assertEqual(LONG_SCENE_STORYBOARD[index][0],mode)
        self.assertEqual(
            set(LONG_CODE_SNIPPETS),
            {i for i,(mode,_) in enumerate(LONG_SCENE_STORYBOARD)
             if mode==2},
        )
        self.assertEqual(set(LONG_ROW_CALLOUTS),{11,12,13})
        self.assertIn("50",LONG_ROW_CALLOUTS[12])
        self.assertIn("58",LONG_ROW_CALLOUTS[13])

    def test_privacy_math_and_workflow_long_frames_render_distinctly(self):
        # The same long video now has multiple source-specific visual modes
        # whose actual pixels render; no external graphic/voice is fetched.
        slots=[1,5,11,14,19,22]
        images=[render_hindi_frame("csv_tutorial_long_hi",
                    i*18+9,width=640) for i in slots]
        self.assertTrue(all(img.size==(640,360) for img in images))
        self.assertEqual(len({img.tobytes() for img in images}),len(images))
        self.assertNotEqual(images[0].getpixel((320,190)),
                            images[2].getpixel((320,190)))

    def test_cue_changes_during_first_video_scene(self):
        short=_authored_profile("csv_tutorial_short_hi")
        self.assertNotEqual(_shown_cue(short,500),_shown_cue(short,8500))

    def test_frames_are_deterministic(self):
        a=render_hindi_frame("csv_tutorial_long_hi",3,width=640)
        b=render_hindi_frame("csv_tutorial_long_hi",3,width=640)
        self.assertEqual(a.tobytes(),b.tobytes())

    def test_every_authored_long_scene_renders_with_real_devanagari(self):
        profile=_authored_profile("csv_tutorial_long_hi")
        for index,(start,end,*_) in enumerate(profile[2]):
            # Real scene midpoint, not just the beginning of an unfinished plan.
            with self.subTest(scene=index+1):
                mid=(start+end)/2000
                img=render_hindi_frame("csv_tutorial_long_hi",mid,width=640)
                self.assertEqual(img.size,(640,360))
                self.assertTrue(_shown_cue(profile,int(mid*1000)))

    def test_every_hindi_short_scene_renders_and_last_frame(self):
        profile=_authored_profile("csv_tutorial_short_hi")
        for index,(start,end,*_) in enumerate(profile[2]):
            with self.subTest(scene=index+1):
                img=render_hindi_frame("csv_tutorial_short_hi",
                                      (start+end)/2000,width=360)
                self.assertEqual(img.size,(360,640))
        final=render_hindi_frame("csv_tutorial_short_hi",41.875,width=360)
        self.assertEqual(final.size,(360,640))

    def test_bounds_fail_closed(self):
        with self.assertRaises(WorkflowError):
            render_hindi_frame("not_a_video",1,width=360)
        for width in (0,600,1000):
            with self.subTest(width=width),self.assertRaises(WorkflowError):
                render_hindi_frame("csv_tutorial_short_hi",1,width=width)
        with self.assertRaises(WorkflowError):
            render_hindi_frame("csv_tutorial_long_hi",432,width=640)

    def test_no_automatic_overwriting_or_media_storage_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"output.mp4"
            p.write_bytes(b"exists")
            with self.assertRaises(WorkflowError):
                render_hindi_visual_preview("csv_tutorial_short_hi",p)
            p.unlink()
            with self.assertRaises(WorkflowError):
                render_hindi_visual_preview("csv_tutorial_short_hi",
                                            Path(tmp)/"not_created"/"output.mp4")
            
    def test_invalid_requested_full_long_media_render_exceeds_proof_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"clip.mp4"
            with self.assertRaises(WorkflowError):
                render_hindi_visual_preview("csv_tutorial_long_hi",p,
                                            duration_s=432,fps=24)
            self.assertFalse(p.exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Preinstalled FFmpeg required")
    def test_actual_two_video_outputs_decode_and_remain_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            for episode,width,dimensions in (
                ("csv_tutorial_short_hi",360,(360,640)),
                ("csv_tutorial_long_hi",640,(640,360)),
            ):
                with self.subTest(episode=episode):
                    path=Path(tmp)/(episode+".mp4")
                    result=render_hindi_visual_preview(
                        episode,path,duration_s=0.5,fps=8,width=width)
                    self.assertTrue(result["actual_video_pixels_encoded"])
                    self.assertFalse(result["audio_track_present"])
                    self.assertFalse(result["publishing_authorized"])
                    self.assertEqual((result["width"],result["height"]),dimensions)
                    meta=subprocess.run([
                        "ffprobe","-v","error","-show_entries",
                        "stream=codec_type,codec_name,width,height:format=duration",
                        "-of","json",str(path)],capture_output=True,text=True,
                        check=True,timeout=20)
                    record=json.loads(meta.stdout)
                    self.assertEqual(len(record["streams"]),1)
                    self.assertEqual(record["streams"][0]["codec_type"],"video")
                    self.assertEqual(record["streams"][0]["codec_name"],"h264")
                    self.assertEqual(
                        (record["streams"][0]["width"],record["streams"][0]["height"]),
                        dimensions)
                    subprocess.run([
                        "ffmpeg","-v","error","-xerror","-i",str(path),
                        "-f","null","-"],check=True,timeout=30)

if __name__=="__main__":
    unittest.main()
