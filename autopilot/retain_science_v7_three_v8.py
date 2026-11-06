"""B4e6b: physically render 2 Shorts + LONG with science_v7 action visuals.

Genuine main-only GitHub CPU Kokoro + FFmpeg encoding of EXISTING original
science demos (not current stories): 19 source-action-specific illustrations,
B4e1 native captions/soft sound FX, B4e4a source-locked editorial title grid. No third-party reference
clip, Google channel credentials, expensive cloud, human approval or upload.

For each topic persist a pair of uncaptioned source-storyboard *before/after*
art-comparison stills plus actual decoded final MP4 sampling frames. These
are REVIEW evidence, not automatic artistic quality or rights certification.
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
    STATUS,_topic_png,render_full_topic_video,
)
from autopilot.primary_sourced_storyboards import SLOTS,build_story
from autopilot.retain_public_topic_drafts import _retain_one,PreviewRefused

STATUS_V8="B4E6B_REAL_SCIENCE_V7_TWO_SHORTS_LONG_MEDIA_UNAPPROVED"
SLOT_SEQUENCE=("short_am","long","short_pm")


def _verified_file(path:Path,max_size:int=320_000_000)->dict:
    if path.is_symlink() or not path.is_file():
        raise PreviewRefused("Missing, symlink or invalid source preview")
    length=path.stat().st_size
    if not 1200<=length<=max_size:
        raise PreviewRefused("Unusable or oversized preview bytes")
    h=sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda:stream.read(1024*1024),b""):
            h.update(piece)
    return {"filename":path.name,"sha256":h.hexdigest(),"bytes":length}


def _encoded_frame(video:Path,t:float,out:Path)->dict:
    if not isinstance(t,(int,float)) or not 0.0<t<=320:
        raise PreviewRefused("Unbounded actual video frame review time")
    try:
        subprocess.run([
            "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-ss",f"{t:.2f}","-i",str(video),"-frames:v","1",
            "-y",str(out)
        ],check=True,timeout=45,capture_output=True)
    except (OSError,subprocess.SubprocessError):
        raise PreviewRefused("Actual encoded video screenshot extraction failed") from None
    info=_verified_file(out,12_000_000)
    if info["bytes"]<15000:
        raise PreviewRefused("Tiny or blank actual encoded video frame")
    return {**info,"from_actual_encoded_mp4":True,
            "timestamp_seconds":round(t,2),"human_approved":False}


def _render_art_compare(story:dict,temp:Path,destination:Path)->dict:
    from PIL import Image,ImageDraw,ImageFont,ImageChops
    before=temp/"old-primitive-preview.png"
    after=temp/"new-cinematic-preview.png"
    scene_index={"short_am":2,"long":7,"short_pm":2}[story["slot"]]
    _topic_png(story,scene_index,60,before,visual_style="floating_v6")
    _topic_png(story,scene_index,60,after,visual_style="science_v7")
    with Image.open(before) as a,Image.open(after) as b:
        if a.size!=b.size:
            raise PreviewRefused("Before/after not compared on same native canvas")
        if ImageChops.difference(a.convert("RGB"),b.convert("RGB")).getbbox() is None:
            raise PreviewRefused("Science v7 action image must visibly differ from floating v6")
        # Include identical original-source titles / captions unburned, so the
        # change is only original PIL art instead of a fabricated comparison.
        target=(400,710) if story["format"]=="short" else (560,330)
        a=a.convert("RGB"); b=b.convert("RGB")
        a.thumbnail(target);b.thumbnail(target)
        left=a.copy();right=b.copy()
    W=left.width+right.width+45
    H=max(left.height,right.height)+102
    comparison=Image.new("RGB",(W,H),(7,17,31))
    d=ImageDraw.Draw(comparison)
    font=ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",21)
    d.text((16,17),"BEFORE  /  FLOATING V6",font=font,fill=(210,218,227))
    d.text((left.width+30,17),"AFTER  /  SCIENCE V7",font=font,fill=(111,221,192))
    comparison.paste(left,(12,58))
    comparison.paste(right,(left.width+30,58))
    comparison.save(destination,format="PNG",optimize=True)
    record=_verified_file(destination,14_000_000)
    if record["sha256"] in (sha256(before.read_bytes()).hexdigest(),
                             sha256(after.read_bytes()).hexdigest()):
        raise PreviewRefused("Before after comparison did not actually combine both")
    return {**record,"human_visual_preference_verified":False,
            "before_and_after_are_uncaptioned_same_script_scene":True}


def render_three_science_v7_previews(*,model:Path,voices:Path,output:Path)->dict:
    from kokoro_onnx import Kokoro
    verify_pinned_assets(model,voices)
    output=Path(output)
    if not output.is_absolute() or output.exists() or output.is_symlink():
        raise PreviewRefused("New absolute public-owner-review artifact only")
    engine=Kokoro(str(model),str(voices))
    items=[]
    try:
        with tempfile.TemporaryDirectory(prefix="fm-b4e6b-") as tmp:
            work=Path(tmp)
            staging=work/"science-v7-unapproved"
            staging.mkdir(mode=0o700)
            for slot in SLOT_SEQUENCE:
                story=build_story(slot)
                source=work/f"source-{slot}"
                source.mkdir(mode=0o700)
                report,episode=render_full_topic_video(
                    story,engine,source,visual_style="science_v7")
                if (report.get("status")!=STATUS
                    or report.get("b4e3_visual_style")!="science_v7"
                    or report.get("b4e6_source_action_art_in_actual_encoded_video") is not True
                    or report.get("b4e4_source_exact_nonoverlapping_editorial_grid") is not True
                    or report.get("b4e3_original_dimensional_scenes_encoded") is not True
                    or report.get("b4e3_owner_creative_approval") is not False
                    or report.get("b4e3_real_modelled_3d_claimed") is not False
                    or report.get("b4e1_native_ass_safe_band_independently_verified") is not True
                    or report.get("actual_narration_text_and_srt_matched") is not True
                    or report.get("actual_full_encoded_h264_aac_with_captions_and_animation") is not True
                    or report.get("human_complete_watch_listen") is not False
                    or report.get("youtube_upload_enabled") is not False
                    or report.get("youtube_schedule_enabled") is not False
                    or report.get("release_authorized") is not False):
                    raise PreviewRefused("Actually encoded action-specific scene/voice/media QA missing or forged")
                if episode.episode_id!=story["episode_id"]:
                    raise PreviewRefused("Model changed story source/episode identity")
                final=staging/episode.episode_id
                item=_retain_one(story,report,source/episode.episode_id,final)
                video=final/"PREVIEW_UNAPPROVED.mp4"
                duration=float(report["seconds"])
                at=[4.0,16.0,min(duration*.52,duration-3)]
                if episode.kind=="long":
                    at.extend([min(duration*.78,duration-2)])
                item["actual_mp4_review_frames"]=[
                    _encoded_frame(video,t,final/f"ACTUAL_VIDEO_{j+1:02d}_UNAPPROVED.png")
                    for j,t in enumerate(at)
                ]
                compare=_render_art_compare(story,work,
                    final/"FLOATING_V6_VS_SCIENCE_V7_SOURCE_ART_UNAPPROVED.png")
                item["same_source_before_after_art_proof"]=compare
                item["original_story_visual_scene_count"]=story["scene_count"]
                item["source_action_19_physical_original_compositions"]=True
                item["native_ass_captions_independently_verified"]=True
                item["actual_original_2point5d_composited_into_mp4"]=True
                item["actual_source_action_2point5d_in_full_mp4"]=True
                item["real_modelled_3d_used"]=False
                item["owner_creative_approval"]=False
                items.append(item)
            if ([x["format"] for x in items]!=["short","long","short"]
                or len(set(x["files"][0]["sha256"] for x in items))!=3):
                raise PreviewRefused("Not three distinct full physical demos")
            manifest={
                "schema_version":1,"status":STATUS_V8,
                "source":"THREE_PREVIOUSLY_AUTHORED_NASA_NIST_USGS_DEMOS_NOT_FRESH_DAILY", 
                "source_action_19_science_visual_motifs":True,
                "episodes":items,
                "original_user_reference_clip_copied":False,
                "real_human_watch_listen_or_facts_reviewed":False,
                "voice_music_visual_license_reviewed":False,
                "two_shorts_and_one_long_h264_aac":True,
                "real_youtube_published_videos":0,
                "release_authorized":False,
            }
            (staging/"UNAPPROVED_SCIENCE_V7_THREE_MANIFEST.json").write_text(
                json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf8")
            output.parent.mkdir(parents=True,exist_ok=True)
            staging.rename(output)
            return manifest
    finally:
        close=getattr(getattr(engine,"voices",None),"close",None)
        if callable(close):
            close()


def main()->None:
    args=argparse.ArgumentParser(description="Actual original science_v7 three-video source demo, NO YouTube")
    args.add_argument("--model",type=Path,required=True)
    args.add_argument("--voices",type=Path,required=True)
    args.add_argument("--output",type=Path,required=True)
    a=args.parse_args()
    report=render_three_science_v7_previews(model=a.model,voices=a.voices,output=a.output)
    print(json.dumps({"status":STATUS_V8,"videos":len(report["episodes"]),
                      "real_youtube_uploads":0,"creative_human_approved":False}))


if __name__=="__main__":
    main()
