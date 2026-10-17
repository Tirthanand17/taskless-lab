"""Inspect an actual FFmpeg media file; NEVER grant publishing permission.

No credentials, network, cloud providers or YouTube uploads are involved.
Media technical PASS does not imply content, speech, subtitles or rights QA.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import math
import subprocess

@dataclass(frozen=True)
class MediaEvidence:
    status: str
    video_sha256: str | None
    width: int | None
    height: int | None
    duration_seconds: float | None
    fps: float | None
    has_audio: bool
    issues: tuple[str,...]
    publishing_cleared: bool = False
    video_codec: str | None = None
    audio_codec: str | None = None

def _run(args: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args,capture_output=True,text=True,timeout=timeout_seconds,check=False)

def _invalid(*issues: str) -> MediaEvidence:
    return MediaEvidence('BLOCKED_TECHNICAL_QA',None,None,None,None,None,False,tuple(issues))

def inspect_media(path: str | Path, *, expected_width: int, expected_height: int,
                  min_duration_s: float, max_duration_s: float,
                  max_bytes: int = 1_073_741_824, timeout_seconds: int = 120) -> MediaEvidence:
    """FFprobe streams, FFmpeg full-decode, SHA256; safely report only metadata.

    Does not verify human narration, dialogue, actual subtitles, copyright,
    content accuracy, frame-level text legibility, user consent or publication.
    """
    if not (0 < expected_width <= 8192 and 0 < expected_height <= 8192 and
            0 < min_duration_s <= max_duration_s <= 3600 and
            0 < max_bytes <= 1_073_741_824 and 1 <= timeout_seconds <= 600):
        return _invalid('INVALID_INSPECTION_POLICY')
    file=Path(path)
    if not file.is_file() or file.is_symlink():
        return _invalid('MISSING_OR_UNSAFE_MEDIA')
    size=file.stat().st_size
    if not (0 < size <= max_bytes):
        return _invalid('MEDIA_SIZE_OUT_OF_BOUNDS')
    try:
        probe=_run(['ffprobe','-v','error','-show_entries',
                    'stream=index,codec_type,codec_name,width,height,r_frame_rate:format=duration,format_name',
                    '-of','json',str(file)],timeout_seconds)
        if probe.returncode != 0:
            return _invalid('FFPROBE_FAILED')
        parsed=json.loads(probe.stdout)
        videos=[s for s in parsed.get('streams',[]) if s.get('codec_type')=='video']
        audio=[s for s in parsed.get('streams',[]) if s.get('codec_type')=='audio']
        if len(videos)!=1 or len(audio)!=1:
            return _invalid('VIDEO_AUDIO_STREAM_COUNT_INVALID')
        video=videos[0]
        width,height=int(video['width']),int(video['height'])
        duration=float(parsed['format']['duration'])
        fps=float(Fraction(video['r_frame_rate']))
        issues=[]
        if (width,height)!=(expected_width,expected_height):issues.append('DIMENSIONS_INCORRECT')
        if not math.isfinite(duration) or not min_duration_s<=duration<=max_duration_s:
            issues.append('DURATION_INCORRECT')
        if not math.isfinite(fps) or not 20<=fps<=60:issues.append('FRAME_RATE_OUT_OF_BOUNDS')
        video_codec=video.get('codec_name')
        audio_codec=audio[0].get('codec_name')
        if video_codec!='h264' or audio_codec!='aac':
            issues.append('OUTPUT_CODEC_NOT_H264_AAC')
        if 'mp4' not in parsed.get('format',{}).get('format_name','').split(','):
            issues.append('OUTPUT_CONTAINER_NOT_MP4')
        decode=_run(['ffmpeg','-hide_banner','-nostdin','-i',str(file),
                     '-vf','blackdetect=d=0.5:pix_th=0.09',
                     '-af','silencedetect=noise=-45dB:d=0.7',
                     '-f','null','-'],timeout_seconds)
        if decode.returncode != 0:issues.append('FULL_DECODE_FAILED')
        if 'black_start:' in decode.stderr:issues.append('BLACK_VIDEO_SEGMENT_REVIEW')
        if 'silence_start:' in decode.stderr:issues.append('AUDIO_SILENCE_SEGMENT_REVIEW')
        h=sha256()
        with file.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
        return MediaEvidence('PASS_TECHNICAL_ONLY' if not issues else 'BLOCKED_TECHNICAL_QA',
                             h.hexdigest(),width,height,duration,round(fps,3),True,
                             tuple(sorted(set(issues))),False,video_codec,audio_codec)
    except (OSError,subprocess.TimeoutExpired,json.JSONDecodeError,
            ValueError,KeyError,ZeroDivisionError,TypeError):
        return _invalid('MEDIA_INSPECTION_UNAVAILABLE')
