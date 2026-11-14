"""Three CLIVOX first-party fictional arcade review videos (no external IP).

Two vertical Shorts (36s each), one 108s horizontal episode. All screenplay,
art and low-volume ambient sound are original; speech is synthesized locally
with espeak-ng and MUST be reviewed by a human before any publication.
Video files are generated ONLY under GitHub runner temp, not in the git tree.
Never downloads game footage, music, source clips, keys, or invokes YouTube.
"""
from __future__ import annotations

import argparse
from array import array
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from textwrap import wrap
import wave


ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"branch3/original_pilots/arcade_trio.json"
CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"
EPISODE_IDS=(
    "clivox_original_door_choice_s01",
    "clivox_original_portal_choice_s02",
    "clivox_original_three_level_arcade_l01"
)
SAFE_ART={"door","buttons","timer","portal","score","arcade"}
COLORS={
    "bg":(8,12,23),"amber":(255,111,42),"pearl":(232,237,245),
    "muted":(146,166,190),"line":(45,62,87),
    "violet":(127,83,255),"mint":(55,222,195)
}
FONT_CANDIDATES=[
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
]


class ArcadeDenied(ValueError):
    pass


def require(ok:bool,why:str)->None:
    if not ok:
        raise ArcadeDenied("CLIVOX_ORIGINAL_PILOT_DENY_"+why)


def get_font(px:int):
    from PIL import ImageFont
    match=next((p for p in FONT_CANDIDATES if Path(p).is_file()),None)
    require(match is not None,"FONT_NOT_FOUND")
    return ImageFont.truetype(match,px)


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):
            h.update(c)
    return h.hexdigest()


def validate_catalog(data:dict)->list[dict]:
    require(type(data) is dict and set(data)=={
        "schema_version","channel_id","stage","creative_origin",
        "music_or_game_footage_included","third_party_clips_included",
        "external_images_or_audio_included","original_speech_generation",
        "human_editorial_review_completed","owner_signed_release_completed",
        "upload_schedule_or_publish_authorized","episodes"
    },"EXACT_CATALOG_FIELDS")
    require(data["schema_version"]==1 and data["channel_id"]==CHANNEL
            and data["stage"]=="ORIGINAL_FIRST_PARTY_FICTIONAL_ARCADE_REVIEW_ASSETS"
            and data["creative_origin"]=="ALL_ORIGINAL_TEXT_VECTOR_GRAPHICS_NO_EXTERNAL_IP"
            and data["original_speech_generation"]=="ESPEAK_NG_SYNTHETIC_VOICE_NONHUMAN_REVIEW",
            "CATALOG_ORIGIN")
    for key in ("music_or_game_footage_included","third_party_clips_included",
                "external_images_or_audio_included",
                "human_editorial_review_completed",
                "owner_signed_release_completed",
                "upload_schedule_or_publish_authorized"):
        require(data[key] is False,"UNVERIFIED_FLAG_"+key)
    eps=data["episodes"]
    require(type(eps) is list and len(eps)==3,"EPISODE_COUNT")
    require(tuple(e.get("id") for e in eps)==EPISODE_IDS,
            "EPISODE_IDS")
    for idx,e in enumerate(eps):
        require(type(e) is dict and set(e)=={
            "id","format","series","title","description",
            "duration_seconds","beats"
        },"EPISODE_FIELDS")
        require(e["format"]==("long" if idx==2 else "short")
                and e["series"]=="THE IMPOSSIBLE ARCADE",
                "FORMAT_SERIES")
        require(type(e["title"]) is str
                and 12<=len(e["title"])<=92
                and type(e["description"]) is str
                and 45<=len(e["description"])<=550,
                "EDITORIAL_META")
        require(type(e["duration_seconds"]) is int
                and e["duration_seconds"]==(108 if idx==2 else 36),
                "DURATION")
        beats=e["beats"]
        require(type(beats) is list
                and len(beats)==(13 if idx==2 else 5),"BEAT_COUNT")
        cursor=0
        for b in beats:
            require(type(b) is dict and set(b)=={
                "start_s","end_s","headline","subheadline","spoken","art"
            },"BEAT_EXACT_FIELDS")
            require(type(b["start_s"]) is int and
                    type(b["end_s"]) is int
                    and b["start_s"]==cursor
                    and 2<=b["end_s"]-b["start_s"]<=15,
                    "BEAT_CLOCK")
            cursor=b["end_s"]
            require(b["art"] in SAFE_ART,"UNAPPROVED_ART")
            for key,length in (("headline",38),("subheadline",85),("spoken",185)):
                val=b[key]
                require(type(val) is str and 4<=len(val)<=length
                        and all(31<ord(c)<127 for c in val)
                        and "http" not in val.lower()
                        and "\\" not in val,
                        "UNSAFE_TEXT_"+key)
        require(cursor==e["duration_seconds"],"BEATS_NOT_COMPLETE")
    return eps


def render_size(kind:str,mode:str)->tuple[int,int,int]:
    require(kind in ("short","long") and mode in ("preview","full"),"VIDEO_MODE")
    if mode=="full":
        return (1080,1920,30) if kind=="short" else (1920,1080,30)
    return (540,960,24) if kind=="short" else (960,540,24)


def original_review_typography(w:int,h:int,kind:str)->dict:
    """Conservative, proportional text positions for 9:16 and 16:9 review.

    Constrains the CLIVOX logo/tagline and footer so long-video typography
    cannot overlap itself or get clipped by landscape frame edges.
    """
    require(kind in ("short","long") and w>=540 and h>=540,
            "TYPOGRAPHY_LAYOUT_INPUT")
    portrait=kind=="short"
    brand_px=round(min(w*.078,h*.061))
    brand_y=round(h*.065)
    tagline_y=round(h*(.114 if portrait else .131))
    tagline_px=max(10,round(min(w*.018,h*.021)))
    footer_y=round(h*.91)
    footer_px=max(12,round(min(w/35,h*.029)))
    warning_y=round(h*(.955 if portrait else .947))
    warning_px=max(11,round(min(w/38,h*.025)))
    require(brand_y+brand_px+2 <= tagline_y
            and tagline_y+tagline_px < round(h*.16)
            and footer_y+footer_px+3 < warning_y
            and warning_y+warning_px < h,
            "UNSAFE_BRAND_OR_FOOTER_OVERLAP")
    return {
        "brand_font_px":brand_px,
        "brand_y":brand_y,
        "tagline_y":tagline_y,
        "tagline_font_px":tagline_px,
        "footer_y":footer_y,
        "footer_font_px":footer_px,
        "warning_y":warning_y,
        "warning_font_px":warning_px,
    }


def original_art_clearance_geometry(w:int,h:int,kind:str)->dict:
    """Reserve a dedicated illustration slot ABOVE spoken subtitle ink.

    Visual audit of the 23-scene contact sheets showed large door/portal art
    continuing into the lower subtitle line. Keep original icons in middle
    panel, end them above ~75% of frame height, and leave upper scene text
    unobstructed. This is a reproducible layout constraint, not aesthetic
    owner approval or an automatically verified full video review.
    """
    require(kind in ("short","long") and
            type(w) is int and type(h) is int and
            w>=540 and h>=540,"ART_SAFE_LAYOUT_DIMENSIONS")
    port=kind=="short"
    center_y=round(h*(.54 if port else .56))
    radius=round(min(w*.32,h*.19)) if port else round(h*.17)
    top=center_y-radius-16
    bottom=center_y+radius+16
    require(top>=round(h*.33) and
            bottom<=round(h*.755) and
            center_y>round(h*.49),
            "ART_OVERLAPS_HEADLINE_OR_CAPTION_SAFEZONE")
    return {"center_x":w//2,"center_y":center_y,
            "radius":radius,"top":top,"bottom":bottom,
            "caption_reserved_below":round(h*.755)}


def native_ass_caption_style(kind:str)->str:
    """FFmpeg libass SRT font/margins in ASS virtual units, NOT pixels.

    ffmpeg SRT-to-ASS uses 384x288 virtual coordinates; using physical
    pixels in MarginV previously pushed portrait captions out of frame and
    moved huge landscape captions over the headline. Fixed native units
    keep video subtitles within lower-middle safe content area for both.
    """
    require(kind in ("short","long"),"ASS_CAPTION_KIND")
    font_size=8 if kind=="short" else 11
    margin_v=50 if kind=="short" else 55
    margin_x=28
    require(6<=font_size<=12 and 40<=margin_v<=70
            and 20<=margin_x<=40,"ASS_NATIVE_CAPTION_SAFE_BOUNDS")
    return (
        f"FontName=DejaVu Sans,FontSize={font_size},Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101925,"
        "BorderStyle=1,Outline=1.5,Shadow=0,Alignment=2,"
        f"MarginV={margin_v},MarginL={margin_x},MarginR={margin_x}"
    )


def text_fit(draw,txt:str,maxw:int,base:int,min_px:int):
    for size in range(base,min_px-1,-2):
        font=get_font(size)
        b=draw.textbbox((0,0),txt,font=font)
        if b[2]-b[0]<=maxw:
            return font
    raise ArcadeDenied("CLIVOX_ORIGINAL_PILOT_DENY_TEXT_OVERFLOW")


def art_icon(draw:ImageDraw.ImageDraw,kind:str,cx:int,cy:int,r:int):
    col=COLORS["amber"]
    violet=COLORS["violet"]
    mint=COLORS["mint"]
    width=max(2,r//24)
    if kind=="door":
        draw.rounded_rectangle((cx-r//2,cy-r,cx+r//2,cy+r),
                               radius=r//10,fill=(32,48,70),
                               outline=col,width=width*2)
        draw.line((cx-r//3,cy-r//3,cx+r//3,cy-r//3),
                  fill=COLORS["line"],width=width)
        draw.ellipse((cx+r//3-6,cy-2,cx+r//3+6,cy+10),fill=mint)
        draw.arc((cx-r//2-10,cy-r-12,cx+r//2+12,cy+r+14),
                 start=225,end=315,fill=violet,width=width)
    elif kind=="buttons":
        for i,color in enumerate((col,violet,mint)):
            xx=cx+(i-1)*int(r*.75)
            draw.ellipse((xx-r//3,cy-r//3,xx+r//3,cy+r//3),
                         fill=(22,30,46),outline=color,width=width*2)
            draw.ellipse((xx-r//5,cy-r//5,xx+r//5,cy+r//5),fill=color)
    elif kind=="portal":
        for i,color in enumerate((col,(90,168,255),mint)):
            xx=cx+(i-1)*int(r*.77)
            draw.ellipse((xx-r//3,cy-r*.77,xx+r//3,cy+r*.77),
                         outline=color,width=width*3,fill=(20,25,42))
            draw.arc((xx-r//4,cy-r*.67,xx+r//4,cy+r*.67),
                     start=65,end=275,fill=color,width=width)
    elif kind=="timer":
        draw.ellipse((cx-r//2,cy-r//2,cx+r//2,cy+r//2),
                     outline=col,width=width*3,fill=(23,31,51))
        draw.line((cx,cy,cx,cy-r//3),fill=COLORS["pearl"],width=width*3)
        draw.line((cx,cy,cx+r//4,cy+r//7),fill=mint,width=width*3)
        draw.arc((cx-r*.63,cy-r*.63,cx+r*.63,cy+r*.63),
                 start=260,end=350,fill=violet,width=width*2)
    else:
        for i in range(5):
            dy=cy+(i-2)*r//3
            size=r*(i+2)//11
            draw.line((cx-size,dy,cx+size,dy),
                      fill=col if i%2==0 else violet,width=width*2)
        draw.ellipse((cx-r//4,cy-r*.7,cx+r//4,cy-r*.2),
                     outline=mint,width=width*2)


def draw_scene(beat:dict,*,ep:dict,index:int,out:Path,mode:str)->None:
    from PIL import Image, ImageDraw
    w,h,fps=render_size(ep["format"],mode)
    im=Image.new("RGB",(w,h),COLORS["bg"])
    dr=ImageDraw.Draw(im)
    # Original dimensional gradient/vector background.
    for y in range(h):
        phase=y/max(1,h-1)
        dr.line((0,y,w,y),
                fill=(round(7+13*phase),round(11+20*phase),
                      round(22+34*phase)))
    step=max(20,w//13)
    for x in range(-h,w+h,step):
        dr.line((x,0,x+h//2,h),fill=(26,37,58),width=max(1,w//540))
    margin=round(w*.085)
    port=ep["format"]=="short"
    panel_top=round(h*(.15 if port else .16))
    panel_bottom=round(h*(.86 if port else .84))
    dr.rounded_rectangle(
        (margin,panel_top,w-margin,panel_bottom),
        radius=max(12,w//26),fill=(17,25,40),
        outline=(46,62,84),width=max(2,w//540*2))
    dr.rounded_rectangle(
        (margin+4,panel_top+20,margin+9,panel_bottom-20),
        radius=3,fill=COLORS["amber"])
    typography=original_review_typography(w,h,ep["format"])
    dr.text((margin+round(w*.03),typography["brand_y"]),"CLIVOX",
            font=text_fit(dr,"CLIVOX",w//2,
                          typography["brand_font_px"],16),
            fill=COLORS["pearl"])
    dr.text((margin+round(w*.03),typography["tagline_y"]),
            "ORIGINAL ARCADE  /  CHALLENGE",
            font=get_font(typography["tagline_font_px"]),
            fill=COLORS["muted"])
    inner_x=margin+round(w*.06)
    panel_width=w-margin-inner_x-round(w*.04)
    title_font=text_fit(dr,beat["headline"],panel_width,
                        max(20,round(w*(.09 if port else .054))),
                        max(12,round(w*.025)))
    sub_font=text_fit(dr,beat["subheadline"],panel_width,
                      max(13,round(w*(.040 if port else .029))),
                      max(11,round(w*.014)))
    title_y=round(h*(.25 if port else .27))
    dr.text((inner_x,title_y),beat["headline"],font=title_font,
            fill=COLORS["pearl"])
    sub_y=title_y+title_font.size+round(h*.022)
    dr.text((inner_x,sub_y),beat["subheadline"],font=sub_font,
            fill=COLORS["amber"])
    artwork=original_art_clearance_geometry(w,h,ep["format"])
    art_icon(dr,beat["art"],artwork["center_x"],
             artwork["center_y"],artwork["radius"])
    # Mobile-safe bottom band, score/progress, no spinning circle.
    footer_y=typography["footer_y"]
    info=f"{index+1:02d} / {len(ep['beats']):02d}"
    dr.text((margin,footer_y),info,
            font=get_font(typography["footer_font_px"]),
            fill=COLORS["amber"])
    mark="ORIGINAL PREVIEW  /  HUMAN REVIEW REQUIRED"
    dr.text((margin,typography["warning_y"]),mark,
            font=text_fit(dr,mark,w-2*margin,
                          typography["warning_font_px"],9),
            fill=COLORS["muted"])
    track_l=margin+round(w*.19)
    track_r=w-margin
    track_y=footer_y+round(h*.018)
    dr.rounded_rectangle((track_l,track_y,track_r,track_y+max(3,h//240)),
                         radius=3,fill=COLORS["line"])
    dr.rounded_rectangle((track_l,track_y,
       track_l+round((track_r-track_l)*(index+1)/len(ep["beats"])),
       track_y+max(3,h//240)),radius=3,fill=COLORS["amber"])
    out.parent.mkdir(parents=True,exist_ok=True)
    im.save(out,optimize=True)


def write_audio(ep:dict,out:Path)->tuple[Path,list[tuple[float,float]]]:
    require(shutil.which("espeak-ng") is not None
            and shutil.which("ffmpeg") is not None,
            "SPEECH_AND_FFMPEG_REQUIRED")
    sr=48000
    total=ep["duration_seconds"]*sr
    voice=array("h",[0])*total
    voice_regions=[]
    for n,beat in enumerate(ep["beats"]):
        raw=out/f"narration-raw-{n:02}.wav"
        converted=out/f"narration-48k-{n:02}.wav"
        subprocess.run(["espeak-ng","-v","en-us","-s","175","-p","49",
                        "-a","170","-w",str(raw),beat["spoken"]],
                       check=True,stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,timeout=25)
        subprocess.run(
            ["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-i",str(raw),"-ar",str(sr),"-ac","1",
             "-c:a","pcm_s16le",str(converted)],
            check=True,timeout=30
        )
        with wave.open(str(converted),"rb") as wav:
            require(wav.getnchannels()==1
                    and wav.getsampwidth()==2
                    and wav.getframerate()==sr,"VOICE_FORMAT")
            pcm=array("h")
            pcm.frombytes(wav.readframes(wav.getnframes()))
        max_samples=int((beat["end_s"]-beat["start_s"]-.15)*sr)
        # Never silently truncate spoken narration. A modest tempo correction
        # is permitted, but an excessively dense script fails before encoding.
        if len(pcm)>max_samples:
            ratio=(len(pcm)/max_samples)*1.04
            require(ratio<=1.48,"VOICE_TOO_LONG_FOR_BEAT")
            sped=out/f"narration-timed-{n:02}.wav"
            subprocess.run(
                ["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                 "-i",str(converted),"-filter:a",f"atempo={ratio:.5f}",
                 "-ar",str(sr),"-ac","1","-c:a","pcm_s16le",str(sped)],
                check=True,timeout=30
            )
            with wave.open(str(sped),"rb") as wav:
                require(wav.getnchannels()==1 and wav.getsampwidth()==2
                        and wav.getframerate()==sr,
                        "TIMED_VOICE_FORMAT")
                pcm=array("h")
                pcm.frombytes(wav.readframes(wav.getnframes()))
            sped.unlink(missing_ok=True)
        require(len(pcm)<=max_samples,"VOICE_OVERFLOW_AFTER_TIME_CORRECTION")
        off=int((beat["start_s"]+.08)*sr)
        # These bounds are measured from actual post-atempo TTS PCM samples,
        # not from the screenplay beat length or an invented speech transcript.
        # Word/phoneme boundaries within this span remain estimates.
        voice_regions.append((off/sr,(off+len(pcm))/sr))
        for j,value in enumerate(pcm):
            voice[off+j]=int(value*.70)
        raw.unlink(missing_ok=True)
        converted.unlink(missing_ok=True)
    # Original procedural sound bed and 0.17s transition stings.
    # No music library, game effect, speech sample or external sound is used.
    boundaries=[b["start_s"] for b in ep["beats"]]
    block_start=0
    chunk=sr*2
    for left in range(0,total,chunk):
        end=min(total,left+chunk)
        for i in range(left,end):
            t=i/sr
            bed=52*math.sin(2*math.pi*92*t)+24*math.sin(2*math.pi*184*t)
            sting=0.0
            for boundary in boundaries:
                delta=t-boundary
                if 0<=delta<.16:
                    sting+=1250*math.sin(2*math.pi*(360+600*delta)*delta)*math.exp(-24*delta)
            val=voice[i]+round(bed+sting)
            voice[i]=max(-32768,min(32767,val))
    destination=out/"original-tts-and-procedural-ambience.wav"
    with wave.open(str(destination),"wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sr)
        audio.writeframes(voice.tobytes())
    return destination,voice_regions


def stamp(seconds:float)->str:
    n=round(seconds*1000)
    hours,rem=divmod(n,3600000)
    mins,rem=divmod(rem,60000)
    secs,millis=divmod(rem,1000)
    return f"{hours:02}:{mins:02}:{secs:02},{millis:03}"


def draft_srt(
    ep:dict,path:Path,
    voice_regions:list[tuple[float,float]]|None=None
)->None:
    """Draft captions weighted within post-tempo synthesized speech intervals.

    Unlike previous beat-length distribution, real rendered narration segments
    determine the active cue window. Individual word timing is an estimate:
    neither a forced alignment nor human subtitle/voice approval is claimed.
    A final-episode CTA can remain visible through the last frame.
    """
    require(voice_regions is None or
            (type(voice_regions) is list and
             len(voice_regions)==len(ep["beats"])),"VOICE_REGIONS_COUNT")
    cue_lines=[]
    cue_number=0
    for index,beat in enumerate(ep["beats"]):
        words=beat["spoken"].split(" ")
        chunks=[]
        line=[]
        for word in words:
            proposed=" ".join([*line,word])
            if len(proposed)>35 and line:
                chunks.append(" ".join(line))
                line=[word]
            else:
                line.append(word)
        if line:
            chunks.append(" ".join(line))
        lines=["\n".join(chunks[j:j+2])
               for j in range(0,len(chunks),2)]
        if voice_regions is None:
            speech_start=float(beat["start_s"])
            speech_end=float(beat["end_s"])
            # Backward-compatible dummy SRT for no-audio unit tests.
            weights=[1]*len(lines)
        else:
            speech_start,speech_end=voice_regions[index]
            require(
                type(speech_start) in (float,int) and
                type(speech_end) in (float,int) and
                beat["start_s"]<=speech_start<
                speech_end<=beat["end_s"]-.025 and
                speech_end-speech_start>=.30,
                "VOICE_REGION_OUTSIDE_BEAT")
            # A cue of 16 characters should receive more of the measured
            # speech time than a cue of 3 characters. This is still DRAFT.
            weights=[max(1,len(txt.replace("\n"," "))) for txt in lines]
        elapsed=0
        total_weight=sum(weights)
        for j,txt in enumerate(lines):
            cue_number+=1
            start=speech_start+(speech_end-speech_start)*elapsed/total_weight
            elapsed+=weights[j]
            end=speech_start+(speech_end-speech_start)*elapsed/total_weight
            # In real synthesized videos, do not leave a lone final word
            # onscreen for the remaining silent outro. The scene itself
            # already carries the viewer's call-to-action after speech ends.
            require(end-start>=.055 and
                    all(len(x)<=36 for x in txt.split("\n")),
                    "SUBTITLE_WIDTH_OR_DURATION")
            cue_lines.append(
                f"{cue_number}\n{stamp(start)} --> {stamp(end)}\n{txt}\n"
            )
    path.write_text("\n".join(cue_lines)+"\n",encoding="utf-8")


def encode_video(ep:dict,scenes:list[Path],audio:Path,output:Path,
                 mode:str,*,captions:Path)->None:
    w,h,fps=render_size(ep["format"],mode)
    require(len(scenes)==len(ep["beats"]),"SCENE_FILES_COUNT")
    require(captions.is_absolute() and captions.is_file()
            and not captions.is_symlink()
            and re.fullmatch(r"[a-zA-Z0-9_./-]+",str(captions)) is not None,
            "SAFE_LOCAL_CAPTION_PATH_ONLY")
    cmd=["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y"]
    for scene in scenes:
        cmd+=["-i",str(scene)]
    cmd+=["-i",str(audio)]
    filters=[]
    video_tracks=[]
    for i,beat in enumerate(ep["beats"]):
        frames=(beat["end_s"]-beat["start_s"])*fps
        track=f"v{i}"
        filters.append(
            f"[{i}:v]zoompan=z='min(zoom+0.00012,1.05)':"
            f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d={frames}:"
            f"s={w}x{h}:fps={fps},format=yuv420p,setpts=PTS-STARTPTS[{track}]"
        )
        video_tracks.append(f"[{track}]")
    filters.append("".join(video_tracks)+
                   f"concat=n={len(video_tracks)}:v=1:a=0[precap]")
    # Burn *draft* captions into the offline review MP4 as well as supplying
    # editable SRT: Shorts viewers can evaluate the text without enabling
    # a separate subtitle stream. Do not interpret as final speech alignment.
    # libass uses VIRTUAL subtitle units, not output-frame pixels.
    # FontSize=25/MarginV=346 physically pushed vertical captions offscreen.
    caption_style=native_ass_caption_style(ep["format"])
    filters.append(
        f"[precap]subtitles=filename='{captions}':"
        f"force_style='{caption_style}',format=yuv420p[outv]"
    )
    cmd+=["-filter_complex",";".join(filters),"-map","[outv]",
          "-map",f"{len(scenes)}:a:0",
          "-c:v","libx264","-pix_fmt","yuv420p",
          "-preset","ultrafast" if mode=="preview" else "veryfast",
          "-crf","29" if mode=="preview" else "23",
          "-r",str(fps),"-threads","2",
          "-c:a","aac","-ar","48000","-b:a","128k",
          "-movflags","+faststart","-t",str(ep["duration_seconds"]),
          str(output)]
    subprocess.run(cmd,check=True,timeout=850)


def render_episode(ep:dict,folder:Path,mode:str)->dict:
    require(mode in ("preview","full"),"RENDER_MODE")
    require(folder.is_absolute() and folder.is_dir()
            and not folder.is_symlink()
            and ROOT not in folder.parents and folder!=ROOT,
            "OUTPUT_ONLY_OUTSIDE_PUBLIC_REPOSITORY")
    shots=[]
    for i,b in enumerate(ep["beats"]):
        image=folder/f"scene-{i:02}.png"
        draw_scene(b,ep=ep,index=i,out=image,mode=mode)
        shots.append(image)
    audio,voice_regions=write_audio(ep,folder)
    captions=folder/"narration-timing-draft.srt"
    draft_srt(ep,captions,voice_regions=voice_regions)
    mp4=folder/"original-review-preview.mp4"
    encode_video(ep,shots,audio,mp4,mode,captions=captions)
    w,h,fps=render_size(ep["format"],mode)
    manifest={
        "schema_version":1,"channel_id":CHANNEL,
        "stage":"A4_A5_ORIGINAL_FIRST_PARTY_EDITORIAL_REVIEW_NOT_RELEASE",
        "episode_id":ep["id"],"format":ep["format"],
        "title":ep["title"],"description":ep["description"],
        "duration_seconds":ep["duration_seconds"],
        "output_width":w,"output_height":h,"fps":fps,
        "render_mode":mode,
        "source_media_downloaded":False,
        "external_images_video_or_audio_used":False,
        "original_script_and_vector_art":True,
        "tts_voice_synthetic_not_human_recording":True,
        "srt_is_draft_not_forced_aligned":True,
        "srt_measured_synthesized_pcm_speech_windows":True,
        "srt_word_timing_is_estimated_not_forced_aligned":True,
        "draft_captions_burned_into_review_mp4":True,
        "video_file":mp4.name,"video_sha256":sha(mp4),
        "video_bytes":mp4.stat().st_size,
        "audio_file":audio.name,"audio_sha256":sha(audio),
        "subtitle_file":captions.name,"subtitle_sha256":sha(captions),
        "scene_count":len(shots),
        "real_voice_actor_or_music_license_verified":False,
        "human_editorial_review_completed":False,
        "owner_exact_asset_signed":False,
        "ready_to_upload":False,
        "ready_to_schedule":False,
        "ready_to_publish":False,
        "actual_external_api_calls":0
    }
    (folder/"review-manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8"
    )
    return manifest


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("preview","full"),default="preview")
    p.add_argument("--selection",choices=("one","all"),default="one")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    require(args.output.is_absolute() and args.output.is_dir()
            and not args.output.is_symlink()
            and ROOT not in args.output.parents,"OUTPUT_PATH")
    catalog=json.loads(CATALOG.read_text("utf-8"))
    episodes=validate_catalog(catalog)
    selected=episodes[:1] if args.selection=="one" else episodes
    summaries=[]
    for ep in selected:
        dest=args.output/ep["id"]
        dest.mkdir(parents=True,exist_ok=False)
        m=render_episode(ep,dest,args.mode)
        summaries.append({
            "episode_id":m["episode_id"],
            "format":m["format"],"duration_s":m["duration_seconds"],
            "technical_video_file_generated":True,
            "source_media_downloaded":False,
            "human_review_complete":False,
            "publish_authorized":False
        })
    print(json.dumps({"stage":"CLIVOX_ORIGINAL_FIRST_PARTY_REVIEW",
                      "episodes":summaries,"youtube_upload_calls":0},
                     sort_keys=True))


if __name__=="__main__":
    main()
