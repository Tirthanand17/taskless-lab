#!/usr/bin/env python3
"""FlowMinute natural-style voice track generator (still synthetic speech).

Free Edge TTS baseline. Natural *delivery* is a creative target, never a guarantee:
listen to the actual output before scheduling. Run --dry-run without any network.
"""
from __future__ import annotations
import argparse
import asyncio
from array import array
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import wave

VOICE_PRESETS = {
    "warm-explainer": {"voice": "en-US-AndrewNeural", "rate": -3, "pitch": "-1Hz", "pause_ms": 210},
    "curious-short": {"voice": "en-US-AvaNeural", "rate": -1, "pitch": "+0Hz", "pause_ms": 145},
    "calm-tutorial": {"voice": "en-US-ChristopherNeural", "rate": -5, "pitch": "+0Hz", "pause_ms": 250},
}
ABBREVIATIONS = {"dr.", "mr.", "mrs.", "ms.", "vs.", "e.g.", "i.e.", "prof.", "etc."}


class NarrationError(Exception):
    pass


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise NarrationError("Narration script is empty")
    # This rule keeps punctuation attached to the sentence and avoids splitting
    # non-ending decimals or abbreviations.
    proposed = re.split(r"(?<=[.!?])\s+(?=[\"'“‘(]*[A-Z0-9])", text)
    result = []
    for part in proposed:
        if result and any(result[-1].lower().endswith(a) for a in ABBREVIATIONS):
            result[-1] += " " + part
        else:
            result.append(part)
    return result


def plan_segments(text: str, preset: str) -> list[dict]:
    if preset not in VOICE_PRESETS:
        raise NarrationError("Unknown voice preset")
    chunks = []
    # Two related short sentences per performance phrase; pause at the thought
    # boundary, not at an arbitrary character count.
    pending = ""
    for sentence in sentences(text):
        candidate = (pending + " " + sentence).strip()
        if pending and len(candidate.split()) > 31:
            chunks.append(pending)
            pending = sentence
        else:
            pending = candidate
        # A question is a natural thought boundary even when it is short.
        # This keeps a believable beat before the explanation or reveal.
        if sentence.rstrip().endswith("?"):
            chunks.append(pending)
            pending = ""
    if pending:
        chunks.append(pending)
    if len(chunks) > 180:
        raise NarrationError("Too many narration segments; split into episodes")
    output = []
    for i, chunk in enumerate(chunks):
        count = len(chunk.split())
        if count > 85:
            raise NarrationError(f"Segment {i + 1} too long ({count} words); rewrite into spoken sentences")
        # Intentional, subtle delivery variation across logical phrases;
        # avoid obvious robotic alternation or pitch jumps.
        variation = (0, -1, 1, 0, 1, -1)[i % 6]
        emphasis = chunk.lstrip().lower().startswith(("imagine ", "but ", "here's ", "what if ", "look ", "now "))
        if emphasis:
            variation = min(2, variation + 1)
        pause = VOICE_PRESETS[preset]["pause_ms"]
        if chunk.endswith("?"):
            pause += 100
        if i == len(chunks) - 1:
            pause = 0
        output.append({"text": chunk, "rate_percent": VOICE_PRESETS[preset]["rate"] + variation,
                       "pause_ms": pause, "words": count})
    return output


def find_ffmpeg() -> str:
    program = shutil.which("ffmpeg")
    if program:
        return program
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise NarrationError("Install ffmpeg or imageio-ffmpeg for natural narration assembly") from exc


def run_ffmpeg(ffmpeg: str, args: list[str]) -> None:
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise NarrationError("ffmpeg failed: " + result.stderr[-650:])


def join_pcm_wavs(source_wavs: list[Path], segments: list[dict], outfile: Path) -> float:
    if len(source_wavs) != len(segments) or not source_wavs:
        raise NarrationError("Segment count mismatch")
    frame_rate = 48_000
    total_frames = 0
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(outfile), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(frame_rate)
        for i, (wav_path, segment) in enumerate(zip(source_wavs, segments)):
            with wave.open(str(wav_path), "rb") as clip:
                if (clip.getnchannels(), clip.getsampwidth(), clip.getframerate()) != (1, 2, frame_rate):
                    raise NarrationError("Unexpected PCM format (expect mono, 16-bit, 48kHz)")
                pcm = array("h")
                pcm.frombytes(clip.readframes(clip.getnframes()))
            if not pcm:
                raise NarrationError(f"Empty synthesized segment {i+1}")
            # Brief fades prevent audible boundary clicks; no fake breath samples.
            fade_n = min(240, len(pcm) // 8)
            for n in range(fade_n):
                scale = n / max(1, fade_n)
                pcm[n] = round(pcm[n] * scale)
                pcm[-1-n] = round(pcm[-1-n] * scale)
            target.writeframes(pcm.tobytes())
            total_frames += len(pcm)
            ms = segment["pause_ms"]
            if ms:
                num = round(ms * frame_rate / 1000)
                target.writeframes(b"\0\0" * num)
                total_frames += num
    return total_frames / frame_rate


async def synthesize_segments(planned: list[dict], *, voice: str, pitch: str,
                              ffmpeg: str, workspace: Path) -> tuple[Path, float]:
    try:
        import edge_tts
    except ImportError as exc:
        raise NarrationError("edge-tts missing: pip install edge-tts") from exc
    wavs = []
    for i, segment in enumerate(planned):
        mp3 = workspace / f"chunk-{i:03d}.mp3"
        wav = workspace / f"chunk-{i:03d}.wav"
        service = edge_tts.Communicate(
            text=segment["text"], voice=voice,
            rate=f'{segment["rate_percent"]:+d}%',
            pitch=pitch, volume="+0%",
        )
        await service.save(str(mp3))
        if not mp3.exists() or mp3.stat().st_size < 100:
            raise NarrationError(f"TTS segment {i+1} is missing or empty")
        run_ffmpeg(ffmpeg, ["-i", str(mp3), "-ar", "48000", "-ac", "1",
                           "-c:a", "pcm_s16le", str(wav)])
        wavs.append(wav)
    combined = workspace / "complete.wav"
    duration = join_pcm_wavs(wavs, planned, combined)
    return combined, duration


def report_for(script: Path, output: Path, preset: str, voice: str, segments: list[dict],
               *, duration: float | None, dry_run: bool) -> dict:
    return {
        "source_script": str(script), "source_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "audio_file": str(output), "preset": preset, "voice": voice, "engine": "edge-tts",
        "synthetic_narration": True, "number_of_chunks": len(segments),
        "words": sum(x["words"] for x in segments), "segments": segments,
        "audio_duration_seconds": round(duration, 3) if duration is not None else None,
        "dry_run": dry_run,
        "human_listening_review": "REQUIRED_BEFORE_PUBLICATION",
        "warnings": [
            "Listen to the full output with headphones; regenerate unnatural pronunciations, emphasis or joins.",
            "SRT captions must represent the actual spoken words and timing, not just the script's scene captions.",
            "Do not misrepresent synthesized narration as a recorded human voice.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Natural-style but clearly synthetic FlowMinute narration")
    ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--preset", choices=tuple(VOICE_PRESETS), default="warm-explainer")
    ap.add_argument("--voice", help="Override preset voice; retain provider/usage review")
    ap.add_argument("--report", type=Path, help="Write QA JSON report, no secrets")
    ap.add_argument("--max-duration", type=float, help="Fail if speech exceeds video length (s)")
    ap.add_argument("--dry-run", action="store_true", help="No TTS network calls or audio writes")
    args = ap.parse_args(argv)
    if not args.script.is_file():
        ap.error("script file does not exist")
    if args.max_duration is not None and args.max_duration <= 0:
        ap.error("--max-duration must be positive")
    text = args.script.read_text(encoding="utf-8").strip()
    segments = plan_segments(text, args.preset)
    voice = args.voice or VOICE_PRESETS[args.preset]["voice"]
    output = args.output.resolve()
    if output.suffix.lower() != ".mp3":
        ap.error("output must be MP3")
    duration = None
    if not args.dry_run:
        ffmpeg = find_ffmpeg()
        with tempfile.TemporaryDirectory(prefix="flowminute-voice-") as directory:
            wav, duration = asyncio.run(synthesize_segments(
                segments, voice=voice, pitch=VOICE_PRESETS[args.preset]["pitch"],
                ffmpeg=ffmpeg, workspace=Path(directory)))
            if args.max_duration is not None and duration > args.max_duration:
                raise NarrationError(
                    f"Narration {duration:.2f}s exceeds {args.max_duration:.2f}s; shorten "
                    "the script or increase video duration; do NOT speed to an unnatural rate")
            output.parent.mkdir(parents=True, exist_ok=True)
            temp_mp3 = Path(directory) / "finished.mp3"
            # Spoken-word loudness target. Limit peaks without aggressive compression
            # that would remove subtle delivery dynamics.
            run_ffmpeg(ffmpeg, ["-i", str(wav),
                               "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                               "-c:a", "libmp3lame", "-b:a", "192k",
                               "-ar", "48000", str(temp_mp3)])
            os.replace(temp_mp3, output)
    report = report_for(args.script, output, args.preset, voice, segments,
                        duration=duration, dry_run=args.dry_run)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "segments"}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NarrationError as exc:
        raise SystemExit(f"NARRATION_QA_ERROR: {exc}")
