"""Generate a REVIEW-ONLY synthetic audio take with exact phrase and beat timestamps.

Uses existing Kokoro open weights. No upload, no channel operations, no paid API.
Visual timing, full voice stem and literal phrase-SRT derive from the SAME
synthesized PCM. Human voice/rights/factual/video approval remains false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

PHRASES = [
 (0, "Could an AI agent delete your files?"),
 (0, "Here is the part most people miss."),
 (1, "A chatbot replies."),
 (1, "But an agent may request actions through connected tools."),
 (2, "Imagine it asks to delete a sample folder."),
 (2, "That is a request, not proof it can."),
 (3, "Permissions matter."),
 (3, "Read-only access cannot delete files."),
 (3, "Sensitive actions may need approval."),
 (4, "Deny the action."),
 (4, "Your demo files stay untouched."),
 (5, "Remember: least privilege."),
 (5, "Preview changes, review permissions, and keep backups."),
]
SAMPLE_RATE = 48000
FPS = 30
GAP_SECONDS = 0.075
INTRO_SECONDS = 0.12
OUTRO_SECONDS = 0.55

def srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    sec, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{sec:02d},{millis:03d}"

def ffmpeg(*args: str) -> str:
    p = subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin",
                        *args],capture_output=True,text=True,timeout=120)
    if p.returncode: raise RuntimeError("ffmpeg: "+(p.stderr or p.stdout)[-1100:])
    return p.stdout

def build(model_dir: Path, script_path: Path, public_dir: Path,
          timing_path: Path, results_dir: Path) -> dict:
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro

    if not results_dir.is_dir() or not public_dir.is_dir() or not timing_path.parent.is_dir():
        raise FileNotFoundError("Expected existing output folders")
    script = " ".join(script_path.read_text(encoding="utf-8").split())
    literal = " ".join(line for _,line in PHRASES)
    if script!=literal:
        raise ValueError("Narration phrases differ from the reviewed canonical script")
    if [p[0] for p in PHRASES] != sorted(p[0] for p in PHRASES):
        raise ValueError("Narration beat numbers must be ordered")
    if len(PHRASES)!=13:
        raise AssertionError("Expected exactly 13 known phrase captions")
    voice=Kokoro(str(model_dir/"kokoro-v1.0.onnx"),
                 str(model_dir/"voices-v1.0.bin"))
    all_samples=[np.zeros(round(INTRO_SECONDS*SAMPLE_RATE),dtype=np.float32)]
    position=len(all_samples[0])
    cues=[]
    beat_starts=[0]*6
    seen=set()
    with tempfile.TemporaryDirectory() as work:
        temp=Path(work)
        for idx,(beat,phrase) in enumerate(PHRASES):
            x,rate=voice.create(phrase,voice="af_sarah",lang="en-us",speed=1.0)
            sample=np.asarray(x,dtype=np.float32)
            if sample.ndim!=1 or not np.isfinite(sample).all():
                raise ValueError(f"Invalid synthesis samples at phrase {idx}")
            if not (rate*.28 < len(sample) < rate*12):
                raise ValueError(f"Unexpected duration in phrase {idx}")
            pcm=temp/f"phrase-{idx}.wav"
            converted=temp/f"phrase-{idx}-48k.wav"
            sf.write(str(pcm),sample,int(rate),subtype="PCM_16")
            ffmpeg("-y","-i",str(pcm),"-ac","1","-ar",str(SAMPLE_RATE),
                   "-c:a","pcm_s16le",str(converted))
            clip,sr=sf.read(str(converted),dtype="float32")
            if sr!=SAMPLE_RATE or len(clip)<int(.25*sr):
                raise ValueError("Resampled voice is empty")
            if beat not in seen:
                beat_starts[beat]=max(0,round(position/SAMPLE_RATE*FPS))
                seen.add(beat)
            start_s=position/SAMPLE_RATE
            all_samples.append(clip)
            position+=len(clip)
            end_s=position/SAMPLE_RATE
            cues.append({
                "text":phrase,
                "beat":beat,
                "start_frame":round(start_s*FPS),
                "end_frame":round(end_s*FPS),
                "start_seconds":round(start_s,3),
                "end_seconds":round(end_s,3)
            })
            if idx<len(PHRASES)-1:
                pad=np.zeros(round(GAP_SECONDS*SAMPLE_RATE),dtype=np.float32)
                all_samples.append(pad)
                position+=len(pad)
    all_samples.append(np.zeros(round(OUTRO_SECONDS*SAMPLE_RATE),dtype=np.float32))
    audio=np.concatenate(all_samples)
    seconds=len(audio)/SAMPLE_RATE
    if not (23 <= seconds <= 55):
        raise ValueError(f"Narration {seconds:.2f}s outside useful Short range")
    if np.max(np.abs(audio)) < 0.002:
        raise ValueError("Silent voice")
    if np.max(np.abs(audio)) > .97:
        audio = audio * (.97/np.max(np.abs(audio)))
    for i in range(1,len(beat_starts)):
        if beat_starts[i] <= beat_starts[i-1]:
            raise ValueError("Non-increasing beat timestamps")
    duration_frames=math.ceil(seconds*FPS)
    for i,c in enumerate(cues):
        if c["end_frame"]>duration_frames or c["start_frame"]>=c["end_frame"]:
            raise ValueError(f"Invalid caption cue {i}")
    audio_path=public_dir/"flow-explain-voice.wav"
    sf.write(str(audio_path),audio,SAMPLE_RATE,subtype="PCM_16")
    timing={
       "fps":FPS,"duration_frames":duration_frames,"beat_starts":beat_starts,
       "cues":cues,"status":"SYNTHETIC_PHRASE_ALIGNED_REVIEW_ONLY"
    }
    timing_path.write_text(json.dumps(timing,indent=2)+"\n",encoding="utf-8")
    srt=[]
    for i,c in enumerate(cues):
        srt.append(str(i+1))
        srt.append(srt_time(c["start_seconds"])+" --> "+srt_time(c["end_seconds"]))
        srt.append(c["text"])
        srt.append("")
    (results_dir/"flow-explain-english-phrase-captions.srt").write_text(
        "\n".join(srt),encoding="utf-8")
    sha=hashlib.sha256(audio_path.read_bytes()).hexdigest()
    data={
        "state":"PHRASE_TIMED_AUDIO_ONLY_REVIEW",
        "voice_model":"Kokoro ONNX v1.0",
        "voice_id":"af_sarah",
        "source_text_words":len(script.split()),
        "phrases":len(PHRASES),
        "duration_seconds":round(seconds,3),
        "duration_frames":duration_frames,
        "beat_starts":beat_starts,
        "sample_rate_hz":SAMPLE_RATE,
        "voice_sha256":sha,
        "captions_match_synthesized_phrases":True,
        "word_level_forced_alignment":False,
        "human_listening_approved":False,
        "final_artifact_approved":False,
        "rights_cleared":False,
        "youtube_published":False
    }
    (results_dir/"flow-explain-voice-timing-qa.json").write_text(
        json.dumps(data,indent=2)+"\n",encoding="utf-8")
    return data

def cli() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-dir",type=Path,required=True)
    ap.add_argument("--script",type=Path,required=True)
    ap.add_argument("--public-dir",type=Path,required=True)
    ap.add_argument("--timing-file",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(build(args.model_dir,args.script,args.public_dir,
                           args.timing_file,args.output_dir),indent=2))

if __name__=="__main__":
    cli()
