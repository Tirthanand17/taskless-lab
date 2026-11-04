"""B3d4a hosted CI-only REAL encoded MP4 and storyboard smoke, then destroy.

Test scripts are invented fixtures, not actual provider outputs or reviewable
full-quality videos. No programmatic publishing or external secrets.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from autopilot.test_script_continuity_gate import signed_fixture, NOW, EXCLUDED
from autopilot.script_to_preview_bridge import (
    build_signed_preview_plan, render_ephemeral_preview,
    PreviewBridgeError, VIDEO_STATUS,
)


def main() -> None:
    with TemporaryDirectory(prefix="flowminute-b3d4a-unreviewed-") as root:
        base = Path(root)
        sha = set()
        for index, kind in enumerate(("short","long","short")):
            proposal, slot, observations, anchor, registry, seal, _ = signed_fixture(index)
            plan = build_signed_preview_plan(
                proposal,slot,observations,
                seal=seal,anchor_manifest_sha256=anchor,registry=registry,
                excluded_creator_and_publisher_ids=EXCLUDED,now=NOW,
            )
            folder = base / f"preview_{index:02}"
            folder.mkdir(mode=0o700)
            report = render_ephemeral_preview(plan,folder)
            if (report["status"]!=VIDEO_STATUS
                    or report["scene_count"]!=len(proposal["visual_beats"])
                    or report["episode_id"]!=slot["episode_id"]
                    or report["actual_decoded_video_and_audio"] is not True
                    or report["actual_voice_over_generated"] is not False
                    or report["audio_is_silence_placeholder"] is not True
                    or report["full_video_from_real_live_ai_model_created"] is not False
                    or report["human_creative_and_rights_review_complete"] is not False
                    or report["source_claims_verified"] is not False
                    or report["release_authorized"] is not False
                    or report["youtube_upload_enabled"] is not False):
                raise AssertionError("Preview incorrectly claimed real/approved production")
            dimensions = "540x960" if kind=="short" else "960x540"
            if report["resolution"] != dimensions:
                raise AssertionError("Wrong technical preview display shape")
            sha.add(report["video_sha256"])
            # Recheck untrusted code cannot flip render authorization flags.
            forged = deepcopy(plan)
            forged["release_authorized"] = True
            tamper_dir = base / f"forgery_{index:02}"
            tamper_dir.mkdir(mode=0o700)
            try:
                render_ephemeral_preview(forged,tamper_dir)
                raise AssertionError("Forged preview unexpectedly rendered")
            except PreviewBridgeError:
                pass
            forged = deepcopy(plan)
            forged["scene_plan"][0]["raw_narration"] += " Mutated!"
            try:
                render_ephemeral_preview(forged,tamper_dir)
                raise AssertionError("Tampered authored narration unexpectedly rendered")
            except PreviewBridgeError:
                pass
            print("EPHEMERAL_UNPUBLISHED_SOURCE_BOUND_PREVIEW", json.dumps({
                "episode":report["episode_id"], "seconds":report["duration_seconds"],
                "scene_count":report["scene_count"],
                "resolution":report["resolution"],
                "encoded_sha256":report["video_sha256"],
                "video_codec":report["video_codec"],
                "audio_codec":report["audio_codec"],
                "source_script_rights_approved":False,
                "voice_generated":False,
                "youtube_upload_enabled":False,
            }),flush=True)
        if len(sha) != 3:
            raise AssertionError("Missing or duplicated signed script preview encodes")
    if base.exists():
        raise AssertionError("Hosted temporary unapproved media directory not deleted")
    print("B3D4A_THREE_ACTUAL_VIDEO_PREVIEWS_H264_AAC_DECODED_THEN_DESTROYED_NO_PROVIDER_NO_TTS_NO_PUBLISH",flush=True)


if __name__ == "__main__":
    main()
