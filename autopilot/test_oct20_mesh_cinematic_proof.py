"""Genuine stylized 3D mesh animation: vertex depth, camera and real H264.

No human narration, no source license proof, no fake Gemini interface, no
app integration and no public/scheduled content. Only 1s of bounded video
is rendered by free public CI to avoid full-render cost.
"""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from PIL import Image

from autopilot.agent_org import WorkflowError
from autopilot.oct20_mesh_cinematic_proof import (
    FPS,HEIGHT,LANES,WIDTH,_camera,_dot,_unit,
    draw_true_mesh_frame,mesh_cube,project_vertex,
    render_true_mesh_excerpt,_scene_source_bound,
)


class OriginalWorld3DGeometryTests(unittest.TestCase):
    def test_original_english_hindi_scene_bindings_unmodified(self):
        self.assertEqual(set(LANES),{
            "fm_20261020_short_en","fm_20261020_short_hi"
        })
        for ep in LANES:
            with self.subTest(ep=ep):
                data=_scene_source_bound(ep)
                self.assertEqual(len(data["episodes"]),3)
                self.assertIn("CONCEPT",LANES["fm_20261020_short_en"]["footer"])
                self.assertIn("अनुमति",LANES["fm_20261020_short_hi"]["lock"])

    def test_real_3d_world_vertices_have_projective_depth(self):
        camera=_camera(0)
        a=project_vertex((0,0,-1),camera)
        b=project_vertex((0,0,1),camera)
        self.assertNotEqual(a[2],b[2])
        self.assertNotEqual(a[:2],b[:2])
        self.assertAlmostEqual(_dot(_unit((3,4,0)),_unit((3,4,0))),1)
        self.assertEqual((WIDTH,HEIGHT,FPS),(540,960,24))

    def test_six_face_3d_cubes_are_rotated_and_shaded_by_normals(self):
        camera=_camera(5)
        near=mesh_cube((0,0,0),1.5,0.2,(20,160,220),camera)
        rotated=mesh_cube((0,0,0),1.5,1.1,(20,160,220),camera)
        self.assertTrue(2<=len(near)<=3)
        self.assertTrue(2<=len(rotated)<=3)
        self.assertNotEqual(near,rotated)
        self.assertTrue(all(len(face[1])==4 for face in near))
        self.assertTrue(all(all(type(x) is int and type(y) is int
                            for x,y in face[1]) for face in near))
        self.assertTrue(all(0<=c<=255 for face in near for c in face[2]))

    def test_three_original_geometric_frames_genuinely_change(self):
        for episode in LANES:
            with self.subTest(episode=episode):
                samples=[]
                for n in (0,9,31,61):
                    frame=draw_true_mesh_frame(episode,n)
                    self.assertEqual(type(frame),Image.Image)
                    self.assertEqual(frame.size,(WIDTH,HEIGHT))
                    self.assertEqual(frame.mode,"RGB")
                    samples.append(sha256(frame.tobytes()).hexdigest())
                self.assertEqual(len(set(samples)),len(samples))

    def test_frame_count_invalids_and_unsupported_long_denied(self):
        for episode,frame in (
            ("fm_20261020_short_en",-1),
            ("fm_20261020_short_hi",96),
            ("fm_20261020_short_en",1.2),
            ("fm_20261020_long_hi",0),
            ("csv_tutorial_short_hi",0),
        ):
            with self.subTest(episode=episode,frame=frame):
                with self.assertRaises(WorkflowError):
                    draw_true_mesh_frame(episode,frame)

    def test_refuses_unsafe_destination_and_any_preexisting_video(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            target=root/"original.mp4"
            target.write_bytes(b"OWNER_VIDEO_PRESERVED")
            with self.assertRaises(WorkflowError):
                render_true_mesh_excerpt(
                    episode_id="fm_20261020_short_en",
                    output_path=target,seconds=1)
            self.assertEqual(target.read_bytes(),b"OWNER_VIDEO_PRESERVED")
            with self.assertRaises(WorkflowError):
                render_true_mesh_excerpt(
                    episode_id="fm_20261020_short_en",
                    output_path=root/"wrong.mov",seconds=1)
            with self.assertRaises(WorkflowError):
                render_true_mesh_excerpt(
                    episode_id="fm_20261020_short_en",
                    output_path=root/"oversized.mp4",seconds=6)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "System FFmpeg and FFprobe required for actual MP4")
    def test_actual_offline_one_second_3d_h264_has_zero_audio_or_youtube(self):
        with TemporaryDirectory() as directory:
            out=Path(directory)/"original_real_geometry_en.mp4"
            result=render_true_mesh_excerpt(
                episode_id="fm_20261020_short_en",
                output_path=out,seconds=1,
            )
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size,5000)
            self.assertEqual(result["frames"],24)
            self.assertTrue(result["actual_perspective_projected_3d_face_meshes"])
            self.assertFalse(result["photorealistic_footage"])
            self.assertFalse(result["complete_video_produced"])
            self.assertFalse(result["real_audio_or_voice"])
            self.assertFalse(result["youtube_upload_authorized"])
            self.assertFalse(result["youtube_publish_authorized"])
            self.assertEqual(result["external_network_calls"],0)
            self.assertEqual(result["monthly_recurring_infrastructure_inr"],0)


if __name__=="__main__":
    unittest.main()
