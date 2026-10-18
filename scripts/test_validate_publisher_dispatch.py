"""No network / no YouTube credentials dispatch input policy regression tests."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_publisher_dispatch import (
    validate_dispatch_inputs,validate_downloaded_files,
)


def valid()->dict:
    return {
        "EPISODE_PATH":"content/episodes/pilot_001.json",
        "SOURCE_RUN_ID":"39090000001",
        "ARTIFACT_NAME":"flowminute-reviewed-media",
        "VIDEO_FILE":"pilot_001_final.mp4",
        "CAPTIONS_FILE":"captions.srt",
        "THUMBNAIL_FILE":"scene_01.png",
        "RECEIPT_PATH":"state/published/pilot_001.json",
        "PRIVACY":"private",
    }


class PublisherDispatchGateTests(unittest.TestCase):
    def test_allow_structural_owner_private_pilot_inputs_but_never_approve_release(self):
        x=validate_dispatch_inputs(valid())
        self.assertEqual(x["video"],"pilot_001_final.mp4")
        self.assertEqual(x["privacy"],"private")
        self.assertFalse(x["publishing_authorized"])

    def test_shell_command_interpolation_and_traversal_denied(self):
        pairs=(
            ("SOURCE_RUN_ID",'123"; echo PWNED; echo "'),
            ("ARTIFACT_NAME",'$(touch /tmp/never)'),
            ("VIDEO_FILE",'clip.mp4"; echo PWNED'),
            ("CAPTIONS_FILE",'../../credentials.srt'),
            ("THUMBNAIL_FILE",'clip.png;echo PWNED'),
            ("EPISODE_PATH",'content/episodes/../../secrets.json'),
            ("RECEIPT_PATH",'state/published/../../keys.json'),
            ("RECEIPT_PATH",'state/published/a.json";rm -rf .'),
        )
        for field,bad in pairs:
            with self.subTest(field=field,bad=bad):
                x=valid();x[field]=bad
                with self.assertRaises(ValueError):
                    validate_dispatch_inputs(x)

    def test_reject_public_or_unlisted_without_separate_approval(self):
        for privacy in ("public","unlisted","PRIVATE","",None):
            x=valid();x["PRIVACY"]=privacy
            with self.subTest(privacy=privacy),self.assertRaises(ValueError):
                validate_dispatch_inputs(x)

    def test_require_same_episode_and_receipt_identity(self):
        x=valid();x["RECEIPT_PATH"]="state/published/not_pilot_001.json"
        with self.assertRaises(ValueError):
            validate_dispatch_inputs(x)

    def test_no_missing_required_fields(self):
        for field in valid():
            x=valid();x.pop(field)
            with self.subTest(field=field),self.assertRaises(ValueError):
                validate_dispatch_inputs(x)

    def test_existing_three_artifacts_are_required(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for name in ("pilot_001_final.mp4","captions.srt","scene_01.png"):
                (folder/name).write_bytes(b"unreviewed-test-only")
            validate_downloaded_files(valid(),folder)
            (folder/"captions.srt").unlink()
            with self.assertRaises(ValueError):
                validate_downloaded_files(valid(),folder)

    def test_symlink_artifact_denied(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            other=folder/"other-file"
            other.write_bytes(b"test")
            for name in ("pilot_001_final.mp4","captions.srt"):
                (folder/name).write_bytes(b"test")
            (folder/"scene_01.png").symlink_to(other)
            with self.assertRaises(ValueError):
                validate_downloaded_files(valid(),folder)

    def test_zero_byte_video_denied(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"pilot_001_final.mp4").write_bytes(b"")
            (folder/"captions.srt").write_bytes(b"test")
            (folder/"scene_01.png").write_bytes(b"test")
            with self.assertRaises(ValueError):
                validate_downloaded_files(valid(),folder)


if __name__=="__main__":
    unittest.main()
