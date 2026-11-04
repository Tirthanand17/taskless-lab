"""B3d3b adversarial verifier tests. All keys/claims are disposable CI fixtures.

A test signature can be mathematically valid without a real reviewer,
truthful claim, original video, private evidence store or release authority.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, replace
from datetime import timedelta
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from autopilot.test_script_continuity_gate import NOW, EXCLUDED, serialized
from autopilot.test_source_claim_preflight import (
    accepted_excerpt, source_bound_fixture, draft_claim,
)
from autopilot.source_claim_preflight import script_surface_docket, atomic_claim_docket
from autopilot.independent_fact_review_gate import (
    PURPOSE, FactReviewClaim, SignedFactReview, TrustedFactReviewer,
    FactReviewError, STATUS_PENDING, STATUS_BLOCKED, canonical_json,
    review_docket_hash, verify_independent_fact_records,
)


def fixture(index=0, *, has_claim=None):
    # Only slot 0 has a synthetic primary-source excerpt in this fixture.
    # Other release slots intentionally test fully covered no-claim packets.
    if has_claim is None:
        has_claim = index == 0
    item = source_bound_fixture(index)
    proposal, slot, observations, anchor, script_registry, seal, _ = item
    surface = script_surface_docket(
        proposal, slot, observations, seal=seal,
        anchor_manifest_sha256=anchor,
        registry=script_registry,
        excluded_creator_and_publisher_ids=EXCLUDED, now=NOW,
    )
    excerpt = accepted_excerpt()
    excerpts = [excerpt] if has_claim else []
    claims_raw = [draft_claim(surface, excerpt)] if has_claim else []
    claims = atomic_claim_docket(surface, claims_raw, excerpts)
    docket_hash = review_docket_hash(surface, claims, excerpts)
    keys, registry, reviews = {}, {}, []
    for name, key_id, scope in (
        ("coverage_reviewer", "coverage_key", "surface"),
        ("accuracy_reviewer", "accuracy_key", "claim"),
    ):
        key = Ed25519PrivateKey.generate()
        raw_pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        keys[name] = key
        registry[name] = TrustedFactReviewer(
            name, key_id, base64.b64encode(raw_pub).decode(), (scope,)
        )
    def add_review(scope_kind, scope_id, decision, refs=()):
        idx = len(reviews) + 1
        person = "coverage_reviewer" if scope_kind == "surface" else "accuracy_reviewer"
        claim = FactReviewClaim(
            purpose=PURPOSE,
            channel_id=surface["episode_id"] and "UCCcL9Q_jqVq6LJmnYUSAFZA",
            episode_id=surface["episode_id"],
            manifest_sha256=surface["manifest_sha256"],
            review_docket_sha256=docket_hash,
            scope_kind=scope_kind,
            scope_id=scope_id,
            decision=decision,
            reviewer_id=person,
            key_id=registry[person].key_id,
            assessed_at_utc=(NOW - timedelta(minutes=12)).isoformat(),
            expires_at_utc=(NOW + timedelta(hours=3)).isoformat(),
            evidence_refs=tuple(refs),
            reviewer_notes=(
                "Synthetic unit-test review decision only; independent human "
                "fact truth and copyright legitimacy are not being attested."
            ),
            receipt_id=f"receipt_{idx:03d}",
        )
        reviews.append(SignedFactReview(
            claim, base64.b64encode(keys[person].sign(canonical_json(asdict(claim)))).decode()
        ))
    for s in surface["surface_rows"]:
        mapped = any(x["surface_id"] == s["surface_id"] for x in claims["potential_claims"])
        add_review("surface", s["surface_id"], "CLAIMS_MAPPED" if mapped else "NO_FACTUAL_ASSERTION")
    for claim in claims["potential_claims"]:
        refs = tuple(sorted(
            f'{link["source_id"]}:{link["excerpt_sha256"]}' for link in claim["cited_excerpt_links"]
        ))
        add_review("claim", claim["atomic_claim_id"], "SUPPORTED", refs)
    return {
        "item": item,
        "surface": surface, "claims": claims,
        "claims_raw": claims_raw, "excerpts": excerpts,
        "reviewer_keys": keys, "reviewers": registry,
        "signed_reviews": reviews,
    }


def test_verify(data, *, exclusions=EXCLUDED, now=NOW):
    p, slot, obs, anchor, script_registry, seal, _ = data["item"]
    return verify_independent_fact_records(
        p, slot, obs,
        script_seal=seal,
        external_script_anchor_sha256=anchor,
        script_registry=script_registry,
        proposed_atomic_claims=data["claims_raw"],
        source_excerpt_records=data["excerpts"],
        signed_reviews=data["signed_reviews"],
        fact_reviewer_registry=data["reviewers"],
        excluded_creator_and_publisher_ids=exclusions,
        now=now,
    )


def resign(record, key, **patch):
    edited = replace(record.claim, **patch)
    return SignedFactReview(
        edited, base64.b64encode(key.sign(canonical_json(asdict(edited)))).decode()
    )


class IndependentFactReviewTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def test_full_signed_records_only_prove_record_coverage_not_truth_or_release(self):
        r = test_verify(self.data)
        self.assertEqual(r["status"], STATUS_PENDING)
        self.assertEqual(r["problems"], [])
        self.assertEqual(r["signed_review_records_valid_count"],
                         r["expected_surface_count"] + r["expected_atomic_claim_count"])
        self.assertEqual(r["expected_atomic_claim_count"], 1)
        self.assertTrue(r["signed_review_record_coverage_satisfied"])
        for field in (
            "reviewers_real_identity_authenticated_by_software",
            "independent_fact_truth_verified_by_software",
            "independent_atomic_claim_completeness_proven",
            "external_private_review_ledger_deployed",
            "external_owner_review_and_release_grant_present",
            "full_final_render_or_thumbnail_reviewed",
            "originality_or_rights_approved",
            "media_render_enabled", "youtube_upload_enabled",
            "youtube_schedule_enabled", "release_authorized",
        ):
            self.assertFalse(r[field], field)

    def test_three_distinct_video_slots_remain_nonpublishing(self):
        seen=set()
        for index in range(3):
            r=test_verify(fixture(index))
            self.assertEqual(r["status"], STATUS_PENDING)
            self.assertFalse(r["release_authorized"])
            seen.add(r["script_manifest_sha256"])
        self.assertEqual(len(seen), 3)

    def test_zero_claims_with_signed_nonfactual_surfaces_never_grants_fact_truth(self):
        r=test_verify(fixture(has_claim=False))
        self.assertEqual(r["status"], STATUS_PENDING)
        self.assertEqual(r["expected_atomic_claim_count"], 0)
        self.assertFalse(r["independent_atomic_claim_completeness_proven"])
        self.assertFalse(r["release_authorized"])

    def test_missing_surface_review_blocks(self):
        self.data["signed_reviews"].pop(0)
        r=test_verify(self.data)
        self.assertEqual(r["status"], STATUS_BLOCKED)
        self.assertIn("REQUIRED_SCRIPT_SURFACE_OR_CLAIM_REVIEW_MISSING", r["problems"])

    def test_missing_claim_review_blocks(self):
        self.data["signed_reviews"].pop()
        r=test_verify(self.data)
        self.assertEqual(r["status"], STATUS_BLOCKED)
        self.assertIn("REQUIRED_SCRIPT_SURFACE_OR_CLAIM_REVIEW_MISSING",r["problems"])

    def test_replayed_receipt_or_duplicate_scope_denied(self):
        self.data["signed_reviews"].append(self.data["signed_reviews"][0])
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_missing_independent_trust_registry_rejected(self):
        self.data["reviewers"]={}
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_replaced_verification_key_denies_valid_old_signature(self):
        item=self.data["reviewers"]["coverage_reviewer"]
        new=Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.data["reviewers"]["coverage_reviewer"]=replace(
            item, public_key_ed25519_b64=base64.b64encode(new).decode())
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_revoked_reviewer_denied(self):
        x=self.data["reviewers"]["coverage_reviewer"]
        self.data["reviewers"]["coverage_reviewer"]=replace(x, active=False)
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_creator_or_publisher_cannot_review(self):
        with self.assertRaises(FactReviewError):
            test_verify(self.data, exclusions=frozenset((*EXCLUDED,"coverage_reviewer")))

    def test_missing_creator_publisher_exclusion_denied(self):
        with self.assertRaises(FactReviewError):
            test_verify(self.data, exclusions=frozenset())

    def test_changed_source_hash_after_signing_rejected(self):
        self.data["item"][2]["sources"][0]["response_sha256"]="f"*64
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_changed_script_title_after_signing_rejected(self):
        self.data["item"][0]["title"]="Tampered title even though review records exist"
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_claim_text_altered_without_rereview_fails(self):
        self.data["claims_raw"][0]["claim_text"]="Forged unreviewed quote"
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_claim_to_source_mismatch_fails(self):
        self.data["claims_raw"][0]["excerpt_keys"]=[["f"*24,"e"*64]]
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_changed_excerpt_packet_without_new_review_fails(self):
        self.data["excerpts"][0]["adjacent_context_sha256"]="e"*64
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_invalid_signature_bitflip_rejected(self):
        r=self.data["signed_reviews"][0]
        sig=bytearray(base64.b64decode(r.signature_ed25519_b64))
        sig[11]^=0x80
        self.data["signed_reviews"][0]=replace(
            r, signature_ed25519_b64=base64.b64encode(sig).decode())
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_changed_signed_channel_rejected_even_resigned(self):
        r=self.data["signed_reviews"][0]
        self.data["signed_reviews"][0]=resign(
            r, self.data["reviewer_keys"]["coverage_reviewer"],
            channel_id="foreign_youtube_channel")
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_wrong_slot_episode_signature_replayed_denied(self):
        r=self.data["signed_reviews"][0]
        self.data["signed_reviews"][0]=resign(
            r, self.data["reviewer_keys"]["coverage_reviewer"],
            episode_id="fm_20261106_short_pm")
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_tampered_docket_sha_even_if_resigned_denied(self):
        r=self.data["signed_reviews"][0]
        self.data["signed_reviews"][0]=resign(
            r, self.data["reviewer_keys"]["coverage_reviewer"],
            review_docket_sha256="f"*64)
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_wrong_scope_type_or_unknown_id_denied(self):
        for field, value in (("scope_kind", "upload"), ("scope_id", "thumbnail:0")):
            with self.subTest(field=field):
                d=fixture()
                r=d["signed_reviews"][0]
                d["signed_reviews"][0]=resign(r,d["reviewer_keys"]["coverage_reviewer"],**{field:value})
                with self.assertRaises(FactReviewError):
                    test_verify(d)

    def test_wrong_role_not_permitted_to_sign_claim(self):
        r=self.data["signed_reviews"][-1]
        self.data["signed_reviews"][-1]=resign(
            r,self.data["reviewer_keys"]["coverage_reviewer"],
            reviewer_id="coverage_reviewer",key_id="coverage_key")
        with self.assertRaises(FactReviewError):
            test_verify(self.data)

    def test_same_identity_cannot_review_coverage_and_claim(self):
        d=fixture()
        r=d["signed_reviews"][-1]
        d["reviewers"]["coverage_reviewer"]=replace(
            d["reviewers"]["coverage_reviewer"], allowed_scopes=("surface","claim"))
        d["signed_reviews"][-1]=resign(
            r,d["reviewer_keys"]["coverage_reviewer"],
            reviewer_id="coverage_reviewer",key_id="coverage_key")
        result=test_verify(d)
        self.assertEqual(result["status"],STATUS_BLOCKED)
        self.assertIn("FACT_REVIEWER_NOT_SEPARATED_FROM_SCOPE_REVIEWER",result["problems"])

    def test_expired_fact_review_denied(self):
        with self.assertRaises(FactReviewError):
            test_verify(self.data,now=NOW+timedelta(hours=5))

    def test_future_review_denied(self):
        with self.assertRaises(FactReviewError):
            test_verify(self.data,now=NOW-timedelta(hours=1))

    def test_naive_clock_denied(self):
        with self.assertRaises(FactReviewError):
            test_verify(self.data,now=NOW.replace(tzinfo=None))

    def test_signed_rejection_blocks_entire_episode(self):
        d=fixture()
        r=d["signed_reviews"][-1]
        d["signed_reviews"][-1]=resign(
            r,d["reviewer_keys"]["accuracy_reviewer"],decision="REJECT")
        out=test_verify(d)
        self.assertEqual(out["status"],STATUS_BLOCKED)
        self.assertIn("SIGNED_REVIEW_REJECTED",out["problems"])
        self.assertFalse(out["release_authorized"])

    def test_unresolved_fact_blocks_entire_episode(self):
        d=fixture()
        r=d["signed_reviews"][-1]
        d["signed_reviews"][-1]=resign(
            r,d["reviewer_keys"]["accuracy_reviewer"],decision="UNRESOLVED")
        out=test_verify(d)
        self.assertEqual(out["status"],STATUS_BLOCKED)
        self.assertIn("FACTUAL_REVIEW_UNRESOLVED",out["problems"])

    def test_surface_claim_mismatch_rejected_even_if_resigned(self):
        d=fixture()
        title_i=next(i for i,r in enumerate(d["signed_reviews"]) if
                     r.claim.scope_kind=="surface" and r.claim.scope_id=="title:0")
        r=d["signed_reviews"][title_i]
        d["signed_reviews"][title_i]=resign(
            r,d["reviewer_keys"]["coverage_reviewer"],decision="NO_FACTUAL_ASSERTION")
        with self.assertRaises(FactReviewError):
            test_verify(d)

    def test_false_mapped_surface_without_claim_denied(self):
        d=fixture(has_claim=False)
        r=d["signed_reviews"][0]
        d["signed_reviews"][0]=resign(
            r,d["reviewer_keys"]["coverage_reviewer"],decision="CLAIMS_MAPPED")
        with self.assertRaises(FactReviewError):
            test_verify(d)

    def test_claim_support_requires_all_exact_known_excerpt_refs(self):
        d=fixture()
        r=d["signed_reviews"][-1]
        d["signed_reviews"][-1]=resign(
            r,d["reviewer_keys"]["accuracy_reviewer"],evidence_refs=())
        with self.assertRaises(FactReviewError):
            test_verify(d)

    def test_unsupported_extra_source_excerpt_rejected(self):
        d=fixture()
        r=d["signed_reviews"][-1]
        d["signed_reviews"][-1]=resign(
            r,d["reviewer_keys"]["accuracy_reviewer"],evidence_refs=("a"*24+":"+"b"*64,))
        with self.assertRaises(FactReviewError):
            test_verify(d)

    def test_forged_unsigned_positive_fields_in_source_packet_fail(self):
        d=fixture()
        d["excerpts"][0]["semantic_support_for_claim_verified"]=True
        with self.assertRaises(FactReviewError):
            test_verify(d)

    def test_reviewer_notes_missing_denied(self):
        d=fixture()
        r=d["signed_reviews"][0]
        d["signed_reviews"][0]=resign(
            r,d["reviewer_keys"]["coverage_reviewer"],reviewer_notes="ok")
        with self.assertRaises(FactReviewError):
            test_verify(d)

    def test_production_revocation_and_custodian_expiry_still_required(self):
        d=fixture()
        d["item"][4]["trusted_custodian"]=replace(
            d["item"][4]["trusted_custodian"], active=False)
        with self.assertRaises(FactReviewError):
            test_verify(d)


if __name__=="__main__":
    unittest.main()
