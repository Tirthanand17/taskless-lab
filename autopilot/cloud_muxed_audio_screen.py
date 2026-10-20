"""Read-only checks for silence and obvious placeholders in FINAL muxed AAC.

Requires full MP4 hash/size observation. Samples five deterministic PCM
windows. Sound is NOT proof of intelligible human Hindi/English, speaker
identity, pronunciation, caption alignment, editorial approval or rights.
No upload, network, media creation or publishing actions.
"""
from __future__ import annotations
from array import array
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite,sqrt
from pathlib import Path
import subprocess
import sys

from .agent_org import WorkflowError
from .cloud_capacity_admission import FPS,LANES
from .cloud_full_media_evidence import (
    TechnicalFullHDObservation,_sha_file,MAX_SHORT_BYTES,MAX_LONG_BYTES,
)
from .phase3_voice_signal_screen import _fft_power_fraction

N=4096
RATE=16000
POSITIONS=(.10,.30,.50,.70,.90)
SPEC={lane.lane:lane for lane in LANES}


@dataclass(frozen=True)
class MuxedAudioScreen:
    lane:str
    video_sha256:str
    samples_checked:int
    non_silent_windows:int
    static_tone_windows:int
    clipped_windows:int
    dc_biased_windows:int
    technical_signal_pass:bool
    blockers:tuple[str,...]
    actual_speech_recognized:bool=False
    intended_language_verified:bool=False
    distinct_short_narrators_verified:bool=False
    spoken_caption_alignment_verified:bool=False
    commercial_rights_verified:bool=False
    publishing_authorized:bool=False


def _signal(raw:bytes)->tuple[float,float,float,float]:
    """RMS, clipped fraction, DC, strongest-tone share for exact PCM window."""
    if type(raw) is not bytes or len(raw)!=N*2:
        raise WorkflowError("Exact 4096 sample little-endian mono PCM16 required")
    values=array("h")
    values.frombytes(raw)
    if sys.byteorder!="little":
        values.byteswap()
    rms=sqrt(sum(x*x for x in values)/N)/32768
    clipping=sum(abs(x)>=32760 for x in values)/N
    offset=abs(sum(values)/N)/32768
    tone=_fft_power_fraction([float(x) for x in values]) if rms>=.003 else 0.
    if not all(isfinite(x) and x>=0 for x in (rms,clipping,offset,tone)):
        raise WorkflowError("Non-finite or invalid AAC signal feature")
    return rms,clipping,offset,tone


def inspect_muxed_audio(path:Path,obs:TechnicalFullHDObservation)->MuxedAudioScreen:
    """Checks a real original file whose previous full-intake SHA is pinned."""
    if not isinstance(obs,TechnicalFullHDObservation):
        raise WorkflowError("Missing original typed full-media intake")
    lane=SPEC.get(obs.lane)
    if (lane is None
            or obs.width!=lane.width or obs.height!=lane.height
            or obs.frames_decoded_or_counted!=lane.duration_s*FPS
            or obs.video_codec!="h264" or obs.audio_codec!="aac"
            or obs.whole_media_ffmpeg_decode_passed is not True
            or obs.original_file_unchanged_after_inspection is not True
            or obs.publishing_authorized is not False
            or obs.signed_by_independent_reviewer is not False
            or type(obs.video_bytes) is not int or obs.video_bytes<2048
            or not isinstance(obs.video_sha256,str)
            or len(obs.video_sha256)!=64
            or any(c not in "0123456789abcdef" for c in obs.video_sha256)):
        raise WorkflowError("Unverified or falsely elevated original media")
    file=Path(path)
    if not file.is_absolute() or file.is_symlink():
        raise WorkflowError("Existing absolute ordinary MP4 required")
    limit=MAX_SHORT_BYTES if lane.lane.startswith("short_") else MAX_LONG_BYTES
    original,n,dev,inode=_sha_file(file,limit=limit)
    if (original,n)!=(obs.video_sha256,obs.video_bytes):
        raise WorkflowError("MP4 bytes no longer match full-media observation")
    measures=[]
    for p in POSITIONS:
        begin=max(0.,min(
            lane.duration_s-N/RATE,lane.duration_s*p-N/RATE/2
        ))
        cmd=["ffmpeg","-nostdin","-v","error","-xerror",
             "-ss",f"{begin:.5f}","-i",str(file),
             "-map","0:a:0","-vn","-sn","-dn",
             "-ac","1","-ar",str(RATE),
             "-t",f"{N/RATE:.4f}","-f","s16le","pipe:1"]
        try:
            got=subprocess.run(cmd,stdin=subprocess.DEVNULL,
                               capture_output=True,check=False,timeout=25)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise WorkflowError("Cannot sample muxed AAC") from exc
        if (got.returncode!=0 or got.stderr
                or len(got.stdout)!=N*2):
            raise WorkflowError("Muxed AAC decoder failed or PCM truncated")
        measures.append(_signal(got.stdout))
    final,size,dev2,inode2=_sha_file(file,limit=limit)
    if (final,size,dev2,inode2)!=(original,n,dev,inode):
        raise WorkflowError("MP4 swapped or changed during signal inspection")
    sound=sum(r>=.003 for r,_,_,_ in measures)
    tone=sum(t>=.92 for _,_,_,t in measures)
    clip=sum(c>=.045 for _,c,_,_ in measures)
    dc=sum(d>=.14 for _,_,d,_ in measures)
    reasons=[]
    if sound<4: reasons.append("MUXED_AUDIO_MOSTLY_SILENT")
    if tone>=4: reasons.append("MUXED_AUDIO_PURE_TONE_PLACEHOLDER")
    if clip>=2: reasons.append("MUXED_AUDIO_CLIPPING")
    if dc>=2: reasons.append("MUXED_AUDIO_DC_OFFSET")
    return MuxedAudioScreen(
        lane.lane,original,len(measures),sound,tone,clip,dc,
        not reasons,tuple(sorted(reasons)),
    )


def summarize_muxed_audio(
    original:tuple[TechnicalFullHDObservation,...],
    screens:tuple[MuxedAudioScreen,...])->dict:
    """Never promote a waveform technical pass into release or legal proof."""
    if (not isinstance(original,tuple) or not isinstance(screens,tuple)
            or len(original)>len(LANES) or len(screens)>len(LANES)):
        raise WorkflowError("Bounded original audio bundle required")
    source={}
    for obs in original:
        if (not isinstance(obs,TechnicalFullHDObservation)
                or obs.lane not in SPEC or obs.lane in source):
            raise WorkflowError("Duplicate or invalid source video lane")
        source[obs.lane]=obs.video_sha256
    seen=set()
    issues=[]
    for record in screens:
        if (not isinstance(record,MuxedAudioScreen)
                or record.lane not in source
                or record.lane in seen
                or record.video_sha256!=source[record.lane]
                or any(getattr(record,key) is not False for key in (
                    "actual_speech_recognized","intended_language_verified",
                    "distinct_short_narrators_verified",
                    "spoken_caption_alignment_verified",
                    "commercial_rights_verified","publishing_authorized",
                ))):
            raise WorkflowError("Unbound or falsely released technical signal")
        seen.add(record.lane)
        if (record.samples_checked!=len(POSITIONS)
                or record.technical_signal_pass is not True
                or record.blockers):
            issues.append(record.lane+":MUXED_AAC_SIGNAL_FAILED")
    for lane in LANES:
        if lane.lane not in seen:
            issues.append(lane.lane+":MUXED_AAC_NOT_INSPECTED")
        issues.append(lane.lane+":REAL_SPEECH_LANGUAGE_CAPTIONS_RIGHTS_NOT_VERIFIED")
    return {
        "status":"AAC_SIGNAL_TECHNICAL_ONLY_RELEASE_BLOCKED",
        "inspected_lanes":tuple(sorted(seen)),
        "blockers":tuple(sorted(set(issues))),
        "independent_language_speech_validation_present":False,
        "two_distinct_short_speakers_verified":False,
        "speech_aligned_subtitles_verified":False,
        "commercial_voice_and_media_rights_verified":False,
        "publishing_authorized":False,
        "youtube_upload_authorized":False,
        "monthly_recurring_infrastructure_inr":0,
    }
