"""Phase 3R2: untrusted actual-timecode SRT candidate intake, never release.

A source-locked subtitle file is checked against the exact original Hindi or
English authored episode and a separately technically inspected complete WAV.
The file's timestamps are only *submitted candidate positions*. Neither SRT
parsing nor SHA-256 validates that the words were spoken, understood, aligned
to audio, legally licensed or reviewed by an independent human.

No ASR, voice downloads, provider, network, video mux, upload or file writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Sequence

from .agent_org import WorkflowError
from .phase2r3_authored_pack_audit import SOURCE, SECTIONS, TIME, _sections, _seconds
from .phase3_complete_narration_intake import (
    CompleteNarrationTake, EPISODES, review_complete_narration_takes,
)
from .phase3_voice_subtitle_handoff import (
    MAX_CUE_CHARS, MAX_CUE_DURATION_MS, build_subtitles_from_authored_csv,
)

HEX = re.compile(r"[0-9a-f]{64}\Z")
TIMECODE = re.compile(r"(\d\d):([0-5]\d):([0-5]\d),(\d{3})\Z")
TIMING = re.compile(r"(\d\d:[0-5]\d:[0-5]\d,\d{3}) --> (\d\d:[0-5]\d:[0-5]\d,\d{3})\Z")
BLOCKED = re.compile(r"[\x00-\x08\x0b-\x1f\x7f\u202a-\u202e\u2066-\u2069]")
MAX_SRT_BYTES = 100_000
MAX_CUES = 800
MAX_INTER_CUE_GAP_MS = 15_000
MAX_FIRST_CUE_DELAY_MS = 5_000
MAX_END_TRAILING_MS = 8_000
# Scene boundary estimates are NOT proof of audible speech alignment. They
# only detect grossly shifted scripted words against existing authored visuals.
MAX_SCENE_BOUNDARY_DRIFT_SHORT_MS = 3_000
MAX_SCENE_BOUNDARY_DRIFT_LONG_MS = 7_000
ALLOWED_ORIGINS = frozenset(("manually_timecoded_unverified", "automatic_alignment_unverified"))


@dataclass(frozen=True)
class CandidateCaption:
    episode_id: str
    srt_path: Path
    srt_sha256: str
    wav_sha256: str
    declared_language: str
    declared_narrator_id: str
    origin_claim: str


def _milliseconds(value: str) -> int:
    matched = TIMECODE.fullmatch(value)
    if not matched:
        raise WorkflowError("Invalid complete SRT timecode")
    hours, minutes, seconds, millis = map(int, matched.groups())
    if hours != 0:
        raise WorkflowError("Only current sub-hour episodes are accepted")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def _load_plain_file(path: Path) -> tuple[str, str]:
    if (not isinstance(path, Path) or path.is_symlink() or not path.is_file()
            or path.suffix.lower() != ".srt" or not 1 <= path.stat().st_size <= MAX_SRT_BYTES):
        raise WorkflowError("Plain bounded regular SRT file required")
    content = path.read_bytes()
    if len(content) > MAX_SRT_BYTES or content.startswith(b"\xef\xbb\xbf"):
        raise WorkflowError("Oversized or BOM-prefixed SRT")
    try:
        value = content.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise WorkflowError("SRT must be valid UTF-8") from exc
    if ("\r" in value or BLOCKED.search(value) or "<" in value
            or "\t" in value):
        raise WorkflowError("Potentially unsafe subtitle control or markup")
    return value, sha256(content).hexdigest()


def _parse_srt(raw: str) -> list[tuple[int, int, str]]:
    if not raw.endswith("\n") or "\n\n\n" in raw:
        raise WorkflowError("SRT must contain complete newline-delimited cues")
    blocks = raw.strip("\n").split("\n\n")
    if not 1 <= len(blocks) <= MAX_CUES:
        raise WorkflowError("No captions or excessive SRT cues")
    parsed = []
    previous_end = 0
    for index, block in enumerate(blocks, 1):
        lines = block.split("\n")
        if len(lines) != 3 or lines[0] != str(index):
            raise WorkflowError("Exactly one text line and numbered cue required")
        match = TIMING.fullmatch(lines[1])
        if match is None:
            raise WorkflowError("Invalid SRT cue time range")
        begin, end = (_milliseconds(x) for x in match.groups())
        phrase = lines[2]
        if not 250 <= end - begin <= MAX_CUE_DURATION_MS:
            raise WorkflowError("Unreadable or out-of-bounds cue duration")
        if not phrase or not phrase.strip() == phrase or len(phrase) > MAX_CUE_CHARS or ">" in phrase:
            raise WorkflowError("Invalid or overlong subtitle line")
        if index == 1 and begin > MAX_FIRST_CUE_DELAY_MS:
            raise WorkflowError("Excessive subtitle introduction delay")
        if begin < previous_end or begin - previous_end > MAX_INTER_CUE_GAP_MS:
            raise WorkflowError("Subtitle cue overlap or implausible gap")
        previous_end = end
        parsed.append((begin, end, phrase))
    return parsed


def _check_authored_scene_anchors(
    cues: list[tuple[int, int, str]],
    authored_rows: list[tuple[str, str, str, str, str, str]],
    *,
    episode_kind: str,
) -> tuple[int, int]:
    """Bound approximate cue/scene textual timing drift, NOT WAV word alignment.

    The accepted screenplay is contiguous across authored scenes. A rewritten
    SRT may preserve every single word in order yet shift the entire first
    scene's words into the next visual, harming educational comprehension.
    Approximate each scene boundary from its word offset within an SRT cue;
    allow generous slack for real speakers' differing pacing. This cannot
    establish what anyone actually said, or when, without trusted listening.
    """
    limit = (MAX_SCENE_BOUNDARY_DRIFT_SHORT_MS
             if episode_kind == "short" else MAX_SCENE_BOUNDARY_DRIFT_LONG_MS)
    if episode_kind not in ("short", "long") or len(authored_rows) < 2:
        raise WorkflowError("Unknown authored visual scene plan")
    boundaries = []
    consumed = 0
    for row in authored_rows[:-1]:
        consumed += len(row[4].split())
        boundaries.append((consumed, _seconds(row[2], row[3]) * 1000))
    count = 0
    max_drift = 0
    pointer = 0
    cue_begin_word = 0
    for boundary_tokens, expected_ms in boundaries:
        while pointer < len(cues):
            start, end, phrase = cues[pointer]
            cue_end_word = cue_begin_word + len(phrase.split())
            if cue_end_word >= boundary_tokens:
                if cue_end_word == cue_begin_word:
                    raise WorkflowError("Empty SRT cue cannot anchor scene")
                relative = (boundary_tokens - cue_begin_word) / (
                    cue_end_word - cue_begin_word
                )
                approx = round(start + relative * (end - start))
                drift = abs(approx - expected_ms)
                if drift > limit:
                    raise WorkflowError(
                        "Candidate SRT words drift beyond authored visual scene"
                    )
                max_drift = max(max_drift, drift)
                count += 1
                break
            pointer += 1
            cue_begin_word = cue_end_word
        else:
            raise WorkflowError("Missing authored scene boundary in captions")
    return count, max_drift


def review_candidate_caption(candidate: CandidateCaption, audio_receipt: dict) -> dict:
    """Check one SRT against original written words and a technical WAV receipt.

    Passing this routine is never proof of real spoken alignment, even when a
    claimant manually changes timestamps or recalculates every SHA.
    """
    if not isinstance(candidate, CandidateCaption):
        raise WorkflowError("Typed subtitle candidate required")
    ep = candidate.episode_id
    if ep not in EPISODES or not isinstance(audio_receipt, dict):
        raise WorkflowError("Unknown episode or missing technical WAV receipt")
    if not isinstance(candidate.srt_sha256, str) or not HEX.fullmatch(candidate.srt_sha256):
        raise WorkflowError("Invalid submitted SRT hash")
    if not isinstance(candidate.wav_sha256, str) or not HEX.fullmatch(candidate.wav_sha256):
        raise WorkflowError("Invalid submitted WAV hash")
    if candidate.origin_claim not in ALLOWED_ORIGINS:
        raise WorkflowError("Only explicitly unverified caption origins accepted")
    planned = {x[2]: x for x in SECTIONS}[ep]
    language, narrator, expected_seconds = planned[1], planned[3], planned[4]
    if (candidate.declared_language != language
            or candidate.declared_narrator_id != narrator
            or audio_receipt.get("episode_id") != ep
            or audio_receipt.get("original_language_declared") != language
            or audio_receipt.get("intended_narrator_id") != narrator
            or audio_receipt.get("clip_sha256") != candidate.wav_sha256
            or audio_receipt.get("technical_wav_screen_passed") is not True):
        raise WorkflowError("SRT episode, lane, narrator or WAV integrity mismatch")
    for false_key in ("audio_content_recognized_as_speech", "spoken_subtitles_word_aligned",
                      "approved_for_audio_mux", "publishing_authorized"):
        if audio_receipt.get(false_key) is not False:
            raise WorkflowError("Untrusted audio receipt claims excessive authority")
    duration = audio_receipt.get("duration_seconds")
    if type(duration) not in (int, float) or not expected_seconds-1.5 <= duration <= expected_seconds+1.5:
        raise WorkflowError("Audio duration not technically matched to this video")
    draft = build_subtitles_from_authored_csv()[ep]
    if (audio_receipt.get("draft_srt_sha256") != draft["srt_sha256"]
            or not draft["timings_are_script_estimates"]
            or draft["actual_voice_alignment_verified"]):
        raise WorkflowError("Audio receipt does not bind the current draft screenplay")
    source_sections = _sections(SOURCE.read_text(encoding="utf-8"))
    original = dict(zip((entry[2] for entry in SECTIONS), source_sections))[ep]
    authored_rows = TIME.findall(original)
    spoken = " ".join(match[4] for match in authored_rows)
    raw, found_sha = _load_plain_file(candidate.srt_path)
    if found_sha != candidate.srt_sha256:
        raise WorkflowError("SRT bytes were changed after candidate submission")
    if found_sha == draft["srt_sha256"]:
        raise WorkflowError("Script-estimated SRT cannot masquerade as corrected speech timing")
    cues = _parse_srt(raw)
    submitted = " ".join(text for _, _, text in cues)
    if submitted.split() != spoken.split():
        raise WorkflowError("Candidate captions omit, duplicate, reorder or alter original speech text")
    anchor_count, max_scene_drift_ms = _check_authored_scene_anchors(
        cues, authored_rows, episode_kind=planned[0]
    )
    max_audio_ms = round(duration * 1000)
    if cues[-1][1] > min(max_audio_ms, expected_seconds * 1000 + 1500):
        raise WorkflowError("Captions run beyond actual technically measured WAV")
    if cues[-1][1] < expected_seconds * 1000 - MAX_END_TRAILING_MS:
        raise WorkflowError("Implausibly early end of a complete screenplay's captions")
    return {
        "status": "UNVERIFIED_SRT_TIMECODE_CANDIDATE_SOURCE_LOCKED",
        "episode_id": ep, "language_declared": language,
        "narrator_plan_id": narrator, "wav_sha256": candidate.wav_sha256,
        "srt_sha256": found_sha, "source_script_sha256": draft["script_sha256"],
        "draft_estimated_srt_sha256": draft["srt_sha256"],
        "cue_count": len(cues), "caption_end_ms": cues[-1][1],
        "wav_duration_ms_technical": max_audio_ms,
        "authored_visual_scene_boundaries_screened": anchor_count,
        "max_claimed_scene_boundary_drift_ms": max_scene_drift_ms,
        "scene_boundary_timing_is_unverified_estimate": True,
        "all_authored_text_preserved_exactly": True,
        "timestamps_structurally_plausible": True,
        "claimed_origin": candidate.origin_claim,
        "actual_spoken_words_recognized": False,
        "true_speech_to_caption_alignment_verified": False,
        "caption_editor_identity_verified": False,
        "independent_language_listening_review_verified": False,
        "licensed_voice_and_asset_rights_verified": False,
        "ready_for_mux": False, "ready_for_upload": False,
        "publishing_authorized": False, "network_calls": 0,
    }


def review_three_caption_candidates(
    takes: Sequence[CompleteNarrationTake],
    captions: Sequence[CandidateCaption],
) -> dict:
    """Recheck all real local WAV technical takes before caption-only intake.

    Neither authenticated human review nor release permission is created by
    this validation. No media or raw scripts are returned in metadata.
    """
    if not isinstance(captions, (tuple, list)) or len(captions) != 3:
        raise WorkflowError("Exactly one corrected-SRT candidate per planned episode required")
    takes_report = review_complete_narration_takes(takes)
    if takes_report.get("publishing_authorized") is not False:
        raise WorkflowError("Complete WAV technical receipt must remain unapproved")
    receipts = {x["episode_id"]: x for x in takes_report["episodes"]}
    seen = set()
    results = []
    for caption in captions:
        if not isinstance(caption, CandidateCaption) or caption.episode_id in seen:
            raise WorkflowError("Duplicate or incorrectly typed corrected caption")
        seen.add(caption.episode_id)
        results.append(review_candidate_caption(caption, receipts.get(caption.episode_id)))
    if seen != set(EPISODES):
        raise WorkflowError("Missing required Hindi/English candidate")
    return {
        "status": "THREE_UNVERIFIED_TIME_CODE_CANDIDATES_NOT_APPROVED",
        "episodes": sorted(results, key=lambda x: x["episode_id"]),
        "caption_files_structurally_screened": 3,
        "genuine_speech_alignment_verified": False,
        "independent_multilingual_review_verified": False,
        "all_voice_rights_authenticated": False,
        "final_audio_mux_authorized": False,
        "youtube_upload_or_publishing_authorized": False,
        "network_calls": 0,
    }
