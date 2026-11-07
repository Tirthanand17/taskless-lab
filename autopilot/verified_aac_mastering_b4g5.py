"""B4g5 loudness-correct original synthesized narration before FINAL AAC encode.

Actual B4g4 physical AAC reviews of the 2026-11-07 17-scene rehearsal gave
-26.16, -27.53, -24.46 LUFS, all quiet, while a local *cloud-container*
AAC reconstruction of the same three original clips with this FFmpeg pass
produced -18.25, -18.33, -18.14 LUFS and -1.42/-1.38/-1.42 dBTP.

These are tested loudness *targets*, NOT YouTube's official loudness rules.
Only original synthetic educational media; no rights/owner approval or release.
No external music/voice or write access to any online channel.
"""
from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path
import re
import subprocess

from autopilot.encoded_aac_loudness_review_b4g4 import (
    EncodedLoudnessRefused,
    parse_encoded_loudnorm,
)

STATUS = "B4G5_FINAL_ORIGINAL_AAC_TRUE_PEAK_LIMITED_LOUDNESS_VERIFIED_NO_PUBLISH"
# Feed FFmpeg's loudnorm into AAC. 'linear=false' intentionally applies the
# true-peak limiter when 8-10 dB gain would otherwise cause intersample clips.
# There are no imported media assets or background musical compositions.
LOUDNORM_TARGET_LUFS = -18.0
LOUDNORM_TRUE_PEAK_TARGET_DBTP = -1.5
LOUDNORM_LRA_TARGET_LU = 11
AUDIO_ENCODE_HZ = 48000
AUDIO_MASTERING_FILTER = (
    "loudnorm=I=-18:TP=-1.5:LRA=11:linear=false:print_format=none"
)
MEASUREMENT_FILTER = "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json"
# These are fail-closed engineering acceptance bands, not a platform standard.
ACCEPTED_INTEGRATED_LUFS_MIN = -20.5
ACCEPTED_INTEGRATED_LUFS_MAX = -15.5
ACCEPTED_TRUE_PEAK_DBTP_MAX = -1.0
ACCEPTED_LRA_LU_MAX = 18.0
ACCEPTED_THREE_VIDEO_LUFS_SPREAD_MAX = 4.0
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class EncodedMasteringRefused(ValueError):
    """Original encoded AAC cannot be proven safe for owner-only review."""


def _need(ok:bool, reason:str)->None:
    if not ok:
        raise EncodedMasteringRefused(reason)


def _hash_stream(path:Path)->str:
    h=sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def verify_exact_encoded_master(ffmpeg:str, mp4:Path, media_sha256:str,
                                actual_pcm_seconds:float, *,
                                runner=None)->dict:
    """Independent post-AAC decode; the source MP4 is never modified.

    A syntactically correct audio filter or valid pre-encode WAV does NOT
    prove the output AAC target. Require physically measured R128 input
    loudness and oversampled true-peak from the just-created exact video.
    """
    _need(type(ffmpeg) is str and bool(ffmpeg.strip()) and
          isinstance(mp4,Path) and mp4.is_file() and not mp4.is_symlink()
          and 300_000 <= mp4.stat().st_size <= 240_000_000
          and type(media_sha256) is str and
          HEX64.fullmatch(media_sha256) is not None and
          _hash_stream(mp4)==media_sha256 and
          type(actual_pcm_seconds) in (int,float)
          and math.isfinite(actual_pcm_seconds)
          and 20<=actual_pcm_seconds<=340,
          "Real encoded video identity or source PCM clock cannot be verified")
    run=subprocess.run if runner is None else runner
    try:
        process=run([
            ffmpeg,"-hide_banner","-nostdin","-nostats",
            "-i",str(mp4),"-map","0:a:0","-vn",
            "-af",MEASUREMENT_FILTER,
            "-ar","192000","-f","null","-",
        ],capture_output=True,text=True,check=False,timeout=240)
    except (OSError,subprocess.TimeoutExpired):
        raise EncodedMasteringRefused(
            "Independent final AAC decode/R128 measurement unavailable") from None
    _need(getattr(process,"returncode",None)==0 and
          type(getattr(process,"stderr",None)) is str,
          "Independent AAC EBU R128 measurement failed")
    try:
        actual=parse_encoded_loudnorm(process.stderr)
    except EncodedLoudnessRefused:
        raise EncodedMasteringRefused(
            "Final encoded AAC produced no finite input loudness") from None
    lufs=actual["measured_encoded_integrated_lufs"]
    tp=actual["measured_encoded_true_peak_dbtp"]
    lra=actual["measured_encoded_loudness_range_lu"]
    _need(ACCEPTED_INTEGRATED_LUFS_MIN<=lufs<=ACCEPTED_INTEGRATED_LUFS_MAX
          and tp<=ACCEPTED_TRUE_PEAK_DBTP_MAX
          and lra<=ACCEPTED_LRA_LU_MAX,
          "Final encoded audio falls outside conservative owner-review mastering band")
    return {
        "status":STATUS,
        "exact_original_mp4_sha256":media_sha256,
        "source_pcm_duration_seconds_unchanged":round(actual_pcm_seconds,3),
        "measured_final_encoded_integrated_lufs":lufs,
        "measured_final_encoded_oversampled_true_peak_dbtp":tp,
        "measured_final_encoded_loudness_range_lu":lra,
        "post_encode_measurement_source":"FINAL_ORIGINAL_AAC_INPUT_EBU_R128",
        "source_narration_words_and_caption_cue_times_unchanged":True,
        "original_procedural_sound_effect_timing_unchanged":True,
        "no_third_party_music_or_sample_introduced":True,
        "integrated_lufs_and_true_peak_within_internal_band":True,
        "human_listening_and_mobile_playback_verified":False,
        "rights_and_facts_approved":False,
        "youtube_upload_or_release_authorized":False,
    }


def verify_three_matching_masters(episodes:list[dict])->dict:
    """Reject one bad/outlier owner-review AAC before the three-MP4 export."""
    _need(type(episodes) is list and len(episodes)==3
          and [v.get("slot") for v in episodes]==["short_am","long","short_pm"],
          "The exact original 2 Shorts and 1 Long video are missing")
    values=[]
    for entry in episodes:
        report=entry.get("original_audio_encoded_mastering")
        _need(type(report) is dict and report.get("status")==STATUS
              and report.get("exact_original_mp4_sha256")==
                  entry.get("encoded_h264_aac_sha256")
              and report.get("source_pcm_duration_seconds_unchanged")==
                  entry.get("real_pcm_measured_seconds")
              and report.get("integrated_lufs_and_true_peak_within_internal_band")
                  is True
              and report.get("human_listening_and_mobile_playback_verified")
                  is False
              and report.get("youtube_upload_or_release_authorized") is False,
              "One of the three final encoded audio mastering proofs is absent")
        values.append(report["measured_final_encoded_integrated_lufs"])
    _need(all(type(v) in (int,float) and math.isfinite(v)
              for v in values),"Invalid final original cross-video loudness")
    spread=round(max(values)-min(values),2)
    _need(spread<=ACCEPTED_THREE_VIDEO_LUFS_SPREAD_MAX,
          "Loudness inconsistent between two Shorts and original long")
    return {
        "all_three_final_encoded_aac_masters_in_conservative_range":True,
        "actual_final_three_video_integrated_lufs_spread":spread,
        "original_rehearsal_owner_listening_completed":False,
        "youtube_release_authorized":False,
    }
