"""B3d4c2b3b no-network mock vault metadata and signed backup integrity tests.

All keys are throwaway Ed25519 fixtures created in GitHub CI; never owner
keys, real cloud IAM policies, provider credential values or video release.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, replace
from hashlib import sha256
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autopilot.private_cloud_recovery_preflight import (
    STATUS,RECOVERY_STATUS,DOMAIN,ReadinessError,
    SecretRequirement,PrivateCloudRequirements,MockAuditEvent,
    build_mock_recovery_manifest,verify_mock_restored_backup,
    inspect_private_cloud_requirements,canonical,
)

def sh(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def plan(provider="aws_secrets_manager",region="us-east-1"):
    purposes={
        "inference_gateway":"gemini_draft_api_credential",
        "ledger_gateway":"postgres_mock_gateway_credential",
        "youtube_publisher":"youtube_oauth_refresh_credential",
    }
    entries=tuple(SecretRequirement(
        role=role,purpose=purpose,
        logical_secret_ref=f"flowminute://vault/{role}/{purpose}/version-1",
        workload_principal_sha256=sh(f"fake_custodian_{role}"),
        resource_policy_sha256=sh(f"fake_policy_{role}"),
        private_endpoint_policy_sha256=sh(f"fake_network_{role}"),
        encryption_policy_sha256=sh(f"fake_encryption_{role}"),
        cloud_backend=provider,region_id=region,
        allowed_operation="read_secret_version",
        session_ttl_seconds=600,
        max_rotation_interval_days=30,
        requires_private_endpoint=True,
        requires_access_audit=True,
        requires_workload_identity=True,
    ) for role,purpose in purposes.items())
    return PrivateCloudRequirements(
        schema_version=1,
        isolated_owner_project_sha256=sh("invented_project"),
        cloud_backend=provider,region_id=region,
        planned_secret_requirements=entries,
        database_tls_minimum="TLS1.3",
        database_owner_no_login=True,
        deny_runtime_db_superuser=True,
        independent_backup_reader_required=True,
        independent_external_audit_anchor_required=True,
        max_backup_rpo_minutes=15,
        max_backup_rto_minutes=60,
    )


def events():
    return [
        MockAuditEvent(1,"lease_one","fm_20261105_short_am","BURN",sh("mock_a")),
        MockAuditEvent(2,"lease_one","fm_20261105_short_am","MOCK_CLOSE",sh("mock_a_end")),
        MockAuditEvent(3,"lease_two","fm_20261105_long","BURN",sh("mock_b")),
        MockAuditEvent(4,"lease_three","fm_20261105_short_pm","BURN",sh("mock_c")),
    ]


def sealed_example(generation=1):
    signer=Ed25519PrivateKey.generate()
    pub=signer.public_key().public_bytes(
        serialization.Encoding.Raw,serialization.PublicFormat.Raw
    )
    ev=events()[:2] if generation==1 else events()
    prior=None
    if generation==2:
        prior=build_mock_recovery_manifest(
            events=events()[:2],snapshot_bytes=b"synthetic_postgres_burn_backup_v1",
            backup_id="backup_round_one",generation=1,
        )
    image=(b"synthetic_postgres_burn_backup_v1"
           if generation==1 else b"synthetic_postgres_burn_backup_v2")
    manifest=build_mock_recovery_manifest(
        events=ev,snapshot_bytes=image,
        backup_id="backup_round_one" if generation==1 else "backup_round_two",
        generation=generation,parent=prior,
    )
    head=sha256(canonical(asdict(manifest))).hexdigest()
    signature=base64.b64encode(signer.sign(DOMAIN+bytes.fromhex(head))).decode()
    return {
        "manifest":manifest,"events":ev,"snapshot":image,
        "parent":prior,"anchor":head,"signature":signature,
        "public":base64.b64encode(pub).decode(),
        "signer":signer,
        "expected_generation":generation,"expected_event_count":len(ev),
    }


def check(example):
    return verify_mock_restored_backup(
        manifest=example["manifest"],
        restored_bytes=example["snapshot"],
        restored_events=example["events"],
        parent=example["parent"],
        externally_pinned_manifest_sha256=example["anchor"],
        detached_external_signature_b64=example["signature"],
        trusted_external_anchor_public_key_b64=example["public"],
        expected_generation=example["expected_generation"],
        expected_event_count=example["expected_event_count"],
    )


class PrivateCloudRequirementsTests(unittest.TestCase):
    def test_three_distinct_principals_and_purposes_are_metadata_only(self):
        p=plan()
        out=inspect_private_cloud_requirements(p)
        self.assertEqual(out["status"],STATUS)
        self.assertEqual(out["distinct_secret_purposes"],3)
        self.assertTrue(out["requirements_schema_valid"])
        self.assertFalse(out["cloud_secret_actually_exists"])
        self.assertFalse(out["actual_workload_identity_authenticated"])
        self.assertFalse(out["cloud_iam_permissions_independently_verified"])
        self.assertFalse(out["independent_immutable_audit_service_connected"])
        self.assertFalse(out["live_generative_inference_enabled"])
        self.assertFalse(out["youtube_upload_enabled"])
        self.assertFalse(out["release_authorized"])
        serialized=json.dumps(asdict(p))
        self.assertNotIn("BEGIN PRIVATE KEY",serialized)
        self.assertNotIn("ya29.",serialized)
        self.assertNotIn("x-goog-api-key",serialized)

    def test_aws_and_gcp_are_deployment_research_options_not_connected_services(self):
        for backend,region in (
            ("aws_secrets_manager","us-east-1"),
            ("gcp_secret_manager","asia-south1"),
        ):
            with self.subTest(backend=backend,region=region):
                output=inspect_private_cloud_requirements(plan(backend,region))
                self.assertFalse(output["private_endpoint_exists"])
                self.assertFalse(output["kms_key_policy_verified"])

    def test_cross_purpose_secret_ref_or_role_is_rejected(self):
        original=plan()
        for replacement in (
            "flowminute://vault/ledger_gateway/postgres_mock_gateway_credential/version-1",
            "flowminute://vault/*/gemini_draft_api_credential/version-1",
            "https://my.fake-secret-value.test",
            "flowminute://vault/inference_gateway/gemini_draft_api_credential/latest",
            "flowminute://vault/inference_gateway/gemini_draft_api_credential/version-0",
        ):
            with self.subTest(replacement=replacement):
                items=list(original.planned_secret_requirements)
                items[0]=replace(items[0],logical_secret_ref=replacement)
                with self.assertRaises(ReadinessError):
                    inspect_private_cloud_requirements(replace(
                        original,planned_secret_requirements=tuple(items)
                    ))

    def test_shared_workload_identity_or_duplicate_role_rejected(self):
        base=plan()
        for column in ("workload_principal_sha256","logical_secret_ref","role"):
            items=list(base.planned_secret_requirements)
            items[1]=replace(items[1],**{column:getattr(items[0],column)})
            with self.subTest(column=column),self.assertRaises(ReadinessError):
                inspect_private_cloud_requirements(replace(
                    base,planned_secret_requirements=tuple(items)
                ))

    def test_broad_permissions_and_missing_security_controls_rejected(self):
        base=plan()
        for field,value in (
            ("allowed_operation","all"),
            ("allowed_operation","admin"),
            ("allowed_operation","write_secret"),
            ("requires_access_audit",False),
            ("requires_private_endpoint",False),
            ("requires_workload_identity",False),
            ("session_ttl_seconds",True),
            ("session_ttl_seconds",3600),
            ("max_rotation_interval_days",0),
            ("max_rotation_interval_days",365),
            ("resource_policy_sha256",""),
            ("encryption_policy_sha256","f"*63),
            ("private_endpoint_policy_sha256","f"*65),
            ("cloud_backend","unapproved_vault"),
        ):
            with self.subTest(field=field,value=value):
                items=list(base.planned_secret_requirements)
                items[0]=replace(items[0],**{field:value})
                with self.assertRaises(ReadinessError):
                    inspect_private_cloud_requirements(replace(
                        base,planned_secret_requirements=tuple(items)
                    ))

    def test_deployment_global_controls_must_all_be_required(self):
        base=plan()
        for field,value in (
            ("schema_version",True),
            ("isolated_owner_project_sha256","fake"),
            ("cloud_backend","random"),
            ("database_tls_minimum","TLS1.2"),
            ("database_owner_no_login",False),
            ("deny_runtime_db_superuser",False),
            ("independent_backup_reader_required",False),
            ("independent_external_audit_anchor_required",False),
            ("max_backup_rpo_minutes",0),
            ("max_backup_rpo_minutes",61),
            ("max_backup_rto_minutes",241),
        ):
            with self.subTest(field=field):
                with self.assertRaises(ReadinessError):
                    inspect_private_cloud_requirements(replace(base,**{field:value}))

    def test_missing_or_additional_secret_roles_denied(self):
        base=plan()
        with self.assertRaises(ReadinessError):
            inspect_private_cloud_requirements(replace(
                base,planned_secret_requirements=base.planned_secret_requirements[:2]
            ))
        with self.assertRaises(ReadinessError):
            inspect_private_cloud_requirements(replace(
                base,planned_secret_requirements=base.planned_secret_requirements+
                   (base.planned_secret_requirements[0],)
            ))


class MockExternalBackupEvidenceTests(unittest.TestCase):
    def test_external_test_signer_round_one_and_incremental_round_two(self):
        for generation in (1,2):
            with self.subTest(generation=generation):
                d=sealed_example(generation)
                out=check(d)
                self.assertEqual(out["status"],RECOVERY_STATUS)
                self.assertEqual(out["backup_generation"],generation)
                self.assertEqual(out["audit_event_count"],len(d["events"]))
                self.assertTrue(out["ordered_mock_audit_history_match"])
                self.assertFalse(out["actual_database_backup_restored_by_this_function"])
                self.assertFalse(out["real_external_anchor_independently_deployed"])
                self.assertFalse(out["trusted_real_world_signer_enrolled"])
                self.assertFalse(out["provider_live_call_enabled"])
                self.assertFalse(out["youtube_upload_enabled"])

    def test_mutated_snapshot_bytes_cannot_be_restored(self):
        d=sealed_example()
        d["snapshot"]=d["snapshot"]+b"attacker_metadata"
        with self.assertRaises(ReadinessError):
            check(d)

    def test_reordered_or_missing_history_denied(self):
        for mutation in ("reverse","omit","duplicate","renumber","different_payload"):
            with self.subTest(mutation=mutation):
                d=sealed_example(2)
                e=list(d["events"])
                if mutation=="reverse":
                    e.reverse()
                elif mutation=="omit":
                    e=e[:-1]
                elif mutation=="duplicate":
                    e[-1]=e[0]
                elif mutation=="renumber":
                    e[-1]=replace(e[-1],sequence=7)
                elif mutation=="different_payload":
                    e[-1]=replace(e[-1],value_sha256=sh("forged_changed_content"))
                d["events"]=e
                with self.assertRaises(ReadinessError):
                    check(d)

    def test_unanchored_self_computed_manifest_not_sufficient(self):
        d=sealed_example()
        d["anchor"]="f"*64
        with self.assertRaises(ReadinessError):
            check(d)

    def test_signed_by_untrusted_key_even_with_right_hash_denied(self):
        d=sealed_example()
        other=sealed_example()
        d["public"]=other["public"]
        with self.assertRaises(ReadinessError):
            check(d)

    def test_altered_manifest_fields_denied_even_if_signature_not_altered(self):
        for field,value in (
            ("backup_id","fake_backup"),("event_count",7),
            ("snapshot_sha256","0"*64),("parent_manifest_sha256","a"*64),
        ):
            with self.subTest(field=field):
                d=sealed_example()
                d["manifest"]=replace(d["manifest"],**{field:value})
                with self.assertRaises(ReadinessError):
                    check(d)

    def test_rollback_to_old_generation_denied_by_external_expected_head(self):
        old=sealed_example(1)
        latest=sealed_example(2)
        old["expected_generation"]=2
        old["expected_event_count"]=4
        old["anchor"]=latest["anchor"]
        with self.assertRaises(ReadinessError):
            check(old)

    def test_parent_history_rewrite_denied_even_with_changed_snapshot_and_new_manifest(self):
        previous=sealed_example(1)["manifest"]
        changed=list(events())
        changed[1]=replace(changed[1],value_sha256=sh("rewrote_finished_response"))
        with self.assertRaises(ReadinessError):
            build_mock_recovery_manifest(
                events=changed,snapshot_bytes=b"new backup",
                backup_id="backup_round_two",generation=2,parent=previous,
            )

    def test_cannot_start_second_generation_without_parent(self):
        with self.assertRaises(ReadinessError):
            build_mock_recovery_manifest(
                events=events(),snapshot_bytes=b"backup",backup_id="backup_no_parent",
                generation=2,parent=None,
            )

    def test_replay_parent_without_append_does_not_change_audit_count(self):
        prior=sealed_example(1)["manifest"]
        second=build_mock_recovery_manifest(
            events=events()[:2],snapshot_bytes=b"repeated data",
            backup_id="backup_next",generation=2,parent=prior,
        )
        self.assertEqual(second.event_count,prior.event_count)
        self.assertEqual(second.parent_event_count,prior.event_count)
        # Repeating an identical backup generation cannot invent new progress.
        self.assertNotEqual(
            sha256(canonical(asdict(second))).hexdigest(),
            sha256(canonical(asdict(prior))).hexdigest(),
        )

    def test_duplicate_or_missing_burn_before_close_denied(self):
        ev=events()
        bad=[
            [ev[1]],
            [ev[0],replace(ev[1],sequence=2,episode_id="fm_20261105_long")],
            [ev[0],replace(ev[0],sequence=2)],
            [ev[0],ev[1],replace(ev[1],sequence=3)],
        ]
        for row in bad:
            with self.subTest(length=len(row)),self.assertRaises(ReadinessError):
                build_mock_recovery_manifest(
                    events=row,snapshot_bytes=b"sample",
                    backup_id="backup_bad",generation=1,
                )

    def test_reject_unsafe_event_identity_actions_or_bad_sequence(self):
        first=events()[0]
        for field,value in (
            ("lease_id","../../etc/passwd"),("episode_id","wrong_account"),
            ("value_sha256","synthetic_secret"),("sequence",True),
            ("action","PUBLISH_VIDEO"),("action","RESET_LEDGER"),
        ):
            with self.subTest(field=field),self.assertRaises(ReadinessError):
                build_mock_recovery_manifest(
                    events=[replace(first,**{field:value})],snapshot_bytes=b"data",
                    backup_id="backup_bad_event",generation=1,
                )

    def test_signature_is_domain_separated_and_not_generic_hash(self):
        d=sealed_example()
        new_sig=base64.b64encode(d["signer"].sign(bytes.fromhex(d["anchor"]))).decode()
        d["signature"]=new_sig
        with self.assertRaises(ReadinessError):
            check(d)

    def test_invalid_base64_and_missing_public_key_denied(self):
        for bad in ("!!!!","a"*11,"",123):
            with self.subTest(bad=bad):
                d=sealed_example()
                d["public"]=bad
                with self.assertRaises(ReadinessError):
                    check(d)

    def test_nonbytes_and_oversized_backup_denied(self):
        for sample in (None,b"",bytearray(b"backup"),b"X"*2_000_001):
            with self.subTest(size=len(sample) if isinstance(sample,(bytes,bytearray)) else 0):
                with self.assertRaises(ReadinessError):
                    build_mock_recovery_manifest(
                        events=events(),snapshot_bytes=sample,
                        backup_id="backup_wrong",generation=1,
                    )

    def test_external_custodian_key_never_embedded_in_receipt(self):
        d=sealed_example(2)
        report=check(d)
        self.assertNotIn("signer",json.dumps(report))
        self.assertNotIn("private_key",json.dumps(report))
        self.assertNotIn("owner_approved",json.dumps(report))
        self.assertFalse(report["release_authorized"])


if __name__=="__main__":
    unittest.main()
