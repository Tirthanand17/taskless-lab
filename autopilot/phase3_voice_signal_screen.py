"""Phase 3R1: conservative offline PCM placeholder-tone detector, NOT an ASR.

A technical WAV can be a loud sine wave. Inspect five independent windows in
an ORIGINAL, already admitted complete WAV. Refuse sustained near silence and
strongly concentrated single-frequency (sine-like) signals before the mixed
three-video source handoff. More elaborate fake audio can still pass. This
CANNOT classify speech, verify a language, identity, voice naturalness,
authorization, commercial rights, or subtitle word timing.

No models, providers, network, subprocesses, video writes, new libraries, or
file storage. Uses built-in standard library PCM + bounded 4096-point FFT.
"""
from __future__ import annotations

from array import array
from hashlib import sha256
from math import cos, sin, pi, sqrt, log2
from pathlib import Path
import math
import sys
import wave

from .agent_org import WorkflowError
from .phase3_complete_narration_intake import EPISODES

WINDOW_SAMPLES = 4096
WINDOW_FRACTIONS = (.10,.30,.50,.70,.90)
STATIC_TONE_DOMINANCE_MIN = .92
MAX_TONE_WINDOWS = 3
MAX_SILENT_WINDOWS = 2
MIN_WINDOW_RMS = .003
MAX_WAV_BYTES = 70 * 1024 * 1024


def _fft_power_fraction(samples: list[float]) -> float:
    """Peak + adjacent frequency bins over all AC power; Hann window.

    Used ONLY to reject very obvious continuous pure sine tone. A low value
    is NOT evidence of human speech. No signal classifier is trained here.
    """
    n=len(samples)
    if n!=WINDOW_SAMPLES:
        raise WorkflowError("Unexpected FFT sample window length")
    avg=sum(samples)/n
    data=[complex((x-avg)*(.5-.5*cos(2*pi*i/(n-1))),0)
          for i,x in enumerate(samples)]
    j=0
    for i in range(1,n):
        mask=n>>1
        while j&mask:
            j^=mask
            mask>>=1
        j^=mask
        if i<j:
            data[i],data[j]=data[j],data[i]
    length=2
    while length<=n:
        angle=-2*pi/length
        root=complex(cos(angle),sin(angle))
        for offset in range(0,n,length):
            u=complex(1,0)
            half=length>>1
            for k in range(half):
                a=data[offset+k]
                b=data[offset+k+half]*u
                data[offset+k]=a+b
                data[offset+k+half]=a-b
                u*=root
        length*=2
    # Drop DC and Nyquist. Full positive-bin power includes harmonics.
    power=[data[k].real**2+data[k].imag**2
           for k in range(1,n//2)]
    total=sum(power)
    if total<=1e-16:
        return 0.0
    # Valid neighboring windows at edges; strong sine spreads into Hann bins.
    strongest=max(
        sum(power[max(0,k-1):min(len(power),k+2)])
        for k in range(len(power))
    )
    return strongest/total


def _hash_file(path:Path)->str:
    digest=sha256()
    with path.open("rb") as fd:
        for part in iter(lambda:fd.read(1048576),b""):
            digest.update(part)
    return digest.hexdigest()


def inspect_nonplaceholder_audio_candidate(
    *,wav_path:Path,episode_id:str,
    expected_sha256:str,
) -> dict:
    """Check five bounded PCM windows; never declare natural/human speech.

    A positive result means ONLY obvious uninterrupted pure tones/silence were
    not detected in sampled positions. No automatic publishing privileges.
    """
    if episode_id not in EPISODES:
        raise WorkflowError("Unrecognized original episode")
    if (not isinstance(wav_path,Path) or wav_path.is_symlink()
            or not wav_path.is_file() or wav_path.suffix.lower()!=".wav"
            or not 44<=wav_path.stat().st_size<=MAX_WAV_BYTES
            or not isinstance(expected_sha256,str)
            or len(expected_sha256)!=64
            or any(c not in "0123456789abcdef" for c in expected_sha256)):
        raise WorkflowError("Bounded original PCM WAV and valid expected digest required")
    if _hash_file(wav_path)!=expected_sha256:
        raise WorkflowError("WAV bytes changed after complete narration intake")
    try:
        with wave.open(str(wav_path),"rb") as reader:
            channels=reader.getnchannels()
            sample_width=reader.getsampwidth()
            rate=reader.getframerate()
            frames=reader.getnframes()
            if (reader.getcomptype()!="NONE"
                    or channels not in (1,2)
                    or sample_width!=2
                    or rate not in (16000,22050,24000,44100,48000)
                    or abs(frames/rate-EPISODES[episode_id])>1.5
                    or frames < WINDOW_SAMPLES*2):
                raise WorkflowError("Original complete PCM WAV properties invalid")
            tone_windows=0
            silent_windows=0
            sample_results=[]
            for position in WINDOW_FRACTIONS:
                start=max(0,min(frames-WINDOW_SAMPLES,
                                round(position*frames)-WINDOW_SAMPLES//2))
                reader.setpos(start)
                raw=reader.readframes(WINDOW_SAMPLES)
                if len(raw)!=WINDOW_SAMPLES*channels*2:
                    raise WorkflowError("Missing interior audio frame window")
                pcm=array("h")
                pcm.frombytes(raw)
                if sys.byteorder!="little":
                    pcm.byteswap()
                if channels==1:
                    mono=[float(v) for v in pcm]
                else:
                    mono=[(pcm[i]+pcm[i+1])/2.0 for i in range(0,len(pcm),2)]
                rms=sqrt(sum(v*v for v in mono)/WINDOW_SAMPLES)/32768
                if not math.isfinite(rms):
                    raise WorkflowError("Invalid decoded audio amplitude")
                silent=rms<MIN_WINDOW_RMS
                if silent:
                    silent_windows+=1
                    tone_share=0.0
                else:
                    tone_share=_fft_power_fraction(mono)
                    if tone_share>=STATIC_TONE_DOMINANCE_MIN:
                        tone_windows+=1
                sample_results.append({
                    "normalized_rms":round(rms,5),
                    "strongest_single_tone_power_share":round(tone_share,4),
                })
    except (OSError,EOFError,wave.Error) as exc:
        raise WorkflowError("Original WAV cannot be sampled safely") from exc
    if silent_windows>MAX_SILENT_WINDOWS:
        raise WorkflowError("Excessive silent sampled narration windows")
    if tone_windows>MAX_TONE_WINDOWS:
        raise WorkflowError("Sustained synthetic-like pure tone, not suitable narration")
    if silent_windows+tone_windows>=len(WINDOW_FRACTIONS):
        raise WorkflowError("No sampled evidence beyond silence/single-tone placeholders")
    return {
        "status":"OBVIOUS_AUDIO_PLACEHOLDER_NOT_DETECTED_UNVERIFIED",
        "episode_id":episode_id,
        "wav_sha256":expected_sha256,
        "checked_pcm_windows":len(WINDOW_FRACTIONS),
        "near_silent_windows":silent_windows,
        "high_purity_tone_windows":tone_windows,
        "window_signal_features":sample_results,
        "intelligible_speech_recognized":False,
        "human_voice_naturalness_verified":False,
        "declared_language_or_speaker_verified":False,
        "independent_listening_verified":False,
        "voice_license_verified":False,
        "actual_srt_alignment_verified":False,
        "ready_for_mux_or_upload":False,
        "publishing_authorized":False,
        "network_calls":0,
    }
