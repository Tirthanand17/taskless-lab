"""Clivox A7: API fixtures, wrong-channel and privacy/least-scope rejection.

Tests never contact Google or use real Google credentials.
"""
from __future__ import annotations
import copy
import json
import unittest
from unittest.mock import patch

from scripts.branch3_a7_readonly_youtube import (
    CHANNEL_PATH,EXPECTED_CHANNEL,OLD_CHANNEL,READONLY_SCOPE,
    YOUTUBE_HOST,OAUTH_HOST,MAX_INVENTORY,ChannelBindingDenied,
    POLICY,FIXTURE_CHANNEL,FIXTURE_INVENTORY,
    validate_policy,validate_channels_mine,playlist_path,
    validate_inventory_sample,refresh_readonly_token,
    inspect_owner_channel,synthetic_fixture_report,
    _http_json,main,
)

class A7ReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads(POLICY.read_text("utf-8"))
        self.mine=json.loads(FIXTURE_CHANNEL.read_text("utf-8"))
        self.inventory=json.loads(FIXTURE_INVENTORY.read_text("utf-8"))
        self.token="TEST_BEARER_TOKEN_EXPLICITLY_SYNTHETIC_123456789"

    def test_synthetic_fixture_passes_without_claiming_oauth(self):
        r=synthetic_fixture_report()
        self.assertTrue(r["fixture_identity_check_passed"])
        self.assertEqual(r["actual_api_requests"],0)
        for flag in ("actual_clivox_oauth_verified",
                     "oauth_scope_really_verified",
                     "clivox_readonly_secrets_configured",
                     "real_private_inventory_inspected",
                     "upload_authorized","schedule_authorized","publish_authorized"):
            self.assertFalse(r[flag])
        self.assertEqual(r["fixture_inventory"]["inventory_first_page_count"],0)
        self.assertFalse(r["fixture_inventory"]["inventory_complete"])

    def test_live_oauth_is_disabled_even_if_fake_secrets_supplied(self):
        with patch("sys.argv",["a7","--mode","live"]),self.assertRaises(ChannelBindingDenied):
            main()
        self.assertFalse(self.policy["live_run_allowed"])
        self.assertFalse(self.policy["distinct_oauth_client_enrolled"])

    def test_no_wrong_channel_or_multiple_google_channels(self):
        for variant in ("old","different","none","multi","wrong_playlist"):
            mine=copy.deepcopy(self.mine)
            if variant=="old":
                mine["items"][0]["id"]=OLD_CHANNEL
            elif variant=="different":
                mine["items"][0]["id"]="UC"+"x"*22
            elif variant=="none":
                mine["items"]=[]
            elif variant=="multi":
                mine["items"].append(copy.deepcopy(mine["items"][0]))
            elif variant=="wrong_playlist":
                mine["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]="UU"+"x"*22
            with self.subTest(variant=variant),self.assertRaises(ChannelBindingDenied):
                validate_channels_mine(mine)

    def test_source_api_report_limited_to_read_only(self):
        calls=[]
        def fake_call(host,method,path,body,bearer):
            calls.append((host,method,path,body,bearer))
            if path==CHANNEL_PATH:
                return self.mine
            self.assertEqual(path,playlist_path("UU"+EXPECTED_CHANNEL[2:]))
            return self.inventory
        r=inspect_owner_channel(self.token,http_call=fake_call)
        self.assertTrue(r["identity_matches_clivox"])
        self.assertEqual(r["read_only_requests"],2)
        self.assertEqual(len(calls),2)
        self.assertEqual([z[1] for z in calls],["GET","GET"])
        self.assertTrue(all(z[0]==YOUTUBE_HOST and z[3] is None for z in calls))
        self.assertNotIn(self.token,json.dumps(r))
        self.assertFalse(r["inventory"]["video_ids_exported"])
        self.assertFalse(r["upload_authorized"])
        self.assertFalse(r["publish_authorized"])

    def test_on_wrong_channel_no_inventory_request(self):
        mine=copy.deepcopy(self.mine);mine["items"][0]["id"]=OLD_CHANNEL
        paths=[]
        def fake_call(host,method,path,body,bearer):
            paths.append(path)
            return mine
        with self.assertRaises(ChannelBindingDenied):
            inspect_owner_channel(self.token,http_call=fake_call)
        self.assertEqual(paths,[CHANNEL_PATH])

    def test_inventory_sample_is_not_a_complete_private_ledger(self):
        item={"kind":"youtube#playlistItem",
              "contentDetails":{"videoId":"ABCDEFGHIJK"}}
        self.inventory["items"]=[item]
        report=validate_inventory_sample(self.inventory)
        self.assertEqual(report["inventory_first_page_count"],1)
        self.assertFalse(report["private_and_scheduled_inventory_exhaustively_verified"])
        self.assertNotIn("ABCDEFGHIJK",json.dumps(report))
        self.inventory["items"]=[item,item]
        with self.assertRaises(ChannelBindingDenied):
            validate_inventory_sample(self.inventory)
        self.inventory["items"]=[{"contentDetails":{"videoId":"short"}}]
        with self.assertRaises(ChannelBindingDenied):
            validate_inventory_sample(self.inventory)
        self.inventory["items"]=[
            {"contentDetails":{"videoId":f"{i:011d}"}} for i in range(MAX_INVENTORY+1)
        ]
        with self.assertRaises(ChannelBindingDenied):
            validate_inventory_sample(self.inventory)

    def test_oauth_refresh_uses_only_expected_scope_and_fixed_endpoint(self):
        seen=[]
        def fake_call(host,method,path,body,bearer):
            seen.append((host,method,path,body,bearer))
            return {"token_type":"Bearer","access_token":self.token,
                    "scope":READONLY_SCOPE,"expires_in":3599}
        t=refresh_readonly_token(
            client_id="1234567890-abcdefghijklmnop.apps.googleusercontent.com",
            client_secret="SYNTHETIC_CLIENT_SECRET_12345",
            refresh_token="SYNTHETIC_REFRESH_TOKEN_123456789",
            http_call=fake_call)
        self.assertEqual(t,self.token)
        self.assertEqual(len(seen),1)
        host,method,path,body,bearer=seen[0]
        self.assertEqual((host,method,path,bearer),(OAUTH_HOST,"POST","/token",None))
        self.assertNotIn(b"TEST_BEARER_TOKEN",body)
        self.assertNotIn("secret",path)
        self.assertNotIn("refresh_token",path)

    def test_broad_oauth_scopes_and_missing_scope_are_rejected(self):
        for scope in (
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            READONLY_SCOPE+" https://www.googleapis.com/auth/youtube.upload",
            "",
            None,
        ):
            with self.subTest(scope=scope),self.assertRaises(ChannelBindingDenied):
                refresh_readonly_token(
                    client_id="1234567890-abcdefghijklmnop.apps.googleusercontent.com",
                    client_secret="SYNTHETIC_CLIENT_SECRET_12345",
                    refresh_token="SYNTHETIC_REFRESH_TOKEN_123456789",
                    http_call=lambda *args:{"token_type":"Bearer",
                        "access_token":self.token,"scope":scope})

    def test_fixed_http_transport_rejects_write_or_untrusted_url_before_network(self):
        for host,method,path,body,bearer in (
            (YOUTUBE_HOST,"POST",CHANNEL_PATH,b"x",self.token),
            (YOUTUBE_HOST,"DELETE","/youtube/v3/videos?id=123",None,self.token),
            ("evil.example","GET",CHANNEL_PATH,None,self.token),
            (YOUTUBE_HOST,"GET","/youtube/v3/videos?part=snippet",None,self.token),
            (YOUTUBE_HOST,"GET",CHANNEL_PATH+"&access_token=secret",None,self.token),
            (OAUTH_HOST,"GET","/token",None,None),
            (OAUTH_HOST,"POST","/token?client_secret=oops",b"x",None),
        ):
            with self.subTest(host=host,method=method,path=path),self.assertRaises(ChannelBindingDenied):
                _http_json(host,method,path,body,bearer)

    def test_policy_cannot_enable_upload_or_authorization_without_review(self):
        validate_policy(self.policy)
        for field in self.policy["blocked_flags"]:
            x=copy.deepcopy(self.policy)
            x["blocked_flags"][field]=True
            with self.subTest(field=field),self.assertRaises(ChannelBindingDenied):
                validate_policy(x)
        for field in ("live_run_allowed","distinct_oauth_client_enrolled",
                      "owner_google_consent_verified",
                      "oauth_refresh_secret_configured",
                      "private_clivox_identity_verified_via_oauth"):
            x=copy.deepcopy(self.policy);x[field]=True
            with self.subTest(field=field),self.assertRaises(ChannelBindingDenied):
                validate_policy(x)
        x=copy.deepcopy(self.policy);x["channel_id"]=OLD_CHANNEL
        with self.assertRaises(ChannelBindingDenied):
            validate_policy(x)

if __name__=="__main__":
    unittest.main()
