"""B4e1 original dimensional educational YouTube thumbnail renderer.

One clear hierarchy: small Flowminute label, two-line human-readable hook,
big numerical fact, original subject-specific dimensional object on the right,
subtle tiny DRAFT indicator. No fake article photos, no borrowed 3D clip art.
All geometry is in exact 1280x720 pixel coordinates and laid out to avoid
left-type/right-object intersection. Source is still UNAPPROVED for release.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import math

THUMB_STATUS="ORIGINAL_SOURCE_LINKED_EDITORIAL_COVER_DRAFT_NO_RELEASE"
SPEC={
    "lunar_signal":{
        "title":("MOON SIGNAL","DELAY"),
        "stat":"1.28 s one way",
        "eyebrow":"SPACE • SIGNALS",
        "accent":(87,191,243),
        "dark":(7,22,42),
    },
    "file_transfer":{
        "title":("BITS vs","BYTES"),
        "stat":"8 bits = 1 byte",
        "eyebrow":"TECH • EXPLAINED",
        "accent":(83,221,178),
        "dark":(5,25,30),
    },
    "quake_energy":{
        "title":("EARTHQUAKE","ENERGY"),
        "stat":"1 STEP ≈ 32×",
        "eyebrow":"SCIENCE • SCALE",
        "accent":(255,168,96),
        "dark":(37,13,21),
    },
}


class ThumbnailQualityRejected(ValueError):
    """Missing rights/source or a poorly aligned thumbnail design."""


def _font(size:int,bold:bool=False):
    from PIL import ImageFont
    f="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(f,size)
    except OSError:
        raise ThumbnailQualityRejected("Host DejaVu font installation unavailable") from None


def _text_fit(draw,xy,text,font,max_right,max_bottom,**options):
    box=draw.textbbox(xy,text,font=font)
    if box[2]>max_right or box[3]>max_bottom or box[0]<0 or box[1]<0:
        raise ThumbnailQualityRejected("Original thumbnail typography crossed its layout grid")
    draw.text(xy,text,font=font,**options)


def _halo(im,x,y,r,accent):
    from PIL import Image,ImageDraw,ImageFilter
    glow=Image.new("RGBA",im.size,(0,0,0,0))
    d=ImageDraw.Draw(glow)
    d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,135))
    glow=glow.filter(ImageFilter.GaussianBlur(96))
    im.paste(glow,(0,0),glow)


def _moon(draw,accent):
    # Original illustrated Earth, orbital ring and Moon; not NASA imagery.
    draw.ellipse((780,162,1206,588),outline=(31,67,93),width=6)
    draw.arc((790,179,1195,575),40,320,fill=accent,width=4)
    draw.ellipse((833,268,1013,448),fill=(26,78,139),
                 outline=(101,205,243),width=5)
    draw.polygon([(859,330),(889,281),(941,294),(962,338),
                  (918,365),(900,417),(861,392)],fill=(62,174,150))
    draw.ellipse((1064,246,1184,366),fill=(186,199,209),
                 outline=(239,244,248),width=4)
    for x,y,r in ((1093,275,9),(1148,296,15),(1115,332,7)):
        draw.ellipse((x-r,y-r,x+r,y+r),fill=(128,148,159))
    draw.line((1010,345,1065,316),fill=accent,width=5)
    draw.rounded_rectangle((861,514,1165,567),radius=18,
                           fill=(10,31,51),outline=(36,96,134),width=2)
    _text_fit(draw,(890,522),"~ 384,400 km",_font(25,True),1155,557,fill=(227,242,249))


def _transfer(draw,accent):
    # Perspective laptop body + split bits/bytes UI cards, original 2.5D.
    draw.rounded_rectangle((796,180,1180,454),radius=20,
                           fill=(44,59,74),outline=(147,180,193),width=5)
    draw.rounded_rectangle((813,198,1163,434),radius=8,fill=(8,22,40))
    draw.rounded_rectangle((848,224,1119,284),radius=12,
                           fill=(20,46,59),outline=accent,width=2)
    _text_fit(draw,(876,239),"00010111",_font(25,True),1106,279,fill=accent)
    draw.polygon([(792,458),(1182,458),(1230,507),(748,507)],
                 fill=(81,97,108))
    draw.polygon([(817,468),(1157,468),(1175,487),(798,487)],
                 fill=(19,28,43))
    draw.rounded_rectangle((755,306,904,392),radius=18,fill=(16,56,67),
                           outline=accent,width=3)
    _text_fit(draw,(778,324),"Mb",_font(40,True),888,376,fill=(238,247,249))
    draw.rounded_rectangle((1088,383,1243,477),radius=18,
                           fill=(12,56,67),outline=(244,238,205),width=3)
    _text_fit(draw,(1118,404),"MB",_font(38,True),1232,464,fill=(238,247,249))


def _quake(draw,accent):
    # Visible dimensional bars + depth surfaces to encode 32x energy.
    draw.line((794,506,1213,506),fill=(174,130,111),width=4)
    for x,top,label in ((838,345,"M 6"),(1038,205,"M 7")):
        width=122
        draw.polygon([(x,top),(x+width,top),(x+width+28,top-28),
                      (x+28,top-28)],fill=(255,197,145))
        draw.rectangle((x,top,x+width,505),fill=accent if label=="M 7" else (131,78,61))
        draw.polygon([(x+width,top),(x+width+28,top-28),
                      (x+width+28,477),(x+width,505)],
                     fill=(104,43,29) if label=="M 7" else (67,40,37))
        _text_fit(draw,(x+29,527),label,_font(29,True),x+width+25,572,
                  fill=(240,231,222))
    draw.rounded_rectangle((917,122,1155,181),radius=15,
                           fill=(62,28,33),outline=accent,width=2)
    _text_fit(draw,(941,133),"ENERGY",_font(26,True),1137,175,fill=(249,223,190))


def render_editorial_thumbnail(story:dict,output:Path)->str:
    from PIL import Image,ImageDraw
    if type(story) is not dict or story.get("theme") not in SPEC:
        raise ThumbnailQualityRejected("Only three already authored research demonstration themes allowed")
    if story.get("release_authorized") is not False or story.get("youtube_upload_enabled") is not False:
        raise ThumbnailQualityRejected("Refuse authorized/public release thumbnail")
    theme=story["theme"]
    c=SPEC[theme]
    W,H=1280,720
    im=Image.new("RGB",(W,H),c["dark"])
    d=ImageDraw.Draw(im)
    # A little studio-light falloff and no large disconnected boxes.
    for y in range(H):
        k=y/H
        d.line((0,y,W,y),fill=tuple(max(0,min(255,int(v*(1-.22*k))))
                                      for v in c["dark"]))
    _halo(im,995,347,200,c["accent"])
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((69,60,440,104),radius=15,fill=(13,29,37),
                        outline=(*c["accent"],),width=2)
    _text_fit(d,(87,67),"FLOWMINUTE  /  EXPLAINS",_font(20,True),
              428,97,fill=(232,243,249))
    _text_fit(d,(84,138),c["eyebrow"],_font(25,True),692,184,fill=c["accent"])
    headline_size=64 if theme=="quake_energy" else 74
    for i,row in enumerate(c["title"]):
        _text_fit(d,(76,224+i*99),row,_font(headline_size,True),
                  754,433,fill=(241,245,251))
    _text_fit(d,(81,488),c["stat"],_font(44,True),730,563,fill=c["accent"])
    # Elegant 3px accent rule, not a giant border or legal warning across art.
    d.line((86,615,709,615),fill=(*c["accent"],),width=3)
    _text_fit(d,(86,644),"ORIGINAL DEMO  ·  UNAPPROVED",
              _font(20,True),703,680,fill=(185,194,206))
    if theme=="lunar_signal":
        _moon(d,c["accent"])
    elif theme=="file_transfer":
        _transfer(d,c["accent"])
    else:
        _quake(d,c["accent"])
    output=Path(output)
    if output.exists() or output.is_symlink():
        raise ThumbnailQualityRejected("Do not overwrite signed or already reviewed image")
    im.save(output,format="PNG",optimize=True)
    if im.size!=(1280,720) or output.stat().st_size<12000:
        raise ThumbnailQualityRejected("Empty or wrong size original editorial cover")
    return sha256(output.read_bytes()).hexdigest()
