"""Audit 2026-11-02 three-video release media without uploading to YouTube.

Takes EXACT owner-reviewed GitHub Actions staging downloads. Fails on mismatched
hash, clip duration, stream shape, caption text or timing. Does not alter approval
flags, use any token or invoke a production publisher.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RELEASES = (
    ("en", "fm_20261102_agent_permissions_short_en",
     "FLOWMINUTE_ENGLISH_V6_AUDIO_MASTER_REVIEW_ONLY.mp4",
     "flow-explain-english-phrase-captions.srt",
     "1f1a740002aa035a1eaed8c7a308831efe0ea6a8950c61337ceaafda3a9386fc", 1080, 1920, 896, 13),
    ("hi", "fm_20261102_agent_permissions_short_hi",
     "FLOWMINUTE_HINDI_V2_AUDIO_MASTER_REVIEW_ONLY.mp4",
     "flow-explain-hindi-phrase-captions.srt",
     "ba27ed6b3af872b3c5973f4b371c6ff8abfb7885929def88d9e16dc890c0f772", 1080, 1920, 1112, 13),
    ("long", "fm_20261102_agent_permissions_long_hi",
     "FLOWMINUTE_HI_LONG_AUDIO_MASTER_REVIEW_ONLY.mp4",
     "hindi-long-captions.srt",
     "05cd121643df040727b9e8490341c4bf6e881d27728edea42e3c2de8aa16a213", 1920, 1080, 3737, 29),
)

def sec(s: str) -> float:
    match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", s)
    if not match:
        raise ValueError("Invalid SRT time: " + repr(s))
    h, m, seconds, ms = map(int, match.groups())
    return 3600 * h + 60 * m + seconds + ms / 1000

def get_captions(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    chunks = re.split(r"\n\s*\n", text.strip())
    result = []
    for n, chunk in enumerate(chunks, 1):
        lines = chunk.splitlines()
        if len(lines) < 3 or lines[0].strip() != str(n):
            raise ValueError("Missing/nonsequential SRT caption " + str(n))
        timing = re.fullmatch(r"([^ ]+) --> ([^ ]+)", lines[1].strip())
        if not timing:
            raise ValueError("Invalid SRT timestamp " + str(n))
        a, b = map(sec, timing.groups())
        if a >= b:
            raise ValueError("Invalid SRT range " + str(n))
        result.append({"start": a, "end": b, "text": " ".join(lines[2:]).strip()})
    return result

def check(root: Path) -> dict:
    items=[]
    for folder, name, video, captions, expected, width, height, frames, n in RELEASES:
        ep = json.loads((PROJECT / "content/episodes" / (name + ".json")).read_text())
        approval = json.loads((PROJECT / "state/approvals" / (name + ".json")).read_text())
        source = root / folder
        clip = source / video
        track = source / captions
        assert clip.is_file() and track.is_file(), (clip, track)
        digest = hashlib.sha256(clip.read_bytes()).hexdigest()
        assert digest == expected, ("SHA mismatch", name, digest)
        assert approval["candidate_video_sha256"] == digest
        assert approval.get("owner_publish_authorized") is True
        assert approval.get("youtube_uploaded") is False
        assert ep["id"] == name
        assert ep["language"] == ("en" if folder == "en" else "hi")
        manifest_cues=ep["captions"]
        srt_cues=get_captions(track)
        assert len(manifest_cues) == len(srt_cues) == n
        for idx, (x, y) in enumerate(zip(manifest_cues, srt_cues), 1):
            assert x["text"] == y["text"], ("Caption text differs", name, idx)
            assert abs(float(x["start"])-y["start"])<0.005,("Caption start differs",name,idx)
            assert abs(float(x["end"])-y["end"])<0.005,("Caption end differs",name,idx)
        probe=subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "stream=codec_type,codec_name,width,height,nb_frames","-of","json",str(clip)],
            capture_output=True,text=True,check=True)
        streams=json.loads(probe.stdout)["streams"]
        v=next(s for s in streams if s["codec_type"]=="video")
        a=next(s for s in streams if s["codec_type"]=="audio")
        assert (v["width"],v["height"],int(v["nb_frames"]))==(width,height,frames)
        assert v["codec_name"]=="h264" and a["codec_name"]=="aac"
        from scripts.publish_youtube import approval_allows_exact_video
        blocked=not approval_allows_exact_video(approval,digest)
        assert blocked, "Independent rights/voice/factual review unexpectedly granted"
        items.append({"id":name,"sha256":digest,"frames":frames,"srt_cues":n,
                      "exact_media_and_captions_verified":True,
                      "youtube_release_blocked":True,"youtube_video_id":None})
        print("PASS_EXACT_STAGED_MEDIA_AND_CAPTIONS",name,digest)
    return {"status":"THREE_RELEASES_MEDIA_PREFLIGHT_OK_PUBLICATION_BLOCKED",
            "youtube_uploads":0,"staged_count":len(items),"items":items}

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: verify_nov02_three_staged_releases.py /staged/root")
    report=check(Path(sys.argv[1]))
    Path("three_video_release_preflight_20261102.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NO_YOUTUBE_SECRETS_OR_UPLOADS_EXECUTED")
