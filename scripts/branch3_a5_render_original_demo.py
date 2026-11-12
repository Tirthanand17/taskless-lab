"""Clivox A5 ORIGINAL-ONLY render benchmark, never an authorized source clip.

Creates abstract vector/typographic scene cards from the approved-to-*draft*
A4 SOURCE-FREE blueprint; does NOT access source videos, transcripts, YouTube,
OAuth or creator media. Audio is an ORIGINAL LOW-VOLUME SYNTHETIC TEST TONE,
NOT narration or an approved soundtrack.

Dependencies on GitHub Actions: Python 3.12, Pillow, FFmpeg/FFprobe.
Output only into the runner's temporary directory. No uploader exists.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import wave

from scripts.branch3_a4_editorial import check_script

CLIVOX="UCfPEvy0SefE_5nNlYlY_CyQ"
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"branch3/editorial/fixtures/ymh_ep347_source_free.json"
BG=(8,12,22)
ORANGE=(255,91,36)
SILVER=(230,234,244)
MUTED=(156,168,186)

class RenderDenied(ValueError):
    pass

def require(value: bool, reason: str) -> None:
    if not value:
        raise RenderDenied("CLIVOX_A5_DENY_"+reason)

def font_path() -> Path:
    available=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",
    ]
    for path in available:
        if Path(path).is_file():
            return Path(path)
    raise RenderDenied("CLIVOX_A5_DENY_NO_SYSTEM_FONT")

def draw_card(beat: dict, index: int, total: int, out: Path, mode: str) -> None:
    # No outside artwork or user supplied media is ever loaded.
    from PIL import Image, ImageDraw, ImageFont
    width,height=(1080,1920) if mode=="full" else (540,960)
    k=width/1080
    font=font_path()
    def f(px: int):
        return ImageFont.truetype(str(font),max(10,int(px*k)))
    def xy(*coords):
        return tuple(round(c*k) for c in coords)
    im=Image.new("RGB",(width,height),BG)
    draw=ImageDraw.Draw(im)
    # Dimensional blue-charcoal studio background; original procedural art.
    for y in range(height):
        t=y/max(1,height-1)
        draw.line([(0,y),(width,y)],
                  fill=(int(8+11*t),int(12+16*t),int(22+20*t)))
    for x in range(-height,width+height,round(112*k)):
        draw.line([(x,0),(x+int(660*k),height)],
                  fill=(25,34,52),width=max(1,int(2*k)))
    # Strong left orange signature and restrained metallic side strokes.
    draw.rounded_rectangle(xy(85,352,996,1500),radius=int(46*k),
                           fill=(17,24,39),outline=(52,62,80),width=max(1,int(2*k)))
    draw.rounded_rectangle(xy(89,394,99,1430),radius=int(5*k),fill=ORANGE)
    draw.line([xy(112,204),xy(364,204)],fill=ORANGE,width=max(2,int(6*k)))
    draw.text(xy(108,100),"CLIVOX",font=f(69),fill=SILVER)
    draw.text(xy(110,226),"ORIGINAL EDIT / DESIGN LAB",font=f(25),fill=MUTED)
    draw.text(xy(110,377),f"0{index+1} / 0{total}",font=f(30),fill=ORANGE)
    draw.text(xy(110,1650),"DEMO ONLY",font=f(33),fill=ORANGE)
    draw.text(xy(110,1713),"NOT CLEARED FOR YOUTUBE RELEASE",
              font=f(23),fill=SILVER)
    draw.rounded_rectangle(xy(108,1780,972,1790),radius=int(4*k),fill=(42,50,66))
    draw.rounded_rectangle(xy(108,1780,108+round((864*(index+1)/total)),1790),
                           radius=int(4*k),fill=ORANGE)
    # All text is original authored by Clivox. The unlicensed footage scene
    # is intentionally just a visible locked placeholder.
    lines={
        "hook":(["WOULD YOU TRY","AN '80s","RESTAURANT?"],"A QUESTION WORTH EXPLORING"),
        "context":(["A MENU.","A MEMORY.","A MOMENT."],"ORIGINAL HYPOTHETICAL SETUP"),
        "licensed_source_placeholder":(["SOURCE","SLOT LOCKED"],"NO CREATOR FOOTAGE / NO LICENSE"),
        "original_analysis":(["NOSTALGIA","IS THE","SECRET"],"ORIGINAL CLIVOX COMMENTARY"),
        "ending":(["VISIT","OR SKIP?"],"YOUR TAKE"),
    }
    role=beat["role"]
    require(role in lines,"UNSUPPORTED_SCENE")
    headline,description=lines[role]
    main=f(100 if max(map(len,headline))<=12 else 86)
    yy=525
    for line in headline:
        # Lay out by measured actual font width to avoid cropped typography.
        bbox=draw.textbbox((0,0),line,font=main)
        require(bbox[2]-bbox[0]<730*k,"HEADLINE_OUT_OF_SAFE_AREA")
        draw.text(xy(155,yy),line,font=main,fill=SILVER)
        yy+=154
    draw.text(xy(157,1112),description,font=f(27),fill=ORANGE)
    if role=="licensed_source_placeholder":
        draw.rounded_rectangle(xy(159,1250,900,1385),
                               radius=int(15*k),outline=ORANGE,
                               width=max(2,int(3*k)))
        draw.text(xy(188,1288),"UNVERIFIED RIGHTS",font=f(37),fill=SILVER)
    elif role=="original_analysis":
        for i,label in enumerate(("FAMILIAR","PERSONAL","SURPRISING")):
            top=1160+i*86
            draw.rounded_rectangle(xy(159,top,880,top+68),radius=int(14*k),
                                   fill=(30,40,59),outline=(57,67,82),
                                   width=max(1,int(k)))
            draw.text(xy(190,top+12),label,font=f(34),fill=SILVER)
    elif role=="ending":
        for i,label in enumerate(("TRY IT","SKIP IT")):
            left=158+i*360
            draw.rounded_rectangle(xy(left,1190,left+320,1280),
                                   radius=int(15*k),
                                   fill=ORANGE if i==0 else (39,50,67))
            draw.text(xy(left+28,1214),label,font=f(34),
                      fill=(12,16,23) if i==0 else SILVER)
    elif role=="context":
        draw.rounded_rectangle(xy(168,1210,872,1360),radius=int(20*k),
                               fill=(31,42,61),outline=(68,79,98),
                               width=max(1,int(2*k)))
        draw.text(xy(208,1256),"A ORIGINAL STORY",font=f(32),fill=SILVER)
    elif role=="hook":
        draw.line([xy(159,1244),xy(872,1244)],fill=ORANGE,
                  width=max(2,int(6*k)))
        draw.text(xy(159,1300),"WHAT WOULD YOU ORDER?",font=f(35),fill=MUTED)
    out.parent.mkdir(parents=True,exist_ok=True)
    im.save(out,optimize=True)

def original_tones(out: Path, seconds: int, beat_boundaries: list[int]) -> None:
    # Synthesis only. NOT a voiceover, music library, or licensed track.
    sr=48000
    samples=array("h")
    total=seconds*sr
    for i in range(total):
        t=i/sr
        fade=min(1.0,t/0.12,(seconds-t)/0.18)
        drone=(math.sin(2*math.pi*98*t)+0.35*math.sin(2*math.pi*196*t))*250
        pulse=0.
        for boundary in beat_boundaries:
            dt=t-boundary
            if 0<=dt<=0.28:
                pulse+=math.sin(2*math.pi*(420+160*dt)*dt)*math.exp(-14*dt)*2100
        value=round(max(-32768,min(32767,(drone+pulse)*max(0.,fade))))
        samples.append(value)
    with wave.open(str(out),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(samples.tobytes())

def timestamp(seconds: float) -> str:
    ms=int(round(seconds*1000))
    h,rem=divmod(ms,3_600_000)
    m,rem=divmod(rem,60_000)
    s,milli=divmod(rem,1000)
    return f"{h:02}:{m:02}:{s:02},{milli:03}"

def visual_script_srt(beats: list[dict], output: Path) -> None:
    # Cues describe the proposed on-screen script. With synthesized tones
    # instead of speech these are NOT an audio transcript.
    from textwrap import wrap
    cues=[]
    for b in beats:
        narration=b["original_narration"]
        if narration is None:
            text="SOURCE PLACEHOLDER — RIGHTS NOT VERIFIED"
            segments=[text]
        else:
            words=narration.split()
            segments=[]
            line=""
            for word in words:
                check=(line+" "+word).strip()
                if len(check)>42 and line:
                    segments.append(line)
                    line=word
                else:
                    line=check
            if line:
                segments.append(line)
        duration=b["end_s"]-b["start_s"]
        for i,segment in enumerate(segments):
            start=b["start_s"]+duration*i/len(segments)
            end=b["start_s"]+duration*(i+1)/len(segments)
            lines=wrap(segment,width=24,break_long_words=False,break_on_hyphens=False)
            require(len(lines)<=2 and all(len(line)<=30 for line in lines),"SUBTITLE_TOO_DENSE")
            cues.append((start,end,"\n".join(lines)))
    result=[]
    for i,(start,end,text) in enumerate(cues,1):
        result.append(f"{i}\n{timestamp(start)} --> {timestamp(end)}\n{text}\n")
    output.write_text("\n".join(result)+"\n",encoding="utf-8")

def encode(scene_files: list[Path], wav_file: Path, output: Path,
           seconds: list[int], mode: str) -> None:
    require(shutil.which("ffmpeg") and shutil.which("ffprobe"),
            "FFMPEG_NOT_INSTALLED")
    width,height,fps=(1080,1920,30) if mode=="full" else (540,960,24)
    fade_frames=round(fps*0.375)
    fade=fade_frames/fps
    cmd=["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y"]
    for file in scene_files:
        cmd+=["-i",str(file)]
    cmd+=["-i",str(wav_file)]
    filters=[]
    for i,duration in enumerate(seconds):
        frames=round(duration*fps)+(0 if i==len(seconds)-1 else fade_frames)
        filters.append(
            f"[{i}:v]zoompan=z='min(zoom+0.00018,1.065)':"
            f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d={frames}:"
            f"s={width}x{height}:fps={fps},settb=AVTB,"
            f"setpts=PTS-STARTPTS,format=yuv420p[v{i}]"
        )
    last="v0"
    offset=0
    for i in range(1,len(seconds)):
        offset+=seconds[i-1]
        new=f"m{i}"
        filters.append(f"[{last}][v{i}]xfade=transition=fade:"
                       f"duration={fade:.6f}:offset={offset:.6f}[{new}]")
        last=new
    filters.append(f"[{last}]format=yuv420p[outv]")
    cmd+=["-filter_complex",";".join(filters),"-map","[outv]",
          "-map",f"{len(scene_files)}:a:0",
          "-c:v","libx264","-pix_fmt","yuv420p","-preset","veryfast",
          "-crf","24" if mode=="full" else "27",
          "-profile:v","high","-r",str(fps),"-threads","2",
          "-c:a","aac","-ar","48000","-b:a","96k",
          "-movflags","+faststart","-t",str(sum(seconds)),
          str(output)]
    subprocess.run(cmd,check=True,timeout=600)

def digest_file(path: Path) -> str:
    hasher=hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda:file.read(1024*1024),b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_demo(proposal: dict, out: Path, mode: str) -> dict:
    checked=check_script(proposal)  # mandatory fail-closed A4 readback
    require(mode in ("preview","full"),"MODE")
    require(out.exists() and out.is_dir() and not out.is_symlink(),"OUTPUT_DIRECTORY")
    beats=proposal["beats"]
    seconds=[b["end_s"]-b["start_s"] for b in beats]
    require(sum(seconds)==40 and len(beats)==5,"A5_DEMO_SCENE_SHAPE")
    scene_files=[]
    for i,beat in enumerate(beats):
        png=out/f"scene-{i:02}.png"
        draw_card(beat,i,len(beats),png,mode)
        scene_files.append(png)
    wav=out/"original-preview-tones.wav"
    original_tones(wav,40,[0,2,7,21,36])
    srt=out/"on-screen-editorial-script-not-dialogue.srt"
    visual_script_srt(beats,srt)
    mp4=out/"clivox-original-only-a5-demo.mp4"
    encode(scene_files,wav,mp4,seconds,mode)
    manifest={
        "schema_version":1,"channel_id":CLIVOX,
        "stage":"A5_ORIGINAL_ONLY_SYNTHETIC_BENCHMARK",
        "mode":mode,
        "concept_id":proposal["proposal_id"],
        "source_blueprint_sha256":checked["editorial_plan_sha256"],
        "video_name":mp4.name,"video_sha256":digest_file(mp4),
        "video_size_bytes":mp4.stat().st_size,
        "srt_name":srt.name,"srt_sha256":digest_file(srt),
        "scene_card_names":[p.name for p in scene_files],
        "source_media_attached":False,
        "third_party_source_audio_used":False,
        "original_voiceover_recorded":False,
        "audio_content":"LOW_VOLUME_ORIGINAL_SYNTHETIC_TONES_NOT_NARRATION",
        "subtitle_content":"PROPOSED_ON_SCREEN_EDITORIAL_TEXT_NOT_SPEECH_TRANSCRIPT",
        "source_placeholder_visible":True,
        "watermark":"DEMO ONLY / NOT CLEARED FOR YOUTUBE RELEASE",
        "reviewed_by_human":False,
        "actual_media_qa_passed":False,
        "copyright_clearance_verified":False,
        "ready_to_upload":False,
        "ready_to_schedule":False,
        "ready_to_publish":False,
    }
    path=out/"synthetic-demo-manifest.json"
    path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=DEFAULT)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mode",choices=("preview","full"),default="preview")
    args=parser.parse_args()
    require(args.input.is_file() and not args.input.is_symlink()
            and args.input.stat().st_size<100_000,"INPUT_FILE")
    require(args.output.is_absolute(),"OUTPUT_MUST_BE_ABSOLUTE")
    require(ROOT not in args.output.parents and args.output!=ROOT,
            "MUST_NOT_RENDER_IN_PUBLIC_REPOSITORY")
    require(args.output.exists() and args.output.is_dir() and not args.output.is_symlink(),
            "OUTPUT_DIRECTORY_MISSING")
    proposal=json.loads(args.input.read_text("utf-8"))
    result=create_demo(proposal,args.output,args.mode)
    print(json.dumps({
        "stage":result["stage"],"mode":result["mode"],
        "sha256":result["video_sha256"],"size":result["video_size_bytes"],
        "ready_to_publish":False,
    },sort_keys=True))
    print("CLIVOX_A5_ORIGINAL_ONLY_NO_CREATOR_FOOTAGE_NO_YOUTUBE_WRITE")

if __name__=="__main__":
    main()
