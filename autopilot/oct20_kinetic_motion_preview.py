"""FlowMinute Oct 20: kinetic original 2.5D storyboard animation (NO VOICE).

Pure Pillow drawings streamed as RGB frames into installed FFmpeg.  Three
independent beats per Short: shifting camera/depth, layered isometric cards,
moving connector pulses, progress and approval lock. Hindi uses a distinct
Devanagari design, not a fake app screenshot. NO 3D mesh, licensed narration,
ASR, finished-video, cloud service, publish or claimed original-voice rights.
No filesystem writes except one explicitly requested fresh preview MP4.
"""
from __future__ import annotations

from functools import lru_cache
from math import cos, sin, pi
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .agent_org import WorkflowError
from .oct20_silent_concept_preview import load_preview_plan,preview_spec

WIDTH=432
HEIGHT=768
FPS=24
BEAT_SECONDS=4
MAX_BEATS=3
MAX_PREVIEW_SECONDS=12

CHROME={
 "en":{
    "concept":"ORIGINAL 2.5D CONCEPT  /  NO LIVE APP",
    "tagline":"HUMAN CONTROL  >  AUTONOMY",
    "step":"STEP",
    "review":"REVIEWABLE",
    "lock":"FINAL ACTION LOCKED",
    "approval":"REQUIRES EXPLICIT HUMAN APPROVAL",
    "footer":"SILENT DRAFT / NOT FOR UPLOAD",
 },
 "hi":{
    "concept":"मूल 2.5D अवधारणा / असली ऐप नहीं",
    "tagline":"नियंत्रण आपके हाथ में",
    "step":"कदम",
    "review":"जाँच",
    "lock":"अंतिम कार्रवाई बंद",
    "approval":"आपकी स्पष्ट अनुमति ज़रूरी है",
    "footer":"बिना आवाज़ / अपलोड के लिए नहीं",
 },
}

BEATS={
 "fm_20261020_short_en":(
  ("CHAT TO ACTION","Question","Tool plan","Review"),
  ("GROCERY LIST","List","Compare","Draft"),
  ("DRAFT, DON'T BUY","Draft cart","Check price","Approve"),
 ),
 "fm_20261020_short_hi":(
  ("AI खरीदे?","सोचें","प्लान","जाँच"),
  ("किराने की सूची","सामान","तुलना","ड्राफ़्ट"),
  ("ऑर्डर से पहले जाँच","कीमत","पता","अनुमति"),
 ),
}
COLORS={
 "bg":(7,16,33),"panel":(17,34,56),"cyan":(74,219,237),
 "teal":(43,202,172),"white":(243,247,251),
 "muted":(156,178,197),"dark":(3,9,22),
}


def _deny():
    raise WorkflowError("Unlicensed kinetic storyboard preview unavailable")


@lru_cache(maxsize=12)
def _font(lang:str,size:int,bold:bool=False):
    name="Noto Sans Devanagari" if lang=="hi" else "DejaVu Sans"
    if bold:name+=":style=Bold"
    try:
        p=subprocess.run(["fc-match","-f","%{file}",name],
                         capture_output=True,text=True,check=True,timeout=3)
        file=Path(p.stdout.strip())
        if not file.is_file():_deny()
        return ImageFont.truetype(str(file),size,layout_engine=ImageFont.Layout.RAQM)
    except (OSError,ValueError,subprocess.SubprocessError):
        _deny()


def _draw_fit(d:ImageDraw.ImageDraw,label:str,lang:str,xy:tuple,
              max_width:int,desired:int,color:tuple):
    for sz in range(desired,12,-1):
        f=_font(lang,sz,bold=True)
        if d.textlength(label,font=f)<=max_width:
            d.text(xy,label,font=f,fill=color)
            return
    _deny()


def _design_valid(episode_id:str,seconds:int)->None:
    if (type(episode_id) is not str or episode_id not in BEATS
            or type(seconds) is not int or not 1<=seconds<=MAX_PREVIEW_SECONDS):
        _deny()
    # The ONLY acceptable content plan is the existing, still UNPUBLISHED
    # authored October 20 pack. Editorial source/timeline also validated.
    plan=load_preview_plan()
    detail=preview_spec(plan,episode_id)
    if detail.kind!="short" or detail.scenes!=7:
        _deny()
    if len(BEATS[episode_id])!=3:
        _deny()
    for beat in BEATS[episode_id]:
        if type(beat) is not tuple or len(beat)!=4:
            _deny()


def _background(phase:float)->Image.Image:
    base=Image.new("RGB",(WIDTH,HEIGHT),COLORS["bg"])
    d=ImageDraw.Draw(base)
    for y in range(HEIGHT):
        wobble=sin(phase*.4+y/145)
        v=int(4+5*(y/HEIGHT)+3*wobble)
        d.line((0,y,WIDTH,y),fill=(7+v//2,16+v,33+v*2))
    glow=Image.new("RGBA",(WIDTH,HEIGHT),(0,0,0,0))
    g=ImageDraw.Draw(glow)
    gx=320+int(70*sin(phase*.3))
    gy=285+int(58*cos(phase*.2))
    g.ellipse((gx-150,gy-150,gx+150,gy+150),fill=(21,140,161,62))
    glow=glow.filter(ImageFilter.GaussianBlur(55))
    return Image.alpha_composite(base.convert("RGBA"),glow)


def _card(layer:Image.Image,index:int,text:str,language:str,
          phase:float,beat:int)->None:
    d=ImageDraw.Draw(layer)
    drift=10*sin(phase*.85-index*.95)
    lift=8*cos(phase*.65+index*1.2)
    x=int(34+index*10+drift)
    y=int(286+index*95+lift)
    w=355-index*12
    h=83
    depth=12+index*2
    # Perspective-looking extrusion + offset soft shadow, no fake true 3D.
    d.rounded_rectangle((x+14,y+depth,w+x+14,y+h+depth),
                        radius=17,fill=(3,10,22,230))
    d.polygon([(x+8,y+h-5),(x+w+3,y+h-5),
               (x+w+15,y+h+depth),(x+21,y+h+depth)],
              fill=(9,51+index*8,66+index*7,255))
    fill=(18,48,69,247) if index!=2 else (17,51,62,249)
    outline=(*COLORS["cyan"],255) if beat==index else (57,108,130,255)
    d.rounded_rectangle((x,y,x+w,y+h),radius=17,fill=fill,
                        outline=outline,width=2)
    d.ellipse((x+16,y+21,x+44,y+49),fill=(*COLORS["teal"],255))
    d.line((x+22,y+35,x+29,y+42,x+40,y+26),fill=(*COLORS["bg"],255),width=3)
    _draw_fit(d,text,language,(x+57,y+16),w-76,22,(*COLORS["white"],255))
    c=CHROME[language]
    subtitle=f"{c['step']} 0{index+1}  /  {c['review']}"
    _draw_fit(d,subtitle,language,(x+59,y+52),
              w-75,11,(*COLORS["muted"],255))
    if index<2:
        progress=.5+.5*sin(phase*1.9-index*1.4)
        d.line((x+w-6,y+h+3,x+w-6,y+h+14),fill=(*COLORS["cyan"],255),width=3)
        d.ellipse((x+w-11,y+h+5+progress*8,
                   x+w-3,y+h+13+progress*8),
                  fill=(*COLORS["teal"],255))


def draw_motion_frame(episode_id:str,frame_number:int)->Image.Image:
    if (episode_id not in BEATS or type(frame_number) is not int
            or not 0<=frame_number<MAX_PREVIEW_SECONDS*FPS):
        _deny()
    seconds=frame_number/FPS
    beat=min(int(seconds/BEAT_SECONDS),MAX_BEATS-1)
    local=(seconds-beat*BEAT_SECONDS)/BEAT_SECONDS
    lang="hi" if episode_id.endswith("_hi") else "en"
    phase=seconds*1.9
    base=_background(phase)
    d=ImageDraw.Draw(base)
    # A moving grid communicates camera parallax rather than motionless slides.
    offset=int((seconds*17)%36)
    for x in range(-36+offset,WIDTH+25,36):
        d.line((x,226,x-50,640),fill=(26,69,87,84),width=1)
    for y in range(226,640,39):
        d.line((0,y+offset//4,WIDTH,y+offset//4),
               fill=(29,74,91,60),width=1)
    d.text((26,25),"FM  /  FLOWMINUTE LAB",
           font=_font("en",15,True),fill=(*COLORS["cyan"],255))
    _draw_fit(d,CHROME[lang]["concept"],lang,(26,59),380,12,
              (*COLORS["muted"],255))
    d.line((26,90,406,90),fill=(*COLORS["cyan"],115),width=2)
    heading,*steps=BEATS[episode_id][beat]
    entrance=(1-min(1,local*5))**2
    heading_y=int(127-27*entrance+2*sin(phase))
    _draw_fit(d,heading,lang,(27,heading_y),376,34,(*COLORS["white"],255))
    _draw_fit(d,CHROME[lang]["tagline"],lang,(29,202),375,18,
              (*COLORS["teal"],255))
    for i,item in enumerate(steps):
        _card(base,i,item,lang,phase,beat)
    # Meaningful animation: progress advances, human approval remains LOCKED.
    d=ImageDraw.Draw(base)
    d.rounded_rectangle((27,634,407,697),radius=17,
                        fill=(5,20,38,245),outline=(57,164,165,255),width=2)
    _draw_fit(d,CHROME[lang]["lock"],lang,(47,649),333,18,
              (*COLORS["cyan"],255))
    _draw_fit(d,CHROME[lang]["approval"],lang,(47,676),329,13,
              (*COLORS["white"],255))
    d.rounded_rectangle((27,721,407,728),radius=3,fill=(30,62,78,255))
    d.rounded_rectangle((27,721,27+int(380*(frame_number+1)/
                                          (MAX_PREVIEW_SECONDS*FPS)),728),
                        radius=3,fill=(*COLORS["teal"],255))
    _draw_fit(d,CHROME[lang]["footer"],lang,(27,739),375,12,
              (*COLORS["muted"],255))
    return base.convert("RGB")


def render_kinetic_silent_excerpt(*,episode_id:str,
                                  output_path:Path,seconds:int=9)->dict:
    """Render 1..12 seconds H.264 video-only. NO audio or publication."""
    _design_valid(episode_id,seconds)
    if (not isinstance(output_path,Path)
            or output_path.suffix.lower()!=".mp4"
            or output_path.exists() or output_path.is_symlink()
            or not output_path.parent.is_dir()
            or output_path.parent.is_symlink()
            or shutil.which("ffmpeg") is None
            or shutil.which("ffprobe") is None):
        _deny()
    proc=None
    try:
        with TemporaryDirectory(prefix="fm-original-motion-",dir=output_path.parent):
            cmd=[
              "ffmpeg","-hide_banner","-v","error","-nostdin","-n",
              "-f","rawvideo","-pix_fmt","rgb24",
              "-s",f"{WIDTH}x{HEIGHT}","-r",str(FPS),"-i","pipe:0",
              "-an","-c:v","libx264","-pix_fmt","yuv420p",
              "-preset","veryfast","-crf","23",
              "-movflags","+faststart",str(output_path),
            ]
            # Python draws each ORIGINAL RGB frame. FFMPEG cannot grab media,
            # devices, providers or any other files beyond this explicit path.
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            try:
                for n in range(seconds*FPS):
                    image=draw_motion_frame(episode_id,n)
                    proc.stdin.write(image.tobytes())
                proc.stdin.close()
                result=proc.wait(timeout=55)
            except (BrokenPipeError,OSError,subprocess.TimeoutExpired):
                proc.kill()
                proc.wait(timeout=5)
                _deny()
            if result!=0 or not output_path.is_file():
                _deny()
            out=subprocess.run(
                ["ffprobe","-v","error","-show_entries",
                 "format=duration:stream=codec_type,codec_name,nb_frames,width,height",
                 "-of","json",str(output_path)],
                capture_output=True,text=True,check=True,timeout=12,
            )
            info=json.loads(out.stdout)
            tracks=info["streams"]
            if (len(tracks)!=1 or tracks[0].get("codec_type")!="video"
                    or tracks[0].get("codec_name")!="h264"
                    or int(tracks[0].get("width"))!=WIDTH
                    or int(tracks[0].get("height"))!=HEIGHT
                    or int(tracks[0].get("nb_frames"))!=seconds*FPS
                    or abs(float(info["format"]["duration"])-seconds)>.09):
                _deny()
    except (subprocess.CalledProcessError,ValueError,TypeError,
            KeyError,TimeoutError,OSError):
        output_path.unlink(missing_ok=True)
        _deny()
    return {
      "status":"ANIMATED_2_5D_SILENT_STORYBOARD_PREVIEW_ONLY",
      "episode_id":episode_id,"seconds":seconds,
      "width":WIDTH,"height":HEIGHT,"fps":FPS,
      "frame_count":seconds*FPS,"audio_track_count":0,
      "has_actual_layered_motion":True,
      "independent_hindi_and_english_designs":True,
      "full_episode_completed":False,
      "cinematic_3d_mesh_rendered":False,
      "licensed_narration_verified":False,
      "independent_speech_subtitle_alignment_verified":False,
      "media_rights_cleared":False,
      "youtube_upload_authorized":False,
      "youtube_publish_authorized":False,
      "external_network_calls":0,
      "monthly_recurring_infrastructure_inr":0,
    }
