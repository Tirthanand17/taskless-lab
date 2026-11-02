"""Regression tests: technical checks must never be conflated with upload QA."""
from dataclasses import replace
import unittest
from autopilot.premium_preview_qa import MediaFacts, MotionFacts, PreviewQAError, validate_preview

M=MediaFacts(10.,960,540,12.,120,"h264","aac",True)
V=MotionFacts((12.747,20.037,17.777),"real_3d_geometry","sandbox_render_reference")

class CinematicPreviewTests(unittest.TestCase):
    def test_baseline(self):
        result=validate_preview(M,V)
        self.assertTrue(result["technical_preview_valid"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["youtube_scheduled"])
        self.assertEqual(result["audio_track"],"sound_effects_only")

    def test_bad_decode(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(replace(M,fully_decoded=False),V)

    def test_bad_frame_count(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(replace(M,frames=20),V)

    def test_bad_resolution(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(replace(M,width=320),V)

    def test_not_an_image_parallax(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(M,replace(V,renderer_kind="flat_still_pan"))

    def test_static_frames(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(M,replace(V,between_keyframe_mae=(0.01,0.02,0.1)))

    def test_source_missing(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(M,replace(V,source_reference=""))

    def test_no_self_authorization(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(M,V,release_authorized=True)
        with self.assertRaises(PreviewQAError):
            validate_preview(M,V,independently_approved=True)

    def test_speech_does_not_grant_rights(self):
        state=validate_preview(M,V,has_speech=True)
        self.assertFalse(state["voice_license_reviewed"])

    def test_silent_preview_stays_blocked(self):
        state=validate_preview(replace(M,audio_codec="none"),V)
        self.assertEqual(state["audio_track"],"silent")
        self.assertFalse(state["release_authorized"])

    def test_wrong_duration(self):
        with self.assertRaises(PreviewQAError):
            validate_preview(replace(M,duration_seconds=3),V)

    def test_inspection_is_not_approval(self):
        r=validate_preview(M,V,reviewed_character_motion=True)
        self.assertFalse(r["release_authorized"])
        self.assertFalse(r["full_episode_rendered"])

if __name__=="__main__":
    unittest.main()
