"""Review-only 15 B1 SRT readability improvements with identical timing and spoken words.

Do not mutate MP4/ASS, copyright approvals, YouTube captions, or schedule.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import textwrap

TIMESTAMP=re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
CUE_TIMES=re.compile(
    r"^(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})$")
LIMITS={"short":42,"long":44}

class CaptionRefused(ValueError):
    """Do not upload edited, mistimed or altered-language caption tracks."""

def _seconds(value):
    match=TIMESTAMP.fullmatch(value)
    if match is None:
        raise CaptionRefused("Malformed or unsupported SRT timestamp")
    h,m,s,ms=(int(x) for x in match.groups())
    if m>=60 or s>=60:
        raise CaptionRefused("Malformed SRT clock value")
    return 3600*h+60*m+s+ms/1000

def reflow(original,kind):
    if kind not in LIMITS or not isinstance(original,str):
        raise CaptionRefused("Unknown video type or subtitles")
    source=original.replace("\r\n","\n").replace("\r","\n").strip()
    if "\ufeff" in source:
        source=source.lstrip("\ufeff")
    if len(source)>200_000 or not source:
        raise CaptionRefused("Unbounded original caption text")
    cues=re.split(r"\n\s*\n",source)
    if not 1<=len(cues)<=600:
        raise CaptionRefused("Unexpected number of original spoken cues")
    result=[]
    prev=0.0
    for index,cue in enumerate(cues,1):
        lines=cue.split("\n")
        if len(lines)<3 or lines[0]!=str(index):
            raise CaptionRefused("Missing sequential caption cue ID")
        match=CUE_TIMES.fullmatch(lines[1])
        if match is None:
            raise CaptionRefused("Missing exact timestamp pair")
        start,end=match.groups()
        t0,t1=_seconds(start),_seconds(end)
        if t0<prev or t1<=t0 or t1-t0>20:
            raise CaptionRefused("Overlapping, negative or implausible time range")
        prev=t1
        spoken=" ".join(" ".join(lines[2:]).split())
        if len(spoken)<1 or len(spoken)>150:
            raise CaptionRefused("Unexpected spoken cue length")
        wrapped=textwrap.wrap(spoken,width=LIMITS[kind],
                break_long_words=False,break_on_hyphens=False)
        if not 1<=len(wrapped)<=3 or max(map(len,wrapped))>LIMITS[kind]:
            raise CaptionRefused("Would need tiny or four-line subtitles")
        if spoken!=" ".join(wrapped):
            raise CaptionRefused("Spoken words changed by line reflow")
        result.append(lines[0]+"\n"+lines[1]+"\n"+"\n".join(wrapped))
    return "\n\n".join(result)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kind",choices=sorted(LIMITS),required=True)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists() or args.out.is_symlink() or not args.source.is_file():
        raise CaptionRefused("Refuse to overwrite or read unknown original captions")
    raw=args.source.read_text("utf-8")
    revised=reflow(raw,args.kind)
    args.out.write_text(revised,encoding="utf-8")
    print("SRT_REVIEW_ONLY_TIMES_WORDS_UNCHANGED_NO_YOUTUBE_WRITES",args.out.name)
if __name__=="__main__":
    main()
