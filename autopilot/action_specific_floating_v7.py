"""B4e6 original ACTION-SPECIFIC explanatory art, not generic looping widgets.

The user's review contact sheets revealed repeated sliders, Earth/Moon stills,
three quake columns and five recycled motifs across a 20-shot long video.
Replace select source-backed beats with distinct scientific visual grammar.

ALL spoken text, source claims, release rights, captions, thumbnails and
original SVG data remain unchanged. This only changes bounded native hero art.
No reused third-party frames, real 3D claim, provider or YouTube publisher.
"""
from __future__ import annotations

from hashlib import sha256
import math

from autopilot.cinematic_scene_v3 import (
    PALETTE, SCENE_PANEL, SIZES, CinematicSceneRejected,
)
from autopilot.cinematic_editorial_grid_v5 import STYLE
from autopilot.floating_cinematic_v6 import (
    _stage_background, paint_floating_original_beat,
)
from autopilot.primary_sourced_storyboards import require_exact_draft

STATUS = "B4E6_SOURCE_ACTION_SPECIFIC_FLOATING_SCIENCE_ART_UNAPPROVED"
MOTIFS = {
    "lunar_signal": frozenset((
        "orbit_ruler", "signal_sweep", "one_way_clock", "return_wave",
    )),
    "quake_energy": frozenset((
        "energy_columns", "energy_two_steps", "damage_caveat", "takeaway_quake",
    )),
    "file_transfer": frozenset((
        "eight_bit_grid", "speedometer_bits", "transfer_timer",
        "network_overhead", "unit_split", "decimal_binary_compare",
        "two_timers", "formula_pipeline", "capitalization_pair",
        "binary_decimal_scales", "conclusion_transfer",
    )),
}
SPECIALIZED = frozenset().union(*MOTIFS.values())


def _font(size):
    from PIL import ImageFont
    if type(size) is not int or not 12 <= size <= 72:
        raise CinematicSceneRejected("Invalid scene typography size")
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size,
        )
    except OSError:
        raise CinematicSceneRejected("Original science scene font unavailable") from None


def _art(image, story, scene, tick):
    from PIL import ImageDraw
    stage = SCENE_PANEL[story["format"]]
    x0,y0,x1,y1 = stage
    width,height=x1-x0,y1-y0
    # ALL artwork stays inside the original source's interior science hero.
    ax=x0+round(width*.09); bx=x1-round(width*.09)
    ay=y0+round(height*.09); by=y1-round(height*.12)
    w,h=bx-ax,by-ay
    d=ImageDraw.Draw(image)
    colors=PALETTE[story["theme"]]
    accent=colors["accent"]; secondary=colors["secondary"]
    faint=tuple(max(15,round(v*.37)) for v in accent)
    bright=tuple(min(255,round(v*1.10)) for v in accent)
    prog=tick/120

    def p(x,y):
        return (round(ax+x*w), round(ay+y*h))
    def straight(points, color=accent, width=6):
        d.line([p(*point) for point in points],fill=color,width=width,joint="curve")
    def dot(x,y,r=8,color=None):
        xx,yy=p(x,y)
        d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=color or accent)
    def text(value,x,y,size=34,color=None):
        if type(value) is not str or not 1 <= len(value) <= 62:
            raise CinematicSceneRejected("Unknown or lengthy source metric label")
        px,py=p(x,y)
        font=_font(size)
        bounds=d.textbbox((px,py),value,font=font,anchor="mm")
        if (bounds[0] < x0+12 or bounds[2] > x1-12
            or bounds[1] < y0+8 or bounds[3] > y1-8):
            raise CinematicSceneRejected("Topic-specific science label clips outside hero")
        d.text((px,py),value,font=font,fill=color or accent,anchor="mm")
    def rail(y,begin=.09,end=.91,selected=None):
        straight([(begin,y),(end,y)],faint,4)
        if selected is not None:
            sx=begin+(end-begin)*selected
            dot(sx,y,10)
    action=scene["visual_action"]
    source_value=scene["display_value"]

    if action=="orbit_ruler":
        text("EARTH",.12,.19,25,secondary)
        text("MOON",.87,.19,25,secondary)
        for x,r,color in ((.14,38,(33,114,178)),(.86,20,(204,210,216))):
            xx,yy=p(x,.40)
            d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=color,
                      outline=accent,width=3)
        rail(.40,.21,.78,prog)
        for k in range(7):
            x=.23+.53*k/6
            straight([(x,.43),(x,.49)],faint,3)
        text(source_value,.50,.73,44,bright)
        text("AVERAGE SEPARATION",.50,.85,24,secondary)

    elif action=="signal_sweep":
        text("RADIO TRAVELS AT LIGHT SPEED",.50,.20,26,secondary)
        wave=[(.10+i*.8/24,.43+.07*math.sin(i*.86)) for i in range(25)]
        straight(wave,accent,5)
        dot(.10+.8*prog,.43+.07*math.sin(prog*24*.86),14,bright)
        straight([(.10,.56),(.90,.56)],faint,2)
        text(source_value,.50,.76,37,bright)

    elif action=="one_way_clock":
        text("DISTANCE / SPEED",.50,.20,35,secondary)
        straight([(.12,.40),(.88,.40)],accent,7)
        dot(.12+.76*prog,.40,13,bright)
        for x in (.12,.50,.88):
            straight([(x,.36),(x,.47)],secondary,3)
        text(source_value,.50,.69,55,bright)
        text("ONE-WAY SIGNAL TIME",.50,.84,24,secondary)

    elif action=="return_wave":
        text("OUTBOUND",.20,.20,25,secondary)
        text("RETURN",.80,.20,25,secondary)
        straight([(.10,.35),(.90,.35)],accent,6)
        straight([(.90,.61),(.10,.61)],secondary,6)
        dot(.10+.8*prog,.35,12,bright)
        dot(.90-.8*prog,.61,12,bright)
        text(source_value,.50,.83,42,bright)

    elif action=="energy_columns":
        text("ONE MAGNITUDE STEP",.50,.15,27,secondary)
        points=[(.13,.78),(.40,.63),(.64,.38),(.84,.17)]
        straight(points,accent,11)
        for j,(x,y) in enumerate(points):
            dot(x,y,9,bright if j==round(prog*3) else secondary)
        text(source_value,.50,.90,48,bright)

    elif action=="energy_two_steps":
        text("TWO LOGARITHMIC STEPS",.50,.18,27,secondary)
        for i,(name,height) in enumerate((("M5",.20),("M6",.38),("M7",.62))):
            x=.20+i*.30
            left,ground=p(x-.075,.79)
            right,top=p(x+.075,.79-height)
            d.rectangle((left,top,right,ground),
                        fill=accent if i==2 else faint)
            text(name,x,.87,29,secondary)
        straight([(.20,.65),(.50,.47),(.80,.23)],bright,4)
        text(source_value,.50,.09,32,bright)

    elif action=="damage_caveat":
        text("ENERGY IS NOT DAMAGE",.50,.16,29,secondary)
        for i,xx in enumerate((.23,.64)):
            x,y=p(xx,.42)
            W,H=round(w*.13),round(h*(.23 if i==0 else .35))
            d.polygon([(x-W,y+H),(x-W,y),(x,y-round(h*.07)),
                       (x+W,y),(x+W,y+H)],fill=faint,outline=accent)
            for col in (-1,0,1):
                d.line((x+col*W//2,y+18,x+col*W//2,y+H-12),
                       fill=secondary,width=2)
        for j in range(3):
            yy=.76+j*.055
            straight([(.07,yy),(.34,yy+.012),(.62,yy),(.93,yy+.016)],
                     accent if j==0 else faint,3)
        text("DEPTH  /  DISTANCE  /  BUILDINGS",.50,.93,23,secondary)

    elif action=="takeaway_quake":
        text("LOGARITHMIC, NOT LINEAR",.50,.15,27,secondary)
        coords=[(.12,.77),(.33,.73),(.53,.61),(.69,.43),(.84,.16)]
        straight(coords,bright,8)
        for i,(x,y) in enumerate((coords[0],coords[2],coords[4])):
            dot(x,y,10,accent)
            text(("M5","M6","M7")[i],x,.90,24,secondary)

    elif action=="eight_bit_grid":
        text("EIGHT BITS MAKE ONE BYTE",.50,.16,30,secondary)
        for i in range(8):
            left,top=p(.045+i*.116,.35)
            right,bottom=p(.128+i*.116,.59)
            if i==round(7*prog):
                fill=accent
            else:
                fill=faint
            d.rounded_rectangle((left,top,right,bottom),radius=8,
                                fill=fill,outline=secondary,width=2)
            text("1" if i%3==0 else "0",.0865+i*.116,.47,22,
                 (2,16,23) if i==round(7*prog) else secondary)
        text("8 BITS = 1 BYTE",.50,.78,34,bright)

    elif action=="speedometer_bits":
        text("DECIMAL NETWORK SPEED",.50,.17,28,secondary)
        text(source_value,.50,.42,57,bright)
        rail(.70,.08,.92,prog)
        text("MEGABITS / SECOND",.50,.86,24,secondary)

    elif action=="transfer_timer":
        text("THEORETICAL FLOOR",.50,.17,29,secondary)
        text(source_value,.50,.47,57,bright)
        rail(.76,.12,.88,prog)
        text("IDEAL ASSUMPTIONS ONLY",.50,.89,24,secondary)

    elif action=="network_overhead":
        text("REAL TRANSFERS HAVE OVERHEAD",.50,.16,26,secondary)
        nodes=[(.11,.49),(.37,.49),(.63,.49),(.89,.49)]
        for u,v in zip(nodes,nodes[1:]):
            straight([u,v],secondary,5)
        for i,(x,y) in enumerate(nodes):
            xx,yy=p(x,y)
            r=round(h*(.10 if i==2 else .055))
            d.rounded_rectangle((xx-r,yy-r,xx+r,yy+r),
                                radius=8,fill=faint,outline=accent,width=4)
        dot(.11+.78*prog,.49,9,bright)
        text("HEADERS  /  CONGESTION  /  SERVER",.50,.82,23,secondary)

    elif action in ("unit_split","decimal_binary_compare"):
        text("DECIMAL  /  BINARY",.50,.14,30,secondary)
        for x,label,length in ((.26,"MB",.58),(.73,"MiB",.64)):
            text(label,x,.39,48,bright)
            left,top=p(x-.19,.60)
            right,bottom=p(x-.19+length*.45,.66)
            d.rounded_rectangle((left,top,right,bottom),
                                radius=9,fill=accent if label=="MB" else secondary)
        text("UNITS MUST MATCH",.50,.85,24,secondary)

    elif action=="two_timers":
        text("THE SAME 20 Mb/s CONNECTION",.50,.17,27,secondary)
        texts=(story["scenes"][7]["display_value"],
               story["scenes"][14]["display_value"])
        for k,(label,value) in enumerate((("100 MB",texts[0]),("100 MiB",texts[1]))):
            yy=.41+.27*k
            text(label,.22,yy,28,secondary)
            rail(yy,.44,.91,prog if not k else prog*.90)
            text(value,.76,yy-.085,29,bright)

    elif action=="formula_pipeline":
        text("TRACE THE UNITS",.50,.15,28,secondary)
        for i,label in enumerate(("FILE","BYTES","BITS","SECONDS")):
            x=.13+.245*i
            text(label,x,.44,26,bright if i==round(prog*3) else secondary)
            dot(x,.63,8)
            if i:
                straight([(.13+.245*(i-1),.63),(x,.63)],accent,3)
        text("FILE  ->  BITS  ->  SECONDS",.50,.84,26,bright)

    elif action=="capitalization_pair":
        text("A SINGLE LETTER CHANGES THE UNIT",.50,.17,26,secondary)
        text("b",.29,.48,72,accent)
        text("B",.70,.48,72,secondary)
        straight([(.45,.39),(.54,.57)],bright,4)
        straight([(.45,.57),(.54,.39)],bright,4)
        text("BITS  vs  BYTES",.50,.85,30,bright)

    elif action=="binary_decimal_scales":
        text("TWO DIFFERENT MULTIPLIERS",.50,.16,27,secondary)
        text("2^20",.26,.47,55,accent)
        text("10^6",.73,.47,55,secondary)
        text("BINARY",.26,.70,26,secondary)
        text("DECIMAL",.73,.70,26,secondary)

    elif action=="conclusion_transfer":
        text("THE REPEATABLE CHECK",.50,.16,30,secondary)
        for i,label in enumerate(("CALCULATE","SHOW UNITS","MEASURE")):
            x=.17+.33*i
            text(label,x,.46,26,bright if i==round(prog*2) else secondary)
            if i<2:
                straight([(x+.12,.61),(x+.21,.61)],accent,5)
        text("NUMBERS NEED CONTEXT",.50,.85,27,secondary)

    else:
        raise CinematicSceneRejected("Unregistered editorial science action")


def paint_action_specific_source_scene(
    image, *, story: dict, scene_index: int, tick: int,
) -> dict:
    """Only hero pixels change; outer sourced text and native ASS stay exact."""
    from PIL import Image, ImageChops
    require_exact_draft(story)
    if (type(scene_index) is not int or type(tick) is not int
        or not 0 <= scene_index < story["scene_count"]
        or not 0 <= tick <= 120 or image.mode != "RGB"
        or image.size != SIZES[story["format"]]):
        raise CinematicSceneRejected("Invalid original scene or native source frame")
    scene=story["scenes"][scene_index]
    theme=story["theme"]
    action=scene["visual_action"]
    before=image.copy()
    if action in MOTIFS[theme]:
        stage=SCENE_PANEL[story["format"]]
        _stage_background(image,stage,theme,scene_index,tick)
        _art(image,story,scene,tick)
        specialized=True
        style_name="SOURCE_ACTION_"+action.upper()
    else:
        legacy=paint_floating_original_beat(
            image,story=story,scene_index=scene_index,tick=tick)
        if (legacy["release_authorized"] is not False
            or legacy["source_story_draft_sha256"]!=story["draft_sha256"]):
            raise CinematicSceneRejected("Original unboxed fallback changed approval")
        specialized=False
        style_name=legacy["story_object_type"]
    y0,y1=SCENE_PANEL[story["format"]][1],SCENE_PANEL[story["format"]][3]
    for rect in ((0,0,image.width,y0),(0,y1,image.width,image.height)):
        if ImageChops.difference(before.crop(rect),image.crop(rect)).getbbox():
            raise CinematicSceneRejected("Science action art crossed source or caption safety")
    bg=STYLE[theme]["bg"]
    x0,x1=SCENE_PANEL[story["format"]][0],SCENE_PANEL[story["format"]][2]
    for rect in ((0,y0,x0,y1),(x1,y0,image.width,y1)):
        if image.crop(rect).getextrema()!=tuple((v,v) for v in bg):
            raise CinematicSceneRejected("Old diagram escaped new unboxed science hero")
    return {
        "status":STATUS,
        "scene_id":scene["scene_id"],
        "source_story_draft_sha256":story["draft_sha256"],
        "source_display_title_sha256":sha256(
            scene["display_title"].encode("utf8")).hexdigest(),
        "source_display_value_sha256":sha256(
            scene["display_value"].encode("utf8")).hexdigest(),
        "science_story_action":action,
        "visual_motif":style_name,
        "unique_science_action_composition_used":specialized,
        "old_bordered_presentation_panel_removed":True,
        "generic_spinner_absence_human_verified":False,
        "reference_clip_media_reused":False,
        "fully_modelled_real_3d_claimed":False,
        "all_source_narration_unchanged":True,
        "human_visual_preference_verified":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
