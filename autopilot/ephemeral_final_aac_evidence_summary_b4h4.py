"""B4h4 expose already-measured final AAC physical evidence without MP4 retention.

B4e1 independently decodes and post-measures all three AAC/H.264 files in
memory on the disposable runner. The old normal daily workflow only printed
generic decode success and reserved detailed human audio QA for explicit
manual, public 1-day artifact opt-in. This *additional* no-retention report
rechecks the existing SHA-bound B4g5 results (no second encode or provider)
and prints ONLY bounded numbers and unresolved review warnings.

The three real MP4s and all voices remain ephemeral; never approvals.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re

from autopilot.full_original_rehearsal_media_b4e1 import STATUS as FULL_STATUS
from autopilot.verified_aac_mastering_b4g5 import (
    STATUS as AAC_STATUS, ACCEPTED_INTEGRATED_LUFS_MIN,
    ACCEPTED_INTEGRATED_LUFS_MAX, ACCEPTED_TRUE_PEAK_DBTP_MAX,
    ACCEPTED_LRA_LU_MAX, ACCEPTED_THREE_VIDEO_LUFS_SPREAD_MAX,
)

STATUS = "B4H4_ALREADY_MEASURED_EPHEMERAL_THREE_AAC_REPORT_NOT_HUMAN_REVIEW"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SLOTS = ("short_am","long","short_pm")
REPORT_PATH = Path("/tmp/flowminute-b4e1-complete-rehearsals/"
                   "EPHEMERAL_FULL_VOICE_REHEARSAL_QA.json")


class MasterEvidenceRefused(ValueError):
    """Unsupported, forged or misleading original-video evidence."""


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise MasterEvidenceRefused(reason)


def _finite(value: object, low: float, high: float) -> bool:
    return type(value) in (int,float) and math.isfinite(value) and low<=value<=high


def summarize_measured_ephemeral_masters(report: object) -> dict:
    _need(type(report) is dict and report.get("status")==FULL_STATUS
          and report.get("full_daily_nonfactual_rehearsal_videos_encoded")==3
          and report.get("actually_voiced_complete_original_scene_count")==17
          and report.get("all_three_real_h264_aac_ffmpeg_full_decodes_passed") is True
          and report.get("all_three_final_encoded_aac_masters_in_conservative_range") is True
          and report.get("all_caption_reading_rates_approved") is False
          and report.get("real_news_facts_approved")==0
          and report.get("rights_approvals")==0
          and report.get("human_full_watches")==0
          and report.get("youtube_uploads")==0
          and report.get("release_authorized") is False
          and type(report.get("episodes")) is list
          and len(report["episodes"])==3,
          "Missing exact original full-encode, no-release evidence")
    items=[]
    source_hashes=set()
    lufs_values=[]
    for index,(slot,ep) in enumerate(zip(SLOTS,report["episodes"])):
        _need(type(ep) is dict and ep.get("slot")==slot
              and ep.get("original_full_scene_count") == (9 if slot=="long" else 4)
              and ep.get("actual_full_ffmpeg_decode_passed") is True
              and ep.get("b4g5_post_encode_aac_lufs_true_peak_verified") is True
              and ep.get("release_authorized") is False
              and ep.get("youtube_uploaded") is False
              and ep.get("human_full_audio_visual_watch_completed") is False
              and ep.get("fully_release_ready_for_youtube") is False,
              "Wrong original three-video identity or media authorization")
        sha=ep.get("encoded_h264_aac_sha256")
        master=ep.get("original_audio_encoded_mastering")
        _need(type(sha) is str and HEX64.fullmatch(sha) is not None
              and sha not in source_hashes
              and type(master) is dict
              and master.get("status")==AAC_STATUS
              and master.get("exact_original_mp4_sha256")==sha
              and master.get("source_pcm_duration_seconds_unchanged")==
                  ep.get("real_pcm_measured_seconds")
              and master.get("post_encode_measurement_source")==
                  "FINAL_ORIGINAL_AAC_INPUT_EBU_R128"
              and master.get("integrated_lufs_and_true_peak_within_internal_band")
                  is True
              and master.get("human_listening_and_mobile_playback_verified")
                  is False
              and master.get("rights_and_facts_approved") is False
              and master.get("youtube_upload_or_release_authorized") is False
              and master.get("source_narration_words_and_caption_cue_times_unchanged")
                  is True
              and master.get("original_procedural_sound_effect_timing_unchanged")
                  is True,
              "Missing verified SHA-bound final encoded AAC measurements")
        source_hashes.add(sha)
        lufs=master.get("measured_final_encoded_integrated_lufs")
        tp=master.get("measured_final_encoded_oversampled_true_peak_dbtp")
        lra=master.get("measured_final_encoded_loudness_range_lu")
        cps=ep.get("caption_peak_physical_chars_per_second")
        seconds=ep.get("real_pcm_measured_seconds")
        _need(_finite(lufs,ACCEPTED_INTEGRATED_LUFS_MIN,
                      ACCEPTED_INTEGRATED_LUFS_MAX)
              and _finite(tp,-80.0,ACCEPTED_TRUE_PEAK_DBTP_MAX)
              and _finite(lra,0.0,ACCEPTED_LRA_LU_MAX)
              and _finite(cps,0.0,150.0)
              and _finite(seconds,20.0,340.0)
              and ep.get("caption_reading_speed_needs_human_review")
                  is (cps>25.0),
              "Encoded audio/PCM caption measurements inconsistent or unbounded")
        lufs_values.append(lufs)
        items.append({
            "slot":slot,
            "actual_narrated_seconds":seconds,
            "encoded_aac_integrated_lufs":lufs,
            "encoded_aac_true_peak_dbtp":tp,
            "encoded_aac_loudness_range_lu":lra,
            "highest_caption_characters_per_second":cps,
            "fast_caption_pacing_needs_human_review":cps>25.0,
            "final_encoded_mp4_identity_rechecked_without_retaining_hash":True,
        })
    spread=round(max(lufs_values)-min(lufs_values),2)
    _need(_finite(report.get("actual_final_three_video_integrated_lufs_spread"),
                  0.0,ACCEPTED_THREE_VIDEO_LUFS_SPREAD_MAX)
          and spread==report["actual_final_three_video_integrated_lufs_spread"],
          "Cross-video AAC loudness spread disagrees with real measurements")
    result={
        "status":STATUS,
        "physical_original_videos_with_SHA_bound_final_AAC_measurements":3,
        "actual_original_scenes_in_full_decoded_videos":17,
        "final_encoded_aac_r128_loudness_spread_lu":spread,
        "episodes":items,
        "mp4_narration_script_title_url_or_source_text_retained":False,
        "extra_ffmpeg_or_paid_model_run_performed":False,
        "human_full_watch_or_audio_listening_verified":False,
        "news_claim_and_media_rights_approved":False,
        "youtube_uploads_and_release_authority":0,
        "no_rehearsal_video_retained_by_this_step":True,
        "read_only_engineering_QA_not_content_approval":True,
    }
    _need(len(json.dumps(result,allow_nan=False))<4500,
          "Unbounded public metrics-only summary")
    return result


def main() -> None:
    parser=argparse.ArgumentParser(
        description="Unapproved existing final AAC evidence; no media retention")
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    _need(args.report==REPORT_PATH
          and os.environ.get("GITHUB_ACTIONS")=="true"
          and os.environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
          and os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")=="0"
          and os.environ.get("PUBLISH_ENABLED")=="false"
          and os.environ.get("GITHUB_EVENT_NAME") in
              ("push","schedule","workflow_dispatch")
          and args.report.is_file() and not args.report.is_symlink()
          and 100<=args.report.stat().st_size<=512_000,
          "Unapproved or missing ephemeral physical report")
    try:
        source=json.loads(args.report.read_text("utf8"),
                         parse_constant=lambda _: (_ for _ in ()).throw(
                             MasterEvidenceRefused("Nonfinite physical source")))
    except (UnicodeError,json.JSONDecodeError):
        raise MasterEvidenceRefused("Malformed ephemeral physical report") from None
    summary=summarize_measured_ephemeral_masters(source)
    target=Path(os.environ.get("GITHUB_STEP_SUMMARY",""))
    _need(target.is_file() and not target.is_symlink(),
          "Cannot verify GitHub safe summary endpoint")
    lines=[
        "\n## Final encoded AAC QA — all 3 ephemeral rehearsals (NO PUBLISH)",
        "Existing SHA-bound **post-encode** R128/oversampled true-peak evidence "
        "was rechecked. This step does not re-encode or retain media.",
    ]
    for row in summary["episodes"]:
        lines.append(
            f"- {row['slot']}: {row['encoded_aac_integrated_lufs']} LUFS, "
            f"{row['encoded_aac_true_peak_dbtp']} dBTP, "
            f"{row['encoded_aac_loudness_range_lu']} LU LRA; "
            f"PCM {row['actual_narrated_seconds']}s; "
            f"caption peak {row['highest_caption_characters_per_second']} cps "
            f"({'HUMAN REVIEW' if row['fast_caption_pacing_needs_human_review'] else 'no peak-speed warning'})."
        )
    lines += [
        "Three-video LUFS spread: "+
            str(summary["final_encoded_aac_r128_loudness_spread_lu"])+" LU.",
        "**Not factual/rights approval, human listening, or a YouTube release.** "
        "No video, speech, URLs, titles, sources or SHA identities retained.",
    ]
    with target.open("a",encoding="utf8") as stream:
        stream.write("\n".join(lines)+"\n")
    print(json.dumps({
        "status":STATUS,
        "physical_encoded_aac_evidence":3,
        "original_scenes":17,
        "youtube_uploads":0,
        "release_authorized":False,
        "video_assets_retained":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
