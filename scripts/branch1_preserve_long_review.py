"""Cloud-only preservation of exact real Python long video for an owner release.

Accepts ONLY physical main GitHub source run #43880108409. It never uploads to
YouTube, alters a source MP4, creates a public GitHub release or claims owner
rights/caption approval. Local artifact is temporary on a GitHub Actions runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

SOURCE_RUN=43880108409
SOURCE_ARTIFACT="b1-REAL-PYTHON-LONG-OWNER-REVIEW-ONLY-43880108409"
VIDEO="REAL_PYTHON_LONG_NARRATED_REVIEW_ONLY.mp4"
CAPTIONS="ORIGINAL_SOURCE_TIMED_CAPTIONS.srt"
RECEIPT="ORIGINAL_LONG_MEDIA_RECEIPT_NO_RELEASE.json"
MOTION="LONG_SOURCE_PIXEL_SCREEN_REVIEW_ONLY.json"
THUMB="REAL_RECORDED_PYTHON_TOTALS_COVER_REVIEW_ONLY.png"
BUNDLE="REAL_PYTHON_LONG_PRIVATE_REVIEW_BUNDLE.json"
EXPECTED_VIDEO_SHA="1a20dedf886f3228445ed718e1f2e93a7e38cd74abf8aeb211540e32b6683f42"
EXPECTED_CAPTION_SHA="b4b317c8d1d9883294e9ebb32b23c6790a4cdb891be9bbd560fd459baa132a0e"
EPISODE="fm_real_python_csv_three_bugs_long_en"

class PrivateReviewRefused(ValueError):
    pass

def need(condition,reason):
    if not condition:
        raise PrivateReviewRefused(reason)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def proof(video_sha:str,caption_sha:str,receipt:dict,motion:dict)->dict:
    need(video_sha==EXPECTED_VIDEO_SHA and caption_sha==EXPECTED_CAPTION_SHA,
         "EXACT_20261116_LONG_FILE_AND_CAPTIONS_REQUIRED")
    need(type(receipt) is dict and receipt.get("schema")==
         "FLOWMINUTE_B1_EXECUTED_PYTHON_LONG_V1"
         and receipt.get("episode_id")==EPISODE
         and receipt.get("final_sha256")==video_sha
         and receipt.get("caption_sha256")==caption_sha
         and receipt.get("status")=="LONG_REAL_PYTHON_EXECUTED_SOURCE_OWNER_REVIEW_ONLY"
         and receipt.get("duration_seconds")==214.833
         and receipt.get("true_software_execution") is True
         and receipt.get("fictional_data_only") is True
         and receipt.get("raw_csv_rows")==8
         and receipt.get("clean_csv_rows")==6
         and receipt.get("raw_total")=="2656.25"
         and receipt.get("clean_total")=="1430.75"
         and receipt.get("owner_watched") is False
         and receipt.get("rights_signed") is False
         and receipt.get("publishing_authorized") is False
         and receipt.get("youtube_uploads")==0
         and receipt.get("youtube_schedules")==0,
         "ORIGINAL_REAL_PYTHON_RECEIPT_UNTRUSTED")
    audio=receipt.get("independent_encoded_aac_mastering")
    need(type(audio) is dict
         and audio.get("exact_original_mp4_sha256")==video_sha
         and audio.get("integrated_lufs_and_true_peak_within_internal_band") is True
         and audio.get("human_listening_and_mobile_playback_verified") is False
         and audio.get("rights_and_facts_approved") is False
         and audio.get("youtube_upload_or_release_authorized") is False,
         "ORIGINAL_AAC_OR_RIGHTS_RECEIPT_UNTRUSTED")
    need(type(motion) is dict
         and motion.get("schema")=="FLOWMINUTE_B1_LONG_REAL_SOURCE_PIXEL_V1"
         and motion.get("final_sha256")==video_sha
         and motion.get("status")=="PASS_LONG_SOURCE_MOTION_HUMAN_REVIEW_REQUIRED"
         and motion.get("static_screen_risk") is False
         and motion.get("real_first_three_second_change") is True
         and motion.get("owner_creative_approval") is False
         and motion.get("youtube_uploads")==0
         and motion.get("youtube_schedules")==0,
         "SOURCE_PIXEL_EVIDENCE_UNTRUSTED")
    return {
        "schema":"FLOWMINUTE_B1_PRIVATE_CLOUD_LONG_REVIEW_STAGING_V1",
        "source_run_id":SOURCE_RUN,
        "source_artifact":SOURCE_ARTIFACT,
        "video_file":VIDEO,"video_sha256":video_sha,
        "caption_file":CAPTIONS,"caption_sha256":caption_sha,
        "episode_id":EPISODE,"duration_seconds":214.833,
        "channel_id":"UCCcL9Q_jqVq6LJmnYUSAFZA",
        "platform_title":"Why Your CSV Total Is Wrong: 3 Data-Cleaning Bugs in Python",
        "fictional_data_only":True,
        "owner_video_approval_in_chat_does_not_sign_rights_or_facts":True,
        "owner_rights_fact_captions_signature_verified":False,
        "youtube_authenticated_channel_readback":False,
        "youtube_uploads":0,"youtube_schedules":0,
        "automatic_public_release":False,
        "release_status":"NOT_RELEASED_AWAIT_OWNER_OAUTH_AND_SIGNED_RELEASE"
    }

def stage(source:Path,destination:Path)->dict:
    need(source.is_dir() and not source.is_symlink()
         and destination.parent.is_dir() and not destination.exists(),
         "DIRECTORIES_NOT_ISOLATED")
    paths={name:source/name for name in (VIDEO,CAPTIONS,RECEIPT,MOTION)}
    for name,p in paths.items():
        need(p.is_file() and not p.is_symlink() and
             100<=p.stat().st_size<=12_000_000,"MISSING_OR_UNSAFE_"+name)
    receipt=json.loads(paths[RECEIPT].read_text("utf8"))
    motion=json.loads(paths[MOTION].read_text("utf8"))
    result=proof(sha(paths[VIDEO]),sha(paths[CAPTIONS]),receipt,motion)
    need(paths[VIDEO].stat().st_size>500_000
         and paths[CAPTIONS].read_text("utf8").count("-->")>=40,
         "TRUNCATED_REAL_LONG_MEDIA_OR_CAPTIONS")
    destination.mkdir(mode=0o700)
    for item in paths.values():
        shutil.copyfile(item,destination/item.name)
    thumb=destination/THUMB
    p=subprocess.run([
        "ffmpeg","-nostdin","-hide_banner","-v","error","-y",
        "-ss","1.8","-i",str(paths[VIDEO]),"-frames:v","1",
        "-vf","scale=1280:720:flags=lanczos",
        str(thumb)
    ],capture_output=True,timeout=60)
    need(p.returncode==0 and thumb.is_file()
         and 20000<thumb.stat().st_size<3_000_000,
         "EXACT_RECORDED_THUMBNAIL_FAILED")
    result["thumbnail_file"]=THUMB
    result["thumbnail_sha256"]=sha(thumb)
    (destination/BUNDLE).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n","utf8")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(stage(args.source,args.output),sort_keys=True))

if __name__=="__main__":
    main()
