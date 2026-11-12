"""Clivox A4 editorial: source-free storyboards must never authorize media or release."""
from __future__ import annotations

import copy
import json
import unittest

from scripts.branch3_a4_editorial import FIXTURE,EditorialHold,check_script

def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

class A4EditorialTests(unittest.TestCase):
    def test_valid_original_hypothesis_still_held(self):
        r=check_script(fixture())
        self.assertEqual(r["status"],"HOLD_UNTIL_VERIFIED_RIGHTS_AND_EDITORIAL_REVIEW")
        self.assertEqual(r["total_duration_seconds"],40)
        self.assertGreaterEqual(r["original_narration_word_count"],30)
        self.assertGreaterEqual(r["original_planned_duration_seconds"],20)
        self.assertEqual(r["licensed_source_placeholder_seconds"],14)
        for key in ("originality_quality_human_review_completed",
                    "source_quote_fact_checked","creator_license_verified",
                    "source_download_authorized","video_render_authorized",
                    "youtube_upload_authorized","youtube_schedule_authorized"):
            self.assertFalse(r[key])
        self.assertRegex(r["editorial_plan_sha256"],r"^[a-f0-9]{64}$")

    def test_reproducible_sha(self):
        self.assertEqual(check_script(fixture()),check_script(copy.deepcopy(fixture())))

    def test_wrong_channel_and_unreleased_state(self):
        for key,value in (
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("state","READY_FOR_UPLOAD"),
            ("schema_version",2),
            ("source_video_id","bad"),
            ("source_url","https://evil.invalid/test"),
            ("category","other"),
        ):
            f=fixture()
            f[key]=value
            with self.subTest(key=key),self.assertRaises(EditorialHold):
                check_script(f)

    def test_cannot_make_up_source_transcript_or_timestamps(self):
        for key,val in (
            ("full_source_watched",True),
            ("precise_clip_start_ms",3894000),
            ("precise_clip_end_ms",4000000),
            ("transcript_verified",True),
            ("speaker_quotation_included",True),
            ("premise_verified",True),
        ):
            f=fixture()
            f["research_context"][key]=val
            with self.subTest(key=key),self.assertRaises(EditorialHold):
                check_script(f)
        f=fixture()
        f["beats"][2]["source_quotation"]="A made-up Bert quote"
        with self.assertRaises(EditorialHold):
            check_script(f)

    def test_cannot_approach_source_placeholder_as_media(self):
        for key,val in (
            ("original_narration","A fake quote"),
            ("visual","original_animation"),
        ):
            f=fixture()
            f["beats"][2][key]=val
            with self.subTest(key=key),self.assertRaises(EditorialHold):
                check_script(f)

    def test_all_release_flags_remain_false(self):
        for flag in fixture()["release_locks"]:
            f=fixture()
            f["release_locks"][flag]=True
            with self.subTest(flag=flag),self.assertRaises(EditorialHold):
                check_script(f)

    def test_no_fake_originality_review(self):
        for key in ("factual_claims_checked","human_originality_review_passed"):
            f=fixture()
            f["creative_intent"][key]=True
            with self.subTest(key=key),self.assertRaises(EditorialHold):
                check_script(f)

    def test_requires_satisfying_timeline(self):
        for idx,key,value in ((1,"start_s",3),
                              (1,"start_s",1),
                              (0,"end_s",10),
                              (4,"end_s",41),
                              (2,"role","original_analysis"),
                              (0,"role","context"),
                              (4,"role","hook")):
            f=fixture()
            f["beats"][idx][key]=value
            with self.subTest(idx=idx,key=key,value=value),self.assertRaises(EditorialHold):
                check_script(f)

    def test_requires_substantive_original_story_design(self):
        f=fixture()
        f["beats"][3]["original_narration"]="It is funny."
        with self.assertRaises(EditorialHold):
            check_script(f)
        f=fixture()
        f["beats"][0]["original_narration"]="This is a very very very very very long impossible hook to speak in two seconds"
        with self.assertRaises(EditorialHold):
            check_script(f)

    def test_brand_music_spinner_and_stock_clip_denied(self):
        cases=(
            ("no_looping_spinner_overlay",False),
            ("no_unlicensed_music",False),
            ("third_party_visuals_in_storyboard",True),
            ("captions_are_substantive_editorial_substitute",True),
            ("paid_promotion_status","NOT_REQUIRED"),
            ("safe_vertical_caption_margin_px",0),
        )
        for key,value in cases:
            f=fixture()
            f["design"][key]=value
            with self.subTest(key=key),self.assertRaises(EditorialHold):
                check_script(f)

    def test_treat_youtube_media_as_unlicensed(self):
        for key,val in (("licensed_media_attached",True),
                        ("original_audio_recorded",True),
                        ("width",1920),("height",1080)):
            f=fixture()
            f["format"][key]=val
            with self.subTest(key=key),self.assertRaises(EditorialHold):
                check_script(f)

    def test_all_5_categories_supported_without_media(self):
        for category in ("gaming","livestream","comedy","entertainment","podcast_interview"):
            f=fixture()
            f["category"]=category
            # Synthetic generic source case; do not misclassify YMH's comedy program.
            if category!="comedy":
                f["source_case_id"]="clivox_synthetic_test_case"
                f["source_video_id"]="AAAAAAAAAAA"
                f["source_url"]="https://www.youtube.com/watch?v=AAAAAAAAAAA"
            with self.subTest(category=category):
                result=check_script(f)
                self.assertEqual(result["category"],category)
                self.assertFalse(result["source_download_authorized"])

    def test_untrusted_script_markup_and_extra_keys_rejected(self):
        for field,place in (("A script\ninjection","original_narration"),
                            ("<script>do bad things</script>","editor_note")):
            f=fixture()
            f["beats"][0][place]=field
            with self.subTest(place=place),self.assertRaises(EditorialHold):
                check_script(f)
        f=fixture()
        f["creator_permission_verified"]=True
        with self.assertRaises(EditorialHold):
            check_script(f)

if __name__=="__main__":
    unittest.main()
