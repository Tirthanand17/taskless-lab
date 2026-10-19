"""Three-lane final AAC QA handoff for English Short, Hindi Short, Hindi long.

Combines existing full-duration per-cue acoustic results with *both*
Short track-collision fingerprints. Cannot approve voices or publishing.
All inputs are LOCAL, untrusted, synthetic unless independently sourced.
"""
from __future__ import annotations

from .agent_org import WorkflowError
from .cloud_capacity_admission import LANES
from .cloud_cue_audio_activity import (
    CueAcousticCoverage,summarize_cue_activity,
)
from .cloud_short_voice_collision_screen import (
    ShortAudioFingerprint,compare_short_audio_fingerprints,
)

REQUIRED_LANES=frozenset(x.lane for x in LANES)


def evaluate_three_lane_audio_handoff(
    cue_reports:tuple[CueAcousticCoverage,...],
    short_fingerprints:tuple[ShortAudioFingerprint,...],
)->dict:
    """Never release; only declare whether technical collision checks passed."""
    # Use existing field-shape and false-positive-approval enforcement.
    cue=summarize_cue_activity(cue_reports)
    short=compare_short_audio_fingerprints(short_fingerprints)
    by_lane={x.lane:x for x in cue_reports}
    if set(by_lane)!=REQUIRED_LANES:
        raise WorkflowError("Entire English/Hindi/long narration set is required")
    if len(by_lane)!=len(cue_reports):
        raise WorkflowError("Duplicate source cue evidence")
    short_by_lane={x.lane:x for x in short_fingerprints}
    for lane in ("short_en","short_hi"):
        if short_by_lane[lane].media_sha256!=by_lane[lane].media_sha256:
            raise WorkflowError("Short fingerprint is not tied to the same MP4")
    errors=[]
    for lane in sorted(REQUIRED_LANES):
        record=by_lane[lane]
        if (record.entire_audio_decoded is not True
                or record.technical_cue_activity_pass is not True
                or record.blockers
                or type(record.cue_count) is not int
                or record.cue_count<=0
                or type(record.activity_windows_scanned) is not int
                or record.activity_windows_scanned<=0
                or type(record.cue_count_with_acoustic_activity) is not int
                or record.cue_count_with_acoustic_activity!=record.cue_count
                or type(record.acoustically_sparse_cues) is not int
                or record.acoustically_sparse_cues!=0
                or type(record.lowest_cue_active_percent) is not int
                or not 25<=record.lowest_cue_active_percent<=100):
            errors.append(lane+":INCOMPLETE_OR_SPARSE_CUE_ACOUSTICS")
    for reason in short["audio_collision_blockers"]:
        errors.append("SHORT_AUDIO_COLLISION:"+reason)
    errors=tuple(sorted(set(errors)))
    return {
        "status":"THREE_LANE_AUDIO_TECHNICAL_HANDOFF_ONLY",
        "three_language_lane_shapes_present":True,
        "cue_acoustic_coverage_checked_for_all_three":True,
        "exact_final_short_track_collision_screen_checked":True,
        "technical_audio_handoff_unblocked":not errors,
        "technical_blocking_reasons":errors,
        "real_spoken_words_verified":False,
        "natural_human_voice_quality_verified":False,
        "distinct_short_narrator_identity_verified":False,
        "native_hindi_english_speech_verified":False,
        "spoken_subtitle_alignment_verified":False,
        "commercial_voice_and_media_rights_verified":False,
        "independent_signed_human_review_verified":False,
        "zero_rupee_sustainable_cloud_media_capacity_verified":False,
        "upload_authorized":False,
        "publishing_authorized":False,
        "monthly_recurring_infrastructure_inr":0,
    }
