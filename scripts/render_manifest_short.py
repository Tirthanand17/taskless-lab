from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1920
BG="#09111f"; CARD="#121e32"; CARD2="#172943"; TEXT="#f7f9fc"
MUTED="#a9bbcf"; CYAN="#5ee7ff"; GREEN="#71efa8"; RED="#ff8181"; YELLOW="#ffd966"
FONT_B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def F(size,bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R,size)

def wrap(d,text,font,width):
    out=[]; line=""
    for word in text.split():
        test=(line+" "+word).strip()
        if d.textbbox((0,0),test,font=font)[2] <= width:
            line=test
        else:
            if line: out.append(line)
            line=word
    if line: out.append(line)
    return out

def pill(d,xy,label,fill,fg=TEXT):
    x1,y1,x2,y2=xy
    d.rounded_rectangle(xy,radius=24,fill=fill)
    d.text(((x1+x2)//2,(y1+y2)//2),label,anchor="mm",font=F(32,True),fill=fg)

def draw_scene(scene,path):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    pill(d,(60,60,430,132),scene.get("kicker","FLOWMINUTE"),CARD2,CYAN)
    y=185
    for ln in wrap(d,scene["title"],F(76,True),W-120):
        d.text((60,y),ln,font=F(76,True),fill=TEXT); y+=90
    y+=28

    table=scene.get("table")
    if table:
        headers=table["headers"]; rows=table["rows"]; n=max(1,len(headers))
        total=W-140; col=total//n; x=70; rh=82
        for i,h in enumerate(headers):
            d.rounded_rectangle((x+i*col,y,x+(i+1)*col-10,y+rh),radius=16,fill="#1c3656")
            d.text((x+i*col+18,y+23),str(h),font=F(29,True),fill=TEXT)
        y+=rh+12
        for row in rows:
            for i,val in enumerate(row):
                fill=CARD
                d.rounded_rectangle((x+i*col,y,x+(i+1)*col-10,y+rh),radius=16,fill=fill)
                d.text((x+i*col+18,y+23),str(val),font=F(27),fill=TEXT)
            y+=rh+12
        y+=25

    for item in scene.get("body",[]):
        if y>H-250: break
        d.rounded_rectangle((70,y,W-70,y+96),radius=22,fill=CARD)
        d.text((98,y+28),"✓",font=F(30,True),fill=GREEN)
        lines=wrap(d,str(item),F(30,True),W-230)
        yy=y+25
        for ln in lines[:2]:
            d.text((150,yy),ln,font=F(30,True),fill=TEXT); yy+=38
        y+=116

    note=scene.get("note")
    if note and y<H-270:
        d.rounded_rectangle((70,y,W-70,y+170),radius=26,fill="#2b2415")
        d.text((100,y+32),scene.get("note_label","KEY RULE"),font=F(29,True),fill=YELLOW)
        yy=y+82
        for ln in wrap(d,note,F(30,True),W-190)[:2]:
            d.text((100,yy),ln,font=F(30,True),fill=TEXT); yy+=40

    d.line((60,H-105,W-60,H-105),fill="#29425f",width=3)
    d.text((60,H-78),"FLOWMINUTE LAB  •  PRACTICAL AUTOMATION",font=F(25,True),fill=MUTED)
    im.save(path)

def run(cmd):
    subprocess.run(cmd,check=True)

def duration(path):
    p=subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)],
        capture_output=True,text=True,check=True
    )
    return float(p.stdout.strip())

async def speak(text,voice,rate,path):
    await edge_tts.Communicate(text,voice=voice,rate=rate).save(str(path))

def ts(seconds):
    ms=round(seconds*1000)
    h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def captions_for_scene(text,start,end):
    parts=[p.strip() for p in re.split(r"(?<=[.!?])\s+",text) if p.strip()]
    if not parts: return []
    weights=[max(1,len(p.split())) for p in parts]; total=sum(weights)
    cur=start; out=[]
    for i,(p,w) in enumerate(zip(parts,weights)):
        stop=end if i==len(parts)-1 else cur+(end-start)*(w/total)
        out.append((cur,stop,p)); cur=stop
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    args=ap.parse_args()
    manifest=args.manifest if args.manifest.is_absolute() else ROOT/args.manifest
    data=json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("renderer")!="manifest_v2":
        raise SystemExit("manifest renderer must be manifest_v2")

    out=ROOT/"assets"/data["id"]; out.mkdir(parents=True,exist_ok=True)
    work=out/"_render"; work.mkdir(exist_ok=True)
    voice=data.get("voice","en-US-AndrewNeural")
    rate=data.get("voice_rate","+4%")
    fps=30

    scene_mp4s=[]; caption_rows=[]; cursor=0.0
    for i,scene in enumerate(data["scenes"],1):
        image=out/f"scene_{i:02}.png"; audio=work/f"scene_{i:02}.mp3"; video=work/f"scene_{i:02}.mp4"
        draw_scene(scene,image)
        asyncio.run(speak(scene["narration"],voice,rate,audio))
        dur=duration(audio)+0.25
        caption_rows += captions_for_scene(scene["narration"],cursor,cursor+dur)
        cursor += dur
        frames=max(1,int(dur*fps))
        vf=(
            "scale=1120:1990,"
            f"zoompan=z='min(zoom+0.00038,1.032)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1080x1920:fps={fps},format=yuv420p"
        )
        run(["ffmpeg","-y","-loglevel","error","-loop","1","-i",str(image),"-i",str(audio),
             "-vf",vf,"-r",str(fps),"-c:v","libx264","-preset","veryfast","-crf","20",
             "-c:a","aac","-b:a","160k","-shortest",str(video)])
        scene_mp4s.append(video)

    concat=work/"concat.txt"
    concat.write_text("\n".join([f"file '{p.as_posix()}'" for p in scene_mp4s]),encoding="utf-8")
    base=work/"base.mp4"
    run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(base)])

    srt=out/"captions.srt"
    chunks=[]
    for i,(a,b,text) in enumerate(caption_rows,1):
        chunks += [str(i),f"{ts(a)} --> {ts(b)}",text,""]
    srt.write_text("\n".join(chunks),encoding="utf-8")

    final=out/f"{data['id']}_final.mp4"
    style="FontName=DejaVu Sans,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BackColour=&H90000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=145"
    run(["ffmpeg","-y","-loglevel","error","-i",str(base),
         "-vf",f"subtitles='{srt.as_posix()}':force_style='{style}'",
         "-c:v","libx264","-preset","veryfast","-crf","19","-c:a","copy",str(final)])

    (out/"render_receipt.json").write_text(json.dumps({
        "episode_id":data["id"],"duration_seconds":round(duration(final),2),
        "voice":voice,"voice_rate":rate,"caption_count":len(caption_rows),
        "final_video":str(final.relative_to(ROOT)),
        "cover":str((out/"scene_01.png").relative_to(ROOT))
    },indent=2)+"\n",encoding="utf-8")

    print(final)

if __name__=="__main__":
    main()
