"""B4f7 native-pixel ASS captions for the 17-scene original rehearsal renderer.

The real November 7 owner review artifact proved forced-style SRT burned
oversized text at the TOP of 1080x1920 Shorts, clipping text and covering
diagrams. Libass interprets FontSize on SRT through a synthetic 384x288
PlayRes. Force-style FontSize=27 is NOT 27 actual portrait pixels.

Generate explicit authored ASS with PlayRes = physical pixels and bounded
two-line microcards, retaining EVERY ORIGINAL SPOKEN WORD and its actual
PCM cue interval. Place text ONLY inside a genuinely reserved low panel.
No YouTube activity, internet, external assets or release approval.
"""
from __future__ import annotations

from pathlib import Path
import math
import re

from autopilot.polished_caption_v2 import (
    CaptionQualityRejected, caption_cards,
)

STATUS="B4F7_ACTUAL_PIXEL_TWO_LINE_CAPTION_NON_OVERLAP_NOT_RELEASE"
# Bounds here match _draw_original_full_scene; body cards/progress end before
# the panel. Landscape panel is enlarged upwards for 2-line readability.
STYLE={
    "short":{
        "w":1080,"h":1920, "font":43,
        "x":540,"y":1680,
        "panel_top":1530,"panel_bottom":1792,
        "text_top":1614,"text_bottom":1764,
        "max_chars":29,
    },
    "long":{
        "w":1920,"h":1080,"font":36,
        "x":960,"y":883,
        "panel_top":760,"panel_bottom":952,
        "text_top":829,"text_bottom":935,
        "max_chars":42,
    },
}
ASS_TEXT=re.compile(r"^[^\x00-\x1f{}\\]+$",re.UNICODE)


class NativeCaptionRefused(ValueError):
    """Do not silently fall back to giant default-SRT libass typography."""


def native_caption_layout(kind: str) -> dict:
    if kind not in STYLE:
        raise NativeCaptionRefused("Unknown original MP4 canvas")
    c=STYLE[kind]
    half=53 if kind=="short" else 45
    if (not 0<c["text_top"]<c["y"]-half<c["y"]+half<c["text_bottom"]
        <c["panel_bottom"]<c["h"] or not c["panel_top"]<c["text_top"]
        or not 30<=c["font"]<=45):
        raise NativeCaptionRefused("Subtitle text does not fit reserved panel")
    return dict(c)


def _ass_time(t: float) -> str:
    if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=360:
        raise NativeCaptionRefused("Nonfinite or out-of-range PCM text time")
    n=round(t*100)
    hh,n=divmod(n,360000)
    mm,n=divmod(n,6000)
    ss,cc=divmod(n,100)
    return f"{hh}:{mm:02}:{ss:02}.{cc:02}"


def compose_rehearsal_native_ass(cues: list[dict],kind: str
                                ) -> tuple[str,dict]:
    """Create native-scale libass script from actual measured PCM cue text.

    Split a long original voiced phrase into timed, shorter two-line cards.
    Do not delete, rewrite, approve or invent any spoken word.
    """
    c=native_caption_layout(kind)
    try:
        cards=caption_cards(cues,kind)
    except (CaptionQualityRejected,TypeError,KeyError,ValueError):
        raise NativeCaptionRefused("Audio phrases cannot be safely fitted") from None
    if (not cards or len(cards)>1600
        or any(len(card.lines)>2
               or any(len(line)>c["max_chars"] or
                      ASS_TEXT.fullmatch(line) is None
                      for line in card.lines)
               for card in cards)):
        raise NativeCaptionRefused("Subtitles too long for exact pixel card")
    before=" ".join(" ".join(str(cue["text"]).split()) for cue in cues)
    after=" ".join(card.text for card in cards)
    if before!=after:
        raise NativeCaptionRefused("Original spoken words lost or reordered")
    # Enforce NO clipping and NO need to move the caption box into diagrams.
    font=c["font"]
    x,y,w,h=c["x"],c["y"],c["w"],c["h"]
    header=(
        "[Script Info]\n"
        "Title: Flowminute Original Rehearsal Native Scale, NO PUBLISH\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {w}\nPlayResY: {h}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
        "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,"
        "ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
        "MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Caption,DejaVu Sans,{font},&H00FFFFFF&,&H00FFFFFF&,"
        "&H0008101B&,&H80000000&,-1,0,0,0,100,100,0,0,1,2.2,0,5,"
        "70,70,0,1\n\n"
        "[Events]\n"
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    rows=[]
    for card in cards:
        lines=card.lines
        # ASS \N is an explicit line break. Always center in the lower
        # RESERVED art panel, never the default synthetic SRT canvas.
        text=r"\N".join(lines)
        rows.append(
            "Dialogue: 0,"+_ass_time(card.start)+","+
            _ass_time(card.end)+",Caption,,0,0,0,,"+
            r"{\an5\pos("+str(x)+","+str(y)+r")\fad(60,65)}"+text
        )
    return (header+"\n".join(rows)+"\n", {
        "status":STATUS,
        "format":kind,
        "physical_canvas_pixels":[w,h],
        "ass_playres_matches_encoded_canvas":True,
        "position_pixels":[x,y],
        "true_pixel_font_size":font,
        "original_pcm_phrase_count":len(cues),
        "two_line_voice_timed_microcard_count":len(cards),
        "max_subtitle_lines":2,
        "source_spoken_words_preserved":True,
        "caption_panel_nonoverlap_geometry_validated":True,
        "human_watch_completed":False,
        "news_facts_and_rights_approved":False,
        "youtube_release_authorized":False,
    })


def write_rehearsal_native_ass(folder:Path,cues:list[dict],kind:str)->Path:
    if (not isinstance(folder,Path) or not folder.is_dir()
        or folder.is_symlink()):
        raise NativeCaptionRefused("Unsafe original renderer caption directory")
    content,_=compose_rehearsal_native_ass(cues,kind)
    target=folder/"EPHEMERAL_NATIVE_PIXEL_VOICE_CAPTIONS.ass"
    if target.exists() or target.is_symlink():
        raise NativeCaptionRefused("Refuse overwrite of existing caption file")
    target.write_text(content,encoding="utf8")
    return target
