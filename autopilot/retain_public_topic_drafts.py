"""B4d2: render three existing original-topic drafts into a GitHub review artifact.

This is a REAL standalone, CPU/FFmpeg/Kokoro technical production adapter,
not a simulated upload. It retains ONLY unapproved media intended for a public
repository review, never the downloaded model, voice weights, source bodies,
owner identity, credentials or approval signatures. Do not use for confidential
scripts or unreleased licensed assets.

Must only be run by a read-only, owner-controlled main-branch GitHub Actions
workflow. This program never contacts YouTube, Google or paid clouds, and
never authorizes any publisher. A review artifact is not a finished upload.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import shutil
import stat
import tempfile

from autopilot.full_topic_narrated_pack import (
    STATUS, TopicRenderError, render_full_topic_video,
)
from autopilot.primary_sourced_storyboards import build_story
from autopilot.signed_narrated_cloud_pack import verify_pinned_assets

SLOTS = ("short_am","long","short_pm")
SOURCE_MEDIA = {
    "PREVIEW_UNAPPROVED.mp4":"UNAPPROVED_FULL_EDUCATION_TEST.mp4",
    "CAPTIONS_UNAPPROVED.srt":"scene_captions.srt",
    "THUMBNAIL_UNAPPROVED.png":"UNAPPROVED_THUMBNAIL_TEST.png",
}
MAX_MP4_BYTES = 300_000_000
MAX_SRT_BYTES = 200_000
MAX_PNG_BYTES = 18_000_000
STATUS_RETAINED="PUBLIC_REVIEW_DRAFT_MEDIA_RETAINED_NOT_RELEASE_APPROVED"


class PreviewRefused(ValueError):
    """Do not retain a changed, unreviewed or incomplete video pack."""


def _hash_file(path: Path,limit: int) -> tuple[str,int]:
    if (path.is_symlink() or not path.is_file()
            or not stat.S_ISREG(path.stat().st_mode)):
        raise PreviewRefused("Missing or nonregular draft media input")
    h=hashlib.sha256()
    total=0
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            total+=len(chunk)
            if total>limit:
                raise PreviewRefused("Draft media exceeds public artifact budget")
            h.update(chunk)
    if total<20:
        raise PreviewRefused("Unusable tiny draft media")
    return h.hexdigest(),total


def _require_true_technical_report(story: dict, report: dict) -> None:
    """Technical authenticity is not an editorial approval or upload grant."""
    if (type(story) is not dict or type(report) is not dict
        or report.get("status")!=STATUS
        or report.get("episode")!=story.get("episode_id")
        or report.get("original_source_story_draft_sha256")!=story.get("draft_sha256")
        or report.get("original_research_topics")!=story.get("theme")
        or report.get("actual_full_encoded_h264_aac_with_captions_and_animation") is not True
        or report.get("actual_narration_text_and_srt_matched") is not True
        or report.get("original_svg_frames_really_animated") is not True
        or report.get("human_complete_watch_listen") is not False
        or report.get("human_original_visual_semantics_review") is not False
        or report.get("independently_verified_model_voice_music_rights") is not False
        or report.get("live_primary_sources_human_claim_reviewed") is not False
        or report.get("provider_live_api_called") is not False
        or report.get("youtube_upload_enabled") is not False
        or report.get("youtube_schedule_enabled") is not False
        or report.get("release_authorized") is not False):
        raise PreviewRefused("Cannot retain changed/approved/incomplete technical draft")
    if (type(report.get("video_sha256")) is not str
        or len(report["video_sha256"])!=64
        or type(report.get("original_unreviewed_thumbnail_sha256")) is not str
        or len(report["original_unreviewed_thumbnail_sha256"])!=64):
        raise PreviewRefused("Missing technical MP4/thumbnail digests")


def _retain_one(story: dict,report: dict,source:Path,destination:Path) -> dict:
    """Copy only MP4, SRT and thumbnail from verified original AV outputs."""
    _require_true_technical_report(story,report)
    if source.name!=story["episode_id"] or not source.is_dir() or source.is_symlink():
        raise PreviewRefused("Source is not exact original draft episode")
    if destination.exists() or destination.is_symlink():
        raise PreviewRefused("Refusing to overwrite any preexisting review artifact")
    destination.mkdir(mode=0o700)
    files=[]
    for outfile,infile in SOURCE_MEDIA.items():
        origin=source/infile
        limit=(MAX_MP4_BYTES if outfile.endswith(".mp4")
               else MAX_PNG_BYTES if outfile.endswith(".png") else MAX_SRT_BYTES)
        digest,size=_hash_file(origin,limit)
        if outfile.endswith(".mp4") and digest!=report["video_sha256"]:
            raise PreviewRefused("Original encoded MP4 changed after QA")
        if outfile.endswith(".png") and digest!=report["original_unreviewed_thumbnail_sha256"]:
            raise PreviewRefused("Original illustration/thumbnail changed after QA")
        target=destination/outfile
        with origin.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src,dst,1024*1024)
        digest_after,size_after=_hash_file(target,limit)
        if (digest,size)!=(digest_after,size_after):
            raise PreviewRefused("Post-copy media no longer matches original hashes")
        files.append({"filename":outfile,"sha256":digest,"bytes":size})
    return {
        "slot":story["slot"],
        "format":story["format"],
        "episode_id":story["episode_id"],
        "source_draft_sha256":story["draft_sha256"],
        "source_claims_human_fact_verified":False,
        "owner_full_watch_completed":False,
        "media_and_voice_rights_approved":False,
        "technical_full_video_decode_passed":True,
        "technical_spoken_srt_and_scene_checks_passed":True,
        "files":files,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


def render_retain_public_three(
    *, model:Path,voices:Path,output:Path
) -> dict:
    """Real 3-video generation; artifact folder persists until workflow cleanup.

    Only the developer-authored, fixed NASA/NIST/USGS storyboards in this PUBLIC
    repository are supported. The output can be downloaded by public visitors.
    """
    # Exact source model weights and voice bytes must match pinned SHA256.
    verify_pinned_assets(model,voices)
    from kokoro_onnx import Kokoro
    output=Path(output)
    if output.exists() or output.is_symlink() or not output.is_absolute():
        raise PreviewRefused("Require NEW absolute GitHub runner artifact folder")
    result=[]
    engine=Kokoro(str(model),str(voices))
    try:
        with tempfile.TemporaryDirectory(prefix="flowminute-b4d2-") as tempdir:
            staging=Path(tempdir)/"staging"
            staging.mkdir(mode=0o700)
            for slot in SLOTS:
                story=build_story(slot)
                with tempfile.TemporaryDirectory(prefix="flowminute-b4d2-render-") as episode_tmp:
                    empty=Path(episode_tmp)/"working"
                    empty.mkdir(mode=0o700)
                    report,episode=render_full_topic_video(story,engine,empty)
                    if episode.episode_id!=story["episode_id"]:
                        raise PreviewRefused("Actual renderer changed episode ID")
                    result.append(_retain_one(
                        story,report,empty/episode.episode_id,
                        staging/episode.episode_id,
                    ))
            if (len(result)!=3 or len({x["episode_id"] for x in result})!=3
                or len({x["source_draft_sha256"] for x in result})!=3
                or len({x["files"][0]["sha256"] for x in result})!=3
                or [x["format"] for x in result]!=["short","long","short"]
                or sum(x["files"][0]["bytes"] for x in result)>600_000_000):
                raise PreviewRefused("Incomplete or oversized distinct three-video draft pack")
            manifest={
                "schema_version":1,
                "status":STATUS_RETAINED,
                "artifact_scope":"PUBLIC_GITHUB_ACTIONS_EPHEMERAL_REVIEW_ONLY",
                "source":"THREE_FIXED_20261104_ORIGINAL_TOPIC_DEMOS_NOT_DAILY_FRESH_EPISODES",
                "technical_original_mp4_captions_thumbnail_count":len(result),
                "episodes":result,
                "contains_public_original_source_demo_material_only":True,
                "original_voice_model_file_weights_archived":False,
                "real_rights_or_editorial_approval":False,
                "actual_live_youtube_uploads":0,
                "release_authorized":False,
            }
            final=staging/"UNAPPROVED_PUBLIC_REVIEW_MANIFEST.json"
            final.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
            output.parent.mkdir(parents=True,exist_ok=True)
            staging.rename(output)
            return manifest
    finally:
        close=getattr(getattr(engine,"voices",None),"close",None)
        if callable(close):
            close()


def main():
    cli=argparse.ArgumentParser(description="Retain public UNAPPROVED original-media demo previews only")
    cli.add_argument("--model",type=Path,required=True)
    cli.add_argument("--voices",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args()
    m=render_retain_public_three(model=args.model,voices=args.voices,output=args.output)
    print(json.dumps({
        "status":m["status"],"count":len(m["episodes"]),
        "file_count":sum(len(x["files"]) for x in m["episodes"]),
        "release_authorized":False,"youtube_uploaded":0,
    }))


if __name__=="__main__":
    main()
