"""Generated-only vertical editing and independent decoded QA.

No user path, third-party media, credentials, upload, or approved release.
The fixture contains synthetic visual blocks, test captions and a test tone,
not actual speech. The fit and stack layouts are deterministic, not tracking.
"""
from __future__ import annotations

import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

from scripts.branch3_v3_multimodal_candidates import demo
from scripts.branch3_v3_transcript_context import fixture_rows
from scripts.branch3_v3_editorial_draft import draft, layout
from scripts.branch3_v2_p5_synthetic_moment_proposals import _probe_closed

W, H, FPS = 1080, 1920, 24


def run(args, cwd, limit=0):
    result = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=120, check=True)
    if len(result.stdout) > limit:
        raise ValueError("unexpected media tool output")
    return result.stdout


def need(ok, code):
    if not ok:
        raise ValueError("CLIVOX_V3_RENDER_" + code)


def ass_time(ms):
    cs = ms // 10
    return f"{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}"


def caption_ass(cues):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Caption,DejaVu Sans,48,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,110,150,310,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    lines = [header]
    for c in cues:
        text = c["text"]
        need(type(text) is str and 0 < len(text) <= 42
             and not any(ch in text for ch in "{}\\\r\n"), "CAPTION_TEXT")
        a,b = c["start_ms"],c["end_ms"]
        need(type(a) is int and type(b) is int and 0 <= a < b <= 24000, "CAPTION_TIME")
        if b//10 > a//10:
            lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Caption,,0,0,0,,{text}\n")
    return "".join(lines)


def geometry_filter(spec):
    """The only accepted geometries are the exact generated fixture presets."""
    fit = layout("dialogue", 320, 180)
    stack = layout("gaming", 320, 180, [0,0,80,180], [80,0,240,180])
    need(spec in (fit,stack), "FIXTURE_GEOMETRY")
    def scale(w,h):
        return (f"scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x111820,setsar=1")
    if spec == fit:
        return "[0:v]"+scale(W,H)+"[base]"
    return ("[0:v]split=2[a][b];[a]crop=80:180:0:0,"+scale(W,600)+"[top];"
            "[b]crop=240:180:80:0,"+scale(W,1320)+"[bottom];"
            "[top][bottom]vstack=inputs=2[base]")


def probe_output(folder, name, duration):
    info=json.loads(run(["ffprobe","-v","error","-protocol_whitelist","file",
                         "-show_streams","-show_format","-of","json",name],folder,64000))
    streams=info["streams"]
    need(len(streams)==2,"STREAM_COUNT")
    v=next(s for s in streams if s["codec_type"]=="video")
    a=next(s for s in streams if s["codec_type"]=="audio")
    need((v["width"],v["height"],v["codec_name"],v["pix_fmt"],v["avg_frame_rate"])
         ==(W,H,"h264","yuv420p","24/1"),"VIDEO")
    need((a["codec_name"],a["sample_rate"],a["channels"])==("aac","48000",1),"AUDIO")
    need(abs(float(info["format"]["duration"])-duration)<.15
         and abs(float(v["duration"])-float(a["duration"]))<.15
         and abs(float(v["start_time"])-float(a["start_time"]))<.1,"AV_TIMING")
    run(["ffmpeg","-v","error","-xerror","-nostdin","-protocol_whitelist","file",
         "-i",name,"-map","0:v","-map","0:a","-f","null","-"],folder)
    # Dark/colored generated fixture has no white source pixels. Bright pixels
    # in the caption area verify actual burn-in, independent of subtitle file.
    pixels=run(["ffmpeg","-v","error","-nostdin","-ss","1","-i",name,
                "-vf","crop=820:180:100:1450,format=gray","-frames:v","1",
                "-f","rawvideo","pipe:1"],folder,820*180)
    need(len(pixels)==820*180 and sum(p>210 for p in pixels)>100,"CAPTION_PIXELS")
    pcm=run(["ffmpeg","-v","error","-nostdin","-ss","1","-i",name,
             "-vn","-t","1","-ac","1","-ar","8000","-f","s16le","pipe:1"],folder,16000)
    samples=array.array("h"); samples.frombytes(pcm)
    if sys.byteorder!="little":
        samples.byteswap()
    need(len(samples)>=7900,"AUDIO_DECODE")
    peak=max(abs(x) for x in samples)
    rms=math.sqrt(sum(x*x for x in samples)/len(samples))
    need(1000<rms<10000 and peak<30000,"AUDIO_LEVEL")
    data=(folder/name).read_bytes()
    need(1024<len(data)<20_000_000,"SIZE")
    return {"width":W,"height":H,"duration_seconds":duration,"codec":"h264/aac",
            "caption_pixels_verified":True,"audio_peak_pcm16":peak,
            "sha256":hashlib.sha256(data).hexdigest()}


def smoke():
    _probe_closed()
    measurements=demo("dialogue")
    measurements["semantic_events_ms"]=None
    plan=draft(measurements,fixture_rows(),"v3_01",320,180)
    need(plan["candidate"]["start_ms"]==0 and plan["candidate"]["end_ms"]==24000
         and plan["render_authorized"] is False,"FIXTURE_DRAFT")
    with tempfile.TemporaryDirectory(prefix="clivox-v3-render-") as root:
        folder=Path(root)
        (folder/"captions.ass").write_text(caption_ass(plan["caption_cues"]),encoding="utf-8")
        run(["ffmpeg","-hide_banner","-v","error","-nostdin","-f","lavfi","-i",
             "color=c=0x244863:s=320x180:r=24:d=24","-f","lavfi","-i",
             "sine=frequency=440:sample_rate=48000:duration=24","-vf",
             "drawbox=x=0:y=0:w=80:h=180:color=0x225533:t=fill",
             "-c:v","libx264","-threads:v","1","-pix_fmt","yuv420p","-c:a","aac",
             "-t","24","source.mp4"],folder)
        output=[]
        for spec in (plan["layout"],layout("gaming",320,180,[0,0,80,180],[80,0,240,180])):
            name=spec["mode"]+".mp4"
            graph=geometry_filter(spec)+";[base]ass=captions.ass[v]"
            run(["ffmpeg","-hide_banner","-v","error","-nostdin","-protocol_whitelist","file",
                 "-i","source.mp4","-filter_complex_threads","1","-filter_complex",graph,
                 "-map","[v]","-map","0:a:0","-af","volume=1.5,alimiter=limit=0.8:level=false",
                 "-c:v","libx264","-threads:v","2","-preset","ultrafast","-crf","23",
                 "-pix_fmt","yuv420p","-r","24","-c:a","aac","-ar","48000","-ac","1",
                 "-movflags","+faststart","-t","24",name],folder)
            output.append(dict(layout=spec["mode"],**probe_output(folder,name,24)))
        _probe_closed()
        return {"generated_fixture_only":True,"outputs":output,"source_speech_verified":False,
                "automatic_subject_tracking":False,"original_commentary_approved":False,
                "production_ready":False,"youtube_upload_authorized":False}


if __name__=="__main__":
    print(json.dumps(smoke(),sort_keys=True))
