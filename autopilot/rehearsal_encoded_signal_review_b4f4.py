"""B4f4 FFmpeg encoded-media signal diagnostics for owner review ONLY.

Runs only on 3 explicitly opted-in, original synthetic educational MP4 files.
Inspects the REAL final encoded audio/video, not intermediate PNGs or scripts:
black frames, frozen frames, long audio silence and sample peak. Detection
is advisory (static diagrams/speech pauses may be intentional). Never claims
human viewing, factual verification, rights clearance or YouTube approval.

No network, no subprocess shell, no raw frames, no audio files, no source
excerpts, no secrets, no uploaded media beyond the existing explicit artifact.
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

REPORT_NAME = "ENCODED_MP4_SIGNAL_WARNINGS_UNAPPROVED.json"
STATUS = "B4F4_FINAL_ENCODED_AV_SIGNAL_DIAGNOSTICS_OWNER_REVIEW_ONLY"
MAX_SCAN_SECONDS = 360
MAX_LOG_BYTES = 350_000
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
BLACK = re.compile(r"black_start:([0-9]+(?:\.[0-9]+)?)\s+black_end:([0-9]+(?:\.[0-9]+)?)\s+black_duration:([0-9]+(?:\.[0-9]+)?)")
FREEZE_START = re.compile(r"freeze_start:\s*([0-9]+(?:\.[0-9]+)?)")
FREEZE_END = re.compile(r"freeze_end:\s*([0-9]+(?:\.[0-9]+)?)\s*\|\s*freeze_duration:\s*([0-9]+(?:\.[0-9]+)?)")
SILENCE = re.compile(r"silence_end:\s*([0-9]+(?:\.[0-9]+)?)\s*\|\s*silence_duration:\s*([0-9]+(?:\.[0-9]+)?)")
PEAK = re.compile(r"max_volume:\s*(-?(?:[0-9]+(?:\.[0-9]+)?|inf))\s*dB")
MEAN = re.compile(r"mean_volume:\s*(-?(?:[0-9]+(?:\.[0-9]+)?|inf))\s*dB")


class SignalReviewRefused(ValueError):
    """Actual media identity/decoder/diagnostic mismatch: do not export QA."""


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise SignalReviewRefused(message)


def _finite(raw: str, limit: float) -> float:
    try:
        x = float(raw)
    except (TypeError, ValueError):
        raise SignalReviewRefused("Invalid FFmpeg measurement") from None
    _need(math.isfinite(x) and 0 <= x <= limit, "FFmpeg measurement out of range")
    return x


def _periods(matches, duration: float, *, minimum: float) -> list[dict]:
    periods=[]
    for start,end,length in matches:
        a,b,n=(_finite(start,MAX_SCAN_SECONDS+1),
               _finite(end,MAX_SCAN_SECONDS+1),
               _finite(length,MAX_SCAN_SECONDS+1))
        _need(0 <= a < b <= duration+2 and abs((b-a)-n)<0.45,
              "Impossible FFmpeg interval")
        if n >= minimum:
            periods.append({"start_seconds":round(a,2),
                            "end_seconds":round(b,2),
                            "duration_seconds":round(n,2)})
    _need(len(periods) <= 80, "Unbounded anomaly intervals")
    return periods


def parse_ffmpeg_signals(stderr: str, *, duration: float) -> dict:
    """Strictly parse one actual FFmpeg full-video decode/filter stderr."""
    _need(type(stderr) is str and 150 <= len(stderr.encode("utf8")) <= MAX_LOG_BYTES,
          "Missing or oversized FFmpeg decoder observation")
    _need(type(duration) in (int,float) and 20 <= duration <= MAX_SCAN_SECONDS,
          "Unsafe physical video duration")
    _need("video:" in stderr and "audio:" in stderr,
          "FFmpeg media stream summary absent")
    blacks = _periods(BLACK.findall(stderr), duration, minimum=0.8)
    silences=[]
    for end,length in SILENCE.findall(stderr):
        b=_finite(end,MAX_SCAN_SECONDS+1)
        n=_finite(length,MAX_SCAN_SECONDS+1)
        _need(n<=b and b <= duration+2,"Invalid audio silence interval")
        if n >= 1.6:
            silences.append({"start_seconds":round(b-n,2),
                             "end_seconds":round(b,2),
                             "duration_seconds":round(n,2)})
    _need(len(silences)<=80,"Unbounded speech silence observations")

    starts=[_finite(x,MAX_SCAN_SECONDS+1) for x in FREEZE_START.findall(stderr)]
    ends=[(_finite(b,MAX_SCAN_SECONDS+1),
           _finite(n,MAX_SCAN_SECONDS+1))
          for b,n in FREEZE_END.findall(stderr)]
    # FFmpeg can leave the final freeze unfinished (no freeze_end).
    _need(len(starts) <= 80 and len(ends)<=len(starts),
          "Unbounded/malformed freeze record")
    freezes=[]
    for i,(b,n) in enumerate(ends):
        if i >= len(starts):
            raise SignalReviewRefused("Unmatched freeze interval")
        a=starts[i]
        _need(a < b <= duration+2 and abs((b-a)-n)<0.45,
              "Implausible freeze interval")
        if n>=5:
            freezes.append({"start_seconds":round(a,2),
                            "end_seconds":round(b,2),
                            "duration_seconds":round(n,2)})
    if len(starts)>len(ends):
        _need(len(starts)==len(ends)+1,"Unmatched freeze start")
        a=starts[-1]
        _need(a<=duration+1,"Freeze starts outside video duration")
        if duration-a>=5:
            freezes.append({"start_seconds":round(a,2),
                            "end_seconds":round(duration,2),
                            "duration_seconds":round(duration-a,2),
                            "unfinished_at_video_end":True})

    peaks=PEAK.findall(stderr)
    means=MEAN.findall(stderr)
    _need(len(peaks)==1 and len(means)==1, "Audio sample volume not measured")
    try:
        sample_peak=float(peaks[0])
        sample_mean=float(means[0])
    except ValueError:
        raise SignalReviewRefused("Bad sample audio measurements") from None
    _need(math.isfinite(sample_peak) and math.isfinite(sample_mean)
          and -100 <= sample_mean <= sample_peak <= 6,
          "Invalid or silent encoded audio")
    warning_codes=[]
    if blacks: warning_codes.append("BLACK_SEGMENT_REVIEW")
    if freezes: warning_codes.append("POTENTIALLY_STATIC_OR_FROZEN_VISUAL_REVIEW")
    if silences: warning_codes.append("LONG_SILENCE_LISTEN_AND_CHECK")
    if sample_peak >= -0.15: warning_codes.append("SAMPLE_PEAK_NEAR_ZERO_CLIPPING_RISK")
    if sample_mean < -31: warning_codes.append("AVERAGE_AUDIO_VERY_QUIET_CHECK")
    return {
        "black_intervals":blacks,
        "freeze_intervals":freezes,
        "audio_silence_intervals":silences,
        "sample_peak_dbfs_not_true_peak":round(sample_peak,2),
        "sample_mean_dbfs_not_integrated_lufs":round(sample_mean,2),
        "warning_codes":warning_codes,
        "technical_anomaly_detector_is_not_a_human_judgment":True,
        "human_full_audio_visual_watch_completed":False,
        "final_rights_or_facts_approved":False,
    }


def _sha_file(path: Path) -> str:
    hasher=sha256()
    with path.open("rb") as stream:
        for part in iter(lambda:stream.read(1024*1024),b""):
            hasher.update(part)
    return hasher.hexdigest()


def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError,RuntimeError,OSError):
        raise SignalReviewRefused("Pinned FFmpeg executable unavailable") from None


def inspect_review_directory(
    folder: Path, *, ffmpeg: str | None = None, runner=None,
) -> dict:
    """Inspect three exact exported MP4 hashes; never follow other paths."""
    _need(isinstance(folder, Path) and folder.is_dir() and not folder.is_symlink(),
          "Invalid owner-review artifact folder")
    manifest_path=folder/"REVIEW_ONLY_NO_PUBLISH.json"
    _need(manifest_path.is_file() and not manifest_path.is_symlink()
          and 200<=manifest_path.stat().st_size<=24000,
          "Official unapproved review manifest missing")
    try:
        manifest=json.loads(manifest_path.read_text(encoding="utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise SignalReviewRefused("Invalid review manifest") from None
    _need(type(manifest) is dict and manifest.get("status")==EXPORT_STATUS
          and manifest.get("publishing_authorized") is False
          and manifest.get("youtube_releases")==0
          and manifest.get("rights_and_owner_approvals")==0
          and type(manifest.get("videos")) is list
          and len(manifest["videos"])==3,
          "Only exact 3-video unapproved human review media accepted")
    inspect_run=subprocess.run if runner is None else runner
    binary=_ffmpeg_exe() if ffmpeg is None else ffmpeg
    _need(type(binary) is str and binary.strip() != "",
          "Missing trusted FFmpeg binary")
    entries=[]
    for (slot,filename,scene_count),source in zip(SLOT_NAMES,manifest["videos"]):
        _need(type(source) is dict
              and source.get("slot")==slot and source.get("file")==filename
              and source.get("original_voiced_scene_count")==scene_count
              and type(source.get("sha256")) is str
              and HEX64.fullmatch(source["sha256"]) is not None
              and type(source.get("measured_audio_seconds")) in (int,float)
              and 20<=source["measured_audio_seconds"]<=MAX_SCAN_SECONDS
              and source.get("youtube_upload_authorized") is False,
              "Wrong media manifest identity, scenes or simulated authority")
        video=folder/filename
        _need(video.is_file() and not video.is_symlink()
              and 300_000<=video.stat().st_size<=240_000_000
              and _sha_file(video)==source["sha256"],
              "Encoded MP4 changed since review-export hash")
        try:
            process=inspect_run(
                [binary,"-hide_banner","-nostdin","-nostats",
                 "-i",str(video),
                 "-map","0:v:0","-map","0:a:0",
                 "-vf","blackdetect=d=0.8:pix_th=0.1:pic_th=0.99,"
                       "freezedetect=n=-60dB:d=5",
                 "-af","silencedetect=noise=-48dB:d=1.6,volumedetect",
                 "-f","null","-"],
                capture_output=True,text=True,check=False,timeout=230,
            )
        except (OSError,subprocess.TimeoutExpired):
            raise SignalReviewRefused("Actual MP4 decode/technical filters failed") from None
        _need(process.returncode==0 and type(process.stderr) is str,
              "FFmpeg full encoded MP4 decode failed")
        metrics=parse_ffmpeg_signals(
            process.stderr,duration=source["measured_audio_seconds"])
        entries.append({
            "slot":slot,
            "original_voiced_scene_count":scene_count,
            "source_mp4_sha256":source["sha256"],
            "measured_pcm_seconds":source["measured_audio_seconds"],
            **metrics,
        })
    return {
        "status":STATUS,
        "physical_original_encoded_mp4s_independently_decoded_for_signals":3,
        "original_scenes_represented":17,
        "videos":entries,
        "warnings_require_real_owner_playback":True,
        "sample_peak_is_not_oversampled_true_peak":True,
        "audio_quietness_is_not_integrated_lufs":True,
        "human_full_video_reviews":0,
        "factual_and_rights_approvals":0,
        "youtube_uploads_or_release_authority":0,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description="Review-only FFmpeg final MP4 signal diagnostics")
    parser.add_argument("--review-dir",type=Path,required=True)
    args=parser.parse_args()
    _need(os.environ.get("GITHUB_EVENT_NAME")=="workflow_dispatch"
          and os.environ.get("FLOWMINUTE_EXPLICIT_REVIEW_OPT_IN")=="true"
          and os.environ.get("GITHUB_REF")=="refs/heads/main",
          "No diagnostic generation without owner-explicit manual review opt-in")
    result=inspect_review_directory(args.review_dir)
    out=args.review_dir/REPORT_NAME
    _need(not out.exists() and not out.is_symlink(),
          "Existing signal diagnostic file must not be overwritten")
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({
        "status":STATUS,
        "videos_decoded":3,
        "black_events":sum(len(v["black_intervals"]) for v in result["videos"]),
        "freeze_events":sum(len(v["freeze_intervals"]) for v in result["videos"]),
        "silence_events":sum(len(v["audio_silence_intervals"]) for v in result["videos"]),
        "actual_human_watches":0,
        "youtube_uploads":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
