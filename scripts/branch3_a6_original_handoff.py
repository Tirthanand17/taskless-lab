"""A6 exact-file human review handoff for CLIVOX's ORIGINAL arcade pilot videos.

Recomputes the real MP4, WAV, SRT, catalog, metadata and QA digests before
forming an immutable *quarantined review packet*. A mathematically consistent
packet never grants copyright clearance, playback approval, signing authority,
resumable upload, scheduling or a real A9 pilot.

No network, third-party media, signing secret, real owner signature or YouTube.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.branch3_original_arcade_pilots import (
    CATALOG, CHANNEL, ROOT, sha, validate_catalog
)
from scripts.branch3_original_arcade_qa import (
    OriginalQARejected, probe, validate_episode_report
)

DOMAIN="CLIVOX-A6-ORIGINAL-REVIEW-PACKET-V1"
PACKET_NAME="owner-handoff-quarantined.json"
METADATA_NAME="metadata-preview.json"
MP4="original-review-preview.mp4"
WAV="original-tts-and-procedural-ambience.wav"
SRT="narration-timing-draft.srt"
MANIFEST="review-manifest.json"
TECH_QA="technical-review-qa.json"
HEX=re.compile(r"[0-9a-f]{64}\Z")


class OriginalHandoffDenied(ValueError):
    pass


def require(ok:bool,code:str)->None:
    if not ok:
        raise OriginalHandoffDenied("CLIVOX_A6_ORIGINAL_DENY_"+code)


def canonical(value:dict)->bytes:
    require(type(value) is dict,"CANONICAL_OBJECT")
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False).encode("utf-8")


def digest(value:dict)->str:
    return hashlib.sha256(canonical(value)).hexdigest()


def review_metadata(episode:dict,render_mode:str)->dict:
    require(type(episode) is dict
            and episode.get("format") in ("short","long")
            and render_mode in ("preview","full"),
            "METADATA_INPUT")
    return {
        "schema_version":1,
        "channel_id":CHANNEL,
        "episode_id":episode["id"],
        "title":episode["title"],
        "description":episode["description"],
        "format":episode["format"],
        "render_mode":render_mode,
        "declaration":"ORIGINAL_FICTIONAL_ARCADE_SHOW_NOT_REAL_GAMEPLAY",
        "youtube_visibility":"NOT_UPLOADED",
        "youtube_upload_or_publish_authorized":False,
    }


def validate_folder(folder:Path)->None:
    require(isinstance(folder,Path) and folder.is_absolute()
            and folder.is_dir() and not folder.is_symlink()
            and folder!=ROOT and ROOT not in folder.parents,
            "REVIEW_FOLDER_LOCATION")
    for name in (MP4,WAV,SRT,MANIFEST,TECH_QA):
        path=folder/name
        require(path.is_file() and not path.is_symlink()
                and path.parent==folder,
                "MISSING_OR_LINKED_REVIEW_FILE_"+name)
        require(0<path.stat().st_size<300_000_000,
                "REVIEW_FILE_BOUNDS_"+name)


def read_json(file:Path)->dict:
    require(file.stat().st_size<200_000,"JSON_TOO_LARGE")
    result=json.loads(file.read_text("utf-8"))
    require(type(result) is dict,"JSON_OBJECT")
    return result


def build_packet(episode:dict,folder:Path,*,catalog_sha256:str)->tuple[dict,dict]:
    """Compute from real bytes. Existing JSON 'passed' flags are never trusted."""
    validate_folder(folder)
    require(type(catalog_sha256) is str
            and HEX.fullmatch(catalog_sha256) is not None,
            "CATALOG_SHA")
    manifest=read_json(folder/MANIFEST)
    existing_qa=read_json(folder/TECH_QA)
    video=folder/MP4
    audio=folder/WAV
    captions=folder/SRT
    report=validate_episode_report(
        episode,manifest,probe(video),captions.read_text("utf-8"),
        video=video,audio=audio,captions=captions
    )
    require(report==existing_qa,"ACTUAL_QA_REPORT_CHANGED")
    metadata=review_metadata(episode,manifest["render_mode"])
    pkt={
        "schema_version":1,
        "domain":DOMAIN,
        "channel_id":CHANNEL,
        "episode_id":episode["id"],
        "format":episode["format"],
        "render_mode":manifest["render_mode"],
        "exact_video_file":MP4,
        "exact_video_sha256":sha(video),
        "exact_video_size_bytes":video.stat().st_size,
        "exact_audio_sha256":sha(audio),
        "exact_captions_sha256":sha(captions),
        "exact_catalog_sha256":catalog_sha256,
        "exact_metadata_sha256":digest(metadata),
        "independent_ffprobe_qa_sha256":digest(report),
        "asset_claim":"FIRST_PARTY_SCRIPTED_FICTION_NO_BORROWED_GAMEPLAY",
        "draft_synthetic_voice_needs_human_review":True,
        "captions_need_actual_voice_alignment_review":True,
        "exact_video_human_review_confirmed":False,
        "rights_of_all_final_assets_independently_approved":False,
        "owner_signing_identity_enrolled":False,
        "owner_detached_signature_present":False,
        "trusted_revocation_head_verified":False,
        "actual_owner_release_id":None,
        "actual_publish_at_utc":None,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "real_google_api_calls":0,
    }
    pkt["packet_sha256"]=digest(pkt)
    return pkt,metadata


def verify_packet(episode:dict,folder:Path,packet:dict,
                  metadata:dict,*,catalog_sha256:str)->dict:
    require(type(packet) is dict and type(metadata) is dict,
            "HANDOFF_JSON_TYPE")
    rebuilt,expected_meta=build_packet(
        episode,folder,catalog_sha256=catalog_sha256
    )
    require(metadata==expected_meta,"METADATA_CHANGED")
    require(packet==rebuilt,"PACKET_CHANGED_OR_STALE")
    require(packet["packet_sha256"]==digest({
        k:v for k,v in packet.items() if k!="packet_sha256"
    }),"PACKET_DIGEST")
    return {
        "stage":"A6_ORIGINAL_EXACT_FILE_HANDOFF_QUARANTINED",
        "episode_id":episode["id"],
        "actual_video_files_sha256_technically_verified":True,
        "narration_caption_and_artifact_provenance_checked":True,
        "independent_ffprobe_qa_recomputed":True,
        "review_packet_sha256":packet["packet_sha256"],
        "owner_review_and_approval_completed":False,
        "owner_signing_key_independently_enrolled":False,
        "signed_exact_video_release_exists":False,
        "commercial_rights_of_final_assets_approved":False,
        "licensed_creator_clips_verified":0,
        "real_clivox_oauth_available":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "real_google_api_calls":0,
    }


def generate_all(directory:Path,*,selection:str)->dict:
    require(selection in ("one","all"),"SELECTION")
    require(isinstance(directory,Path) and directory.is_absolute()
            and directory.is_dir() and not directory.is_symlink()
            and directory!=ROOT and ROOT not in directory.parents,
            "OUTPUT_DIRECTORY")
    source=json.loads(CATALOG.read_text("utf-8"))
    episodes=validate_catalog(source)
    if selection=="one":
        episodes=episodes[:1]
    outputs=[]
    for episode in episodes:
        folder=directory/episode["id"]
        pkt,metadata=build_packet(
            episode,folder,catalog_sha256=sha(CATALOG)
        )
        require(not (folder/PACKET_NAME).exists()
                and not (folder/METADATA_NAME).exists(),
                "NO_OVERWRITE_EXISTING_OWNER_HANDOFF")
        (folder/METADATA_NAME).write_text(
            json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
        (folder/PACKET_NAME).write_text(
            json.dumps(pkt,indent=2)+"\n",encoding="utf-8")
        outputs.append(verify_packet(
            episode,folder,read_json(folder/PACKET_NAME),
            read_json(folder/METADATA_NAME),
            catalog_sha256=sha(CATALOG)
        ))
    return {
        "stage":"A6_ORIGINAL_FIRST_PARTY_EXACT_MEDIA_HANDOFF_ONLY",
        "episodes_handed_to_owner_review":len(outputs),
        "episode_reports":outputs,
        "all_review_packets_quarantined":True,
        "no_owner_key_or_review_auto_approved":True,
        "actual_google_write_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def fixture()->dict:
    return {
        "stage":"A6_ORIGINAL_HANDOFF_OFFLINE_CONTRACT_NO_REAL_VIDEO",
        "channel_id":CHANNEL,
        "exact_file_handoff_code_implemented":True,
        "actual_human_review_signed":False,
        "production_owner_public_key_enrolled":False,
        "licensed_creator_grants_verified":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "google_api_calls":0,
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("fixture","build"),default="fixture")
    p.add_argument("--selection",choices=("one","all"),default="one")
    p.add_argument("--directory",type=Path)
    args=p.parse_args()
    if args.mode=="fixture":
        result=fixture()
    else:
        require(args.directory is not None,"DIRECTORY_REQUIRED")
        result=generate_all(args.directory,selection=args.selection)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
