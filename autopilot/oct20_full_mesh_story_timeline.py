"""Original 20-Oct bilingual seven-scene 3D geometry silent review timeline.

Every frame of the EN 42-second / HI 44-second script is tied to the authored
seven-scene timeline. The scenes use different geometry labels, choreography,
lighting and approval teaching beats. This uses the pre-existing original
3D polygon projection/lighting helpers; it is NOT another static storyboard.

The full-length option is EXPLICIT and offline, bounded to 1056 frames,
never invoked in ordinary CI. CI renders one genuine second. Outputs contain
NO narration, no true speech captions, no external app shots, no copyrighted
borrowed media, no YouTube or cloud action. No inference, network or payment.
This is ORIGINAL stylized 3D concept animation, not photoreal footage.
"""
from __future__ import annotations

from functools import lru_cache
from math import cos,sin,pi
from pathlib import Path
import json
import shutil
import subprocess
import time

from PIL import Image,ImageDraw,ImageFilter

from .agent_org import WorkflowError
from .oct20_full_silent_timeline import full_silent_scene_plan
from .hybrid_scene_director import render_scene_world,scene_recipe_plan
from .oct20_mesh_cinematic_proof import (
    BLUE,FPS,HEIGHT,LANES,NAVY,TEAL,WHITE,WIDTH,
    _camera,_fitted,_font,mesh_cube,project_vertex,
)

# Specific teaching visuals for each of the SEVEN original source scenes.
# These labels are ORIGINAL GRAPHICS, not live prices, groceries or accounts.
SCENE_STORIES={
 "fm_20261020_short_en":(
    ("WHO APPROVES?","CHAT   >   TOOL   >   ACTION",
     ("CHAT","PLAN","CHECK"),"CONTROL THE FINAL ACTION"),
    ("A FICTIONAL GROCERY LIST","MILK / RICE / VEGETABLES",
     ("LIST","OPTIONS","BUDGET"),"ALL PRICES LEFT BLANK"),
    ("BUILD A DRAFT","LIST   >   COMPARE   >   DRAFT",
     ("LIST","COMPARE","DRAFT"),"NO REAL CART WAS CREATED"),
    ("CHECK THE RISK","PRICE   /   ADDRESS   /   PAYMENT",
     ("PRICE","ADDRESS","PAY"),"PURCHASE BUTTON: LOCKED"),
    ("FOUR SAFETY STEPS","PLAN  /  SOURCES  /  PREVIEW  /  OK",
     ("PLAN","SOURCE","VIEW","APPROVE"),"APPROVAL ONLY AFTER REVIEW"),
    ("CHECK ACCESS FIRST","FEATURES DEPEND ON PLAN & REGION",
     ("APP","PLAN","REGION"),"AVAILABILITY NOT CONFIRMED"),
    ("KEEP HUMAN CONTROL","AUTOMATION HELPS, YOU DECIDE",
     ("AGENT","REVIEW","HUMAN"),"FINAL DECISION STAYS WITH YOU"),
 ),
 "fm_20261020_short_hi":(
    ("आख़िरी फैसला किसका?","सवाल, योजना और जाँच",
     ("सवाल","प्लान","जाँच"),"अंतिम अनुमति आपकी"),
    ("किराने की काल्पनिक सूची","सामान और बजट समझिए",
     ("चावल","दूध","सब्ज़ी"),"कीमतें यहाँ नहीं दिखाई गईं"),
    ("पहले ड्राफ़्ट बनाइए","सूची से तुलना और मसौदा",
     ("सूची","तुलना","ड्राफ़्ट"),"कोई असली कार्ट नहीं बना"),
    ("ऑर्डर से पहले रोकिए","कीमत, पता और भुगतान",
     ("कीमत","पता","पेमेंट"),"खरीदारी का बटन बंद"),
    ("सुरक्षा के चार कदम","प्लान, स्रोत, प्रीव्यू, अनुमति",
     ("प्लान","स्रोत","प्रीव्यू","अनुमति"),"जाँच के बाद आपकी मंज़ूरी"),
    ("सुविधा उपलब्ध है?","प्लान और क्षेत्र जाँचिए",
     ("ऐप","प्लान","क्षेत्र"),"उपलब्धता की पुष्टि नहीं"),
    ("नियंत्रण आपके हाथ","एआई मदद करे, फैसला आप करें",
     ("एआई","जाँच","आप"),"अंतिम अनुमति आपकी"),
 ),
}
SCENE_TONES=(
 ((35,110,208),(12,200,180),(61,130,235),(16,180,183)),
 ((21,152,187),(31,194,130),(82,134,210),(26,188,178)),
 ((34,127,224),(24,199,189),(72,142,215),(26,205,146)),
 ((178,82,103),(72,112,182),(228,149,70),(23,204,187)),
 ((35,128,217),(14,200,174),(22,150,225),(60,204,160)),
 ((71,110,178),(28,183,183),(138,129,194),(65,168,188)),
 ((23,142,208),(10,218,183),(53,135,215),(58,204,163)),
)
TOTAL_FRAMES={"fm_20261020_short_en":1008,"fm_20261020_short_hi":1056}
_MAX_FILE_BYTES=95_000_000


def _hold():
    raise WorkflowError("Oct20 seven-scene 3D silent editorial preview HOLD")


@lru_cache(maxsize=1)
def _background():
    img=Image.new("RGB",(WIDTH,HEIGHT))
    d=ImageDraw.Draw(img)
    for y in range(HEIGHT):
        b=int(6+12*y/HEIGHT)
        d.line((0,y,WIDTH,y),fill=(6+b//2,14+b,29+b))
    glow=Image.new("RGBA",(WIDTH,HEIGHT))
    g=ImageDraw.Draw(glow)
    g.ellipse((120,220,500,810),fill=(14,119,155,68))
    return Image.alpha_composite(
        img.convert("RGBA"),glow.filter(ImageFilter.GaussianBlur(78))
    )


@lru_cache(maxsize=2)
def _authored_cuts(episode_id):
    if type(episode_id) is not str or episode_id not in SCENE_STORIES:
        _hold()
    cuts=full_silent_scene_plan(episode_id)
    if (len(cuts)!=7
            or len(SCENE_STORIES[episode_id])!=7
            or cuts[0].start_frame!=0
            or cuts[-1].end_frame!=TOTAL_FRAMES[episode_id]
            or any(c.start_frame>=c.end_frame for c in cuts)
            or any(a.end_frame!=b.start_frame for a,b in zip(cuts,cuts[1:]))):
        _hold()
    return cuts


def _scene_for_frame(episode_id,frame):
    if (type(frame) is not int or frame<0
            or frame>=TOTAL_FRAMES.get(episode_id,0)):
        _hold()
    for cut in _authored_cuts(episode_id):
        if cut.start_frame<=frame<cut.end_frame:
            return cut
    _hold()


def draw_oct20_full_mesh_frame(episode_id,frame):
    """True polygon mesh and scene-specific original human-control lesson."""
    cut=_scene_for_frame(episode_id,frame)
    number=cut.scene_index
    headline,subtitle,steps,lock=SCENE_STORIES[episode_id][number]
    lang=LANES[episode_id]["lang"]
    phase=frame/FPS
    local_frame=frame-cut.start_frame
    progress=(local_frame+1)/(cut.end_frame-cut.start_frame)
    image=_background().copy()
    d=ImageDraw.Draw(image)
    cam=_camera(frame+number*13)

    # Real differentiated teaching scene: seven independent environments,
    # not the old three/four repeated rotating cubes plus label variations.
    recipe=scene_recipe_plan(episode_id)["shot_recipes"][number]
    if recipe["beat"]!=number or recipe["actual_real_app_screenshot"]:
        _hold()
    render_scene_world(image,episode_id,number,frame)

    d.rounded_rectangle((22,18,518,101),radius=17,
                        fill=(9,26,46,248),outline=(*BLUE,182),width=2)
    d.text((40,32),"FLOWMINUTE LAB  /  ORIGINAL 3D",
           font=_font("en",17),fill=WHITE)
    d.text((40,68),
           ("काल्पनिक दृश्य / वास्तविक ऐप नहीं"
            if lang=="hi" else "FICTIONAL CONCEPT, NOT A REAL APP"),
           font=_font(lang,12),fill=(160,181,205))

    d.text((25,126),headline,
           font=_fitted(d,headline,lang,490,34),fill=WHITE)
    d.text((25,186),subtitle,
           font=_fitted(d,subtitle,lang,490,21),
           fill=(132,230,219))
    d.text((27,239),
           f"SCENE {number+1:02d} / 07  |  SCRIPT {cut.start_second:02d}–{cut.end_second:02d}s",
           font=_font("en",14),fill=(147,179,206))

    # Approval CTA stays LOCKED in every scene, including the demo ending.
    d.rounded_rectangle((22,768,518,880),radius=18,
                        fill=(6,24,46,245),outline=(*TEAL,255),width=2)
    d.text((42,786),
           ("असली ऑर्डर बंद" if lang=="hi" else "REAL PURCHASE / LOCKED"),
           font=_font(lang,17),fill=(*BLUE,255))
    d.text((42,820),lock,font=_fitted(d,lock,lang,455,20),
           fill=WHITE)
    d.rounded_rectangle((26,904,514,912),radius=4,fill=(28,69,91,255))
    d.rounded_rectangle((26,904,26+int(488*(
        (frame+1)/TOTAL_FRAMES[episode_id])),912),
        radius=4,fill=(*TEAL,255))
    footer=("मूल दृश्य / बिना आवाज़ / अपलोड नहीं"
            if lang=="hi" else "STYLIZED 3D / SILENT / NOT FOR UPLOAD")
    d.text((25,930),footer,
           font=_fitted(d,footer,lang,490,13),fill=(160,186,201))
    return image.convert("RGB")


def render_oct20_full_mesh_review(
    *,episode_id:str,output_path:Path,
    smoke_one_second:bool=False,
)->dict:
    """Explicit full script 42/44-sec silent review OR CI-only 1-sec smoke."""
    cuts=_authored_cuts(episode_id)
    if (type(smoke_one_second) is not bool
            or not isinstance(output_path,Path)
            or output_path.suffix.lower()!=".mp4"
            or output_path.exists() or output_path.is_symlink()
            or not output_path.parent.is_dir()
            or output_path.parent.is_symlink()
            or not shutil.which("ffmpeg") or not shutil.which("ffprobe")
            or shutil.disk_usage(output_path.parent).free<250_000_000):
        _hold()
    count=FPS if smoke_one_second else TOTAL_FRAMES[episode_id]
    command=[
        "ffmpeg","-hide_banner","-v","error","-nostdin","-n",
        "-f","rawvideo","-pixel_format","rgb24",
        "-video_size",f"{WIDTH}x{HEIGHT}","-framerate",str(FPS),
        "-i","pipe:0","-an","-c:v","libx264","-pix_fmt","yuv420p",
        "-preset","ultrafast","-crf","26","-threads","2",
        "-movflags","+faststart",str(output_path),
    ]
    proc=None
    success=False
    try:
        proc=subprocess.Popen(
            command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        start=time.monotonic()
        for frame in range(count):
            if time.monotonic()-start>185:
                _hold()
            proc.stdin.write(
                draw_oct20_full_mesh_frame(episode_id,frame).tobytes()
            )
        proc.stdin.close()
        if proc.wait(timeout=30)!=0:
            _hold()
        result=subprocess.run([
            "ffprobe","-v","error","-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,nb_frames",
            "-of","json",str(output_path),
        ],stdin=subprocess.DEVNULL,capture_output=True,
          check=True,timeout=15)
        if len(result.stdout)>14000:
            _hold()
        info=json.loads(result.stdout)
        streams=info["streams"]
        if (len(streams)!=1 or streams[0].get("codec_type")!="video"
                or streams[0].get("codec_name")!="h264"
                or int(streams[0]["width"])!=WIDTH
                or int(streams[0]["height"])!=HEIGHT
                or int(streams[0]["nb_frames"])!=count
                or abs(float(info["format"]["duration"])-count/FPS)>.1
                or not 3000<output_path.stat().st_size<_MAX_FILE_BYTES):
            _hold()
        success=True
    except (OSError,ValueError,TypeError,KeyError,
            subprocess.CalledProcessError,subprocess.TimeoutExpired,
            BrokenPipeError):
        _hold()
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=8)
        if not success:
            output_path.unlink(missing_ok=True)
    return {
        "status":"SOURCE_LOCKED_7_SCENE_ORIGINAL_3D_SILENT_REVIEW_ONLY",
        "episode_id":episode_id,
        "script_total_seconds":cuts[-1].end_second,
        "render_seconds":count/FPS,
        "authored_script_scenes":len(cuts),
        "rendered_scenes":1 if smoke_one_second else len(cuts),
        "actually_rendered_3d_geometry":True,
        "mixed_3d_and_digital_illustration":True,
        "seven_distinct_visual_subjects":True,
        "real_app_demo_recorded":False,
        "all_seven_script_scenes_rendered":not smoke_one_second,
        "fps":FPS,"width":WIDTH,"height":HEIGHT,"frames":count,
        "audio_tracks":0,"photorealistic_final_video":False,
        "human_voice_recorded_or_verified":False,
        "spoken_subtitle_alignment_verified":False,
        "commercial_voice_rights_verified":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_service_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }
