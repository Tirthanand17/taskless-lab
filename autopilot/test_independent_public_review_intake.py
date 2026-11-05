"""B4d3 independent review artifact ingestion and adversarial anti-forgery tests.

Pure stdlib fixtures never claim they are real videos. Real MP4 FFprobe,
SRT, PNG and full original producer hashes are independently checked on
the separate MAIN-branch real GitHub Actions workflow.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import struct
import tempfile
import unittest
from unittest.mock import patch

from autopilot.primary_sourced_storyboards import build_story
from autopilot.independent_public_review_intake import (
    SOURCE_RUN_ID,SOURCE_ARTIFACT_ID,STATUS,SLOTS,
    ReviewIntakeRejected,validate_exact_media_artifact,
    make_owner_review_intake,_review_markdown,inspect_png,inspect_srt,
    inspect_video_ffprobe,
)

def _bytes(name,slot):
    if name.endswith(".mp4"):
        return (f"fake-fixture-only-UNPLAYABLE-{slot}-".encode()*60)
    if name.endswith(".png"):
        return b"fake-not-png-content_"+slot.encode()*30
    cues=[]
    for n in range(1,10):
        a,b=n-1,n
        cues.append(f"{n}\n00:00:{a:02d},000 --> 00:00:{b:02d},000\nOriginal synthetic QA {n}")
    return ("\n\n".join(cues)+"\n").encode()


def _artifact(root: Path):
    episodes=[]
    for slot in SLOTS:
        story=build_story(slot)
        folder=root/story["episode_id"]
        folder.mkdir()
        records=[]
        for name in ("PREVIEW_UNAPPROVED.mp4","CAPTIONS_UNAPPROVED.srt","THUMBNAIL_UNAPPROVED.png"):
            raw=_bytes(name,slot)
            (folder/name).write_bytes(raw)
            records.append({"filename":name,"sha256":sha256(raw).hexdigest(),"bytes":len(raw)})
        episodes.append({
            "slot":slot,"format":story["format"],"episode_id":story["episode_id"],
            "source_draft_sha256":story["draft_sha256"],
            "source_claims_human_fact_verified":False,
            "owner_full_watch_completed":False,
            "media_and_voice_rights_approved":False,
            "technical_full_video_decode_passed":True,
            "technical_spoken_srt_and_scene_checks_passed":True,
            "files":records,"youtube_upload_enabled":False,
            "release_authorized":False,
        })
    manifest={
        "schema_version":1,
        "status":"PUBLIC_REVIEW_DRAFT_MEDIA_RETAINED_NOT_RELEASE_APPROVED",
        "artifact_scope":"PUBLIC_GITHUB_ACTIONS_EPHEMERAL_REVIEW_ONLY",
        "source":"THREE_FIXED_20261104_ORIGINAL_TOPIC_DEMOS_NOT_DAILY_FRESH_EPISODES",
        "technical_original_mp4_captions_thumbnail_count":3,
        "episodes":episodes,
        "contains_public_original_source_demo_material_only":True,
        "original_voice_model_file_weights_archived":False,
        "real_rights_or_editorial_approval":False,
        "actual_live_youtube_uploads":0,
        "release_authorized":False,
    }
    _save(root,manifest)
    return manifest


def _save(root,manifest):
    (root/"UNAPPROVED_PUBLIC_REVIEW_MANIFEST.json").write_text(
        json.dumps(manifest,indent=2),encoding="utf-8"
    )


class IndependentReviewIntakeTests(unittest.TestCase):
    def test_real_source_story_based_fake_bytes_validate_only_hashes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            _artifact(root)
            entries=validate_exact_media_artifact(root)
            self.assertEqual([x["slot"] for x in entries],list(SLOTS))
            self.assertEqual([x["format"] for x in entries],["short","long","short"])
            self.assertTrue(all(x["real_human_approval"] is False for x in entries))
            self.assertTrue(all(x["release_authorized"] is False for x in entries))
            self.assertEqual(len({x["files"]["PREVIEW_UNAPPROVED.mp4"]["sha256"] for x in entries}),3)

    def test_tampered_media_byte_or_length_rejected(self):
        for name in ("PREVIEW_UNAPPROVED.mp4","CAPTIONS_UNAPPROVED.srt",
                     "THUMBNAIL_UNAPPROVED.png"):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as t:
                root=Path(t)
                manifest=_artifact(root)
                target=root/manifest["episodes"][1]["episode_id"]/name
                target.write_bytes(target.read_bytes()+b"CHANGED")
                with self.assertRaises(ReviewIntakeRejected):
                    validate_exact_media_artifact(root)

    def test_fake_human_approval_flags_or_google_publishing_denied(self):
        for key in ("real_rights_or_editorial_approval","release_authorized"):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as t:
                root=Path(t)
                d=_artifact(root)
                d[key]=True
                _save(root,d)
                with self.assertRaises(ReviewIntakeRejected):
                    validate_exact_media_artifact(root)
        for key in ("source_claims_human_fact_verified","owner_full_watch_completed",
                    "media_and_voice_rights_approved","youtube_upload_enabled",
                    "release_authorized"):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as t:
                root=Path(t)
                d=_artifact(root)
                d["episodes"][0][key]=True
                _save(root,d)
                with self.assertRaises(ReviewIntakeRejected):
                    validate_exact_media_artifact(root)

    def test_wrong_episode_identity_format_story_or_order_rejected(self):
        changes=[
            lambda d:d["episodes"][0].update(episode_id="fake"),
            lambda d:d["episodes"][0].update(format="long"),
            lambda d:d["episodes"][0].update(source_draft_sha256="a"*64),
            lambda d:d["episodes"].reverse(),
            lambda d:d.update(technical_original_mp4_captions_thumbnail_count=4),
            lambda d:d.update(actual_live_youtube_uploads=1),
            lambda d:d.update(source="invented"),
            lambda d:d.update(contains_public_original_source_demo_material_only=False),
        ]
        for i,change in enumerate(changes):
            with self.subTest(case=i),tempfile.TemporaryDirectory() as t:
                root=Path(t)
                d=_artifact(root)
                change(d)
                _save(root,d)
                with self.assertRaises(ReviewIntakeRejected):
                    validate_exact_media_artifact(root)

    def test_extra_file_missing_file_and_symlinks_denied(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            d=_artifact(root)
            p=root/d["episodes"][0]["episode_id"]/"UNEXPECTED_SECRET.txt"
            p.write_text("no real secrets")
            with self.assertRaises(ReviewIntakeRejected):
                validate_exact_media_artifact(root)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            d=_artifact(root)
            p=root/d["episodes"][0]["episode_id"]/"CAPTIONS_UNAPPROVED.srt"
            p.unlink()
            with self.assertRaises(ReviewIntakeRejected):
                validate_exact_media_artifact(root)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            d=_artifact(root)
            p=root/d["episodes"][0]["episode_id"]/"CAPTIONS_UNAPPROVED.srt"
            p.unlink()
            p.symlink_to(root/d["episodes"][1]["episode_id"]/"CAPTIONS_UNAPPROVED.srt")
            with self.assertRaises(ReviewIntakeRejected):
                validate_exact_media_artifact(root)

    def test_duplicate_file_inventory_key_and_broken_json_denied(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            d=_artifact(root)
            d["episodes"][0]["files"].append(deepcopy(d["episodes"][0]["files"][0]))
            _save(root,d)
            with self.assertRaises(ReviewIntakeRejected):
                validate_exact_media_artifact(root)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            _artifact(root)
            (root/"UNAPPROVED_PUBLIC_REVIEW_MANIFEST.json").write_text(
                '{"schema_version":1,"schema_version":9}',encoding="utf-8")
            with self.assertRaises(ReviewIntakeRejected):
                validate_exact_media_artifact(root)

    def test_obvious_unplayable_media_never_pass_ffprobe(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"fake.mp4"
            p.write_bytes(b"not a valid mp4"*30)
            with patch("autopilot.independent_public_review_intake.subprocess.run",
                       side_effect=subprocess.CalledProcessError(1,["ffprobe"])):
                with self.assertRaises(ReviewIntakeRejected):
                    inspect_video_ffprobe(p,"short")

    def test_wrong_real_video_codec_duration_and_format_rejected(self):
        valid={
            "streams":[{"codec_type":"video","codec_name":"h264",
                        "pix_fmt":"yuv420p","width":1080,"height":1920},
                       {"codec_type":"audio","codec_name":"aac"}],
            "format":{"duration":"47.500"},
        }
        for transform in (
            lambda d:d["streams"][0].update(codec_name="vp9"),
            lambda d:d["streams"][0].update(width=1920),
            lambda d:d["streams"][1].update(codec_name="mp3"),
            lambda d:d["format"].update(duration="0"),
            lambda d:d["format"].update(duration="nan"),
            lambda d:d.update(streams=[]),
        ):
            with self.subTest(i=str(transform)):
                data=deepcopy(valid)
                transform(data)
                with patch("autopilot.independent_public_review_intake.subprocess.run") as mock:
                    mock.return_value.stdout=json.dumps(data)
                    with self.assertRaises(ReviewIntakeRejected):
                        inspect_video_ffprobe(Path("/tmp/fake-media.mp4"),"short")
        with patch("autopilot.independent_public_review_intake.subprocess.run") as mock:
            mock.return_value.stdout=json.dumps(valid)
            v=inspect_video_ffprobe(Path("/tmp/fake-media.mp4"),"short")
            self.assertEqual(v["codec"],"H264_AAC")
            self.assertFalse(v["full_video_human_watched"])
            self.assertEqual(v["duration_seconds"],47.5)

    def test_real_srt_parser_timestamps_and_no_overlap(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"captions.srt"
            p.write_bytes(_bytes("CAPTIONS_UNAPPROVED.srt","short_am"))
            v=inspect_srt(p,45)
            self.assertEqual(v["caption_cue_count"],9)
            self.assertFalse(v["true_caption_text_human_checked"])
            for changed in (
                p.read_text().replace("-->","--x",1),
                p.read_text().replace("00:00:01,000 --> 00:00:02,000",
                                      "00:00:00,000 --> 00:00:02,000"),
                p.read_text().replace("1\n","99\n",1),
            ):
                p.write_text(changed)
                with self.assertRaises(ReviewIntakeRejected):
                    inspect_srt(p,45)
            p.write_bytes(_bytes("CAPTIONS_UNAPPROVED.srt","short_am"))
            with self.assertRaises(ReviewIntakeRejected):
                inspect_srt(p,2)

    def test_png_image_header_dimensions_must_match_produced_original(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"thumb.png"
            def header(w,h):
                return b"\x89PNG\r\n\x1a\n"+struct.pack(">I",13)+b"IHDR"+struct.pack(">II",w,h)
            p.write_bytes(header(1280,720)+b"restfake")
            v=inspect_png(p)
            self.assertEqual(v["png_size"],"1280x720")
            self.assertFalse(v["visual_thumbnail_human_reviewed"])
            for b in (header(1080,1920),b"notpng"*10):
                p.write_bytes(b)
                with self.assertRaises(ReviewIntakeRejected):
                    inspect_png(p)

    def test_review_checklist_stays_unsigned_and_per_sha(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            _artifact(root)
            episodes=validate_exact_media_artifact(root)
            for ep in episodes:
                ep["actual_ffprobe"]={"resolution":"1080x1920","duration_seconds":52}
                ep["actual_srt"]={"caption_cue_count":10}
            intake={"episodes":episodes}
            text=_review_markdown(intake)
            self.assertEqual(text.count("- [ ] Actually watch/listen"),3)
            self.assertIn("NASA/NIST/USGS",text)
            self.assertIn("UNSIGNED",text)
            self.assertIn("publishing:",text.lower())
            self.assertNotIn("SIGNED_APPROVED",text)
            for ep in episodes:
                self.assertIn(ep["files"]["PREVIEW_UNAPPROVED.mp4"]["sha256"],text)

    def test_artifact_pinning_real_run_id_is_specific_not_generic_relay(self):
        self.assertEqual(SOURCE_RUN_ID,41970364138)
        self.assertEqual(SOURCE_ARTIFACT_ID,13389693311)
        self.assertIn("OWNER_REVIEW_PENDING",STATUS)
        self.assertIn("NO_RELEASE",STATUS)


if __name__=="__main__":
    unittest.main()
