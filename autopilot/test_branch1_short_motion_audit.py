"""Independent motion-audit tests use source-free fabricated grayscale frames."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from autopilot.branch1_short_motion_audit import (
    FORMAT,FRAME_BYTES,MIN_BYTES,ScreenAuditRefused,inspect_receipt,
    plane_score,audit,MAX_STATIC_SECONDS,
)

def frame(i:int)->bytes:
    # High local contrast and changes from independent synthetic patterns.
    return bytes(((n*13+(n//80)*7+i*5)%256 for n in range(FRAME_BYTES)))

class MotionAuditTests(unittest.TestCase):
    def test_real_motion_eligible_only_for_human_review(self):
        planes=[frame(i) for i in range(76)]
        report=plane_score(planes,38.)
        self.assertFalse(report["high_risk_static_pacing"])
        self.assertLess(report["longest_near_frozen_seconds"],MAX_STATIC_SECONDS)
        self.assertTrue(report["first_three_seconds_show_visible_change"])
        self.assertGreater(report["median_grayscale_contrast"],9)

    def test_frozen_app_content_cannot_pass_due_to_caption_churn(self):
        picture=frame(7)
        report=plane_score([picture]*76,38.)
        self.assertTrue(report["high_risk_static_pacing"])
        self.assertIn("LONG_FROZEN_APPLICATION_PIXELS",report["reasons"])
        self.assertIn("EXCESSIVE_STATIC_PIXEL_COVERAGE",report["reasons"])
        self.assertEqual(report["longest_near_frozen_seconds"],37.5)
        self.assertFalse(report["first_three_seconds_show_visible_change"])

    def test_delayed_first_action_caught_even_if_later_video_moves(self):
        p=[frame(1)]*9+[frame(i+10) for i in range(67)]
        report=plane_score(p,38)
        self.assertTrue(report["high_risk_static_pacing"])
        self.assertIn("NO_CHANGE_IN_FIRST_THREE_SECONDS",report["reasons"])
        self.assertIn("LONG_FROZEN_APPLICATION_PIXELS",report["reasons"])

    def test_bad_or_missing_pixels_refused(self):
        for frames in (
            [],[b"xyz"]*70,[frame(i) for i in range(12)],
            [frame(i) for i in range(180)]
        ):
            with self.subTest(length=len(frames)):
                with self.assertRaises(ScreenAuditRefused):
                    plane_score(frames,38)
        with self.assertRaises(ScreenAuditRefused):
            plane_score([frame(i) for i in range(76)],float("nan"))

    def test_nearly_blank_video_not_equal_to_engaging_app_video(self):
        p=[bytes([i%256])*FRAME_BYTES for i in range(76)]
        r=plane_score(p,38)
        self.assertTrue(r["high_risk_static_pacing"])
        self.assertIn("POSSIBLE_BLANK_OR_LOW_CONTRAST_APPLICATION",r["reasons"])

    def test_refuse_forged_release_and_exact_media_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            mp4=folder/"NARRATED_REAL_APP_REVIEW_ONLY.mp4"
            mp4.write_bytes(b"\0"*MIN_BYTES)
            digest=hashlib.sha256(mp4.read_bytes()).hexdigest()
            record={
                "schema":"FLOWMINUTE_B1_NARRATED_REAL_APP_V1",
                "status":"B1_REAL_APP_NARRATED_VIDEO_REQUIRES_HUMAN_REVIEW_NO_YOUTUBE",
                "app":"calc",
                "real_recording_pixel_source":True,
                "postencoded_audio_verified":True,
                "owner_final_watch":False,
                "release_signed":False,
                "youtube_uploads":0,
                "youtube_schedules":0,
                "narrated_mp4_sha256":digest,
                "narrated_mp4_bytes":MIN_BYTES,
                "duration_seconds":38.,
            }
            receipt=folder/"receipt.json"
            receipt.write_text(json.dumps(record),"utf8")
            self.assertEqual(inspect_receipt(receipt,mp4)["app"],"calc")
            # Synthetic zero bytes are NOT a video. The stream check must
            # reject them at ffprobe; identity check is a separate gate.
            with self.assertRaises(ScreenAuditRefused):
                audit(mp4,receipt)
            for key,value in (
                ("release_signed",True),("owner_final_watch",True),
                ("youtube_uploads",1),("youtube_schedules",1),
                ("postencoded_audio_verified",False),
                ("real_recording_pixel_source",False),
                ("app","mock_ui"),("narrated_mp4_sha256","f"*64),
            ):
                with self.subTest(k=key):
                    bad={**record,key:value}
                    receipt.write_text(json.dumps(bad),"utf8")
                    with self.assertRaises(ScreenAuditRefused):
                        inspect_receipt(receipt,mp4)
            receipt.write_text(json.dumps(record),"utf8")
            mp4.write_bytes(mp4.read_bytes()+b"A")
            with self.assertRaises(ScreenAuditRefused):
                inspect_receipt(receipt,mp4)

if __name__=="__main__":
    unittest.main()
