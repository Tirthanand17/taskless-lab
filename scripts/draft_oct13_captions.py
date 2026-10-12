"""Generate clearly UNREVIEWED captions for a HUMAN timing check.
Timings are estimated from generated segment word counts; they are not forced
alignment, should never be treated as verified, and must not be auto-uploaded.
"""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2] / "oct13-production"
DEST=ROOT/"captions"
DEST.mkdir(parents=True,exist_ok=True)
TARGETS=("pilot_017","long_008","pilot_018")

def stamp(seconds):
    ms=round(seconds*1000)
    h,ms=divmod(ms,3600000)
    m,ms=divmod(ms,60000)
    s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

for name in TARGETS:
    report=json.loads((ROOT/"audio"/f"{name}_natural_qa.json").read_text(encoding="utf8"))
    segments=report["segments"]
    duration=float(report["audio_duration_seconds"])
    words=[len(x["text"].split()) for x in segments]
    total_words=sum(words)
    pause=sum(x["pause_ms"]/1000 for x in segments)
    usable=duration-pause
    current=0.0
    result=[]
    for segment, count in zip(segments,words):
        spoken_seconds=usable*count/total_words
        tokens=segment["text"].split()
        groups=[tokens[i:i+8] for i in range(0,len(tokens),8)]
        t=current
        for group in groups:
            subtime=spoken_seconds*len(group)/len(tokens)
            end=min(duration,t+subtime)
            if end>t:
                result.append((t,end," ".join(group)))
            t=end
        current+=spoken_seconds+segment["pause_ms"]/1000
    content=""
    for i,(start,end,text) in enumerate(result,1):
        content+=f"{i}\n{stamp(start)} --> {stamp(end)}\n{text}\n\n"
    output=DEST/(name+"_DRAFT_UNREVIEWED.srt")
    output.write_text(content,encoding="utf-8")
    print(name, "CAPTION_DRAFT",len(result),"cues, requires alignment review:",output)
