"""B3d4b: signed script -> original storyboard, real Kokoro speech & captioned MP4.

This technical TEST renderer accepts exact B3d4a source-bound script plans.
It NEVER accepts real media release authorization, signs factual reviews, calls
AI providers, exports artifacts, or uses YouTube. The supplied content MUST
have been reviewed independently before any future production deployment.
Only caller-controlled ephemeral GitHub-hosted directories are supported.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import textwrap

from autopilot.cloud_av_probe import sha256_stream
from autopilot.cloud_full_duration_pack import (
    encode, narration_and_srt, run, sentence_chunks, validate_cues,
)
from autopilot.full_pack_fixture import ExampleEpisode, Scene
from autopilot.script_to_preview_bridge import (
    STATUS as SCRIPT_PLAN_STATUS, _font, _safe_text, _sha,
)

STATUS = "REAL_KOKORO_SIGNED_SCRIPT_TECHNICAL_DEMO_UNREVIEWED_NO_PUBLISH"
VOICE_FOR_SLOT = {
    "short_am": "af_heart",
    "long": "am_michael",
    "short_pm": "bf_emma",
}
MAX_SCENES = 24
MAX_VIDEO_BYTES = 300_000_000


class NarratedPackError(ValueError):
    """No silent mutations, forged review claims, or incomplete rendered output."""


@dataclass(frozen=True)
class PreparedNarration:
    episode: ExampleEpisode
    script_manifest_sha256: str
    original_script_sha256: str
    scene_ids: tuple[str, ...]


def validate_plan(plan: object) -> PreparedNarration:
    """Revalidate entire authored narration and beat SHA at the TTS boundary."""
    if not isinstance(plan, dict) or plan.get("status") != SCRIPT_PLAN_STATUS:
        raise NarratedPackError("Not a source-bound B3d4a signed-script storyboard")
    for flag in (
        "release_authorized", "youtube_upload_enabled", "youtube_schedule_enabled",
        "source_fact_review_complete", "human_creative_review_complete",
        "rights_approved", "model_provider_live_inference_used",
        "external_review_ledger_connected", "full_length_final_narration_or_video_exists",
    ):
        if plan.get(flag) is not False:
            raise NarratedPackError("Preview tried to impersonate a reviewed live video")
    manifest = plan.get("script_manifest_sha256")
    spoken_sha = plan.get("full_spoken_narration_sha256")
    if (not isinstance(manifest, str) or not re.fullmatch("[0-9a-f]{64}", manifest)
            or not isinstance(spoken_sha, str)
            or not re.fullmatch("[0-9a-f]{64}", spoken_sha)):
        raise NarratedPackError("Missing anchored script fingerprints")
    episode_id = plan.get("episode_id")
    slot = plan.get("release_slot")
    kind = plan.get("format")
    if (not isinstance(episode_id, str)
            or not re.fullmatch(r"fm_[0-9]{8}_(short_am|short_pm|long)", episode_id)
            or not isinstance(slot, str) or episode_id.split("_")[-2:] != (
                ["short", "am"] if slot == "short_am" else
                ["short", "pm"] if slot == "short_pm" else
                ["long"]
            ) or slot not in VOICE_FOR_SLOT
            or kind != ("long" if slot == "long" else "short")):
        raise NarratedPackError("Wrong format, episode or one-of-three daily release slots")
    scenes = plan.get("scene_plan")
    if (not isinstance(scenes, list) or not 4 <= len(scenes) <= MAX_SCENES
            or type(plan.get("scene_count")) is not int
            or plan["scene_count"] != len(scenes)):
        raise NarratedPackError("Missing or excessive dynamic storyboard scenes")
    cursor = 0
    rebuilt = []
    originals = []
    ids = set()
    for i, row in enumerate(scenes):
        if not isinstance(row, dict):
            raise NarratedPackError("Malformed untrusted storyboard record")
        beat = row.get("visual_direction_unverified")
        spoken = row.get("raw_narration")
        if (type(row.get("scene_index")) is not int or row["scene_index"] != i
                or not isinstance(beat, str) or not 20 <= len(beat.strip()) <= 280
                or not isinstance(spoken, str) or not spoken.strip()
                or type(row.get("narration_start_char")) is not int
                or type(row.get("narration_end_char")) is not int
                or row["narration_start_char"] != cursor
                or row["narration_end_char"] != cursor + len(spoken)
                or row.get("visual_direction_sha256") != _sha(beat)
                or row.get("narration_sha256") != _sha(spoken)
                or row.get("scene_id") != _sha(manifest + "\n" + str(i) + "\n" + beat)[:24]
                or row.get("caption_accuracy_verified") is not False
                or row.get("source_assertions_fact_checked") is not False
                or row.get("actual_visual_production_matches_direction") is not False):
            raise NarratedPackError("Unreviewed script/beat/scene span mutated")
        if row["scene_id"] in ids:
            raise NarratedPackError("Repeated visual scene identity")
        ids.add(row["scene_id"])
        cursor += len(spoken)
        rebuilt.append(spoken)
        # B3b speech splits on punctuation. If one sentence is too long,
        # reject rather than generating truncated/missing captions.
        try:
            phrases = sentence_chunks(spoken)
        except ValueError as exc:
            raise NarratedPackError("Unusable narration cue") from exc
        if len(phrases) < 1:
            raise NarratedPackError("Scene has no voiced/captioned text")
        originals.append(Scene(
            title=f"Scene {i + 1} / {len(scenes)}",
            narration=spoken, mode="workflow",
        ))
    if _sha("".join(rebuilt)) != spoken_sha:
        raise NarratedPackError("Full original spoken text altered or lost")
    if len({x for x in ids}) != len(scenes):
        raise NarratedPackError("Nonunique scene plan")
    return PreparedNarration(
        episode=ExampleEpisode(
            episode_id=episode_id,
            kind=kind,
            voice=VOICE_FOR_SLOT[slot],
            theme=plan["title_unverified"],
            scenes=tuple(originals),
        ),
        script_manifest_sha256=manifest,
        original_script_sha256=spoken_sha,
        scene_ids=tuple(row["scene_id"] for row in scenes),
    )


def original_frame(plan: dict, index: int, out: Path) -> str:
    """Original typographic explainer, NOT fictitious screenshots/data/results."""
    from PIL import Image, ImageDraw
    scenes = plan["scene_plan"]
    scene = scenes[index]
    portrait = plan["format"] == "short"
    width, height = (1080, 1920) if portrait else (1920, 1080)
    canvas = Image.new("RGB", (width, height), (12, 25, 43))
    draw = ImageDraw.Draw(canvas)
    big = _font(53 if portrait else 64)
    body = _font(37 if portrait else 39)
    small = _font(26)
    for y in range(0, height, 96):
        draw.line((0, y, width, y), fill=(24, 47, 69), width=2)
    draw.rounded_rectangle((38, 42, width-38, height-42), 28,
                           outline=(67, 130, 154), width=3)
    draw.text((75, 87), "FLOWMINUTE LAB  |  GENERATED VOICE DEMO",
              font=small, fill=(141, 209, 228))
    draw.text((75, 141), f"STORYBOARD {index+1:02d} / {len(scenes):02d}",
              font=small, fill=(236, 244, 252))
    title = _safe_text(plan["title_unverified"], 100)
    top = 222
    for line in textwrap.wrap(title, 24 if portrait else 44, break_long_words=False)[:3]:
        draw.text((76, top), line, font=big, fill=(242, 249, 251))
        top += 78
    # Deliberate original motion/storyboard graphic: different highlight and
    # geometry across scenes, but no false representation of source evidence.
    panel_top = 530 if portrait else 395
    panel_bottom = height-395 if portrait else height-260
    palettes = (
        ((20, 91, 122), (48, 145, 179)),
        ((103, 61, 100), (178, 102, 160)),
        ((35, 106, 81), (96, 187, 137)),
    )
    surface, accent = palettes[index % 3]
    draw.rounded_rectangle((76,panel_top,width-76,panel_bottom),22,fill=surface)
    draw.rounded_rectangle((106,panel_top+36,width-106,panel_top+58),9,fill=accent)
    draw.text((109,panel_top+97),"PLANNED VISUAL BEAT (NOT FACT VERIFIED)",
              font=small,fill=(246,252,255))
    beats = _safe_text(scene["visual_direction_unverified"], 260)
    for j,line in enumerate(textwrap.wrap(beats,33 if portrait else 62,break_long_words=False)[:5]):
        draw.text((110,panel_top+160+j*54),line,font=body,fill=(248,250,253))
    circle_y = min(panel_bottom-115,panel_top+485 if portrait else panel_top+290)
    for step in range(3):
        x=145+step*((width-290)//2)
        radius=34
        draw.ellipse((x-radius,circle_y-radius,x+radius,circle_y+radius),
                     fill=accent if step == (index % 3) else (66,76,96))
    draw.rounded_rectangle((84,height-(325 if portrait else 204),
                            width-84,height-89),16,fill=(15,36,57))
    draw.text((103,height-(306 if portrait else 191)),
              "VOICE + TIMED CAPTIONS: TECHNICAL TEST",font=small,fill=(178,220,250))
    draw.text((103,height-132),"UNREVIEWED  /  NO FACT OR RIGHTS APPROVAL  /  NO UPLOAD",
              font=small,fill=(255,177,143))
    canvas.save(out,format="PNG",optimize=True)
    sha,size=sha256_stream(out,max_bytes=18_000_000)
    if size<5000:
        raise NarratedPackError("Bad original scene image")
    return sha


def inspect_dynamic_media(
    folder: Path, episode: ExampleEpisode, scenes: tuple[str, ...],
    original_seconds: float, captions: list[dict], frames: list[Path],
) -> dict:
    """Check actual H264/AAC, full decode, dimensions and literal SRT cues."""
    mp4 = folder / "UNAPPROVED_FULL_EDUCATION_TEST.mp4"
    meta = json.loads(run([
        "ffprobe", "-v","error","-show_streams","-show_format","-of","json",str(mp4)
    ]))
    streams = meta.get("streams",[])
    video = [s for s in streams if s.get("codec_type")=="video"]
    audio = [s for s in streams if s.get("codec_type")=="audio"]
    width,height = (1080,1920) if episode.kind=="short" else (1920,1080)
    if (len(video)!=1 or len(audio)!=1
            or (video[0].get("width"),video[0].get("height"))!=(width,height)
            or video[0].get("codec_name")!="h264"
            or video[0].get("pix_fmt")!="yuv420p"
            or audio[0].get("codec_name")!="aac"):
        raise NarratedPackError("Actual A/V codec or format unsupported")
    actual = float(meta.get("format",{}).get("duration",0))
    min_seconds,max_seconds = (18,110) if episode.kind=="short" else (60,320)
    if (not math.isfinite(actual)
            or not min_seconds<=actual<=max_seconds
            or abs(actual-original_seconds)>.75):
        raise NarratedPackError("Truncated, unsynced, or implausible full narrated demo")
    validate_cues(captions,original_seconds,len(captions))
    if len({sha256_stream(frame,max_bytes=18_000_000)[0] for frame in frames})!=len(frames):
        raise NarratedPackError("Duplicate visual storyboard scene output")
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-xerror",
         "-i",str(mp4),"-f","null","-"],timeout=1300)
    digest,size=sha256_stream(mp4,max_bytes=MAX_VIDEO_BYTES)
    if size<200_000:
        raise NarratedPackError("Actual audio/video output unexpectedly empty")
    return {
        "episode": episode.episode_id,
        "kind": episode.kind,
        "voice": episode.voice,
        "seconds": round(actual,2),
        "video_sha256": digest,
        "mp4_bytes": size,
        "resolution": f"{width}x{height}",
        "scene_count": len(episode.scenes),
        "original_scene_ids": list(scenes),
        "narration_cues": len(captions),
        "actual_kokoro_speech_generated": True,
        "srt_cues_timed_from_generated_pcm": True,
        "animated_progress_bar_and_original_scene_transition_tones": True,
        "all_original_spoken_characters_preserved_in_plan": True,
        "full_actual_mp4_h264_aac_decode_passed": True,
        "real_provider_generated_script": False,
        "true_per_word_forced_alignment_performed": False,
        "human_full_playback_completed": False,
        "human_voice_quality_review_complete": False,
        "factual_accuracy_independently_approved": False,
        "copyright_and_voice_rights_cleared": False,
        "final_video_publishable": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }


def produce_signed_narrated_demo(
    plan: dict, voice_engine, root: Path,
) -> tuple[dict, ExampleEpisode]:
    """Generate a genuine full technical MP4 from exactly the signed test script.

    Call this only in disposable hosted CI; the function writes no production
    approval receipts and cannot use a publisher or external model.
    """
    prepared = validate_plan(plan)
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise NarratedPackError("Require empty real ephemeral directory")
    episode=prepared.episode
    folder = root / episode.episode_id
    folder.mkdir(mode=0o700)
    voice,srt,timings,cues,seconds,tts_seconds = narration_and_srt(
        voice_engine, episode,folder,
    )
    frames=[]
    for i in range(len(plan["scene_plan"])):
        out=folder/f"scene_{i+1:02d}.png"
        original_frame(plan,i,out)
        frames.append(out)
    encode(episode,folder,frames,timings,voice,srt,seconds)
    report=inspect_dynamic_media(folder,episode,prepared.scene_ids,seconds,cues,frames)
    report["script_manifest_sha256"]=prepared.script_manifest_sha256
    report["full_original_narration_sha256"]=prepared.original_script_sha256
    report["voice_generation_elapsed_seconds"]=tts_seconds
    return report,episode
