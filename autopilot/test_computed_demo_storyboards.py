"""B3d4c1 exact computed-demo provenance and unsupported-topic negative tests.

All data, source observations, script signers and reviewers are synthetic.
These checks never establish real third-party factual accuracy or permission.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import unittest

from autopilot.test_script_to_preview_bridge import staged_plan
from autopilot.test_script_continuity_gate import signed_fixture
from autopilot.computed_demo_storyboards import (
    STATUS, RECIPES, CSV_SAMPLE, ExecutedDemoError,
    canonical, build_executed_demo, require_exact_demo,
)


def packet_for(index: int):
    plan=staged_plan(index)
    proposal=signed_fixture(index)[0]
    recipe=(
        "preserve_text_identifiers",
        "validate_iso_dates",
        "review_duplicate_keys",
    )[index]
    return plan,proposal,recipe,build_executed_demo(plan,proposal,recipe)


class ComputedDemoStoryboardsTests(unittest.TestCase):
    def test_all_three_computations_are_real_stdlib_executions_not_source_claims(self):
        hashes=set()
        kinds=set()
        for index in range(3):
            with self.subTest(index=index):
                plan,proposal,recipe,demo=packet_for(index)
                self.assertEqual(demo["status"], STATUS)
                self.assertTrue(demo["input_is_invented"])
                self.assertTrue(demo["computation_reproduced_from_fixed_test_fixture"])
                self.assertEqual(demo["script_manifest_sha256"],plan["script_manifest_sha256"])
                self.assertEqual(demo["example_csv_sha256"],sha256(CSV_SAMPLE.encode()).hexdigest())
                self.assertEqual(demo["algorithm"],"stdlib_python_csv_and_date_v1")
                self.assertEqual(demo["evidence_packet_sha256"],
                    sha256(canonical({k:v for k,v in demo.items()
                                      if k!="evidence_packet_sha256"})).hexdigest())
                self.assertGreaterEqual(len(demo["executed_steps"]),3)
                self.assertLessEqual(len(demo["executed_steps"]),5)
                require_exact_demo(plan,proposal,recipe,demo)
                for flag in (
                    "independent_reviewer_checked_semantic_fit",
                    "source_article_fact_checked",
                    "rights_and_voice_license_approved",
                    "thumbnail_editorial_review_complete",
                    "generative_model_created_script",
                    "youtube_upload_enabled",
                    "youtube_schedule_enabled",
                    "release_authorized",
                ):
                    self.assertIs(demo[flag],False,flag)
                hashes.add(demo["evidence_packet_sha256"])
                kinds.add(demo["recipe_id"])
        self.assertEqual(len(hashes),3)
        self.assertEqual(len(kinds),3)

    def test_text_identifier_real_int_conversion_drops_zeroes(self):
        result=packet_for(0)[3]["computed_outcome"]
        self.assertEqual(result["identifier_string"],"00127")
        self.assertEqual(result["identifier_length"],5)
        self.assertEqual(result["integer_conversion"],127)
        self.assertEqual(result["converted_string"],"127")
        self.assertEqual(result["leading_zeroes_lost"],2)
        self.assertEqual(result["source_rows_preserved"],4)

    def test_date_parser_accepts_three_then_rejects_ambiguous_input(self):
        result=packet_for(1)[3]["computed_outcome"]
        self.assertEqual([v["row"] for v in result["valid_date_rows"]],[1,2,3])
        self.assertEqual(result["invalid_date_rows"],[{"row":4,"raw":"11/04/26"}])
        self.assertEqual(result["source_rows_preserved"],4)
        self.assertFalse(result["ambiguous_date_automatically_fixed"])

    def test_duplicate_detector_flags_both_source_rows_and_never_deletes(self):
        result=packet_for(2)[3]["computed_outcome"]
        self.assertEqual(result["distinct_identifier_count"],3)
        self.assertEqual(result["source_rows_preserved"],4)
        self.assertEqual(result["rows_deleted"],0)
        self.assertEqual(result["duplicate_conflicts"],[
            {"member_id":"00127","first_row":1,"repeat_row":3,
             "joining_dates_differ":True,"statuses_differ":False}
        ])

    def test_unrecognized_or_python_code_string_recipe_cannot_execute(self):
        plan,proposal,_,_=packet_for(0)
        for recipe in (
            "__import__('os').system('echo unsafe')","unknown",
            "exec", "", None, 0,
        ):
            with self.subTest(recipe=recipe),self.assertRaises(ExecutedDemoError):
                build_executed_demo(plan,proposal,recipe)

    def test_wrong_topic_recipe_is_not_silently_auto_mapped(self):
        for index in range(3):
            plan,proposal,recipe,_=packet_for(index)
            for other in set(RECIPES)-{recipe}:
                with self.subTest(index=index,other=other),self.assertRaises(ExecutedDemoError):
                    build_executed_demo(plan,proposal,other)

    def test_forged_title_and_walkthrough_are_denied_before_data(self):
        plan,proposal,recipe,_=packet_for(0)
        bad=deepcopy(proposal)
        bad["title"]="New identity claim with no signed backing"
        with self.assertRaises(ExecutedDemoError):
            build_executed_demo(plan,bad,recipe)
        bad=deepcopy(proposal)
        bad["example_walkthrough"]="A generic slideshow without runnable code"
        with self.assertRaises(ExecutedDemoError):
            build_executed_demo(plan,bad,recipe)
        bad=deepcopy(proposal)
        bad["narration"]="Unrelated words describing a new topic."
        with self.assertRaises(ExecutedDemoError):
            build_executed_demo(plan,bad,recipe)

    def test_packet_result_tampering_cannot_be_used_in_animation(self):
        plan,proposal,recipe,packet=packet_for(1)
        changed=deepcopy(packet)
        changed["computed_outcome"]["invalid_date_rows"]=[]
        with self.assertRaises(ExecutedDemoError):
            require_exact_demo(plan,proposal,recipe,changed)

    def test_packet_step_tampering_cannot_fake_supported_claim(self):
        plan,proposal,recipe,packet=packet_for(0)
        altered=deepcopy(packet)
        altered["executed_steps"][2]["after"]="Converted text is unchanged"
        with self.assertRaises(ExecutedDemoError):
            require_exact_demo(plan,proposal,recipe,altered)

    def test_packet_digest_self_upgrade_without_underlying_review_rejected(self):
        plan,proposal,recipe,packet=packet_for(2)
        altered=deepcopy(packet)
        altered["source_article_fact_checked"]=True
        altered["evidence_packet_sha256"]=sha256(canonical({
            k:v for k,v in altered.items() if k!="evidence_packet_sha256"})).hexdigest()
        with self.assertRaises(ExecutedDemoError):
            require_exact_demo(plan,proposal,recipe,altered)

    def test_packet_replay_to_other_channel_episode_rejected(self):
        plan,proposal,recipe,packet=packet_for(0)
        other=staged_plan(2)
        with self.assertRaises(ExecutedDemoError):
            require_exact_demo(other,proposal,recipe,packet)

    def test_script_plan_tamper_does_not_turn_into_fact_approval(self):
        plan,proposal,recipe,packet=packet_for(0)
        changed=deepcopy(plan)
        changed["rights_approved"]=True
        with self.assertRaises(ValueError):
            build_executed_demo(changed,proposal,recipe)

    def test_every_step_provenance_is_bounded_and_text_only(self):
        for i in range(3):
            steps=packet_for(i)[3]["executed_steps"]
            for row in steps:
                self.assertEqual(set(row),{
                    "label","before_title","before","after_title","after","takeaway"
                })
                self.assertTrue(all(isinstance(v,str) and 1<=len(v)<=150
                                    for v in row.values()))

    def test_unknown_primitive_values_are_not_valid_viewer_claims(self):
        plan,proposal,recipe,packet=packet_for(0)
        altered=dict(packet,executed_steps=None)
        with self.assertRaises(ExecutedDemoError):
            require_exact_demo(plan,proposal,recipe,altered)


if __name__=="__main__":
    unittest.main()
