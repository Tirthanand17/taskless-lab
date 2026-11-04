"""B3d4c2c3a: GitHub-hosted three SILENT four-second original vector video previews.

Renders original SVG with CairoSVG and actually decodes generated H264 using
FFmpeg/ffprobe. These are NOT narrated, licensed/reviewed final videos; files
live only in a TemporaryDirectory on the hosted runner and are destroyed.

No real YouTube/provider/paid API, external video assets or laptop disk.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from autopilot.primary_sourced_storyboards import (
    build_story, render_original_svg, require_exact_draft,
    evaluate_three_draft_stories,
)


def _run(command: list[str]) -> str:
    result=subprocess.run(
        command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,timeout=180,check=False,
    )
    if result.returncode:
        raise AssertionError(
            "Original private-ephemeral SVG media encoding/decoding failed: "
            +command[0]+" exit "+str(result.returncode)
        )
    return result.stdout


def cloud_original_vector_preview_smoke() -> dict:
    import cairosvg
    from PIL import Image
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise AssertionError("Real FFmpeg and independent ffprobe required")
    three=evaluate_three_draft_stories()
    reports=[]
    with TemporaryDirectory(prefix="flowminute-three-researched-visual-previews-") as tmp:
        root=Path(tmp)
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            require_exact_draft(story)
            episode=root/story["episode_id"]
            episode.mkdir()
            expected=(1920,1080) if slot=="long" else (1080,1920)
            frame_hashes=[]
            for frame in range(12):
                # Different physical motion; every frame is an original SVG
                # authoring output rather than repeated resized artwork.
                tick=frame*10
                svg=render_original_svg(story,frame%story["scene_count"],tick)
                png=episode/f"frame_{frame:03d}.png"
                cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                                  write_to=str(png))
                with Image.open(png) as im:
                    if im.size!=expected or im.mode not in ("RGBA","RGB"):
                        raise AssertionError("Wrong SVG-to-PNG frame geometry")
                    im.verify()
                frame_hashes.append(sha256(png.read_bytes()).hexdigest())
            if len(set(frame_hashes))!=12:
                raise AssertionError("Duplicate/unchanging frames in original video preview")
            output=episode/"UNAPPROVED_SILENT_VECTOR_TECHNICAL_PREVIEW.mp4"
            _run([
                "ffmpeg","-y","-hide_banner","-loglevel","error",
                "-framerate","3","-i",str(episode/"frame_%03d.png"),
                "-an","-c:v","libx264","-preset","ultrafast",
                "-crf","27","-pix_fmt","yuv420p","-movflags","+faststart",
                str(output),
            ])
            probe=json.loads(_run([
                "ffprobe","-v","error","-count_frames",
                "-select_streams","v:0",
                "-show_entries",
                "stream=codec_name,width,height,nb_read_frames",
                "-of","json",str(output),
            ]))
            streams=probe.get("streams",[])
            if (
                len(streams)!=1
                or streams[0].get("codec_name")!="h264"
                or (streams[0].get("width"),streams[0].get("height"))!=expected
                or int(streams[0].get("nb_read_frames",0))!=12
            ):
                raise AssertionError("Wrong actual H264 frame decode/geometry")
            # Independent full decoder must succeed across all video frames.
            _run(["ffmpeg","-v","error","-xerror","-i",str(output),
                  "-f","null","-"])
            reports.append({
                "episode_id":story["episode_id"],
                "theme":story["theme"],
                "source_reference_ids":sorted(story["primary_sources"]),
                "signed_original_story_draft_sha256":story["draft_sha256"],
                "actual_original_png_frames_decoded":12,
                "actual_silent_h264_full_decode_passed":True,
                "video_width":expected[0],
                "video_height":expected[1],
                "video_mp4_sha256":sha256(output.read_bytes()).hexdigest(),
                "raw_video_preview_only":True,
                "factual_claim_reviewed_by_human":False,
                "music_and_voice_rights_approved":False,
                "narration_or_dialogue_mixed":False,
                "human_full_watch_listen_completed":False,
                "private_media_store_deployed":False,
                "youtube_upload_enabled":False,
                "release_authorized":False,
            })
        if len({r["video_mp4_sha256"] for r in reports})!=3:
            raise AssertionError("Rendered video previews were duplicated")
        if set(r["theme"] for r in reports)!={"lunar_signal","quake_energy","file_transfer"}:
            raise AssertionError("Not three different educational graphic systems")
    return {
        "status":"THREE_ORIGINAL_PRIMARY_LINKED_TOPIC_SILENT_PREVIEWS_EPHEMERAL_NOT_PUBLISHABLE",
        "episode_report":reports,
        "preview_mp4_count":3,
        "preview_mp4_bytes_persisted_to_public_repository":0,
        "real_narrated_production_videos":0,
        "human_fact_rights_owner_review":False,
        "provider_live_inference_used":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


def main() -> None:
    result=cloud_original_vector_preview_smoke()
    print("B3D4C2C3A_REAL_SVG_FFMPEG_THREE_SILENT_PREVIEWS_NO_UPLOAD",
          json.dumps(result,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
