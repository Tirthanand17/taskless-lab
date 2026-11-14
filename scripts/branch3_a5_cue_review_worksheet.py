"""CLIVOX A5: exact-file, offline per-caption HUMAN CORRECTION worksheet.

Produces a local CSV and no-script HTML seek links for every draft subtitle.
This is an editorial issue-reporting aid, NEVER a rights check, owner review
attestation, signature, release permission, or YouTube publishing authority.
The complete unsigned A6 handoff is reverified by the caller gallery before
this function is used. No network and no file downloads are performed.
"""
from __future__ import annotations

import csv
from html import escape
from io import StringIO
from pathlib import Path
import re

from scripts.branch3_a5_speech_boundaries import parse_srt_intervals
from scripts.branch3_original_arcade_qa import cue_samples_all_cues
from scripts.branch3_a6_original_handoff import CHANNEL, ROOT, sha, digest

WORKSHEET = "narration-caption-corrections-UNREVIEWED.csv"
VIDEO = "original-review-preview.mp4"
SRT = "narration-timing-draft.srt"
AUDIO = "original-tts-and-procedural-ambience.wav"

FIELDS = (
    "purpose", "episode_id", "exact_video_sha256", "exact_audio_sha256",
    "exact_srt_sha256", "cue_number", "scene_number", "cue_start",
    "cue_end", "draft_caption", "actual_words_and_pronunciation",
    "subtitle_timing", "caption_visual_readability",
    "correction_required", "suggested_replacement_caption",
    "reviewer_issue_notes",
)


class CueWorksheetBlocked(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise CueWorksheetBlocked("CLIVOX_A5_CUE_WORKSHEET_DENIED_" + code)


def normalized(value: str) -> str:
    require(type(value) is str and 0 < len(value) <= 3000, "TEXT")
    return " ".join(value.split())


def safe_csv_cell(value: object) -> str:
    """Prevent spreadsheet CSV formula execution in any source-derived cell."""
    value = str(value)
    # Leading whitespace and control characters can precede a formula.
    if value.lstrip().startswith(("=", "+", "-", "@")) or (
        value and value[0] in ("\t", "\r", "\n")
    ):
        return "'" + value
    return value


def stamp(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, sub = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{sub:03d}"


def make_cue_review_worksheet(
    folder: Path, episode: dict, srt_text: str, packet: dict
) -> tuple[str, int]:
    """Write a non-authorizing, exact-file-bound CSV and return HTML links."""
    require(type(episode) is dict and type(packet) is dict
            and isinstance(folder, Path) and folder.is_absolute()
            and folder.is_dir() and not folder.is_symlink()
            and folder != ROOT and ROOT not in folder.parents,
            "LOCATION")
    episode_id = episode.get("id")
    require(type(episode_id) is str and
            re.fullmatch(r"clivox_original_[a-z0-9_]{1,80}", episode_id)
            is not None and folder.name == episode_id,
            "EPISODE_ID")
    require(packet.get("channel_id") == CHANNEL
            and packet.get("episode_id") == episode_id
            and packet.get("youtube_upload_authorized") is False
            and packet.get("youtube_schedule_authorized") is False
            and packet.get("youtube_publish_authorized") is False
            and packet.get("owner_detached_signature_present") is False
            and packet.get("exact_video_human_review_confirmed") is False
            and packet.get("packet_sha256") == digest({
                k: v for k, v in packet.items() if k != "packet_sha256"
            }), "UNSIGNED_HANDOFF")
    for file_name, hash_key in (
        (VIDEO, "exact_video_sha256"),
        (AUDIO, "exact_audio_sha256"),
        (SRT, "exact_captions_sha256"),
    ):
        f = folder / file_name
        require(f.is_file() and not f.is_symlink()
                and sha(f) == packet.get(hash_key),
                "EXACT_MEDIA_CHANGED_" + file_name)

    target = folder / WORKSHEET
    require(not target.exists() and not target.is_symlink(),
            "NO_OVERWRITE")
    require((folder / SRT).read_text("utf-8") == srt_text,
            "SRT_TEXT_CHANGED")
    intervals = parse_srt_intervals(srt_text)
    cues = cue_samples_all_cues(
        srt_text, episode["beats"], episode["duration_seconds"]
    )
    require(len(intervals) == len(cues) and 1 <= len(cues) <= 70,
            "CUE_MAPPING")
    parts = re.split(r"\n\s*\n", srt_text.strip())
    require(len(parts) == len(cues), "SRT_PARTS")
    scene_words: dict[int, list[str]] = {}
    data_rows: list[list[str]] = []
    html_rows: list[str] = []
    for index, ((start, end), cue, chunk) in enumerate(
        zip(intervals, cues, parts, strict=True)
    ):
        lines = chunk.splitlines()
        require(len(lines) in (3, 4) and lines[0] == str(index + 1),
                "CUE_SHAPE")
        text = normalized(" ".join(lines[2:]))
        scene_index = cue["beat_index"]
        require(type(scene_index) is int
                and 0 <= scene_index < len(episode["beats"]),
                "SCENE_MAP")
        scene_words.setdefault(scene_index, []).append(text)
        data_rows.append([
            "EDITORIAL_CORRECTION_ONLY_NOT_APPROVAL",
            episode_id, packet["exact_video_sha256"],
            packet["exact_audio_sha256"],
            packet["exact_captions_sha256"],
            str(index + 1), str(scene_index + 1),
            stamp(start), stamp(end), text,
            "NOT_REVIEWED", "NOT_REVIEWED", "NOT_REVIEWED",
            "NOT_REVIEWED", "", "",
        ])
        segment = (
            f"{episode_id}/{VIDEO}#t={start:.3f},{end:.3f}"
        )
        html_rows.append(
            '<li class="cue-row"><a href="' + escape(segment, quote=True) +
            f'">Cue {index + 1:02d} · scene {scene_index + 1:02d}'
            f' · {escape(stamp(start))}–{escape(stamp(end))}</a>'
            '<p>Draft: ' + escape(text, quote=True) + '</p></li>'
        )
    require(len(scene_words) == len(episode["beats"]),
            "ALL_SCENES_COVERED")
    for index, beat in enumerate(episode["beats"]):
        require(normalized(" ".join(scene_words[index])) ==
                normalized(beat["spoken"]),
                "SCRIPT_SRT_DIFFER_" + str(index))

    buf = StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(FIELDS)
    for fields in data_rows:
        writer.writerow([safe_csv_cell(x) for x in fields])
    body = buf.getvalue()
    require(100 < len(body.encode("utf-8")) < 150_000, "CSV_BOUNDS")
    target.write_text(body, encoding="utf-8", newline="")
    require(target.is_file() and not target.is_symlink(), "CSV_WRITTEN")
    section = (
        '<details class="cue-review-index">'
        f'<summary>Listen to and correct all {len(cues)} subtitle cues</summary>'
        '<p>These time links are local video seek aids, not proof of speech'
        ' accuracy. Listen to each cue and the entire video. Record'
        ' proposed fixes in the CSV, and rerender before any approval.'
        ' A completed CSV is NOT a signed release.</p>'
        '<ol class="cue-review-items">' + "".join(html_rows) + '</ol>'
        '</details>'
    )
    require("<script" not in section.lower()
            and "http://" not in section.lower()
            and "https://" not in section.lower(), "LOCAL_HTML_ONLY")
    return section, len(cues)
