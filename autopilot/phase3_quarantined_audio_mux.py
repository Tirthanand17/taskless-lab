"""Phase 3R3: REAL audiovisual mux TECHNICAL proof, permanently NOT publishable.

Combines a pre-existing silent visual-only MP4 and a caller-supplied PCM16 WAV
using already installed FFmpeg. Strictly bounds inputs; checks actual streams,
length and decode. A synthetic tone can pass technical QA but is NEVER speech.
An output from this module may not pass FlowMinute editorial/publisher gates.
No voice generation, third-party connection, credentials, upload, or scheduling.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import subprocess

from .agent_org import WorkflowError
from .phase3_voice_subtitle_handoff import inspect_external_voice_wav
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv

EPISODES={
    "csv_tutorial_short_en": ("en","short","narrator_english_b"),
    "csv_tutorial_short_hi": ("hi","short","narrator_hindi_a"),
    "csv_tutorial_long_hi": ("hi","long","narrator_hindi_long_c"),
}
MAX_VIDEO_BYTES=90_000_000
MAX_QA_SECONDS=8.0


def _strict_local(path: Path, *, allowed_suffix: str, max_bytes: int) -> Path:
    if (not isinstance(path,Path) or path.is_symlink() or not path.is_file()
            or path.suffix.lower()!=allowed_suffix
            or not 44<=path.stat().st_size<=max_bytes):
        raise WorkflowError("Existing ordinary bounded local media input required")
    return path


def _ffprobe(path: Path) -> dict:
    if shutil.which("ffprobe") is None:
        raise WorkflowError("FFprobe required on local/provisioned runner")
    try:
        process=subprocess.run([
            "ffprobe","-v","error","-show_entries",
            "format=duration,format_name:stream=index,codec_type,codec_name,width,height,duration",
            "-of","json",str(path)],
            capture_output=True,text=True,check=True,timeout=20)
        if len(process.stdout)>30_000:
            raise WorkflowError("Excessive FFprobe response")
        data=json.loads(process.stdout)
    except (OSError,ValueError,subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        raise WorkflowError("Failed to read audio-video metadata") from exc
    if not isinstance(data,dict) or not isinstance(data.get("streams"),list):
        raise WorkflowError("Media metadata malformed")
    return data


def _media_duration(probe: dict) -> float:
    try:
        duration=float(probe["format"]["duration"])
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        raise WorkflowError("Media has no numeric duration") from exc
    if not math.isfinite(duration) or not 0.25<=duration<=MAX_QA_SECONDS:
        raise WorkflowError("Only bounded test-clip durations are supported")
    return duration


def mux_visual_with_external_wav(
    *, episode_id: str, video_path: Path, wav_path: Path, output_path: Path
) -> dict:
    """Actual H.264 silent visual + WAV -> AAC MP4 proof, **QA-ONLY**.

    Does not create directories, overwrite outputs, follow input symlinks,
    install tools or retain captions/voice in public logs. The returned
    source/rights/speech/upload flags are ALWAYS false, irrespective of codecs.
    """
    if episode_id not in EPISODES:
        raise WorkflowError("Unknown or unreviewed episode")
    if shutil.which("ffmpeg") is None:
        raise WorkflowError("Local FFmpeg required, never auto-install here")
    language,kind,narrator=EPISODES[episode_id]
    video=_strict_local(video_path,allowed_suffix=".mp4",max_bytes=MAX_VIDEO_BYTES)
    voice=_strict_local(wav_path,allowed_suffix=".wav",max_bytes=70_000_000)
    output=Path(output_path)
    if (output.suffix.lower()!=".mp4" or output.exists() or output.is_symlink()
            or not output.parent.is_dir()
            or output.resolve()==video.resolve()):
        raise WorkflowError("A fresh MP4 in an existing local folder is required")
    probe=_ffprobe(video)
    duration=_media_duration(probe)
    streams=probe["streams"]
    visual=[x for x in streams if x.get("codec_type")=="video"]
    audio=[x for x in streams if x.get("codec_type")=="audio"]
    expected_shape=((9,16) if kind=="short" else (16,9))
    if len(visual)!=1 or audio or len(streams)!=1 or visual[0].get("codec_name")!="h264":
        raise WorkflowError("Video input must be a single silent H.264 stream")
    try:
        w,h=int(visual[0]["width"]),int(visual[0]["height"])
    except (TypeError,ValueError,KeyError) as exc:
        raise WorkflowError("Video dimensions unavailable") from exc
    if (w<320 or h<320 or w*h>1920*1080
            or w*expected_shape[1]!=h*expected_shape[0]):
        raise WorkflowError("Wrong episode aspect ratio or excessive visual geometry")
    # Real file inspection, *not* independent narration, language or rights QA.
    wav_report=inspect_external_voice_wav(
        voice,episode_id=episode_id,expected_seconds=duration,
        declared_narrator_id=narrator,declared_language=language)
    _=build_subtitles_from_authored_csv()[episode_id]["srt_sha256"]
    # Subtitles remain an unaligned draft; do not permanently burn them into
    # potentially mistimed clips or accidentally call them speech-sync verified.
    cmd=[
        "ffmpeg","-nostdin","-v","error","-xerror","-n",
        "-i",str(video),"-i",str(voice),
        "-map","0:v:0","-map","1:a:0",
        "-c:v","copy","-c:a","aac","-b:a","96k",
        "-ar","48000","-ac","2",
        "-t",f"{duration:.3f}","-movflags","+faststart",
        "-metadata","comment=UNREVIEWED_SYNTHETIC_OR_UNKNOWN_AUDIO_QA_ONLY",
        str(output)
    ]
    try:
        proc=subprocess.run(cmd,stdin=subprocess.DEVNULL,
                            capture_output=True,check=False,timeout=70)
        if proc.returncode!=0:
            raise WorkflowError("FFmpeg audiovisual mux failed")
        result=_strict_local(output,allowed_suffix=".mp4",max_bytes=MAX_VIDEO_BYTES)
        candidate=_ffprobe(result)
        candidate_duration=_media_duration(candidate)
        v=[s for s in candidate["streams"] if s.get("codec_type")=="video"]
        a=[s for s in candidate["streams"] if s.get("codec_type")=="audio"]
        if (len(candidate["streams"])!=2 or len(v)!=1 or len(a)!=1
                or v[0].get("codec_name")!="h264" or a[0].get("codec_name")!="aac"
                or abs(candidate_duration-duration)>0.2):
            raise WorkflowError("Audiovisual mux failed technical stream or timing validation")
        decoding=subprocess.run([
            "ffmpeg","-nostdin","-v","error","-xerror",
            "-i",str(result),"-f","null","-"],
            stdin=subprocess.DEVNULL,capture_output=True,timeout=70)
        if decoding.returncode!=0:
            raise WorkflowError("Audiovisual MP4 cannot be fully decoded")
        digest=sha256()
        with result.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):
                digest.update(chunk)
        return {
            "status":"REAL_AV_MUX_TECHNICAL_PASS_PUBLICATION_BLOCKED",
            "episode_id":episode_id,
            "duration_s":round(candidate_duration,3),
            "video_width":w,"video_height":h,
            "video_codec":"h264","audio_codec":"aac",
            "output_sha256":digest.hexdigest(),
            "input_audio_sha256":wav_report["sha256"],
            "script_subtitle_estimated":True,
            "actual_natural_speech_verified":False,
            "two_distinct_narrators_verified":False,
            "voice_rights_verified":False,
            "independent_factual_review_verified":False,
            "audio_caption_alignment_verified":False,
            "real_three_video_batch_ready":False,
            "production_release_authorized":False,
            "youtube_upload_authorized":False,
            "publishing_authorized":False,
            "network_calls":0,"external_paid_services_used":False,
        }
    except (OSError,subprocess.TimeoutExpired,WorkflowError):
        output.unlink(missing_ok=True)
        raise
