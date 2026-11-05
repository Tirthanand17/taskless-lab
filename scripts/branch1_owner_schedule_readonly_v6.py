"""Protected GitHub-main ONLY, owner OAuth, zero-mutation read-only inventory.

Never print OAuth, video IDs, private titles or API responses. Writes only a
redacted 21-slot schedule report inside the ephemeral GitHub runner.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from autopilot.branch1_owner_schedule_readonly_v6 import read_owner_nov_schedule

ROOT=Path(__file__).resolve().parents[1]


def main() -> None:
    if (os.environ.get("GITHUB_ACTIONS")!="true"
        or os.environ.get("GITHUB_REF")!="refs/heads/main"
        or os.environ.get("GITHUB_REPOSITORY")!="Tirthanand17/taskless-lab"
        or os.environ.get("PUBLISH_ENABLED")!="false"
        or os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")!="0"
        or os.environ.get("FLOWMINUTE_ALLOW_LAPTOP")!="0"):
        raise ValueError("Trusted GitHub main read-only boundary not established")
    credential_json=os.environ.get("YOUTUBE_TOKEN_JSON")
    if not credential_json or len(credential_json)>16000:
        raise ValueError("Owner YouTube OAuth credential unavailable")
    temp=os.environ.get("RUNNER_TEMP")
    if not temp:
        raise ValueError("Protected ephemeral artifact directory missing")
    outdir=Path(temp).resolve()
    if not outdir.is_dir() or outdir.is_symlink():
        raise ValueError("Protected runner temporary directory unavailable")

    # Only the official OAuth client; no API key, raw personal desktop files,
    # owner login scraping, or generic YouTube public search. This script
    # invokes ONLY read-only YouTube client methods.
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    payload=json.loads(credential_json)
    if type(payload) is not dict or len(payload)>20:
        raise ValueError("Owner OAuth credential form invalid")
    credentials=Credentials.from_authorized_user_info(payload)
    youtube=build("youtube","v3",credentials=credentials,cache_discovery=False)
    report=read_owner_nov_schedule(
        youtube, root=ROOT, checked_at_utc=datetime.now(timezone.utc))
    if report["safe_to_change_any_scheduled_video"] is not False:
        raise ValueError("Read-only report incorrectly authorizes mutation")
    outfile=outdir/"FLOWMINUTE_OWNER_READONLY_REDACTED_NOV05_11.json"
    if outfile.exists() or outfile.is_symlink():
        raise ValueError("Refuse report overwrite")
    outfile.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",
                       encoding="utf8")
    outfile.chmod(0o600)
    # No private title, video ID, personal account, OAuth scopes, or playlist
    # is included in either the machine report or the single safe log line.
    print("OWNER_READONLY_SCAN_OK 21_SLOTS",
          "OWNER_PRIVATE_SCHEDULED",report["private_scheduled_slots_found"],
          "HISTORICAL_MATCHED",report["historical_ids_same_private_schedule_count"],
          "CONFLICTS",report["slot_conflicts"],
          "NO_YOUTUBE_UPLOAD_EDIT_OR_DELETE")


if __name__=="__main__":
    try:
        main()
    except BaseException:
        # Avoid accidental token/headers/YouTube private video metadata in
        # tracebacks, because GitHub workflow logs may be viewable publicly.
        print("OWNER_READONLY_NOT_VERIFIED: missing authorization, incomplete "
              "owner upload listing or channel mismatch; no change performed",
              file=sys.stderr)
        raise SystemExit(2) from None
