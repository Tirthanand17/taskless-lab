"""Stage only technically valid Oct14 media, preserve explicit QA/publishing gates."""
from pathlib import Path
import json,datetime
repo=Path(__file__).resolve().parents[1]
out=repo.parent/"oct14-production"
report=json.loads((out/"oct14_technical_qa.json").read_text(encoding="utf-8"))
videos=report["videos"]
assert len(videos)==3 and all(v["technical_pass"] for v in videos)
ids={v["id"] for v in videos}
assert ids=={"pilot_019","long_009","pilot_020"}
planned=repo/"state"/"planned"/"oct14-pack.json"
p=json.loads(planned.read_text(encoding="utf-8-sig"))
for e in p["entries"]:
    v=next(v for v in videos if v["id"]==e["id"])
    e["status"]="technical_qa_passed_full_human_review_pending"
    e["video_sha256"]=v["video_sha256"]
    e["video_bytes"]=v["bytes"]
    e["video_duration_seconds"]=v["duration_seconds"]
    e["approved"]=False
p["status"]="technical_qa_passed_approval_pending"
p["scheduled_in_youtube"]=False
p["technical_qa_report"]="oct14-production/oct14_technical_qa.json"
p["editorial_approval"]="PENDING"
p["full_narration_listening_review"]="PENDING"
p["captions_human_review"]="PENDING"
p["youtube_upload_status"]="NOT_UPLOADED"
p["updated_at_ist"]=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30))).isoformat()
planned.write_text(json.dumps(p,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
lines=[
"# October 14, 2026 — video production technical QA and publication gates",
"",
"**Status: 3 MP4s technically validated, NOT editorial/listening approved and NOT uploaded or scheduled to YouTube.**",
"",
"Authenticated channel: `UCCcL9Q_jqVq6LJmnYUSAFZA`. Video and related files live only under `C:\\Users\\Dell\\Desktop\\youtube con\\oct14-production`.",
"",
"| Video | Target IST October 14 | MP4 length | Resolution | SHA-256 | Technical status |",
"|---|---|---:|---|---|---|",
]
slots={"pilot_019":"11:00","long_009":"16:00","pilot_020":"20:30"}
for v in videos:
    lines.append(f"| {v['id']} | {slots[v['id']]} | {v['duration_seconds']:.2f} s | {v['dimensions']} | `{v['video_sha256']}` | **Pass** |")
lines+=["",
"All MP4 files decoded fully with FFmpeg (H.264 video and AAC audio). Audio peak checks passed below clipping. Source/motion: `motion-v2/src/October14.tsx`. The long custom thumbnail is `oct14-production/long_009_thumbnail.jpg`. Final contact sheets: `oct14-production/pilot_019_contact_FINAL.jpg`, `long_009_contact_FINAL.jpg`, `pilot_020_contact_FINAL.jpg`.",
"",
"Segments `pilot_019` / `pilot_020`: stock human-phone footage credited to RDNE Stock project via Pexels. Long `long_009`: licensed payment stock scene credited to ArtHouse Studio via Pexels. Actual Chrome product screens and actual paid transactions are **not** claimed; all screen mockups clearly say illustrative/concept interface.",
"",
"**Human approval still needed:** Listen to all three complete synthetic voiceovers for naturalness and pronunciation, watch all MP4s end-to-end for timing/crops/content, and review exact subtitles before uploading. Local `captions/*_DRAFT_UNREVIEWED.srt` are NOT aligned and will not be uploaded unreviewed. This report is automated technical validation only, not a claim of human editorial review.",
"",
"Release manifests are staged under `oct14-production/manifests/`, `qa_approved=false` until the owner reviews/approves. **No real YouTube video ID, no schedule receipt, no live upload attempt.** After genuine owner review, publisher sequence: prepare → private upload → thumbnail → schedule → independently verify `publishAt`, ensuring unique content hashes and no duplicates.",
"",
"Growth rationale and official sourcing: [Editorial & growth audit](OCT14_EDITORIAL_AND_GROWTH_AUDIT.md), [Community interaction playbook](OCT14_COMMUNITY_PLAYBOOK.md). No guarantee of increased views/likes/subscribers.",
]
doc=repo/"docs"/"OCT14_RELEASE_READINESS.md"
doc.write_text("\n".join(lines)+"\n",encoding="utf-8")
print("READINESS_RECORDED",doc)
