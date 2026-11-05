"""B4e4b: original floating scientific hero scenes, no giant presentation panel.

A distinct source-locked visual prototype for TWO Shorts and LONG:
original 2.5D objects, ambient depth, parallax light/particles and safe
foreground, WITHOUT bordered rectangles, repeated DATA / UNITS chrome,
inside-panel status footer or identical corporate slide framing.

Import only existing ORIGINAL Pillow scene object drawers. The user's
third-party reference clip, stills, sound effects and branding are NOT used.
Not real 3D geometry. Not an approved or published video.
"""
from __future__ import annotations

import math
from hashlib import sha256

from autopilot.cinematic_scene_v3 import (
    SCENE_PANEL,SIZES,PALETTE,CinematicSceneRejected,
    _moon_scene,_quake_scene,_data_scene,
)
from autopilot.cinematic_storyboard_v4 import (
    _data_variant,_moon_variant,_quake_variant,
)
from autopilot.cinematic_editorial_grid_v5 import STYLE
from autopilot.primary_sourced_storyboards import require_exact_draft

STATUS="B4E4B_SOURCE_LOCKED_FLOATING_HERO_NO_OUTER_BOX_UNAPPROVED"


def _stage_background(image,stage,theme,scene_index,tick):
    from PIL import Image,ImageDraw,ImageFilter
    x0,y0,x1,y1=stage
    color=STYLE[theme]["bg"]
    accent=PALETTE[theme]["accent"]
    secondary=PALETTE[theme]["secondary"]
    d=ImageDraw.Draw(image)
    # The legacy SVG's Earth circle begins at native x70, *four pixels
    # outside* the new x74 hero pane. Without a full-width SOURCE wipe,
    # a bright cyan crescent survives at the left edge even though the
    # new object itself is clipped perfectly. Clean the entire hero-only
    # horizontal ribbon before drawing original depth art. This never
    # affects source heading above y0 or true native ASS below y1.
    d.rectangle((0,y0,image.width-1,y1-1),fill=color)
    width=x1-x0; height=y1-y0
    # Radial ambient light lives *only* within the measured hero rectangle;
    # unlike the old panel it has NO hard border or new rounded-rectangle.
    radiance=Image.new("RGBA",(width,height),(0,0,0,0))
    lr=ImageDraw.Draw(radiance)
    cx=round(width*(.43+.08*math.sin(scene_index*.4+tick/100)))
    cy=round(height*.47)
    radius=round(min(width*.48,height*.55))
    for k in range(6):
        f=1.0-k*.11
        rr=round(radius*f)
        alpha=max(5,round((21+3*k)*(.55+.3*(tick/120))))
        lr.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),
                   fill=(*accent,alpha))
    radiance=radiance.filter(ImageFilter.GaussianBlur(20))
    base=image.convert("RGBA")
    base.alpha_composite(radiance,dest=(x0,y0))
    image.paste(base.convert("RGB"))
    d=ImageDraw.Draw(image)
    # Vanishing-plane grid: faint distant depth cue, no enclosing frame.
    horizon=round(y0+height*.77)
    origin_x=round(x0+width*.48)
    gridcolor=tuple(int(v*.22) for v in secondary)
    for j in range(-4,5):
        target=round(origin_x+j*width*.19)
        target=max(x0+32,min(x1-32,target))
        d.line((origin_x,horizon-35,target,y1-36),
               fill=gridcolor,width=2)
    for i in (0,1,2):
        off=round((height*.075)*(i+1)**1.45)
        yy=horizon+off
        if yy<y1-25:
            d.line((x0+45,yy,x1-45,yy),fill=gridcolor,width=1)
    # Deterministic small distant particles drift with scene and narration.
    for i in range(23):
        px=x0+45+((i*271+scene_index*91+tick*2)%(width-90))
        py=y0+42+((i*137+scene_index*59+tick//3)%(height-110))
        r=1+(i%3==0)
        d.ellipse((px-r,py-r,px+r,py+r),
                  fill=tuple(int(v*(.32 if i%4 else .55)) for v in accent))


def paint_floating_original_beat(image,*,story:dict,scene_index:int,tick:int)->dict:
    """Replace only original science hero with an unboxed original animation.

    Exact immutable script and all outside-hero pixels are preserved. The
    B4e4a editorial source title/metric/footer and B4e1 ASS captions can
    be applied separately in the actual renderer after this prototype.
    """
    from PIL import Image,ImageDraw,ImageChops
    require_exact_draft(story)
    if (type(scene_index) is not int or type(tick) is not int
        or not 0<=scene_index<story["scene_count"] or not 0<=tick<=120):
        raise CinematicSceneRejected("Original source beat or phase not permitted")
    kind=story["format"];theme=story["theme"]
    if not isinstance(image,Image.Image) or image.mode!="RGB" or image.size!=SIZES[kind]:
        raise CinematicSceneRejected("One exact native RGB original video frame required")
    before=image.copy()
    stage=SCENE_PANEL[kind]
    _stage_background(image,stage,theme,scene_index,tick)
    x0,y0,x1,y1=stage
    w,h=x1-x0,y1-y0
    # Hero objects occupy more of the actual video frame than old tiny
    # diagram-in-a-box. Subject changes every sourced beat, not every video.
    object_area=(
        x0+round(w*.07),y0+round(h*.09),
        x1-round(w*.07),y1-round(h*.09),
    )
    accent=PALETTE[theme]["accent"]
    secondary=PALETTE[theme]["secondary"]
    p=PALETTE[theme]
    layer=Image.new("RGBA",image.size,(0,0,0,0))
    d=ImageDraw.Draw(layer)
    variant=scene_index%5
    if theme=="lunar_signal":
        if variant in (0,3):
            object_type=_moon_scene(layer,object_area,tick,accent,secondary,scene_index)
        else:
            _moon_variant(d,object_area,variant,tick,p)
            object_type="SOURCE_ORBITAL_EVIDENCE_"+str(variant)
    elif theme=="quake_energy":
        if variant in (0,2):
            object_type=_quake_scene(layer,object_area,tick,accent,secondary,scene_index)
        else:
            _quake_variant(d,object_area,variant,tick,p)
            object_type="SOURCE_SEISMIC_ENERGY_"+str(variant)
    else:
        if variant==0:
            object_type=_data_scene(layer,object_area,tick,accent,secondary,scene_index)
        else:
            _data_variant(d,object_area,variant,tick,p)
            object_type="SOURCE_FILE_UNIT_EVIDENCE_"+str(variant)
    # Crop the transparent layer to the original stage before compositing:
    # foreground can NEVER silently cross the independently tested ASS region.
    combined=image.convert("RGBA")
    combined.alpha_composite(layer.crop(stage),dest=(x0,y0))
    image.paste(combined.convert("RGB"))
    if ImageChops.difference(
        before.crop((0,0,image.width,y0)),
        image.crop((0,0,image.width,y0))
    ).getbbox():
        raise CinematicSceneRejected("Unboxed hero crossed native source heading")
    if ImageChops.difference(
        before.crop((0,y1,image.width,image.height)),
        image.crop((0,y1,image.width,image.height))
    ).getbbox():
        raise CinematicSceneRejected("Unboxed hero crossed bottom/native ASS")
    # Unlike the old scene this deliberately wipes stale flat SVG art on
    # both sides of the new hero, so blue partial circles never leak into
    # an otherwise floating composition. Both outer margins must be EXACT
    # theme background with no foreign glyph or frame-line.
    for margin in ((0,y0,x0,y1),(x1,y0,image.width,y1)):
        tile=image.crop(margin)
        if tile.getextrema()!=tuple((v,v) for v in STYLE[theme]["bg"]):
            raise CinematicSceneRejected("Legacy source fragment escaped cleaned hero margin")
    return {
        "status":STATUS,
        "source_story_draft_sha256":story["draft_sha256"],
        "scene_id":story["scenes"][scene_index]["scene_id"],
        "source_visible_metric_sha256":sha256(
            story["scenes"][scene_index]["display_value"].encode()).hexdigest(),
        "theme":theme,
        "story_object_type":object_type,
        "old_bordered_presentation_panel_removed":True,
        "true_3d_geometry_claimed":False,
        "reference_clip_media_reused":False,
        "human_visual_or_fact_approved":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


def render_floating_source_proofs(destination):
    """Public original-image source before/after proof, no full media export."""
    from pathlib import Path
    import io,json
    import cairosvg
    from PIL import Image,ImageDraw,ImageFont
    from autopilot.primary_sourced_storyboards import build_story,render_original_svg
    from autopilot.cinematic_storyboard_v4 import paint_source_story_scene
    from autopilot.cinematic_editorial_grid_v5 import apply_source_cinematic_editorial_grid

    folder=Path(destination)
    if not folder.is_absolute() or folder.exists() or folder.is_symlink():
        raise CinematicSceneRejected("New absolute original source art proof folder required")
    folder.mkdir(parents=True,mode=0o700)
    receipts=[]
    for slot,scene in (("short_am",0),("short_am",3),("long",0),
                       ("long",1),("long",10),("short_pm",0),("short_pm",3)):
        story=build_story(slot)
        data=render_original_svg(story,scene,60)
        base=Image.open(io.BytesIO(cairosvg.svg2png(
            bytestring=data.encode("utf-8")))).convert("RGB")
        old=base.copy();new=base.copy()
        old_beat=paint_source_story_scene(old,story=story,scene_index=scene,tick=60)
        new_beat=paint_floating_original_beat(
            new,story=story,scene_index=scene,tick=60)
        old_layout=apply_source_cinematic_editorial_grid(
            old,story=story,scene_index=scene)
        new_layout=apply_source_cinematic_editorial_grid(
            new,story=story,scene_index=scene)
        if (old_layout["release_authorized"]
            or new_layout["release_authorized"]
            or new_beat["release_authorized"]):
            raise CinematicSceneRejected("Unapproved public source cannot authorize release")
        prefix=f"{slot}_{scene:02d}"
        old_name=prefix+"_BOXED_B4E4A.png"
        new_name=prefix+"_FLOATING_B4E4B.png"
        old.save(folder/old_name,optimize=True)
        new.save(folder/new_name,optimize=True)
        # JPEG review collage, convenient to judge on web/mobile.
        view=(340,604) if story["format"]=="short" else (500,282)
        left=old.copy();right=new.copy()
        left.thumbnail(view);right.thumbnail(view)
        comparison=Image.new("RGB",(left.width+right.width+30,
            max(left.height,right.height)+58),(9,17,32))
        d=ImageDraw.Draw(comparison)
        f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",18)
        d.text((8,12),"BOXED BEFORE",font=f,fill=(222,226,235))
        d.text((left.width+18,12),"FLOATING AFTER",font=f,fill=(102,229,190))
        comparison.paste(left,(8,44));comparison.paste(right,(left.width+22,44))
        comparison_name=prefix+"_REAL_VISUAL_COMPARE_UNAPPROVED.png"
        comparison.save(folder/comparison_name,optimize=True)
        receipts.append({
            "slot":slot,"scene":scene,"story_sha256":story["draft_sha256"],
            "source_title_not_changed":True,"source_metric_not_changed":True,
            "original_2point5d_subject":new_beat["story_object_type"],
            "boxed_panel_removed":True,
            "comparison_image":comparison_name,
            "before_image":old_name,"after_image":new_name,
            "reference_clip_copied":False,"release_authorized":False,
            "owner_visual_approved":False,
        })
    result={
        "status":STATUS,"source_only_real_visual_previews":receipts,
        "reference_video_assets_imported":False,
        "full_movie_video_encoded":False,"real_3d":False,
        "owner_visual_approved":False,"youtube_upload_enabled":False,
    }
    (folder/"UNAPPROVED_FLOATING_STORYBOARD_MANIFEST.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    import argparse,json
    parser=argparse.ArgumentParser(description="Source-authored floating hero preview; no YouTube")
    parser.add_argument("--out",required=True)
    a=parser.parse_args()
    print(json.dumps(render_floating_source_proofs(a.out),sort_keys=True))
