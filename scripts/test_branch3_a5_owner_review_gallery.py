"""A5/A6 portable offline review gallery: no script, network, or false rights."""
from __future__ import annotations

import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_a5_owner_review_gallery import (
    OUTPUT, GalleryBlocked, make_gallery, fixture, safe
)
from scripts.branch3_a6_original_handoff import (
    CATALOG, PACKET_NAME, METADATA_NAME, MP4, WAV, SRT, MANIFEST, TECH_QA,
    build_packet, sha
)
from scripts.branch3_a6_original_review_signature import (
    REQUEST_FILE, make_unsigned_review_request
)
from scripts.branch3_original_arcade_pilots import validate_catalog


class OfflineOwnerReviewGalleryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        self.episodes=validate_catalog(json.loads(CATALOG.read_text("utf-8")))
        self.reports={}
        with patch.multiple(
            "scripts.branch3_a6_original_handoff",
            probe=lambda video:{"fake":"pure-mock-no-real-FFprobe"},
            validate_episode_report=lambda *a,**kw:{"mock_qa":True}
        ):
            for ep in self.episodes:
                folder=self.directory/ep["id"]
                folder.mkdir()
                (folder/MP4).write_bytes(
                    ("SYNTHETIC_ONLY_VIDEO_"+ep["id"]).encode("ascii")
                )
                (folder/WAV).write_bytes(b"synthetic-only-voice")
                (folder/SRT).write_text(
                    "1\n00:00:00,000 --> 00:00:01,000\nSYNTHETIC TEST\n",
                    encoding="utf-8"
                )
                (folder/MANIFEST).write_text(
                    json.dumps({"render_mode":"full"}),encoding="utf-8"
                )
                (folder/TECH_QA).write_text(
                    json.dumps({"mock_qa":True}),encoding="utf-8"
                )
                packet,metadata=build_packet(
                    ep,folder,catalog_sha256=sha(CATALOG)
                )
                (folder/PACKET_NAME).write_text(json.dumps(packet),encoding="utf-8")
                (folder/METADATA_NAME).write_text(json.dumps(metadata),encoding="utf-8")
                unsigned=make_unsigned_review_request(packet,metadata)
                (folder/REQUEST_FILE).write_text(json.dumps(unsigned),encoding="utf-8")
                self.reports[ep["id"]]={
                    "packet":packet,"metadata":metadata,"unsigned":unsigned
                }

    def proof(self,selection="all"):
        return patch(
            "scripts.branch3_a5_owner_review_gallery.verify_unsigned_requests",
            return_value={
                "all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed":True,
                "actual_human_video_approvals_verified":0,
                "youtube_upload_authorized":False,
            }
        )

    def test_all_three_video_cards_are_local_and_unsigned(self):
        with self.proof():
            result=make_gallery(self.directory,selection="all")
        self.assertEqual(result["episode_count"],3)
        self.assertTrue(result["only_relative_local_mp4_srt_links"])
        self.assertTrue(result["no_remote_assets_or_browser_scripts"])
        self.assertFalse(result["human_editorial_review_completed"])
        self.assertFalse(result["real_owner_release_signed"])
        self.assertFalse(result["youtube_upload_authorized"])
        self.assertFalse(result["youtube_schedule_authorized"])
        html=(self.directory/OUTPUT).read_text("utf-8")
        self.assertEqual(html.count("<video controls"),3)
        self.assertEqual(html.count("UNSIGNED · NOT PUBLISHED"),3)
        self.assertEqual(html.count("Open draft SRT captions"),3)
        for episode in self.episodes:
            self.assertIn(episode["id"]+"/"+MP4,html)
            self.assertIn(episode["id"]+"/"+SRT,html)
            self.assertIn(self.reports[episode["id"]]["packet"]["exact_video_sha256"],
                          html)
        for bad in ("<script","https://","http://","fetch(","owner-signed","oauth-token"):
            self.assertNotIn(bad,html.lower())
        self.assertIn("Human review required",html)
        self.assertIn("not word-aligned",html)

    def test_single_short_card_only_for_fast_pr_preview(self):
        with self.proof():
            out=make_gallery(self.directory,selection="one")
        self.assertEqual(out["episode_count"],1)
        html=(self.directory/OUTPUT).read_text("utf-8")
        self.assertEqual(html.count("<video controls"),1)
        self.assertIn(self.episodes[0]["id"],html)
        self.assertNotIn(self.episodes[1]["id"]+"/"+MP4,html)

    def test_edited_video_or_srt_rejected_after_proof(self):
        for name in (MP4,SRT):
            ep=self.episodes[0]
            folder=self.directory/ep["id"]
            path=folder/name
            original=path.read_bytes()
            path.write_bytes(original+b"INJECTED")
            with self.proof(),self.subTest(name=name),self.assertRaisesRegex(
                GalleryBlocked,"MEDIA_HAS_CHANGED"
            ):
                make_gallery(self.directory,selection="one")
            path.write_bytes(original)

    def test_missing_symlink_media_and_false_review_rejected(self):
        folder=self.directory/self.episodes[0]["id"]
        file=folder/MP4
        data=file.read_bytes()
        file.unlink()
        with self.proof(),self.assertRaises(GalleryBlocked):
            make_gallery(self.directory,selection="one")
        file.symlink_to(folder/SRT)
        with self.proof(),self.assertRaises(GalleryBlocked):
            make_gallery(self.directory,selection="one")
        file.unlink()
        file.write_bytes(data)
        form=folder/REQUEST_FILE
        content=json.loads(form.read_text("utf-8"))
        content["owner_review_checks"]["exact_full_video_watched"]=True
        form.write_text(json.dumps(content),encoding="utf-8")
        with self.proof(),self.assertRaisesRegex(GalleryBlocked,
                                                  "NO_REVIEW_COMPLETED"):
            make_gallery(self.directory,selection="one")

    def test_forged_title_and_visibility_rejected(self):
        folder=self.directory/self.episodes[0]["id"]
        file=folder/METADATA_NAME
        original=json.loads(file.read_text("utf-8"))
        for field,value in (("title","Fake gameplay footage"),
                            ("youtube_visibility","public")):
            altered={**original,field:value}
            file.write_text(json.dumps(altered),encoding="utf-8")
            with self.proof(),self.subTest(field=field),self.assertRaises(
                GalleryBlocked
            ):
                make_gallery(self.directory,selection="one")
        file.write_text(json.dumps(original),encoding="utf-8")

    def test_refuses_to_overwrite_existing_gallery_and_repo_location(self):
        with self.proof():
            make_gallery(self.directory,selection="one")
            with self.assertRaisesRegex(GalleryBlocked,"NO_REPLACE"):
                make_gallery(self.directory,selection="one")
            with self.assertRaises(GalleryBlocked):
                make_gallery(Path.cwd(),selection="one")

    def test_html_escape_and_fixture_no_real_approval(self):
        self.assertEqual(safe('<img src="x">'),
                         "&lt;img src=&quot;x&quot;&gt;")
        with self.assertRaises(GalleryBlocked):
            safe(123)
        f=fixture()
        self.assertTrue(f["can_build_verified_local_html_review_gallery"])
        self.assertFalse(f["real_review_gallery_produced_in_fixture"])
        self.assertFalse(f["actual_owner_signature_verified"])
        self.assertFalse(f["human_video_review_completed"])
        self.assertFalse(f["youtube_upload_authorized"])
        self.assertEqual(f["actual_google_api_calls"],0)


if __name__=="__main__":
    unittest.main()
