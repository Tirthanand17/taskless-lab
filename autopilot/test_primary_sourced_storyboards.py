"""B3d4c2c3a adversarial tests for three newly researched real-topic drafts.

Primary-source URLs/claims are reviewed/public references; this suite does
NOT live-fetch NASA/NIST/USGS pages or equate references with a fact check.
Narration is original educational draft text, NOT an owner-approved video.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import re
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
import unittest

from autopilot.primary_sourced_storyboards import (
    PRIMARY_REFERENCES,SLOTS,STATUS,StoryboardError,
    build_story,canonical,evaluate_three_draft_stories,
    render_original_svg,require_exact_draft,research_facts,
)


class PrimarySourcedStoryboardsTests(unittest.TestCase):
    def test_actual_public_science_publisher_refs_not_fake_cited_news(self):
        allowed={
            "science.nasa.gov","physics.nist.gov","www.nist.gov",
            "www.usgs.gov","earthquake.usgs.gov",
        }
        self.assertEqual(len(PRIMARY_REFERENCES),6)
        for sid,item in PRIMARY_REFERENCES.items():
            with self.subTest(sid=sid):
                ref=urlsplit(item["url"])
                self.assertEqual(ref.scheme,"https")
                self.assertIn(ref.hostname,allowed)
                self.assertNotIn("?",ref.query)
                self.assertEqual(item["reviewed"],"2026-11-04")
                self.assertIn(item["publisher"],("NASA","NIST","USGS"))
                self.assertGreater(len(item["role"]),30)

    def test_exact_moon_light_speed_formula_and_roundtrip(self):
        facts=research_facts()
        self.assertEqual(facts["moon_average_km"],384400)
        self.assertEqual(facts["vacuum_light_m_s"],299792458)
        self.assertEqual(
            facts["moon_one_way_seconds_rounded"],
            str((Decimal(384400)*1000/Decimal(299792458)).quantize(Decimal("0.01")))
        )
        self.assertEqual(
            facts["moon_round_trip_seconds_rounded"],
            str((Decimal(384400)*2000/Decimal(299792458)).quantize(Decimal("0.01")))
        )
        self.assertLess(Decimal(facts["moon_one_way_seconds_rounded"]),Decimal("1.4"))

    def test_earthquake_exponential_not_one_percent(self):
        f=research_facts()
        self.assertEqual(f["quake_one_magnitude_amplitude_multiplier"],10)
        self.assertEqual(f["quake_one_magnitude_energy_multiplier_rounded"],"31.6")
        self.assertEqual(f["quake_two_magnitudes_energy_multiplier"],1000)
        self.assertNotEqual(f["quake_one_magnitude_energy_multiplier_rounded"],"10.0")

    def test_nist_mb_vs_mib_theoretical_transfer_not_measured(self):
        f=research_facts()
        self.assertEqual(f["byte_in_bits"],8)
        self.assertEqual(f["decimal_mb_bytes"],1000000)
        self.assertEqual(f["binary_mib_bytes"],1048576)
        self.assertEqual(f["theoretical_100_mb_transfer_seconds"],"40.00")
        self.assertEqual(f["theoretical_100_mib_transfer_seconds"],"41.94")
        self.assertLess(Decimal(f["theoretical_100_mb_transfer_seconds"]),
                        Decimal(f["theoretical_100_mib_transfer_seconds"]))

    def test_two_shorts_and_one_real_long_draft_are_substantively_separate(self):
        stories=[build_story(s) for s in ("short_am","long","short_pm")]
        self.assertEqual([s["format"] for s in stories],["short","long","short"])
        self.assertEqual([s["time_ist"] for s in stories],["11:00","16:00","20:30"])
        self.assertEqual([s["theme"] for s in stories],
                         ["lunar_signal","file_transfer","quake_energy"])
        self.assertEqual([s["scene_count"] for s in stories],[6,20,6])
        self.assertGreaterEqual(stories[1]["estimated_duration_seconds"],310)
        self.assertGreater(stories[1]["narration_words"],300)
        for s in stories:
            self.assertEqual(s["status"],STATUS)
            self.assertEqual(s["evidence_status"],
                             "public_primary_links_curated_not_refetched_in_ci")
            self.assertFalse(s["real_primary_source_live_rechecked_by_runner"])
            self.assertFalse(s["independent_claim_by_claim_human_review_passed"])
            self.assertFalse(s["real_provider_generated_script"])
            self.assertFalse(s["actual_video_rendered_for_this_story"])
            self.assertFalse(s["youtube_upload_enabled"])
            self.assertFalse(s["release_authorized"])

    def test_all_narration_scenes_have_claim_coverage_and_no_unreferenced_assertions(self):
        for slot in SLOTS:
            story=build_story(slot)
            claims=set(story["claim_index"])
            self.assertGreaterEqual(len(claims),3)
            referenced=set()
            for scene in story["scenes"]:
                self.assertGreaterEqual(len(scene["narration"].split()),8)
                self.assertGreaterEqual(scene["estimated_seconds"],6)
                self.assertTrue(scene["claim_ids"])
                referenced.update(scene["claim_ids"])
                self.assertFalse(set(scene["claim_ids"])-claims)
            self.assertEqual(referenced,claims)
            for claim in story["claim_index"].values():
                self.assertTrue(claim["sources"])
                for citation in claim["sources"]:
                    self.assertIn(citation,story["primary_sources"])

    def test_three_first_scene_vector_grammars_are_independently_distinct(self):
        packet=evaluate_three_draft_stories()
        self.assertEqual(packet["primary_reference_id_count"],6)
        self.assertEqual(len(set(packet["first_original_vector_scene_sha256"])),3)
        self.assertEqual(len(set(packet["draft_sha256"])),3)
        self.assertTrue(packet["three_different_executed_topic_calculations"])
        self.assertTrue(packet["three_original_svg_visual_grammars"])
        self.assertFalse(packet["primary_sources_fetched_and_human_claim_reviewed"])
        self.assertFalse(packet["actual_audio_video_encoded"])
        self.assertFalse(packet["actual_youtube_upload_or_schedule"])
        self.assertFalse(packet["release_authorized"])

    def test_every_scene_emits_valid_original_vector_xml(self):
        expected_features={
            "short_am":"EARTH",
            "long":"8 bits = 1 byte",
            "short_pm":"32",
        }
        for slot in SLOTS:
            story=build_story(slot)
            for index in range(story["scene_count"]):
                vector=render_original_svg(story,index,tick=60)
                root=ET.fromstring(vector)
                self.assertEqual(root.tag,"{http://www.w3.org/2000/svg}svg")
                self.assertEqual(root.attrib["width"],
                                 "1920" if slot=="long" else "1080")
                self.assertIn(expected_features[slot],vector)
                self.assertIn("NOT APPROVED",vector)
                self.assertNotIn("<script",vector)
                self.assertNotIn("<image ",vector)
                self.assertNotIn("href=",vector)

    def test_signal_packet_and_other_drawing_motion_change_with_tick(self):
        for slot in SLOTS:
            story=build_story(slot)
            a=render_original_svg(story,0,0)
            b=render_original_svg(story,0,100)
            self.assertNotEqual(sha256(a.encode()).hexdigest(),
                                sha256(b.encode()).hexdigest())
            self.assertIn('xmlns="http://www.w3.org/2000/svg"',a)

    def test_changed_title_scene_or_claim_root_cannot_reuse_draft_sha(self):
        story=build_story("short_am")
        for field,change in (
            ("status","PERMISSION_GRANTED"),
            ("estimated_duration_seconds",0),
            ("real_provider_generated_script",True),
            ("release_authorized",True),
            ("youtube_upload_enabled",True),
        ):
            altered=deepcopy(story)
            altered[field]=change
            with self.subTest(field=field),self.assertRaises(StoryboardError):
                require_exact_draft(altered)
        for field in ("narration","display_value","visual_action","claim_ids"):
            altered=deepcopy(story)
            altered["scenes"][0][field]="Forged claim" if field!="claim_ids" else ["fake_claim"]
            with self.subTest(field=field),self.assertRaises(StoryboardError):
                require_exact_draft(altered)

    def test_changed_public_source_attribution_is_not_authorized(self):
        story=build_story("long")
        altered=deepcopy(story)
        altered["primary_sources"]["nist_binary"]["url"]="https://attacker.example/fake"
        with self.assertRaises(StoryboardError):
            require_exact_draft(altered)
        altered=deepcopy(story)
        altered["claim_index"]["bit_byte"]["summary"]="A byte contains nine bits"
        with self.assertRaises(StoryboardError):
            require_exact_draft(altered)

    def test_wrong_date_or_missing_slot_rejected(self):
        for bad in ("not-a-date","2026-11-11","2026-11-12Z","2031-01-01"):
            with self.subTest(day=bad),self.assertRaises(StoryboardError):
                build_story("short_am",bad)
        with self.assertRaises(StoryboardError):
            build_story("unknown")
        with self.assertRaises(StoryboardError):
            require_exact_draft({"slot":"short_am","episode_id":"broken"})

    def test_scene_animation_requires_exact_draft_and_bounded_ticks(self):
        story=build_story("short_pm")
        for index,tick in ((-1,0),(999,0),(0,-1),(0,121),(True,0),(0,True)):
            with self.subTest(index=index,tick=tick),self.assertRaises(StoryboardError):
                render_original_svg(story,index,tick)
        changed=deepcopy(story)
        changed["scenes"][0]["narration"]="<script>alert(1)</script>"
        with self.assertRaises(StoryboardError):
            render_original_svg(changed,0,1)

    def test_new_day_rebuilds_unique_episode_ids_and_hashes(self):
        d1=evaluate_three_draft_stories("2026-11-12")
        d2=evaluate_three_draft_stories("2026-11-13")
        self.assertNotEqual(d1["draft_sha256"],d2["draft_sha256"])
        self.assertNotEqual(d1["episode_ids"],d2["episode_ids"])
        self.assertEqual(d1["research_topics"],d2["research_topics"])
        self.assertFalse(d2["release_authorized"])

    def test_text_does_not_misrepresent_idealized_calculations_as_live_events(self):
        alltext=" ".join(
            row["narration"] for slot in SLOTS for row in build_story(slot)["scenes"]
        ).lower()
        for word in (
            "actual distance changes",
            "before equipment processing",
            "not automatically",
            "protocol headers",
            "not a promise",
            "not a live mission measurement",
        ):
            self.assertIn(word,alltext)
        self.assertNotIn("yesterday's quake was exactly",alltext)


if __name__=="__main__":
    unittest.main()
