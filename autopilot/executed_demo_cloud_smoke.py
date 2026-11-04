"""B3d4c1 hosted full encoded video pack with real computed educational panels.

Every input script and source registry is a synthetic test fixture. Pinned
Kokoro voices + original Pillow visuals + fully decoded FFmpeg media are real,
but NOT independently fact/rights/creative reviewed or publishable. Media,
raw audio, captions, thumbs and frames are destroyed after this hosted run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from autopilot.cloud_av_probe import verify_pinned_assets, sha256_stream
from autopilot.computed_demo_storyboards import (
    build_executed_demo, require_exact_demo, RECIPES,
)
from autopilot.independent_av_review import review_encoded_episode
from autopilot.final_media_evidence_gate import (
    create_unapproved_final_media_inventory,
    require_exact_unapproved_inventory,
    inspect_three_different_unapproved_media,
)
from autopilot.script_to_preview_bridge import build_signed_preview_plan
from autopilot.signed_narrated_cloud_pack import produce_signed_narrated_demo
from autopilot.test_script_continuity_gate import NOW, EXCLUDED, signed_fixture

RECIPES_IN_SLOT_ORDER = (
    "preserve_text_identifiers",
    "validate_iso_dates",
    "review_duplicate_keys",
)
STATUS = "B3D4C1_THREE_EXECUTED_EDUCATIONAL_DEMOS_TECHNICALLY_RENDERED_NOT_PUBLISHABLE"


def check_image(path: Path, *, width: int, height: int) -> None:
    """Independent actual PNG decode, not accepting an author SHA alone."""
    from PIL import Image
    if not path.is_file() or path.is_symlink():
        raise AssertionError("Original computed PNG missing or symlinked")
    with Image.open(path) as im:
        im.load()
        if im.size != (width,height) or im.mode != "RGB":
            raise AssertionError("Original computed visual dimensions/mode unexpected")


def run_pack(model: Path, voices: Path) -> dict:
    from kokoro_onnx import Kokoro
    assets=verify_pinned_assets(model,voices)
    engine=Kokoro(str(model),str(voices))
    reports=[]
    hashes=set()
    thumbs=set()
    final_evidence_inventories=[]
    root=None
    try:
        with TemporaryDirectory(prefix="flowminute-b3d4c1-computed-no-publish-") as temp:
            root=Path(temp)
            for index, recipe in enumerate(RECIPES_IN_SLOT_ORDER):
                proposal, slot, sources, anchor, registry, seal, _=signed_fixture(index)
                plan=build_signed_preview_plan(
                    proposal,slot,sources,
                    seal=seal,
                    anchor_manifest_sha256=anchor,
                    registry=registry,
                    excluded_creator_and_publisher_ids=EXCLUDED,
                    now=NOW,
                )
                executed=build_executed_demo(plan,proposal,recipe)
                require_exact_demo(plan,proposal,recipe,executed)
                out=root/f"unreviewed_{index:02d}"
                out.mkdir(mode=0o700)
                report,episode=produce_signed_narrated_demo(
                    plan,engine,out,
                    proposal=proposal,slot=slot,observations=sources,
                    seal=seal,
                    anchor_manifest_sha256=anchor,
                    registry=registry,
                    excluded_creator_and_publisher_ids=EXCLUDED,
                    now=NOW,
                    demo_recipe=recipe,
                )
                folder=out/episode.episode_id
                independent=review_encoded_episode(
                    folder,episode,
                    report_entry={"episode":report["episode"],"seconds":report["seconds"]},
                )
                thumbnail=folder/"UNAPPROVED_THUMBNAIL_TEST.png"
                check_image(thumbnail,width=1280,height=720)
                thumb_sha,_=sha256_stream(thumbnail,max_bytes=18_000_000)
                if thumb_sha!=report["original_unreviewed_thumbnail_sha256"]:
                    raise AssertionError("Unexpected PNG thumbnail digest")
                width,height=((1080,1920) if report["kind"]=="short" else (1920,1080))
                frame_shas=set()
                for scene in range(report["scene_count"]):
                    png=folder/f"scene_{scene+1:02d}.png"
                    check_image(png,width=width,height=height)
                    digest,_=sha256_stream(png,max_bytes=18_000_000)
                    frame_shas.add(digest)
                if len(frame_shas)!=report["scene_count"]:
                    raise AssertionError("Computed storyboard visual pixels duplicated")
                evidence_kwargs={
                    "plan":plan,"proposal":proposal,"slot":slot,
                    "observations":sources,"seal":seal,
                    "external_script_anchor_sha256":anchor,
                    "script_registry":registry,
                    "excluded_creator_and_publisher_ids":EXCLUDED,
                    "report":report,"episode_folder":folder,
                    "demo_recipe":recipe,"now":NOW,
                }
                inventory=create_unapproved_final_media_inventory(**evidence_kwargs)
                require_exact_unapproved_inventory(inventory,**evidence_kwargs)
                if (
                    inventory["asset_count"]!=report["scene_count"]+6
                    or inventory["all_title_thumbnail_caption_visual_claims_verified"] is not False
                    or inventory["sound_voice_music_license_rights_checked"] is not False
                    or inventory["full_human_watch_listen_completed"] is not False
                    or inventory["release_authorized"] is not False
                ):
                    raise AssertionError("Final exact-media inventory impersonates an editorial approval")
                final_evidence_inventories.append(inventory)
                if (
                    report["computed_test_example_executed"] is not True
                    or report["computed_example_evidence_sha256"]!=executed["evidence_packet_sha256"]
                    or report["human_approved_demo_visual_semantics"] is not False
                    or report["synthetic_data_not_external_factual_support"] is not True
                    or report["real_provider_generated_script"] is not False
                    or report["release_authorized"] is not False
                    or report["youtube_upload_enabled"] is not False
                    or independent["burned_caption_independently_observed"] is not True
                    or independent["distinct_encoded_scenes_observed"] is not True
                    or independent["every_caption_matches_original_spoken_text"] is not True
                    or independent["independent_claim_or_rights_review_complete"] is not False
                    or independent["human_complete_watch_or_listen_complete"] is not False
                ):
                    raise AssertionError("Independent media/content rights safety mismatch")
                if not independent["ffmpeg_actual_encoded_audio"]["typical_online_video_target_diagnostic"]:
                    raise AssertionError("Encoded real voice outside diagnostic quality band")
                hashes.add(report["video_sha256"])
                thumbs.add(thumb_sha)
                item={
                    "episode": report["episode"],
                    "format":report["kind"],
                    "actual_voice":report["voice"],
                    "duration_seconds":report["seconds"],
                    "actual_original_scene_frames":report["scene_count"],
                    "source_narration_srt_cues":report["narration_cues"],
                    "actual_source_data_computation":recipe,
                    "computed_evidence_sha256":executed["evidence_packet_sha256"],
                    "original_unapproved_thumbnail_sha256":thumb_sha,
                    "exact_final_asset_inventory_sha256":inventory["unapproved_inventory_sha256"],
                    "exact_final_asset_count":inventory["asset_count"],
                    "srt_spoken_phrases_exact":inventory["srt_text_and_cue_timing"]["all_spoken_sentences_text_exactly_represented"],
                    "ffmpeg_lufs":independent["ffmpeg_actual_encoded_audio"]["integrated_lufs"],
                    "ffmpeg_true_peak_dbtp":independent["ffmpeg_actual_encoded_audio"]["true_peak_dbtp"],
                    "burned_caption_pixels":independent["caption_visible_changed_pixels"],
                    "independent_visual_scene_change_pixels":independent["first_to_later_scene_changed_pixels"],
                    "actual_all_frame_decodes":report["full_actual_mp4_h264_aac_decode_passed"],
                    "model_generated_script":False,
                    "human_source_and_rights_review":False,
                    "youtube_upload_enabled":False,
                    "release_authorized":False,
                }
                reports.append(item)
                print("B3D4C1_ACTUAL_COMPUTED_DEMO_VIDEO_AND_THUMBNAIL",
                      json.dumps(item,sort_keys=True),flush=True)
            if (
                len(reports)!=3
                or len(hashes)!=3
                or len(thumbs)!=3
                or [x["format"] for x in reports]!=["short","long","short"]
                or len({x["actual_voice"] for x in reports})!=3
                or len({x["computed_evidence_sha256"] for x in reports})!=3
                or len({x["exact_final_asset_inventory_sha256"] for x in reports})!=3
            ):
                raise AssertionError("Three independently computed subject-specific video outputs incomplete")
            cross=inspect_three_different_unapproved_media(final_evidence_inventories)
            if (cross["semantic_originality_approved"] is not False
                    or cross["human_fact_and_rights_reviews_complete"] is not False
                    or cross["youtube_upload_enabled"] is not False
                    or cross["release_authorized"] is not False):
                raise AssertionError("Cross-episode file uniqueness forged content approval")
            print("B3D4C2C1_THREE_EXACT_MP4_SRT_WAV_THUMB_SCENE_INVENTORIES_UNAPPROVED",
                  json.dumps(cross,sort_keys=True),flush=True)
    finally:
        close=getattr(getattr(engine,"voices",None),"close",None)
        if callable(close):
            close()
    if root is None or root.exists():
        raise AssertionError("Synthetic test videos were retained after hosted runner")
    return {
        "status":STATUS,
        "model_sha256_verified":assets["model_sha256"],
        "voice_pack_sha256_verified":assets["voice_pack_sha256"],
        "episode_count":len(reports),
        "episodes":reports,
        "synthetic_data_only":True,
        "external_generative_provider_calls":0,
        "independent_semantic_claim_rights_checks_completed":False,
        "three_rebuilt_exact_media_inventories_checked":len(final_evidence_inventories)==3,
        "originality_for_new_daily_content_verified":False,
        "private_durable_video_storage_connected":False,
        "all_video_thumb_and_voice_artifacts_deleted":True,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description="Three executed original demo media test episodes; NO PUBLISH")
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--voices",type=Path,required=True)
    args=parser.parse_args()
    report=run_pack(args.model,args.voices)
    print("B3D4C1_THREE_ACTUAL_COMPUTED_EDUCATION_VIDEOS_QUALITY_CHECKED_AND_DELETED_NO_PUBLISH",json.dumps({
        "durations":[r["duration_seconds"] for r in report["episodes"]],
        "different_examples":[r["actual_source_data_computation"] for r in report["episodes"]],
        "different_voices":[r["actual_voice"] for r in report["episodes"]],
        "distinct_video_hashes":len({r["episode"] for r in report["episodes"]}),
        "original_thumbnail_created":[bool(r["original_unapproved_thumbnail_sha256"]) for r in report["episodes"]],
        "media_deleted":report["all_video_thumb_and_voice_artifacts_deleted"],
        "real_ai_inference_performed":False,
        "human_content_approved":False,
        "youtube_upload_enabled":False,
    }),flush=True)


if __name__=="__main__":
    main()
