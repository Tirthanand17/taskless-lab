"""Kokoro Hindi long lesson REVIEW renderer input; no YouTube account actions.

All visuals and subtitle cues use the same generated PCM and timeline JSON.
The output is synthetic speech and must be approved by a human listener.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

FPS = 24
RATE = 48000
GAP = 0.11
INTRO = 0.18
OUTRO = 0.9

def run_ffmpeg(*args: str) -> None:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
                       *args], capture_output=True, text=True, timeout=180)
    if p.returncode:
        raise RuntimeError(p.stderr[-1100:])

def timestamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def generate(*,model_dir:Path,source:Path,public_dir:Path,timing_path:Path,output_dir:Path)->dict:
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    data=json.loads(source.read_text(encoding="utf-8"))
    phrases=data["phrases"]
    chapters=data["chapters"]
    if data.get("language")!="hi" or len(chapters)!=6 or not 24<=len(phrases)<=42:
        raise ValueError("Six-chapter Hindi lesson with 24-42 phrases required")
    if [p["chapter"] for p in phrases]!=sorted(p["chapter"] for p in phrases):
        raise ValueError("Chapters out of order")
    if set(p["chapter"] for p in phrases)!=set(range(6)):
        raise ValueError("Every chapter needs narration")
    if not public_dir.is_dir() or not timing_path.parent.is_dir() or not output_dir.is_dir():
        raise FileNotFoundError("Missing target directory")
    speaker=Kokoro(str(model_dir/"kokoro-v1.0.onnx"),str(model_dir/"voices-v1.0.bin"))
    samples=[np.zeros(round(INTRO*RATE),dtype=np.float32)]
    cursor=len(samples[0])
    cues=[]
    chapter_starts=[0]*6
    seen=set()
    with TemporaryDirectory() as d:
        tmp=Path(d)
        for i,part in enumerate(phrases):
            chapter=int(part["chapter"])
            text=str(part["text"]).strip()
            if not text or len(text)>220:
                raise ValueError(f"Unreviewed/overlong speech phrase {i}")
            y,sr=speaker.create(text,voice="hf_alpha",lang="hi",speed=1.0)
            y=np.asarray(y,dtype=np.float32)
            if y.ndim!=1 or not np.isfinite(y).all() or not sr*0.4<len(y)<sr*20:
                raise ValueError(f"Implausible speech duration in phrase {i}")
            raw=tmp/f"speech-{i:02}.wav"
            out=tmp/f"speech-{i:02}-48k.wav"
            sf.write(str(raw),y,int(sr),subtype="PCM_16")
            run_ffmpeg("-y","-i",str(raw),"-ac","1","-ar",str(RATE),"-c:a","pcm_s16le",str(out))
            clip,rate=sf.read(str(out),dtype="float32")
            if rate!=RATE: raise ValueError("Resample failed")
            if chapter not in seen:
                chapter_starts[chapter]=round(cursor/RATE*FPS)
                seen.add(chapter)
            start=cursor/RATE
            samples.append(clip)
            cursor+=len(clip)
            end=cursor/RATE
            cues.append({"chapter":chapter,"text":text,"start_frame":round(start*FPS),
                         "end_frame":round(end*FPS),
                         "start_seconds":round(start,3),"end_seconds":round(end,3)})
            if i<len(phrases)-1:
                padding=np.zeros(round(GAP*RATE),dtype=np.float32)
                samples.append(padding)
                cursor+=len(padding)
    samples.append(np.zeros(round(OUTRO*RATE),dtype=np.float32))
    combined=np.concatenate(samples)
    duration=len(combined)/RATE
    if not 125<=duration<=360:
        raise ValueError(f"Lesson runtime {duration:.2f}s outside 125-360s; revise script")
    if max(abs(float(combined.max())),abs(float(combined.min())))<0.003:
        raise ValueError("Narration is silent")
    if max(abs(float(combined.max())),abs(float(combined.min())))>.97:
        combined*=.97/max(abs(float(combined.max())),abs(float(combined.min())))
    frames=math.ceil(duration*FPS)
    assert all(x<y for x,y in zip(chapter_starts,chapter_starts[1:]))
    assert frames>=cues[-1]["end_frame"]
    wav=public_dir/"flow-explain-long-hi.wav"
    sf.write(str(wav),combined,RATE,subtype="PCM_16")
    timeline={"fps":FPS,"duration_frames":frames,"chapter_starts":chapter_starts,
              "cues":cues,"status":"HINDI_SYNTHETIC_VOICE_PHRASE_TIMED_REVIEW_ONLY"}
    timing_path.write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=[]
    for i,c in enumerate(cues,1):
        lines.extend([str(i),timestamp(c["start_seconds"])+" --> "+timestamp(c["end_seconds"]),c["text"],""])
    (output_dir/"hindi-long-captions.srt").write_text("\n".join(lines),encoding="utf-8")
    report={"status":"AUDIO_VIDEO_QA_PENDING_NOT_PUBLISHED","voice":"Kokoro hf_alpha synthetic",
            "phrases":len(cues),"chapters":len(chapters),
            "duration_seconds":round(duration,3),"duration_frames":frames,
            "wav_sha256":hashlib.sha256(wav.read_bytes()).hexdigest(),
            "human_voice_approved":False,"rights_cleared":False,
            "final_video_approved":False,"youtube_uploaded":False}
    (output_dir/"hindi-long-speech-qa.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for flag in ("model-dir","source","public-dir","timing-file","output-dir"):
        p.add_argument("--"+flag,type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(generate(model_dir=args.model_dir,source=args.source,
                              public_dir=args.public_dir,timing_path=args.timing_file,
                              output_dir=args.output_dir),indent=2,ensure_ascii=False))
