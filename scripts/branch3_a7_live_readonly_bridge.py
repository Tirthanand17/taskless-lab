"""Owner-reviewed Clivox A7 live connection, READ-ONLY.

Designed for manual GitHub workflow_dispatch on main using a separately
configured protected clivox-readonly GitHub environment.
No authorization flow, token collection or OAuth secrets committed here.
Never attempts media downloads or YouTube writes.

Owner consent and environment protection MUST be independently established.
The owner-controlled enable secret is an explicit opt-in, not proof of actual
environment protection rules.
"""
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from typing import Callable

from scripts.branch3_a7_readonly_youtube import (
    EXPECTED_CHANNEL,
    ChannelBindingDenied,require,
    _http_json,refresh_readonly_token,inspect_owner_channel,
    synthetic_fixture_report,
)

REPOSITORY="Tirthanand17/taskless-lab"
WORKFLOW_REF=(REPOSITORY+
    "/.github/workflows/branch3-clivox-a7-live-readonly.yml@refs/heads/main")
ENABLE_SECRET="CLIVOX_A7_CONNECT_APPROVED"
CREDENTIALS=(
    "CLIVOX_A7_READONLY_CLIENT_ID",
    "CLIVOX_A7_READONLY_CLIENT_SECRET",
    "CLIVOX_A7_READONLY_REFRESH_TOKEN",
)

def validate_manual_context(env:Mapping[str,str])->None:
    require(env.get("GITHUB_ACTIONS")=="true","NOT_GITHUB_ACTIONS")
    require(env.get("GITHUB_REPOSITORY")==REPOSITORY,"WRONG_REPOSITORY")
    require(env.get("GITHUB_EVENT_NAME")=="workflow_dispatch","NOT_MANUAL")
    require(env.get("GITHUB_REF")=="refs/heads/main","NOT_MAIN")
    require(env.get("GITHUB_WORKFLOW_REF")==WORKFLOW_REF,"UNEXPECTED_WORKFLOW_REF")
    # GitHub protection rules must be separately configured by owner.
    # This key should be an ENVIRONMENT secret (not a repo secret).
    require(env.get(ENABLE_SECRET)=="approved-readonly-clivox-v1","OWNER_OPT_IN_MISSING")
    for key in CREDENTIALS:
        value=env.get(key)
        require(type(value) is str and len(value)>15 and
                all(c not in value for c in ("\r","\n")),
                "DEDICATED_SECRET_MISSING_"+key)

def run_live_owner_readonly(
    env:Mapping[str,str], *,
    http_call:Callable=_http_json,
)->dict:
    validate_manual_context(env)
    access_token=refresh_readonly_token(
        client_id=env[CREDENTIALS[0]],
        client_secret=env[CREDENTIALS[1]],
        refresh_token=env[CREDENTIALS[2]],
        http_call=http_call,
    )
    # Old channel / any wrong Brand Account fails before playlist request.
    result=inspect_owner_channel(access_token,http_call=http_call)
    require(result["identity_matches_clivox"] is True
            and result["expected_channel_id"]==EXPECTED_CHANNEL,
            "LIVE_CHANNEL_BINDING_FAILED")
    require(result["read_only_requests"]==2
            and result["api_operations"]==[
                "channels.list:mine=true","playlistItems.list:uploads:first_page"
            ],"UNEXPECTED_YOUTUBE_ACTION")
    # Do not export private video IDs or inventory counts in public logs.
    return {
        "stage":"A7_LIVE_READONLY_OWNER_CONNECTION",
        "channel_id":EXPECTED_CHANNEL,
        "authenticated_clivox_identity_confirmed":True,
        "read_only_youtube_get_requests":2,
        "oauth_refresh_executed":True,
        "inventory_sample_performed":True,
        "inventory_complete":False,
        "private_video_ids_disclosed":False,
        "creator_clip_rights_approved":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "youtube_publish_enabled":False,
        "note":"Live read-only identity checked; no source, upload, schedule or publishing rights."
    }

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("fixture","live"),default="fixture")
    args=parser.parse_args()
    if args.mode=="fixture":
        result=synthetic_fixture_report()
    else:
        result=run_live_owner_readonly(os.environ)
    print(json.dumps(result,sort_keys=True))
    print("CLIVOX_A7_READONLY_AUTH_CHECK_FINISHED_NO_YOUTUBE_WRITES")

if __name__=="__main__":
    main()
