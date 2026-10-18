"""Manual YouTube dispatch validation — NO API, OAuth, upload or billing.

The legacy workflow interpolated untrusted workflow_dispatch inputs directly
into Bash. Only evaluate user inputs as environment data; reject traversal,
shell metacharacters, symlinks, unsafe receipt paths, mismatched identifiers,
and public/unlisted privacy until owner explicitly approves a separate release.

This module never grants publication. It is designed for an INACTIVE DRAFT
workflow and may be tested offline with no YouTube credentials.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re

SAFE_BASENAME=re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
EPISODE_ID=re.compile(r"[a-z0-9][a-z0-9_-]{2,63}\Z")
REQUIRED=(
    "EPISODE_PATH","SOURCE_RUN_ID","ARTIFACT_NAME","VIDEO_FILE",
    "CAPTIONS_FILE","THUMBNAIL_FILE","RECEIPT_PATH","PRIVACY",
)


def _filename(value:str,suffix:str)->str:
    if (not isinstance(value,str) or
            not SAFE_BASENAME.fullmatch(value) or
            ".." in value or value.startswith(".") or
            not value.lower().endswith(suffix)):
        raise ValueError("Invalid bounded artifact filename")
    return value


def validate_dispatch_inputs(env:dict)->dict:
    if not isinstance(env,dict) or any(k not in env for k in REQUIRED):
        raise ValueError("Incomplete private-pilot dispatch inputs")
    run=env["SOURCE_RUN_ID"]
    if (not isinstance(run,str) or not re.fullmatch(r"[1-9][0-9]{0,17}",run)):
        raise ValueError("Invalid GitHub Actions numeric source run ID")
    artifact=_filename(env["ARTIFACT_NAME"],suffix="")  # safe basename
    video=_filename(env["VIDEO_FILE"],suffix=".mp4")
    captions=_filename(env["CAPTIONS_FILE"],suffix=".srt")
    thumbnail=_filename(env["THUMBNAIL_FILE"],suffix=".png")
    episode=env["EPISODE_PATH"]
    receipt=env["RECEIPT_PATH"]
    if not isinstance(episode,str) or not isinstance(receipt,str):
        raise ValueError("Invalid episode/receipt paths")
    if not episode.startswith("content/episodes/") or not episode.endswith(".json"):
        raise ValueError("Episode metadata must be in its fixed repository folder")
    if not receipt.startswith("state/published/") or not receipt.endswith(".json"):
        raise ValueError("Receipt must stay in its fixed repository folder")
    episode_name=episode.removeprefix("content/episodes/").removesuffix(".json")
    receipt_name=receipt.removeprefix("state/published/").removesuffix(".json")
    if (not EPISODE_ID.fullmatch(episode_name) or episode_name!=receipt_name):
        raise ValueError("Episode and receipt ID must match a bounded identifier")
    if env["PRIVACY"]!="private":
        raise ValueError("Only a separately owner-approved PRIVATE upload may be piloted")
    return {
        "episode":episode,"receipt":receipt,"source_run_id":run,
        "artifact":artifact,"video":video,"captions":captions,
        "thumbnail":thumbnail,"privacy":"private",
        "publishing_authorized":False,
    }


def validate_downloaded_files(environ:dict,folder:Path)->None:
    values=validate_dispatch_inputs(environ)
    path=Path(folder)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Real existing incoming artifact folder required")
    root=path.resolve()
    for field in ("video","captions","thumbnail"):
        file=root/values[field]
        if (file.is_symlink() or not file.is_file()
                or file.resolve().parent != root
                or not 0<file.stat().st_size<=500_000_000):
            raise ValueError("Downloaded artifact missing, oversized, symlinked or untrusted")


def main()->int:
    parser=argparse.ArgumentParser(description="Offline fail-closed dispatch gate")
    parser.add_argument("--check-artifact-root",type=Path)
    args=parser.parse_args()
    if args.check_artifact_root is None:
        validate_dispatch_inputs(os.environ)
    else:
        validate_downloaded_files(os.environ,args.check_artifact_root)
    print("PRIVATE_PILOT_DISPATCH_STRUCTURAL_GATE_ONLY__NO_RELEASE_APPROVAL")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
