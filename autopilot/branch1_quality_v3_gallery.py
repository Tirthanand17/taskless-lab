"""Branch 1 B1q3 physical original 9-scene corrected editorial gallery.

This is ORIGINAL SOURCE ART (no copyrighted reference), NOT a real MP4.
Real narrated post-merge proof remains the existing main-only B1q2 workflow.
"""
from __future__ import annotations
from pathlib import Path
import json
from hashlib import sha256

from autopilot.branch1_three_narrated_no_spinner_v2 import _load_source,SOURCES
from autopilot.branch1_no_spinner_storyboard import draw_source_keyframe,storyboard_cues

STATUS="B1Q3_ACTUAL_ENLARGED_ORIGINAL_SCENE_SINGLE_CAPTION_UNAPPROVED"


def render_nine_source_proofs(root:Path,out:Path)->dict:
    from PIL import Image,ImageDraw,ImageFont
    root=Path(root);out=Path(out)
    if (not root.is_dir() or not out.is_absolute() or out.exists()
        or out.is_symlink()):
        raise ValueError("Only new ephemeral GitHub original scene review path allowed")
    out.mkdir(parents=True,mode=0o700)
    cells=[]
    evidence=[]
    for episode_id,_ in SOURCES:
        source=_load_source(root,episode_id)
        cues=storyboard_cues(source)
        selected=(0,len(cues)//2,len(cues)-1)
        for idx in selected:
            image,receipt=draw_source_keyframe(
                source,idx,.78,caption_layer="original_source_proof")
            if (receipt["editorial_headline"]==cues[idx]["source_text"]
                or receipt["headline_is_verbatim_audio_caption"]
                or not receipt["visual_hero_enlarged_in_native_canvas"]
                or not receipt["no_circle_spinner_drawn"]
                or receipt["human_approved"] or receipt["youtube_uploaded"]):
                raise ValueError("New larger art, single caption, original owner approval gate failed")
            name=f"{episode_id}_beat_{idx+1:02d}_ORIGINAL_SOURCE_PROOF_UNAPPROVED.png"
            target=out/name
            image.save(target,optimize=True)
            data=target.read_bytes()
            evidence.append({
                "episode":episode_id,"beat":idx+1,"scene_variant":receipt["distinct_original_visual_subject"],
                "file":name,"bytes":len(data),"sha256":sha256(data).hexdigest(),
                "editorial_headline":receipt["editorial_headline"],
                "source_caption_sha256":receipt["caption_source_sha256"],
                "actual_video_with_voice_encoded":False,
                "youTube_remote_updated":False,
            })
            thumb=image.copy()
            thumb.thumbnail((315,565))
            cells.append((name,thumb))
    if len(evidence)!=9:
        raise ValueError("Need exactly nine original proof scenes")
    width=3*328+24;height=3*606+24
    proof=Image.new("RGB",(width,height),(8,17,27))
    draw=ImageDraw.Draw(proof)
    font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",15)
    for i,(name,thumb) in enumerate(cells):
        x=12+(i%3)*328;y=12+(i//3)*606
        proof.paste(thumb,(x,y))
        draw.text((x,y+567),name.split("_2026")[0],fill=(195,220,239),font=font)
        draw.text((x,y+587),evidence[i]["scene_variant"][:29],
                  fill=(130,194,219),font=font)
    cover="B1Q3_NINE_ORIGINAL_BEFORE_OWNER_APPROVAL_SOURCE_PROOF.jpg"
    proof.save(out/cover,quality=89)
    m={
        "status":STATUS,
        "original_scene_count":9,
        "original_episodes_count":3,
        "no_repeating_spinner":True,
        "only_source_photo_illustration_not_third_party_reference":True,
        "original_caption_present_once":True,
        "new_video_encoded":False,
        "previous_youtube_uploaded_binary_mutated":False,
        "owner_fact_visual_voice_rights_approved":False,
        "contact_sheet":cover,
        "scenes":evidence,
    }
    (out/"UNAPPROVED_B1Q3_ORIGINAL_QUALITY_MANIFEST.json").write_text(
        json.dumps(m,indent=2,sort_keys=True)+"\n",encoding="utf8")
    return m


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description="Nine source-only improved subject scenes, NO VIDEO PUBLISH")
    parser.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    r=render_nine_source_proofs(args.repo,args.output)
    print(json.dumps({"status":r["status"],"scenes":r["original_scene_count"],
                      "new_youtube_uploads":0}))
