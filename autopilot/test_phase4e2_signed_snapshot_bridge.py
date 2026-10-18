"""Phase 4E.2 local signed redacted snapshot verification. Synthetic ONLY."""
import base64
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autopilot.core import CHANNEL_ID
from autopilot.phase4d_signed_observations import (
    CollectorTrust,ObservationClaim,SignedObservation,ObservationBlocked,
    sanitized_snapshot_hash,_canonical,
)
from autopilot.phase4e_readonly_import import (
    parse_d1_schema_observation,parse_youtube_channel_video_observation,
)
from autopilot.phase4e2_signed_snapshot_bridge import inspect_signed_sanitized_phase4e_snapshots

NOW=datetime(2026,10,18,8,30,tzinfo=timezone.utc)
NONCE="nonce_bounded_sample_19"
VID="abc123def45"

def sample_d1():
    return parse_d1_schema_observation(table_list_rows=[
        {"name":"releases","type":"table","schema":"main"},
        {"name":"oauth_grants","type":"table","schema":"main"},
    ],table_details={
        "releases":{"columns":[
            {"name":"channel_id"},{"name":"episode_id"},{"name":"planned_utc"},
            {"name":"media_sha256"},{"name":"version"},
            {"name":"refresh_token","default_value":"SECRET_NEVER_ECHO"},
        ],"indexes":[
            {"unique":True,"columns":["channel_id","episode_id"]},
            {"unique":True,"columns":["refresh_token"]},
        ]},
        "oauth_grants":{"columns":[{"name":"refresh_token"}]}
    })

def sample_youtube():
    return parse_youtube_channel_video_observation(
        channel_response={"items":[{"id":CHANNEL_ID,"snippet":{"title":"SECRET"}}]},
        video_response={"items":[{
            "id":VID,"snippet":{"channelId":CHANNEL_ID,"title":"SECRET_VIDEO_NAME"},
            "status":{"privacyStatus":"private","publishAt":"2026-10-20T05:30:00Z"},
            "processingDetails":{"processingStatus":"succeeded"},
            "description":"SECRET_DESCRIPTION",
        }]},
    )

class OfflineSignedSnapshotBridgeTests(unittest.TestCase):
    def setUp(self):
        self.d1=sample_d1()
        self.youtube=sample_youtube()
        self.keys={}
        self.registry={}
        self.signed=[]
        for kind,id_ in (("d1_schema","collector_d1"),
                          ("youtube_history","collector_yt")):
            key=Ed25519PrivateKey.generate()
            self.keys[kind]=key
            pub=key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw)
            self.registry[id_]=CollectorTrust(
                collector_id=id_,key_id="key_"+id_,
                public_key_b64=base64.b64encode(pub).decode(),
                allowed_kind=kind,
            )
        self.resign()

    def resign(self):
        d={"d1_schema":self.d1,"youtube_history":self.youtube}
        self.signed=[]
        for kind,id_ in (("d1_schema","collector_d1"),
                          ("youtube_history","collector_yt")):
            claim=ObservationClaim(
                1,kind,CHANNEL_ID,id_,"key_"+id_,
                sanitized_snapshot_hash(d[kind]),NONCE,
                (NOW-timedelta(minutes=1)).isoformat(timespec="seconds"),
                (NOW+timedelta(minutes=5)).isoformat(timespec="seconds"),
            )
            self.signed.append(SignedObservation(
                claim,base64.b64encode(
                    self.keys[kind].sign(_canonical(claim))).decode()))

    def review(self,*,d1=None,youtube=None,signed=None,nonce=NONCE,seen=frozenset(),registry=None):
        return inspect_signed_sanitized_phase4e_snapshots(
            d1_snapshot=self.d1 if d1 is None else d1,
            youtube_snapshot=self.youtube if youtube is None else youtube,
            signed_observations=self.signed if signed is None else signed,
            trusted_registry=self.registry if registry is None else registry,
            request_nonce=nonce,already_seen_nonces=seen,now=NOW)

    def test_exact_bounded_verified_signatures_do_not_prove_remote_access(self):
        report=self.review()
        self.assertEqual(report["status"],
                         "OFFLINE_SIGNED_SANITIZED_READBACK_ONLY_PRODUCTION_BLOCKED")
        self.assertTrue(report["signed_integrity_for_exact_sanitized_snapshot_bytes"])
        self.assertEqual(report["d1_metadata_object_count"],1)
        self.assertEqual(report["candidate_canonical_table_count"],1)
        self.assertEqual(report["youtube_video_count"],1)
        self.assertFalse(report["live_authenticated_d1_access_verified"])
        self.assertFalse(report["live_authenticated_youtube_channel_owner_verified"])
        self.assertFalse(report["migration_authorized"])
        self.assertFalse(report["private_upload_or_scheduling_authorized"])
        self.assertFalse(report["public_publishing_authorized"])
        self.assertEqual(report["network_calls"],0)
        self.assertEqual(report["database_writes"],0)
        self.assertEqual(report["generated_sql"],[])
        self.assertNotIn("SECRET",str(report))
        self.assertNotIn(VID,str(report))
        self.assertNotIn("oauth_grants",str(report))
        self.assertEqual(len(report["snapshot_sha256_by_kind"]["d1_schema"]),64)

    def test_reversed_signature_order_is_deterministic(self):
        self.assertEqual(self.review(),self.review(signed=list(reversed(self.signed))))

    def test_changed_d1_snapshot_rejected_even_with_existing_signature(self):
        mutated=deepcopy(self.d1)
        mutated["objects"][0]["columns"].pop()
        with self.assertRaises(ObservationBlocked):
            self.review(d1=mutated)

    def test_changed_youtube_privacy_rejected_even_with_old_signature(self):
        changed=deepcopy(self.youtube)
        changed["videos"][0]["privacy"]="public"
        changed["videos"][0]["publish_at_utc"]=None
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=changed)

    def test_malformed_extra_secret_never_returned(self):
        changed=deepcopy(self.youtube)
        changed["api_access_token"]="SECRET"
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=changed)
        changed=deepcopy(self.d1)
        changed["objects"][0]["debug_sql"]="SECRET"
        with self.assertRaises(ObservationBlocked):
            self.review(d1=changed)

    def test_unsafe_protected_object_rejected_not_hashed_as_clean(self):
        changed=deepcopy(self.d1)
        changed["objects"][0]["name"]="refresh_token"
        with self.assertRaises(ObservationBlocked):
            self.review(d1=changed)

    def test_protected_column_and_unproved_index_rejected(self):
        changed=deepcopy(self.d1)
        changed["objects"][0]["columns"][0]["name"]="oauth_token"
        with self.assertRaises(ObservationBlocked):
            self.review(d1=changed)
        changed=deepcopy(self.d1)
        changed["objects"][0]["indexes"].append(
            {"unique":True,"columns":["nonexistent_column"]})
        with self.assertRaises(ObservationBlocked):
            self.review(d1=changed)

    def test_malformed_unhashable_index_fields_fail_with_redacted_observation_blocked(self):
        # The public verifier is separately callable with untrusted,
        # provider-shaped JSON; it must not rely on a private pre-validator.
        for invalid in ([], {}, None, 42, ["embedded"], {"oauth_refresh_token": "NEVER_ECHO"}):
            with self.subTest(invalid_type=type(invalid).__name__):
                changed=deepcopy(self.d1)
                changed["objects"][0]["indexes"][0]["columns"]=[
                    "channel_id",invalid]
                with self.assertRaises(ObservationBlocked) as cm:
                    self.review(d1=changed)
                self.assertNotIn("NEVER_ECHO",str(cm.exception))
                self.assertNotIn("oauth_refresh_token",str(cm.exception))

    def test_duplicate_or_non_identifier_index_columns_fail_closed(self):
        for columns in (["channel_id","channel_id"],
                        ["channel_id","not-a-valid-identifier"],
                        ["channel_id","nonexistent_field"]):
            with self.subTest(columns=columns):
                changed=deepcopy(self.d1)
                changed["objects"][0]["indexes"][0]["columns"]=columns
                with self.assertRaises(ObservationBlocked):
                    self.review(d1=changed)

    def _resign_d1_receipt_with_older_claim(self, skew_seconds):
        # Both signatures remain cryptographically correct and within the
        # Phase 4D per-receipt TTL. Only their cross-collector skew changes.
        prior=self.signed[0]
        changed=replace(
            prior.claim,
            collected_at_utc=(
                NOW-timedelta(minutes=1,seconds=skew_seconds)
            ).isoformat(timespec="seconds"),
        )
        self.signed[0]=SignedObservation(
            changed,
            base64.b64encode(
                self.keys["d1_schema"].sign(_canonical(changed))
            ).decode(),
        )

    def test_five_minute_receipt_claim_boundary_still_not_provider_proof(self):
        self._resign_d1_receipt_with_older_claim(300)
        report=self.review()
        self.assertEqual(report["signed_receipt_claim_skew_seconds"],300)
        self.assertTrue(report["signed_integrity_for_exact_sanitized_snapshot_bytes"])
        self.assertFalse(report["live_authenticated_d1_access_verified"])
        self.assertFalse(report["live_authenticated_youtube_channel_owner_verified"])
        self.assertFalse(report["migration_authorized"])
        self.assertFalse(report["public_publishing_authorized"])

    def test_sixth_minute_cross_collector_gap_denied_even_when_signed(self):
        self._resign_d1_receipt_with_older_claim(301)
        with self.assertRaisesRegex(
            ObservationBlocked,
            "Signed collector receipt claims are too far apart",
        ):
            self.review()

    def test_no_normal_receipt_skew_in_fixture_and_no_provider_authentication(self):
        report=self.review()
        self.assertEqual(report["signed_receipt_claim_skew_seconds"],0)
        self.assertEqual(report["youtube_non_succeeded_processing_count"],0)
        self.assertNotIn("NON_SUCCEEDED_YOUTUBE_PROCESSING_OBSERVED",report["blockers"])

    def test_non_succeeded_video_processing_reported_without_private_ids(self):
        for state in ("processing","failed","terminated","unknown"):
            with self.subTest(processing_state=state):
                self.youtube=parse_youtube_channel_video_observation(
                    channel_response={"items":[{"id":CHANNEL_ID}]},
                    video_response={"items":[{
                        "id":VID,
                        "snippet":{"channelId":CHANNEL_ID},
                        "status":{"privacyStatus":"private"},
                        "processingDetails":{"processingStatus":state},
                    }]},
                )
                self.resign()
                report=self.review()
                self.assertEqual(report["youtube_non_succeeded_processing_count"],1)
                self.assertIn("NON_SUCCEEDED_YOUTUBE_PROCESSING_OBSERVED",report["blockers"])
                self.assertEqual(
                    report["youtube_unknown_or_conflicting_count"],
                    int(state=="unknown"),
                )
                self.assertNotIn(VID,str(report))
                self.assertFalse(report["private_upload_or_scheduling_authorized"])
                self.assertFalse(report["public_publishing_authorized"])

    def test_missing_signature_wrong_nonce_and_replay_blocked(self):
        with self.assertRaises(ObservationBlocked):
            self.review(signed=self.signed[:1])
        with self.assertRaises(ObservationBlocked):
            self.review(nonce="nonce_changed")
        with self.assertRaises(ObservationBlocked):
            self.review(seen=frozenset({NONCE}))

    def test_swapped_roles_or_one_shared_collector_denied(self):
        incorrect=dict(self.registry)
        incorrect["collector_d1"]=replace(
            incorrect["collector_d1"],allowed_kind="youtube_history")
        with self.assertRaises(ObservationBlocked):
            self.review(registry=incorrect)

    def test_provider_authenticated_claim_cannot_be_added(self):
        modified=deepcopy(self.youtube)
        modified["saw_authenticated_provider_request"]=True
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=modified)
        modified=deepcopy(self.d1)
        modified["migration_authorized"]=True
        with self.assertRaises(ObservationBlocked):
            self.review(d1=modified)

    def test_incomplete_pagination_is_explained_not_approved(self):
        self.youtube=parse_youtube_channel_video_observation(
            channel_response={"items":[{"id":CHANNEL_ID}]},
            video_response={"items":[{"id":VID,"snippet":{"channelId":CHANNEL_ID},
                                      "status":{"privacyStatus":"private"}}],
                            "nextPageToken":"sample_next_page"},
        )
        self.resign()
        report=self.review()
        self.assertIn("INCOMPLETE_YOUTUBE_VIDEO_PAGINATION",report["blockers"])
        self.assertIn("UNKNOWN_OR_CONFLICTING_VIDEO_STATUS",report["blockers"])
        self.assertFalse(report["youtube_pagination_complete"])

    def test_missing_canonical_ledger_is_not_migration_authority(self):
        self.d1=parse_d1_schema_observation(
            table_list_rows=[{"name":"releases","type":"table","schema":"main"}],
            table_details={"releases":{"columns":[{"name":"episode_id"}]}},
        )
        self.resign()
        report=self.review()
        self.assertEqual(report["candidate_canonical_table_count"],0)
        self.assertIn("NO_SINGLE_UNAMBIGUOUS_CANONICAL_LEDGER_TABLE",
                      report["blockers"])
        self.assertFalse(report["migration_authorized"])

    def test_unknown_owner_or_added_video_field_rejected(self):
        changed=deepcopy(self.youtube)
        changed["videos"][0]["channel_id"]="not_flowminute"
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=changed)
        changed=deepcopy(self.youtube)
        changed["videos"][0]["title"]="SECRET"
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=changed)

    def test_bad_video_count_duplicate_id_and_contradictory_uncertainty(self):
        changed=deepcopy(self.youtube)
        changed["video_count"]=99
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=changed)
        changed=deepcopy(self.youtube)
        changed["videos"].append(deepcopy(changed["videos"][0]))
        changed["video_count"]=2
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=changed)
        changed=deepcopy(self.youtube)
        changed["videos"][0]["uncertain_metadata"]=True
        changed["has_conflicting_state"]=True
        with self.assertRaises(ObservationBlocked):
            self.review(youtube=changed)

    def test_no_video_rows_is_insufficient_even_if_signed(self):
        self.youtube=parse_youtube_channel_video_observation(
            channel_response={"items":[{"id":CHANNEL_ID}]},
            video_response={"items":[]},
        )
        self.resign()
        report=self.review()
        self.assertEqual(report["youtube_video_count"],0)
        self.assertFalse(report["live_authenticated_youtube_channel_owner_verified"])
        self.assertFalse(report["migration_authorized"])

    def test_all_samples_are_private_free_of_network_access(self):
        r=self.review()
        for key in ("private_media_or_oauth_secret_accessed",
                    "schema_specific_migration_sql_generated",
                    "production_ledger_writer_deployed",
                    "historical_video_ids_reconciled_to_release_rows"):
            self.assertIs(r[key],False)

if __name__=="__main__":
    unittest.main()
