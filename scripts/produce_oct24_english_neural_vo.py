"""Make a review-only Kokoro neural-voice version of the 40s English visual insert.

No personal voice cloning, publishing or paid APIs. Requires licensed local model
files. Do not treat automated audio as approved natural narration.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

CUES = (
    "No, Gemini isn't replaced. Google Cloud simply offers a new model choice.",
    "Model Garden is like a shelf. OpenAI models and Codex workflows are joining it.",
    "Developers can choose models for specific tasks, not change your Gemini app.",
    "Teams still need access controls, policies, and responsible data governance.",
    "Availability will expand later. Always check access, pricing, and your actual use case.",
)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} failed: {(r.stderr or r.stdout)[-700:]}")
    return r.stdout

def meta(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height",
        "-of", "json", str(path)]))

def length(path):
    return float(meta(path)["format"]["duration"])

def build(visual, model_dir, out, voice="af_sarah", speed=1.12):
    if visual.is_symlink() or not visual.is_file() or abs(length(visual)-40) > .15:
        raise ValueError("The original 40-second animation is required")
    vm = meta(visual)
    v = [s for s in vm["streams"] if s.get("codec_type") == "video"]
    a = [s for s in vm["streams"] if s.get("codec_type") == "audio"]
    if len(v) != 1 or len(a) != 1 or (v[0].get("width"),v[0].get("height")) != (720,1280):
        raise ValueError("Require one video/audio stream with 720x1280 portrait frames")
    if not .85 <= speed <= 1.35 or voice not in ("af_sarah","af_heart","bf_emma"):
        raise ValueError("Unapproved voice or speed")
    if not all((model_dir/f).is_file() for f in ("kokoro-v1.0.onnx","voices-v1.0.bin")):
        raise ValueError("Required source-licensed speech model files absent")
    from kokoro_onnx import Kokoro
    import soundfile as sf
    speech = Kokoro(str(model_dir/"kokoro-v1.0.onnx"),str(model_dir/"voices-v1.0.bin"))
    out.mkdir(parents=True,exist_ok=True)
    final=out/"FlowMinute_Oct24_English_40s_NEURAL_VO_REVIEW_ONLY.mp4"
    if final.exists():
        raise FileExistsError("Refusing to overwrite an existing video")
    report=[]
    with TemporaryDirectory(prefix="fm-voice-",dir=out) as temp:
        tmp=Path(temp);parts=[]
        for i,line in enumerate(CUES):
            raw=tmp/f"raw_{i}.wav";adjusted=tmp/f"beat_{i}.wav"
            audio,sr=speech.create(line,voice=voice,speed=speed,lang="en-us")
            sf.write(str(raw),audio,sr,subtype="PCM_16")
            d=length(raw)
            if not 2.4 <= d <= 13: raise ValueError(f"Unusable beat {i+1} duration: {d}")
            tempo=max(1.0,d/7.42)
            if tempo>1.45: raise ValueError(f"Beat {i+1} needs human script revision")
            filt=(f"aresample=48000,atempo={tempo:.5f},adelay=160,"
                  "apad,atrim=0:8,asetpts=N/SR/TB,"
                  "afade=t=in:st=0:d=.13,afade=t=out:st=7.67:d=.33")
            run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
                 "-af",filt,"-ar","48000","-ac","1","-c:a","pcm_s16le",str(adjusted)])
            if not 7.99<=length(adjusted)<=8.01:
                raise RuntimeError(f"Incorrect speech beat {i+1} timing")
            report.append({"start_in_full_short":8+i*8,"text":line,
                           "raw_speech_seconds":round(d,2),
                           "tempo_correction":round(tempo,3)})
            parts.append(adjusted)
        listfile=tmp/"concat.txt"
        listfile.write_text("".join(f"file '{p.name}'\n" for p in parts))
        narration=tmp/"speech_40.wav"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","1",
             "-i",str(listfile),"-ar","48000","-ac","1","-c:a","pcm_s16le",str(narration)])
        if abs(length(narration)-40)>.05:raise RuntimeError("Speech timeline drift")
        run(["ffmpeg","-hide_banner","-loglevel","error","-y",
             "-i",str(visual),"-i",str(narration),
             "-filter_complex","[0:a]volume=0.13[fx];[1:a]volume=1.0[vo];"
                               "[fx][vo]amix=inputs=2:duration=first:normalize=0[a]",
             "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac",
             "-b:a","160k","-t","40","-movflags","+faststart",str(final)])
    run(["ffmpeg","-hide_banner","-loglevel","error","-xerror",
         "-i",str(final),"-f","null","-"])
    if abs(length(final)-40)>.2:raise RuntimeError("Output duration drift")
    with final.open("rb") as stream:
        checksum=hashlib.file_digest(stream,"sha256").hexdigest()
    evidence={
      "episode_id":"fm_20261024_short_en",
      "status":"REVIEW_ONLY_NEURAL_AUDIO_NOT_YOUTUBE_READY",
      "model":"Kokoro v1.0 ONNX (Apache-2.0 weights)",
      "voice":voice,"speech_segments":report,"output_file":final.name,
      "output_sha256":checksum,"duration_seconds":round(length(final),3),
      "full_ffmpeg_decode_passed":True,
      "voice_listening_approved":False,"subtitles_synced":False,
      "joined_with_approved_heygen_8s":False,
      "entire_short_completed":False,"youtube_scheduled":False,
      "model_url":"https://huggingface.co/hexgrad/Kokoro-82M"
    }
    (out/"review_only_neural_vo_qa.json").write_text(json.dumps(evidence,indent=2)+"\n")
    return evidence

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--visual",type=Path,required=True)
    p.add_argument("--model-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--voice",default="af_sarah")
    p.add_argument("--speed",type=float,default=1.12)
    opts=p.parse_args()
    print(json.dumps(build(opts.visual,opts.model_dir,opts.out,opts.voice,opts.speed),indent=2))
