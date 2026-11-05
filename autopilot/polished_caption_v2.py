"""B4e1 visual-quality rescue: explicitly scaled, tightly timed captions.

Purpose: replace oversized libass default-SRT captions with deterministic ASS
PlayRes (actual portrait/landscape pixels), at most two short lines per card,
short voice-timed cards, bounded true-pixel font size, selective emphasis and
a reserved non-overlapping caption zone.

This module contains NO content generator, voice clone, asset downloader,
real author approval, provider credential or YouTube uploader. The selected
colors/spacing are original Flowminute art direction, not copied assets from
the owner's third-party reference video.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Mapping

W_H={"short":(1080,1920),"long":(1920,1080)}
# These are CANVAS PIXELS thanks to matching ASS PlayRes; NOT libass 384x288 units.
CONFIG={
    "short":{"font":49,"line_chars":29,"words":7,"y":1420,
             "safe_top":1295,"safe_bottom":1570,"x":540,
             "color":"&H0066D9FF&"},  # soft sunrise gold, ASS BGR
    "long":{"font":48,"line_chars":42,"words":10,"y":845,
            "safe_top":756,"safe_bottom":935,"x":960,
            "color":"&H0069DCC1&"},
}
HIGHLIGHTS={
    "lunar_signal":frozenset({"moon","signal","delay","384,400","1.28","2.56","light"}),
    "quake_energy":frozenset({"earthquake","magnitude","energy","31.6","32","1,000","ten"}),
    "file_transfer":frozenset({"bit","bits","byte","bytes","megabit","megabits","megabyte",
                              "megabytes","mb","mib","20","40","41.94","eight"}),
}
BASE_COLOR="&H00F7F9FF&"  # bright almost-white in ASS BGR
STATUS="B4E1_PIXEL_EXACT_CAPTION_SAFE_TWO_LINES_NO_RELEASE"


class CaptionQualityRejected(ValueError):
    """Bad caption input or an unworkable typography/timing layout."""


@dataclass(frozen=True)
class CaptionCard:
    start:float
    end:float
    lines:tuple[str,...]
    text:str


def _safe_words(phrase:object)->list[str]:
    if not isinstance(phrase,str) or not 1<=len(phrase)<=300:
        raise CaptionQualityRejected("Unbounded or missing original spoken cue")
    if any((ord(c)<32 or c in "{}\\") for c in phrase):
        raise CaptionQualityRejected("Unsafe ASS markup/control text")
    words=phrase.split()
    if not 1<=len(words)<=80:
        raise CaptionQualityRejected("Unbounded spoken words")
    return words


def _pack_two_lines(words:list[str],kind:str)->list[tuple[str,...]]:
    cfg=CONFIG[kind]
    max_chars,max_words=cfg["line_chars"],cfg["words"]
    if any(len(w)>max_chars for w in words):
        raise CaptionQualityRejected("Overlong word needs editorial shortening")
    # Deterministic first-fit each card, maximum TWO lines and MAX words.
    cards=[]
    k=0
    while k<len(words):
        lines=[]
        n=0
        for _ in range(2):
            line_words=[]
            while k<len(words) and n<max_words:
                proposal=" ".join((*line_words,words[k]))
                if len(proposal)>max_chars:
                    break
                line_words.append(words[k])
                k+=1
                n+=1
            if line_words:
                lines.append(" ".join(line_words))
            if k>=len(words) or n>=max_words:
                break
        if not lines or any(len(x)>max_chars for x in lines) or len(lines)>2:
            raise CaptionQualityRejected("Caption layout exceeded two lines")
        cards.append(tuple(lines))
    if " ".join(" ".join(lines) for lines in cards)!=" ".join(words):
        raise CaptionQualityRejected("Original narrator words lost or reordered")
    return cards


def caption_cards(cues:list[Mapping],kind:str)->list[CaptionCard]:
    if kind not in CONFIG or type(cues) is not list or not 1<=len(cues)<=500:
        raise CaptionQualityRejected("Wrong video format or cue count")
    result=[]
    last_end=-1.0
    for cue in cues:
        if type(cue) is not dict:
            raise CaptionQualityRejected("Invalid timed voice cue")
        start,end=cue.get("start"),cue.get("end")
        if (type(start) not in (int,float) or type(end) not in (int,float)
            or not math.isfinite(start) or not math.isfinite(end)
            or start<0 or start<last_end-.002 or end<=start or end>360):
            raise CaptionQualityRejected("Overlapping, nonfinite or out-of-order spoken cues")
        last_end=end
        words=_safe_words(cue.get("text"))
        cards=_pack_two_lines(words,kind)
        weights=[sum(max(1,len(w.strip(",.!?;:"))) for x in lines for w in x.split())
                 for lines in cards]
        total=sum(weights)
        duration=end-start
        if duration/len(cards)<.27:
            raise CaptionQualityRejected("Unreasonably fast subtitle cards; revise spoken cue")
        progress=0
        for index,lines in enumerate(cards):
            a=start+duration*progress/total
            progress+=weights[index]
            b=end if index==len(cards)-1 else start+duration*progress/total
            if b-a<.23:
                raise CaptionQualityRejected("Unreadable brief caption requires review")
            result.append(CaptionCard(round(a,4),round(b,4),lines,
                                      " ".join(lines)))
    if len(result)>1600:
        raise CaptionQualityRejected("Excessive flash captions")
    return result


def _ass_stamp(seconds:float)->str:
    cs=round(seconds*100)
    hour,rem=divmod(cs,360000)
    minutes,rem=divmod(rem,6000)
    sec,cent=divmod(rem,100)
    return f"{hour}:{minutes:02d}:{sec:02d}.{cent:02d}"


def _paint_line(line:str,theme:str,kind:str)->str:
    selected=HIGHLIGHTS.get(theme)
    if selected is None:
        raise CaptionQualityRejected("Unexpected chapter color/claim context")
    out=[]
    for w in line.split():
        norm=re.sub(r"^[^\w\d]+|[^\w\d,.]+$","",w).lower()
        if norm in selected:
            out.append("{\\1c"+CONFIG[kind]["color"]+"}"+w+
                       "{\\1c"+BASE_COLOR+"}")
        else:
            out.append(w)
    return " ".join(out)


def compose_ass(cues:list[Mapping],kind:str,theme:str)->tuple[str,list[CaptionCard]]:
    """Explicit ASS PlayRes prevents inherited SRT PlayRes font explosion."""
    if theme not in HIGHLIGHTS:
        raise CaptionQualityRejected("Unexpected theme")
    cards=caption_cards(cues,kind)
    W,H=W_H[kind]
    c=CONFIG[kind]
    # Preserve exact pixel safe-zone invariant with native-scale PlayRes.
    if (c["safe_top"]<0 or c["safe_bottom"]>H
        or not c["safe_top"]<c["y"]-65<c["y"]+65<c["safe_bottom"]
        or c["font"]>52 or c["font"]<36):
        raise CaptionQualityRejected("Caption intrudes on illustration or UI safe area")
    header=(
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {W}\nPlayResY: {H}\n"
        "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
        "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,"
        "ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
        "MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Caption,DejaVu Sans,{c['font']},{BASE_COLOR},&H00FFFFFF&,"
        "&H00191B22&,&H00000000&,-1,0,0,0,100,100,0,0,1,1.3,0.5,5,"
        "60,60,0,1\n\n"
        "[Events]\n"
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    rows=[]
    for card in cards:
        text="\\N".join(_paint_line(line,theme,kind) for line in card.lines)
        # A subtle 95ms fade and 130ms pop; a PALETTE, not an SFX claim.
        prefix=(r"{\an5\pos("+str(c["x"])+","+str(c["y"])+
                r")\fad(65,80)\fscx94\fscy94\t(0,130,\fscx100\fscy100)}")
        rows.append("Dialogue: 0,"+_ass_stamp(card.start)+","+
                    _ass_stamp(card.end)+",Caption,,0,0,0,,"+prefix+text)
    return header+"\n".join(rows)+"\n",cards
