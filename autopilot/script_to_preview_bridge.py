"""B3d4a: exact signed-script -> ORIGINAL, clearly UNREVIEWED visual video preview.

This is a *technical* producer bridge, not an editor, fact checker or publisher.
- Every scene maps to original contiguous narration Unicode-character spans.
- Untrusted model visual beats are displayed as *plans*, not invented facts.
- Actual Pillow frames and FFmpeg H.264/AAC previews are made only in ephemeral
  GitHub-hosted test directories; no TTS or actual final media is asserted.
- A valid script signature is NOT independent editorial/rights authorization.
No YouTube API, network, paid models, OAuth, cloud artifact uploads or keys here.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import textwrap
from typing import Mapping
from datetime import datetime

from autopilot.core import CHANNEL_ID
from autopilot.narration_review_inventory import sentence_spans
from autopilot.script_continuity_gate import DetachedScriptSeal, TrustedScriptCustodian
from autopilot.source_claim_preflight import script_surface_docket

STATUS = "SIGNED_SCRIPT_STORYBOARD_PREVIEW_ONLY_NO_PUBLISH"
VIDEO_STATUS = "ACTUAL_ENCODED_WATERMARKED_PREVIEW_NO_TTS_NO_PUBLISH"
MAX_SCENES = 24
MAX_PREVIEW_BYTES = 35_000_000
PREVIEW_SECONDS_PER_SCENE = 0.38
FONTS = ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")


class PreviewBridgeError(ValueError):
    """Never silently convert a script to a publishable or invented video."""


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_signed_preview_plan(
    proposal: dict, slot: dict, observations: dict,
    *, seal: DetachedScriptSeal, anchor_manifest_sha256: str,
    registry: Mapping[str, TrustedScriptCustodian],
    excluded_creator_and_publisher_ids: frozenset[str],
    now: datetime | None = None,
) -> dict:
    """Build ONLY an unapproved storyboard after B3d1/B3d2/B3d3a revalidation.

    Does not accept an unsupported 'approved' flag from any model or dossier.
    """
    surfaces = script_surface_docket(
        proposal, slot, observations,
        seal=seal, anchor_manifest_sha256=anchor_manifest_sha256,
        registry=registry,
        excluded_creator_and_publisher_ids=excluded_creator_and_publisher_ids,
        now=now,
    )
    if (surfaces["all_defined_surfaces_reviewed"] is not False
            or surfaces["release_authorized"] is not False
            or surfaces["youtube_upload_enabled"] is not False):
        raise PreviewBridgeError("Script surface review cannot grant render/publication rights")
    beats = proposal["visual_beats"]
    spans = sentence_spans(proposal["narration"])
    if (not isinstance(beats, list) or not 4 <= len(beats) <= MAX_SCENES
            or len(spans) < len(beats)):
        raise PreviewBridgeError("No exact scene-to-sentence alignment without omissions")
    count = len(beats)
    result = []
    for index, beat in enumerate(beats):
        a = index * len(spans) // count
        b = (index + 1) * len(spans) // count
        if b <= a:
            raise PreviewBridgeError("Scene has no original spoken sentences")
        start, end = spans[a][0], spans[b - 1][1]
        exact = proposal["narration"][start:end]
        if (not exact.strip() or not isinstance(beat, str) or not beat.strip()):
            raise PreviewBridgeError("Missing intended scene narration or storyboard beat")
        result.append({
            "scene_index": index,
            "scene_id": _sha(surfaces["manifest_sha256"] + "\n" + str(index) + "\n" + beat)[:24],
            "visual_direction_unverified": beat,
            "raw_narration": exact,
            "narration_start_char": start,
            "narration_end_char": end,
            "narration_sha256": _sha(exact),
            "visual_direction_sha256": _sha(beat),
            "caption_accuracy_verified": False,
            "source_assertions_fact_checked": False,
            "actual_visual_production_matches_direction": False,
        })
    if "".join(r["raw_narration"] for r in result) != proposal["narration"]:
        raise PreviewBridgeError("Signed screenplay lost/reordered narration while partitioning")
    if len({r["scene_id"] for r in result}) != count:
        raise PreviewBridgeError("Repeated scene identity")
    return {
        "schema_version": 1,
        "status": STATUS,
        "channel_id": CHANNEL_ID,
        "episode_id": surfaces["episode_id"],
        "format": proposal["format"],
        "release_slot": slot["release_slot"],
        "script_manifest_sha256": surfaces["manifest_sha256"],
        "full_spoken_narration_sha256": _sha(proposal["narration"]),
        "title_unverified": proposal["title"],
        "hook_unverified": proposal["hook"],
        "viewer_benefit_unverified": proposal["viewer_benefit"],
        "scene_count": count,
        "scene_plan": result,
        "all_original_script_characters_preserved": True,
        "source_fact_review_complete": False,
        "human_creative_review_complete": False,
        "rights_approved": False,
        "model_provider_live_inference_used": False,
        "external_review_ledger_connected": False,
        "full_length_final_narration_or_video_exists": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }


def _command(args: list[str], *, timeout: int = 110) -> str:
    try:
        output = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, check=True, timeout=timeout)
        return output.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as exc:
        raise PreviewBridgeError("Hosted preview encoder/decoder failed: " +
                                 type(exc).__name__) from exc


def _font(size: int):
    from PIL import ImageFont
    for file in FONTS:
        try:
            return ImageFont.truetype(file, size)
        except OSError:
            continue
    raise PreviewBridgeError("Expected a free DejaVu font on cloud runner")


def _safe_text(s: str, limit: int = 220) -> str:
    """Make untrusted script text renderable while preserving original in plan."""
    if not isinstance(s, str) or len(s) > 1500:
        raise PreviewBridgeError("Unbounded preview display text")
    return "".join(c if ord(c) >= 32 else " " for c in s)[:limit]


def render_ephemeral_preview(plan: dict, dest: Path) -> dict:
    """Write *temporary* original preview PNGs and encoded visual+silent AAC MP4.

    The caller MUST provide a disposable, empty GitHub-hosted directory and
    discard all contents after local QA. No user media / TTS / external images.
    Images represent text of plan only; they do not illustrate asserted facts.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise PreviewBridgeError("Pillow is required only for cloud preview test") from exc
    if (not isinstance(plan, dict) or plan.get("status") != STATUS
            or plan.get("release_authorized") is not False
            or plan.get("youtube_upload_enabled") is not False
            or plan.get("rights_approved") is not False
            or plan.get("full_length_final_narration_or_video_exists") is not False
            or not isinstance(plan.get("scene_plan"), list)
            or plan.get("scene_count") != len(plan["scene_plan"])
            or not 4 <= len(plan["scene_plan"]) <= MAX_SCENES):
        raise PreviewBridgeError("Render bridge will only accept a non-privileged preview plan")
    kind = plan.get("format")
    if kind not in ("short", "long"):
        raise PreviewBridgeError("Unknown video preview kind")
    # Content continuity is checked again at the final producer edge. This
    # detects in-memory or serialized scene edits after signed plan creation.
    cursor = 0
    rebuilt = []
    seen = set()
    for index, scene in enumerate(plan["scene_plan"]):
        if (not isinstance(scene, dict) or scene.get("scene_index") != index
                or type(scene.get("narration_start_char")) is not int
                or type(scene.get("narration_end_char")) is not int
                or scene["narration_start_char"] != cursor
                or not isinstance(scene.get("raw_narration"), str)
                or scene["narration_end_char"] != cursor + len(scene["raw_narration"])
                or scene.get("narration_sha256") != _sha(scene["raw_narration"])
                or not isinstance(scene.get("visual_direction_unverified"), str)
                or scene.get("visual_direction_sha256") != _sha(scene["visual_direction_unverified"])
                or scene.get("scene_id") != _sha(
                    plan["script_manifest_sha256"] + "\n" + str(index) + "\n" +
                    scene["visual_direction_unverified"]
                )[:24]
                or scene.get("source_assertions_fact_checked") is not False):
            raise PreviewBridgeError("Preview scenes changed after script planning")
        if scene["scene_id"] in seen:
            raise PreviewBridgeError("Repeated scene after script planning")
        seen.add(scene["scene_id"])
        rebuilt.append(scene["raw_narration"])
        cursor = scene["narration_end_char"]
    if _sha("".join(rebuilt)) != plan.get("full_spoken_narration_sha256"):
        raise PreviewBridgeError("Full authored script narration changed after planning")
    # Deliberately half-resolution, to make a technical demo visibly distinct
    # from a production-ready 1080p mastered/approved video.
    w, h = (540, 960) if kind == "short" else (960, 540)
    dest = Path(dest)
    if dest.is_symlink() or not dest.is_dir() or any(dest.iterdir()):
        raise PreviewBridgeError("Refuse nonempty or symlinked preview output directory")
    frames = []
    display_font = _font(28 if kind == "short" else 27)
    body_font = _font(21)
    badge_font = _font(17)
    for index, scene in enumerate(plan["scene_plan"]):
        if (not isinstance(scene, dict) or scene.get("scene_index") != index
                or not isinstance(scene.get("raw_narration"), str)
                or not isinstance(scene.get("visual_direction_unverified"), str)
                or scene.get("source_assertions_fact_checked") is not False):
            raise PreviewBridgeError("A scene tried to assert approval or change its order")
        base = Image.new("RGB", (w, h), (10, 22, 38))
        d = ImageDraw.Draw(base)
        for y in range(0, h, 65):
            d.line([(0, y), (w, y)], fill=(20, 43, 66), width=1)
        d.rounded_rectangle((22, 24, w-22, h-24), radius=18,
                            outline=(65, 145, 175), width=2)
        d.text((38, 45), "FLOWMINUTE LAB  /  SCRIPT PREVIEW", font=badge_font,
               fill=(126, 213, 227))
        d.text((38, 83), f"SCENE {index + 1:02} / {len(plan['scene_plan']):02}",
               font=badge_font, fill=(236, 245, 250))
        title = _safe_text(plan["title_unverified"], 100)
        yy = 135
        for line in textwrap.wrap(title, 30 if kind=="short" else 54,
                                  break_long_words=False)[:3]:
            d.text((38, yy), line, font=display_font, fill=(239, 250, 253))
            yy += 37
        d.rounded_rectangle((38, yy+18, w-38, min(h-155,yy+230)), radius=14,
                            fill=(29, 54, 76))
        d.text((52, yy+32), "UNVERIFIED MODEL VISUAL DIRECTION",
               font=badge_font, fill=(138, 225, 199))
        beat = _safe_text(scene["visual_direction_unverified"], 240)
        for i, line in enumerate(textwrap.wrap(beat, 34 if kind=="short" else 63,
                                               break_long_words=False)[:5]):
            d.text((52, yy+68+i*30), line, font=body_font, fill=(228, 236, 245))
        d.text((38, h-134), "VISUAL STORYBOARD ONLY", font=body_font,
               fill=(255, 212, 140))
        d.text((38, h-100), "NO FACT CHECK  /  NO TTS  /  NO UPLOAD",
               font=badge_font, fill=(255, 166, 146))
        out = dest / f"scene_{index+1:02}.png"
        base.save(out, format="PNG", optimize=True)
        if out.stat().st_size < 1800:
            raise PreviewBridgeError("Missing useful rendered storyboard pixels")
        frames.append(out)
    concat = dest / "frames.ffconcat"
    lines = ["ffconcat version 1.0"]
    for file in frames:
        lines += [f"file '{file.as_posix()}'",f"duration {PREVIEW_SECONDS_PER_SCENE:.3f}"]
    lines += [f"file '{frames[-1].as_posix()}'"]
    concat.write_text("\n".join(lines)+"\n", encoding="utf-8")
    mp4 = dest / "UNREVIEWED_SCRIPT_STORYBOARD_PREVIEW.mp4"
    duration = len(frames)*PREVIEW_SECONDS_PER_SCENE
    _command([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
        "-vf", "fps=10,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "33",
        "-threads", "2", "-c:a", "aac", "-b:a", "48k",
        "-t", f"{duration:.3f}", "-shortest", "-movflags", "+faststart",
        "-y", str(mp4),
    ],timeout=200)
    if not mp4.is_file() or not 12_000 <= mp4.stat().st_size <= MAX_PREVIEW_BYTES:
        raise PreviewBridgeError("Encoded preview missing or unbounded")
    meta = json.loads(_command(
        ["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(mp4)]))
    video = [x for x in meta["streams"] if x.get("codec_type")=="video"]
    audio = [x for x in meta["streams"] if x.get("codec_type")=="audio"]
    if (len(video)!=1 or len(audio)!=1
            or video[0].get("codec_name")!="h264"
            or audio[0].get("codec_name")!="aac"
            or (video[0].get("width"),video[0].get("height"))!=(w,h)):
        raise PreviewBridgeError("Unexpected actual encoded preview streams")
    actual = float(meta["format"]["duration"])
    if not math.isfinite(actual) or not 1 <= actual <= 12 or abs(actual-duration)>.55:
        raise PreviewBridgeError("Preview timestamps or duration out of bound")
    # Decode every actual frame and audio packet, not just trust FFprobe metadata.
    _command(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-xerror",
              "-i",str(mp4),"-f","null","-"],timeout=120)
    with mp4.open("rb") as file:
        content_hash = hashlib.sha256()
        while block := file.read(128*1024):
            content_hash.update(block)
    return {
        "schema_version": 1,
        "status": VIDEO_STATUS,
        "episode_id": plan["episode_id"],
        "script_manifest_sha256": plan["script_manifest_sha256"],
        "video_sha256": content_hash.hexdigest(),
        "scene_count": len(frames),
        "duration_seconds": round(actual,2),
        "resolution": f"{w}x{h}",
        "video_codec": "h264",
        "audio_codec": "aac",
        "audio_is_silence_placeholder": True,
        "actual_decoded_video_and_audio": True,
        "every_original_spoken_script_character_preserved_in_storyboard": True,
        "actual_voice_over_generated": False,
        "full_video_from_real_live_ai_model_created": False,
        "source_claims_verified": False,
        "human_creative_and_rights_review_complete": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }
