"""A8 private GitHub real-CAS sandbox adapter tests: zero live APIs or video."""
from __future__ import annotations

import base64
import copy
import json
import unittest

from scripts.branch3_a3_private_vault_readback import VaultReadbackDenied
from scripts.test_branch3_a3_private_vault_readback import (
    repo_data, owner_collaborators,
)
from scripts.branch3_a2_private_ledger_cas import git_blob_sha
from scripts.branch3_a8_cas_sandbox_writer import (
    APPROVAL, APPROVAL_ENV, BRANCH, CLIVOX, FIELDS, FILE_PATH, NAME_ENV,
    SERIAL_ENV, SHA_ENV, SUBJECT, TOKEN_ENV, WORKFLOW_REF,
    SandboxCASConflict, SandboxWriteBlocked, canonical_bytes, decode_probe,
    fixed_paths, fixture_report, http_get, http_put, propose_update,
    run_owner_sandbox, validate_manual_context, validate_probe, validate_put,
)

VAULT="clivox-owner-media-vault"
TOKEN="FINE_GRAINED_SANDBOX_FAKE_TOKEN_NEVER_REAL_123456789"
INITIAL={
    "schema_version":1,"channel_id":CLIVOX,"test_only":True,
    "production_ledger":False,"youtube_upload_authorized":False,
    "write_serial":1,"writer":"sandbox-probe-first",
    "subject":SUBJECT
}


def contents(data:dict)->dict:
    raw=canonical_bytes(data)
    return {
        "type":"file","name":"cas-probe-v1.json","path":FILE_PATH,
        "encoding":"base64","size":len(raw),"sha":git_blob_sha(raw),
        "content":base64.b64encode(raw).decode("ascii")
    }


def env():
    return {
        "GITHUB_ACTIONS":"true",
        "GITHUB_REPOSITORY":"Tirthanand17/taskless-lab",
        "GITHUB_REF":"refs/heads/main",
        "GITHUB_EVENT_NAME":"workflow_dispatch",
        "GITHUB_WORKFLOW_REF":WORKFLOW_REF,
        "GITHUB_ACTOR":"Tirthanand17",
        "GITHUB_TRIGGERING_ACTOR":"Tirthanand17",
        "GITHUB_RUN_ATTEMPT":"1",
        NAME_ENV:VAULT,TOKEN_ENV:TOKEN,APPROVAL_ENV:APPROVAL,
        SERIAL_ENV:"1",SHA_ENV:contents(INITIAL)["sha"]
    }


class MockGitHub:
    def __init__(self,*,scenario="good",initial=None,
                 repo=None,collaborators=None):
        self.scenario=scenario
        self.remote=contents(INITIAL if initial is None else initial)
        self.repo=repo_data() if repo is None else repo
        self.users=owner_collaborators() if collaborators is None else collaborators
        self.gets=[]
        self.puts=[]

    def get(self,path,token):
        self.gets.append((path,token))
        paths=fixed_paths(VAULT)
        if path==paths[0]:
            return copy.deepcopy(self.repo),""
        if path==paths[1]:
            return copy.deepcopy(self.users),""
        if path==paths[2]:
            return copy.deepcopy(self.remote),""
        raise AssertionError("Unexpected mock GET")

    def put(self,path,token,body,*,vault_name):
        self.puts.append((path,token,body,vault_name))
        validate_put(vault_name,path,body)
        if self.scenario=="conflict":
            raise SandboxCASConflict("CLIVOX_A8_SANDBOX_DENIED_STALE_SHA_HTTP_409_NO_RETRY")
        if self.scenario=="timeout":
            raise SandboxWriteBlocked(
                "CLIVOX_A8_SANDBOX_DENIED_UNKNOWN_PUT_OUTCOME_NO_RETRY"
            )
        if body["sha"]!=self.remote["sha"]:
            raise SandboxCASConflict("CLIVOX_A8_SANDBOX_DENIED_STALE_SHA_HTTP_409_NO_RETRY")
        new=json.loads(base64.b64decode(body["content"]))
        self.remote=contents(new)
        if self.scenario=="bad_confirmation":
            return {"content":{"sha":"f"*40,"path":FILE_PATH},
                    "commit":{"sha":"b"*40}}
        if self.scenario=="bad_readback":
            self.remote=contents(INITIAL)
        return {
            "content":{"sha":git_blob_sha(canonical_bytes(new)),
                       "path":FILE_PATH},
            "commit":{"sha":"b"*40}
        }


class A8CASVerifiedSandboxTests(unittest.TestCase):

    def test_realistic_sandbox_get_put_readback_passes_but_never_releases(self):
        server=MockGitHub()
        result=run_owner_sandbox(env(),get=server.get,put=server.put)
        self.assertEqual(result["new_sandbox_serial"],2)
        self.assertTrue(result["sandbox_branch_not_main"])
        self.assertTrue(result["only_test_probe_changed"])
        self.assertEqual(result["actual_github_get_count"],4)
        self.assertEqual(result["actual_github_put_attempts"],1)
        self.assertEqual(len(server.puts),1)
        self.assertEqual(len(server.gets),4)
        proposed=decode_probe(server.remote)[0]
        self.assertEqual(proposed["write_serial"],2)
        self.assertFalse(proposed["production_ledger"])
        self.assertFalse(proposed["youtube_upload_authorized"])
        self.assertEqual(server.puts[0][2]["branch"],BRANCH)
        self.assertEqual(server.puts[0][2]["sha"],
                         contents(INITIAL)["sha"])
        self.assertFalse(result["real_production_attempt_ledger_changed"])
        self.assertFalse(result["real_cross_runner_linearizability_proven"])
        self.assertFalse(result["youtube_upload_authorized"])
        self.assertFalse(result["youtube_schedule_authorized"])
        self.assertFalse(result["youtube_publish_authorized"])
        self.assertEqual(result["actual_youtube_api_calls"],0)
        out=json.dumps(result)
        for value in (VAULT,TOKEN,FILE_PATH,
                      "clivox-private","github.com",SUBJECT):
            self.assertNotIn(value,out)

    def test_realistic_409_conflict_never_retries(self):
        server=MockGitHub(scenario="conflict")
        res=run_owner_sandbox(env(),get=server.get,put=server.put)
        self.assertTrue(res["conflict_observed"])
        self.assertTrue(res["owner_manual_readback_required"])
        self.assertFalse(res["automatic_retry_allowed"])
        self.assertEqual(res["actual_github_put_attempts"],1)
        self.assertEqual(len(server.gets),3)
        self.assertEqual(len(server.puts),1)
        self.assertFalse(res["youtube_publish_authorized"])

    def test_unknown_put_response_aborts_without_second_put(self):
        server=MockGitHub(scenario="timeout")
        with self.assertRaisesRegex(SandboxWriteBlocked,"UNKNOWN_PUT_OUTCOME"):
            run_owner_sandbox(env(),get=server.get,put=server.put)
        self.assertEqual(len(server.puts),1)
        self.assertEqual(len(server.gets),3)

    def test_accepted_body_but_untrusted_response_halts(self):
        server=MockGitHub(scenario="bad_confirmation")
        with self.assertRaisesRegex(SandboxWriteBlocked,"PUT_COMMIT_CONFIRMATION"):
            run_owner_sandbox(env(),get=server.get,put=server.put)
        self.assertEqual(len(server.puts),1)
        self.assertEqual(len(server.gets),3)

    def test_changed_remote_readback_refuses_claim_of_success(self):
        server=MockGitHub(scenario="bad_readback")
        with self.assertRaisesRegex(SandboxWriteBlocked,"POSTPUT_READBACK"):
            run_owner_sandbox(env(),get=server.get,put=server.put)
        self.assertEqual(len(server.puts),1)
        self.assertEqual(len(server.gets),4)

    def test_owner_floor_mismatch_denies_before_put(self):
        for key,value in (
            (SERIAL_ENV,"2"),(SHA_ENV,"f"*40),(SERIAL_ENV,"1000")
        ):
            e=env();e[key]=value
            server=MockGitHub()
            with self.subTest(key=key,value=value),self.assertRaises(
                SandboxWriteBlocked
            ):
                run_owner_sandbox(e,get=server.get,put=server.put)
            self.assertEqual(len(server.puts),0)
        server=MockGitHub()
        e=env();e[SERIAL_ENV]="001"
        with self.assertRaises(SandboxWriteBlocked):
            run_owner_sandbox(e,get=server.get,put=server.put)
        self.assertEqual(len(server.gets),0)

    def test_owner_exact_context_and_all_secrets_before_network(self):
        for key,bad in (
            ("GITHUB_ACTIONS","false"),
            ("GITHUB_REPOSITORY","Tirthanand17/flowminute-control-private"),
            ("GITHUB_REF","refs/heads/sandbox"),
            ("GITHUB_EVENT_NAME","pull_request"),
            ("GITHUB_WORKFLOW_REF","bad/workflow"),
            ("GITHUB_ACTOR","attacker"),
            ("GITHUB_TRIGGERING_ACTOR","attacker"),
            ("GITHUB_RUN_ATTEMPT","2"),
            (APPROVAL_ENV,"approved")
        ):
            e=env();e[key]=bad
            with self.subTest(key=key),self.assertRaises(SandboxWriteBlocked):
                validate_manual_context(e)
        for key in (NAME_ENV,TOKEN_ENV,APPROVAL_ENV,SERIAL_ENV,SHA_ENV):
            e=env();e.pop(key)
            with self.subTest(key=key),self.assertRaises(
                (SandboxWriteBlocked,VaultReadbackDenied)
            ):
                validate_manual_context(e)
        for key,bad in (
            (NAME_ENV,"taskless-lab"),(NAME_ENV,"clivox-../secrets"),
            (TOKEN_ENV,"abc"),(TOKEN_ENV,TOKEN+"\nLEAK"),
            (SERIAL_ENV,"0"),(SERIAL_ENV,"-1"),
            (SHA_ENV,"a"*64)
        ):
            e=env();e[key]=bad
            with self.subTest(key=key),self.assertRaises(
                (SandboxWriteBlocked,VaultReadbackDenied)
            ):
                validate_manual_context(e)

    def test_repo_acl_must_remain_private_owner_only(self):
        for wrong in (
            {"private":False},{"visibility":"public"},
            {"full_name":"Tirthanand17/taskless-lab"},
            {"owner":{"login":"someone","type":"User"}},
            {"archived":True},
        ):
            r=repo_data();r.update(wrong);mock=MockGitHub(repo=r)
            with self.subTest(wrong=wrong),self.assertRaises(VaultReadbackDenied):
                run_owner_sandbox(env(),get=mock.get,put=mock.put)
            self.assertEqual(len(mock.puts),0)
        users=owner_collaborators()+[
            {"login":"other","role_name":"write","permissions":{"admin":False}}
        ]
        mock=MockGitHub(collaborators=users)
        with self.assertRaises(VaultReadbackDenied):
            run_owner_sandbox(env(),get=mock.get,put=mock.put)
        self.assertEqual(len(mock.puts),0)

    def test_unapproved_sandbox_shapes_fail(self):
        for field,value in (
            ("schema_version",True),
            ("channel_id","UCxxx"),
            ("test_only",False),
            ("production_ledger",True),
            ("youtube_upload_authorized",True),
            ("write_serial",0),("write_serial",True),
            ("write_serial",1001),
            ("writer","real-uploader"),
            ("subject","third-party-video")
        ):
            trial={**INITIAL,field:value}
            with self.subTest(field=field),self.assertRaises(SandboxWriteBlocked):
                validate_probe(trial)
        with self.assertRaises(SandboxWriteBlocked):
            validate_probe({**INITIAL,"access_token":"secret"})

    def test_content_integrity_exact_path_sha_and_canonical_json(self):
        good=contents(INITIAL)
        d,sha=decode_probe(good)
        self.assertEqual(d,INITIAL)
        self.assertEqual(sha,good["sha"])
        for field,value in (
            ("path","clivox-private/upload-control/attempt-ledger-v1.json"),
            ("type","symlink"),("name","source.mp4"),
            ("size",99999),("sha","0"*40),
            ("encoding","utf-8"),("content","invalid%%%")
        ):
            item={**good,field:value}
            with self.subTest(field=field),self.assertRaises(SandboxWriteBlocked):
                decode_probe(item)
        raw=json.dumps(INITIAL,indent=2).encode()+b"\n"
        wrong={**good,"size":len(raw),"sha":git_blob_sha(raw),
               "content":base64.b64encode(raw).decode()}
        with self.assertRaisesRegex(SandboxWriteBlocked,"NOT_CANONICAL"):
            decode_probe(wrong)

    def test_invalid_post_body_or_production_path_rejected_before_http(self):
        fresh,body=propose_update(INITIAL,contents(INITIAL)["sha"])
        self.assertEqual(fresh["write_serial"],2)
        approved=fixed_paths(VAULT)[2].split("?ref=")[0]
        validate_put(VAULT,approved,body)
        for path in (
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/clivox-private/upload-control/attempt-ledger-v1.json",
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/LICENSE.md",
        ):
            with self.subTest(path=path),self.assertRaises(SandboxWriteBlocked):
                validate_put(VAULT,path,body)
        for invalid in (
            {**body,"branch":"main"},
            {**body,"sha":"a"*64},
            {**body,"access_token":TOKEN},
            {**body,"message":"upload to YouTube"},
            {**body,"content":"invalid%%%"},
        ):
            with self.subTest(invalid=invalid),self.assertRaises(SandboxWriteBlocked):
                validate_put(VAULT,approved,invalid)

    def test_no_real_network_on_unapproved_transport_paths(self):
        for path in (
            "/repos/Tirthanand17/taskless-lab",
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/clivox-private/upload-control/attempt-ledger-v1.json?ref=main",
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/clivox-private/sandbox/cas-probe-v1.json?ref=main",
            "/repos/Tirthanand17/clivox-owner-media-vault/contents/private-video.mp4",
            "/repos/Tirthanand17/clivox-owner-media-vault/../outside",
        ):
            with self.subTest(path=path),self.assertRaises(SandboxWriteBlocked):
                http_get(path,TOKEN)

    def test_fixture_is_not_github_or_youtube_production_writer(self):
        d=fixture_report()
        self.assertFalse(d["actual_live_sandbox_job_executed"])
        self.assertFalse(d["production_ledger_put_implemented"])
        self.assertFalse(d["production_cross_runner_global_reservation_proven"])
        self.assertEqual(d["actual_github_get_count"],0)
        self.assertEqual(d["actual_github_put_count"],0)
        self.assertEqual(d["actual_youtube_api_calls"],0)
        self.assertFalse(d["youtube_upload_authorized"])
        self.assertFalse(d["youtube_publish_authorized"])


if __name__=="__main__":
    unittest.main()
