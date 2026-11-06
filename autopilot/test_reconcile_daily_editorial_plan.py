"""B4d5 one provenance-linked daily plan, independent board and two aligned receipts.

Real publisher network fetches belong to the trusted GitHub daily job; these
adversarial tests reuse the existing fake source bytes and never approve facts.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from autopilot.daily_cloud_plan import build_plan
from autopilot.daily_evidence_bundle import (
    DailyEvidenceRefused,build_retained_draft_receipt,
)
from autopilot.daily_editorial_board import (
    build_editorial_board,sanitized_public_receipt,
)
from autopilot.reconcile_daily_editorial_plan import (
    RECONCILIATION_STATUS,PlanReconciliationRefused,
    align_plan_to_editorial_board,
)
from autopilot.test_daily_editorial_board import inputs


class EditorSelectedCanonicalPlanProofTests(unittest.TestCase):
    def setUp(self):
        self.plan,self.scout,self.evidence=inputs()
        self.board=build_editorial_board(self.plan,self.scout,self.evidence)

    def align(self):
        return align_plan_to_editorial_board(
            self.plan,self.board,self.scout,self.evidence)

    def test_original_first_three_leads_and_editorial_selection_differ(self):
        original=[s["research_lead"]["url"] for s in self.plan["slots"]]
        selected=[s["research_lead"]["unverified_url"] for s in self.board["slots"]]
        self.assertNotEqual(original,selected,
                            "Regression fixture must exercise real mismatch")
        self.assertEqual(len(set(selected)),3)

    def test_reconciled_plan_exactly_matches_editorial_source_and_angle(self):
        aligned=self.align()
        self.assertEqual(aligned["editorial_reconciliation_status"],RECONCILIATION_STATUS)
        self.assertEqual(aligned["editorial_selected_unverified_topics"],3)
        self.assertEqual(aligned["editorial_selected_distinct_publishers"],3)
        for old,new,board in zip(self.plan["slots"],aligned["slots"],self.board["slots"]):
            lead=new["research_lead"]
            self.assertEqual(lead["publisher"],board["research_lead"]["publisher"])
            self.assertEqual(lead["url"],board["research_lead"]["unverified_url"])
            self.assertEqual(lead["title"],board["research_lead"]["unverified_title"])
            self.assertEqual(new["editorial_research_angle_id"],board["angle_id"])
            self.assertTrue(new["research_assignment_reconciled_unverified"])
            self.assertEqual(old["episode_id"],new["episode_id"])
            self.assertEqual(old["required_handoffs"],new["required_handoffs"])
            self.assertFalse(new["rights_approved"])
            self.assertFalse(new["real_script_exists"])
            self.assertFalse(new["real_narration_exists"])
            self.assertFalse(new["real_media_exists"])
            self.assertFalse(new["real_media_qa_passed"])
            self.assertFalse(new["youtube_uploaded"])
            self.assertFalse(new["youtube_scheduled"])
            self.assertFalse(new["release_authorized"])
        self.assertFalse(aligned["youtube_upload_enabled"])
        self.assertFalse(aligned["youtube_schedule_enabled"])
        self.assertEqual(aligned["maximum_incremental_spend_inr"],0)
        self.assertEqual(self.plan["slots"][0]["research_lead"]["url"],
                         "https://openai.com/index/agents-workflows-original",
                         "Do not mutate the original nonreconciled plan in place")

    def test_two_retained_public_receipts_are_joinable_to_three_topics(self):
        aligned=self.align()
        editorial=sanitized_public_receipt(self.board)
        retained=build_retained_draft_receipt(
            aligned,self.evidence,editorial_receipt=editorial)
        self.assertTrue(retained["editorial_and_plan_reconciled"])
        self.assertEqual(retained["sanitized_editorial_receipt_sha256"],
                         editorial["receipt_sha256"])
        self.assertEqual(retained["selected_distinct_research_topics"],3)
        self.assertEqual([x["lead_publisher_public_only"] for x in retained["slots"]],
                         [x["research_lead"]["publisher"]
                          for x in self.board["slots"]])
        self.assertFalse(retained["youtube_publishing_enabled"])
        self.assertEqual(retained["independently_verified_unattended_youtube_releases"],0)
        text=json.dumps(retained)
        for item in self.scout["leads"]:
            self.assertNotIn(item["title"],text)
            self.assertNotIn(item["url"],text)
        self.assertNotIn("https://",text)

    def test_old_mismatched_first_three_plan_cannot_claim_reconciliation(self):
        editorial=sanitized_public_receipt(self.board)
        with self.assertRaises(DailyEvidenceRefused):
            build_retained_draft_receipt(
                self.plan,self.evidence,editorial_receipt=editorial)

    def test_modified_editorial_board_cannot_rewrite_plan(self):
        cases=(
            lambda b:b["slots"][0]["research_lead"].update(
                unverified_url="https://evil.example/private"),
            lambda b:b["slots"][1].update(angle_id="FALSE_CLAIM_READY"),
            lambda b:b["slots"][1].update(real_script_exists=True),
            lambda b:b["slots"][0]["research_lead"].update(
                article_bytes_observed=True,source_digest="0"*64),
            lambda b:b["slots"][2].update(release_authorized=True),
            lambda b:b.update(youtube_upload_enabled=True),
            lambda b:b.update(rights_approved=True),
            lambda b:b.update(model_inference_performed=True),
            lambda b:b.update(distinct_topics_selected=2),
            lambda b:b["slots"][1].update(
                research_lead=deepcopy(b["slots"][0]["research_lead"])),
        )
        for change in cases:
            with self.subTest(case=str(change)):
                hacked=deepcopy(self.board)
                change(hacked)
                with self.assertRaises(PlanReconciliationRefused):
                    align_plan_to_editorial_board(
                        self.plan,hacked,self.scout,self.evidence)

    def test_editorial_recalculation_refuses_modified_source_observations(self):
        e=deepcopy(self.evidence)
        e["sources"][0]["response_sha256"]="a"*64
        with self.assertRaises(PlanReconciliationRefused):
            align_plan_to_editorial_board(
                self.plan,self.board,self.scout,e)

    def test_modifying_original_lead_set_refused(self):
        scout=deepcopy(self.scout)
        scout["leads"][0]["title"]="Modified source claim"
        with self.assertRaises(PlanReconciliationRefused):
            align_plan_to_editorial_board(
                self.plan,self.board,scout,self.evidence)

    def test_old_plan_remains_usable_as_legacy_unapproved_receipt_without_claiming_alignment(self):
        legacy=build_retained_draft_receipt(self.plan,self.evidence)
        self.assertFalse(legacy["editorial_and_plan_reconciled"])
        self.assertIsNone(legacy["sanitized_editorial_receipt_sha256"])
        self.assertFalse(legacy["youtube_publishing_enabled"])

    def test_forged_editorial_reconciliation_hash_fails(self):
        p=self.align()
        editorial=sanitized_public_receipt(self.board)
        for key,value in (("editorial_reconciliation_status","APPROVED"),
                          ("editorial_factual_script_count",1),
                          ("editorial_media_count",1),
                          ("editorial_board_sha256","not-sha")):
            with self.subTest(key=key):
                test=deepcopy(p)
                test[key]=value
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(
                        test,self.evidence,editorial_receipt=editorial)

    def test_mismatched_final_receipt_sources_refused_even_if_hash_updated(self):
        p=self.align()
        editorial=sanitized_public_receipt(self.board)
        hacked=deepcopy(editorial)
        hacked["slots"][1]["subject_sha256"]="0"*64
        self._resign_public_receipt(hacked)
        with self.assertRaises(DailyEvidenceRefused):
            build_retained_draft_receipt(
                p,self.evidence,editorial_receipt=hacked)

    def test_forged_editorial_digest_refused(self):
        p=self.align()
        editorial=sanitized_public_receipt(self.board)
        editorial["receipt_sha256"]="0"*64
        with self.assertRaises(DailyEvidenceRefused):
            build_retained_draft_receipt(
                p,self.evidence,editorial_receipt=editorial)

    @staticmethod
    def _resign_public_receipt(receipt):
        from hashlib import sha256
        original=dict(receipt)
        original.pop("receipt_sha256")
        receipt["receipt_sha256"]=sha256(json.dumps(original,
           sort_keys=True,separators=(",",":"),ensure_ascii=False
        ).encode("utf8")).hexdigest()

    def test_no_topic_day_remains_three_empty_research_tasks(self):
        scout=deepcopy(self.scout)
        scout["leads"]=[]
        p=build_plan("2026-11-07",scout_report=scout,
            generated_at_utc=datetime(2026,11,6,9,tzinfo=timezone.utc))
        empty_board=build_editorial_board(p,scout,self.evidence)
        aligned=align_plan_to_editorial_board(p,empty_board,scout,self.evidence)
        self.assertEqual(aligned["editorial_selected_unverified_topics"],0)
        self.assertTrue(all(x["research_lead"] is None for x in aligned["slots"]))
        r=build_retained_draft_receipt(
            aligned,self.evidence,editorial_receipt=sanitized_public_receipt(empty_board))
        self.assertEqual(r["selected_distinct_research_topics"],0)

    def test_cli_can_prepare_reconciled_plan_only_on_new_isolated_output(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            for name,record in (("plan.json",self.plan),("board.json",self.board),
                                ("scout.json",self.scout),("source.json",self.evidence)):
                (folder/name).write_text(json.dumps(record),encoding="utf8")
            output=folder/"aligned-unapproved.json"
            args=[sys.executable,"-B","-m","autopilot.reconcile_daily_editorial_plan",
                  "--plan",str(folder/"plan.json"),
                  "--board",str(folder/"board.json"),
                  "--scout-report",str(folder/"scout.json"),
                  "--source-observations",str(folder/"source.json"),
                  "--output",str(output)]
            proc=subprocess.run(args,capture_output=True,text=True,timeout=20)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["distinct_research_assignments"],3)
            self.assertEqual(json.loads(output.read_text())["editorial_selected_unverified_topics"],3)
            repeated=subprocess.run(args,capture_output=True,text=True,timeout=20)
            self.assertNotEqual(repeated.returncode,0)
            self.assertFalse(self.plan["youtube_upload_enabled"])


if __name__=="__main__":
    unittest.main()
