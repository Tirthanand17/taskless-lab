"""Synthetic Google Takeout ZIP fixtures; no real Google account or upload."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from autopilot.flow_takeout_bridge import (
    scan_flow_takeout, FlowTakeoutError, import_review_candidates, redacted_report)

MAP=[{"episode_id":"fm_20261024_short_en","clip_id":"01","media_id":"abc123"}]
HEADER=b"\x00\x00\x00\x18ftypmp42"+b"1"*180


class FlowTakeoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.archive=Path(self.tmp.name)/"flow_takeout.zip"

    def fixture(self, *, media=HEADER, metadata=True, extras=(), meta=None):
        with zipfile.ZipFile(self.archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("Takeout/Flow/media/abc123.mp4",media)
            if metadata:
                z.writestr("Takeout/Flow/media/abc123_metadata.json",
                           json.dumps(meta or {"prompt":"Private content, do not leak","model":"Omni"}))
            for name,data in extras:
                z.writestr(name,data)

    def test_pair_and_hash_but_never_approve_release(self):
        self.fixture()
        r=scan_flow_takeout(self.archive,MAP)[0]
        self.assertFalse(r.issues)
        self.assertEqual(r.status,"SCAN_PASSED_EDITORIAL_REVIEW_PENDING")
        self.assertEqual(len(r.media_sha256),64)
        self.assertTrue(r.paired_metadata_found)
        self.assertIn("prompt",r.metadata_key_names)
        self.assertFalse(r.youtube_scheduled)
        self.assertFalse(r.publication_authorized)

    def test_no_prompts_leak_into_report(self):
        self.fixture(meta={"prompt":"SECRET_PASSWORD_FROM_USER","model":"Omni"})
        result=json.dumps(redacted_report(scan_flow_takeout(self.archive,MAP)))
        self.assertNotIn("SECRET_PASSWORD_FROM_USER",result)

    def test_no_paired_metadata(self):
        self.fixture(metadata=False)
        self.assertIn("PAIRED_METADATA_MISSING",scan_flow_takeout(self.archive,MAP)[0].issues)

    def test_wrong_mp4_header(self):
        self.fixture(media=b"X"*200)
        self.assertIn("NOT_AN_MP4_HEADER",scan_flow_takeout(self.archive,MAP)[0].issues)

    def test_traversal_entry_rejected(self):
        self.fixture(extras=[("../sensitive.txt","secret")])
        with self.assertRaisesRegex(FlowTakeoutError,"Unsafe archive entry"):
            scan_flow_takeout(self.archive,MAP)

    def test_backslash_path_rejected(self):
        self.fixture(extras=[("Takeout\\bad.txt","secret")])
        with self.assertRaisesRegex(FlowTakeoutError,"Unsafe archive entry"):
            scan_flow_takeout(self.archive,MAP)

    def test_duplicate_media_id_path_does_not_guess(self):
        self.fixture(extras=[("other/media/abc123.mp4",HEADER)])
        self.assertIn("MISSING_OR_AMBIGUOUS_MEDIA",
                      scan_flow_takeout(self.archive,MAP)[0].issues)

    def test_duplicate_mapping_rejected(self):
        self.fixture()
        with self.assertRaisesRegex(FlowTakeoutError,"Duplicate"):
            scan_flow_takeout(self.archive,MAP+MAP)

    def test_missing_requested_media_rejected(self):
        self.fixture()
        other=[{**MAP[0],"media_id":"missing123"}]
        self.assertIn("MISSING_OR_AMBIGUOUS_MEDIA",
                      scan_flow_takeout(self.archive,other)[0].issues)

    def test_encrypted_or_symlinked_archive_path_rejected(self):
        self.fixture()
        link=Path(self.tmp.name)/"shortcut.zip"
        try:
            link.symlink_to(self.archive)
        except OSError:
            self.skipTest("No symlink support")
        with self.assertRaisesRegex(FlowTakeoutError,"real Takeout ZIP"):
            scan_flow_takeout(link,MAP)

    def test_corrupted_metadata(self):
        with zipfile.ZipFile(self.archive,"w") as z:
            z.writestr("media/abc123.mp4",HEADER)
            z.writestr("media/abc123_metadata.json","invalid JSON")
        self.assertIn("PAIRED_METADATA_INVALID",scan_flow_takeout(self.archive,MAP)[0].issues)

    def test_unreviewed_import_cannot_bypass_zip_scan(self):
        from pathlib import Path
        import json
        self.fixture(media=b"x"*200)
        pack=json.loads((Path(__file__).resolve().parents[1]/"content"/"flow"
                        /"oct24_cinematic_flow_scene_package.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(FlowTakeoutError,"scanner rejected"):
            import_review_candidates(self.archive,MAP,self.tmp.name,pack)
        self.assertEqual(list(Path(self.tmp.name).glob("*.mp4")),[])


if __name__=="__main__":
    unittest.main()
