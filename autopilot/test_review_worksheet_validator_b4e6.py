"""Adversarial B4e6 worksheet validator tests; no external media or YouTube."""
from copy import deepcopy
from hashlib import sha256
import unittest

from autopilot.manual_rehearsal_review_export_b4e3 import EXPORT_STATUS, SLOT_NAMES
from autopilot.review_worksheet_validator_b4e6 import inspect, ReviewValidationError, CHECKS


def cases():
    videos = []
    reports = []
    for idx, (slot, filename, count) in enumerate(SLOT_NAMES):
        digest = sha256(slot.encode()).hexdigest()
        secs = (57.8, 241.5, 57.3)[idx]
        reports.append(dict(slot=slot, file=filename, sha256=digest,
            measured_audio_seconds=secs, original_voiced_scene_count=count,
            all_rights_and_fact_approvals=False, youtube_upload_authorized=False))
        videos.append(dict(slot=slot, filename=filename, sha256=digest,
            duration_seconds_measured_pcm=secs,
            scenes=[dict(scene_number=k, review_status="NOT_REVIEWED",
                         timecode_mm_ss=None, defect_notes=None)
                    for k in range(1, count+1)],
            checks={c:"NOT_REVIEWED" for c in CHECKS},
            overall_human_decision="NOT_REVIEWED"))
    manifest = dict(status=EXPORT_STATUS, publishing_authorized=False,
        youtube_releases=0, rights_and_owner_approvals=0,
        factual_news_claims_reviewed=0, videos=reports)
    worksheet = dict(schema="B4E5_SHA_BOUND_BLANK_HUMAN_QA_WORKSHEET_V1",
        synthetic_educational_media_only=True, human_review_completed=False,
        factual_news_approved=False, rights_approved=False,
        youtube_publish_authorized=False, videos=videos)
    return manifest, worksheet


class WorksheetValidatorTests(unittest.TestCase):
    def test_blank_worksheet_remains_unreviewed(self):
        a,b = cases()
        r = inspect(a,b)
        self.assertEqual(r["scene_count"],17)
        self.assertEqual(r["self_reported_reviewed_scenes"],0)
        self.assertEqual(r["individual_checks_not_reviewed"],47)
        self.assertFalse(r["youtube_release_authorized"])

    def test_timecoded_failures_are_counted_not_approved(self):
        a,b=cases()
        s=b["videos"][0]["scenes"][0]
        s.update(review_status="FAIL", timecode_mm_ss="00:04",
                 defect_notes="Subtitle overlaps with source-free footer")
        b["videos"][0]["checks"]["caption_readability_mobile_safe_area_and_spelling"]="FAIL"
        b["videos"][0]["overall_human_decision"]="FAIL"
        r=inspect(a,b)
        self.assertEqual(r["needs_defect_followup_count"],2)
        self.assertEqual(r["self_reported_reviewed_scenes"],1)
        self.assertFalse(r["independent_human_observation_verified"])

    def test_hash_and_duration_binding_rejects_other_video(self):
        a,b=cases()
        for change in (
            lambda: b["videos"][1].update(sha256="f"*64),
            lambda: b["videos"][1].update(duration_seconds_measured_pcm=17),
            lambda: b["videos"][1].update(filename="different.mp4"),
        ):
            a,b=cases();change()
            with self.assertRaises(ReviewValidationError):inspect(a,b)

    def test_unsafe_approval_forgery_rejected(self):
        for name in ("human_review_completed", "factual_news_approved",
                     "rights_approved", "youtube_publish_authorized"):
            a,b=cases()
            b[name]=True
            with self.subTest(name=name),self.assertRaises(ReviewValidationError):
                inspect(a,b)
        a,b=cases()
        a["publishing_authorized"]=True
        with self.assertRaises(ReviewValidationError):inspect(a,b)

    def test_reordered_scene_and_missing_check_fail(self):
        a,b=cases()
        b["videos"][1]["scenes"][0]["scene_number"]=2
        with self.assertRaises(ReviewValidationError):inspect(a,b)
        a,b=cases()
        del b["videos"][0]["checks"][next(iter(CHECKS))]
        with self.assertRaises(ReviewValidationError):inspect(a,b)

    def test_failed_scene_needs_valid_time_and_explanation(self):
        for stamp, note in [(None,"readable wrong"),("99:99","readable wrong"),
                            ("01:59","readable wrong"),("00:03","bad")]:
            a,b=cases()
            b["videos"][0]["scenes"][0].update(review_status="FAIL",
                timecode_mm_ss=stamp,defect_notes=note)
            with self.subTest(stamp=stamp),self.assertRaises(ReviewValidationError):
                inspect(a,b)

    def test_overall_pass_is_not_implied_from_partial_review(self):
        a,b=cases()
        b["videos"][0]["overall_human_decision"]="PASS"
        with self.assertRaises(ReviewValidationError):inspect(a,b)

    def test_self_reported_complete_pass_is_still_not_publishable(self):
        a,b=cases()
        for v in b["videos"]:
            v["checks"]={c:"PASS" for c in CHECKS}
            for s in v["scenes"]:
                s.update(review_status="PASS",timecode_mm_ss="00:01")
            v["overall_human_decision"]="PASS"
        r=inspect(a,b)
        self.assertEqual(r["self_reported_reviewed_scenes"],17)
        self.assertFalse(r["youtube_release_authorized"])
        self.assertFalse(r["copyright_and_factual_source_verified"])


if __name__ == "__main__":
    unittest.main()
