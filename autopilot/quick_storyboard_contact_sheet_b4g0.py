"""B4g0 cloud-only fast preview of all 17 B4f9 original editorial scenes.

Generates 3 watermarked contact sheets in one cheap CPU operation, without
Google, news scraping, TTS model download, audio, YouTube, or user laptop.
The source files are test-only synthetic claims; NO release approval.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw

from autopilot.cinematic_scene_board_b4f9 import (
    BEATS, STATUS as SCENE_STATUS, render_editorial_frame,
)
from autopilot.nonfactual_narration_rehearsal import build_nonfactual_rehearsals
from autopilot.test_nonfactual_narration_rehearsal_b4d9 import pipeline
from autopilot.full_original_rehearsal_media_b4e1 import prepare_full_rehearsal_plan
from autopilot.real_rehearsal_voice_media_b4e0 import _font

STATUS="B4G0_QUICK_VISUAL_EDITORIAL_CONTACT_SHEETS_NO_MEDIA_NO_PUBLISH"
LAYOUTS={
    "short_am":{"columns":2,"cell":(540,960)},
    "long":{"columns":3,"cell":(640,360)},
    "short_pm":{"columns":2,"cell":(540,960)},
}


class PreviewRefused(ValueError):
    """No invalid source fixture or uncontrolled public preview."""


def _need(ok:bool,message:str)->None:
    if not ok:
        raise PreviewRefused(message)


def _sha(path:Path)->str:
    h=sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def generate_original_contact_sheets(folder:Path)->dict:
    _need(isinstance(folder,Path) and folder.is_dir()
          and not folder.is_symlink() and not list(folder.iterdir()),
          "Only empty owner-preapproved output directory")
    source=pipeline()
    rehearsals=build_nonfactual_rehearsals(*source)
    plan=prepare_full_rehearsal_plan(*source,rehearsals)
    _need(plan["status"]=="B4E1_SOURCE_LOCKED_ALL_17_SCENES_NO_PUBLISH"
          and plan["original_full_scene_count"]==17
          and plan["release_authorized"] is False,
          "Original synthetic 17-scene plan cannot be verified")
    manifest=[]
    for ep in plan["episodes"]:
        slot=ep["slot"]
        cfg=LAYOUTS[slot]
        columns=cfg["columns"];cw,ch=cfg["cell"]
        n=len(ep["scenes"])
        _need(n==(9 if slot=="long" else 4),
              "The original rehearsal scene count changed")
        rows=(n+columns-1)//columns
        sheet=Image.new("RGB",(columns*cw,rows*(ch+50)),(8,15,25))
        painter=ImageDraw.Draw(sheet)
        digests=[]
        layout_names=[]
        for index,scene in enumerate(ep["scenes"]):
            rendered=render_editorial_frame(ep,scene,revealed=True)
            _need(rendered.size==tuple(ep["size"]),
                  "The renderer did not preserve physical MP4 orientation")
            col=index%columns;row=index//columns
            x,y=col*cw,row*(ch+50)
            frame=rendered.resize((cw,ch),Image.Resampling.LANCZOS)
            sheet.paste(frame,(x,y))
            label=f"{slot.upper()}  ·  SCENE {index+1:02} / {n:02}"
            painter.text((x+12,y+ch+10),label,
                         font=_font(26),fill=(190,224,247))
            digests.append(sha256(rendered.tobytes()).hexdigest())
            layout_names.append(BEATS[scene["scene_id"]][3])
        _need(len(set(digests))==n,"Visual scenes are not unique")
        name=f"REVIEW_ONLY_{slot.upper()}_EDITORIAL_CONTACT.png"
        dest=folder/name
        sheet.save(dest,"PNG",optimize=True)
        _need(dest.is_file() and dest.stat().st_size>30000,
              "Original editorial preview could not be encoded")
        manifest.append({
            "slot":slot,
            "source_derived_scene_count":n,
            "layout_families":layout_names,
            "contact_file":name,
            "contact_png_sha256":_sha(dest),
            "actual_original_full_mp4_generated":False,
            "human_full_watch_completed":False,
            "licensed_or_factual_for_publication":False,
        })
    _need(len(manifest)==3 and sum(x["source_derived_scene_count"]
                                  for x in manifest)==17,
          "All three original synthetic storyboards required")
    result={
        "status":STATUS,
        "storyboards":manifest,
        "original_synthetic_scenes":17,
        "human_approved_videos":0,
        "actual_queued_video_render_verified_here":False,
        "all_mp4_caption_layers_embedded":False,
        "publication_authorized":False,
        "live_youtube_uploads_or_modifications":0,
    }
    (folder/"CONTACT_SHEET_VISUAL_REVIEW_ONLY.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return result


def main()->None:
    ap=argparse.ArgumentParser(description="Original, unapproved visual contact sheets")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    _need(os.environ.get("GITHUB_ACTIONS")=="true"
          and os.environ.get("GITHUB_REF")=="refs/heads/main"
          and os.environ.get("GITHUB_EVENT_NAME")=="workflow_dispatch"
          and os.environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
          and os.environ.get("FLOWMINUTE_VISUAL_QA_ONLY")=="true"
          and args.output==Path(os.environ.get("RUNNER_TEMP","/tmp"))/
              "flowminute-b4g0-visual-only",
          "No unapproved GitHub local visual-preview execution")
    args.output.mkdir(parents=True,exist_ok=False)
    result=generate_original_contact_sheets(args.output)
    print(f"B4G0_UNAPPROVED_ORIGINAL_SCENES={result['original_synthetic_scenes']}")
    print("B4G0_NO_VIDEO_UPLOAD_NO_FACT_RIGHTS_APPROVAL")


if __name__=="__main__":
    main()
