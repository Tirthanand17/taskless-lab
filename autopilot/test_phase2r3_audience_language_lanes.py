"""Two original language-specific Shorts; offline planning, never targeting claims."""
from copy import deepcopy
from pathlib import Path
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase2r3_audience_language_lanes import (
    LANES,prepare_audience_language_lanes,report_language_tracking_plan,
    _spoken_language_check,_metadata_language_check,
)
from autopilot.phase2r3_authored_pack_audit import SOURCE


class LanguageSeparationTests(unittest.TestCase):
    def setUp(self):
        self.original=SOURCE.read_text(encoding="utf-8")

    def test_one_original_short_per_language_not_two_languages_in_one_short(self):
        plan=prepare_audience_language_lanes()
        shorts=[x for x in plan["episodes"] if x["episode_kind"]=="short"]
        self.assertEqual(len(shorts),2)
        self.assertEqual({x["original_spoken_language"] for x in shorts},{"hi","en"})
        self.assertEqual(len({x["narrator_plan_id"] for x in shorts}),2)
        self.assertEqual(plan["intended_hindi_shorts"],1)
        self.assertEqual(plan["intended_english_shorts"],1)
        self.assertEqual(plan["actual_uploaded_videos"],0)

    def test_hindi_titles_descriptions_and_captions_use_hindi_lane(self):
        plan=prepare_audience_language_lanes()
        hindi=next(x for x in plan["episodes"] if x["episode_id"]=="csv_tutorial_short_hi")
        self.assertEqual(hindi["subtitle_language"],"hi")
        self.assertEqual(hindi["thumbnail_language"],"hi")
        self.assertEqual(hindi["video_default_language_proposed"],"hi")
        self.assertIn("Python से",hindi["title"])
        self.assertEqual(hindi["related_long_episode_id"],"csv_tutorial_long_hi")
        self.assertFalse(hindi["actual_audio_language_verified"])

    def test_english_viewers_not_sent_to_hindi_only_long_video(self):
        plan=prepare_audience_language_lanes()
        en=next(x for x in plan["episodes"] if x["episode_id"]=="csv_tutorial_short_en")
        self.assertIsNone(en["related_long_episode_id"])
        self.assertNotIn("full walkthrough",en["description"].lower())
        self.assertEqual(en["subtitle_language"],"en")
        self.assertEqual(en["video_default_language_proposed"],"en")

    def test_distinct_metadata_scripts_and_srt_digests(self):
        data=prepare_audience_language_lanes()
        shorts=[x for x in data["episodes"] if x["episode_kind"]=="short"]
        for name in ("script_spoken_text_sha256","script_section_sha256","draft_srt_sha256"):
            self.assertEqual(len({x[name] for x in shorts}),2)
            self.assertTrue(all(len(x[name])==64 for x in shorts))
        self.assertNotEqual(shorts[0]["title"],shorts[1]["title"])

    def test_no_audio_or_audience_algorithm_claim_made(self):
        data=prepare_audience_language_lanes()
        self.assertFalse(data["youtube_language_matching_guaranteed"])
        self.assertFalse(data["publishing_authorized"])
        self.assertFalse(data["auto_dub_enabled_or_toggled"])
        for video in data["episodes"]:
            self.assertFalse(video["youtube_snippet_default_audio_language_set"])
            self.assertFalse(video["geographic_or_language_audience_exclusivity_guaranteed"])
            self.assertFalse(video["licensed_distinct_narrator_verified"])
            self.assertFalse(video["speech_to_caption_alignment_verified"])
            self.assertFalse(video["ready_for_upload"])

    def test_fails_if_hindi_video_receives_english_title_or_description(self):
        for key,value in (
            ("title","Learn Python CSV in Hindi"),
            ("description","Learn a helpful Python CSV practice workflow with sample data and no personal details."),
        ):
            specs=deepcopy(LANES)
            specs["csv_tutorial_short_hi"][key]=value
            with self.subTest(key=key),self.assertRaises(WorkflowError):
                prepare_audience_language_lanes(lane_specs=specs)

    def test_fails_if_english_video_receives_hindi_title_or_description(self):
        for key,value in (
            ("title","Python से CSV सीखें"),
            ("description","Python से डेटा पढ़ें और सीखें। Our English tutorial uses fictional data."),
        ):
            specs=deepcopy(LANES)
            specs["csv_tutorial_short_en"][key]=value
            with self.subTest(key=key),self.assertRaises(WorkflowError):
                prepare_audience_language_lanes(lane_specs=specs)

    def test_rejects_swapped_subtitle_thumbnail_language_or_cross_language_cta(self):
        for name,value in (
            ("caption_language","en"),("thumbnail_language","en"),
            ("language","en"),("target_audience_language","en"),
            ("long_video_followup",None),
        ):
            specs=deepcopy(LANES)
            specs["csv_tutorial_short_hi"][name]=value
            with self.subTest(name=name),self.assertRaises(WorkflowError):
                prepare_audience_language_lanes(lane_specs=specs)
        specs=deepcopy(LANES)
        specs["csv_tutorial_short_en"]["long_video_followup"]="csv_tutorial_long_hi"
        with self.assertRaises(WorkflowError):
            prepare_audience_language_lanes(lane_specs=specs)

    def test_rejects_full_english_substitution_of_original_hindi_voice_script(self):
        changed=self.original.replace(
            "क्या आपको Excel जैसी CSV फ़ाइल का डेटा जल्दी समझना है? चलिए Python से सिर्फ़ नकली उदाहरण पर तरीका देखते हैं।",
            "This is a demonstration using invented Python CSV data for learning how rows and columns work.",
            1
        )
        # Replacing a single Hindi beat is still majority Hindi (Hinglish
        # allows English technical terms); replacing EVERY Hindi word fails.
        start=changed.index("## SHORT 1")
        end=changed.index("## SHORT 2")
        segment=changed[start:end]
        for char in set(segment):
            if "\u0900"<=char<="\u097f":
                segment=segment.replace(char,"x")
        substituted=changed[:start]+segment+changed[end:]
        with self.assertRaises(WorkflowError):
            prepare_audience_language_lanes(markdown=substituted)

    def test_rejects_english_spoken_script_with_hindi_intrusion(self):
        start=self.original.index("## SHORT 2")
        end=self.original.index("## LONG VIDEO")
        en=self.original[start:end].replace(
            "Your CSV looks like a wall of rows?",
            "क्या आपने CSV देखा है?",
            1)
        with self.assertRaises(WorkflowError):
            prepare_audience_language_lanes(
                markdown=self.original[:start]+en+self.original[end:])

    def test_hindi_metadata_cannot_be_mostly_english_with_small_hindi_fragment(self):
        specs=deepcopy(LANES)
        specs["csv_tutorial_short_hi"]["title"]=(
            "Learn Python CSV reader basics and data science for beginners अब सीखें"
        )
        with self.assertRaises(WorkflowError):
            prepare_audience_language_lanes(lane_specs=specs)
        specs=deepcopy(LANES)
        specs["csv_tutorial_short_hi"]["description"]=(
            "हम हिंदी में डेटा सीखेंगे और समझेंगे। "
            + "Practice the basics of Python data science and file import workflows "
              "in a complete beginner tutorial with helpful examples. "*5
        )
        with self.assertRaises(WorkflowError):
            prepare_audience_language_lanes(lane_specs=specs)

    def test_refuses_external_links_in_both_video_languages(self):
        for episode,key,extra in (
            ("csv_tutorial_short_en","description"," Visit https://unsafe.example/invite"),
            ("csv_tutorial_short_en","title"," www.example.com"),
            ("csv_tutorial_short_hi","description"," example.app पर और सीखें"),
        ):
            with self.subTest(episode=episode,key=key):
                specs=deepcopy(LANES)
                specs[episode][key]+=extra
                with self.assertRaises(WorkflowError):
                    prepare_audience_language_lanes(lane_specs=specs)

    def test_refuses_unreviewed_promises_and_fake_actions(self):
        for episode,key,promise in (
            ("csv_tutorial_short_en","description"," This is guaranteed viral."),
            ("csv_tutorial_short_en","description"," We booked your ticket."),
            ("csv_tutorial_short_hi","description"," पक्की कमाई की गारंटी।"),
            ("csv_tutorial_long_hi","title"," गारंटी"),
        ):
            with self.subTest(episode=episode,key=key):
                specs=deepcopy(LANES)
                specs[episode][key]+=promise
                with self.assertRaises(WorkflowError):
                    prepare_audience_language_lanes(lane_specs=specs)

    def test_refuses_bidi_and_control_character_metadata_injection(self):
        for marker in ("\\n","\\t","\\u202e","\\u2066","\\u200b"):
            with self.subTest(marker=repr(marker)):
                specs=deepcopy(LANES)
                specs["csv_tutorial_short_en"]["title"]+=marker+"secret"
                with self.assertRaises(WorkflowError):
                    prepare_audience_language_lanes(lane_specs=specs)

    def test_unicode_hindi_joiner_is_not_banned_as_directional_attack(self):
        # ZWJ can form intentional Devanagari conjuncts; do not confuse it
        # with bidi controls or U+200B invisible word-break characters.
        specs=deepcopy(LANES)
        specs["csv_tutorial_short_hi"]["description"]+=" क्ष\\u200dमा उदाहरण।"
        plan=prepare_audience_language_lanes(lane_specs=specs)
        self.assertFalse(plan["publishing_authorized"])

    def test_same_hindi_title_across_short_and_long_is_rejected(self):
        specs=deepcopy(LANES)
        specs["csv_tutorial_long_hi"]["title"]=specs["csv_tutorial_short_hi"]["title"]
        with self.assertRaises(WorkflowError):
            prepare_audience_language_lanes(lane_specs=specs)

    def test_legitimate_technical_english_terms_in_hindi_copy_still_pass(self):
        specs=deepcopy(LANES)
        specs["csv_tutorial_short_hi"]["description"]+=(
            " CSV, Python और DictReader से सीखने का आसान तरीका।"
        )
        plan=prepare_audience_language_lanes(lane_specs=specs)
        self.assertEqual(len(plan["episodes"]),3)
        self.assertEqual(plan["actual_uploaded_videos"],0)
        self.assertFalse(plan["publishing_authorized"])

    def test_normal_english_technical_words_allowed_in_hinglish(self):
        self.assertGreater(_spoken_language_check(
            "Python CSV के लिए हम डेटा फ़ाइल बनाएँगे। Python का DictReader डेटा पढ़कर परिणाम दिखाएगा।"*5,
            "hi")["devanagari_letters"],100)

    def test_no_fabricated_language_engagement_counts(self):
        analytics=report_language_tracking_plan()
        self.assertIsNone(analytics["counts"])
        self.assertFalse(analytics["data_connected"])
        self.assertFalse(analytics["youtube_analytics_readback_verified"])
        self.assertTrue(analytics["no_guaranteed_language_only_distribution"])

    def test_no_unknown_third_language_lane(self):
        specs=deepcopy(LANES)
        specs["unknown_arabic_short"]=specs.pop("csv_tutorial_short_en")
        with self.assertRaises(WorkflowError):
            prepare_audience_language_lanes(lane_specs=specs)


if __name__=="__main__":
    unittest.main()
