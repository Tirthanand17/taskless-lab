"""B3d4c2c1: exact byte and script-lineage inventory for UNAPPROVED media.

The physical source (MP4, SRT, WAV, thumbnail, all storyboard PNGs) is
hashed from actual ephemeral files, not trusted merely because a render report
claims those hashes. A signed source/script plan and executed demonstration
are re-derived from B3d4a/B3d4c1 trusted inputs. Captions are parsed and
compared to every original spoken text cue. The B3d4b independent FFmpeg
decoder and full-frame/PNG probes remain separate QA responsibilities.

This evidence does NOT prove real source factual truth, editorial originality,
music/voice license, visual semantic accuracy, human full watch/listen or a
right to publish. There is NO uploader, owner approval, permanent store, cloud
secret, model API, live inference or production media release.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import stat
from typing import Mapping

from autopilot.cloud_full_duration_pack import sentence_chunks
from autopilot.computed_demo_storyboards import (
    RECIPES, build_executed_demo, require_exact_demo,
)
from autopilot.script_continuity_gate import DetachedScriptSeal, TrustedScriptCustodian
from autopilot.script_to_preview_bridge import build_signed_preview_plan
from autopilot.signed_narrated_cloud_pack import VOICE_FOR_SLOT, validate_plan

STATUS = "EXACT_TEMP_MEDIA_LINEAGE_AND_CAPTIONS_VERIFIED_UNREVIEWED_NO_PUBLISH"
MAX_MP4_BYTES = 300_000_000
MAX_AUDIO_BYTES = 85_000_000
MAX_IMAGE_BYTES = 18_000_000
MAX_SRT_BYTES = 100_000
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
CUE_TIME = re.compile(
    r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3}) --> "
    r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3})\Z"
)
UNAPPROVED_FLAGS = (
    "human_full_playback_completed",
    "human_voice_quality_review_complete",
    "factual_accuracy_independently_approved",
    "copyright_and_voice_rights_cleared",
    "final_video_publishable",
    "youtube_upload_enabled",
    "youtube_schedule_enabled",
    "release_authorized",
)


class FinalMediaEvidenceError(ValueError):
    """A media file or unverified script lineage was changed, absent or replayed."""


def _compact(obj: object) -> bytes:
    try:
        payload=json.dumps(
            obj,sort_keys=True,ensure_ascii=False,
            separators=(",",":"),allow_nan=False
        ).encode("utf-8")
    except (ValueError,TypeError,OverflowError,RecursionError) as exc:
        raise FinalMediaEvidenceError("Unserializable final media evidence") from exc
    if len(payload)>150_000:
        raise FinalMediaEvidenceError("Unbounded final media packet")
    return payload


def _asset(path: Path, *, max_size: int, kind: str, dimensions=None) -> dict:
    """Bounded stream hash, local regular-file check, and file-signature check.

    The PNG header is only an early guard: independent hosted Pillow full
    decode remains mandatory. MP4 ftyp is not a replacement for FFmpeg full
    decode. No media claim is authorized by its file magic.
    """
    if path.is_symlink() or not path.is_file():
        raise FinalMediaEvidenceError("Missing or symlinked encoded media asset")
    if not stat.S_ISREG(path.stat().st_mode):
        raise FinalMediaEvidenceError("Not a regular media file")
    h=sha256()
    total=0
    prefix=b""
    try:
        with path.open("rb") as fh:
            while True:
                part=fh.read(1024*1024)
                if not part:break
                total+=len(part)
                if total>max_size:
                    raise FinalMediaEvidenceError("Media asset exceeds bounded file budget")
                if len(prefix)<32:
                    prefix+=part[:32-len(prefix)]
                h.update(part)
    except OSError as exc:
        raise FinalMediaEvidenceError("Media contents inaccessible") from exc
    if total<16:
        raise FinalMediaEvidenceError("Empty media artifact")
    if kind=="mp4":
        if total<200_000 or prefix[4:8]!=b"ftyp":
            raise FinalMediaEvidenceError("No plausible full MP4 box header")
    elif kind=="wav":
        if total<3000 or prefix[:4]!=b"RIFF" or prefix[8:12]!=b"WAVE":
            raise FinalMediaEvidenceError("Unusable WAV RIFF header")
    elif kind=="png":
        if prefix[:8]!=b"\x89PNG\r\n\x1a\n" or prefix[12:16]!=b"IHDR":
            raise FinalMediaEvidenceError("PNG header invalid")
        if dimensions is not None and (
            int.from_bytes(prefix[16:20],"big"),
            int.from_bytes(prefix[20:24],"big")
        )!=dimensions:
            raise FinalMediaEvidenceError("Actual PNG dimensions disagree with video slot")
    elif kind=="srt":
        if b"\x00" in prefix:
            raise FinalMediaEvidenceError("Non-text SRT header")
    elif kind=="ffconcat":
        if not prefix.startswith(b"ffconcat version 1.0"):
            raise FinalMediaEvidenceError("Unexpected FFmpeg scene order header")
    else:
        raise FinalMediaEvidenceError("Unapproved extra asset kind")
    return {"file_name":path.name,"sha256":h.hexdigest(),"bytes":total}


def _cue_ms(h: str, m: str, s: str, ms: str) -> int:
    return ((int(h)*60+int(m))*60+int(s))*1000+int(ms)


def verify_caption_text(srt: Path, plan: dict, duration_seconds: float) -> dict:
    if (not isinstance(duration_seconds,(float,int))
            or isinstance(duration_seconds,bool)
            or not 0<duration_seconds<320):
        raise FinalMediaEvidenceError("Invalid rendered video timing")
    raw=srt.read_bytes()
    if len(raw)>MAX_SRT_BYTES or not raw:
        raise FinalMediaEvidenceError("Captions missing or oversized")
    try:
        text=raw.decode("utf-8",errors="strict")
    except UnicodeError as exc:
        raise FinalMediaEvidenceError("SRT cannot be decoded losslessly") from exc
    chunks=[s for s in text.strip().split("\n\n") if s]
    expected=[]
    for scene in plan["scene_plan"]:
        expected.extend(sentence_chunks(scene["raw_narration"]))
    if len(chunks)!=len(expected) or len(chunks)<len(plan["scene_plan"]):
        raise FinalMediaEvidenceError("Caption count does not match anchored narration")
    prior_end=0
    observed=[]
    for i,(block,phrase) in enumerate(zip(chunks,expected),1):
        lines=block.splitlines()
        if len(lines)<3 or lines[0]!=str(i) or not CUE_TIME.fullmatch(lines[1]):
            raise FinalMediaEvidenceError("Out-of-order SRT caption timestamp/index")
        stamp=CUE_TIME.fullmatch(lines[1])
        assert stamp is not None
        a=_cue_ms(*stamp.groups()[:4])
        b=_cue_ms(*stamp.groups()[4:])
        if (a<prior_end or b<=a or b>int(duration_seconds*1000)+50
                or " ".join(lines[2:])!=phrase):
            raise FinalMediaEvidenceError("SRT coverage, order or cue timing altered")
        prior_end=b
        observed.append(phrase)
    return {
        "cue_count":len(expected),
        "srt_exact_spoken_phrase_sequence_sha256":
            sha256(_compact(observed)).hexdigest(),
        "last_cue_end_ms":prior_end,
        "all_spoken_sentences_text_exactly_represented":True,
        "caption_actual_visual_readability_human_reviewed":False,
        "true_word_level_alignment_completed":False,
    }


def create_unapproved_final_media_inventory(
    *,
    plan: dict, proposal: dict, slot: dict, observations: dict,
    seal: DetachedScriptSeal,
    external_script_anchor_sha256: str,
    script_registry: Mapping[str,TrustedScriptCustodian],
    excluded_creator_and_publisher_ids: frozenset[str],
    report: dict, episode_folder: Path, demo_recipe: str,
    now: datetime | None = None,
) -> dict:
    """Independently rebuild final test lineage and rehash ALL produced files.

    Not a release gate: all output editorial and publish flags remain false.
    External signer registry and script anchor are required but CI keys are
    disposable and do not constitute human editorial approval.
    """
    if not isinstance(report,dict) or not isinstance(plan,dict):
        raise FinalMediaEvidenceError("No media report or source-bound plan")
    try:
        rebuilt=build_signed_preview_plan(
            proposal,slot,observations,
            seal=seal,anchor_manifest_sha256=external_script_anchor_sha256,
            registry=script_registry,
            excluded_creator_and_publisher_ids=excluded_creator_and_publisher_ids,
            now=now,
        )
        if _compact(rebuilt)!=_compact(plan):
            raise FinalMediaEvidenceError("Plan was not regenerated from signed source")
        prepared=validate_plan(plan)
        demo=build_executed_demo(plan,proposal,demo_recipe)
        require_exact_demo(plan,proposal,demo_recipe,demo)
    except FinalMediaEvidenceError:
        raise
    except (ValueError,TypeError,KeyError,AssertionError) as exc:
        raise FinalMediaEvidenceError("Signed script or executed demo lineage invalid") from exc
    if (
        report.get("episode")!=plan["episode_id"]
        or report.get("kind")!=plan["format"]
        or report.get("voice")!=VOICE_FOR_SLOT[plan["release_slot"]]
        or report.get("scene_count")!=plan["scene_count"]
        or report.get("original_scene_ids")!=list(prepared.scene_ids)
        or report.get("script_manifest_sha256")!=plan["script_manifest_sha256"]
        or report.get("full_original_narration_sha256")!=plan["full_spoken_narration_sha256"]
        or report.get("computed_example_evidence_sha256")!=demo["evidence_packet_sha256"]
        or report.get("computed_test_example_executed") is not True
        or report.get("human_approved_demo_visual_semantics") is not False
        or report.get("synthetic_data_not_external_factual_support") is not True
        or report.get("real_provider_generated_script") is not False
        or report.get("full_actual_mp4_h264_aac_decode_passed") is not True
        or report.get("actual_kokoro_speech_generated") is not True
        or report.get("srt_cues_timed_from_generated_pcm") is not True
        or any(report.get(k) is not False for k in UNAPPROVED_FLAGS)
    ):
        raise FinalMediaEvidenceError("Media report has inconsistent lineage or forged approvals")
    folder=Path(episode_folder)
    if folder.is_symlink() or not folder.is_dir() or folder.name!=plan["episode_id"]:
        raise FinalMediaEvidenceError("Wrong or symlinked episode output directory")
    names={p.name for p in folder.iterdir()}
    scenes=tuple(f"scene_{i+1:02d}.png" for i in range(plan["scene_count"]))
    expected=set(scenes) | {
        "UNAPPROVED_FULL_EDUCATION_TEST.mp4",
        "UNAPPROVED_THUMBNAIL_TEST.png",
        "scene_captions.srt",
        "original_voice.wav",
        "scene_order.ffconcat",
        "moving_progress.png",
    }
    if names!=expected:
        raise FinalMediaEvidenceError("Unexpected, missing, replaced or covert media asset")
    width,height=(1080,1920) if plan["format"]=="short" else (1920,1080)
    records=[
        _asset(folder/"UNAPPROVED_FULL_EDUCATION_TEST.mp4",
               max_size=MAX_MP4_BYTES,kind="mp4"),
        _asset(folder/"scene_captions.srt",
               max_size=MAX_SRT_BYTES,kind="srt"),
        _asset(folder/"original_voice.wav",
               max_size=MAX_AUDIO_BYTES,kind="wav"),
        _asset(folder/"UNAPPROVED_THUMBNAIL_TEST.png",
               max_size=MAX_IMAGE_BYTES,kind="png",dimensions=(1280,720)),
    ]
    for scene in scenes:
        records.append(_asset(folder/scene,max_size=MAX_IMAGE_BYTES,
                              kind="png",dimensions=(width,height)))
    records.extend([
        _asset(folder/"moving_progress.png",max_size=MAX_IMAGE_BYTES,
               kind="png",dimensions=(82,14)),
        _asset(folder/"scene_order.ffconcat",max_size=MAX_SRT_BYTES,kind="ffconcat"),
    ])
    index={r["file_name"]:r for r in records}
    # Validate that each reported byte digest really matches actual file data.
    mp4=index["UNAPPROVED_FULL_EDUCATION_TEST.mp4"]
    thumb=index["UNAPPROVED_THUMBNAIL_TEST.png"]
    if (
        mp4["sha256"]!=report.get("video_sha256")
        or mp4["bytes"]!=report.get("mp4_bytes")
        or thumb["sha256"]!=report.get("original_unreviewed_thumbnail_sha256")
        or len({index[x]["sha256"] for x in scenes})!=len(scenes)
    ):
        raise FinalMediaEvidenceError("Actual bytes differ from independent render report")
    captions=verify_caption_text(folder/"scene_captions.srt",plan,report["seconds"])
    if captions["cue_count"]!=report.get("narration_cues"):
        raise FinalMediaEvidenceError("Actual caption count does not match decoded report")
    immutable={
        "schema_version":1,
        "status":STATUS,
        "episode_id":plan["episode_id"],
        "format":plan["format"],
        "release_slot":plan["release_slot"],
        "signed_original_script_manifest_sha256":plan["script_manifest_sha256"],
        "signed_full_spoken_narration_sha256":plan["full_spoken_narration_sha256"],
        "computed_demo_recipe":demo_recipe,
        "computed_demo_evidence_sha256":demo["evidence_packet_sha256"],
        "source_observations_sha256":sha256(_compact(observations)).hexdigest(),
        "executed_example_uses_invented_csv_only":True,
        "voice":report["voice"],
        "duration_seconds":report["seconds"],
        "asset_sha256_and_exact_sizes":records,
        "asset_count":len(records),
        "all_asset_bytes_rehashed_from_actual_ephemeral_files":True,
        "srt_text_and_cue_timing":captions,
        "media_codec_and_pixels_technically_independently_probed_upstream":True,
        "full_human_watch_listen_completed":False,
        "independent_real_world_reviewer_approved":False,
        "all_title_thumbnail_caption_visual_claims_verified":False,
        "final_visual_semantic_truth_verified":False,
        "real_source_claim_review_completed":False,
        "originality_and_nonrepetition_semantically_approved":False,
        "sound_voice_music_license_rights_checked":False,
        "synthetic_media_disclosure_decision_reviewed":False,
        "creator_and_copyright_owner_permission_confirmed":False,
        "real_provider_generated_script":False,
        "private_immutable_content_ledger_connected":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
    }
    return {
        **immutable,
        "unapproved_inventory_sha256":sha256(_compact(immutable)).hexdigest(),
    }


def require_exact_unapproved_inventory(packet: dict, **kwargs) -> None:
    expected=create_unapproved_final_media_inventory(**kwargs)
    if not isinstance(packet,dict) or _compact(packet)!=_compact(expected):
        raise FinalMediaEvidenceError("Replayed or mutated final bytes/source inventory")


def inspect_three_different_unapproved_media(inventories: list[dict]) -> dict:
    """Three different hashes != three human-cleared original videos."""
    if not isinstance(inventories,list) or len(inventories)!=3:
        raise FinalMediaEvidenceError("Require exactly 2 Shorts and one long")
    slots={}
    days=set()
    for item in inventories:
        if not isinstance(item,dict) or item.get("status")!=STATUS:
            raise FinalMediaEvidenceError("Not an unapproved byte-level inventory")
        for k in (
            "full_human_watch_listen_completed",
            "independent_real_world_reviewer_approved",
            "all_title_thumbnail_caption_visual_claims_verified",
            "final_visual_semantic_truth_verified",
            "real_source_claim_review_completed",
            "originality_and_nonrepetition_semantically_approved",
            "sound_voice_music_license_rights_checked",
            "synthetic_media_disclosure_decision_reviewed",
            "creator_and_copyright_owner_permission_confirmed",
            "real_provider_generated_script",
            "private_immutable_content_ledger_connected",
            "youtube_upload_enabled",
            "youtube_schedule_enabled",
            "release_authorized",
        ):
            if item.get(k) is not False:
                raise FinalMediaEvidenceError("Faked final editorial approval")
        slot=item.get("release_slot")
        eid=item.get("episode_id")
        if (
            slot not in VOICE_FOR_SLOT
            or not isinstance(eid,str)
            or not re.fullmatch(r"fm_[0-9]{8}_(?:short_am|short_pm|long)",eid)
            or not eid.endswith("_"+slot)
            or slot in slots
            or item.get("format")!=("long" if slot=="long" else "short")
        ):
            raise FinalMediaEvidenceError("Replayed or mismatched slot")
        slots[slot]=item
        days.add(eid[3:11])
    if len(days)!=1 or len(slots)!=3:
        raise FinalMediaEvidenceError("Three slots must share one planned date")
    for field in (
        "signed_original_script_manifest_sha256",
        "signed_full_spoken_narration_sha256",
        "computed_demo_evidence_sha256",
        "unapproved_inventory_sha256",
    ):
        if len({r.get(field) for r in inventories})!=3 or any(
            not isinstance(r.get(field),str) or not HEX64.fullmatch(r[field])
            for r in inventories
        ):
            raise FinalMediaEvidenceError("Same narration/demo or duplicated inventory")
    mp4s=[]
    thumbs=[]
    for item in inventories:
        rows=item.get("asset_sha256_and_exact_sizes")
        if not isinstance(rows,list):
            raise FinalMediaEvidenceError("Missing actual asset manifest")
        index={r.get("file_name"):r.get("sha256") for r in rows if isinstance(r,dict)}
        mp4s.append(index.get("UNAPPROVED_FULL_EDUCATION_TEST.mp4"))
        thumbs.append(index.get("UNAPPROVED_THUMBNAIL_TEST.png"))
    if any(not isinstance(x,str) or not HEX64.fullmatch(x) for x in mp4s+thumbs):
        raise FinalMediaEvidenceError("Unverifiable MP4 or thumbnail digest")
    if len(set(mp4s))!=3 or len(set(thumbs))!=3:
        raise FinalMediaEvidenceError("Same output MP4 or thumbnail reused for different slots")
    return {
        "status":"THREE_BYTE_DISTINCT_UNAPPROVED_MEDIA_INVENTORIES_ONLY",
        "episode_ids":sorted(x["episode_id"] for x in inventories),
        "three_exact_technical_video_and_thumbnail_hashes_differ":True,
        "semantic_originality_approved":False,
        "human_fact_and_rights_reviews_complete":False,
        "external_provider_script_generation_used":False,
        "private_durable_media_store_connected":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
    }
