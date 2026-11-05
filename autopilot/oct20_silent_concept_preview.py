"""Original October 20 concept storyboards: offline preview, never uploadable.

Produces drawn 2.5D concept diagrams using existing Pillow/system fonts and,
optionally, a bounded silent H264 excerpt using existing FFmpeg. No external
assets, model downloads, web search, narrator, voice, copyright proof, account
connection, Google API, publication or schedule. Do not mistake graphics for
actual store/Gemini screenshots, cinematic 3D footage, or full video.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import math
import re
import shutil
import subprocess

from PIL import Image,ImageDraw,ImageFont

from .agent_org import WorkflowError
from .original_episode_pack_audit import PACK,audit_original_editorial_pack

HEADLINES={
 "fm_20261020_short_en":(
    "CHAT OR AGENT?","THE SHOPPING LIST","DRAFT, DON'T BUY",
    "LOCK THE CHECKOUT","PLAN  /  PREVIEW","CHECK YOUR PLAN","YOU DECIDE"),
 "fm_20261020_short_hi":(
    "AI खरीदे?","1000 की लिस्ट","पहले तुलना","ऑर्डर से पहले जाँच",
    "चार सुरक्षित कदम","प्लान उपलब्ध है?","फैसला आपका"),
 "fm_20261020_long_hi":(
    "AI AGENT: पहले PLAN","Chatbot बनाम Agent","हमारी किराना लिस्ट",
    "स्पष्ट निर्देश","कहाँ से आई कीमत?","Tool Access की सीमा",
    "अंतिम Approval","READ  /  DRAFT  /  ACT",
    "किसे मिलेगी सुविधा?","चार सुरक्षा नियम","आपका अगला अभ्यास"),
}
NAVY=(7,16,36)
CYAN=(77,222,242)
TEAL=(48,204,173)
WHITE=(242,248,254)
SLATE=(148,168,194)


@dataclass(frozen=True)
class VisualPreview:
    episode_id:str
    scenes:int
    duration_seconds:int
    language:str
    kind:str


def _deny():
    raise WorkflowError("Original silent storyboard preview refused")


def load_preview_plan()->dict:
    """Read only original source-locked, explicitly unrendered draft."""
    report=audit_original_editorial_pack()
    if (report.get("status")!="ORIGINAL_EDITED_SCRIPT_AND_SCENE_PLAN_ONLY"
            or report.get("youtube_upload_authorized") is not False
            or report.get("real_hd_media_rendered") is not False):
        _deny()
    return json.loads(PACK.read_text(encoding="utf-8"))


def preview_spec(data:dict,episode_id:str)->VisualPreview:
    if (type(data) is not dict
            or data.get("status")!="SCRIPT_AND_STORYBOARD_CANDIDATE_ONLY"
            or type(data.get("episodes")) is not list
            or type(data.get("content_release_policy")) is not dict):
        _deny()
    flags=data["content_release_policy"]
    if any(flags.get(key) is not False for key in (
        "prerecorded_voice_exists","actual_media_encoded",
        "private_upload_authorized","public_publish_authorized")):
        _deny()
    if type(episode_id) is not str or episode_id not in HEADLINES:
        _deny()
    hits=[p for p in data["episodes"] if type(p) is dict
          and p.get("episode_id")==episode_id]
    if len(hits)!=1:
        _deny()
    ep=hits[0]
    chapters=ep.get("segments")
    if type(chapters) is not list or len(chapters)!=len(HEADLINES[episode_id]):
        _deny()
    previous=0
    for ch in chapters:
        if (type(ch) is not dict or type(ch.get("start_second")) is not int
                or type(ch.get("end_second")) is not int
                or ch["start_second"]!=previous
                or ch["end_second"]<=previous):
            _deny()
        previous=ch["end_second"]
    expected={
        "fm_20261020_short_en":(42,"en","short"),
        "fm_20261020_short_hi":(44,"hi","short"),
        "fm_20261020_long_hi":(480,"hi","long"),
    }[episode_id]
    if (previous,ep.get("original_spoken_language"),ep.get("kind"))!=expected:
        _deny()
    return VisualPreview(episode_id,len(chapters),previous,expected[1],expected[2])


def _font(language:str,size:int):
    family=("Noto Sans Devanagari:style=Bold" if language=="hi"
            else "Noto Sans:style=Bold")
    try:
        check=subprocess.run(["fc-match","-f","%{file}",family],
                             stdin=subprocess.DEVNULL,capture_output=True,
                             text=True,check=True,timeout=3)
        file=check.stdout.strip()
        if not file or not Path(file).is_file():
            _deny()
        return ImageFont.truetype(file,size,layout_engine=ImageFont.Layout.RAQM)
    except (OSError,subprocess.SubprocessError,ValueError):
        return ImageFont.load_default()


def _runs(text:str,lang:str,size:int):
    if lang=="en":
        yield text,_font("en",size)
        return
    for part in re.findall(r"[\u0900-\u097f]+|[^\u0900-\u097f]+",text):
        if part:
            yield part,_font("hi" if "\u0900"<=part[0]<="\u097f" else "en",size)


def _mixed(d:ImageDraw.ImageDraw,text:str,lang:str,x:float,y:float,
           size:int,fill:tuple)->None:
    for part,font in _runs(text,lang,size):
        d.text((x,y),part,font=font,fill=fill)
        x+=d.textlength(part,font=font)


def _fitted(d,text,lang,limit,size=52):
    while size>=18:
        if sum(d.textlength(s,font=f) for s,f in _runs(text,lang,size))<=limit:
            break
        size-=2
    return size


def _panel(d,bbox,fill,radius=22,outline=None):
    d.rounded_rectangle(bbox,radius=radius,fill=fill,outline=outline,width=2)


def render_storyboard_keyframe(
    *,plan:dict,episode_id:str,scene_number:int,output_path:Path,
    width:int=540,height:int=960,
)->dict:
    spec=preview_spec(plan,episode_id)
    if (type(scene_number) is not int or not 0<=scene_number<spec.scenes
            or not isinstance(output_path,Path)
            or output_path.suffix.lower()!=".png"
            or output_path.exists() or output_path.is_symlink()
            or not output_path.parent.is_dir()
            or type(width) is not int or type(height) is not int
            or not 360<=width<=1080 or not 600<=height<=1920
            or width*16!=height*9):
        _deny()
    # Draw at fixed editorial geometry and resize: bounded CPU and RAM.
    img=Image.new("RGB",(540,960),NAVY)
    px=img.load()
    for y in range(960):
        for x in range(540):
            r=(x-390)/430
            v=(y-320)/620
            glow=max(0,1-math.sqrt(r*r+v*v))
            px[x,y]=(int(7+9*glow),int(16+17*glow),int(36+31*glow))
    d=ImageDraw.Draw(img)
    d.text((30,35),"FM  /  FLOWMINUTE LAB",font=_font("en",16),fill=CYAN)
    d.text((30,73),"ORIGINAL CONCEPT  ·  NOT A LIVE APP DEMO",
           font=_font("en",11),fill=SLATE)
    d.line((30,110,510,110),fill=(63,93,129),width=2)
    headline=HEADLINES[episode_id][scene_number]
    _mixed(d,headline,spec.language,30,153,_fitted(d,headline,spec.language,472),WHITE)
    terms=(("CHAT","AGENT","LIST","COMPARE","DRAFT","PREVIEW","APPROVE")
           if spec.language=="en"
           else ("सूची","तुलना","ड्राफ़्ट","कीमत","पता","समीक्षा","अनुमति"))
    for i,x in enumerate((38,194,350)):
        y=330+(i%2)*21
        _panel(d,(x+9,y+13,x+144,y+171),(2,8,21),17)
        _panel(d,(x,y,x+135,y+150),(16,39+7*i,69+7*i),17,
               outline=(35,100+20*i,140+15*i))
        d.ellipse((x+15,y+17,x+37,y+39),
                  fill=CYAN if i==0 else TEAL if i==1 else WHITE)
        d.line((x+16,y+56,x+108,y+56),fill=(62,132,164),width=2)
        word=terms[(scene_number+i)%len(terms)]
        _mixed(d,word,spec.language,x+12,y+72,
               _fitted(d,word,spec.language,112,21),WHITE)
        d.text((x+14,y+118),f"STEP 0{i+1}",
               font=_font("en",12),fill=SLATE)
        if i<2:
            d.line((x+138,y+83,x+153,y+83),fill=TEAL,width=3)
    _panel(d,(30,570,510,726),(10,31,56),22,outline=(40,85,122))
    d.text((49,590),"HUMAN APPROVAL",
           font=_font("en",25),fill=CYAN)
    d.text((49,635),"REVIEW  >  PREVIEW  >  CONFIRM",
           font=_font("en",18),fill=WHITE)
    d.text((49,678),"NO PURCHASE OR ACCOUNT ACTION EXECUTED",
           font=_font("en",12),fill=SLATE)
    d.text((30,794),f"SCENE {scene_number+1:02d} / {spec.scenes:02d}",
           font=_font("en",16),fill=CYAN)
    d.rounded_rectangle((30,835,510,842),radius=3,fill=(35,66,97))
    d.rounded_rectangle((30,835,30+480*(scene_number+1)/spec.scenes,842),
                        radius=3,fill=TEAL)
    d.text((30,879),"EDITORIAL PREVIEW  ·  SILENT  ·  NOT FOR UPLOAD",
           font=_font("en",13),fill=SLATE)
    if (width,height)!=(540,960):
        img=img.resize((width,height),Image.Resampling.LANCZOS)
    img.save(output_path,optimize=True)
    return {
        "status":"SILENT_EDITORIAL_KEYFRAME_ONLY",
        "episode_id":episode_id,
        "scene_index":scene_number,
        "width":width,"height":height,
        "original_artwork_reuse_source":"programmatic_original",
        "human_narration_verified":False,
        "phoneme_or_word_alignment_verified":False,
        "cinematic_3d_render_verified":False,
        "youtube_upload_or_publish_authorized":False,
        "external_api_calls":0,"monthly_recurring_infrastructure_inr":0,
    }


def render_silent_preview_excerpt(
    *,episode_id:str,output_path:Path,
    scenes:int=3,seconds_per_scene:int=2,
    width:int=540,height:int=960,
)->dict:
    """Actual short, silent MP4 excerpt. Does not produce full episode."""
    plan=load_preview_plan()
    spec=preview_spec(plan,episode_id)
    if (spec.kind!="short" or type(scenes) is not int
            or not 1<=scenes<=3
            or type(seconds_per_scene) is not int
            or not 1<=seconds_per_scene<=3
            or not isinstance(output_path,Path)
            or output_path.suffix.lower()!=".mp4"
            or output_path.exists() or output_path.is_symlink()
            or not output_path.parent.is_dir()
            or shutil.which("ffmpeg") is None
            or shutil.which("ffprobe") is None):
        _deny()
    with TemporaryDirectory(prefix="fm-silent-editorial-",dir=output_path.parent) as tmp:
        root=Path(tmp)
        inputs=[]
        for i in range(scenes):
            png=root/f"scene{i}.png"
            render_storyboard_keyframe(plan=plan,episode_id=episode_id,
                                       scene_number=i,output_path=png,
                                       width=width,height=height)
            inputs.extend(["-loop","1","-framerate","24","-t",
                           str(seconds_per_scene),"-i",str(png)])
        graph=";".join(f"[{i}:v]fps=24,format=yuv420p,setsar=1[v{i}]"
                       for i in range(scenes))
        graph+=";"+"".join(f"[v{i}]" for i in range(scenes))
        graph+=f"concat=n={scenes}:v=1:a=0[vout]"
        command=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-n",
                 *inputs,"-filter_complex",graph,"-map","[vout]","-an",
                 "-c:v","libx264","-pix_fmt","yuv420p","-preset","veryfast",
                 "-crf","24","-movflags","+faststart",str(output_path)]
        try:
            subprocess.run(command,stdin=subprocess.DEVNULL,
                           capture_output=True,check=True,timeout=110)
            res=subprocess.run(["ffprobe","-v","error","-show_entries",
                 "format=duration:stream=codec_type,codec_name,nb_frames,width,height",
                 "-of","json",str(output_path)],stdin=subprocess.DEVNULL,
                 capture_output=True,text=True,check=True,timeout=15)
            probe=json.loads(res.stdout)
            tracks=probe["streams"]
            if (len(tracks)!=1 or tracks[0].get("codec_type")!="video"
                    or tracks[0].get("codec_name")!="h264"
                    or int(tracks[0]["nb_frames"])!=scenes*seconds_per_scene*24
                    or abs(float(probe["format"]["duration"])-
                           scenes*seconds_per_scene)>0.1):
                raise ValueError("Preview wrong codec/duration/track count")
        except (OSError,ValueError,KeyError,TypeError,
                subprocess.CalledProcessError,subprocess.TimeoutExpired):
            output_path.unlink(missing_ok=True)
            _deny()
    return {
        "status":"SILENT_VIDEO_EXCERPT_NOT_PRODUCTION_READY",
        "episode_id":episode_id,"scene_count":scenes,
        "duration_seconds":scenes*seconds_per_scene,
        "frames":scenes*seconds_per_scene*24,
        "audio_tracks":0,
        "full_video_complete":False,
        "licensed_voice_observed":False,
        "real_speech_or_subtitle_alignment_verified":False,
        "cinematic_3d_footage_verified":False,
        "youtube_upload_authorized":False,
        "publishing_authorized":False,
        "external_api_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }
