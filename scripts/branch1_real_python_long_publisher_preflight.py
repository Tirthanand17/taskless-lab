"""Fail-closed source-only publisher metadata for one hash-locked Python tutorial.

Confirms exact source-artifact release fields are structurally compatible with
the EXISTING publisher. Neither this test nor its owner chat approval substitutes
for the required detached Ed25519 signature, complete rights/facts/caption
attestations, live YouTube OAuth, schedule inventory or an actual upload.
"""
from __future__ import annotations
import json
from pathlib import Path

from scripts.validate_release import validate as validate_editorial_release

ROOT=Path(__file__).resolve().parents[1]
META=ROOT/"content"/"episodes"/"fm_real_python_csv_three_bugs_long_en.json"
REVIEW=ROOT/"content"/"recovery_pilot"/"real_python_long_release_review_candidate.json"
CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
EXPECTED_MP4="1a20dedf886f3228445ed718e1f2e93a7e38cd74abf8aeb211540e32b6683f42"
EXPECTED_SRT="b4b317c8d1d9883294e9ebb32b23c6790a4cdb891be9bbd560fd459baa132a0e"
EXPECTED_COVER="0d9126ca4ada6f04676c2d813361107cfeed52323b644dcfb7c17dec117892f1"
EXPECTED_TITLE="Why Your CSV Total Is Wrong: 3 Data-Cleaning Bugs in Python"
EXPECTED_DOCS=("https://docs.python.org/3/library/csv.html",
               "https://docs.python.org/3/library/decimal.html")
EXPECTED_CUE_COUNT=44

class MetadataNotReleaseReady(ValueError):
    pass

def need(ok:bool,reason:str):
    if not ok:
        raise MetadataNotReleaseReady(reason)

def validate(metadata:dict,review:dict)->dict:
    need(type(metadata) is dict and type(review) is dict,
         "MISSING_REAL_RELEASE_METADATA")
    need(metadata.get("id")==review.get("episode_id")==
         "fm_real_python_csv_three_bugs_long_en"
         and metadata.get("channel_id")==CHANNEL
         and metadata.get("renderer")=="real_python_terminal_capture_v1"
         and metadata.get("type")=="long"
         and metadata.get("language")=="en"
         and metadata.get("title")==review.get("title")==EXPECTED_TITLE,
         "VIDEO_ID_CHANNEL_RENDERER_OR_EXACT_TITLE_MISMATCH")
    need(metadata.get("exact_original_mp4_sha256")==review.get("sha256")==EXPECTED_MP4
         and metadata.get("exact_original_srt_sha256")==EXPECTED_SRT
         and type(metadata.get("reviewed_mp4_duration_seconds")) in (float,int)
         and abs(metadata["reviewed_mp4_duration_seconds"]-214.833)<0.001
         and metadata.get("original_github_preservation_run")==43898583072
         and metadata.get("original_github_preservation_artifact_id")==14240127005,
         "WRONG_OR_UNVERIFIED_EXACT_MEDIA_BYTES")
    need(metadata.get("source_captured_and_narrated") is True
         and metadata.get("first_party_fictional_invoice_data") is True
         and metadata.get("raw_row_count")==review["source_data"]["raw_rows"]==8
         and metadata.get("deduplicated_row_count")==review["source_data"]["clean_rows"]==6
         and metadata.get("raw_total_usd")==review["source_data"]["naive_usd"]=="2656.25"
         and metadata.get("unique_total_usd")==review["source_data"]["clean_usd"]=="1430.75",
         "MISREPRESENTED_OR_UNVERIFIED_EXECUTED_CSV")
    description=metadata.get("description")
    need(metadata.get("source_links")==list(EXPECTED_DOCS)
         and type(description) is str
         and all(x in description for x in (
             "fictional", "$2,656.25", "$1,430.75",
             "Decimal", *EXPECTED_DOCS))
         and "customer data" in description,
         "MISLEADING_DESCRIPTION_OR_MISSING_OFFICIAL_SOURCES")
    cues=metadata.get("captions")
    need(type(cues) is list and len(cues)==EXPECTED_CUE_COUNT,
         "MISSING_REAL_44_SUBTITLE_CUES")
    previous_end=-1.0
    for cue in cues:
        need(type(cue) is dict and set(cue)=={"start","end"}
             and all(type(cue[k]) in (float,int) for k in ("start","end")),
             "WRONG_CAPTION_FORMAT")
        start,end=cue["start"],cue["end"]
        need(previous_end<=start<end<=214.833 and end-start<=11.5,
             "NONMONOTONIC_OR_MISALIGNED_REAL_SUBTITLES")
        previous_end=end
    need(abs(cues[0]["start"]-0)<0.001 and abs(cues[-1]["end"]-214.601)<0.001,
         "SUBTITLE_START_OR_END_CHANGED")
    need(metadata.get("actual_subtitle_cue_count")==EXPECTED_CUE_COUNT,
         "WRONG_DECLARED_SUBTITLE_COUNT")
    need(metadata.get("owner_video_chat_approval_observed") is True
         and metadata.get("owner_full_voice_captions_rights_facts_release_signed") is False
         and metadata.get("published_before") is False
         and metadata.get("youtube_uploaded") is False
         and metadata.get("youtube_scheduled") is False
         and metadata.get("actual_youtube_upload_id") is None
         and metadata.get("actual_youtube_publish_at_utc") is None,
         "FORGED_CHANNEL_RELEASE_OR_OWNER_RIGHTS_APPROVAL")
    # The actual protected publisher also validates PII/metadata. Its required
    # owner signature and live future schedule are intentionally NOT in metadata.
    problems=validate_editorial_release(metadata,[])
    need(problems==[],"EXISTING_PROTECTED_PUBLISHER_METADATA_GATE_FAILED")
    return {
        "status":"SOURCE_METADATA_COMPATIBLE_OWNER_SIGNATURE_AND_YOUTUBE_MISSING",
        "video_sha256":EXPECTED_MP4,
        "captions_sha256":EXPECTED_SRT,
        "thumbnail_sha256":EXPECTED_COVER,
        "original_caption_cues":EXPECTED_CUE_COUNT,
        "channel_id":CHANNEL,
        "live_youtube_auth_verified":False,
        "complete_exact_media_owner_release_signed":False,
        "youtube_uploads":0,
        "youtube_schedules":0,
    }

def main()->None:
    need(META.is_file() and not META.is_symlink() and META.stat().st_size<25000,
         "MISSING_OR_UNSAFE_CANONICAL_EPISODE")
    need(REVIEW.is_file() and not REVIEW.is_symlink(),
         "MISSING_CANONICAL_LONG_REVIEW")
    print(json.dumps(validate(json.loads(META.read_text("utf8")),
                              json.loads(REVIEW.read_text("utf8"))),
                     sort_keys=True,indent=2))

if __name__=="__main__":
    main()
