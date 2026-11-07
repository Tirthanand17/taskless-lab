"""B4g4 exact SHA-bound original MP4 loudness/true-peak measurements.

Runs FFmpeg loudnorm in ANALYZE-ONLY mode: it decodes an existing encoded
AAC stream to the null output and reads the 'input_*' EBU R128 statistics.
The filter's normalized 'output_*' metrics are NOT used, and it never writes
a replacement MP4 or authorizes release. No YouTube, music, user audio or SDK.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess

from autopilot.manual_rehearsal_review_export_b4e3 import (
    EXPORT_STATUS, SLOT_NAMES,
)
from autopilot.rehearsal_encoded_signal_review_b4f4 import _ffmpeg_exe, _sha_file

STATUS="B4G4_REAL_ENCODED_AAC_R128_AND_TRUE_PEAK_OWNER_REVIEW_ONLY"
REPORT_NAME="ENCODED_AAC_LOUDNESS_TRUE_PEAK_UNAPPROVED.json"
SCRIPT_KEY="input_i"
SHA=re.compile(r"[0-9a-f]{64}\Z")
LOUDFIELD=("input_i","input_tp","input_lra","input_thresh")
TARGET_FILTER="loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json"
MAX_FFMPEG_TEXT=160_000

class EncodedLoudnessRefused(ValueError):
    """Missing/altered owner media, undecodable audio, or unsafe stats."""


def _need(ok:bool,why:str)->None:
    if not ok:
        raise EncodedLoudnessRefused(why)


def _as_finite(raw:object,lo:float,hi:float)->float:
    _need(type(raw) in (str,int,float) and type(raw) is not bool,
          "Missing or invalid R128 numeric measurement")
    try:
        x=float(raw)
    except (TypeError,ValueError):
        raise EncodedLoudnessRefused("R128 field is not a number") from None
    _need(math.isfinite(x) and lo<=x<=hi,
          "Silence, infinity or physically invalid R128 measurement")
    return round(x,2)


def parse_encoded_loudnorm(stderr:str)->dict:
    """Parse ONE real FFmpeg loudnorm JSON block; never echo raw stderr."""
    _need(type(stderr) is str and
          80<=len(stderr.encode("utf8"))<=MAX_FFMPEG_TEXT,
          "Missing or oversized real decoded-audio measurement")
    anchors=list(re.finditer(r'\{\s*"input_i"\s*:',stderr))
    _need(len(anchors)==1,"Expected exactly one FFmpeg R128 input report")
    try:
        values,end=json.JSONDecoder().raw_decode(stderr[anchors[0].start():])
    except (json.JSONDecodeError,ValueError):
        raise EncodedLoudnessRefused(
            "FFmpeg R128 report was malformed") from None
    _need(type(values) is dict and
          all(k in values for k in LOUDFIELD) and
          values.get("normalization_type") in ("linear","dynamic") and
          "output_i" in values and "output_tp" in values,
          "Not a complete actual loudnorm R128 JSON report")
    integrated=_as_finite(values["input_i"],-70,0)
    true_peak=_as_finite(values["input_tp"],-90,15)
    lra=_as_finite(values["input_lra"],0,70)
    threshold=_as_finite(values["input_thresh"],-100,0)
    _need(threshold<=integrated+2 and lra>=0,
          "Physically inconsistent R128 loudness report")
    warning_codes=[]
    if true_peak > -1.0:
        warning_codes.append("TRUE_PEAK_ABOVE_REVIEW_CEILING")
    if integrated < -23.0:
        warning_codes.append("INTEGRATED_LOUDNESS_QUIET_CHECK_ON_PHONE")
    if integrated > -11.0:
        warning_codes.append("INTEGRATED_LOUDNESS_HOT_CHECK_ON_PHONE")
    if lra > 18.0:
        warning_codes.append("LOUDNESS_RANGE_WIDE_REVIEW_DYNAMICS")
    return {
        "measured_encoded_integrated_lufs":integrated,
        "measured_encoded_true_peak_dbtp":true_peak,
        "measured_encoded_loudness_range_lu":lra,
        "measured_encoded_relative_gate_threshold_lufs":threshold,
        "warnings":warning_codes,
        "measurement_is_actual_input_aac_not_normalized_output":True,
        "automatic_gain_normalization_or_limiting_applied":False,
        "perceived_mobile_loudness_or_intelligibility_verified":False,
        "human_audio_playback_review_completed":False,
        "publication_authorized":False,
    }


def inspect_exact_three_mp4s(folder:Path, *,ffmpeg:str|None=None,
                             runner=None)->dict:
    """Validate original owner export SHA before each independent decode."""
    _need(isinstance(folder,Path) and folder.is_dir() and
          not folder.is_symlink(),"Invalid owner review directory")
    manifest_path=folder/"REVIEW_ONLY_NO_PUBLISH.json"
    _need(manifest_path.is_file() and not manifest_path.is_symlink() and
          200<=manifest_path.stat().st_size<=24000,
          "Missing original SHA-bound unapproved media manifest")
    try:
        manifest=json.loads(manifest_path.read_text(encoding="utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise EncodedLoudnessRefused("Unsafe owner manifest") from None
    _need(type(manifest) is dict and
          manifest.get("status")==EXPORT_STATUS and
          manifest.get("publishing_authorized") is False and
          manifest.get("youtube_releases")==0 and
          manifest.get("rights_and_owner_approvals")==0 and
          type(manifest.get("videos")) is list and
          len(manifest["videos"])==3,
          "Unexpected source rights or publishing state")
    binary=_ffmpeg_exe() if ffmpeg is None else ffmpeg
    _need(type(binary) is str and bool(binary.strip()),
          "Missing trusted FFmpeg binary")
    execute=subprocess.run if runner is None else runner
    records=[]
    for (slot,file,count),source in zip(SLOT_NAMES,manifest["videos"]):
        _need(type(source) is dict and
              source.get("slot")==slot and
              source.get("file")==file and
              source.get("original_voiced_scene_count")==count and
              type(source.get("sha256")) is str and
              SHA.fullmatch(source["sha256"]) is not None and
              type(source.get("measured_audio_seconds")) in (int,float)
              and 20<=source["measured_audio_seconds"]<=340 and
              source.get("youtube_upload_authorized") is False,
              "Encoded MP4 is not the approved-for-review original")
        media=folder/file
        _need(media.is_file() and not media.is_symlink()
              and 300_000<=media.stat().st_size<=240_000_000
              and _sha_file(media)==source["sha256"],
              "Original MP4 hash changed before EBU R128 measurement")
        try:
            process=execute([
                binary,"-hide_banner","-nostdin","-nostats",
                "-i",str(media),"-map","0:a:0","-vn",
                "-af",TARGET_FILTER,"-ar","192000",
                "-f","null","-",
            ],capture_output=True,text=True,check=False,timeout=230)
        except (OSError,subprocess.TimeoutExpired):
            raise EncodedLoudnessRefused(
                "Cannot decode full original AAC audio for measurement") from None
        _need(getattr(process,"returncode",None)==0 and
              type(getattr(process,"stderr",None)) is str,
              "FFmpeg encoded AAC measurement process failed")
        parsed=parse_encoded_loudnorm(process.stderr)
        records.append({
            "slot":slot,
            "source_mp4_sha256":source["sha256"],
            "original_voiced_scene_count":count,
            "source_duration_pcm_seconds":source["measured_audio_seconds"],
            **parsed,
        })
    levels=[x["measured_encoded_integrated_lufs"] for x in records]
    delta=round(max(levels)-min(levels),2)
    return {
        "status":STATUS,
        "videos_measured_from_real_encoded_aac":3,
        "original_narrated_scenes_represented":17,
        "videos":records,
        "three_video_integrated_lufs_spread":delta,
        "three_video_consistency_warning":(
            "THREE_VIDEO_LEVEL_MISMATCH_LISTEN_AND_REVIEW"
            if delta>5.0 else None),
        "measurement_method":"FFMPEG_LOUDNORM_INPUT_R128_OVERSAMPLED_TRUE_PEAK",
        "normalization_filter_output_was_discarded_not_reencoded":True,
        "human_audio_playback_reviews":0,
        "factual_and_media_rights_approvals":0,
        "youtube_writes_or_release_authority":0,
    }


def main()->None:
    parser=argparse.ArgumentParser(description="Real encoded AAC loudness review only")
    parser.add_argument("--review-dir",required=True,type=Path)
    args=parser.parse_args()
    _need(os.environ.get("GITHUB_EVENT_NAME")=="workflow_dispatch"
          and os.environ.get("GITHUB_REF")=="refs/heads/main"
          and os.environ.get("FLOWMINUTE_EXPLICIT_REVIEW_OPT_IN")=="true"
          and args.review_dir==Path("/tmp/flowminute-b4e3-unapproved-owner-review"),
          "Loudness report only for explicitly selected owner review")
    result=inspect_exact_three_mp4s(args.review_dir)
    out=args.review_dir/REPORT_NAME
    _need(not out.exists() and not out.is_symlink(),
          "An existing loudness report must never be overwritten")
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",
                   encoding="utf8")
    print(json.dumps({
        "status":STATUS,
        "actual_encoded_aac_streams_analyzed":3,
        "cross_video_lufs_spread":result["three_video_integrated_lufs_spread"],
        "audio_listen_approvals":0,
        "youtube_video_writes":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
