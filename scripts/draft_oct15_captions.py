"""Create NON-ALIGNED, HUMAN-REVIEW-REQUIRED SRT drafts.
For the long narration, use exact chunk PCM boundaries; word times are
estimated within chunks. Never upload without full human timing review.
"""
import json
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
OUT=REPO.parent/"oct15-production"
CAPS=OUT/"captions"
CAPS.mkdir(parents=True,exist_ok=True)

def ts(seconds):
 ms=max(0,round(seconds*1000))
 h,ms=divmod(ms,3600000)
 m,ms=divmod(ms,60000)
 s,ms=divmod(ms,1000)
 return f"{h:02}:{m:02}:{s:02},{ms:03}"

for ep in ("pilot_021","pilot_022","long_010"):
 report=json.loads((OUT/"audio"/(ep+"_natural_qa.json")).read_text(encoding="utf-8"))
 segs=report["segments"]
 duration=report["audio_duration_seconds"]
 pauses=sum(seg["pause_ms"]/1000 for seg in segs)
 word_total=sum(x["words"] for x in segs)
 estimated=duration-pauses
 cursor=0.
 lines=[]
 for chunk in segs:
  if "start_seconds" in chunk:
   start=chunk["start_seconds"]
   speech=chunk["speech_duration_seconds"]
  else:
   start=cursor
   speech=estimated*chunk["words"]/word_total
  tokens=chunk["text"].split()
  group_time=speech/len(tokens)
  for n in range(0,len(tokens),8):
   stop=min(n+8,len(tokens))
   a=start+group_time*n
   b=start+group_time*stop
   lines.append((a,b," ".join(tokens[n:stop])))
  cursor=start+speech+chunk["pause_ms"]/1000
 file=CAPS/(ep+"_DRAFT_UNREVIEWED.srt")
 file.write_text("\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n" for i,(a,b,txt) in enumerate(lines,1)),encoding="utf-8")
 print(ep,"UNREVIEWED_SRT",len(lines),"cues",file)
