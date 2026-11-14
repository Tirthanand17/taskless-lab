"""Real-media owner storyboard sheet protection; synthetic mock frames only."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_a5_review_contact_sheet import (
    NAME, ContactSheetBlocked, build, create_one, fixture
)
from scripts.branch3_original_arcade_qa import cue_samples_all_cues
from scripts.branch3_original_arcade_pilots import (
    CATALOG, draft_srt, sha, validate_catalog
)


class OriginalStoryboardSheetTests(unittest.TestCase):
    def setUp(self):
        self.episodes=validate_catalog(json.loads(CATALOG.read_text("utf-8")))
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for episode in self.episodes:
            folder=self.root/episode["id"]
            folder.mkdir()
            vid=folder/"original-review-preview.mp4"
            vid.write_bytes(("SYNTHETIC_FAKE_MP4_"+episode["id"]).encode()*150)
            draft_srt(episode,folder/"narration-timing-draft.srt")
            cues=cue_samples_all_cues(
                (folder/"narration-timing-draft.srt").read_text("utf-8"),
                episode["beats"],episode["duration_seconds"]
            )
            (folder/"review-manifest.json").write_text('{"fake":"yes"}',"utf-8")
            (folder/"owner-handoff-quarantined.json").write_text(
                json.dumps({"exact_video_sha256":sha(vid)}),"utf-8"
            )
            (folder/"technical-review-qa.json").write_text(
                json.dumps({
                    "decoded_actual_frame_caption_safezone_qa":{
                        "every_storyboard_beat_caption_visible_in_safe_zone":True,
                        "every_draft_caption_cue_visible_in_safe_zone":True,
                        "actual_encoded_frames_checked":len(cues),
                        "draft_caption_cue_count":len(cues),
                        "storyboard_beat_count":len(episode["beats"]),
                        "caption_layout_human_approved":False,
                    },
                    "youtube_upload_authorized":False,
                }),"utf-8"
            )

    def proof(self):
        return patch(
            "scripts.branch3_a5_review_contact_sheet.verify_unsigned_requests",
            return_value={
                "all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed":True,
                "actual_human_video_approvals_verified":0,
                "youtube_upload_authorized":False,
            }
        )

    def fake_frames(self):
        try:
            from PIL import Image
        except ModuleNotFoundError:
            self.skipTest("Pillow only installed in dedicated real-media CI")
        # Mock decoded frames; the actual render CI uses real FFmpeg/MP4.
        return patch(
            "scripts.branch3_a5_review_contact_sheet.decode_actual_frame",
            side_effect=lambda *_:Image.new("RGB",(540,960),(14,23,44))
        )

    def test_two_short_and_one_long_contact_sheets_all_beats_plus_outro(self):
        with self.proof(),self.fake_frames() as decoder:
            got=build(self.root,selection="all")
        self.assertEqual(got["episode_count"],3)
        self.assertTrue(got["all_scene_frames_included_plus_outro"])
        self.assertFalse(got["owner_review_and_playback_completed"])
        self.assertFalse(got["youtube_upload_authorized"])
        self.assertEqual(decoder.call_count,5+1+5+1+13+1)
        self.assertEqual([x["total_contact_sheet_frames"]
                          for x in got["contact_sheets"]],[6,6,14])
        from PIL import Image
        for ep,report in zip(self.episodes,got["contact_sheets"]):
            with self.subTest(ep=ep["id"]):
                file=self.root/ep["id"]/NAME
                self.assertTrue(file.is_file())
                with Image.open(file) as im:
                    self.assertEqual(im.format,"JPEG")
                    self.assertGreater(im.width,500)
                    self.assertGreater(im.height,500)
                self.assertEqual(len(report["jpg_sha256"]),64)
                self.assertFalse(report["full_video_human_watched"])

    def test_not_a_licensing_or_signing_step(self):
        f=fixture()
        self.assertTrue(f["every_beat_contact_sheet_generation_supported"])
        self.assertEqual(f["actual_video_frames_decoded_in_fixture"],0)
        self.assertFalse(f["owner_review_verified"])
        self.assertEqual(f["actual_google_calls"],0)
        self.assertFalse(f["youtube_upload_authorized"])
        self.assertFalse(f["youtube_publish_authorized"])

    def test_rejects_fake_all_beat_qa_and_stale_mp4_sha(self):
        ep=self.episodes[0]
        folder=self.root/ep["id"]
        qa_path=folder/"technical-review-qa.json"
        original=json.loads(qa_path.read_text())
        for variant in (
            {"decoded_actual_frame_caption_safezone_qa":None},
            {"decoded_actual_frame_caption_safezone_qa":{
                **original["decoded_actual_frame_caption_safezone_qa"],
                "actual_encoded_frames_checked":1}},
            {"decoded_actual_frame_caption_safezone_qa":{
                **original["decoded_actual_frame_caption_safezone_qa"],
                "every_draft_caption_cue_visible_in_safe_zone":False}},
            {"youtube_upload_authorized":True},
        ):
            changed={**original,**variant}
            qa_path.write_text(json.dumps(changed),"utf-8")
            with self.subTest(variant=variant),self.fake_frames(),self.assertRaises(
                ContactSheetBlocked
            ):
                create_one(folder,ep)
        qa_path.write_text(json.dumps(original),"utf-8")
        vid=folder/"original-review-preview.mp4"
        vid.write_bytes(vid.read_bytes()+b"changed")
        with self.fake_frames(),self.assertRaisesRegex(
            ContactSheetBlocked,"EXACT_REVIEW_VIDEO_HASH"
        ):
            create_one(folder,ep)

    def test_unchanged_contact_sheet_cannot_be_overwritten(self):
        ep=self.episodes[0]
        folder=self.root/ep["id"]
        with self.fake_frames():
            create_one(folder,ep)
        with self.fake_frames(),self.assertRaisesRegex(
            ContactSheetBlocked,"NO_OVERWRITE"
        ):
            create_one(folder,ep)

    def test_repo_worktree_and_unauthenticated_handoff_rejected(self):
        with self.fake_frames(),self.assertRaises(ContactSheetBlocked):
            build(Path.cwd(),selection="one")
        with self.fake_frames(),self.assertRaises(ContactSheetBlocked):
            build(self.root,selection="many")
        ep=self.episodes[0]
        folder=self.root/ep["id"]
        with patch(
            "scripts.branch3_a5_review_contact_sheet.verify_unsigned_requests",
            return_value={
                "all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed":False,
                "actual_human_video_approvals_verified":0,
                "youtube_upload_authorized":False,
            }
        ),self.fake_frames(),self.assertRaises(ContactSheetBlocked):
            build(self.root,selection="one")


if __name__=="__main__":
    unittest.main()
