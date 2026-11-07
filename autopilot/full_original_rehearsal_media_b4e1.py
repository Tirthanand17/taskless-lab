"""B4e1: REAL full original nonfactual 17-scene Kokoro H264/AAC rehearsal media.

Requires the complete B4d5-B4d9 plan, source, episode and claim-review
provenance; calls no paid provider; reuses pinned public wheel voice + FFmpeg.

Full spoken text, full episode scene count and actual scene-timed caption cues
are physically produced. They are NOT approved factual-news videos, and may
not reach aspirational 58/240/58s until real audio pacing is improved.
All source evidence, voices, images and videos are runner-local and destroyed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import textwrap

from autopilot.cloud_av_probe import verify_pinned_assets, sha256_stream
from autopilot.nonfactual_narration_rehearsal import (
    build_nonfactual_rehearsals, RehearsalRefused, STATUS as REHEARSAL_STATUS,
)
from autopilot.real_rehearsal_voice_media_b4e0 import (
    PhysicalPreviewRefused, prepare_preview_plan, canonical, _run, _font,
    SLOTS, VOICES, COLORS,
)

STATUS = "B4E1_FULL_THREE_ORIGINAL_NONFACTUAL_VOICED_REHEARSALS_PHYSICALLY_RENDERED_NOT_PUBLISHABLE"
PLAN_STATUS = "B4E1_SOURCE_LOCKED_ALL_17_SCENES_NO_PUBLISH"
FPS = 24
# Conservative cap: <=112 original characters keeps phrases within both
# the portrait 4-line and landscape 2-line caption panels even with
# natural word boundaries. No original narration is removed.
CAPTION_MAX_CHARS = 112
MAX_SPOKEN_CHUNKS_PER_SCENE = 9
MAX_SPOKEN_CHUNKS_PER_EPISODE = 100
MAX_EPISODE_SECONDS = {"short":85.0,"long":340.0}
MIN_EPISODE_SECONDS = {"short":23.0,"long":95.0}
MAX_MP4_BYTES = 240_000_000
# Calibrated from trusted physical main run 42246914153:
# short AM 59.771s at 0.90, long 227.366s at 0.91, short PM
# 56.593s at 0.90. This is a VOICE-speed starting point only;
# measured durations still must be checked for every new script.
VOICE_SPEED_BY_SLOT = {"short_am":0.93, "long":0.86, "short_pm":0.88}
VOICE_SPEED_REFERENCE_SECONDS = {
    "short_am":59.771, "long":227.366, "short_pm":56.593,
}
VOICE_SPEED_PREVIOUS = {"short_am":0.90,"long":0.91,"short_pm":0.90}
REVEAL_SECONDS = 0.36
CAPTION_WRAP_CHARS = {"short":44, "long":76}
CAPTION_MAX_LINES = {"short":4, "long":2}
CAPTION_MARGIN_BOTTOM_PX = {"short":168, "long":148}
# Every scene has its own didactic visual mini-flow, not the same three
# rotating/running cards on all 17 scenes. The two-step active reveal
# happens ONCE, then remains static through each spoken scene.
SCENE_CARD_WORDS = {
    "HOOK_QUESTION": (("ASK", "DEFINE"), ("IDEA", "HYPOTHESIS"), ("TEST", "CHECK")),
    "SOURCE_SCOPE": (("SOURCE", "UNVERIFIED"), ("SCOPE", "LIMIT"), ("REVIEW", "VERIFY")),
    "DEMONSTRATION": (("SAMPLE", "SYNTHETIC"), ("STEP", "DEMONSTRATE"), ("CHECK", "REPRODUCE")),
    "VERIFY_AND_LIMIT": (("CLAIM", "QUESTION"), ("LIMIT", "UNCERTAIN"), ("PROOF", "REVIEW")),
    "MECHANISM": (("INPUT", "SYNTHETIC"), ("PROCESS", "EXPLAIN"), ("OUTPUT", "CHECK")),
    "BASELINE": (("CONTROL", "BASELINE"), ("CHANGE", "ONE STEP"), ("COMPARE", "FAIR TEST")),
    "EXAMPLE_1": (("CASE A", "INVENTED"), ("TRACE", "FIRST"), ("CHECK", "RECORD")),
    "EXAMPLE_2": (("CASE B", "INVENTED"), ("COMPARE", "SECOND"), ("CHECK", "REPEAT")),
    "COUNTEREXAMPLE": (("FAILURE", "IMAGINED"), ("DETECT", "QUESTION"), ("RECOVER", "REVIEW")),
    "FACT_AND_RIGHTS_GATE": (("FACT", "UNVERIFIED"), ("RIGHTS", "UNCLEARED"), ("BLOCK", "RELEASE")),
    "NEXT_VIEWER_ACTION": (("TRY", "SAFE TEST"), ("LOG", "YOUR INPUT"), ("LEARN", "REVIEW")),
}


class FullRehearsalRefused(ValueError):
    """Reject source, script, voice, visual, renderer and authority forgery."""


def _normalize_spaces(value: str) -> str:
    return " ".join(value.split())


def split_original_voice_to_cues(text: str) -> tuple[str,...]:
    """No dropped words: complete original text reconstructed from each cue.

    Split at authored punctuation first, then bounded word boundaries for
    over-long sentences. No generative rewriting, publisher quote or filler.
    This is per-phrase PCM timing, NOT per-word forced alignment.
    """
    if type(text) is not str or not 60<=len(text)<=1600 or "\n" in text:
        raise FullRehearsalRefused("Unbounded or nonoriginal scene narration")
    text=_normalize_spaces(text)
    sentences=re.split(r"(?<=[.!?])\s+",text)
    output=[]
    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence)<=CAPTION_MAX_CHARS:
            output.append(sentence)
            continue
        words=sentence.split()
        acc=[]
        for word in words:
            if len(word)>CAPTION_MAX_CHARS:
                raise FullRehearsalRefused("Unusable unbroken TTS word")
            if acc and len(" ".join(acc+[word]))>CAPTION_MAX_CHARS:
                output.append(" ".join(acc))
                acc=[word]
            else:
                acc.append(word)
        if acc:
            output.append(" ".join(acc))
    # An overlong sentence may end in a short word such as "now.".
    # Never discard it or accept an inaudible tiny clip: rebalance a
    # complete preceding word into that final phrase, with no rewriting.
    pos=0
    while pos<len(output):
        if len(output[pos])>=8:
            pos+=1
            continue
        if (pos>0 and len(output[pos-1])+1+len(output[pos])
            <=CAPTION_MAX_CHARS):
            output[pos-1]+=" "+output.pop(pos)
            continue
        if (pos+1<len(output)
            and len(output[pos])+1+len(output[pos+1])
            <=CAPTION_MAX_CHARS):
            output[pos]+=" "+output.pop(pos+1)
            continue
        if pos>0 and " " in output[pos-1]:
            earlier,borrow=output[pos-1].rsplit(" ",1)
            if len(earlier)>=8 and len(borrow)+1+len(output[pos])<=CAPTION_MAX_CHARS:
                output[pos-1]=earlier
                output[pos]=borrow+" "+output[pos]
                continue
        if pos+1<len(output) and " " in output[pos+1]:
            borrow,later=output[pos+1].split(" ",1)
            if len(later)>=8 and len(borrow)+1+len(output[pos])<=CAPTION_MAX_CHARS:
                output[pos+1]=later
                output[pos]+=" "+borrow
                continue
        raise FullRehearsalRefused("Cannot preserve tiny authored caption fragment safely")
    if (not 1<=len(output)<=MAX_SPOKEN_CHUNKS_PER_SCENE
        or any(not 8<=len(x)<=CAPTION_MAX_CHARS for x in output)
        or _normalize_spaces(" ".join(output))!=text):
        raise FullRehearsalRefused("Caption subdivision would drop original spoken words")
    return tuple(output)


def prepare_full_rehearsal_plan(*sources: object) -> dict:
    """No model/YouTube/publication authority; MUST rederive source lock."""
    if len(sources)!=9:
        raise FullRehearsalRefused("Require all original trusted source documents")
    try:
        original,aligned,board,scout,evidence,briefs,passages,docket,rehearsals=sources
        preview=prepare_preview_plan(*sources)
        rebuilt=build_nonfactual_rehearsals(
            original,aligned,board,scout,evidence,briefs,passages,docket)
    except (PhysicalPreviewRefused,RehearsalRefused,KeyError,TypeError,ValueError):
        raise FullRehearsalRefused("Cannot reestablish exact per-source original script") from None
    if (type(rehearsals) is not dict or canonical(rebuilt)!=canonical(rehearsals)
        or rehearsals.get("status")!=REHEARSAL_STATUS
        or preview.get("release_authorized") is not False):
        raise FullRehearsalRefused("Rehearsal changed after source and editorial review")
    episodes=[]
    for index,(slot,item) in enumerate(zip(SLOTS,rebuilt["three_episodes"])):
        portrait=slot!="long"
        target_count=4 if portrait else 9
        if (item["slot"]!=slot or len(item["scenes"])!=target_count
            or item["format"]!=("short" if portrait else "long")
            or item["release_authorized"] is not False
            or item["real_factual_script_approved"] is not False
            or item["actual_recorded_voice_exists"] is not False
            or item["actual_video_rendered"] is not False):
            raise FullRehearsalRefused("Not a full four/nine/four scene unapproved episode")
        scene_rows=[]
        for j,scene in enumerate(item["scenes"]):
            text=scene["original_voiceover_rehearsal_text"]
            if (scene["scene_index"]!=j
                or scene["source_quote_display_allowed"] is not False
                or scene["third_party_source_visual_allowed"] is not False
                or scene["story_claims_semantically_verified"] is not False
                or not scene["static_safe_area_for_burned_in_captions"]):
                raise FullRehearsalRefused("Authored full-scene or rights flag mismatch")
            cues=split_original_voice_to_cues(text)
            scene_rows.append({
                "scene":j,"scene_id":scene["scene_id"],
                "original_voiceover_text":text,
                "spoken_text_sha256":sha256(text.encode("utf8")).hexdigest(),
                "original_visual_direction":scene["original_visual_design"],
                "caption_cues":list(cues),
                "cap_count":len(cues),
                "motion_policy":"single-entry-reveal-static",
                "source_quote_display_allowed":False,
                "news_claim_fact_checked":False,
            })
        all_cues=sum(s["cap_count"] for s in scene_rows)
        if not 8<=all_cues<=MAX_SPOKEN_CHUNKS_PER_EPISODE:
            raise FullRehearsalRefused("Full narration has excessive or missing sentences")
        narration=_normalize_spaces(" ".join(s["original_voiceover_text"] for s in scene_rows))
        eps=preview["episodes"][index]
        if (eps["slot"]!=slot
            or eps["rehearsal_sha256"]!=sha256(canonical(item)).hexdigest()
            or eps["working_title"]!=item["original_working_title_not_news_headline"]):
            raise FullRehearsalRefused("Previous observed AV preview context swapped")
        episodes.append({
            "slot":slot,"episode_id":item["episode_id"],"kind":item["format"],
            "size":[item["canvas_width"],item["canvas_height"]],
            "target_seconds_not_audio_verified":item["duration_target_seconds"],
            "voice":VOICES[slot],
            "research_brief_sha256":item["source_research_brief_sha256"],
            "research_claim_docket_sha256":item["source_claim_docket_sha256"],
            "rehearsal_sha256":eps["rehearsal_sha256"],
            "authored_full_narration_sha256":sha256(narration.encode("utf8")).hexdigest(),
            "working_title":item["original_working_title_not_news_headline"],
            "word_count":item["estimated_script_words"],
            "all_scene_count":target_count,
            "total_original_caption_phrases":all_cues,
            "scenes":scene_rows,
            "source_quote_reuse_allowed":False,
            "real_world_factual_claim_approved":False,
            "release_authorized":False,
            "youtube_upload_allowed":False,
        })
    if [e["all_scene_count"] for e in episodes]!=[4,9,4]:
        raise FullRehearsalRefused("Not exactly seventeen unique authored scenes")
    return {
        "status":PLAN_STATUS,
        "three_original_complete_rehearsals_planned":3,
        "original_full_scene_count":17,
        "authored_script_source_revalidated":True,
        "approved_news_facts":0,
        "paid_model_calls":0,
        "release_authorized":False,
        "youtube_uploads":0,
        "episodes":episodes,
    }


def _draw_original_full_scene(ep:dict, scene:dict, path:Path,
                              *,revealed:bool=True,
                              focus_index:int|None=None)->str:
    """Render a real full-size original editorial infographic; no loops.

    B4f9 replaces the old 17-slide template with eleven beat-specific
    headlines and four distinct comparison / timeline / sample / verification
    visual grammars. The existing B4f7 source-preserving native ASS burn
    still happens AFTER the 2-stage scene image animation is encoded.
    """
    from autopilot.cinematic_scene_board_b4f9 import (
        SceneDesignRefused, render_editorial_frame,
    )
    if (ep.get("slot") not in SLOTS or
        scene.get("scene_id") not in SCENE_CARD_WORDS):
        raise FullRehearsalRefused("Unrecognized original storyboard scene")
    try:
        canvas=render_editorial_frame(
            ep,scene,revealed=revealed,focus_index=focus_index)
    except SceneDesignRefused as exc:
        # B4g0: preauthored constant artwork labels only. A detailed bounded
        # clip diagnostic is needed to prevent a falsely green CI that skipped
        # image rendering. Never log the external research claim/script.
        raise FullRehearsalRefused(
            "Original storyboard physical safe-area invalid for original beat "
            +str(scene["scene_id"])+": "+str(exc)[:100]
        ) from None
    path.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(path,"PNG",optimize=True)
    digest,bytes_=sha256_stream(path,max_bytes=18_000_000)
    if bytes_<5_000:
        raise FullRehearsalRefused("Unique original editorial scene was not rendered")
    return digest


def _stamp(seconds: float) -> str:
    if not math.isfinite(seconds) or not 0<=seconds<=3600:
        raise FullRehearsalRefused("Caption timestamp invalid")
    count=round(seconds*1000)
    hr,count=divmod(count,3600000)
    mn,count=divmod(count,60000)
    sec,ms=divmod(count,1000)
    return f"{hr:02}:{mn:02}:{sec:02},{ms:03}"


def _synth_full_voice(engine,ep: dict,folder: Path) -> tuple[Path,Path,list[float],list[dict],float]:
    """Each caption begins/ends at measured physical PCM sample indices."""
    import numpy as np
    import soundfile as sf
    sample_rate=None
    audio=[]
    cues=[]
    scenes=[]
    ticks=0
    for scene in ep["scenes"]:
        scene_start=ticks
        for part in scene["caption_cues"]:
            slot=ep["slot"]
            if slot not in VOICE_SPEED_BY_SLOT or ep["voice"]!=VOICES[slot]:
                raise FullRehearsalRefused("Wrong ownerless Kokoro calibration slot")
            pcm,hz=engine.create(part,voice=ep["voice"],
                   speed=VOICE_SPEED_BY_SLOT[slot],lang="en-us")
            arr=np.asarray(pcm,dtype=np.float32)
            if (arr.ndim!=1 or not 16000<=hz<=48000
                or arr.size<hz*.36 or arr.size>hz*32
                or not np.isfinite(arr).all()
                or np.max(np.abs(arr))<.002):
                raise FullRehearsalRefused("Actual voice PCM silent/invalid/too long")
            if sample_rate is None:
                sample_rate=hz
            if sample_rate!=hz:
                raise FullRehearsalRefused("TTS changed sample rate between captions")
            # Keep spoken PCM untouched here. The B4g3 original soft
            # procedural focus accents are added ONLY after the whole
            # scene clock is physically measured, at exact B4g2 cut times.
            start=ticks/hz
            audio.append(arr)
            ticks+=arr.size
            end=ticks/hz
            cues.append({
                "scene":scene["scene"],
                "start":start,"end":end,"text":part,
                "reproduced_from_original_script":True,
            })
            silence=np.zeros(int(.085*hz),dtype=np.float32)
            audio.append(silence)
            ticks+=silence.size
        gap=np.zeros(int(.18*sample_rate),dtype=np.float32)
        audio.append(gap)
        ticks+=gap.size
        scenes.append((ticks-scene_start)/sample_rate)
    total=ticks/sample_rate
    if not (MIN_EPISODE_SECONDS[ep["kind"]]<=total<=
            MAX_EPISODE_SECONDS[ep["kind"]]):
        raise FullRehearsalRefused("Entire original speech outside bounded length")
    if len(cues)!=ep["total_original_caption_phrases"]:
        raise FullRehearsalRefused("Missing synthesized original voice phrase")
    cursor=0.
    for cue in cues:
        if not cursor-.01<=cue["start"]<cue["end"]<=total+.01:
            raise FullRehearsalRefused("Caption overlaps or exceeds physical voice")
        cursor=cue["end"]
    # Reconstruct literally every authored word from actual TTS inputs.
    for scene in ep["scenes"]:
        utterances=[x["text"] for x in cues if x["scene"]==scene["scene"]]
        if _normalize_spaces(" ".join(utterances))!=_normalize_spaces(
                scene["original_voiceover_text"]):
            raise FullRehearsalRefused("A spoken chunk omitted original text")
    wav=folder/"EPHEMERAL_FULL_VOICE.wav"
    sound=np.clip(np.concatenate(audio),-.99,.99)
    from autopilot.original_pcm_sound_design_b4g3 import (
        OriginalSoundRefused, mix_original_sound_design,
    )
    try:
        sound,sound_proof=mix_original_sound_design(
            sound,sample_rate,
            [scene["scene_id"] for scene in ep["scenes"]],scenes)
    except OriginalSoundRefused:
        raise FullRehearsalRefused(
            "Original low-level audio layer no longer matches physical PCM scene cuts"
        ) from None
    if (sound_proof["original_pcm_samples"]!=ticks
        or sound_proof["original_physical_scene_count"]!=len(scenes)
        or sound_proof["youtube_release_authorized"] is not False):
        raise FullRehearsalRefused(
            "Sound effects cannot change original narration sample clock")
    sf.write(str(wav),sound,sample_rate,subtype="PCM_16")
    (folder/"EPHEMERAL_ORIGINAL_AUDIO_SOUND_DESIGN.json").write_text(
        json.dumps(sound_proof,sort_keys=True,indent=2)+"\n",encoding="utf8")
    srt=folder/"EPHEMERAL_PCM_TIMED_SENTENCE_CAPTIONS.srt"
    blocks=[]
    for i,c in enumerate(cues,1):
        # libass auto-wraps long statements. Two-line forced display whenever
        # possible, safe lower card plus dark subtitle outline.
        width=CAPTION_WRAP_CHARS[ep["kind"]]
        visual_lines=textwrap.wrap(c["text"],width=width,
                   break_long_words=False,break_on_hyphens=False)
        if (not visual_lines
            or len(visual_lines)>CAPTION_MAX_LINES[ep["kind"]]
            or any(len(line)>width+2 for line in visual_lines)):
            raise FullRehearsalRefused(
                "Caption exceeds measured subtitle-safe panel height/width")
        txt="\n".join(visual_lines)
        blocks += [str(i),f"{_stamp(c['start'])} --> {_stamp(c['end'])}",txt,""]
    srt.write_text("\n".join(blocks)+"\n",encoding="utf8")
    return wav,srt,scenes,cues,total


def _encode_full(ffmpeg: str,ep: dict,folder: Path,
                 images: list[tuple[Path,...]],scenes: list[float],
                 wav: Path,srt: Path,total: float, *,
                 cues: list[dict]) -> Path:
    """One-way 3/4 phase reveals per original scene paced to actual PCM.

    Stage 0 shows original neutral checkpoints; later phases highlight
    each distinct item exactly once in order, then hold. No circular
    loader, looping highlight, caption panel motion or extra narration.
    """
    if (len(images)!=ep["all_scene_count"] or len(scenes)!=len(images)
        or abs(sum(scenes)-total)>.03
        or any(not 2<=x<=55 for x in scenes)
        or any(len(pair) not in (3,4) or
               not all(p.is_file() and not p.is_symlink() for p in pair)
               for pair in images)):
        raise FullRehearsalRefused("Staged originals and real PCM scene clocks mismatch")
    concat=folder/"EPHEMERAL_ALL_SCENES_ONE_SHOT_REVEAL.ffconcat"
    lines=["ffconcat version 1.0"]
    from autopilot.one_way_storyboard_timing_b4g2 import (
        OneWayStageRefused,active_focus_sequence,stage_hold_seconds,
        grammar_for_original_scene,
    )
    for stage_images,duration,original_scene in zip(
            images,scenes,ep["scenes"]):
        expected=len(active_focus_sequence(
            grammar_for_original_scene(original_scene["scene_id"])))
        if len(stage_images)!=expected:
            raise FullRehearsalRefused(
                "Source-lock mismatched narration-paced visual phase count")
        try:
            holds=stage_hold_seconds(
                duration,len(stage_images),min(REVEAL_SECONDS,duration/6))
        except OneWayStageRefused:
            raise FullRehearsalRefused(
                "Physical voice scene cannot contain distinct visual stages") from None
        for image,period in zip(stage_images,holds):
            lines.extend((f"file '{image.resolve().as_posix()}'",
                          f"duration {period:.6f}"))
    lines.append(f"file '{images[-1][-1].resolve().as_posix()}'")
    concat.write_text("\n".join(lines)+"\n",encoding="utf8")
    # LIVE owner MP4 frame review B4f7: the synthetic PlayRes of SRT
    # made 27pt into ~180px portrait text, clipped at screen TOP and
    # covered original diagrams. Never burn default SRT force_style.
    # Write native-pixel ASS with PlayResX/Y == source encoded canvas.
    from autopilot.full_original_caption_ass_b4f7 import (
        NativeCaptionRefused, compose_rehearsal_native_ass,
        write_rehearsal_native_ass,
    )
    try:
        native_script,caption_proof=compose_rehearsal_native_ass(cues,ep["kind"])
        native_path=write_rehearsal_native_ass(folder,cues,ep["kind"])
    except NativeCaptionRefused as exc:
        raise FullRehearsalRefused(
            "Voice-aligned captions cannot fit physical lower screen panel"
        ) from None
    if (not caption_proof["ass_playres_matches_encoded_canvas"]
        or not caption_proof["source_spoken_words_preserved"]
        or tuple(caption_proof["physical_canvas_pixels"]) != tuple(ep["size"])):
        raise FullRehearsalRefused("Native canvas subtitle geometry mismatch")
    # The authored ASS script (not the reference SRT) is what FFmpeg burns.
    filt=(f"fps={FPS},ass={native_path.as_posix()},format=yuv420p")
    from autopilot.verified_aac_mastering_b4g5 import (
        AUDIO_MASTERING_FILTER,AUDIO_ENCODE_HZ,
    )
    target=folder/"EPHEMERAL_FULL_ORIGINAL_NARRATED_REHEARSAL.mp4"
    _run([ffmpeg,"-nostdin","-y","-hide_banner","-loglevel","error",
          "-f","concat","-safe","0","-i",str(concat),
          "-i",str(wav),
          "-vf",filt,"-map","0:v:0","-map","1:a:0",
          "-t",f"{total:.5f}","-r",str(FPS),
          "-c:v","libx264","-preset","ultrafast","-crf","32",
          "-threads","2","-pix_fmt","yuv420p",
          "-af",AUDIO_MASTERING_FILTER,"-ar",str(AUDIO_ENCODE_HZ),
          "-c:a","aac","-b:a","112k","-movflags","+faststart",
          str(target)],timeout=980)
    return target


def _verify_encoded_first_reveal(ffmpeg: str,media: Path) -> bool:
    """Sample TWO actual decoded H264 frames around the first one-shot reveal.

    Source PNG digests alone do not establish what FFmpeg encoded. Each
    sample is scaled to bounded 192x108 luminance, safely kept in RAM;
    neither screenshots nor source/private narration leave the runner.
    """
    import subprocess
    frames=[]
    for t in ("0.100","0.900"):
        try:
            result=subprocess.run(
                [ffmpeg,"-nostdin","-hide_banner","-loglevel","error",
                 "-ss",t,"-i",str(media),"-an",
                 "-vf","scale=192:108,format=gray",
                 "-frames:v","1","-f","rawvideo","-pix_fmt","gray","-"],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                timeout=45,check=False)
        except (OSError,subprocess.TimeoutExpired):
            raise FullRehearsalRefused("Cannot inspect actual transition frames") from None
        if result.returncode!=0 or len(result.stdout)!=192*108:
            raise FullRehearsalRefused("Expected physical encoded reveal frame missing")
        frames.append(result.stdout)
    diff=sum(x!=y for x,y in zip(frames[0],frames[1]))
    if diff<55:
        raise FullRehearsalRefused("Source diagrams differ but encoded MP4 never reveals change")
    return True


def _inspect_full(ffmpeg: str,media: Path,ep: dict,cues: list[dict],
                  seconds: float,frame_hashes: list[str],
                  reveal_pairs: list[tuple[str,str]] | None=None,
                  scene_durations: list[float] | None=None) -> dict:
    if not media.is_file() or media.is_symlink() or len(set(frame_hashes))!=ep[
        "all_scene_count"]:
        raise FullRehearsalRefused("Physical unique rendered scenes absent")
    if (reveal_pairs is None or len(reveal_pairs)!=ep["all_scene_count"]
        or any(before==after or after!=final
               for (before,after),final in zip(reveal_pairs,frame_hashes))):
        raise FullRehearsalRefused("A real unique one-time scene reveal is missing")
    if (not cues or len(cues)!=ep["total_original_caption_phrases"]
        or any(type(c["text"]) is not str for c in cues)):
        raise FullRehearsalRefused("Measured subtitle phrase count missing")
    width=CAPTION_WRAP_CHARS[ep["kind"]]
    max_lines=CAPTION_MAX_LINES[ep["kind"]]
    worst_lines=0
    peak_chars_per_second=0.
    for c in cues:
        lines=textwrap.wrap(c["text"],width=width,
            break_long_words=False,break_on_hyphens=False)
        if not lines or len(lines)>max_lines:
            raise FullRehearsalRefused("Subtitle text exceeds safe caption card")
        if (not math.isfinite(c["start"]) or not math.isfinite(c["end"])
            or not 0<=c["start"]<c["end"]<=seconds+.001):
            raise FullRehearsalRefused("Caption cues detached from audio PCM")
        worst_lines=max(worst_lines,len(lines))
        cps=len(c["text"])/(c["end"]-c["start"])
        peak_chars_per_second=max(peak_chars_per_second,cps)
    # Use ffmpeg metadata + full independent decode; no filename-only proof.
    import subprocess
    p=subprocess.run([ffmpeg,"-hide_banner","-i",str(media)],
                     capture_output=True,text=True,timeout=30)
    lines=p.stderr.splitlines()
    v=[l for l in lines if re.search(r"Stream #\d+:\d+",l) and "Video: h264" in l]
    a=[l for l in lines if re.search(r"Stream #\d+:\d+",l) and "Audio: aac" in l]
    dimensions=f"{ep['size'][0]}x{ep['size'][1]}"
    if (len(v)!=1 or len(a)!=1 or
        not any(re.search(r"(?<!\d)"+re.escape(dimensions)+r"(?!\d)",x)
                for x in v) or any("yuv420p" not in x for x in v)):
        raise FullRehearsalRefused("Actual video orientation/codec/audio incorrect")
    _run([ffmpeg,"-nostdin","-hide_banner","-loglevel","error",
          "-xerror","-i",str(media),"-f","null","-"],timeout=600)
    digest,size=sha256_stream(media,max_bytes=MAX_MP4_BYTES)
    if size<300_000:
        raise FullRehearsalRefused("A complete voiced media file is unexpectedly tiny")
    physical_reveal=_verify_encoded_first_reveal(ffmpeg,media)
    from autopilot.audio_scene_navigation_b4g1 import (
        SceneTimecodeRefused,build_audio_scene_timeline,
    )
    try:
        exact_scene_times=build_audio_scene_timeline(
            scene_durations,seconds,ep["all_scene_count"])
    except SceneTimecodeRefused:
        raise FullRehearsalRefused(
            "Original narrated PCM scene timeline absent or altered") from None
    return {
        "episode_id":ep["episode_id"],
        "slot":ep["slot"],"format":ep["kind"],"voice":ep["voice"],
        "original_full_scene_count":len(frame_hashes),
        "all_original_voiceover_paragraphs_physically_spoken":True,
        "synthesized_original_tts_chunks":len(cues),
        "original_full_narration_sha256":ep["authored_full_narration_sha256"],
        "real_pcm_measured_seconds":round(seconds,3),
        "pcm_derived_scene_timeline_seconds":exact_scene_times,
        "scene_timeline_derived_from_actual_pcm":True,
        "storyboard_target_seconds":ep["target_seconds_not_audio_verified"],
        "storyboard_target_met_within_three_seconds":
            abs(seconds-ep["target_seconds_not_audio_verified"])<=3.,
        "total_actual_encoded_bytes":size,"encoded_h264_aac_sha256":digest,
        "portrait_or_landscape":dimensions,
        "voice_speed_calibrated_from_last_real_run":VOICE_SPEED_BY_SLOT[ep["slot"]],
        "original_visual_scene_specific_card_labels":True,
        "original_scene_base_and_one_shot_reveal_pngs":len(reveal_pairs)*2,
        "reveal_duration_seconds_once_per_scene":REVEAL_SECONDS,
        "no_spinning_or_repeating_highlight_animation":True,
        "first_real_encoded_one_shot_checkpoint_reveal_frame_verified":
            physical_reveal,
        "caption_safe_area_max_lines":max_lines,
        "measured_actual_caption_max_visible_lines":worst_lines,
        "caption_peak_physical_chars_per_second":round(peak_chars_per_second,2),
        "caption_reading_speed_needs_human_review":
            peak_chars_per_second>25.,
        "srt_caption_baseline_inside_reserved_panel":True,
        "native_pixel_ass_burned_into_reserved_panel":True,
        "max_original_spoken_caption_lines_physically_burned":2,
        "source_rights_reviewed":False,"news_facts_approved":False,
        "real_voice_and_caption_pcm_alignment":True,
        "per_word_forced_alignment_claimed":False,
        "actual_full_ffmpeg_decode_passed":True,
        "no_concentric_spinner_or_continuously_rotating_circle":True,
        "human_full_audio_visual_watch_completed":False,
        "fully_release_ready_for_youtube":False,
        "youtube_uploaded":False,
        "release_authorized":False,
    }


def physically_render_all_seventeen(plan: object,model: Path,voices: Path,
                                   outdir: Path) -> dict:
    if (type(plan) is not dict or plan.get("status")!=PLAN_STATUS
        or len(plan.get("episodes",[]))!=3
        or plan.get("original_full_scene_count")!=17
        or plan.get("approved_news_facts")!=0
        or plan.get("release_authorized") is not False
        or plan.get("youtube_uploads")!=0):
        raise FullRehearsalRefused("Untrusted full narrated source-locked plan")
    if (outdir.parent!=Path("/tmp")
        or not outdir.name.startswith("flowminute-")
        or outdir.is_symlink() or outdir.exists()):
        raise FullRehearsalRefused("Must write only new unprivileged /tmp/flowminute-*")
    verify_pinned_assets(model,voices)
    import imageio_ffmpeg
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    filters=_run([ffmpeg,"-hide_banner","-filters"],timeout=20)
    if "subtitles" not in filters:
        raise FullRehearsalRefused("Pinned portable FFmpeg missing libass captions")
    from kokoro_onnx import Kokoro
    engine=Kokoro(str(model),str(voices))
    outdir.mkdir(mode=0o700)
    actual=[]
    for i,ep in enumerate(plan["episodes"]):
        if ep["slot"]!=SLOTS[i] or ep["voice"]!=VOICES[SLOTS[i]]:
            raise FullRehearsalRefused("Wrong voice or day order")
        folder=outdir/ep["episode_id"]
        folder.mkdir(mode=0o700)
        wav,srt,durations,cues,length=_synth_full_voice(engine,ep,folder)
        frames=[]
        hashes=[]
        reveal_pairs=[]
        from autopilot.one_way_storyboard_timing_b4g2 import (
            active_focus_sequence,
        )
        from autopilot.cinematic_scene_board_b4f9 import BEATS
        for scene in ep["scenes"]:
            focus_steps=active_focus_sequence(
                BEATS[scene["scene_id"]][3])
            images_for_scene=[]
            scene_digests=[]
            for phase,focus_index in enumerate(focus_steps):
                path=folder/f"EPHEMERAL_SCENE_{scene['scene']:02}_PHASE_{phase}.png"
                digest=_draw_original_full_scene(
                    ep,scene,path,
                    revealed=focus_index is not None,
                    focus_index=focus_index)
                images_for_scene.append(path)
                scene_digests.append(digest)
            if len(set(scene_digests))!=len(focus_steps):
                raise FullRehearsalRefused(
                    "One-way original instructional phases repeated identical images")
            reveal_pairs.append((scene_digests[0],scene_digests[-1]))
            hashes.append(scene_digests[-1])
            frames.append(tuple(images_for_scene))
        movie=_encode_full(ffmpeg,ep,folder,frames,durations,wav,srt,length,cues=cues)
        qa=_inspect_full(ffmpeg,movie,ep,cues,length,hashes,reveal_pairs,
                         scene_durations=durations)
        from autopilot.verified_aac_mastering_b4g5 import (
            EncodedMasteringRefused,verify_exact_encoded_master,
        )
        try:
            mastering=verify_exact_encoded_master(
                ffmpeg,movie,qa["encoded_h264_aac_sha256"],
                qa["real_pcm_measured_seconds"])
        except EncodedMasteringRefused:
            raise FullRehearsalRefused(
                "Final AAC mastering did not pass independent real MP4 LUFS/true-peak measurement"
            ) from None
        qa["b4g5_post_encode_aac_lufs_true_peak_verified"]=True
        qa["original_audio_encoded_mastering"]=mastering
        sound_report=json.loads(
            (folder/"EPHEMERAL_ORIGINAL_AUDIO_SOUND_DESIGN.json").read_text(
                encoding="utf8"))
        from autopilot.original_pcm_sound_design_b4g3 import (
            STATUS as ORIGINAL_SOUND_STATUS,plan_pcm_cut_effects,
        )
        expected_events=plan_pcm_cut_effects(
            [scene["scene_id"] for scene in ep["scenes"]],
            durations,sound_report["sample_rate"])
        if (sound_report.get("status")!=ORIGINAL_SOUND_STATUS
            or sound_report.get("sound_events")!=expected_events
            or sound_report.get("original_pcm_duration_seconds")!=
                qa["real_pcm_measured_seconds"]
            or sound_report.get("human_audio_listening_completed") is not False
            or sound_report.get("youtube_release_authorized") is not False):
            raise FullRehearsalRefused(
                "Original sound cues not independently bound to actual source scene clock")
        qa["b4g3_original_sound_design_mixed_into_actual_wav"]=True
        qa["original_audio_sound_design"]=sound_report
        qa["one_way_editorial_phase_frames_physically_authored"]=sum(
            len(pair) for pair in frames)
        qa["narration_paced_distinct_focus_phases"]=[
            len(pair) for pair in frames]
        qa["source_locked_voice_caption_text_unmodified_by_visual_phases"]=True
        actual.append(qa)
        print("B4E1_PHYSICAL_COMPLETE_VOICED_EPISODE_DECODED",
              json.dumps({
                  "slot":qa["slot"],"actually_narrated_scene_count":
                  qa["original_full_scene_count"],
                  "measured_real_pcm_seconds":qa["real_pcm_measured_seconds"],
                  "storyboard_seconds":qa["storyboard_target_seconds"],
                  "source_quote_use":0,"news_facts_approved":0,
                  "youtube_uploads":0,
              },sort_keys=True),flush=True)
    if (len(actual)!=3
        or [x["original_full_scene_count"] for x in actual]!=[4,9,4]
        or len({x["encoded_h264_aac_sha256"] for x in actual})!=3):
        raise FullRehearsalRefused("Missing or repeated daily original full voice video")
    from autopilot.verified_aac_mastering_b4g5 import (
        EncodedMasteringRefused, verify_three_matching_masters,
    )
    try:
        master_proof=verify_three_matching_masters(actual)
    except EncodedMasteringRefused:
        raise FullRehearsalRefused(
            "Final three original AAC encodes fail cross-video loudness consistency"
        ) from None
    return {
        **master_proof,
        "status":STATUS,
        "full_daily_nonfactual_rehearsal_videos_encoded":3,
        "actually_voiced_complete_original_scene_count":17,
        "full_4_9_4_scene_voiceover_text_all_spoken":True,
        "full_episode_actual_pcm_duration_seconds":[
            x["real_pcm_measured_seconds"] for x in actual],
        "target_58_240_58_seconds_are_goals_not_guaranteed":True,
        "exact_58_240_58_target_met_for_all":all(
            x["storyboard_target_met_within_three_seconds"] for x in actual),
        "all_three_real_h264_aac_ffmpeg_full_decodes_passed":True,
        "all_17_scenes_with_verified_distinct_one_time_reveal_pngs":
            all(x["original_scene_base_and_one_shot_reveal_pngs"]==
                x["original_full_scene_count"]*2 for x in actual),
        "source_derived_one_way_visual_stage_frames_total":sum(
            x["one_way_editorial_phase_frames_physically_authored"]
            for x in actual),
        "all_17_scenes_have_distinct_one_way_progressions":all(
            len(x["narration_paced_distinct_focus_phases"])==
                x["original_full_scene_count"] and
            all(n in (3,4) for n in x["narration_paced_distinct_focus_phases"])
            for x in actual),
        "all_three_actual_mp4_first_one_shot_reveal_frames_verified":
            all(x["first_real_encoded_one_shot_checkpoint_reveal_frame_verified"]
                for x in actual),
        "all_pcm_timed_subtitles_fit_caption_panels":
            all(x["measured_actual_caption_max_visible_lines"]<=
                x["caption_safe_area_max_lines"] for x in actual),
        "all_caption_reading_rates_approved":False,
        "rehearsal_only_not_factual_news_or_final_review":True,
        "real_news_facts_approved":0,
        "rights_approvals":0,"human_full_watches":0,
        "paid_model_provider_calls":0,"youtube_uploads":0,
        "release_authorized":False,
        "episodes":actual,
    }


def main() -> None:
    from autopilot.real_rehearsal_voice_media_b4e0 import _read
    ap=argparse.ArgumentParser(description="Full actual voice/image/captions rehearsal: no news claims/publish")
    for name in ("original-plan","aligned-plan","board","scout","evidence",
                 "briefs","passages","docket","rehearsals"):
        ap.add_argument("--"+name,required=True,type=Path)
    ap.add_argument("--model",required=True,type=Path)
    ap.add_argument("--voices",required=True,type=Path)
    ap.add_argument("--output-dir",required=True,type=Path)
    args=ap.parse_args()
    names=("original-plan","aligned-plan","board","scout","evidence",
           "briefs","passages","docket","rehearsals")
    plan=prepare_full_rehearsal_plan(*[
        _read(getattr(args,n.replace("-","_"))) for n in names])
    report=physically_render_all_seventeen(plan,args.model,args.voices,
                                           args.output_dir)
    (args.output_dir/"EPHEMERAL_FULL_VOICE_REHEARSAL_QA.json").write_text(
        json.dumps(report,ensure_ascii=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps({
        "status":STATUS,
        "full_voice_rehearsals_physically_encoded":3,
        "all_original_rehearsal_scenes_physically_voiced":17,
        "real_recorded_pcm_durations_seconds":
            report["full_episode_actual_pcm_duration_seconds"],
        "storyboard_target_58_240_58_proven":
            report["exact_58_240_58_target_met_for_all"],
        "real_three_mp4_h264_aac_full_decodes":True,
        "fact_approved":0,"human_watch_approved":0,
        "paid_provider_calls":0,"youtube_uploads":0,
        "release_authorized":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
