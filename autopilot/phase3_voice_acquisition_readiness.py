"""FlowMinute Phase 3: source-locked, read-only narrator acquisition handoff.

No input media, network, voice synthesis, rights decision, production account,
reviewer authentication, approval, recording or publishing is performed.
This packet lists exact planned 3-video requirements, never supplied evidence.
"""
from __future__ import annotations

from hashlib import sha256
import json

from .agent_org import WorkflowError
from .phase2r3_authored_pack_audit import SOURCE, SECTIONS, TIME, _sections, _seconds
from .phase2r3_audience_language_lanes import prepare_audience_language_lanes
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv

VERSION = "flowminute-original-voice-acquisition-readiness-v1"
MAX_WAV_BYTES = 70 * 1024 * 1024
REQUIRED_EVIDENCE = (
    "original_full_duration_pcm_wav_from_explicitly_approved_source",
    "sha256_and_technical_wav_intake_of_exact_original_episode",
    "authentic_commercial_and_adaptation_rights_per_voice_and_asset",
    "speaker_consent_or_model_and_voice_artifact_license_legally_reviewed",
    "independent_native_language_pronunciation_and_naturalness_listening",
    "short_narrators_audibly_distinct_by_independent_listening",
    "corrected_srt_checked_against_actually_spoken_words_and_timestamps",
    "separate_audio_visual_scene_and_final_mix_human_quality_review",
)
_ACQUISITION = (
    "owner_recorded_voice_with_real_documented_speaker_consent",
    "owner_approved_pinned_offline_tts_after_model_loader_and_voice_license_audit",
)


def _canonical(value: dict) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def build_voice_acquisition_readiness_packet(*, markdown: str | None = None) -> dict:
    """Create a deterministic, immutable-in-meaning list of *missing* proofs.

    Caller-supplied Markdown is useful for offline mutation testing, not
    authenticated creator, source or reviewer approval. A spoofed packet can
    never promote itself by setting clearance fields.
    """
    raw = SOURCE.read_text(encoding="utf-8") if markdown is None else markdown
    sections = _sections(raw)
    captions = build_subtitles_from_authored_csv(markdown=raw)
    lanes = prepare_audience_language_lanes(markdown=raw)["episodes"]
    mapped = {lane["episode_id"]: lane for lane in lanes}
    if len(sections) != 3 or set(mapped) != {entry[2] for entry in SECTIONS}:
        raise WorkflowError("Original bilingual source inventory changed")

    episodes = []
    for section, spec in zip(sections, SECTIONS):
        kind, language, episode, narrator, seconds, beats = spec
        rows = TIME.findall(section)
        lane = mapped[episode]
        sub = captions[episode]
        if (len(rows) != beats or not rows or lane["episode_kind"] != kind
                or lane["original_spoken_language"] != language
                or lane["narrator_plan_id"] != narrator
                or lane["script_section_sha256"] != sha256(
                    section.encode("utf-8")).hexdigest()
                or sub["language"] != language
                or sub["narrator_plan_id"] != narrator
                or sub["duration_ms"] != seconds * 1000
                or sub["srt_sha256"] != lane["draft_srt_sha256"]):
            raise WorkflowError("Original episode/script/caption readiness mismatch")
        prior = 0
        for a, b, c, d, spoken, _visual in rows:
            start, end = _seconds(a, b), _seconds(c, d)
            if (start != prior or end <= start or not spoken.strip()):
                raise WorkflowError("Incomplete original scene voice plan")
            prior = end
        if prior != seconds:
            raise WorkflowError("Original scene duration does not fill video")
        speech = " ".join(row[4] for row in rows)
        if (sha256(speech.encode("utf-8")).hexdigest()
                != lane["script_spoken_text_sha256"]):
            raise WorkflowError("Original spoken text hash differs from language lane")
        episodes.append({
            "episode_id": episode,
            "kind": kind,
            "original_language": language,
            "planned_narrator_id": narrator,
            "planned_duration_seconds": seconds,
            "authored_scene_count": beats,
            "spoken_script_sha256": lane["script_spoken_text_sha256"],
            "source_section_sha256": lane["script_section_sha256"],
            "estimated_draft_srt_sha256": sub["srt_sha256"],
            "voice_wav_format_requirement": "uncompressed_PCM16_mono_or_stereo",
            "voice_wav_allowed_sample_rates_hz": (16000, 22050, 24000, 44100, 48000),
            "voice_wav_max_bytes": MAX_WAV_BYTES,
            "voice_duration_tolerance_seconds": 1.5,
            "caption_timing_state": "SCRIPT_ESTIMATE_NOT_SPEECH_ALIGNED",
            "evidence_required_not_collected": REQUIRED_EVIDENCE,
            "source_wav_received": False,
            "language_and_voice_listening_verified": False,
            "commercial_rights_authenticated": False,
            "actual_spoken_caption_alignment_verified": False,
            "approved_for_render_or_mux": False,
            "approved_for_upload_or_publish": False,
        })

    if len({x["planned_narrator_id"] for x in episodes}) != 3:
        raise WorkflowError("Original three narrated episodes need distinct narrator plans")
    if {x["original_language"] for x in episodes if x["kind"] == "short"} != {"hi", "en"}:
        raise WorkflowError("Both separate-language Shorts required")

    summary = {
        "schema_version": VERSION,
        "status": "SOURCE_LOCKED_VOICE_ASSET_REQUEST_ONLY_NOT_RECEIVED",
        "authored_markdown_sha256": sha256(raw.encode("utf-8")).hexdigest(),
        "episodes": episodes,
        "permitted_paths_to_examine_after_separate_owner_authorization": _ACQUISITION,
        "evidence_categories_required": REQUIRED_EVIDENCE,
        "real_voice_assets_available_in_this_packet": 0,
        "independently_verified_voice_assets": 0,
        "voice_provider_or_model_connected": False,
        "legal_or_human_editor_authenticated": False,
        "separate_owner_authorization_for_new_model_or_service_obtained": False,
        "authenticity_or_naturalness_verified": False,
        "real_audio_caption_alignment_verified": False,
        "release_or_production_ready": False,
        "publishing_authorized": False,
        "network_calls": 0,
        "files_written": 0,
        "recurring_infrastructure_budget_inr": 0,
    }
    fingerprint = sha256(_canonical(summary)).hexdigest()
    return {**summary, "packet_sha256": fingerprint}
