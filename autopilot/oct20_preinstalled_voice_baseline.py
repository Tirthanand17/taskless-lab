"""Phase 3Y: REAL optional preinstalled eSpeak bilingual speech benchmark.

This is a deliberately LOW-FIDELITY reference to measure whether the first
English/Hindi scripts fit their intended scene slots. It DOES synthesize WAV
speech when the eSpeak binary was already installed, but it is mechanical and
NOT approved FlowMinute narration. No model download, HF contact, API, user
laptop, new provider, external data, voice identity or YouTube action.

The sample is bounded to the existing verified OCT20 FIRST SCENE only. This
function is never part of the publisher, render, mux or live release path.
"""
from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import shutil
import subprocess
import wave

from .agent_org import WorkflowError
from .oct20_owned_voice_handoff import create_oct20_voice_session_packet
from .phase3_voice_subtitle_handoff import inspect_external_voice_wav

SPEAKERS={
    "fm_20261020_short_en":("en-us",150,"en","narrator_en_baseline"),
    "fm_20261020_short_hi":("hi",135,"hi","narrator_hi_baseline"),
}
MAX_SAMPLE_BYTES=1_000_000


def _deny():
    raise WorkflowError("Offline mechanical voice comparison HOLD")


def original_first_scene(episode_id:str)->dict:
    if type(episode_id) is not str or episode_id not in SPEAKERS:
        _deny()
    packet=create_oct20_voice_session_packet()
    lanes=[x for x in packet["lanes"] if x["episode_id"]==episode_id]
    if len(lanes)!=1 or lanes[0]["cue_count"]!=7:
        _deny()
    item=lanes[0]
    first=item["cues"][0]
    _voice,speed,lang,_role=SPEAKERS[episode_id]
    if (item["language"]!=lang or type(first["recording_text"]) is not str
            or first["editorial_start_second"]!=0
            or first["editorial_end_second"] not in (4,5)
            or first["cue_is_estimated_not_asr_aligned"] is not True
            or first["recording_text_sha256"]!=
                sha256(first["recording_text"].encode("utf-8")).hexdigest()):
        _deny()
    return {
        "episode_id":episode_id,
        "source_first_scene_text":first["recording_text"],
        "first_scene_duration_seconds":first["target_scene_seconds"],
        "source_first_scene_sha256":first["recording_text_sha256"],
        "voice_language":lang,
        "baseline_voice_rate":speed,
    }


def make_existing_espeak_comparison(*,episode_id:str,output_path:Path)->dict:
    """Explicit caller-requested local sample WAV. Not natural speech.

    Runs an ALREADY INSTALLED local eSpeak CLI with argument-array and stdin,
    not a shell. Explicit path must be fresh; no downloads and no new folders.
    No full script/narration is rendered. Deliberately excludes all upload APIs.
    """
    scene=original_first_scene(episode_id)
    if (not isinstance(output_path,Path)
            or output_path.suffix.lower()!=".wav"
            or output_path.exists() or output_path.is_symlink()
            or not output_path.parent.is_dir()
            or output_path.parent.is_symlink()):
        _deny()
    executable=shutil.which("espeak")
    if not executable:
        _deny()
    voice,speed,language,role=SPEAKERS[episode_id]
    try:
        run=subprocess.run(
            [executable,"--stdin","-v",voice,"-s",str(speed),
             "-a","140","-w",str(output_path)],
            input=scene["source_first_scene_text"],text=True,
            encoding="utf-8",stdin=None,capture_output=True,
            timeout=15,check=False,
        )
        if run.returncode!=0 or not output_path.is_file():
            _deny()
        if not 1000<=output_path.stat().st_size<=MAX_SAMPLE_BYTES:
            _deny()
        with wave.open(str(output_path),"rb") as reader:
            observed=reader.getnframes()/reader.getframerate()
        # Reuse the REAL existing technical waveform inspection; check
        # against observed metadata, NOT the editorial scene-time target.
        receipt=inspect_external_voice_wav(
            output_path,episode_id=episode_id,
            expected_seconds=observed,
            declared_narrator_id=role,
            declared_language=language,
        )
        if (receipt["real_speech_verified"] is not False
                or receipt["license_rights_verified"] is not False
                or receipt["publishable"] is not False
                or receipt["sha256"]!=sha256(output_path.read_bytes()).hexdigest()):
            _deny()
    except (subprocess.TimeoutExpired,OSError,ValueError,
            EOFError,wave.Error,WorkflowError):
        output_path.unlink(missing_ok=True)
        _deny()
    # This baseline is intentionally not eligible for voice selection,
    # regardless of language, duration, waveform, lack of clipping or grade.
    baseline_seconds=round(observed,3)
    gap=round(baseline_seconds-scene["first_scene_duration_seconds"],3)
    return {
        "status":"ACTUAL_ESPEAK_MECHANICAL_BASELINE_REJECTED_FOR_NARRATION",
        "episode_id":episode_id,
        "source_first_scene_sha256":scene["source_first_scene_sha256"],
        "wav_sha256":receipt["sha256"],
        "technical_pcm_screen_passed":True,
        "recorded_voice_language_claim":language,
        "editorial_scene_target_seconds":scene["first_scene_duration_seconds"],
        "observed_mechanical_tts_seconds":baseline_seconds,
        "mechanical_tts_minus_edit_target_seconds":gap,
        "spoken_word_timing_verified":False,
        "actual_human_speech_verified":False,
        "natural_voice_quality_verified":False,
        "native_hindi_pronunciation_verified":False,
        "distinct_short_speakers_verified":False,
        "commercial_voice_rights_reviewed":False,
        "not_a_production_voice":True,
        "eligible_for_mux":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "new_models_downloaded":0,
        "external_network_requests":0,
        "monthly_recurring_infrastructure_inr":0,
    }
