"""15 source-locked, mobile-readable, compact thumbnail alternatives (NO YOUTUBE).

Does not edit original MP4, caption, existing ORIGINAL_COVER.png,
published videos, release hashes or source fiction/owner approval.
All art is drawn using original Pillow primitives, no stock or app screenshot.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from autopilot.branch1_nov13_17_original_batch import read_day

ROOT=Path(__file__).resolve().parents[1]
ACC={13:(68,231,190),14:(66,207,249),15:(255,194,86),
     16:(183,149,255),17:(80,225,191)}
# (two-line hook, app category, original case value, safe result, diagram)
# Values are educational mock data, not images captured from real accounts.
COPY={
"trim_nbsp_part1_short_en":(("TRIM MISSED","THE SPACE?"),"EXCEL","TRIM(A2)","STILL A SPACE","sheet"),
"count_vs_counta_short_en":(("COUNT  ≠","COUNTA"),"EXCEL","COUNT = 2","COUNTA = 4","sheet"),
"invisible_excel_characters_long_en":(("SAME NAME.","NO MATCH."),"EXCEL","ANNA","HIDDEN CHARACTER","sheet"),
"chrome_notifications_short_en":(("STOP THE","SITE PINGS"),"CHROME","ALLOW","BLOCK","browser"),
"thirdparty_access_short_en":(("OLD APP","STILL LINKED?"),"GOOGLE","OLD APP","REVIEW ACCESS","browser"),
"browser_permissions_long_en":(("5 ACCESS","CHECKS"),"CHROME","SITE SETTINGS","CHECK BEFORE ALLOW","browser"),
"spill_error_short_en":(("#SPILL!","WHAT BLOCKED?"),"EXCEL","#SPILL!","CHECK THE RANGE","sheet"),
"xlookup_first_short_en":(("FIRST MATCH","NOT LATEST"),"EXCEL","FIRST MATCH","CHECK ROW ORDER","sheet"),
"formula_errors_long_en":(("EXCEL ERRORS:","3 REAL CHECKS"),"EXCEL","#SPILL!","CHECK SOURCE","sheet"),
"temporary_chat_short_en":(("TEMP CHAT","NOT INSTANTLY GONE"),"CHATGPT","TEMP CHAT","UP TO 30 DAYS","chat"),
"temporary_chat_save_short_en":(("SAVE CHANGES","THE RULES"),"CHATGPT","TEMP CHAT","REGULAR CHAT","chat"),
"temporary_chat_privacy_long_en":(("TEMP VS","REGULAR"),"CHATGPT","SIX PRIVACY POINTS","CHECK YOUR SETTINGS","chat"),
"filter_view_short_en":(("FILTER VIEW","NOT DELETE"),"SHEETS","MY VIEW","NOT YOURS","sheet"),
"protected_range_short_en":(("PROTECTED","≠ PRIVATE"),"SHEETS","EDIT LOCK","NOT DATA PRIVACY","sheet"),
"sheets_collaboration_long_en":(("TEAM SHEETS","5 MISTAKES"),"SHEETS","SHARED FILTER","USE FILTER VIEW","sheet"),
}
TYPE_SIZE={"short":(720,1280),"long":(960,540)}
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MAX_BYTES=120_000

class ThumbnailRefused(ValueError):
    pass

def need(ok,why):
    if not ok:
        raise ThumbnailRefused(why)

def ft(size,bold=True):
    return ImageFont.truetype(FONT if bold else REG,size)

def fit(draw,pos,t,max_width,size,fill):
    need(type(t) is str and 1<=len(t)<=45 and "\n" not in t,
         "Unreviewed banner text")
    while size>13 and draw.textbbox((0,0),t,font=ft(size))[2]>max_width:
        size-=2
    need(size>=14,"Unreadably small hook")
    draw.text(pos,t,font=ft(size),fill=fill)

def rounded(draw,box,fill,r=25,outline=None,width=2):
    draw.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)

def diagram(im,category,x,y,w,h,accent):
    d=ImageDraw.Draw(im)
    rounded(d,(x,y,x+w,y+h),(25,57,78),31,(66,119,144),3)
    rounded(d,(x+15,y+15,x+w-15,y+73),(42,82,103),15)
    if category=="sheet":
        for i in range(3):
            for j in range(3):
                xx=x+32+i*(w-64)//3
                yy=y+115+j*86
                bw=(w-84)//3
                color=(184,242,218) if (i,j)==(1,1) else (63,112,129)
                rounded(d,(xx,yy,xx+bw,yy+72),color,9)
                if (i,j)==(1,1):
                    fit(d,(xx+7,yy+14),"✓",bw-14,38,(18,83,71))
    elif category=="browser":
        for i,field in enumerate(("NOTIFY","LOCATION","CAMERA")):
            yy=y+109+i*88
            fit(d,(x+27,yy+12),field,w*.56,31,(225,244,247))
            rounded(d,(x+w-128,yy+10,x+w-28,yy+57),
                    accent if i==0 else (72,104,120),24)
            ex=x+w-(83 if i==0 else 121)
            d.ellipse((ex,yy+15,ex+38,yy+53),fill=(246,251,253))
    else:
        for i in range(3):
            xx=x+(28 if i%2==0 else 92)
            yy=y+104+i*107
            rounded(d,(xx,yy,x+w-(40 if i%2==0 else 25),yy+87),
                    accent if i==1 else (70,113,138),20)
            for offset,length in ((24,63),(44,130)):
                rounded(d,(xx+17,yy+offset,xx+17+length,yy+offset+11),
                        (26,67,88) if i==1 else (198,226,233),5)

def render(ep):
    need(ep.get("date_ist") in {f"2026-11-{n:02d}" for n in range(13,18)}
         and ep.get("kind") in TYPE_SIZE
         and ep.get("approval",{}).get("youtube_scheduled") is False
         and ep.get("approval",{}).get("owner_final_watch") is False,
         "Untrusted episode or fabricated owner status")
    date=ep["date_ist"]
    prefix=f"fm_{date.replace('-','')}_"
    need(ep.get("id","").startswith(prefix) and ep["id"].endswith("_en"),
         "Wrong original episode identity")
    key=ep["id"][len(prefix):]
    need(key in COPY and ep["kind"]==("long" if "_long_en" in key else "short"),
         "Unrecognized thumbnail script/format")
    lines,app,before,after,style=COPY[key]
    W,H=TYPE_SIZE[ep["kind"]]
    acc=ACC[int(date[-2:])]
    im=Image.new("RGB",(W,H),(8,22,40))
    d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H
        d.line((0,y,W,y),fill=(6+int(t*9),19+int(t*14),36+int(t*20)))
    glow=Image.new("RGBA",(W,H),(0,0,0,0))
    ImageDraw.Draw(glow).ellipse((int(W*.35),int(H*.08),
                                 int(W*1.45),int(H*.78)),fill=(*acc,42))
    glow=glow.filter(ImageFilter.GaussianBlur(int(W*.15)))
    im=Image.alpha_composite(im.convert("RGBA"),glow).convert("RGB")
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,12,H),fill=acc)
    fit(d,(44,39) if ep["kind"]=="short" else (38,24),
        "FLOWMINUTE LAB  /  "+app,W*.9,
        23 if ep["kind"]=="short" else 19,(195,224,237))
    if ep["kind"]=="short":
        for i,line in enumerate(lines):
            fit(d,(46,147+i*112),line,624,79,(255,255,255) if i==0 else acc)
        rounded(d,(46,390,674,408),acc,7)
        diagram(im,style,67,454,586,367,acc)
        d=ImageDraw.Draw(im)
        rounded(d,(45,861,675,1025),(232,250,252),26)
        fit(d,(68,884),"CHECK THE REAL RESULT",570,22,(49,101,118))
        fit(d,(68,923),after,578,54,(11,44,65))
        rounded(d,(47,1061,673,1147),(22,78,80),19,acc,2)
        fit(d,(69,1086),before,579,43,(223,255,249))
        fit(d,(47,1192),"ORIGINAL EXPLAINER • NO LIVE ACCOUNT",
            629,14,(151,184,200))
    else:
        for i,line in enumerate(lines):
            fit(d,(52,155+i*108),line,525,65,
                (247,252,255) if i==0 else acc)
        rounded(d,(50,408,520,463),(32,77,87),16,acc,2)
        fit(d,(70,418),after,432,26,(246,255,252))
        diagram(im,style,572,98,348,365,acc)
        fit(d,(48,494),"ORIGINAL DEMO • SOURCE-BASED",445,17,(180,210,225))
    return im

def generate(out:Path,dates:list[str],repo:Path=ROOT):
    need(not out.exists() and not out.is_symlink(),"Never overwrite reviewed thumbnails")
    need(repo.is_dir() and len(dates)==len(set(dates))
         and set(dates).issubset({f"2026-11-{n:02d}" for n in range(13,18)}),
         "Invalid source repo/date set")
    source=[]
    for date in dates:
        data,source_sha=read_day(date,repo)
        for ep in data["episodes"]:
            source.append((ep,source_sha))
    need(len(source)==3*len(dates) and len({e["id"] for e,h in source})==len(source),
         "Missing one of fifteen original source-locked episodes")
    out.mkdir(parents=True,mode=0o700)
    results=[]
    for ep,source_sha in source:
        image=render(ep)
        binary=BytesIO()
        image.save(binary,format="JPEG",quality=83,optimize=True,
                   progressive=True,subsampling=1)
        raw=binary.getvalue()
        need(raw[:3]==b"\xff\xd8\xff"
             and 15_000<=len(raw)<=MAX_BYTES
             and image.size==TYPE_SIZE[ep["kind"]],
             "Thumbnail incorrect size, aspect or mobile bytes")
        filename=ep["id"]+"_COMPACT_PREVIEW_ONLY.jpg"
        path=out/filename
        path.write_bytes(raw)
        need(sha256(path.read_bytes()).hexdigest()==sha256(raw).hexdigest(),
             "Thumbnail integrity drift")
        results.append({
            "episode_id":ep["id"],"kind":ep["kind"],
            "date_ist":ep["date_ist"],"time_ist":ep["time_ist"],
            "title":ep["title"],"source_brief_sha256":source_sha,
            "original_demo_only":True,"owner_thumbnail_approved":False,
            "youtube_thumbnail_updated":False,"youtube_scheduled_by_job":False,
            "jpg_sha256":sha256(raw).hexdigest(),"jpg_bytes":len(raw),
            "size_px":list(image.size),"file":filename,
        })
    (out/"MANIFEST_COMPACT_REVIEW_NOT_YOUTUBE.json").write_text(json.dumps({
        "status":"FIFTEEN_MOBILE_FIRST_THUMBNAILS_REVIEW_ONLY_NO_YOUTUBE",
        "count":len(results),"human_approval_count":0,
        "youtube_thumbnail_updates":0,"youtube_schedule_changes":0,
        "items":results},indent=2,ensure_ascii=False)+"\n","utf8")
    return results

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--date",choices=sorted({f"2026-11-{n:02d}" for n in range(13,18)}))
    args=parser.parse_args()
    need(__import__("os").environ.get("PUBLISH_ENABLED","false").lower()!="true"
         and __import__("os").environ.get("FLOWMINUTE_ENABLE_PUBLISH","0")=="0",
         "Thumbnail production must not include publishing authority")
    dates=[args.date] if args.date else sorted({f"2026-11-{n:02d}" for n in range(13,18)})
    results=generate(args.out,dates)
    print(json.dumps({"status":"COMPACT_REVIEW_ONLY_NO_UPLOAD",
                      "thumbnail_count":len(results),
                      "total_bytes":sum(x["jpg_bytes"] for x in results),
                      "scheduled_by_job":0},sort_keys=True))
if __name__=="__main__":
    main()
