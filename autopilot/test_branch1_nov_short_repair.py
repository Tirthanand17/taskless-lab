"""Branch1 B1q1 real receipt scan, no-spinner source artwork and honest analytics loop."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autopilot.branch1_nov_repair_inventory import (
    STATUS as AUDIT_STATUS,START,END,CHANNEL,
    NovAuditRejected,build_nov_repair_inventory,
)
from autopilot.branch1_no_spinner_storyboard import (
    STATUS as ART_STATUS,NoSpinnerVisualRejected,
    storyboard_cues,draw_source_keyframe,render_three_source_shorts,
)
from autopilot.creative_iteration_evidence_loop import (
    MeasuredShort,CreativeCycleRejected,compare_creative_versions,
    iterate_once,BASELINE,VERSION,STATUS_HOLD,STATUS_REVIEW,
)

ROOT=Path(__file__).resolve().parents[1]

class Branch1NovemberEvidenceTests(unittest.TestCase):
    def test_actual_nov_05_through_11_repo_receipts_are_not_mistaken_for_live_youtube(self):
        result=build_nov_repair_inventory(ROOT)
        self.assertEqual(result["status"],AUDIT_STATUS)
        self.assertEqual(result["channel_expected"],CHANNEL)
        self.assertEqual(result["date_start_ist"],"2026-11-05")
        self.assertEqual(result["date_end_ist"],"2026-11-11")
        self.assertEqual(result["expected_three_slots"],21)
        self.assertEqual(len(result["slots"]),21)
        self.assertEqual(result["historical_repo_receipt_count"],4)
        self.assertEqual(result["no_repo_evidence_slot_count"],17)
        self.assertFalse(result["real_youtube_current_readback_performed"])
        self.assertFalse(result["owner_screenshot_specific_original_video_ids_verified"])
        self.assertFalse(result["original_video_bytes_in_repo_or_replacement_ready"])
        self.assertTrue(result["never_delete_or_unpublish_original_automatically"])
        self.assertEqual(len({(r["date_ist"],r["slot"]) for r in result["slots"]}),21)
        self.assertTrue(all(r["needs_readonly_owner_youtube_videos_list_for_current_status"]
                            for r in result["slots"]))
        found=[r for r in result["slots"] if r["historical"]]
        self.assertEqual(len(found),4)
        self.assertEqual({r["date_ist"] for r in found},
                         {"2026-11-05","2026-11-06","2026-11-07"})
        self.assertEqual({r["historical"]["original_id"] for r in found},{
            "fm_20261105_ai_voice_cloning_callback_short_en",
            "fm_20261106_photo_gps_metadata_short_en",
            "fm_20261106_passkeys_phishing_long_en",
            "fm_20261107_incognito_not_invisible_short_en",
        })
        for row in found:
            prior=row["historical"]
            self.assertTrue(prior["historically_scheduled_verified"])
            self.assertTrue(prior["historical_confirmation_not_live_readback"])
            self.assertTrue(prior["source_caption_manifest_in_github"])
            self.assertFalse(prior["new_replacement_uploaded"])
            self.assertFalse(prior["same_video_id_binary_replacement_possible"])

    def test_duplicate_or_forged_remote_future_slot_is_rejected_not_marked_verified(self):
        with tempfile.TemporaryDirectory() as root:
            d=Path(root)/"state"/"scheduled"
            d.mkdir(parents=True)
            eid="fm_20261108_fake_illustrative_short_en"
            obj={
                "id":eid,"date_local":"2026-11-08",
                "scheduled_local":"2026-11-08T11:00:00+05:30",
                "youtube_video_id":"AbCdEf12345",
                "remote_publish_at_utc":"2026-11-09T05:30:00Z",
                "status":"scheduled_verified",
            }
            (d/(eid+".json")).write_text(json.dumps(obj),encoding="utf8")
            with self.assertRaises(NovAuditRejected):
                build_nov_repair_inventory(Path(root))


@unittest.skipUnless(
    __import__("importlib").util.find_spec("PIL") is not None,
    "Native 1080x1920 original drawing requires Pillow and DejaVu CI runner",
)
class NoRepeatedSpinnerSourceCreativeTests(unittest.TestCase):
    def _source(self,name):
        p=ROOT/"content"/"episodes"/(name+".json")
        return json.loads(p.read_text(encoding="utf8"))

    def test_circular_spinner_cannot_be_drawn_by_our_source_renderer(self):
        import autopilot.branch1_no_spinner_storyboard as mod
        source=inspect.getsource(mod)
        self.assertNotIn("d.ellipse(",source)
        self.assertNotIn("d.arc(",source)
        self.assertNotIn("d.pieslice(",source)
        self.assertNotIn("rotate(",source)
        self.assertNotIn("while True",source)
        self.assertNotIn("animationIterationCount",source)

    def test_all_three_actual_known_november_source_shorts_source_locked(self):
        for eid in (
            "fm_20261105_ai_voice_cloning_callback_short_en",
            "fm_20261106_photo_gps_metadata_short_en",
            "fm_20261107_incognito_not_invisible_short_en",
        ):
            source=self._source(eid)
            with self.subTest(episode=eid):
                cues=storyboard_cues(source)
                self.assertGreaterEqual(len(cues),5)
                self.assertTrue(all(x["no_circle_arc_or_spinner"] for x in cues))
                self.assertTrue(all(x["unbounded_repeat_count"]==0 for x in cues))
                self.assertNotEqual(cues[0]["motion_mode"],cues[1]["motion_mode"])
                self.assertEqual(
                    {x["source_text_sha256"] for x in cues},
                    {sha256(c["text"].encode()).hexdigest() for c in source["captions"]},
                )
                image_a,receipt=draw_source_keyframe(source,0,.2)
                image_b,_=draw_source_keyframe(source,0,.82)
                self.assertEqual(image_a.size,(1080,1920))
                self.assertEqual(receipt["status"],ART_STATUS)
                self.assertFalse(receipt["youtube_uploaded"])
                self.assertFalse(receipt["full_video_encoded"])
                self.assertNotEqual(
                    sha256(image_a.tobytes()).hexdigest(),
                    sha256(image_b.tobytes()).hexdigest())

    def test_actual_18_source_art_pngs_sha_unchanged_no_upload(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"new-shots"
            report=render_three_source_shorts(ROOT,output)
            self.assertEqual(report["status"],ART_STATUS)
            self.assertEqual(report["total_original_physical_png_keyframes"],18)
            self.assertEqual(len(list(output.glob("*.png"))),18)
            self.assertFalse(report["video_or_audio_replacement_encoded"])
            self.assertFalse(report["youtube_upload_enabled"])
            self.assertFalse(report["owner_full_watch_listen_and_rights_approved"])
            for row in report["items"]:
                p=output/row["file"]
                self.assertEqual(p.stat().st_size,row["bytes"])
                self.assertEqual(sha256(p.read_bytes()).hexdigest(),row["sha256"])
                self.assertTrue(row["no_circle_spinner_drawn"])
            with self.assertRaises(NoSpinnerVisualRejected):
                render_three_source_shorts(ROOT,output)

    def test_invalid_source_phase_and_fake_title_rejected(self):
        orig=self._source("fm_20261106_photo_gps_metadata_short_en")
        bad=dict(orig)
        bad["captions"]=[{"start":0,"end":20,"text":"Narration never recorded"}]
        with self.assertRaises(NoSpinnerVisualRejected):
            storyboard_cues(bad)
        for phase in (-.1,1.1,"forever"):
            with self.assertRaises(NoSpinnerVisualRejected):
                draw_source_keyframe(orig,0,phase)


class BoundedRealEngagementFeedbackTests(unittest.TestCase):
    def _sample(self,i,variant,percentage):
        chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        code=f"{i:011d}"
        return MeasuredShort(video_id=code,
                             topic_family="tech_safety",visual_variant=variant,
                             age_hours=72,engaged_views=280,views=460,
                             average_view_percentage=percentage,
                             average_view_duration=29.5,
                             source="official_youtube_analytics")

    def test_empty_or_one_sided_data_never_fabricates_audience_improvement(self):
        score=compare_creative_versions([],topic_family="tech_safety")
        self.assertEqual(score["status"],STATUS_HOLD)
        self.assertIsNone(score["claimed_incremental_causal_engagement_lift"])
        one=[self._sample(i,BASELINE,55) for i in range(6)]
        self.assertEqual(compare_creative_versions(one,topic_family="tech_safety")["status"],STATUS_HOLD)

    def test_six_matched_per_arm_are_observational_not_causal_or_auto_publish(self):
        old=[self._sample(i,BASELINE,50) for i in range(6)]
        new=[self._sample(i+6,VERSION,60) for i in range(6)]
        result=iterate_once(records=old+new,topic_family="tech_safety",latest_candidate=VERSION)
        self.assertEqual(result["status"],STATUS_REVIEW)
        self.assertEqual(result["variant_counts"][VERSION],6)
        self.assertEqual(result["observed_percentage_point_difference_not_causal"],10)
        self.assertFalse(result["candidate_approved"])
        self.assertFalse(result["auto_publish"])
        self.assertIsNone(result["claimed_incremental_causal_engagement_lift"])
        second=iterate_once(records=old+new,topic_family="tech_safety",
                            latest_candidate=VERSION,already_changed_this_cycle=True)
        self.assertEqual(second["status"],"ONE_CHANGE_PER_CYCLE_ALREADY_USED")

    def test_fake_stats_duplicate_ids_and_forced_causal_claims_rejected(self):
        bad=self._sample(1,BASELINE,50)
        for sample in (replace(bad,source="fake"),
                       replace(bad,engaged_views=500),
                       replace(bad,views=-2),
                       replace(bad,average_view_percentage=float("nan"))):
            with self.assertRaises(CreativeCycleRejected):
                compare_creative_versions([sample],topic_family="tech_safety")
        with self.assertRaises(CreativeCycleRejected):
            compare_creative_versions([bad,bad],topic_family="tech_safety")

if __name__=="__main__":
    unittest.main()
