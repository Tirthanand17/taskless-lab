"""B1q8: exact, inert source-only repair for 11 confirmed scheduled Shorts.

The November 5–11 owner read-only inventory found 19 still-private
scheduled videos and two already public on November 5 (89 total uploads).
Eleven of the thirteen still-scheduled SHORT master checksums match their
historical YouTube upload receipts AND their render scripts contain the
SAME unmotivated moving circular arc. This code does NOT open, overwrite,
upload, reschedule, unpublish, delete, or re-render those videos.

The original source scripts currently live in owner-controlled production
folders, NOT in public GitHub. Repair should only be applied to privately
staged, SHA-matched source with explicit full-watch/rights approval and a
later exact new video release receipt, never to the old URL's video bytes.
"""
from __future__ import annotations

from hashlib import sha256
import re

STATUS = "B1Q8_CONFIRMED_GENERIC_CENTRAL_ARC_REMOVAL_UNRELEASED"
TARGET = (
    "    phase=.5+.5*math.sin(t*7)\n"
    "    d.arc((242,573,480,801),int(15+130*phase),"
    "int(155+130*phase),fill=c,width=5)\n"
)
REPLACEMENT = (
    "    # B1q8: suppress repeated center spinner. Original scene image,\n"
    "    # one-shot camera movement and finite lower progress remain intact.\n"
)
SCHEDULED_ARC_SLOTS_IST = (
    ("2026-11-05", "20:30"),
    ("2026-11-06", "20:30"),
    ("2026-11-07", "20:30"),
    ("2026-11-08", "11:00"),
    ("2026-11-08", "20:30"),
    ("2026-11-09", "11:00"),
    ("2026-11-09", "20:30"),
    ("2026-11-10", "11:00"),
    ("2026-11-10", "20:30"),
    ("2026-11-11", "11:00"),
    ("2026-11-11", "20:30"),
)
OTHER_RENDERER_SLOTS_IST = (
    ("2026-11-06", "11:00"),
    ("2026-11-07", "11:00"),
)
EXPECTED_CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
_HEX = re.compile(r"^[0-9a-f]{64}$")


class SourceRepairRejected(ValueError):
    """Original content or media checksum differs from scheduled receipt."""


def _newline_source(source: str) -> tuple[str, str]:
    if type(source) is not str or len(source) > 100_000:
        raise SourceRepairRejected("Unexpected source length or type")
    if "\r" in source.replace("\r\n", ""):
        raise SourceRepairRejected("Mixed/untrusted source newline style")
    newline = "\r\n" if "\r\n" in source else "\n"
    return source.replace("\r\n", "\n"), newline


def remove_verified_central_arc(source: str) -> tuple[str, dict]:
    """Return PATCHED IN-MEMORY SOURCE, not a file or production mutation.

    Require the exact rotating arc. All original images/voice/captions/SFX
    are unchanged and their previous checksums must be re-established by
    separate full cloud media QA after any later approved replacement.
    """
    normalized, newline = _newline_source(source)
    if (
        normalized.count(TARGET) != 1
        or normalized.count("def render_scene(") != 1
        or normalized.count("m.draw_core=render_scene") != 1
        or normalized.count("d.arc(") != 1
        or normalized.count(
            "    d.line((53,1216,53+int(614*min(1,t/TOTAL)),1216),fill=c,width=8)"
        ) != 1
    ):
        raise SourceRepairRejected("Non-exact old circular animation; no patch")
    out = normalized.replace(TARGET, REPLACEMENT)
    if (
        "    phase=.5+.5*math.sin(t*7)\n" in out
        or "d.arc(" in out
        or TARGET in out
    ):
        raise SourceRepairRejected("Source repair was incomplete")
    if out.replace(REPLACEMENT, TARGET) != normalized:
        raise SourceRepairRejected("Unexpected additional source modification")
    before_sha = sha256(source.encode("utf-8")).hexdigest()
    output = out.replace("\n", newline)
    return output, {
        "status": STATUS,
        "source_sha256_before": before_sha,
        "patched_source_sha256": sha256(output.encode("utf-8")).hexdigest(),
        "replaced_exactly_one_repeating_center_arc": True,
        "original_scene_images_preserved": True,
        "one_shot_camera_and_linear_progress_preserved": True,
        "exact_narration_or_captions_modified": False,
        "original_youtube_upload_modified": False,
        "youtube_video_edited_or_rescheduled": False,
        "new_video_uploaded": False,
        "new_video_owner_approved": False,
    }


def verify_original_master_against_receipt(
    master_bytes: bytes, render_qa: dict, youtube_receipt: dict
) -> dict:
    """Prove WHICH previous scheduled master is at issue, with no IDs output."""
    if (
        type(master_bytes) is not bytes
        or not master_bytes or len(master_bytes) > 600_000_000
        or type(render_qa) is not dict
        or type(youtube_receipt) is not dict
    ):
        raise SourceRepairRejected("Original master or evidence unavailable")
    actual = sha256(master_bytes).hexdigest()
    stored = render_qa.get("sha256")
    receipt = youtube_receipt.get("video_sha256")
    if (
        type(stored) is not str or not _HEX.fullmatch(stored)
        or type(receipt) is not str or not _HEX.fullmatch(receipt)
        or stored != actual or receipt != actual
        or youtube_receipt.get("channel_id") != EXPECTED_CHANNEL
        or render_qa.get("full_media_decode_passed") is not True
    ):
        raise SourceRepairRejected("Original master not the uploaded-SHA receipt")
    return {
        "status": "EXACT_ORIGINAL_UPLOADED_MEDIA_SHA_CONFIRMED",
        "original_mp4_sha256": actual,
        "local_original_master_matches_recorded_youtube_receipt": True,
        "new_replacement_media_prepared": False,
        "new_replacement_owner_approved": False,
        "original_youtube_video_changed": False,
    }


def safe_slot_counts() -> dict:
    """Historical time-bounded owner observation, NOT an API or current claim."""
    assert len(SCHEDULED_ARC_SLOTS_IST) == 11
    assert len(OTHER_RENDERER_SLOTS_IST) == 2
    assert set(SCHEDULED_ARC_SLOTS_IST).isdisjoint(OTHER_RENDERER_SLOTS_IST)
    return {
        "as_of_date_ist": "2026-11-05",
        "provenance": "OWNER_LIVE_READONLY_GOOGLE_API_PLUS_EXACT_LOCAL_SHA_RECEIPT",
        "owner_uploads_scanned_at_observation": 89,
        "expected_release_slots_nov05_to_nov11": 21,
        "already_published_nov05_at_observation": 2,
        "remaining_private_scheduled_at_observation": 19,
        "remaining_private_shorts_at_observation": 13,
        "exact_source_arc_and_master_receipt_matched": 11,
        "other_visual_sources_need_separate_review": 2,
        "automatic_new_upload_or_old_scheduled_delete": False,
        "live_automatic_authorized_youtube_write": False,
    }
