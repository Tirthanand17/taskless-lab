"""B4e3 original source-driven science shot composition for BOTH video formats.

Adds actual story-varying, source-linked visual objects inside B4e2's
2.5D lit window, preserving B4e1's independent portrait/landscape caption
zone. Not a claim of Blender/3D photorealism, factual human approval or
licensed third-party reference material.

All visible value text comes ONLY from the already checked public fixed
NASA/NIST/USGS authored draft; no fresh claim generation or network.
"""
from __future__ import annotations

from hashlib import sha256
from autopilot.cinematic_scene_v3 import (
    paint_original_premium_scene,PALETTE,SCENE_PANEL,CinematicSceneRejected,
)
from autopilot.primary_sourced_storyboards import require_exact_draft

STATUS="B4E3_THREE_STORY_FORMATS_ORIGINAL_SOURCE_OBJECT_SHOTS_UNAPPROVED"

def _font(size):
    from PIL import ImageFont
    if type(size) is not int or not 14<=size<=48:
        raise CinematicSceneRejected("Caption/source UI font outside measured bounds")
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",size)
    except OSError:
        raise CinematicSceneRejected("Original source shot DejaVu font missing") from None


def _source_label(draw,xy,text,bound_right,bound_bottom,accent,size=27):
    if not isinstance(text,str) or not text or len(text)>90:
        raise CinematicSceneRejected("Unsigned or empty source scene label")
    for n in range(size,13,-1):
        face=_font(n)
        b=draw.textbbox(xy,text,font=face)
        if b[0]>=0 and b[1]>=0 and b[2]<=bound_right and b[3]<=bound_bottom:
            draw.text(xy,text,font=face,fill=accent)
            return n
    raise CinematicSceneRejected("Source metadata does not fit actual native art window")


def _inner(rect):
    x0,y0,x1,y1=rect
    return (x0+46,y0+98,x1-44,y1-112)


def _shade_region(draw,inner,palette):
    # Replace the prototype's default object *inside* the unchanged frame
    # when a different source-scene object tells the story more effectively.
    # No wipe/mask can ever extend beyond the strictly measured image window.
    x0,y0,x1,y1=inner
    draw.rounded_rectangle(inner,radius=20,
        fill=(*palette["bg"],255) if draw.mode=="RGBA" else palette["bg"])


def _source_signal_path(draw,inner,tick,accent,large=False):
    """Three finite, horizontal information paths; NO rotating circles/orbit.

    Each phase reveals at most one source-bound progress pass from 0 to 120.
    There is no 360-degree modulo, ring stroke, orbital dot or periodic
    animation that can repeat across different spoken scenes.
    """
    x0,y0,x1,y1=inner
    width,height=x1-x0,y1-y0
    left=x0+round(width*.14)
    right=x1-round(width*.12)
    span=right-left
    for index,ratio in enumerate((.30,.50,.70) if large else (.33,.50,.67)):
        mid=y0+round(height*ratio)
        shadow=tuple(max(0,int(v*.31)) for v in accent)
        draw.rounded_rectangle((left,mid-12,right,mid+12),
                               radius=9,fill=shadow)
        # Single finite left-to-right reveal, not a continuously cycling UI.
        amount=max(0,min(1,(tick/120-index*.14)/(1-index*.14)))
        fill_end=left+round(span*amount)
        if fill_end>left:
            draw.rounded_rectangle((left,mid-7,fill_end,mid+7),
                                   radius=6,fill=accent)
        # Rectangular endpoint communicates a measurable stop, not a loader.
        cursor=max(left,min(right,fill_end))
        draw.rounded_rectangle((cursor-5,mid-21,cursor+5,mid+21),
                               radius=3,fill=accent)


def _data_variant(draw,inner,variant,tick,pal):
    x0,y0,x1,y1=inner
    w,h=x1-x0,y1-y0
    accent=pal["accent"]
    secondary=pal["secondary"]
    if variant==1:
        # Stack of original dimensional file sheets, data-value not brand.
        for n in range(3):
            dx=n*round(w*.066)
            dy=n*round(h*.055)
            px=x0+round(w*.17)+dx
            py=y0+round(h*.16)+dy
            width=round(w*.45)
            height=round(h*.59)
            draw.polygon([(px,py),(px+width,py),(px+width+18,py-17),
                          (px+18,py-17)],fill=accent if n==2 else (56,96,119))
            draw.rounded_rectangle((px,py,px+width,py+height),radius=17,
                                   fill=(19+12*n,37+14*n,57+11*n),
                                   outline=secondary,width=3)
            for j in range(3):
                ty=py+round(height*(.36+.14*j))
                draw.rounded_rectangle((px+29,ty,px+width-36,ty+8),radius=3,
                                       fill=(63,110,132))
        _source_label(draw,(x0+round(w*.69),y0+round(h*.35)),
                      "DATA",x1-14,y1-20,accent,29)
    elif variant==2:
        # Two independent conceptual quantities in perspective cards.
        top=y0+round(h*.23)
        width=round(w*.36)
        for i,(name,fill) in enumerate((("Mb",secondary),("MB",accent))):
            px=x0+round(w*(.12+.42*i))
            draw.rounded_rectangle((px+10,top+13,px+width+10,top+round(h*.50)+13),
                                   radius=18,fill=(5,16,25))
            draw.rounded_rectangle((px,top,px+width,top+round(h*.50)),
                                   radius=18,fill=(17,41,59),
                                   outline=fill,width=5)
            _source_label(draw,(px+35,top+round(h*.18)),name,
                          px+width-10,top+round(h*.42),fill,42)
    elif variant==3:
        # Progression path is expressly an illustrative unit conversion.
        cy=y0+round(h*.49)
        sx=x0+round(w*.12)
        ex=x0+round(w*.87)
        draw.line((sx,cy,ex,cy),fill=secondary,width=6)
        for idx,word in enumerate(("BITS","BYTES","UNITS")):
            cx=round(sx+(ex-sx)*idx/2)
            active=idx==round(tick/60)
            r=round(min(h,w)*.095)
            draw.ellipse((cx-r,cy-r,cx+r,cy+r),
                        fill=accent if active else (26,71,86),
                        outline=secondary,width=4)
            _source_label(draw,(cx-r+11,cy+r+14),word,
                          min(x1,cx+r+54),y1-10,secondary,18)
    else:
        # Source-independent numeric visualization: moving columns + scan.
        base=y0+round(h*.78)
        for i,ratio in enumerate((.19,.48,.34,.67,.29,.58,.44)):
            px=x0+round(w*(.10+.116*i))
            val=.1+.9*(tick/120)
            height=round(h*(ratio*(.85+.15*val)))
            draw.rounded_rectangle((px,base-height,px+round(w*.074),base),
                                   radius=8,fill=accent if i==round(6*tick/120)
                                   else (30,81,97))
        draw.line((x0+35,base+4,x1-35,base+4),fill=secondary,width=3)


def _moon_variant(draw,inner,variant,tick,pal):
    accent=pal["accent"]
    secondary=pal["secondary"]
    if variant in (1,2,4):
        _source_signal_path(draw,inner,tick,accent,large=True)
        x0,y0,x1,y1=inner
        if variant==1:
            _source_label(draw,(x0+37,y0+28),"EARTH — MOON",
                          x1-30,y0+67,secondary,29)
        elif variant==2:
            _source_label(draw,(x0+37,y0+28),"RADIO SIGNAL",
                          x1-30,y0+67,secondary,29)
        else:
            _source_label(draw,(x0+37,y0+28),"RETURN TRIP",
                          x1-30,y0+67,secondary,29)
    elif variant in (3,5):
        # Former radial hand was an unrelated scanner-like moving dial.
        # Replace with an explicit, non-looping four-stage linear journey.
        x0,y0,x1,y1=inner
        width,height=x1-x0,y1-y0
        left=x0+round(width*.12)
        right=x1-round(width*.12)
        cy=y0+round(height*.51)
        n=4
        cell=round((right-left)/(n*1.18))
        for i in range(n):
            x=left+round((right-left-cell)*i/(n-1))
            seen=tick >= (i+1)*24
            draw.rounded_rectangle((x+6,cy-42,x+cell+6,cy+48),
                                   radius=13,fill=(6,23,37))
            draw.rounded_rectangle((x,cy-51,x+cell,cy+35),
                                   radius=13,fill=(25,73,89) if not seen else (35,112,119),
                                   outline=accent if seen else secondary,width=4)
            draw.rounded_rectangle((x+17,cy-8,x+cell-17,cy+3),
                                   radius=4,fill=accent if seen else secondary)


def _quake_variant(draw,inner,variant,tick,pal):
    accent=pal["accent"]
    secondary=pal["secondary"]
    if variant in (1,3,5):
        x0,y0,x1,y1=inner
        import math
        cy=round(y0+(y1-y0)*.5)
        points=[]
        for i in range(201):
            x=x0+round((x1-x0)*i/200)
            t=i/200
            envelope=max(0,math.sin(math.pi*t))**2
            amp=round((y1-y0)*.32*envelope)
            y=cy+round(amp*math.sin(23*math.pi*t+tick*math.pi/60))
            points.append((x,y))
        draw.line(points,fill=secondary,width=5,joint="curve")
        cursor=round(x0+(x1-x0)*tick/120)
        draw.line((cursor,y0+24,cursor,y1-35),fill=accent,width=3)
    elif variant in (2,4):
        _source_signal_path(draw,inner,tick,accent)


def paint_source_story_scene(image,*,story:dict,scene_index:int,tick:int)->dict:
    """Compose one actual script beat as original image with no caption intrusion."""
    require_exact_draft(story)
    if (type(scene_index) is not int or type(tick) is not int
        or not 0<=scene_index<story["scene_count"] or not 0<=tick<=120):
        raise CinematicSceneRejected("Invalid beat index or motion phase")
    kind=story["format"]; theme=story["theme"]
    from PIL import ImageDraw,ImageChops
    before=image.copy()
    receipt=paint_original_premium_scene(
        image,theme=theme,kind=kind,scene_index=scene_index,
        scene_count=story["scene_count"],tick=tick)
    rect=SCENE_PANEL[kind]
    inner=_inner(rect)
    draw=ImageDraw.Draw(image)
    palette=PALETTE[theme]
    phase=scene_index%5
    if phase:
        _shade_region(draw,inner,palette)
        if theme=="file_transfer":
            _data_variant(draw,inner,phase,tick,palette)
        elif theme=="lunar_signal":
            _moon_variant(draw,inner,phase,tick,palette)
        else:
            _quake_variant(draw,inner,phase,tick,palette)
    # Source exact text (NOT a generated fact) is shown in the scene footer.
    # Distinct 20-scene long video stops repeating a fixed "data" card.
    scene=story["scenes"][scene_index]
    source_value=scene["display_value"]
    if not isinstance(source_value,str) or len(source_value)>85:
        raise CinematicSceneRejected("Source scene metric not safe or bounded")
    x0,y0,x1,y1=rect
    footer=(x0+42,y1-66,x1-38,y1-15)
    draw.rounded_rectangle(footer,radius=12,fill=palette["bg"],
                           outline=palette["secondary"],width=2)
    _source_label(draw,(x0+65,y1-58),source_value,
                  x1-58,y1-18,palette["secondary"],29)
    # A standalone separate native caption mask is applied by the
    # unchanged full_topic_narrated_pack._topic_png pipeline after us.
    caption_top=1295 if kind=="short" else 756
    if ImageChops.difference(
        before.crop((0,caption_top,image.width,image.height)),
        image.crop((0,caption_top,image.width,image.height))
    ).getbbox():
        raise CinematicSceneRejected("Source-based art changed subtitle/footer safe region")
    return {
        "status":STATUS,
        "source_scene_id":scene["scene_id"],
        "visual_scene_source_story_sha256":story["draft_sha256"],
        "visible_source_beat_value_sha256":sha256(source_value.encode()).hexdigest(),
        "source_driven_visual_phase":phase,
        "original_2point5d_artwork":receipt["original_dimensional_object"],
        "actual_real_3d_geometry_claimed":False,
        "original_reference_media_imported":False,
        "human_visual_quality_approved":False,
        "release_authorized":False,
    }
