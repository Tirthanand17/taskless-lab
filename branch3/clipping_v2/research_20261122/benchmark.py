"""Compare two candidate signals on generated footage. No external media inputs."""
import argparse
import array
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from scripts import branch3_v2_p5_longform_local_signal_planner as p5
from scripts.branch3_v2_p6_longform_editorial_intake import build_unreviewed_editorial_intake
from .media import digest, probe, rank, render, save, transcribe, validate

CHAPTERS = [
    [
        "Why does a recording sound different across the room?",
        "The microphone hears your voice and every reflection from the walls.",
        "Move closer and the balance changes before you touch a single setting.",
        "Try the same sentence twice and listen to the difference.",
        "The quieter room often matters more than an expensive microphone.",
        "That simple comparison is a good place to start.",
    ],
    [
        "How do you tell whether a caption is easy to read?",
        "Play the video on a phone and turn the sound down.",
        "Read the text once at normal speed while watching the person speaking.",
        "A line that disappears halfway through a sentence needs more time.",
        "Move the words above the controls so the buttons do not cover them.",
        "Now replay the same section and see whether the meaning is clear.",
    ],
]
RATE = 16000


def synthesize(text, output):
    engine = shutil.which("espeak-ng") or shutil.which("espeak")
    if engine:
        subprocess.run([engine, "-v", "en", "-s", "155", "-w", str(output), text], check=True)
    elif os.name == "nt":
        code = ("Add-Type -AssemblyName System.Speech; "
                "$v=New-Object System.Speech.Synthesis.SpeechSynthesizer; $v.Rate=-1; "
                "$v.SetOutputToWaveFile($env:DEMO_WAVE); $v.Speak($env:DEMO_TEXT); $v.Dispose()")
        subprocess.run(["powershell.exe", "-NoProfile", "-Command", code], check=True,
                       env={**os.environ, "DEMO_WAVE": str(output), "DEMO_TEXT": text})
    else:
        raise RuntimeError("Install espeak-ng for the speech benchmark")


def make_fixture(folder, speech):
    samples = bytearray()
    rows = []
    tone = array.array("h", [round(3500*math.sin(2*math.pi*220*i/RATE)) for i in range(RATE)])
    if sys.byteorder != "little":
        tone.byteswap()
    for chapter in CHAPTERS:
        samples.extend(bytes(6 * RATE * 2))
        if speech:
            wav = folder / "chapter.wav"
            synthesize(" ".join(chapter), wav)
            samples.extend(subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(wav),
                          "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"]))
        else:
            for sentence in chapter:
                start = len(samples) / (2 * RATE)
                samples.extend(tone.tobytes() * 5)
                rows.append(dict(start=start, end=start+5, text=sentence))
    track = folder / "audio.wav"
    with wave.open(str(track), "wb") as w:
        w.setparams((1, 2, RATE, 0, "NONE", ""))
        w.writeframes(samples)
    source = folder / "fixture.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "color=0x244863:s=640x360:r=24", "-i", str(track), "-shortest",
                    "-c:v", "libx264", "-c:a", "aac", str(source)], check=True)
    return source, rows


def measure(source):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(source), "-ac", "1",
                                  "-ar", str(RATE), "-f", "s16le", "-"])
    pcm = array.array("h")
    pcm.frombytes(raw)
    if sys.byteorder != "little":
        pcm.byteswap()
    width = RATE // 2
    rms = []
    for offset in range(0, len(pcm), width):
        chunk = pcm[offset:offset+width]
        rms.append(min(32767, round(math.sqrt(sum(x*x for x in chunk)/len(chunk)))))
    return dict(schema_version=1, channel_id=p5.CHANNEL, source_measurements_state=p5.STATE,
                duration_ms=math.ceil(len(pcm)*1000/RATE), rms_step_ms=p5.STEP_MS,
                audio_rms=rms, scene_cuts_ms=[], unverified_editor_marks_ms=[])


def verify_captions(path):
    # The entire source and matte are dark. Bright pixels in this band are rendered glyphs.
    pixels = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                                      "fps=1,crop=720:360:0:760,scale=180:90,format=gray",
                                      "-f", "rawvideo", "-"])
    if sum(p > 160 for p in pixels) < 40:
        raise ValueError("No visible caption pixels in the decoded lower portion of the frame")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--speech", action="store_true", help="Generate speech and use cached base ASR")
    parser.add_argument("--output", type=Path, help="Retain synthetic results in a new directory")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        if args.output:
            folder = args.output.resolve()
            folder.mkdir(parents=True, exist_ok=False)
        source, supplied = make_fixture(folder, args.speech)
        signals = measure(source)
        plan = p5.plan_longform_candidates(signals)
        intake = build_unreviewed_editorial_intake(measurements=signals, report=plan)
        if not intake["cards"] or intake["ready_to_publish"] or intake["ready_to_render"]:
            raise ValueError("Expected synthetic, unapproved P6 review cards")
        rows = transcribe(source, "en") if args.speech else supplied
        duration, _, _ = probe(source)
        validate(rows, duration)
        proposals = rank(rows, 2)
        if len(proposals) != 2:
            raise ValueError("Expected two disjoint synthetic excerpts")
        for i, clip in enumerate(proposals, 1):
            dest = folder / f"clip-{i}"
            render(source, rows, clip, dest)
            verify_captions(dest / "short.mp4")
            clip["sha256"] = digest(dest / "short.mp4")
        report = dict(synthetic=True, transcript_origin="faster-whisper" if args.speech else "fixture",
                      candidate_windows=proposals, acoustic_plan=plan, editorial_intake=intake)
        save(folder / "result.json", report)
        print(json.dumps({"source_seconds": round(duration, 2), "transcript": report["transcript_origin"],
                          "review_cards": len(intake["cards"]),
                          "rendered_seconds": [round(c["end"]-c["start"], 2) for c in proposals]}))


if __name__ == "__main__":
    main()
