"""Create natural continuous 24-second English narration for cinematic 32s cut.

The separate HeyGen opener retains its real speech for the first 8 seconds.
This module ONLY creates a review-stage WAV for the 8–32s window. Its existence
does not prove the three 3D video clips were generated or license-cleared.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

NARRATION = (
    "Think of Google Cloud as a workshop, with many tools for different jobs. "
    "Model Garden is its shelf of AI model choices. "
    "Gemini is still there; OpenAI models are planned as another choice. "
    "A developer can select a model for a job, connect it to a real workflow, "
    "and keep alternatives available. "
    "But a model listing does not mean instant, free access. "
    "Check your permissions, pricing, and rollout details before you build."
)
MAX_GAP_SECONDS = 1.20
SILENCE_RE = re.compile(r"silence_(start|end):\s*([0-9.]+)")


def call(*cmd: str) -> str:
    r = subprocess.run(cmd,capture_output=True,text=True,timeout=160)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout)[-1200:])
    return r.stdout


def inspect_wav(path: Path):
    import soundfile as sf
    y,sr=sf.read(str(path))
    if sr != 48000 or y.ndim != 1:
        raise ValueError("Expected 48kHz mono PCM")
    return y,sr


def voice_gap_report(wav: Path, *, duration: float = 24.) -> dict:
    # Must audit the vocal stem, not music-masked composite audio.
    p=subprocess.run([
      "ffmpeg","-hide_banner","-nostdin","-i",str(wav),"-af",
      "silencedetect=noise=-36dB:d=0.3","-f","null","-"],
      capture_output=True,text=True,timeout=90)
    if p.returncode:
        raise RuntimeError("FFmpeg vocal-only silence analysis failed")
    starts=[]
    spans=[]
    for line in p.stderr.splitlines():
        v=re.search(r"silence_start:\s*([0-9.]+)",line)
        w=re.search(r"silence_end:\s*([0-9.]+)",line)
        if v:starts.append(float(v.group(1)))
        if w and starts:
            spans.append((starts.pop(0),float(w.group(1))))
    for x in starts:spans.append((x,duration))
    violations=[{"start":round(a,3),"end":round(b,3),"seconds":round(b-a,3)}
                for a,b in spans if b-a>MAX_GAP_SECONDS]
    return {"pass":not violations, "max_speech_gap_s":MAX_GAP_SECONDS,
            "long_gaps":violations,"audited_stem":"SPEECH_ONLY_NO_MUSIC",
            "human_voice_review_approved":False}


def produce(weights: Path, output: Path, *, voice="af_sarah") -> dict:
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    if voice != "af_sarah":
        raise ValueError("Single consistent English voice only")
    if not (weights/"kokoro-v1.0.onnx").is_file() or not (weights/"voices-v1.0.bin").is_file():
        raise FileNotFoundError("Kokoro model weights not available")
    if output.exists() or output.suffix.lower() != ".wav" or not output.parent.is_dir():
        raise ValueError("Destination must be a new WAV inside an existing directory")
    tts=Kokoro(str(weights/"kokoro-v1.0.onnx"),str(weights/"voices-v1.0.bin"))
    audio,sr=tts.create(NARRATION,voice=voice,lang="en-us",speed=1.00)
    sf.write(str(output.with_suffix(".raw_temp.wav")),audio,sr,subtype="PCM_16")
    raw=output.with_suffix(".raw_temp.wav")
    try:
        frames,rate=sf.read(str(raw),dtype="float32")
        seconds=len(frames)/rate
        # Adjust at most ±12%, not robotic acceleration to hide an overlong script.
        if not 20.9 <= seconds <= 26.0:
            raise ValueError(f"Speech duration {seconds:.2f}s unsuitable; manually revise script")
        desired_spoken_seconds=23.15
        tempo=seconds/desired_spoken_seconds
        if not .90 <= tempo <= 1.125:
            raise ValueError(f"Required tempo {tempo:.3f} unnatural")
        from tempfile import TemporaryDirectory
        with TemporaryDirectory(dir=output.parent) as td:
            fixed=Path(td)/"tempo.wav"
            call("ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
                 "-af",f"aresample=48000,atempo={tempo:.6f}",
                 "-ar","48000","-ac","1","-c:a","pcm_s16le",str(fixed))
            spoken,freq=sf.read(str(fixed),dtype="float32")
            head=int(.14*freq)
            target=np.zeros(24*freq,dtype=np.float32)
            if len(spoken)+head > 24*freq-int(.35*freq):
                raise ValueError("Spoken track exceeds safe 24s scene window")
            target[head:head+len(spoken)]=spoken
            # Soft 100ms onset and 170ms exit; do not suppress speech for 4s.
            inc=min(int(.1*freq),len(spoken)//4)
            target[head:head+inc]*=np.linspace(0,1,inc)
            tail=min(int(.17*freq),len(spoken)//4)
            target[head+len(spoken)-tail:head+len(spoken)]*=np.linspace(1,0,tail)
            sf.write(str(output),target,freq,subtype="PCM_16")
        decoded,freq=inspect_wav(output)
        if len(decoded)!=24*freq:
            raise RuntimeError("Output PCM must last precisely 24 seconds")
        gap=voice_gap_report(output)
        if not gap["pass"]:
            output.unlink(missing_ok=True)
            raise ValueError(f"Speech gaps exceed {MAX_GAP_SECONDS}s: {gap['long_gaps']}")
        digest=sha256(output.read_bytes()).hexdigest()
        return {
         "state":"NATURAL_VOICE_REVIEW_ONLY_3D_SCENES_MISSING",
         "episode":"fm_20261024_short_en",
         "voice_model":"Kokoro ONNX licensed open weights",
         "voice":"af_sarah",
         "narration_text":NARRATION,
         "spoken_words":len(NARRATION.split()),
         "generated_raw_seconds":round(seconds,3),
         "tempo_multiplier":round(tempo,4),
         "audio_duration_seconds":24.0,
         "speech_only_gap_audit":gap,
         "mp3_or_wav_publish_ready":False,
         "three_3d_clips_created":False,
         "movie_32s_assembled":False,
         "voice_listening_approved":False,
         "youtube_scheduled":False,
         "file_sha256":digest
        }
    finally:
        raw.unlink(missing_ok=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opts=p.parse_args()
    result=produce(opts.model_dir,opts.out)
    report=opts.out.with_suffix(".qa.json")
    report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
