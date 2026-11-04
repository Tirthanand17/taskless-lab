"""No-network/no-model fast tests for pinned cloud voice/video benchmark gates."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from autopilot.cloud_av_probe import (
    MODEL_NAME, MODEL_SHA256, VOICES_NAME, VOICES_SHA256, SLOTS,
    ProbeError, sha256_stream, verify_pinned_assets, check_media, render_probe,
)


class MediaProbeTests(unittest.TestCase):
    def test_upstream_pinned_release_hashes_and_three_different_voices(self):
        self.assertEqual(len(MODEL_SHA256), 64)
        self.assertEqual(len(VOICES_SHA256), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in MODEL_SHA256 + VOICES_SHA256))
        self.assertEqual(MODEL_NAME, "kokoro-v1.0.int8.onnx")
        self.assertEqual(VOICES_NAME, "voices-v1.0.bin")
        self.assertEqual([x[0] for x in SLOTS], ["short_am", "long", "short_pm"])
        self.assertEqual([x[1] for x in SLOTS], ["short", "long", "short"])
        self.assertEqual(len({x[2] for x in SLOTS}), 3)
        self.assertEqual(len({x[3] for x in SLOTS}), 3)

    def test_sha256_stream_and_bounded_file_size(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"fake.onnx"
            p.write_bytes(b"abc")
            self.assertEqual(sha256_stream(p,max_bytes=3),
                             (hashlib.sha256(b"abc").hexdigest(),3))
            with self.assertRaises(ProbeError):
                sha256_stream(p,max_bytes=2)

    def test_invalid_weights_cannot_load(self):
        with tempfile.TemporaryDirectory() as temp:
            m=Path(temp)/MODEL_NAME
            v=Path(temp)/VOICES_NAME
            m.write_bytes(b"fake model")
            v.write_bytes(b"fake voices")
            with self.assertRaisesRegex(ProbeError,"SHA256"):
                verify_pinned_assets(m,v)
            with self.assertRaises(ProbeError):
                verify_pinned_assets(Path(temp)/"bad-model.onnx",v)

    def test_symlink_weights_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            real=d/"real-model"
            real.write_bytes(b"abc")
            link=d/MODEL_NAME
            try:
                link.symlink_to(real)
            except (OSError,NotImplementedError):
                self.skipTest("No local symlinks")
            voice=d/VOICES_NAME
            voice.write_bytes(b"123")
            with self.assertRaises(ProbeError):
                verify_pinned_assets(link,voice)

    def _metadata(self,kind="short",*,width=None,height=None,vcodec="h264",
                  acodec="aac",duration="4.0",pix_fmt="yuv420p"):
        w,h=(1920,1080) if kind=="long" else (1080,1920)
        return {"format":{"duration":duration},
                "streams":[
                    {"codec_type":"video","codec_name":vcodec,
                     "width":width if width is not None else w,
                     "height":height if height is not None else h,"pix_fmt":pix_fmt},
                    {"codec_type":"audio","codec_name":acodec}]}

    def _check(self,metadata,kind="short"):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"demo.mp4"
            p.write_bytes(b"generated demo placeholder for mocked ffprobe")
            def fake_execute(command,*,timeout_s=120):
                if command[0]=="ffprobe":
                    return subprocess.CompletedProcess(command,0,stdout=json.dumps(metadata),stderr="")
                if command[0]=="ffmpeg":
                    return subprocess.CompletedProcess(command,0,stdout="",stderr="")
                raise AssertionError("unexpected tool")
            with patch("autopilot.cloud_av_probe.execute",side_effect=fake_execute):
                return check_media(p,kind)

    def test_metadata_checks_and_full_decode_branch(self):
        qa=self._check(self._metadata())
        self.assertEqual(qa["width"],1080)
        self.assertEqual(qa["height"],1920)
        self.assertTrue(qa["full_decode_passed"])
        self.assertFalse(qa["video_ready_to_publish"])
        self.assertFalse(qa["viewer_or_rights_review_performed"])
        self.assertEqual(len(qa["sha256"]),64)
        q=self._check(self._metadata("long"),"long")
        self.assertEqual(q["width"],1920)

    def test_dimension_codec_chroma_and_duration_rejections(self):
        bad=[
            (self._metadata(width=720), "short"),
            (self._metadata(vcodec="vp9"), "short"),
            (self._metadata(acodec="opus"), "short"),
            (self._metadata(duration="1.0"), "short"),
            (self._metadata(duration="50.0"), "short"),
            (self._metadata(pix_fmt="yuv444p"), "short"),
            (self._metadata("short"), "long"),
        ]
        for m,kind in bad:
            with self.subTest(kind=kind,metadata=m), self.assertRaises(ProbeError):
                self._check(m,kind)

    def test_no_audio_no_video_or_extra_streams_refused(self):
        m=self._metadata()
        for streams in ([m["streams"][0]], [m["streams"][1]], [*m["streams"], m["streams"][1]]):
            with self.subTest(streams=len(streams)),self.assertRaises(ProbeError):
                self._check({**m,"streams":streams})

    def test_render_receives_original_demo_labels_and_no_upload(self):
        observed=[]
        def fake_execute(command,*,timeout_s=120):
            observed.append(command)
            return subprocess.CompletedProcess(command,0,stdout="",stderr="")
        with patch("autopilot.cloud_av_probe.execute",side_effect=fake_execute):
            render_probe(Path("/tmp/narration.wav"),Path("/tmp/demo.mp4"),"short","short_am")
        command=observed[0]
        self.assertEqual(command[0],"ffmpeg")
        self.assertIn("libx264",command)
        self.assertIn("aac",command)
        self.assertIn("NO PUBLISH"," ".join(command))
        self.assertNotIn("youtube", " ".join(command).lower())

    def test_bad_slot_refused_before_process_spawn(self):
        with patch("autopilot.cloud_av_probe.execute") as fake:
            with self.assertRaises(ProbeError):
                render_probe(Path("sample.wav"),Path("bad.mp4"),"long","unknown")
            fake.assert_not_called()

    def test_missing_ffprobe_input_refused(self):
        with self.assertRaises(ProbeError):
            check_media(Path("/does/not/exist.mp4"),"short")


if __name__=="__main__":
    unittest.main()
