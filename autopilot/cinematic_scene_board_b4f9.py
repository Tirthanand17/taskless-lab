"""B4f9 original editorial diagrams for physically rendered Flowminute rehearsals.

Designed against owner-inspected 2026-11-07 encoded MP4 contact sheets: the
previous 17 scenes repeated a small 3-card PowerPoint layout and generic
headline. This replacement uses individual idea-first editorial headlines,
four different visual grammars, strong typography, readable comparisons,
and 2-stage (never looping) visual emphasis. Original source-independent
words, PCM-timed narration and native-pixel subtitle geometry are unchanged.

No remote assets, image-model, public claim, rotating circle or YouTube write.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

from autopilot.real_rehearsal_voice_media_b4e0 import _font, SLOTS

STATUS = "B4F9_ORIGINAL_EDITORIAL_STORYBOARDS_HUMAN_REVIEW_ONLY"
PALE = (229,240,252)
MUTED = (158,184,207)
DEEP = (9,18,33)
FRAME = (19,36,55)

THEMES = {
    "short_am": {"accent":(92,195,255), "soft":(27,62,87), "name":"MORNING LAB"},
    "long": {"accent":(193,158,255), "soft":(65,49,88), "name":"FIELD GUIDE"},
    "short_pm": {"accent":(93,232,193), "soft":(24,75,69), "name":"EVENING LAB"},
}
# These are original, non-factual educational editorial labels,
# not content scraped from a real article or an unapproved claim.
BEATS = {
    "HOOK_QUESTION": ("THE QUESTION", ("IS IT", "REALLY TRUE?"),
                      "Ask first. Test before trusting.", "compare"),
    "SOURCE_SCOPE": ("CHECK THE EVIDENCE", ("START WITH", "THE SOURCE"),
                     "Confidence needs a clear origin.", "steps"),
    "DEMONSTRATION": ("A SMALL EXPERIMENT", ("BUILD A", "FAIR TEST"),
                      "Fictional inputs. Visible steps.", "matrix"),
    "VERIFY_AND_LIMIT": ("QUESTION THE RESULT", ("WHERE CAN", "IT FAIL?"),
                         "Limits belong in the explanation.", "gate"),
    "MECHANISM": ("TRACE THE LOGIC", ("FOLLOW THE", "DECISION"),
                  "Every choice leaves a checkpoint.", "steps"),
    "BASELINE": ("CONTROL THE COMPARISON", ("ONE FAIR", "BASELINE"),
                 "Change one thing, not everything.", "compare"),
    "EXAMPLE_1": ("CONTROLLED EXAMPLE", ("CASE A:", "THE START"),
                  "Write down the first condition.", "matrix"),
    "EXAMPLE_2": ("THE SECOND EXAMPLE", ("CASE B:", "THE CHANGE"),
                  "Compare against the same baseline.", "compare"),
    "COUNTEREXAMPLE": ("THE FAILURE CASE", ("WHEN THE", "RULE BREAKS"),
                       "Find the edge case early.", "gate"),
    "FACT_AND_RIGHTS_GATE": ("BEFORE RELEASING", ("PROOF AND", "PERMISSION"),
                             "No verified sources means no release.", "gate"),
    "NEXT_VIEWER_ACTION": ("YOUR NEXT MOVE", ("TRY A", "SAFER TEST"),
                           "Keep the results open for review.", "steps"),
}
CARD_WORDS = {
    "HOOK_QUESTION":(("ASK","DEFINE"),("IDEA","HYPOTHESIS"),("TEST","CHECK")),
    "SOURCE_SCOPE":(("SOURCE","UNVERIFIED"),("SCOPE","LIMIT"),("REVIEW","VERIFY")),
    "DEMONSTRATION":(("SAMPLE","SYNTHETIC"),("STEP","DEMONSTRATE"),("CHECK","REPRODUCE")),
    "VERIFY_AND_LIMIT":(("CLAIM","QUESTION"),("LIMIT","UNCERTAIN"),("PROOF","REVIEW")),
    "MECHANISM":(("INPUT","SYNTHETIC"),("PROCESS","EXPLAIN"),("OUTPUT","CHECK")),
    "BASELINE":(("CONTROL","BASELINE"),("CHANGE","ONE STEP"),("COMPARE","FAIR TEST")),
    "EXAMPLE_1":(("CASE A","INVENTED"),("TRACE","FIRST"),("CHECK","RECORD")),
    "EXAMPLE_2":(("CASE B","INVENTED"),("COMPARE","SECOND"),("CHECK","REPEAT")),
    "COUNTEREXAMPLE":(("FAILURE","IMAGINED"),("DETECT","QUESTION"),("RECOVER","REVIEW")),
    "FACT_AND_RIGHTS_GATE":(("FACT","UNVERIFIED"),("RIGHTS","UNCLEARED"),("BLOCK","RELEASE")),
    "NEXT_VIEWER_ACTION":(("TRY","SAFE TEST"),("LOG","YOUR INPUT"),("LEARN","REVIEW")),
}


class SceneDesignRefused(ValueError):
    """Source, layout or media-identity mismatch."""


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise SceneDesignRefused(message)


def _rgb(color: tuple[int,int,int], delta: int) -> tuple[int,int,int]:
    return tuple(max(0,min(255,v+delta)) for v in color)


def _safe_text(draw, xy: tuple[int,int], value: str, *, size: int,
               fill: tuple, box: tuple[int,int,int,int]) -> None:
    """Measure actual Pillow glyph bounds; no silently cropped screen text."""
    _need(type(value) is str and 0<len(value)<=110
          and "\n" not in value and size>=15,
          "Invalid original diagram text")
    font=_font(size)
    bounds=draw.textbbox(xy,value,font=font)
    x0,y0,x1,y1=box
    _need(bounds[0]>=x0-3 and bounds[1]>=y0-4
          and bounds[2]<=x1+3 and bounds[3]<=y1+4,
          f"Editorial text exceeded reserved visible region: {value[:24]}")
    draw.text(xy,value,font=font,fill=fill)


def _soft_box(draw, rect, *, fill=FRAME, outline=None, radius=24, width=2) -> None:
    draw.rounded_rectangle(rect,radius=radius,fill=fill,
                           outline=outline,width=width)


def _diagram(draw, area: tuple, scene_id: str, *, revealed: bool,
             active: int, accent: tuple, soft: tuple) -> None:
    """Four genuinely different grammars, never a circular loader."""
    x0,y0,x1,y1=area
    w,h=x1-x0,y1-y0
    scale=min(w/930,h/670)
    def X(u):return x0+round(u*w/1000)
    def Y(u):return y0+round(u*h/1000)
    def F(px):return max(15,round(px*scale))
    safe=(x0+10,y0+10,x1-10,y1-10)
    shape=BEATS[scene_id][3]
    words=CARD_WORDS[scene_id]
    _soft_box(draw,(x0,y0,x1,y1),fill=(16,32,51),
              outline=_rgb(accent,-25),radius=round(28*scale),width=3)
    draw.rectangle((X(42),Y(58),X(52),Y(115)),fill=accent)
    _safe_text(draw,(X(80),Y(64)),{"compare":"COMPARE THE CONDITIONS",
         "steps":"FOLLOW THE SEQUENCE","matrix":"EXAMINE THE SAMPLE",
         "gate":"QUESTION THE EVIDENCE"}[shape],
         size=F(31),fill=MUTED,box=safe)
    if shape=="compare":
        for i in (0,1):
            bx0=X(55+i*470); bx1=X(478+i*470)
            by0=Y(188);by1=Y(790)
            chosen=revealed and i==(active%2)
            _soft_box(draw,(bx0,by0,bx1,by1),
                      fill=soft if chosen else (27,43,62),
                      outline=accent if chosen else (77,106,127),
                      radius=round(23*scale),width=4 if chosen else 2)
            draw.rectangle((bx0+round(25*scale),by0+round(28*scale),
                            bx0+round(34*scale),by0+round(120*scale)),
                           fill=accent if chosen else MUTED)
            _safe_text(draw,(bx0+round(53*scale),by0+round(27*scale)),
                       f"PATH {'A' if i==0 else 'B'}",size=F(31),
                       fill=accent if chosen else MUTED,
                       box=(bx0,by0,bx1,by1))
            label,sub=words[i*2]
            _safe_text(draw,(bx0+round(30*scale),by0+round(155*scale)),
                       label,size=F(69),fill=PALE,box=(bx0,by0,bx1,by1))
            _safe_text(draw,(bx0+round(30*scale),by0+round(240*scale)),
                       sub,size=F(36),fill=accent if chosen else MUTED,
                       box=(bx0,by0,bx1,by1))
            draw.rectangle((bx0+round(30*scale),by1-round(66*scale),
                            bx1-round(30*scale),by1-round(52*scale)),
                           fill=accent if chosen else (76,98,122))
        _safe_text(draw,(X(76),Y(855)),"SAME QUESTION  /  DIFFERENT PATH",
                   size=F(30),fill=PALE,box=safe)
    elif shape=="steps":
        draw.rectangle((X(99),Y(181),X(104),Y(848)),fill=soft)
        for i,(label,sub) in enumerate(words):
            y=Y(180+i*225)
            chosen=revealed and i==active
            _soft_box(draw,(X(147),y,X(944),y+round(190*h/1000)),
                      fill=soft if chosen else (27,43,62),
                      outline=accent if chosen else (76,103,125),
                      radius=round(20*scale),width=4 if chosen else 2)
            _safe_text(draw,(X(172),y+round(33*scale)),str(i+1).zfill(2),
                       size=F(66),fill=accent,box=(X(150),y,X(935),y+round(190*h/1000)))
            _safe_text(draw,(X(330),y+round(42*scale)),label,
                       size=F(47),fill=PALE,box=(X(300),y,X(939),y+round(190*h/1000)))
            _safe_text(draw,(X(330),y+round(92*scale)),sub,
                       size=F(29),fill=MUTED,box=(X(300),y,X(939),y+round(190*h/1000)))
        _safe_text(draw,(X(190),Y(887)),"ONE STEP AT A TIME",size=F(29),
                   fill=accent,box=safe)
    elif shape=="matrix":
        for i,(label,sub) in enumerate(words):
            left=X(48+i*316);right=X(337+i*316)
            chosen=revealed and i==active
            _soft_box(draw,(left,Y(215),right,Y(755)),
                      fill=soft if chosen else (27,43,62),
                      outline=accent if chosen else (85,108,132),
                      radius=round(16*scale),width=4 if chosen else 2)
            _safe_text(draw,(left+round(27*scale),Y(255)),
                       f"0{i+1}",size=F(58),fill=accent,box=(left,Y(220),right,Y(755)))
            draw.rectangle((left+round(25*scale),Y(385),
                            right-round(25*scale),Y(403)),
                           fill=accent if chosen else (75,109,130))
            _safe_text(draw,(left+round(25*scale),Y(465)),
                       label,size=F(32),fill=PALE,box=(left,Y(450),right,Y(755)))
            _safe_text(draw,(left+round(25*scale),Y(545)),
                       sub,size=F(24),fill=MUTED,box=(left,Y(515),right,Y(755)))
        _safe_text(draw,(X(60),Y(847)),"SYNTHETIC INPUTS  /  NO MEASURED RESULT",
                   size=F(27),fill=PALE,box=safe)
    else:
        # Gate: human decision barrier, with explicit unanswered outcome.
        _soft_box(draw,(X(65),Y(211),X(937),Y(475)),fill=(33,51,69),
                  outline=accent,radius=round(18*scale),width=3)
        _safe_text(draw,(X(112),Y(244)),"CAN WE VERIFY IT?",size=F(61),
                   fill=PALE,box=(X(70),Y(211),X(930),Y(475)))
        _safe_text(draw,(X(115),Y(362)),"UNRESOLVED  /  CHECK FIRST",
                   size=F(29),fill=MUTED,box=(X(70),Y(211),X(930),Y(475)))
        for i,(label,sub) in enumerate(words[:2]):
            b0=X(65+i*468);b1=X(468+i*468)
            chosen=revealed and i==(active%2)
            _soft_box(draw,(b0,Y(555),b1,Y(802)),
                      fill=soft if chosen else (26,43,62),
                      outline=accent if chosen else (85,108,132),
                      radius=round(19*scale),width=3)
            _safe_text(draw,(b0+round(23*scale),Y(593)),label,
                       size=F(43),fill=PALE,box=(b0,Y(550),b1,Y(810)))
            _safe_text(draw,(b0+round(23*scale),Y(691)),sub,
                       size=F(30),fill=MUTED,box=(b0,Y(560),b1,Y(810)))
        _safe_text(draw,(X(75),Y(877)),"THE GATE STAYS CLOSED WITHOUT PROOF",
                   size=F(26),fill=accent,box=safe)


def render_editorial_frame(ep:dict,scene:dict,*,revealed:bool,
                           focus_index:int|None=None) -> Image.Image:
    """Create one full-size frame whose scene title and diagram are measurable."""
    _need(type(ep) is dict and type(scene) is dict
          and type(revealed) is bool,
          "Invalid unapproved storyboard input")
    slot=ep.get("slot")
    scene_id=scene.get("scene_id")
    number=scene.get("scene")
    portrait=ep.get("kind")=="short"
    w,h=(1080,1920) if portrait else (1920,1080)
    expected=4 if portrait else 9
    _need(slot in SLOTS and scene_id in BEATS
          and ep.get("kind")==("short" if slot!="long" else "long")
          and tuple(ep.get("size",()))==(w,h)
          and ep.get("all_scene_count")==expected
          and type(number) is int and 0<=number<expected,
          "Unverified scene/count/canvas or slot")
    beat=BEATS[scene_id]
    grammar=beat[3]
    choices=2 if grammar in ("compare","gate") else 3
    _need((focus_index is None) or (
          type(focus_index) is int and revealed
          and 0 <= focus_index < choices),
          "Untrusted scene focus or unavailable focus target")
    active=focus_index if focus_index is not None else number % choices
    palette=THEMES[slot]
    accent=palette["accent"]
    image=Image.new("RGB",(w,h),DEEP)
    draw=ImageDraw.Draw(image)
    for y in range(0,h,18):
        ratio=y/max(1,h-1)
        color=(round(12-3*ratio),round(25-8*ratio),round(43-9*ratio))
        draw.rectangle((0,y,w,y+18),fill=color)
    # Nonrepeating technical texture: crisp lines/squares, NEVER rings.
    draw.rectangle((0,0,18,h),fill=accent)
    for x in range(115,w-80,230):
        draw.line((x,0,x,h),fill=(20,34,51),width=1)
    top=82 if portrait else 68
    _safe_text(draw,(82,top),"FLOWMINUTE  /  LAB",
               size=35 if portrait else 37,fill=PALE,
               box=(70,40,w-70,top+100))
    right=f"{number+1:02}  /  {expected:02}"
    _safe_text(draw,(w-(210 if portrait else 234),top),right,
               size=35 if portrait else 37,fill=accent,
               box=(w-(235 if portrait else 270),top-5,w-64,top+95))
    draw.rectangle((82,top+74,w-82,top+79),fill=accent)
    header_y=225 if portrait else 165
    _safe_text(draw,(90,header_y),beat[0],size=33 if portrait else 34,
               fill=accent,box=(80,header_y-5,w-86,header_y+70))
    title_y=295 if portrait else 248
    title_font=100 if portrait else 93
    line_gap=121 if portrait else 114
    for i,line in enumerate(beat[1]):
        max_right=(w-80 if portrait else 845)
        _safe_text(draw,(84,title_y+i*line_gap),line,
                   size=title_font,fill=PALE,
                   box=(78,title_y+i*line_gap-5,max_right,
                        title_y+(i+1)*line_gap))
    desc_y=575 if portrait else 548
    _safe_text(draw,(88,desc_y),beat[2],size=32 if portrait else 33,
               fill=MUTED,box=(80,desc_y-4,w-78 if portrait else 870,
                               desc_y+75))
    area=((75,690,1005,1395) if portrait else
          (932,184,1840,705))
    _diagram(draw,area,scene_id,revealed=revealed,
             active=active,accent=accent,soft=palette["soft"])
    # Progress is *static* for each scene; no circular load, rotation or loop.
    bar_y=1460 if portrait else 728
    block_width=(850-12*(expected-1))//expected
    for i in range(expected):
        xx=90+i*(block_width+12)
        draw.rounded_rectangle((xx,bar_y,xx+block_width,bar_y+13),
                               radius=6,
                               fill=accent if i<=number else (61,82,105))
    if portrait:
        caption_top=h-390
        caption_bottom=h-128
    else:
        caption_top=h-320
        caption_bottom=h-128
    _need(area[3]+50 < caption_top,
          "Educational graphics would overlap native ASS subtitle card")
    _soft_box(draw,(82,caption_top,w-82,caption_bottom),
              fill=(17,34,53),outline=_rgb(accent,-40),
              radius=26,width=2)
    draw.rectangle((107,caption_top+23,194,caption_top+30),fill=accent)
    # This panel intentionally has NO static text: 2-line native ASS
    # captions alone occupy the central portion around y=1680 / 883.
    footer_y=h-89
    _safe_text(draw,(85,footer_y),
               "ORIGINAL SYNTHETIC PRACTICE  /  NOT VERIFIED NEWS  /  NO UPLOAD",
               size=22 if portrait else 24,fill=(136,164,187),
               box=(76,footer_y-6,w-74,h-45))
    return image
