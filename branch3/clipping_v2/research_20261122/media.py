import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def probe(path):
    cmd = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    info = json.loads(subprocess.check_output(cmd))
    streams = info["streams"]
    video = next((s for s in streams if s["codec_type"] == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
    audio = next((s for s in streams if s["codec_type"] == "audio"), None)
    if not video or not audio:
        raise ValueError("A recording with both a video and an audio track is required")
    duration = float(info["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Invalid media duration")
    return duration, video, audio


def transcribe(path, language):
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download

    weights = snapshot_download("Systran/faster-whisper-base", local_files_only=True,
                                revision="ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66")
    model = WhisperModel(weights, device="cpu", compute_type="int8", cpu_threads=4,
                         local_files_only=True)
    segments, _ = model.transcribe(str(path), language=language, vad_filter=True, beam_size=3,
                                   word_timestamps=True)
    return [dict(start=s.start, end=s.end, text=s.text.strip(),
                 words=[dict(start=w.start, end=w.end, text=w.word) for w in s.words or []])
            for s in segments if s.text.strip()]


def validate(rows, duration):
    previous = 0
    for row in rows:
        start, end = row["start"], row["end"]
        if not (0 <= start < end <= duration + 0.5 and start >= previous - 0.05
                and isinstance(row["text"], str) and row["text"].strip()):
            raise ValueError("Invalid, overlapping or out-of-bounds transcript segment")
        previous = end
        row["end"] = min(end, duration)
    if not rows:
        raise ValueError("No speech was found")


def rank(rows, count):
    """Favor standalone openings, complete endings, steady speech and ~32 second clips."""
    choices = []
    for i, first in enumerate(rows):
        for j in range(i, len(rows)):
            last = rows[j]
            length = last["end"] - first["start"]
            if length > 50 or (j > i and last["start"] - rows[j-1]["end"] > 2.5):
                break
            if length < 15:
                continue
            text = " ".join(r["text"] for r in rows[i:j+1])
            speech_time = sum(r["end"] - r["start"] for r in rows[i:j+1])
            hook = bool(re.search(r"\b(why|how|mistake|because|instead|secret|first|learned)\b|\d",
                                  first["text"], re.I))
            complete = bool(re.search(r"[.!?।。！？][\"'”]?$", last["text"]))
            fresh = i == 0 or bool(re.search(r"[.!?।。！？][\"'”]?$", rows[i-1]["text"]))
            score = 2*complete + fresh + hook + speech_time/length - abs(length-32)/20
            choices.append((score, i, j, text))
    picked = []
    for score, i, j, text in sorted(choices, key=lambda x: (-x[0], x[1], x[2])):
        start, end = rows[i]["start"], rows[j]["end"]
        if any(start < p["end"] and end > p["start"] for p in picked):
            continue
        title = re.split(r"(?<=[.!?।。！？])\s+", text, maxsplit=1)[0]
        title = " ".join(title.replace("<", "").replace(">", "").split())[:95].rstrip()
        picked.append(dict(start=start, end=end, title=title or "Excerpt", score=round(score, 3),
                           transcript=text, first=i, last=j))
        if len(picked) == count:
            break
    return picked


def ass_time(t):
    cs = max(0, round(t * 100))
    return f"{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}"


def caption_events(row):
    words = row.get("words") or []
    if not words:
        yield row["start"], row["end"], row["text"]
        return
    group = []
    for w in words:
        group.append(w)
        if len(group) >= 6 or len("".join(x["text"] for x in group)) >= 30:
            yield group[0]["start"], group[-1]["end"], "".join(x["text"] for x in group)
            group = []
    if group:
        yield group[0]["start"], group[-1]["end"], "".join(x["text"] for x in group)


def render(source, rows, clip, folder):
    folder.mkdir(parents=True, exist_ok=True)
    start, end = clip["start"], clip["end"]
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,Arial,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,55,80,240,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    lines = [header]
    for row in rows[clip["first"]:clip["last"]+1]:
        for a, b, text in caption_events(row):
            a, b = max(start, a), min(end, b)
            if a < b:
                safe = " ".join(text.split()).translate(str.maketrans({"\\": "＼", "{": "(", "}": ")"}))
                lines.append(f"Dialogue: 0,{ass_time(a-start)},{ass_time(b-start)},Main,,0,0,0,,{safe}\n")
    (folder / "captions.ass").write_text("".join(lines), encoding="utf-8-sig")
    layout = ("scale=720:1280:force_original_aspect_ratio=decrease:force_divisible_by=2,"
              "pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=0x111820,setsar=1,"
              "fps=30,ass=captions.ass")
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(start),
           "-i", str(source.resolve()), "-t", str(end-start), "-map", "0:V:0", "-map", "0:a:0",
           "-vf", layout, "-c:v", "libx264", "-threads", "4", "-preset", "veryfast", "-crf", "22",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", "2", "-ar", "48000", "-b:a", "128k",
           "-movflags", "+faststart", "partial.mp4"]
    subprocess.run(cmd, cwd=folder, check=True)
    output = folder / "partial.mp4"
    actual, video, audio = probe(output)
    if ((video["width"], video["height"], video["codec_name"], audio["codec_name"])
            != (720, 1280, "h264", "aac") or abs(actual - (end-start)) > 0.35):
        raise ValueError("Rendered clip failed media verification")
    output.replace(folder / "short.mp4")
