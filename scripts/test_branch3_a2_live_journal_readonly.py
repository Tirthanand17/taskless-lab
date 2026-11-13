"""Offline adversarial tests for owner-only GitHub journal read-only bridge."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from scripts.branch3_a2_live_journal_readonly import (
    APPROVAL_ENV, ANCHOR_SEQ_ENV, ANCHOR_SHA_ENV, KEY_ENV, TOKEN_ENV,
    VAULT_ENV, WORKFLOW_REF, APPROVED_VALUE, JournalBridgeDenied,
    expected_journal_paths, fixture_report, github_get,
    run_owner_readonly, validate_manual_context
)
from scripts.branch3_a2_private_ledger_cas import (
    initial_ledger, canonical_ledger, git_blob_sha, prepare_append, ReviewDenied
)
from scripts.branch3_a2_checkpointed_revocations import GENESIS_HEAD_SHA256
from scripts.test_branch3_a2_private_ledger_cas import event_for
from scripts.branch3_a3_private_vault_readback import VaultReadbackDenied
from scripts.test_branch3_a3_private_vault_readback import (
    repo_data, owner_collaborators
)
from scripts.branch3_a2_review_receipt import CLIVOX_ID

VAULT = "clivox-owner-media-vault"
TOKEN = "ghp_FAKE_ONLY_FOR_MOCK_TEST_NEVER_A_REAL_TOKEN_0987654321"
NOW = datetime(2026, 11, 13, 5, tzinfo=timezone.utc)


def public_raw(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def context(key: Ed25519PrivateKey) -> dict:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": "Tirthanand17/taskless-lab",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_WORKFLOW_REF": WORKFLOW_REF,
        "GITHUB_ACTOR": "Tirthanand17",
        "GITHUB_TRIGGERING_ACTOR": "Tirthanand17",
        "GITHUB_RUN_ATTEMPT": "1",
        VAULT_ENV: VAULT, TOKEN_ENV: TOKEN,
        APPROVAL_ENV: APPROVED_VALUE,
        KEY_ENV: public_raw(key).hex(),
        ANCHOR_SEQ_ENV: "0",
        ANCHOR_SHA_ENV: GENESIS_HEAD_SHA256,
    }


def contents(ledger: dict) -> dict:
    import base64
    raw = canonical_ledger(ledger)
    return {
        "name": "revocation-journal-v1.json",
        "path": "clivox-private/rights/revocation-journal-v1.json",
        "sha": git_blob_sha(raw),
        "size": len(raw),
        "type": "file",
        "encoding": "base64",
        "content": base64.b64encode(raw).decode("ascii"),
    }


def mock_http(calls: list, ledger=None, *, repo=None, collaborators=None,
              contents_override=None, repo_link="", users_link="",
              contents_link=""):
    paths = expected_journal_paths(VAULT)
    r = repo_data() if repo is None else repo
    users = owner_collaborators() if collaborators is None else collaborators
    obj = contents(initial_ledger() if ledger is None else ledger)
    if contents_override is not None:
        obj = contents_override
    def do_get(path, bearer):
        calls.append((path, bearer))
        if path == paths[0]:
            return copy.deepcopy(r), repo_link
        if path == paths[1]:
            return copy.deepcopy(users), users_link
        if path == paths[2]:
            return copy.deepcopy(obj), contents_link
        raise AssertionError("Disallowed GitHub path")
    return do_get


class LiveJournalReadOnlyTests(unittest.TestCase):

    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.env = context(self.key)

    def test_valid_mock_readonly_is_still_unlicensed(self):
        calls = []
        result = run_owner_readonly(self.env,http_get=mock_http(calls),now=NOW)
        self.assertEqual(result["channel_id"], CLIVOX_ID)
        self.assertEqual(result["actual_github_get_count"],3)
        self.assertEqual([r[0] for r in calls],
                         list(expected_journal_paths(VAULT)))
        self.assertTrue(all(r[1]==TOKEN for r in calls))
        for name in (
            "owner_pinned_key_independently_authenticated",
            "anchor_external_nonrollbackable_storage_proven",
            "remote_journal_completeness_proven",
            "private_vault_owner_usage_approved_by_this_check",
            "source_media_download_authorized",
            "youtube_upload_authorized",
            "youtube_schedule_authorized",
            "youtube_publish_authorized",
        ):
            self.assertFalse(result[name],name)
        self.assertEqual(result["actual_github_write_count"],0)
        self.assertEqual(result["genuine_creator_licenses_verified"],0)
        displayed = json.dumps(result)
        for secret in (VAULT,TOKEN,public_raw(self.key).hex(),"clivox-private",
                       "revocation-journal-v1.json"):
            self.assertNotIn(secret,displayed)

    def test_invalid_manual_owner_context_denies_before_api(self):
        variants = (
            ("GITHUB_ACTIONS", "false"),
            ("GITHUB_REPOSITORY", "someone/taskless-lab"),
            ("GITHUB_EVENT_NAME", "pull_request"),
            ("GITHUB_REF", "refs/heads/untrusted"),
            ("GITHUB_WORKFLOW_REF", "other/workflow"),
            ("GITHUB_ACTOR", "SomeoneElse"),
            ("GITHUB_TRIGGERING_ACTOR", "SomeoneElse"),
            ("GITHUB_RUN_ATTEMPT", "2"),
            (APPROVAL_ENV, "true"),
        )
        for key,value in variants:
            env=dict(self.env);env[key]=value
            calls=[]
            with self.subTest(key=key),self.assertRaises(
                    (JournalBridgeDenied,VaultReadbackDenied)):
                run_owner_readonly(env,http_get=mock_http(calls),now=NOW)
            self.assertEqual(calls,[])

    def test_all_secrets_required_and_bad_shape_denied_before_network(self):
        for key in (TOKEN_ENV, VAULT_ENV, APPROVAL_ENV,
                    KEY_ENV, ANCHOR_SEQ_ENV, ANCHOR_SHA_ENV):
            env=dict(self.env);env.pop(key)
            calls=[]
            with self.subTest(key=key),self.assertRaises(
                    (JournalBridgeDenied,VaultReadbackDenied)):
                run_owner_readonly(env,http_get=mock_http(calls),now=NOW)
            self.assertEqual(calls,[])
        for key,value in (
            (VAULT_ENV,"taskless-lab"),
            (VAULT_ENV,"clivox-bad/../secret"),
            (TOKEN_ENV,"bad-token"),
            (TOKEN_ENV,TOKEN+"\nEXFILTRATE"),
            (KEY_ENV,"0"*63),
            (KEY_ENV,"invalid"*11),
            (ANCHOR_SEQ_ENV,"-1"),
            (ANCHOR_SEQ_ENV,"001"),
            (ANCHOR_SEQ_ENV,"251"),
            (ANCHOR_SHA_ENV,"a"*40),
            (ANCHOR_SHA_ENV,"f"*64),
        ):
            env=dict(self.env);env[key]=value
            calls=[]
            with self.subTest(key=key,value=value),self.assertRaises(
                    (JournalBridgeDenied,VaultReadbackDenied)):
                run_owner_readonly(env,http_get=mock_http(calls),now=NOW)
            self.assertEqual(calls,[])

    def test_private_repo_identity_and_acl_precede_contents_read(self):
        cases=(
            ({"private":False},None),
            ({"visibility":"public"},None),
            ({"full_name":"Tirthanand17/taskless-lab"},None),
            ({"owner":{"login":"Other","type":"User"}},None),
            ({"archived":True},None),
        )
        for updates,_ in cases:
            repo=repo_data();repo.update(updates)
            calls=[]
            with self.subTest(updates=updates),self.assertRaises(
                    (JournalBridgeDenied,VaultReadbackDenied)):
                run_owner_readonly(self.env,
                    http_get=mock_http(calls,repo=repo),now=NOW)
            self.assertEqual(len(calls),1)
        calls=[]
        users=owner_collaborators()+[{"login":"Untrusted","role_name":"write",
                                     "permissions":{"admin":False}}]
        with self.assertRaises(VaultReadbackDenied):
            run_owner_readonly(self.env,
                http_get=mock_http(calls,collaborators=users),now=NOW)
        self.assertEqual(len(calls),2)

    def test_any_api_pagination_rejected_and_raw_private_data_not_logged(self):
        for kw,expected_calls in (
            ({"repo_link":'<x>; rel="next"'},1),
            ({"users_link":'<x>; rel="next"'},2),
            ({"contents_link":'<x>; rel="next"'},3),
        ):
            calls=[]
            with self.subTest(kw=kw),self.assertRaises(
                    (JournalBridgeDenied,VaultReadbackDenied)):
                run_owner_readonly(
                    self.env,http_get=mock_http(calls,**kw),now=NOW)
            self.assertEqual(len(calls),expected_calls)

    def test_signed_tombstones_and_new_external_floor_detect_rollback(self):
        key=self.key
        first=prepare_append(
            initial_ledger(),signed_event=event_for(key),revocation_public_key=public_raw(key),
            trusted_floor={"sequence":0,"head_sha256":GENESIS_HEAD_SHA256},now=NOW
        )
        calls=[]
        result=run_owner_readonly(
            self.env,http_get=mock_http(calls,ledger=first),now=NOW
        )
        self.assertFalse(result["youtube_upload_authorized"])
        stale=dict(self.env)
        stale[ANCHOR_SEQ_ENV]="1"
        stale[ANCHOR_SHA_ENV]=first["head_sha256"]
        with self.assertRaises(ReviewDenied):
            run_owner_readonly(
                stale,http_get=mock_http([],ledger=initial_ledger()),now=NOW
            )
        self.assertEqual(
            run_owner_readonly(
                stale,http_get=mock_http([],ledger=first),now=NOW
            )["actual_github_get_count"],3
        )

    def test_wrong_revocation_signer_denied(self):
        bad_signer=Ed25519PrivateKey.generate()
        first=prepare_append(
            initial_ledger(),signed_event=event_for(bad_signer),
            revocation_public_key=public_raw(bad_signer),
            trusted_floor={"sequence":0,"head_sha256":GENESIS_HEAD_SHA256},now=NOW
        )
        with self.assertRaises(ReviewDenied):
            run_owner_readonly(self.env,
                http_get=mock_http([],ledger=first),now=NOW)

    def test_changed_json_or_hash_denied(self):
        for key,value in (
            ("sha","0"*40),
            ("size",9999),
            ("encoding","other"),
            ("type","symlink"),
            ("path","public/creator-license.json"),
        ):
            wrong=contents(initial_ledger());wrong[key]=value
            with self.subTest(key=key),self.assertRaises(ReviewDenied):
                run_owner_readonly(self.env,
                    http_get=mock_http([],contents_override=wrong),now=NOW)

    def test_api_failure_denied_without_retry_or_write(self):
        calls=[]
        def blocked_get(path,token):
            calls.append((path,token))
            raise JournalBridgeDenied("NO_ACCESS")
        with self.assertRaises(JournalBridgeDenied):
            run_owner_readonly(self.env,http_get=blocked_get,now=NOW)
        self.assertEqual(len(calls),1)

    def test_fixture_no_actual_remote_or_media_access(self):
        f=fixture_report()
        self.assertEqual(f["actual_github_get_count"],0)
        self.assertEqual(f["actual_github_write_count"],0)
        self.assertFalse(f["live_private_journal_verified"])
        self.assertFalse(f["source_media_download_authorized"])
        self.assertFalse(f["youtube_publish_authorized"])


if __name__ == "__main__":
    unittest.main()
