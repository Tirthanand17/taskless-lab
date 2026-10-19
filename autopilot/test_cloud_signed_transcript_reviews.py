"""Signed transcript-review rehearsal; ephemeral Ed25519 keys ONLY."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import base64
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autopilot.cloud_transcript_alignment_intake import CandidateWordTranscript
from autopilot.test_cloud_transcript_alignment_intake import packet
from autopilot.cloud_signed_transcript_reviews import (
    TrustedTranscriptReviewer,TranscriptAttestationClaim,
    SignedTranscriptAttestation,transcript_digest,_canonical,
    verify_signed_transcript_attestations,
)

NOW=datetime(2026,10,19,9,tzinfo=timezone.utc)
EXCLUDED=frozenset(("video_creator","channel_publisher"))


def fixture(lane="short_en"):
    candidate,media,audio=packet(lane)
    private={}
    registry={}
    signed=[]
    for role,name in (
        ("transcriber","transcriber_qa"),
        ("independent_listener","listener_qa"),
    ):
        key=Ed25519PrivateKey.generate()
        private[name]=key
        public=key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        registry[name]=TrustedTranscriptReviewer(
            name,"key_"+name,role,base64.b64encode(public).decode(),
        )
        claim=TranscriptAttestationClaim(
            transcript_sha256=transcript_digest(candidate),
            lane=lane,episode_id=candidate.episode_id,
            media_sha256=media.video_sha256,
            authored_srt_sha256=candidate.authored_draft_srt_sha256,
            reviewer_id=name,key_id="key_"+name,role=role,
            decision="ACCEPT",
            assessed_at_utc=(NOW-timedelta(minutes=7)).isoformat(),
            expires_at_utc=(NOW+timedelta(hours=1)).isoformat(),
            evidence_sha256=sha256(("synthetic_evidence_"+role).encode()).hexdigest(),
            review_notes="Synthetic key-only fixture, no audio heard by a person.",
            receipt_id="receipt_"+name,
        )
        signed.append(SignedTranscriptAttestation(
            claim,base64.b64encode(key.sign(_canonical(claim))).decode()
        ))
    return candidate,media,audio,private,registry,tuple(signed)


def resign(signed,key,**changes):
    claim=replace(signed.claim,**changes)
    return SignedTranscriptAttestation(
        claim,base64.b64encode(key.sign(_canonical(claim))).decode(),
    )


def verify(f,*,candidate=None,media=None,audio=None,signed=None,
           registry=None,excluded=EXCLUDED,now=NOW):
    a,b,c,_,r,s=f
    return verify_signed_transcript_attestations(
        candidate=a if candidate is None else candidate,
        media=b if media is None else media,
        audio_screen=c if audio is None else audio,
        signed_attestations=s if signed is None else signed,
        registry=r if registry is None else registry,
        excluded_creator_publisher_ids=excluded,now=now,
    )


class SignedTranscriptionTests(unittest.TestCase):
    def test_two_roles_three_lanes_signed_records_never_claim_speech(self):
        for lane in ("short_en","short_hi","long_hi"):
            f=fixture(lane)
            with self.subTest(lane=lane):
                report=verify(f)
                self.assertEqual(report["blocking_reasons"],())
                self.assertEqual(report["status"],
                  "SIGNED_TRANSCRIPT_RECORDS_AWAITING_REAL_WORLD_VERIFICATION")
                self.assertEqual(
                    report["valid_roles"],
                    ("independent_listener","transcriber"),
                )
                self.assertTrue(report[
                    "identity_attestation_authenticated_to_provisioned_keys"
                ])
                for field in (
                    "real_transcriber_or_listener_identity_independently_verified",
                    "actual_audio_words_verified",
                    "spoken_language_verified","spoken_word_subtitle_sync_verified",
                    "voice_consent_and_asset_rights_verified",
                    "publishing_authorized","youtube_upload_authorized",
                ):
                    self.assertFalse(report[field])

    def test_wrong_cryptographic_key_cannot_be_supplied_by_receipt(self):
        f=fixture()
        *_,keys,registry,signed=f
        adversary=Ed25519PrivateKey.generate()
        bad=resign(signed[0],adversary)
        report=verify(f,signed=(bad,signed[1]))
        self.assertIn(
            "INVALID_OR_STALE_TRANSCRIPT_SIGNATURE",report["blocking_reasons"]
        )

    def test_signed_transcript_sha_and_audio_video_hash_binding(self):
        f=fixture()
        a,b,c,keys,registry,signed=f
        for wrong in (
            {"transcript_sha256":"0"*64},
            {"media_sha256":"f"*64},
            {"authored_srt_sha256":"f"*64},
            {"lane":"short_hi"},
            {"episode_id":"csv_tutorial_short_hi"},
        ):
            altered=resign(signed[0],keys[signed[0].claim.reviewer_id],**wrong)
            with self.subTest(change=wrong):
                result=verify(f,signed=(altered,signed[1]))
                self.assertIn("INVALID_OR_STALE_TRANSCRIPT_SIGNATURE",
                              result["blocking_reasons"])
        updated=replace(a,words=a.words[:-1])
        # An invalid original candidate is refused *before* signatures.
        with self.assertRaises(Exception):
            verify(f,candidate=updated)

    def test_revoked_or_mismatched_registry_role_and_key_denied(self):
        f=fixture()
        a,b,c,keys,registry,signed=f
        reviewer=signed[0].claim.reviewer_id
        for bad in (
            replace(registry[reviewer],active=False),
            replace(registry[reviewer],role="independent_listener"),
            replace(registry[reviewer],key_id="key_replaced"),
        ):
            changed={**registry,reviewer:bad}
            with self.subTest(registration=bad),self.assertNotEqual(
                verify(f,registry=changed)["blocking_reasons"],(),
            )

    def test_excluded_creator_or_publisher_cannot_sign_as_independent_listener(self):
        f=fixture()
        a,b,c,keys,registry,signed=f
        id=signed[1].claim.reviewer_id
        report=verify(f,excluded=frozenset(("video_creator",id)))
        self.assertIn(
            "CREATOR_PUBLISHER_CANNOT_ATTEST_TRANSCRIPT",
            report["blocking_reasons"],
        )

    def test_expired_future_and_too_distant_expiry_denied(self):
        f=fixture()
        a,b,c,keys,registry,signed=f
        reviewer=signed[0].claim.reviewer_id
        for change in (
            {"assessed_at_utc":(NOW+timedelta(minutes=1)).isoformat()},
            {"assessed_at_utc":(NOW-timedelta(days=3)).isoformat()},
            {"expires_at_utc":(NOW-timedelta(seconds=1)).isoformat()},
            {"expires_at_utc":(NOW+timedelta(days=5)).isoformat()},
        ):
            altered=resign(signed[0],keys[reviewer],**change)
            with self.subTest(change=change):
                report=verify(f,signed=(altered,signed[1]))
                self.assertIn(
                    "INVALID_OR_STALE_TRANSCRIPT_SIGNATURE",
                    report["blocking_reasons"],
                )

    def test_explicit_reject_or_missing_role_stays_blocked(self):
        f=fixture()
        a,b,c,keys,registry,signed=f
        rej=resign(signed[1],keys[signed[1].claim.reviewer_id],
                   decision="REJECT")
        report=verify(f,signed=(signed[0],rej))
        self.assertIn("INDEPENDENT_TRANSCRIPT_REVIEW_REJECTED",
                      report["blocking_reasons"])
        report=verify(f,signed=(signed[0],))
        self.assertIn("TRANSCRIBER_AND_INDEPENDENT_LISTENER_REQUIRED",
                      report["blocking_reasons"])

    def test_duplicate_receipt_or_same_reviewer_cannot_fake_distinct_roles(self):
        f=fixture()
        a,b,c,keys,registry,signed=f
        duplicate=verify(f,signed=(signed[0],signed[0]))
        self.assertIn("DUPLICATE_TRANSCRIPT_RECEIPT",
                      duplicate["blocking_reasons"])
        reviewer=signed[0].claim.reviewer_id
        forgery=resign(signed[1],keys[reviewer],
                       reviewer_id=reviewer,key_id=signed[0].claim.key_id)
        changed={**registry,reviewer:replace(registry[reviewer],
                                              role="independent_listener")}
        self.assertNotEqual(verify(f,signed=(signed[0],forgery),
                                   registry=changed)["blocking_reasons"],())

    def test_unsigned_change_rejected_and_bad_notes_or_evidence_denied(self):
        f=fixture()
        a,b,c,keys,registry,signed=f
        changed=replace(signed[0].claim,decision="REJECT")
        from autopilot.cloud_signed_transcript_reviews import SignedTranscriptAttestation
        altered=SignedTranscriptAttestation(changed,signed[0].signature_ed25519_b64)
        self.assertIn("INVALID_OR_STALE_TRANSCRIPT_SIGNATURE",
                      verify(f,signed=(altered,signed[1]))["blocking_reasons"])
        reviewer=signed[0].claim.reviewer_id
        for fields in (
            {"review_notes":"too short"},
            {"evidence_sha256":"bad"},
        ):
            new=resign(signed[0],keys[reviewer],**fields)
            self.assertIn("INVALID_OR_STALE_TRANSCRIPT_SIGNATURE",
                          verify(f,signed=(new,signed[1]))["blocking_reasons"])

    def test_no_approval_under_fixture_and_wrong_clock_fails_closed(self):
        f=fixture()
        out=verify(f)
        self.assertFalse(out["publishing_authorized"])
        self.assertFalse(out["actual_audio_words_verified"])
        self.assertEqual(out["monthly_recurring_infrastructure_inr"],0)
        with self.assertRaises(Exception):
            verify(f,now=NOW.replace(tzinfo=None))


if __name__=="__main__":
    unittest.main()
