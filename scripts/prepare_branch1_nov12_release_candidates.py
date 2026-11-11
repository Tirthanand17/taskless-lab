"""B1 Nov 12: GitHub-only, exact-source render artifact -> four flat candidate bundles.

Does not call YouTube, create approvals, sign a release, or schedule media.
Only prepares *not approved* review files in correct flat layout for the
existing guarded manual publish-artifact-youtube.yml workflow.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
import shutil

SOURCE_STATUS="B1_NOV12_FOUR_REAL_ORIGINAL_VIDEO_FILES_OWNER_REVIEW_ONLY_NO_UPLOAD"
PREP_STATUS="B1_NOV12_FOUR_SHA_VERIFIED_FLAT_CANDIDATES_NOT_APPROVED_NOT_SCHEDULED"
NAMES=(
    "nov12_short_a_excel_16digits",
    "nov12_short_b_ai_fake_citations",
    "nov12_long_excel_silent_errors",
    "nov12_short_c_drive_link",
)
SLOTS_UTC=(
    "2026-11-12T05:30:00Z",
    "2026-11-12T08:00:00Z",
    "2026-11-12T10:30:00Z",
    "2026-11-12T15:00:00Z",
)
FILES=("REVIEW_ONLY_FINAL.mp4","ORIGINAL_SOURCE_TIMED_CAPTIONS.srt",
       "ORIGINAL_COVER.png")
SOURCE=Path("/tmp/flowminute-nov12-source-owner-review")
OUTPUT=Path("/tmp/flowminute-nov12-flat-release-candidates")
REPO=Path(__file__).resolve().parents[1]


class CandidateRefused(ValueError):
    """Source, owner, channel, encoded media or clock cannot be trusted."""


def need(ok,why):
    if not ok:
        raise CandidateRefused(why)


def digest(path: Path) -> str:
    h=sha256()
    with path.open("rb") as fp:
        for block in iter(lambda:fp.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    need(path.is_file() and not path.is_symlink()
         and path.stat().st_size<=150_000,
         "Missing bounded regular signed-source input")
    try:
        return json.loads(path.read_text("utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise CandidateRefused("Malformed source report") from None


def validate_source_run(meta):
    """Used on GitHub's *actual* successful source-run API response."""
    need(type(meta) is dict
         and meta.get("headBranch")=="main"
         and meta.get("conclusion")=="success"
         and meta.get("event")=="workflow_dispatch"
         and meta.get("workflowName")==
             "FlowMinute Branch 1 Nov12 Four Real Original Owner-Review Videos (NO YOUTUBE)"
         and type(meta.get("headSha")) is str
         and re.fullmatch("[0-9a-f]{40}",meta["headSha"]) is not None,
         "Source is not the approved GitHub-main four-video render workflow")
    return True


def validate_and_stage(root=SOURCE,output=OUTPUT,repo=REPO):
    need(isinstance(root,Path) and isinstance(output,Path) and isinstance(repo,Path)
         and root.is_dir() and not root.is_symlink()
         and not output.exists() and not output.is_symlink()
         and repo.is_dir(),
         "Untrusted source or nonempty destination")
    report=read_json(root/"FOUR_VIDEO_REVIEW_MANIFEST.json")
    source_brief=repo/"content/nov12_2026/four_video_review_brief.json"
    need(source_brief.is_file() and not source_brief.is_symlink()
         and report.get("status")==SOURCE_STATUS
         and report.get("date_ist")=="2026-11-12"
         and report.get("source_brief_sha256")==digest(source_brief)
         and report.get("physical_review_mp4_count")==4
         and report.get("original_short_count")==3
         and report.get("original_long_count")==1
         and report.get("owner_video_and_voice_reviews_completed")==0
         and report.get("youtube_uploads")==0
         and report.get("youtube_schedule_writes")==0
         and report.get("release_authorized") is False
         and report.get("simulated_ui_not_real_product_screen_capture") is True
         and type(report.get("episode_reports")) is list
         and len(report["episode_reports"])==4,
         "Original full-render claim or owner release state invalid")
    brief=read_json(source_brief)
    need(type(brief.get("episodes")) is list
         and [ep.get("id") for ep in brief["episodes"]]==list(NAMES)
         and brief.get("channel_id")=="UCCcL9Q_jqVq6LJmnYUSAFZA"
         and brief.get("target_timezone")=="Asia/Kolkata"
         and brief.get("safety",{}).get("actual_publishing_allowed") is False
         and brief.get("safety",{}).get("owner_final_watch") is False,
         "Brief cannot be interpreted as an owner release")
    staged=[]
    identities=set()
    # Verify everything first so an unexpected file never creates half a
    # supposed four-video candidate batch.
    for i,(id_,ep) in enumerate(zip(NAMES,report["episode_reports"])):
        original=brief["episodes"][i]
        metadata=read_json(repo/"content/episodes"/(id_+".json"))
        folder=root/id_
        need(type(ep) is dict and ep.get("episode_id")==id_
             and ep.get("kind") == ("long" if i==2 else "short")
             and ep.get("suggested_ist_slot")==original["time"]
             and ep.get("physical_h264_aac_full_decode_passed") is True
             and ep.get("human_full_watch") is False
             and ep.get("rights_and_factual_owner_signoff") is False
             and ep.get("youtube_scheduled") is False
             and ep.get("release_authorized") is False
             and type(ep.get("files")) is list
             and len(ep["files"])==4
             and type(ep.get("actual_mp4_sha256")) is str
             and re.fullmatch("[0-9a-f]{64}",ep["actual_mp4_sha256"])
             and ep["actual_mp4_sha256"] not in identities
             and type(ep.get("original_mp4_aac_post_encode")) is dict
             and ep["original_mp4_aac_post_encode"].get(
                 "integrated_lufs_and_true_peak_within_internal_band") is True,
             "Unverified or ambiguous original video/audio/owner release state")
        identities.add(ep["actual_mp4_sha256"])
        need(type(metadata) is dict and metadata.get("id")==id_
             and metadata.get("title")==original["title"]
             and metadata.get("description")==original["description"]
             and metadata.get("language")=="en"
             and metadata.get("proposed_time_ist")==original["time"]
             and metadata.get("requested_date_ist")=="2026-11-12"
             and metadata.get("owner_exact_media_release_signoff_observed") is False
             and metadata.get("youtube_uploaded") is False
             and metadata.get("youtube_scheduled") is False
             and metadata.get("renderer")=="manifest_v2"
             and len(metadata.get("scenes",[]))==(12 if i==2 else 5),
             "Metadata is not the exact source-locked unapproved episode")
        need(folder.is_dir() and not folder.is_symlink()
             and sorted(p.name for p in folder.iterdir())==
                 sorted(FILES+("ORIGINAL_SCENE_CONTACT_SHEET.png","READ_THIS_FIRST.txt")),
             "Untrusted owner review directory contents")
        entries={f.get("name"):f for f in ep["files"]}
        need(set(entries)==set(FILES+("ORIGINAL_SCENE_CONTACT_SHEET.png",)),
             "Missing exact physical MP4/SRT/cover data")
        for filename in entries:
            info=entries[filename]
            path=folder/filename
            need(path.is_file() and not path.is_symlink()
                 and type(info.get("bytes")) is int
                 and info["bytes"]==path.stat().st_size
                 and 100<=info["bytes"]<=200_000_000
                 and type(info.get("sha256")) is str
                 and re.fullmatch("[0-9a-f]{64}",info["sha256"])
                 and digest(path)==info["sha256"],
                 "Physical file content/size differs from successful source render")
        media=folder/"REVIEW_ONLY_FINAL.mp4"
        with media.open("rb") as stream:
            header=stream.read(12)
        need(header[4:8]==b"ftyp"
             and ep["actual_mp4_sha256"]==entries[media.name]["sha256"],
             "Original encoded MP4 lacks correct format or SHA")
        caption=folder/"ORIGINAL_SOURCE_TIMED_CAPTIONS.srt"
        need("-->" in caption.read_text("utf8") and caption.stat().st_size<100_000,
             "Timed original SRT absent")
        with (folder/"ORIGINAL_COVER.png").open("rb") as stream:
            need(stream.read(8)==b"\x89PNG\r\n\x1a\n",
                 "Original visual cover is not a PNG")
        staged.append({
            "id":id_,
            "title":metadata["title"],
            "proposed_publish_at_utc":SLOTS_UTC[i],
            "video_sha256":entries["REVIEW_ONLY_FINAL.mp4"]["sha256"],
            "srt_sha256":entries["ORIGINAL_SOURCE_TIMED_CAPTIONS.srt"]["sha256"],
            "thumbnail_sha256":entries["ORIGINAL_COVER.png"]["sha256"],
            "metadata_sha256":digest(repo/"content/episodes"/(id_+".json")),
            "source_run_status":"GITHUB_SUCCESSFUL_MAIN_PHYSICAL_FULL_DECODE",
            "owner_approval_verified":False,
            "owner_signature_verified":False,
            "youtube_upload_or_schedule_verified":False,
        })
    need(len(staged)==4 and len(identities)==4,
         "Not four distinct actual reviewed original videos")
    output.mkdir(mode=0o700)
    for item in staged:
        id_=item["id"]
        dest=output/id_
        dest.mkdir(mode=0o700)
        for filename in FILES:
            shutil.copyfile(root/id_/filename,dest/filename)
            need(digest(dest/filename)==digest(root/id_/filename),
                 "Output differs from the trusted exact source media")
        (dest/"CANDIDATE_PROVENANCE_NOT_RELEASE_APPROVAL.json").write_text(
            json.dumps({"status":PREP_STATUS,**item},sort_keys=True,indent=2)
            +"\n",encoding="utf8")
    (output/"FOUR_RELEASE_CANDIDATES_NO_YOUTUBE_UPLOAD.json").write_text(
        json.dumps({"status":PREP_STATUS,"date_ist":"2026-11-12",
                    "total_candidate_count":4,
                    "approved_release_count":0,
                    "youtube_scheduled_count":0,
                    "candidates":staged},sort_keys=True,indent=2)
        +"\n",encoding="utf8")
    return staged


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-run",required=True)
    args=parser.parse_args()
    need(os.environ.get("GITHUB_ACTIONS")=="true"
         and os.environ.get("GITHUB_REF")=="refs/heads/main"
         and os.environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
         and os.environ.get("PUBLISH_ENABLED")=="false"
         and os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")=="0"
         and re.fullmatch("[1-9][0-9]{0,19}",args.source_run)
         and SOURCE.parent==Path("/tmp")
         and OUTPUT.parent==Path("/tmp"),
         "Only GitHub-main manual no-OAuth artifact preparation allowed")
    proof_file=Path("/tmp/flowminute-nov12-source-run-readback.json")
    validate_source_run(read_json(proof_file))
    rows=validate_and_stage()
    print(json.dumps({"status":PREP_STATUS,"actual_sha_verified_candidates":len(rows),
        "youtube_uploads":0,"schedule_writes":0,"owner_signatures_provided":0},
                     sort_keys=True))


if __name__=="__main__":
    main()
