"""One-command stage and preflight for exactly 4 real cinematic MP4s.

Use only after 3 genuinely new Flow cinematic clips are supplied.
No files are generated, no video upload or YouTube schedule is attempted.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

from autopilot.flow_episode_compositor import (
  validate_manifest, AssemblyError,
  APPROVED_REEXPORTED_OPENING_SHA256
)

FILES=[
 ("asha_jay_opening","Asha_Jay_Approved_8s_Reference.mp4"),
 ("cinematic_02","scene_02_real.mp4"),
 ("cinematic_03","scene_03_real.mp4"),
 ("cinematic_04","scene_04_real.mp4")
]


def make_manifest(folder:Path)->dict:
    if not folder.is_dir() or folder.is_symlink():
        raise AssemblyError("Existing real, non-symlinked media folder required")
    segments=[]
    for name,filename in FILES:
        path=folder/filename
        if not path.is_file() or path.is_symlink() or path.stat().st_size<100000:
            raise AssemblyError(f"Actual original/new video missing or invalid: {filename}")
        with path.open("rb") as h:
            checksum=sha256()
            for part in iter(lambda:h.read(1024*1024),b""):
                checksum.update(part)
        digest=checksum.hexdigest()
        if name=="asha_jay_opening" and digest!=APPROVED_REEXPORTED_OPENING_SHA256:
            raise AssemblyError("Approved original opening MP4 bytes do not match pinned reference")
        segments.append({
          "id":name,"path":str(path.resolve()),
          "sha256":digest,"source_start_ms":0,"duration_ms":8000
        })
    manifest={
      "schema_version":1,
      "episode_id":"fm_20261024_short_en",
      "creative_revision":"cinematic_v2_32s",
      "status":"FOUR_REAL_SOURCES_INTAKED_EDITORIAL_QA_REQUIRED",
      "segments":segments,
      "human_character_consistency_verified":False,
      "human_3d_art_direction_verified":False,
      "voice_approved":False,
      "subtitle_alignment_verified":False,
      "rights_clearance_verified":False,
      "youtube_scheduled":False
    }
    result=validate_manifest(manifest,test_mode=False)
    if not result["full_duration"] or result["assembled_ms"]!=32000:
        raise AssemblyError("Physical source media incomplete or wrong duration")
    return manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",type=Path,required=True,
                   help="Folder with approved 8s opening and 3 real generated Flow MP4 files")
    p.add_argument("--manifest",type=Path,required=True)
    args=p.parse_args()
    if args.manifest.exists() or not args.manifest.parent.is_dir():
        raise SystemExit("Refusing overwrite or nonexistent manifest output folder")
    info=make_manifest(args.directory)
    args.manifest.write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"TECHNICAL_32S_SCENE_INTAKE_PASS_NOT_RELEASE_APPROVED",
      "mp4_count":4,"new_3d_files_received":3,"expected_seconds":32,
      "manifest_file":args.manifest.name,"youtube_scheduled":False},indent=2))


if __name__=="__main__":
    main()
