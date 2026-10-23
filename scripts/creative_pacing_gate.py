"""Fail-closed narration gap detector for FlowMinute visual review.

An FFmpeg silence check cannot prove that a human voice sounds natural.
Soundtrack music can mask dead narration; always listen to the vocal stem too.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path

START=re.compile(r"\bsilence_start:\s*([0-9.]+)")
END=re.compile(r"\bsilence_end:\s*([0-9.]+)")


def parse_silence_log(log: str, duration: float) -> list[tuple[float,float]]:
    result=[]
    current=None
    for line in log.splitlines():
        a=START.search(line)
        b=END.search(line)
        if a:
            if current is not None:
                raise ValueError("Nested silence_start")
            current=float(a.group(1))
        if b:
            if current is None:
                raise ValueError("Orphan silence_end")
            stop=float(b.group(1))
            if stop<current or stop>duration+.15:
                raise ValueError("Invalid time interval")
            result.append((current,stop))
            current=None
    if current is not None:
        result.append((current,duration))
    return result


def audit_intervals(intervals:list[tuple[float,float]], duration:float,
                    *, narration_start=8.0,max_gap=1.2,end_grace=.4)->dict:
    if not 0<=narration_start<duration or not .15<=max_gap<=3:
        raise ValueError("Unsafe pacing policy")
    rejected=[]
    for a,b in intervals:
        a=max(a,narration_start)
        b=min(b,duration)
        if b<=a:
            continue
        # Do not let the short's last quarter-second count as a pacing failure,
        # but never excuse several seconds of silence at the ending.
        permitted=max_gap+(end_grace if abs(b-duration)<.01 else 0)
        if b-a>permitted:
            rejected.append({"start_s":round(a,3),"end_s":round(b,3),
                            "gap_s":round(b-a,3)})
    return {"pass":not rejected,
            "max_allowed_explanation_gap_s":max_gap,
            "gaps_exceeding_maximum":rejected,
            "total_long_gap_seconds":round(sum(x["gap_s"] for x in rejected),3),
            "human_voice_review":False,
            "caveat":"Non-silent music may mask a missing speech track."}


def audit_file(path:Path,*,noise="-36dB",min_duration=.35,
               narration_start=8.,max_gap=1.2)->dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],
        check=True,capture_output=True,text=True)
    duration=float(p.stdout.strip())
    r=subprocess.run(["ffmpeg","-hide_banner","-nostdin","-i",str(path),
        "-af",f"silencedetect=noise={noise}:d={min_duration}",
        "-f","null","-"],capture_output=True,text=True)
    if r.returncode:
        raise RuntimeError("Audio audit failed: invalid media or unavailable FFmpeg")
    periods=parse_silence_log(r.stderr,duration)
    out=audit_intervals(periods,duration,narration_start=narration_start,max_gap=max_gap)
    out.update({"source_file":path.name,"source_duration_s":round(duration,3),
                "noise_threshold":noise,"min_gap_detected_s":min_duration})
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument("video",type=Path)
    p.add_argument("--narration-start",type=float,default=8.)
    p.add_argument("--max-gap",type=float,default=1.2)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    data=audit_file(args.video,narration_start=args.narration_start,max_gap=args.max_gap)
    body=json.dumps(data,indent=2)+"\n"
    if args.output:
        args.output.write_text(body,encoding="utf-8")
    print(body)
    if not data["pass"]:
        raise SystemExit(2)


if __name__=="__main__":
    main()
