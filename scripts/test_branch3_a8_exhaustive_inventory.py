"""Offline adversarial test suite for Clivox owner-only read-only YouTube inventory."""
from __future__ import annotations

import copy
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from scripts.branch3_a7_readonly_youtube import (
    CHANNEL_PATH, EXPECTED_CHANNEL, OLD_CHANNEL, READONLY_SCOPE,
    FIXTURE_CHANNEL, ChannelBindingDenied, YOUTUBE_HOST, OAUTH_HOST
)
from scripts.branch3_a8_exhaustive_inventory import (
    ENV_VALUE, ENABLE_ENV, WORKFLOW_REF,
    CLIENT_ENV, SECRET_ENV, REFRESH_ENV,
    MAX_PER_PAGE, MAX_PAGES, MAX_VIDEOS,
    allowlisted_http, fixture_report, inspect_uploaded_inventory,
    playlist_path, require_context, run_owner_inventory,
    validate_playlist_page, validate_video_batch, videos_path
)

VID1="A234567890a"
VID2="B234567890b"
VID3="C234567890c"
ACCESS="SYNTHETIC_READONLY_ACCESS_TOKEN_NEVER_LIVE_00123456"


def owner_env():
    return {
        "GITHUB_ACTIONS":"true",
        "GITHUB_REPOSITORY":"Tirthanand17/taskless-lab",
        "GITHUB_EVENT_NAME":"workflow_dispatch",
        "GITHUB_REF":"refs/heads/main",
        "GITHUB_WORKFLOW_REF":WORKFLOW_REF,
        "GITHUB_ACTOR":"Tirthanand17",
        "GITHUB_TRIGGERING_ACTOR":"Tirthanand17",
        "GITHUB_RUN_ATTEMPT":"1",
        ENABLE_ENV:ENV_VALUE,
        CLIENT_ENV:"1234567890123456789-abcdefghi.apps.googleusercontent.com",
        SECRET_ENV:"SYNTHETIC_OAUTH_CLIENT_SECRET_NEVER_REAL",
        REFRESH_ENV:"SYNTHETIC_REFRESH_TOKEN_NEVER_REAL"
    }


def playlist_page(ids, token=None):
    d={"kind":"youtube#playlistItemListResponse",
       "items":[{"contentDetails":{"videoId":v}} for v in ids]}
    if token is not None:
        d["nextPageToken"]=token
    return d


def batch(ids, statuses=None, wrong_channel=False):
    statuses={} if statuses is None else statuses
    return {"kind":"youtube#videoListResponse",
            "items":[
              {"id":v,"snippet":{"channelId":OLD_CHANNEL if wrong_channel
                         else EXPECTED_CHANNEL},
               "status": statuses.get(v,{"privacyStatus":"private"})}
              for v in ids
            ]}


def synthetic_api(calls, pages=None, statuses=None, wrong_channel=False,
                  scope=READONLY_SCOPE, video_override=None):
    pages=[playlist_page([VID1,VID2])] if pages is None else pages
    def invoke(host,method,path,body,bearer):
        calls.append((host,method,path,body,bearer))
        if host==OAUTH_HOST:
            assert method=="POST" and path=="/token"
            return {"token_type":"Bearer","access_token":ACCESS,"scope":scope}
        assert host==YOUTUBE_HOST and method=="GET" and bearer==ACCESS
        if path==CHANNEL_PATH:
            x=json.loads(FIXTURE_CHANNEL.read_text("utf-8"))
            if wrong_channel:
                x["items"][0]["id"]=OLD_CHANNEL
            return x
        u=urlsplit(path)
        q=parse_qs(u.query)
        if u.path.endswith("playlistItems"):
            token=q.get("pageToken",[""])[0]
            mapping={"":0,"PAGE_2":1,"PAGE_3":2}
            return copy.deepcopy(pages[mapping[token]])
        if u.path.endswith("/videos"):
            ids=q["id"][0].split(",")
            if video_override is not None:
                return copy.deepcopy(video_override)
            return batch(ids,statuses)
        raise AssertionError("unexpected path "+path)
    return invoke


class A8ReadOnlyInventoryTests(unittest.TestCase):

    def test_two_page_snapshot_and_status_batch_without_disclosing_private_ids(self):
        pages=[playlist_page([VID1,VID2],"PAGE_2"),
               playlist_page([VID3])]
        statuses={
            VID1:{"privacyStatus":"private"},
            VID2:{"privacyStatus":"unlisted"},
            VID3:{"privacyStatus":"private",
                  "publishAt":"2026-11-20T12:30:00Z"}
        }
        calls=[]
        result=run_owner_inventory(
            owner_env(),
            http_call=synthetic_api(calls,pages=pages,statuses=statuses)
        )
        self.assertTrue(result["owner_google_channel_identity_matched"])
        self.assertTrue(result["uploaded_playlist_pagination_exhausted_within_limit"])
        self.assertEqual(result["uploaded_playlist_pages_checked"],2)
        self.assertEqual(result["uploaded_playlist_videos_checked"],3)
        self.assertEqual(result["private_count"],2)
        self.assertEqual(result["unlisted_count"],1)
        self.assertEqual(result["private_with_schedule_count"],1)
        self.assertEqual(result["youtube_readonly_get_count"],4)
        self.assertEqual([x[1] for x in calls],["POST","GET","GET","GET","GET"])
        self.assertFalse(result["real_time_remote_completeness_guaranteed"])
        self.assertFalse(result["exact_uploaded_binary_sha256_verified"])
        for flag in ("ambiguous_ledger_attempt_automatically_reconciled",
                     "automatic_duplicate_retry_authorized",
                     "youtube_upload_authorized",
                     "youtube_schedule_authorized",
                     "youtube_publish_authorized"):
            self.assertFalse(result[flag],flag)
        out=json.dumps(result)
        for secret in (ACCESS,VID1,VID2,VID3,"SYNTHETIC_REFRESH_TOKEN_NEVER_REAL"):
            self.assertNotIn(secret,out)

    def test_empty_playlist_is_only_a_bounded_snapshot(self):
        calls=[]
        result=run_owner_inventory(
            owner_env(),http_call=synthetic_api(calls,pages=[playlist_page([])])
        )
        self.assertEqual(result["uploaded_playlist_videos_checked"],0)
        self.assertEqual(result["youtube_readonly_get_count"],2)
        self.assertFalse(result["real_time_remote_completeness_guaranteed"])
        self.assertFalse(result["automatic_duplicate_retry_authorized"])

    def test_wrong_brand_account_stops_before_private_inventory(self):
        calls=[]
        with self.assertRaises(ChannelBindingDenied):
            run_owner_inventory(
                owner_env(),
                http_call=synthetic_api(calls,wrong_channel=True)
            )
        self.assertEqual([c[1] for c in calls],["POST","GET"])

    def test_wrong_scope_stops_before_channel_lookup(self):
        for scope in (
            "https://www.googleapis.com/auth/youtube.upload",
            READONLY_SCOPE+" https://www.googleapis.com/auth/youtube.upload",
            "", "https://www.googleapis.com/auth/youtube"
        ):
            calls=[]
            with self.subTest(scope=scope),self.assertRaises(ChannelBindingDenied):
                run_owner_inventory(owner_env(),http_call=synthetic_api(
                    calls,scope=scope))
            self.assertEqual(len(calls),1)

    def test_invalid_owner_main_manual_context_prevents_auth(self):
        for key,value in (
            ("GITHUB_ACTIONS","false"),
            ("GITHUB_REPOSITORY","Other/repo"),
            ("GITHUB_EVENT_NAME","pull_request"),
            ("GITHUB_REF","refs/heads/feature"),
            ("GITHUB_WORKFLOW_REF","Other/workflow"),
            ("GITHUB_ACTOR","Other"),
            ("GITHUB_TRIGGERING_ACTOR","Other"),
            ("GITHUB_RUN_ATTEMPT","2"),
            (ENABLE_ENV,"not-approved")
        ):
            env=owner_env();env[key]=value
            calls=[]
            with self.subTest(key=key),self.assertRaises(ChannelBindingDenied):
                run_owner_inventory(env,http_call=synthetic_api(calls))
            self.assertEqual(calls,[])
        for k in (ENABLE_ENV,CLIENT_ENV,SECRET_ENV,REFRESH_ENV):
            env=owner_env();env.pop(k)
            with self.subTest(k=k),self.assertRaises(ChannelBindingDenied):
                require_context(env)

    def test_duplicate_ids_and_replayed_page_tokens_block(self):
        for pages in (
            [playlist_page([VID1,VID1])],
            [playlist_page([VID1],"PAGE_2"),playlist_page([VID1])],
            [playlist_page([VID1],"PAGE_2"),playlist_page([VID2],"PAGE_2")],
            [playlist_page([VID1],"unsafe/token")],
            [playlist_page(["INVALID_VIDEO_ID"])],
        ):
            calls=[]
            with self.subTest(pages=pages),self.assertRaises(ChannelBindingDenied):
                run_owner_inventory(owner_env(),
                                    http_call=synthetic_api(calls,pages=pages))

    def test_incomplete_video_batch_or_wrong_owner_or_privacy_denies(self):
        for override in (
            batch([VID1]),
            batch([VID1,VID1]),
            batch([VID1,VID2],wrong_channel=True),
            batch([VID1,VID2],statuses={VID1:{"privacyStatus":"UNKNOWN"}}),
            batch([VID1,VID2],statuses={VID2:{"privacyStatus":"public",
                                               "publishAt":"2026-11-20T12:30:00Z"}}),
            batch([VID1,VID2],statuses={VID2:{"privacyStatus":"private",
                                               "publishAt":"NOT_A_DATE"}}),
        ):
            with self.subTest(override=override),self.assertRaises(ChannelBindingDenied):
                run_owner_inventory(owner_env(),
                   http_call=synthetic_api([],video_override=override))

    def test_max_pages_never_approves_incomplete_inventory(self):
        # Page 20 still has nextPageToken. No false success after cap.
        def fetch(host,method,path,body,bearer):
            if host==OAUTH_HOST:
                return {"token_type":"Bearer","access_token":ACCESS,
                        "scope":READONLY_SCOPE}
            if path==CHANNEL_PATH:
                return json.loads(FIXTURE_CHANNEL.read_text("utf-8"))
            index=int(parse_qs(urlsplit(path).query).get("pageToken",["0"])[0])
            return playlist_page([],str(index+1))
        with self.assertRaises(ChannelBindingDenied):
            run_owner_inventory(owner_env(),http_call=fetch)

    def test_allowlisted_transport_rejects_mutation_and_other_hosts_before_network(self):
        for req in (
            (YOUTUBE_HOST,"POST","/youtube/v3/videos",None,ACCESS),
            (YOUTUBE_HOST,"DELETE",CHANNEL_PATH,None,ACCESS),
            (YOUTUBE_HOST,"GET","/youtube/v3/videos?part=snippet",None,ACCESS),
            (YOUTUBE_HOST,"GET","/youtube/v3/search?part=snippet",None,ACCESS),
            (YOUTUBE_HOST,"GET",playlist_path()+"&client_secret=secret",None,ACCESS),
            (YOUTUBE_HOST,"GET",playlist_path()+"#fragment",None,ACCESS),
            ("evil.example","GET",CHANNEL_PATH,None,ACCESS),
            (OAUTH_HOST,"POST","/wrong",b"somebody",None)
        ):
            with self.subTest(req=req),self.assertRaises(ChannelBindingDenied):
                allowlisted_http(*req)

    def test_video_ids_batch_limit_and_wrong_channel_digests_denied(self):
        for ids in ((),(VID1,VID1),("BAD",),tuple([VID1]*51)):
            with self.assertRaises(ChannelBindingDenied):
                videos_path(ids)
        for token in ("../escape","a&client_secret=oops",""):
            with self.assertRaises(ChannelBindingDenied):
                playlist_path(token)

    def test_fixture_does_not_claim_real_connection(self):
        out=fixture_report()
        self.assertFalse(out["real_owner_google_oauth_configured"])
        self.assertFalse(out["real_remote_inventory_readback_completed"])
        self.assertEqual(out["youtube_get_calls"],0)
        self.assertEqual(out["youtube_write_calls"],0)
        self.assertFalse(out["youtube_publish_authorized"])


if __name__=="__main__":
    unittest.main()
