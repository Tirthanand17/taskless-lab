"""Clivox A5 media benchmark validator: original-only, fail closed."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest

from scripts.branch3_a5_render_original_demo import (
    DEFAULT,RenderDenied,CLIVOX,visual_script_srt,create_demo
)
from scripts.branch3_a5_media_qa import (
    MediaQARejected,check_metadata,check_srt,
)

def fixture():
    return json.loads(DEFAULT.read_text(encoding="utf-8"))

def baseline_manifest():
    return {
        "schema_version":1,
        "channel_id":CLIVOX,
        "stage":"A5_ORIGINAL_ONLY_SYNTHETIC_BENCHMARK",
        "mode":"preview",
        "video_sha256":"a"*64,
        "srt_sha256":"b"*64,
        "source_media_attached":False,
        "third_party_source_audio_used":False,
        "original_voiceover_recorded":False,
        "source_placeholder_visible":True,
        "audio_content":"LOW_VOLUME_ORIGINAL_SYNTHETIC_TONES_NOT_NARRATION",
        "subtitle_content":"PROPOSED_ON_SCREEN_EDITORIAL_TEXT_NOT_SPEECH_TRANSCRIPT",
        "watermark":"DEMO ONLY / NOT CLEARED FOR YOUTUBE RELEASE",
        "reviewed_by_human":False,
        "actual_media_qa_passed":False,
        "copyright_clearance_verified":False,
        "ready_to_upload":False,
        "ready_to_schedule":False,
        "ready_to_publish":False,
    }

def baseline_probe():
    return {
        "streams":[
            {"codec_type":"video","codec_name":"h264",
             "width":540,"height":960,"pix_fmt":"yuv420p",
             "avg_frame_rate":"24/1"},
            {"codec_type":"audio","codec_name":"aac",
             "sample_rate":"48000","channels":1}
        ],
        "format":{"duration":"40.001","size":"1000000"}
    }

class A5Tests(unittest.TestCase):
    def test_original_blueprint_required(self):
        with self.assertRaises(RenderDenied):
            create_demo(fixture(),Path("/nonexistent-clivox-a5-output"),"preview")
        with self.assertRaises(RenderDenied):
            create_demo(fixture(),Path("/tmp"),"third_party")
        f=fixture()
        f["release_locks"]["youtube_upload_authorized"]=True
        with self.assertRaises(Exception):
            create_demo(f,Path("/tmp"),"preview")

    def test_srt_generation_from_source_free_beat_timeline(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"text.srt"
            visual_script_srt(fixture()["beats"],target)
            data=target.read_text("utf-8")
            report=check_srt(data,40)
            self.assertGreaterEqual(report["cue_count"],5)
            self.assertFalse(report["is_audio_transcript"])
            self.assertIn("SOURCE PLACEHOLDER",data)
            self.assertNotIn("real speaker said",data)

    def test_probe_passes_only_as_non_releasable_synthetic_benchmark(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"text.srt"
            visual_script_srt(fixture()["beats"],target)
            report=check_metadata(baseline_probe(),baseline_manifest(),target.read_text("utf-8"))
            self.assertTrue(report["synthetic_video_technical_checks_passed"])
            self.assertFalse(report["ready_to_publish"])
            self.assertFalse(report["youtube_upload_authorized"])
            self.assertFalse(report["licensed_media_qa_completed"])
            self.assertFalse(report["voiceover_and_production_mix_qa_completed"])

    def test_wrong_channel_and_approval_spoof_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"text.srt"
            visual_script_srt(fixture()["beats"],target)
            srt=target.read_text("utf-8")
            for key,val in (
                ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
                ("stage","A5_READY_FOR_PUBLISH"),
                ("mode","copyrighted_source"),
                ("source_media_attached",True),
                ("third_party_source_audio_used",True),
                ("original_voiceover_recorded",True),
                ("source_placeholder_visible",False),
                ("reviewed_by_human",True),
                ("actual_media_qa_passed",True),
                ("copyright_clearance_verified",True),
                ("ready_to_upload",True),
                ("ready_to_schedule",True),
                ("ready_to_publish",True),
                ("watermark",""),
                ("video_sha256","forged"),
            ):
                man=baseline_manifest()
                man[key]=val
                with self.subTest(key=key),self.assertRaises(MediaQARejected):
                    check_metadata(baseline_probe(),man,srt)

    def test_bad_video_and_audio_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"text.srt"
            visual_script_srt(fixture()["beats"],target)
            srt=target.read_text("utf-8")
            cases=(
                ("video","codec_name","vp9"),
                ("video","width",1920),
                ("video","height",1080),
                ("video","pix_fmt","yuv444p"),
                ("video","avg_frame_rate","25/1"),
                ("audio","codec_name","mp3"),
                ("audio","sample_rate","44100"),
                ("audio","channels",0),
            )
            for typ,key,val in cases:
                p=baseline_probe()
                index=0 if typ=="video" else 1
                p["streams"][index][key]=val
                with self.subTest(key=key,val=val),self.assertRaises(MediaQARejected):
                    check_metadata(p,baseline_manifest(),srt)
            p=baseline_probe()
            p["format"]["duration"]="37"
            with self.assertRaises(MediaQARejected):
                check_metadata(p,baseline_manifest(),srt)

    def test_caption_malformed_and_mobile_readability_denied(self):
        for text in (
            "1\n00:00:00,000 --> 00:00:10,000\none\n",
            "1\n00:00:02,000 --> 00:00:01,000\nbad\n",
            "1\n00:00:00,000 --> 00:00:02,000\n"+"a"*100+"\n",
        ):
            with self.subTest(text=text[:30]),self.assertRaises(MediaQARejected):
                check_srt(text,40)

if __name__=="__main__":
    unittest.main()
