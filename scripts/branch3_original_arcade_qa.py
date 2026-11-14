"""Independent actual FFprobe/manifest/caption QA for original arcade REVIEW only.

No copyrighted external media can be accepted as a source by catalog contract.
No technical QA result may set YouTube upload or public release flags.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import wave

from scripts.branch3_original_arcade_pilots import (
    ROOT,CATALOG,CHANNEL,validate_catalog,render_size,sha,stamp,
    ArcadeDenied
)

TIMING=re.compile(
    r"(\d+)\n(\d\d:\d\d:\d\d,\d\d\d) --> "
    r"(\d\d:\d\d:\d\d,\d\d\d)\n(.+)",
    flags=re.S
)
HASH=re.compile(r"[a-f0-9]{64}\Z")


class OriginalQARejected(ValueError):
    pass


def require(ok:bool,why:str)->None:
    if not ok:
        raise OriginalQARejected("CLIVOX_ORIGINAL_QA_DENIED_"+why)


def srt_seconds(value:str)->float:
    hours,minutes,rest=value.split(":")
    seconds,millis=rest.split(",")
    return int(hours)*3600+int(minutes)*60+int(seconds)+int(millis)/1000.0


def check_caption_draft(content:str,duration:int)->dict:
    require(type(content) is str and 0<len(content)<=30_000,
            "CAPTION_TEXT")
    sections=re.split(r"\n\s*\n",content.strip())
    require(5<=len(sections)<=70,"CAPTION_COUNT")
    last=0
    for i,section in enumerate(sections,1):
        m=TIMING.fullmatch(section)
        require(m is not None and int(m[1])==i,"SRT_CUE_SEQUENCE")
        start,end=srt_seconds(m[2]),srt_seconds(m[3])
        require(start>=last-.002 and end>start+.05
                and end<=duration+.2,"CUE_CLOCK")
        lines=m[4].split("\n")
        require(1<=len(lines)<=2
                and all(0<len(line)<=36 for line in lines)
                and not any("http" in line.lower() for line in lines),
                "CUE_MOBILE_SAFE")
        last=end
    require(abs(last-duration)<.2,"SRT_NOT_FULL_TIMELINE")
    return {"draft_caption_cues":len(sections),
            "owner_must_review_speech_sync":True,
            "machine_forced_alignment_proven":False}


def visible_caption_safezone_qa(video:Path,srt:str)->dict:
    """Independent decoded-frame QA: on-screen white subtitle ink MUST be
    visible in lower-middle safe zone, not offscreen or over the headline.

    Original scene artwork here uses orange/violet/mint, not white, at this
    lower-panel location; opaque caption glyphs are white. The zero-external-
    media frame check is a regression signal, not aesthetic or content approval.
    """
    from PIL import Image
    require(video.is_file() and not video.is_symlink()
            and video.stat().st_size>100_000,"CAPTION_VIDEO_MISSING")
    sections=re.split(r"\n\s*\n",srt.strip())
    require(len(sections)>0,"CAPTION_CUES_MISSING")
    m=TIMING.fullmatch(sections[0])
    require(m is not None,"FIRST_CAPTION_CUE_BAD")
    start,end=srt_seconds(m[2]),srt_seconds(m[3])
    require(0<=start<end and end-start>.05,"CAPTION_START_INVALID")
    moment=start+(end-start)/2
    result=subprocess.run([
        "ffmpeg","-hide_banner","-loglevel","error","-nostdin",
        "-ss",f"{moment:.3f}","-i",str(video),
        "-frames:v","1","-f","image2pipe","-vcodec","png","pipe:1"
    ],capture_output=True,check=True,timeout=45)
    require(2_000<len(result.stdout)<12_000_000,"CAPTION_FRAME_DECODE")
    with Image.open(BytesIO(result.stdout)) as original:
        im=original.convert("RGB")
    w,h=im.size
    require(w>=540 and h>=540,"CAPTION_FRAME_DIMENSIONS")
    x0,x1=round(w*.13),round(w*.87)
    y0,y1=round(h*.70),round(h*.875)
    zone=im.crop((x0,y0,x1,y1))
    # Detect sufficiently bright non-neutral-graphic text pixels only in
    # the caption safe zone; colored arcade art doesn't satisfy this.
    white=sum(1 for pixel in zone.getdata()
              if pixel[0]>=195 and pixel[1]>=195 and pixel[2]>=195)
    min_white=max(35,round(w*h*.00010))
    require(white>=min_white,"BURNED_CAPTION_MISSING_OR_OFFSCREEN")
    return {
        "first_voice_cue_visible_in_safe_zone":True,
        "white_text_pixel_count_in_safe_zone":white,
        "minimum_required_white_caption_pixels":min_white,
        "caption_sampled_from_actual_encoded_frame":True,
        "caption_layout_human_approved":False,
    }


def probe(path:Path)->dict:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_size>100_000,
            "VIDEO_FILE_REQUIRED")
    r=subprocess.run([
        "ffprobe","-v","error",
        "-show_entries",
        "stream=codec_name,codec_type,width,height,pix_fmt,"
        "avg_frame_rate,sample_rate,channels:"
        "format=duration,size",
        "-of","json",str(path)
    ],capture_output=True,text=True,check=True,timeout=40)
    return json.loads(r.stdout)


def validate_episode_report(episode:dict,manifest:dict,
                            probe_result:dict,subtitles:str,
                            *,video:Path|None=None,audio:Path|None=None,
                            captions:Path|None=None)->dict:
    require(type(manifest) is dict
            and manifest.get("schema_version")==1
            and manifest.get("channel_id")==CHANNEL
            and manifest.get("stage")==
              "A4_A5_ORIGINAL_FIRST_PARTY_EDITORIAL_REVIEW_NOT_RELEASE"
            and manifest.get("episode_id")==episode["id"]
            and manifest.get("format")==episode["format"]
            and manifest.get("duration_seconds")==episode["duration_seconds"],
            "MANIFEST_IDENTITY")
    require(manifest.get("title")==episode["title"]
            and manifest.get("description")==episode["description"]
            and manifest.get("render_mode") in ("preview","full"),
            "MANIFEST_EDITORIAL_META")
    expected=render_size(episode["format"],manifest["render_mode"])
    require((manifest.get("output_width"),
             manifest.get("output_height"),manifest.get("fps"))==expected,
            "MANIFEST_DIMENSIONS")
    require(manifest.get("scene_count")==len(episode["beats"]),"SCENES")
    for key in ("source_media_downloaded",
                "external_images_video_or_audio_used",
                "real_voice_actor_or_music_license_verified",
                "human_editorial_review_completed",
                "owner_exact_asset_signed",
                "ready_to_upload","ready_to_schedule","ready_to_publish"):
        require(manifest.get(key) is False,"FALSE_CLEARANCE_"+key)
    for key in ("original_script_and_vector_art",
                "tts_voice_synthetic_not_human_recording",
                "srt_is_draft_not_forced_aligned",
                "srt_measured_synthesized_pcm_speech_windows",
                "srt_word_timing_is_estimated_not_forced_aligned",
                "draft_captions_burned_into_review_mp4"):
        require(manifest.get(key) is True,"FALSE_ORIGINALITY_"+key)
    require(manifest.get("actual_external_api_calls")==0,
            "UNTRUSTED_EXTERNAL_CALL")
    for key in ("video_sha256","audio_sha256","subtitle_sha256"):
        require(type(manifest.get(key)) is str
                and HASH.fullmatch(manifest[key]) is not None,
                "FILE_HASH_MISSING")
    require(manifest.get("video_file")=="original-review-preview.mp4"
            and manifest.get("audio_file")==
              "original-tts-and-procedural-ambience.wav"
            and manifest.get("subtitle_file")=="narration-timing-draft.srt",
            "UNEXPECTED_OUTPUT_FILE")
    require(type(probe_result) is dict,"PROBE_MISSING")
    streams=probe_result.get("streams",[])
    videos=[s for s in streams if s.get("codec_type")=="video"]
    audios=[s for s in streams if s.get("codec_type")=="audio"]
    require(len(videos)==1 and len(audios)==1,"STREAM_COUNT")
    vid,au=videos[0],audios[0]
    require(vid.get("codec_name")=="h264"
            and vid.get("pix_fmt")=="yuv420p"
            and (vid.get("width"),vid.get("height"))==expected[:2],
            "VIDEO_FORMAT")
    fps=vid.get("avg_frame_rate")
    require(type(fps) is str and "/" in fps,"FPS_TYPE")
    n,d=map(int,fps.split("/"))
    require(d>0 and abs(n/d-expected[2])<.1,"VIDEO_FPS")
    require(au.get("codec_name")=="aac"
            and str(au.get("sample_rate"))=="48000"
            and au.get("channels") in (1,2),"AUDIO_FORMAT")
    duration=float(probe_result.get("format",{}).get("duration",0))
    require(abs(duration-episode["duration_seconds"])<.65,"DURATION")
    caption_report=check_caption_draft(
        subtitles,episode["duration_seconds"]
    )
    caption_visual=None
    if video is not None:
        caption_visual=visible_caption_safezone_qa(video,subtitles)
        require(sha(video)==manifest["video_sha256"],"VIDEO_SHA_TAMPER")
        require(video.stat().st_size==manifest.get("video_bytes"),
                "VIDEO_SIZE")
    if captions is not None:
        require(sha(captions)==manifest["subtitle_sha256"],
                "CAPTION_SHA_TAMPER")
    if audio is not None:
        require(sha(audio)==manifest["audio_sha256"],"AUDIO_SHA_TAMPER")
        require(audio.is_file() and not audio.is_symlink(),
                "AUDIO_FILE")
        with wave.open(str(audio),"rb") as wav:
            require(wav.getnchannels()==1 and wav.getsampwidth()==2
                    and wav.getframerate()==48000
                    and abs(wav.getnframes()/48000-
                            episode["duration_seconds"])<.1,
                    "AUDIO_WAV_FORMAT")
            sample=wav.readframes(min(wav.getnframes(),48000))
            require(any(sample), "SILENT_AUDIO")
    return {
        "stage":"A5_ORIGINAL_FIRST_PARTY_FFPROBE_HUMAN_REVIEW_PENDING",
        "episode_id":episode["id"],
        "format":episode["format"],
        "duration_seconds":round(duration,3),
        "actual_ffprobe_checks_passed":True,
        "resolution":f"{expected[0]}x{expected[1]}",
        "audio_is_synthetic_narration_and_procedural_ambience":True,
        "draft_caption_speech_window_derived_from_synthesized_pcm":True,
        "draft_captions_burned_in_mobile_review_mp4":True,
        "decoded_actual_frame_caption_safezone_qa":caption_visual,
        "subtitle_visual_editor_approval_completed":False,
        "human_word_alignment_verified":False,
        "captions":caption_report,
        "human_editorial_video_review_completed":False,
        "owner_final_asset_signature_exists":False,
        "real_clivox_private_first_upload_exists":False,
        "licensed_creator_media_included":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_external_api_calls":0
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--selection",choices=("one","all"),default="one")
    args=p.parse_args()
    require(args.directory.is_absolute() and args.directory.is_dir()
            and not args.directory.is_symlink()
            and ROOT not in args.directory.parents,
            "OUTPUT_OUTSIDE_PUBLIC_REPO")
    episodes=validate_catalog(json.loads(CATALOG.read_text("utf-8")))
    if args.selection=="one":
        episodes=episodes[:1]
    results=[]
    for episode in episodes:
        folder=args.directory/episode["id"]
        require(folder.is_dir() and not folder.is_symlink(),"MISSING_EPISODE")
        man_file=folder/"review-manifest.json"
        require(man_file.is_file() and not man_file.is_symlink(),
                "MISSING_MANIFEST")
        manifest=json.loads(man_file.read_text("utf-8"))
        vid=folder/"original-review-preview.mp4"
        wav=folder/"original-tts-and-procedural-ambience.wav"
        srt=folder/"narration-timing-draft.srt"
        result=validate_episode_report(
            episode,manifest,probe(vid),srt.read_text("utf-8"),
            video=vid,audio=wav,captions=srt
        )
        (folder/"technical-review-qa.json").write_text(
            json.dumps(result,indent=2)+"\n",encoding="utf-8"
        )
        results.append(result)
    print(json.dumps({"episode_reports":results,
                      "human_review_pending":True,
                      "youtube_upload_or_schedule_authorized":False},
                     sort_keys=True))


if __name__=="__main__":
    main()
