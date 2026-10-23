"""FlowMinute Flow pilot: side-effect-free credit/release and intake regression."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from autopilot.flow_cinematic_handoff import (
    build_plan, validate_source_package, validate_import_receipt, FlowHandoffError
)

PACK = (Path(__file__).resolve().parents[1] / "content" / "flow"
        / "oct24_cinematic_flow_scene_package.json")

def loaded():
    return json.loads(PACK.read_text(encoding="utf-8"))

class FlowHandoffTests(unittest.TestCase):
    def test_current_package_is_valid_draft(self):
        validate_source_package(loaded())

    def test_one_pilot_is_15_estimated_not_spent_credits(self):
        p=build_plan(loaded())
        self.assertEqual(p["clip_count"],1)
        self.assertEqual(p["estimated_flow_credits"],15)
        self.assertEqual(p["real_credits_spent"],0)
        self.assertFalse(p["generation_authorized_by_this_plan"])

    def test_lean_day_is_five_real_3d_anchor_shots(self):
        p=build_plan(loaded(),mode="lean_day")
        self.assertEqual(p["clip_count"],5)
        self.assertEqual(p["estimated_flow_credits"],75)
        self.assertEqual(p["cinematic_seconds_planned"],50)
        self.assertEqual(p["non_cinematic_seconds_still_to_produce"],
                         {"fm_20261024_short_en":38,
                          "fm_20261024_short_hi":38,
                          "fm_20261024_long_hi":270})
        self.assertFalse(p["youtube_schedule_verified"])

    def test_legacy_full_plan_is_more_expensive(self):
        p=build_plan(loaded(),mode="full_keyshots")
        self.assertEqual(p["clip_count"],16)
        self.assertEqual(p["estimated_flow_credits"],240)
        self.assertEqual(p["raw_ai_generated_seconds"],160)
        self.assertEqual(p["cinematic_seconds_planned"],156)
        self.assertEqual(p["trim_seconds_by_episode"],{"fm_20261024_short_en":2,
            "fm_20261024_short_hi":2,"fm_20261024_long_hi":0})

    def test_price_is_assumption_not_live_credit(self):
        p=build_plan(loaded(),price=18)
        self.assertEqual(p["estimated_flow_credits"],18)
        self.assertIsNone(p["actual_available_credits"])

    def test_synthetic_receipts_do_not_make_media_releasable(self):
        selected=build_plan(loaded())["clips"][0]
        receipt={"episode_id":selected["episode_id"],"clip_id":selected["clip_id"],
                 "sha256":"1"*64,"duration_seconds":10,
                 "orientation":"9:16","source":"user_supplied_file",
                 "file_name":"flow_pilot_take1.mp4"}
        result=validate_import_receipt(receipt, selection=selected)
        self.assertFalse(result["ready_for_youtube"])
        self.assertFalse(result["rights_reviewed"])

    def test_bad_or_empty_receipt_rejected(self):
        selected=build_plan(loaded())["clips"][0]
        with self.assertRaises(FlowHandoffError):
            validate_import_receipt({},selection=selected)

    def test_parent_paths_rejected(self):
        selected=build_plan(loaded())["clips"][0]
        receipt={"episode_id":selected["episode_id"],"clip_id":selected["clip_id"],
                 "sha256":"1"*64,"duration_seconds":10,
                 "orientation":"9:16","source":"user_supplied_file",
                 "file_name":"../flow_pilot_take1.mp4"}
        with self.assertRaises(FlowHandoffError):
            validate_import_receipt(receipt,selection=selected)

    def test_mismatched_aspect_rejected(self):
        selected=build_plan(loaded())["clips"][0]
        receipt={"episode_id":selected["episode_id"],"clip_id":selected["clip_id"],
                 "sha256":"1"*64,"duration_seconds":10,"orientation":"16:9",
                 "source":"google_flow_download","file_name":"take.mp4"}
        with self.assertRaises(FlowHandoffError):
            validate_import_receipt(receipt,selection=selected)

    def test_no_self_created_flow_id_in_draft(self):
        p=loaded();p["episodes"][0]["clips"][0]["flow_asset_id"]="invented"
        with self.assertRaises(FlowHandoffError):
            validate_source_package(p)

    def test_no_fabricated_live_credit_balance(self):
        p=loaded();p["credit_calculation"]["actual_available_credits"]=500
        with self.assertRaises(FlowHandoffError):
            validate_source_package(p)

    def test_cannot_relabel_video_as_generated(self):
        p=loaded();p["episodes"][0]["clips"][0]["clip_status"]="RENDERED"
        with self.assertRaises(FlowHandoffError):
            validate_source_package(p)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(FlowHandoffError):build_plan(loaded(),mode="bill_me")

    def test_bool_price_not_accepted(self):
        with self.assertRaises(FlowHandoffError):build_plan(loaded(),price=True)

    def test_duplicate_clips_rejected(self):
        p=loaded();p["episodes"][0]["clips"].append(deepcopy(p["episodes"][0]["clips"][0]))
        with self.assertRaises(FlowHandoffError):validate_source_package(p)

if __name__=="__main__":
    unittest.main()
