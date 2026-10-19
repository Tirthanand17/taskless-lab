"""Real original seven-scene EN/HI projected 3D animation binding.

CI validates the complete 42/44s scene plan and renders only a bounded
one-second actual FFmpeg H264 silent geometry clip. No new downloads, human
voice, licensed audio, ASR, Google OAuth, upload or publishing.
"""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from PIL import Image

from autopilot.agent_org import WorkflowError
from autopilot.oct20_full_mesh_story_timeline import (
    FPS,HEIGHT,SCENE_STORIES,TOTAL_FRAMES,WIDTH,
    _authored_cuts,_scene_for_frame,draw_oct20_full_mesh_frame,
    render_oct20_full_mesh_review,
)


class Oct20SevenSceneOriginalMeshTests(unittest.TestCase):
    def test_exact_english_hindi_source_storyboard_all_seven_scenes(self):
        self.assertEqual(set(SCENE_STORIES),{
            "fm_20261020_short_en","fm_20261020_short_hi"})
        for ep,expected in TOTAL_FRAMES.items():
            with self.subTest(ep=ep):
                cuts=_authored_cuts(ep)
                self.assertEqual(len(cuts),7)
                self.assertEqual(len(SCENE_STORIES[ep]),7)
                self.assertEqual(cuts[0].start_frame,0)
                self.assertEqual(cuts[-1].end_frame,expected)
                self.assertEqual(sum(c.end_frame-c.start_frame
                                     for c in cuts),expected)
                self.assertEqual([x.scene_index for x in cuts],list(range(7)))
                for cut in cuts:
                    self.assertIs(_scene_for_frame(ep,cut.start_frame),cut)
                    self.assertIs(_scene_for_frame(ep,cut.end_frame-1),cut)

    def test_seven_distinct_english_and_hindi_original_story_cues(self):
        for ep,scenes in SCENE_STORIES.items():
            with self.subTest(ep=ep):
                self.assertEqual(len(scenes),7)
                titles=[scene[0] for scene in scenes]
                self.assertEqual(len(set(titles)),7)
                self.assertTrue(all(len(scene)==4 for scene in scenes))
                self.assertTrue(all(len(s[2]) in (3,4) for s in scenes))
                self.assertTrue(any(len(s[2])==4 for s in scenes))
                self.assertTrue(all(len(s[3])>8 for s in scenes))
                if ep.endswith("_hi"):
                    for header,subtitle,labels,lock in scenes:
                        content="".join((header,subtitle,*labels,lock))
                        self.assertTrue(any("\u0900"<=c<="\u097f" for c in content))
                else:
                    self.assertTrue(all(all(ord(c)<128 for c in
                        scene[0]+scene[1]+scene[3]) for scene in scenes))

    def test_actual_mesh_frames_at_every_original_scene_start_are_distinct(self):
        for episode in SCENE_STORIES:
            seen=[]
            for cut in _authored_cuts(episode):
                with self.subTest(episode=episode,scene=cut.scene_index):
                    image=draw_oct20_full_mesh_frame(episode,cut.start_frame)
                    self.assertIs(type(image),Image.Image)
                    self.assertEqual(image.mode,"RGB")
                    self.assertEqual(image.size,(WIDTH,HEIGHT))
                    seen.append(sha256(image.tobytes()).hexdigest())
            self.assertEqual(len(set(seen)),7)

    def test_true_polygon_frame_moves_during_an_ordinary_scene(self):
        for ep in SCENE_STORIES:
            with self.subTest(episode=ep):
                a=draw_oct20_full_mesh_frame(ep,0)
                b=draw_oct20_full_mesh_frame(ep,5)
                c=draw_oct20_full_mesh_frame(ep,15)
                self.assertEqual(len({
                    sha256(img.tobytes()).hexdigest() for img in (a,b,c)
                }),3)

    def test_end_frame_exact_and_invalid_scene_episode_denied(self):
        for ep,last in TOTAL_FRAMES.items():
            with self.subTest(episode=ep):
                self.assertEqual(_scene_for_frame(ep,last-1).scene_index,6)
                for frame in (-1,last,last+1,True,1.1):
                    with self.assertRaises(WorkflowError):
                        draw_oct20_full_mesh_frame(ep,frame)
        for ep in ("fm_20261020_long_hi","csv_tutorial_short_en","bogus",None):
            with self.subTest(ep=str(ep)),self.assertRaises(WorkflowError):
                _authored_cuts(ep)

    def test_existing_destination_never_overwritten_or_unsafe_output(self):
        with TemporaryDirectory() as tmp:
            destination=Path(tmp)/"owner.mp4"
            destination.write_bytes(b"OWNER_ASSET_NOT_FOR_REPLACEMENT")
            with self.assertRaises(WorkflowError):
                render_oct20_full_mesh_review(
                    episode_id="fm_20261020_short_en",
                    output_path=destination,smoke_one_second=True)
            self.assertEqual(destination.read_bytes(),
                             b"OWNER_ASSET_NOT_FOR_REPLACEMENT")
            for invalid in (
                Path(tmp)/"wrong.mkv",
                Path(tmp)/"missing_dir"/"future.mp4",
            ):
                with self.assertRaises(WorkflowError):
                    render_oct20_full_mesh_review(
                        episode_id="fm_20261020_short_hi",
                        output_path=invalid,smoke_one_second=True)
                self.assertFalse(invalid.exists())

    def test_fake_smoke_mode_and_long_episode_cannot_enter_render(self):
        with TemporaryDirectory() as tmp:
            for fake in (1,0,None,"false",.1):
                with self.subTest(fake=str(fake)),self.assertRaises(WorkflowError):
                    render_oct20_full_mesh_review(
                        episode_id="fm_20261020_short_en",
                        output_path=Path(tmp)/"bad.mp4",
                        smoke_one_second=fake)
            with self.assertRaises(WorkflowError):
                render_oct20_full_mesh_review(
                    episode_id="fm_20261020_long_hi",
                    output_path=Path(tmp)/"no_long.mp4")
            self.assertFalse((Path(tmp)/"no_long.mp4").exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe must already be installed")
    def test_real_one_second_3d_geometry_ffmpeg_video_only_gate(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)/"short3d_silent_smoke.mp4"
            receipt=render_oct20_full_mesh_review(
                episode_id="fm_20261020_short_en",
                output_path=output,smoke_one_second=True)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size,3000)
            self.assertEqual(receipt["status"],
                             "SOURCE_LOCKED_7_SCENE_ORIGINAL_3D_SILENT_REVIEW_ONLY")
            self.assertEqual(receipt["script_total_seconds"],42)
            self.assertEqual(receipt["render_seconds"],1)
            self.assertEqual(receipt["frames"],24)
            self.assertEqual(receipt["audio_tracks"],0)
            self.assertEqual(receipt["authored_script_scenes"],7)
            self.assertEqual(receipt["rendered_scenes"],1)
            self.assertFalse(receipt["all_seven_script_scenes_rendered"])
            self.assertTrue(receipt["actually_rendered_3d_geometry"])
            for claim in (
                "photorealistic_final_video",
                "human_voice_recorded_or_verified",
                "spoken_subtitle_alignment_verified",
                "commercial_voice_rights_verified",
                "youtube_upload_authorized","youtube_publish_authorized",
            ):
                self.assertIs(receipt[claim],False)
            self.assertEqual(receipt["external_service_calls"],0)
            self.assertEqual(receipt["monthly_recurring_infrastructure_inr"],0)


if __name__=="__main__":
    unittest.main()
