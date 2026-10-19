"""October 20 FlowMinute owned-voice handoff and full-take technical intake.

Reuses existing PCM WAV verification for the actual 42s EN, 44s HI and 480s
HI-long AI-agent episodes; it DOES NOT use the older CSV durations/voice IDs.

The script/source-verified packet is a human narrator recording cue sheet.
Scene times are editorial guide marks, NOT measured speech word timings.
Intake checks *caller-supplied* PCM bytes, source SHA and a locally supplied
rights file SHA, but cannot authenticate consent, copyright, actual language,
natural human voices, distinct speakers or ASR/SRT synchronization.

No device access, microphone, TTS, downloaded model, cloud provider, Google,
account connection, token, upload, media mux, shell execution or publishing.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Sequence
import re

from .agent_org import WorkflowError
from .oct20_silent_concept_preview import load_preview_plan
from .phase3_voice_subtitle_handoff import inspect_external_voice_wav
from .phase3_complete_narration_intake import _hash_existing

TARGETS={
    "fm_20261020_short_en":("en","short",42,"narrator_en_short_oct20"),
    "fm_20261020_short_hi":("hi","short",44,"narrator_hi_short_oct20"),
    "fm_20261020_long_hi":("hi","long",480,"narrator_hi_long_oct20"),
}
HEX=re.compile(r"[a-f0-9]{64}\Z")
MAX_RIGHTS_BYTES=200_000
_FILENAME=re.compile(r"[a-z0-9_]{3,70}\.recording_notes\.md\Z")


def _deny():
    # Do not include private WAV paths, full speech or rights documents
    # in exceptions because CI/application logs may not be private.
    raise WorkflowError("October 20 voice evidence incomplete; HOLD")


def _script_digest(lines:tuple[str,...])->str:
    return sha256("\n".join(lines).encode("utf-8")).hexdigest()


def create_oct20_voice_session_packet()->dict:
    """Generate all 25 exact-scene narrator lines from the researched pack.

    The operator may use these instructions to record or source original
    licensed speech, but this function does not claim any recording exists.
    """
    data=load_preview_plan()  # Includes entire source/fact/language review.
    source=data["episodes"]
    if type(source) is not list or len(source)!=3:
        _deny()
    by_id={x["episode_id"]:x for x in source}
    if set(by_id)!=set(TARGETS):
        _deny()
    records=[]
    hashes=set()
    for episode_id,(lang,kind,duration,role) in TARGETS.items():
        ep=by_id[episode_id]
        if (ep["kind"]!=kind or ep["original_spoken_language"]!=lang
                or ep["target_duration_seconds"]!=duration
                or not ep["narrator_plan_id"].endswith("_unlicensed")):
            _deny()
        cues=[]
        previous=0
        for number,scene in enumerate(ep["segments"],1):
            text=scene["narration"]
            start=scene["start_second"]
            end=scene["end_second"]
            if (type(start) is not int or type(end) is not int
                    or start!=previous or not start<end<=duration
                    or type(text) is not str or not text.strip()
                    or "\n" in text or "\r" in text):
                _deny()
            cues.append({
                "scene":number,
                "editorial_start_second":start,
                "editorial_end_second":end,
                "target_scene_seconds":end-start,
                "recording_text":text,
                "recording_text_sha256":sha256(text.encode("utf-8")).hexdigest(),
                "cue_is_estimated_not_asr_aligned":True,
            })
            previous=end
        if previous!=duration or len(cues)!=(7 if kind=="short" else 11):
            _deny()
        digest=_script_digest(tuple(c["recording_text"] for c in cues))
        if digest in hashes:
            _deny()
        hashes.add(digest)
        records.append({
            "episode_id":episode_id,
            "language":lang,
            "kind":kind,
            "target_seconds":duration,
            "narrator_role":role,
            "narrator_person_identified_or_licensed":False,
            "script_sha256":digest,
            "cue_count":len(cues),
            "cues":cues,
        })
    return {
        "status":"ORIGINAL_THREE_VIDEO_NARRATOR_RECORDING_SCRIPT_ONLY",
        "date_local":"2026-10-20",
        "recording_take_count_required":3,
        "total_recording_cues":25,
        "lanes":records,
        "recording_instructions":{
            "source":"Record original consented human speech. Never reuse another creator's narration or clone a person without authorization.",
            "capture":"Record a separate full take per episode; prefer quiet space, natural conversational pacing, PCM16 WAV mono 48000 Hz. Leave short intentional pauses near scene transitions.",
            "humanity":"Do not use synthetic tones as narrators or assume an AI-generated voice is a distinct human speaker.",
            "hindi":"Speak in natural Hindi with clear Devanagari pronunciation; do not simply dub the English script.",
            "timing":"Scene target seconds are editing guide marks, not verified audio timestamps. Retime video/subtitles based on real audio rather than forcibly speeding up speech.",
            "identity":"For production, privately retain independent speaker consent and a commercial-use rights agreement. Keep signed evidence out of public repositories.",
            "rights":"A file's claimed license and SHA do not prove lawful use or that a real person spoke.",
            "qa":"After actual WAV receipt: independently listen, transcribe and align; review language, speech quality, clipping and rights before any mux or upload.",
        },
        "independent_human_voice_confirmed":False,
        "rights_legally_authenticated":False,
        "actual_wav_takes_received":0,
        "word_level_audio_alignment_verified":False,
        "full_video_or_audio_mux_completed":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_requests":0,
        "monthly_recurring_infrastructure_inr":0,
    }


@dataclass(frozen=True,repr=False)
class Oct20OwnedVoiceTake:
    episode_id:str
    source_wav:Path
    declared_wav_sha256:str
    script_sha256:str
    narrator_role:str
    rights_file:Path
    declared_rights_sha256:str
    source_kind:str
    commercial_use_declared:bool
    speaker_consent_declared:bool

    def __repr__(self):
        return "<Oct20OwnedVoiceTake: paths and claimed rights REDACTED>"


def screen_oct20_owned_voice_takes(
    takes:Sequence[Oct20OwnedVoiceTake],
)->dict:
    """Technical screening of THREE real WAVs + locally declared rights bytes.

    The caller owns these files; this function never produces recording bytes
    or publishes anything. Positive checks are only documentary declarations.
    """
    if type(takes) not in (tuple,list) or len(takes)!=3:
        _deny()
    script=create_oct20_voice_session_packet()
    expected={x["episode_id"]:x for x in script["lanes"]}
    accepted=set()
    wav_hashes=set()
    rights_hashes=set()
    for take in takes:
        if type(take) is not Oct20OwnedVoiceTake:
            _deny()
        ep=take.episode_id
        if type(ep) is not str or ep not in expected or ep in accepted:
            _deny()
        item=expected[ep]
        if (take.narrator_role!=item["narrator_role"]
                or take.script_sha256!=item["script_sha256"]
                or take.source_kind!="owned_recording"
                or take.commercial_use_declared is not True
                or take.speaker_consent_declared is not True
                or type(take.declared_wav_sha256) is not str
                or HEX.fullmatch(take.declared_wav_sha256) is None
                or type(take.declared_rights_sha256) is not str
                or HEX.fullmatch(take.declared_rights_sha256) is None
                or not isinstance(take.source_wav,Path)
                or not isinstance(take.rights_file,Path)):
            _deny()
        try:
            rights=_hash_existing(take.rights_file,MAX_RIGHTS_BYTES)
        except (OSError,WorkflowError):
            _deny()
        if rights!=take.declared_rights_sha256:
            _deny()
        try:
            # Reuse existing real bounded PCM WAV/silence/duration QA.
            sound=inspect_external_voice_wav(
                take.source_wav,episode_id=ep,
                expected_seconds=item["target_seconds"],
                declared_narrator_id=item["narrator_role"],
                declared_language=item["language"],
            )
        except (OSError,WorkflowError):
            _deny()
        if (type(sound) is not dict
                or sound.get("sha256")!=take.declared_wav_sha256
                or sound.get("status")!="WAV_TECHNICAL_EVIDENCE_NOT_SPEECH_APPROVAL"
                or sound.get("declared_language")!=item["language"]
                or sound.get("declared_narrator_id")!=item["narrator_role"]
                or sound.get("real_speech_verified") is not False
                or sound.get("human_naturalness_verified") is not False
                or sound.get("license_rights_verified") is not False
                or sound.get("audio_caption_alignment_verified") is not False
                or type(sound.get("duration_seconds")) not in (int,float)
                or abs(sound["duration_seconds"]-item["target_seconds"])>1.5):
            _deny()
        if sound["sha256"] in wav_hashes:
            _deny()
        accepted.add(ep)
        wav_hashes.add(sound["sha256"])
        rights_hashes.add(rights)
    if accepted!=set(TARGETS) or len(wav_hashes)!=3:
        _deny()
    return {
        "status":"OCT20_THREE_FULL_WAVS_TECHNICAL_ONLY_HUMAN_REVIEW_REQUIRED",
        "expected_episode_count":3,
        "wav_digest_checks_passed":3,
        "recording_lengths_matched_targets":True,
        "local_rights_document_hashes_matched":True,
        "declared_owned_recording_source_present":True,
        "distinct_wav_file_bytes":len(wav_hashes),
        "independent_human_voice_confirmed":False,
        "real_speech_language_verified":False,
        "two_distinct_short_speakers_audibly_verified":False,
        "commercial_voice_rights_legally_authenticated":False,
        "human_consent_independently_authenticated":False,
        "word_level_asr_transcription_verified":False,
        "srt_sync_verified":False,
        "ready_for_media_mux":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_requests":0,
        "monthly_recurring_infrastructure_inr":0,
    }


def export_oct20_narrator_notes(directory:Path)->dict:
    """Explicit local export of the script only; NO WAV or rights docs.

    Never invoked automatically in CI or connected accounts. Refuses any
    preexisting destination file before writing the first note.
    """
    if (not isinstance(directory,Path) or directory.is_symlink()
            or not directory.is_dir()):
        _deny()
    packet=create_oct20_voice_session_packet()
    targets={}
    for lane in packet["lanes"]:
        filename=lane["episode_id"]+".recording_notes.md"
        if not _FILENAME.fullmatch(filename):
            _deny()
        target=directory/filename
        if target.exists() or target.is_symlink():
            _deny()
        targets[lane["episode_id"]]=target
    for lane in packet["lanes"]:
        target=targets[lane["episode_id"]]
        lines=[
            "# FLOWMINUTE LAB / ORIGINAL NARRATOR RECORDING NOTES",
            "",
            "**Draft editorial cues. Not spoken timing or verified consent.**",
            f"Episode: {lane['episode_id']}",
            f"Language: {lane['language']}",
            f"Target length: {lane['target_seconds']} seconds",
            f"Intended narrator role: {lane['narrator_role']} (UNLICENSED)",
            "",
            "Record in a quiet room using a natural voice. Do not upload or",
            "reuse anyone else's voice without their independent permission.",
            "Use PCM16 mono WAV, ideally 48 kHz. Record a full take per video.",
            "Do not speed up speech artificially to match estimated cues.",
            "",
        ]
        for cue in lane["cues"]:
            lines.extend([
                f"## Scene {cue['scene']} — guide {cue['editorial_start_second']}s to {cue['editorial_end_second']}s",
                "",
                cue["recording_text"],
                "",
            ])
        lines.extend(["**HOLD:** Independent consent, legal rights, speech",
                      "transcription, timing and pronunciation review missing.",""])
        target.write_text("\n".join(lines),encoding="utf-8")
    return {
        "status":"THREE_SCRIPT_NOTES_EXPORTED_NO_VOICE_RECORDER",
        "files_written":3,
        "voice_assets_created":0,
        "actual_speech_recorded":False,
        "signed_consent_verified":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_requests":0,
    }
