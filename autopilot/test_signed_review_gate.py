"""Phase 3C signed reviewer attestation tests; all keys are disposable and local.

No production key is created or saved. Synthetic reviews cannot certify any
real person, video, commercial license, or YouTube release.
"""
import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autopilot.media_rights_review import EvidencePacket
from autopilot.narration_inspection import AudioEvidence
from autopilot.render_inspection import MediaEvidence
from autopilot.signed_review_gate import (
    DIMENSIONS, ReviewClaim, SignedReview, TrustedReviewer, packet_digest,
    verify_separated_reviews, _canonical
)

NOW = datetime(2026, 10, 17, 15, tzinfo=timezone.utc)
EP = "flowminute_ep_01"


def media():
    video=MediaEvidence(
        "PASS_TECHNICAL_ONLY","a"*64,1080,1920,10.,25.,True,(),False,"h264","aac")
    audio=AudioEvidence("PASS_AUDIO_TECHNICAL_ONLY","b"*64,10.,48000,1,())
    return EvidencePacket(
        "INSPECTED_AWAITING_INDEPENDENT_REVIEW",
        video,audio,("asset_original_voice","asset_original_demo"),(),
        True,True,True,True
    )


def synthetic_review_bundle(*, packet=None, issued=None, expires=None):
    packet=packet or media()
    entries,registry,keys=[],{},{}
    created=issued or NOW-timedelta(minutes=20)
    expiry=expires or NOW+timedelta(hours=5)
    for i,dimension in enumerate(sorted(DIMENSIONS)):
        reviewer_id=f"reviewer_{i+1}"
        key_id=f"key_{i+1}"
        signing_key=Ed25519PrivateKey.generate()
        public_key=signing_key.public_key().public_bytes(
            serialization.Encoding.Raw,serialization.PublicFormat.Raw
        )
        registry[reviewer_id]=TrustedReviewer(
            reviewer_id,key_id,base64.b64encode(public_key).decode(),
            (dimension,))
        claim=ReviewClaim(
            EP,packet_digest(packet),packet.video.video_sha256,
            packet.narration.sha256_hex,dimension,reviewer_id,key_id,
            "PASS",created.isoformat(),expiry.isoformat(),
            (f"{i+1:064x}",),
            f"Synthetic fixture review of {dimension} evidence; not a real human approval",
            f"receipt_{i+1}"
        )
        entries.append(SignedReview(
            claim,base64.b64encode(signing_key.sign(_canonical(claim))).decode()))
        keys[reviewer_id]=signing_key
    return packet,entries,registry,keys


def resign(record, key, **changes):
    updated=replace(record.claim,**changes)
    return SignedReview(updated,base64.b64encode(key.sign(_canonical(updated))).decode())


def verify(packet,entries,registry,*,excluded=None,now=NOW):
    return verify_separated_reviews(
        episode_id=EP,packet=packet,
        signed_reviews=tuple(entries),registry=registry,
        excluded_creator_and_publisher_ids=excluded or
        frozenset(("creator_video","publisher_api")),
        now=now)


class SignedReviewTests(unittest.TestCase):
    def setUp(self):
        self.packet,self.receipts,self.registry,self.keys=synthetic_review_bundle()

    def test_four_separate_signed_reviews_never_authorize_upload(self):
        out=verify(self.packet,self.receipts,self.registry)
        self.assertEqual(out.status,"SIGNED_RECORDS_PRESENT_AWAITING_EXTERNAL_APPROVAL")
        self.assertEqual(out.problems,())
        self.assertEqual(set(out.valid_dimensions),DIMENSIONS)
        self.assertEqual(len(out.signed_reviewer_ids),4)
        self.assertFalse(out.human_review_observed_by_software)
        self.assertFalse(out.license_legality_verified_by_software)
        self.assertFalse(out.media_content_verified_by_software)
        self.assertFalse(out.publishing_authorized)
        self.assertFalse(out.scheduling_enabled)

    def test_missing_review_blocks(self):
        out=verify(self.packet,self.receipts[:3],self.registry)
        self.assertEqual(out.status,"BLOCKED_REVIEW_EVIDENCE")
        self.assertIn("REQUIRED_INDEPENDENT_REVIEW_MISSING",out.problems)

    def test_changed_video_file_hash_invalidates_every_review(self):
        other=replace(self.packet,video=replace(self.packet.video,video_sha256="f"*64))
        out=verify(other,self.receipts,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)
        self.assertFalse(out.publishing_authorized)

    def test_changed_audio_file_hash_invalidates_every_review(self):
        other=replace(self.packet,narration=replace(self.packet.narration,sha256_hex="f"*64))
        out=verify(other,self.receipts,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_changed_rights_packet_invalidates_review_binding(self):
        other=replace(self.packet,checked_asset_ids=self.packet.checked_asset_ids+("asset_new",))
        out=verify(other,self.receipts,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_missing_technical_preflight_blocks_even_with_valid_signatures(self):
        other=replace(self.packet,status="BLOCKED_TECHNICAL_PREFLIGHT")
        # Signatures bind to the old packet, so they are also invalidated.
        out=verify(other,self.receipts,self.registry)
        self.assertIn("MEDIA_OR_RIGHTS_PREFLIGHT_NOT_READY",out.problems)

    def test_signature_bitflip_rejected(self):
        edited=list(self.receipts)
        r=edited[0]
        sig=bytearray(base64.b64decode(r.signature_ed25519_b64))
        sig[15] ^= 0x20
        edited[0]=replace(r,signature_ed25519_b64=base64.b64encode(sig).decode())
        out=verify(self.packet,edited,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_unknown_or_revoked_reviewer_denied(self):
        registry=dict(self.registry)
        first=self.receipts[0].claim.reviewer_id
        registry[first]=replace(registry[first],active=False)
        out=verify(self.packet,self.receipts,registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_wrong_dimension_enrollment_denied(self):
        registry=dict(self.registry)
        first=self.receipts[0].claim.reviewer_id
        registry[first]=replace(registry[first],allowed_dimensions=("source_accuracy",))
        if self.receipts[0].claim.dimension=="source_accuracy":
            registry[first]=replace(registry[first],allowed_dimensions=("asset_rights",))
        out=verify(self.packet,self.receipts,registry)
        self.assertIn("REVIEWER_NOT_AUTHORIZED_FOR_DIMENSION",out.problems)

    def test_untrusted_receipt_key_cannot_override_pinned_public_key(self):
        entry=self.receipts[0]
        key=Ed25519PrivateKey.generate()
        edited=list(self.receipts)
        edited[0]=SignedReview(entry.claim,base64.b64encode(key.sign(_canonical(entry.claim))).decode())
        out=verify(self.packet,edited,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_review_expired_denied(self):
        first=self.receipts[0]
        changed=list(self.receipts)
        changed[0]=resign(first,self.keys[first.claim.reviewer_id],
                          assessed_at_utc=(NOW-timedelta(days=2)).isoformat(),
                          expires_at_utc=(NOW-timedelta(days=1)).isoformat())
        out=verify(self.packet,changed,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_future_review_denied(self):
        first=self.receipts[0]
        edited=list(self.receipts)
        edited[0]=resign(first,self.keys[first.claim.reviewer_id],
                         assessed_at_utc=(NOW+timedelta(minutes=1)).isoformat(),
                         expires_at_utc=(NOW+timedelta(hours=1)).isoformat())
        out=verify(self.packet,edited,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_rejection_never_approves(self):
        first=self.receipts[0]
        edited=list(self.receipts)
        edited[0]=resign(first,self.keys[first.claim.reviewer_id],decision="REJECT")
        out=verify(self.packet,edited,self.registry)
        self.assertIn("INDEPENDENT_REVIEW_REJECTED",out.problems)

    def test_creator_as_reviewer_disallowed_even_with_genuine_key(self):
        id0=self.receipts[0].claim.reviewer_id
        out=verify(self.packet,self.receipts,self.registry,
                   excluded=frozenset(("publisher_api",id0)))
        self.assertIn("CREATOR_OR_PUBLISHER_ATTEMPTED_TO_REVIEW",out.problems)

    def test_duplicate_same_receipt_detected(self):
        edited=[self.receipts[0],self.receipts[0],*self.receipts[1:]]
        out=verify(self.packet,edited,self.registry)
        self.assertIn("DUPLICATED_REVIEW_RECEIPT",out.problems)

    def test_duplicate_signer_across_reviews_denied_even_if_role_claimed(self):
        edited=list(self.receipts)
        first,second=edited[:2]
        changed_id=first.claim.reviewer_id
        claim=replace(second.claim,reviewer_id=changed_id,key_id=first.claim.key_id)
        edited[1]=SignedReview(claim,base64.b64encode(self.keys[changed_id].sign(_canonical(claim))).decode())
        registry=dict(self.registry)
        registry[changed_id]=replace(registry[changed_id],allowed_dimensions=
                                     (first.claim.dimension,second.claim.dimension))
        out=verify(self.packet,edited,registry)
        self.assertIn("REVIEWER_REUSED_ACROSS_DIMENSIONS",out.problems)

    def test_replay_on_another_episode_denied(self):
        out=verify_separated_reviews(
            episode_id="different_episode",packet=self.packet,
            signed_reviews=tuple(self.receipts),registry=self.registry,
            excluded_creator_and_publisher_ids=frozenset(("creator_video","publisher_api")),
            now=NOW)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_missing_owner_exclusion_list_stops(self):
        out=verify_separated_reviews(
            episode_id=EP,packet=self.packet,signed_reviews=tuple(self.receipts),
            registry=self.registry,excluded_creator_and_publisher_ids=frozenset(),
            now=NOW)
        self.assertIn("REVIEW_TRUST_BOUNDARY_INVALID",out.problems)

    def test_empty_evidence_claim_denied_even_with_real_signature(self):
        first=self.receipts[0]
        edited=list(self.receipts)
        edited[0]=resign(first,self.keys[first.claim.reviewer_id],evidence_sha256=())
        out=verify(self.packet,edited,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

    def test_invalid_base64_signature_denied(self):
        edited=list(self.receipts)
        edited[0]=replace(edited[0],signature_ed25519_b64="%%%invalid%%%")
        out=verify(self.packet,edited,self.registry)
        self.assertIn("INVALID_OR_STALE_REVIEW_SIGNATURE",out.problems)

if __name__=="__main__":
    unittest.main()
