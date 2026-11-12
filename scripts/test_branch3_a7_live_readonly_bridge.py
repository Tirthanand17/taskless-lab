"""Clivox A7 manual-only protected connection: synthetic mocks, no real calls."""
from __future__ import annotations

import copy
import json
import unittest

from scripts.branch3_a7_readonly_youtube import (
    CHANNEL_PATH,EXPECTED_CHANNEL,READONLY_SCOPE,
    YOUTUBE_HOST,OAUTH_HOST,FIXTURE_CHANNEL,FIXTURE_INVENTORY,
    ChannelBindingDenied,
)
from scripts.branch3_a7_live_readonly_bridge import (
    REPOSITORY,WORKFLOW_REF,CREDENTIALS,ENABLE_SECRET,
    validate_manual_context,run_live_owner_readonly
)

def environment():
    return {
        "GITHUB_ACTIONS":"true",
        "GITHUB_REPOSITORY":REPOSITORY,
        "GITHUB_EVENT_NAME":"workflow_dispatch",
        "GITHUB_REF":"refs/heads/main",
        "GITHUB_WORKFLOW_REF":WORKFLOW_REF,
        ENABLE_SECRET:"approved-readonly-clivox-v1",
        CREDENTIALS[0]:"1234567890123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com",
        CREDENTIALS[1]:"SYNTHETIC_CLIENT_SECRET_abcdefg",
        CREDENTIALS[2]:"SYNTHETIC_REFRESH_TOKEN_abcdefg",
    }

def fake_api(calls:list, *, wrong_channel:bool=False, scope:str=READONLY_SCOPE):
    mine=json.loads(FIXTURE_CHANNEL.read_text("utf-8"))
    playlist=json.loads(FIXTURE_INVENTORY.read_text("utf-8"))
    if wrong_channel:
        mine["items"][0]["id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
    def invoke(host,method,path,body,bearer):
        calls.append((host,method,path,body,bearer))
        if host==OAUTH_HOST:
            assert method=="POST" and path=="/token" and bearer is None
            return {"token_type":"Bearer","access_token":"SYNTHETIC_LONG_LIVED_ACCESS_TOKEN_ABCDE123456789",
                    "scope":scope}
        assert host==YOUTUBE_HOST and method=="GET" and bearer is not None
        if path==CHANNEL_PATH: return mine
        assert path.startswith("/youtube/v3/playlistItems?")
        return playlist
    return invoke

class LiveBridgeTests(unittest.TestCase):
    def test_valid_manual_fixture_is_still_nonpublishing(self):
        calls=[]
        result=run_live_owner_readonly(environment(),http_call=fake_api(calls))
        self.assertTrue(result["authenticated_clivox_identity_confirmed"])
        self.assertEqual(result["channel_id"],EXPECTED_CHANNEL)
        self.assertEqual(len(calls),3) # POST token; two YouTube GETs
        self.assertEqual([c[1] for c in calls],["POST","GET","GET"])
        self.assertFalse(result["youtube_upload_enabled"])
        self.assertFalse(result["youtube_schedule_enabled"])
        self.assertFalse(result["youtube_publish_enabled"])
        self.assertFalse(result["creator_clip_rights_approved"])
        self.assertFalse(result["inventory_complete"])
        self.assertNotIn("SYNTHETIC_LONG_LIVED_ACCESS_TOKEN",json.dumps(result))
        self.assertNotIn("SYNTHETIC_REFRESH_TOKEN",json.dumps(result))
        self.assertNotIn("SYNTHETIC_CLIENT_SECRET",json.dumps(result))

    def test_github_runtime_must_be_exact_owner_manual_main(self):
        variants={
            "GITHUB_ACTIONS":"false",
            "GITHUB_REPOSITORY":"SomeoneElse/repo",
            "GITHUB_EVENT_NAME":"pull_request",
            "GITHUB_REF":"refs/heads/untrusted",
            "GITHUB_WORKFLOW_REF":WORKFLOW_REF.replace("main","feature"),
            ENABLE_SECRET:"true"
        }
        for key,value in variants.items():
            env=environment();env[key]=value
            with self.subTest(key=key),self.assertRaises(ChannelBindingDenied):
                validate_manual_context(env)

    def test_no_secrets_or_wrong_env_enable_stops_before_api(self):
        for key in (*CREDENTIALS,ENABLE_SECRET):
            env=environment();env.pop(key)
            calls=[]
            with self.subTest(key=key),self.assertRaises(ChannelBindingDenied):
                run_live_owner_readonly(env,http_call=fake_api(calls))
            self.assertEqual(calls,[])

    def test_wrong_brand_account_hard_stops_before_inventory(self):
        calls=[]
        with self.assertRaises(ChannelBindingDenied):
            run_live_owner_readonly(environment(),
                http_call=fake_api(calls,wrong_channel=True))
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0][1],"POST")
        self.assertEqual(calls[1][2],CHANNEL_PATH)

    def test_wrong_or_broad_refresh_scope_stops_before_channel_request(self):
        for scope in (
            "https://www.googleapis.com/auth/youtube.upload",
            READONLY_SCOPE+" https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
            ""
        ):
            calls=[]
            with self.subTest(scope=scope),self.assertRaises(ChannelBindingDenied):
                run_live_owner_readonly(environment(),
                    http_call=fake_api(calls,scope=scope))
            self.assertEqual(len(calls),1)

    def test_no_other_credentials_fallback_and_no_alternate_workflow(self):
        env=environment()
        env["FLOWMINUTE_REFRESH_TOKEN"]="DO_NOT_USE_OLD_TOKEN"
        env[CREDENTIALS[2]]=""
        with self.assertRaises(ChannelBindingDenied):
            validate_manual_context(env)
        env=environment()
        env["GITHUB_WORKFLOW_REF"]="other/repository/.github/workflows/anything.yml@refs/heads/main"
        with self.assertRaises(ChannelBindingDenied):
            validate_manual_context(env)

if __name__=="__main__":
    unittest.main()
