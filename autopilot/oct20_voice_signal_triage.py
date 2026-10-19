"""Offline Oct20 PCM signal-anomaly triage, never a speech or rights classifier.

Closes a concrete loophole: a single perfectly repeated quarter-second square
wave can satisfy the old WAV duration / energy inspector for all 42/44/480s.
This reads REAL, bounded PCM frames and places obviously repeated test tones,
heavily clipped waveforms and near-all-silent material on manual HOLD.

This is NOT AI speech recognition and cannot reject all synthetic/robotic
voices, certify actual human speech, judge naturalness, Hindi pronunciation,
owner consent or legal rights. A candidate with no detected anomalies STILL
requires independent listening, transcription and lawful rights verification.
No model download, subprocess, network, services or file modification.
"""
from __future__ import annotations

from array import array
from collections import Counter
from hashlib import sha256
from pathlib import Path
import math
import sys
import wave

from .agent_org import WorkflowError

MAX_WAV_BYTES=70*1024*1024
MAX_SECONDS=600
MIN_ACTIVE_BLOCKS=12
REPEAT_HOLD_RATIO=0.65
CLIP_HOLD_RATIO=0.02
SILENCE_HOLD_RATIO=0.90
ACTIVE_RMS_MIN=0.0030


def _hold():
    raise WorkflowError("Oct20 bounded audio signal inspection HOLD")


def inspect_oct20_wav_signal_anomalies(wav_path:Path)->dict:
    """Measure exact PCM chunks, with no waveform, speaker or file path emitted."""
    if (not isinstance(wav_path,Path) or wav_path.suffix.lower()!=".wav"
            or wav_path.is_symlink() or not wav_path.is_file()):
        _hold()
    try:
        before=wav_path.stat()
        if not 44<=before.st_size<=MAX_WAV_BYTES:
            _hold()
        active_counter=Counter()
        active_blocks=0
        silent_blocks=0
        total_blocks=0
        peak_clipped_samples=0
        total_samples=0
        frames_seen=0
        with wave.open(str(wav_path),"rb") as src:
            channels=src.getnchannels()
            rate=src.getframerate()
            width=src.getsampwidth()
            frames_claimed=src.getnframes()
            if (src.getcomptype()!="NONE" or width!=2
                    or channels not in (1,2)
                    or rate not in (16000,22050,24000,44100,48000)
                    or not .25<=frames_claimed/rate<=MAX_SECONDS):
                _hold()
            step=round(rate/4)
            framebytes=channels*width
            while frames_seen<frames_claimed:
                data=src.readframes(min(step,frames_claimed-frames_seen))
                if (not data or len(data)%framebytes):
                    _hold()
                count=len(data)//framebytes
                frames_seen+=count
                pcm=array("h")
                pcm.frombytes(data)
                if sys.byteorder!="little":
                    pcm.byteswap()
                if not pcm:
                    _hold()
                peak_clipped_samples+=sum(
                    1 for sample in pcm if abs(sample)>=32700
                )
                total_samples+=len(pcm)
                rms=math.sqrt(sum(v*v for v in pcm)/len(pcm))/32768
                total_blocks+=1
                if rms<ACTIVE_RMS_MIN:
                    silent_blocks+=1
                else:
                    active_blocks+=1
                    # Exact repeated NONSILENT quarter-second PCM bytes.
                    # Real pauses can repeat silence and should not falsely
                    # trigger duplicate non-silent-tone detection.
                    if count==step:
                        active_counter[sha256(data).digest()]+=1
        if (frames_seen!=frames_claimed or total_samples!=frames_claimed*channels
                or total_blocks==0 or total_samples==0):
            _hold()
        after=wav_path.stat()
        fingerprint=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns)
        if fingerprint(before)!=fingerprint(after):
            _hold()
        # A second complete byte hash binds this observation to the same
        # caller-supplied WAV digest checked elsewhere, without loading the
        # entire 480-second recording into memory.
        hasher=sha256()
        with wav_path.open("rb") as fh:
            while True:
                block=fh.read(1024*1024)
                if not block:
                    break
                hasher.update(block)
        if fingerprint(before)!=fingerprint(wav_path.stat()):
            _hold()
        ratio_clipped=peak_clipped_samples/total_samples
        ratio_silent=silent_blocks/total_blocks
        most_repeated=max(active_counter.values(),default=0)
        ratio_repeated=most_repeated/max(1,active_blocks)
        findings=[]
        if (active_blocks>=MIN_ACTIVE_BLOCKS
                and most_repeated>=MIN_ACTIVE_BLOCKS
                and ratio_repeated>=REPEAT_HOLD_RATIO):
            findings.append("REPEATED_IDENTICAL_ACTIVE_PCM_BLOCKS")
        if ratio_clipped>=CLIP_HOLD_RATIO:
            findings.append("EXCESSIVE_FULL_SCALE_CLIPPING")
        if ratio_silent>=SILENCE_HOLD_RATIO:
            findings.append("MOSTLY_SILENT_PCM")
        return {
            "status":"OCT20_AUDIO_SIGNAL_SHAPE_TECHNICAL_ONLY",
            "wav_sha256":hasher.hexdigest(),
            "duration_seconds":round(frames_seen/rate,3),
            "sample_rate":rate,
            "pcm_channels":channels,
            "inspected_pcm_quartersecond_blocks":total_blocks,
            "max_repeated_active_block_count":most_repeated,
            "repeated_active_block_fraction":round(ratio_repeated,4),
            "clipped_pcm_sample_fraction":round(ratio_clipped,4),
            "near_silent_block_fraction":round(ratio_silent,4),
            "technical_signal_holds":tuple(findings),
            "technical_anomaly_screen_passed":not findings,
            "waveform_verified_as_spoken_language":False,
            "natural_human_voice_verified":False,
            "commercial_voice_rights_verified":False,
            "transcript_acoustic_alignment_verified":False,
            "ready_for_media_mux":False,
            "youtube_upload_authorized":False,
            "youtube_publish_authorized":False,
            "external_network_calls":0,
            "monthly_recurring_infrastructure_inr":0,
        }
    except (OSError,EOFError,ValueError,OverflowError,ZeroDivisionError,
            TypeError,wave.Error):
        _hold()
