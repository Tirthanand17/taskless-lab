"""Source-free negative tests for CLIVOX V2 P4, never third-party media."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace

from scripts.branch3_media_storage_preflight import (
    CHANNEL_STATE, CREATOR_PERMS, MANIFEST, POLICY, read_json,
)
from scripts.branch3_v2_p4_synthetic_handoff_preflight import (
    CHANNEL, STATUS, P4Denied, check_probe, closed_boundary,
    actual_closed_boundary, inspect_synthetic_fixture,
)

BYTES = b"\x00\x00\x00\x18ftypisom" + b"\0" * 128
PROBE = {
    "streams": [
        {"codec_type": "video", "codec_name": "h264",
         "pix_fmt": "yuv420p", "width": 160, "height": 90},
        {"codec_type": "audio", "codec_name": "aac",
         "sample_rate": "48000", "channels": 1},
    ],
    "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2",
               "duration": "1.000000", "size": str(len(BYTES))}
}


def inputs():
    return dict(storage_policy=read_json(POLICY),
                manifest=read_json(MANIFEST),
                creator_registry=read_json(CREATOR_PERMS),
                channel_state=read_json(CHANNEL_STATE),
                v2_status=read_json(STATUS))


def media_runner(command, **kwargs):
    if command[0] == "ffprobe":
        return SimpleNamespace(returncode=0, stdout=json.dumps(PROBE), stderr="")
    if command[0] == "ffmpeg":
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    raise AssertionError("unapproved command")


class P4QuarantineTests(unittest.TestCase):
    def test_real_upstream_boundary_remains_shut(self):
        p = actual_closed_boundary()
        self.assertEqual(p["channel_id"], CHANNEL)
        self.assertEqual(p["rights_grants_verified"], 0)
        self.assertFalse(p["private_vault_activated"])
        self.assertFalse(p["p4_milestone_complete"])
        self.assertFalse(p["creator_media_fetch_enabled"])
        self.assertFalse(p["creator_media_write_enabled"])
        self.assertFalse(p["youtube_upload_enabled"])
        self.assertFalse(p["youtube_publish_enabled"])
        self.assertEqual(p["real_media_delivered"], 0)

    def test_forged_rights_flags_or_source_are_rejected(self):
        scenarios = [
            ("v2_status", "confirmed_creator_commercial_grants", 1),
            ("v2_status", "confirmed_creator_commercial_grants", True),
            ("v2_status", "confirmed_rights_cleared_source_files", 1),
            ("v2_status", "private_licensed_media_storage_ready", True),
            ("v2_status", "owner_commercial_reuse_authorization_verified", True),
            ("v2_status", "clivox_live_uploads_enabled", True),
            ("v2_status", "youtube_media_download_enabled", True),
            ("v2_status", "creator_outreach_sent", True),
            ("v2_status", "clivox_channel_oauth_write_enabled", True),
            ("v2_status", "roadmap_confirmed_completed_phases", 4),
            ("v2_status", "p3_real_source_clip_licenses_attained", 1),
            ("v2_status", "channel_id", "UC" + "x" * 22),
            ("v2_status", "public_repo", "other-owner/other"),
            ("storage_policy", "mode", "PROVISIONED"),
            ("storage_policy", "media_fetch_enabled", True),
            ("creator_registry", "creators", [{"id": "forged"}]),
        ]
        for section, field, value in scenarios:
            p = inputs()
            p[section][field] = value
            with self.subTest(section=section, field=field), self.assertRaises(P4Denied):
                closed_boundary(**p)

    def test_synthetic_test_mp4_byte_and_container_checks(self):
        with tempfile.TemporaryDirectory() as d:
            scratch = Path(d)
            sample = scratch / "self_generated.mp4"
            sample.write_bytes(BYTES)
            report = inspect_synthetic_fixture(
                scratch=scratch, basename=sample.name,
                expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                expected_bytes=len(BYTES), runner=media_runner,
            )
            self.assertTrue(report["synthetic_fixture_integrity_checked"])
            self.assertTrue(report["synthetic_fixture_codec_checked"])
            self.assertTrue(report["synthetic_fixture_decoded"])
            self.assertFalse(report["p4_milestone_complete"])
            self.assertEqual(report["real_media_delivered"], 0)
            self.assertNotIn(str(scratch), json.dumps(report))
            self.assertNotIn("sha256", json.dumps(report))

    def test_wrong_digest_and_wrong_size(self):
        with tempfile.TemporaryDirectory() as d:
            scratch = Path(d)
            (scratch / "clip.mp4").write_bytes(BYTES)
            valid = dict(scratch=scratch, basename="clip.mp4",
                         expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                         expected_bytes=len(BYTES), runner=media_runner)
            with self.assertRaises(P4Denied):
                inspect_synthetic_fixture(**{**valid, "expected_sha256": "0" * 64})
            with self.assertRaises(P4Denied):
                inspect_synthetic_fixture(**{**valid, "expected_bytes": len(BYTES)+1})
            with self.assertRaises(P4Denied):
                inspect_synthetic_fixture(**{**valid, "expected_bytes": True})

    def test_rejects_traversal_symlink_and_unlisted_name(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "clip.mp4").write_bytes(BYTES)
            (root / "shortcut.mp4").symlink_to(root / "clip.mp4")
            base = dict(scratch=root, expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                        expected_bytes=len(BYTES), runner=media_runner)
            for name in ("../clip.mp4", "/tmp/clip.mp4", "a/b.mp4",
                         "clip.mov", "clip.mp4\nOK", "shortcut.mp4"):
                with self.subTest(name=name), self.assertRaises(P4Denied):
                    inspect_synthetic_fixture(**{**base, "basename": name})

    def test_rejects_spoofed_mp4_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fake = b"\x00\x00\x00\x18UNSAFE" + b"\0" * 128
            (root / "clip.mp4").write_bytes(fake)
            with self.assertRaises(P4Denied):
                inspect_synthetic_fixture(
                    scratch=root, basename="clip.mp4", expected_bytes=len(fake),
                    expected_sha256=hashlib.sha256(fake).hexdigest(),
                    runner=media_runner)

    def test_bad_ffprobe_codec_extra_stream_duration_size(self):
        variations = [
            ("codec_type", "subtitle", 0),
            ("codec_name", "vp9", 0),
            ("pix_fmt", "yuv444p", 0),
            ("width", 5000, 0),
            ("codec_name", "mp3", 1),
            ("sample_rate", "96000", 1),
        ]
        for key, value, index in variations:
            doc = copy.deepcopy(PROBE)
            doc["streams"][index][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(P4Denied):
                check_probe(doc, len(BYTES))
        for field, value in (
            ("duration", "Infinity"), ("duration", "11"),
            ("size", "0"), ("format_name", "matroska,webm")
        ):
            doc = copy.deepcopy(PROBE)
            doc["format"][field] = value
            with self.subTest(field=field), self.assertRaises(P4Denied):
                check_probe(doc, len(BYTES))
        doc = copy.deepcopy(PROBE)
        doc["streams"].append({"codec_type": "subtitle"})
        with self.assertRaises(P4Denied):
            check_probe(doc, len(BYTES))

    def test_bad_probe_json_or_decode_exit_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "clip.mp4").write_bytes(BYTES)
            args = dict(scratch=root, basename="clip.mp4",
                        expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                        expected_bytes=len(BYTES))
            def bad_json(cmd, **kwargs):
                return SimpleNamespace(returncode=0, stdout="not-json", stderr="")
            def failed_decode(cmd, **kwargs):
                return SimpleNamespace(returncode=0 if cmd[0] == "ffprobe" else 1,
                                       stdout=json.dumps(PROBE), stderr="private-path")
            def timed_out(cmd, **kwargs):
                raise subprocess.TimeoutExpired(cmd, 20)
            for runner in (bad_json, failed_decode, timed_out):
                with self.subTest(runner=runner.__name__), self.assertRaises(P4Denied):
                    inspect_synthetic_fixture(**args, runner=runner)

    def test_rejects_probe_body_greater_than_bound(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "clip.mp4").write_bytes(BYTES)
            def huge_probe(cmd, **kwargs):
                return SimpleNamespace(returncode=0, stdout="x" * 40001, stderr="")
            with self.assertRaises(P4Denied):
                inspect_synthetic_fixture(
                    scratch=root, basename="clip.mp4",
                    expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                    expected_bytes=len(BYTES), runner=huge_probe)


if __name__ == "__main__":
    unittest.main()
