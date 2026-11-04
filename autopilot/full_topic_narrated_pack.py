"""B3d4c2c3b: genuinely TOPIC-SPECIFIC narrated original educational DEMOS.

Uses exact source-linked original NASA/NIST/USGS scripts from PR #30, original
moving SVG graphics, pinned public Kokoro model on GitHub-hosted CPU,
existing measured-PCM narration/SRT, optional original programmatic ambient,
full FFmpeg H264/AAC and independently executed FFprobe/full decode plus
caption/visual technical review. NO external model provider or YouTube client.

The educational drafts have not received actual external human claim,
copyright/voice, exact final watch/listen or channel owner approval. No files
are persisted: the hosted workflow holds outputs only in TemporaryDirectory.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json
import math
import re
import stat
from typing import Callable
from xml.etree import ElementTree as ET

from autopilot.cloud_av_probe import sha256_stream, verify_pinned_assets
from autopilot.cloud_full_duration_pack import (
    FPS, narration_and_srt, sentence_chunks, run, validate_cues,
)
from autopilot.full_pack_fixture import ExampleEpisode, Scene
from autopilot.independent_av_review import review_encoded_episode
from autopilot.primary_sourced_storyboards import (
    build_story, canonical, render_original_svg, require_exact_draft,
    evaluate_three_draft_stories, StoryboardError,
)
from autopilot.signed_narrated_cloud_pack import VOICE_FOR_SLOT, inspect_dynamic_media

STATUS = "THREE_SOURCE_LINKED_FULL_KOKORO_H264_DRAFTS_TECHNICALLY_RENDERED_UNREVIEWED"
FRAMES_PER_SCENE = 5
MAX_FULL_OUTPUT_BYTES = 300_000_000
MAX_PNG_BYTES = 18_000_000
MAX_WAV_BYTES = 100_000_000
REQUIRED_FALSE = (
    "real_primary_source_live_rechecked_by_runner",
    "independent_claim_by_claim_human_review_passed",
    "actual_content_originality_human_reviewed",
    "voice_music_image_rights_approved",
    "human_full_watch_listen_completed",
    "real_provider_generated_script",
    "private_media_and_editorial_receipts_deployed",
    "actual_video_rendered_for_this_story",
    "youtube_upload_enabled",
    "release_authorized",
)


class TopicRenderError(ValueError):
    """No release on a changed storyboard, missing voice or broken media."""


def episode_from_research_story(story: dict) -> ExampleEpisode:
    require_exact_draft(story)
    if any(story.get(key) is not False for key in REQUIRED_FALSE):
        raise TopicRenderError("Source-linked draft impersonates approved production")
    slot=story["slot"]
    kind=story["format"]
    if story["scene_count"]>24 or story["scene_count"]!=len(story["scenes"]):
        raise TopicRenderError("Topic scene count is not bounded")
    scenes=[]
    for index,row in enumerate(story["scenes"]):
        if row["scene_id"]!=f"{slot}_beat_{index+1:02d}":
            raise TopicRenderError("Altered original narration scene identity")
        for phrase in sentence_chunks(row["narration"]):
            if len(phrase)>235:
                raise TopicRenderError("Source narration cue over voice limits")
        scenes.append(Scene(
            title=row["display_title"],
            narration=row["narration"],
            mode="workflow",
        ))
    return ExampleEpisode(
        episode_id=story["episode_id"],
        kind=kind,
        voice=VOICE_FOR_SLOT[slot],
        theme=story["theme"],
        scenes=tuple(scenes),
    )


def variable_frame_concat_lines(
    story: dict,timings: list[dict],paths: list[list[Path]],
    *,scene_index_dir: Path,
) -> tuple[str,str]:
    """Precise existing PCM voice scene timings; 5 moving SVG samples per beat.

    Return separate per-SCENE and per-FRAME ffconcat content. The independent
    AV reviewer consumes per-scene start positions, while actual encoder
    consumes every moving SVG sampled frame over exactly the same duration.
    """
    require_exact_draft(story)
    if len(timings)!=story["scene_count"] or len(paths)!=story["scene_count"]:
        raise TopicRenderError("Visual motion timeline differs from actual voice")
    scene_lines=["ffconcat version 1.0"]
    frame_lines=["ffconcat version 1.0"]
    seen=set()
    previous_end=0.0
    for i,(row,parts) in enumerate(zip(timings,paths)):
        duration=row.get("duration")
        start=row.get("start")
        if (
            type(duration) not in (float,int)
            or type(start) not in (float,int)
            or not math.isfinite(duration) or not math.isfinite(start)
            or not 1.0<=duration<=40.0 or abs(start-previous_end)>.002
            or not isinstance(parts,list) or len(parts)!=FRAMES_PER_SCENE
        ):
            raise TopicRenderError("Missing, inconsistent or impossible voice/image timing")
        previous_end=start+duration
        first=parts[0]
        if first.parent!=scene_index_dir:
            raise TopicRenderError("Moving frame outside its ephemeral folder")
        for j,part in enumerate(parts):
            if part in seen or part.parent!=scene_index_dir or part.suffix!=".png":
                raise TopicRenderError("Repeated/foreign SVG frame in motion timeline")
            expected=f"moving_{i+1:02d}_{j:02d}.png"
            if part.name!=expected or "'" in str(part):
                raise TopicRenderError("Unsafe or reordered original motion frame")
            seen.add(part)
            frame_lines.extend([f"file '{part.as_posix()}'",f"duration {duration/FRAMES_PER_SCENE:.7f}"])
        scene_lines.extend([
            f"file '{first.as_posix()}'",
            f"duration {duration:.7f}",
        ])
    if len(seen)!=story["scene_count"]*FRAMES_PER_SCENE:
        raise TopicRenderError("Missing moving original assets")
    frame_lines.append(f"file '{paths[-1][-1].as_posix()}'")
    scene_lines.append(f"file '{paths[-1][0].as_posix()}'")
    return "\n".join(scene_lines)+"\n","\n".join(frame_lines)+"\n"


def original_ambient_tone(wav: Path, theme: str) -> str:
    """Low-level nonmusical mathematically generated bed, no copied recording.

    This adds no external music sample, no melodic composition, no user speech
    impersonation, and DOES NOT approve actual voice/model licensing.
    """
    import numpy as np
    import soundfile as sf
    if theme not in ("lunar_signal","quake_energy","file_transfer"):
        raise TopicRenderError("No original thematic tone recipe")
    if wav.is_symlink() or not wav.is_file():
        raise TopicRenderError("Missing measured speech")
    data,rate=sf.read(str(wav),dtype="float32",always_2d=False)
    if data.ndim!=1 or data.size<rate*18 or rate not in (22050,24000,44100,48000):
        raise TopicRenderError("Unexpected original mono narration wave")
    if not np.isfinite(data).all():
        raise TopicRenderError("Nonfinite narration samples")
    freq={"lunar_signal":78.0,"quake_energy":66.0,"file_transfer":104.0}[theme]
    seconds=np.arange(data.size,dtype=np.float64)/rate
    fade=np.minimum(1.0,np.minimum(seconds,(data.size-1)/rate-seconds)/.65).clip(0.0,1.0)
    slow=(.5+.5*np.sin(2*np.pi*.13*seconds))
    bed=(.0027*np.sin(2*np.pi*freq*seconds)+
         .0014*np.sin(2*np.pi*(freq*1.5)*seconds))*fade*slow
    result=np.clip(data+bed,-.995,.995).astype(np.float32)
    sf.write(str(wav),result,rate,subtype="PCM_16")
    return sha256(
        canonical({"recipe":"two_original_inaudible_intent_ambient_sines_v1",
                   "theme":theme,"f":freq,"sample_count":data.size,"rate":rate})
    ).hexdigest()


def _topic_thumbnail(story: dict,output: Path) -> str:
    from PIL import Image, ImageDraw, ImageFont
    palette={
        "lunar_signal":((10,24,50),(68,196,241)),
        "file_transfer":((10,31,42),(99,224,182)),
        "quake_energy":((50,24,28),(255,162,98)),
    }
    bg,accent=palette[story["theme"]]
    im=Image.new("RGB",(1280,720),bg)
    d=ImageDraw.Draw(im)
    try:
        main=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",61)
        detail=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",37)
    except OSError as exc:
        raise TopicRenderError("Hosted DejaVu fonts are required for original title artwork") from exc
    d.rounded_rectangle((36,32,1244,688),radius=28,outline=accent,width=7)
    d.text((78,89),"FLOWMINUTE • ORIGINAL EDUCATION DRAFT",font=detail,fill=accent)
    if story["theme"]=="lunar_signal":
        main_lines=("MOON SIGNAL DELAY","1.28 SECONDS ONE WAY")
    elif story["theme"]=="file_transfer":
        main_lines=("MEGABITS ≠ MEGABYTES","40 s versus 41.94 s")
    else:
        main_lines=("EARTHQUAKE ENERGY","+1 MAGNITUDE ≈ 32×")
    for i,line in enumerate(main_lines):
        d.text((78,211+i*115),line,font=main,fill=(240,245,252) if i==0 else accent)
    d.text((78,568),"UNAPPROVED · HUMAN FACT / RIGHTS REVIEW PENDING",
           font=detail,fill=(225,229,237))
    d.line((76,655,1205,655),fill=accent,width=5)
    im.save(output,format="PNG")
    return sha256(output.read_bytes()).hexdigest()


def visible_topic_motion_pulse(story: dict, tick: int) -> tuple[int,int]:
    """Five guaranteed distinct original motion positions ABOVE caption panel.

    Some long 20-scene source SVG progress elements sit behind caption-safe
    overlay; a visible topic-tinted moving signal/packet/energy indicator
    ensures no underlying source animation is silently obscured or repeated.
    """
    require_exact_draft(story)
    if type(tick) is not int or not 0<=tick<=120:
        raise TopicRenderError("Moving original visual tick outside bounds")
    w,h=(1080,1920) if story["format"]=="short" else (1920,1080)
    return round(90+(w-180)*tick/120),round(h*(.66 if story["format"]=="short" else .62))


def _topic_png(story: dict,idx: int,tick: int,output: Path) -> str:
    import cairosvg
    from PIL import Image,ImageDraw
    svg=render_original_svg(story,idx,tick)
    ET.fromstring(svg)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"),write_to=str(output))
    expected=(1080,1920) if story["format"]=="short" else (1920,1080)
    with Image.open(output) as im:
        im.load()
        if im.size!=expected:
            raise TopicRenderError("Wrong original full-scene vector dimensions")
        rgb=im.convert("RGB")
    # A fixed dark, consistently safe caption strip in each source frame.
    # Burned captions are added later by FFmpeg and checked independently.
    d=ImageDraw.Draw(rgb)
    x,y=visible_topic_motion_pulse(story,tick)
    accent={
        "lunar_signal":(80,200,238),
        "file_transfer":(111,222,188),
        "quake_energy":(248,158,99),
    }[story["theme"]]
    # Original moving signal/packet/energy node lives in the main visible
    # field, never under the opaque subtitle panel at the bottom.
    w,h=rgb.size
    d.line((90,y,w-90,y),fill=accent,width=5)
    d.ellipse((x-20,y-20,x+20,y+20),fill=(246,248,254),
              outline=accent,width=7)
    d.ellipse((x-8,y-8,x+8,y+8),fill=accent)
    bottom=380 if story["format"]=="short" else 265
    d.rounded_rectangle((56,expected[1]-bottom,
                         expected[0]-56,expected[1]-46),
                        radius=18,fill=(10,18,30),outline=(80,117,145),width=3)
    rgb.save(output,format="PNG")
    digest,size=sha256_stream(output,max_bytes=MAX_PNG_BYTES)
    if size<1500:
        raise TopicRenderError("Blank or empty original SVG-produced frame")
    return digest


def _encode_moving_topic(
    episode: ExampleEpisode,folder: Path,timings: list[dict],
    wav: Path,srt: Path,total: float,
) -> Path:
    from PIL import Image,ImageDraw
    if not 24<=total<=360 or not timings:
        raise TopicRenderError("Unbounded or wrong full narration duration")
    dot=Image.new("RGBA",(82,14),(0,0,0,0))
    ImageDraw.Draw(dot).rounded_rectangle((0,0,81,13),radius=6,fill=(90,220,175,255))
    dot_path=folder/"moving_progress.png"
    dot.save(dot_path)
    margin=24 if episode.kind=="short" else 31
    fontsize=23 if episode.kind=="short" else 21
    subtitle=(
        f"subtitles={srt.as_posix()}:"
        "force_style='FontName=DejaVu Sans,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        f"Outline=2,FontSize={fontsize},Alignment=2,MarginV={margin}'"
    )
    filters=(
        f"[0:v]fps={FPS},{subtitle},format=yuv420p[base];"
        f"[base][2:v]overlay=x='max(0,min(W-w,(W-w)*t/{total:.4f}))':"
        "y=H-h-38:shortest=1,format=yuv420p[v]"
    )
    out=folder/"UNAPPROVED_FULL_EDUCATION_TEST.mp4"
    run([
        "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
        "-f","concat","-safe","0",
        "-i",str(folder/"animated_frames.ffconcat"),
        "-i",str(wav),
        "-loop","1","-framerate",str(FPS),"-i",str(dot_path),
        "-filter_complex",filters,
        "-map","[v]","-map","1:a:0",
        "-c:v","libx264","-preset","ultrafast","-crf","30",
        "-pix_fmt","yuv420p","-threads","2",
        "-af","loudnorm=I=-16:LRA=9:TP=-2,alimiter=limit=0.50:level=0",
        "-c:a","aac","-b:a","128k",
        "-t",f"{total:.4f}","-movflags","+faststart",
        "-y",str(out),
    ],timeout=1600)
    return out


def _exact_assets(folder: Path,story: dict,report: dict) -> dict:
    """Re-check all actual audio/SRT/MP4/thumb/moving SVG scene bytes."""
    expected={
        "original_voice.wav","scene_captions.srt",
        "UNAPPROVED_FULL_EDUCATION_TEST.mp4",
        "UNAPPROVED_THUMBNAIL_TEST.png",
        "scene_order.ffconcat","animated_frames.ffconcat",
        "moving_progress.png",
    }
    for i in range(story["scene_count"]):
        expected.add(f"scene_{i+1:02d}.png")
        for j in range(FRAMES_PER_SCENE):
            expected.add(f"moving_{i+1:02d}_{j:02d}.png")
    if folder.is_symlink() or not folder.is_dir() or {x.name for x in folder.iterdir()}!=expected:
        raise TopicRenderError("Unexpected unreviewed media output files")
    records=[]
    for name in sorted(expected):
        path=folder/name
        if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise TopicRenderError("Not a real owned-media file")
        limit=(MAX_FULL_OUTPUT_BYTES if name.endswith(".mp4")
               else MAX_WAV_BYTES if name.endswith(".wav")
               else 18_000_000 if name.endswith(".png") else 200_000)
        digest,size=sha256_stream(path,max_bytes=limit)
        if size<20:
            raise TopicRenderError("Empty original visual/audio proof file")
        records.append({"name":name,"sha256":digest,"bytes":size})
    mp4=next(r for r in records if r["name"]=="UNAPPROVED_FULL_EDUCATION_TEST.mp4")
    thumb=next(r for r in records if r["name"]=="UNAPPROVED_THUMBNAIL_TEST.png")
    if (mp4["sha256"]!=report["video_sha256"]
            or mp4["bytes"]!=report["mp4_bytes"]
            or thumb["sha256"]!=report["original_unreviewed_thumbnail_sha256"]):
        raise TopicRenderError("Actual physical bytes changed after technical render")
    strict={
        "status":STATUS,
        "episode_id":story["episode_id"],
        "source_draft_sha256":story["draft_sha256"],
        "primary_source_ids":sorted(story["primary_sources"]),
        "format":story["format"],
        "theme":story["theme"],
        "exact_file_hashes_and_sizes":records,
        "asset_count":len(records),
        "all_original_video_audio_subtitle_thumb_and_scene_bytes_hashed":True,
        "real_source_claim_sufficiency_independently_verified":False,
        "voice_and_model_redistribution_or_use_rights_independently_verified":False,
        "complete_audio_video_human_playback_approved":False,
        "final_asset_publishable":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    return {**strict,"draft_asset_inventory_sha256":sha256(canonical(strict)).hexdigest()}


def prepare_story_timing(story: dict) -> dict:
    """Safe no-network preflight: all narration cues individually TTS-ready."""
    episode=episode_from_research_story(story)
    cue_lengths=[len(sentence_chunks(scene.narration)) for scene in episode.scenes]
    if sum(cue_lengths)<8 or max(cue_lengths)>5:
        raise TopicRenderError("Spoken source story too sparse/dense for timed captions")
    return {
        "episode_id":episode.episode_id,
        "voice":episode.voice,
        "scene_count":len(episode.scenes),
        "caption_chunk_count":sum(cue_lengths),
        "all_text_exactly_from_source_recomputed_draft":True,
        "source_human_fact_review_verified":False,
        "tts_output_or_video_generated":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


def render_full_topic_video(
    story: dict, voice_engine, root: Path,
) -> tuple[dict,ExampleEpisode]:
    """Actual ephemeral full narration/animated render, no release authority."""
    episode=episode_from_research_story(story)
    root=Path(root)
    if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise TopicRenderError("Need empty pre-created protected ephemeral output root")
    folder=root/episode.episode_id
    folder.mkdir(mode=0o700)
    wav,srt,timings,cues,total,tts_seconds=narration_and_srt(
        voice_engine,episode,folder,
    )
    if abs(total-sum(x["duration"] for x in timings))>.005:
        raise TopicRenderError("Audio start/scene timestamps inconsistent")
    if not (28<=total<=110 if episode.kind=="short" else 90<=total<=320):
        raise TopicRenderError("Real generated speech outside intended Short/long bounds")
    original_tone_sha=original_ambient_tone(wav,story["theme"])
    frame_groups=[]
    frames=[]
    all_motion_hashes=[]
    for i in range(story["scene_count"]):
        group=[]
        for j in range(FRAMES_PER_SCENE):
            path=folder/f"moving_{i+1:02d}_{j:02d}.png"
            digest=_topic_png(story,i,j*24,path)
            group.append(path)
            all_motion_hashes.append(digest)
        frame_groups.append(group)
        original=folder/f"scene_{i+1:02d}.png"
        # Independent full-scene proof is physically the same exact visual
        # drawing as the first animated sample, not a generic CSV frame.
        original.write_bytes(group[0].read_bytes())
        frames.append(original)
    if len(set(all_motion_hashes))!=len(all_motion_hashes):
        raise TopicRenderError("Moving topic animation contains duplicate image frames")
    scene_timeline,actual_motion=variable_frame_concat_lines(
        story,timings,frame_groups,scene_index_dir=folder,
    )
    (folder/"scene_order.ffconcat").write_text(scene_timeline,encoding="utf-8")
    (folder/"animated_frames.ffconcat").write_text(actual_motion,encoding="utf-8")
    thumbnail_sha=_topic_thumbnail(story,folder/"UNAPPROVED_THUMBNAIL_TEST.png")
    output=_encode_moving_topic(episode,folder,timings,wav,srt,total)
    report=inspect_dynamic_media(
        folder,episode,tuple(x["scene_id"] for x in story["scenes"]),
        total,cues,frames,
    )
    if report["narration_cues"]!=sum(
        len(sentence_chunks(x["narration"])) for x in story["scenes"]
    ):
        raise TopicRenderError("Spoken cue count differs from original research script")
    report.update({
        "status":STATUS,
        "original_source_story_draft_sha256":story["draft_sha256"],
        "original_research_topics":story["theme"],
        "original_source_ids":sorted(story["primary_sources"]),
        "original_animated_svg_frame_count":len(all_motion_hashes),
        "original_svg_frames_really_animated":True,
        "original_programmatic_low_level_ambient_sha256":original_tone_sha,
        "external_music_tracks_used":False,
        "original_unreviewed_thumbnail_sha256":thumbnail_sha,
        "live_primary_sources_human_claim_reviewed":False,
        "independently_verified_model_voice_music_rights":False,
        "originality_vs_real_channel_catalogue_approved":False,
        "human_complete_watch_listen":False,
        "human_original_visual_semantics_review":False,
        "private_media_vault_connected":False,
        "provider_live_api_called":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
        "tts_generation_elapsed_s":tts_seconds,
    })
    # Independent complete WAV/SRT/video/graphics evidence before reviewer
    # writes ffmpeg diagnostic snapshot files beside these original assets.
    inventory=_exact_assets(folder,story,report)
    if inventory["asset_count"]!=7+story["scene_count"]*(FRAMES_PER_SCENE+1):
        raise TopicRenderError("Untracked original animated frames")
    # Independent external FFmpeg audio/pixel reviewer exercises actual
    # finished MP4, real burned captions, voice loudness and later scenes.
    observed=review_encoded_episode(
        folder,episode,
        report_entry={"episode":episode.episode_id,"seconds":report["seconds"]},
    )
    if (
        observed["burned_caption_independently_observed"] is not True
        or observed["distinct_encoded_scenes_observed"] is not True
        or observed["every_caption_matches_original_spoken_text"] is not True
        or observed["independent_claim_or_rights_review_complete"] is not False
    ):
        raise TopicRenderError("Actual final video caption/pixel/audio technical QA incomplete")
    report.update({
        "exact_original_media_inventory_sha256":inventory["draft_asset_inventory_sha256"],
        "exact_original_asset_count":inventory["asset_count"],
        "actual_ffmpeg_caption_changed_pixels":observed["caption_visible_changed_pixels"],
        "actual_ffmpeg_scene_changed_pixels":observed["first_to_later_scene_changed_pixels"],
        "actual_audio_lufs":observed["ffmpeg_actual_encoded_audio"]["integrated_lufs"],
        "actual_audio_peak_dbtp":observed["ffmpeg_actual_encoded_audio"]["true_peak_dbtp"],
        "actual_narration_text_and_srt_matched":True,
        "actual_full_encoded_h264_aac_with_captions_and_animation":True,
    })
    return report,episode


def cloud_full_three_topic_narrated_smoke(model:Path,voices:Path) -> dict:
    from tempfile import TemporaryDirectory
    from kokoro_onnx import Kokoro
    assets=verify_pinned_assets(model,voices)
    engine=Kokoro(str(model),str(voices))
    plans=evaluate_three_draft_stories()
    episode_reports=[]
    try:
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            prepare_story_timing(story)
            # One new ephemeral directory per video; all raw bytes deleted
            # after each iteration, even when a source claim gate fails.
            with TemporaryDirectory(prefix="flowminute-b3d4c2c3b-") as directory:
                report,episode=render_full_topic_video(
                    story,engine,Path(directory),
                )
                if report["release_authorized"] is not False:
                    raise TopicRenderError("Technical test cannot approve content")
                episode_reports.append(report)
                print("B3D4C2C3B_ONE_REAL_ORIGINAL_NARRATED_DRAFT",
                      json.dumps(report,sort_keys=True),flush=True)
    finally:
        close=getattr(getattr(engine,"voices",None),"close",None)
        if callable(close):
            close()
    if (
        len(episode_reports)!=3
        or len({x["video_sha256"] for x in episode_reports})!=3
        or len({x["original_unreviewed_thumbnail_sha256"] for x in episode_reports})!=3
        or len({x["exact_original_media_inventory_sha256"] for x in episode_reports})!=3
        or len({x["original_research_topics"] for x in episode_reports})!=3
        or set(x["voice"] for x in episode_reports)!=set(VOICE_FOR_SLOT.values())
    ):
        raise TopicRenderError("Three different physically narrated education drafts not produced")
    return {
        "status":STATUS,
        "episode_reports":episode_reports,
        "three_full_narrated_animated_mp4s_rendered_and_deleted":True,
        "real_private_cloud_media_storage_connected":False,
        "real_human_fact_originality_rights_full_watch_completed":False,
        "owner_channel_or_payment_permitted":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


def main() -> None:
    import argparse
    parser=argparse.ArgumentParser(description="GitHub hosted UNAPPROVED 3-topic full render ONLY")
    parser.add_argument("--model",required=True,type=Path)
    parser.add_argument("--voices",required=True,type=Path)
    args=parser.parse_args()
    report=cloud_full_three_topic_narrated_smoke(args.model,args.voices)
    print("B3D4C2C3B_THREE_ACTUAL_SOURCE_LINKED_FULL_NARRATED_VIDEOS_NO_RELEASE",
          json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
