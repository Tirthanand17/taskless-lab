"""Acoustically anchor CLIVOX draft captions to original synthesized speech.

Two independent passes:
1. On ORIGINAL unmixed eSpeak PCM, locate actual above-threshold waveform
   activity, excluding eSpeak's trailing silence rather than timing the
   complete WAV container.
2. In the FINAL mixed original WAV, subtract the known deterministic,
   original-only low-level sinusoidal bed and transition sting, then
   independently locate residual speech-like activity. Compare actual
   SRT cue bounds against that signal within a small tolerance.

These are signal-activity checks, NOT speech recognition, word/phoneme
forced alignment, commercial-rights clearance, human review or release.
"""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import re
import sys
import wave

RATE=48_000
FRAME_MS=20
FRAME=RATE*FRAME_MS//1000
SAMPLE_STRIDE=16
THRESHOLD_RMS=250.0
MIN_ACTIVE_FRAMES=10
SYNC_TOLERANCE_S=0.14
SRT_CLOCK=re.compile(r"\d{2}:\d{2}:\d{2},\d{3}\Z")


class SpeechBoundaryDenied(ValueError):
    pass


def require(ok:bool,what:str)->None:
    if not ok:
        raise SpeechBoundaryDenied("CLIVOX_A5_SPEECH_BOUNDARY_DENIED_"+what)


def measure_unmixed_speech_activity(samples:array)->tuple[float,float]:
    """Return actual dry TTS activity [start, end] relative to its PCM file.

    eSpeak may include 200-350ms of silent samples at the end of a spoken
    utterance. The previous full-file length held subtitles after speech.
    """
    require(isinstance(samples,array) and samples.typecode=="h"
            and 0<len(samples)<=RATE*15 and
            len(samples)>=FRAME*MIN_ACTIVE_FRAMES,
            "DRY_PCM_SHAPE")
    active=[]
    for offset in range(0,len(samples)-FRAME+1,FRAME):
        selected=samples[offset:offset+FRAME:SAMPLE_STRIDE]
        rms=math.sqrt(sum(int(x)*int(x) for x in selected)/len(selected))
        if rms>=THRESHOLD_RMS:
            active.append(offset//FRAME)
    require(len(active)>=MIN_ACTIVE_FRAMES,"NO_MEANINGFUL_DRY_SPEECH_ACTIVITY")
    start=active[0]*FRAME/RATE
    end=(active[-1]+1)*FRAME/RATE
    require(0<=start<end<=len(samples)/RATE+FRAME/RATE,
            "DRY_SPEECH_WINDOW")
    return start,end


def parse_srt_intervals(content:str)->list[tuple[float,float]]:
    require(type(content) is str and 1<=len(content)<=30_000,
            "SRT_TEXT_LIMIT")
    chunks=re.split(r"\n\s*\n",content.strip())
    require(1<=len(chunks)<=80,"SRT_CHUNKS")
    cues=[]
    for idx,chunk in enumerate(chunks,1):
        lines=chunk.splitlines()
        require(len(lines) in (3,4) and lines[0]==str(idx)
                and " --> " in lines[1],"SRT_SEQUENCE_AND_LINES")
        times=lines[1].split(" --> ")
        require(len(times)==2 and
                all(SRT_CLOCK.fullmatch(t) for t in times),
                "SRT_TIME_STAMP")
        def seconds(stamp:str)->float:
            hh,mm,ss,ms=map(int,stamp.replace(",",":").split(":"))
            require(mm<60 and ss<60 and ms<1000,"SRT_TIME_RANGE")
            return hh*3600+mm*60+ss+ms/1000
        start,end=seconds(times[0]),seconds(times[1])
        require(0<=start<end
                and (not cues or start>=cues[-1][1]-.002),
                "SRT_CLOCK_OVERLAP")
        cues.append((start,end))
    return cues


def bed_sample_without_speech(sample_index:int,beat_start:int)->int:
    """Recreate ONLY the documented original procedural sine/sting signal.

    A deterministic bed-only WAV cannot pass the recovered-speech test.
    No third-party soundtrack or web media is accessed.
    """
    require(type(sample_index) is int and sample_index>=0
            and type(beat_start) is int and 0<=beat_start<=600,
            "BED_SAMPLE_TIME")
    t=sample_index/RATE
    require(t>=beat_start,"BED_CLOCK")
    bed=52*math.sin(2*math.pi*92*t)+24*math.sin(2*math.pi*184*t)
    delta=t-beat_start
    sting=(
        1250*math.sin(2*math.pi*(360+600*delta)*delta)*math.exp(-24*delta)
        if 0<=delta<.16 else 0.0
    )
    return round(bed+sting)


def audit_mixed_speech_caption_bounds(
    wav_path:Path,*,beats:list[dict],duration:int,srt:str
)->dict:
    """Validate exact TTS onset/offset against SRT from FINAL mixed PCM.

    Merely having loud sound, e.g. the procedural sting, is not enough:
    the expected original-only bed and sting are subtracted first. This
    still cannot prove text correctness or voice identity and works ONLY
    with this source-free renderer's deterministic sound design.
    """
    require(isinstance(wav_path,Path) and wav_path.is_file()
            and not wav_path.is_symlink()
            and 100_000<wav_path.stat().st_size<30_000_000,
            "WAV_PATH")
    require(type(duration) is int and 1<=duration<=600
            and type(beats) is list and 1<=len(beats)<=25,
            "BEAT_COUNT_AND_DURATION")
    intervals=parse_srt_intervals(srt)
    for beat in beats:
        require(type(beat) is dict
                and type(beat.get("start_s")) is int
                and type(beat.get("end_s")) is int
                and 0<=beat["start_s"]<beat["end_s"]<=duration,
                "BEAT_CLOCK")
    require(beats[0]["start_s"]==0
            and beats[-1]["end_s"]==duration
            and all(beats[i]["end_s"]==beats[i+1]["start_s"]
                    for i in range(len(beats)-1)),
            "CONTIGUOUS_BEATS")
    try:
        with wave.open(str(wav_path),"rb") as source:
            require(source.getnchannels()==1
                    and source.getsampwidth()==2
                    and source.getframerate()==RATE
                    and source.getcomptype()=="NONE"
                    and source.getnframes()==duration*RATE,
                    "EXACT_MONO_PCM_FORMAT_DURATION")
            final=array("h")
            final.frombytes(source.readframes(source.getnframes()))
    except (OSError,EOFError,wave.Error):
        raise SpeechBoundaryDenied(
            "CLIVOX_A5_SPEECH_BOUNDARY_DENIED_CORRUPT_WAV"
        ) from None
    if sys.byteorder!="little":
        final.byteswap()
    require(len(final)==duration*RATE,"TRUNCATED_PCM")
    results=[]
    for index,beat in enumerate(beats):
        beg,end=beat["start_s"],beat["end_s"]
        matching=[
            (start,stop) for start,stop in intervals
            if start>=beg-.003 and stop<=end+.003
        ]
        require(len(matching)>=1,
                "NO_SRT_IN_SCENE_"+str(index))
        active=[]
        max_rms=0.0
        for tick in range(beg*50,end*50):
            # 20ms windows, 3 kHz effective sampling. This is a detection
            # signal, NOT an archival reconstruction or export of TTS.
            window_start=tick*FRAME
            squared=0
            checked=0
            for j in range(window_start,window_start+FRAME,SAMPLE_STRIDE):
                restored=int(final[j])-bed_sample_without_speech(j,beg)
                squared+=restored*restored
                checked+=1
            rms=math.sqrt(squared/checked)
            max_rms=max(rms,max_rms)
            if rms>=THRESHOLD_RMS:
                active.append(tick)
        require(len(active)>=MIN_ACTIVE_FRAMES,
                "NO_TTS_LIKE_SIGNAL_AFTER_BED_SUBTRACTION_"+str(index))
        signal_start=active[0]*FRAME/RATE
        signal_end=(active[-1]+1)*FRAME/RATE
        subtitle_start=matching[0][0]
        subtitle_end=matching[-1][1]
        require(abs(subtitle_start-signal_start)<=SYNC_TOLERANCE_S,
                "CAPTION_START_NOT_ANCHORED_TO_SPEECH_"+str(index))
        require(abs(subtitle_end-signal_end)<=SYNC_TOLERANCE_S,
                "CAPTION_END_NOT_ANCHORED_TO_SPEECH_"+str(index))
        results.append({
            "beat_index":index,
            "active_speech_like_windows":len(active),
            "max_recovered_speech_rms":round(max_rms,1),
            "signal_start_s":round(signal_start,3),
            "signal_end_s":round(signal_end,3),
            "draft_caption_start_s":round(subtitle_start,3),
            "draft_caption_end_s":round(subtitle_end,3),
            "spoken_words_or_phonemes_forced_aligned":False,
        })
    return {
        "stage":"A5_ORIGINAL_SPEECH_ACTIVITY_SRT_BOUNDARY_AUDIT",
        "sample_rate_hz":RATE,
        "beat_count":len(results),
        "all_scenes_recovered_speech_like_activity_above_procedural_bed":True,
        "draft_caption_onset_offset_within_140ms_of_detected_activity":True,
        "independent_final_mixed_wav_sampled":True,
        "source_voice_is_synthetic_and_not_human_approved":True,
        "individual_spoken_words_verified":False,
        "phoneme_forced_alignment_or_asr_performed":False,
        "commercial_speech_rights_verified":False,
        "human_edit_and_caption_approval_complete":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "per_beat":results,
    }
