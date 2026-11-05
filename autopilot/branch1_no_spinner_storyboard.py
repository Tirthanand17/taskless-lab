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
# Only the video-mode stage headline changes. Full original source sentence
# is spoken and appears ONCE in the native-timed lower caption strip. These
# three compact labels summarize source-locked verified scripted concepts.
EDITORIAL_HERO_HEADLINE={
    "voice":("FAMILIAR VOICE?", "STOP. CALL BACK.", "VERIFY THE CALLER"),
    "photo":("PHOTOS CAN REVEAL DATA", "INSPECT PHOTO DETAILS", "CHECK BEFORE SHARING"),
    "browser":("INCOGNITO IS NOT INVISIBLE", "SAVED ON YOUR DEVICE", "KNOW THE PRIVACY LIMITS"),
}

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


def _draw_subject(d,topic:str,mode:str,amount:float,colors:dict,
                  *,beat:int,total:int)->str:
    """Three DIFFERENT original hero compositions per topic; no orbit.

    The opening, proof and closing scenes have materially distinct object
    silhouettes. Changes are driven by caption index, not random effects.
    """
    if type(beat) is not int or type(total) is not int or not 0<=beat<total:
        raise NoSpinnerVisualRejected("Authored visual beat index required")
    stage=min(2,(3*beat)//total)
    ac=colors["accent"];sec=colors["secondary"]
    def label(x,y,text,n=28,col=None):
        d.text((x,y),text,font=_font(n),fill=col or sec)

    if topic=="voice" and stage==0:
        # Hook: stand-alone symbolic audio bars, NOT actual person audio.
        values=(.14,.39,.25,.66,.44,.78,.31,.94,.63,.38,.82,.29,.58,.34,.16)
        for i,v in enumerate(values):
            height=round(360*v*(.73+.27*amount))
            x=160+i*51;mid=858+round((i%2)*7)
            d.rounded_rectangle((x,mid-height//2,x+24,mid+height//2),
                                radius=8,fill=ac if i<=round(14*amount) else colors["hero"])
        label(197,1112,"SYNTHETIC VOICE EXAMPLE",24)
        d.rectangle((195,1178,195+round(678*amount),1190),fill=ac)
        variant="VOICE_WAVEFORM_HOOK"
    elif topic=="voice" and stage==1:
        # Middle: no visualized impersonation. Show the verification
        # decision as a different clearly bounded pair of action cards.
        left=round(120+40*(1-amount))
        d.rounded_rectangle((left,590,left+350,1110),radius=22,
                            fill=(69,38,60),outline=ac,width=4)
        d.rounded_rectangle((575,590,960,1110),radius=22,
                            fill=(24,58,66),outline=sec,width=4)
        label(left+36,642,"STOP",49,col=ac)
        label(left+36,737,"HANG UP",29)
        label(606,643,"VERIFY",46,col=sec)
        label(606,737,"CALL BACK",28)
        for j in range(3):
            d.rectangle((left+42,894+j*51,left+42+round(248*amount),908+j*51),fill=ac)
            d.rectangle((607,894+j*51,607+round(288*amount),908+j*51),fill=sec)
        variant="TWO_STEP_CALL_VERIFICATION"
    elif topic=="voice":
        # Final beat: confident original call-back checklist, no circle.
        d.rounded_rectangle((150,594,930,1113),radius=24,
                            fill=(31,55,72),outline=sec,width=3)
        label(197,641,"VERIFY THE CALLER",40,col=sec)
        for idx,name in enumerate(("PAUSE","USE A KNOWN NUMBER","CONFIRM DIRECTLY")):
            y=759+idx*108
            d.rounded_rectangle((190,y,252,y+58),radius=8,fill=ac)
            label(206,y+11,str(idx+1),31,col=(17,23,39))
            label(284,y+9,name,25)
        variant="VERIFIED_CALLER_CHECKLIST"
    elif topic=="photo" and stage==0:
        # Hook: photo illustration with distinct polygon landscape,
        # purely synthetic, no actual private photograph or GPS fields.
        shift=round(42*(1-amount))
        d.rounded_rectangle((158+shift,500,740+shift,1130),radius=24,
                            fill=(31,68,76),outline=ac,width=4)
        d.polygon(((188+shift,1018),(365+shift,732),(524+shift,889),
                   (625+shift,760),(705+shift,1000)),fill=(64,146,136))
        d.rectangle((188+shift,1030,704+shift,1050),fill=sec)
        d.rounded_rectangle((600,840,930,1100),radius=16,
                            fill=(11,44,55),outline=sec,width=4)
        for j,w in enumerate((242,195,267)):
            d.rectangle((625,894+j*53,625+round(w*amount),906+j*53),
                        fill=ac if j==1 else sec)
        variant="PHOTO_METADATA_DISCOVERY"
    elif topic=="photo" and stage==1:
        # Proof: info pane instead of the same photo frame; illustrates
        # the owner's original spoken "inspect information" step.
        d.rounded_rectangle((268,495,830,1228),radius=27,
                            fill=(22,60,74),outline=sec,width=4)
        d.rounded_rectangle((300,545,798,631),radius=12,fill=(30,94,100))
        label(328,570,"PHOTO INFO",29)
        for i,(word,w) in enumerate((("DATE",345),("DETAILS",290),("LOCATION",350))):
            yy=695+i*130
            label(320,yy,word,26,col=ac)
            d.rectangle((321,yy+55,321+round(w*amount),yy+70),fill=sec)
        variant="PHOTO_INFO_INSPECTOR"
    elif topic=="photo":
        # Takeaway: two separate share routes, no map-pin orbit.
        label(165,538,"BEFORE SHARING",34,col=ac)
        for i,text in enumerate(("CHECK DETAILS","CHECK SHARING")):
            yy=657+i*224
            d.rounded_rectangle((150,yy,930,yy+156),radius=20,
                                fill=(31,75,80),outline=sec,width=3)
            label(202,yy+41,text,32)
            d.rectangle((198,yy+116,198+round(657*amount),yy+126),fill=ac)
        variant="PHOTO_SHARE_SAFETY_ACTIONS"
    elif topic=="browser" and stage==0:
        # Browser hook: simple fictional window, not a brand's actual UI.
        d.rounded_rectangle((130,500,950,1135),radius=26,
                            fill=(18,44,72),outline=sec,width=3)
        d.rounded_rectangle((152,523,928,611),radius=13,fill=(34,76,107))
        d.rectangle((180,559,405,570),fill=sec)
        d.rectangle((188,670,455,955),fill=(42,91,125))
        d.rectangle((530,670,877,955),fill=(27,70,100))
        d.rectangle((194,1002,194+round(681*amount),1017),fill=ac)
        variant="PRIVATE_BROWSER_TAB_HOOK"
    elif topic=="browser" and stage==1:
        # Middle: downloaded files and bookmarks on device persist.
        label(180,543,"SAVED ON DEVICE",35,col=ac)
        for j,(word,w) in enumerate((("DOWNLOADS",540),("BOOKMARKS",460))):
            yy=669+j*225
            d.rounded_rectangle((160,yy,921,yy+157),radius=22,
                                fill=(23,61,91),outline=sec,width=3)
            label(207,yy+47,word,35)
            d.rectangle((205,yy+109,205+round(w*amount),yy+121),fill=ac)
        variant="DEVICE_SAVED_INFORMATION"
    else:
        # Final: explain a distinction with a split visual, not fake
        # anonymity or "invisible" protection guarantee.
        label(168,550,"WHAT PRIVATE MEANS",32,col=ac)
        for j,(head,detail) in enumerate((("ON DEVICE","LOCAL SESSION"),
                                          ("ON INTERNET","NOT INVISIBLE"))):
            xx=132+j*429
            d.rounded_rectangle((xx,674,xx+391,1105),radius=23,
                                fill=(24,62,95),outline=sec,width=3)
            label(xx+24,723,head,28)
            label(xx+24,825,detail,21,col=ac)
            d.rectangle((xx+30,937,xx+30+round(308*amount),956),fill=ac)
        variant="BROWSER_PRIVACY_DIFFERENCE"
    # A restrained one-shot "look here" movement ends after this source beat.
    # No continuous rotation, arc, orbit, bouncing dot or indefinitely
    # looping visual, and no animation crosses the original SRT band.
    if mode in ("cursor_focus","step_highlight","source_zoom"):
        x=180+round(660*amount)
        d.line((x,1275,x+44,1275),fill=ac,width=6)
    elif mode in ("split_compare","card_reveal","evidence_wipe"):
        d.rectangle((185,1265,185+round(700*amount),1276),fill=ac)
    else:
        d.rectangle((214,1268,214+round(535*amount),1279),fill=ac)
    return variant

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


def draw_source_keyframe(episode:dict,beat:int,phase:float,
                         *,caption_layer:str="original_source_proof",
                         hero_zoom:str="expanded"):
    """One visual beat, separate original static-preview vs burned-ASS modes.

    In an actual MP4, the original captions must be displayed by timed native
    ASS, NOT twice: never write static words in the same lower caption panel.
    """
    from PIL import Image,ImageDraw
    if caption_layer not in ("original_source_proof","timed_ass_overlay"):
        raise NoSpinnerVisualRejected("Only verified native caption rendering modes")
    if hero_zoom not in ("expanded","original"):
        raise NoSpinnerVisualRejected("Only original source or bounded focal hero layout allowed")
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
    # A spoken sentence is already displayed by the native ASS caption;
    # don't ALSO reproduce the entire sentence as a giant headline.
    # Three different fact-checked semantic title concepts align with the
    # three genuinely different opening / proof / takeaway subjects.
    scene_stage=min(2,(3*beat)//len(cues))
    headline=(EDITORIAL_HERO_HEADLINE[topic][scene_stage]
              if caption_layer=="timed_ass_overlay" else cues[beat]["source_text"])
    _text_lines(d,headline,x=82,y=306,width=900,height=184,
                font_size=51,max_lines=3,fill=(238,246,252))
    hero_variant=_draw_subject(d,topic,cues[beat]["motion_mode"],t,colors,
                              beat=beat,total=len(cues))
    # B1q3 focal visual composition: the physically inspected MP4 frame
    # leaves the main object too small. Only this bounded hero region is
    # enlarged; owner-source heading y0..494, native ASS y1410..1650,
    # quiet footer y1650..1919 and their text remain pixel-identical.
    # B1q2b's PCM-derived scene timeline and timed subtitles are untouched.
    if hero_zoom=="expanded":
        from PIL import Image
        original_hero=image.crop((88,495,992,1325))
        focal=original_hero.resize((1016,880),Image.Resampling.LANCZOS)
        d.rectangle((0,495,1079,1383),fill=colors["bg"])
        image.paste(focal,(31,500))
    # Genuine caption safe band, no art or overlays bleed into subtitles.
    d.rounded_rectangle((82,1410,998,1650),radius=16,fill=(7,14,27))
    if caption_layer=="original_source_proof":
        _text_lines(d,cues[beat]["source_text"],x=118,y=1460,width=847,
                    height=160,font_size=38,max_lines=4,fill=(246,249,253))
    # timed_ass_overlay mode reserves the SAME clean region for timed
    # captions burned into the actual encoded video, no double text.
    d.rectangle((82,1711,82+round(916*(beat+t)/len(cues)),1718),fill=accent)
    d.text((82,1785),"ORIGINAL ILLUSTRATION  •  NOT A LIVE SOFTWARE DEMO",
           font=_font(19,False),fill=sec)
    d.text((905,1785),f"{beat+1:02d}",font=_font(24),fill=accent)
    return image,{
        "status":STATUS,"episode_id":episode["id"],"beat":beat+1,
        "motion_mode":cues[beat]["motion_mode"],
        "distinct_original_visual_subject":hero_variant,
        "caption_source_sha256":cues[beat]["source_text_sha256"],
        "phase":phase,"no_circle_spinner_drawn":True,
        "caption_layer":caption_layer,
        "hero_editorial_headline":headline,
        "hero_headline_repeats_full_spoken_sentence":
            headline==cues[beat]["source_text"],
        "original_subject_focal_zoom":hero_zoom,
        "original_subject_focal_zoom_bounded_to_y495_1383":hero_zoom=="expanded",
        "timed_ass_caption_overlay_required":caption_layer=="timed_ass_overlay",
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
