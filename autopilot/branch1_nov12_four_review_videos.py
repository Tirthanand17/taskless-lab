"""Flowminute Branch 1 Nov 12: source-locked, original four-video owner review.

Three Shorts and one long, physically rendered on disposable GitHub runners.
No OAuth, YouTube API, publishing, real-screen-capture misrepresentation,
external video/music/stock assets, or desktop filesystem use.
The words and illustrative values are authored and vendor-source-cited.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess
import textwrap

STATUS="B1_NOV12_FOUR_REAL_ORIGINAL_VIDEO_FILES_OWNER_REVIEW_ONLY_NO_UPLOAD"
ROOT=Path(__file__).resolve().parents[1]
BRIEF=ROOT/"content/nov12_2026/four_video_review_brief.json"
SLOTS=("11:00","13:30","16:00","20:30")
IDENTIFIERS=(
    "nov12_short_a_excel_16digits",
    "nov12_short_b_ai_fake_citations",
    "nov12_long_excel_silent_errors",
    "nov12_short_c_drive_link",
)
PALETTE=((90,209,236),(235,176,101),(148,201,242),(109,220,171))
ALLOWED_SOURCES={
    "https://support.microsoft.com/en-us/excel/format-numbers-as-text",
    "https://support.microsoft.com/en-us/excel/keeping-leading-zeros-and-large-numbers",
    "https://help.openai.com/en/articles/8313428-does-chatgpt-tell-the-truth",
    "https://support.google.com/drive/answer/7166529",
}
MIN_WORDS={"short":60,"long":360}
MAX_WORDS={"short":110,"long":640}
VIDEO_SIZE={"short":(1080,1920),"long":(1920,1080)}
FPS=30
AUDIO_TARGET=-18.0
B4G5_AUDIO_FILTER="loudnorm=I=-18:TP=-1.5:LRA=11:linear=false:print_format=none"
DEJAVU="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEJAVU_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


class FourVideoRefused(ValueError):
    """Reject forged release state, wrong source, layout or physical media."""


def need(condition,reason):
    if not condition:
        raise FourVideoRefused(reason)


def canonical(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=True,
                      separators=(",",":"),allow_nan=False).encode("ascii")


def load_brief(source=BRIEF):
    need(source==BRIEF and source.is_file() and not source.is_symlink()
         and source.stat().st_size<65000,"Missing source-authored four-video brief")
    raw=source.read_bytes()
    data=json.loads(raw)
    need(type(data) is dict and
         data.get("status")=="UNAPPROVED_BRANCH1_2026_11_12_FOUR_ORIGINAL_EDUCATIONAL_VIDEOS"
         and data.get("date_ist")=="2026-11-12"
         and data.get("channel_id")=="UCCcL9Q_jqVq6LJmnYUSAFZA"
         and data.get("target_timezone")=="Asia/Kolkata"
         and data.get("decision")=="owner_review_before_any_youtube_upload_or_schedule"
         and data.get("safety")=={
             "actual_publishing_allowed":False,"owner_final_watch":False,
             "rights_final_review":False,"mock_app_ui_labeled":True,
         } and type(data.get("episodes")) is list
         and len(data["episodes"])==4,"Improper date/channel/approval scope")
    need([x.get("id") for x in data["episodes"]]==list(IDENTIFIERS)
         and [x.get("time") for x in data["episodes"]]==list(SLOTS)
         and [x.get("type") for x in data["episodes"]]==
             ["short","short","long","short"],
         "Four ordered original November 12 slots are required")
    for ep in data["episodes"]:
        kind=ep["type"]
        need(ep.get("source") in ALLOWED_SOURCES
             and type(ep.get("title")) is str and 14<len(ep["title"])<=100
             and type(ep.get("description")) is str and 65<len(ep["description"])<=1200
             and ep.get("voice") in ("af_heart","am_michael","bf_emma","af_sarah")
             and type(ep.get("cover")) is str and 7<=len(ep["cover"])<=26,
             "Unknown source, voice, or episode packaging")
        scenes=ep.get("scenes")
        need(type(scenes) is list
             and len(scenes)==(5 if kind=="short" else 12),
             "Do not pad or omit real source-authored narrative beats")
        words=0
        for scene in scenes:
            need(type(scene) is list and len(scene)==4
                 and all(type(value) is str and value.strip()==value
                         for value in scene)
                 and 4<=len(scene[0])<=38 and 4<=len(scene[1])<=27
                 and 3<=len(scene[2])<=27
                 and 30<=len(scene[3])<=540
                 and not any("\n" in value or "\r" in value
                             for value in scene),
                 "Unbounded source authored script or visual labels")
            words+=len(scene[3].split())
        need(MIN_WORDS[kind]<=words<=MAX_WORDS[kind],
             "Wrong promised duration: real script cannot be padded")
    return data,sha256(raw).hexdigest()


def font(size,bold=False):
    from PIL import ImageFont
    path=DEJAVU_BOLD if bold else DEJAVU
    need(Path(path).is_file(),"Unlicensed/missing local glyph font")
    return ImageFont.truetype(path,size)


def fitting_font(draw,label,max_width,size,min_size=21,bold=True):
    for value in range(size,min_size-1,-1):
        chosen=font(value,bold)
        if draw.textbbox((0,0),label,font=chosen)[2]<=max_width:
            return chosen
    raise FourVideoRefused("Text would be clipped at physical video size")


def draw_text(draw,label,x,y,maxwidth,size,color,bold=True):
    chosen=fitting_font(draw,label,maxwidth,size,bold=bold)
    draw.text((x,y),label,font=chosen,fill=color)
    bounds=draw.textbbox((x,y),label,font=chosen)
    need(bounds[2]<=x+maxwidth+2,"Exact physical text safe area overflow")


def rounded(draw,rect,fill,outline=None,radius=24,width=2):
    draw.rounded_rectangle(rect,radius=radius,fill=fill,
                           outline=outline,width=width)


def draw_illustrative_spreadsheet(draw,ep,scene,index,phase,accent):
    """Original data-type demonstration fills the empty long-video left half.

    Clearly marked as a synthetic illustration; no actual Excel capture,
    no unverified vendor UI claim, no customer identifiers and no external media.
    """
    from PIL import ImageDraw
    heading,source,observed,_=scene
    x0,y0,x1,y1=108,355,747,790
    rounded(draw,(x0,y0,x1,y1),(231,242,246),(123,175,193),25,3)
    rounded(draw,(x0+12,y0+13,x1-12,y0+82),(29,71,88),
            (29,71,88),12,2)
    draw_text(draw,"FICTIONAL DATA  /  NOT A LIVE SCREEN",
              x0+28,y0+31,x1-x0-56,25,(218,244,250),False)
    # Light spreadsheet grid with an informative column comparison.
    col=(x0+318)
    draw.rectangle((x0+21,y0+101,x1-21,y0+148),
                   fill=(192,218,231))
    draw_text(draw,"RAW SOURCE",x0+37,y0+108,265,29,(31,68,89))
    draw_text(draw,"CELL IMPORT",col+12,y0+108,x1-col-32,29,(31,68,89))
    rows=[(source,observed),("TEXT VALUE","AUTO TYPE"),
          ("CHECK INPUT","VERIFY RESULT")]
    for j,(left,right) in enumerate(rows):
        top=y0+169+j*76
        fill=(247,251,252) if j%2==0 else (224,236,242)
        draw.rectangle((x0+21,top,x1-21,top+67),fill=fill)
        if (phase>=1 and j==0):
            draw.rectangle((x0+21,top,col,top+67),fill=(207,241,245))
        if (phase>=2 and j==0):
            draw.rectangle((col,top,x1-21,top+67),fill=(255,230,198))
        draw_text(draw,left,x0+35,top+19,col-x0-58,
                  33 if j==0 else 28,(17,50,69))
        draw_text(draw,right,col+12,top+19,x1-col-40,
                  33 if j==0 else 28,
                  (142,58,30) if phase>=2 and j==0 else (17,50,69))
        draw.line((col,top,col,top+67),fill=(136,165,180),width=2)
    draw_text(draw,"WATCH THE VALUE, NOT JUST THE FORMAT",
              x0+32,y1-55,x1-x0-60,23,(27,79,97),False)


def render_frame(ep,scene,index,phase,accent):
    """Four original instructional diagram layouts, 3 one-way states.

    Each frame contains the actual case/example and never a spinning circle.
    No fabricated real app screenshot; all material tagged ILLUSTRATIVE.
    """
    from PIL import Image,ImageDraw
    kind=ep["type"]
    portrait=kind=="short"
    w,h=VIDEO_SIZE[kind]
    need(type(phase) is int and phase in (0,1,2)
         and type(index) is int and 0<=index<len(ep["scenes"]),
         "Invalid original one-way scene frame")
    image=Image.new("RGB",(w,h),(8,17,30))
    d=ImageDraw.Draw(image)
    for y in range(0,h,24):
        value=y/h
        d.rectangle((0,y,w,min(h,y+24)),
                    fill=(9+int(value*5),19+int(value*6),34+int(value*12)))
    d.rectangle((0,0,14,h),fill=accent)
    margin=78 if portrait else 108
    draw_text(d,"FLOWMINUTE  /  REAL-LIFE TECH FIX",margin,65,w-2*margin,
              29 if portrait else 28,(156,193,217),False)
    d.line((margin,130,w-margin,130),fill=(55,82,107),width=3)
    heading,first,second,_=scene
    if portrait:
        draw_text(d,heading,margin,178,w-2*margin,79,(246,251,255))
        draw_text(d,"FICTIONAL DEMO  /  VERIFIED PRODUCT RULE",
                  margin,297,w-2*margin,25,(156,192,217),False)
        area=(margin,405,w-margin,1390)
        caption=(margin,1500,w-margin,1765)
        step_y=1440
    else:
        draw_text(d,heading,margin,171,w-2*margin,93,(246,251,255))
        draw_text(d,"FICTIONAL EXAMPLE  /  OFFICIAL GUIDANCE",
                  margin,288,w-2*margin,26,(153,189,215),False)
        area=(780,352,w-margin,790)
        caption=(margin,827,w-margin,1017)
        step_y=805
    ax0,ay0,ax1,ay1=area
    if not portrait:
        draw_illustrative_spreadsheet(d,ep,scene,index,phase,accent)
    rounded(d,area,(19,35,54),(61,89,117),25,3)
    mode=index%4
    visible1=phase>=1
    visible2=phase>=2
    if mode==0:
        if portrait:
            cards=[(ax0+34,ay0+120,ax1-34,ay0+415),
                   (ax0+34,ay0+515,ax1-34,ay0+810)]
        else:
            mid=(ax0+ax1)//2
            cards=[(ax0+25,ay0+110,mid-12,ay1-58),
                   (mid+12,ay0+110,ax1-25,ay1-58)]
        draw_text(d,"BEFORE  /  AFTER" if index==0 else "COMPARE THE OUTCOME",
                  ax0+42,ay0+34,ax1-ax0-85,35,accent,True)
        for j,(rect,label,active) in enumerate(zip(
                cards,(first,second),(visible1,visible2))):
            rounded(d,rect,(35,67,82) if active else (26,43,63),
                    accent if active else (63,91,111),23,4 if active else 2)
            rw=rect[2]-rect[0]
            title="INPUT" if j==0 else "RESULT / CHECK"
            draw_text(d,title,rect[0]+27,rect[1]+35,rw-54,30,
                      accent if active else (137,162,180))
            draw_text(d,label,rect[0]+27,rect[1]+128,rw-54,
                      67 if portrait else 55,
                      (242,248,255) if active else (165,187,205))
        if portrait and index==0 and ep["id"]=="nov12_short_a_excel_16digits":
            draw_text(d,"LAST DIGIT  6 → 0",ax0+45,ay1-100,
                      ax1-ax0-90,57,accent)
    elif mode==1:
        draw_text(d,"THE RULE",ax0+42,ay0+43,ax1-ax0-85,37,accent)
        draw_text(d,first,ax0+46,ay0+(205 if portrait else 132),ax1-ax0-98,
                  115 if portrait else 78,
                  (244,248,253) if visible1 else (116,137,157))
        line_y=ay0+(390 if portrait else 257)
        d.line((ax0+55,line_y,ax1-55,line_y),
                fill=accent if visible1 else (77,98,120),width=5)
        draw_text(d,second,ax0+46,ay0+(520 if portrait else 295),
                  ax1-ax0-98,95 if portrait else 67,
                  accent if visible2 else (114,142,161))
    elif mode==2:
        draw_text(d,"FOLLOW THE TWO CHECKS",ax0+40,ay0+36,
                  ax1-ax0-85,36,accent)
        cards=[(ax0+40,ay0+172,ax1-40,ay0+420),
               (ax0+40,ay0+505,ax1-40,ay0+755)] if portrait else [
                (ax0+33,ay0+116,ax1-33,ay0+244),
                (ax0+33,ay0+286,ax1-33,ay0+405)]
        for i,(rect,label,active) in enumerate(zip(
                cards,(first,second),(visible1,visible2))):
            rounded(d,rect,(34,65,78) if active else (23,41,61),
                    accent if active else (69,97,115),22)
            draw_text(d,f"{i+1:02}",rect[0]+25,rect[1]+34,98,
                      65 if portrait else 48,accent)
            draw_text(d,label,rect[0]+140 if portrait else rect[0]+105,
                      rect[1]+52 if portrait else rect[1]+41,
                      rect[2]-rect[0]-(174 if portrait else 129),
                      63 if portrait else 52,
                      (246,250,253) if active else (144,166,185))
    else:
        # Native-looking ORIGINAL education visualization, not a real UI.
        top=ay0+(115 if portrait else 45)
        rounded(d,(ax0+38,top,ax1-38,ay1-20),
                (230,237,241),(111,139,160),20,3)
        d.rectangle((ax0+39,top,ax1-39,top+77),fill=(45,70,94))
        for n,c in enumerate(((235,115,100),(230,184,90),(116,209,161))):
            d.ellipse((ax0+62+n*36,top+26,ax0+78+n*36,top+42),fill=c)
        draw_text(d,"ILLUSTRATIVE DATA",ax0+72,
                  top+(125 if portrait else 92),
                  ax1-ax0-140,37,(20,50,78))
        cardwidth=ax1-ax0-130
        left=ax0+67
        for i,(label,active) in enumerate(((first,visible1),(second,visible2))):
            cy=top+(240 if portrait else 150)+i*(197 if portrait else 105)
            rounded(d,(left,cy,left+cardwidth,cy+(150 if portrait else 104)),
                    (224,247,248) if active else (210,223,232),
                    (34,153,165) if active else (126,149,164),18)
            draw_text(d,label,left+24,cy+(49 if portrait else 27),
                      cardwidth-48,57 if portrait else 46,
                      (19,56,67) if active else (98,110,121))
    # The content timeline advances once; NO looped circular indicator.
    base_width=(w-2*margin-(len(ep["scenes"])-1)*8)//len(ep["scenes"])
    for j in range(len(ep["scenes"])):
        xx=margin+j*(base_width+8)
        rounded(d,(xx,step_y,xx+base_width,step_y+11),
                accent if j<=index else (57,79,100),radius=4)
    rounded(d,caption,(16,39,55),(63,92,113),20,2)
    d.rectangle((caption[0]+28,caption[1]+23,
                 caption[0]+140,caption[1]+31),fill=accent)
    footer_y=h-91 if portrait else h-50
    draw_text(d,"ORIGINAL EDUCATION  -  NO REAL CUSTOMER DATA",
              margin,footer_y,w-2*margin,23,(123,154,178),False)
    # Replace the generic loopable slide middle with distinctive,
    # topic-specific original evidence. Keep title/header and the actual
    # native ASS caption-safe card unchanged at their physical pixels.
    from autopilot.branch1_nov12_viewer_first_hero_b1r3 import (
        overlay_original_hero,
    )
    return overlay_original_hero(image,ep,scene,index,phase,accent)


def split_script(text,kind):
    limit=82 if kind=="short" else 114
    sentences=re.split(r"(?<=[.!?])\s+",text)
    parts=[]
    for sentence in sentences:
        if len(sentence)<=limit:
            parts.append(sentence)
            continue
        words=sentence.split(" ")
        chunk=[]
        for word in words:
            if chunk and len(" ".join(chunk+[word]))>limit:
                parts.append(" ".join(chunk))
                chunk=[]
            chunk.append(word)
        if chunk:parts.append(" ".join(chunk))
    need(1<=len(parts)<=12 and all(8<=len(p)<=limit for p in parts)
         and " ".join(parts)==" ".join(text.split()),
         "Narration lost a word or created illegible cue")
    return parts


def secs_stamp(t,ass=False):
    need(type(t) in (int,float) and math.isfinite(t) and 0<=t<3600,
         "Invalid exact PCM cue")
    count=round(t*(100 if ass else 1000))
    if ass:
        hr,count=divmod(count,360000)
        mn,count=divmod(count,6000)
        sec,cs=divmod(count,100)
        return f"{hr}:{mn:02}:{sec:02}.{cs:02}"
    hr,count=divmod(count,3600000)
    mn,count=divmod(count,60000)
    sec,ms=divmod(count,1000)
    return f"{hr:02}:{mn:02}:{sec:02},{ms:03}"


def cues_to_files(cues,kind,folder):
    ass=folder/"ORIGINAL_NATIVE_CAPTIONS.ass"
    srt=folder/"ORIGINAL_SOURCE_TIMED_CAPTIONS.srt"
    portrait=kind=="short"
    w,h=VIDEO_SIZE[kind]
    size=45 if portrait else 43
    margin=250 if portrait else 120
    style=(f"Style: Default,DejaVu Sans,{size},&H00FFFFFF,&H00000000,"
           f"&H900C1C2E,&H00000000,1,0,0,0,100,100,0,0,1,3,0,2,"
           f"120,120,{margin},1")
    header=(
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\n"
        "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
        "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,"
        "ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,"
        "MarginR,MarginV,Encoding\n"+style+"\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,"
        "MarginV,Effect,Text\n")
    lines=[header]
    srt_rows=[]
    for idx,c in enumerate(cues,1):
        maxw=36 if portrait else 63
        visual=textwrap.wrap(c["text"],width=maxw,
                             break_long_words=False,break_on_hyphens=False)
        need(1<=len(visual)<=3,"Native caption too tall")
        need(not any("{" in line or "}" in line for line in visual),
             "Caption data could contain ASS control codes")
        lines.append(f"Dialogue: 0,{secs_stamp(c['start'],True)},"
                     f"{secs_stamp(c['end'],True)},Default,,0,0,0,,"
                     +r"\N".join(visual)+"\n")
        srt_rows.extend((str(idx),
                         f"{secs_stamp(c['start'])} --> {secs_stamp(c['end'])}",
                         "\n".join(visual),""))
    ass.write_text("".join(lines),encoding="utf8")
    srt.write_text("\n".join(srt_rows)+"\n",encoding="utf8")
    return ass,srt


def synthesize(engine,ep,folder):
    import numpy as np
    import soundfile as sf
    scenes=[]
    cues=[]
    audio=[]
    sample_rate=None
    ticks=0
    for idx,scene in enumerate(ep["scenes"]):
        began=ticks
        for part in split_script(scene[3],ep["type"]):
            pcm,hz=engine.create(part,voice=ep["voice"],
                                 speed=1.02 if ep["type"]=="short" else .97,
                                 lang="en-us")
            a=np.asarray(pcm,dtype=np.float32)
            need(a.ndim==1 and 16000<=hz<=48000
                 and hz*.29<=a.size<=hz*30
                 and np.isfinite(a).all() and np.max(np.abs(a))>=.002,
                 "Voice missing, silent or out of range")
            if sample_rate is None:sample_rate=hz
            need(hz==sample_rate,"Voice sample rate changed")
            start=ticks/hz
            audio.append(a)
            ticks+=a.size
            cues.append({"start":start,"end":ticks/hz,
                         "text":part,"scene":idx})
            gap=np.zeros(round(.06*hz),np.float32)
            audio.append(gap);ticks+=gap.size
        gap=np.zeros(round(.15*hz),np.float32)
        audio.append(gap);ticks+=gap.size
        scenes.append((ticks-began)/hz)
    total=ticks/sample_rate
    need(18<=total<=(64 if ep["type"]=="short" else 340)
         and len(cues)>=len(ep["scenes"]), "Actual voice incomplete or too long")
    # Original restrained 65ms tap at every story transition,
    # once per scene, rather than repetitive animation or copyrighted sound.
    joined=np.concatenate(audio).astype(np.float32)
    cursor=0
    for n,duration in enumerate(scenes):
        count=min(round(.065*sample_rate),joined.size-cursor)
        t=np.arange(count,dtype=np.float32)/sample_rate
        pulse=.012*np.sin(2*np.pi*(530 if n%2==0 else 415)*t)
        pulse*=np.sin(np.linspace(0,math.pi,count,dtype=np.float32))**2
        joined[cursor:cursor+count]+=pulse
        cursor+=round(duration*sample_rate)
    joined=np.clip(joined,-.96,.96)
    wav=folder/"REAL_ORIGINAL_VOICE.wav"
    sf.write(wav,joined,sample_rate,subtype="PCM_16")
    need(abs(sum(scenes)-total)<.015,"Original PCM scene timing drift")
    return wav,scenes,cues,round(total,3)


def execute(cmd,timeout=450):
    try:
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired):
        raise FourVideoRefused("Physical media command unavailable or timed out") from None
    if result.returncode:
        raise FourVideoRefused("Actual encode/decode failed; no release")
    return result.stdout


def digest(path):
    need(path.is_file() and not path.is_symlink(),"Missing original media")
    h=sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def build_contact(ep,images,folder):
    from PIL import Image,ImageDraw
    portrait=ep["type"]=="short"
    cw,ch=(360,640) if portrait else (480,270)
    cols=3 if portrait else 4
    rows=math.ceil(len(images)/cols)
    sheet=Image.new("RGB",(cols*cw,rows*(ch+48)),(8,17,28))
    painter=ImageDraw.Draw(sheet)
    for i,filename in enumerate(images):
        x=(i%cols)*cw;y=(i//cols)*(ch+48)
        with Image.open(filename) as image:
            sheet.paste(image.resize((cw,ch),Image.Resampling.LANCZOS),(x,y))
        painter.text((x+15,y+ch+9),f"SCENE {i+1:02}  /  {len(images):02}",
                     font=font(23),fill=(186,215,231))
    path=folder/"ORIGINAL_SCENE_CONTACT_SHEET.png"
    sheet.save(path,optimize=True)
    return path


def build_cover(ep,accent,folder):
    from PIL import Image,ImageDraw
    portrait=ep["type"]=="short"
    w,h=VIDEO_SIZE["short"] if portrait else (1280,720)
    image=Image.new("RGB",(w,h),(8,21,38))
    d=ImageDraw.Draw(image)
    margin=70
    rounded(d,(margin,margin,w-margin,h-margin),
            (24,43,61),accent,27,5)
    d.rectangle((margin+35,margin+42,margin+48,h-margin-40),fill=accent)
    line_y=h//2-90
    words=ep["cover"].split()
    lines=[]
    if len(words)>3:
        cut=math.ceil(len(words)/2)
        lines=[" ".join(words[:cut])," ".join(words[cut:])]
    else:lines=[ep["cover"]]
    for i,heading in enumerate(lines):
        draw_text(d,heading,margin+85,line_y+i*(145 if portrait else 128),
                  w-2*margin-155,102 if portrait else 88,
                  (242,251,255))
    draw_text(d,"SEE THE REAL FIX  /  EXAMPLES LABELED",
              margin+92,h-margin-112,w-2*margin-170,26,accent,False)
    out=folder/"ORIGINAL_COVER.png"
    image.save(out,optimize=True)
    return out


def render_video(ffmpeg,engine,ep,accent,root):
    folder=root/ep["id"]
    folder.mkdir(mode=0o700)
    wav,scene_seconds,cues,total=synthesize(engine,ep,folder)
    ass,srt=cues_to_files(cues,ep["type"],folder)
    images=[]
    timeline=["ffconcat version 1.0"]
    for i,(scene,seconds) in enumerate(zip(ep["scenes"],scene_seconds)):
        need(2.5<=seconds<=70.0 and math.isfinite(seconds),
             "Scene too short or TTS voice reading missing")
        phases=[]
        for phase in range(3):
            path=folder/f"FRAME_{i:02}_PHASE_{phase}.png"
            frame=render_frame(ep,scene,i,phase,accent)
            need(frame.size==VIDEO_SIZE[ep["type"]],
                 "Original scene wrong aspect ratio")
            frame.save(path,optimize=True)
            phases.append(path)
        images.append(phases[-1])
        # Exact measured narration clock, progressively revealed once only.
        holds=(.20,max(.9,(seconds-.20)*.42),0)
        last=seconds-holds[0]-holds[1]
        need(last>=1.0,"Unable to show final clear result")
        for path,hold in zip(phases,(holds[0],holds[1],last)):
            timeline.extend((f"file '{path.as_posix()}'",
                             f"duration {hold:.6f}"))
    timeline.append(f"file '{images[-1].as_posix()}'")
    concat=folder/"ONE_WAY_ORIGINAL_STORY.ffconcat"
    concat.write_text("\n".join(timeline)+"\n",encoding="utf8")
    output=folder/"REVIEW_ONLY_FINAL.mp4"
    execute([ffmpeg,"-nostdin","-y","-hide_banner","-loglevel","error",
             "-f","concat","-safe","0","-i",str(concat),
             "-i",str(wav),
             "-vf",f"fps={FPS},ass={ass.as_posix()},format=yuv420p",
             "-map","0:v:0","-map","1:a:0","-t",f"{total:.6f}",
             "-r",str(FPS),"-c:v","libx264","-threads","2",
             "-preset","ultrafast","-crf","29",
             "-pix_fmt","yuv420p",
             "-af",B4G5_AUDIO_FILTER,"-ar","48000",
             "-c:a","aac","-b:a","128k","-movflags","+faststart",
             str(output)],timeout=1250)
    execute([ffmpeg,"-nostdin","-hide_banner","-loglevel","error",
             "-xerror","-i",str(output),"-f","null","-"],timeout=750)
    metadata=subprocess.run([ffmpeg,"-hide_banner","-i",str(output)],
                            capture_output=True,text=True,timeout=25)
    dims="%sx%s"%VIDEO_SIZE[ep["type"]]
    need(dims in metadata.stderr
         and "Video: h264" in metadata.stderr
         and "Audio: aac" in metadata.stderr
         and 100000<=output.stat().st_size<=240000000,
         "Real video/audio codec, duration or size incorrect")
    from autopilot.verified_aac_mastering_b4g5 import (
        verify_exact_encoded_master, EncodedMasteringRefused,
    )
    try:
        proof=verify_exact_encoded_master(
            ffmpeg,output,digest(output),total)
    except EncodedMasteringRefused:
        raise FourVideoRefused("Post-encode real AAC LUFS/true-peak failed") from None
    contact=build_contact(ep,images,folder)
    cover=build_cover(ep,accent,folder)
    # Do not upload 70+ temporary full-res source PNGs to user-facing artifacts.
    for image in folder.glob("FRAME_*_PHASE_*.png"):
        image.unlink()
    wav.unlink();ass.unlink();concat.unlink()
    # Exact full rendered video, captions, thumbnail, storyboard and only
    # SHA-pinned, limited fact/rights evidence leave runner for human review.
    info={
        "episode_id":ep["id"],"kind":ep["type"],
        "suggested_ist_slot":ep["time"],"youtube_scheduled":False,
        "title":ep["title"],"editorial_source_url":ep["source"],
        "actual_mp4_sha256":digest(output),
        "physical_h264_aac_full_decode_passed":True,
        "actual_pcm_seconds":total,
        "real_speech_scene_count":len(ep["scenes"]),
        "original_narration_cues_synthesized":len(cues),
        "original_one_way_visual_scene_phases":len(ep["scenes"])*3,
        "original_mp4_aac_post_encode":proof,
        "caption_peak_character_rate":round(max(
            len(c["text"])/(c["end"]-c["start"]) for c in cues),2),
        "rights_and_factual_owner_signoff":False,
        "human_full_watch":False,
        "release_authorized":False,
        "files":[{"name":p.name,"sha256":digest(p),"bytes":p.stat().st_size}
                 for p in (output,srt,contact,cover)],
    }
    (folder/"READ_THIS_FIRST.txt").write_text(
        f"UNAPPROVED ORIGINAL PRACTICE - {ep['id']}\n"
        f"Suggested: {ep['time']} IST on Nov 12, 2026 (NOT SCHEDULED).\n"
        "Review the actual MP4 from beginning to end, full voice and captions.\n"
        "The UI/values are original illustrative graphics, NOT app screenshots.\n"
        "Verify official source claims, rights, dates and owner approval.\n"
        "No upload may happen from this review artifact.\n",encoding="utf8")
    print("B1_NOV12_REAL_ORIGINAL_REVIEW_VIDEO",
          json.dumps({"id":ep["id"],"actual_seconds":total,
                      "encoded_bytes":output.stat().st_size,
                      "full_decode":True,"youtube_uploads":0}),flush=True)
    return info


def main():
    parser=argparse.ArgumentParser(description="GitHub-only four real review videos")
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--voices",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    need(os.environ.get("GITHUB_ACTIONS")=="true"
         and os.environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
         and os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")=="0"
         and os.environ.get("PUBLISH_ENABLED")=="false"
         and args.out.parent==Path("/tmp")
         and args.out.name=="flowminute-nov12-review-four"
         and not args.out.exists()
         and not args.out.is_symlink(),
         "Only disposable GitHub-owned no-publish production")
    from autopilot.cloud_av_probe import verify_pinned_assets
    verify_pinned_assets(args.model,args.voices)
    from kokoro_onnx import Kokoro
    import imageio_ffmpeg
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    need("subtitles" in execute([ffmpeg,"-hide_banner","-filters"],30),
         "No native ASS caption renderer")
    engine=Kokoro(str(args.model),str(args.voices))
    brief,brief_sha=load_brief()
    args.out.mkdir(mode=0o700)
    reports=[]
    for ep,accent in zip(brief["episodes"],PALETTE):
        reports.append(render_video(ffmpeg,engine,ep,accent,args.out))
    need(len(reports)==4
         and [r["real_speech_scene_count"] for r in reports]==[5,5,12,5]
         and len({r["actual_mp4_sha256"] for r in reports})==4
         and all(r["physical_h264_aac_full_decode_passed"] is True
                 and r["release_authorized"] is False
                 and r["youtube_scheduled"] is False for r in reports),
         "Four actual distinct original files or no-release gates missing")
    result={
        "status":STATUS,"date_ist":"2026-11-12",
        "source_brief_sha256":brief_sha,
        "physical_review_mp4_count":4,
        "original_short_count":3,"original_long_count":1,
        "episode_reports":reports,
        "simulated_ui_not_real_product_screen_capture":True,
        "owner_video_and_voice_reviews_completed":0,
        "youtube_uploads":0,"youtube_schedule_writes":0,
        "release_authorized":False,
    }
    (args.out/"FOUR_VIDEO_REVIEW_MANIFEST.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("B1_NOV12_REAL_FOUR_VIDEOS_FOUR_FULL_DECODES_ZERO_YOUTUBE_MUTATIONS")


if __name__=="__main__":
    main()
