"""Nov13-17: strictly validate 3 real full-decoded originals; stage owner-only flat assets.

No YouTube connection; does NOT grant copyright, voice/listening,
facts or signed release approvals. Every byte is hash-bound to a
successful main workflow_dispatch original render; no external URLs.
"""
from __future__ import annotations

from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
import shutil

SOURCE_STATUS="B1_NOV13_17_PHYSICAL_THREE_ORIGINALS_OWNER_REVIEW_NO_UPLOAD"
DEST_STATUS="B1_NOV13_17_THREE_FLAT_SHA_VERIFIED_UNAPPROVED_CANDIDATES_NO_UPLOAD"
SOURCE_WORKFLOW="Flowminute B1 Nov13-17 Original 2 Shorts + 1 Long Review (NO YOUTUBE)"
HEX40=re.compile(r"[0-9a-f]{40}\Z")
HEX64=re.compile(r"[0-9a-f]{64}\Z")
RUN_ID=re.compile(r"[1-9][0-9]{0,19}\Z")
DATES=frozenset(f"2026-11-{n:02d}" for n in range(13,18))
TIMES=("11:00","20:30","16:00")
OFFSETS=("05:30:00","15:00:00","10:30:00")
FILE_NAMES=("REVIEW_ONLY_FINAL.mp4","ORIGINAL_SOURCE_TIMED_CAPTIONS.srt",
            "ORIGINAL_COVER.png","ORIGINAL_SCENE_CONTACT_SHEET.png")
PACKAGE_NAMES=("REVIEW_ONLY_FINAL.mp4","ORIGINAL_SOURCE_TIMED_CAPTIONS.srt",
               "ORIGINAL_COVER.png")
DEFAULT_REPO=Path(__file__).resolve().parents[1]
TEMP=Path("/tmp")


class OwnerCandidateRefused(ValueError):
    """Fail closed on forged source, media, date, channel or release claim."""


def required(ok,reason):
    if not ok:
        raise OwnerCandidateRefused(reason)


def file_hash(path):
    h=sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def bounded_json(path):
    required(isinstance(path,Path) and path.is_file() and not path.is_symlink()
             and path.stat().st_size<=400_000 and path.stat().st_size>3,
             "Missing source-owned bounded JSON")
    try:
        return json.loads(path.read_text("utf8"))
    except (ValueError,UnicodeError):
        raise OwnerCandidateRefused("Malformed source-owned JSON") from None


def check_main_render_proof(raw):
    required(type(raw) is dict
             and raw.get("headBranch")=="main"
             and raw.get("event")=="workflow_dispatch"
             and raw.get("conclusion")=="success"
             and raw.get("workflowName")==SOURCE_WORKFLOW
             and type(raw.get("headSha")) is str
             and HEX40.fullmatch(raw["headSha"]) is not None,
             "Source job is not a successful exact trusted main render")
    return raw["headSha"]


def _expected_episodes(date,repo):
    from autopilot.branch1_nov13_17_original_batch import read_day
    day,hash_ =read_day(date,repo)
    return day["episodes"],hash_


def stage_three(date, source, dest, repo=DEFAULT_REPO):
    required(date in DATES and isinstance(source,Path) and isinstance(dest,Path)
             and isinstance(repo,Path) and repo.is_dir()
             and source.is_dir() and not source.is_symlink()
             and not dest.exists() and not dest.is_symlink(),
             "Invalid date, source or existing destination")
    rows,brief_hash=_expected_episodes(date,repo)
    orig=bounded_json(source/"DAY_ORIGINAL_THREE_REVIEW_MANIFEST.json")
    required(type(orig) is dict
             and orig.get("status")==SOURCE_STATUS
             and orig.get("date_ist")==date
             and orig.get("source_brief_sha256")==brief_hash
             and orig.get("actual_h264_aac_verified_mp4_count")==3
             and orig.get("actual_original_shorts")==2
             and orig.get("actual_original_longs")==1
             and orig.get("release_owner_authorizations")==0
             and orig.get("youtube_uploads")==0
             and orig.get("youtube_scheduled_writes")==0
             and type(orig.get("episodes")) is list
             and len(orig["episodes"])==3,
             "Media report cannot be interpreted as an approved release")
    all_bytes=set()
    output=[]
    for i,(spec,entry) in enumerate(zip(rows,orig["episodes"])):
        id_=spec["id"]
        folder=source/id_
        expected=(date+"T"+OFFSETS[i]+"Z")
        metadata_path=repo/"content/episodes"/(id_+".json")
        metadata=bounded_json(metadata_path)
        required(type(entry) is dict
                 and entry.get("episode_id")==id_
                 and entry.get("date_ist")==date
                 and entry.get("kind")==spec["kind"]
                 and entry.get("proposed_time_ist")==TIMES[i]
                 and entry.get("title")==spec["title"]
                 and entry.get("primary_source")==spec["source"]
                 and entry.get("original_scenes")==len(spec["scenes"])
                 and entry.get("one_way_original_visual_states")==3*len(spec["scenes"])
                 and entry.get("physical_h264_aac_full_decode_passed") is True
                 and entry.get("owner_final_voice_captions_facts_rights_review") is False
                 and entry.get("release_signed") is False
                 and entry.get("youtube_uploaded") is False
                 and entry.get("youtube_scheduled") is False,
                 "A release or scene identity claim differs from original video")
        mastering=entry.get("post_encoded_mastering")
        required(type(mastering) is dict
                 and mastering.get("status")==
                     "B4G5_FINAL_ORIGINAL_AAC_TRUE_PEAK_LIMITED_LOUDNESS_VERIFIED_NO_PUBLISH"
                 and mastering.get("integrated_lufs_and_true_peak_within_internal_band") is True
                 and mastering.get("human_listening_and_mobile_playback_verified") is False
                 and mastering.get("rights_and_facts_approved") is False
                 and mastering.get("youtube_upload_or_release_authorized") is False
                 and mastering.get("exact_original_mp4_sha256")==entry.get("actual_mp4_sha256")
                 and mastering.get("source_pcm_duration_seconds_unchanged")==entry.get("actual_pcm_seconds"),
                 "Independent final original AAC proof missing/forged")
        required(type(metadata) is dict
                 and metadata.get("id")==id_
                 and metadata.get("renderer")=="manifest_v2"
                 and metadata.get("type")==spec["kind"]
                 and metadata.get("language")=="en"
                 and metadata.get("title")==spec["title"]
                 and metadata.get("requested_date_ist")==date
                 and metadata.get("proposed_time_ist")==TIMES[i]
                 and metadata.get("owner_exact_media_release_signoff_observed") is False
                 and metadata.get("youtube_uploaded") is False
                 and metadata.get("youtube_scheduled") is False
                 and [s.get("narration") for s in metadata.get("scenes",[])]==
                     [s[3] for s in spec["scenes"]]
                 and metadata.get("source_links")==[spec["source"]],
                 "Release metadata is not the exact original content and owner status")
        required(folder.is_dir() and not folder.is_symlink()
                 and set(p.name for p in folder.iterdir())==
                     set(FILE_NAMES+("README_OWNER_REVIEW_NOT_UPLOADED.txt",)),
                 "Original episode folder contains unknown media")
        claims=entry.get("files")
        required(type(claims) is list and len(claims)==4,
                 "Four physical original files are needed")
        claims_by_name={f.get("name"):f for f in claims if type(f) is dict}
        required(set(claims_by_name)==set(FILE_NAMES),
                 "Missing exact scene contact sheet or media SHA claim")
        for filename,details in claims_by_name.items():
            candidate=folder/filename
            required(candidate.is_file() and not candidate.is_symlink()
                     and type(details.get("bytes")) is int
                     and 100<=details["bytes"]<=240_000_000
                     and candidate.stat().st_size==details["bytes"]
                     and type(details.get("sha256")) is str
                     and HEX64.fullmatch(details["sha256"]) is not None
                     and file_hash(candidate)==details["sha256"],
                     "Physical original MP4, SRT, cover or scene art differs from proof")
        mp4=folder/"REVIEW_ONLY_FINAL.mp4"
        with mp4.open("rb") as f:
            hdr=f.read(12)
        required(hdr[4:8]==b"ftyp"
                 and claims_by_name["REVIEW_ONLY_FINAL.mp4"]["sha256"]==
                     entry["actual_mp4_sha256"]
                 and entry["actual_mp4_sha256"] not in all_bytes,
                 "Not a distinct physical original MP4")
        all_bytes.add(entry["actual_mp4_sha256"])
        srt=(folder/"ORIGINAL_SOURCE_TIMED_CAPTIONS.srt").read_text("utf8")
        required("-->" in srt and len(srt)>100 and len(srt)<150_000,
                 "Original speech-timed SRT absent")
        with (folder/"ORIGINAL_COVER.png").open("rb") as f:
            required(f.read(8)==b"\x89PNG\r\n\x1a\n","Original cover is not a PNG")
        output.append({
            "episode_id":id_,"title":spec["title"],"kind":spec["kind"],
            "future_proposed_publish_at_utc":expected,
            "video_sha256":entry["actual_mp4_sha256"],
            "captions_sha256":claims_by_name["ORIGINAL_SOURCE_TIMED_CAPTIONS.srt"]["sha256"],
            "thumbnail_sha256":claims_by_name["ORIGINAL_COVER.png"]["sha256"],
            "metadata_sha256":file_hash(metadata_path),
            "source_brief_sha256":brief_hash,
            "source_real_h264_aac_mastering_verified":True,
            "owner_exact_media_approved":False,
            "owner_release_ed25519_signed":False,
            "youtube_scheduled_by_this_workflow":False,
        })
    required(len(output)==3 and len(all_bytes)==3,"Not 3 exact unique approved-safe review files")
    dest.mkdir(mode=0o700)
    for entry in output:
        origin=source/entry["episode_id"]
        folder=dest/entry["episode_id"]
        folder.mkdir(mode=0o700)
        for name in PACKAGE_NAMES:
            shutil.copyfile(origin/name,folder/name)
            required(file_hash(folder/name)==file_hash(origin/name),
                     "Staged output no longer matches source MP4/SRT/cover")
        (folder/"SHA_VERIFIED_NOT_RELEASE_APPROVED.json").write_text(
            json.dumps({"status":DEST_STATUS,**entry},indent=2,sort_keys=True)+"\n",
            encoding="utf8")
    (dest/"THREE_FLAT_RELEASE_CANDIDATES_UNAPPROVED.json").write_text(
        json.dumps({"status":DEST_STATUS,"date_ist":date,"verified_count":3,
                    "youtube_scheduled_count":0,"owner_approved_count":0,
                    "entries":output},indent=2,sort_keys=True)+"\n",
        encoding="utf8")
    return output


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",choices=sorted(DATES),required=True)
    ap.add_argument("--source-run",required=True)
    args=ap.parse_args()
    required(os.environ.get("GITHUB_ACTIONS")=="true"
             and os.environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
             and os.environ.get("GITHUB_REF")=="refs/heads/main"
             and os.environ.get("PUBLISH_ENABLED")=="false"
             and os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")=="0"
             and RUN_ID.fullmatch(args.source_run) is not None,
             "Only validated GitHub main original review packaging allowed")
    source=TEMP/f"flowminute-b1-{args.date}-source"
    dest=TEMP/f"flowminute-b1-{args.date}-flat"
    proof=bounded_json(TEMP/f"flowminute-b1-{args.date}-source-run.json")
    check_main_render_proof(proof)
    entries=stage_three(args.date,source,dest)
    print(json.dumps({
        "status":DEST_STATUS,"source_run_id":args.source_run,
        "date_ist":args.date,"original_exact_mp4_sha256_verified":len(entries),
        "youtube_uploads":0,"youtube_scheduled":0,"owner_signatures":0
    },sort_keys=True))


if __name__=="__main__":
    main()
