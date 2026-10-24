"""Safely inspect Google Flow Google Takeout archives without unzipping unrelated data.

Flow Takeout exports media/<id>.mp4 and media/<id>_metadata.json. This
accepts an EXPLICIT media_id-to-storyboard mapping; never guesses release
identity from AI-generated prompts. No cloud API, credentials, spending, or uploads.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path, PurePosixPath
import json
import os
import re
import shutil
import stat
import tempfile
import zipfile

MAX_ARCHIVE=3_000_000_000
MAX_EXPANDED=5_000_000_000
MAX_MEDIA=250_000_000
MAX_METADATA=2_000_000
MEDIA_ID=re.compile(r"[A-Za-z0-9_-]{4,96}")
EPISODE_ID=re.compile(r"fm_[a-z0-9_]{5,80}")
CLIP_ID=re.compile(r"[A-Za-z0-9_-]{1,32}")


class FlowTakeoutError(ValueError):
    pass


@dataclass(frozen=True)
class TakeoutEvidence:
    episode_id: str
    clip_id: str
    media_id: str
    status: str
    file_name: str | None
    media_sha256: str | None
    media_size_bytes: int | None
    paired_metadata_found: bool
    metadata_key_names: tuple[str, ...]
    issues: tuple[str, ...]
    source_independently_authenticated: bool = False
    visual_quality_verified: bool = False
    natural_voice_verified: bool = False
    licensing_verified: bool = False
    publication_authorized: bool = False
    youtube_scheduled: bool = False


def demand(ok: bool, message: str):
    if not ok:
        raise FlowTakeoutError(message)


def check_mapping(mapping):
    demand(isinstance(mapping,list) and 1 <= len(mapping) <= 50,
           "Use 1-50 explicit Flow media mappings")
    seen_clip=set()
    seen_media=set()
    for entry in mapping:
        demand(isinstance(entry,dict), "Invalid mapping")
        ep,clip,media=entry.get("episode_id"),entry.get("clip_id"),entry.get("media_id")
        demand(isinstance(ep,str) and EPISODE_ID.fullmatch(ep) is not None,
               "Invalid episode")
        demand(isinstance(clip,str) and CLIP_ID.fullmatch(clip) is not None,
               "Invalid clip")
        demand(isinstance(media,str) and MEDIA_ID.fullmatch(media) is not None,
               "Invalid Flow media ID")
        demand((ep,clip) not in seen_clip and media not in seen_media,
               "Duplicate clip or Flow media ID")
        seen_clip.add((ep,clip))
        seen_media.add(media)


def open_verified_archive(archive):
    path=Path(archive)
    demand(path.is_file() and not path.is_symlink() and path.suffix.lower()==".zip",
           "Existing real Takeout ZIP required")
    demand(0 < path.stat().st_size <= MAX_ARCHIVE, "Archive size exceeds limit")
    try:
        zf=zipfile.ZipFile(path)
        items=zf.infolist()
        demand(len(items) <= 10000, "Too many ZIP members")
        index={}
        total=0
        for item in items:
            name=item.filename
            demand(bool(name) and len(name)<=500 and "\\" not in name
                   and "\x00" not in name and not name.startswith("/")
                   and re.match(r"^[a-zA-Z]:",name) is None
                   and ".." not in PurePosixPath(name).parts,
                   "Unsafe archive entry path")
            if item.is_dir():
                continue
            demand(name not in index, "Duplicate ZIP entry")
            demand(not stat.S_ISLNK(item.external_attr >> 16), "ZIP symlink rejected")
            demand(not(item.flag_bits & 1), "Encrypted ZIP member unsupported")
            total+=item.file_size
            demand(total<=MAX_EXPANDED, "Expanded archive too large")
            demand(item.file_size <= (MAX_MEDIA if name.lower().endswith(".mp4") else MAX_EXPANDED),
                   "Oversized ZIP entry")
            if item.file_size>10_000_000:
                demand(item.compress_size>0 and item.file_size/item.compress_size<=500,
                       "Suspicious ZIP compression")
            index[name]=item
        return zf,index
    except Exception:
        if "zf" in locals():
            zf.close()
        raise


def match_media(index,media_id):
    return [path for path in index
            if "media" in PurePosixPath(path).parts
            and PurePosixPath(path).name==media_id+".mp4"]


def scan_flow_takeout(archive, mappings):
    """Read just requested MP4s and paired metadata; never expose prompt text."""
    check_mapping(mappings)
    zf,index=open_verified_archive(archive)
    results=[]
    try:
        for entry in mappings:
            ep,clip,media=(entry["episode_id"],entry["clip_id"],entry["media_id"])
            matches=match_media(index,media)
            issues=[]
            filename=None
            digest=None
            size=None
            meta_keys=()
            paired=False
            if len(matches)!=1:
                issues.append("MISSING_OR_AMBIGUOUS_MEDIA")
            else:
                filename=matches[0]
                asset=index[filename]
                companion=filename[:-4]+"_metadata.json"
                if companion not in index:
                    issues.append("PAIRED_METADATA_MISSING")
                elif index[companion].file_size > MAX_METADATA:
                    issues.append("PAIRED_METADATA_TOO_LARGE")
                else:
                    paired=True
                    try:
                        with zf.open(companion) as stream:
                            md=json.load(stream)
                        demand(isinstance(md,dict), "Metadata not a JSON object")
                        meta_keys=tuple(sorted(k for k in md if isinstance(k,str) and len(k)<=80))
                    except (json.JSONDecodeError,UnicodeDecodeError,ValueError,
                            RecursionError,zipfile.BadZipFile,OSError):
                        issues.append("PAIRED_METADATA_INVALID")
                if asset.file_size<100:
                    issues.append("MP4_TOO_SMALL")
                else:
                    size=asset.file_size
                    try:
                        hasher=sha256()
                        with zf.open(filename) as stream:
                            head=stream.read(20)
                            hasher.update(head)
                            if b"ftyp" not in head[:12]:
                                issues.append("NOT_AN_MP4_HEADER")
                            for block in iter(lambda:stream.read(1024*1024),b""):
                                hasher.update(block)
                        digest=hasher.hexdigest()
                    except (zipfile.BadZipFile,OSError,EOFError):
                        issues.append("MP4_CRC_OR_READ_ERROR")
            results.append(TakeoutEvidence(
                ep,clip,media,"SCAN_PASSED_EDITORIAL_REVIEW_PENDING" if not issues
                else "BLOCKED_TAKEOUT_SCAN",
                PurePosixPath(filename).name if filename else None,digest,
                size,paired,meta_keys,tuple(issues)))
    finally:
        zf.close()
    return results


def import_review_candidates(archive,mappings,destination,package,*,mode="pilot"):
    """Optionally extract matched, fully decoded MP4 candidates into an existing dir.

    Import success is *never* publication approval. No overwrite, rollback on
    failures. Does not extract unrelated personal Takeout archive contents.
    """
    from .flow_cinematic_handoff import build_plan
    from .flow_clip_intake import inspect_flow_clip
    selected=build_plan(package,mode=mode)
    permitted={(x["episode_id"],x["clip_id"]) for x in selected["clips"]}
    check_mapping(mappings)
    demand(all((e["episode_id"],e["clip_id"]) in permitted for e in mappings),
           "Clip ID not in selected Flow production plan")
    scan=scan_flow_takeout(archive,mappings)
    demand(all(not x.issues for x in scan),"Takeout scanner rejected media")
    outdir=Path(destination)
    demand(outdir.is_dir() and not outdir.is_symlink(),
           "Existing safe destination required")
    targets=[outdir/(m["episode_id"]+"__"+m["clip_id"]+"__"+m["media_id"]+".mp4")
             for m in mappings]
    demand(all(not p.exists() and not p.is_symlink() for p in targets),
           "Output already exists")
    zf,index=open_verified_archive(archive)
    written=[]
    approved=[]
    try:
        with tempfile.TemporaryDirectory(prefix="flowminute_takeout_",dir=outdir) as t:
            temp=Path(t)
            for item,target in zip(mappings,targets):
                matching=match_media(index,item["media_id"])
                demand(len(matching)==1,"Takeout changed during import")
                staged=temp/target.name
                with zf.open(matching[0]) as src, staged.open("xb") as dst:
                    shutil.copyfileobj(src,dst,1024*1024)
                evidence=inspect_flow_clip(staged,package,
                   episode_id=item["episode_id"],clip_id=item["clip_id"],
                   mode=mode,source="user_supplied_file")
                demand(evidence.technical_candidate,"Media failed FFmpeg intake")
                matching_scan=next(x for x in scan if x.media_id==item["media_id"])
                demand(evidence.media_sha256==matching_scan.media_sha256,
                       "MP4 checksum differs from ZIP scan")
                approved.append(evidence)
            for target in targets:
                demand(not target.exists() and not target.is_symlink(),
                       "File appeared while importing; refusing overwrite")
                # Same-filesystem hard link never overwrites and is atomic per file.
                os.link(temp/target.name,target)
                written.append(target)
    except Exception:
        for path in written:
            path.unlink(missing_ok=True)
        raise
    finally:
        zf.close()
    return {
        "status":"IMPORTED_MP4S_PENDING_INDEPENDENT_CONTENT_QA",
        "clips_imported":len(approved),
        "file_names":[x.name for x in targets],
        "sha256_values":[x.media_sha256 for x in approved],
        "source_provenance_independently_verified":False,
        "commercial_rights_reviewed":False,
        "natural_voice_and_lip_sync_reviewed":False,
        "publication_authorized":False,
        "youtube_scheduled":False
    }


def redacted_report(results):
    return [asdict(x) for x in results]
