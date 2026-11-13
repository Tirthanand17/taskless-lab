"""A8 private upload-control journal live-bridge adversarial offline tests."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import unittest

from scripts.branch3_a8_live_attempt_readonly import (
    APPROVAL_ENV, APPROVED_VALUE, ANCHOR_SEQ_ENV, ANCHOR_SHA_ENV,
    TOKEN_ENV, VAULT_ENV, WORKFLOW_REF, AttemptBridgeDenied,
    expected_attempt_paths, github_get, run_owner_readonly,
    validate_manual_context, fixture_report
)
from scripts.branch3_a8_private_cas_ledger import (
    GENESIS, PrivateCASBlocked, new_ledger, append_simulated_event,
    decode_github_contents,
)
from scripts.test_branch3_a8_private_cas_ledger import (
    response, D, AT
)
from scripts.branch3_a3_private_vault_readback import VaultReadbackDenied
from scripts.test_branch3_a3_private_vault_readback import (
    repo_data, owner_collaborators
)

NOW = datetime(2026,11,13,17,tzinfo=timezone.utc)
VAULT = "clivox-owner-media-vault"
TOKEN = "github_fake_private_contents_read_only_TOKEN_NEVER_REAL"
ANCHOR = {"sequence":0,"head_sha256":GENESIS}


def context():
    return {
        "GITHUB_ACTIONS":"true",
        "GITHUB_REPOSITORY":"Tirthanand17/taskless-lab",
        "GITHUB_REF":"refs/heads/main",
        "GITHUB_EVENT_NAME":"workflow_dispatch",
        "GITHUB_WORKFLOW_REF":WORKFLOW_REF,
        "GITHUB_ACTOR":"Tirthanand17",
        "GITHUB_TRIGGERING_ACTOR":"Tirthanand17",
        "GITHUB_RUN_ATTEMPT":"1",
        VAULT_ENV:VAULT, TOKEN_ENV:TOKEN,
        APPROVAL_ENV:APPROVED_VALUE,
        ANCHOR_SEQ_ENV:"0",ANCHOR_SHA_ENV:GENESIS,
    }


def fake_get(calls, *, ledger=None, repo=None, users=None, file=None,
             repo_link="", users_link="", file_link=""):
    expected=expected_attempt_paths(VAULT)
    metadata=repo_data() if repo is None else repo
    collaborators=owner_collaborators() if users is None else users
    contents=response(new_ledger() if ledger is None else ledger)
    if file is not None:
        contents=file
    def get(path,bearer):
        calls.append((path,bearer))
        if path==expected[0]:
            return copy.deepcopy(metadata),repo_link
        if path==expected[1]:
            return copy.deepcopy(collaborators),users_link
        if path==expected[2]:
            return copy.deepcopy(contents),file_link
        raise AssertionError("unexpected API path")
    return get


class A8OwnerLiveAttemptTests(unittest.TestCase):

    def test_valid_owner_only_private_empty_genesis_is_still_no_release(self):
        calls=[]
        out=run_owner_readonly(context(),http_get=fake_get(calls),now=NOW)
        self.assertEqual(out["observed_event_count"],0)
        self.assertEqual(out["observed_attempt_count"],0)
        self.assertEqual(out["actual_github_get_count"],3)
        self.assertEqual(out["actual_github_put_count"],0)
        self.assertEqual(out["actual_youtube_api_calls"],0)
        self.assertEqual([p for p,_ in calls],list(expected_attempt_paths(VAULT)))
        self.assertTrue(all(t==TOKEN for _,t in calls))
        self.assertTrue(out["exact_global_attempt_chain_replayed"])
        for k in (
            "independent_external_anchor_durability_verified",
            "remote_atomic_cas_writer_deployed",
            "github_repo_app_installations_or_backups_audited",
            "readback_is_transactional_or_latest_snapshot",
            "legitimate_owner_media_release_verified",
            "can_clear_ambiguous_upload_attempts",
            "automatic_retry_allowed",
            "can_approve_private_media_storage",
            "source_media_download_authorized",
            "youtube_upload_authorized","youtube_schedule_authorized",
            "youtube_publish_authorized",
        ):
            self.assertFalse(out[k],k)
        text_value=json.dumps(out)
        for secret in (VAULT,TOKEN,GENESIS,"clivox-private",
                       "attempt-ledger-v1.json",D["media_sha256"]):
            self.assertNotIn(secret,text_value)

    def test_present_real_reservation_never_authorizes_duplicate_upload(self):
        ledger=append_simulated_event(
            new_ledger(),kind="RESERVE_SYNTHETIC",at_utc=AT,
            anchor=ANCHOR,now=NOW,**D
        )
        got=run_owner_readonly(
            context(),http_get=fake_get([],ledger=ledger),now=NOW
        )
        self.assertEqual(got["observed_attempt_count"],1)
        self.assertEqual(got["observed_event_count"],1)
        self.assertFalse(got["automatic_retry_allowed"])
        self.assertFalse(got["youtube_upload_authorized"])

    def test_explicit_pinned_prior_anchor_detects_rollback(self):
        ledger=append_simulated_event(
            new_ledger(),kind="RESERVE_SYNTHETIC",at_utc=AT,
            anchor=ANCHOR,now=NOW,**D
        )
        context_pinned=context()
        context_pinned[ANCHOR_SEQ_ENV]="1"
        context_pinned[ANCHOR_SHA_ENV]=ledger["head_sha256"]
        with self.assertRaises(PrivateCASBlocked):
            run_owner_readonly(
                context_pinned,http_get=fake_get([],ledger=new_ledger()),now=NOW
            )
        good=run_owner_readonly(
            context_pinned,http_get=fake_get([],ledger=ledger),now=NOW
        )
        self.assertFalse(good["youtube_publish_authorized"])

    def test_manual_owner_main_and_approval_required_before_any_get(self):
        for key,value in (
            ("GITHUB_ACTIONS","false"),
            ("GITHUB_REPOSITORY","Other/repo"),
            ("GITHUB_EVENT_NAME","pull_request"),
            ("GITHUB_REF","refs/heads/feature"),
            ("GITHUB_WORKFLOW_REF","Other/workflow"),
            ("GITHUB_ACTOR","Other"),
            ("GITHUB_TRIGGERING_ACTOR","Other"),
            ("GITHUB_RUN_ATTEMPT","2"),
            (APPROVAL_ENV,"true"),
        ):
            env=context();env[key]=value
            calls=[]
            with self.subTest(key=key),self.assertRaises(AttemptBridgeDenied):
                run_owner_readonly(env,http_get=fake_get(calls),now=NOW)
            self.assertEqual(calls,[])

    def test_missing_secrets_and_untrusted_anchor_reject_before_get(self):
        for key in (
            VAULT_ENV,TOKEN_ENV,APPROVAL_ENV,
            ANCHOR_SEQ_ENV,ANCHOR_SHA_ENV
        ):
            env=context();env.pop(key)
            calls=[]
            with self.subTest(key=key),self.assertRaises(
                (AttemptBridgeDenied,VaultReadbackDenied)
            ):
                run_owner_readonly(env,http_get=fake_get(calls),now=NOW)
            self.assertEqual(calls,[])
        for key,value in (
            (VAULT_ENV,"taskless-lab"),
            (VAULT_ENV,"clivox-../other"),
            (TOKEN_ENV,"bad"),
            (TOKEN_ENV,TOKEN+"\nSUSPICIOUS"),
            (ANCHOR_SEQ_ENV,"000"),
            (ANCHOR_SEQ_ENV,"251"),
            (ANCHOR_SEQ_ENV,"-1"),
            (ANCHOR_SHA_ENV,"a"*40),
            (ANCHOR_SHA_ENV,"f"*64),
        ):
            env=context();env[key]=value
            calls=[]
            with self.subTest(key=key),self.assertRaises(
                (AttemptBridgeDenied,VaultReadbackDenied)
            ):
                run_owner_readonly(env,http_get=fake_get(calls),now=NOW)
            self.assertEqual(calls,[])

    def test_no_public_or_wrong_repo_and_bad_acl(self):
        for bad in (
            {"private":False},{"visibility":"public"},
            {"full_name":"Tirthanand17/taskless-lab"},
            {"owner":{"login":"other","type":"User"}},
            {"archived":True},{"fork":True},
        ):
            repo=repo_data();repo.update(bad);calls=[]
            with self.subTest(bad=bad),self.assertRaises(VaultReadbackDenied):
                run_owner_readonly(
                    context(),http_get=fake_get(calls,repo=repo),now=NOW
                )
            self.assertEqual(len(calls),1)
        users=owner_collaborators()+[
            {"login":"outsider","role_name":"write",
             "permissions":{"admin":False}}
        ]
        calls=[]
        with self.assertRaises(VaultReadbackDenied):
            run_owner_readonly(
                context(),http_get=fake_get(calls,users=users),now=NOW
            )
        self.assertEqual(len(calls),2)

    def test_any_pagination_or_extra_link_fails_closed(self):
        for key,count in (
            ("repo_link",1),("users_link",2),("file_link",3)
        ):
            calls=[]
            with self.subTest(key=key),self.assertRaises(
                (AttemptBridgeDenied,VaultReadbackDenied)
            ):
                run_owner_readonly(
                    context(),http_get=fake_get(
                        calls,**{key:'<fake>; rel="next"'}
                    ),now=NOW
                )
            self.assertEqual(len(calls),count)

    def test_forged_blob_size_path_json_and_sha_rejected(self):
        current=response(new_ledger())
        for field,value in (
            ("path","public/upload.json"),
            ("type","symlink"),
            ("size",99999),
            ("sha","a"*40),
            ("encoding","raw"),
            ("content","@@NOT_BASE64@@"),
        ):
            bad={**current,field:value}
            calls=[]
            with self.subTest(field=field),self.assertRaises(
                PrivateCASBlocked
            ):
                run_owner_readonly(
                    context(),http_get=fake_get(calls,file=bad),now=NOW
                )
            self.assertEqual(len(calls),3)

    def test_changed_channel_tampered_chain_and_replayed_events_fail(self):
        ledger=append_simulated_event(
            new_ledger(),kind="RESERVE_SYNTHETIC",at_utc=AT,
            anchor=ANCHOR,now=NOW,**D
        )
        variants=[]
        tampered=copy.deepcopy(ledger)
        tampered["events"][0]["event_sha256"]="f"*64
        variants.append(tampered)
        tampered=copy.deepcopy(ledger)
        tampered["channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
        variants.append(tampered)
        tampered=copy.deepcopy(ledger)
        tampered["events"].append(copy.deepcopy(tampered["events"][0]))
        variants.append(tampered)
        for candidate in variants:
            file=response(candidate)
            with self.assertRaises(PrivateCASBlocked):
                run_owner_readonly(
                    context(),http_get=fake_get([],file=file),now=NOW
                )

    def test_no_transport_to_other_hosts_private_media_or_put(self):
        for path in (
            "/repos/Tirthanand17/taskless-lab",
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/other.mp4",
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/clivox-private/rights/revocation-journal-v1.json?ref=main",
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/clivox-private/upload-control/attempt-ledger-v1.json?ref=feature",
            "/repos/Tirthanand17/clivox-owner-media-vault?x=https://evil.example",
            "/repos/Tirthanand17/clivox-owner-media-vault/../secrets",
        ):
            with self.subTest(path=path),self.assertRaises(AttemptBridgeDenied):
                github_get(path,TOKEN)
        with self.assertRaises(AttemptBridgeDenied):
            github_get(expected_attempt_paths(VAULT)[0],"bad-token")

    def test_fixture_remains_zero_credentials_or_google_requests(self):
        r=fixture_report()
        self.assertFalse(r["real_authenticated_private_attempt_ledger_readback"])
        self.assertFalse(r["automatic_retry_allowed"])
        self.assertFalse(r["youtube_upload_authorized"])
        self.assertEqual(r["actual_github_get_count"],0)
        self.assertEqual(r["actual_github_put_count"],0)
        self.assertEqual(r["actual_youtube_api_calls"],0)


if __name__=="__main__":
    unittest.main()
