"""Source-free, offline review CONTACT SHEETS from real CLIVOX encoded MP4.

The original media, audio, SRT, metadata and unsigned A6 packets must re-pass
their strict existing technical hash and FFprobe checks before any sheet is
created. Every beat appears exactly once plus one outro frame. Contact sheets
are for owner visual triage, never real human playback or a production release.
No network, browser scripts, secrets, borrowed assets, or Google API calls.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scripts.branch3_a6_original_handoff import (
    CATALOG, ROOT, PACKET_NAME, read_json, sha
)
from scripts.branch3_a6_original_review_signature import (
    verify_unsigned_requests
)
from scripts.branch3_original_arcade_pilots import validate_catalog
from scripts.branch3_original_arcade_qa import (
    cue_samples_by_beat, decode_actual_frame
)

NAME="original-beat-review-contact-sheet.jpg"


class ContactSheetBlocked(ValueError):
    pass


def require(condition:bool,why:str)->None:
    if not condition:
        raise ContactSheetBlocked("CLIVOX_A5_CONTACT_SHEET_DENIED_"+why)


def _font(size:int):
    from PIL import ImageFont
    for name in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(name).is_file():
            return ImageFont.truetype(name,size)
    raise ContactSheetBlocked("CLIVOX_A5_CONTACT_SHEET_DENIED_FONT")


def create_one(folder:Path,episode:dict)->dict:
    from PIL import Image, ImageDraw
    require(folder.is_dir() and not folder.is_symlink(),"EPISODE_FOLDER")
    video=folder/"original-review-preview.mp4"
    srt=folder/"narration-timing-draft.srt"
    manifest=folder/"review-manifest.json"
    technical=folder/"technical-review-qa.json"
    packet=folder/PACKET_NAME
    for source in (video,srt,manifest,technical,packet):
        require(source.is_file() and not source.is_symlink(),"SOURCE_FILE")
    require(sha(video)==read_json(packet)["exact_video_sha256"],
            "EXACT_REVIEW_VIDEO_HASH")
    qa=read_json(technical)
    safety=qa.get("decoded_actual_frame_caption_safezone_qa")
    require(type(safety) is dict
            and safety.get("every_storyboard_beat_caption_visible_in_safe_zone") is True
            and safety.get("actual_encoded_frames_checked")==len(episode["beats"])
            and safety.get("caption_layout_human_approved") is False
            and qa.get("youtube_upload_authorized") is False,
            "MISSING_ALL_BEAT_VISUAL_QA")
    points=cue_samples_by_beat(
        srt.read_text("utf-8"),episode["beats"],episode["duration_seconds"]
    )
    require(len(points)==len(episode["beats"]),"SCENE_COUNT")
    target=folder/NAME
    require(not target.exists() and not target.is_symlink(),
            "NO_OVERWRITE_EXACT_REVIEW_SHEET")
    portrait=episode["format"]=="short"
    cols=3 if portrait else 4
    frame_w,frame_h=(214,380) if portrait else (360,203)
    pad=18
    label_h=60
    cell_w=frame_w+pad*2
    cell_h=frame_h+label_h+pad*2
    render_points=[
        (item["beat_index"],item["time_s"],False) for item in points
    ]
    # Include a frame after speech ends, so late-story/outro overlay problems
    # (including stranded captions) remain visible to the owner.
    end=episode["duration_seconds"]-.26
    require(end>points[-1]["time_s"],"OUTRO_FRAME_AFTER_SPEECH")
    render_points.append((len(points),end,True))
    rows=math.ceil(len(render_points)/cols)
    require(2<=rows<=5,"CONTACT_SHEET_ROWS")
    canvas=Image.new("RGB",(cols*cell_w+2*pad,rows*cell_h+2*pad),
                     (10,15,26))
    draw=ImageDraw.Draw(canvas)
    header_font=_font(17)
    caption_font=_font(13)
    for pos,(index,second,is_outro) in enumerate(render_points):
        require(type(index) is int and type(second) in (int,float),
                "POINT_FORMAT")
        original=decode_actual_frame(video,second)
        thumb=original.resize((frame_w,frame_h),
                              resample=Image.Resampling.LANCZOS)
        x=pad+(pos%cols)*cell_w+pad
        y=pad+(pos//cols)*cell_h+pad
        canvas.paste(thumb,(x,y))
        heading=("FINAL OUTRO" if is_outro else
                 f"BEAT {index+1:02d} / {len(points):02d}")
        draw.text((x,y+frame_h+8),heading,
                  fill=(255,147,77),font=header_font)
        label=("Silent closing scene" if is_outro else
               episode["beats"][index]["headline"])
        # Never execute or download text; plain first-party screenplay only.
        draw.text((x,y+frame_h+32),label[:35],
                  fill=(229,235,245),font=caption_font)
    canvas.save(target,format="JPEG",quality=86,optimize=True)
    require(1_000<target.stat().st_size<8_000_000,
            "CONTACT_SHEET_FILE_BOUNDS")
    return {
        "episode_id":episode["id"],
        "scene_frames":len(points),
        "outro_frames":1,
        "total_contact_sheet_frames":len(render_points),
        "file_name":NAME,
        "jpg_sha256":sha(target),
        "full_video_human_watched":False,
        "youtube_upload_authorized":False,
    }


def build(directory:Path,*,selection:str)->dict:
    require(selection in ("one","all"),"SELECTION")
    require(isinstance(directory,Path) and directory.is_absolute()
            and directory.is_dir() and not directory.is_symlink()
            and ROOT not in directory.parents and directory!=ROOT,
            "OUTSIDE_PUBLIC_GIT_ONLY")
    proof=verify_unsigned_requests(directory,selection=selection)
    require(proof["all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed"]
            and proof["actual_human_video_approvals_verified"]==0
            and proof["youtube_upload_authorized"] is False,
            "NOT_EXACT_UNSIGNED_REVIEW")
    episodes=validate_catalog(json.loads(CATALOG.read_text("utf-8")))
    if selection=="one":
        episodes=episodes[:1]
    result=[create_one(directory/ep["id"],ep) for ep in episodes]
    return {
        "stage":"A5_ORIGINAL_ALL_BEAT_OWNER_VISUAL_CONTACT_SHEETS",
        "episode_count":len(result),
        "contact_sheets":result,
        "actual_original_video_files_revalidated":True,
        "source_media_downloaded":False,
        "all_scene_frames_included_plus_outro":True,
        "owner_review_and_playback_completed":False,
        "real_owner_signed_release_exists":False,
        "actual_google_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def fixture()->dict:
    return {
        "stage":"A5_CONTACT_SHEET_CONTRACT_ONLY_NOT_ACTUAL_MEDIA",
        "every_beat_contact_sheet_generation_supported":True,
        "actual_video_frames_decoded_in_fixture":0,
        "owner_review_verified":False,
        "actual_google_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("fixture","build"),default="fixture")
    parser.add_argument("--selection",choices=("one","all"),default="one")
    parser.add_argument("--directory",type=Path)
    args=parser.parse_args()
    if args.mode=="fixture":
        result=fixture()
    else:
        require(args.directory is not None,"MISSING_DIRECTORY")
        result=build(args.directory,selection=args.selection)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
