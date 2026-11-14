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

from scripts.branch3_a5_narration_energy_qa import audit_original_narration
from scripts.branch3_a5_speech_boundaries import audit_mixed_speech_caption_bounds

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


def check_caption_draft(
    content:str,duration:int,*,allow_speech_end_before_outro:bool=False
)->dict:
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
    require(type(allow_speech_end_before_outro) is bool,
            "DRAFT_TAIL_POLICY")
    if allow_speech_end_before_outro:
        require(duration-12 <= last <= duration+.2,
                "SRT_NOT_IN_FINAL_SCENE")
    else:
        require(abs(last-duration)<.2,"SRT_NOT_FULL_TIMELINE")
    return {"draft_caption_cues":len(sections),
            "draft_last_voice_caption_end_seconds":round(last,3),
            "silence_tail_allowed_for_final_scene":allow_speech_end_before_outro,
            "owner_must_review_speech_sync":True,
            "machine_forced_alignment_proven":False}


def cue_samples_by_beat(
    content:str, beats:list[dict], duration:int
)->list[dict]:
    """Pick one actual cue midpoint in EVERY scene beat (never OCR/word sync)."""
    require(type(content) is str and type(beats) is list
            and 1<=len(beats)<=20 and type(duration) is int
            and 1<=duration<=600,"BEAT_SAMPLE_INPUT")
    sections=re.split(r"\n\s*\n",content.strip())
    cues=[]
    for section in sections:
        m=TIMING.fullmatch(section)
        require(m is not None,"BEAT_SAMPLE_SRT_FORMAT")
        start,end=srt_seconds(m[2]),srt_seconds(m[3])
        require(0<=start<end<=duration+.2,"BEAT_SAMPLE_CLOCK")
        cues.append((start,end))
    samples=[]
    previous_beat_end=0
    for index,beat in enumerate(beats):
        require(type(beat) is dict and
                type(beat.get("start_s")) is int and
                type(beat.get("end_s")) is int and
                beat["start_s"]==previous_beat_end and
                beat["start_s"]<beat["end_s"]<=duration,
                "BEAT_SAMPLE_CONTINUITY")
        previous_beat_end=beat["end_s"]
        matched=next((
            (start,end) for start,end in cues
            if start>=beat["start_s"]-.003 and
               end<=beat["end_s"]+.003
        ),None)
        require(matched is not None,
                "BEAT_WITHOUT_VISIBLE_SPOKEN_CAPTION")
        start,end=matched
        samples.append({
            "beat_index":index,
            "time_s":round((start+end)/2,3),
        })
    require(previous_beat_end==duration,"BEAT_SAMPLE_TOTAL_DURATION")
    return samples


def cue_samples_all_cues(
    content:str, beats:list[dict], duration:int
)->list[dict]:
    """Select midpoint of EVERY draft SRT cue in its own storyboard beat.

    The contact sheet deliberately shows one frame per beat, but encoded
    subtitle QA must also catch a late cue that disappears after the first
    visible cue in that same beat. This is pixel visibility, NOT OCR or ASR.
    """
    # Reuse the existing contiguous storyboard/coverage validator. This
    # also guarantees each beat has at least one qualifying subtitle cue.
    beat_points=cue_samples_by_beat(content,beats,duration)
    require(len(beat_points)==len(beats),"ALL_CUES_BEAT_COVERAGE")
    chunks=re.split(r"\n\s*\n",content.strip())
    require(1<=len(chunks)<=70,"ALL_CUES_COUNT")
    points=[]
    previous_end=0.0
    for cue_index,chunk in enumerate(chunks):
        match=TIMING.fullmatch(chunk)
        require(match is not None and int(match[1])==cue_index+1,
                "ALL_CUES_SEQUENCE")
        start,end=srt_seconds(match[2]),srt_seconds(match[3])
        require(0<=start<end<=duration+.002 and
                start>=previous_end-.002,"ALL_CUES_TIMING")
        previous_end=end
        matching=[
            i for i,beat in enumerate(beats)
            if start>=beat["start_s"]-.003 and
               end<=beat["end_s"]+.003
        ]
        require(len(matching)==1,
                "CUE_CROSSES_SCENE_"+str(cue_index))
        points.append({
            "cue_index":cue_index,
            "beat_index":matching[0],
            "time_s":round((start+end)/2,3),
        })
    require(len({x["beat_index"] for x in points})==len(beats),
            "ALL_CUES_SCENE_COVERAGE")
    return points


def decode_actual_frame(video:Path,time_s:float):
    """Read a single video frame with bounded FFmpeg output, no temp files."""
    from PIL import Image
    require(isinstance(video,Path) and video.is_file()
            and not video.is_symlink()
            and 100_000<video.stat().st_size<300_000_000,
            "CAPTION_VIDEO_MISSING")
    require(type(time_s) in (int,float) and
            0<=time_s<=600,"INVALID_FRAME_TIMESTAMP")
    result=subprocess.run([
        "ffmpeg","-hide_banner","-loglevel","error","-nostdin",
        "-ss",f"{time_s:.3f}","-i",str(video),
        "-frames:v","1","-f","image2pipe","-vcodec","png","pipe:1"
    ],capture_output=True,check=True,timeout=45)
    require(2_000<len(result.stdout)<12_000_000,"CAPTION_FRAME_DECODE")
    with Image.open(BytesIO(result.stdout)) as original:
        im=original.convert("RGB")
    w,h=im.size
    require(w>=540 and h>=540 and w<=1920 and h<=1920,
            "CAPTION_FRAME_DIMENSIONS")
    return im


def visible_caption_safezone_qa(
    video:Path,srt:str,beats:list[dict]|None=None
)->dict:
    """Inspect EVERY SRT cue in the actual encoded MP4, not just each beat.

    The lower-middle safe region is tested for visible caption-like white ink.
    Source-free original artwork is deliberately cleared from that region.
    Pixel visibility does NOT authenticate transcript words or owner review.
    """
    require(type(srt) is str,"SRT_SOURCE_TYPE")
    sections=re.split(r"\n\s*\n",srt.strip())
    require(len(sections)>=1,"CAPTION_CUES_MISSING")
    m=TIMING.fullmatch(sections[0])
    require(m is not None,"FIRST_CAPTION_CUE_BAD")
    a,b=srt_seconds(m[2]),srt_seconds(m[3])
    require(0<=a<b and b-a>.05,"CAPTION_START_INVALID")
    if beats is None:
        samples=[{"beat_index":0,"time_s":round((a+b)/2,3)}]
    else:
        require(type(beats) is list and 1<=len(beats)<=20,
                "VISUAL_BEAT_LIST")
        samples=cue_samples_all_cues(srt,beats,beats[-1]["end_s"])
    result_samples=[]
    for sample in samples:
        im=decode_actual_frame(video,sample["time_s"])
        w,h=im.size
        x0,x1=round(w*.13),round(w*.87)
        y0,y1=round(h*.70),round(h*.875)
        zone=im.crop((x0,y0,x1,y1))
        white=sum(1 for pixel in zone.getdata()
                  if pixel[0]>=195 and pixel[1]>=195 and pixel[2]>=195)
        min_white=max(35,round(w*h*.00010))
        require(white>=min_white,
                "BURNED_CAPTION_MISSING_OR_OFFSCREEN_BEAT_"+
                    str(sample["beat_index"])+"_CUE_"+
                    str(sample.get("cue_index",0)))
        result_samples.append({
            "beat_index":sample["beat_index"],
            "cue_index":sample.get("cue_index",0),
            "time_s":sample["time_s"],
            "white_text_pixel_count":white,
            "minimum_required_pixels":min_white,
        })
    return {
        "first_voice_cue_visible_in_safe_zone":True,
        "every_storyboard_beat_caption_visible_in_safe_zone":True,
        "every_draft_caption_cue_visible_in_safe_zone":beats is not None,
        "actual_encoded_frames_checked":len(result_samples),
        "draft_caption_cue_count":len(result_samples) if beats is not None else None,
        "storyboard_beat_count":len(beats) if beats is not None else 1,
        "white_text_pixel_count_in_safe_zone":min(
            x["white_text_pixel_count"] for x in result_samples
        ),
        "minimum_required_white_caption_pixels":max(
            x["minimum_required_pixels"] for x in result_samples
        ),
        "caption_sampled_from_actual_encoded_frame":True,
        "per_cue_samples":result_samples,
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
        subtitles,episode["duration_seconds"],
        allow_speech_end_before_outro=(
            manifest["srt_measured_synthesized_pcm_speech_windows"]
        )
    )
    caption_visual=None
    if video is not None:
        caption_visual=visible_caption_safezone_qa(video,subtitles,episode["beats"])
        require(sha(video)==manifest["video_sha256"],"VIDEO_SHA_TAMPER")
        require(video.stat().st_size==manifest.get("video_bytes"),
                "VIDEO_SIZE")
    if captions is not None:
        require(sha(captions)==manifest["subtitle_sha256"],
                "CAPTION_SHA_TAMPER")
    narration_energy=None
    speech_caption_boundaries=None
    if audio is not None:
        narration_energy=audit_original_narration(
            audio,beats=episode["beats"],duration=episode["duration_seconds"]
        )
        speech_caption_boundaries=audit_mixed_speech_caption_bounds(
            audio,beats=episode["beats"],duration=episode["duration_seconds"],
            srt=subtitles
        )
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
        "independent_original_narration_per_beat_energy_qa":narration_energy,
        "independent_mixed_audio_vs_srt_speech_boundary_qa":speech_caption_boundaries,
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
