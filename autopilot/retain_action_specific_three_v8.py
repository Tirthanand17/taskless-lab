"""B4e6: real before/after source-art inspection of science-specific scenes.

Outputs original 2026-11-12 NASA/NIST/USGS demonstration contacts for
owner visual REVIEW only. No voice model, proprietary reference, paid cloud,
live research, licensing approval or YouTube publish attempt.
"""
from __future__ import annotations

import io
from hashlib import sha256
import json
from pathlib import Path
import shutil

from autopilot.primary_sourced_storyboards import build_story, render_original_svg
from autopilot.action_specific_floating_v7 import (
    MOTIFS, STATUS as ART_STATUS, paint_action_specific_source_scene,
)
from autopilot.visual_motion_review_v7 import (
    SLOTS, COUNTS, SCENE_DAY, _contact_sheet, _hero_sha, MotionReviewRefused,
)
from autopilot.cinematic_scene_v3 import SCENE_PANEL
from autopilot.cinematic_editorial_grid_v5 import apply_source_cinematic_editorial_grid
from autopilot.visual_motion_review_v7 import _frame as previous_frame

STATUS = "B4E6_ORIGINAL_19_STORY_ACTION_MOTIFS_SOURCE_ART_COMPARISON_UNAPPROVED"
EXAMPLES = frozenset((
    ("short_am",2),("short_am",3),
    ("short_pm",2),("short_pm",4),
    ("long",7),("long",17),("long",18),("long",19),
))


def _new_frame(story: dict, scene_index: int, tick: int = 60):
    from PIL import Image
    import cairosvg
    raw=render_original_svg(story,scene_index,tick).encode()
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=raw))) as original:
        image=original.convert("RGB")
    art=paint_action_specific_source_scene(
        image,story=story,scene_index=scene_index,tick=tick)
    layout=apply_source_cinematic_editorial_grid(
        image,story=story,scene_index=scene_index)
    if (art["release_authorized"] is not False
        or layout["release_authorized"] is not False
        or art["source_story_draft_sha256"]!=story["draft_sha256"]):
        raise MotionReviewRefused("Changed or authorized story in visual proof")
    return image,art


def _comparison(before,after,out:Path,action:str)->dict:
    from PIL import Image,ImageDraw
    if before.size!=after.size or before.mode!=after.mode:
        raise MotionReviewRefused("Invalid original before/after frame geometry")
    size=(332,590) if before.width<before.height else (570,321)
    left=before.copy();right=after.copy()
    left.thumbnail(size);right.thumbnail(size)
    w=left.width+right.width+46;h=max(left.height,right.height)+90
    result=Image.new("RGB",(w,h),(8,18,32))
    d=ImageDraw.Draw(result)
    d.text((10,10),"BEFORE   /   REPEATED ART",fill=(226,231,241))
    d.text((left.width+30,10),"AFTER   /   SOURCE ACTION",fill=(110,227,189))
    result.paste(left,(10,31));result.paste(right,(left.width+30,31))
    d.text((12,h-34),action.replace("_"," ").upper(),fill=(110,227,189))
    result.save(out,format="PNG",optimize=True)
    size=out.stat().st_size
    if not 12_000<=size<=18_000_000:
        raise MotionReviewRefused("Actual before/after artwork missing")
    return {"filename":out.name,"sha256":sha256(out.read_bytes()).hexdigest(),
            "bytes":size,"actual_original_source_images":True,
            "human_quality_approved":False}


def build_action_specific_visual_review(output:Path)->dict:
    from PIL import ImageChops
    output=Path(output)
    if not output.is_absolute() or output.is_symlink() or output.exists():
        raise MotionReviewRefused("New absolute source-only output required")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.mkdir(mode=0o700)
    episodes=[]
    changed=0;unchanged=0
    comparisons=[]
    try:
        for slot in SLOTS:
            story=build_story(slot,SCENE_DAY)
            area=SCENE_PANEL[story["format"]]
            pictures=[];receipts=[]
            for idx,scene in enumerate(story["scenes"]):
                before,_=previous_frame(story,idx,60)
                after,visual=_new_frame(story,idx)
                altered=ImageChops.difference(
                    before.crop(area),after.crop(area)).getbbox() is not None
                expected=scene["visual_action"] in MOTIFS[story["theme"]]
                if altered is not expected:
                    raise MotionReviewRefused(
                        "Selected scene did not genuinely change its hero motif")
                # Headline, cited value, footer and native caption bands must
                # be pixel identical, not just metadata checkmarks.
                for bounds in (
                    (0,0,before.width,area[1]),
                    (0,area[3],before.width,before.height),
                ):
                    if ImageChops.difference(
                        before.crop(bounds),after.crop(bounds)).getbbox():
                        raise MotionReviewRefused("Original scene text/caption altered")
                if (visual["unique_science_action_composition_used"] is not expected
                    or visual["science_story_action"]!=scene["visual_action"]):
                    raise MotionReviewRefused("Story visual action receipt mismatch")
                if expected:changed+=1
                else:unchanged+=1
                pictures.append(after)
                receipts.append({
                    "scene_id":scene["scene_id"],
                    "story_action":scene["visual_action"],
                    "source_value_sha256":visual["source_display_value_sha256"],
                    "changed_science_hero_vs_floating_v6":altered,
                    "new_full_native_hero_sha256":_hero_sha(after,area),
                    "all_outside_hero_source_pixels_unchanged":True,
                    "human_visual_approval":False,
                    "release_authorized":False,
                })
                if (slot,idx) in EXAMPLES:
                    art_name=f"{slot}_{idx+1:02d}_SOURCE_ACTION_BEFORE_AFTER.png"
                    result=_comparison(before,after,output/art_name,scene["visual_action"])
                    comparisons.append({"slot":slot,"scene":idx+1,**result})
            art=_contact_sheet(
                story,pictures,
                output/f"{slot.upper()}_ALL_SCENES_SOURCE_ACTION_UNAPPROVED.png")
            episodes.append({
                "slot":slot,"scene_count":len(receipts),
                "source_draft_sha256":story["draft_sha256"],
                "source_day_ist":SCENE_DAY,
                "science_action_motifs":sum(x["changed_science_hero_vs_floating_v6"]
                                            for x in receipts),
                "scenes":receipts,"contact_sheet":art,
                "source_claim_and_narration_human_reviewed":False,
                "release_authorized":False,
            })
        if (changed!=19 or unchanged!=13
            or len(comparisons)!=8
            or len(episodes)!=3
            or sum(x["scene_count"] for x in episodes)!=32
            or [x["slot"] for x in episodes]!=list(SLOTS)):
            raise MotionReviewRefused("Incomplete or false story-action visual variety")
        result={
            "status":STATUS,"schema_version":1,"source_art_provenance":ART_STATUS,
            "source_day_ist":SCENE_DAY,
            "source_topics_are_new_daily_content":False,
            "total_physical_original_beats":32,
            "scene_hero_motifs_physically_changed":changed,
            "untouched_original_hero_motifs":unchanged,
            "new_action_specific_hero_outside_caption_area":True,
            "visual_user_reference_media_copied":False,
            "contact_sheets":3,
            "before_after_original_source_art_pairs":comparisons,
            "episodes":episodes,
            "all_human_creative_watch_and_claim_reviewed":False,
            "generic_spinner_freedom_human_confirmed":False,
            "three_full_encoded_mp4_created_by_this_job":False,
            "youtube_upload_or_schedule":False,
            "release_authorized":False,
        }
        (output/"UNAPPROVED_STORY_ACTION_VISUAL_REPORT.json").write_text(
            json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
        return result
    except Exception:
        shutil.rmtree(output,ignore_errors=True)
        raise


def main():
    import argparse
    p=argparse.ArgumentParser(description="Original source-action visual proof only")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=build_action_specific_visual_review(a.out)
    print(json.dumps({
        "status":report["status"],
        "total_physical_original_beats":report["total_physical_original_beats"],
        "specialized_action_heroes":report["scene_hero_motifs_physically_changed"],
        "contact_sheets":report["contact_sheets"],
        "youtube_upload_or_schedule":False,
        "release_authorized":False,
    }))


if __name__=="__main__":
    main()
