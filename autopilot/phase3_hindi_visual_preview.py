"""FlowMinute Phase 3R2: ORIGINAL Hindi Short and Hindi long-form visual proofs.

Parses only the fixed authored CSV draft and matching script-derived SRT.
Generates bounded silent MP4 previews without voices, third-party pictures,
external accounts, browser/network access, new service connections or uploads.
Hindi uses installed Noto Devanagari fonts with RAQM shaping; fails closed if
these prerequisites do not exist, rather than publishing tofu/missing glyphs.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont, features

from .agent_org import WorkflowError
from .phase2r3_authored_pack_audit import _sections, _seconds, SOURCE, TIME
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv

PROFILES = {
    "csv_tutorial_short_hi": ("short", 42, 4),
    "csv_tutorial_long_hi": ("long", 432, 24),
}
COLUMNS = (
    ("product", "units", "price"),
    ("Pen", "2", "10"),
    ("Notebook", "1", "30"),
    ("Eraser", "4", "2"),
)
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Medium.ttf",
)
LATIN_FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
)
MAX_FRAMES = 540
MAX_HIRES_FRAMES = 36  # <= 1.5 seconds at 24 fps per preview, no full-sized batch


def _font(size: int, *, devanagari: bool = False) -> ImageFont.FreeTypeFont:
    if devanagari and not features.check("raqm"):
        raise WorkflowError("HarfBuzz/RAQM shaping required for meaningful Hindi glyph rendering")
    candidates = FONT_CANDIDATES if devanagari else LATIN_FONTS
    for name in candidates:
        if Path(name).is_file():
            return ImageFont.truetype(name,size,layout_engine=ImageFont.Layout.RAQM)
    raise WorkflowError("Required installed language font unavailable; never silently use wrong glyphs")


def _timestamp(value: str) -> int:
    if not re.fullmatch(r"\d{2}:\d{2}:\d{2},\d{3}", value):
        raise WorkflowError("Invalid strict SRT timestamp")
    hour,minute,remainder=value.split(":")
    second,millis=remainder.split(",")
    if int(minute)>59 or int(second)>59:
        raise WorkflowError("Invalid SRT clock")
    return (int(hour)*3600+int(minute)*60+int(second))*1000+int(millis)


@lru_cache(maxsize=2)
def _authored_profile(episode_id: str):
    if episode_id not in PROFILES:
        raise WorkflowError("Only fixed Hindi CSV script episodes are supported")
    sections=_sections(SOURCE.read_text(encoding="utf-8"))
    scene=sections[0] if episode_id=="csv_tutorial_short_hi" else sections[2]
    rows=TIME.findall(scene)
    kind,seconds,expected=PROFILES[episode_id]
    if len(rows)!=expected:
        raise WorkflowError("Original authored voice scene count differs")
    beats=[]
    for a,b,c,d,spoken,visual in rows:
        beats.append((_seconds(a,b)*1000,_seconds(c,d)*1000,spoken,visual))
    if not beats or beats[0][0]!=0 or beats[-1][1]!=seconds*1000 or any(
        beats[i-1][1]!=beats[i][0] for i in range(1,len(beats))
    ):
        raise WorkflowError("Original authored voice scene timing altered")
    script_srt=build_subtitles_from_authored_csv()[episode_id]["srt"]
    subtitles=[]
    for block in script_srt.strip().split("\n\n"):
        lines=block.splitlines()
        if len(lines)!=3 or not lines[0].isdigit() or " --> " not in lines[1]:
            raise WorkflowError("Malformed generated SRT")
        first,last=lines[1].split(" --> ")
        subtitles.append((_timestamp(first),_timestamp(last),lines[2]))
    if not subtitles or subtitles[0][0]!=0 or subtitles[-1][1]!=seconds*1000 or any(
        subtitles[i-1][1]!=subtitles[i][0] for i in range(1,len(subtitles))
    ):
        raise WorkflowError("Caption timeline does not cover authored script")
    return kind,seconds,tuple(beats),tuple(subtitles)


def _shown_cue(profile, time_ms: int) -> str:
    for start,end,text in profile[3]:
        if start <= time_ms < end:
            return text
    raise WorkflowError("No authored Hindi cue at video instant")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: float,
          *, max_lines: int=4) -> list[str]:
    lines=[]
    buffer=""
    for word in text.split():
        trial=(buffer+" "+word).strip()
        if draw.textlength(trial,font=font)<=width:
            buffer=trial
        else:
            if not buffer:
                raise WorkflowError("Single word too wide for caption")
            lines.append(buffer)
            buffer=word
    if buffer:
        lines.append(buffer)
    if len(lines)>max_lines:
        raise WorkflowError("Caption exceeds portrait/landscape safe area")
    return lines


def render_hindi_frame(
    episode_id: str,time_seconds: float, *, width: int
) -> Image.Image:
    """Draw one real original animated SVG-like data scene in Pillow.

    No real app screen is depicted; all work is an illustrative *simulation*.
    """
    kind,seconds,beats,cues=_authored_profile(episode_id)
    valid_widths=(360,540,720,1080) if kind=="short" else (640,960,1280,1920)
    if width not in valid_widths or not 0 <= time_seconds < seconds:
        raise WorkflowError("Unsupported script, bounded dimensions or video timestamp")
    ratio=16/9 if kind=="short" else 9/16
    height=round(width*ratio)
    scale=width/(540 if kind=="short" else 960)
    r=lambda n:max(1,round(n*scale))
    x=lambda n:round(n*scale)
    millis=round(time_seconds*1000)
    position=next(i for i,b in enumerate(beats) if b[0]<=millis<b[1])
    caption=_shown_cue((kind,seconds,beats,cues),millis)
    image=Image.new("RGB",(width,height))
    drawer=ImageDraw.Draw(image)
    for y in range(height):
        t=y/height
        drawer.line((0,y,width,y),fill=(6,round(16+7*t),round(32+20*t)))
    d=ImageDraw.Draw(image,"RGBA")
    phase=math.sin(time_seconds*1.3)
    for k in range(14):
        yy=x(68+k*68+(time_seconds*6)%68)
        d.line((0,yy,width,yy),fill=(47,149,183,32),width=r(1))
    for k in range(15):
        px=x((36+77*k+7*math.sin(time_seconds/2+k))%(500 if kind=="short" else 900))
        py=x((104+59*k+9*math.cos(time_seconds/3+k))%(900 if kind=="short" else 490))
        d.ellipse((px-r(2),py-r(2),px+r(2),py+r(2)),fill=(92,225,215,130))

    canvas_w=540 if kind=="short" else 960
    canvas_h=960 if kind=="short" else 540
    d.rounded_rectangle((x(22),x(55),x(canvas_w-22),x(117)),radius=r(18),
                        fill=(6,49,70,240),outline=(68,218,219,190),width=r(2))
    title_font=_font(r(23 if kind=="short" else 28))
    d.text((x(42),x(72)),"FM  /  FLOWMINUTE LAB",font=title_font,fill=(230,250,251))
    d.text((x(43),x(133)),"HINDI DATA LESSON  |  VISUAL ONLY",
           font=_font(r(16)),fill=(112,218,220))

    left=34 if kind=="short" else 44
    right=canvas_w-left
    top=235 if kind=="short" else 184
    bottom=704 if kind=="short" else 425
    bob=round(6*math.sin(time_seconds*1.1))
    d.rounded_rectangle((x(left+4),x(top+bob+8),x(right+4),x(bottom+bob+8)),
                        radius=r(24),fill=(4,126,145,94))
    d.rounded_rectangle((x(left),x(top+bob),x(right),x(bottom+bob)),
                        radius=r(24),fill=(7,44,71,240),
                        outline=(57,212,225,205),width=r(2))

    # Semantic content changes with actual authored scene number, not just
    # a slideshow of arbitrary cards. Four repeating styles reuse the same
    # tiny original fictional CSV dataset, never private user information.
    mode=position%4
    label=("CSV के 3 कॉलम","काल्पनिक डेटा","DictReader उदाहरण","कुल = 58")[mode]
    devanagari=_font(r(22 if kind=="short" else 26),devanagari=True)
    d.text((x(left+25),x(top+25+bob)),label,font=devanagari,fill=(239,250,249))
    if mode==0:
        header=("PRODUCT","UNITS","PRICE")
        data=COLUMNS[1:]
        x0=[left+30,left+140,left+257] if kind=="short" else [left+70,left+300,left+525]
        font_small=_font(r(15 if kind=="short" else 22))
        # Animated row scanner draws attention to actual fictional data.
        focus=int(time_seconds/2)%len(data)
        for i,col in enumerate(header):
            d.text((x(x0[i]),x(top+98+bob)),col,font=font_small,fill=(100,231,216))
        for row_index, row in enumerate(data):
            cy=top+148+row_index*(79 if kind=="short" else 55)
            highlight=row_index==focus
            d.rounded_rectangle((x(left+24),x(cy+bob),x(right-24),x(cy+57+bob if kind=="short" else cy+43+bob)),
                                radius=r(10),
                                fill=((25,162,168,230) if highlight else (30,91,118,170)),
                                outline=((132,253,229,205) if highlight else (55,153,173,90)),
                                width=r(1))
            for i,value in enumerate(row):
                d.text((x(x0[i]),x(cy+15+bob)),value,font=font_small,
                       fill=(245,247,248))
        d.text((x(left+26),x(bottom-51+bob)),"FICTIONAL SAMPLE DATA",
               font=_font(r(14)),fill=(119,236,209))
    elif mode==1:
        # Real explanatory contrast: fictional row contributions, not
        # the previous static table or a fabricated live app screenshot.
        contributions=(("Pen",20),("Notebook",30),("Eraser",8))
        label_font=_font(r(15 if kind=="short" else 21))
        bar_left=left+(133 if kind=="short" else 225)
        bar_right=right-38
        length=bar_right-bar_left
        origin=top+(115 if kind=="short" else 95)
        interval=79 if kind=="short" else 54
        progress=min(1,max(0.2,(time_seconds-beats[position][0]/1000)/2))
        for row_index,(item,units) in enumerate(contributions):
            cy=origin+row_index*interval+bob
            d.text((x(left+29),x(cy+2)),item,font=label_font,fill=(229,242,247))
            d.rounded_rectangle((x(bar_left),x(cy),x(bar_right),x(cy+25)),
                                radius=r(8),fill=(22,84,114,215))
            span=max(12,round(length*(units/30)*progress))
            colors=((57,216,205,240),(248,195,100,240),(81,158,247,240))
            d.rounded_rectangle((x(bar_left),x(cy),x(bar_left+span),x(cy+25)),
                                radius=r(8),fill=colors[row_index])
            d.text((x(bar_right-53),x(cy-26 if kind=="long" else cy+28)),
                   str(units),font=label_font,fill=(252,250,215))
        d.text((x(left+30),x(bottom-50+bob)),
               "20 + 30 + 8 = 58  |  FICTIONAL",
               font=_font(r(14 if kind=="short" else 17)),
               fill=(158,239,215))
    elif mode==2:
        snippets=["import csv","csv.DictReader(rows)","row['units']  ->  2","row['price']  ->  10"]
        for i,code in enumerate(snippets):
            d.text((x(left+43),x(top+113+i*(68 if kind=="short" else 46)+bob)),
                   code,font=_font(r(20 if kind=="short" else 28)),fill=(128,238,220))
        d.text((x(left+33),x(bottom-51+bob)),"ILLUSTRATIVE SIMULATION",
               font=_font(r(13)),fill=(251,208,139))
    else:
        center=(x(canvas_w/2),x(top+246+bob if kind=="short" else top+147+bob))
        rad=r(82 if kind=="short" else 96)
        d.ellipse((center[0]-rad,center[1]-rad,center[0]+rad,center[1]+rad),
                  fill=(9,145,169,192),outline=(96,245,211,235),width=r(4))
        ff=_font(r(68 if kind=="short" else 90))
        w=d.textlength("58",font=ff)
        d.text((center[0]-w/2,center[1]-r(48)), "58",font=ff,fill=(253,246,201))
        d.text((x(left+55),x(bottom-51+bob)),"20 + 30 + 8 = 58 EXAMPLE UNITS",
               font=_font(r(16)),fill=(142,231,223))

    caption_box=(735,899) if kind=="short" else (449,505)
    caption_top,caption_bottom=caption_box
    d.rounded_rectangle((x(28),x(caption_top),x(canvas_w-28),x(caption_bottom)),
                        radius=r(18),fill=(4,14,28,248),
                        outline=(53,178,195,210),width=r(2))
    cap_font=_font(r(19 if kind=="short" else 19),devanagari=True)
    max_lines=4 if kind=="short" else 2
    lines=_wrap(d,caption,cap_font,x(canvas_w-105),max_lines=max_lines)
    line_height=37 if kind=="short" else 26
    y0=caption_top+17 if kind=="short" else caption_top+7
    for line in lines:
        w=d.textlength(line,font=cap_font)
        d.text(((width-w)/2,x(y0)),line,font=cap_font,fill=(246,247,253))
        y0+=line_height
    d.text((x(36),x(919 if kind=="short" else 515)),
           "NO NARRATION  /  NOT FOR PUBLICATION",
           font=_font(r(13 if kind=="short" else 15)),fill=(169,206,211))
    return image


def render_hindi_visual_preview(
    episode_id: str,output: Path, *,
    duration_s: float=2, fps: int=8,width: int|None=None,start_s:float=0
) -> dict:
    kind,seconds,_,_=_authored_profile(episode_id)
    width=width or (360 if kind=="short" else 640)
    # Full-size video frames are much heavier than the existing 360/640px
    # previews. Prove the aspect/glyph/encoder contract with <=36 high-res
    # frames only, without silently authorizing a full production-length job.
    high_resolution = width in (1080,1920)
    max_frames = MAX_HIRES_FRAMES if high_resolution else MAX_FRAMES
    if (not 0.5 <= duration_s <= seconds or fps not in (8,12,24)
            or not 0 <= start_s < seconds or start_s+duration_s > seconds
            or round(duration_s*fps)>max_frames):
        raise WorkflowError("Preview exceeds bounded rendering limits")
    output=Path(output)
    if output.suffix.lower()!=".mp4" or output.is_symlink() or output.exists():
        raise WorkflowError("Fresh MP4 preview output required")
    if not output.parent.is_dir():
        raise WorkflowError("Preview output folder must already exist")
    if shutil.which("ffmpeg") is None:
        raise WorkflowError("System FFmpeg required; no installing or service access")
    # Assert relevant glyph font/shaping availability before launching encoder.
    _font(20,devanagari=True)
    first=render_hindi_frame(episode_id,start_s,width=width)
    size=f"{first.width}x{first.height}"
    cmd=["ffmpeg","-nostdin","-v","error","-y",
         "-f","rawvideo","-pixel_format","rgb24","-video_size",size,
         "-framerate",str(fps),"-i","pipe:0","-an","-c:v","libx264",
         "-preset","veryfast","-pix_fmt","yuv420p","-crf","28",
         "-movflags","+faststart",str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i in range(round(duration_s*fps)):
            img=first if i==0 else render_hindi_frame(
                episode_id,start_s+i/fps,width=width)
            proc.stdin.write(img.tobytes())
        proc.stdin.close()
        stderr=proc.stderr.read()
        proc.wait(timeout=180)
        if proc.returncode:
            raise WorkflowError("Original video-only encoding failed")
        if not output.is_file() or output.stat().st_size < 2048:
            raise WorkflowError("Original visual-only MP4 missing or too small")
    except Exception:
        proc.kill()
        proc.wait()
        output.unlink(missing_ok=True)
        raise
    sha=sha256(output.read_bytes()).hexdigest()
    return {
        "status":"REAL_HINDI_MP4_VISUAL_ONLY_NOT_PUBLISHABLE",
        "episode_id":episode_id,"format":kind,
        "width":first.width,"height":first.height,
        "rendered_duration_seconds":duration_s,
        "preview_offset_seconds":start_s,
        "fps":fps,"sha256":sha,
        "actual_video_pixels_encoded":True,
        "audio_track_present":False,
        "voice_rights_verified":False,
        "spoken_subtitle_alignment_verified":False,
        "script_editorial_facts_verified":False,
        "publishing_authorized":False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description="Phase 3 Hindi visual-only proof")
    parser.add_argument("--episode",choices=sorted(PROFILES),required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--duration",type=float,default=2)
    parser.add_argument("--fps",type=int,default=8)
    parser.add_argument("--width",type=int)
    parser.add_argument("--start",type=float,default=0)
    args=parser.parse_args(argv)
    result=render_hindi_visual_preview(
        args.episode,args.output,duration_s=args.duration,
        fps=args.fps,width=args.width,start_s=args.start)
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
