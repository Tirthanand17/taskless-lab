"""Read-only YouTube confirmation and exact-ID FlowMinute release-ledger sync.

Never uploads, edits, or schedules anything on YouTube. Requires the existing
owner read-only token stored in the ACL-protected workspace private folder.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from datetime import timedelta

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE = WORKSPACE / ".flowminute-private"
sys.path.insert(0, str(WORKSPACE / "flowminute-publisher-worktree" / "scripts"))
import youtube_publisher as publisher

EXPECTED = {
    "pilot_015": ("oN2PgprMbSE", "2026-10-12T11:00:00+05:30"),
    "long_007": ("jbfNmbl3owA", "2026-10-12T16:00:00+05:30"),
    "pilot_016": ("XEV1fz-75-M", "2026-10-12T20:30:00+05:30"),
}
CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
NOW = datetime.now(timezone.utc)
CHECKED_LOCAL = NOW.astimezone(timezone(timedelta(hours=5, minutes=30))).isoformat(timespec="seconds")

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, value):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)

def main():
    api = publisher.youtube_client(PRIVATE / "youtube_readonly_token.json", writable=False)
    ids = [v[0] for v in EXPECTED.values()]
    result = api.videos().list(part="status,snippet", id=",".join(ids), maxResults=50).execute()
    videos = {x["id"]: x for x in result.get("items", [])}
    if set(videos) != set(ids):
        raise SystemExit("Refusing ledger write: some expected videos were not returned")
    # Validate every record before writing any of them.
    updates = []
    for episode, (yt_id, due_local) in EXPECTED.items():
        item = videos[yt_id]
        status = item.get("status", {})
        if status.get("privacyStatus") != "public" or status.get("uploadStatus") != "processed":
            raise SystemExit(f"Refusing ledger write: {episode} not confirmed PUBLIC/processed")
        if item.get("snippet", {}).get("channelId") != CHANNEL:
            raise SystemExit(f"Refusing ledger write: {episode} channel mismatch")
        if NOW < datetime.fromisoformat(due_local).astimezone(timezone.utc):
            raise SystemExit(f"Refusing ledger write: {episode} not yet due")
        for group in ("planned", "scheduled"):
            path = ROOT / "state" / group / (episode + ".json")
            data = load(path)
            if data.get("youtube_video_id") != yt_id:
                raise SystemExit(f"Refusing ledger write: {path} video ID mismatch")
            updates.append((path, data, episode, yt_id, item))
    receipt = []
    for path, data, episode, yt_id, item in updates:
        data["status"] = "public_verified"
        data["public_verified_at_local"] = CHECKED_LOCAL
        data["no_duplicate_upload"] = True
        evidence = {
            "checked_at_local": CHECKED_LOCAL,
            "existing_youtube_id": yt_id,
            "authenticated_youtube_api_privacy": "public",
            "authenticated_youtube_api_upload_status": "processed",
            "expected_channel_id_matches": True,
            "source": "YouTube Data API read-only videos.list(status,snippet) on authorized Nirala device",
            "full_video_playback_tested": False,
            "duplicate_upload": False,
        }
        data["authenticated_api_release_verification_2026_10_12"] = evidence
        if episode == "pilot_016":
            data["public_playability"] = "api_public_processed_player_not_independently_checked"
        elif data.get("public_playability") != "public_verified":
            data["public_playability"] = "api_public_processed_player_not_independently_checked"
        save(path, data)
        if path.parent.name == "scheduled":
            receipt.append({"episode": episode, "youtube_video_id": yt_id, "title": item["snippet"].get("title"), "privacy": "public", "upload_status": "processed"})
    pack = ROOT / "state" / "planned" / "oct12-pack.json"
    if pack.exists():
        data = load(pack)
        for entry in data.get("entries", []):
            if entry.get("id") in EXPECTED:
                if entry.get("youtube_id") != EXPECTED[entry["id"]][0]:
                    raise SystemExit("Refusing pack update: YouTube ID mismatch")
                entry["status"] = "public_verified"
        data["status"] = "all_public_verified"
        data["public_verified_at_local"] = CHECKED_LOCAL
        save(pack, data)
    reconciliation = ROOT / "state" / "reconciliation" / "2026-10-12-api-public-complete.json"
    save(reconciliation, {
        "checked_at_local": CHECKED_LOCAL, "source": "authenticated read-only YouTube Data API",
        "channel_id": CHANNEL, "videos": receipt, "no_duplicate_upload": True,
        "full_video_playback_tested": False,
    })
    print(json.dumps({"result":"all_three_public_and_processed","checked_at_local":CHECKED_LOCAL,"videos":receipt},indent=2))

if __name__ == "__main__":
    main()
