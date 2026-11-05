"""Phase 3R3: optional FULL-DURATION ephemeral H264/AAC mux engineering QA.

Actual 42s Hindi Short, 42s English Short and 432s Hindi long. Requires all
three original HD visual receipts, full WAV technical intake and source-locked
SRT candidate gate first. Running the function with authorized, preexisting
input media creates temporary QA MP4s only, inspects/fully decodes them, hashes
the results and deletes ALL temporary media before returning or on failure.

IMPORTANT: there are NO real supplied/licensed voice takes at this checkpoint.
The module has not performed a real three-video narrated batch. Technical
AAC tracks can contain *tones*, not human narration. No SRT is burned/muxed
because candidate SRT timestamps are not verified speech-aligned. This is
NEVER publication consent, platform deployment or a reusable video output.

No network, shell, model, download, hosted provider, OAuth, YouTube or D1.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from typing import Sequence

from .agent_org import WorkflowError
from .phase3_three_video_handoff import (
    TechnicalHandoffInput, prepare_three_video_technical_handoff,
)
from .phase3_visual_signal_audit import EPISODES

MAX_OUTPUT_BYTES = 180_000_000
MIN_FREE_BYTES = 900_000_000
MAX_PROBE_CHARS = 25_000


def _probe_exact_muxed(path:Path, episode_id:str) -> dict:
    """Probe REAL output metadata and reject noncanonical AV configuration."""
    if episode_id not in EPISODES:
        raise WorkflowError("Unknown original media episode")
    if (not isinstance(path,Path) or path.is_symlink() or not path.is_file()
            or not 4096 <= path.stat().st_size <= MAX_OUTPUT_BYTES):
        raise WorkflowError("Missing, symlink or oversized quarantined AV output")
    try:
        task=subprocess.run([
            "ffprobe","-v","error","-show_entries",
            "stream=codec_type,codec_name,width,height,nb_frames,avg_frame_rate,sample_rate:"
            "format=duration","-of","json",str(path),
        ], stdin=subprocess.DEVNULL,capture_output=True,text=True,
            check=True,timeout=25)
        if len(task.stdout)>MAX_PROBE_CHARS:
            raise WorkflowError("Oversized AV probe response")
        obj=json.loads(task.stdout)
        streams=obj["streams"]
        if len(streams)!=2:
            raise WorkflowError("Exactly one video and one audio stream required")
        video=[x for x in streams if x.get("codec_type")=="video"]
        audio=[x for x in streams if x.get("codec_type")=="audio"]
        if len(video)!=1 or len(audio)!=1:
            raise WorkflowError("AV mux must retain exactly two matching streams")
        duration,w,h,fps,frames=EPISODES[episode_id]
        v,a=video[0],audio[0]
        frame_rate=v["avg_frame_rate"].split("/")
        rate=(float(frame_rate[0])/float(frame_rate[1])
              if len(frame_rate)==2 else float(frame_rate[0]))
        measured=float(obj["format"]["duration"])
        if (v.get("codec_name")!="h264" or a.get("codec_name")!="aac"
                or (int(v["width"]),int(v["height"]))!=(w,h)
                or int(v["nb_frames"])!=frames
                or int(a["sample_rate"])!=48000
                or not math.isfinite(rate) or abs(rate-fps)>.015
                or not math.isfinite(measured) or abs(measured-duration)>.25):
            raise WorkflowError("Wrong original HD frame geometry, codec, audio or duration")
        return {"duration_seconds":round(measured,3),
                "video_width":w,"video_height":h,
                "video_frames":frames,"video_frame_rate":fps,
                "video_codec":"h264","audio_codec":"aac",
                "audio_sample_rate_hz":48000}
    except (OSError,ValueError,KeyError,TypeError,ZeroDivisionError,
            subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        raise WorkflowError("Could not validate actual mixed AV streams") from exc


def _sha_file(path:Path)->str:
    digest=sha256()
    with path.open("rb") as media:
        for chunk in iter(lambda:media.read(1_048_576),b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_ephemeral_quarantined_audio_batch(
    entries:Sequence[TechnicalHandoffInput], *,
    scratch_dir:Path,
) -> dict:
    """Full three-video actual technical mux/decode; output permanently purged.

    Call ONLY when actual lawful narrator files and owner-approved local/cloud
    scratch runtime exist. A successful result is an UNSIGNED, untrusted QA
    receipt and never a publication approval.
    """
    if (not isinstance(scratch_dir,Path) or scratch_dir.is_symlink()
            or not scratch_dir.is_dir()
            or shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None):
        raise WorkflowError("Existing ordinary local scratch and FFmpeg required")
    # Run full actual source and WAV/SRT checks before any output is created.
    handed=prepare_three_video_technical_handoff(entries)
    if (handed.get("status")!="THREE_VIDEO_TECHNICAL_HANDOFF_ONLY_RELEASE_BLOCKED"
            or handed.get("youtube_upload_or_publishing_authorized") is not False
            or handed.get("final_mux_generated") is not False):
        raise WorkflowError("Input quarantine handoff unexpectedly gained release power")
    if shutil.disk_usage(scratch_dir).free < MIN_FREE_BYTES:
        raise WorkflowError("Insufficient temporary disk for three-episode AV QA")

    by_episode={x.episode_id:x for x in entries}
    details=[]
    # Internal temp folder is ALWAYS deleted before control returns.
    with TemporaryDirectory(prefix="flowminute-unreleased-avqa-",dir=scratch_dir) as tmp:
        for episode_id in sorted(EPISODES):
            item=by_episode[episode_id]
            expected_seconds=EPISODES[episode_id][0]
            receipt=next(x for x in handed["episodes"] if x["episode_id"]==episode_id)
            if (receipt.get("mux_permitted") is not False
                    or receipt.get("publishing_authorized") is not False
                    or receipt.get("duration_seconds_expected")!=expected_seconds
                    or receipt.get("wav_sha256")!=item.narration_take.wav_sha256
                    or receipt.get("silent_video_sha256")!=item.video_receipt["video_sha256"]):
                raise WorkflowError("Unprivileged source binding mismatched just before mux")
            # A 1.5s gap is acceptable for exploratory PCM intake but NOT full
            # mux. Avoid silently trimming or padding substantial speech.
            actual_wav_seconds=next(
                x["duration_seconds"] for x in
                # read from a separately re-run real WAV inspector not forged handoff
                [_inspect_input_wav(item, expected_seconds)]
            )
            if abs(actual_wav_seconds-expected_seconds)>.25:
                raise WorkflowError("Unaligned full-duration speech WAV: refusing trim or pad")
            output=Path(tmp)/(episode_id+".qa-only.mp4")
            cmd=[
                "ffmpeg","-nostdin","-v","error","-xerror","-n",
                "-i",str(item.silent_video_path),
                "-i",str(item.narration_take.wav_path),
                "-map","0:v:0","-map","1:a:0","-sn","-dn",
                "-c:v","copy","-c:a","aac","-b:a","128k",
                "-ar","48000","-ac","2",
                "-t",str(expected_seconds),
                "-movflags","+faststart",
                "-metadata","comment=FLOWMINUTE_UNREVIEWED_QA_ONLY_NEVER_UPLOAD",
                str(output),
            ]
            try:
                process=subprocess.run(cmd,stdin=subprocess.DEVNULL,
                                       capture_output=True,check=False,
                                       timeout=540 if expected_seconds>60 else 160)
            except (OSError,subprocess.TimeoutExpired) as exc:
                raise WorkflowError("Bounded FFmpeg temporary audio/video mux failed") from exc
            if process.returncode!=0:
                raise WorkflowError("FFmpeg reported quarantined AV mux failure")
            measured=_probe_exact_muxed(output,episode_id)
            try:
                checked=subprocess.run(
                    ["ffmpeg","-nostdin","-v","error","-xerror",
                     "-i",str(output),"-f","null","-"],
                    stdin=subprocess.DEVNULL,capture_output=True,check=False,
                    timeout=540 if expected_seconds>60 else 160)
            except (OSError,subprocess.TimeoutExpired) as exc:
                raise WorkflowError("Bounded full video/audio decoder failed") from exc
            if checked.returncode!=0:
                raise WorkflowError("Muxed episode cannot be fully decoded")
            details.append({
                "episode_id":episode_id,
                "video_sha256":receipt["silent_video_sha256"],
                "audio_wav_sha256":receipt["wav_sha256"],
                "candidate_srt_sha256":receipt["candidate_srt_sha256"],
                "ephemeral_mux_sha256":_sha_file(output),
                "ephemeral_mux_size_bytes":output.stat().st_size,
                **measured,
                "real_natural_narration_verified":False,
                "caption_alignment_verified":False,
                "rights_or_production_approval_verified":False,
                "final_caption_track_muxed":False,
                "publishing_authorized":False,
            })
    return {
        "status":"FULL_EPHEMERAL_AV_TECHNICAL_MUX_ONLY_ALL_MEDIA_PURGED",
        "episodes":details,
        "number_of_ephemeral_outputs_verified":3,
        "temporary_video_files_retainable":False,
        "any_media_persisted_after_run":False,
        "full_decode_measured":True,
        "human_audio_or_multilingual_editorial_approval":False,
        "real_caption_speech_alignment_authenticated":False,
        "commercial_media_rights_authenticated":False,
        "upload_schedule_or_publishing_authorized":False,
        "network_calls":0,
    }


def _inspect_input_wav(item:TechnicalHandoffInput,expected_seconds:int)->dict:
    # Re-open actual WAV bytes immediately before passing them to FFmpeg.
    from .phase3_voice_subtitle_handoff import inspect_external_voice_wav
    report=inspect_external_voice_wav(
        item.narration_take.wav_path,
        episode_id=item.episode_id,expected_seconds=expected_seconds,
        declared_narrator_id=item.narration_take.declared_narrator_id,
        declared_language=item.narration_take.declared_language,
    )
    if report.get("sha256")!=item.narration_take.wav_sha256:
        raise WorkflowError("WAV changed after all-source admission")
    if report.get("real_speech_verified") is not False or report.get("license_rights_verified") is not False:
        raise WorkflowError("Audio technical inspector must never claim source/rights approval")
    return report
