"""Three *full-duration*, no-publish educational demonstration videos on GitHub.

Synthetic CSV data; original text and graphics; real pinned Kokoro CPU voices,
scene-level spoken caption timestamps measured from generated PCM, subtle original
scene-change sounds, FFmpeg H264/AAC + burned SRT and complete decode. Results,
weight files and sample videos are destroyed after the CI run. NOT RELEASE-READY.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import textwrap
import time

from autopilot.cloud_av_probe import verify_pinned_assets, sha256_stream
from autopilot.full_pack_fixture import EPISODES, inspect_example_csv, validate_fixture

FPS = 24
STATUS = "FULL_DURATION_EDUCATIONAL_TECHNICAL_BENCHMARK_NOT_PUBLISHABLE"


class PackError(ValueError):
    pass


def sentence_chunks(narration: str) -> tuple[str, ...]:
    chunks = tuple(s.strip() for s in re.split(r"(?<=[.!?])\s+", narration) if s.strip())
    if not chunks or any(not 8 <= len(s) <= 235 for s in chunks):
        raise PackError("Bad narration chunks")
    return chunks


def ms_stamp(seconds: float) -> str:
    if not 0 <= seconds <= 3600 or not math.isfinite(seconds):
        raise PackError("Bad caption time")
    t = round(seconds * 1000)
    hh, t = divmod(t, 3600_000)
    mm, t = divmod(t, 60_000)
    ss, milli = divmod(t, 1000)
    return f"{hh:02}:{mm:02}:{ss:02},{milli:03}"


def validate_cues(cues: list[dict], length: float, expected: int) -> None:
    if len(cues) != expected or expected < 8:
        raise PackError("Missing caption cues")
    previous = 0.0
    for c in cues:
        if not isinstance(c["text"], str) or len(c["text"]) < 8:
            raise PackError("Empty spoken caption")
        if not previous - .001 <= c["start"] < c["end"] <= length + .005:
            raise PackError("Caption overlaps or exceeds spoken media")
        previous = c["end"]
    if length - previous > 1:
        raise PackError("Spoken tail has no caption")


def run(cmd: list[str], timeout: int = 1100) -> str:
    try:
        proc = subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=timeout)
        return proc.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        stderr = (getattr(exc, "stderr", "") or "")
        raise PackError(f"Media command failed: {type(exc).__name__}: {stderr[-700:]}") from exc


def narration_and_srt(voice_engine, episode, folder: Path):
    import numpy as np
    import soundfile as sf
    samples, captions, timings = [], [], []
    rate = None
    ticks = 0
    scene_cue_count = 0
    sample_starts = []
    started = time.monotonic()
    for i, scene in enumerate(episode.scenes):
        scene_start = ticks
        sample_starts.append(ticks)
        for cue in sentence_chunks(scene.narration):
            pcm, hz = voice_engine.create(cue, voice=episode.voice,
                                          speed=1.24 if episode.kind == "short" else 1.2,
                                          lang="en-us")
            arr = np.asarray(pcm, dtype=np.float32)
            if (arr.ndim != 1 or arr.size < hz * .7 or
                not np.isfinite(arr).all() or np.max(np.abs(arr)) < .002):
                raise PackError("Invalid real TTS segment")
            if rate is None:
                rate = hz
            if hz != rate:
                raise PackError("Inconsistent TTS sample rate")
            start = ticks / hz
            samples.append(arr)
            ticks += arr.size
            end = ticks / hz
            captions.append({"start": start, "end": end, "text": cue, "scene": i})
            scene_cue_count += 1
            pause = np.zeros(round(hz * .08), dtype=np.float32)
            samples.append(pause)
            ticks += pause.size
        extra = np.zeros(round(rate * .12), dtype=np.float32)
        samples.append(extra)
        ticks += extra.size
        timings.append({"start": scene_start / rate, "duration": (ticks-scene_start) / rate})
    duration = ticks / rate
    validate_cues(captions, duration, scene_cue_count)
    sound = np.concatenate(samples)
    for offset in sample_starts[1:]:
        n = min(int(rate * .045), sound.size - offset)
        t = np.arange(n, dtype=np.float32) / rate
        sound[offset:offset+n] += .007 * np.sin(2 * np.pi * 650 * t) * np.sin(np.linspace(0,math.pi,n))**2
    sound = np.clip(sound, -1, 1)
    wav = folder / "original_voice.wav"
    sf.write(wav, sound, rate, subtype="PCM_16")
    srt = folder / "scene_captions.srt"
    width = 38 if episode.kind == "short" else 69
    blocks = []
    for i, c in enumerate(captions, 1):
        text = "\n".join(textwrap.wrap(c["text"], width=width, break_long_words=False))
        blocks += [str(i), f"{ms_stamp(c['start'])} --> {ms_stamp(c['end'])}", text, ""]
    srt.write_text("\n".join(blocks)+"\n", encoding="utf8")
    return wav, srt, timings, captions, duration, round(time.monotonic()-started,2)


def demo_messages(mode: str, result: dict) -> list[str]:
    options = {
      "raw": ["SOURCE: FOUR ORIGINAL ROWS", "Values remain unchanged", "Review instead of overwriting"],
      "identity": ["MEMBER ID = '00127'", "5 text digits expected", "Not a quantity"],
      "cast": ["int('00127') --> 127", "A label has changed", "Preserve keys as text"],
      "text": ["csv.DictReader => string", "'00127' remains '00127'", "Confirm length before export"],
      "inspect": [f"LOADED: {result['row_count']} rows", "Original IDs preserved", "Review exceptions first"],
      "duplicates": ["00127 repeats in row 3", "First occurrence: row 1", "Flag both records"],
      "comparison": ["ROW 1 vs ROW 3", "Joining dates differ", "Never delete on key alone"],
      "dates": ["ROW 4: 11/04/26", "Expected YYYY-MM-DD", "Ask before guessing date"],
      "report": ["ONE REPEATED KEY", "ONE DATE EXCEPTION", "Two records need review"],
      "headers": ["member_id, joined_on, status", "3 columns checked", "Reject unexpected headers"],
      "workflow": ["01 - READ ORIGINAL", "02 - VALIDATE EXPLICITLY", "03 - REPORT FOR REVIEW"],
      "summary": ["PRESERVE TEXT IDS", "FLAG KEYS AND DATES", "REVIEW BEFORE EXPORT"],
    }
    if mode not in options:
        raise PackError("Unapproved graphic scene")
    return options[mode]


def frame(episode, scene, index: int, result: dict, output: Path) -> str:
    """Render bespoke computed CSV workflow graphics, not borrowed stock assets."""
    from PIL import Image, ImageDraw, ImageFont
    portrait = episode.kind == "short"
    w,h = (1080,1920) if portrait else (1920,1080)
    sans="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    mono="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    F = lambda path,size: ImageFont.truetype(path,size)
    big, body, small, code = F(sans,69 if portrait else 66),F(sans,36 if portrait else 34),F(sans,26),F(mono,26)
    background=(11,21,37); bright=(235,245,255); blue=(78,169,245)
    im=Image.new("RGB",(w,h),background)
    d=ImageDraw.Draw(im)
    for y in range(0,h,83):
        d.line((0,y,w,y),fill=(21,37,57),width=2)
    d.rounded_rectangle((45,46,w-45,h-45),radius=32,outline=(48,77,105),width=3)
    d.text((78,89),"FLOWMINUTE LAB   |   CODED CSV DEMO",font=small,fill=blue)
    d.text((w-195,90),f"{index+1:02} / {len(episode.scenes):02}",font=small,fill=(184,205,222))
    lines=textwrap.wrap(scene.title,width=23 if portrait else 45,break_long_words=False)
    y=192
    for ln in lines[:3]:
        d.text((78,y),ln,font=big,fill=bright)
        y+=80
    top=530 if portrait else 355
    left=(78,top,w-78,top+445) if portrait else (78,top,1020,h-210)
    right=(78,top+473,w-78,h-365) if portrait else (1050,top,w-78,h-210)
    d.rounded_rectangle(left,radius=22,fill=(28,48,69),outline=(51,95,133),width=2)
    d.rounded_rectangle(right,radius=22,fill=(32,55,74),outline=(51,95,133),width=2)
    x1,y1,x2,_=left
    d.text((x1+28,y1+22),"REAL SYNTHETIC CSV INPUT",font=small,fill=(143,213,255))
    cols=[x1+27,x1+145,x1+393,x1+680] if portrait else [x1+27,x1+125,x1+366,x1+677]
    for x,lab in zip(cols,("ROW","MEMBER ID","JOINED ON","STATUS")):
        d.text((x,y1+83),lab,font=small,fill=(143,213,255))
    for j,row in enumerate(result["rows"]):
        yy=y1+150+j*(59 if portrait else 62)
        if j==scene.focus_row:
            d.rounded_rectangle((x1+18,yy-7,x2-18,yy+51),radius=9,fill=(50,83,104))
        values=[f"{j+1:02}",row["member_id"],row["joined_on"],row["status"]]
        for x,val in zip(cols,values):
            highlight=scene.mode in ("duplicates","comparison","dates","report") and j in result["potential_review_rows"]
            d.text((x,yy),val,font=code,fill=(255,178,151) if highlight else bright)
    x2,y2,xend,yend=right
    d.text((x2+24,y2+24),"ACTUAL PYTHON DEMO OUTPUT",font=small,fill=(117,222,183))
    for k,content in enumerate(demo_messages(scene.mode,result)):
        yy=y2+112+k*(90 if portrait else 92)
        if yy<yend-35:
            d.text((x2+27,yy),content,font=body,fill=(255,207,132) if k==0 else bright)
    # Caption-safe panel: SRT text will be burned into the output independently.
    d.rounded_rectangle((85,h-(295 if portrait else 175),w-85,h-88),radius=15,fill=(19,37,56))
    d.text((96,h-104),"UNREVIEWED TEST VIDEO  |  NO PUBLISH",font=small,fill=(162,185,211))
    im.save(output,format="PNG",optimize=True)
    sha,sz=sha256_stream(output,max_bytes=18_000_000)
    return sha


def encode(episode, folder: Path, images: list[Path], timings: list[dict],
           voice: Path, captions: Path, total: float) -> Path:
    from PIL import Image,ImageDraw
    if len(images)!=len(timings) or len(images)<6:
        raise PackError("Scene/image timing mismatch")
    ffcat=folder/"scene_order.ffconcat"
    lines=["ffconcat version 1.0"]
    for pic,t in zip(images,timings):
        if not 1 <= t["duration"] <= 40:
            raise PackError("Spoken scene too short or long")
        lines += [f"file '{pic.as_posix()}'",f"duration {t['duration']:.6f}"]
    lines += [f"file '{images[-1].as_posix()}'"]
    ffcat.write_text("\n".join(lines)+"\n",encoding="utf8")
    dot=Image.new("RGBA",(82,14),(0,0,0,0))
    ImageDraw.Draw(dot).rounded_rectangle((0,0,81,13),radius=6,fill=(90,220,175,255))
    dotfile=folder/"moving_progress.png"
    dot.save(dotfile)
    fontsize=23 if episode.kind=="short" else 21
    # ASS PlayRes scaling: ~24/31 style units positions captions inside\n    # the bottom caption-safe panel, not halfway up the screen.\n    margin=24 if episode.kind=="short" else 31
    subfilter=(f"subtitles={captions.as_posix()}:force_style='FontName=DejaVu Sans,"
               "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
               f"Outline=2,FontSize={fontsize},Alignment=2,MarginV={margin}'")
    filt=(f"[0:v]fps={FPS},{subfilter},format=yuv420p[base];"
          f"[base][2:v]overlay=x='max(0,min(W-w,(W-w)*t/{total:.4f}))':"
          "y=H-h-38:shortest=1,format=yuv420p[v]")
    out=folder/"UNAPPROVED_FULL_EDUCATION_TEST.mp4"
    run([
      "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
      "-f","concat","-safe","0","-i",str(ffcat),
      "-i",str(voice),
      "-loop","1","-framerate",str(FPS),"-i",str(dotfile),
      "-filter_complex",filt,"-map","[v]","-map","1:a:0",
      "-c:v","libx264","-preset","ultrafast","-crf","30",
      "-pix_fmt","yuv420p","-threads","2","-c:a","aac","-b:a","128k",
      "-t",f"{total:.4f}","-movflags","+faststart","-y",str(out)
    ],timeout=1500)
    return out


def inspect(out: Path, episode, cues: list[dict], total: float, images: list[Path]) -> dict:
    probe=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(out)]))
    streams=probe.get("streams",[])
    v=[s for s in streams if s.get("codec_type")=="video"]
    a=[s for s in streams if s.get("codec_type")=="audio"]
    if len(v)!=1 or len(a)!=1:
        raise PackError("Video/audio streams not unique")
    expected=(1080,1920) if episode.kind=="short" else (1920,1080)
    if ((v[0].get("width"),v[0].get("height"))!=expected or
         v[0].get("codec_name")!="h264" or v[0].get("pix_fmt")!="yuv420p" or
         a[0].get("codec_name")!="aac"):
        raise PackError("Wrong media dimensions, codec or pixel format")
    duration=float(probe.get("format",{}).get("duration",0))
    minimum,maximum=(26,88) if episode.kind=="short" else (105,260)
    if not minimum<=duration<=maximum or abs(duration-total)>.75:
        raise PackError(f"Invalid duration or sound drift: {duration:.2f}, expected {total:.2f}")
    validate_cues(cues,total,len(cues))
    if len({sha256_stream(pic,max_bytes=18_000_000)[0] for pic in images})!=len(images):
        raise PackError("Not all storyboard images are unique")
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-xerror",
         "-i",str(out),"-f","null","-"],timeout=1200)
    sha,size=sha256_stream(out,max_bytes=300_000_000)
    if size<200_000:
        raise PackError("MP4 appears empty")
    return {
      "episode":episode.episode_id,"kind":episode.kind,
      "voice":episode.voice,"seconds":round(duration,2),
      "sha256":sha,"bytes":size,
      "resolution":f"{expected[0]}x{expected[1]}",
      "codec":"h264+aac","scene_count":len(images),
      "narration_cues":len(cues),"subtitles_burned":True,
      "captions_timed_by_original_pcm":True,
      "transition_sfx_original":True,"full_decode_passed":True,
      "human_full_watch_asserted":False,
      "independent_fact_review_passed":False,
      "rights_clearance_asserted":False,
      "youtube_upload_enabled":False,
    }


def benchmark(model: Path, voices: Path, root: Path) -> dict:
    from kokoro_onnx import Kokoro
    if root.is_symlink() or (root.exists() and any(root.iterdir())):
        raise PackError("Refusing to overwrite old benchmark")
    assets=verify_pinned_assets(model,voices)
    sample=validate_fixture()
    root.mkdir(parents=True)
    start=time.monotonic()
    engine=Kokoro(str(model),str(voices))
    outputs=[]
    try:
        for episode in EPISODES:
            ep_start=time.monotonic()
            folder=root/episode.episode_id
            folder.mkdir()
            wav,srt,timings,cues,total,tts_s=narration_and_srt(engine,episode,folder)
            images=[]
            for index,scene in enumerate(episode.scenes):
                path=folder/f"scene_{index+1:02}.png"
                frame(episode,scene,index,sample,path)
                images.append(path)
            mp4=encode(episode,folder,images,timings,wav,srt,total)
            qa=inspect(mp4,episode,cues,total,images)
            qa["tts_seconds"]=tts_s
            qa["end_to_end_seconds"]=round(time.monotonic()-ep_start,2)
            qa["script_words"]=sum(len(s.narration.split()) for s in episode.scenes)
            outputs.append(qa)
            print("COMPLETE_UNPUBLISHED_EPISODE",json.dumps({
                "episode":qa["episode"],"duration":qa["seconds"],
                "tts_s":tts_s,"wall_s":qa["end_to_end_seconds"],
                "frames":qa["scene_count"],"captions":qa["narration_cues"]
            }),flush=True)
    finally:
        close=getattr(getattr(engine,"voices",None),"close",None)
        if callable(close):
            close()
    if len(outputs)!=3 or len({x["sha256"] for x in outputs})!=3:
        raise PackError("Missing or duplicated film")
    return {
      "schema_version":1,"status":STATUS,
      "source":"synthetic original Python CSV educational fixture; NOT model-generated",
      "cloud_runner_no_laptop":True,
      "original_membership_sample_rows":sample["row_count"],
      "computed_duplicate_count":len(sample["duplicate_ids"]),
      "computed_date_exception_count":len(sample["invalid_iso_dates"]),
      "model_sha256_verified":assets["model_sha256"],
      "voice_pack_sha256_verified":assets["voice_pack_sha256"],
      "videos":outputs,
      "total_seconds":round(time.monotonic()-start,2),
      "private_durable_storage_connected":False,
      "full_video_human_watch_and_rights_approved":False,
      "external_paid_calls":0,
      "youtube_upload_enabled":False,"youtube_schedule_enabled":False,
      "next_gate":"Independent creative, visual, audio, factual and rights review; later approved secure media publisher",
    }


def main():
    ap=argparse.ArgumentParser(description="GitHub-only full narrated sample pack; NEVER upload")
    ap.add_argument("--model",type=Path,required=True)
    ap.add_argument("--voices",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    report=benchmark(args.model,args.voices,args.output_dir)
    (args.output_dir/"technical_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps({
      "status":report["status"],"videos":len(report["videos"]),
      "durations":[v["seconds"] for v in report["videos"]],
      "scenes":[v["scene_count"] for v in report["videos"]],
      "srt_cues":[v["narration_cues"] for v in report["videos"]],
      "full_decodes":[v["full_decode_passed"] for v in report["videos"]],
      "wall_seconds":report["total_seconds"],"youtube_upload_enabled":False
    }),flush=True)


if __name__=="__main__":
    main()
