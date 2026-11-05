"""B4e4a original SOURCE-title editorial grid for cinematic Shorts and long.

This is a narrow *visible collision fix*: rasterize the old original source
SVG's title/footnote, then replace ONLY top and footer typography on the
cinematic opt-in renderer. Reuses the exact immutable NASA/NIST/USGS
display_title and display_value, never changes narrations or claims.

The legacy SVG long landscape drew title at y=56 and brand at y=85 in
1080-coordinate viewBox then enlarged them to 1920x1080, causing a real
overlap. It also drew scene footer near y=947 and progress bars below the
caption band. The B4e4a 1920x1080 grid reserves top 0..270 for mutually
exclusive brand/heading/subvalue, hero art 280..720, native ASS captions
756..935 and a separate tiny footer 946..995; the progress dot appears
at y1028. Portrait reserves top 0..516, hero 533..1220, native captions
1295..1570, footer 1710..1770 and app chrome below.

Actual photoreal 3D, human design approval and YouTube publishing all FALSE.
"""
from __future__ import annotations

from hashlib import sha256

STATUS="B4E4A_SOURCE_LOCKED_PIXEL_EDITIONAL_GRID_UNAPPROVED"

STYLE={
    "lunar_signal":{"bg":(9,15,37),"accent":(88,201,237),
                    "paper":(242,229,191),"topic":"LUNAR SIGNAL"},
    "quake_energy":{"bg":(33,19,26),"accent":(255,159,98),
                    "paper":(238,227,215),"topic":"QUAKE ENERGY"},
    "file_transfer":{"bg":(10,27,39),"accent":(114,223,189),
                     "paper":(223,244,255),"topic":"FILE TRANSFER"},
}


class EditorialAlignmentRejected(ValueError):
    pass


def _font(size:int):
    from PIL import ImageFont
    if type(size) is not int or not 18<=size<=68:
        raise EditorialAlignmentRejected("Invalid editorial text size")
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",size)
    except OSError:
        raise EditorialAlignmentRejected("DejaVu source typeface unavailable") from None


def _text(draw,xy,word,*,font_size,fill,bounds):
    x,y=xy
    if type(word) is not str or not word or len(word)>110:
        raise EditorialAlignmentRejected("Unsigned/fake source text or text overflow")
    face=_font(font_size)
    bb=draw.textbbox((x,y),word,font=face)
    x0,y0,x1,y1=bounds
    if bb[0]<x0 or bb[1]<y0 or bb[2]>x1 or bb[3]>y1:
        raise EditorialAlignmentRejected("Typed original text crossed editorial safe grid")
    draw.text((x,y),word,font=face,fill=fill)
    return (bb[0],bb[1],bb[2],bb[3])


def _fit_title(draw,text,*,x,y,right,bottom,max_size,limit_lines):
    if type(text) is not str or not 0<len(text)<=105:
        raise EditorialAlignmentRejected("Invalid authored source title")
    # Prefer one line over two; adjust font to fill measured width.
    for n in range(max_size,29,-1):
        font=_font(n)
        bb=draw.textbbox((x,y),text,font=font)
        if bb[2]<=right and bb[3]<=bottom:
            return [_text(draw,(x,y),text,font_size=n,fill=(244,247,252),
                          bounds=(x,y,right,bottom))]
    words=text.split(" ")
    if limit_lines<2 or len(words)<2:
        raise EditorialAlignmentRejected("Original title cannot fit in one line")
    # Exhaustive stable two-line split, never truncation or lost facts.
    for n in range(min(46,max_size),29,-1):
        face=_font(n)
        for at in range(1,len(words)):
            chunks=(" ".join(words[:at])," ".join(words[at:]))
            if " ".join(chunks)!=text:
                continue
            first=draw.textbbox((x,y),chunks[0],font=face)
            second=draw.textbbox((x,y+n+4),chunks[1],font=face)
            if first[2]<=right and second[2]<=right and second[3]<=bottom:
                firstbb=_text(draw,(x,y),chunks[0],font_size=n,
                              fill=(244,247,252),bounds=(x,y,right,bottom))
                secondbb=_text(draw,(x,y+n+4),chunks[1],font_size=n,
                               fill=(244,247,252),bounds=(x,y,right,bottom))
                return [firstbb,secondbb]
    raise EditorialAlignmentRejected("Authored title refuses to fit measured two-line region")


def _not_overlap(rects):
    for i,a in enumerate(rects):
        for b in rects[i+1:]:
            if max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3]):
                raise EditorialAlignmentRejected("Original information hierarchy overlaps")


def apply_source_cinematic_editorial_grid(image,*,story:dict,scene_index:int)->dict:
    """Redraw old ill-positioned labels without modifying rendered hero or ASS.

    The *actual* cinema painter is applied first by _topic_png, then this
    limited typography grid; native ASS filter and final independent review
    occur later. Existing non-cinematic classic_v2 gets no modifications.
    """
    from PIL import Image,ImageDraw,ImageChops
    from autopilot.primary_sourced_storyboards import require_exact_draft
    require_exact_draft(story)
    kind=story["format"];theme=story["theme"]
    if (theme not in STYLE or kind not in ("short","long")
        or type(scene_index) is not int
        or not 0<=scene_index<story["scene_count"]
        or not isinstance(image,Image.Image) or image.mode!="RGB"
        or image.size!=((1080,1920) if kind=="short" else (1920,1080))):
        raise EditorialAlignmentRejected("Unknown source, clip or native format")
    scene=story["scenes"][scene_index]
    title=scene["display_title"]
    value=scene["display_value"]
    if (not isinstance(title,str) or not isinstance(value,str)
        or len(title)>105 or len(value)>85):
        raise EditorialAlignmentRejected("Unsigned source text too long")
    p=STYLE[theme]
    d=ImageDraw.Draw(image)
    if kind=="long":
        header=(0,0,1920,270);footer=(0,936,1920,1080)
        hero=(0,280,1920,720);captions=(0,756,1920,935)
        brand_xy=(125,34);chapter_xy=(1575,34)
        title_xy=(126,102);title_right=1768;title_bottom=211
        value_xy=(128,222);value_bounds=(126,214,1755,268)
        footer_xy=(130,969);footer_right=1450
        end_xy=(1720,969)
        brand_size=31;value_size=31;footer_size=20;title_size=64
    else:
        header=(0,0,1080,518);footer=(0,1571,1080,1920)
        hero=(0,533,1080,1220);captions=(0,1295,1080,1570)
        brand_xy=(72,75);chapter_xy=(859,75)
        title_xy=(74,266);title_right=1010;title_bottom=402
        value_xy=(78,438);value_bounds=(74,431,1014,506)
        footer_xy=(74,1735);footer_right=788
        end_xy=(882,1735)
        brand_size=28;value_size=28;footer_size=20;title_size=60
    old=image.copy()
    d.rectangle(header,fill=p["bg"])
    d.rectangle(footer,fill=p["bg"])
    brand=_text(d,brand_xy,"FLOWMINUTE  /  "+p["topic"],
                font_size=brand_size,fill=p["accent"],
                bounds=(brand_xy[0],0,chapter_xy[0]-15,148 if kind=="short" else 91))
    chapter=_text(d,chapter_xy,
                  f"{scene_index+1:02d}/{story['scene_count']:02d}",
                  font_size=26 if kind=="short" else 25,
                  fill=p["paper"],
                  bounds=(chapter_xy[0],0,image.width-35,142 if kind=="short" else 91))
    heading=_fit_title(d,title,x=title_xy[0],y=title_xy[1],
                       right=title_right,bottom=title_bottom,
                       max_size=title_size,limit_lines=2)
    metric=_text(d,value_xy,value,font_size=value_size,fill=p["accent"],
                 bounds=value_bounds)
    if kind=="long":
        _not_overlap([brand,chapter,*heading,metric])
    else:
        _not_overlap([brand,chapter,*heading,metric])
    status=_text(d,footer_xy,"DRAFT  /  INTERNAL VISUAL REVIEW",
                 font_size=footer_size,fill=p["paper"],
                 bounds=(footer_xy[0],footer[1],footer_right,
                         footer[3]-55 if kind=="long" else footer[3]-80))
    count=_text(d,end_xy,f"SCENE {scene_index+1:02d}",
                font_size=20,fill=p["accent"],
                bounds=(end_xy[0],footer[1],image.width-24,
                        footer[3]-55 if kind=="long" else footer[3]-80))
    _not_overlap([status,count])
    # The original scientific hero and the complete true ASS region remain
    # *bitwise identical* after the new title/footer grid.
    for rect in (hero,captions):
        if ImageChops.difference(old.crop(rect),image.crop(rect)).getbbox():
            raise EditorialAlignmentRejected("Editorial typography erased original cinematic hero or native captions")
    return {
        "status":STATUS,
        "original_source_story_draft_sha256":story["draft_sha256"],
        "source_title_exact_text_sha256":sha256(title.encode()).hexdigest(),
        "source_metric_exact_text_sha256":sha256(value.encode()).hexdigest(),
        "title_bounding_rectangles":heading,
        "brand_and_title_collisions":False,
        "footer_caption_collision":False,
        "original_hero_untouched":True,
        "native_ass_caption_zone_untouched":True,
        "human_artist_reviewed":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
