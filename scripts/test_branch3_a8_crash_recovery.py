"""Adversarial A8 recovery decisions: no automatic retry even if reports look good."""
from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime,timezone

from scripts.branch3_a8_private_cas_ledger import (
    GENESIS,new_ledger,append_simulated_event,PrivateCASBlocked
)
from scripts.branch3_a8_crash_recovery import (
    ANCHOR,AT,NOW,SCENARIOS,MAX_WORKERS,RecoveryBlocked,
    check_inventory_claim,classify_recovery,fixture_report,
    simulate_competing_workers,synthetic_subject
)
from scripts.branch3_a8_exhaustive_inventory import (
    inspect_uploaded_inventory
)
from scripts.test_branch3_a8_exhaustive_inventory import (
    synthetic_api
)

SUBJECT=synthetic_subject(0)
OTHER=synthetic_subject(1)


def ledger_with_reservation(subject=None):
    return append_simulated_event(
        new_ledger(),kind="RESERVE_SYNTHETIC",
        anchor=ANCHOR,now=NOW,at_utc=AT,
        **(SUBJECT if subject is None else subject)
    )


def decision(ledger,scenario,subject=None,inventory=None,anchor=None):
    return classify_recovery(
        ledger=ledger,anchor=ANCHOR if anchor is None else anchor,
        now=NOW,scenario=scenario,
        inventory_claim=inventory,
        **(SUBJECT if subject is None else subject)
    )


def safe(result):
    assert result["decision"].startswith("HOLD_")
    for key in (
        "authenticated_google_inventory_proven_by_this_function",
        "original_uploaded_video_binary_sha256_proven",
        "external_anchor_immutability_proven",
        "real_remote_cas_linearizability_proven",
        "second_github_put_allowed","automatic_upload_retry_allowed",
        "youtube_video_insert_authorized","youtube_schedule_authorized",
        "youtube_publish_authorized"
    ):
        assert result[key] is False, key
    assert result["owner_manual_reconciliation_required"] is True
    assert result["github_api_calls"]==result["google_api_calls"]==0
    txt=json.dumps(result)
    for secret in (SUBJECT["release_id"],SUBJECT["media_sha256"],
                   "A234567890a","B234567890b"):
        assert secret not in txt


class A8CrashRecoveryTests(unittest.TestCase):

    def test_all_ambiguous_outcomes_without_reservation_are_hold(self):
        for scenario in sorted(SCENARIOS):
            with self.subTest(scenario=scenario):
                got=decision(new_ledger(),scenario)
                safe(got)
                self.assertFalse(got["exact_attempt_event_seen"])
                self.assertEqual(got["decision"],
                    "HOLD_CONTRADICTORY_COMMIT_CONFIRMATION"
                    if scenario=="CAS_CONFIRMED_READBACK"
                    else "HOLD_NO_PROVEN_RESERVATION_NO_RETRY")

    def test_all_outcomes_with_reserved_record_are_hold(self):
        current=ledger_with_reservation()
        for scenario in sorted(SCENARIOS):
            with self.subTest(scenario=scenario):
                r=decision(current,scenario)
                safe(r)
                self.assertTrue(r["exact_attempt_event_seen"])
                self.assertFalse(r["attempt_ever_marked_remote_unknown"])
                self.assertTrue(r["global_event_chain_replayed"])
                self.assertTrue(r["caller_prior_anchor_matched"])
        self.assertEqual(
            decision(current,"CAS_CONFIRMED_READBACK")["decision"],
            "HOLD_GITHUB_RESERVATION_CONFIRMED_NOT_YOUTUBE_PERMISSION"
        )
        self.assertEqual(decision(current,"CAS_CONFLICT_409")["decision"],
                         "HOLD_GITHUB_CAS_CONFLICT_NO_SECOND_WRITE")

    def test_ever_unknown_reservation_remains_hold_across_all_scenarios(self):
        ledger=append_simulated_event(
            ledger_with_reservation(),
            kind="MARK_UNKNOWN_NO_RETRY",
            at_utc="2026-11-13T11:59:30Z",
            anchor=ANCHOR,now=NOW,**SUBJECT
        )
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                d=decision(ledger,scenario)
                safe(d)
                self.assertTrue(d["attempt_ever_marked_remote_unknown"])
                self.assertEqual(d["decision"],
                   "HOLD_UNKNOWN_REMOTE_STATE_OWNER_MUST_RECONCILE")

    def test_other_release_or_same_media_already_reserved_blocks(self):
        ledger=ledger_with_reservation(OTHER)
        for alter in (
            {**SUBJECT,"media_sha256":OTHER["media_sha256"]},
            {**SUBJECT,"release_id":OTHER["release_id"]},
        ):
            with self.subTest(alter=alter):
                got=decision(ledger,"NO_WRITE_STARTED",alter)
                safe(got)
                self.assertTrue(got["duplicate_release_or_media_other_attempt_seen"])
                self.assertEqual(got["decision"],
                    "HOLD_DUPLICATE_RELEASE_OR_MEDIA_CROSS_ATTEMPT")
        # Different release, media digest, etc. must not be coalesced.
        safe(decision(ledger,"CAS_TIMEOUT_UNKNOWN",SUBJECT))

    def test_inventory_snapshot_even_with_zero_videos_never_allows_retry(self):
        calls=[]
        snapshot=inspect_uploaded_inventory(
            "SYNTHETIC_ACCESS_TOKEN_NOT_LIVE_01234567890",
            http_call=synthetic_api(calls,pages=[
                {"kind":"youtube#playlistItemListResponse","items":[]}
            ])
        )
        self.assertEqual(snapshot["uploaded_playlist_videos_checked"],0)
        r=decision(new_ledger(),"CAS_TIMEOUT_UNKNOWN",inventory=snapshot)
        safe(r)
        self.assertTrue(r["owner_supplied_inventory_report_shape_checked"])
        self.assertFalse(r["authenticated_google_inventory_proven_by_this_function"])
        self.assertFalse(r["original_uploaded_video_binary_sha256_proven"])
        s=decision(ledger_with_reservation(),"YOUTUBE_VIDEO_ID_UNVERIFIED",
                   inventory=snapshot)
        safe(s)
        self.assertEqual(s["decision"],
                         "HOLD_YOUTUBE_ID_OR_ORIGINAL_FILE_SHA_NOT_AUTHENTICATED")

    def test_invalid_inventory_or_forged_binaries_are_rejected(self):
        snapshot=inspect_uploaded_inventory(
            "SYNTHETIC_ACCESS_TOKEN_NOT_LIVE_01234567890",
            http_call=synthetic_api([],pages=[
                {"kind":"youtube#playlistItemListResponse","items":[]}
            ])
        )
        mutations=(
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("owner_google_channel_identity_matched",False),
            ("youtube_upload_authorized",True),
            ("automatic_duplicate_retry_authorized",True),
            ("real_time_remote_completeness_guaranteed",True),
            ("exact_uploaded_binary_sha256_verified",True),
            ("actual_youtube_write_calls",1),
            ("uploaded_playlist_videos_checked",-1),
            ("uploaded_playlist_videos_checked",1),
            ("uploaded_playlist_pages_checked",21),
            ("private_count",True),
            ("video_ids",["A234567890a"]),
        )
        for key,val in mutations:
            changed=copy.deepcopy(snapshot)
            changed[key]=val
            with self.subTest(key=key,val=val),self.assertRaises(
                RecoveryBlocked
            ):
                decision(new_ledger(),"READBACK_FAILED",inventory=changed)

    def test_corrupted_journal_wrong_anchor_and_out_of_order_rejected(self):
        valid=ledger_with_reservation()
        variants=[]
        d=copy.deepcopy(valid);d["head_sha256"]="f"*64;variants.append(d)
        d=copy.deepcopy(valid);d["events"][0]["event_sha256"]="b"*64;variants.append(d)
        d=copy.deepcopy(valid);d["sequence"]=999;variants.append(d)
        d=copy.deepcopy(valid);d["channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA";variants.append(d)
        for ledger in variants:
            with self.subTest(ledger=ledger),self.assertRaises(RecoveryBlocked):
                decision(ledger,"CRASH_AFTER_PUT_UNKNOWN")
        with self.assertRaises(RecoveryBlocked):
            decision(new_ledger(),"CAS_CONFLICT_409",
                     anchor={"sequence":1,"head_sha256":"c"*64})
        with self.assertRaises(RecoveryBlocked):
            classify_recovery(
                ledger=valid,anchor=ANCHOR,
                now=datetime(2026,11,13,12),
                scenario="CAS_TIMEOUT_UNKNOWN",**SUBJECT
            )

    def test_malformed_subject_scenario_and_typo_fail(self):
        for key,val in (
            ("release_id","wrong-release"),
            ("media_sha256","x"*64),
            ("metadata_sha256","AB"*32),
            ("rights_evidence_sha256",None),
        ):
            tampered={**SUBJECT,key:val}
            with self.subTest(key=key),self.assertRaises(RecoveryBlocked):
                decision(new_ledger(),"NO_WRITE_STARTED",tampered)
        with self.assertRaises(RecoveryBlocked):
            decision(new_ledger(),"UPLOAD_CONFIRMED")
        with self.assertRaises(RecoveryBlocked):
            decision(new_ledger(),None)

    def test_stress_2_to_12_independent_mock_workers_all_hold(self):
        executions=0
        for n in (2,3,4,5,6,7,8,10,12):
            for seed in range(11):
                with self.subTest(n=n,seed=seed):
                    result=simulate_competing_workers(
                        workers=n,seed=seed,same_media=(seed%2==0))
                    self.assertEqual(result["worker_count"],n)
                    self.assertEqual(result["accepted_synthetic_cas_updates"],1)
                    self.assertEqual(result["rejected_stale_cas_updates"],n-1)
                    self.assertEqual(result["global_attempt_count"],1)
                    self.assertTrue(result["all_workers_explicit_hold"])
                    self.assertFalse(result["github_linearizable_concurrency_proven"])
                    self.assertFalse(result["youtube_video_insert_authorized"])
                    self.assertFalse(result["youtube_publish_authorized"])
                    self.assertEqual(result["actual_github_requests"],0)
                    executions+=1
        self.assertEqual(executions,99)

    def test_worker_bounds_bad_inputs_and_safety_report(self):
        for n in (0,1,13,True):
            with self.subTest(n=n),self.assertRaises(RecoveryBlocked):
                simulate_competing_workers(workers=n,seed=1)
        for seed in (-1,100001,True,0.5):
            with self.subTest(seed=seed),self.assertRaises(RecoveryBlocked):
                simulate_competing_workers(workers=3,seed=seed)
        fixture=fixture_report()
        self.assertEqual(fixture["synthetic_scenarios_exercised"],32)
        self.assertTrue(fixture["all_scenarios_one_model_reservation_only"])
        self.assertTrue(fixture["all_scenarios_never_retry_or_upload"])
        self.assertFalse(fixture["real_global_cas_writer_deployed"])
        self.assertFalse(fixture["external_rollback_resistant_anchor_enrolled"])
        self.assertFalse(fixture["youtube_video_insert_authorized"])
        self.assertEqual(fixture["actual_google_api_calls"],0)


if __name__=="__main__":
    unittest.main()
