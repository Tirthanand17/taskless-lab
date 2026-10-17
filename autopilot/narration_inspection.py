"""Local FFprobe/FFmpeg inspector for a real narration audio file.

Technical stream validity is NOT natural-human-voice quality, permissions,
pronunciation or language accuracy. No audio is uploaded or synthesized.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import math
import subprocess

@dataclass(frozen=True)
class AudioEvidence:
    status: str
    sha256_hex: str | None
    duration_seconds: float | None
    sample_rate_hz: int | None
    channels: int | None
    problems: tuple[str, ...]
    narration_naturalness_verified: bool = False
    commercial_rights_verified: bool = False
    publishing_authorized: bool = False

def reject(problem: str) -> AudioEvidence:
    return AudioEvidence("BLOCKED_AUDIO_TECHNICAL_QA",None,None,None,None,(problem,))

def inspect_narration(path: str | Path,*,expected_duration_s:float|None=None,
                      duration_tolerance_s:float=1.5,
                      size_ceiling:int=256_000_000,
                      timeout_s:int=90)->AudioEvidence:
    if (type(size_ceiling) is not int or not 1<=size_ceiling<=256_000_000
            or type(timeout_s) is not int or not 1<=timeout_s<=600
            or not 0<=duration_tolerance_s<=5
            or (expected_duration_s is not None and not 1<=expected_duration_s<=3600)):
        return reject("INVALID_INSPECTION_POLICY")
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        return reject("UNSAFE_OR_MISSING_AUDIO")
    if not 0<p.stat().st_size<=size_ceiling:
        return reject("AUDIO_SIZE_OUT_OF_BOUNDS")
    try:
        probe=subprocess.run([
            "ffprobe","-v","error",
            "-show_entries","stream=codec_type,codec_name,sample_rate,channels:format=duration",
            "-of","json",str(p)],capture_output=True,text=True,timeout=timeout_s,check=False)
        if probe.returncode!=0:
            return reject("FFPROBE_REJECTED_AUDIO")
        payload=json.loads(probe.stdout)
        streams=payload["streams"]
        audio=[s for s in streams if s.get("codec_type")=="audio"]
        if len(audio)!=1 or len(streams)!=1:
            return reject("AUDIO_STREAM_COUNT_INVALID")
        info=audio[0]
        seconds=float(payload["format"]["duration"])
        hz=int(info["sample_rate"])
        channels=int(info["channels"])
        issues=[]
        if not math.isfinite(seconds) or not 1<=seconds<=3600:
            issues.append("AUDIO_DURATION_INVALID")
        if expected_duration_s is not None and abs(seconds-expected_duration_s)>duration_tolerance_s:
            issues.append("AUDIO_TIMING_DIFFERS_FROM_PLAN")
        if hz<16000 or hz>192000 or channels not in (1,2):
            issues.append("AUDIO_STREAM_PARAMETERS_UNEXPECTED")
        if not info.get("codec_name"):
            issues.append("AUDIO_CODEC_MISSING")
        decode=subprocess.run([
            "ffmpeg","-hide_banner","-nostdin","-i",str(p),
            "-af","silencedetect=noise=-45dB:d=0.7",
            "-f","null","-"],capture_output=True,text=True,timeout=timeout_s,check=False)
        if decode.returncode!=0:
            issues.append("AUDIO_FULL_DECODE_FAILED")
        if "silence_start:" in decode.stderr:
            issues.append("SIGNIFICANT_SILENCE_REQUIRES_REVIEW")
        h=sha256()
        with p.open("rb") as file:
            for data in iter(lambda:file.read(1024*1024),b""):
                h.update(data)
        return AudioEvidence(
            "PASS_AUDIO_TECHNICAL_ONLY" if not issues else "BLOCKED_AUDIO_TECHNICAL_QA",
            h.hexdigest(),seconds,hz,channels,tuple(sorted(set(issues))))
    except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired,json.JSONDecodeError):
        return reject("AUDIO_INSPECTION_UNAVAILABLE")
