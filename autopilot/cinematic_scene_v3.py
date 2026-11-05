"""B4e2 ORIGINAL layered cinematic scientific scene renderer (not 3D software).

Pixel-composited 2.5D / isometric-style depth, soft physically drawn halo,
ambient light, topic-specific illustrated subject, bounded kinetic indicator
and minimal labels. All artwork is procedurally drawn and ORIGINAL.
- No external image or sound copied from user's reference.
- No real Blender/3D-engine claim; perspective is PIL 2.5D.
- No new research claims or actual human editorial/rights approval.
- No real OAuth/network, model payment, or video publisher.

This standalone art pass is first tested on native 1080x1920 and 1920x1080
under GitHub-hosted CI. It is not wired into live video until reviewed.
"""
from __future__ import annotations

import math
from pathlib import Path

PALETTE={
    "lunar_signal":{
        "bg":(8,19,37),"accent":(94,194,248),
        "secondary":(101,226,186),"label":"SPACE / SIGNAL",
    },
    "quake_energy":{
        "bg":(31,15,24),"accent":(250,162,109),
        "secondary":(246,211,146),"label":"SCIENCE / ENERGY",
    },
    "file_transfer":{
        "bg":(6,23,36),"accent":(98,217,183),
        "secondary":(116,184,235),"label":"DATA / UNITS",
    },
}
SCENE_PANEL={
    "short":(74,533,1006,1220),
    "long":(130,280,1790,720),
}
SIZES={"short":(1080,1920),"long":(1920,1080)}
STATUS="ORIGINAL_PIL_2POINT5D_TOPIC_OBJECT_MOTION_UNAPPROVED"


class CinematicSceneRejected(ValueError):
    """Source image, geometry, themes or unapproved security scope changed."""


def _lerp(a:float,b:float,t:float)->float:
    return a+(b-a)*t


def _font(n:int):
    from PIL import ImageFont
    if not 12<=n<=54:
        raise CinematicSceneRejected("Unbounded UI font")
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",n)
    except OSError:
        raise CinematicSceneRejected("Required DejaVu font not installed") from None


def _place_text(draw,xy,text,n,fill,limit):
    if not isinstance(text,str) or len(text)>45:
        raise CinematicSceneRejected("Unknown external label")
    font=_font(n)
    bounds=draw.textbbox(xy,text,font=font)
    if bounds[0]<0 or bounds[2]>limit[0] or bounds[1]<0 or bounds[3]>limit[1]:
        raise CinematicSceneRejected("2.5D scene text crosses object or safe-zone bounds")
    draw.text(xy,text,font=font,fill=fill)


def _world(area,ux,uy):
    x0,y0,x1,y1=area
    return (round(x0+(x1-x0)*ux),round(y0+(y1-y0)*uy))


def _glow(base,center,r,accent,clip):
    from PIL import Image,ImageDraw,ImageFilter
    a=Image.new("RGBA",base.size,(0,0,0,0))
    d=ImageDraw.Draw(a)
    x,y=center
    d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,83))
    a=a.filter(ImageFilter.GaussianBlur(max(18,round(r*.25))))
    base.alpha_composite(a.crop(clip),dest=clip[:2])


def _disc(d,x,y,r,primary,rim,phase):
    """Layered Lambert-like sphere: radial rings give depth without 3D assets."""
    d.ellipse((x-r+10,y-r+17,x+r+15,y+r+25),fill=(5,12,22,155))
    for ring in range(r,6,-4):
        edge=max(0,min(1,ring/max(r,1)))
        lit=.50+.50*(1-edge)
        shift=int(phase*18)
        col=tuple(max(0,min(255,int(v*lit+shift))) for v in primary)
        d.ellipse((x-ring,y-ring,x+ring,y+ring),fill=(*col,255))
    d.arc((x-r+8,y-r+8,x+r-8,y+r-8),235,344,fill=(*rim,235),width=5)


def _moon_scene(art,area,tick,accent,secondary,scene_index):
    from PIL import ImageDraw
    d=ImageDraw.Draw(art)
    x0,y0,x1,y1=area
    w,h=x1-x0,y1-y0
    cy=round(y0+h*.52)
    earth_x=round(x0+w*.28)
    moon_x=round(x0+w*.78)
    r_earth=round(min(w*.18,h*.25))
    r_moon=round(r_earth*.52)
    _disc(d,earth_x,cy,r_earth,(23,111,174),accent,tick/120-.5)
    _disc(d,moon_x,cy-21,r_moon,(170,183,191),(244,244,246),tick/150)
    for s in ((-26,-9,9),(17,13,14),(12,-24,7)):
        xx=moon_x+s[0]*r_moon/45
        yy=cy-21+s[1]*r_moon/45
        rr=s[2]*r_moon/45
        d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(126,146,161,215))
    # Bright progress pulse continuously sweeps from Earth to Moon.
    sx=earth_x+r_earth+18
    ex=moon_x-r_moon-19
    d.line((sx,cy,ex,cy-17),fill=(*secondary,128),width=4)
    for i in range(5):
        x=_lerp(sx,ex,i/4)
        y=_lerp(cy,cy-17,i/4)
        d.ellipse((x-4,y-4,x+4,y+4),fill=(*secondary,175))
    pos=tick/120
    px=_lerp(sx,ex,pos)
    py=_lerp(cy,cy-17,pos)
    d.ellipse((px-14,py-14,px+14,py+14),
              fill=(*accent,240),outline=(242,250,255,255),width=3)
    _place_text(d,(earth_x-r_earth+25,cy+r_earth+17),"EARTH",
                20,(223,237,245,255),(x1,y1))
    _place_text(d,(moon_x-r_moon+4,cy+r_moon+12),"MOON",
                20,(223,237,245,255),(x1,y1))
    return "ORBIT_SIGNAL_2POINT5D"


def _quake_scene(art,area,tick,accent,secondary,scene_index):
    from PIL import ImageDraw
    d=ImageDraw.Draw(art)
    x0,y0,x1,y1=area
    w,h=x1-x0,y1-y0
    floor=int(y0+h*.82)
    tops=(.20,.41,.63)
    width=round(w*.15)
    centers=[x0+round(w*f) for f in (.23,.48,.74)]
    for n,(cx,ratio) in enumerate(zip(centers,tops)):
        height=round(h*ratio)
        start=floor-height
        dx=round(width*.20)
        dy=round(width*.09)
        bright=scene_index%3==n
        topcolor=tuple(min(255,int(c*(1.13 if bright else .91))) for c in accent)
        front=tuple(max(0,int(c*(.95 if bright else .59))) for c in accent)
        side=tuple(max(0,int(c*.46)) for c in accent)
        d.polygon([(cx,start),(cx+width,start),(cx+width+dx,start-dy),
                   (cx+dx,start-dy)],fill=(*topcolor,255))
        d.polygon([(cx+width,start),(cx+width+dx,start-dy),
                   (cx+width+dx,floor-dy),(cx+width,floor)],fill=(*side,255))
        d.rectangle((cx,start,cx+width,floor),fill=(*front,255))
        d.line((cx+5,start+5,cx+5,floor-5),
               fill=(*secondary,190),width=4)
        _place_text(d,(cx+25,floor+14),f"M{5+n}",20,
                    (237,235,233,255),(x1,y1))
    d.line((x0+50,floor+5,x1-50,floor+5),fill=(*secondary,150),width=3)
    # A rising energy glint is coupled to tick, not a random shake animation.
    px=_lerp(centers[0],centers[2]+width, tick/120)
    d.ellipse((px-8,floor-14,px+8,floor+2),fill=(*secondary,240))
    return "ORIGINAL_ISOMETRIC_MAGNITUDE_ENERGY_BARS"


def _data_scene(art,area,tick,accent,secondary,scene_index):
    from PIL import ImageDraw
    d=ImageDraw.Draw(art)
    x0,y0,x1,y1=area
    w,h=x1-x0,y1-y0
    # Laptop screen and slanted keyboard: original block perspective.
    left=round(x0+w*.16)
    top=round(y0+h*.17)
    right=round(x0+w*.83)
    bottom=round(y0+h*.63)
    bezel=round(min(w,h)*.036)
    d.rounded_rectangle((left+10,top+13,right+16,bottom+22),
                        radius=bezel,fill=(4,10,19,200))
    d.rounded_rectangle((left,top,right,bottom),radius=bezel,
                        fill=(38,63,74,255),outline=(144,183,201,255),
                        width=5)
    d.rounded_rectangle((left+19,top+19,right-19,bottom-20),
                        radius=round(bezel*.4),fill=(7,29,44,255))
    # Bits sequentially highlight across the screen like a packet.
    active=(tick//15+scene_index)%8
    for i in range(8):
        a=left+33+i*(right-left-66)/8
        x=round(a)
        y=round(top+(bottom-top)*.40)
        sw=round((right-left-72)/9)
        d.rounded_rectangle((x,y,x+sw,y+round(h*.13)),
                            radius=8,fill=(*accent,245) if i==active else (31,69,83,255),
                            outline=(*secondary,160),width=2)
        _place_text(d,(x+8,y+9),str((i+scene_index)%2),
                    20,(4,20,31,255) if i==active else (235,249,245,255),
                    (x+sw+15,y+round(h*.13)+3))
    d.polygon([(left-42,bottom+14),(right+30,bottom+14),
               (right+83,bottom+60),(left-82,bottom+60)],
              fill=(87,105,119,255))
    d.polygon([(left+15,bottom+22),(right-18,bottom+22),
               (right+7,bottom+43),(left-7,bottom+43)],
              fill=(19,37,53,255))
    # An original user-interface data transfer loading indicator.
    meter=(left+32,round(y0+h*.81),right-34,round(y0+h*.84))
    d.rounded_rectangle(meter,radius=10,fill=(28,56,70,255))
    width=round((meter[2]-meter[0])*(.10+.84*tick/120))
    d.rounded_rectangle((meter[0],meter[1],meter[0]+width,meter[3]),
                        radius=8,fill=(*accent,242))
    return "PERSPECTIVE_LAPTOP_BIT_PACKET_TRANSFER"


def paint_original_premium_scene(
    image, *,
    theme:str,kind:str,scene_index:int,scene_count:int,tick:int
)->dict:
    from PIL import Image,ImageDraw
    if (theme not in PALETTE or kind not in SCENE_PANEL
        or type(scene_index) is not int or type(scene_count) is not int
        or not 0<=scene_index<scene_count<=24
        or type(tick) is not int or not 0<=tick<=120):
        raise CinematicSceneRejected("Unapproved source theme or motion step")
    if not isinstance(image,Image.Image) or image.mode!="RGB" or image.size!=SIZES[kind]:
        raise CinematicSceneRejected("Expected exact original RGB native video frame")
    x0,y0,x1,y1=SCENE_PANEL[kind]
    if x1-x0<500 or y1-y0<300:
        raise CinematicSceneRejected("Panel too small for any legible foreground")
    palette=PALETTE[theme]
    accent=palette["accent"]
    secondary=palette["secondary"]
    original=image.copy()
    # Original clean studio panel with deep glowing backing and raised surface.
    output=image.convert("RGBA")
    cx=(x0+x1)//2; cy=(y0+y1)//2
    d=ImageDraw.Draw(output)
    d.rounded_rectangle((x0+17,y0+24,x1+17,y1+24),
                        radius=31,fill=(1,6,13,255))
    d.rounded_rectangle((x0,y0,x1,y1),
                        radius=31,fill=(*palette["bg"],255),
                        outline=(*accent,140),width=3)
    # Top and bottom boundaries have physically constrained margin.
    d.line((x0+35,y0+79,x1-35,y0+79),fill=(*accent,70),width=2)
    d.line((x0+35,y1-82,x1-35,y1-82),fill=(*accent,65),width=2)
    # Glow is clipped inside content pane: never alter source-title or caption
    # pixels beyond the dedicated art window.
    inner=(x0+45,y0+95,x1-43,y1-110)
    _glow(output,(cx,cy),round((x1-x0)*.42),accent,inner)
    _place_text(d,(x0+40,y0+26),palette["label"],22,
                (*accent,255),(x1-150,y0+73))
    _place_text(d,(x1-134,y0+26),f"{scene_index+1:02}/{scene_count:02}",
                19,(205,215,228,255),(x1-20,y0+72))
    layer=Image.new("RGBA",output.size,(0,0,0,0))
    if theme=="lunar_signal":
        art=_moon_scene(layer,inner,tick,accent,secondary,scene_index)
    elif theme=="quake_energy":
        art=_quake_scene(layer,inner,tick,accent,secondary,scene_index)
    else:
        art=_data_scene(layer,inner,tick,accent,secondary,scene_index)
    output.alpha_composite(layer)
    result=output.convert("RGB")
    # NEVER touch subtitle band; it is masked separately in the final stage.
    caption_top=1295 if kind=="short" else 756
    from PIL import ImageChops
    if ImageChops.difference(
       result.crop((0,caption_top,image.width,image.height)),
       original.crop((0,caption_top,image.width,image.height))
    ).getbbox():
        raise CinematicSceneRejected("Dimensional original illustration escaped caption safe area")
    image.paste(result)
    return {
        "status":STATUS,
        "theme":theme,
        "scene_index":scene_index,
        "tick":tick,
        "original_dimensional_object":art,
        "actual_new_editorial_facts_introduced":False,
        "reference_clip_assets_copied":False,
        "human_visual_review_completed":False,
        "release_authorized":False,
    }


def render_real_source_scene_preview_set(output_dir:Path)->dict:
    """Actually draw 3 distinct source-linked 1080p/landscape preview PNGs.

    No video/TTS runner cost and no unreviewed content/rights approval. This
    reads the SAME fixed authored NASA/NIST/USGS storyboards already in repo,
    preserving their semantic title and value. Meant for PR visual critique.
    """
    import io
    from hashlib import sha256
    import cairosvg
    from PIL import Image
    from autopilot.primary_sourced_storyboards import build_story,render_original_svg

    folder=Path(output_dir)
    if not folder.is_absolute() or folder.exists() or folder.is_symlink():
        raise CinematicSceneRejected("Use NEW absolute original storyboard preview folder")
    records=[]
    folder.mkdir(parents=True,mode=0o700)
    for slot in ("short_am","long","short_pm"):
        story=build_story(slot)
        svg=render_original_svg(story,0,60)
        im=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode("utf8"))))
        im=im.convert("RGB")
        proof=paint_original_premium_scene(im,theme=story["theme"],
            kind=story["format"],scene_index=0,
            scene_count=story["scene_count"],tick=60)
        if proof["reference_clip_assets_copied"] or proof["release_authorized"]:
            raise CinematicSceneRejected("Review art cannot import reference or authorize release")
        filename=f"{slot}_UNAPPROVED_ORIGINAL_CINEMATIC_SCENE.png"
        target=folder/filename
        im.save(target,format="PNG",optimize=True)
        data=target.read_bytes()
        if len(data)<40000:
            raise CinematicSceneRejected("Blank or undersized original illustrated scene")
        records.append({
            "slot":slot,"format":story["format"],
            "source_story_draft_sha256":story["draft_sha256"],
            "theme":story["theme"],"file":filename,
            "bytes":len(data),"sha256":sha256(data).hexdigest(),
            "actual_human_approved":False,"youtube_upload_enabled":False,
        })
    return {
        "status":STATUS,
        "prototypes":records,
        "public_repository_fixtures_only":True,
        "actual_3d_modeling_claimed":False,
        "owner_human_watch_listen_fact_rights_approved":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


if __name__=="__main__":
    import argparse,json
    parser=argparse.ArgumentParser(description="Original 2.5D scene previews, no video upload")
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    print(json.dumps(render_real_source_scene_preview_set(a.out),sort_keys=True))
