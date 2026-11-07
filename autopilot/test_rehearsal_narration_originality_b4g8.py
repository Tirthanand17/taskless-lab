"""B4g8 real original rehearsal script hash history, no script or YouTube uploads."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZipFile,ZIP_DEFLATED
import unittest

from autopilot.test_nonfactual_narration_rehearsal_b4d9 import pipeline
from autopilot.nonfactual_narration_rehearsal import build_nonfactual_rehearsals
from autopilot.rehearsal_narration_originality_b4g8 import (
    STATUS,NarrationOriginalityRefused,inspect_narration_originality,
)
from autopilot.recent_research_history import (
    HISTORY_STATUS,HistoryRefused,_receipt_from_archive,
)
from autopilot.test_recent_research_history_b4d8 import sample_receipts


def source_synthetic():
    return build_nonfactual_rehearsals(*pipeline())


def empty_hist():
    return {
        "status":HISTORY_STATUS,
        "verified_prior_research_days":0,
        "verified_prior_script_review_days":0,
        "historical_script_sha256":[],
        "not_a_youtube_publication_readback":True,
        "video_release_authorized":False,
    }


class UniqueSpokenNarrationSourceTests(unittest.TestCase):
    def setUp(self):
        self.samples=source_synthetic()
        self.history=empty_hist()

    def test_real_seventeen_scenes_generate_only_three_public_sha256_proofs(self):
        receipt=inspect_narration_originality(self.samples,self.history)
        self.assertEqual(receipt["status"],STATUS)
        self.assertEqual(receipt["plan_day_ist"],self.samples["research_day_ist"])
        self.assertEqual(receipt["episode_slots"],["short_am","long","short_pm"])
        self.assertEqual(len(receipt["script_fingerprints_sha256"]),3)
        self.assertEqual(len(set(receipt["script_fingerprints_sha256"])),3)
        self.assertTrue(all(len(x)==64 for x in receipt["script_fingerprints_sha256"]))
        self.assertEqual(receipt["exact_repeat_detected_per_slot"],
                         [False,False,False])
        self.assertFalse(receipt["unique_against_every_prior_day_proven"])
        self.assertEqual(receipt["previous_verified_receipt_days_with_script_hashes"],0)
        self.assertFalse(receipt["all_three_daily_videos_factually_original_or_rights_checked"])
        self.assertFalse(receipt["youtube_release_authorized"])
        data=json.dumps(receipt)
        for ep in self.samples["three_episodes"]:
            for scene in ep["scenes"]:
                phrase=scene["original_voiceover_rehearsal_text"][:30]
                self.assertNotIn(phrase,data)
        self.assertNotIn("https://",data)

    def test_changing_day_episode_id_and_headline_cannot_forge_novel_spoken_video(self):
        original=inspect_narration_originality(self.samples,self.history)
        next_day=deepcopy(self.samples)
        next_day["research_day_ist"]="2026-11-08"
        for ep in next_day["three_episodes"]:
            ep["episode_id"]=ep["episode_id"].replace("20261107","20261108")
            ep["original_working_title_not_news_headline"]="Entirely new headline"
        self.history["historical_script_sha256"]=sorted(
            original["script_fingerprints_sha256"])
        self.history["verified_prior_research_days"]=1
        self.history["verified_prior_script_review_days"]=1
        result=inspect_narration_originality(next_day,self.history)
        self.assertEqual(result["script_fingerprints_sha256"],
                         original["script_fingerprints_sha256"])
        self.assertEqual(result["exact_repeat_detected_per_slot"],
                         [True,True,True])
        self.assertTrue(result["exact_repeat_detected_in_previous_7_day_receipts"])
        self.assertFalse(result["youtube_release_authorized"])
        changed=deepcopy(next_day)
        changed["three_episodes"][0]["scenes"][0][
            "original_voiceover_rehearsal_text"]+=" New original example."
        new=inspect_narration_originality(changed,self.history)
        self.assertEqual(new["exact_repeat_detected_per_slot"],
                         [False,True,True])

    def test_bogus_prior_hashes_approvals_or_source_identity_refused(self):
        for mutation in (
            lambda x:x["history"].update(
                historical_script_sha256=["not-sha256"]),
            lambda x:x["history"].update(
                historical_script_sha256=["f"*64,"f"*64]),
            lambda x:x["history"].update(
                verified_prior_script_review_days=2),
            lambda x:x["history"].update(video_release_authorized=True),
            lambda x:x["samples"].update(release_authorized=True),
            lambda x:x["samples"]["three_episodes"][0].update(
                episode_id="fm_20261107_short_pm"),
            lambda x:x["samples"]["three_episodes"][1].update(
                factual_news_narration_written=True),
            lambda x:x["samples"]["three_episodes"][2]["scenes"][0].update(
                source_quote_display_allowed=True),
        ):
            ctx={"samples":deepcopy(self.samples),
                 "history":deepcopy(self.history)}
            mutation(ctx)
            with self.subTest(label=str(mutation)),self.assertRaises(
                    NarrationOriginalityRefused):
                inspect_narration_originality(ctx["samples"],ctx["history"])

    def test_safe_public_receipt_option_remains_unapproved_and_hash_integrity_holds(self):
        from autopilot.daily_editorial_board import build_editorial_board,sanitized_public_receipt
        from autopilot.daily_evidence_bundle import build_retained_draft_receipt,DailyEvidenceRefused
        from autopilot.test_daily_editorial_board import inputs
        from autopilot.reconcile_daily_editorial_plan import align_plan_to_editorial_board
        original,scout,evidence=inputs()
        board=build_editorial_board(original,scout,evidence)
        plan=align_plan_to_editorial_board(original,board,scout,evidence)
        preview=inspect_narration_originality(self.samples,self.history)
        receipt=build_retained_draft_receipt(
            plan,evidence,editorial_receipt=sanitized_public_receipt(board),
            originality_report=preview)
        saved=receipt["unapproved_rehearsal_narration_originality"]
        self.assertEqual(saved["script_fingerprints_sha256"],
                         preview["script_fingerprints_sha256"])
        self.assertFalse(saved["youtube_release_authorized"])
        self.assertFalse(receipt["release_authorized"])
        self.assertFalse(receipt["youtube_publishing_enabled"])
        self.assertNotIn("actual",json.dumps(saved).lower()[:2])
        altered=deepcopy(preview)
        altered["youtube_release_authorized"]=True
        with self.assertRaises(DailyEvidenceRefused):
            build_retained_draft_receipt(
                plan,evidence,editorial_receipt=sanitized_public_receipt(board),
                originality_report=altered)

    def test_legacy_research_receipt_has_zero_proven_script_history(self):
        from autopilot.test_recent_research_history_b4d8 import zip_receipts
        editorial,research,scout=sample_receipts()
        doc=_receipt_from_archive(
            zip_receipts(editorial,research),
            __import__("datetime").date(2026,11,8))
        self.assertEqual(doc["historical_spoken_sha256"],set())

    def test_prior_trusted_research_receipt_parses_only_exact_safe_script_hashes(self):
        from autopilot.test_recent_research_history_b4d8 import zip_receipts
        from datetime import date
        editorial,research,scout=sample_receipts()
        preview=inspect_narration_originality(self.samples,self.history)
        research["unapproved_rehearsal_narration_originality"]={
            k:preview[k] for k in (
                "status","plan_day_ist","episode_slots",
                "script_fingerprints_sha256","source_fingerprint_domain",
                "unique_against_every_prior_day_proven",
                "all_three_daily_videos_factually_original_or_rights_checked",
                "actual_human_factual_and_rights_approvals",
                "youtube_release_authorized",
            )}
        self.assertEqual(research["plan_day_ist"],"2026-11-07")
        doc=_receipt_from_archive(
            zip_receipts(editorial,research),date(2026,11,8))
        self.assertEqual(doc["historical_spoken_sha256"],
                         set(preview["script_fingerprints_sha256"]))
        # Adding unapproved metadata without updating an authoritative
        # research-receipt root MUST be spotted by future source-gate tests.
        bad=deepcopy(research)
        bad["unapproved_rehearsal_narration_originality"]["youtube_release_authorized"]=True
        with self.assertRaises(HistoryRefused):
            _receipt_from_archive(zip_receipts(editorial,bad),
                                  date(2026,11,8))


if __name__=="__main__":
    unittest.main()
