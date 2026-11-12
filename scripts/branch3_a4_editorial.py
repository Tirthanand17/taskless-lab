"""Clivox A4 original editorial storyboard planner (source-free, no release).

Works only from creator-unlicensed research hypotheses. Narration text here
must be independently written by Clivox; no third-party quotes or media.
Passing validation does not establish originality, rights or YPP eligibility.
No network, no media files, no model calls, no permissions/YouTube changes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"branch3/editorial/fixtures/ymh_ep347_source_free.json"
CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"
CATEGORIES=frozenset({"gaming","livestream","comedy","entertainment","podcast_interview"})
VISUALS=frozenset({"original_kinetic_typography","original_illustration",
                   "original_diagram","original_animation",
                   "none_until_rights_verified"})
ROLES=frozenset({"hook","context","licensed_source_placeholder",
                 "original_analysis","ending"})
RELEASE_LOCKS=(
    "creator_grant_verified","underlying_rights_cleared",
    "source_context_checked","clip_timestamp_verified",
    "original_commentary_human_approved","all_media_qa_passed",
    "exact_asset_signed","ready_to_download","ready_to_render",
    "youtube_upload_authorized","youtube_publish_authorized",
)
KEYS={
    "schema_version","channel_id","proposal_id","category","state",
    "source_case_id","source_video_id","source_url","research_context",
    "format","creative_intent","beats","design","release_locks",
}
SOURCE_VIDEO=re.compile(r"[A-Za-z0-9_-]{11}\Z")
ID=re.compile(r"clivox_[a-z0-9][a-z0-9_-]{5,100}\Z")
WORDS=re.compile(r"\b[\w'-]+\b")

class EditorialHold(ValueError):
    """Source-free hypothesis cannot be treated as a cleared edit."""

def require(value: bool, code: str) -> None:
    if not value:
        raise EditorialHold("CLIVOX_A4_DENY_"+code)

def text(value: object, limit: int=400) -> str:
    require(type(value) is str and 0<len(value)<=limit
            and value==value.strip() and all(ord(c)>=32 for c in value),
            "TEXT_INVALID")
    require("<script" not in value.lower() and "javascript:" not in value.lower(),
            "UNTRUSTED_MARKUP")
    return value

def check_script(proposal: dict) -> dict:
    require(type(proposal) is dict and set(proposal)==KEYS,"ROOT_KEYS")
    require(proposal["schema_version"]==1 and proposal["channel_id"]==CHANNEL,
            "SCHEMA_OR_CHANNEL")
    require(proposal["category"] in CATEGORIES,"CATEGORY")
    require(proposal["state"]=="SOURCE_FREE_HYPOTHESIS_NOT_FOR_RELEASE",
            "CLAIMED_READY_STATE")
    for key in ("proposal_id","source_case_id"):
        val=text(proposal[key],110)
        require(ID.fullmatch(val) is not None,"IDENTIFIER")
    require(proposal["proposal_id"]!=proposal["source_case_id"],"ID_COLLISION")
    vid=proposal["source_video_id"]
    require(type(vid) is str and SOURCE_VIDEO.fullmatch(vid) is not None,"VIDEO_ID")
    require(proposal["source_url"]==f"https://www.youtube.com/watch?v={vid}",
            "CANONICAL_SOURCE")
    if vid=="i6pmnpaOaZQ":
        require(proposal["source_case_id"]=="clivox_ymh_ep347_case","PILOT_SOURCE_CASE")
    c=proposal["research_context"]
    require(type(c) is dict and set(c)=={
        "full_source_watched","precise_clip_start_ms","precise_clip_end_ms",
        "transcript_verified","speaker_quotation_included","premise",
        "premise_verified",
    },"RESEARCH_KEYS")
    require(all(c[k] is False for k in (
        "full_source_watched","transcript_verified",
        "speaker_quotation_included","premise_verified",
    )),"INVENTED_SOURCE_VERIFICATION")
    require(c["precise_clip_start_ms"] is None and
            c["precise_clip_end_ms"] is None,"FAKE_SOURCE_TIME")
    text(c["premise"],350)
    f=proposal["format"]
    require(type(f) is dict and set(f)=={
        "width","height","orientation","total_duration_seconds",
        "original_audio_recorded","licensed_media_attached",
    },"FORMAT_KEYS")
    require(f["width"]==1080 and f["height"]==1920
            and f["orientation"]=="vertical"
            and type(f["total_duration_seconds"]) is int
            and 20<=f["total_duration_seconds"]<=55,
            "SHORTS_FORMAT")
    require(f["original_audio_recorded"] is False and
            f["licensed_media_attached"] is False,
            "UNVERIFIED_MEDIA")
    creative=proposal["creative_intent"]
    require(type(creative) is dict and set(creative)=={
        "hook_type","suggested_title","what_clivox_adds",
        "story_thesis","factual_claims_checked",
        "human_originality_review_passed",
    },"CREATIVE_KEYS")
    require(creative["hook_type"] in {
        "curiosity_question","surprising_contrast","clear_stakes",
        "humorous_hypothetical","original_thesis",
    },"HOOK_KIND")
    for key,limit in (("suggested_title",110),
                      ("what_clivox_adds",350),("story_thesis",350)):
        text(creative[key],limit)
    require(creative["factual_claims_checked"] is False
            and creative["human_originality_review_passed"] is False,
            "SELF_ATTESTED_ORIGINALITY")
    beats=proposal["beats"]
    require(type(beats) is list and 4<=len(beats)<=10,"BEAT_COUNT")
    require(all(type(b) is dict and set(b)=={
        "start_s","end_s","role","visual","original_narration",
        "source_quotation","editor_note",
    } for b in beats),"BEAT_KEYS")
    prev=0
    role_counts={k:0 for k in ROLES}
    source_placeholder_duration=0
    original_duration=0
    original_analysis_words=0
    original_words=0
    for index,b in enumerate(beats):
        start,end=b["start_s"],b["end_s"]
        require(type(start) is int and type(end) is int
                and 0<=start<end<=f["total_duration_seconds"]
                and start==prev,"BEAT_GAP_OR_OVERLAP")
        prev=end
        role=b["role"]
        require(role in ROLES and b["visual"] in VISUALS,"ROLE_OR_VISUAL")
        require(b["source_quotation"] is None,"SOURCE_QUOTE_WITHOUT_TRANSCRIPT")
        text(b["editor_note"],350)
        role_counts[role]+=1
        duration=end-start
        if role=="licensed_source_placeholder":
            require(b["visual"]=="none_until_rights_verified"
                    and b["original_narration"] is None,
                    "SOURCE_PLACEHOLDER_MUST_BE_EMPTY")
            source_placeholder_duration+=duration
        else:
            require(b["visual"]!="none_until_rights_verified",
                    "PLACEHOLDER_IN_ORIGINAL_BEAT")
            narration=text(b["original_narration"],350)
            require("http://" not in narration and "https://" not in narration,
                    "SOURCE_LINK_IN_NARRATION")
            words=len(WORDS.findall(narration))
            require(words>0 and words/duration<=3.7,"IMPRACTICAL_VOICEOVER")
            original_duration+=duration
            original_words+=words
            if role=="original_analysis":
                original_analysis_words+=words
    require(prev==f["total_duration_seconds"],"INCOMPLETE_TIMELINE")
    require(beats[0]["role"]=="hook" and beats[0]["end_s"]<=3,
            "HOOK_NOT_IMMEDIATE")
    require(beats[-1]["role"]=="ending","PAYOFF_OR_END_MISSING")
    require(role_counts["licensed_source_placeholder"]==1
            and role_counts["original_analysis"]>=1
            and role_counts["hook"]==1 and role_counts["ending"]==1,
            "REQUIRED_STORY_ELEMENTS")
    require(8<=source_placeholder_duration<=20
            and original_analysis_words>=18
            and original_words>=30
            and original_duration>=20,
            "INSUFFICIENT_ORIGINAL_STORY_DESIGN")
    design=proposal["design"]
    require(type(design) is dict and set(design)=={
        "brand","safe_vertical_caption_margin_px",
        "no_looping_spinner_overlay","no_unlicensed_music",
        "third_party_visuals_in_storyboard",
        "captions_are_substantive_editorial_substitute",
        "paid_promotion_status",
    },"DESIGN_KEYS")
    require(design["brand"]=="Clivox silver-and-orange"
            and type(design["safe_vertical_caption_margin_px"]) is int
            and 180<=design["safe_vertical_caption_margin_px"]<=420,
            "BRAND_OR_SAFE_AREA")
    require(design["no_looping_spinner_overlay"] is True
            and design["no_unlicensed_music"] is True
            and design["third_party_visuals_in_storyboard"] is False
            and design["captions_are_substantive_editorial_substitute"] is False
            and design["paid_promotion_status"]=="NOT_REVIEWED",
            "MISLEADING_OR_UNLICENSED_VISUALS")
    locks=proposal["release_locks"]
    require(type(locks) is dict and set(locks)==set(RELEASE_LOCKS)
            and all(locks[k] is False for k in RELEASE_LOCKS),
            "FALSE_RELEASE_AUTHORIZATION")
    serialized=json.dumps(proposal,sort_keys=True,ensure_ascii=False,
                          separators=(",",":"))
    return {
        "stage":"A4_SOURCE_FREE_ORIGINAL_EDITORIAL",
        "channel_id":CHANNEL,
        "proposal_id":proposal["proposal_id"],
        "source_video_id":vid,
        "category":proposal["category"],
        "status":"HOLD_UNTIL_VERIFIED_RIGHTS_AND_EDITORIAL_REVIEW",
        "total_duration_seconds":f["total_duration_seconds"],
        "original_narration_word_count":original_words,
        "original_planned_duration_seconds":original_duration,
        "licensed_source_placeholder_seconds":source_placeholder_duration,
        "originality_quality_human_review_completed":False,
        "source_quote_fact_checked":False,
        "creator_license_verified":False,
        "source_download_authorized":False,
        "video_render_authorized":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "editorial_plan_sha256":hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "note":"Original script structure only; duration and word counts are NOT a YouTube originality or copyright safe harbor.",
    }

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    require(args.input.is_file() and not args.input.is_symlink()
            and args.input.stat().st_size<65_536,"INPUT_FILE")
    report=check_script(json.loads(args.input.read_text(encoding="utf-8")))
    output=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if args.out:
        require(not args.out.is_symlink(),"OUTPUT_SYMLINK")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(output,encoding="utf-8")
    else:
        print(output,end="")
    print("CLIVOX_A4_SOURCE_FREE_STORYBOARD_VALIDATED_NOT_RENDERED_NOT_PUBLISHED")

if __name__=="__main__":
    main()
