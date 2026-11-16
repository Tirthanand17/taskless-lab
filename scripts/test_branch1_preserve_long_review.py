"""Synthetic tests: staging preserves identity without releasing to YouTube."""
from copy import deepcopy
from pathlib import Path
import unittest
from scripts.branch1_preserve_long_review import (
    EXPECTED_VIDEO_SHA,EXPECTED_CAPTION_SHA,EPISODE,
    PrivateReviewRefused,proof,VIDEO,CAPTIONS,RECEIPT,MOTION
)

class PreserveLongReviewTests(unittest.TestCase):
    def setUp(self):
        self.receipt={
            "schema":"FLOWMINUTE_B1_EXECUTED_PYTHON_LONG_V1",
            "episode_id":EPISODE,
            "status":"LONG_REAL_PYTHON_EXECUTED_SOURCE_OWNER_REVIEW_ONLY",
            "final_sha256":EXPECTED_VIDEO_SHA,
            "caption_sha256":EXPECTED_CAPTION_SHA,
            "duration_seconds":214.833,
            "true_software_execution":True,"fictional_data_only":True,
            "raw_csv_rows":8,"clean_csv_rows":6,
            "raw_total":"2656.25","clean_total":"1430.75",
            "owner_watched":False,"rights_signed":False,
            "publishing_authorized":False,
            "youtube_uploads":0,"youtube_schedules":0,
            "independent_encoded_aac_mastering":{
                "exact_original_mp4_sha256":EXPECTED_VIDEO_SHA,
                "integrated_lufs_and_true_peak_within_internal_band":True,
                "human_listening_and_mobile_playback_verified":False,
                "rights_and_facts_approved":False,
                "youtube_upload_or_release_authorized":False
            }
        }
        self.motion={
            "schema":"FLOWMINUTE_B1_LONG_REAL_SOURCE_PIXEL_V1",
            "final_sha256":EXPECTED_VIDEO_SHA,
            "status":"PASS_LONG_SOURCE_MOTION_HUMAN_REVIEW_REQUIRED",
            "static_screen_risk":False,
            "real_first_three_second_change":True,
            "owner_creative_approval":False,
            "youtube_uploads":0,"youtube_schedules":0
        }

    def verify(self,receipt=None,motion=None,video=EXPECTED_VIDEO_SHA,
               captions=EXPECTED_CAPTION_SHA):
        return proof(video,captions,
                     receipt if receipt is not None else self.receipt,
                     motion if motion is not None else self.motion)

    def test_original_review_only_source_permitted_for_preservation(self):
        summary=self.verify()
        self.assertEqual(summary["video_sha256"],EXPECTED_VIDEO_SHA)
        self.assertEqual(summary["caption_sha256"],EXPECTED_CAPTION_SHA)
        self.assertFalse(summary["owner_rights_fact_captions_signature_verified"])
        self.assertFalse(summary["youtube_authenticated_channel_readback"])
        self.assertFalse(summary["automatic_public_release"])
        self.assertEqual(summary["youtube_uploads"],0)
        self.assertEqual(summary["youtube_schedules"],0)
        self.assertEqual(summary["release_status"],
                         "NOT_RELEASED_AWAIT_OWNER_OAUTH_AND_SIGNED_RELEASE")

    def test_exact_video_or_captions_must_not_be_replaced(self):
        for key,value in (("video","f"*64),("captions","a"*64)):
            with self.subTest(key=key):
                kwargs={key:value}
                with self.assertRaises(PrivateReviewRefused):
                    self.verify(**kwargs)

    def test_forged_creator_signoff_and_fake_media_cannot_pass(self):
        for key,bad in (
            ("owner_watched",True),("rights_signed",True),
            ("publishing_authorized",True),("youtube_uploads",1),
            ("youtube_schedules",1),("true_software_execution",False),
            ("raw_total","2000.00"),("clean_csv_rows",7),
            ("duration_seconds",215.0),("final_sha256","0"*64)
        ):
            with self.subTest(field=key):
                altered=deepcopy(self.receipt);altered[key]=bad
                with self.assertRaises(PrivateReviewRefused):
                    self.verify(receipt=altered)
        for key,bad in (
            ("static_screen_risk",True),("owner_creative_approval",True),
            ("real_first_three_second_change",False),
            ("status","REJECT_LONG_STATIC_SOURCE")
        ):
            with self.subTest(field=key):
                altered=deepcopy(self.motion);altered[key]=bad
                with self.assertRaises(PrivateReviewRefused):
                    self.verify(motion=altered)

    def test_no_bypass_of_separate_audio_or_rights(self):
        for key,bad in (
            ("integrated_lufs_and_true_peak_within_internal_band",False),
            ("human_listening_and_mobile_playback_verified",True),
            ("rights_and_facts_approved",True),
            ("youtube_upload_or_release_authorized",True)
        ):
            a=deepcopy(self.receipt)
            a["independent_encoded_aac_mastering"][key]=bad
            with self.assertRaises(PrivateReviewRefused):
                self.verify(receipt=a)

    def test_cloud_runner_uses_real_mp4_frame_not_generated_screenshot(self):
        src=(Path(__file__).parent/"branch1_preserve_long_review.py").read_text("utf8")
        self.assertIn('"-ss","1.8","-i",str(paths[VIDEO])',src)
        self.assertIn('"scale=1280:720:flags=lanczos"',src)
        self.assertIn("shutil.copyfile(item,destination/item.name)",src)
        self.assertNotIn("publish_youtube(",src)
        self.assertNotIn("googleapiclient",src)
        self.assertNotIn("oauth2",src)

if __name__=="__main__":
    unittest.main()
