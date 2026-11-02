"""Create a REVIEW-ONLY original English voice take with Kokoro ONNX.

No YouTube upload, publishing, secrets, paid provider, laptop or GitHub write.
The naturalness/rights/facts/captions still need independent human acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

MAX_GAP = 1.30

def run(*args: str) -> str:
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, timeout=160, check=False)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-1300:])
    return p.stdout

def validate_script(text: str) -> int:
    clean = " ".join(text.split())
    words = len(clean.split())
    if not 55 <= words <= 95:
        raise ValueError(f"Expected 55-95 natural spoken words, received {words}")
    if "delete" not in clean.lower() or "permission" not in clean.lower():
        raise ValueError("Missing factual teaching terms")
    if re.search(r"(subscribe now|guaranteed|100% safe)", clean, re.I):
        raise ValueError("Unverified or inappropriate claim in script")
    return words

def find_silence(path: Path, duration: float) -> dict:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
                        "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=90)
    if p.returncode:
        raise RuntimeError("Cannot inspect voice stem")
    starts = []
    intervals = []
    for line in p.stderr.splitlines():
        s = re.search(r"silence_start:\s*([\d.]+)", line)
        e = re.search(r"silence_end:\s*([\d.]+)", line)
        if s:
            starts.append(float(s.group(1)))
        if e and starts:
            intervals.append((starts.pop(0), float(e.group(1))))
    intervals.extend((s, duration) for s in starts)
    violations = [{"start_s":round(a,3), "duration_s":round(b-a,3)}
                  for a,b in intervals if (b-a)>MAX_GAP]
    return {"pass":not violations, "threshold_seconds":MAX_GAP,
            "violations":violations, "scope":"VOICE_ONLY_NO_MUSIC"}

def synthesize(*, model_dir: Path, script: Path, output: Path) -> dict:
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro

    text = " ".join(script.read_text(encoding="utf-8").split())
    words = validate_script(text)
    if not script.is_file() or not model_dir.is_dir():
        raise FileNotFoundError("Missing script or model dir")
    if output.suffix.lower() != ".wav" or output.exists() or not output.parent.is_dir():
        raise ValueError("Output must be a new .wav in an existing directory")
    model = model_dir / "kokoro-v1.0.onnx"
    voices = model_dir / "voices-v1.0.bin"
    if model.stat().st_size < 1_000_000 or voices.stat().st_size < 100_000:
        raise ValueError("Kokoro model/voice assets missing or undersized")

    tts = Kokoro(str(model), str(voices))
    audio, sr = tts.create(text, voice="af_sarah", lang="en-us", speed=1.00)
    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim != 1 or len(samples)<sr*18 or len(samples)>sr*48:
        raise ValueError("Voice length is not plausible for a Short: re-edit text")
    if not np.isfinite(samples).all() or np.max(np.abs(samples))<0.003:
        raise ValueError("Silent, NaN or corrupt voice output")
    # Avoid aggressive loudness processing; leave this to the final mixer.
    if np.max(np.abs(samples))>0.97:
        samples *= 0.97 / np.max(np.abs(samples))
    temp = output.with_name(output.stem + ".raw-temp.wav")
    try:
        sf.write(str(temp), samples, int(sr), subtype="PCM_16")
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(temp),
            "-af", "aresample=48000", "-ar", "48000", "-ac", "1",
            "-c:a", "pcm_s16le", str(output))
    finally:
        temp.unlink(missing_ok=True)

    encoded, sample_rate = sf.read(str(output), dtype="float32")
    duration = len(encoded) / sample_rate
    if sample_rate!=48000 or not (18 <= duration <= 48):
        output.unlink(missing_ok=True)
        raise ValueError("Output unexpected duration or sample rate")
    gap = find_silence(output,duration)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    result = {
        "status":"SYNTHETIC_VOICE_LISTENING_REVIEW_ONLY",
        "episode":"flowminute_agent_permission_flow_en",
        "source_script":str(script),
        "narration_text":text,
        "voice_id":"af_sarah",
        "model":"Kokoro ONNX v1.0",
        "voice_seconds":round(duration,3),
        "words":words,
        "sample_rate_hz":sample_rate,
        "voice_only_silence":gap,
        "file_sha256":digest,
        "human_listening_approved":False,
        "factual_review_approved":False,
        "rights_cleared":False,
        "captions_synced":False,
        "final_video_assembled":False,
        "published_to_youtube":False,
    }
    output.with_suffix(".qa.json").write_text(json.dumps(result,indent=2)+"\n",
                                                    encoding="utf-8")
    return result

if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model-dir",type=Path,required=True)
    p.add_argument("--script",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(synthesize(model_dir=args.model_dir,script=args.script,
                                output=args.out),indent=2))
