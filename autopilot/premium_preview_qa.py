"""FlowMinute preview-only media QA; no release authorization or network calls."""
from __future__ import annotations
from dataclasses import dataclass

class PreviewQAError(ValueError):
    pass

@dataclass(frozen=True)
class MediaFacts:
    duration_seconds: float
    width: int
    height: int
    fps: float
    frames: int
    video_codec: str
    audio_codec: str | None
    fully_decoded: bool

@dataclass(frozen=True)
class MotionFacts:
    between_keyframe_mae: tuple[float, ...]
    renderer_kind: str
    source_reference: str


def validate_preview(media: MediaFacts, motion: MotionFacts, *,
                     has_speech: bool = False,
                     reviewed_character_motion: bool = False,
                     independently_approved: bool = False,
                     release_authorized: bool = False) -> dict:
    """Structural evidence is never proof of art, factual safety or publishing."""
    if release_authorized or independently_approved:
        raise PreviewQAError("Preview cannot self-authorize release or independent QA")
    if not media.fully_decoded:
        raise PreviewQAError("Media must decode entirely")
    if media.video_codec != "h264" or media.width < 854 or media.height < 480:
        raise PreviewQAError("Unsupported video codec or unreadable dimensions")
    if not 8 <= media.duration_seconds <= 12 or not 12 <= media.fps <= 60:
        raise PreviewQAError("Ten-second preview duration/fps invalid")
    if abs(media.frames / media.fps - media.duration_seconds) > .12:
        raise PreviewQAError("Frame count disagrees with duration")
    if media.audio_codec not in ("aac", "none"):
        raise PreviewQAError("Unrecognized preview audio")
    if motion.renderer_kind != "real_3d_geometry" or not isinstance(motion.source_reference, str) or not motion.source_reference:
        raise PreviewQAError("3D source provenance and geometry required")
    values = motion.between_keyframe_mae
    if len(values) < 3 or any(type(x) not in (int, float) or not 2 <= x <= 255 for x in values):
        raise PreviewQAError("Keyframe samples show inadequate or invalid visual movement")
    return {
        "technical_preview_valid": True,
        "duration_seconds": media.duration_seconds,
        "motion_samples": len(values),
        "audio_track": "narration_present_unreviewed" if has_speech else (
            "sound_effects_only" if media.audio_codec != "none" else "silent"),
        "character_artistic_qa": "REVIEW_RECORDED_NOT_APPROVED" if reviewed_character_motion else "PENDING",
        "stage": "TECHNICAL_PREVIEW_NOT_RELEASE_READY",
        "full_episode_rendered": False,
        "voice_license_reviewed": False,
        "subtitle_alignment_reviewed": False,
        "fact_claims_independently_verified": False,
        "youtube_upload_id": None,
        "youtube_scheduled": False,
        "release_authorized": False,
    }
