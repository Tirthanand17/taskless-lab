"""B4e0: physically synthesize and encode 3 ORIGINAL, nonfactual AV rehearsals.

Runs only on a disposable GitHub-hosted runner with SHA256-pinned public
Kokoro speech weights, free open-source Pillow/numpy/soundfile and wheel FFmpeg.
No provider inference, no scraped publisher sentences or images, no reuse of
outside video, no private credentials, no YouTube and NO publish authorization.

Strictly re-derive B4d9 from original per-episode B4d5/B4d7 inputs BEFORE TTS.
Produces two real voiced/captioned illustrated *excerpt previews* per episode,
not full 58/240/58-second daily finished videos. Output destroyed on runner.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import textwrap
from tempfile import TemporaryDirectory

from autopilot.cloud_av_probe import verify_pinned_assets, sha256_stream
from autopilot.nonfactual_narration_rehearsal import (
    build_nonfactual_rehearsals, RehearsalRefused, STATUS as REHEARSAL_STATUS,
    SAFE_SFX,
)
from autopilot.ephemeral_claim_review_docket import _read as bounded_research_read

STATUS = "B4E0_THREE_REAL_NONFACTUAL_KOKORO_VOICED_CAPTIONED_MEDIA_PREVIEWS_NO_PUBLISH"
MAX_MEDIA_BYTES = 55_000_000
SLOTS = ("short_am", "long", "short_pm")
VOICES = {"short_am":"af_heart", "long":"am_michael", "short_pm":"bf_emma"}
COLORS = (
    ((12,23,41),(63,159,216),(141,219,236)),
    ((21,25,46),(154,115,214),(222,197,255)),
    ((14,34,34),(67,181,159),(159,239,208)),
)


class PhysicalPreviewRefused(ValueError):
    """Wrong source script or incomplete/unsupported/silent actual media."""


def canonical(value: object) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False).encode("ascii")


def prepare_preview_plan(original: object,aligned: object,board: object,
                         scout: object,evidence: object,briefs: object,
                         passages: object,docket: object,rehearsals: object) -> dict:
    """Recompute entire source-locked plan; never blindly TTS an arbitrary JSON."""
    try:
        expected=build_nonfactual_rehearsals(
            original,aligned,board,scout,evidence,briefs,passages,docket)
    except (RehearsalRefused,KeyError,TypeError,ValueError):
        raise PhysicalPreviewRefused("Untrusted source-locked rehearsal source") from None
    if (type(rehearsals) is not dict or expected != rehearsals
        or rehearsals.get("status")!=REHEARSAL_STATUS
        or rehearsals.get("release_authorized") is not False
        or rehearsals.get("factual_news_scripts_completed")!=0
        or rehearsals.get("provider_model_calls")!=0
        or rehearsals.get("actual_video_files_created")!=0
        or len(rehearsals.get("three_episodes",[]))!=3):
        raise PhysicalPreviewRefused("Wrong episode/scene or forged media authority")
    episodes=[]
    for slot,episode in zip(SLOTS,expected["three_episodes"]):
        if (episode["slot"]!=slot or episode["release_authorized"] is not False
            or episode["factual_news_narration_written"] is not False
            or episode["real_factual_script_approved"] is not False
            or episode["owner_final_watch_approved"] is not False
            or episode["real_rights_cleared"] is not False):
            raise PhysicalPreviewRefused("Unreviewed real-world script cannot be narrated")
        # First two uniquely authored sections; first sentence of each
        # becomes the strictly bounded actually-voiced physical media.
        previews=[]
        for i,scene in enumerate(episode["scenes"][:2]):
            spoken=scene["original_voiceover_rehearsal_text"]
            sentences=re.split(r"(?<=[.!?])\s+",spoken.strip())
            piece=sentences[0].strip()
            # A very short first sentence (e.g. "Begin by naming the
            # question.") is not a useful standalone narrated illustration.
            # Add exactly one next COMPLETE sentence rather than silently
            # clipping/padding the audio or inventing words.
            if (len(piece)<42 or len(piece.split())<8) and len(sentences)>1:
                piece+=" "+sentences[1].strip()
            if (type(piece) is not str or not 42<=len(piece)<=235
                or len(piece.split())<8
                or piece not in spoken
                or scene["scene_index"]!=i
                or scene["source_quote_display_allowed"] is not False):
                raise PhysicalPreviewRefused("Invalid short original narration excerpt")
            previews.append({
                "scene":i,
                "original_voiceover_text":piece,
                "number_of_original_spoken_sentences":len(
                    re.findall(r"[.!?](?:\s|$)",piece)),
                "original_text_sha256":sha256(piece.encode("utf8")).hexdigest(),
                "scene_id":scene["scene_id"],
                "visual_direction":scene["original_visual_design"],
                "SFX":SAFE_SFX[i],
            })
        episodes.append({
            "episode_id":episode["episode_id"],
            "slot":slot, "kind":episode["format"],
            "size":(episode["canvas_width"],episode["canvas_height"]),
            "voice":VOICES[slot],
            "working_title":episode["original_working_title_not_news_headline"],
            "research_brief_sha256":episode["source_research_brief_sha256"],
            "rehearsal_sha256":sha256(canonical(episode)).hexdigest(),
            "scenes":previews,
            "source_articles_quoted":0,
            "news_factual_claims_approved":0,
            "youtube_upload_allowed":False,
            "full_day_episode_rendered":False,
        })
    if len({e["rehearsal_sha256"] for e in episodes})!=3:
        raise PhysicalPreviewRefused("Duplicate rehearsal narration across daily slots")
    return {"status":"B4E0_EPHEMERAL_SOURCE_LOCKED_PREVIEW_PLAN_NO_PUBLISH",
            "episodes":episodes,"three_previews_planned":3,
            "source_quotations":0,"approved_facts":0,
            "live_external_ai_calls":0,"youtube_uploads":0,
            "release_authorized":False}


def _run(cmd: list[str], *, timeout: int=180) -> str:
    try:
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,check=False,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired):
        raise PhysicalPreviewRefused("Bounded multimedia execution unavailable") from None
    if p.returncode:
        # Don't expose file/metadata/possible sensitive content of stderr.
        raise PhysicalPreviewRefused("Physical media encode or full decode failed")
    return p.stdout


def _font(size: int, mono: bool=False):
    from PIL import ImageFont
    path=("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf" if mono
          else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not Path(path).is_file():
        raise PhysicalPreviewRefused("Open-source DejaVu glyph font unavailable")
    return ImageFont.truetype(path,size)


def _wrap(text: str, max_chars: int, max_lines: int) -> list[str]:
    chunks=textwrap.wrap(text,width=max_chars,break_long_words=False,
                         break_on_hyphens=False)
    if len(chunks)>max_lines:
        # Never cut the narration mid-caption; all actual spoken words must
        # remain visible in the bottom caption-safe visual panel.
        raise PhysicalPreviewRefused("Original voice text exceeds visual caption safe area")
    return chunks


def original_preview_frame(episode: dict, scene: dict, target: Path) -> str:
    """One clear original diagram, no concentric/running circular spinner."""
    from PIL import Image,ImageDraw
    w,h=episode["size"]
    portrait=episode["kind"]=="short"
    bg,accent,soft=COLORS[SLOTS.index(episode["slot"])]
    if scene["scene"]==1:
        accent,soft=soft,accent
    im=Image.new("RGB",(w,h),bg)
    d=ImageDraw.Draw(im)
    for n in range(0,h,92):
        d.line((0,n,w,n),fill=tuple(min(255,a+11) for a in bg),width=2)
    d.rounded_rectangle((46,52,w-46,h-52),radius=28,
                        outline=soft,width=3)
    d.text((88,105),"FLOWMINUTE LAB  /  ORIGINAL PRACTICE",font=_font(27),
           fill=soft)
    d.text((88,162),
           f"{episode['slot'].upper()}   /   SCENE {scene['scene']+1:02} OF 02",
           font=_font(24,mono=True),fill=(202,220,234))
    title_lines=_wrap(episode["working_title"],22 if portrait else 42,3)
    y=239
    for text in title_lines:
        d.text((88,y),text,font=_font(62 if portrait else 58),
               fill=(244,248,253))
        y+=82
    # Original static step diagram; colored cards never rotate.
    chart_top=max(570,y+50) if portrait else max(390,y+12)
    card_height=164 if portrait else 208
    if portrait:
        rects=[(100,chart_top+i*211,w-100,chart_top+i*211+card_height)
               for i in range(3)]
    else:
        cell=(w-224-64)//3
        rects=[(92+i*(cell+32),chart_top,92+i*(cell+32)+cell,
                chart_top+card_height) for i in range(3)]
    labels=(("QUESTION","DEFINE"),("EXAMPLE","COMPARE"),
            ("CHECK","VERIFY"))
    for i,(x1,y1,x2,y2) in enumerate(rects):
        fill=tuple(min(255,a+24+i*7) for a in bg)
        d.rounded_rectangle((x1,y1,x2,y2),radius=22,fill=fill,
                            outline=accent if i==scene["scene"] else soft,width=3)
        d.rectangle((x1+18,y1+26,x1+31,y1+82),fill=accent)
        d.text((x1+50,y1+20),labels[i][0],font=_font(32 if portrait else 30),
               fill=(248,250,252))
        d.text((x1+50,y1+88),labels[i][1],font=_font(29 if portrait else 27),
               fill=soft)
        if i<2:
            if portrait:
                d.line((w//2,y2+7,w//2,y2+35),fill=soft,width=6)
            else:
                d.line((x2+5,y1+card_height//2,x2+27,y1+card_height//2),
                       fill=soft,width=6)
    # Strong text-safe area; no script title drawn over the caption card.
    bottom=h-(488 if portrait else 330)
    d.rounded_rectangle((94,bottom,w-94,h-127),radius=24,
                        fill=(28,47,68),outline=soft,width=2)
    d.text((128,bottom+26),"WHAT THE VOICE ACTUALLY SAYS",
           font=_font(27),fill=soft)
    spoken=_wrap(scene["original_voiceover_text"],
                 39 if portrait else 75,5 if portrait else 3)
    cursor=bottom+81
    size=36 if portrait else 35
    for ln in spoken:
        d.text((128,cursor),ln,font=_font(size),fill=(252,251,246))
        cursor+=55 if portrait else 48
    if cursor-(55 if portrait else 48)+size > h-132:
        raise PhysicalPreviewRefused("Caption baseline falls outside safe bounds")
    d.text((100,h-97),"FICTIONAL EDUCATIONAL EXAMPLE  •  NOT FOR PUBLICATION",
           font=_font(20),fill=(185,205,223))
    target.parent.mkdir(parents=True,exist_ok=True)
    im.save(target,format="PNG",optimize=True)
    digest,size=sha256_stream(target,max_bytes=18_000_000)
    if size<5_000:
        raise PhysicalPreviewRefused("Original drawn scene not physical pixels")
    return digest


def _generate_pcm(engine,episode: dict,folder: Path) -> tuple[Path,list[float],float]:
    """Real CPU-synthesized audio; scene-change transition tone is original."""
    import numpy as np
    import soundfile as sf
    rate=None
    joined=[]
    durations=[]
    for i,scene in enumerate(episode["scenes"]):
        pcm,hz=engine.create(scene["original_voiceover_text"],
                             voice=episode["voice"],
                             speed=1.12 if episode["kind"]=="short" else 1.06,
                             lang="en-us")
        a=np.asarray(pcm,dtype=np.float32)
        if (a.ndim!=1 or not 16000<=hz<=48000
            or len(a)<hz*1.1 or len(a)>hz*32
            or not np.isfinite(a).all()
            or np.max(np.abs(a))<0.002):
            raise PhysicalPreviewRefused("Invalid, silence-only or unbounded real TTS PCM")
        if rate is None:
            rate=hz
        if hz!=rate:
            raise PhysicalPreviewRefused("Inconsistent PCM sample rate")
        pad=np.zeros(int(rate*.22),dtype=np.float32)
        # Optional one-time original low-level entry pulse, not a continuous
        # looping sound effect. Keep it short and under narration.
        n=int(rate*.075)
        tt=np.arange(n,dtype=np.float32)/rate
        pulse=.014*np.sin(2*np.pi*(570 if i==0 else 430)*tt)
        pulse*=np.sin(np.linspace(0,np.pi,n,dtype=np.float32))**2
        a=a.copy()
        a[:n]+=pulse
        joined.extend((a,pad))
        durations.append((a.size+pad.size)/rate)
    combined=np.clip(np.concatenate(joined),-0.99,0.99)
    wav=folder/"EPHEMERAL_ACTUAL_TTS_VOICE.wav"
    sf.write(str(wav),combined,rate,subtype="PCM_16")
    return wav,durations,combined.size/rate


def _encode(ffmpeg: str,folder: Path,images: list[Path],
            durations: list[float],wav: Path,total: float) -> Path:
    if (len(images)!=2 or len(durations)!=2
        or not 4.0<=total<=65.0 or any(not 1<=d<=35 for d in durations)):
        raise PhysicalPreviewRefused("Not two bounded and distinct timed audio segments")
    concat=folder/"EPHEMERAL_VISUAL_SCENES.ffconcat"
    lines=["ffconcat version 1.0"]
    for img,duration in zip(images,durations):
        lines.extend((f"file '{img.resolve().as_posix()}'",
                      f"duration {duration:.6f}"))
    lines.append(f"file '{images[-1].resolve().as_posix()}'")
    concat.write_text("\n".join(lines)+"\n",encoding="utf8")
    output=folder/"UNAPPROVED_VOICED_TWO_SCENE_PREVIEW.mp4"
    _run([ffmpeg,"-nostdin","-y","-hide_banner","-loglevel","error",
          "-f","concat","-safe","0","-i",str(concat),
          "-i",str(wav),
          "-filter:v","fps=24,fade=t=in:st=0:d=0.25,format=yuv420p",
          "-map","0:v:0","-map","1:a:0",
          "-t",f"{total:.5f}","-c:v","libx264","-preset","ultrafast",
          "-crf","30","-threads","2","-pix_fmt","yuv420p",
          "-c:a","aac","-b:a","112k","-movflags","+faststart",
          str(output)],timeout=330)
    return output


def inspect_physical_preview(ffmpeg: str,output: Path,episode: dict,
                             expected_audio_seconds: float,
                             scene_pngs: list[Path]) -> dict:
    import subprocess
    if not output.is_file() or output.is_symlink():
        raise PhysicalPreviewRefused("No real encoded preview file found")
    media=subprocess.run([ffmpeg,"-hide_banner","-i",str(output)],
                         capture_output=True,text=True,timeout=30)
    # FFmpeg -i exits 1 without output; metadata is on stderr.
    lines=media.stderr.splitlines()
    v=[x for x in lines if re.search(r"Stream #\d+:\d+",x) and
       "Video: h264" in x]
    a=[x for x in lines if re.search(r"Stream #\d+:\d+",x) and
       "Audio: aac" in x]
    dims=f"{episode['size'][0]}x{episode['size'][1]}"
    if (len(v)!=1 or len(a)!=1 or
        not any(re.search(r"(?<!\d)"+re.escape(dims)+r"(?!\d)",x) for x in v)
        or any("yuv420p" not in x for x in v)):
        raise PhysicalPreviewRefused("Wrong H264/AAC actual bytes or orientation")
    if len(set(sha256_stream(f,max_bytes=18_000_000)[0] for f in scene_pngs))!=2:
        raise PhysicalPreviewRefused("Two visual scenes identical in pixels")
    _run([ffmpeg,"-nostdin","-hide_banner","-loglevel","error","-xerror",
          "-i",str(output),"-f","null","-"],timeout=300)
    digest,size=sha256_stream(output,max_bytes=MAX_MEDIA_BYTES)
    if size<100_000:
        raise PhysicalPreviewRefused("Very small real H264/AAC physical preview")
    # PCM-derived target; encoder audio/video drift needs explicit actual
    # frame/stream duration review in later full-length production gate.
    return {
        "slot":episode["slot"],"kind":episode["kind"],
        "voice":episode["voice"],"episode_id":episode["episode_id"],
        "spoken_segments_actually_synthesized":2,
        "complete_source_independent_sentences_actually_synthesized":sum(
            p["number_of_original_spoken_sentences"] for p in episode["scenes"]),
        "generated_pcm_duration_seconds":round(expected_audio_seconds,2),
        "real_original_captioned_png_scenes":2,
        "mp4_sha256":digest,"actual_bytes":size,
        "resolution":dims,"codec":"H264/AAC",
        "physical_full_media_decode_passed":True,
        "real_audio_synthesized":True,
        "subtitles_are_scene_sentence_cards_not_word_aligned":True,
        "original_audio_entry_and_transition_cues":True,
        "no_circular_spinners_drawn":True,
        "full_episode_voice_generated":False,
        "full_58_or_240_second_video_completed":False,
        "independent_fact_or_rights_review_performed":False,
        "full_human_playback_completed":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


def render_three_previews(plan: dict,model: Path,voices: Path,outdir: Path) -> dict:
    if (type(plan) is not dict
        or plan.get("status")!="B4E0_EPHEMERAL_SOURCE_LOCKED_PREVIEW_PLAN_NO_PUBLISH"
        or plan.get("release_authorized") is not False
        or plan.get("three_previews_planned")!=3
        or len(plan.get("episodes",[]))!=3):
        raise PhysicalPreviewRefused("Untrusted preview plan")
    if (outdir.exists() and (outdir.is_symlink() or any(outdir.iterdir()))
        or not str(outdir).startswith("/tmp/flowminute-")
        or outdir.parent!=Path("/tmp")):
        raise PhysicalPreviewRefused("Only empty disposable /tmp/flowminute-* output allowed")
    verify_pinned_assets(model,voices)
    import imageio_ffmpeg
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    _run([ffmpeg,"-hide_banner","-version"],timeout=20)
    from kokoro_onnx import Kokoro
    engine=Kokoro(str(model),str(voices))
    outdir.mkdir(parents=True,exist_ok=False)
    reports=[]
    for index,ep in enumerate(plan["episodes"]):
        if ep["slot"]!=SLOTS[index] or ep["youtube_upload_allowed"] is not False:
            raise PhysicalPreviewRefused("Daily episode preview source order changed")
        folder=outdir/ep["episode_id"]
        folder.mkdir(mode=0o700)
        files=[]
        for scene in ep["scenes"]:
            path=folder/f"original_scene_{scene['scene']:02}.png"
            original_preview_frame(ep,scene,path)
            files.append(path)
        wav,durations,seconds=_generate_pcm(engine,ep,folder)
        mp4=_encode(ffmpeg,folder,files,durations,wav,seconds)
        proof=inspect_physical_preview(ffmpeg,mp4,ep,seconds,files)
        reports.append(proof)
        print("B4E0_REAL_PRIVATE_PREVIEW_DECODE_OK",
              json.dumps({"slot":proof["slot"],"seconds":proof[
                  "generated_pcm_duration_seconds"],"mp4_bytes":proof[
                  "actual_bytes"],"actual_spoken_segments":2,
                  "approved_fact_claims":0,"youtube_uploads":0}),flush=True)
    if len({r["mp4_sha256"] for r in reports})!=3:
        raise PhysicalPreviewRefused("Duplicated encoded preview outputs")
    return {
        "status":STATUS,"real_short_voiced_previews":2,
        "real_long_format_voiced_previews":1,
        "actual_abridged_media_files":3,
        "real_original_pillow_scene_images":6,
        "actual_spoken_tts_segments":6,
        "actual_complete_spoken_sentences":sum(
            r["complete_source_independent_sentences_actually_synthesized"]
            for r in reports),
        "pinned_public_tts_model_validated":True,
        "full_h264_aac_decode_passed_all_three":True,
        "full_daily_video_assets_completed":0,
        "actual_58s_or_240s_full_renders":0,
        "real_news_facts_verified":0,"voice_and_media_rights_approved":False,
        "human_review_complete":False,
        "billed_provider_calls":0,"youtube_uploads":0,
        "release_authorized":False,
        "previews":reports,
    }


def _read(path: Path) -> object:
    if (not path.is_file() or path.is_symlink()
        or not 2<=path.stat().st_size<=512_000):
        raise PhysicalPreviewRefused("Unsafe or absent runner-local preview input")
    try:
        return json.loads(path.read_text("utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise PhysicalPreviewRefused("Malformed research preview JSON") from None


def main() -> None:
    ap=argparse.ArgumentParser(description="Real 3 clipped ORIGINAL TTS+H264/AAC cloud media previews ONLY")
    for name in ("original-plan","aligned-plan","board","scout",
                 "evidence","briefs","passages","docket","rehearsals"):
        ap.add_argument("--"+name,required=True,type=Path)
    ap.add_argument("--model",required=True,type=Path)
    ap.add_argument("--voices",required=True,type=Path)
    ap.add_argument("--output-dir",required=True,type=Path)
    args=ap.parse_args()
    plan=prepare_preview_plan(*[
        _read(getattr(args,name.replace("-","_"))) for name in (
            "original-plan","aligned-plan","board","scout","evidence",
            "briefs","passages","docket","rehearsals")])
    report=render_three_previews(plan,args.model,args.voices,args.output_dir)
    (args.output_dir/"EPHEMERAL_PHYSICAL_PREVIEW_PROOF.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=True)+"\n",encoding="utf8")
    print(json.dumps({
        "status":STATUS,
        "physical_voiced_media_previews":3,
        "synthetic_hypothetical_previews_only":True,
        "original_actual_illustration_scenes":6,
        "real_spoken_segments":6,
        "real_complete_spoken_sentences":report["actual_complete_spoken_sentences"],
        "three_h264_aac_fully_decoded":True,
        "full_narrated_58_240_58_second_videos":0,
        "fact_rights_approvals":0,
        "owner_final_watches":0,
        "paid_model_calls":0,
        "youtube_uploads":0,
        "release_authorized":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
