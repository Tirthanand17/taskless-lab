"""B4d3 independent review-intake for *actual* GitHub-retained B4d2 media.

Only reads 3 existing author-created demo MP4/SRT/PNG files from a downloaded
GitHub Actions artifact. Does not import producer/renderer; independently
rehashes every actual byte, reads PNG headers, parses SRT timings, executes
ffprobe with argv (not shell), verifies exact source-storyboard identity,
and produces a public reviewer checklist/metadata receipt.

Everything remains unapproved and CANNOT authorize YouTube upload. This is
not independent human listening, claim validation, originality, or licenses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import subprocess

from autopilot.primary_sourced_storyboards import build_story

SOURCE_RUN_ID=41970364138
SOURCE_ARTIFACT_ID=13389693311
SOURCE_SHA="0e230a842790b05616ffa007dea2f43f9cfaf4c3"
SOURCE_ARTIFACT_NAME=f"flowminute-unapproved-three-real-demo-videos-{SOURCE_RUN_ID}-1"
STATUS="REAL_RETAINED_3_VIDEO_REVIEW_INTAKE_OWNER_REVIEW_PENDING_NO_RELEASE"
REQUIRED_FILES=frozenset(("PREVIEW_UNAPPROVED.mp4","CAPTIONS_UNAPPROVED.srt","THUMBNAIL_UNAPPROVED.png"))
SLOTS=("short_am","long","short_pm")
SHA=re.compile(r"^[a-f0-9]{64}$")
STAMP=re.compile(r"^(\d{2}):([0-5]\d):([0-5]\d),(\d{3})$")
TIMING=re.compile(r"^(\d\d:[0-5]\d:[0-5]\d,\d{3}) --> (\d\d:[0-5]\d:[0-5]\d,\d{3})$")
PNG_MAGIC=b"\x89PNG\r\n\x1a\n"


class ReviewIntakeRejected(ValueError):
    """An incomplete/changed/approved public technical preview is not reviewable."""


def _plain_file(path: Path, max_bytes: int) -> tuple[str,int]:
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise ReviewIntakeRejected("Missing/nonregular public technical media file")
    size=path.stat().st_size
    if not 20 <= size <= max_bytes:
        raise ReviewIntakeRejected("Media unexpectedly empty/oversize")
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest(),size


def _unique_pairs(pairs):
    obj={}
    for k,v in pairs:
        if k in obj:
            raise ReviewIntakeRejected("Duplicate reviewer manifest JSON key")
        obj[k]=v
    return obj


def _json_object(path: Path) -> dict:
    digest,size=_plain_file(path,50000)
    try:
        d=json.loads(path.read_text(encoding="utf-8"),
                     object_pairs_hook=_unique_pairs,
                     parse_constant=lambda _:
                        (_ for _ in ()).throw(ReviewIntakeRejected("Nonfinite manifest")))
    except (UnicodeError,ValueError,TypeError) as exc:
        if isinstance(exc,ReviewIntakeRejected):
            raise
        raise ReviewIntakeRejected("Invalid reviewer manifest") from None
    if type(d) is not dict:
        raise ReviewIntakeRejected("Expected JSON manifest object")
    return d


def _all_false(obj: dict, keys: tuple[str,...]) -> None:
    if any(obj.get(k) is not False for k in keys):
        raise ReviewIntakeRejected("Changed, missing or forged authorization flag")


def validate_exact_media_artifact(root: Path) -> list[dict]:
    """Verified identity/hash structure independent of source render functions.

    This is *not* approval of third party factual claims or legal rights.
    """
    root=Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ReviewIntakeRejected("Unsafe artifact root")
    manifest_name="UNAPPROVED_PUBLIC_REVIEW_MANIFEST.json"
    d=_json_object(root/manifest_name)
    expected_root_keys={
        "schema_version","status","artifact_scope","source",
        "technical_original_mp4_captions_thumbnail_count","episodes",
        "contains_public_original_source_demo_material_only",
        "original_voice_model_file_weights_archived",
        "real_rights_or_editorial_approval",
        "actual_live_youtube_uploads","release_authorized",
    }
    if (set(d)!=expected_root_keys or type(d.get("schema_version")) is not int
        or d["schema_version"]!=1
        or d.get("status")!="PUBLIC_REVIEW_DRAFT_MEDIA_RETAINED_NOT_RELEASE_APPROVED"
        or d.get("artifact_scope")!="PUBLIC_GITHUB_ACTIONS_EPHEMERAL_REVIEW_ONLY"
        or d.get("source")!="THREE_FIXED_20261104_ORIGINAL_TOPIC_DEMOS_NOT_DAILY_FRESH_EPISODES"
        or type(d.get("technical_original_mp4_captions_thumbnail_count")) is not int
        or d["technical_original_mp4_captions_thumbnail_count"]!=3
        or d.get("contains_public_original_source_demo_material_only") is not True
        or d.get("original_voice_model_file_weights_archived") is not False
        or type(d.get("actual_live_youtube_uploads")) is not int
        or d["actual_live_youtube_uploads"]!=0):
        raise ReviewIntakeRejected("Unexpected original review-artifact provenance")
    _all_false(d,("real_rights_or_editorial_approval","release_authorized"))
    episodes=d.get("episodes")
    if type(episodes) is not list or len(episodes)!=3:
        raise ReviewIntakeRejected("Missing original three episodes")
    stories=[build_story(slot) for slot in SLOTS]
    if {x.name for x in root.iterdir()} != {
        manifest_name,*[x["episode_id"] for x in stories]
    }:
        raise ReviewIntakeRejected("Unreviewed files or missing episode folders")
    verified=[]
    seen_shas=set()
    for item,story in zip(episodes,stories):
        if (type(item) is not dict or set(item)!={
            "slot","format","episode_id","source_draft_sha256",
            "source_claims_human_fact_verified","owner_full_watch_completed",
            "media_and_voice_rights_approved",
            "technical_full_video_decode_passed",
            "technical_spoken_srt_and_scene_checks_passed",
            "files","youtube_upload_enabled","release_authorized",
        }):
            raise ReviewIntakeRejected("Episode manifest changed or gained privilege")
        if (item.get("slot")!=story["slot"] or item.get("format")!=story["format"]
            or item.get("episode_id")!=story["episode_id"]
            or item.get("source_draft_sha256")!=story["draft_sha256"]
            or item.get("technical_full_video_decode_passed") is not True
            or item.get("technical_spoken_srt_and_scene_checks_passed") is not True):
            raise ReviewIntakeRejected("Renderer identity/technical report disagreement")
        _all_false(item,(
            "source_claims_human_fact_verified","owner_full_watch_completed",
            "media_and_voice_rights_approved","youtube_upload_enabled",
            "release_authorized",
        ))
        folder=root/story["episode_id"]
        if folder.is_symlink() or not folder.is_dir() or {f.name for f in folder.iterdir()}!=REQUIRED_FILES:
            raise ReviewIntakeRejected("Unexpected media files/directories")
        files=item.get("files")
        if type(files) is not list or len(files)!=3:
            raise ReviewIntakeRejected("Missing exact three media file records")
        names=set()
        details={}
        for rec in files:
            if (type(rec) is not dict or set(rec)!={"filename","sha256","bytes"}
                or type(rec["filename"]) is not str
                or rec["filename"] not in REQUIRED_FILES
                or rec["filename"] in names
                or type(rec["sha256"]) is not str or not SHA.fullmatch(rec["sha256"])
                or type(rec["bytes"]) is not int):
                raise ReviewIntakeRejected("Forged media inventory member")
            names.add(rec["filename"])
            name=rec["filename"]
            limit=300000000 if name.endswith(".mp4") else (
                18000000 if name.endswith(".png") else 200000)
            digest,size=_plain_file(folder/name,limit)
            if digest!=rec["sha256"] or size!=rec["bytes"]:
                raise ReviewIntakeRejected("Physical media bytes disagree with manifest")
            details[name]={"sha256":digest,"bytes":size}
        if names!=REQUIRED_FILES:
            raise ReviewIntakeRejected("Wrong exact draft file set")
        if details["PREVIEW_UNAPPROVED.mp4"]["sha256"] in seen_shas:
            raise ReviewIntakeRejected("Identical videos reused for different topics")
        seen_shas.add(details["PREVIEW_UNAPPROVED.mp4"]["sha256"])
        verified.append({
            "slot":story["slot"],"format":story["format"],
            "episode_id":story["episode_id"],
            "theme":story["theme"],
            "source_story_draft_sha256":story["draft_sha256"],
            "files":details,
            "real_human_approval":False,
            "release_authorized":False,
        })
    return verified


def _srt_milliseconds(value: str) -> int:
    match=STAMP.fullmatch(value)
    if not match:
        raise ReviewIntakeRejected("Invalid SRT timestamp")
    hours,minutes,seconds,ms=(int(x) for x in match.groups())
    if hours>2:
        raise ReviewIntakeRejected("Unbounded SRT time")
    return ((hours*60+minutes)*60+seconds)*1000+ms


def inspect_srt(path: Path, duration: float) -> dict:
    try:
        text=path.read_text(encoding="utf-8-sig").replace("\r\n","\n")
    except (UnicodeError,ValueError):
        raise ReviewIntakeRejected("SRT not UTF8") from None
    if not text.strip() or "\x00" in text or len(text.encode("utf-8"))>200000:
        raise ReviewIntakeRejected("Empty or invalid caption text")
    blocks=re.split(r"\n\s*\n",text.strip())
    if not 8 <= len(blocks)<=400:
        raise ReviewIntakeRejected("Unexpected number of timed original speech cues")
    last_end=-1
    for n,block in enumerate(blocks,1):
        lines=block.splitlines()
        if len(lines)<3 or lines[0].strip()!=str(n):
            raise ReviewIntakeRejected("Broken SRT cue order or empty caption")
        m=TIMING.fullmatch(lines[1].strip())
        if not m:
            raise ReviewIntakeRejected("Broken SRT time range")
        start,end=(_srt_milliseconds(v) for v in m.groups())
        if start < max(0,last_end) or end<=start or end > (duration+.8)*1000:
            raise ReviewIntakeRejected("Caption overlap/gap-boundary beyond real video")
        if not all(0<len(s.strip())<=235 for s in lines[2:]):
            raise ReviewIntakeRejected("Empty/oversize caption text")
        last_end=end
    return {
        "caption_cue_count":len(blocks),
        "last_caption_end_seconds":round(last_end/1000,3),
        "true_caption_text_human_checked":False,
    }


def inspect_png(path: Path) -> dict:
    with path.open("rb") as f:
        header=f.read(24)
    if (len(header)!=24 or header[:8]!=PNG_MAGIC
        or header[12:16]!=b"IHDR"
        or struct.unpack(">I",header[8:12])[0]!=13):
        raise ReviewIntakeRejected("Wrong PNG header or IHDR")
    width,height=struct.unpack(">II",header[16:24])
    if (width,height)!=(1280,720):
        raise ReviewIntakeRejected("Wrong original review thumbnail size")
    return {"png_size":"1280x720","visual_thumbnail_human_reviewed":False}


def inspect_video_ffprobe(path: Path, kind: str) -> dict:
    """Runs ONLY fixed ffprobe argv locally, NO shell or network process."""
    try:
        p=subprocess.run(
            ["ffprobe","-v","error","-show_streams","-show_format",
             "-of","json",str(path)],text=True,capture_output=True,
            timeout=50,check=True,
        )
        data=json.loads(p.stdout)
    except (OSError,ValueError,subprocess.SubprocessError):
        raise ReviewIntakeRejected("Actual FFprobe media readback failed") from None
    if type(data) is not dict or type(data.get("streams")) is not list:
        raise ReviewIntakeRejected("Malformed FFprobe response")
    streams=data["streams"]
    video=[s for s in streams if s.get("codec_type")=="video"]
    audio=[s for s in streams if s.get("codec_type")=="audio"]
    width,height=(1920,1080) if kind=="long" else (1080,1920)
    if (len(video)!=1 or len(audio)!=1
        or video[0].get("codec_name")!="h264"
        or video[0].get("pix_fmt")!="yuv420p"
        or (video[0].get("width"),video[0].get("height"))!=(width,height)
        or audio[0].get("codec_name")!="aac"):
        raise ReviewIntakeRejected("Wrong actual video/audible codec or dimensions")
    try:
        duration=float(data["format"]["duration"])
    except (KeyError,TypeError,ValueError,OverflowError):
        raise ReviewIntakeRejected("Missing physical video duration") from None
    import math
    low,high=(90,320) if kind=="long" else (28,110)
    if not math.isfinite(duration) or not low<=duration<=high:
        raise ReviewIntakeRejected("Wrong actual Short/long video duration")
    return {
        "codec":"H264_AAC",
        "resolution":f"{width}x{height}",
        "duration_seconds":round(duration,3),
        "full_video_human_watched":False,
    }


def make_owner_review_intake(root: Path) -> dict:
    """Recheck producer's persisted files with ffprobe, SRT and PNG parsing."""
    episodes=validate_exact_media_artifact(root)
    for entry in episodes:
        folder=Path(root)/entry["episode_id"]
        media=inspect_video_ffprobe(folder/"PREVIEW_UNAPPROVED.mp4",entry["format"])
        cap=inspect_srt(folder/"CAPTIONS_UNAPPROVED.srt",media["duration_seconds"])
        img=inspect_png(folder/"THUMBNAIL_UNAPPROVED.png")
        entry.update({"actual_ffprobe":media,"actual_srt":cap,"actual_png":img})
    return {
        "schema_version":1,"status":STATUS,
        "b4d2_producer_main_sha":SOURCE_SHA,
        "b4d2_producer_github_run_id":SOURCE_RUN_ID,
        "b4d2_producer_artifact_id":SOURCE_ARTIFACT_ID,
        "b4d2_producer_artifact_name":SOURCE_ARTIFACT_NAME,
        "files_physically_rehashed_again_in_independent_runner":True,
        "actual_ffprobe_and_caption_time_and_png_header_checked":True,
        "episodes":episodes,
        "actual_human_full_watch_listen_completed":False,
        "all_atomic_claims_independently_reviewed_by_human":False,
        "original_voice_model_and_graphic_rights_cleared":False,
        "thumbnail_title_caption_narration_reviewed_by_owner":False,
        "owner_oauth_connected":False,
        "real_youtube_upload_or_schedule":False,
        "release_authorized":False,
    }


def _review_markdown(data: dict) -> str:
    lines=[
        "# FlowMinute — OWNER REVIEW REQUIRED (three public technical previews)",
        "",
        "This checklist is UNSIGNED, UNAPPROVED, and is NOT an automated publication grant.",
        "Producer: https://github.com/Tirthanand17/taskless-lab/actions/runs/41970364138",
        "Download the 7-day public review ZIP before November 12, 2026:",
        "https://github.com/Tirthanand17/taskless-lab/actions/runs/41970364138/artifacts/13389693311",
        "",
        "Technical SHA, FFprobe and captions checks cannot decide factual accuracy, licensing, or visual truth.",
        "Never put credentials, private owner IDs, personal details or signature keys into a public GitHub comment.",
        "",
    ]
    for x in data["episodes"]:
        lines += [
            f"## {x['slot']} — {x['format']} — {x['episode_id']}",
            f"SHA256 MP4: `{x['files']['PREVIEW_UNAPPROVED.mp4']['sha256']}`",
            f"FFprobe: {x['actual_ffprobe']['resolution']}, {x['actual_ffprobe']['duration_seconds']} seconds",
            f"Captions: {x['actual_srt']['caption_cue_count']} checked SRT time ranges",
            "",
            "- [ ] Actually watch/listen to the full MP4, including the final scene",
            "- [ ] Verify narrated wording matches on-screen captions and source-linked facts",
            "- [ ] Independently check each mathematical/scientific claim against NASA/NIST/USGS",
            "- [ ] Inspect every visual animation and thumbnail for misleading claims",
            "- [ ] Check original scripts, Kokoro model/voice terms, fonts, art and music rights",
            "- [ ] Assess uniqueness vs. the channel catalogue and required synthetic-media disclosure",
            "- [ ] Confirm title/description/format and actual schedule slot are appropriate",
            "- [ ] Reject and request changes if any check fails; a box in this public template proves no identity",
            "",
        ]
    lines += [
        "**Current state:** NONE of these reviews have been completed or authenticated.",
        "**YouTube publishing:** DISABLED. No real Google owner OAuth or release authorization.",
        "**Independent uploader:** NOT CONNECTED; do not dispatch the assisted publisher from this unsigned intake.",
        "",
    ]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser(description="B4d3 independent real media review intake, NO UPLOAD")
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=make_owner_review_intake(a.input)
    folder=a.output
    if folder.exists() or folder.is_symlink() or not folder.is_absolute():
        raise ReviewIntakeRejected("Use NEW isolated absolute review output folder")
    folder.mkdir(mode=0o700,parents=True)
    (folder/"UNAPPROVED_INDEPENDENT_REVIEW_INTAKE.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (folder/"UNSIGNED_OWNER_REVIEW_CHECKLIST.md").write_text(
        _review_markdown(result),encoding="utf-8")
    print(json.dumps({
        "status":STATUS,"episode_count":len(result["episodes"]),
        "actual_file_rehash":True,"actual_ffprobe":True,
        "actual_human_review":False,"youtube_uploads":0,
        "release_authorized":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
