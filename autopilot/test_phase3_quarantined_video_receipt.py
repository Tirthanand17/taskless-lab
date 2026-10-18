"""Unsigned quarantine video receipts NEVER grant video publishing rights.

Test synthetic temp bytes for hash-chain policy. The separate existing public
Cloud Render Smoke uses actual fully decoded original MP4s and FFmpeg frame QA.
"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autopilot.agent_org import WorkflowError
from autopilot.phase3_quarantined_video_receipt import (
    VERSION,EPISODES,create_quarantined_video_receipt,
    verify_quarantined_receipt,_canonical_bytes,
)
from hashlib import sha256


def fake_pixel_audit(episode_id, path):
    # Synthetic fixture, not an independent human or real video test.
    count=26 if episode_id=="csv_tutorial_long_hi" else 5
    return {
        "status":"VISUAL_SIGNAL_QA_PASS_UNPUBLISHABLE",
        "publishing_authorized":False,
        "visual_signal":{
            "sample_count":count,
            "adjacent_mean_absolute_rgb_change":[12.1]*(count-1),
            "nearblack_fraction":[.005]*count,
            "sample_sha256":[sha256(str(x).encode()).hexdigest() for x in range(count)],
        },
        "issues":[],
    }


class QuarantinedVideoReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/"unapproved.mp4"
        self.p.write_bytes(b"synthetic-not-media"*200)

    def create(self,episode="csv_tutorial_short_en"):
        with patch("autopilot.phase3_quarantined_video_receipt.inspect_authored_visual_signal",
                   side_effect=fake_pixel_audit):
            return create_quarantined_video_receipt(episode_id=episode,mp4=self.p)

    def verify(self,receipt,episode="csv_tutorial_short_en"):
        return verify_quarantined_receipt(
            receipt=receipt,episode_id=episode,mp4=self.p)

    def test_all_three_episode_metadata_tied_to_actual_script_and_srt(self):
        for ep in EPISODES:
            with self.subTest(ep=ep):
                receipt=self.create(ep)
                self.assertEqual(receipt["format_version"],VERSION)
                self.assertEqual(receipt["episode_id"],ep)
                self.assertEqual(len(receipt["authored_script_section_sha256"]),64)
                self.assertEqual(len(receipt["estimated_srt_sha256"]),64)
                self.assertEqual(len(receipt["video_sha256"]),64)
                self.assertEqual(
                    receipt["actual_video_pixel_samples"],
                    26 if ep=="csv_tutorial_long_hi" else 5)
                self.assertEqual(
                    self.verify(receipt,ep)["status"],
                    "LOCAL_QUARANTINE_INTEGRITY_RECHECK_PASS_NOT_RELEASE_APPROVAL")

    def test_unsigned_receipt_never_authorizes_real_voice_or_release(self):
        receipt=self.create()
        for field in (
            "media_has_narration","narrator_identity_authenticated",
            "two_distinct_short_voices_authenticated",
            "estimated_subtitles_are_speech_aligned",
            "spoken_subtitle_alignment_authenticated",
            "fact_editorial_approval_authenticated",
            "third_party_rights_authenticated",
            "human_visual_editorial_approval_authenticated",
            "receipt_issuer_authenticated","receipt_cryptographically_signed",
            "production_media_storage_verified",
            "publishing_authorized","youtube_upload_authorized",
        ):
            with self.subTest(field=field):
                self.assertIs(receipt[field],False)
        verified=self.verify(receipt)
        self.assertIs(verified["publishing_authorized"],False)
        self.assertIs(verified["signed_by_trusted_reviewer"],False)

    def test_original_media_mutation_detected_even_with_same_name(self):
        receipt=self.create()
        self.p.write_bytes(b"other-contents"*300)
        with self.assertRaises(WorkflowError):
            self.verify(receipt)

    def test_receipt_field_edit_detected(self):
        receipt=self.create()
        receipt["video_size_bytes"]+=1
        with self.assertRaises(WorkflowError):
            self.verify(receipt)

    def test_rehashed_fake_publishing_permission_rejected(self):
        receipt=self.create()
        receipt["publishing_authorized"]=True
        bare={k:v for k,v in receipt.items() if k!="receipt_integrity_sha256"}
        receipt["receipt_integrity_sha256"]=sha256(_canonical_bytes(bare)).hexdigest()
        with self.assertRaises(WorkflowError):
            self.verify(receipt)

    def test_rehashed_fake_rights_or_authenticated_issuer_rejected(self):
        for field in ("receipt_issuer_authenticated","third_party_rights_authenticated",
                      "media_has_narration","fact_editorial_approval_authenticated"):
            with self.subTest(field=field):
                receipt=self.create()
                receipt[field]=True
                bare={k:v for k,v in receipt.items() if k!="receipt_integrity_sha256"}
                receipt["receipt_integrity_sha256"]=sha256(_canonical_bytes(bare)).hexdigest()
                with self.assertRaises(WorkflowError):
                    self.verify(receipt)

    def test_unknown_or_swapped_episode_refused(self):
        with self.assertRaises(WorkflowError):
            self.create("unapproved")
        receipt=self.create()
        with self.assertRaises(WorkflowError):
            self.verify(receipt,episode="csv_tutorial_short_hi")

    def test_local_file_links_and_absent_media_refused(self):
        linked=Path(self.tmp.name)/"symlink.mp4"
        linked.symlink_to(self.p)
        with patch("autopilot.phase3_quarantined_video_receipt.inspect_authored_visual_signal",
                   side_effect=fake_pixel_audit):
            with self.assertRaises(WorkflowError):
                create_quarantined_video_receipt(
                    episode_id="csv_tutorial_short_en",mp4=linked)
        self.p.unlink()
        with self.assertRaises(WorkflowError):
            self.create()

    def test_failed_visual_audit_refuses_receipt_creation(self):
        failed=fake_pixel_audit("csv_tutorial_short_en",self.p)
        failed["status"]="VISUAL_SIGNAL_QA_REVIEW_REQUIRED"
        failed["issues"]=["NEAR_STATIC_ACROSS_ADJACENT_SAMPLED_SCENES"]
        with patch("autopilot.phase3_quarantined_video_receipt.inspect_authored_visual_signal",
                   return_value=failed):
            with self.assertRaisesRegex(WorkflowError,"visual QA issues"):
                create_quarantined_video_receipt(
                    episode_id="csv_tutorial_short_en",mp4=self.p)

    def test_visual_sample_count_mismatch_rejected(self):
        bad=fake_pixel_audit("csv_tutorial_short_en",self.p)
        bad["visual_signal"]["sample_count"]=4
        with patch("autopilot.phase3_quarantined_video_receipt.inspect_authored_visual_signal",
                   return_value=bad):
            with self.assertRaises(WorkflowError):
                create_quarantined_video_receipt(
                    episode_id="csv_tutorial_short_en",mp4=self.p)

    def test_receipt_digest_is_canonical_order_independent(self):
        a=self.create()
        shuffled=dict(reversed(list(a.items())))
        self.assertEqual(a,shuffled)
        self.assertEqual(self.verify(a),self.verify(shuffled))

    def test_source_doc_digest_binding_changes_with_script(self):
        receipt=self.create()
        self.assertNotEqual(
            receipt["authored_script_section_sha256"],
            receipt["authored_script_document_sha256"])

if __name__=="__main__":
    unittest.main()
