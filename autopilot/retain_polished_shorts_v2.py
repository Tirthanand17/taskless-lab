"""B4e1 render TWO original (not daily-fresh) polished Shorts for owner critique.

True Kokoro PCM voice, original source-linked SVG, pixel-native v2 ASS cards,
fixed topic 2.5D thumbnail, original bounded UI effects and full FFmpeg decode.
Only after main-branch source merge. No actual YouTube/video scheduler,
external model calls, owner OAuth, human fact/rights approval or private media.

This is a technical iteration, not a claim of high subjective quality.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from autopilot.cloud_av_probe import verify_pinned_assets
from autopilot.full_topic_narrated_pack import (
    STATUS,render_full_topic_video,
)
from autopilot.primary_sourced_storyboards import build_story
from autopilot.retain_public_topic_drafts import _retain_one,PreviewRefused

STATUS_V2="B4E1_TWO_REAL_POLISHED_SHORTS_UNAPPROVED_REVIEW_ONLY"
SLOTS=("short_am","short_pm")


def _screenshot(path:Path,at_seconds:int,out:Path)->dict:
    if at_seconds not in (4,16):
        raise PreviewRefused("Unexpected inspection time")
    try:
        subprocess.run([
            "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-ss",str(at_seconds),"-i",str(path),
            "-frames:v","1","-y",str(out)
        ],check=True,timeout=35,capture_output=True)
    except (OSError,subprocess.SubprocessError):
        raise PreviewRefused("Real FFmpeg caption frame screenshot failed") from None
    if not out.is_file() or out.stat().st_size<20000:
        raise PreviewRefused("Empty visual review sample")
    return {
        "filename":out.name,
        "sha256":sha256(out.read_bytes()).hexdigest(),
        "bytes":out.stat().st_size,
        "at_seconds":at_seconds,
        "human_visual_approval":False,
    }


def render_polished_two(*,model:Path,voices:Path,output:Path)->dict:
    verify_pinned_assets(model,voices)
    from kokoro_onnx import Kokoro
    output=Path(output)
    if not output.is_absolute() or output.exists() or output.is_symlink():
        raise PreviewRefused("Need NEW absolute owner public review output path")
    engine=Kokoro(str(model),str(voices))
    entries=[]
    with tempfile.TemporaryDirectory(prefix="fm-b4e1-two-short-") as temporary:
        root=Path(temporary)
        staging=root/"public-review"
        staging.mkdir(mode=0o700)
        for slot in SLOTS:
            story=build_story(slot)
            render_root=root/("render-"+slot)
            render_root.mkdir(mode=0o700)
            report,episode=render_full_topic_video(story,engine,render_root)
            if (report.get("status")!=STATUS
                or report.get("original_ui_sound_effects_count")!=5
                or report.get("original_ui_sounds_not_external_recordings") is not True
                or report.get("youtube_upload_enabled") is not False
                or report.get("youtube_schedule_enabled") is not False
                or report.get("release_authorized") is not False
                or report.get("human_complete_watch_listen") is not False
                or episode.kind!="short"):
                raise PreviewRefused("Wrong source, audio effects, format or synthetic approval")
            entry=_retain_one(
                story,report,render_root/episode.episode_id,
                staging/episode.episode_id,
            )
            dest=staging/episode.episode_id
            video=dest/"PREVIEW_UNAPPROVED.mp4"
            entry["visual_review_frames"]=[
                _screenshot(video,t,dest/f"FRAME_{t:02d}s_UNAPPROVED.png")
                for t in (4,16)
            ]
            entry["original_technical_scene_ui_effects_count"]=5
            entry["explicit_native_resolution_ass_microcaptions_expected"]=True
            entry["existing_human_reviewer_approval"]=False
            entries.append(entry)
        if [x["format"] for x in entries]!=["short","short"]:
            raise PreviewRefused("Not exactly two original source Shorts")
        if len({x["files"][0]["sha256"] for x in entries})!=2:
            raise PreviewRefused("Duplicate source short media")
        manifest={
            "schema_version":1,
            "status":STATUS_V2,
            "source":"FIXED_ORIGINAL_SCIENCE_DEMOS_NOT_NEW_DAILY_CONTENT",
            "videos":entries,
            "original_reference_audio_or_graphics_imported":False,
            "real_owner_full_watch_listen_and_claim_review":False,
            "real_voice_model_sound_font_graphics_rights_cleared":False,
            "real_youtube_uploads":0,
            "release_authorized":False,
        }
        (staging/"UNAPPROVED_B4E1_POLISHED_TWO_SHORTS_MANIFEST.json").write_text(
            json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
        output.parent.mkdir(parents=True,exist_ok=True)
        staging.rename(output)
        return manifest


def main()->None:
    p=argparse.ArgumentParser(description="B4e1 real original polished preview; no upload")
    p.add_argument("--model",type=Path,required=True)
    p.add_argument("--voices",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    m=render_polished_two(model=a.model,voices=a.voices,output=a.output)
    print(json.dumps({
        "status":STATUS_V2,"real_h264_aac_shorts":len(m["videos"]),
        "actual_reference_recording_copied":False,
        "real_human_approved":False,"actual_youtube_uploads":0,
    }))


if __name__=="__main__":
    main()
