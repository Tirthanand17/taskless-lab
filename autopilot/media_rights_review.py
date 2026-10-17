"""Phase 3B: independent *technical* media and rights-evidence preflight.

No backend or provider connections. Inspects actual local media bytes, checks
their SHA-256/timing against Phase 3 draft contracts, and checks bounded local
license *documents*. The legal meaning of those documents, whether text was
spoken accurately, and commercial permissions CANNOT be established by these
checks. Even a complete packet is only ready for independent human review.
NEVER publishes, approves a release, or modifies media or any OAuth token.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Sequence

from .agent_org import WorkflowError
from .phase2_pipeline import digest, CreativeScript, HookVariants, LanguageReview, LocalizedDraft
from .phase3_production import (
    Storyboard, VoiceDirection, NarrationAssetRecord, SubtitleTimeline, RenderRecipe
)
from .render_inspection import inspect_media, MediaEvidence
from .narration_inspection import inspect_narration, AudioEvidence

MAX_LICENSE_BYTES = 2_000_000

@dataclass(frozen=True)
class RightsDeclaration:
    asset_id: str
    kind: str
    source_description: str
    license_document_path: str
    license_document_sha256: str
    commercial_use_claimed: bool
    adaptation_allowed_claimed: bool
    attribution_prepared: bool
    expires_at_utc: str | None = None

@dataclass(frozen=True)
class EvidencePacket:
    status: str
    video: MediaEvidence
    narration: AudioEvidence
    checked_asset_ids: tuple[str, ...]
    problems: tuple[str, ...]
    media_hash_verified: bool
    narration_hash_verified: bool
    rights_documents_hash_verified: bool
    voice_rights_record_matched: bool
    production_claims_authenticated: bool = False
    human_qa_completed: bool = False
    license_legality_verified: bool = False
    publishing_authorized: bool = False
    cloud_deployed: bool = False


def _sha256_file(path: Path, ceiling: int) -> str | None:
    """Reject links, empty/oversized files and vanished files; never expose contents."""
    try:
        if path.is_symlink() or not path.is_file():
            return None
        size = path.stat().st_size
        if not 0 < size <= ceiling:
            return None
        h = sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024*1024), b""):
                h.update(block)
        return h.hexdigest()
    except (OSError, ValueError):
        return None


def _license_evidence_check(record: RightsDeclaration, now: datetime) -> tuple[bool, str]:
    if (not isinstance(record.asset_id,str) or not record.asset_id.startswith("asset_")
            or len(record.asset_id)>60 or not record.asset_id.removeprefix("asset_").replace("_","").isalnum()):
        return False,"INVALID_ASSET_ID"
    if record.kind not in ("voice","music","screen_capture","video","graphic","font","animation"):
        return False,"INVALID_ASSET_TYPE"
    if not (isinstance(record.source_description,str) and
            20<=len(record.source_description.strip())<=300):
        return False,"ASSET_ORIGIN_NOT_DESCRIBED"
    if record.commercial_use_claimed is not True or record.adaptation_allowed_claimed is not True:
        return False,"NO_DECLARED_COMMERCIAL_ADAPTATION_RIGHTS"
    if record.attribution_prepared is not True:
        return False,"ATTRIBUTION_NOT_PREPARED"
    if record.expires_at_utc is not None:
        try:
            expiry=datetime.fromisoformat(record.expires_at_utc.replace("Z","+00:00"))
            if expiry.tzinfo is None or expiry.astimezone(timezone.utc)<=now.astimezone(timezone.utc):
                return False,"EXPIRED_OR_UNVERIFIED_LICENSE_DATE"
        except (TypeError,ValueError,OverflowError):
            return False,"EXPIRED_OR_UNVERIFIED_LICENSE_DATE"
    if (not isinstance(record.license_document_sha256,str)
            or len(record.license_document_sha256)!=64
            or any(c not in "0123456789abcdef" for c in record.license_document_sha256)):
        return False,"INVALID_LICENSE_EVIDENCE_HASH"
    if not isinstance(record.license_document_path,str):
        return False,"INVALID_LICENSE_EVIDENCE_FILE"
    p=Path(record.license_document_path)
    if _sha256_file(p,MAX_LICENSE_BYTES)!=record.license_document_sha256:
        return False,"LICENSE_EVIDENCE_FILE_MISSING_OR_CHANGED"
    return True,"LICENSE_DOCUMENT_HASH_PRESENT_NOT_LEGALLY_VERIFIED"


def inspect_release_materials(
    *, video_path: str | Path, narration_path: str | Path,
    script: CreativeScript, hooks: HookVariants, language_review: LanguageReview,
    localized: LocalizedDraft, expected_kind: str, expected_language: str,
    storyboard: Storyboard, voice: VoiceDirection,
    narration: NarrationAssetRecord, subtitles: SubtitleTimeline,
    recipe: RenderRecipe, rights: Sequence[RightsDeclaration],
    now: datetime | None = None
) -> EvidencePacket:
    """Return a bounded review packet from file bytes; no stage or video approval.

    All planned artifacts are digests of the Phase 3 draft, NOT trusted media
    evidence. Caller must later bind this packet to an authenticated human or
    independent reviewer and use a separate publisher-release approval policy.
    """
    current=now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise WorkflowError("Review clock must be timezone aware")
    empty_video=MediaEvidence("NOT_INSPECTED",None,None,None,None,None,False,())
    empty_audio=AudioEvidence("NOT_INSPECTED",None,None,None,None,None,())
    problems=[]
    # Bound all cross-artifact claims before using the files.
    try:
        if any(x.episode_id!=recipe.episode_id for x in (storyboard,voice,narration,subtitles)):
            raise WorkflowError("Different episodes in production packet")
        if (recipe.storyboard_digest!=digest(storyboard)
                or recipe.narration_digest!=digest(narration)
                or recipe.subtitle_digest!=digest(subtitles)):
            raise WorkflowError("Production artifacts diverge from recipe")
        if narration.voice_plan_digest!=digest(voice):
            raise WorkflowError("Narration no longer matches voice plan")
        if subtitles.narration_digest!=digest(narration) or subtitles.language!=voice.language:
            raise WorkflowError("Subtitles do not match narration/language")
        if expected_kind not in ("short","long") or expected_language not in ("en","hi"):
            raise WorkflowError("Unapproved episode kind or language")
        if (storyboard.kind!=expected_kind or storyboard.language!=expected_language
                or voice.language!=expected_language or recipe.selected_language!=expected_language):
            raise WorkflowError("Mismatched episode kind or language")
        if (script.episode_id!=recipe.episode_id or hooks.episode_id!=recipe.episode_id
                or language_review.episode_id!=recipe.episode_id or localized.episode_id!=recipe.episode_id):
            raise WorkflowError("Mismatched Phase2 episode")
        storyboard.validate(script,hooks,kind=expected_kind,language=expected_language)
        voice.validate(language_review,localized)
        narration.validate(voice,storyboard)
        subtitles.validate(narration,localized)
        recipe.validate(storyboard,narration,subtitles)
    except (WorkflowError,ValueError,TypeError,AttributeError):
        problems.append("STALE_OR_INVALID_PRODUCTION_PLAN")
    if problems:
        return EvidencePacket("BLOCKED_TECHNICAL_PREFLIGHT",empty_video,empty_audio,(),tuple(problems),False,False,False,False)

    duration_ms=storyboard.scenes[-1].end_ms
    v=inspect_media(video_path,expected_width=recipe.target_width,
                    expected_height=recipe.target_height,
                    min_duration_s=max(0.1,duration_ms/1000-1.5),
                    max_duration_s=duration_ms/1000+1.5)
    a=inspect_narration(narration_path,expected_duration_s=narration.duration_ms/1000)
    if v.status!="PASS_TECHNICAL_ONLY":
        problems.append("VIDEO_TECHNICAL_CHECK_FAILED")
    if a.status!="PASS_AUDIO_TECHNICAL_ONLY":
        problems.append("AUDIO_TECHNICAL_CHECK_FAILED")
    if v.video_sha256 is None:
        problems.append("VIDEO_HASH_UNAVAILABLE")
    audio_hash_good=(a.sha256_hex is not None and a.sha256_hex==narration.audio_sha256)
    if not audio_hash_good:
        problems.append("NARRATION_FILE_HASH_MISMATCH")
    # Video output hash is available only at inspection, NOT in the draft recipe.
    video_hash_good=(v.video_sha256 is not None and v.status=="PASS_TECHNICAL_ONLY")
    if v.duration_seconds is not None and a.duration_seconds is not None:
        if abs(v.duration_seconds-a.duration_seconds)>1.5:
            problems.append("VIDEO_AUDIO_DURATION_DIFFERENCE")

    declared={}
    if not 1<=len(rights)<=50:
        problems.append("INVALID_RIGHTS_MANIFEST_SIZE")
    else:
        for record in rights:
            if not isinstance(record,RightsDeclaration) or record.asset_id in declared:
                problems.append("DUPLICATE_OR_INVALID_RIGHTS_DECLARATION")
                continue
            declared[record.asset_id]=record
    required_ids={x for scene in storyboard.scenes for x in scene.assets}
    # An explicit narrator rights declaration and every referenced scene asset
    # are mandatory. No automatic inference of music/graphics from a video.
    voices=[x for x in declared.values() if x.kind=="voice"]
    if len(voices)!=1:
        problems.append("VOICE_RIGHTS_DECLARATION_MISSING_OR_AMBIGUOUS")
    missing=required_ids-set(declared)
    if missing:
        problems.append("STORYBOARD_ASSET_WITHOUT_RIGHTS_DECLARATION")
    voice_rights_match=(len(voices)==1 and
                         voices[0].license_document_sha256==voice.rights_reference)
    if not voice_rights_match:
        problems.append("VOICE_RIGHTS_REFERENCE_MISMATCH")
    rights_valid=True
    for item in declared.values():
        checked,category=_license_evidence_check(item,current)
        if not checked:
            rights_valid=False
            problems.append(category)
    if not declared:
        rights_valid=False
    problems=tuple(sorted(set(problems)))
    return EvidencePacket(
        "INSPECTED_AWAITING_INDEPENDENT_REVIEW" if not problems else "BLOCKED_TECHNICAL_PREFLIGHT",
        v,a,tuple(sorted(declared)),problems,video_hash_good,audio_hash_good,
        rights_valid,voice_rights_match
    )
