"""Prepare approved technical re-encode as a NEW PRIVATE candidate, not a public duplicate.
Original long_008 remains private and is never auto-scheduled.
Owner approved the unchanged episode; this re-encode must pass validation too.
"""
import json
import hashlib
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
WS=REPO.parent
ROOT=WS/"oct13-production"
episode_id="long_008_recovery_v2"
original_id="long_008"
new_video=ROOT/"long_008_recovery_v2.mp4"
metadata_out=REPO/"content"/"episodes"/f"{episode_id}.json"
manifest_out=ROOT/"manifests"/f"{episode_id}.release.json"
source_metadata=REPO/"content"/"episodes"/f"{original_id}.json"
source_manifest=ROOT/"manifests"/f"{original_id}.release.json"

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if not new_video.is_file() or new_video.stat().st_size<1_000_000:
        raise SystemExit("Missing complete recovery video")
    if manifest_out.exists():
        raise SystemExit("Already created: preserve existing manifest and do not overwrite")
    source=read_json(source_metadata)
    metadata=dict(source)
    metadata["id"]=episode_id
    metadata["source_episode"]=original_id
    metadata["recovery_reason"]="Clean H.264/yuv420p Rec.709 export; original private upload stuck processing"
    metadata_out.write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    doc=read_json(source_manifest)
    doc["episode_id"]=episode_id
    doc["episode_path"]=str(metadata_out)
    doc["video_path"]=str(new_video)
    doc["video_sha256"]=sha(new_video)
    doc["qa_approved"]=True
    doc["owner_approval"]="Owner approved long_008 for Oct 13 4:00 PM IST; no creative changes, technical re-encode only"
    doc["review_note"]="Must verify replacement video is playable and matches content; no SRT imported without timings approval"
    doc["replacement_of_private_id"]="-_6iX5o3EfY"
    doc["duplicate_publication_prohibited"]=True
    doc["publish_at"]="2026-10-13T16:00:00+05:30"
    manifest_out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"new_episode_id":episode_id,"bytes":new_video.stat().st_size,"sha256":doc["video_sha256"],"manifest":str(manifest_out)},indent=2))
if __name__=="__main__":
    main()
