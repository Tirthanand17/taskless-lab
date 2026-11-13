"""A6 exact-video owner handoff: no false approval, every byte hash bound.

These unit tests mock FFprobe/media QA only to exercise packet integrity. The
real render workflow reruns FFprobe and independent QA on the actual MP4.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_original_arcade_pilots import (
    CATALOG, CHANNEL, sha, validate_catalog
)
from scripts.branch3_a6_original_handoff import (
    DOMAIN, MANIFEST, TECH_QA, MP4, SRT, WAV, PACKET_NAME, METADATA_NAME,
    OriginalHandoffDenied, build_packet, canonical, digest, fixture,
    generate_all, review_metadata, verify_packet
)


def episode():
    return validate_catalog(json.loads(CATALOG.read_text("utf-8")))[0]


class ExactOwnerReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        self.folder=self.dir/episode()["id"]
        self.folder.mkdir()
        (self.folder/MP4).write_bytes(b"fake-video-for-PURE-unit-tests")
        (self.folder/WAV).write_bytes(b"fake-audio-for-PURE-unit-tests")
        (self.folder/SRT).write_text("fictional test captions\n",encoding="utf-8")
        (self.folder/MANIFEST).write_text(
            json.dumps({"render_mode":"preview"}),encoding="utf-8")
        (self.folder/TECH_QA).write_text(
            json.dumps({"actual_ffprobe_checks_passed":True,
                        "youtube_upload_authorized":False}),encoding="utf-8")
        self.expected_qa={
            "actual_ffprobe_checks_passed":True,
            "youtube_upload_authorized":False
        }

    def simulate_real_qa(self):
        return patch.multiple(
            "scripts.branch3_a6_original_handoff",
            probe=lambda path:{"test_only":True},
            validate_episode_report=lambda *args,**kwargs:self.expected_qa
        )

    def build(self):
        return build_packet(
            episode(),self.folder,catalog_sha256=sha(CATALOG)
        )

    def validate(self,packet,metadata):
        return verify_packet(
            episode(),self.folder,packet,metadata,
            catalog_sha256=sha(CATALOG)
        )

    def test_exact_handoff_binds_three_artifact_hashes_and_metadata(self):
        with self.simulate_real_qa():
            packet,metadata=self.build()
            result=self.validate(packet,metadata)
        self.assertEqual(packet["domain"],DOMAIN)
        self.assertEqual(packet["channel_id"],CHANNEL)
        self.assertEqual(packet["exact_video_sha256"],sha(self.folder/MP4))
        self.assertEqual(packet["exact_audio_sha256"],sha(self.folder/WAV))
        self.assertEqual(packet["exact_captions_sha256"],sha(self.folder/SRT))
        self.assertEqual(packet["exact_catalog_sha256"],sha(CATALOG))
        self.assertEqual(packet["exact_metadata_sha256"],digest(metadata))
        self.assertEqual(
            packet["packet_sha256"],
            digest({k:v for k,v in packet.items() if k!="packet_sha256"})
        )
        self.assertTrue(result["actual_video_files_sha256_technically_verified"])
        for key in (
            "exact_video_human_review_confirmed",
            "rights_of_all_final_assets_independently_approved",
            "owner_signing_identity_enrolled",
            "owner_detached_signature_present",
            "trusted_revocation_head_verified",
            "youtube_upload_authorized",
            "youtube_schedule_authorized",
            "youtube_publish_authorized"
        ):
            self.assertFalse(packet[key],key)
        self.assertEqual(result["licensed_creator_clips_verified"],0)
        self.assertFalse(result["owner_review_and_approval_completed"])
        self.assertEqual(result["real_google_api_calls"],0)

    def test_changed_video_audio_and_captions_each_invalidate_packet(self):
        for filename in (MP4,WAV,SRT):
            original=(self.folder/filename).read_bytes()
            with self.simulate_real_qa():
                packet,metadata=self.build()
                (self.folder/filename).write_bytes(original+b"tampered")
                with self.subTest(filename=filename),self.assertRaisesRegex(
                    OriginalHandoffDenied,"PACKET_CHANGED"):
                    self.validate(packet,metadata)
            (self.folder/filename).write_bytes(original)

    def test_changed_title_description_or_channel_id_invalidates(self):
        with self.simulate_real_qa():
            packet,metadata=self.build()
            for key,val in (
                ("title","Changed misleading title"),
                ("description","Modified description"),
                ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
                ("youtube_upload_or_publish_authorized",True)
            ):
                incorrect=dict(metadata)
                incorrect[key]=val
                with self.subTest(field=key),self.assertRaisesRegex(
                    OriginalHandoffDenied,"METADATA_CHANGED"):
                    self.validate(packet,incorrect)
            incorrect=dict(packet)
            incorrect["exact_video_human_review_confirmed"]=True
            with self.assertRaisesRegex(
                    OriginalHandoffDenied,"PACKET_CHANGED"):
                self.validate(incorrect,metadata)
            incorrect=dict(packet)
            incorrect["actual_publish_at_utc"]="2026-11-20T00:00:00Z"
            with self.assertRaisesRegex(
                    OriginalHandoffDenied,"PACKET_CHANGED"):
                self.validate(incorrect,metadata)
            incorrect=dict(packet)
            incorrect["packet_sha256"]="a"*64
            with self.assertRaisesRegex(
                    OriginalHandoffDenied,"PACKET_CHANGED"):
                self.validate(incorrect,metadata)

    def test_catalog_hash_or_external_manifest_edit_rejected(self):
        with self.simulate_real_qa():
            packet,metadata=self.build()
            with self.assertRaisesRegex(OriginalHandoffDenied,"PACKET_CHANGED"):
                verify_packet(episode(),self.folder,packet,metadata,
                              catalog_sha256="f"*64)
            with self.assertRaisesRegex(OriginalHandoffDenied,"CATALOG_SHA"):
                build_packet(episode(),self.folder,catalog_sha256="BAD")
            (self.folder/MANIFEST).write_text(
                json.dumps({"render_mode":"full"}),encoding="utf-8")
            # Render mode change is rejected at metadata preflight, before packet compare.
            with self.assertRaisesRegex(OriginalHandoffDenied,"METADATA_CHANGED"):
                self.validate(packet,metadata)

    def test_existing_qa_must_equal_fresh_recomputed_qa(self):
        with self.simulate_real_qa():
            self.build()
            (self.folder/TECH_QA).write_text(json.dumps({
                "actual_ffprobe_checks_passed":True,
                "youtube_upload_authorized":True
            }),encoding="utf-8")
            with self.assertRaisesRegex(
                    OriginalHandoffDenied,"ACTUAL_QA_REPORT_CHANGED"):
                self.build()

    def test_missing_file_symlink_and_repo_content_denied(self):
        with self.simulate_real_qa():
            for name in (MP4,WAV,SRT,MANIFEST,TECH_QA):
                target=self.folder/name
                save=target.read_bytes()
                target.unlink()
                with self.subTest(name=name),self.assertRaisesRegex(
                    OriginalHandoffDenied,"MISSING_OR_LINKED"):
                    self.build()
                target.write_bytes(save)
            link=self.folder/"fake-media.mp4"
            link.symlink_to(self.folder/MP4)
            original=(self.folder/MP4).read_bytes()
            (self.folder/MP4).unlink()
            (self.folder/MP4).symlink_to(link)
            with self.assertRaisesRegex(
                OriginalHandoffDenied,"MISSING_OR_LINKED"):
                self.build()
            (self.folder/MP4).unlink()
            (self.folder/MP4).write_bytes(original)

    def test_packet_is_not_real_release_and_no_auto_write(self):
        out=fixture()
        self.assertTrue(out["exact_file_handoff_code_implemented"])
        self.assertFalse(out["actual_human_review_signed"])
        self.assertFalse(out["production_owner_public_key_enrolled"])
        self.assertFalse(out["youtube_upload_authorized"])
        self.assertEqual(out["google_api_calls"],0)
        md=review_metadata(episode(),"full")
        self.assertEqual(md["youtube_visibility"],"NOT_UPLOADED")
        self.assertFalse(md["youtube_upload_or_publish_authorized"])
        self.assertEqual(md["channel_id"],CHANNEL)
        self.assertEqual(canonical(md),canonical(dict(reversed(list(md.items())))))

    def test_existing_packet_cannot_be_silently_overwritten(self):
        with self.simulate_real_qa():
            packet,metadata=self.build()
            (self.folder/PACKET_NAME).write_text(
                json.dumps(packet),encoding="utf-8"
            )
            with self.assertRaisesRegex(
                    OriginalHandoffDenied,"NO_OVERWRITE_EXISTING_OWNER_HANDOFF"):
                generate_all(self.dir,selection="one")


if __name__=="__main__":
    unittest.main()
