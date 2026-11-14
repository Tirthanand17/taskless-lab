"""Offline, adversarial P4 local master inspection tests (all synthetic)."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace

from scripts.branch3_v2_p4_private_master_technical_qa import (
    MasterDenied, inspect_local_master, production_media_ingest,
    validate_master_probe, HOLD,
)

SAMPLE = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 512
NAME = "master_testfixture.mp4"


def probe(size=len(SAMPLE)):
    return {
        "streams": [
            {"codec_type": "video", "codec_name": "h264",
             "pix_fmt": "yuv420p", "width": 640, "height": 360,
             "avg_frame_rate": "30/1"},
            {"codec_type": "audio", "codec_name": "aac",
             "sample_rate": "48000", "channels": 2},
        ],
        "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                   "duration": "12.0", "size": str(size)},
    }


def mocked_runner(cmd, **kwargs):
    assert cmd[0] == "ffprobe"
    assert cmd[cmd.index("-protocol_whitelist") + 1] == "file"
    assert "https://" not in " ".join(cmd)
    return SimpleNamespace(returncode=0, stdout=json.dumps(probe()), stderr="")


def kw(root):
    return dict(scratch=root, basename=NAME,
                expected_sha256=hashlib.sha256(SAMPLE).hexdigest(),
                expected_bytes=len(SAMPLE), runner=mocked_runner)


class PrivateLocalMasterQATests(unittest.TestCase):
    def test_local_valid_bytes_and_metadata_does_not_promote_rights(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / NAME).write_bytes(SAMPLE)
            report = inspect_local_master(**kw(root))
            self.assertEqual(report["status"], HOLD)
            self.assertEqual(report["technical_media"]["width"], 640)
            self.assertTrue(report["technical_hash_and_probe_passed"])
            for key in (
                "creator_identity_authenticated",
                "creator_commercial_license_authenticated",
                "underlying_music_game_guest_rights_authenticated",
                "vault_access_rights_authenticated",
                "revocations_rechecked", "source_ingest_authorized",
                "clip_edit_authorized", "youtube_upload_authorized",
                "youtube_publish_authorized", "p4_real_milestone_complete",
                "full_decode_and_editorial_review_passed",
            ):
                self.assertFalse(report[key], key)
            encoded = json.dumps(report)
            self.assertNotIn(str(root), encoded)
            self.assertNotIn(NAME, encoded)
            self.assertNotIn(hashlib.sha256(SAMPLE).hexdigest(), encoded)
            self.assertNotIn("access_token", encoded)

    def test_bad_digest_size_header_and_non_mp4_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / NAME).write_bytes(SAMPLE)
            for change in (
                {"expected_sha256": "0" * 64},
                {"expected_sha256": "X" * 64},
                {"expected_bytes": len(SAMPLE) + 1},
                {"expected_bytes": True},
                {"basename": "../master_testfixture.mp4"},
                {"basename": "master_bad.mov"},
            ):
                with self.subTest(change=change), self.assertRaises(MasterDenied):
                    inspect_local_master(**(kw(root) | change))
            (root / NAME).write_bytes(b"\0" * len(SAMPLE))
            with self.assertRaises(MasterDenied):
                inspect_local_master(**kw(root))

    def test_private_scratch_symlink_and_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / NAME).write_bytes(SAMPLE)
            alias = root / "master_aliasclip.mp4"
            alias.symlink_to(root / NAME)
            with self.assertRaises(MasterDenied):
                inspect_local_master(**(kw(root) | {"basename": alias.name}))
            link = root / "master_hardlinked.mp4"
            link.hardlink_to(root / NAME)
            with self.assertRaises(MasterDenied):
                inspect_local_master(**kw(root))
            link.unlink()
            root.chmod(0o755)
            try:
                with self.assertRaises(MasterDenied):
                    inspect_local_master(**kw(root))
            finally:
                root.chmod(0o700)

    def test_actual_probe_contract_rejects_broken_media(self):
        base = probe()
        self.assertEqual(validate_master_probe(base, len(SAMPLE))["frame_rate"], 30.0)
        for where, index, field, value in (
            ("video", 0, "codec_name", "vp9"),
            ("video", 0, "pix_fmt", "yuv444p"),
            ("video", 0, "width", 200),
            ("video", 0, "avg_frame_rate", "0/0"),
            ("video", 0, "avg_frame_rate", "240/1"),
            ("audio", 1, "codec_name", "opus"),
            ("audio", 1, "channels", 4),
        ):
            doc = copy.deepcopy(base)
            doc["streams"][index][field] = value
            with self.subTest(where=where, field=field), self.assertRaises(MasterDenied):
                validate_master_probe(doc, len(SAMPLE))
        for field, val in (
            ("duration", "nan"), ("duration", "Infinity"),
            ("duration", "5"), ("duration", "7201"),
            ("size", "0"), ("format_name", "matroska,webm"),
        ):
            doc = copy.deepcopy(base)
            doc["format"][field] = val
            with self.subTest(field=field), self.assertRaises(MasterDenied):
                validate_master_probe(doc, len(SAMPLE))
        doc = copy.deepcopy(base)
        doc["streams"].append({"codec_type": "subtitle"})
        with self.assertRaises(MasterDenied):
            validate_master_probe(doc, len(SAMPLE))

    def test_probe_failure_timeout_and_modified_master_deny(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / NAME
            target.write_bytes(SAMPLE)
            def bad_json(*_a, **_k):
                return SimpleNamespace(returncode=0, stdout="not-json", stderr="")
            def failed(*_a, **_k):
                return SimpleNamespace(returncode=1, stdout="", stderr="")
            def timed_out(*_a, **_k):
                raise subprocess.TimeoutExpired("ffprobe", 45)
            def mutate(*_a, **_k):
                target.write_bytes(SAMPLE[:13] + b"X" + SAMPLE[14:])
                return SimpleNamespace(returncode=0, stdout=json.dumps(probe()), stderr="")
            for runner in (bad_json, failed, timed_out):
                with self.subTest(runner=runner.__name__), self.assertRaises(MasterDenied):
                    inspect_local_master(**(kw(root) | {"runner": runner}))
            with self.assertRaises(MasterDenied):
                inspect_local_master(**(kw(root) | {"runner": mutate}))

    def test_production_upload_stays_disabled(self):
        for args in ({}, {"creator_grant": True},
                     {"source_path": "/private/master.mp4"},
                     {"youtube_upload_authorized": True}):
            with self.subTest(args=args), self.assertRaises(MasterDenied):
                production_media_ingest(**args)


if __name__ == "__main__":
    unittest.main()
