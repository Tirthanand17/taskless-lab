"""B4e3 explicit opt-in, 1-day ORIGINAL (nonfactual) MP4 owner review exports.

No external publishing. The GitHub Actions workflow may invoke this ONLY on
a human-requested workflow_dispatch run where review_artifacts=true.

The repository may be PUBLIC: GitHub Actions artifacts are downloadable by
any signed-in user with read access. Never label those media files private or
put publisher text, raw research, voices weights, prompts, wav/srt into them.
A review manifest containing only hashes and safe numeric QA travels with the
three ORIGINAL unreviewed educational MP4s.
"""
from __future__ import annotations

from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
import shutil

REPORT_STATUS = "B4E1_FULL_THREE_ORIGINAL_NONFACTUAL_VOICED_REHEARSALS_PHYSICALLY_RENDERED_NOT_PUBLISHABLE"
EXPORT_STATUS = "B4E3_PUBLICLY_READABLE_ONE_DAY_HUMAN_REVIEW_ONLY_NO_PUBLISH"
SLOT_NAMES = (
    ("short_am", "01_MORNING_SHORT_UNAPPROVED_REHEARSAL.mp4", 4),
    ("long", "02_LONG_VIDEO_UNAPPROVED_REHEARSAL.mp4", 9),
    ("short_pm", "03_EVENING_SHORT_UNAPPROVED_REHEARSAL.mp4", 4),
)
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
EPISODE = re.compile(r"[A-Za-z0-9_-]{10,100}\Z")
MAX_VIDEO = 240_000_000
MAX_TOTAL = 360_000_000
ROOT = Path("/tmp/flowminute-b4e1-complete-rehearsals")
TARGET = Path("/tmp/flowminute-b4e3-unapproved-owner-review")


class ReviewExportRefused(ValueError):
    """Fail-closed when media is forged, wrong, unreviewed or public-risky."""


def _read_report(path: Path) -> dict:
    if (path.is_symlink() or not path.is_file() or
        not 200<=path.stat().st_size<=40_000):
        raise ReviewExportRefused("Missing or invalid review QA proof")
    try:
        obj=json.loads(path.read_text(encoding="utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise ReviewExportRefused("Unsafe review QA report") from None
    if not isinstance(obj,dict):
        raise ReviewExportRefused("QA report must be a JSON object")
    return obj


def _sha_file(path: Path) -> tuple[str,int]:
    h=sha256()
    n=0
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            n+=len(part)
            if n>MAX_VIDEO:
                raise ReviewExportRefused("One review video exceeded size ceiling")
            h.update(part)
    return h.hexdigest(),n


def prepare_review_export(root: Path, target: Path, report: dict) -> dict:
    # Never accept a caller-controlled path elsewhere on disk. This ensures
    # the upload cannot include unrelated files or publisher source material.
    if (root!=ROOT or target!=TARGET or root.is_symlink()
        or not root.is_dir() or target.exists() or target.is_symlink()):
        raise ReviewExportRefused("Review export must use expected runner-only paths")
    if (type(report) is not dict
        or report.get("status")!=REPORT_STATUS
        or report.get("full_daily_nonfactual_rehearsal_videos_encoded")!=3
        or report.get("actually_voiced_complete_original_scene_count")!=17
        or report.get("full_4_9_4_scene_voiceover_text_all_spoken") is not True
        or report.get("all_three_real_h264_aac_ffmpeg_full_decodes_passed") is not True
        or report.get("all_17_scenes_with_verified_distinct_one_time_reveal_pngs") is not True
        or report.get("all_three_actual_mp4_first_one_shot_reveal_frames_verified") is not True
        or report.get("all_pcm_timed_subtitles_fit_caption_panels") is not True
        or report.get("all_caption_reading_rates_approved") is not False
        or report.get("rehearsal_only_not_factual_news_or_final_review") is not True
        or report.get("real_news_facts_approved")!=0
        or report.get("rights_approvals")!=0
        or report.get("human_full_watches")!=0
        or report.get("paid_model_provider_calls")!=0
        or report.get("youtube_uploads")!=0
        or report.get("release_authorized") is not False
        or type(report.get("episodes")) is not list
        or len(report["episodes"])!=3):
        raise ReviewExportRefused("Media has no verified 3-video technical/non-release proof")
    target.mkdir(mode=0o700)
    try:
        entries=[]
        total=0
        for (slot,filename,scene_count),item in zip(SLOT_NAMES,report["episodes"]):
            if (type(item) is not dict
                or item.get("slot")!=slot
                or item.get("original_full_scene_count")!=scene_count
                or item.get("all_original_voiceover_paragraphs_physically_spoken") is not True
                or item.get("actual_full_ffmpeg_decode_passed") is not True
                or item.get("srt_caption_baseline_inside_reserved_panel") is not True
                or item.get("no_concentric_spinner_or_continuously_rotating_circle") is not True
                or item.get("first_real_encoded_one_shot_checkpoint_reveal_frame_verified") is not True
                or item.get("source_rights_reviewed") is not False
                or item.get("news_facts_approved") is not False
                or item.get("human_full_audio_visual_watch_completed") is not False
                or item.get("fully_release_ready_for_youtube") is not False
                or item.get("youtube_uploaded") is not False
                or item.get("release_authorized") is not False):
                raise ReviewExportRefused("Forged episode approval or incomplete technical video")
            episode=item.get("episode_id")
            digest=item.get("encoded_h264_aac_sha256")
            original_bytes=item.get("total_actual_encoded_bytes")
            seconds=item.get("real_pcm_measured_seconds")
            if (type(episode) is not str or not EPISODE.fullmatch(episode)
                or type(digest) is not str or not DIGEST.fullmatch(digest)
                or type(original_bytes) is not int or not 300_000<=original_bytes<=MAX_VIDEO
                or type(seconds) not in (int,float) or not 20<=seconds<=340):
                raise ReviewExportRefused("Invalid source video identity/size/duration")
            src=root/episode/"EPHEMERAL_FULL_ORIGINAL_NARRATED_REHEARSAL.mp4"
            if src.is_symlink() or not src.is_file():
                raise ReviewExportRefused("Original decoded video is unavailable")
            actual_hash,actual_size=_sha_file(src)
            if (actual_hash!=digest or actual_size!=original_bytes):
                raise ReviewExportRefused("Actual MP4 bytes mismatch full decoder QA")
            total+=actual_size
            if total>MAX_TOTAL:
                raise ReviewExportRefused("Review artifact exceeds combined safety size")
            dst=target/filename
            # Never follow symlink or glob contents. Copy ONLY three
            # explicitly verified MP4 files and a separate safe README.
            shutil.copyfile(src,dst,follow_symlinks=False)
            entries.append({
                "slot":slot,
                "file":filename,
                "sha256":digest,
                "measured_audio_seconds":seconds,
                "original_voiced_scene_count":scene_count,
                "passed_full_h264_aac_decode":True,
                "all_rights_and_fact_approvals":False,
                "youtube_upload_authorized":False,
            })
        info={
            "status":EXPORT_STATUS,
            "intended_use":"Original synthetic educational rehearsal video for human visual/audio review ONLY. Files may be accessible to anyone with repository read access.",
            "artifact_retention_days":1,
            "original_synthetic_educational_video_files":3,
            "source_news_and_publisher_article_passages_included":False,
            "factual_news_claims_reviewed":0,
            "rights_and_owner_approvals":0,
            "youtube_releases":0,
            "publishing_authorized":False,
            "videos":entries,
        }
        # Machine-readable review worksheet is intentionally blank: hashes tie
        # human notes to the *specific* decoded bytes, not to a later rerender.
        # No reviewer identity, source text, release token, or fake PASS exists.
        checks=(
            "opening_hook_under_2_seconds",
            "every_scene_unique_and_no_rotating_spinner",
            "voice_clear_pronunciation_and_no_clipping",
            "caption_readability_mobile_safe_area_and_spelling",
            "audio_caption_sync_and_sound_effect_balance",
            "original_visual_labels_legible_and_not_cropped",
            "narrative_payoff_and_ending",
            "visual_audio_model_and_music_rights_verified",
            "factual_claims_primary_source_verified",
            "human_listened_and_watched_entire_clip",
        )
        worksheet={
            "schema":"B4E5_SHA_BOUND_BLANK_HUMAN_QA_WORKSHEET_V1",
            "synthetic_educational_media_only":True,
            "human_review_completed":False,
            "factual_news_approved":False,
            "rights_approved":False,
            "youtube_publish_authorized":False,
            "instructions":"Watch each full file, then make a separate private copy of this worksheet. Replace NOT_REVIEWED only with evidence; record scene/timestamp issues. Never treat this blank artifact as a release approval.",
            "videos":[{
                "slot":item["slot"],
                "filename":item["file"],
                "sha256":item["sha256"],
                "duration_seconds_measured_pcm":item["measured_audio_seconds"],
                "scenes":[{
                    "scene_number":index,
                    "review_status":"NOT_REVIEWED",
                    "timecode_mm_ss":None,
                    "defect_notes":None,
                } for index in range(1,item["original_voiced_scene_count"]+1)],
                "checks":{check:"NOT_REVIEWED" for check in checks},
                "overall_human_decision":"NOT_REVIEWED",
            } for item in entries],
        }
        # The owner opens this LOCAL file next to the three explicit MP4s.
        # No web server, CDN, JS dependency, secrets, uploads or approval.
        from autopilot.offline_review_portal_b4e7 import (
            build_portal, PORTAL_FILE,
        )
        (target/PORTAL_FILE).write_text(
            build_portal(info, worksheet), encoding="utf8",
        )
        (target/"HUMAN_REVIEW_WORKSHEET_UNFILLED.json").write_text(
            json.dumps(worksheet,indent=2,ensure_ascii=True)+"\n",encoding="utf8")
        (target/"REVIEW_ONLY_NO_PUBLISH.json").write_text(
            json.dumps(info,indent=2,ensure_ascii=True)+"\n",encoding="utf8")
        (target/"READ_ME_FIRST.txt").write_text(
            "FLOWMINUTE LAB — ORIGINAL SYNTHETIC EDUCATIONAL REHEARSALS\n"
            "NOT FACT-CHECKED NEWS. NOT LICENSED FOR PUBLIC YOUTUBE RELEASE.\n"
            "This package was manually requested from the GitHub Actions workflow.\n"
            "GitHub artifacts are readable by signed-in users with repository read access.\n"
            "Review only: narrative originality, voice pronunciation, caption legibility,\n"
            "audio synchronization, pacing, scene variety and absence of spinning circles.\n"
            "Open OPEN_LOCAL_REVIEW_DASHBOARD.html locally, alongside the 3 original MP4s.\n"
            "Download its PRIVATE review JSON only after full human playback.\n"
            "Fill a PRIVATE COPY of HUMAN_REVIEW_WORKSHEET_UNFILLED.json only after playback.\n"
            "Do not publish, redistribute, assume owner final approval, or quote publisher news.\n"
            "All source snippets, raw research, model weights, MP3/WAV and captions are excluded.\n"
            "After 1 day the review download is expected to expire under repo retention policy.\n",
            encoding="utf8",
        )
        if set(p.name for p in target.iterdir())!=set(
            name for _,name,_ in SLOT_NAMES)|{
            "REVIEW_ONLY_NO_PUBLISH.json","READ_ME_FIRST.txt",
            "HUMAN_REVIEW_WORKSHEET_UNFILLED.json",
            "OPEN_LOCAL_REVIEW_DASHBOARD.html"}:
            raise ReviewExportRefused("Unrecognized extra file in review package")
        return info
    except BaseException:
        shutil.rmtree(target,ignore_errors=True)
        raise


def main() -> None:
    parser=argparse.ArgumentParser(description="Manual-review 1-day GitHub artifacts ONLY; no publishing")
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--origin",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    if os.getenv("GITHUB_EVENT_NAME")!="workflow_dispatch" or os.getenv(
            "FLOWMINUTE_EXPLICIT_REVIEW_OPT_IN")!="true":
        raise ReviewExportRefused("Explicit manual GitHub owner review opt-in is required")
    if args.report!=ROOT/"EPHEMERAL_FULL_VOICE_REHEARSAL_QA.json":
        raise ReviewExportRefused("Report must be the exact trusted runner output")
    summary=prepare_review_export(args.origin,args.output_dir,_read_report(args.report))
    # The log never includes unverified narration, article bytes or HTML.
    print(json.dumps({
        "status":EXPORT_STATUS,
        "review_mp4_count":summary["original_synthetic_educational_video_files"],
        "artifact_retention_days":1,
        "news_claims_verified":0,
        "rights_approved":0,
        "youtube_uploaded":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
