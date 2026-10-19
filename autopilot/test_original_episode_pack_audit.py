"""Original 20 October videos: validate candidate storyboards but never upload."""
from copy import deepcopy
import json
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.original_episode_pack_audit import PACK,audit_original_editorial_pack


def load():
    return json.loads(PACK.read_text(encoding="utf-8"))


def audit(model):
    return audit_original_editorial_pack(
        source_json=json.dumps(model,ensure_ascii=False),
    )


class OriginalBilingualProductionPackTests(unittest.TestCase):
    def test_actual_three_script_video_pack_passes_editorial_only(self):
        report=audit_original_editorial_pack()
        self.assertEqual(report["independent_language_lanes"],3)
        self.assertEqual(report["hindi_short_count"],1)
        self.assertEqual(report["english_short_count"],1)
        self.assertEqual(report["hindi_long_count"],1)
        self.assertGreaterEqual(report["total_storyboard_scenes"],25)
        self.assertGreaterEqual(report["source_bound_scene_count"],6)
        self.assertTrue(report["complete_scene_timing_drafts"])
        self.assertTrue(report["all_visual_demonstrations_are_marked_mockups"])
        for key in (
            "licensed_narration_recordings_observed",
            "natural_distinct_voice_verified",
            "spoken_words_independently_transcribed",
            "actual_srt_alignment_verified","real_hd_media_rendered",
            "rights_or_creator_identity_authored",
            "actual_provider_tasks_demo_verified","youtube_upload_authorized",
            "youtube_publishing_authorized",
        ):
            self.assertFalse(report[key])
        self.assertEqual(report["cloud_audio_or_video_jobs_executed"],0)
        self.assertEqual(report["monthly_recurring_infrastructure_inr"],0)
        for marker in ("youtube_video_id","PRIVATE_KEY","oauth_refresh_token"):
            self.assertNotIn(marker,str(report))

    def test_exact_independent_hindi_english_lanes_not_fake_translation(self):
        model=load()
        self.assertEqual(len(model["episodes"]),3)
        self.assertEqual(
            {(e["kind"],e["original_spoken_language"]) for e in model["episodes"]},
            {("short","hi"),("short","en"),("long","hi")},
        )
        heads=[x["segments"][0]["narration"] for x in model["episodes"]]
        self.assertEqual(len(set(heads)),3)
        self.assertNotEqual(
            model["episodes"][0]["title"],model["episodes"][1]["title"],
        )
        self.assertNotEqual(
            model["episodes"][0]["narrator_plan_id"],
            model["episodes"][1]["narrator_plan_id"],
        )

    def test_missing_episode_duplicate_episode_or_wrong_lane_fails(self):
        for edit in ("remove","duplicate","swap_language","wrong_kind","wrong_length"):
            model=load()
            if edit=="remove":model["episodes"].pop()
            if edit=="duplicate":model["episodes"][1]=deepcopy(model["episodes"][0])
            if edit=="swap_language":model["episodes"][0]["original_spoken_language"]="hi"
            if edit=="wrong_kind":model["episodes"][1]["kind"]="long"
            if edit=="wrong_length":model["episodes"][2]["target_duration_seconds"]=479
            with self.subTest(edit=edit),self.assertRaises(WorkflowError):
                audit(model)

    def test_end_of_scene_timing_gap_overlap_invalid_boundary_fails(self):
        for edit in ("gap","overlap","zero","wrong_end","floats"):
            model=load()
            series=model["episodes"][0]["segments"]
            if edit=="gap":series[1]["start_second"]+=1
            if edit=="overlap":series[1]["start_second"]-=1
            if edit=="zero":series[2]["end_second"]=series[2]["start_second"]
            if edit=="wrong_end":series[-1]["end_second"]-=1
            if edit=="floats":series[2]["start_second"]=float(series[2]["start_second"])
            with self.subTest(edit=edit),self.assertRaises(WorkflowError):
                audit(model)

    def test_claim_of_real_recordings_review_or_upload_fails_closed(self):
        for key in (
            "original_footage_and_audio_available",
            "prerecorded_voice_exists","real_asr_word_timing_checked",
            "license_and_consent_verified","actual_provider_demo_executed",
            "original_narrator_identity_verified",
            "actual_thumbnail_rendered","actual_media_encoded",
            "youtube_schedule_verified","private_upload_authorized",
            "public_publish_authorized",
        ):
            model=load()
            model["content_release_policy"][key]=True
            with self.subTest(key=key),self.assertRaises(WorkflowError):
                audit(model)

    def test_banned_budget_and_fake_success_status_rejected(self):
        for edit in ("fee","status","extra","locale","date","revision"):
            model=load()
            if edit=="fee":model["content_release_policy"]["recurring_infrastructure_inr"]=10
            if edit=="status":model["status"]="published"
            if edit=="extra":model["content_release_policy"]["oauth_token"]="SECRET"
            if edit=="locale":model["timezone"]="UTC"
            if edit=="date":model["date_local"]="2026-10-21"
            if edit=="revision":model["schema_version"]="v999"
            with self.subTest(edit=edit),self.assertRaises(WorkflowError):
                audit(model)

    def test_wrong_fact_url_or_untrusted_partner_claim_denied(self):
        for edit in ("url","id","date","extra","missing"):
            model=load()
            source=model["sources"][0]
            if edit=="url":source["url"]="https://look-alike.example/"
            if edit=="id":source["id"]="unverified_video"
            if edit=="date":source["published_date"]="2026-12-20"
            if edit=="extra":source["authored_credentials"]="redacted"
            if edit=="missing":model["sources"].pop(0)
            with self.subTest(edit=edit),self.assertRaises(WorkflowError):
                audit(model)

    def test_fake_factual_source_reference_not_silently_accepted(self):
        for edit in ("unlisted","no_url","empty"):
            model=load()
            chapter=model["episodes"][0]["segments"][0]
            if edit=="unlisted":chapter["source_ids"]=["fake_press_release"]
            if edit=="no_url":chapter["source_ids"]=[{"url":"https://example.org"}]
            if edit=="empty":
                for e in model["episodes"]:
                    for ch in e["segments"]:
                        ch["source_ids"]=[]
            with self.subTest(edit=edit),self.assertRaises(WorkflowError):
                audit(model)

    def test_mock_visual_label_required_every_demonstration(self):
        model=load()
        chapter=model["episodes"][1]["segments"][0]
        self.assertTrue(chapter["original_research_demo"])
        chapter["visual_guide"]="Shopping app live screenshot with a Buy button."
        with self.assertRaises(WorkflowError):
            audit(model)

    def test_original_voice_plan_names_not_legal_or_human_identity(self):
        model=load()
        model["episodes"][0]["narrator_plan_id"]="voice_en_short_oct20_licensed"
        with self.assertRaises(WorkflowError):
            audit(model)
        model=load()
        model["episodes"][1]["narrator_plan_id"]=model["episodes"][0]["narrator_plan_id"]
        with self.assertRaises(WorkflowError):
            audit(model)

    def test_hindi_language_swapped_with_english_draft_is_rejected(self):
        model=load()
        hindi=model["episodes"][1]
        for chapter in hindi["segments"]:
            chapter["narration"]="The agent will perform shopping if you grant permission."
        with self.assertRaises(WorkflowError):
            audit(model)

    def test_english_spoken_track_cannot_be_hindi(self):
        model=load()
        for chapter in model["episodes"][0]["segments"]:
            chapter["narration"]="एजेंट आपके लिए योजना बना सकता है।"
        with self.assertRaises(WorkflowError):
            audit(model)

    def test_false_viral_claim_or_external_link_in_spoken_word_denied(self):
        for phrase in ("guaranteed viral","https://unsafe.example","100% accurate"):
            model=load()
            model["episodes"][0]["segments"][0]["narration"]+=(" "+phrase)
            with self.subTest(phrase=phrase),self.assertRaises(WorkflowError):
                audit(model)

    def test_control_direction_unicode_and_duplicate_titles_denied(self):
        for change in ("control","title","bidi"):
            model=load()
            if change=="control":model["episodes"][0]["title"]="Unsafe\x00title"
            if change=="title":model["episodes"][1]["title"]=model["episodes"][0]["title"]
            if change=="bidi":
                model["episodes"][2]["segments"][0]["narration"]="abc\u202ehidden"
            with self.subTest(change=change),self.assertRaises(WorkflowError):
                audit(model)

    def test_extra_secret_bearing_field_is_not_echoed(self):
        model=load()
        model["episodes"][0]["segments"][0]["private_api_key"]="LEAK_ME_NEVER"
        with self.assertRaises(WorkflowError) as error:
            audit(model)
        self.assertNotIn("LEAK_ME_NEVER",str(error.exception))

    def test_oct20_planned_slots_match_existing_daily_config_but_no_booking(self):
        from pathlib import Path
        base=PACK.parents[2]
        plan=json.loads((base/"state/planned/oct20-pack.json").read_text("utf-8"))
        cadence=json.loads((base/"config/daily-publishing-v1.json").read_text("utf-8"))
        episodes={e["episode_id"]:e for e in load()["episodes"]}
        slots=plan["planned_slots_not_bookings"]
        self.assertEqual(plan["date_local"],"2026-10-20")
        self.assertEqual(plan["timezone"],"Asia/Kolkata")
        self.assertEqual(len(slots),3)
        self.assertEqual(
            [s["local_target"][11:16] for s in slots],
            [s["publish_local"] for s in cadence["cadence"]["slots"]],
        )
        self.assertEqual({s["episode_id"] for s in slots},set(episodes))
        self.assertEqual(len({s["narrator_id"] for s in slots}),3)
        for slot in slots:
            current=episodes[slot["episode_id"]]
            self.assertEqual(slot["language"],current["original_spoken_language"])
            self.assertEqual(slot["format"],current["kind"])
            self.assertEqual(slot["duration_seconds"],current["target_duration_seconds"])
            self.assertEqual(slot["narrator_id"],current["narrator_plan_id"])
        for key in ("youtube_schedule_created","publication_confirmed",
                    "external_provider_connected"):
            self.assertIs(plan[key],False)
        self.assertEqual(plan["real_youtube_uploads"],0)
        self.assertEqual(plan["actual_hd_video_files"],0)
        self.assertEqual(plan["verified_human_voice_assets"],0)
        self.assertEqual(plan["monthly_recurring_infrastructure_inr"],0)

    def test_candidate_footage_must_be_original_not_reuploaded(self):
        model=load()
        self.assertIn("original",model["visualization_direction"]["rights"].lower())
        self.assertIn("MOCK",model["visualization_direction"]["long"])
        self.assertFalse(
            model["content_release_policy"]["public_publish_authorized"]
        )


if __name__=="__main__":
    unittest.main()
