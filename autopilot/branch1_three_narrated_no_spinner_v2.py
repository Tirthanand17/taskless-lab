"""Branch 1 B1q2: genuinely render THREE original, no-spinner, narrated Shorts.

GitHub-hosted disposable Kokoro CPU, 1080x1920, 24fps H264/AAC, native
timed ASS captions based on the *actual* generated PCM. Each unique original
spoken phrase is taken verbatim from its GitHub source captions; original
old fixed SRT timings are never reused with a differently paced voice.

Review-only: NEVER uploads, edits, schedules or deletes a YouTube video;
never invokes an owner credential, paid cloud or user's laptop. Source
script ≠ legal/factual/editorial approval. New MP4 differs from old uploaded
binary and cannot acquire the previous video's YouTube ID.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import subprocess
from hashlib import sha256
from tempfile import TemporaryDirectory
from typing import Any

from autopilot.branch1_no_spinner_storyboard import (
    SIZE,NoSpinnerVisualRejected,_font,_wrap,draw_source_keyframe,storyboard_cues,
)
from autopilot.cloud_av_probe import verify_pinned_assets,sha256_stream
from autopilot.full_topic_narrated_pack import _repair_if_encoded_audio_out_of_band

STATUS="B1Q2_THREE_ACTUAL_NO_SPINNER_SOURCE_NARRATED_MP4S_UNAPPROVED"
FPS=24
SOURCES=(
    ("fm_20261105_ai_voice_cloning_callback_short_en","af_heart"),
    ("fm_20261106_photo_gps_metadata_short_en","bf_emma"),
    ("fm_20261107_incognito_not_invisible_short_en","am_michael"),
)

class RealShortRejected(ValueError):
    """Fail-closed physical or provenance/caption/audio integrity error."""


def _exec(args:list[str],timeout:int=660)->str:
    if not all(isinstance(x,str) and x for x in args) or len(args)>150:
        raise RealShortRejected("Malformed bounded local FFmpeg command")
    try:
        p=subprocess.run(args,check=True,capture_output=True,text=True,timeout=timeout)
        return p.stdout
    except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        # No bearer tokens or provider keys are ever supplied to FFmpeg.
        raise RealShortRejected("Local original H264/AAC command failed: "+type(exc).__name__) from None


def _load_source(root:Path,episode_id:str)->dict:
    if episode_id not in dict(SOURCES):
        raise RealShortRejected("Only three known source-caption episodes are authorized for REVIEW")
    src=root/"content"/"episodes"/(episode_id+".json")
    rec=root/"state"/"scheduled"/(episode_id+".json")
    if any(not p.is_file() or p.is_symlink() or p.stat().st_size>120_000 for p in (src,rec)):
        raise RealShortRejected("GitHub source script and historical receipt required")
    try:
        story=json.loads(src.read_text(encoding="utf8"))
        historical=json.loads(rec.read_text(encoding="utf8"))
    except (ValueError,UnicodeError) as exc:
        raise RealShortRejected("Unparseable or untrusted historical source file") from exc
    if (type(story) is not dict or type(historical) is not dict
        or story.get("id")!=episode_id or historical.get("id")!=episode_id
        or historical.get("youtube_channel_id")!="UCCcL9Q_jqVq6LJmnYUSAFZA"
        or not re.fullmatch(r"[A-Za-z0-9_-]{11}",str(historical.get("youtube_video_id","")))
        or story.get("youtube_video_id")!=historical.get("youtube_video_id")
        or historical.get("status")!="scheduled_verified"
        or historical.get("remote_privacy")!="private"):
        raise RealShortRejected("Historical ownership and exact original source binding mismatch")
    storyboard_cues(story)
    return story


def _time_srt(value:float)->str:
    if not 0<=value<=120 or not math.isfinite(value):
        raise RealShortRejected("Bad actual voice-derived cue time")
    milli=round(value*1000)
    hours,milli=divmod(milli,3600_000)
    mins,milli=divmod(milli,60_000)
    sec,milli=divmod(milli,1000)
    return f"{hours:02}:{mins:02}:{sec:02},{milli:03}"


def _time_ass(value:float)->str:
    if not 0<=value<=120 or not math.isfinite(value):
        raise RealShortRejected("Bad actual ASS cue time")
    centi=round(value*100)
    hours,centi=divmod(centi,360000)
    mins,centi=divmod(centi,6000)
    seconds,centi=divmod(centi,100)
    return f"{hours}:{mins:02}:{seconds:02}.{centi:02}"


def _esc_ass(value:str)->str:
    if type(value) is not str or any(x in value for x in ("\n","\r","\0")):
        raise RealShortRejected("Only source-verified single-line original narration")
    return value.replace("\\", "＼").replace("{","(").replace("}",")")


def _fit_original_ass_text(text:str)->tuple[list[str],int]:
    from PIL import Image,ImageDraw
    d=ImageDraw.Draw(Image.new("RGB",(8,8)))
    for size in range(38,25,-2):
        lines,_,font_size=_wrap(d,text,max_width=810,max_lines=4,
                                max_font=size,min_font=26)
        if len(lines)*math.ceil(font_size*1.26)<=160:
            return lines,font_size
    raise RealShortRejected("Caption cannot fit native 1080px subtitle safe band")


def _render_caption_files(cues:list[dict],folder:Path)->tuple[Path,Path]:
    if not 5<=len(cues)<=30:
        raise RealShortRejected("No reliable measured original narration cues")
    blocks=[];events=[]
    for i,c in enumerate(cues,1):
        if c["end"]<=c["start"] or c["end"]-c["start"]>15:
            raise RealShortRejected("Invalid actual spoken segment")
        lines,fs=_fit_original_ass_text(c["text"])
        content=_esc_ass(c["text"])
        if " ".join(lines)!=c["text"]:
            raise RealShortRejected("Native caption wrap truncated original words")
        blocks.extend((str(i),f'{_time_srt(c["start"])} --> {_time_srt(c["end"])}',
                       c["text"],""))
        asscontent=r"\N".join(_esc_ass(x) for x in lines)
        events.append(f'Dialogue: 0,{_time_ass(c["start"])},{_time_ass(c["end"])},Original,,0,0,0,,'
                      +r'{\an8\pos(540,1450)\fs'+str(fs)+"}"+asscontent)
    srt=folder/"ORIGINAL_VOICE_ACTUAL_PCM_CAPTIONS.srt"
    ass=folder/"NATIVE_ORIGINAL_CAPTIONS.ass"
    srt.write_text("\n".join(blocks)+"\n",encoding="utf8")
    ass.write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
        "ScaledBorderAndShadow: yes\nWrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Original,DejaVu Sans,36,&H00FDFDFD,&H00FFFFFF,&H00101010,&H00000000,"
        "-1,0,0,0,100,100,0,0,1,2,0,8,80,80,0,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        +"\n".join(events)+"\n",encoding="utf8")
    return srt,ass


def original_pcm_and_measured_cues(engine,episode:dict,folder:Path,voice:str)->tuple[Path,list[dict],float,dict]:
    import numpy as np
    import soundfile as sf
    if voice not in dict(SOURCES).values():
        raise RealShortRejected("Unexpected licensed model voice profile")
    src=storyboard_cues(episode)
    sample_rate=None
    segments=[];out=[]
    frames=0
    sfx_at=[]
    for index,beat in enumerate(src):
        pcm,rate=engine.create(beat["source_text"],voice=voice,speed=1.15,lang="en-us")
        pcm=np.asarray(pcm,dtype=np.float32)
        if (type(rate) is not int or not 16000<=rate<=48000
            or pcm.ndim!=1 or pcm.size<round(rate*.27)
            or pcm.size>rate*15 or not np.isfinite(pcm).all()
            or float(np.max(np.abs(pcm)))<.003):
            raise RealShortRejected("Real source-locked model speech missing/invalid")
        if sample_rate is None:
            sample_rate=rate
        if sample_rate!=rate:
            raise RealShortRejected("Source voice sample rate unexpectedly changed")
        start=frames/rate
        segments.append(pcm)
        frames+=pcm.size
        end=frames/rate
        out.append({"scene":index,"start":start,"end":end,"text":beat["source_text"],
                    "source_caption_sha256":beat["source_text_sha256"],
                    "original_visual_motion":beat["motion_mode"]})
        # Quiet distinctive original double chime only at scene thirds,
        # not the user's reference tone, no repeated SMS alert or music loop.
        if index in (max(1,len(src)//3),max(2,(2*len(src))//3)):
            sfx_at.append(frames)
        silence=np.zeros(round(rate*.13),dtype=np.float32)
        segments.append(silence)
        frames+=silence.size
    total=frames/sample_rate
    if not 22<=total<=100:
        raise RealShortRejected("Unbounded actual Short voice duration; needs editorial review")
    speech=np.concatenate(segments)
    for start in sfx_at:
        n=min(round(sample_rate*.065),speech.size-start)
        if n<10:
            continue
        secs=np.arange(n,dtype=np.float32)/sample_rate
        envelope=np.sin(np.pi*np.linspace(0,1,n,dtype=np.float32))**2
        speech[start:start+n]+=.0048*np.sin(2*np.pi*720*secs)*envelope
    if np.max(np.abs(speech))>1.0:
        raise RealShortRejected("Unbounded original narration sample amplitude")
    wav=folder/"original_three_shot_voice.wav"
    sf.write(str(wav),speech,sample_rate,subtype="PCM_16")
    if wav.stat().st_size<100_000:
        raise RealShortRejected("Truncated real narrated WAV")
    return wav,out,total,{
        "actual_model_voice":voice,
        "actual_model_segment_count":len(out),
        "exact_source_words_unchanged":True,
        "spoken_duration_from_generated_pcm_seconds":round(total,3),
        "sfx_original_tiny_phase_ending_chimes":len(sfx_at),
        "human_voice_approval":False,
        "exact_word_forced_alignment_performed":False,
    }


def original_animated_keyframe_timeline(episode:dict,cues:list[dict],folder:Path,
                                       *,max_fps_updates:int=4)->tuple[Path,int,dict]:
    """Actually draw many native 1080x1920 frames over full measured speech.

    24fps output is encoded by FFmpeg; the authored source art updates
    every <=~0.4 seconds in bounded one-shot motion, not a looping spinner.
    Not claiming true 24fps independently modelled 3D animation.
    """
    if max_fps_updates!=4:
        raise RealShortRejected("Only measured 4-frame-per-second max original art treatment")
    ffcat=folder/"original_source_motion.ffconcat"
    lines=["ffconcat version 1.0"]
    n=0
    keys=set()
    prev_end=0.0
    first_last=None
    for idx,c in enumerate(cues):
        if idx>=30 or c["start"]<prev_end-.01 or c["end"]<=c["start"]:
            raise RealShortRejected("Discontinuous source voice times for physical art")
        scene_seconds=c["end"]-c["start"]
        frames=max(3,min(60,math.ceil(scene_seconds*4)))
        each=scene_seconds/frames
        for j in range(frames):
            phase=(j+.5)/frames
            im,receipt=draw_source_keyframe(
                episode,idx,phase,caption_layer="timed_ass_overlay")
            if receipt["timed_ass_caption_overlay_required"] is not True:
                raise RealShortRejected("Original image illegally wrote static subtitle")
            if receipt["caption_source_sha256"]!=c["source_caption_sha256"]:
                raise RealShortRejected("Source picture has different spoken words")
            if receipt["no_circle_spinner_drawn"] is not True:
                raise RealShortRejected("Unexpected looping circle in video frame")
            frame=folder/f"motion_{idx:02}_{j:02}.png"
            im.save(frame,optimize=False,compress_level=1)
            if first_last is None:
                first_last=frame
            lines += [f"file '{frame.as_posix()}'",f"duration {each:.6f}"]
            n+=1
        prev_end=c["end"]
    # Last pose hold for trailing voice silence; avoids a blank final frame.
    if not first_last:
        raise RealShortRejected("No original source image frames")
    ending=folder/f"motion_{len(cues)-1:02}_{max(3,min(60,math.ceil((cues[-1]['end']-cues[-1]['start'])*4)))-1:02}.png"
    if not ending.is_file():
        raise RealShortRejected("Final pose disappeared")
    lines.append(f"file '{ending.as_posix()}'")
    ffcat.write_text("\n".join(lines)+"\n",encoding="utf8")
    # Attest three different source-authored concept silhouettes, never
    # claim every caption beat uses a unique hero with this prototype.
    for index in (0,len(cues)//2,len(cues)-1):
        from autopilot.branch1_no_spinner_storyboard import _draw_subject
        from PIL import Image,ImageDraw
        demo=Image.new("RGB",SIZE)
        item=draw_source_keyframe(episode,index,.8,caption_layer="timed_ass_overlay")[1]
        keys.add(item["distinct_original_visual_subject"])
    if len(keys)!=3:
        raise RealShortRejected("No opening/proof/takeaway composition differentiation")
    return ffcat,n,{
        "native_original_keyframes_drawn":n,
        "three_distinct_original_semantic_hero_subjects":True,
        "original_motion_shot_types":len(set(x["original_visual_motion"] for x in cues)),
        "perpetual_spinning_ring_absent":True,
        "interpolation_is_discrete_art_updates_not_fully_continuous_3d":True,
    }


def _verified_srt_source(srt:Path,original:list[dict],video_duration:float)->None:
    import re
    if not srt.is_file() or srt.stat().st_size>60000:
        raise RealShortRejected("Missing voiced original captions")
    blocks=[s.splitlines() for s in re.split(r"\n\s*\n",srt.read_text(encoding="utf8")) if s.strip()]
    if len(blocks)!=len(original):
        raise RealShortRejected("Caption count differs from exact voiced script")
    last=0.0
    def parse(t):
        a,b,c=t.split(":")
        secs,millis=c.split(",")
        return int(a)*3600+int(b)*60+int(secs)+int(millis)/1000
    for i,(lines,c) in enumerate(zip(blocks,original),1):
        if len(lines)!=3 or lines[0]!=str(i) or " --> " not in lines[1]:
            raise RealShortRejected("Bad real SRT index, format, or timing")
        start,end=(parse(v) for v in lines[1].split(" --> "))
        if (not last-.002<=start<end<=video_duration+.75
            or abs(start-c["start"])>.004 or abs(end-c["end"])>.004
            or lines[2]!=c["text"]):
            raise RealShortRejected("Native SRT script or audio timing mismatch")
        last=end
    if video_duration-last>1.0:
        raise RealShortRejected("Uncaptioned voice tail")


def physical_encoded_review(mp4:Path,srt:Path,episode:dict,
                            original:list[dict],spoken_total:float,
                            output:Path)->dict:
    if not mp4.is_file() or mp4.stat().st_size<100_000:
        raise RealShortRejected("Actual final H264/AAC missing")
    meta=json.loads(_exec(["ffprobe","-v","error","-show_format","-show_streams",
                           "-of","json",str(mp4)],timeout=80))
    streams=meta.get("streams",[])
    vs=[x for x in streams if x.get("codec_type")=="video"]
    aus=[x for x in streams if x.get("codec_type")=="audio"]
    if len(vs)!=1 or len(aus)!=1:
        raise RealShortRejected("Must have exactly one actual video and audio stream")
    vid,aud=vs[0],aus[0]
    if (vid.get("width"),vid.get("height"))!=SIZE or vid.get("codec_name")!="h264" \
        or vid.get("pix_fmt")!="yuv420p" or aud.get("codec_name")!="aac":
        raise RealShortRejected("Non-portrait or non-H264/AAC reconstructed output")
    duration=float(meta.get("format",{}).get("duration",0))
    if not 22<=duration<=100 or abs(duration-spoken_total)>.65:
        raise RealShortRejected("Real encoded video does not match generated speech PCM")
    _verified_srt_source(srt,original,duration)
    _exec(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
           "-xerror","-i",str(mp4),"-f","null","-"],timeout=600)
    # Actual decoded frame samples, not drawings claimed to come from MP4.
    screenshots=[]
    for label,sec in (("OPENING",max(.4,original[0]["start"]+.6)),
                      ("PROOF",duration*.49),
                      ("TAKEAWAY",duration*.87)):
        shot=output/f"{label}_ACTUAL_H264_FRAME_UNAPPROVED.png"
        _exec(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
               "-ss",f"{sec:.3f}","-i",str(mp4),"-frames:v","1",
               "-update","1","-y",str(shot)],timeout=90)
        if shot.stat().st_size<12_000:
            raise RealShortRejected("Actual decoded review screenshot blank")
        screenshots.append(_asset(shot))
    return {
        "actual_h264_aac_full_decode":True,
        "native_resolution":"1080x1920","fps_target":FPS,
        "physical_encoded_duration_seconds":round(duration,3),
        "real_all_source_caption_text_in_srt_matches_pcm":True,
        "actual_independent_encoded_frames":screenshots,
        "youtube_status_or_video_id_queried":False,
        "human_full_video_watch_and_listen":False,
    }


def _asset(path:Path)->dict:
    if path.is_symlink() or not path.is_file():
        raise RealShortRejected("Missing safe original review asset")
    digest,size=sha256_stream(path,max_bytes=100_000_000)
    return {"filename":path.name,"sha256":digest,"bytes":size}


def render_three_actual_review_shorts(*,repository:Path,model:Path,voices:Path,
                                     output:Path)->dict:
    root=Path(repository);out=Path(output)
    if (not root.is_dir() or root.is_symlink() or not out.is_absolute()
        or out.exists() or out.is_symlink()):
        raise RealShortRejected("Only fresh absolute ephemeral hosted CI review folder")
    pinned=verify_pinned_assets(model,voices)
    from kokoro_onnx import Kokoro
    engine=Kokoro(str(model),str(voices))
    out.mkdir(parents=True,mode=0o700)
    results=[]
    try:
        for eid,voice in SOURCES:
            story=_load_source(root,eid)
            folder=out/eid
            folder.mkdir(mode=0o700)
            with TemporaryDirectory(prefix="flowminute-b1q2-source-render-") as temp:
                work=Path(temp)
                wav,cues,total,speech=original_pcm_and_measured_cues(
                    engine,story,work,voice)
                srt,ass=_render_caption_files(cues,work)
                cat,drawn,scene_info=original_animated_keyframe_timeline(story,cues,work)
                mp4=folder/"UNAPPROVED_NO_SPINNER_NARRATED_SHORT.mp4"
                _exec([
                    "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                    "-f","concat","-safe","0","-i",str(cat),"-i",str(wav),
                    "-vf",f"fps={FPS},ass={ass.as_posix()},format=yuv420p",
                    "-map","0:v:0","-map","1:a:0",
                    "-c:v","libx264","-preset","ultrafast","-crf","28",
                    "-pix_fmt","yuv420p","-threads","2",
                    "-c:a","aac","-b:a","128k","-ar","48000",
                    "-af","loudnorm=I=-16:LRA=9:TP=-4.0,"
                          "aresample=48000,alimiter=limit=0.55:level=0",
                    "-t",f"{total:.4f}","-movflags","+faststart",
                    "-y",str(mp4),
                ],timeout=1500)
                # Never disable strict independent *actual encoded AAC*
                # -20..-12 LUFS and <=-1.5dBTP checks for a preview.
                audio=_repair_if_encoded_audio_out_of_band(mp4)
                if not audio["typical_online_video_target_diagnostic"]:
                    raise RealShortRejected("Actual AAC still outside safety limits")
                review=physical_encoded_review(mp4,srt,story,cues,total,folder)
                exported=folder/"SOURCE_ACTUAL_PCM_SYNC_CAPTIONS.srt"
                exported.write_bytes(srt.read_bytes())
                scene0,_=draw_source_keyframe(
                    story,0,.82,caption_layer="original_source_proof")
                cover=folder/"ORIGINAL_NO_SPINNER_COVER_UNAPPROVED.png"
                scene0.save(cover,optimize=True)
                originals=folder/"ORIGINAL_SCRIPT_SHA256.txt"
                original_values="".join(f"{x['source_caption_sha256']}  {i+1:02}\n"
                                        for i,x in enumerate(cues))
                originals.write_text(original_values,encoding="ascii")
                files=[_asset(mp4),_asset(exported),_asset(cover),_asset(originals)]
                files.extend(review["actual_independent_encoded_frames"])
                if len(files)!=7:
                    raise RealShortRejected("Review media inventory incomplete")
                results.append({
                    "original_source_episode_id":eid,
                    "previous_historical_youtube_video_id":story["youtube_video_id"],
                    "original_caption_count":len(cues),
                    "source_caption_text_sha256":sha256(
                        "\n".join(x["text"] for x in cues).encode()).hexdigest(),
                    "actual_original_pcm_voice":speech,
                    "visual_motion":scene_info,
                    "audio_actual_encoded_measurement":audio,
                    "physical_full_media":review,
                    "files":files,
                    "new_youtube_video_id":None,
                    "existing_remote_video_modified":False,
                    "new_private_replacement_uploaded":False,
                    "new_scheduled_publish_at_verified":False,
                    "human_approved":False,
                })
    finally:
        close=getattr(getattr(engine,"voices",None),"close",None)
        if callable(close):
            close()
    if len(results)!=3 or len({x["files"][0]["sha256"] for x in results})!=3:
        raise RealShortRejected("Missing or duplicated real rendered original Short")
    report={
        "status":STATUS,
        "source_reconstructed_from":"GitHub source original caption text ONLY",
        "current_youtube_remote_readback_performed":False,
        "actual_narrated_short_count":len(results),
        "original_file_spinners_replaced_on_youtube":0,
        "new_original_private_uploads":0,
        "real_laptop_or_paid_api_used":False,
        "third_party_reference_voice_music_or_video_reused":False,
        "human_fact_rights_visual_and_voice_review":False,
        "no_automatic_deletion_reschedule_or_upload":True,
        "kokoro_public_model_sha256":pinned["model_sha256"],
        "kokoro_public_voicepack_sha256":pinned["voice_pack_sha256"],
        "episodes":results,
    }
    (out/"UNAPPROVED_B1Q2_THREE_NARRATED_REVIEW_MANIFEST.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return report


if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(description="Create original B1 no-spinner private studio REVIEW MP4s, NO YouTube")
    ap.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--model",type=Path,required=True)
    ap.add_argument("--voices",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    report=render_three_actual_review_shorts(
        repository=a.repo,model=a.model,voices=a.voices,output=a.output)
    print(json.dumps({"status":report["status"],
                      "physical_full_narrated_videos":len(report["episodes"]),
                      "new_youtube_uploads":report["new_original_private_uploads"]}))
