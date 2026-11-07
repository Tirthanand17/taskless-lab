"""B4g8 expose recycled rehearsal narration across distinct day/topic IDs.

The daily public-source scout changes labels, but the B4d9 demonstration
voiceovers come from a small set of static educational templates. New dates
and selected headlines do NOT imply new spoken stories. Hash normalized
narration ONLY; never retain words, titles, URL or source bytes in GitHub
research artifacts. This is a draft originality WARNING, never approval.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

from autopilot.recent_research_history import HISTORY_STATUS

STATUS="B4G8_ORIGINAL_REHEARSAL_VOICEOVER_REPEAT_CHECK_NOT_CONTENT_APPROVAL"
HEX64=re.compile(r"[0-9a-f]{64}\Z")
SLOTS=("short_am","long","short_pm")
MAX_REHEARSAL=128_000
MAX_HISTORY=512_000
MIN_WORDS=15


class NarrationOriginalityRefused(ValueError):
    """Unbounded or forged source, history or release/identity state."""


def _need(ok:bool,why:str)->None:
    if not ok:
        raise NarrationOriginalityRefused(why)


def _canonical_narration(scenes:object)->bytes:
    _need(type(scenes) is list and len(scenes) in (4,9),
          "Invalid original narration scene count")
    spoken=[]
    for i,scene in enumerate(scenes):
        _need(type(scene) is dict
              and scene.get("scene_index")==i
              and scene.get("story_claims_semantically_verified") is False
              and scene.get("third_party_source_visual_allowed") is False
              and scene.get("source_quote_display_allowed") is False,
              "Not an unapproved 17-scene original rehearsal")
        text=scene.get("original_voiceover_rehearsal_text")
        _need(type(text) is str and 100<=len(text)<=2200,
              "Missing or oversized synthetic original narration")
        norm=" ".join(unicodedata.normalize("NFKC",text).casefold().split())
        _need(len(norm)>=75 and len(re.findall(r"\b[\w'-]+\b",norm))>=MIN_WORDS,
              "Insufficient original spoken scene content")
        spoken.append(norm)
    return "\nSCENE_BOUNDARY\n".join(spoken).encode("utf8")


def _lexical_terms(scenes:object)->set[str]:
    out=set()
    for scene in scenes:
        normal=" ".join(unicodedata.normalize(
            "NFKC",scene["original_voiceover_rehearsal_text"]).casefold().split())
        out.update(
            " ".join(words[i:i+4])
            for words in [re.findall(r"\b[a-z0-9]+\b",normal)]
            for i in range(max(0,len(words)-3)))
    return out


def _simhash64(scenes:object)->str:
    """Approximate 4-word overlap, no spoken text retained in history.

    A 64-bit SimHash is a *similarity hint*, NOT proof that two scripts
    have been copied, checked for rights, or cleared for publication.
    """
    grams=_lexical_terms(scenes)
    _need(bool(grams), "No spoken words for similarity diagnosis")
    weights=[0]*64
    for phrase in grams:
        value=int.from_bytes(sha256(
            b"FLOWMINUTE_B4G9_SPOKEN_4GRAM_V1\0"+phrase.encode("utf8")
        ).digest()[:8],"big")
        for bit in range(64):
            weights[bit]+=1 if value & (1<<bit) else -1
    return f"{sum((1<<bit) for bit,v in enumerate(weights) if v>0):016x}"


def inspect_narration_originality(rehearsals:object,history:object)->dict:
    _need(type(rehearsals) is dict
          and rehearsals.get("status")==
              "B4D9_EPISODE_LOCKED_ORIGINAL_NONFACTUAL_NARRATION_REHEARSAL_NO_RELEASE"
          and rehearsals.get("planned_video_count")==3
          and rehearsals.get("original_scene_count")==17
          and rehearsals.get("factual_news_scripts_completed")==0
          and rehearsals.get("fact_checks_completed")==0
          and rehearsals.get("source_rights_approvals")==0
          and rehearsals.get("youtube_uploads")==0
          and rehearsals.get("release_authorized") is False
          and type(rehearsals.get("three_episodes")) is list
          and len(rehearsals["three_episodes"])==3,
          "Missing original source-locked non-factual rehearsal")
    _need(type(history) is dict
          and history.get("status")==HISTORY_STATUS
          and history.get("not_a_youtube_publication_readback") is True
          and history.get("video_release_authorized") is False
          and type(history.get("verified_prior_research_days")) is int
          and 0<=history["verified_prior_research_days"]<=7
          and type(history.get("verified_prior_script_review_days")) is int
          and 0<=history["verified_prior_script_review_days"]<=7
          and history["verified_prior_script_review_days"]<=
              history["verified_prior_research_days"]
          and type(history.get("historical_script_sha256")) is list,
          "History has no validated source-only prior narration fingerprints")
    prior=history["historical_script_sha256"]
    _need(len(prior)<=21 and len(set(prior))==len(prior)
          and all(type(x) is str and HEX64.fullmatch(x) for x in prior),
          "Unbounded or forged historical spoken-content fingerprints")
    simprior=history.get("historical_script_simhash64",[])
    simdays=history.get("verified_prior_script_simhash_days",0)
    _need(type(simprior) is list and len(simprior)<=21
          and len(set(simprior))==len(simprior)
          and all(type(h) is str and re.fullmatch(r"[0-9a-f]{16}",h)
                  for h in simprior)
          and type(simdays) is int and 0<=simdays<=7
          and simdays<=history["verified_prior_script_review_days"]
          and (simdays>0 or not simprior),
          "Unverified or unbounded near-repeat history")
    day=rehearsals.get("research_day_ist")
    _need(type(day) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}",day),
          "No correct source date for episode identity")
    fingerprints=[]
    similarity_fingerprints=[]
    lexical=[]
    for ep,slot,scenes in zip(rehearsals["three_episodes"],SLOTS,(4,9,4)):
        _need(type(ep) is dict and ep.get("slot")==slot
              and ep.get("episode_id")==f"fm_{day.replace('-','')}_{slot}"
              and ep.get("scene_count")==scenes
              and ep.get("narration_rehearsal_nonfactual") is True
              and ep.get("factual_news_narration_written") is False
              and ep.get("release_authorized") is False,
              "Episode ID/slot or authority changed before originality test")
        narration=ep.get("scenes")
        payload=_canonical_narration(narration)
        fingerprint=sha256(b"FLOWMINUTE_B4G8_SPOKEN_SCENES_V1\0"+payload).hexdigest()
        lexical.append(_lexical_terms(narration))
        fingerprints.append(fingerprint)
        similarity_fingerprints.append(_simhash64(narration))
    _need(len(set(fingerprints))==3,
          "Identical whole narrated scripts inside one day")
    overlaps=[]
    for i in range(3):
        for j in range(i+1,3):
            shared=len(lexical[i]&lexical[j])
            union=len(lexical[i]|lexical[j])
            ratio=round(shared/union if union else 1.0,4)
            overlaps.append({"left_slot":SLOTS[i],"right_slot":SLOTS[j],
                             "four_word_overlap_jaccard":ratio})
    repeats=[f in prior for f in fingerprints]
    # Hamming <=8 is an intentionally conservative review *signal*.
    # A hash mismatch does not prove novelty, nor does a near match
    # prove copyright infringement. No speech is logged or persisted.
    near_repeats=[
        any((int(sig,16)^int(old,16)).bit_count()<=8
            for old in simprior)
        for sig in similarity_fingerprints
    ]
    # Historical coverage 0 means 'UNKNOWN', never 'novel' or 'approved'.
    covered=history["verified_prior_script_review_days"]
    result={
        "status":STATUS,
        "plan_day_ist":day,
        "episode_slots":list(SLOTS),
        "script_fingerprints_sha256":fingerprints,
        "spoken_4gram_simhash64":similarity_fingerprints,
        "previous_verified_receipt_days_with_simhash64":simdays,
        "suspected_near_repeat_per_slot":near_repeats,
        "suspected_near_repeat_in_previous_7_day_receipts":any(near_repeats),
        "near_repeat_hamming_distance_threshold":8,
        "near_repeat_is_only_a_review_signal":True,
        "source_fingerprint_domain":"NORMALIZED_SPOKEN_SCENES_NOT_EPISODE_ID",
        "previous_verified_receipt_days_with_script_hashes":covered,
        "exact_repeat_detected_per_slot":repeats,
        "exact_repeat_detected_in_previous_7_day_receipts":any(repeats),
        "cross_slot_4gram_overlap_diagnostic":overlaps,
        "unique_against_every_prior_day_proven":False,
        "all_three_daily_videos_factually_original_or_rights_checked":False,
        "third_party_news_or_narration_copied":False,
        "actual_human_factual_and_rights_approvals":0,
        "youtube_release_authorized":False,
    }
    _need(len(json.dumps(result))<6500,"Only bounded hash-only originality facts")
    return result


def _read(path:Path,bound:int)->dict:
    _need(path.is_file() and not path.is_symlink()
          and 2<=path.stat().st_size<=bound,
          "Invalid ephemeral original rehearsal or prior GitHub history file")
    try:
        result=json.loads(path.read_text("utf8"),
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              NarrationOriginalityRefused("Nonfinite research JSON")))
    except (UnicodeError,json.JSONDecodeError):
        raise NarrationOriginalityRefused("Malformed ephemeral source") from None
    _need(type(result) is dict,"Expected source object")
    return result


def main()->None:
    p=argparse.ArgumentParser(description="No-publish identical spoken-story detection")
    p.add_argument("--rehearsals",type=Path,required=True)
    p.add_argument("--history",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    _need(args.output.parent.name=="out"
          and args.output.name.startswith("flowminute-ephemeral-")
          and not args.output.exists() and not args.output.is_symlink(),
          "Only new GitHub ephemeral audit file accepted")
    result=inspect_narration_originality(
        _read(args.rehearsals,MAX_REHEARSAL),
        _read(args.history,MAX_HISTORY))
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n","utf8")
    print(json.dumps({
        "status":STATUS,
        "source_independent_scripts_inspected":3,
        "previous_days_with_script_hashes":
            result["previous_verified_receipt_days_with_script_hashes"],
        "scripts_identical_to_recent_verified_receipt":
            sum(result["exact_repeat_detected_per_slot"]),
        "factual_news_scripts_approved":0,
        "youtube_publications":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
