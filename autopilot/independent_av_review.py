"""Independent FFmpeg technical reviewer for Branch 2 original cloud fixtures.

Reads already encoded MP4, original PNGs and SRT. Audio loudness, true peak,
silences, actual burned-caption pixel changes, scene variation and transcript
correspondence are tested. NO rights/factual/human playback or YouTube approval.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import subprocess

from autopilot.full_pack_fixture import EPISODES
from autopilot.cloud_full_duration_pack import sentence_chunks, PackError

AUDIO_TECHNICAL_STATUS = "MEASURED_TECHNICAL_QA_ONLY_NOT_EDITORIAL_APPROVAL"


class ReviewerError(ValueError):
    pass


def _run(cmd: list[str], timeout_s: int = 420) -> tuple[str, str]:
    try:
        x=subprocess.run(cmd, check=True, capture_output=True,text=True,timeout=timeout_s)
        return x.stdout,x.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        raise ReviewerError("Independent FFmpeg inspection failed: "+type(exc).__name__) from exc


def parse_loudnorm(stderr: str) -> dict:
    """Parse the real loudnorm analysis-only summary, not source claims."""
    if not isinstance(stderr,str) or len(stderr)>2_000_000:
        raise ReviewerError("Invalid audio observation")
    chunks=re.findall(r'\{\s*"input_i"\s*:\s*"[^"]+"[\s\S]*?\}',stderr)
    if len(chunks)!=1:
        raise ReviewerError("Expected one FFmpeg audio loudness JSON summary")
    try:
        src=json.loads(chunks[0])
        measured={k:float(src[k]) for k in ("input_i","input_tp","input_lra")}
    except (KeyError,ValueError,TypeError) as exc:
        raise ReviewerError("Invalid FFmpeg loudness numbers") from exc
    if not all(math.isfinite(x) for x in measured.values()):
        raise ReviewerError("Nonfinite loudness is silent or invalid media")
    if measured["input_i"] < -31 or measured["input_i"] > -7:
        raise ReviewerError("Audio grossly quiet or overloaded: requires correction")
    if measured["input_tp"] > 0:
        raise ReviewerError("Unsafe true-peak audio")
    return {
        "integrated_lufs":round(measured["input_i"],2),
        "true_peak_dbtp":round(measured["input_tp"],2),
        "loudness_range_lu":round(measured["input_lra"],2),
        "typical_online_video_target_diagnostic":(-20<=measured["input_i"]<=-12 and measured["input_tp"]<=-1.5),
        "independent_human_listening_completed":False,
    }


def parse_silence_observations(stderr: str) -> dict:
    if not isinstance(stderr,str) or len(stderr)>2_000_000:
        raise ReviewerError("Invalid silence observation")
    matches=[float(x) for x in re.findall(r'silence_duration:\s*(\d+(?:\.\d+)?)',stderr)]
    if len(matches)>100 or any(not math.isfinite(x) or x>3600 for x in matches):
        raise ReviewerError("Malformed/unbounded silence results")
    return {"long_silence_count":len(matches),
            "longest_silence_seconds":round(max(matches,default=0),2),
            "human_audio_inspection_required":True}


def _timestamp(raw:str)->float:
    match=re.fullmatch(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})",raw)
    if not match:raise ReviewerError("Malformed SRT time")
    h,m,s,ms=map(int,match.groups())
    if m>59 or s>59:return _fail_time()
    return h*3600+m*60+s+ms/1000


def _fail_time():
    raise ReviewerError("Out-of-range SRT time digits")


def verify_srt_against_script(path:Path, episode, video_seconds:float)->dict:
    if not path.is_file() or path.stat().st_size>200_000:
        raise ReviewerError("Missing or unexpectedly large SRT")
    raw=path.read_text(encoding="utf8").replace("\r\n","\n")
    blocks=[x.strip() for x in re.split(r"\n\s*\n",raw) if x.strip()]
    original=[s for scene in episode.scenes for s in sentence_chunks(scene.narration)]
    if len(blocks)!=len(original):
        raise ReviewerError("Some spoken lines have no SRT cue")
    previous=0.0
    starts=[]
    for i,(block,spoken) in enumerate(zip(blocks,original),1):
        lines=block.splitlines()
        if len(lines)<3 or lines[0]!=str(i):
            raise ReviewerError("SRT index missing/reordered")
        match=re.fullmatch(r"(\S+) --> (\S+)",lines[1])
        if not match:
            raise ReviewerError("Bad SRT cue separator")
        start,end=(_timestamp(x) for x in match.groups())
        if not previous-0.001<=start<end<=video_seconds+0.4:
            raise ReviewerError("SRT scene timing overlap or clipping")
        previous=end
        actual=" ".join(" ".join(lines[2:]).split())
        if actual!=spoken:
            raise ReviewerError("SRT spoken script does not match original narration")
        starts.append(start)
    if video_seconds-previous>1.5:
        raise ReviewerError("Missing caption at narration tail")
    return {"verified_srt_cue_count":len(original),
            "every_caption_matches_original_spoken_text":True,
            "all_cues_monotone_and_in_video":True,
            "exact_word_forced_alignment_claimed":False,
            "human_spoken_word_accuracy_approved":False}


def changed_pixels(source:Path,encoded:Path,region:tuple[int,int,int,int],threshold:int=76)->int:
    from PIL import Image,ImageChops
    import numpy as np
    try:
        with Image.open(source) as a,Image.open(encoded) as b:
            if a.size!=b.size:
                raise ReviewerError("Encoded video snapshot dimensions changed")
            diff=ImageChops.difference(a.convert("RGB").crop(region),
                                       b.convert("RGB").crop(region))
            count=int((np.asarray(diff).max(axis=2)>threshold).sum())
    except (OSError,ValueError) as exc:
        raise ReviewerError("Unable to decode actual screenshot pixel data") from exc
    return count


def _snapshot(mp4:Path,when:float,out:Path)->None:
    _run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
          "-ss",f"{when:.3f}","-i",str(mp4),
          "-frames:v","1","-update","1","-y",str(out)],timeout_s=100)
    if not out.exists() or out.stat().st_size<1000:
        raise ReviewerError("Cannot sample encoded video frames")


def review_encoded_episode(folder:Path,episode, *,report_entry:dict)->dict:
    mp4=folder/"UNAPPROVED_FULL_EDUCATION_TEST.mp4"
    srt=folder/"scene_captions.srt"
    first=folder/"scene_01.png"
    last=folder/f"scene_{len(episode.scenes):02}.png"
    if not all(p.is_file() for p in (mp4,srt,first,last)):
        raise ReviewerError("Missing original render evidence")
    seconds=report_entry["seconds"]
    if report_entry["episode"]!=episode.episode_id or seconds<=20:
        raise ReviewerError("Video and proposed episode mismatch")
    srts=verify_srt_against_script(srt,episode,seconds)
    _,stderr=_run(["ffmpeg","-hide_banner","-nostdin","-nostats",
                   "-i",str(mp4),"-map","0:a:0",
                   "-af","loudnorm=print_format=json","-f","null","-"],timeout_s=450)
    audio=parse_loudnorm(stderr)
    _,silence=_run(["ffmpeg","-hide_banner","-nostdin","-nostats",
                   "-i",str(mp4),"-map","0:a:0",
                   "-af","silencedetect=noise=-45dB:duration=1.25",
                   "-f","null","-"],timeout_s=450)
    pauses=parse_silence_observations(silence)
    # Test at first spoken cue where captions SHOULD be visible.
    chunks=[x.strip() for x in re.split(r"\n\s*\n",srt.read_text(encoding="utf8")) if x.strip()]
    one=chunks[0].splitlines()[1].split(" --> ")
    cue_time=(_timestamp(one[0])+_timestamp(one[1]))/2
    startshot=folder/"encoded_caption_snapshot.png"
    _snapshot(mp4,cue_time,startshot)
    width,height=((1080,1920) if episode.kind=="short" else (1920,1080))
    crop=(185,height-385,width-185,height-125) if episode.kind=="short" else (225,height-265,width-225,height-75)
    changed=changed_pixels(first,startshot,crop)
    if changed<350:
        # Numeric-only vertical scan diagnoses a caption positioned in the
        # wrong ASS region. Never export screenshot bytes or weaken approval.
        bands=[]
        for i in range(8):
            y0=height*i//8
            y1=height*(i+1)//8
            bands.append(changed_pixels(first,startshot,(185,y0,width-185,y1),threshold=90))
        raise ReviewerError(
            f"Burned subtitles not in bottom caption panel: pixels={changed}, screen_bands={bands}")
    # Check a late scene frame differs substantively from the early scene,
    # beyond the caption strip or the moving progress accent.
    ffconcat=folder/"scene_order.ffconcat"
    contents=ffconcat.read_text(encoding="utf8")
    durations=[float(x) for x in re.findall(r"(?m)^duration\s+(\d+(?:\.\d+)?)[ \t]*$",contents)]
    if len(durations)!=len(episode.scenes):
        raise ReviewerError("Source scene timeline mismatch")
    last_start=sum(durations[:-1])
    last_mid=min(seconds-.25,last_start+min(durations[-1]/2,2.5))
    endshot=folder/"encoded_last_scene_snapshot.png"
    _snapshot(mp4,last_mid,endshot)
    scene_crop=(100,175,width-100,height-470 if episode.kind=="short" else height-305)
    scene_change=changed_pixels(startshot,endshot,scene_crop)
    if scene_change<5_000:
        raise ReviewerError("Encodings do not show substantive original scene changes")
    return {
       "episode":episode.episode_id,
       "status":AUDIO_TECHNICAL_STATUS,
       "ffmpeg_actual_encoded_audio":audio,
       "ffmpeg_long_silence_diagnostics":pauses,
       **srts,
       "caption_visible_changed_pixels":changed,
       "first_to_later_scene_changed_pixels":scene_change,
       "burned_caption_independently_observed":True,
       "distinct_encoded_scenes_observed":True,
       "independent_claim_or_rights_review_complete":False,
       "human_complete_watch_or_listen_complete":False,
       "youtube_upload_enabled":False,
       "youtube_schedule_enabled":False,
    }


def review_full_pack(folder:Path)->dict:
    report_file=folder/"technical_report.json"
    report=json.loads(report_file.read_text(encoding="utf8"))
    if report.get("status")!="FULL_DURATION_EDUCATIONAL_TECHNICAL_BENCHMARK_NOT_PUBLISHABLE":
        raise ReviewerError("Refuse any release-labelled media as technical sample")
    rows=report.get("videos",[])
    if len(rows)!=3 or [x.get("episode") for x in rows]!=[x.episode_id for x in EPISODES]:
        raise ReviewerError("Wrong or re-ordered three-pack media")
    results=[review_encoded_episode(folder/ep.episode_id,ep,report_entry=record)
             for ep,record in zip(EPISODES,rows)]
    return {
       "schema_version":1,
       "status":AUDIO_TECHNICAL_STATUS,
       "episodes":results,
       "machine_checked_count":3,
       "release_authorized":False,
       "human_editorial_approval":False,
       "credentials_used":False,
       "youtube_upload_enabled":False,
       "next_gate":"Independent human full-playback, correctness, rights and source-backed creative review; real AI agent-generated scripts",
    }


def main()->None:
    import argparse
    p=argparse.ArgumentParser(description="Independent encoded media QA; no remote writes")
    p.add_argument("--pack-dir",type=Path,required=True)
    args=p.parse_args()
    summary=review_full_pack(args.pack_dir)
    target=args.pack_dir/"independent_technical_qa.json"
    target.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf8")
    print(json.dumps({
        "status":summary["status"],
        "count":len(summary["episodes"]),
        "lufs":[x["ffmpeg_actual_encoded_audio"]["integrated_lufs"] for x in summary["episodes"]],
        "true_peak":[x["ffmpeg_actual_encoded_audio"]["true_peak_dbtp"] for x in summary["episodes"]],
        "burned_caption_checks":[x["burned_caption_independently_observed"] for x in summary["episodes"]],
        "encoded_scene_variation":[x["distinct_encoded_scenes_observed"] for x in summary["episodes"]],
        "youtube_upload_enabled":False,
    }),flush=True)


if __name__=="__main__":
    main()
