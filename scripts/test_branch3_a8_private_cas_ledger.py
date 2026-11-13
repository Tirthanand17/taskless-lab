"""Adversarial A8 cross-run GitHub Contents CAS model; zero real API calls."""
from __future__ import annotations

import base64
import copy
from datetime import datetime, timezone
import json
from threading import Barrier, Lock
from concurrent.futures import ThreadPoolExecutor
import unittest

from scripts.branch3_a8_private_first_dryrun import CLIVOX, candidate_attempt_key
from scripts.branch3_a8_private_cas_ledger import (
    GENESIS, FILE_PATH, PrivateCASBlocked, POLICY, STATE_RESERVED, STATE_UNKNOWN,
    append_simulated_event, build_github_put_contract, bytes_for_ledger,
    decode_github_contents, fixture_report, new_ledger,
    reconcile_unknown_commit, simulate_cas, validate_closed_policy,
    verify_ledger
)
from scripts.branch3_a2_private_ledger_cas import git_blob_sha

NOW = datetime(2026, 11, 13, 6, 0, tzinfo=timezone.utc)
AT = "2026-11-13T05:58:00Z"
RELEASE = "clivox_demo_a8_unique_release_v1"
D = {"release_id": RELEASE, "media_sha256": "a" * 64,
     "metadata_sha256": "b" * 64, "rights_evidence_sha256": "c" * 64}
ANCHOR = {"sequence": 0, "head_sha256": GENESIS}


def append(ledger, kind="RESERVE_SYNTHETIC", *, d=None, anchor=None,
           at=AT):
    args=D if d is None else d
    return append_simulated_event(
        ledger, kind=kind, at_utc=at, anchor=ANCHOR if anchor is None else anchor,
        now=NOW, **args
    )


def attempt_key(d=None):
    args=D if d is None else d
    return candidate_attempt_key(channel_id=CLIVOX, **args)


def response(ledger):
    raw=bytes_for_ledger(ledger)
    return {
        "type": "file", "name": "attempt-ledger-v1.json",
        "path": FILE_PATH, "encoding": "base64",
        "size": len(raw), "sha": git_blob_sha(raw),
        "content": base64.b64encode(raw).decode("ascii")
    }


class SharedFakeGitHubContent:
    """Simulates SHA-conditional update; NOT the live GitHub API."""
    def __init__(self):
        self.mutex=Lock()
        self.raw=response(new_ledger())

    def get(self):
        with self.mutex:
            return copy.deepcopy(self.raw)

    def try_put(self, body):
        with self.mutex:
            new_blob=simulate_cas(
                current_remote_blob_sha=self.raw["sha"],
                proposed_body=body
            )
            raw=base64.b64decode(body["content"],validate=True)
            self.raw={
                **self.raw, "sha":new_blob, "size":len(raw),
                "content":body["content"]
            }
            return new_blob


class GitHubCASAttemptTests(unittest.TestCase):

    def test_genesis_is_safely_inactive(self):
        report=verify_ledger(new_ledger(), anchor=ANCHOR, now=NOW)
        self.assertEqual(report["event_count"],0)
        self.assertFalse(report["youtube_upload_authorized"])
        self.assertFalse(report["production_cross_run_store_provisioned"])
        self.assertFalse(report["independent_external_durable_anchor_verified"])
        self.assertEqual(report["actual_youtube_api_calls"],0)

    def test_reservation_then_ambiguous_hold_is_monotonic(self):
        first=append(new_ledger())
        self.assertEqual(first["sequence"],1)
        self.assertEqual(first["events"][0]["kind"],"RESERVE_SYNTHETIC")
        self.assertEqual(new_ledger()["sequence"],0)
        second=append(first,"MARK_UNKNOWN_NO_RETRY",at="2026-11-13T05:59:00Z")
        self.assertEqual(second["sequence"],2)
        self.assertEqual(verify_ledger(second,anchor=ANCHOR,now=NOW)["attempt_count"],1)
        for ledger in (first,second):
            decision=reconcile_unknown_commit(
                observed_ledger=ledger, attempt_key=attempt_key(),
                anchor=ANCHOR, now=NOW
            )
            self.assertTrue(decision["remote_ledger_contains_attempt"])
            self.assertFalse(decision["automatic_retry_allowed"])
            self.assertFalse(decision["youtube_upload_authorized"])
        with self.assertRaises(PrivateCASBlocked):
            append(second,"MARK_UNKNOWN_NO_RETRY",at="2026-11-13T05:59:30Z")

    def test_duplicate_release_media_and_attempt_denied(self):
        first=append(new_ledger())
        for d in (
            dict(D),
            {**D, "metadata_sha256":"d"*64},
            {**D, "release_id":"clivox_demo_different_release_v1"}
        ):
            with self.subTest(d=d), self.assertRaisesRegex(
                PrivateCASBlocked,"DUPLICATE_RELEASE_MEDIA_OR_ATTEMPT"
            ):
                append(first,d=d)

    def test_github_cas_one_writer_wins_others_conflict(self):
        server=SharedFakeGitHubContent()
        barrier=Barrier(6)
        def runner(_):
            local=server.get()
            parsed, blob_sha=decode_github_contents(local)
            proposal=build_github_put_contract(
                existing_blob_sha=blob_sha,updated=append(parsed)
            )
            barrier.wait()
            try:
                server.try_put(proposal)
                return "COMMITTED"
            except PrivateCASBlocked:
                return "STALE"
        with ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(runner,range(6)))
        self.assertEqual(results.count("COMMITTED"),1)
        self.assertEqual(results.count("STALE"),5)
        observed,_=decode_github_contents(server.get())
        self.assertEqual(verify_ledger(observed,anchor=ANCHOR,now=NOW)["event_count"],1)

    def test_ambiguous_put_commit_or_no_commit_always_holds(self):
        server=SharedFakeGitHubContent()
        original=server.get()
        before,sha=decode_github_contents(original)
        proposal=build_github_put_contract(existing_blob_sha=sha,
                                           updated=append(before))
        # Network response lost AFTER simulated server accepted it.
        server.try_put(proposal)
        observed,_=decode_github_contents(server.get())
        r=reconcile_unknown_commit(
            observed_ledger=observed, attempt_key=attempt_key(),
            anchor=ANCHOR,now=NOW
        )
        self.assertEqual(r["decision"],"HOLD_PREVIOUS_RESERVATION_POSSIBLY_COMMITTED")
        self.assertFalse(r["youtube_upload_authorized"])
        # Network response lost BEFORE the simulated server accepted the PUT.
        r=reconcile_unknown_commit(
            observed_ledger=before, attempt_key=attempt_key(),
            anchor=ANCHOR,now=NOW
        )
        self.assertEqual(r["decision"],"HOLD_COMMIT_NOT_CONFIRMED_NO_RETRY")
        self.assertFalse(r["automatic_retry_allowed"])

    def test_older_blob_and_rollback_anchor_never_allow_second_upload(self):
        first=append(new_ledger())
        pinned={"sequence":1,"head_sha256":first["head_sha256"]}
        with self.assertRaisesRegex(PrivateCASBlocked,"ROLLBACK_OR_FORK"):
            verify_ledger(new_ledger(),anchor=pinned,now=NOW)
        with self.assertRaises(PrivateCASBlocked):
            reconcile_unknown_commit(
                observed_ledger=new_ledger(),attempt_key=attempt_key(),
                anchor=pinned,now=NOW
            )
        self.assertEqual(verify_ledger(first,anchor=pinned,now=NOW)["event_count"],1)

    def test_exact_release_digest_channel_and_type_forgery_denied(self):
        first=append(new_ledger())
        mutations=(
            ("channel_id","UC"+"z"*22),
            ("sequence",0), ("head_sha256","f"*64),
            ("ledger_id","flowminute"),
        )
        for field,value in mutations:
            case=copy.deepcopy(first)
            case[field]=value
            with self.subTest(field=field),self.assertRaises(PrivateCASBlocked):
                verify_ledger(case,anchor=ANCHOR,now=NOW)
        for field,value in (
            ("media_sha256","e"*64),
            ("metadata_sha256","f"*64),
            ("rights_evidence_sha256","0"*64),
            ("release_id","clivox_demo_modified_release_v1"),
            ("attempt_key","f"*64),
            ("prev_sha256","b"*64),
            ("event_sha256","a"*64),
            ("recorded_at_utc","2026-11-13T06:01:00Z"),
            ("kind","REMOTE_UPLOADED_CONFIRMED"),
            ("sequence",True),
        ):
            case=copy.deepcopy(first)
            case["events"][0][field]=value
            with self.subTest(field=field),self.assertRaises(PrivateCASBlocked):
                verify_ledger(case,anchor=ANCHOR,now=NOW)

    def test_event_injection_and_unknown_hold_without_reservation_denied(self):
        first=append(new_ledger())
        case=copy.deepcopy(first)
        case["events"][0]["owner_private_token"]="secret"
        with self.assertRaises(PrivateCASBlocked):
            verify_ledger(case,anchor=ANCHOR,now=NOW)
        with self.assertRaises(PrivateCASBlocked):
            append(new_ledger(),"MARK_UNKNOWN_NO_RETRY")

    def test_invalid_utc_and_duplicated_or_reordered_events_denied(self):
        first=append(new_ledger())
        second=append(first,"MARK_UNKNOWN_NO_RETRY",at="2026-11-13T05:59:00Z")
        for mutation in (
            lambda c:c["events"].reverse(),
            lambda c:c["events"].append(copy.deepcopy(c["events"][0])),
            lambda c:c["events"][1].update(recorded_at_utc="2026-11-13T05:00:00Z"),
            lambda c:c["events"][1].update(recorded_at_utc="2026-11-13T05:59:00+00:00"),
        ):
            case=copy.deepcopy(second)
            mutation(case)
            with self.assertRaises(PrivateCASBlocked):
                verify_ledger(case,anchor=ANCHOR,now=NOW)

    def test_contents_blob_path_sha_size_and_canonical_strict(self):
        good=response(new_ledger())
        parsed, sha=decode_github_contents(good)
        self.assertEqual(parsed,new_ledger())
        self.assertEqual(sha,good["sha"])
        for field,value in (
            ("type","symlink"),("name","source.mp4"),
            ("path","branch3/a8/public-ledger.json"),
            ("encoding","utf-8"),("size",99999),
            ("sha","a"*40),("content","invalid==="),
        ):
            case={**good,field:value}
            with self.subTest(field=field),self.assertRaises(PrivateCASBlocked):
                decode_github_contents(case)
        raw=json.dumps(new_ledger(),indent=2).encode()+b"\n"
        noncanonical={**good,"size":len(raw),"sha":git_blob_sha(raw),
                      "content":base64.b64encode(raw).decode()}
        with self.assertRaisesRegex(PrivateCASBlocked,"NONCANONICAL_JSON"):
            decode_github_contents(noncanonical)

    def test_stale_wrong_branch_and_nonvalid_put_denied(self):
        first=append(new_ledger())
        before=response(new_ledger())["sha"]
        body=build_github_put_contract(existing_blob_sha=before,updated=first)
        after=simulate_cas(current_remote_blob_sha=before,proposed_body=body)
        self.assertNotEqual(after,before)
        with self.assertRaisesRegex(PrivateCASBlocked,"STALE_WRITE"):
            simulate_cas(current_remote_blob_sha=after,proposed_body=body)
        for bad in ({**body,"branch":"other"},
                    {**body,"sha":"b"*40},
                    {**body,"token":"secret"}):
            with self.assertRaises(PrivateCASBlocked):
                simulate_cas(current_remote_blob_sha=before,proposed_body=bad)

    def test_policy_has_zero_real_trust_no_youtube(self):
        policy=json.loads(POLICY.read_text("utf-8"))
        validate_closed_policy(policy)
        for key,value in (
            ("creator_licenses_authenticated",1),
            ("real_owner_video_signatures_verified",1),
            ("actual_github_get_put_enabled",True),
            ("cross_runner_durable_ledger_verified",True),
            ("real_clivox_upload_oauth_configured",True),
            ("source_media_downloads_enabled",True),
            ("youtube_api_writes_enabled",True),
            ("private_vault_name_selected",True),
        ):
            tampered={**policy,key:value}
            with self.subTest(key=key),self.assertRaises(PrivateCASBlocked):
                validate_closed_policy(tampered)
        report=fixture_report()
        self.assertEqual(report["actual_github_put_calls"],0)
        self.assertEqual(report["actual_youtube_api_calls"],0)
        self.assertFalse(report["actual_private_cross_run_ledger_provisioned"])
        self.assertFalse(report["youtube_publish_authorized"])


if __name__=="__main__":
    unittest.main()
