"""Clivox A4 -> A5 -> A6 -> A8 integrated *source-free* rehearsal.

Checks actual A5 MP4 and SRT against original storyboard, FFprobe QA and
A6/A8 quarantine. No third-party footage, YouTube OAuth, media download or
release network operations. A passing result is NOT a licensed A9 pilot.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import re

from scripts.branch3_a4_editorial import check_script
from scripts.branch3_a5_render_original_demo import digest_file
from scripts.branch3_a5_media_qa import check_metadata, probe_file
from scripts.branch3_a6_signed_release import validate_quarantine_manifest, FIXTURE as RELEASE, POLICY as RELEASE_POLICY
from scripts.branch3_a8_private_first_dryrun import validate_fixture, PLAN, LEDGER

ROOT=Path(__file__).resolve().parents[1]
BLUEPRINT=ROOT/"branch3/editorial/fixtures/ymh_ep347_source_free.json"
CLIVOX="UCfPEvy0SefE_5nNlYlY_CyQ"
SHA256=re.compile(r"[0-9a-f]{64}\Z")
MP4="clivox-original-only-a5-demo.mp4"
SRT="on-screen-editorial-script-not-dialogue.srt"
MANIFEST="synthetic-demo-manifest.json"
QA="synthetic-technical-qa-report.json"

class RehearsalDenied(ValueError):
    """Any inconsistency stops the demo, never allows a release."""

def require(ok: bool,reason:str)->None:
    if not ok:
        raise RehearsalDenied("CLIVOX_REHEARSAL_DENY_"+reason)

def read_json(path:Path,max_bytes:int=80_000)->dict:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_size<=max_bytes,"UNSAFE_JSON_FILE")
    value=json.loads(path.read_text("utf-8"))
    require(type(value) is dict,"JSON_NOT_OBJECT")
    return value

def validate_handoff(
    *,blueprint:dict,manifest:dict,qa:dict,
    video_hash:str,video_bytes:int,srt_hash:str,probe:dict,srt_text:str,
    release:dict,release_policy:dict,
    schedule:dict,ledger:dict,
)->dict:
    """Cross-check actual stages; call with bytes probed independently from files."""
    editorial=check_script(blueprint)
    require(editorial["channel_id"]==CLIVOX
            and editorial["status"]=="HOLD_UNTIL_VERIFIED_RIGHTS_AND_EDITORIAL_REVIEW",
            "EDITORIAL_NOT_ON_HOLD")
    require(type(manifest) is dict
            and manifest.get("stage")=="A5_ORIGINAL_ONLY_SYNTHETIC_BENCHMARK"
            and manifest.get("channel_id")==CLIVOX
            and manifest.get("mode") in ("preview","full")
            and manifest.get("concept_id")==blueprint["proposal_id"]
            and manifest.get("source_blueprint_sha256")==editorial["editorial_plan_sha256"],
            "STORYBOARD_TO_MP4_PROVENANCE")
    require(manifest.get("video_name")==MP4 and manifest.get("srt_name")==SRT,
            "UNEXPECTED_FILE_NAME")
    require(manifest.get("scene_card_names")==[
        f"scene-{i:02}.png" for i in range(len(blueprint["beats"]))
    ],"SCENE_LIST")
    require(type(video_hash) is str and SHA256.fullmatch(video_hash) is not None
            and video_hash==manifest.get("video_sha256"),
            "EXACT_MP4_HASH")
    require(type(srt_hash) is str and SHA256.fullmatch(srt_hash) is not None
            and srt_hash==manifest.get("srt_sha256"),
            "EXACT_CAPTION_HASH")
    require(type(video_bytes) is int and video_bytes>100_000
            and video_bytes==manifest.get("video_size_bytes"),
            "EXACT_MP4_LENGTH")
    require(type(qa) is dict,"QA_REPORT")
    actual_qa=check_metadata(probe,manifest,srt_text)
    require(qa==actual_qa,"QA_RESULT_CHANGED_OR_FORGED")
    require(qa["synthetic_video_technical_checks_passed"] is True
            and qa["source_rights_verified"] is False
            and qa["licensed_media_qa_completed"] is False
            and qa["voiceover_and_production_mix_qa_completed"] is False
            and qa["ready_to_publish"] is False,
            "QA_PREMATURE_RELEASE")
    require("SOURCE PLACEHOLDER" in srt_text
            and manifest.get("original_voiceover_recorded") is False
            and manifest.get("source_media_attached") is False,
            "LICENSED_SOURCE_OR_VOICE_MISREPRESENTED")
    quarantine=validate_quarantine_manifest(release,release_policy)
    require(quarantine["video_upload_authorized"] is False
            and quarantine["signed_licensed_assets"]==0,"A6_PRODUCTION_RELEASE")
    dry_run=validate_fixture(schedule,ledger)
    require(dry_run["youtube_upload_authorized"] is False
            and dry_run["youtube_schedule_authorized"] is False
            and dry_run["actual_youtube_network_calls"]==0,
            "A8_UPLOAD_OR_SCHEDULE")
    require(release["release_id"]==schedule["source_release_id"],
            "RELEASE_PLAN_MISMATCH")
    require(editorial["youtube_upload_authorized"] is False
            and qa["youtube_upload_authorized"] is False
            and quarantine["video_upload_authorized"] is False
            and dry_run["youtube_upload_authorized"] is False,
            "RELEASE_IN_ANY_STAGE")
    return {
        "stage":"CLIVOX_A4_A5_A6_A8_INTEGRATED_SOURCE_FREE_REHEARSAL",
        "channel_id":CLIVOX,
        "result":"TECHNICALLY_CHECKED_ORIGINAL_DEMO_QUARANTINED",
        "stages_verified":[
            "A4_SOURCE_FREE_STORYBOARD","A5_MP4_SRT_FFPROBE_AND_HASHES",
            "A6_UNSIGNED_QUARANTINE","A8_NO_WRITE_PRIVATE_FIRST_DRYRUN"
        ],
        "mode":manifest["mode"],
        "resolution":qa["resolution"],
        "duration_seconds":qa["duration_seconds"],
        "video_sha256":video_hash,
        "video_size_bytes":video_bytes,
        "storyboard_sha256":editorial["editorial_plan_sha256"],
        "caption_sha256":srt_hash,
        "synthetic_tones_not_voiceover":True,
        "unlicensed_source_placeholder_visible":True,
        "creator_license_verified":False,
        "real_licensed_pilot_completed":False,
        "human_editorial_review_completed":False,
        "real_owner_video_signature_present":False,
        "google_oauth_or_youtube_network_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "note":"End-to-end original-only technical rehearsal, NOT a creator-licensed video or YouTube publication."
    }

def inspect_directory(directory:Path)->dict:
    require(directory.is_absolute() and directory.is_dir()
            and not directory.is_symlink()
            and directory!=ROOT and ROOT not in directory.parents,
            "MUST_USE_EPHEMERAL_OUTSIDE_PUBLIC_REPO")
    needed=[MP4,SRT,MANIFEST,QA]
    for filename in needed:
        p=directory/filename
        require(p.is_file() and not p.is_symlink() and p.parent==directory,
                "REQUIRED_REHEARSAL_FILE")
    media=directory/MP4
    caption=directory/SRT
    require(media.stat().st_size<250_000_000
            and caption.stat().st_size<100_000,"EXCESSIVE_MEDIA_FILE")
    return validate_handoff(
        blueprint=read_json(BLUEPRINT),
        manifest=read_json(directory/MANIFEST),
        qa=read_json(directory/QA),
        video_hash=digest_file(media),
        video_bytes=media.stat().st_size,
        srt_hash=digest_file(caption),
        probe=probe_file(media),
        srt_text=caption.read_text("utf-8"),
        release=read_json(RELEASE),
        release_policy=read_json(RELEASE_POLICY),
        schedule=read_json(PLAN),
        ledger=read_json(LEDGER),
    )

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,required=True)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    report=inspect_directory(args.directory)
    if args.report:
        require(args.report.is_absolute()
                and args.report.parent==args.directory
                and args.report.name=="integrated-source-free-rehearsal-report.json"
                and not args.report.is_symlink(),"REPORT_LOCATION")
        args.report.write_text(json.dumps(report,indent=2)+"\n","utf-8")
    else:
        print(json.dumps(report,sort_keys=True))
    print("CLIVOX_INTEGRATION_REHEARSAL_PASSED_NO_LICENSE_NO_YOUTUBE_UPLOAD")

if __name__=="__main__":
    main()
