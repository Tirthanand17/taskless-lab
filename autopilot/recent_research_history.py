"""B4d8 previous-day topic repetition guard using ONLY sanitized GitHub receipts.

Retrieves a bounded selection of prior successful DEFAULT-BRANCH daily GitHub
research artifacts using the built-in gh CLI with actions:read. Never puts a
YouTube token, user history, page text, titles or URLs in public logs.

History is *research selection* memory, not proof a video was published.
Only receipt-verified 64-digit subject and 24-digit exact source hashes are
used. The same next-day plan can be rerun without treating itself as history.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile, BadZipFile
from zoneinfo import ZoneInfo

from autopilot.daily_editorial_board import _subject_hash
from autopilot.evidence_probe import verify_public_source_url, EvidenceError

REPOSITORY = "Tirthanand17/taskless-lab"
WORKFLOW = "flowminute-daily-cloud-foundation.yml"
RECEIPT_NAME = "flowminute-public-editorial-receipt.json"
RESEARCH_NAME = "flowminute-public-research-draft-receipt.json"
HISTORY_STATUS = "B4D8_PREVIOUS_SUCCESSFUL_GITHUB_RESEARCH_RECEIPTS_ONLY"
FILTER_STATUS = "B4D8_PRIOR_TOPIC_AND_SOURCE_RESEARCH_REPETITION_FILTERED"
SCOUT_STATUS = "leads_only_no_publish_authorization"
DAYS = 7
MAX_ZIP = 100_000
MAX_PAGES = 1
MAX_DOWNLOADS = 14
MAX_RUNS = 100
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX24 = re.compile(r"[0-9a-f]{24}\Z")
RUN_ID = re.compile(r"[0-9]{8,16}\Z")


class HistoryRefused(ValueError):
    """Forged/unbounded GitHub research receipt or unsafe history input."""


def _date(value: object) -> date:
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",value):
        raise HistoryRefused("Unsafe YYYY-MM-DD history date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HistoryRefused("Invalid calendar date") from None


def _canonical(value: object) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode("utf8")


def _receipt_from_archive(data: bytes, day: date) -> dict | None:
    if type(data) is not bytes or not 80 <= len(data) <= MAX_ZIP:
        raise HistoryRefused("Unbounded archive")
    try:
        with ZipFile(BytesIO(data)) as z:
            filenames={x.filename:x for x in z.infolist()}
            if (set(filenames)!={RECEIPT_NAME,RESEARCH_NAME}
                or any(x.file_size > 12000 or x.is_dir() for x in filenames.values())):
                raise HistoryRefused("Unsafe research receipt archive contents")
            board=json.loads(z.read(RECEIPT_NAME))
            plan=json.loads(z.read(RESEARCH_NAME))
    except (BadZipFile,UnicodeError,json.JSONDecodeError,RuntimeError,KeyError):
        raise HistoryRefused("Unparseable sanitized GitHub receipt archive") from None
    if (type(board) is not dict or type(plan) is not dict
        or board.get("status")!="B4D2_SANITIZED_DAILY_EDITORIAL_RECEIPT_NO_CONTENT"
        or plan.get("status")!="GITHUB_RETAINED_RESEARCH_DRAFT_EVIDENCE_ONLY"
        or board.get("receipt_sha256") is None
        or type(board.get("receipt_sha256")) is not str
        or not HEX64.fullmatch(board["receipt_sha256"])
        or plan.get("sanitized_editorial_receipt_sha256")!=board["receipt_sha256"]
        or plan.get("editorial_and_plan_reconciled") is not True
        or plan.get("raw_source_headlines_urls_and_bodies_retained") is not False
        or board.get("headlines_urls_source_bodies_and_scripts_included") is not False
        or board.get("release_authorized") is not False
        or plan.get("release_authorized") is not False
        or plan.get("youtube_publishing_enabled") is not False
        or board.get("real_youtube_uploads")!=0
        or board.get("fresh_original_scripts_completed")!=0):
        raise HistoryRefused("Receipt appears unsafe or inconsistent")
    # B4g8: independently verify the RESEARCH manifest's own digest,
    # not merely the already-verified editorial board digest. The new
    # public script-fingerprint field must not be silently added to a
    # previously trusted GitHub artifact after the fact.
    receipt_digest=plan.get("receipt_sha256")
    if type(receipt_digest) is not str or HEX64.fullmatch(receipt_digest) is None:
        raise HistoryRefused("Research receipt has no integrity root")
    plan_without_hash={key:value for key,value in plan.items()
                       if key!="receipt_sha256"}
    try:
        validated=sha256(json.dumps(
            plan_without_hash,sort_keys=True,separators=(",",":"),
            ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()
    except (TypeError,ValueError,UnicodeError):
        raise HistoryRefused("Invalid historical research receipt canonical bytes") from None
    if validated!=receipt_digest:
        raise HistoryRefused("Historical research receipt content changed")
    digest=board.pop("receipt_sha256")
    verified=sha256(_canonical(board)).hexdigest()
    board["receipt_sha256"]=digest
    if digest!=verified:
        raise HistoryRefused("Editorial content integrity hash mismatch")
    pday=_date(board.get("plan_date_ist"))
    if _date(plan.get("plan_day_ist"))!=pday:
        raise HistoryRefused("Research and editorial day mismatch")
    if pday>=day or pday<day-timedelta(days=DAYS):
        return None  # Same next-day rerun and expired history are not repeats.
    slots=board.get("slots")
    if (type(slots) is not list or len(slots)!=3
        or board.get("selected_distinct_topics")!=sum(
            item.get("source_id") is not None for item in slots if type(item) is dict)):
        raise HistoryRefused("Inconsistent historical topic count")
    source_ids,hashes=set(),set()
    for item in slots:
        if (type(item) is not dict or item.get("release_authorized") is not False
            or item.get("youtube_uploaded") is not False):
            raise HistoryRefused("Historical video authority mismatch")
        sid,sub=item.get("source_id"),item.get("subject_sha256")
        if sid is None and sub is None:
            continue
        if (type(sid) is not str or type(sub) is not str
            or not HEX24.fullmatch(sid) or not HEX64.fullmatch(sub)
            or sid in source_ids or sub in hashes):
            raise HistoryRefused("Malformed or duplicated historical source hashes")
        source_ids.add(sid)
        hashes.add(sub)
    # B4g8: optional cross-day original-script fingerprint data.
    # Old archival research-only receipts are accepted, but they are NOT
    # retroactively credited with a real narration originality check.
    hashes_of_voice=set()
    simhashes_of_voice=set()
    scripted=plan.get("unapproved_rehearsal_narration_originality")
    if scripted is not None:
        if (type(scripted) is not dict
            or scripted.get("status")!=
                "B4G8_ORIGINAL_REHEARSAL_VOICEOVER_REPEAT_CHECK_NOT_CONTENT_APPROVAL"
            or scripted.get("plan_day_ist")!=pday.isoformat()
            or scripted.get("episode_slots")!=["short_am","long","short_pm"]
            or scripted.get("source_fingerprint_domain")!=
                "NORMALIZED_SPOKEN_SCENES_NOT_EPISODE_ID"
            or scripted.get("unique_against_every_prior_day_proven") is not False
            or scripted.get("all_three_daily_videos_factually_original_or_rights_checked") is not False
            or scripted.get("actual_human_factual_and_rights_approvals")!=0
            or scripted.get("youtube_release_authorized") is not False
            or type(scripted.get("script_fingerprints_sha256")) is not list
            or len(scripted["script_fingerprints_sha256"])!=3
            or any(type(v) is not str or HEX64.fullmatch(v) is None
                   for v in scripted["script_fingerprints_sha256"])
            or len(set(scripted["script_fingerprints_sha256"]))!=3):
            raise HistoryRefused(
                "Invalid or authority-claiming unapproved narration hash receipt")
        hashes_of_voice=set(scripted["script_fingerprints_sha256"])
        # Backward compatible with B4g8 research receipts (exact SHA only).
        # Near-similarity coverage is NEVER invented for older artifacts.
        signatures=scripted.get("spoken_4gram_simhash64")
        if signatures is not None:
            if (type(signatures) is not list or len(signatures)!=3
                or any(type(x) is not str
                       or re.fullmatch(r"[0-9a-f]{16}",x) is None
                       for x in signatures)
                or scripted.get("near_repeat_is_only_a_review_signal") is not True):
                raise HistoryRefused("Invalid unapproved narration similarity receipt")
            simhashes_of_voice=set(signatures)
    return {"plan_day_ist":pday.isoformat(),"subject_hashes":hashes,
            "source_ids":source_ids,
            "historical_spoken_sha256":hashes_of_voice,
            "historical_spoken_simhash64":simhashes_of_voice}


def gather_history(runs: object, fetch_archive, *, target_day: str) -> dict:
    day=_date(target_day)
    if type(runs) is not list or len(runs)>MAX_RUNS:
        raise HistoryRefused("Unbounded GitHub workflow run list")
    relevant=[]
    for run in runs:
        if type(run) is not dict:
            raise HistoryRefused("Malformed workflow-run record")
        raw_id=run.get("id")
        created=run.get("created_at")
        try:
            date_created=datetime.fromisoformat(created.replace("Z","+00:00"))
        except (AttributeError,TypeError,ValueError):
            continue
        if date_created.tzinfo is None:
            continue
        if (type(raw_id) is not int or not RUN_ID.fullmatch(str(raw_id))
            or run.get("head_branch")!="main"
            or run.get("conclusion")!="success"
            or run.get("status")!="completed"
            or run.get("event") not in ("push","schedule","workflow_dispatch")
            or run.get("path")!=f".github/workflows/{WORKFLOW}"
            or not isinstance(run.get("head_repository"),dict)
            or run["head_repository"].get("full_name")!=REPOSITORY
            or date_created.date()>day
            or date_created.date()<day-timedelta(days=DAYS+2)):
            continue
        attempt=run.get("run_attempt")
        if type(attempt) is not int or not 1<=attempt<=20:
            continue
        relevant.append((date_created,raw_id,attempt))
    relevant.sort(reverse=True)
    seen_days=set()
    seen_run_days=set()
    source_ids=set()
    hashes=set()
    spoken_hashes=set()
    spoken_days=set()
    simhashes=set()
    simhash_days=set()
    downloads=0
    for created,run_id,attempt in relevant:
        if len(seen_days)>=DAYS or downloads>=MAX_DOWNLOADS:
            break
        # Same UTC run-date may contain several PR push receipts. Query at
        # most 2 per UTC date, and retain only one validated *plan day*.
        rday=created.date()
        # Runs created today in UTC are research for the same upcoming
        # IST planning day; never burn the network budget replaying today's
        # multiple PR/merge receipts.
        if rday >= day-timedelta(days=1) or rday in seen_run_days:
            continue
        downloads+=1
        expected=f"flowminute-unapproved-research-receipt-{run_id}-{attempt}"
        try:
            archive=fetch_archive(run_id,expected)
            entry=_receipt_from_archive(archive,day)
        except (HistoryRefused,OSError,subprocess.CalledProcessError):
            continue
        if entry is None:
            seen_run_days.add(rday)
            continue
        planned=entry["plan_day_ist"]
        if planned in seen_days:
            seen_run_days.add(rday)
            continue
        hashes.update(entry["subject_hashes"])
        source_ids.update(entry["source_ids"])
        spoken_hashes.update(entry["historical_spoken_sha256"])
        if entry["historical_spoken_sha256"]:
            spoken_days.add(planned)
        simhashes.update(entry["historical_spoken_simhash64"])
        if entry["historical_spoken_simhash64"]:
            simhash_days.add(planned)
        seen_days.add(planned)
        seen_run_days.add(rday)
    return {
        "status":HISTORY_STATUS, "target_day_ist":day.isoformat(),
        "lookback_days":DAYS, "verified_prior_research_days":len(seen_days),
        "verified_prior_research_plan_days":sorted(seen_days),
        "historical_exact_source_ids":sorted(source_ids),
        "historical_subject_sha256":sorted(hashes),
        "historical_script_sha256":sorted(spoken_hashes),
        "verified_prior_script_review_days":len(spoken_days),
        "historical_script_simhash64":sorted(simhashes),
        "verified_prior_script_simhash_days":len(simhash_days),
        "trusted_run_receipt_download_attempts":downloads,
        "not_a_youtube_publication_readback":True,
        "video_release_authorized":False,
    }


def filter_scout_with_history(scout: object, history: object) -> dict:
    if (type(scout) is not dict or scout.get("status")!=SCOUT_STATUS
        or type(scout.get("leads")) is not list
        or len(scout["leads"])>24
        or type(history) is not dict or history.get("status")!=HISTORY_STATUS
        or history.get("video_release_authorized") is not False
        or history.get("not_a_youtube_publication_readback") is not True
        or type(history.get("verified_prior_research_days")) is not int
        or not 0<=history["verified_prior_research_days"]<=DAYS
        or type(history.get("historical_exact_source_ids")) is not list
        or type(history.get("historical_subject_sha256")) is not list):
        raise HistoryRefused("Invalid research-only scout or prior history")
    ids=history["historical_exact_source_ids"]
    subjects=history["historical_subject_sha256"]
    if (len(ids)>DAYS*3 or len(subjects)>DAYS*3
        or len(set(ids))!=len(ids) or len(set(subjects))!=len(subjects)
        or any(type(x) is not str or not HEX24.fullmatch(x) for x in ids)
        or any(type(x) is not str or not HEX64.fullmatch(x) for x in subjects)):
        raise HistoryRefused("Unsafe history ID/hash list")
    kept=[]
    seen_urls=set()
    removed=0
    for row in scout["leads"]:
        if type(row) is not dict:
            raise HistoryRefused("Malformed scout candidate")
        title,link,publisher=row.get("title"),row.get("url"),row.get("publisher")
        if type(title) is not str or type(link) is not str or type(publisher) is not str:
            raise HistoryRefused("Malformed scout source title or URL")
        try:
            valid_url=verify_public_source_url(link,publisher)
            h=_subject_hash(" ".join(title.split())[:200])
        except (EvidenceError,ValueError):
            # Old safety gates already exclude invalid leads; never persist
            # or print their content here.
            continue
        sid=sha256(valid_url.encode("utf8")).hexdigest()[:24]
        if sid in ids or h in subjects or link in seen_urls:
            removed+=1
            continue
        seen_urls.add(link)
        kept.append(row)
    filtered={**scout,
              "leads":kept,
              "independent_feeds_with_leads":len({r["publisher"] for r in kept}),
              "research_history_filter_status":FILTER_STATUS,
              "prior_verified_research_days":history["verified_prior_research_days"],
              "recent_research_topic_or_exact_source_repeats_removed":removed,
              "recent_research_leads_retained":len(kept),
              "fresh_source_content_proven":False,
              "prior_youtube_published_content_checked":False,
              "youtube_upload_enabled":False}
    return filtered


def _exec_gh(args: list[str], *, timeout: int, env: dict | None=None) -> bytes:
    try:
        result=subprocess.run(args,timeout=timeout,capture_output=True,
                              env=env,check=False)
    except (OSError,subprocess.TimeoutExpired):
        raise HistoryRefused("Trusted GitHub read-only CLI unavailable") from None
    if result.returncode!=0 or len(result.stdout)>1_200_000:
        # Never print gh error output because remotes may echo credentials.
        raise HistoryRefused("Trusted GitHub receipt read did not complete")
    return result.stdout


def _read_live_history(day: date) -> dict:
    if not os.environ.get("GH_TOKEN"):
        raise HistoryRefused("Read-only trusted Actions token not configured")
    endpoint=(f"repos/{REPOSITORY}/actions/workflows/{WORKFLOW}"
              "/runs?branch=main&status=success&per_page=100")
    raw=_exec_gh(["gh","api",endpoint],timeout=20)
    try:
        container=json.loads(raw)
        runs=container["workflow_runs"]
    except (UnicodeError,json.JSONDecodeError,TypeError,KeyError):
        raise HistoryRefused("Malformed official GitHub Actions run history") from None
    def fetch_archive(run_id: int,name: str) -> bytes:
        with tempfile.TemporaryDirectory(prefix="flowminute-b4d8-history-") as td:
            _exec_gh(["gh","run","download",str(run_id),
                      "--repo",REPOSITORY,"--name",name,"--dir",td],
                     timeout=18)
            folder=Path(td)
            # gh run download unzips the two receipt JSON files directly.
            paths=list(folder.iterdir())
            if (set(x.name for x in paths)!={RECEIPT_NAME,RESEARCH_NAME}
                or any(x.is_symlink() or not x.is_file() or x.stat().st_size>12000
                       for x in paths)):
                raise HistoryRefused("Unexpected GitHub research artifact layout")
            # Re-package in-memory strictly to reuse single validator.
            from zipfile import ZIP_DEFLATED
            out=BytesIO()
            with ZipFile(out,"w",ZIP_DEFLATED) as z:
                for path in paths:
                    z.writestr(path.name,path.read_bytes())
            return out.getvalue()
    return gather_history(runs,fetch_archive,target_day=day.isoformat())


def _read(path: Path) -> object:
    if (not path.is_file() or path.is_symlink() or
        not 2<=path.stat().st_size<=512_000):
        raise HistoryRefused("Missing or oversized research-only input")
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise HistoryRefused("Bad research-only JSON") from None


def main() -> None:
    ap=argparse.ArgumentParser(description="Github-only sanitized prior-topic repetition gate; no publishing")
    sub=ap.add_subparsers(dest="action",required=True)
    collect=sub.add_parser("collect")
    collect.add_argument("--output",type=Path,required=True)
    collect.add_argument("--target-day",type=str)
    filt=sub.add_parser("filter")
    filt.add_argument("--scout",type=Path,required=True)
    filt.add_argument("--history",type=Path,required=True)
    filt.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if (args.output.exists() or args.output.is_symlink()
        or args.output.parent.name!="out"
        or not args.output.name.startswith("flowminute-ephemeral-")):
        raise HistoryRefused("Only new runner-local ephemeral history outputs allowed")
    if args.action=="collect":
        day=_date(args.target_day) if args.target_day else (
            datetime.now(ZoneInfo("Asia/Kolkata")).date()+timedelta(days=1))
        result=_read_live_history(day)
        summary={
            "status":HISTORY_STATUS,
            "past_successful_research_days_with_receipts":
            result["verified_prior_research_days"],
            "historic_distinct_subject_hashes":
            len(result["historical_subject_sha256"]),
            "historic_exact_source_ids":
            len(result["historical_exact_source_ids"]),
            "youtube_releases_verified":0,
        }
    else:
        result=filter_scout_with_history(_read(args.scout),_read(args.history))
        summary={
            "status":FILTER_STATUS,
            "previously_selected_headline_or_source_repeats_removed":
            result["recent_research_topic_or_exact_source_repeats_removed"],
            "new_unverified_research_leads":result["recent_research_leads_retained"],
            "looked_back_at_verified_plan_days":result["prior_verified_research_days"],
            "youtube_releases_verified":0,
        }
    payload=json.dumps(result,separators=(",",":"),ensure_ascii=True)
    if len(payload)>512_000:
        raise HistoryRefused("Unbounded history output")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(payload+"\n",encoding="utf8")
    print(json.dumps(summary,sort_keys=True))


if __name__=="__main__":
    main()
