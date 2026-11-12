"""Clivox A7: strict read-only YouTube OAuth identity and small inventory preview.

Current production state: NO Clivox-specific OAuth consent or secrets configured.
A passing fixture is NOT a live identity check. This module never calls any
YouTube mutation endpoint, and never prints credentials or private video IDs.
GitHub PR QA runs fixtures only; real mode requires a separately enabled,
human-reviewed Clivox OAuth setup and a different (future) protected workflow.

Official: https://developers.google.com/youtube/data/guides/authentication
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
from pathlib import Path
import re
import ssl
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"branch3/a7/readonly-oauth-policy.json"
FIXTURE_CHANNEL=ROOT/"branch3/a7/fixtures/clivox-channels-mine-synthetic.json"
FIXTURE_INVENTORY=ROOT/"branch3/a7/fixtures/clivox-uploads-page-synthetic.json"
EXPECTED_CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"
OLD_CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
READONLY_SCOPE="https://www.googleapis.com/auth/youtube.readonly"
YOUTUBE_HOST="www.googleapis.com"
OAUTH_HOST="oauth2.googleapis.com"
CHANNEL_PATH="/youtube/v3/channels?"+urlencode({
    "part":"id,snippet,contentDetails","mine":"true"
})
VIDEO_ID=re.compile(r"[A-Za-z0-9_-]{11}\Z")
CHANNEL_ID=re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
MAX_JSON=512_000
MAX_INVENTORY=10

class ChannelBindingDenied(ValueError):
    """Clivox OAuth identity or rights boundary failed; never fall back."""

def require(ok:bool,code:str)->None:
    if not ok:
        raise ChannelBindingDenied("CLIVOX_A7_DENY_"+code)

def load_json(path:Path)->dict:
    require(path.is_file() and not path.is_symlink() and
            path.stat().st_size<=MAX_JSON,"INPUT_FILE")
    value=json.loads(path.read_text(encoding="utf-8"))
    require(type(value) is dict,"INPUT_JSON_OBJECT")
    return value

def validate_policy(policy:dict)->None:
    require(type(policy) is dict and set(policy)=={
        "schema_version","channel_id","channel_handle","stage",
        "workflow_state","required_scope","distinct_oauth_client_enrolled",
        "owner_google_consent_verified","oauth_refresh_secret_configured",
        "private_clivox_identity_verified_via_oauth","identity_client_implemented",
        "private_uploads_inventory_reader_implemented","live_run_allowed",
        "oauth_secret_source","token_handling","allowed_request_methods",
        "allowed_youtube_api_paths","fixed_google_hosts","initial_inventory_limit",
        "inventory_completeness","active_google_environment",
        "oauth_test_status","blocked_flags","notes"
    },"POLICY_KEYS")
    require(policy["schema_version"]==1
            and policy["channel_id"]==EXPECTED_CHANNEL
            and policy["channel_handle"]=="@ClivoxPulse"
            and policy["stage"]=="A7_READONLY_ACCOUNT_BINDING"
            and policy["workflow_state"]=="OFFLINE_FIXTURE_ONLY_UNTIL_OWNER_OAUTH",
            "WRONG_CHANNEL_OR_STAGE")
    require(policy["required_scope"]==READONLY_SCOPE
            and policy["oauth_secret_source"]=="DEDICATED_CLIVOX_SECRETS_ONLY_NO_FLOWMINUTE_FALLBACK",
            "UNSAFE_OAUTH_SCOPE_OR_SECRET")
    for field in (
        "distinct_oauth_client_enrolled","owner_google_consent_verified",
        "oauth_refresh_secret_configured","private_clivox_identity_verified_via_oauth",
        "live_run_allowed",
    ):
        require(policy[field] is False,"FALSE_OWNER_OAUTH_"+field)
    require(policy["identity_client_implemented"] is True
            and policy["private_uploads_inventory_reader_implemented"] is True
            and policy["active_google_environment"] is None,
            "UNVERIFIED_API_RUNTIME")
    require(policy["allowed_request_methods"]==["GET"]
            and policy["allowed_youtube_api_paths"]==[
                "/youtube/v3/channels","/youtube/v3/playlistItems"
            ] and policy["fixed_google_hosts"]==[YOUTUBE_HOST,OAUTH_HOST],
            "UNSAFE_HOST_OR_METHOD")
    require(policy["initial_inventory_limit"]==MAX_INVENTORY
            and policy["inventory_completeness"]==
            "FIRST_PAGE_SAMPLE_ONLY_NOT_PRIVATE_RELEASE_LEDGER",
            "INVENTORY_SCOPE")
    require(policy["blocked_flags"]=={
        "media_download_enabled":False,
        "youtube_video_insert_enabled":False,
        "youtube_video_update_enabled":False,
        "youtube_video_delete_enabled":False,
        "youtube_schedule_enabled":False,
        "youtube_publish_enabled":False,
        "flowminute_oauth_fallback_enabled":False,
    },"YOUTUBE_WRITE_ENABLED")
    require(policy["token_handling"]=={
        "never_print_token":True,"never_commit_token":True,
        "no_token_in_url":True,"do_not_log_raw_api_response":True,
        "redact_http_errors":True,"do_not_store_refresh_response":True,
    },"UNSAFE_SECRET_HANDLING")

def validate_channels_mine(response:dict)->dict:
    require(type(response) is dict and response.get("kind")==
            "youtube#channelListResponse","CHANNELS_RESPONSE")
    channels=response.get("items")
    require(type(channels) is list and len(channels)==1,
            "ONE_OAUTH_CHANNEL_REQUIRED")
    channel=channels[0]
    require(type(channel) is dict and channel.get("kind")=="youtube#channel",
            "CHANNEL_ITEM")
    ident=channel.get("id")
    require(ident==EXPECTED_CHANNEL and ident!=OLD_CHANNEL,
            "AUTHENTICATED_WRONG_CHANNEL")
    details=channel.get("contentDetails")
    require(type(details) is dict,"CONTENT_DETAILS_REQUIRED")
    playlists=details.get("relatedPlaylists")
    require(type(playlists) is dict,"UPLOADS_PLAYLIST_MISSING")
    uploads=playlists.get("uploads")
    require(type(uploads) is str and
            uploads=="UU"+EXPECTED_CHANNEL[2:],
            "UPLOADS_PLAYLIST_CROSS_CHANNEL")
    snippet=channel.get("snippet")
    require(snippet is None or type(snippet) is dict,"INVALID_SNIPPET")
    title=snippet.get("title") if type(snippet) is dict else None
    require(title is None or (type(title) is str and 0<len(title)<=150),
            "INVALID_TITLE")
    # The caller should not export even a private uploads list from a public CI job.
    return {"identity_matches_clivox":True,
            "expected_channel_id":EXPECTED_CHANNEL,
            "uploads_playlist":uploads,
            "reported_channel_title":title}

def playlist_path(uploads_playlist:str)->str:
    require(uploads_playlist=="UU"+EXPECTED_CHANNEL[2:],
            "UNTRUSTED_PLAYLIST")
    return "/youtube/v3/playlistItems?"+urlencode({
        "part":"contentDetails","playlistId":uploads_playlist,
        "maxResults":MAX_INVENTORY
    })

def validate_inventory_sample(response:dict)->dict:
    require(type(response) is dict and response.get("kind")==
            "youtube#playlistItemListResponse","INVENTORY_RESPONSE")
    items=response.get("items")
    require(type(items) is list and len(items)<=MAX_INVENTORY,
            "INVENTORY_SIZE")
    seen=set()
    for item in items:
        require(type(item) is dict,"INVENTORY_ITEM")
        content=item.get("contentDetails")
        require(type(content) is dict,"INVENTORY_CONTENT")
        video_id=content.get("videoId")
        require(type(video_id) is str and
                VIDEO_ID.fullmatch(video_id) is not None
                and video_id not in seen,"VIDEO_ID_OR_DUPLICATE")
        seen.add(video_id)
    # Do not publish potentially private item IDs, raw snippets or page tokens.
    return {"inventory_first_page_count":len(items),
            "inventory_sample_limit":MAX_INVENTORY,
            "inventory_complete":False,
            "private_and_scheduled_inventory_exhaustively_verified":False,
            "video_ids_exported":False}

def _http_json(host:str,method:str,path:str,body:bytes|None=None,
               bearer:str|None=None)->dict:
    require(host in (YOUTUBE_HOST,OAUTH_HOST),"FIXED_API_HOST")
    if host==YOUTUBE_HOST:
        require(method=="GET" and body is None
                and (path==CHANNEL_PATH or
                     path.startswith("/youtube/v3/playlistItems?")),
                "YOUTUBE_ONLY_GET")
    else:
        require(method=="POST" and path=="/token" and bearer is None
                and body is not None and len(body)<16_000,
                "OAUTH_ONLY_REFRESH")
    require("access_token" not in path.lower() and
            "refresh_token" not in path.lower()
            and "client_secret" not in path.lower(),"TOKEN_IN_URL")
    require(type(path) is str and all(c not in path for c in ("\r","\n","#")),
            "PATH_INJECTION")
    require(bearer is None or (type(bearer) is str and 20<len(bearer)<4096
            and all(c not in bearer for c in ("\r","\n"))),
            "ACCESS_TOKEN_INVALID")
    headers={"Accept":"application/json"}
    if bearer is not None:
        headers["Authorization"]="Bearer "+bearer
    if body is not None:
        headers["Content-Type"]="application/x-www-form-urlencoded"
    connection=None
    try:
        connection=http.client.HTTPSConnection(host,timeout=12,context=ssl.create_default_context())
        connection.request(method,path,body=body,headers=headers)
        response=connection.getresponse()
        data=response.read(MAX_JSON+1)
        require(response.status==200,"REMOTE_AUTH_OR_API_REJECTED")
        require(len(data)<=MAX_JSON,"REMOTE_RESPONSE_TOO_LARGE")
        document=json.loads(data)
        require(type(document) is dict,"REMOTE_RESPONSE_FORMAT")
        return document
    except ChannelBindingDenied:
        raise
    except (OSError,TimeoutError,ValueError,http.client.HTTPException):
        # Do not print or return raw endpoint error; it may contain sensitive data.
        raise ChannelBindingDenied("CLIVOX_A7_DENY_NETWORK_OR_JSON_FAILURE") from None
    finally:
        if connection is not None:
            connection.close()

def refresh_readonly_token(*,client_id:str,client_secret:str,
                           refresh_token:str,http_call=_http_json)->str:
    require(type(client_id) is str and
            client_id.endswith(".apps.googleusercontent.com")
            and 20<len(client_id)<300,"DEDICATED_CLIENT_ID")
    for value,name in ((client_secret,"CLIENT_SECRET"),
                       (refresh_token,"REFRESH_TOKEN")):
        require(type(value) is str and 10<len(value)<4000
                and not any(x in value for x in ("\n","\r")),
                "INVALID_"+name)
    form=urlencode({"client_id":client_id,
        "client_secret":client_secret,"refresh_token":refresh_token,
        "grant_type":"refresh_token"}).encode("ascii")
    # Never log body, credentials or returned token. OAuth endpoint is fixed.
    response=http_call(OAUTH_HOST,"POST","/token",form,None)
    require(response.get("token_type")=="Bearer" and
            type(response.get("access_token")) is str
            and 20<len(response["access_token"])<4096,
            "OAUTH_REFRESH_INVALID")
    # Scope should be the exact granted read-only YouTube scope; do not accept
    # broader youtube, youtube.upload, youtube.force-ssl or analytics scopes.
    # Some issuers omit scope on refresh: fail closed until verified.
    raw_scope=response.get("scope")
    require(type(raw_scope) is str and
            set(raw_scope.split())=={READONLY_SCOPE},
            "READONLY_SCOPE_NOT_VERIFIED")
    return response["access_token"]

def inspect_owner_channel(access_token:str,http_call=_http_json)->dict:
    require(type(access_token) is str and 20<len(access_token)<4096,
            "ACCESS_TOKEN_MISSING")
    mine=http_call(YOUTUBE_HOST,"GET",CHANNEL_PATH,None,access_token)
    identity=validate_channels_mine(mine)
    # Only after exact channel binding can an inventory read be attempted.
    inventory=http_call(YOUTUBE_HOST,"GET",
        playlist_path(identity["uploads_playlist"]),None,access_token)
    report=validate_inventory_sample(inventory)
    return {"stage":"A7_READONLY_CLIVOX_ACCOUNT_IDENTITY",
        "expected_channel_id":EXPECTED_CHANNEL,
        "identity_matches_clivox":True,
        "api_operations":["channels.list:mine=true","playlistItems.list:uploads:first_page"],
        "read_only_requests":2,
        "token_written_to_disk":False,
        "access_token_exported":False,
        "inventory":report,
        "upload_authorized":False,
        "schedule_authorized":False,
        "publish_authorized":False,
        "note":"Read-only identity and first-page uploads sample; NOT exhaustive private/scheduled inventory or approval to publish."}

def synthetic_fixture_report()->dict:
    policy=load_json(POLICY)
    validate_policy(policy)
    identity=validate_channels_mine(load_json(FIXTURE_CHANNEL))
    inventory=validate_inventory_sample(load_json(FIXTURE_INVENTORY))
    return {"stage":"A7_OFFLINE_SYNTHETIC_FIXTURE",
        "channel_id":EXPECTED_CHANNEL,
        "fixture_identity_check_passed":identity["identity_matches_clivox"],
        "fixture_inventory":inventory,
        "actual_clivox_oauth_verified":False,
        "oauth_scope_really_verified":False,
        "clivox_readonly_secrets_configured":False,
        "actual_api_requests":0,
        "real_private_inventory_inspected":False,
        "upload_authorized":False,"schedule_authorized":False,
        "publish_authorized":False,
        "note":"Fixtures represent example API shapes and are not a real YouTube readback."}

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("fixture","live"),default="fixture")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    policy=load_json(POLICY)
    validate_policy(policy)
    if args.mode=="fixture":
        report=synthetic_fixture_report()
    else:
        # This must be enabled only in a separately audited protected
        # main-branch environment. A7 is currently deliberately closed.
        require(policy["live_run_allowed"] is True,
                "LIVE_CONNECTION_NOT_OWNER_APPROVED")
        client_id=os.environ.get("CLIVOX_A7_READONLY_CLIENT_ID")
        secret=os.environ.get("CLIVOX_A7_READONLY_CLIENT_SECRET")
        refresh=os.environ.get("CLIVOX_A7_READONLY_REFRESH_TOKEN")
        require(all((client_id,secret,refresh)),
                "DEDICATED_CLIVOX_OAUTH_SECRETS_MISSING")
        access=refresh_readonly_token(client_id=client_id,
            client_secret=secret,refresh_token=refresh)
        report=inspect_owner_channel(access)
        report["real_clivox_readonly_oauth_verified"]=True
    encoded=json.dumps(report,indent=2)+"\n"
    if args.out:
        require(not args.out.is_symlink(),"OUTPUT_SYMLINK")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(encoded,encoding="utf-8")
    else:
        print(encoded,end="")
    print("CLIVOX_A7_READONLY_ACCOUNT_CHECK_NO_YOUTUBE_WRITES")

if __name__=="__main__":
    main()
