"""B4d8 no-network adversarial history de-dupe tests: actual canonical receipts."""
from __future__ import annotations

from copy import deepcopy
from datetime import date,timedelta
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile,ZIP_DEFLATED
from unittest.mock import patch

from autopilot.daily_editorial_board import (
    build_editorial_board,sanitized_public_receipt,_subject_hash,
)
from autopilot.daily_evidence_bundle import build_retained_draft_receipt
from autopilot.reconcile_daily_editorial_plan import align_plan_to_editorial_board
from autopilot.recent_research_history import (
    RESEARCH_NAME,RECEIPT_NAME,HISTORY_STATUS,FILTER_STATUS,HistoryRefused,
    _receipt_from_archive,_canonical,gather_history,filter_scout_with_history,
    _exec_gh,
)
from autopilot.test_daily_editorial_board import inputs


DAY="2026-11-08"


def sample_receipts(day="2026-11-07"):
    original,scout,evidence=inputs()
    board=build_editorial_board(original,scout,evidence)
    aligned=align_plan_to_editorial_board(original,board,scout,evidence)
    ed=sanitized_public_receipt(board)
    research=build_retained_draft_receipt(
        aligned,evidence,editorial_receipt=ed)
    assert ed["plan_date_ist"]==day
    return ed,research,scout


def zip_receipts(ed,research,extra=None):
    b=BytesIO()
    with ZipFile(b,"w",ZIP_DEFLATED) as z:
        z.writestr(RECEIPT_NAME,json.dumps(ed))
        z.writestr(RESEARCH_NAME,json.dumps(research))
        if extra:
            z.writestr(extra,b"credential data leak")
    return b.getvalue()


def fake_run(run_id=42200000001, created="2026-11-06T13:30:00Z"):
    return {
        "id":run_id,
        "run_attempt":1,
        "path":".github/workflows/flowminute-daily-cloud-foundation.yml",
        "head_branch":"main",
        "head_repository":{"full_name":"Tirthanand17/taskless-lab"},
        "created_at":created,
        "status":"completed",
        "conclusion":"success",
        "event":"push",
    }


def history_for(ed,research):
    return gather_history(
        [fake_run()],
        lambda run_id,name:zip_receipts(ed,research),
        target_day=DAY,
    )


class RecentGithubHistoryTests(unittest.TestCase):
    def setUp(self):
        self.editorial,self.research,self.scout=sample_receipts()
        self.artifact=zip_receipts(self.editorial,self.research)
        self.history=history_for(self.editorial,self.research)

    def test_real_sanitized_receipts_are_bound_to_previous_day(self):
        r=_receipt_from_archive(self.artifact,date.fromisoformat(DAY))
        self.assertEqual(r["plan_day_ist"],"2026-11-07")
        self.assertEqual(len(r["subject_hashes"]),3)
        self.assertEqual(len(r["source_ids"]),3)
        self.assertNotIn("https://",json.dumps(self.history))
        self.assertEqual(self.history["status"],HISTORY_STATUS)
        self.assertEqual(self.history["verified_prior_research_days"],1)
        self.assertEqual(self.history["lookback_days"],7)
        self.assertFalse(self.history["video_release_authorized"])
        self.assertTrue(self.history["not_a_youtube_publication_readback"])

    def test_same_day_rerun_does_not_blacklist_itself(self):
        r=gather_history(
            [fake_run()],lambda rid,name:self.artifact,
            target_day="2026-11-07")
        self.assertEqual(r["verified_prior_research_days"],0)
        self.assertEqual(r["historical_exact_source_ids"],[])
        self.assertEqual(r["historical_subject_sha256"],[])

    def test_filter_removes_prior_selected_source_ids_and_subjects(self):
        filtered=filter_scout_with_history(self.scout,self.history)
        self.assertEqual(filtered["research_history_filter_status"],FILTER_STATUS)
        self.assertEqual(filtered["prior_verified_research_days"],1)
        self.assertEqual(filtered["recent_research_topic_or_exact_source_repeats_removed"],3)
        self.assertEqual(len(filtered["leads"]),3)
        self.assertEqual(len(self.scout["leads"]),6)  # no mutation
        self.assertTrue(all(
            sha256(x["url"].encode()).hexdigest()[:24]
            not in self.history["historical_exact_source_ids"]
            and _subject_hash(x["title"])
            not in self.history["historical_subject_sha256"]
            for x in filtered["leads"]))
        self.assertFalse(filtered["youtube_upload_enabled"])
        self.assertFalse(filtered["fresh_source_content_proven"])
        self.assertFalse(filtered["prior_youtube_published_content_checked"])

    def test_all_prior_topics_leaves_zero_candidates_not_fabricated_replacements(self):
        h=deepcopy(self.history)
        h["historical_exact_source_ids"]=[]
        h["historical_subject_sha256"]=sorted({
            _subject_hash(x["title"]) for x in self.scout["leads"]})
        f=filter_scout_with_history(self.scout,h)
        self.assertEqual(len(f["leads"]),0)
        self.assertEqual(f["recent_research_topic_or_exact_source_repeats_removed"],6)

    def test_exact_url_changed_headline_cannot_bypass_prior_source_filter(self):
        s=deepcopy(self.scout)
        chosen=self.editorial["slots"][0]
        sid=chosen["source_id"]
        p=next(x for x in s["leads"] if
               sha256(x["url"].encode()).hexdigest()[:24]==sid)
        p["title"]="Invented entirely new headline although original URL same"
        f=filter_scout_with_history(s,self.history)
        self.assertNotIn(p["url"],[x["url"] for x in f["leads"]])

    def test_same_headline_changed_source_url_cannot_bypass_subject_hash(self):
        s=deepcopy(self.scout)
        prior_hash=self.editorial["slots"][0]["subject_sha256"]
        item=next(x for x in s["leads"] if _subject_hash(x["title"])==prior_hash)
        item["url"]="https://openai.com/index/new-path-same-subject"
        f=filter_scout_with_history(s,self.history)
        self.assertNotIn(item["url"],[x["url"] for x in f["leads"]])

    def test_invalid_approval_or_malformed_or_wrong_digest_receipt_rejected(self):
        bad=deepcopy(self.editorial)
        bad["release_authorized"]=True
        for board,plan in (
            (bad,self.research),
            ({**self.editorial,"receipt_sha256":"a"*64},self.research),
            (self.editorial,{**self.research,
                             "sanitized_editorial_receipt_sha256":"f"*64}),
        ):
            with self.subTest(v=str(board.get("release_authorized"))):
                with self.assertRaises(HistoryRefused):
                    _receipt_from_archive(
                        zip_receipts(board,plan),date.fromisoformat(DAY))

    def test_forged_board_receipt_hash_plus_rights_flags_still_refused(self):
        e=deepcopy(self.editorial)
        e["slots"][1]["release_authorized"]=True
        e.pop("receipt_sha256")
        e["receipt_sha256"]=sha256(_canonical(e)).hexdigest()
        research=deepcopy(self.research)
        research["sanitized_editorial_receipt_sha256"]=e["receipt_sha256"]
        with self.assertRaises(HistoryRefused):
            _receipt_from_archive(zip_receipts(e,research),
                                  date.fromisoformat(DAY))

    def test_bad_archives_extra_files_or_zip_slips_denied(self):
        for archive in (b"random random"*100,
                        zip_receipts(self.editorial,self.research,"../private.env")):
            with self.assertRaises(HistoryRefused):
                _receipt_from_archive(archive,date.fromisoformat(DAY))

    def test_enormous_decompressed_archive_cannot_bypass_sanitized_bound(self):
        b=BytesIO()
        with ZipFile(b,"w",ZIP_DEFLATED) as z:
            z.writestr(RECEIPT_NAME,b"A"*200000)
            z.writestr(RESEARCH_NAME,b"{}")
        with self.assertRaises(HistoryRefused):
            _receipt_from_archive(b.getvalue(),date.fromisoformat(DAY))

    def test_no_future_or_stale_history_copied(self):
        future=_receipt_from_archive(self.artifact,date(2026,11,7))
        stale=_receipt_from_archive(self.artifact,date(2026,11,20))
        self.assertIsNone(future)
        self.assertIsNone(stale)

    def test_only_successful_authenticated_main_workflow_runs_eligible(self):
        for change in (
            {"head_branch":"feature/fake"},
            {"head_repository":{"full_name":"attacker/repository"}},
            {"event":"pull_request"},
            {"conclusion":"failure"},
            {"status":"in_progress"},
            {"path":".github/workflows/different.yml"},
            {"created_at":"2025-01-01T10:00:00Z"},
        ):
            run={**fake_run(),**change}
            called=[]
            result=gather_history([run],
                 lambda rid,name:called.append((rid,name)) or self.artifact,
                 target_day=DAY)
            self.assertEqual(result["verified_prior_research_days"],0)
            self.assertEqual(called,[])

    def test_duplicate_successful_runs_only_use_latest_one_day(self):
        r=gather_history(
            [fake_run(42200000003,"2026-11-06T13:45:00Z"),
             fake_run(42200000002,"2026-11-06T13:30:00Z")],
            lambda rid,name:self.artifact,
            target_day=DAY,
        )
        self.assertEqual(r["verified_prior_research_days"],1)
        self.assertEqual(r["trusted_run_receipt_download_attempts"],1)

    def test_missing_artifact_does_not_invent_prior_research(self):
        r=gather_history([fake_run()],
                         lambda rid,name: (_ for _ in ()).throw(OSError("missing")),
                         target_day=DAY)
        self.assertEqual(r["verified_prior_research_days"],0)
        self.assertEqual(r["historical_exact_source_ids"],[])
        self.assertEqual(r["trusted_run_receipt_download_attempts"],1)

    def test_unsafe_duplicated_hex_or_future_history_input_refused(self):
        for key,value in (
            ("historical_exact_source_ids",["0"*24,"0"*24]),
            ("historical_exact_source_ids",["https://malware.example"]),
            ("historical_subject_sha256",["0"*64]*2),
            ("verified_prior_research_days",99),
            ("video_release_authorized",True),
        ):
            with self.subTest(key=key):
                h=deepcopy(self.history)
                h[key]=value
                with self.assertRaises(HistoryRefused):
                    filter_scout_with_history(self.scout,h)

    def test_untrusted_scout_origin_does_not_enter_filtered_current_topics(self):
        fake=deepcopy(self.scout)
        fake["leads"].append({**fake["leads"][0],
                              "url":"https://169.254.169.254/latest/meta-data"})
        f=filter_scout_with_history(fake,self.history)
        self.assertNotIn("169.254.169.254",json.dumps(f))

    def test_gh_command_failure_is_private_without_credentials_or_error_body(self):
        with patch("subprocess.run",return_value=type("P",(),{
            "returncode":1,"stdout":b"","stderr":b"GH_TOKEN=PRIVATE_SECRET_XYZ"})()):
            with self.assertRaises(HistoryRefused) as caught:
                _exec_gh(["gh","api","repos/abc"],timeout=5)
        self.assertNotIn("PRIVATE_SECRET_XYZ",str(caught.exception))

    def test_cli_filter_uses_existing_local_receipts_only_and_prints_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/"out"
            folder.mkdir()
            (folder/"scout.json").write_text(json.dumps(self.scout),encoding="utf8")
            (folder/"history.json").write_text(json.dumps(self.history),encoding="utf8")
            dest=folder/"flowminute-ephemeral-filtered-scout.json"
            cmd=[sys.executable,"-B","-m","autopilot.recent_research_history",
                 "filter","--scout",str(folder/"scout.json"),
                 "--history",str(folder/"history.json"),
                 "--output",str(dest)]
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)[
                "previously_selected_headline_or_source_repeats_removed"],3)
            self.assertEqual(len(json.loads(dest.read_text())["leads"]),3)
            for row in self.scout["leads"]:
                self.assertNotIn(row["title"],run.stdout)
                self.assertNotIn(row["url"],run.stdout)
            twice=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
            self.assertNotEqual(twice.returncode,0)


if __name__=="__main__":
    unittest.main()
