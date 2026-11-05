"""B1q1 original Short scene redesign WITHOUT rotating-circle template artifacts.

Review-only keyframe PNGs from exact GitHub episode caption/source text.
NO artificial GUI app endorsement, no owner's reference clip, no copying
someone else's film or voice. This is a *candidate*, not an encoded YouTube
replacement. Real video, true 30fps movement, original author approval,
caption alignment, narration licenses and remote schedule remain separate.

The repeated central circular orbit is categorically absent. Every
animated effect is finite, authored from a distinct shot mode, and finishes
within its own caption's measured voice window. No infinite spinner loop.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import json
import math

STATUS="B1Q1_NO_REPEAT_CIRCLE_ORIGINAL_STORYBOARD_NOT_FULL_VIDEO_UNAPPROVED"
SIZE=(1080,1920)
MODES=("cursor_focus","split_compare","evidence_wipe","card_reveal",
       "step_highlight","row_scan","source_zoom","brief_callout")
COLORS={
    "voice": {"bg":(13,18,35),"accent":(253,151,167),"hero":(79,37,62),
              "secondary":(252,216,196),"tag":"VOICE SAFETY"},
    "photo": {"bg":(7,25,35),"accent":(110,226,186),"hero":(25,69,77),
              "secondary":(184,239,245),"tag":"PHOTO PRIVACY"},
    "browser":{"bg":(10,20,42),"accent":(130,196,245),"hero":(24,53,84),
               "secondary":(208,236,248),"tag":"BROWSER PRIVACY"},
}
FONT_B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

class NoSpinnerVisualRejected(ValueError):
    pass


def _theme(episode:dict)->str:
    eid=episode.get("id","")
    if not isinstance(eid,str):
        raise NoSpinnerVisualRejected("Episode ID missing")
    if "voice" in eid:
        return "voice"
    if "photo" in eid:
        return "photo"
    if "incognito" in eid or "browser" in eid:
        return "browser"
    raise NoSpinnerVisualRejected("No matching original visual concept yet")


def _verify_caption_source(episode:dict)->list[dict]:
    if type(episode) is not dict or episode.get("type")!="short":
        raise NoSpinnerVisualRejected("Only source-authored Shorts allowed")
    _theme(episode)
    cues=episode.get("captions")
    if type(cues) is not list or not 5<=len(cues)<=30:
        raise NoSpinnerVisualRejected("Need original timed full-language caption beats")
    previous=0.0
    for j,cue in enumerate(cues):
        if type(cue) is not dict:
            raise NoSpinnerVisualRejected("Source caption is not object")
        a,b,text=cue.get("start"),cue.get("end"),cue.get("text")
        if (type(a) not in (int,float) or type(b) not in (int,float)
            or not all(math.isfinite(v) for v in (a,b))
            or a<0 or a<previous-.001 or b<=a or b-a>15
            or type(text) is not str or not 5<=len(text.strip())<=240):
            raise NoSpinnerVisualRejected("Untrusted caption time, text or overlap")
        previous=b
    return cues


def _font(n:int,bold=True):
    from PIL import ImageFont
    return ImageFont.truetype(FONT_B if bold else FONT_R,n)


def _wrap(draw,text,*,max_width,max_lines,max_font,min_font=26):
    if type(text) is not str or not text.strip() or len(text)>240:
        raise NoSpinnerVisualRejected("Blank/out-of-source or oversized text")
    for fs in range(max_font,min_font-1,-2):
        f=_font(fs)
        lines=[]
        line=""
        for word in text.strip().split():
            trial=(line+" "+word).strip()
            if draw.textbbox((0,0),trial,font=f)[2]<=max_width:
                line=trial
            else:
                if line:
                    lines.append(line)
                line=word
        if line:
            lines.append(line)
        if (len(lines)<=max_lines
            and all(draw.textbbox((0,0),x,font=f)[2]<=max_width for x in lines)):
            return lines,f,fs
    raise NoSpinnerVisualRejected("Refuse truncation or unsafe text overflow")


def _text_lines(draw,text,*,x,y,width,height,font_size,max_lines,fill):
    # Fit BOTH actual glyph width and the reserved physical video height;
    # never truncate source caption words or let text cross the hero boundary.
    for requested in range(font_size,25,-2):
        lines,font,fs=_wrap(draw,text,max_width=width,max_lines=max_lines,
                            max_font=requested)
        stride=int(fs*1.26)
        if len(lines)*stride<=height:
            break
    else:
        raise NoSpinnerVisualRejected("Source words would overlap other video regions")
    for j,line in enumerate(lines):
        draw.text((x,y+stride*j),line,font=font,fill=fill)
    return {"lines":lines,"text_sha256":sha256(text.encode()).hexdigest(),
            "rect":[x,y,x+width,y+len(lines)*stride]}


def _ease(value:float)->float:
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:
        raise NoSpinnerVisualRejected("Motion phase outside bounded shot")
    return value*value*(3-2*value)


def _draw_subject(d,scene:str,mode:str,amount:float,colors:dict):
    """Only original rectangular evidence/illustration assets, never circles."""
    ac=colors["accent"];sec=colors["secondary"];bg=colors["bg"]
    # Free-standing objects, not a recurring giant outer presentation box.
    if scene=="voice":
        # Synthetic audio waveform: variable HEIGHT bars with moving focus,
        # not a voice fingerprint, biometric signature or real call recording.
        n=15
        values=(.14,.39,.25,.66,.44,.78,.31,.94,.63,.38,.82,.29,.58,.34,.16)
        for i,v in enumerate(values):
            height=round(330*v*(.73+.27*amount))
            x=160+i*51
            mid=855+round((i%2)*7)
            d.rounded_rectangle((x,mid-height//2,x+24,mid+height//2),
                                radius=8,fill=ac if i<=round(14*amount) else colors["hero"])
        d.rounded_rectangle((190,1130,890,1210),radius=19,
                            fill=(31,51,67),outline=sec,width=3)
        d.rectangle((225,1163,225+round(600*amount),1177),fill=ac)
    elif scene=="photo":
        # Source-neutral photo card + rectangular metadata fields, no GPS
        # coordinates invented or real location/photograph copied.
        shift=round(42*(1-amount))
        d.rounded_rectangle((158+shift,500,720+shift,1130),radius=24,
                            fill=(31,68,76),outline=ac,width=4)
        d.polygon(((188+shift,1018),(365+shift,732),(524+shift,889),
                   (625+shift,760),(684+shift,1000)),fill=(64,146,136))
        d.rectangle((188+shift,1030,686+shift,1050),fill=sec)
        d.rounded_rectangle((568,838,916,1095),radius=16,
                            fill=(11,44,55),outline=sec,width=4)
        for i,w in enumerate((250,200,280)):
            d.rounded_rectangle((590,891+i*53,590+round(w*amount),905+i*53),
                                radius=4,fill=ac if i==1 else sec)
    else:
        # Educational original *fictional* browser tabs and privacy layers.
        # Rectangular track and switching panels signal device vs network.
        d.rounded_rectangle((115,515,965,1150),radius=30,
                            fill=(18,44,72),outline=sec,width=3)
        d.rounded_rectangle((136,538,944,618),radius=15,
                            fill=(34,76,107))
        d.rectangle((165,575,390,585),fill=sec)
        d.rectangle((165,676,435,950),fill=(42,91,125))
        d.rectangle((521,676,894,950),fill=(27,70,100))
        d.rectangle((175,987,175+round(705*amount),1005),fill=ac)
        for i in range(3):
            d.rounded_rectangle((551,718+i*67,553+round((255-i*45)*amount),739+i*67),
                                radius=6,fill=sec)
    # A single restrained highlight varies by shot type. It is bounded,
    # does not circle anything and cannot run beyond the scene.
    if mode in ("cursor_focus","step_highlight","source_zoom"):
        x=180+round(660*amount)
        d.line((x,1260,x+56,1260),fill=ac,width=7)
    elif mode in ("split_compare","card_reveal","evidence_wipe"):
        d.rectangle((185,1251,185+round(700*amount),1262),fill=ac)
    elif mode in ("row_scan","brief_callout"):
        d.rounded_rectangle((210,1254,210+round(540*amount),1267),
                            radius=6,fill=ac)


def storyboard_cues(episode:dict)->list[dict]:
    cues=_verify_caption_source(episode)
    topic=_theme(episode)
    shift={"voice":0,"photo":2,"browser":5}[topic]
    plan=[]
    for j,c in enumerate(cues):
        mode=MODES[(j+shift)%len(MODES)]
        if plan and plan[-1]["motion_mode"]==mode:
            raise NoSpinnerVisualRejected("Repeated templated motion style")
        plan.append({
            "beat":j+1,"source_text":c["text"],
            "source_text_sha256":sha256(c["text"].encode()).hexdigest(),
            "start_seconds":c["start"],"end_seconds":c["end"],
            "motion_mode":mode,"duration_seconds":round(c["end"]-c["start"],3),
            "no_circle_arc_or_spinner":True,
            "unbounded_repeat_count":0,
            "owner_approved":False,
        })
    return plan


def draw_source_keyframe(episode:dict,beat:int,phase:float):
    from PIL import Image,ImageDraw
    cues=storyboard_cues(episode)
    if type(beat) is not int or not 0<=beat<len(cues):
        raise NoSpinnerVisualRejected("Unrecognized original beat")
    t=_ease(phase)
    topic=_theme(episode)
    colors=COLORS[topic]
    image=Image.new("RGB",SIZE,colors["bg"])
    d=ImageDraw.Draw(image)
    accent=colors["accent"];sec=colors["secondary"]
    # Ultra quiet brand header, not user reference product branding.
    d.text((82,74),"FLOWMINUTE  /  ORIGINAL EXPLAINER",
           font=_font(28),fill=sec)
    d.rectangle((82,135,998,138),fill=tuple(int(v*.44) for v in accent))
    d.text((82,222),colors["tag"],font=_font(31),fill=accent)
    _text_lines(d,cues[beat]["source_text"],x=82,y=306,width=900,height=184,
                font_size=51,max_lines=3,fill=(238,246,252))
    _draw_subject(d,topic,cues[beat]["motion_mode"],t,colors)
    # Genuine caption safe band, no art or overlays bleed into subtitles.
    d.rounded_rectangle((82,1410,998,1650),radius=16,fill=(7,14,27))
    _text_lines(d,cues[beat]["source_text"],x=118,y=1460,width=847,
                height=160,font_size=38,max_lines=4,fill=(246,249,253))
    d.rectangle((82,1711,82+round(916*(beat+t)/len(cues)),1718),fill=accent)
    d.text((82,1785),"ORIGINAL ILLUSTRATION  •  NOT A LIVE SOFTWARE DEMO",
           font=_font(19,False),fill=sec)
    d.text((905,1785),f"{beat+1:02d}",font=_font(24),fill=accent)
    return image,{
        "status":STATUS,"episode_id":episode["id"],"beat":beat+1,
        "motion_mode":cues[beat]["motion_mode"],
        "caption_source_sha256":cues[beat]["source_text_sha256"],
        "phase":phase,"no_circle_spinner_drawn":True,
        "original_recording_or_reference_reused":False,
        "full_video_encoded":False,
        "human_approved":False,"youtube_uploaded":False,
    }


def render_three_source_shorts(source_root:Path,out:Path)->dict:
    root=Path(source_root);out=Path(out)
    if not root.is_dir() or not out.is_absolute() or out.exists() or out.is_symlink():
        raise NoSpinnerVisualRejected("Need clean GitHub checkout and fresh absolute CI output")
    out.mkdir(mode=0o700,parents=True)
    samples=[]
    for eid in (
        "fm_20261105_ai_voice_cloning_callback_short_en",
        "fm_20261106_photo_gps_metadata_short_en",
        "fm_20261107_incognito_not_invisible_short_en",
    ):
        path=root/"content"/"episodes"/f"{eid}.json"
        if not path.is_file() or path.is_symlink():
            raise NoSpinnerVisualRejected("Source schedule manifest missing from GitHub")
        episode=json.loads(path.read_text(encoding="utf8"))
        plan=storyboard_cues(episode)
        indices=sorted(set((0,len(plan)//2,len(plan)-1)))
        for idx in indices:
            for phase in (0.20,0.82):
                im,receipt=draw_source_keyframe(episode,idx,phase)
                name=f"{eid}_beat_{idx+1:02d}_phase_{int(phase*100):02d}_UNAPPROVED.png"
                target=out/name
                im.save(target,optimize=True)
                item={
                    "file":name,"bytes":target.stat().st_size,
                    "sha256":sha256(target.read_bytes()).hexdigest(),
                    **receipt,
                }
                if item["bytes"]<10000:
                    raise NoSpinnerVisualRejected("Original keyframe unexpectedly blank")
                samples.append(item)
    manifest={
        "status":STATUS,
        "total_original_physical_png_keyframes":len(samples),
        "episodes":3,
        "source_github_only":True,
        "exact_original_animation_project_in_repo":False,
        "video_or_audio_replacement_encoded":False,
        "youtube_upload_enabled":False,
        "owner_full_watch_listen_and_rights_approved":False,
        "reference_video_or_voice_cloned":False,
        "items":samples,
    }
    (out/"UNAPPROVED_NO_SPINNER_SCENE_MANIFEST.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return manifest


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description="Original static storyboard, NO spinner, NO upload")
    parser.add_argument("--repository",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=render_three_source_shorts(args.repository,args.output)
    print(json.dumps({"status":result["status"],
                      "physical_png_count":len(result["items"]),
                      "actual_uploaded_videos":0}))
