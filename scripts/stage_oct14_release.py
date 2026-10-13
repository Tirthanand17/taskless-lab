"""Stage October 14 release manifests WITHOUT approving or publishing.
The owner must review full narration, the rendered video and captions before
qa_approved may be truthfully set to true. Never attempts a YouTube write.
"""
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parent
OUT = WORKSPACE / "oct14-production"
TARGETS = [
    ("pilot_019", "2026-10-14T11:00:00+05:30"),
    ("long_009", "2026-10-14T16:00:00+05:30"),
    ("pilot_020", "2026-10-14T20:30:00+05:30"),
]
CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    dest = OUT / "manifests"
    dest.mkdir(parents=True, exist_ok=True)
    for episode_id, date in TARGETS:
        video = OUT / (episode_id + ".mp4")
        if not video.exists() or video.stat().st_size == 0:
            print(episode_id, "NOT_READY: no video MP4")
            continue
        manifest_path = dest / (episode_id + ".release.json")
        if manifest_path.exists():
            print(episode_id, "EXISTING: not overwriting any prior owner review")
            continue
        metadata = REPO / "content" / "episodes" / (episode_id + ".json")
        manifest = {
            "episode_id": episode_id,
            "episode_path": str(metadata),
            "video_path": str(video),
            "video_sha256": sha256(video),
            "expected_channel_id": CHANNEL,
            "publish_at": date,
            "made_for_kids": False,
            "synthetic_media": False,
            "qa_approved": False,
            "captions_reviewed": False,
            "editorial_review": "PENDING",
            "narration_listening_review": "PENDING",
            "full_video_playback_review": "PENDING",
            "srt_review": "PENDING"
        }
        if episode_id == "long_009":
            thumbnail = OUT / "long_009_thumbnail.jpg"
            if thumbnail.exists():
                manifest["thumbnail_path"] = str(thumbnail)
                manifest["thumbnail_sha256"] = sha256(thumbnail)
        manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
        print(episode_id, "STAGED_NOT_APPROVED:", manifest_path)
if __name__ == "__main__":
    main()
