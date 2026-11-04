"""B3d4b hosted real three-video narrative/QA smoke; destroys all output.

Uses only in-memory fake source/scripts, disposable Ed25519 signing keys, publicly
pinned Kokoro voice files and free open-source CPU FFmpeg/Pillow. Never calls
Gemini, uploads media, stores private content, or signs human approvals.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from autopilot.cloud_av_probe import verify_pinned_assets
from autopilot.independent_av_review import review_encoded_episode
from autopilot.script_to_preview_bridge import build_signed_preview_plan
from autopilot.signed_narrated_cloud_pack import (
    STATUS, produce_signed_narrated_demo,
)
from autopilot.test_script_continuity_gate import NOW, EXCLUDED, signed_fixture

VALIDATED_OUTPUT = "SIGNED_SCRIPT_KOKORO_AND_ENCODER_TECHNICAL_QA_NO_PUBLISH"


def benchmark(model: Path, voices: Path) -> dict:
    from kokoro_onnx import Kokoro

    assets=verify_pinned_assets(model,voices)
    outputs=[]
    fingerprints=set()
    root_path=None
    engine=Kokoro(str(model),str(voices))
    try:
        with TemporaryDirectory(prefix="flowminute-b3d4b-unreviewed-speech-") as temp:
            root=Path(temp)
            root_path=root
            for index in range(3):
                proposal,slot,sources,anchor,registry,seal,_=signed_fixture(index)
                plan=build_signed_preview_plan(
                    proposal,slot,sources,
                    seal=seal,anchor_manifest_sha256=anchor,
                    registry=registry,
                    excluded_creator_and_publisher_ids=EXCLUDED,
                    now=NOW,
                )
                folder=root/f"episode_{index:02}"
                folder.mkdir(mode=0o700)
                report,episode=produce_signed_narrated_demo(
                    plan,engine,folder,
                    proposal=proposal,slot=slot,observations=sources,
                    seal=seal,anchor_manifest_sha256=anchor,
                    registry=registry,
                    excluded_creator_and_publisher_ids=EXCLUDED,
                    now=NOW,
                )
                independent=review_encoded_episode(
                    folder/episode.episode_id, episode,
                    report_entry={"episode":report["episode"],"seconds":report["seconds"]},
                )
                if (report["youtube_upload_enabled"] is not False
                        or report["release_authorized"] is not False
                        or report["real_provider_generated_script"] is not False
                        or report["full_actual_mp4_h264_aac_decode_passed"] is not True
                        or independent["youtube_upload_enabled"] is not False
                        or independent["human_complete_watch_or_listen_complete"] is not False
                        or independent["independent_claim_or_rights_review_complete"] is not False
                        or independent["burned_caption_independently_observed"] is not True
                        or independent["distinct_encoded_scenes_observed"] is not True
                        or independent["every_caption_matches_original_spoken_text"] is not True
                        or report["scene_count"]!=len(plan["scene_plan"])
                        or report["script_manifest_sha256"]!=plan["script_manifest_sha256"]):
                    raise AssertionError("Real encoded file failed independent diagnostic or claimed approval")
                fingerprints.add(report["video_sha256"])
                outputs.append({
                    "episode":report["episode"],
                    "format":report["kind"],
                    "voice":report["voice"],
                    "seconds":report["seconds"],
                    "scene_count":report["scene_count"],
                    "srt_cues":report["narration_cues"],
                    "resolution":report["resolution"],
                    "mp4_sha256":report["video_sha256"],
                    "mp4_bytes":report["mp4_bytes"],
                    "spoken_voice_generated":True,
                    "measured_encoded_lufs":independent["ffmpeg_actual_encoded_audio"]["integrated_lufs"],
                    "measured_encoded_true_peak_dbtp":independent["ffmpeg_actual_encoded_audio"]["true_peak_dbtp"],
                    "burned_caption_pixels":independent["caption_visible_changed_pixels"],
                    "independently_verified_scene_pixel_changes":independent["first_to_later_scene_changed_pixels"],
                    "fact_rights_creative_approval":False,
                    "youtube_upload_enabled":False,
                })
                print("B3D4B_REAL_UNAPPROVED_SIGNED_SCRIPT_NARRATED_VIDEO",
                      json.dumps(outputs[-1]),flush=True)
            if (len(outputs)!=3 or len(fingerprints)!=3
                    or [x["format"] for x in outputs]!=["short","long","short"]
                    or len({x["voice"] for x in outputs})!=3):
                raise AssertionError("Missing/duplicated technically narrated three-slot video pack")
    finally:
        close=getattr(getattr(engine,"voices",None),"close",None)
        if callable(close):
            close()
    if root_path is None or root_path.exists():
        raise AssertionError("Unreviewed cloud media survived TemporaryDirectory cleanup")
    return {
        "status":VALIDATED_OUTPUT,
        "technical_only":True,
        "synthetic_test_sources_and_scripts":True,
        "model_weights_sha256":assets["model_sha256"],
        "public_voice_pack_sha256":assets["voice_pack_sha256"],
        "episodes":outputs,
        "external_generative_api_calls":0,
        "private_durable_media_store_connected":False,
        "owner_and_human_review_approved":False,
        "local_laptop_access":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
        "all_temporary_mp4_srt_png_and_audio_deleted":True,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description="Full real source-bound Kokoro media diagnostic; no publish")
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--voices",type=Path,required=True)
    args=parser.parse_args()
    result=benchmark(args.model,args.voices)
    print("B3D4B_THREE_ACTUAL_SIGNED_SCRIPT_TTS_SUBTITLED_MP4S_AND_INDEPENDENT_QA_PASS_DELETE_ALL_NO_PUBLISH",
          json.dumps({
              "durations":[r["seconds"] for r in result["episodes"]],
              "cues":[r["srt_cues"] for r in result["episodes"]],
              "voices":[r["voice"] for r in result["episodes"]],
              "human_content_approved":False,
              "model_inference_performed":False,
              "youtube_upload_enabled":False,
              "deleted":result["all_temporary_mp4_srt_png_and_audio_deleted"],
          }),flush=True)


if __name__=="__main__":
    main()
