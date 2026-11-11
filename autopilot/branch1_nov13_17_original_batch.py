"""Nov13–17 Branch 1: real, original, case-specific educational video bundles.

Produces 2 Shorts and 1 Long for ONE requested future date (five jobs can
run independently); GitHub runner-only, public pinned Kokoro voice, no stock,
no owner OAuth, no approval, no YouTube mutation, no fake app screenshots.
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

from autopilot.branch1_nov12_four_review_videos import (
    VIDEO_SIZE,FPS,B4G5_AUDIO_FILTER,
    draw_text,font,rounded,secs_stamp,split_script,synthesize,
    cues_to_files,execute,digest,
)

ROOT=Path(__file__).resolve().parents[1]
STATUS="B1_NOV13_17_PHYSICAL_THREE_ORIGINALS_OWNER_REVIEW_NO_UPLOAD"
VALID_DATES={f"2026-11-{day:02d}" for day in range(13,18)}
EXPECTED_SOURCE_BY_DATE={
    "2026-11-13":("https://support.microsoft.com/en-us/excel/functions/trim-function",
        "https://support.microsoft.com/en-us/excel/find-and-remove-duplicates",
        "https://support.microsoft.com/en-us/excel/find-and-remove-duplicates"),
    "2026-11-14":("https://support.google.com/chrome/answer/3220216",
        "https://support.google.com/accounts/answer/13533235",
        "https://support.google.com/chrome/answer/3220216"),
    "2026-11-15":("https://support.microsoft.com/en-us/excel/how-to-correct-a-spill-error",
        "https://support.microsoft.com/en-us/excel/functions/xlookup-function",
        "https://support.microsoft.com/en-us/excel/how-to-correct-a-spill-error"),
    "2026-11-16":("https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt",
        "https://help.openai.com/en/articles/8313428-does-chatgpt-tell-the-truth",
        "https://help.openai.com/en/articles/8313428-does-chatgpt-tell-the-truth"),
    "2026-11-17":("https://support.microsoft.com/en-us/excel/import-data-from-a-folder-with-multiple-files-power-query",)*3,
}
TIME_IST=("11:00","20:30","16:00")
ACCENT_BY_DAY={
    "2026-11-13":(85,215,232),
    "2026-11-14":(125,221,168),
    "2026-11-15":(250,190,111),
    "2026-11-16":(188,169,252),
    "2026-11-17":(104,203,240),
}
WHITE=(245,250,253)
BG=(8,20,34)
MUTED=(168,195,214)
INK=(15,54,73)
WARN=(249,137,108)
OK=(106,232,187)
PAPER=(226,243,249)

class OriginalBatchRefused(ValueError):
    """Unsafe source, incorrect video, physical QA, or potential publication."""


def need(ok,reason):
    if not ok:
        raise OriginalBatchRefused(reason)


def read_day(date,repo=ROOT):
    need(date in VALID_DATES,"Only Nov 13–17 owner-requested calendar")
    path=repo/"content/nov13_17_2026"/f"day_{date}.json"
    need(path.is_file() and not path.is_symlink()
         and path.stat().st_size<50000,"Missing original authored daily brief")
    raw=path.read_bytes()
    d=json.loads(raw)
    need(type(d) is dict
         and d.get("schema")=="FLOWMINUTE_B1_SEARCH_LED_FIVE_DAY_V1"
         and d.get("date_ist")==date
         and d.get("channel_id")=="UCCcL9Q_jqVq6LJmnYUSAFZA"
         and d.get("status")=="SOURCE_APPROVED_BY_VENDOR_LINKS_ONLY_OWNER_RELEASE_UNAPPROVED"
         and type(d.get("episodes")) is list
         and len(d["episodes"])==3,
         "Only three exact original episode sources/day; no approval")
    names=set()
    for i,ep in enumerate(d["episodes"]):
        kind="long" if i==2 else "short"
        wc=0
        need(type(ep) is dict
             and ep.get("id")==f"fm_{date.replace('-','')}_"+ep["id"].split(f"fm_{date.replace('-','')}_",1)[-1]
             and re.fullmatch(r"fm_2026111[3-7]_[a-z0-9_]+_(short|long)_en",ep["id"])
             and ep.get("date_ist")==date
             and ep["id"] not in names
             and ep.get("kind")==kind
             and ep.get("time_ist")==TIME_IST[i]
             and ep.get("source")==EXPECTED_SOURCE_BY_DATE[date][i]
             and ep.get("language")=="en"
             and ep.get("voice") in ("af_heart","bf_emma","am_michael")
             and type(ep.get("title")) is str and 18<=len(ep["title"])<=100
             and ep.get("approval")=={
                 "owner_final_watch":False,"rights_cleared":False,
                 "facts_approved":False,"release_signed":False,
                 "youtube_scheduled":False,
             },"Unknown chapter/source/schedule/owner approval")
        names.add(ep["id"])
        scenes=ep.get("scenes")
        need(type(scenes) is list and len(scenes)==(5 if kind=="short" else 12),
             "Missing original complete narrative acts")
        for s in scenes:
            need(type(s) is list and len(s)==4
                 and all(type(x) is str and 1<len(x)<=620
                         and x.strip()==x and "\n" not in x
                         and "{" not in x and "}" not in x for x in s)
                 and len(s[0])<=48 and len(s[1])<=30 and len(s[2])<=30
                 and 35<=len(s[3])<=620,
                 "Scene text or physical art labels unsafe")
            words=len(s[3].split())
            wc+=words
            # Validate it remains exactly vocalizable (not generated filler).
            split_script(s[3],kind)
        need((70<=wc<=112) if kind=="short" else (350<=wc<=650),
             "Original scene count/word budget not credible")
    return d,sha256(raw).hexdigest()


def txt(draw,label,x,y,width,size,color=WHITE,bold=True):
    draw_text(draw,label,x,y,width,size,color,bold)


def panel(draw,rect,fill,stroke,r=20,w=3):
    rounded(draw,rect,fill,stroke,r,w)


def _palette(kind,index):
    pairs=((17,57,76),(24,65,82),(20,55,76),(27,70,82))
    return pairs[index%4]


def _draw_sheet(draw,rect,a,b,phase,accent,index):
    x0,y0,x1,y1=rect
    panel(draw,rect,PAPER,(84,146,175),24)
    panel(draw,(x0+25,y0+25,x1-25,y0+105),(27,76,95),(27,76,95),11)
    txt(draw,"ILLUSTRATIVE DATA / ORIGINAL",x0+55,y0+47,x1-x0-110,30)
    txt(draw,"BEFORE / SOURCE",x0+46,y0+146,x1-x0-96,32,INK)
    panel(draw,(x0+43,y0+208,x1-43,y0+368),
          (204,244,235) if phase==1 else WHITE,
          accent if phase==1 else (113,171,180),15)
    txt(draw,a,x0+65,y0+264,x1-x0-130,80 if x1-x0>900 else 55,INK)
    txt(draw,"AFTER / RESULT",x0+46,y0+431,x1-x0-96,32,INK)
    panel(draw,(x0+43,y0+501,x1-43,y0+670),
          (253,222,209) if phase==2 else WHITE,
          WARN if phase==2 else (118,171,184),15)
    txt(draw,b,x0+65,y0+550,x1-x0-130,82 if x1-x0>900 else 55,
        (125,49,41))
    txt(draw,"CHECK THE REAL VALUE, NOT JUST THE FORMATTING",
        x0+46,y1-92,x1-x0-92,27,INK,False)


def _draw_permissions(draw,rect,a,b,phase,accent,index):
    x0,y0,x1,y1=rect
    panel(draw,rect,(18,42,60),(80,130,151),24)
    panel(draw,(x0+29,y0+31,x1-29,y0+116),
          (44,91,110),(44,91,110),12)
    txt(draw,"FICTIONAL SETTINGS DEMO",x0+63,y0+56,x1-x0-126,30)
    txt(draw,"CURRENT / ALLOWED",x0+53,y0+178,x1-x0-106,32,MUTED)
    panel(draw,(x0+53,y0+239,x1-53,y0+421),
          (43,66,84) if phase==0 else (42,81,87),
          OK if phase==1 else (97,136,155),20)
    txt(draw,a,x0+85,y0+305,x1-x0-170,75,WHITE)
    txt(draw,"REVIEW / ACTION",x0+53,y0+479,x1-x0-106,32,MUTED)
    panel(draw,(x0+53,y0+542,x1-53,y0+731),
          (59,58,75) if phase!=2 else (65,82,68),
          accent if phase==2 else (104,119,143),20)
    txt(draw,b,x0+85,y0+610,x1-x0-170,74,WHITE)
    txt(draw,"ONLY ALLOW THE PERMISSIONS YOU NEED",
        x0+55,y1-77,x1-x0-110,30,accent)


def _draw_ai(draw,rect,a,b,phase,accent,index):
    x0,y0,x1,y1=rect
    panel(draw,rect,(18,43,66),(105,120,173),24)
    txt(draw,"FICTIONAL ASSISTANT / VERIFIED SOURCE",
        x0+38,y0+45,x1-x0-76,30,accent)
    panel(draw,(x0+46,y0+158,x1-110,y0+391),
          (38,66,92),accent if phase==1 else (89,111,141),22)
    txt(draw,"AI ANSWER",x0+73,y0+197,x1-x0-152,29,MUTED)
    txt(draw,a,x0+73,y0+279,x1-x0-200,79,WHITE)
    panel(draw,(x0+108,y0+473,x1-46,y0+735),
          (39,70,75) if phase==2 else (34,58,75),
          OK if phase==2 else (89,122,143),22)
    txt(draw,"SOURCE / REAL CHECK",x0+134,y0+511,x1-x0-200,29,MUTED)
    txt(draw,b,x0+134,y0+594,x1-x0-212,74,WHITE)
    txt(draw,"VERIFY BEFORE YOU SHARE",
        x0+57,y1-71,x1-x0-114,31,accent)


def _draw_folder(draw,rect,a,b,phase,accent,index):
    x0,y0,x1,y1=rect
    panel(draw,rect,(19,44,62),(85,145,179),24)
    txt(draw,"ORIGINAL MONTHLY CSV FOLDER DEMO",
        x0+40,y0+39,x1-x0-80,30,MUTED)
    panel(draw,(x0+42,y0+148,x1-42,y0+399),
          (34,69,86),accent if phase==1 else (102,139,154),20)
    txt(draw,"INPUT FILES / HEADERS",x0+80,y0+188,x1-x0-160,31,accent)
    txt(draw,a,x0+80,y0+291,x1-x0-160,83,WHITE)
    panel(draw,(x0+42,y0+474,x1-42,y0+736),
          (51,77,66) if phase==2 else (33,60,78),
          OK if phase==2 else (99,137,154),20)
    txt(draw,"COMBINED / VERIFIED",x0+80,y0+516,x1-x0-160,31,OK)
    txt(draw,b,x0+80,y0+623,x1-x0-160,81,WHITE)
    txt(draw,"SAME COLUMNS + CORRECT FILES",
        x0+54,y1-76,x1-x0-108,30,accent)


def _style(ep):
    date=ep["date_ist"]
    return ("browser" if date=="2026-11-14" else
            "ai" if date=="2026-11-16" else
            "folder" if date=="2026-11-17" else "sheet")


def frame(ep,scene,index,phase,accent):
    """Real full-resolution original frame; 3 finite one-way reveal states.

    Both before and after content are present from phase0 so viewers never
    wait 2 seconds for the actual problem. Captions remain in a fixed safe box.
    """
    from PIL import Image,ImageDraw
    kind=ep["kind"]
    w,h=VIDEO_SIZE[kind]
    need(type(index) is int and 0<=index<len(ep["scenes"])
         and type(phase) is int and phase in (0,1,2)
         and type(accent) is tuple and len(accent)==3,
         "Wrong original scene or looping phase")
    im=Image.new("RGB",(w,h),BG)
    d=ImageDraw.Draw(im)
    for y in range(0,h,27):
        factor=y/h
        d.rectangle((0,y,w,min(h,y+27)),
                    fill=(7+int(factor*7),18+int(factor*11),32+int(factor*16)))
    margin=78 if kind=="short" else 110
    d.rectangle((0,0,15,h),fill=accent)
    txt(d,"FLOWMINUTE LAB  /  PRACTICAL DATA + PRIVACY",
        margin,57,w-2*margin,27,MUTED,False)
    d.line((margin,128,w-margin,128),fill=(61,96,116),width=3)
    heading,a,b,_=scene
    txt(d,heading,margin,170,w-2*margin,73 if kind=="short" else 83)
    txt(d,"ILLUSTRATIVE ORIGINAL CASE  /  CHECK OFFICIAL SOURCE",
        margin,290,w-2*margin,24,MUTED,False)
    if kind=="short":
        area=(margin,392,w-margin,1418)
        inner=(margin+30,440,w-margin-30,1320)
        caption=(margin,1515,w-margin,1750)
        bars=1457
        footer=h-80
    else:
        area=(margin,356,w-margin,802)
        inner=(margin+40,363,w-margin-40,795)
        caption=(margin,835,w-margin,1021)
        bars=818
        footer=h-40
    # The long video must not try to draw a portrait-height widget in a
    # landscape view; separate hand-placed case evidence occupies 2 columns.
    if kind=="long":
        x0,y0,x1,y1=area
        panel(d,area,(15,41,59),(76,116,141),26)
        m=(x0+x1)//2
        panel(d,(x0+22,y0+35,m-16,y1-35),
              (28,61,80),OK if phase==1 else (78,118,139),22)
        txt(d,"SOURCE / FIRST",x0+60,y0+69,m-x0-114,31,OK)
        txt(d,a,x0+60,y0+180,m-x0-115,83,WHITE)
        panel(d,(m+16,y0+35,x1-22,y1-35),
              (49,52,69) if phase==0 else (65,56,64),
              WARN if phase==2 else (97,115,131),22)
        txt(d,"RESULT / NEXT",m+57,y0+69,x1-m-115,31,WARN)
        txt(d,b,m+57,y0+180,x1-m-115,83,WHITE)
        txt(d,"CASE %02d OF %02d"%(index+1,len(ep["scenes"])),
            x0+60,y1-73,x1-x0-120,27,MUTED,False)
    else:
        mode=_style(ep)
        fn={"sheet":_draw_sheet,"browser":_draw_permissions,
            "ai":_draw_ai,"folder":_draw_folder}[mode]
        fn(d,inner,a,b,phase,accent,index)
    base_width=(w-2*margin-(len(ep["scenes"])-1)*8)//len(ep["scenes"])
    for j in range(len(ep["scenes"])):
        x=margin+j*(base_width+8)
        panel(d,(x,bars,x+base_width,bars+11),
              accent if j<=index else (66,91,112),
              accent if j<=index else (66,91,112),4,1)
    panel(d,caption,(14,41,56),(60,102,123),18)
    d.rectangle((caption[0]+30,caption[1]+26,
                 caption[0]+144,caption[1]+33),fill=accent)
    txt(d,"ORIGINAL DEMO. NO ACTUAL CUSTOMER DATA.",
        margin,footer,w-2*margin,23,MUTED,False)
    return im


def cover(ep,accent,folder):
    from PIL import Image,ImageDraw
    kind=ep["kind"]
    w,h=(1080,1920) if kind=="short" else (1280,720)
    image=Image.new("RGB",(w,h),(7,19,33))
    d=ImageDraw.Draw(image)
    for y in range(0,h,18):
        d.rectangle((0,y,w,min(h,y+18)),fill=(
            8+int(9*y/h),19+int(9*y/h),34+int(14*y/h)))
    d.rectangle((0,0,14,h),fill=accent)
    margin=75 if kind=="short" else 69
    txt(d,"FLOWMINUTE / REAL WORLD FIX",margin,62,w-2*margin,31,MUTED)
    txt(d,ep["scenes"][0][0],margin,178,w-2*margin,
        88 if kind=="short" else 84,WHITE)
    a,b=ep["scenes"][0][1:3]
    top=595 if kind=="short" else 347
    height=255 if kind=="short" else 150
    gap=61 if kind=="short" else 23
    for i,val in enumerate((a,b)):
        y=top+i*(height+gap) if kind=="short" else top
        x=margin if kind=="short" or i==0 else 674
        boxw=w-2*margin if kind=="short" else 540
        panel(d,(x,y,x+boxw,y+height),
              (27,65,74) if i==0 else (67,43,53),
              OK if i==0 else WARN,22,4)
        txt(d,"SOURCE" if i==0 else "RESULT / CHECK",
            x+25,y+30,boxw-50,31,OK if i==0 else WARN)
        txt(d,val,x+27,y+102 if kind=="short" else y+69,
            boxw-54,74 if kind=="short" else 56,WHITE)
    if kind=="short":
        txt(d,"VERIFY / FIX / SAVE",margin,1624,w-2*margin,47,accent)
        txt(d,"FICTIONAL EDUCATIONAL ILLUSTRATION",
            margin,1800,w-2*margin,22,MUTED,False)
    else:
        txt(d,"FICTIONAL CASE — NOT A LIVE SOFTWARE SCREEN",
            margin,626,w-2*margin,26,MUTED,False)
    dest=folder/"ORIGINAL_COVER.png"
    image.save(dest,optimize=True)
    return dest


def render(ffmpeg,engine,ep,accent,root):
    from PIL import Image,ImageDraw
    folder=root/ep["id"]
    folder.mkdir(mode=0o700)
    proxy={**ep,"type":ep["kind"]}
    wav,durations,cues,total=synthesize(engine,proxy,folder)
    ass,srt=cues_to_files(cues,ep["kind"],folder)
    previews=[]
    timing=["ffconcat version 1.0"]
    for index,(scene,duration) in enumerate(zip(ep["scenes"],durations)):
        need(2.5<=duration<=70.0 and math.isfinite(duration),
             "Narration scene outside physical duration bound")
        frames=[]
        for phase in range(3):
            path=folder/f"CASE_{index:02d}_PHASE_{phase}.png"
            artwork=frame(ep,scene,index,phase,accent)
            artwork.save(path,optimize=True)
            frames.append(path)
        previews.append(frames[-1])
        hold0=.15
        hold1=max(.85,(duration-hold0)*.36)
        hold2=duration-hold0-hold1
        need(hold2>=1,"Unclear time to read actual result")
        for path,hold in zip(frames,(hold0,hold1,hold2)):
            timing.append(f"file '{path.as_posix()}'")
            timing.append(f"duration {hold:.6f}")
    timing.append(f"file '{previews[-1].as_posix()}'")
    concat=folder/"ORIGINAL_PROGRESSIVE.ffconcat"
    concat.write_text("\n".join(timing)+"\n","utf8")
    mp4=folder/"REVIEW_ONLY_FINAL.mp4"
    execute([ffmpeg,"-nostdin","-hide_banner","-y","-loglevel","error",
             "-f","concat","-safe","0","-i",str(concat),"-i",str(wav),
             "-vf",f"fps={FPS},ass={ass.as_posix()},format=yuv420p",
             "-map","0:v:0","-map","1:a:0","-t",f"{total:.6f}",
             "-r",str(FPS),"-c:v","libx264","-threads","2",
             "-preset","ultrafast","-crf","28","-pix_fmt","yuv420p",
             "-af",B4G5_AUDIO_FILTER,"-ar","48000","-c:a","aac",
             "-b:a","128k","-movflags","+faststart",str(mp4)],timeout=1500)
    execute([ffmpeg,"-nostdin","-hide_banner","-loglevel","error","-xerror",
             "-i",str(mp4),"-f","null","-"],timeout=760)
    from autopilot.verified_aac_mastering_b4g5 import (
        verify_exact_encoded_master,EncodedMasteringRefused,
    )
    try:
        proof=verify_exact_encoded_master(ffmpeg,mp4,digest(mp4),total)
    except EncodedMasteringRefused:
        raise OriginalBatchRefused("Exact final AAC mastered media refused") from None
    width,height=(360,640) if ep["kind"]=="short" else (480,270)
    columns=3 if ep["kind"]=="short" else 4
    rows=math.ceil(len(previews)/columns)
    sheet=Image.new("RGB",(columns*width,rows*(height+45)),BG)
    artist=ImageDraw.Draw(sheet)
    for i,path in enumerate(previews):
        xpos=(i%columns)*width
        ypos=(i//columns)*(height+45)
        with Image.open(path) as still:
            sheet.paste(still.resize((width,height),Image.Resampling.LANCZOS),
                        (xpos,ypos))
        artist.text((xpos+12,ypos+height+11),
                    f"ORIGINAL CASE {i+1:02d}",font=font(22),
                    fill=MUTED)
    contact=folder/"ORIGINAL_SCENE_CONTACT_SHEET.png"
    sheet.save(contact,optimize=True)
    thumb=cover(ep,accent,folder)
    for path in folder.glob("CASE_*_PHASE_*.png"):
        path.unlink()
    wav.unlink()
    ass.unlink()
    concat.unlink()
    need(mp4.stat().st_size>100_000
         and proof["integrated_lufs_and_true_peak_within_internal_band"] is True,
         "Original render physical media or postencode QA not verified")
    report={
        "episode_id":ep["id"],"date_ist":ep["date_ist"],
        "kind":ep["kind"],"proposed_time_ist":ep["time_ist"],
        "title":ep["title"],"primary_source":ep["source"],
        "actual_pcm_seconds":total,"actual_mp4_sha256":digest(mp4),
        "original_scenes":len(ep["scenes"]),
        "real_derived_caption_cues":len(cues),
        "one_way_original_visual_states":3*len(ep["scenes"]),
        "physical_h264_aac_full_decode_passed":True,
        "post_encoded_mastering":proof,
        "owner_final_voice_captions_facts_rights_review":False,
        "release_signed":False,"youtube_uploaded":False,
        "youtube_scheduled":False,
        "files":[{
            "name":p.name,"sha256":digest(p),"bytes":p.stat().st_size
        } for p in (mp4,srt,thumb,contact)],
    }
    (folder/"README_OWNER_REVIEW_NOT_UPLOADED.txt").write_text(
        f"Unapproved {ep['kind']} original visual education / {ep['date_ist']} / "
        f"{ep['time_ist']} Asia/Kolkata\n"
        "Full-watch the MP4; verify narrated facts, captions, original sound and "
        "illustrations, rights and owner approval. No YouTube release.\n","utf8")
    print("B1_NOV13_17_REAL_PHYSICAL_VIDEO",json.dumps({
        "id":ep["id"],"seconds":total,"decode":True,
        "schedule_writes":0,"bytes":mp4.stat().st_size
    }),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description="3 original videos/day, no publish")
    parser.add_argument("--date",required=True,choices=sorted(VALID_DATES))
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--voices",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    need(os.environ.get("GITHUB_ACTIONS")=="true"
         and os.environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
         and os.environ.get("PUBLISH_ENABLED")=="false"
         and os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")=="0"
         and args.out.parent==Path("/tmp")
         and args.out.name==f"flowminute-b1-{args.date}-three"
         and not args.out.exists() and not args.out.is_symlink(),
         "Only disposable GitHub no-write video preparation permitted")
    from autopilot.cloud_av_probe import verify_pinned_assets
    verify_pinned_assets(args.model,args.voices)
    import imageio_ffmpeg
    from kokoro_onnx import Kokoro
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    need("ass" in execute([ffmpeg,"-hide_banner","-filters"],30),
         "Real native ASS render required")
    engine=Kokoro(str(args.model),str(args.voices))
    day,digest_brief=read_day(args.date)
    args.out.mkdir(mode=0o700)
    reports=[render(ffmpeg,engine,ep,ACCENT_BY_DAY[args.date],args.out)
             for ep in day["episodes"]]
    need(len(reports)==3 and len({x["actual_mp4_sha256"] for x in reports})==3
         and all(x["physical_h264_aac_full_decode_passed"] is True
                 and x["release_signed"] is False
                 and x["youtube_uploaded"] is False
                 and x["youtube_scheduled"] is False for x in reports),
         "Not exactly 3 physical owner-review-only videos")
    (args.out/"DAY_ORIGINAL_THREE_REVIEW_MANIFEST.json").write_text(
        json.dumps({
            "status":STATUS,"date_ist":args.date,
            "source_brief_sha256":digest_brief,
            "actual_h264_aac_verified_mp4_count":3,
            "actual_original_shorts":2,"actual_original_longs":1,
            "release_owner_authorizations":0,
            "youtube_uploads":0,"youtube_scheduled_writes":0,
            "episodes":reports,
        },indent=2,sort_keys=True)+"\n","utf8")
    print("B1_NOV13_17_THREE_REAL_ORIGINAL_MP4S_NO_YOUTUBE_UPLOADS")


if __name__=="__main__":
    main()
