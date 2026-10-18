"""Phase 3R1 — bounded PCM pacing and waveform damage screening.

A fixed small window every ~1 second detects obvious long quiet stretches,
saturated/clipped PCM and DC bias in supplied original English/Hindi complete
WAVs. Structural screening ONLY. Never estimates intelligibility, legal rights,
human or synthetic identity, Hindi/English pronunciation, alignment or quality.

This module is explicitly fallible: quiet speech, brief defects between sampled
windows and clever artificial audio can bypass it; some legitimate artistic
pauses may trigger rejection. Independent native-language review is required.

No network, FFmpeg/model/provider, files written, voice generation or upload.
"""
from __future__ import annotations

from array import array
from hashlib import sha256
from math import ceil, sqrt, isfinite
from pathlib import Path
import re
import sys
import wave

from .agent_org import WorkflowError
from .phase3_complete_narration_intake import EPISODES

MAX_WAV_BYTES = 70 * 1024 * 1024
WINDOW_FRAMES = 2048
QUIET_RMS = .003
CLIP_LEVEL = 32760
MAX_CLIPPED_FRACTION = .045
MAX_DC_MEAN = .14
HEX = re.compile(r"[0-9a-f]{64}\Z")


def _hash_file(file:Path) -> str:
    digest=sha256()
    with file.open("rb") as handle:
        for part in iter(lambda: handle.read(1048576), b""):
            digest.update(part)
    return digest.hexdigest()


def _waveform_window(pcm: array, channels: int) -> tuple[float,float,float]:
    n=len(pcm)//channels
    if n != WINDOW_FRAMES or channels not in (1,2):
        raise WorkflowError("Wrong bounded PCM sample collection")
    # Measure saturation on *actual channel samples*, not downmixed channels;
    # cancellation across antiphase stereo must not hide damaged audio.
    saturated=sum(1 for v in pcm if abs(v)>=CLIP_LEVEL)/len(pcm)
    if channels==1:
        mono=pcm
        sum_values=sum(pcm)
        squared=sum(v*v for v in pcm)
    else:
        # True channel-average normalised mean and sample RMS; avoids calling
        # antiphase stereo silence when it contains strong raw channel signal.
        sum_values=sum(pcm)/2
        squared=sum(v*v for v in pcm)/2
    rms=sqrt(squared/n)/32768
    dc=abs(sum_values/n)/32768
    if not isfinite(rms) or not isfinite(dc):
        raise WorkflowError("Invalid bounded original PCM sample")
    return rms,saturated,dc


def inspect_voice_pacing_candidate(*, wav_path:Path, episode_id:str,
                                   expected_sha256:str) -> dict:
    """Reject only obvious unusable WAV defects before source handoff.

    A PASS means technically plausible pacing and no major sampled waveform
    defects, not a real human voice or lawful usage.
    """
    if episode_id not in EPISODES:
        raise WorkflowError("Unknown original narration episode")
    if (not isinstance(wav_path,Path) or wav_path.is_symlink()
            or not wav_path.is_file() or wav_path.suffix.lower()!=".wav"
            or not 44<=wav_path.stat().st_size<=MAX_WAV_BYTES
            or not isinstance(expected_sha256,str) or not HEX.fullmatch(expected_sha256)):
        raise WorkflowError("Only bounded existing local WAV/digest accepted")
    if _hash_file(wav_path) != expected_sha256:
        raise WorkflowError("Narration WAV changed after technical intake")
    try:
        with wave.open(str(wav_path),"rb") as reader:
            n=reader.getnframes()
            channels=reader.getnchannels()
            rate=reader.getframerate()
            if (reader.getcomptype()!="NONE"
                    or reader.getsampwidth()!=2
                    or channels not in (1,2)
                    or rate not in (16000,22050,24000,44100,48000)
                    or abs(n/rate-EPISODES[episode_id])>1.5
                    or n<WINDOW_FRAMES*3):
                raise WorkflowError("Wrong complete original WAV format or duration")
            seconds=ceil(n/rate)
            quiet=clipped=offset=0
            longest=run=leading=0
            last_run=0
            for second in range(seconds):
                start=max(0,min(n-WINDOW_FRAMES,
                                int((second+.5)*rate)-WINDOW_FRAMES//2))
                reader.setpos(start)
                raw=reader.readframes(WINDOW_FRAMES)
                if len(raw)!=WINDOW_FRAMES*channels*2:
                    raise WorkflowError("Truncated complete original audio")
                pcm=array("h")
                pcm.frombytes(raw)
                if sys.byteorder!="little":
                    pcm.byteswap()
                rms,clip_fraction,dc=_waveform_window(pcm,channels)
                silent=rms<QUIET_RMS
                if silent:
                    quiet+=1
                    run+=1
                    longest=max(longest,run)
                else:
                    if second==run:
                        leading=run
                    run=0
                last_run=run
                clipped+=int(clip_fraction>=MAX_CLIPPED_FRACTION)
                offset+=int(dc>=MAX_DC_MEAN)
            if quiet==seconds:
                leading=seconds
            trailing=last_run
    except (OSError,EOFError,wave.Error) as exc:
        raise WorkflowError("Cannot inspect bounded original WAV") from exc

    # Detect grossly unusable edits while accommodating ordinary pauses.
    short=EPISODES[episode_id]<=60
    if ((leading>=4 if short else leading>=9)
            or (trailing>=6 if short else trailing>=12)
            or (longest>=7 if short else longest>=16)
            or quiet/seconds>.60):
        raise WorkflowError("Excessive sampled pauses, missing intro or tail audio")
    if clipped>=max(3,ceil(.09*seconds)):
        raise WorkflowError("Severe saturated/clipped original narrator PCM")
    if offset>=max(3,ceil(.09*seconds)):
        raise WorkflowError("Severe sustained DC offset in original PCM")
    return {
        "status":"PACING_AND_WAVEFORM_TECHNICAL_SCREEN_ONLY_UNVERIFIED",
        "episode_id":episode_id,
        "wav_sha256":expected_sha256,
        "window_seconds_sampled":seconds,
        "quiet_sampled_seconds":quiet,
        "longest_consecutive_quiet_sampled_seconds":longest,
        "hard_clipped_sampled_seconds":clipped,
        "dc_offset_sampled_seconds":offset,
        "natural_human_speech_verified":False,
        "correct_declared_language_or_narrator_verified":False,
        "word_audio_alignment_verified":False,
        "copyright_and_voice_rights_verified":False,
        "independent_professional_audio_review_verified":False,
        "ready_for_mux_or_upload":False,
        "publishing_authorized":False,
        "network_calls":0,
        "files_written":0,
    }
