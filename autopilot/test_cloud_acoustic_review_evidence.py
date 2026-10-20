"""Cryptographic sidecar-byte binding tests, no audio or secrets stored."""
from dataclasses import replace
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.test_cloud_signed_transcript_reviews import fixture,resign,NOW,EXCLUDED
from autopilot.cloud_signed_transcript_reviews import transcript_digest
from autopilot.cloud_acoustic_review_evidence import verify_signed_acoustic_sidecars


def _data(candidate,claim):
    words=candidate.words
    return {
        "schema_version":1,
        "scope":"UNVERIFIED_ACOUSTIC_REVIEW_CLAIM",
        "role":claim.role,"reviewer_id":claim.reviewer_id,
        "lane":candidate.lane,"episode_id":candidate.episode_id,
        "media_sha256":candidate.media_sha256,
        "transcript_sha256":transcript_digest(candidate),
        "authored_srt_sha256":candidate.authored_draft_srt_sha256,
        "claimed_method":"synthetic_test",
        "observed_language_claim":candidate.declared_language,
        "word_anchors":[{
            "index":i,"text":words[i].text,
            "start_ms":words[i].start_ms,"end_ms":words[i].end_ms,
        } for i in (0,len(words)//2,len(words)-1)],
        "note":"Synthetic metadata only. No actual listener or transcription was involved.",
        "independent_real_world_listener_verified":False,
        "youtube_publishing_authorized":False,
    }


class SignedAcousticEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary=TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory=Path(temporary.name)
        self.fixture=fixture("short_hi")
        candidate,media,audio,keys,registry,attestations=self.fixture
        files={}
        self.payloads={}
        signed=[]
        for entry in attestations:
            role=entry.claim.role
            item=_data(candidate,entry.claim)
            raw=json.dumps(item,sort_keys=True,
                           ensure_ascii=False,separators=(",",":")).encode()
            p=self.directory/(role+".json")
            p.write_bytes(raw)
            signed.append(resign(
                entry,keys[entry.claim.reviewer_id],
                evidence_sha256=sha256(raw).hexdigest(),
            ))
            files[entry.claim.reviewer_id]=p
            self.payloads[entry.claim.reviewer_id]=item
        self.signed=tuple(signed)
        self.files=files

    def check(self,*,files=None,signed=None,fixture=None):
        candidate,media,audio,keys,registry,unused=fixture or self.fixture
        return verify_signed_acoustic_sidecars(
            candidate=candidate,media=media,audio_screen=audio,
            signed_attestations=self.signed if signed is None else signed,
            registry=registry,
            excluded_creator_publisher_ids=EXCLUDED,
            evidence_files=self.files if files is None else files,
            now=NOW,
        )

    def test_exact_signed_evidence_bytes_verify_without_speech_approval(self):
        answer=self.check()
        self.assertEqual(answer["checked_anchor_count"],6)
        self.assertTrue(answer["signed_bytes_hash_match"])
        self.assertTrue(answer["sidecar_text_and_timestamps_match"])
        self.assertFalse(answer["actual_listening_or_asr_execution_verified"])
        self.assertFalse(answer["real_world_reviewer_independence_verified"])
        self.assertFalse(answer["publishing_authorized"])
        self.assertEqual(len(answer["signed_sidecar_hashes"]),2)

    def test_altered_metadata_even_with_same_word_count_is_rejected(self):
        reviewer=next(iter(self.files))
        path=self.files[reviewer]
        path.write_bytes(path.read_bytes().replace(b"synthetic_test",b"claimed_asr_review"))
        with self.assertRaises(WorkflowError):
            self.check()

    def test_malicious_party_resigning_modified_sidecar_cannot_fake_anchor(self):
        candidate,media,audio,keys,registry,_=self.fixture
        first=self.signed[0]
        reviewer=first.claim.reviewer_id
        p=self.files[reviewer]
        item=dict(self.payloads[reviewer])
        anchors=[dict(a) for a in item["word_anchors"]]
        anchors[0]["start_ms"]+=1
        item["word_anchors"]=anchors
        raw=json.dumps(item,sort_keys=True,ensure_ascii=False,
                       separators=(",",":")).encode()
        p.write_bytes(raw)
        resigned=resign(first,keys[reviewer],
                        evidence_sha256=sha256(raw).hexdigest())
        with self.assertRaises(WorkflowError):
            self.check(signed=(resigned,self.signed[1]))

    def test_wrong_language_or_media_hash_even_with_valid_resign_denied(self):
        candidate,media,audio,keys,registry,_=self.fixture
        first=self.signed[0]
        reviewer=first.claim.reviewer_id
        for key,value in (("observed_language_claim","en"),
                          ("media_sha256","f"*64),
                          ("transcript_sha256","e"*64)):
            with self.subTest(key=key):
                changed=dict(self.payloads[reviewer],**{key:value})
                raw=json.dumps(changed,sort_keys=True,
                               ensure_ascii=False,separators=(",",":")).encode()
                self.files[reviewer].write_bytes(raw)
                resigned=resign(first,keys[reviewer],
                                evidence_sha256=sha256(raw).hexdigest())
                with self.assertRaises(WorkflowError):
                    self.check(signed=(resigned,self.signed[1]))

    def test_duplicate_json_fields_denied_even_if_signed_after_change(self):
        candidate,media,audio,keys,registry,_=self.fixture
        first=self.signed[0]
        reviewer=first.claim.reviewer_id
        raw=self.files[reviewer].read_bytes().replace(
            b'"schema_version":1',b'"schema_version":1,"schema_version":1'
        )
        self.files[reviewer].write_bytes(raw)
        signed=resign(first,keys[reviewer],
                      evidence_sha256=sha256(raw).hexdigest())
        with self.assertRaises(WorkflowError):
            self.check(signed=(signed,self.signed[1]))

    def test_symlink_or_missing_or_relative_sidecar_denied(self):
        reviewer=next(iter(self.files))
        alias=self.directory/"alias.json"
        alias.symlink_to(self.files[reviewer])
        for changed in (alias,self.directory/"missing.json",Path("relative.json")):
            with self.subTest(path=str(changed)),self.assertRaises(WorkflowError):
                self.check(files={**self.files,reviewer:changed})

    def test_oversized_sidecar_denied_before_json_or_signature_reuse(self):
        reviewer=next(iter(self.files))
        self.files[reviewer].write_bytes(b" "*8193)
        with self.assertRaises(WorkflowError):
            self.check()

    def test_false_independent_approval_and_publishing_flags_denied(self):
        candidate,media,audio,keys,registry,_=self.fixture
        entry=self.signed[0]
        reviewer=entry.claim.reviewer_id
        for field in ("independent_real_world_listener_verified",
                      "youtube_publishing_authorized"):
            with self.subTest(field=field):
                obj=dict(self.payloads[reviewer],**{field:True})
                raw=json.dumps(obj,sort_keys=True,ensure_ascii=False,
                               separators=(",",":")).encode()
                self.files[reviewer].write_bytes(raw)
                signed=resign(entry,keys[reviewer],
                              evidence_sha256=sha256(raw).hexdigest())
                with self.assertRaises(WorkflowError):
                    self.check(signed=(signed,self.signed[1]))

    def test_missing_second_role_or_unsigned_digests_refused(self):
        first=self.signed[0]
        with self.assertRaises(WorkflowError):
            self.check(signed=(first,))
        reviewer=first.claim.reviewer_id
        wrong=resign(first,self.fixture[3][reviewer],evidence_sha256="0"*64)
        with self.assertRaises(WorkflowError):
            self.check(signed=(wrong,self.signed[1]))
        with self.assertRaises(WorkflowError):
            self.check(files={reviewer:self.files[reviewer]})

    def test_exactly_three_sampled_words_do_not_prove_real_speech(self):
        answer=self.check()
        self.assertEqual(answer["checked_anchor_count"],6)
        self.assertFalse(answer["speech_caption_sync_verified"])
        self.assertFalse(answer["spoken_language_verified"])
        self.assertFalse(answer["voice_and_visual_rights_verified"])
        self.assertEqual(answer["monthly_recurring_infrastructure_inr"],0)


if __name__=="__main__":
    unittest.main()
