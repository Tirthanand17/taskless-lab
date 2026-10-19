"""Synthetic signed review-to-SRT editing handoff, no speech or release approval."""
from dataclasses import replace
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os
import sqlite3
import stat
import time
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_transcript_replay_ledger import OfflineTranscriptReviewLedger
from autopilot.cloud_cue_audio_activity import CueAcousticCoverage
from autopilot.cloud_signed_transcript_reviews import transcript_digest
from autopilot.cloud_transcript_alignment_intake import _draft_cues
from autopilot.cloud_provisional_signed_srt import stage_provisional_srt
from autopilot.test_cloud_transcript_replay_ledger import fixture
from autopilot.test_cloud_acoustic_review_evidence import _data
from autopilot.test_cloud_signed_transcript_reviews import resign, EXCLUDED


class ProvisionalSignedSubtitleTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.ledger=OfflineTranscriptReviewLedger(self.root/"journal.sqlite3")
        (self.candidate,self.media,self.audio,self.keys,
         self.registry,original)=fixture("short_hi")
        self.sidecars={}
        signed=[]
        for record in original:
            reviewer_id=record.claim.reviewer_id
            raw=json.dumps(
                _data(self.candidate,record.claim),sort_keys=True,
                ensure_ascii=False,separators=(",",":"),
            ).encode("utf-8")
            p=self.root/(record.claim.role+".review.json")
            p.write_bytes(raw)
            self.sidecars[reviewer_id]=p
            signed.append(resign(
                record,self.keys[reviewer_id],
                evidence_sha256=sha256(raw).hexdigest(),
            ))
        self.signed=tuple(signed)
        cue_count=len(_draft_cues(self.candidate.episode_id))
        self.cue=CueAcousticCoverage(
            lane=self.candidate.lane,media_sha256=self.media.video_sha256,
            candidate_transcript_sha256=transcript_digest(self.candidate),
            authored_srt_sha256=self.candidate.authored_draft_srt_sha256,
            cue_count=cue_count,
            activity_windows_scanned=210,
            cue_count_with_acoustic_activity=cue_count,
            acoustically_sparse_cues=0,lowest_cue_active_percent=100,
            entire_audio_decoded=True,technical_cue_activity_pass=True,
            blockers=(),
        )

    def admit(self,*,nonce=True,sidecars=True):
        return self.ledger.commit(
            candidate=self.candidate,media=self.media,audio_screen=self.audio,
            signed_attestations=self.signed,registry=self.registry,
            excluded_creator_publisher_ids=EXCLUDED,now=None,
            evidence_files=self.sidecars if sidecars else None,
            expected_current_sha=None,
            **({
                "signed_command_nonce":"srt_handoff_test_nonce_12345",
                "signed_command_expires_at_epoch":int(time.time())+120,
            } if nonce else {}),
        )

    def stage(self,event,*,candidate=None,cue=None,destination=None):
        return stage_provisional_srt(
            ledger=self.ledger,
            candidate=self.candidate if candidate is None else candidate,
            media=self.media,audio_screen=self.audio,
            cue_report=self.cue if cue is None else cue,
            expected_event_sha256=event,
            destination_directory=destination,
        )

    def test_current_signed_nonce_review_can_make_editor_only_caption_file(self):
        event=self.admit()
        result=self.stage(event["event_sha256"],destination=self.root)
        self.assertEqual(result["status"],
                         "SIGNED_REVIEW_PROVISIONAL_SUBTITLE_FOR_EDITOR_ONLY")
        self.assertTrue(result["exclusive_file_created"])
        self.assertTrue(result["export_basename"].endswith(
            ".reviewed_claim_unverified_speech.srt"))
        path=self.root/result["export_basename"]
        raw=path.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(),result["provisional_srt_sha256"])
        self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
        self.assertIn(" --> ",raw.decode("utf-8"))
        self.assertIn("ह",raw.decode("utf-8"))
        self.assertGreater(result["cue_count"],3)
        self.assertEqual(result["journal_event_sha256"],event["event_sha256"])
        for flag in (
            "real_audio_words_independently_verified",
            "timings_authenticated_to_actual_speech",
            "reviewers_real_world_identity_verified",
            "commercial_rights_verified","approved_for_media_mux",
            "youtube_upload_authorized","publishing_authorized",
        ):
            self.assertFalse(result[flag])

    def test_file_only_created_exclusively_cannot_overwrite_original(self):
        event=self.admit()
        self.stage(event["event_sha256"],destination=self.root)
        path=next(self.root.glob("*.reviewed_claim_unverified_speech.srt"))
        old=path.read_bytes()
        with self.assertRaises(WorkflowError):
            self.stage(event["event_sha256"],destination=self.root)
        self.assertEqual(path.read_bytes(),old)
        self.assertEqual(len(list(self.root.glob("*.reviewed_claim_unverified_speech.srt"))),1)

    def test_detached_only_or_sidecar_only_legacy_review_cannot_export(self):
        for nonce,sidecars in ((False,False),(False,True)):
            with self.subTest(nonce=nonce,sidecars=sidecars):
                with TemporaryDirectory() as td:
                    ledger=OfflineTranscriptReviewLedger(Path(td)/"audit.sqlite3")
                    result=ledger.commit(
                        candidate=self.candidate,media=self.media,
                        audio_screen=self.audio,signed_attestations=self.signed,
                        registry=self.registry,
                        excluded_creator_publisher_ids=EXCLUDED,
                        evidence_files=self.sidecars if sidecars else None,
                        now=None,expected_current_sha=None,
                    )
                    with self.assertRaises(WorkflowError):
                        stage_provisional_srt(
                            ledger=ledger,candidate=self.candidate,
                            media=self.media,audio_screen=self.audio,
                            cue_report=self.cue,
                            expected_event_sha256=result["event_sha256"],
                        )

    def test_wrong_event_digest_revised_word_or_media_refused(self):
        event=self.admit()
        with self.assertRaises(WorkflowError):
            self.stage("f"*64)
        changed=replace(self.candidate,words=(
            replace(self.candidate.words[0],end_ms=
                    self.candidate.words[0].end_ms+1),
            *self.candidate.words[1:],
        ))
        with self.assertRaises(WorkflowError):
            self.stage(event["event_sha256"],candidate=changed)
        self.assertFalse(any(self.root.glob("*.reviewed_claim_unverified_speech.srt")))

    def test_missing_or_forged_prior_sound_review_refused(self):
        event=self.admit()
        for report in (
            replace(self.cue,publishing_authorized=True),
            replace(self.cue,actual_subtitle_alignment_verified=True),
            replace(self.cue,media_sha256="f"*64),
            replace(self.cue,technical_cue_activity_pass=False),
            replace(self.cue,acoustically_sparse_cues=1),
            replace(self.cue,candidate_transcript_sha256="e"*64),
        ):
            with self.subTest(change=report.blockers),self.assertRaises(WorkflowError):
                self.stage(event["event_sha256"],cue=report)

    def test_symlink_destination_or_relative_or_missing_folder_refused(self):
        event=self.admit()
        link=self.root/"alias"
        link.symlink_to(self.root,target_is_directory=True)
        for directory in (Path("relative"),link,self.root/"not_created"):
            with self.subTest(directory=str(directory)),self.assertRaises(WorkflowError):
                self.stage(event["event_sha256"],destination=directory)
        self.assertFalse(any(self.root.glob("*.reviewed_claim_unverified_speech.srt")))

    def test_journal_tamper_before_export_refuses_to_write_file(self):
        event=self.admit()
        with sqlite3.connect(self.ledger.path) as db:
            db.execute("DELETE FROM transcript_review_command_nonces")
        with self.assertRaises(WorkflowError):
            self.stage(event["event_sha256"],destination=self.root)
        self.assertFalse(any(self.root.glob("*.reviewed_claim_unverified_speech.srt")))

    def test_no_export_default_checks_strict_review_without_writing(self):
        event=self.admit()
        before=set(self.root.iterdir())
        output=self.stage(event["event_sha256"])
        self.assertFalse(output["exclusive_file_created"])
        self.assertIsNone(output["export_basename"])
        self.assertEqual(before,set(self.root.iterdir()))
        self.assertFalse(output["publishing_authorized"])


if __name__=="__main__":
    unittest.main()
