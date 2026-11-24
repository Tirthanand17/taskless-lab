"""CLIVOX V3 unapproved editorial draft from recomputed candidate evidence.

Creates no media, files, external requests or permissions. Layout coordinates
are explicitly operator-proposed, not detected faces or verified subject regions.
"""
from __future__ import annotations

import hashlib
import re
from scripts.branch3_v2_p5_longform_local_signal_planner import canonical
from scripts.branch3_v3_transcript_context import combine_observations


def need(ok, reason):
    if not ok:
        raise ValueError("CLIVOX_V3_DRAFT_" + reason)


def clean(text):
    return " ".join(text.split()).translate(str.maketrans({"<":"‹",">":"›","{":"(","}":")","\\":"＼"}))


def clock(ms):
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def captions(rows, start, end):
    groups, group = [], []
    def flush():
        if group:
            groups.append({"start_ms":group[0][0]-start, "end_ms":group[-1][1]-start,
                           "text":" ".join(w[2] for w in group)})
            group.clear()
    for row in rows:
        for word in row["words"]:
            a,b = word["start_ms"],word["end_ms"]
            if a < start or b > end:
                continue
            text=clean(word["text"])
            need(bool(text),"EMPTY_WORD")
            if group and (a-group[-1][1]>500 or b-group[0][0]>3000
                          or len(" ".join(w[2] for w in group))+1+len(text)>42):
                flush()
            need(len(text)<=42,"LONG_WORD_REVIEW")
            group.append((a,b,text))
        flush()
    return groups


def srt(cues):
    return "".join(f"{i}\n{clock(c['start_ms'])} --> {clock(c['end_ms'])}\n{c['text']}\n\n"
                   for i,c in enumerate(cues,1))


def layout(profile, width, height, facecam=None, game=None):
    """Fit preserves source; optional explicit game/facecam crops, no guessed tracking."""
    need(type(width) is int and type(height) is int and
         16<=width<=7680 and 16<=height<=4320 and width%2==height%2==0,"DIMENSIONS")
    def region(box):
        need(type(box) is list and len(box)==4 and all(type(v) is int and v%2==0 for v in box),"REGION")
        x,y,w,h=box
        need(x>=0 and y>=0 and w>=16 and h>=16 and x+w<=width and y+h<=height,"REGION_BOUNDS")
        return box
    need(profile in ("gaming","dialogue","reaction"),"PROFILE")
    if facecam is None and game is None:
        return {"mode":"fit","output":[1080,1920],"layers":[{"source":[0,0,width,height],
                  "target":[0,0,1080,1920],"scale_mode":"contain"}],
                "operator_subject_review_required":True}
    need(profile=="gaming" and facecam is not None and game is not None,"STACK_REQUIRES_BOTH_REGIONS")
    return {"mode":"game_facecam_stack","output":[1080,1920],"layers":[
        {"source":region(facecam),"target":[0,0,1080,600],"scale_mode":"contain"},
        {"source":region(game),"target":[0,600,1080,1320],"scale_mode":"contain"}],
        "operator_subject_review_required":True}


def draft(measurements, rows, candidate_id, width, height, facecam=None, game=None):
    report=combine_observations(measurements,rows)
    matches=[c for c in report["candidates"] if c["candidate_id"]==candidate_id]
    need(len(matches)==1,"CANDIDATE")
    c=matches[0]
    a,b=c["start_ms"],c["end_ms"]
    cues=captions(rows,a,b)
    # Only text actually observed, never invent a spoken hook or title.
    bounds=c["transcript_segment_range"]
    title=None
    if bounds is not None:
        first=clean(rows[bounds[0]]["text"])
        if len(first)<=95 and re.search(r"[.!?।。！？][\"'”]?$",first):
            title=first
    plan={"stage":"V3_UNAPPROVED_EDIT_DRAFT",
          "candidate":c,"candidate_report_digest":hashlib.sha256(canonical(report)).hexdigest(),
          "layout":layout(measurements["profile"],width,height,facecam,game),
          "caption_cues":cues,"caption_srt":srt(cues),
          "observed_opening_title_draft":title,"original_commentary":None,
          "human_checks":["verify_source_rights","verify_exact_words","review_context_and_payoff",
                          "write_original_commentary","review_mobile_layout_and_captions",
                          "approve_exact_metadata_and_render"],
          "quote_verified":False,"human_editor_approved":False,"render_authorized":False,
          "youtube_upload_authorized":False}
    plan["draft_digest_not_release_authorization"]=hashlib.sha256(canonical(plan)).hexdigest()
    return plan
