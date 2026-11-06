"""B4d2 synthetic independent source/triage adversarial tests.

Fake public response bytes are used ONLY to exercise the actual existing
source-probe code; no real network or false human claim validation.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from autopilot.daily_cloud_plan import build_plan
from autopilot.daily_editorial_board import (
    STATUS, EditorialTriageRefused, build_editorial_board,
    sanitized_public_receipt, _family, _related, _subject_hash,
)
from autopilot.evidence_probe import probe_report
from autopilot.test_evidence_probe import FakeOpener

CLOCK=datetime(2026,11,6,9,0,tzinfo=timezone.utc)
DAY="2026-11-07"


def scout_fixture() -> dict:
    leads = [
        ("OpenAI","How new AI agents coordinate complex workflows",
         "https://openai.com/index/agents-workflows-original"),
        ("OpenAI","AI agents coordinate workflows in a new approach",
         "https://openai.com/index/agents-workflows-copy"),
        ("Google DeepMind","Gemini reasoning model evaluation and benchmarks",
         "https://deepmind.google/discover/blog/gemini-reasoning-models"),
        ("The Verge","A dataset and analytics research method explained",
         "https://www.theverge.com/2026/11/6/data-analytics-method"),
        ("OpenAI","Software coding API for developer productivity",
         "https://openai.com/index/software-coding-tools"),
        ("The Verge","How security privacy challenges affect authentication",
         "https://www.theverge.com/2026/11/6/security-authentication"),
    ]
    return {
        "status":"leads_only_no_publish_authorization",
        "generated_at_utc":CLOCK.isoformat(),
        "leads":[{
            "publisher":pub,"title":title,"url":url,
            "published_utc":(CLOCK-timedelta(hours=i+2)).isoformat(),
            "status":"unverified_lead","relevance":.85,
        } for i,(pub,title,url) in enumerate(leads)],
    }


def inputs() -> tuple[dict,dict,dict]:
    scout=scout_fixture()
    plan=build_plan(DAY,scout_report=scout,generated_at_utc=CLOCK)
    evidence=probe_report(scout,clock=CLOCK,opener=FakeOpener(),max_sources=3)
    return plan,scout,evidence


class DailyEditorialBoardTests(unittest.TestCase):
    def setUp(self):
        self.plan,self.scout,self.evidence=inputs()

    def board(self,*,history=None):
        return build_editorial_board(
            self.plan,self.scout,self.evidence,previous_subject_hashes=history)

    def test_three_distinct_source_based_research_angles_not_scripts(self):
        result=self.board()
        self.assertEqual(result["status"],STATUS)
        self.assertEqual(result["episode_count"],3)
        self.assertEqual(result["distinct_topics_selected"],3)
        self.assertEqual(result["distinct_subject_hashes"],3)
        self.assertEqual([x["format"] for x in result["slots"]],["short","long","short"])
        self.assertEqual(
            [x["local_ist"] for x in result["slots"]],["11:00","16:00","20:30"])
        self.assertEqual(
            [x["angle_id"] for x in result["slots"]],
            ["WHAT_TO_TEST_FIRST","EXPLAIN_AND_DEMONSTRATE","MYTH_VS_LIMITATION"])
        self.assertEqual({x["research_lead"]["topic_family"] for x in result["slots"]},
                         {"agents","models","data"})
        self.assertGreaterEqual(result["article_bytes_observed_selected"],1)
        for x in result["slots"]:
            self.assertFalse(x["release_authorized"])
            self.assertFalse(x["real_script_exists"])
            self.assertFalse(x["real_media_exists"])
            self.assertFalse(x["factual_narration_draft_exists"])
            self.assertFalse(x["rights_approved"])
            self.assertFalse(x["youtube_uploaded"])
            self.assertFalse(x["youtube_scheduled"])
            self.assertTrue(x["research_question_not_factual_claim"].endswith("?")
                            or "Require" in x["research_question_not_factual_claim"])
        self.assertEqual(result["billable_api_calls"],0)
        self.assertEqual(result["scripts_generated"],0)
        self.assertFalse(result["youtube_upload_enabled"])
        self.assertFalse(result["youtube_schedule_enabled"])
        self.assertFalse(result["fresh_source_corroboration_performed"])

    def test_lexically_similar_agents_headlines_not_both_selected(self):
        board=self.board()
        urls=[x["research_lead"]["unverified_url"] for x in board["slots"]]
        self.assertNotIn("https://openai.com/index/agents-workflows-copy",urls)
        self.assertEqual(len(set(urls)),3)

    def test_same_url_cannot_be_selected_twice(self):
        duplicate=deepcopy(self.scout["leads"][0])
        duplicate["title"]="Different looking fake headline with same origin article"
        self.scout["leads"].insert(1,duplicate)
        result=self.board()
        urls=[x["research_lead"]["unverified_url"] for x in result["slots"]]
        self.assertEqual(len(urls),len(set(urls)))

    def test_fewer_verified_articles_does_not_invent_three_evidence_claims(self):
        self.evidence["sources"]=[]
        self.evidence.update({
            "source_probes_attempted":0,"sources_observed_total":0,
            "sources_fetched":0,"feed_entries_observed_only":0,"sources_failed":0,
            "direct_article_fetch_failure_counts":{},
            "source_articles_with_bounded_publisher_redirect":0,
            "failures":[],
        })
        report=self.board()
        self.assertEqual(report["article_bytes_observed_selected"],0)
        self.assertEqual(report["distinct_topics_selected"],3)
        self.assertTrue(all(
            x["research_lead"]["source_evidence_level"]==
                "SCOUT_HEADLINE_ONLY_UNOBSERVED" for x in report["slots"]))
        self.assertTrue(all(x["real_script_exists"] is False for x in report["slots"]))

    def test_empty_scout_is_three_empty_research_tasks_not_fabricated_topics(self):
        self.scout["leads"]=[]
        report=self.board()
        self.assertEqual(report["distinct_topics_selected"],0)
        self.assertEqual(report["article_bytes_observed_selected"],0)
        self.assertTrue(all(x["research_lead"] is None for x in report["slots"]))
        self.assertTrue(all(
            x["editorial_status"]=="NO_DISTINCT_CURRENT_TOPIC_FOUND_RESEARCH_REQUIRED"
            for x in report["slots"]))

    def test_history_prevents_repeat_subjects_across_days(self):
        first=self.board()
        previous=[first["slots"][0]["research_lead"]["subject_sha256"]]
        result=self.board(history=previous)
        self.assertEqual(result["distinct_topics_selected"],3)
        actual=[x["research_lead"]["subject_sha256"] for x in result["slots"]]
        self.assertNotIn(previous[0],actual)

    def test_history_rejects_malformed_or_oversized_inputs(self):
        for h in ([123],["z"*64],["a"*64]*501,{"z":"hash"},True):
            with self.subTest(history_type=str(type(h))):
                with self.assertRaises(EditorialTriageRefused):
                    self.board(history=h)

    def test_article_was_really_observed_by_injected_test_source_reader(self):
        self.assertEqual(self.evidence["sources_fetched"],3)
        self.assertEqual(self.evidence["sources_observed_total"],3)
        self.assertEqual(self.evidence["claims_verified"],0)
        self.assertEqual(len(self.evidence["sources"]),3)
        result=self.board()
        for x in result["slots"]:
            lead=x["research_lead"]
            if lead and lead["article_bytes_observed"]:
                actual=next(y for y in self.evidence["sources"]
                            if y["source_id"]==lead["source_id"])
                self.assertEqual(lead["source_digest"],actual["response_sha256"])
                self.assertFalse(actual["facts_verified"])

    def test_article_claim_promoted_to_verified_refused(self):
        self.evidence["sources"][0]["facts_verified"]=True
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_forged_article_digest_rejected(self):
        self.evidence["sources"][0]["response_sha256"]="XX"*32
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_observation_url_wrong_host_refused(self):
        self.evidence["sources"][0]["source_url"]="https://localhost/admin"
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_observation_id_wrong_hash_refused(self):
        self.evidence["sources"][0]["source_id"]="0"*24
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_identical_article_claim_from_wrong_publisher_refused(self):
        self.evidence["sources"][0]["publisher"]="The Verge"
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_observation_headline_mismatch_refused(self):
        self.evidence["sources"][0]["title"]="Completely altered fake research headline"
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_invalid_observation_status_refused(self):
        self.evidence["sources"][0]["status"]="FACTS_VERIFIED"
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_forged_rss_entry_as_direct_article_denied(self):
        x=self.evidence["sources"][0]
        x["status"]="RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED"
        x["source_article_fetched"]=True
        self.evidence["sources_fetched"]-=1
        self.evidence["feed_entries_observed_only"]+=1
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_status_counters_must_reconcile(self):
        self.evidence["source_probes_attempted"]+=1
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_wrong_observation_time_refused(self):
        self.evidence["sources"][0]["observed_at_utc"]="2020-01-01T00:00:00+00:00"
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_stale_scout_items_skipped_not_promoted(self):
        for item in self.scout["leads"]:
            item["published_utc"]="2020-01-01T00:00:00Z"
        result=self.board()
        self.assertEqual(result["distinct_topics_selected"],0)
        self.assertTrue(all(s["research_lead"] is None for s in result["slots"]))

    def test_future_published_article_does_not_count_as_latest(self):
        for item in self.scout["leads"]:
            item["published_utc"]=(CLOCK+timedelta(days=3)).isoformat()
        self.assertEqual(self.board()["distinct_topics_selected"],0)

    def test_privileged_plan_flags_block_before_board_generation(self):
        for field,bad in (
            ("youtube_upload_enabled",True),
            ("youtube_schedule_enabled",True),
            ("approved_provider_credentials_connected",True),
            ("cloud_publisher_connected",True),
            ("new_billable_resources_enabled",True),
            ("any_content_verified",True),
        ):
            with self.subTest(field=field):
                original=self.plan[field]
                self.plan[field]=bad
                with self.assertRaises(EditorialTriageRefused):
                    self.board()
                self.plan[field]=original

    def test_existing_script_forgery_denied(self):
        self.plan["slots"][0]["real_script_exists"]=True
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_wrong_time_slot_and_channel_consistency_denied(self):
        self.plan["slots"][2]["local_ist"]="20:00"
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_public_receipt_contains_source_block_categories_but_no_server_data(self):
        report=self.board()
        receipt=sanitized_public_receipt(report)
        self.assertEqual(receipt["direct_article_http_failure_counts"],{})
        self.assertEqual(receipt["direct_articles_with_publisher_only_redirect"],0)
        serialized=json.dumps(receipt)
        self.assertNotIn("https://",serialized)
        self.assertNotIn("http_status",serialized)
        self.assertFalse(receipt["release_authorized"])

    def test_forged_article_fetch_failure_counts_rejected(self):
        self.evidence["direct_article_fetch_failure_counts"]={"HTTP_ACCESS_DENIED":3}
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_disallowed_url_leakage_in_error_class_rejected(self):
        self.evidence["direct_article_fetch_failure_counts"]={
            "https://private.example/auth?secret=abc":1}
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_mismatched_observed_redirect_count_rejected(self):
        self.evidence["source_articles_with_bounded_publisher_redirect"]=1
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_article_redirect_must_have_structurally_consistent_proof(self):
        self.evidence["sources"][0]["approved_same_publisher_redirect"]=True
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_rss_entry_diagnostic_requires_actual_http_failure_class(self):
        source=self.evidence["sources"][0]
        source["status"]="RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED"
        source["source_article_fetched"]=False
        source["feed_entry_sha256"]="b"*64
        self.evidence["sources_fetched"]-=1
        self.evidence["feed_entries_observed_only"]+=1
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_unsupported_scout_promotion_denied(self):
        self.scout["status"]="publish_ready"
        with self.assertRaises(EditorialTriageRefused):
            self.board()

    def test_public_receipt_contains_no_urls_headlines_titles_or_source_bodies(self):
        board=self.board()
        receipt=sanitized_public_receipt(board)
        s=json.dumps(receipt)
        self.assertFalse(receipt["release_authorized"])
        self.assertEqual(receipt["fresh_original_scripts_completed"],0)
        self.assertEqual(len(receipt["slots"]),3)
        self.assertEqual(len(receipt["receipt_sha256"]),64)
        self.assertNotIn("https://",s)
        for item in self.scout["leads"]:
            self.assertNotIn(item["url"],s)
            self.assertNotIn(item["title"],s)
        self.assertNotIn("source_digest",s)
        self.assertNotIn("unverified_title",s)
        self.assertFalse(receipt["headlines_urls_source_bodies_and_scripts_included"])

    def test_public_receipt_refuses_fake_script_or_video_release(self):
        board=self.board()
        for slot,bad_key in (
            (0,"release_authorized"),(1,"real_media_exists"),
            (2,"real_script_exists")
        ):
            with self.subTest(key=bad_key):
                changed=deepcopy(board)
                changed["slots"][slot][bad_key]=True
                with self.assertRaises(EditorialTriageRefused):
                    sanitized_public_receipt(changed)

    def test_source_subject_family_is_deterministic_and_hash_no_raw_title(self):
        self.assertEqual(_family("Gemini model reasoning benchmarks"),"models")
        self.assertEqual(_family("Data analytics spreadsheet"),"data")
        self.assertEqual(_family("Software coding API developer"),"developer_tools")
        h=_subject_hash("AI agents evaluate workflows")
        self.assertRegex(h,r"^[0-9a-f]{64}$")
        self.assertNotIn("agent",h)
        self.assertTrue(_related(
            {"subject_hash":h,"tokens":{"agent","workflow"}},
            {"subject_hash":h,"tokens":{"agent","workflow"}}))

    def test_cli_runs_on_fake_local_public_metadata_without_network(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root)
            plan,scout,evidence=inputs()
            for name,data in (("plan.json",plan),("scout.json",scout),("evidence.json",evidence)):
                (d/name).write_text(json.dumps(data),encoding="utf-8")
            p=subprocess.run([
                sys.executable,"-B","-m","autopilot.daily_editorial_board",
                "--plan",str(d/"plan.json"),
                "--scout-report",str(d/"scout.json"),
                "--evidence",str(d/"evidence.json"),
                "--board-output",str(d/"private-ephemeral-board.json"),
                "--public-receipt-output",str(d/"sanitized-receipt.json"),
            ],capture_output=True,text=True,timeout=20)
            self.assertEqual(p.returncode,0,p.stderr)
            summary=json.loads(p.stdout)
            self.assertEqual(summary["distinct_topics_selected"],3)
            self.assertFalse(summary["youtube_uploaded_or_scheduled"])
            self.assertEqual(summary["scripts_generated"],0)
            saved=json.loads((d/"sanitized-receipt.json").read_text())
            self.assertNotIn("https://",json.dumps(saved))
            self.assertEqual(saved["fresh_original_scripts_completed"],0)


if __name__=="__main__":
    unittest.main()
