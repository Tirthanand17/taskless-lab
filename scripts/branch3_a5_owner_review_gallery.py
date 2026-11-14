"""Build an offline premium CLIVOX review gallery from REAL original media.

This human-friendly HTML travels INSIDE GitHub review artifacts, links only
relative MP4 + SRT, and includes exact owner-handoff SHA values. It never
collects or records owner consent, creates signatures, requests the network,
downloads source clips, or reaches YouTube. Every video remains unapproved.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

from scripts.branch3_a6_original_handoff import (
    CATALOG, ROOT, PACKET_NAME, METADATA_NAME, read_json, sha
)
from scripts.branch3_a6_original_review_signature import (
    CHECKS, REQUEST_FILE, verify_unsigned_requests
)
from scripts.branch3_original_arcade_pilots import validate_catalog

OUTPUT="CLIVOX-REVIEW-START-HERE.html"
VIDEO="original-review-preview.mp4"
SRT="narration-timing-draft.srt"
CSS="""
:root{color-scheme:dark;--bg:#090d17;--card:#151e2d;--edge:#364253;--text:#f0f4f9;--muted:#aab5c5;--orange:#ff762e}
*{box-sizing:border-box}html{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--text)}
body{margin:0;padding:clamp(16px,4vw,48px);line-height:1.48;max-width:1500px;margin-inline:auto}
.brand{font-size:clamp(28px,5vw,48px);font-weight:900;letter-spacing:.13em;color:#f7faff}
.brand span{color:var(--orange)}
.eyebrow{color:var(--orange);font-size:13px;font-weight:800;letter-spacing:.17em;text-transform:uppercase}
h1{font-size:clamp(23px,3.6vw,42px);line-height:1.17;margin:14px 0}
h2{font-size:clamp(20px,2.5vw,29px);line-height:1.26;margin:9px 0}
.intro{max-width:860px;color:var(--muted);font-size:clamp(15px,1.4vw,18px)}
.notice{border:1px solid #9a5f31;background:#251c19;border-radius:16px;padding:17px;margin:26px 0;color:#ffdfc0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,360px),1fr));gap:22px}
article{background:var(--card);border:1px solid var(--edge);border-radius:20px;padding:19px;min-width:0}
article p{color:var(--muted)}.player{display:grid;place-items:center;background:#02040a;border-radius:12px;padding:12px;min-height:200px}
video{display:block;width:100%;max-height:520px;object-fit:contain;border-radius:9px;background:#000}
.pill{font-size:11px;letter-spacing:.09em;color:#ffce9b;background:#422619;padding:6px 10px;border-radius:999px;display:inline-block}
.meta{font-size:13px;margin:12px 0;color:#b3c2d4}
a{color:#ffb37a;text-decoration:underline;text-underline-offset:3px}
code{font-size:12px;overflow-wrap:anywhere;color:#c5d5e8}
details{border-top:1px solid var(--edge);margin-top:18px;padding-top:12px}
summary{color:var(--orange);cursor:pointer;font-weight:700}
ul{padding-left:22px}li{margin:8px 0}
footer{color:var(--muted);font-size:12px;margin:40px 0 0}
strong{color:#fff}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
"""


class GalleryBlocked(ValueError):
    pass


def require(ok:bool,reason:str)->None:
    if not ok:
        raise GalleryBlocked("CLIVOX_OWNER_GALLERY_DENIED_"+reason)


def safe(text:str)->str:
    require(type(text) is str and len(text)<3000,"UNSAFE_HTML_TEXT")
    return escape(text,quote=True)


def make_gallery(directory:Path,*,selection:str)->dict:
    require(selection in ("one","all"),"SELECT")
    require(isinstance(directory,Path) and directory.is_absolute()
            and directory.is_dir() and not directory.is_symlink()
            and ROOT not in directory.parents and directory!=ROOT,
            "OUTSIDE_PUBLIC_GIT_TREE")
    proof=verify_unsigned_requests(directory,selection=selection)
    require(proof["all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed"]
            and proof["actual_human_video_approvals_verified"]==0
            and proof["youtube_upload_authorized"] is False,
            "OWNER_APPROVAL_UNTRUSTED")
    catalog=validate_catalog(json.loads(CATALOG.read_text("utf-8")))
    selected=catalog[:1] if selection=="one" else catalog
    target=directory/OUTPUT
    require(not target.exists() and not target.is_symlink(),
            "NO_REPLACE_EXISTING_GALLERY")
    cards=[]
    for episode in selected:
        folder=directory/episode["id"]
        packet=read_json(folder/PACKET_NAME)
        meta=read_json(folder/METADATA_NAME)
        form=read_json(folder/REQUEST_FILE)
        require(all(form["owner_review_checks"][name] is False
                    for name in CHECKS),"NO_REVIEW_COMPLETED")
        require(meta["title"]==episode["title"]
                and meta["description"]==episode["description"]
                and meta["youtube_visibility"]=="NOT_UPLOADED",
                "VIDEO_NOT_A_PUBLISHED_ASSET")
        video_file=folder/VIDEO
        sub_file=folder/SRT
        require(video_file.is_file() and not video_file.is_symlink()
                and sub_file.is_file() and not sub_file.is_symlink()
                and sha(video_file)==packet["exact_video_sha256"]
                and sha(sub_file)==packet["exact_captions_sha256"],
                "MEDIA_HAS_CHANGED")
        name=safe(episode["title"])
        description=safe(episode["description"])
        local_video=safe(episode["id"]+"/"+VIDEO)
        local_srt=safe(episode["id"]+"/"+SRT)
        digest=safe(packet["exact_video_sha256"])
        format_label=safe(
            ("Vertical Short" if episode["format"]=="short"
             else "Landscape Episode")+" · "+str(episode["duration_seconds"])+" s"
        )
        checklist="".join(
            "<li>Not yet reviewed: "+safe(key.replace("_"," ").capitalize())+"</li>"
            for key in CHECKS
        )
        cards.append(f"""
<article>
  <span class="pill">UNSIGNED · NOT PUBLISHED</span>
  <p class="meta">{format_label}</p>
  <h2>{name}</h2>
  <div class="player"><video controls playsinline preload="metadata"
      src="{local_video}" aria-label="Preview: {name}"></video></div>
  <p>{description}</p>
  <p><a href="{local_video}" download>Save original MP4 review copy</a>
  · <a href="{local_srt}" download>Open draft SRT captions</a></p>
  <details><summary>Exact video SHA-256 and pending owner checks</summary>
    <p><code>{digest}</code></p>
    <ul>{checklist}</ul>
    <p>Final voice, captions, commercial rights and signer identity
       have not been independently approved.</p>
  </details>
</article>
""")
    markup="""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>CLIVOX — Original Arcade Owner Review (UNSIGNED)</title>
<style>"""+CSS+"""</style></head>
<body>
<div class="brand">CLI<span>VOX</span></div>
<div class="eyebrow">Original arcade · Exact-media owner review pack</div>
<h1>Watch the entire videos before deciding anything.</h1>
<p class="intro">These are original fictional interactive gaming challenges,
not footage of GTA or a real game. Every file has been independently checked
against its exact SHA-256 handoff and an unapproved owner checklist.</p>
<section class="notice"><strong>Human review required — no video is approved.</strong>
The voice is a synthetic draft; captions are estimated and not word-aligned.
This offline HTML cannot record review, create a signature, grant commercial
rights or upload to YouTube. Open this file from the extracted artifact ZIP
so the video paths work. Do not publish these preview masters.</section>
<section class="grid" aria-label="Original CLIVOX episode preview cards">
"""+("\n".join(cards))+"""
</section>
<footer>Source-free GitHub Actions review artifact · no JavaScript · no external
fonts, scripts, network assets, OAuth or playback analytics.
CLIVOX channel: UCfPEvy0SefE_5nNlYlY_CyQ · Automatic publishing is OFF.</footer>
</body></html>
"""
    require("<script" not in markup.lower() and
            "http://" not in markup.lower() and
            "https://" not in markup.lower()
            and "fetch(" not in markup.lower()
            and len(cards)==len(selected),"OFFLINE_ONLY_AND_COUNTS")
    target.write_text(markup,encoding="utf-8")
    return {
        "stage":"A5_A6_CLIVOX_OFFLINE_OWNER_REVIEW_GALLERY_UNAPPROVED",
        "episode_count":len(selected),
        "html_file":OUTPUT,
        "actual_video_audio_srt_and_unsigned_reverified":True,
        "only_relative_local_mp4_srt_links":True,
        "no_remote_assets_or_browser_scripts":True,
        "human_editorial_review_completed":False,
        "real_owner_release_signed":False,
        "commercial_music_voice_tool_licenses_approved":False,
        "actual_google_api_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def fixture()->dict:
    return {
        "stage":"A5_A6_OFFLINE_GALLERY_CODE_ONLY_NOT_VIDEO_RENDER",
        "can_build_verified_local_html_review_gallery":True,
        "real_review_gallery_produced_in_fixture":False,
        "actual_owner_signature_verified":False,
        "human_video_review_completed":False,
        "actual_google_api_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
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
        require(args.directory is not None,"DIRECTORY")
        result=make_gallery(args.directory,selection=args.selection)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
