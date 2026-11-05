"""Real-pixel sample QA and conservative nonpublication regression checks."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_visual_signal_audit import (
    EPISODES,_sample_times,_probe,_thumb,
    analyze_rgb_samples,inspect_authored_visual_signal,
)


class VisualSampleStatsTests(unittest.TestCase):
    @staticmethod
    def frame(offset:int, *,w:int=16,h:int=12)->bytes:
        return bytes((offset+i*17)%256 for i in range(w*h*3))

    def test_different_visible_frames_pass_signal_only(self):
        sample=tuple(self.frame(i*37) for i in range(4))
        x=analyze_rgb_samples(sample,width=16,height=12)
        self.assertEqual(x["status"],"VISUAL_SIGNAL_QA_PASS_UNPUBLISHABLE")
        self.assertEqual(x["issues"],[])
        self.assertEqual(x["sample_count"],4)
        self.assertEqual(len(x["sample_sha256"]),4)
        self.assertFalse(x["human_visual_review_observed"])
        self.assertFalse(x["factual_csv_explanation_verified"])
        self.assertFalse(x["actual_caption_legibility_verified"])
        self.assertFalse(x["youtube_publishing_authorized"])

    def test_black_and_flat_frames_need_review(self):
        x=analyze_rgb_samples((bytes(16*12*3),self.frame(42)),width=16,height=12)
        self.assertEqual(x["status"],"VISUAL_SIGNAL_QA_REVIEW_REQUIRED")
        self.assertIn("BLANK_BLACK_SCENE_SAMPLE",x["issues"])
        self.assertIn("VERY_LOW_CONTRAST_SCENE_SAMPLE",x["issues"])

    def test_identical_and_near_identical_scenes_flagged(self):
        single=self.frame(9)
        x=analyze_rgb_samples((single,single,single),width=16,height=12)
        self.assertIn("DUPLICATE_EXACT_SCENE_SAMPLES",x["issues"])
        self.assertIn("NEAR_STATIC_ACROSS_ADJACENT_SAMPLED_SCENES",x["issues"])

    def test_bounded_data_and_byte_integrity(self):
        for data,shape in (
            ((self.frame(4),),(16,12)),
            ((self.frame(4),self.frame(7)),(500,500)),
            ((b"x",self.frame(7)),(16,12)),
            ((None,self.frame(7)),(16,12)),
        ):
            with self.subTest(shape=shape),self.assertRaises(WorkflowError):
                analyze_rgb_samples(data,width=shape[0],height=shape[1])

    def test_expected_authored_samples_and_formats(self):
        self.assertEqual(len(EPISODES),3)
        for ep in ("csv_tutorial_short_en","csv_tutorial_short_hi"):
            self.assertEqual(_sample_times(ep),(0.5,10.5,20.5,30.5,41.5))
            self.assertEqual(EPISODES[ep],(42,1080,1920,24,1008))
        samples=_sample_times("csv_tutorial_long_hi")
        self.assertEqual(len(samples),26)
        self.assertEqual(samples[:3],(0.5,9.0,27.0))
        self.assertEqual(samples[-2:],(423.0,431.5))
        self.assertEqual(EPISODES["csv_tutorial_long_hi"],
                         (432,1920,1080,24,10368))
        with self.assertRaises(WorkflowError):
            _sample_times("other")

    def test_authored_long_storyboard_scene_change_diagnostic(self):
        # A cheap but real Pillow pixel regression, not an MP4 or speech proof.
        # Uses the exact long-video authored scene sample clock and reports
        # any near-static neighboring images with precise timestamps.
        from PIL import Image
        from autopilot.phase3_hindi_visual_preview import render_hindi_frame
        stamps=_sample_times("csv_tutorial_long_hi")
        raw=tuple(render_hindi_frame(
            "csv_tutorial_long_hi",t,width=640
        ).resize((160,90),Image.Resampling.BILINEAR).tobytes() for t in stamps)
        metrics=analyze_rgb_samples(raw,width=160,height=90)
        violations=[
            (stamps[i],stamps[i+1],delta)
            for i,delta in enumerate(metrics["adjacent_mean_absolute_rgb_change"])
            if delta<1.0
        ]
        self.assertEqual(violations,[],f"Near-static authored scenes: {violations}")

    def test_missing_or_tampered_video_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"none.mp4"
            with self.assertRaises(WorkflowError):
                inspect_authored_visual_signal(
                    episode_id="csv_tutorial_short_en",path=p)
            p.write_bytes(b"not-real-mp4")
            with self.assertRaises(WorkflowError):
                inspect_authored_visual_signal(
                    episode_id="csv_tutorial_short_hi",path=p)
            with self.assertRaises(WorkflowError):
                inspect_authored_visual_signal(
                    episode_id="not_a_real_video",path=p)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Requires local pre-installed ffmpeg and ffprobe")
    def test_decodes_real_video_pixel_sample(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"actual_test_signal.mp4"
            subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-f","lavfi",
                 "-i","testsrc2=s=160x90:r=24:d=2",
                 "-t","2","-an","-c:v","libx264","-pix_fmt","yuv420p",
                 str(p)],
                stdin=subprocess.DEVNULL,capture_output=True,
                check=True,timeout=25)
            w,h,n,fps,dur=_probe(p)
            self.assertEqual((w,h,n),(160,90,48))
            self.assertAlmostEqual(fps,24)
            self.assertAlmostEqual(dur,2,places=2)
            first=_thumb(p,.5,width=160,height=90)
            second=_thumb(p,1.5,width=160,height=90)
            self.assertEqual(len(first),160*90*3)
            self.assertNotEqual(first,second)
            r=analyze_rgb_samples((first,second),width=160,height=90)
            self.assertFalse(r["youtube_publishing_authorized"])
            self.assertEqual(r["sample_count"],2)


if __name__=="__main__":
    unittest.main()
