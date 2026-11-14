"""Offline, no-script CLIVOX beat navigator from exact hashed draft SRT.

This is a human review aid. Matching the authored text and draft subtitle
text does NOT verify audible words, narration quality, rights, or approval.
It never makes network calls, records consent, or publishes a video.
"""
from __future__ import annotations

from html import escape
import re

from scripts.branch3_a5_speech_boundaries import parse_srt_intervals

LOCAL_VIDEO = re.compile(
    r"clivox_original_[a-z0-9_]+/original-review-preview\.mp4\Z"
)


class SceneReviewIndexDenied(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SceneReviewIndexDenied("CLIVOX_A5_SCENE_INDEX_DENIED_" + code)


def normalize(value: str) -> str:
    require(type(value) is str and len(value) < 3000, "TEXT_LIMIT")
    return " ".join(value.split())


def make_scene_review_index(
    episode: dict, srt_text: str, relative_video: str
) -> tuple[str, int]:
    """Build a seekable per-scene transcript index, not an editorial signoff."""
    require(type(episode) is dict and type(episode.get("beats")) is list
            and 1 <= len(episode["beats"]) <= 25, "BEATS")
    require(type(relative_video) is str
            and LOCAL_VIDEO.fullmatch(relative_video) is not None
            and relative_video.startswith(episode.get("id", "") + "/"),
            "LOCAL_MEDIA_ONLY")
    intervals = parse_srt_intervals(srt_text)
    chunks = re.split(r"\n\s*\n", srt_text.strip())
    require(len(chunks) == len(intervals), "CUE_COUNT")
    texts = []
    for chunk in chunks:
        lines = chunk.splitlines()
        require(len(lines) in (3, 4), "CUE_SHAPE")
        text = normalize(" ".join(lines[2:]))
        require(text != "", "EMPTY_CUE")
        texts.append(text)

    beats = episode["beats"]
    used = set()
    rows = []
    for index, beat in enumerate(beats):
        require(type(beat) is dict
                and type(beat.get("start_s")) is int
                and type(beat.get("end_s")) is int
                and 0 <= beat["start_s"] < beat["end_s"] <= 600,
                "BEAT_TIME")
        if index:
            require(beats[index-1]["end_s"] == beat["start_s"],
                    "BEAT_CLOCK_GAP")
        start, end = beat["start_s"], beat["end_s"]
        matching = [
            cue_index for cue_index, (a, b) in enumerate(intervals)
            if a >= start - .003 and b <= end + .003
        ]
        require(matching, "SCENE_WITHOUT_CAPTIONS_" + str(index))
        require(not any(i in used for i in matching), "REUSED_CUE")
        used.update(matching)
        actual_draft = normalize(" ".join(texts[i] for i in matching))
        planned = normalize(beat.get("spoken"))
        require(actual_draft == planned,
                "CAPTIONS_DIFFER_FROM_AUTHORED_SCRIPT_" + str(index))
        label = normalize(beat.get("headline"))
        require(1 <= len(label) <= 120, "HEADLINE")
        start_label = f"{start // 60:02d}:{start % 60:02d}"
        end_label = f"{end // 60:02d}:{end % 60:02d}"
        seek = escape(f"{relative_video}#t={start},{end}", quote=True)
        rows.append(
            '<li class="scene-row">'
            f'<a href="{seek}" aria-label="Open scene {index+1} media segment">'
            f'Scene {index+1:02d} · {start_label}–{end_label} '
            f'· {escape(label, quote=True)}</a>'
            '<p class="scene-script"><strong>Planned narration:</strong> '
            f'{escape(planned, quote=True)}</p>'
            '<p class="scene-draft"><strong>Draft caption text:</strong> '
            f'{escape(actual_draft, quote=True)}</p>'
            '</li>'
        )
    require(len(used) == len(intervals),
            "EXTRA_OR_CROSS_SCENE_CAPTION_CUES")
    html = (
        '<details class="scene-review-index">'
        f'<summary>Review all {len(rows)} scenes and draft captions</summary>'
        '<p>Each local link opens the video near the scene start in browsers '
        'supporting media fragments. Watch and listen to the FULL video too. '
        'Identical draft text is NOT evidence that eSpeak pronounced it '
        'correctly or that word timing is aligned.</p>'
        '<ol>' + "".join(rows) + '</ol>'
        '</details>'
    )
    require("<script" not in html.lower()
            and "https://" not in html.lower()
            and "http://" not in html.lower(), "OFFLINE_ONLY")
    return html, len(rows)
