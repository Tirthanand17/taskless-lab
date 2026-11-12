"""Clivox A5 media QA for ORIGINAL-ONLY demo renders.

FFprobe validates actual codec/duration, plus manifest/SRT, but passing
technical QA is never clip licensing, human editorial review or upload
authorization. No network or YouTube access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

from scripts.branch3_a5_render_original_demo import CLIVOX,digest_file

class MediaQARejected(ValueError):
    pass

def require(value: bool,reason: str) -> None:
    if not value:
        raise MediaQARejected("CLIVOX_A5_QA_DENY_"+reason)

CUE=re.compile(
    r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> "
    r"(\d{2}:\d{2}:\d{2},\d{3})\n([^\n]+(?:\n[^\n]+)?)\Z"
)

def srt_seconds(value: str) -> float:
    hh,mm,ss=value.split(":")
    seconds,ms=ss.split(",")
    return int(hh)*3600+int(mm)*60+int(seconds)+int(ms)/1000

def check_srt(raw: str, total_s: float) -> dict:
    # Source text is visual proposed script, not a speech transcript.
    require(type(raw) is str and raw.strip(),"SRT_EMPTY")
    cues=re.split(r"\n\s*\n",raw.strip())
    require(5<=len(cues)<=30,"SRT_CUE_COUNT")
    last=0.
    max_cps=0.
    for idx,chunk in enumerate(cues,1):
        m=CUE.fullmatch(chunk)
        require(m is not None and int(m[1])==idx,"SRT_STRUCTURE")
        start,end=map(srt_seconds,(m[2],m[3]))
        require(start>=last-0.002 and end>start+0.05
                and end<=total_s+0.15,"SRT_TIMECODES")
        last=end
        rows=m[4].split("\n")
        require(len(rows)<=2 and all(1<=len(row)<=30 for row in rows),
                "SRT_MOBILE_LINE_LENGTH")
        chars=sum(len(row) for row in rows)
        cps=chars/(end-start)
        max_cps=max(max_cps,cps)
        require(cps<=30,"SRT_TOO_FAST")
        require("http://" not in m[4] and "https://" not in m[4],
                "SOURCE_URL_IN_CAPTION")
    require(abs(last-total_s)<=0.15,"SRT_NOT_COVERING_FULL_PLAN")
    return {"cue_count":len(cues),"max_visual_text_chars_per_second":round(max_cps,2),
            "is_audio_transcript":False,"is_visual_editorial_plan":True}

def probe_file(file: Path) -> dict:
    require(file.is_file() and not file.is_symlink(),"MP4_FILE")
    require(file.stat().st_size>100_000,"MP4_TOO_SMALL")
    result=subprocess.run(
        ["ffprobe","-v","error","-show_entries",
         "format=duration,size:stream=codec_name,codec_type,width,height,"
         "pix_fmt,avg_frame_rate,sample_rate,channels",
         "-of","json",str(file)],
        check=True,capture_output=True,text=True,timeout=30,
    )
    return json.loads(result.stdout)

def check_metadata(probe: dict, manifest: dict, srt: str,
                   *, media_path: Path|None=None, captions_path: Path|None=None) -> dict:
    require(type(probe) is dict and type(manifest) is dict,"INPUT")
    require(manifest.get("schema_version")==1
            and manifest.get("channel_id")==CLIVOX
            and manifest.get("stage")=="A5_ORIGINAL_ONLY_SYNTHETIC_BENCHMARK",
            "NOT_SYNTHETIC_STAGE")
    require(manifest.get("mode") in ("preview","full"),"MODE")
    expected=(1080,1920,30) if manifest["mode"]=="full" else (540,960,24)
    video=[s for s in probe.get("streams",[]) if s.get("codec_type")=="video"]
    audio=[s for s in probe.get("streams",[]) if s.get("codec_type")=="audio"]
    require(len(video)==len(audio)==1,"TRACK_COUNT")
    v,a=video[0],audio[0]
    require(v.get("codec_name")=="h264"
            and (v.get("width"),v.get("height"))==expected[:2]
            and v.get("pix_fmt")=="yuv420p","VIDEO_FORMAT")
    fps=v.get("avg_frame_rate","")
    require(type(fps) is str and "/" in fps,"FPS_INVALID")
    numerator,denominator=map(int,fps.split("/"))
    require(denominator>0 and abs(numerator/denominator-expected[2])<0.1,"FPS")
    require(a.get("codec_name")=="aac" and str(a.get("sample_rate"))=="48000"
            and a.get("channels") in (1,2),"AUDIO_FORMAT")
    duration=float(probe.get("format",{}).get("duration",0))
    require(39.5<=duration<=40.3,"VIDEO_DURATION")
    require(manifest.get("source_media_attached") is False
            and manifest.get("third_party_source_audio_used") is False
            and manifest.get("original_voiceover_recorded") is False
            and manifest.get("source_placeholder_visible") is True,
            "UNTRUSTED_SOURCE_MEDIA")
    require(manifest.get("audio_content")==
            "LOW_VOLUME_ORIGINAL_SYNTHETIC_TONES_NOT_NARRATION"
            and manifest.get("subtitle_content")==
            "PROPOSED_ON_SCREEN_EDITORIAL_TEXT_NOT_SPEECH_TRANSCRIPT",
            "FALSE_AUDIO_OR_CAPTION_CLAIM")
    require(manifest.get("watermark")==
            "DEMO ONLY / NOT CLEARED FOR YOUTUBE RELEASE","MISSING_DEMO_WATERMARK")
    for flag in ("reviewed_by_human","actual_media_qa_passed",
                 "copyright_clearance_verified","ready_to_upload",
                 "ready_to_schedule","ready_to_publish"):
        require(manifest.get(flag) is False,"FALSE_APPROVAL_"+flag)
    require(type(manifest.get("video_sha256")) is str and
            re.fullmatch(r"[0-9a-f]{64}",manifest["video_sha256"]) is not None,
            "MISSING_MEDIA_DIGEST")
    require(type(manifest.get("srt_sha256")) is str and
            re.fullmatch(r"[0-9a-f]{64}",manifest["srt_sha256"]) is not None,
            "MISSING_SRT_DIGEST")
    if media_path is not None:
        require(digest_file(media_path)==manifest["video_sha256"],
                "VIDEO_HASH_MISMATCH")
    if captions_path is not None:
        require(digest_file(captions_path)==manifest["srt_sha256"],
                "SRT_HASH_MISMATCH")
    srt_report=check_srt(srt,40)
    return {
        "stage":"A5_ORIGINAL_ONLY_AV_TECHNICAL_CHECK",
        "channel_id":CLIVOX,
        "mode":manifest["mode"],
        "codec":"h264","resolution":f"{v['width']}x{v['height']}",
        "frame_rate":round(numerator/denominator,3),
        "audio_codec":"aac","audio_sample_rate_hz":48000,
        "duration_seconds":round(duration,3),
        "srt":srt_report,"ffprobe_checked":True,
        "synthetic_video_technical_checks_passed":True,
        "licensed_media_qa_completed":False,
        "voiceover_and_production_mix_qa_completed":False,
        "owner_final_video_review_completed":False,
        "source_rights_verified":False,
        "ready_to_publish":False,
        "youtube_upload_authorized":False,
    }

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,required=True)
    args=parser.parse_args()
    folder=args.directory
    require(folder.is_dir() and not folder.is_symlink(),"DIRECTORY")
    mf=folder/"synthetic-demo-manifest.json"
    require(mf.is_file(),"MANIFEST_MISSING")
    manifest=json.loads(mf.read_text("utf-8"))
    mp4=folder/manifest["video_name"]
    srt=folder/manifest["srt_name"]
    require(mp4.parent==folder and srt.parent==folder
            and not mp4.is_symlink() and not srt.is_symlink(),"UNSAFE_PATH")
    report=check_metadata(probe_file(mp4),manifest,srt.read_text("utf-8"),
                          media_path=mp4,captions_path=srt)
    out=folder/"synthetic-technical-qa-report.json"
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,sort_keys=True))
    print("CLIVOX_A5_SYNTHETIC_TECH_QA_PASS_RELEASE_DISABLED")

if __name__=="__main__":
    main()
