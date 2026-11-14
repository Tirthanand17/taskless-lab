"""CLIVOX A5: independently check audible energy in EACH original narration beat.

This is a conservative acoustic signal check, not ASR, speaker recognition,
word alignment, linguistic quality, or a copyright/license verification.
No network, imports of personal media, external clips or publishing logic.
"""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import sys
import wave

CHANNELS=1
RATE=48_000
WINDOW_FRAMES=RATE//4
MIN_VOICE_RMS=600.0
MIN_ACTIVE_WINDOWS=3
MAX_SAFE_PEAK=32_700


class NarrationEnergyDenied(ValueError):
    pass


def require(cond:bool,reason:str)->None:
    if not cond:
        raise NarrationEnergyDenied("CLIVOX_A5_ENERGY_DENIED_"+reason)


def audit_original_narration(wav_path:Path,*,beats:list[dict],duration:int)->dict:
    require(isinstance(wav_path,Path) and wav_path.is_file()
            and not wav_path.is_symlink() and wav_path.stat().st_size>100_000
            and wav_path.stat().st_size<30_000_000,
            "WAV_PATH_OR_BOUNDS")
    require(type(duration) is int and 1<=duration<=600
            and type(beats) is list and 1<=len(beats)<=25,
            "BEATS_INPUT")
    previous=0
    summaries=[]
    try:
        with wave.open(str(wav_path),"rb") as wav:
            require(wav.getnchannels()==CHANNELS
                    and wav.getframerate()==RATE
                    and wav.getsampwidth()==2
                    and wav.getcomptype()=="NONE","PCM_48K_MONO_S16")
            require(wav.getnframes()==duration*RATE,"EXACT_DURATION")
            for i,beat in enumerate(beats):
                require(type(beat) is dict
                        and type(beat.get("start_s")) is int
                        and type(beat.get("end_s")) is int
                        and beat["start_s"]==previous
                        and beat["end_s"]>previous
                        and beat["end_s"]<=duration,
                        "STRICT_BEAT_TIMELINE")
                previous=beat["end_s"]
                active_windows=0
                max_rms=0.0
                peak=0
                windows=(beat["end_s"]-beat["start_s"])*4
                for _ in range(windows):
                    raw=wav.readframes(WINDOW_FRAMES)
                    require(len(raw)==WINDOW_FRAMES*2,"TRUNCATED_BEAT")
                    pcm=array("h")
                    pcm.frombytes(raw)
                    if sys.byteorder!="little":
                        pcm.byteswap()
                    squares=sum(int(x)*int(x) for x in pcm)
                    rms=math.sqrt(squares/WINDOW_FRAMES)
                    peak=max(peak,max(abs(int(x)) for x in pcm))
                    max_rms=max(max_rms,rms)
                    if rms>=MIN_VOICE_RMS:
                        active_windows+=1
                require(peak<MAX_SAFE_PEAK,"POSSIBLE_WAV_CLIPPING_"+str(i))
                require(active_windows>=MIN_ACTIVE_WINDOWS,
                        "SILENT_OR_INAUDIBLE_SCENE_"+str(i))
                summaries.append({
                    "beat_index":i,
                    "active_voice_proxy_windows":active_windows,
                    "total_quarter_second_windows":windows,
                    "max_quarter_second_rms":round(max_rms,1),
                    "peak_sample_amplitude":peak,
                    "caption_word_alignment_verified":False,
                })
            require(previous==duration and wav.tell()==wav.getnframes(),
                    "LEFTOVER_AUDIO_OR_TIMELINE_GAP")
    except (OSError,EOFError,wave.Error):
        raise NarrationEnergyDenied(
            "CLIVOX_A5_ENERGY_DENIED_CORRUPT_WAV"
        ) from None
    return {
        "stage":"A5_ORIGINAL_NARRATION_ENERGY_PER_BEAT_ONLY",
        "sample_rate_hz":RATE,
        "beat_count":len(summaries),
        "all_beats_have_nontrivial_sound_energy":True,
        "no_near_full_scale_pcm_clipping":True,
        "voice_energy_is_not_speech_or_word_accuracy_proof":True,
        "all_speech_approved_by_real_human":False,
        "commercial_soundtrack_and_voice_rights_approved":False,
        "owner_exact_video_release_signed":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "per_beat":summaries,
    }
