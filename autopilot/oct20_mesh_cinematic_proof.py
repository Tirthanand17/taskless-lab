"""October 20: original animated 3D box meshes in a bounded offline preview.

A genuine 3D world model (vertices, face normals, camera perspective, lighting,
z ordering) is rasterized in pure Pillow, using FFmpeg only for an optional
SILENT short MP4. No Blender, pretrained/downloaded image model, copyrighted
app screenshot, real shopping price, third-party asset, network or paid service.

This is stylized original geometry, NOT photorealistic footage, an approved
narrator, a completed episode, or a real Gemini screen. No YouTube permission.
"""
from __future__ import annotations

from functools import lru_cache
from math import cos,sin,pi,sqrt
from pathlib import Path
import json
import shutil
import subprocess

from PIL import Image,ImageDraw,ImageFont,ImageFilter

from .agent_org import WorkflowError
from .oct20_silent_concept_preview import load_preview_plan,preview_spec

WIDTH=540
HEIGHT=960
FPS=24
MAX_FRAMES=96
LANES={
 "fm_20261020_short_en":{
   "lang":"en","headline":"AI AGENTS CAN ACT",
   "subline":"ONE RULE: REVIEW BEFORE APPROVAL",
   "labels":("ASK","PLAN","CHECK"),
   "lock":"HUMAN APPROVAL REQUIRED",
   "footer":"ORIGINAL 3D CONCEPT  /  SILENT UNRELEASED",
 },
 "fm_20261020_short_hi":{
   "lang":"hi","headline":"AI से काम करवाएँ?",
   "subline":"ऑर्डर से पहले खुद जाँच करें",
   "labels":("सवाल","प्लान","जाँच"),
   "lock":"अंतिम अनुमति आपकी",
   "footer":"मूल 3D अवधारणा / बिना आवाज़ / अपलोड नहीं",
 },
}
NAVY=(5,15,32)
LIGHT=(0.4,0.8,0.65)
CAM_TARGET=(0.,0.,0.)
BLUE=(32,195,238)
TEAL=(19,212,177)
WHITE=(235,247,250)


def _deny():
    raise WorkflowError("Oct20 original mesh preview is not a production export")


def _dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def _cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _unit(a):
    n=sqrt(_dot(a,a))
    if n<1e-8:
        _deny()
    return tuple(v/n for v in a)


def _rotate_y(v,theta):
    x,y,z=v
    return (x*cos(theta)+z*sin(theta),y,-x*sin(theta)+z*cos(theta))


@lru_cache(maxsize=10)
def _font(language,points):
    # Proven system paths are already installed in public CI; require RAQM
    # shaping for Hindi. No model/font download or licensed font export.
    try:
        import subprocess
        name=("Noto Sans Devanagari" if language=="hi" else "DejaVu Sans")
        fontpath=subprocess.run(
            ["fc-match","-f","%{file}",name],capture_output=True,
            text=True,check=True,timeout=4
        ).stdout.strip()
        font=ImageFont.truetype(fontpath,points,layout_engine=ImageFont.Layout.RAQM)
        return font
    except (OSError,ValueError,subprocess.SubprocessError):
        _deny()


def _fitted(draw,label,lang,max_width,max_px):
    for n in range(max_px,11,-1):
        font=_font(lang,n)
        if draw.textlength(label,font=font)<=max_width:
            return font
    _deny()


def _camera(frame):
    phase=frame/FPS
    pos=(7.0+0.75*sin(phase*0.7),
         4.35+0.3*cos(phase*0.45),
         11.2+0.65*cos(phase*0.8))
    forward=_unit(tuple(t-p for t,p in zip(CAM_TARGET,pos)))
    right=_unit(_cross(forward,(0,1,0)))
    up=_cross(right,forward)
    return pos,right,up,forward


def project_vertex(point,camera):
    pos,right,up,forward=camera
    rel=tuple(a-b for a,b in zip(point,pos))
    depth=_dot(rel,forward)
    if depth<=0.5:
        _deny()
    focal=610.0
    return (WIDTH/2+focal*_dot(rel,right)/depth,
            540-focal*_dot(rel,up)/depth,
            depth)


def mesh_cube(center,scale,rot,base,camera):
    """Six independent 3D quad faces, real world normals + diffuse light."""
    cx,cy,cz=center
    radius=scale/2
    faces=[
      ((-1,-1, 1),( 1,-1, 1),( 1, 1, 1),(-1, 1, 1)),
      (( 1,-1,-1),(-1,-1,-1),(-1, 1,-1),( 1, 1,-1)),
      (( 1,-1, 1),( 1,-1,-1),( 1, 1,-1),( 1, 1, 1)),
      ((-1,-1,-1),(-1,-1, 1),(-1, 1, 1),(-1, 1,-1)),
      ((-1, 1, 1),( 1, 1, 1),( 1, 1,-1),(-1, 1,-1)),
      ((-1,-1,-1),( 1,-1,-1),( 1,-1, 1),(-1,-1, 1)),
    ]
    face_normals=[(0,0,1),(0,0,-1),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]
    viewer=camera[0]
    out=[]
    for index,(quad,norm) in enumerate(zip(faces,face_normals)):
        corners=[]
        for v in quad:
            world=_rotate_y(tuple(t*radius for t in v),rot)
            corners.append((world[0]+cx,world[1]+cy,world[2]+cz))
        n=_rotate_y(norm,rot)
        center_face=tuple(sum(p[j] for p in corners)/4 for j in range(3))
        if _dot(n,tuple(viewer[j]-center_face[j] for j in range(3)))<=0:
            continue
        q=[project_vertex(p,camera) for p in corners]
        shade=max(.25,min(1,.36+.60*max(0,_dot(_unit(n),_unit(LIGHT)))))
        col=tuple(max(0,min(255,round(v*shade))) for v in base)
        out.append((sum(v[2] for v in q)/4,
                    tuple((int(v[0]),int(v[1])) for v in q),col,index))
    return out


def _scene_source_bound(episode_id):
    if type(episode_id) is not str or episode_id not in LANES:
        _deny()
    doc=load_preview_plan()
    spec=preview_spec(doc,episode_id)
    if (spec.kind!="short" or spec.scenes!=7 or
            spec.language!=LANES[episode_id]["lang"]):
        _deny()
    return doc


def draw_true_mesh_frame(episode_id,frame):
    if (type(frame) is not int or not 0<=frame<MAX_FRAMES
            or episode_id not in LANES):
        _deny()
    config=LANES[episode_id]
    lang=config["lang"]
    t=frame/FPS
    camera=_camera(frame)
    image=Image.new("RGB",(WIDTH,HEIGHT),NAVY)
    draw=ImageDraw.Draw(image)

    # Depth-graded cinematic glow, original generated pixels.
    glow=Image.new("RGBA",(WIDTH,HEIGHT),(0,0,0,0))
    halo=ImageDraw.Draw(glow)
    halo.ellipse((135,250,500,735),fill=(0,127,186,74))
    image=Image.alpha_composite(
        image.convert("RGBA"),glow.filter(ImageFilter.GaussianBlur(85))
    )
    draw=ImageDraw.Draw(image)
    # Ground is a perspective-projected 3D plane, not a flat screen grid.
    for k in range(-5,6):
        for a,b in (
            ((k*.65,-1.40,-4.2),(k*.65,-1.40,4.2)),
            ((-4.2,-1.40,k*.65),(4.2,-1.40,k*.65)),
        ):
            p=project_vertex(a,camera)
            q=project_vertex(b,camera)
            draw.line((p[0],p[1],q[0],q[1]),fill=(28,73,98,170),width=1)

    face_items=[]
    centers=[(-2.10,0,0),(0,.26,0),(2.10,0,0)]
    tones=[(20,114,205),(5,214,184),(52,128,238)]
    for index,(center,tone) in enumerate(zip(centers,tones)):
        offset=.16*sin(t*1.3+index)
        xyz=(center[0],center[1]+offset,center[2])
        # Truly rotated shaded six-face 3D cubic mesh.
        face_items.extend(mesh_cube(xyz,1.48,0.23+index*.22+t*(.31+index*.05),
                                    tone,camera))
    # Correct global camera-depth sorting; farthest faces drawn first.
    for _,poly,color,face in sorted(face_items,key=lambda row:-row[0]):
        draw.polygon(poly,fill=(*color,255))
        draw.line((*poly[0],*poly[1]),fill=(109,226,235,255),width=2)
        draw.line([*poly,poly[0]],fill=(*BLUE,160),width=2)

    # Three-dimensional moving energy connection, world coordinates.
    for link in range(2):
        a=centers[link]
        b=centers[link+1]
        coords=[]
        for i in range(23):
            f=i/22
            x=a[0]+(b[0]-a[0])*f
            p=(x,1.03+.20*sin(f*pi),-.36)
            coords.append(project_vertex(p,camera))
        draw.line([(v[0],v[1]) for v in coords],fill=(*TEAL,255),width=4)
        phase=(t*.62+link*.4)%1
        ix=min(21,int(phase*22))
        cx,cy,_=coords[ix]
        draw.ellipse((cx-7,cy-7,cx+7,cy+7),fill=(*WHITE,255),
                     outline=(*BLUE,255),width=3)
    # Labels are fixed HUD overlay rather than faked app imagery.
    draw.rounded_rectangle((22,18,518,90),radius=19,
                           fill=(8,24,45,235),outline=(*BLUE,180),width=2)
    draw.text((39,32),"FLOWMINUTE LAB  /  ORIGINAL 3D",
              font=_font("en",18),fill=WHITE)
    draw.text((40,66),"CONCEPT SCENE  •  NOT A REAL SHOPPING APP",
              font=_font("en",12),fill=(150,181,200))
    font=_fitted(draw,config["headline"],lang,495,36)
    draw.text((25,128),config["headline"],font=font,fill=WHITE)
    draw.text((25,190),config["subline"],
              font=_fitted(draw,config["subline"],lang,495,22),
              fill=(129,232,223))

    # Project actual world-space cube positions for the three labels.
    for idx,c in enumerate(centers):
        p=project_vertex((c[0],c[1]+1.12,c[2]),camera)
        txt=config["labels"][idx]
        f=_fitted(draw,txt,lang,125,19)
        width=int(draw.textlength(txt,font=f))
        x=max(8,min(WIDTH-width-8,p[0]-width/2))
        y=p[1]-24
        draw.text((x,y),txt,font=f,fill=(*WHITE,255))

    # Approval locked: no real-world purchase/action is claimed.
    draw.rounded_rectangle((22,769,518,877),radius=20,
                           fill=(7,29,49,241),outline=(*TEAL,255),width=2)
    draw.text((42,786),"FINAL ACTION  /  LOCKED",
              font=_font("en",18),fill=(*BLUE,255))
    draw.text((42,818),config["lock"],
              font=_fitted(draw,config["lock"],lang,454,21),
              fill=WHITE)
    draw.rounded_rectangle((26,908,514,914),radius=3,fill=(25,60,78,255))
    draw.rounded_rectangle((26,908,26+int(488*(frame+1)/MAX_FRAMES),914),
                           radius=3,fill=(*TEAL,255))
    draw.text((25,930),config["footer"],
              font=_fitted(draw,config["footer"],lang,495,13),
              fill=(173,191,210))
    return image.convert("RGB")


def render_true_mesh_excerpt(*,episode_id:str,output_path:Path,seconds:int=3):
    """Only 1..4 seconds. Single H264 silent MP4, not production media."""
    _scene_source_bound(episode_id)
    if (type(seconds) is not int or not 1<=seconds<=4
            or not isinstance(output_path,Path)
            or output_path.suffix.lower()!=".mp4"
            or output_path.exists() or output_path.is_symlink()
            or not output_path.parent.is_dir()
            or output_path.parent.is_symlink()
            or not shutil.which("ffmpeg") or not shutil.which("ffprobe")):
        _deny()
    command=["ffmpeg","-hide_banner","-v","error","-nostdin","-n",
             "-f","rawvideo","-pixel_format","rgb24",
             "-video_size",f"{WIDTH}x{HEIGHT}",
             "-framerate",str(FPS),"-i","pipe:0","-an",
             "-c:v","libx264","-preset","ultrafast","-crf","24",
             "-pix_fmt","yuv420p","-movflags","+faststart",
             str(output_path)]
    proc=None
    validated=False
    try:
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        for n in range(seconds*FPS):
            proc.stdin.write(draw_true_mesh_frame(episode_id,n).tobytes())
        proc.stdin.close()
        if proc.wait(timeout=35)!=0:
            _deny()
        result=subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height,nb_frames",
             "-of","json",str(output_path)],
            capture_output=True,text=True,check=True,timeout=12,
        )
        parsed=json.loads(result.stdout)
        tracks=parsed["streams"]
        if (len(tracks)!=1 or tracks[0].get("codec_type")!="video"
                or tracks[0].get("codec_name")!="h264"
                or int(tracks[0].get("width"))!=WIDTH
                or int(tracks[0].get("height"))!=HEIGHT
                or int(tracks[0].get("nb_frames"))!=seconds*FPS
                or abs(float(parsed["format"]["duration"])-seconds)>.1):
            _deny()
        validated=True
    except (OSError,ValueError,KeyError,TypeError,
            subprocess.CalledProcessError,subprocess.TimeoutExpired):
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        _deny()
    finally:
        # Do not keep an incomplete or misprobed output as a successful
        # render. A process can exit 0 and still output invalid media.
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        if not validated:
            output_path.unlink(missing_ok=True)
    return {
        "status":"REAL_ORIGINAL_3D_MESH_SILENT_PREVIEW_ONLY",
        "episode_id":episode_id,"seconds":seconds,
        "fps":FPS,"frames":seconds*FPS,
        "width":WIDTH,"height":HEIGHT,
        "actual_perspective_projected_3d_face_meshes":True,
        "photorealistic_footage":False,
        "complete_video_produced":False,
        "real_audio_or_voice":False,
        "rights_and_voice_identity_verified":False,
        "asr_subtitle_word_timing_verified":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }
