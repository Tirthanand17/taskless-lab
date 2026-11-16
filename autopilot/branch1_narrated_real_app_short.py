"""Narrated first-party software Short: source-bound, creative-review-only.

Uses actual Calc or Chrome screen recordings, existing pinned Kokoro voice and
FFmpeg ASS captions. Outputs a physical video to ephemeral runner storage.
NO YOU TUBE, no release approval, no third-party media and no personal data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess

from autopilot.branch1_real_app_capture import (
    APPS, CAPTURE, RECEIPT as APP_RECEIPT, plan, sha,
    validate_main_only, verify_receipt,
)
from autopilot.branch1_recovery import RecoveryRefused

OUT_MP4="NARRATED_REAL_APP_REVIEW_ONLY.mp4"
OUT_RECEIPT="NARRATED_REAL_APP_PROVENANCE_NOT_RELEASE_APPROVED.json"
OUT_SRT="ORIGINAL_SOURCE_TIMED_CAPTIONS.srt"
OUT_ASS="ORIGINAL_NATIVE_CAPTIONS.ass"
STATUS="B1_REAL_APP_NARRATED_VIDEO_REQUIRES_HUMAN_REVIEW_NO_YOUTUBE"
FPS=24
VIDEO_W,VIDEO_H=1080,1920
# Chapter labels are original explanatory graphics OVER actual app video,
# never a replacement for the recorded application image.
STORIES={
    "calc":{
        "voice":"af_heart",
        "chapters":(
            ("PROOF  /  REAL CALC RESULT",
             "The direct match is false. Trim makes it true. Watch real Calc show why."),
            ("BEFORE  /  GENUINE WORKBOOK",
             "This real LibreOffice Calc worksheet has a hidden space before the first value."),
            ("WHY  /  DIRECT MATCH FAILS",
             "The original comparison evaluates false, even though the values look alike."),
            ("FIX  /  TRIM BOTH VALUES",
             "Compare both values after applying Trim. Watch the real worksheet calculate the result."),
            ("AFTER  /  CHECK THE RESULT",
             "Now the cleaned comparison evaluates true. Inspect text spacing before matching data.")
        ),
        "source_windows":((.8,8.5),(9.8,8.5),(18.8,8.5),(27.8,8.5),(36.8,8.5))
    },
    "chrome":{
        "voice":"af_heart",
        "chapters":(
            ("PROOF  /  BLOCK NOTIFICATION PROMPTS",
             "Chrome notification requests can be stopped here. Watch this real blocked setting in action."),
            ("BEFORE  /  OPEN SETTINGS",
             "Start in Chrome Settings. Open Privacy and security. Then choose Site settings."),
            ("WHY  /  FIND NOTIFICATION CONTROL",
             "Scroll through Site settings and look for Notifications. This controls which sites can request permission to notify you."),
            ("ACTION  /  CHOOSE BLOCK",
             "Choose Don't allow sites to send notifications. We click the real browser control inside a throwaway demo profile."),
            ("AFTER  /  BLOCK CONFIRMED",
             "The selected block option stops new permission prompts. This changes only our temporary test browser, never your own settings.")
        ),
        "source_windows":((.8,8.5),(9.8,8.5),(18.8,8.5),(27.8,8.5),(36.8,8.5))
    }
}
HEX=re.compile(r"^[0-9a-f]{64}$")

def insist(test,reason):
    if not test:
        raise RecoveryRefused(reason)

def execute(cmd,timeout=360):
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    insist(p.returncode==0,"MEDIA_EXECUTION_FAILED:"+p.stderr[-600:])
    return p.stdout

def validate_story(app):
    insist(app in APPS and app in STORIES, "UNKNOWN_STORY_APP")
    story=STORIES[app]
    insist(story["voice"]=="af_heart" and len(story["chapters"])==5
           and len(story["source_windows"])==5,"VOICE_OR_STORY_SHAPE_NOT_PINNED")
    from autopilot.branch1_nov12_four_review_videos import (
        split_script, FourVideoRefused
    )
    total_words=0
    for name,spoken in story["chapters"]:
        insist(type(name) is str and 10<=len(name)<=45
               and re.fullmatch(r"[A-Z0-9 /]+",name) is not None,
               "INVALID_CHAPTER_LABEL")
        insist(type(spoken) is str and 48<=len(spoken)<=180
               and not any(x in spoken for x in ("{","}","<",">","@","\n")),
               "INVALID_VOICE_NARRATION")
        try:
            split_script(spoken,"short")
        except FourVideoRefused:
            raise RecoveryRefused("INVALID_VOICE_CUE_STRUCTURE") from None
        total_words+=len(spoken.split())
    insist(57<=total_words<=100,"SCRIPT_OUTSIDE_CONCISE_STORY_RANGE")
    for start,seconds in story["source_windows"]:
        insist(0<=start<=39 and 2.0<=seconds<=9
               and start+seconds<=47.5,"UNSUPPORTED_REAL_FOOTAGE_WINDOW")
    return {"app":app,"chapters":len(story["chapters"]),
            "words":total_words,"voice":story["voice"],
            "real_software_capture_required":True,
            "owner_review_approved":False,"youtube_uploads":0}

def story_episode(app):
    validated=validate_story(app)
    brief,_=plan(app)
    return {
        "type":"short","voice":validated["voice"],
        "scenes":[
            [name,"BEFORE","RESULT",spoken]
            for name,spoken in STORIES[app]["chapters"]
        ],
        "id":brief["episode_id"],"real_software_evidence":True,
    }

def chapter_asset(out:Path,index:int,label:str) -> Path:
    insist(re.fullmatch(r"[A-Z0-9 /]+",label) is not None,
           "CHAPTER_TEXT_UNTRUSTED")
    dest=out/f"ORIGINAL_CHAPTER_{index:02}.txt"
    dest.write_text(label+"\n",encoding="utf8")
    return dest

def authentic_source_speed(window_seconds:float,voice_seconds:float)->float:
    """Retiming must use EVERY recorded software action, not repeated frames.

    The maximum 2.1x playback bound is an internal readability safeguard,
    not a YouTube recommendation threshold. Time compression changes the
    presentation speed of genuine app actions; it does not invent action.
    """
    insist(type(window_seconds) in (int,float)
           and type(voice_seconds) in (int,float)
           and math.isfinite(window_seconds) and math.isfinite(voice_seconds)
           and 2.0<=window_seconds<=9.0
           and 2.5<=voice_seconds<=11.0,
           "INVALID_GENUINE_APP_TIMEBASE")
    speed=window_seconds/voice_seconds
    insist(.75<=speed<=2.1,"GENUINE_ACTION_SPEED_OUTSIDE_LEGIBILITY_LIMIT")
    return speed


def video_graph(app:str,durations:list[float],ass:Path,folder:Path):
    """Keep actual recorded pixels for all 5 chapters. No fabricated app UI."""
    windows=STORIES[app]["source_windows"]
    # Refuse the old 10-second pilot when chapter speech needs extended
    # cloned holds. All app pixels must come from an adequately long REAL
    # software recording, not cosmetic caption/animation movement.
    from autopilot.branch1_real_action_coverage_gate import require_coverage
    require_coverage(windows,durations)
    parts=["[0:v]split=5"+ "".join(f"[s{i}]" for i in range(5))]
    for i,((start,window),secs) in enumerate(zip(windows,durations)):
        insist(2.5<=secs<=11.0,"CHAPTER_PACING_TOO_SLOW_OR_TOO_FAST")
        label=chapter_asset(folder,i,STORIES[app]["chapters"][i][0])
        # Both panels are from the SAME genuine, timestamped app video.
        # The Calc top half shows the actual data; the bottom is an enlarged
        # crop of the actual formula/results area. No simulated spreadsheet.
        speed=authentic_source_speed(window,secs)
        base=(
            f"[s{i}]trim=start={start:.3f}:duration={window:.3f},"
            # Preserve every frame of the real app's source window.
            # A 8.5s action segment with 5.0s voice plays at 1.7x,
            # rather than discarding the last 3.5s of genuine actions.
            f"setpts={1.0/speed:.8f}*(PTS-STARTPTS),fps=24,"
            # The existing coverage gate still refuses excessive holds.
            "tpad=stop_mode=clone:stop_duration=1.25,"
            f"trim=duration={secs:.6f},setpts=PTS-STARTPTS,"
        )
        if app=="calc":
            parts.append(base+f"split=2[appmain{i}][appdetail{i}]")
            parts.append(
                f"[appmain{i}]crop=720:460:0:0,"
                f"scale=1080:690:flags=bicubic,setsar=1[upper{i}]"
            )
            parts.append(
                f"[appdetail{i}]crop=440:220:240:75,"
                f"scale=1080:540:flags=bicubic,setsar=1[lower{i}]"
            )
            parts.append(
                f"color=c=0x081827:size=1080x1920:rate=24:"
                f"d={secs:.6f}[canvas{i}]"
            )
            parts.append(
                f"[canvas{i}][upper{i}]overlay=x=0:y=190:"
                f"shortest=1[withupper{i}]"
            )
            parts.append(
                f"[withupper{i}][lower{i}]overlay=x=0:y=900:"
                f"shortest=1[focused{i}]"
            )
        else:
            # Crop the true Chrome settings viewport to cut irrelevant
            # testing chrome and enlarge readable permission text on phone.
            # No software UI pixels are generated or altered.
            parts.append(
                base+
                "crop=600:1067:15:70,"
                "scale=1080:1920:flags=bicubic,setsar=1,"
                f"format=yuv420p[focused{i}]"
            )
        parts.append(
            f"[focused{i}]"
            "drawbox=x=0:y=0:w=iw:h=127:color=0x081827@0.90:t=fill,"
            f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"textfile={label.as_posix()}:fontcolor=white:fontsize=37:"
            "x=51:y=43,"
            "drawbox=x=0:y=1540:w=iw:h=380:color=0x071827@0.36:t=fill,"
            f"format=yuv420p[v{i}]"
        )
    parts.append("".join(f"[v{i}]" for i in range(5))+
                 "concat=n=5:v=1:a=0,format=yuv420p[concat]")
    parts.append(f"[concat]ass={ass.as_posix()},format=yuv420p[video]")
    return ";".join(parts)

def probe(mp4:Path):
    data=json.loads(execute([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration",
        "-of","json",str(mp4)],timeout=25))
    streams=data.get("streams",[])
    v=[x for x in streams if x.get("codec_type")=="video"]
    a=[x for x in streams if x.get("codec_type")=="audio"]
    insist(len(v)==1 and len(a)==1
           and v[0].get("codec_name")=="h264"
           and a[0].get("codec_name")=="aac"
           and v[0].get("width")==VIDEO_W
           and v[0].get("height")==VIDEO_H,
           "FINAL_H264_AAC_OR_DIMENSIONS_MISSING")
    duration=float(data["format"]["duration"])
    insist(20<=duration<=64 and math.isfinite(duration),
           "FINAL_AV_DURATION_BAD")
    return duration

def validate_output(app:str,source_folder:Path,out:Path):
    brief,_=plan(app)
    verify_receipt(brief,source_folder)
    receipt_path=out/OUT_RECEIPT
    insist(receipt_path.is_file() and not receipt_path.is_symlink()
           and receipt_path.stat().st_size<14000,
           "NARRATED_RECEIPT_MISSING")
    receipt=json.loads(receipt_path.read_text("utf8"))
    keys={
        "schema","status","app","episode_id","source_capture_sha256",
        "source_provenance_sha256","public_voice_model_sha256",
        "public_voice_pack_sha256","narration_pcm_sha256",
        "caption_srt_sha256","caption_ass_sha256","narrated_mp4_sha256",
        "narrated_mp4_bytes","duration_seconds","spoken_words",
        "postencoded_audio_verified","real_recording_pixel_source",
        "owner_final_watch","release_signed","youtube_uploads",
        "youtube_schedules",
    }
    insist(type(receipt) is dict and set(receipt)==keys,
           "CLOSED_NARRATED_RECEIPT_SCHEMA")
    insist(receipt["schema"]=="FLOWMINUTE_B1_NARRATED_REAL_APP_V1"
           and receipt["status"]==STATUS and receipt["app"]==app
           and receipt["episode_id"]==brief["episode_id"]
           and receipt["real_recording_pixel_source"] is True
           and receipt["postencoded_audio_verified"] is True
           and receipt["owner_final_watch"] is False
           and receipt["release_signed"] is False
           and type(receipt["youtube_uploads"]) is int
           and receipt["youtube_uploads"]==0
           and type(receipt["youtube_schedules"]) is int
           and receipt["youtube_schedules"]==0,
           "NARRATED_RECEIPT_CANNOT_APPROVE_RELEASE")
    source=(source_folder/CAPTURE)
    source_rec=(source_folder/APP_RECEIPT)
    paths={
        "source_capture_sha256":source,
        "source_provenance_sha256":source_rec,
        "narration_pcm_sha256":out/"REAL_ORIGINAL_VOICE.wav",
        "caption_srt_sha256":out/OUT_SRT,
        "caption_ass_sha256":out/OUT_ASS,
        "narrated_mp4_sha256":out/OUT_MP4,
    }
    for key,p in paths.items():
        insist(p.is_file() and not p.is_symlink()
               and 200<=p.stat().st_size<=230_000_000
               and type(receipt[key]) is str
               and HEX.fullmatch(receipt[key])
               and sha(p)==receipt[key],
               "MEDIA_BINDING_SHA_FAILED_"+key)
    from autopilot.cloud_av_probe import MODEL_SHA256,VOICES_SHA256
    insist(receipt["public_voice_model_sha256"]==MODEL_SHA256
           and receipt["public_voice_pack_sha256"]==VOICES_SHA256
           and type(receipt["narrated_mp4_bytes"]) is int
           and receipt["narrated_mp4_bytes"]==(out/OUT_MP4).stat().st_size
           and type(receipt["duration_seconds"]) in (int,float)
           and 20<=receipt["duration_seconds"]<=64
           and receipt["spoken_words"]==validate_story(app)["words"],
           "VOICE_SOURCE_OR_METADATA_NOT_BOUND")
    actual=probe(out/OUT_MP4)
    insist(abs(actual-receipt["duration_seconds"])<=.5,
           "AUDIO_VIDEO_CLOCK_DRIFT")
    execute(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
             "-xerror","-i",str(out/OUT_MP4),"-f","null","-"],timeout=120)
    return {"status":"NARRATED_EXACT_MEDIA_VERIFIED_REVIEW_ONLY",
            "app":app,"physical_mp4_sha256":receipt["narrated_mp4_sha256"],
            "duration_seconds":round(actual,3),
            "owner_release_approval":False,
            "youtube_uploads":0,"youtube_schedules":0}

def render(app:str,source_folder:Path,out:Path,model:Path,voices:Path):
    validate_main_only(os.environ,app)
    brief,_=plan(app)
    verify_receipt(brief,source_folder)
    validate_story(app)
    insist(not out.exists() and out.parent==Path("/tmp")
           and out.name==f"flowminute-b1-narrated-{app}",
           "RUNNER_OUTPUT_LOCATION_OR_OVERWRITE_REFUSED")
    from autopilot.cloud_av_probe import (
        MODEL_SHA256,VOICES_SHA256,verify_pinned_assets
    )
    verify_pinned_assets(model,voices)
    for name in ("ffmpeg","ffprobe"):
        import shutil
        insist(shutil.which(name) is not None,"FREE_MEDIA_TOOL_MISSING")
    filters=execute(["ffmpeg","-hide_banner","-filters"],timeout=20)
    insist("ass" in filters and "drawtext" in filters and "tpad" in filters,
           "NATIVE_CAPTION_OR_EDIT_FILTER_MISSING")
    out.mkdir(mode=0o700)
    from kokoro_onnx import Kokoro
    from autopilot.branch1_nov12_four_review_videos import (
        synthesize,cues_to_files
    )
    voice=Kokoro(str(model),str(voices))
    wav,durations,cues,total=synthesize(voice,story_episode(app),out)
    insist(20<=total<=64 and len(durations)==5
           and len(cues)>=5
           and abs(sum(durations)-total)<.08,
           "VOICE_REAL_CLOCK_OR_CHAPTERS_MISSING")
    ass,srt=cues_to_files(cues,"short",out)
    src=source_folder/CAPTURE
    execute(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
             "-xerror","-i",str(src),"-f","null","-"],timeout=55)
    graph=video_graph(app,durations,ass,out)
    video=out/OUT_MP4
    from autopilot.verified_aac_mastering_b4g5 import (
        AUDIO_MASTERING_FILTER,verify_exact_encoded_master,
        EncodedMasteringRefused,
    )
    execute(["ffmpeg","-nostdin","-hide_banner","-y","-loglevel","error",
             "-i",str(src),"-i",str(wav),
             "-filter_complex",graph,"-map","[video]","-map","1:a:0",
             "-t",f"{total:.3f}","-r",str(FPS),
             "-c:v","libx264","-threads","2","-preset","veryfast",
             "-crf","25","-pix_fmt","yuv420p",
             "-af",AUDIO_MASTERING_FILTER,"-ar","48000",
             "-c:a","aac","-b:a","128k",
             "-movflags","+faststart",str(video)],timeout=600)
    duration=probe(video)
    insist(abs(duration-total)<=.5,"FINAL_NARRATION_TIMING_FAILED")
    execute(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
             "-xerror","-i",str(video),"-f","null","-"],timeout=180)
    try:
        mastering=verify_exact_encoded_master("ffmpeg",video,sha(video),total)
    except EncodedMasteringRefused as first:
        insist(str(first)==
               "Final encoded audio falls outside conservative owner-review mastering band",
               "AUDIO_MASTER_REJECTED_"+str(first))
        fixed=out/"REMASTER_ONCE.mp4"
        execute(["ffmpeg","-nostdin","-hide_banner","-y","-loglevel","error",
                 "-i",str(video),"-map","0:v:0","-map","0:a:0",
                 "-c:v","copy","-af",
                 "loudnorm=I=-18:TP=-2.5:LRA=11:linear=false:print_format=none",
                 "-ar","48000","-c:a","aac","-b:a","128k",
                 "-movflags","+faststart",str(fixed)],timeout=180)
        mastering=verify_exact_encoded_master("ffmpeg",fixed,sha(fixed),total)
        fixed.replace(video)
    insist(mastering["integrated_lufs_and_true_peak_within_internal_band"] is True,
           "AAC_NOT_PHYSICALLY_VERIFIED")
    receipt={
        "schema":"FLOWMINUTE_B1_NARRATED_REAL_APP_V1",
        "status":STATUS,"app":app,"episode_id":brief["episode_id"],
        "source_capture_sha256":sha(src),
        "source_provenance_sha256":sha(source_folder/APP_RECEIPT),
        "public_voice_model_sha256":MODEL_SHA256,
        "public_voice_pack_sha256":VOICES_SHA256,
        "narration_pcm_sha256":sha(wav),
        "caption_srt_sha256":sha(srt),
        "caption_ass_sha256":sha(ass),
        "narrated_mp4_sha256":sha(video),
        "narrated_mp4_bytes":video.stat().st_size,
        "duration_seconds":total,
        "spoken_words":validate_story(app)["words"],
        "postencoded_audio_verified":True,
        "real_recording_pixel_source":True,
        "owner_final_watch":False,
        "release_signed":False,
        "youtube_uploads":0,"youtube_schedules":0,
    }
    (out/OUT_RECEIPT).write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return validate_output(app,source_folder,out)

def main():
    p=argparse.ArgumentParser(description="No YouTube; actual screen+voice demo review")
    p.add_argument("--app",required=True,choices=sorted(APPS))
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--model",type=Path)
    p.add_argument("--voices",type=Path)
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    if a.verify:
        insist(a.model is None and a.voices is None,"VERIFY_DOES_NOT_LOAD_MODEL")
        result=validate_output(a.app,a.source,a.out)
    else:
        insist(a.model is not None and a.voices is not None,
               "VOICE_FILES_REQUIRED")
        result=render(a.app,a.source,a.out,a.model,a.voices)
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
