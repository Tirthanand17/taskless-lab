"""B3d4c2c3c: complete unapproved factual/script/visible/metadata surface docket.

All three original research scripts, 70 originally spoken sentence cues, 32
scene titles, 32 scene values, actual SVG-derived text, unreviewed thumbnail
copy and proposed YouTube title/description are independently enumerated
and tied to explicitly classified SOURCE/DERIVATION/ASSUMPTION/CAVEAT claims.

This checks structural completeness and exact text/assets, NOT semantic
claim truth, page recency or human review. This module imports no provider,
secret, uploader or human-signature generator.
"""
from __future__ import annotations

from hashlib import sha256
import re
from typing import Mapping
from xml.etree import ElementTree as ET

from autopilot.cloud_full_duration_pack import sentence_chunks
from autopilot.primary_sourced_storyboards import (
    PRIMARY_REFERENCES, THUMB_CONTENT, SLOTS, canonical,
    build_story, render_original_svg, research_facts, require_exact_draft,
)

STATUS="THREE_FACTUAL_AND_VISIBLE_DRAFT_SURFACES_INDEXED_UNREVIEWED"
KINDS=("primary","derived","illustrative_assumption","limitation")

# Curated trust models, not retrieved excerpts and not automatically human
# corroborated facts. IDs must fully match the original authored script.
CLAIM_KINDS={
    "short_am":{
        "moon_distance":"primary",
        "light_speed":"primary",
        "moon_delay":"derived",
    },
    "long":{
        "bit_byte":"primary",
        "mega_decimal":"primary",
        "megabit_definition":"illustrative_assumption",
        "file_sample":"illustrative_assumption",
        "ideal_transfer":"derived",
        "ideal_model":"limitation",
        "binary_prefix":"primary",
        "binary_transfer":"derived",
    },
    "short_pm":{
        "quake_amplitude":"primary",
        "quake_energy":"primary",
        "quake_damage_caveat":"limitation",
    },
}
VISIBLE_BACKGROUND_CLAIMS={
    "short_am":("moon_distance","light_speed","moon_delay"),
    "long":("bit_byte","mega_decimal","megabit_definition","file_sample",
            "ideal_transfer","binary_prefix"),
    "short_pm":("quake_amplitude","quake_energy"),
}
# These are proposed public descriptions, not remotely uploaded metadata.
# Explicit sourcing appears in each metadata record; no unreviewed title
# becomes a real YouTube API title from this module.
DRAFT_METADATA={
    "short_am":{
        "title":"Why Radio Signals to the Moon Take Time",
        "description":(
            "NASA reports an average Earth-Moon separation near 384,400 km. "
            "With NIST's exact vacuum light speed, that gives an idealized "
            "1.28-second one-way signal path or 2.56 seconds for a round trip. "
            "Actual distance, processing and conversation delays vary. "
            "Educational calculation, not a live mission measurement."
        ),
        "claim_ids":("moon_distance","light_speed","moon_delay"),
    },
    "long":{
        "title":"Megabits vs Megabytes: Why 100 MB Is Not 100 MiB",
        "description":(
            "NIST's decimal mega prefix means one million, while binary "
            "mebi means 2 to the twentieth. A byte has eight bits. "
            "At an ideal 20 megabits per second, a hypothetical 100 MB file "
            "would take 40.00 seconds, while 100 MiB takes about 41.94 seconds. "
            "Ignore network overhead only for this illustrative model; "
            "real transfer speeds and durations vary."
        ),
        "claim_ids":("bit_byte","mega_decimal","megabit_definition",
                     "file_sample","ideal_transfer","binary_prefix",
                     "binary_transfer","ideal_model"),
    },
    "short_pm":{
        "title":"Why Earthquake Magnitude +1 Means About 32 Times the Energy",
        "description":(
            "USGS explains that one whole magnitude step represents roughly "
            "ten times measured wave amplitude, versus about 31.6 times "
            "relative earthquake energy. Two magnitude steps correspond "
            "to a thousandfold energy ratio under an idealized comparison. "
            "Observed shaking and damage depend on additional local factors."
        ),
        "claim_ids":("quake_amplitude","quake_energy",
                     "quake_damage_caveat"),
    },
}


class ClaimSurfaceError(ValueError):
    """Cannot claim complete source/visible/script coverage from altered draft."""


def _sha(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def _surface(*,location:str,text:str,claim_ids:tuple[str,...],
             supported:set[str],origin:str) -> dict:
    if (not isinstance(text,str) or not text.strip()
            or len(text)>1300 or not claim_ids
            or any(not isinstance(x,str) or x not in supported for x in claim_ids)):
        raise ClaimSurfaceError("Unbound, empty or oversized original claim surface")
    return {
        "location":location,
        "origin":origin,
        "literal_unapproved_text":text,
        "text_sha256":sha256(text.encode("utf8")).hexdigest(),
        "curated_claim_ids":list(claim_ids),
        "independently_human_reviewed":False,
        "factually_true_semantics_established_by_matching_ids":False,
    }


def make_unapproved_claim_surface_docket(slot:str,
                                          day:str="2026-11-12") -> dict:
    """Full artifact is rebuildable solely from the original authored story."""
    story=build_story(slot,day)
    require_exact_draft(story)
    claims=set(story["claim_index"])
    if (set(CLAIM_KINDS[slot])!=claims
            or not claims<=set(DRAFT_METADATA[slot]["claim_ids"])
            or not set(VISIBLE_BACKGROUND_CLAIMS[slot])<=claims):
        raise ClaimSurfaceError("Missing independently classified source/derived claims")
    refs=story["primary_sources"]
    surfaces=[]
    cue_count=0
    for row in story["scenes"]:
        cid=tuple(row["claim_ids"])
        if not cid or not set(cid)<=claims:
            raise ClaimSurfaceError("Spoken claim not in source evidence registry")
        for cue_index,sentence in enumerate(sentence_chunks(row["narration"]),1):
            cue_count+=1
            surfaces.append(_surface(
                location=f'{row["scene_id"]}:speech:{cue_index:02d}',
                text=sentence,claim_ids=cid,supported=claims,
                origin="exact_original_Kokoro_pcm_narration_sentence",
            ))
        for key in ("display_title","display_value"):
            surfaces.append(_surface(
                location=f'{row["scene_id"]}:{key}',
                text=row[key],claim_ids=cid,supported=claims,
                origin="original_svg_visible_scene_text",
            ))
        # This re-renders actual SVG source text; the output is original vector
        # HTML/XML, not a model self-reported list of imaginary visual claims.
        # Both the first and late animated samples must be indexed.
        for tick in (0,96):
            vector=render_original_svg(story,row_index(story,row),tick)
            root=ET.fromstring(vector)
            text_lines=[
                node.text.strip() for node in root.iter()
                if node.tag.endswith("text") and node.text and node.text.strip()
            ]
            if (row["display_title"] not in text_lines
                    or row["display_value"] not in text_lines
                    or len(text_lines)<5):
                raise ClaimSurfaceError("Rendered vector differs from asserted scene text")
            surfaces.append(_surface(
                location=f'{row["scene_id"]}:original_svg_tick_{tick}',
                text=" | ".join(text_lines),
                claim_ids=tuple(dict.fromkeys(cid+VISIBLE_BACKGROUND_CLAIMS[slot])),
                supported=claims,origin="actual_rebuilt_svg_XML_text_node_inventory",
            ))
    meta=DRAFT_METADATA[slot]
    thumb=THUMB_CONTENT[story["theme"]]
    for index,line in enumerate(thumb["lines"],1):
        surfaces.append(_surface(
            location=f"unapproved_thumbnail_line_{index}",
            text=line,claim_ids=tuple(thumb["claim_ids"]),
            supported=claims,origin="real_original_thumbnail_generator_text",
        ))
    surfaces.append(_surface(
        location="unapproved_youtube_title",text=meta["title"],
        claim_ids=tuple(meta["claim_ids"]),supported=claims,
        origin="proposed_metadata_never_uploaded",
    ))
    surfaces.append(_surface(
        location="unapproved_youtube_description",text=meta["description"],
        claim_ids=tuple(meta["claim_ids"]),supported=claims,
        origin="proposed_metadata_never_uploaded",
    ))
    if len({s["location"] for s in surfaces})!=len(surfaces):
        raise ClaimSurfaceError("Multiple original text surfaces map to same ID")
    if cue_count<8 or cue_count!=sum(
        len(sentence_chunks(row["narration"])) for row in story["scenes"]
    ):
        raise ClaimSurfaceError("Original spoken narration truncated")
    if (len([s for s in surfaces if s["origin"]=="original_svg_visible_scene_text"])
            !=2*story["scene_count"]):
        raise ClaimSurfaceError("Original SVG title/numerical values not all enumerated")
    claim_items=[]
    for claim_id,spec in sorted(story["claim_index"].items()):
        kind=CLAIM_KINDS[slot][claim_id]
        if kind not in KINDS or not spec["sources"]:
            raise ClaimSurfaceError("Unclassified factual or derived claim")
        if not set(spec["sources"])<=set(refs):
            raise ClaimSurfaceError("Untrusted external citation in claim")
        used=[s["location"] for s in surfaces if claim_id in s["curated_claim_ids"]]
        if not used or not any(":speech:" in x for x in used):
            raise ClaimSurfaceError("Factual claim lacks explicit narration mention")
        claim_items.append({
            "id":claim_id,
            "kind":kind,
            "original_unapproved_summary":spec["summary"],
            "primary_reference_ids":list(spec["sources"]),
            "used_in_exact_original_surfaces":used,
            "independent_source_human_fact_adjudication":False,
        })
    binding={
        "schema_version":1,
        "status":STATUS,
        "episode_id":story["episode_id"],
        "source_draft_sha256":story["draft_sha256"],
        "topic":story["theme"],
        "timeslot_ist":story["time_ist"],
        "format":story["format"],
        "source_references":refs,
        "research_values_sha256":_sha(research_facts()),
        "claim_count":len(claim_items),
        "claims":claim_items,
        "original_scene_count":story["scene_count"],
        "exact_original_narration_sentence_cue_count":cue_count,
        "exact_literal_text_surface_count":len(surfaces),
        "exact_original_surface_manifest":surfaces,
        "every_spoken_caption_and_visible_metadata_surface_structurally_indexed":True,
        "source_pages_current_live_readback_completed":False,
        "real_external_source_excerpt_archived_to_private_vault":False,
        "every_atomic_claim_semantically_supported_by_human":False,
        "actual_onscreen_graphic_and_media_final_human_inspected":False,
        "genuine_owner_fact_and_rights_approvals":False,
        "human_full_watch_completed":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    return {**binding,"unapproved_claim_surface_docket_sha256":_sha(binding)}


def row_index(story:dict,row:dict)->int:
    key=row["scene_id"]
    for index,entry in enumerate(story["scenes"]):
        if entry["scene_id"]==key:
            return index
    raise ClaimSurfaceError("Scene is not in the exact original story")


def require_exact_unapproved_claim_surface_docket(packet:Mapping,
        slot:str,day:str="2026-11-12") -> None:
    expected=make_unapproved_claim_surface_docket(slot,day)
    if not isinstance(packet,dict) or canonical(packet)!=canonical(expected):
        raise ClaimSurfaceError("Altered, missing or promoted unapproved claim surface")


def inspect_three_original_claim_dockets(day:str="2026-11-12") -> dict:
    packets=[make_unapproved_claim_surface_docket(slot,day)
             for slot in ("short_am","long","short_pm")]
    if (len({p["episode_id"] for p in packets})!=3
            or len({p["source_draft_sha256"] for p in packets})!=3
            or len({p["unapproved_claim_surface_docket_sha256"] for p in packets})!=3
            or sum(p["original_scene_count"] for p in packets)!=32
            or len({k for p in packets for k in p["source_references"]})!=6):
        raise ClaimSurfaceError("Exact multi-episode source attribution incomplete")
    return {
        "status":STATUS,
        "episodes":[x["episode_id"] for x in packets],
        "claim_docket_hashes":[x["unapproved_claim_surface_docket_sha256"] for x in packets],
        "exact_narration_sentence_cues":sum(x["exact_original_narration_sentence_cue_count"] for x in packets),
        "exact_scene_count":sum(x["original_scene_count"] for x in packets),
        "distinct_primary_source_ids":6,
        "total_curated_atomic_claim_ids":sum(x["claim_count"] for x in packets),
        "total_visible_and_speech_text_surface_records":sum(x["exact_literal_text_surface_count"] for x in packets),
        "every_curated_source_claim_structurally_referenced":True,
        "real_independent_full_fact_accuracy_review":False,
        "real_human_and_rights_approvals":False,
        "real_owner_verified_release":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
