"""No laptop or model/network use: fast negative contract tests for full pack."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from autopilot.full_pack_fixture import (
    CSV_SAMPLE, EPISODES, SHORT_AM, LONG, SHORT_PM,
    inspect_example_csv, validate_fixture, Scene, ExampleEpisode,
)
from autopilot.cloud_full_duration_pack import (
    PackError, STATUS, sentence_chunks, ms_stamp, validate_cues,
    demo_messages,
)


class CloudFullPackContractTests(unittest.TestCase):
    def test_real_computed_source_id_preservation_duplicate_and_date_exception(self):
        r=inspect_example_csv()
        self.assertEqual(r["row_count"],4)
        self.assertEqual(r["ids_preserved"],["00127","00128","00127","00129"])
        self.assertEqual(r["int_conversion_example"],{"raw":"00127","numeric":127})
        self.assertEqual(len(r["duplicate_ids"]),1)
        self.assertEqual(r["duplicate_ids"][0]["first_row"],1)
        self.assertEqual(r["duplicate_ids"][0]["conflicting_row"],3)
        self.assertFalse(r["duplicate_ids"][0]["status_changed"])
        self.assertTrue(r["duplicate_ids"][0]["date_changed"])
        self.assertEqual(r["invalid_iso_dates"],[{"row":4,"raw_value":"11/04/26"}])
        self.assertEqual(r["potential_review_rows"],[3,4])

    def test_bad_csv_headers_shape_and_member_id_rejected(self):
        cases=[
           CSV_SAMPLE.replace("member_id,joined_on,status","status,joined_on,member_id"),
           CSV_SAMPLE.replace("00129,11/04/26,active","0129,11/04/26,active"),
           CSV_SAMPLE.replace("00128,2026-11-02,paused","1O128,2026-11-02,paused"),
           CSV_SAMPLE+"00000,2026-11-03,active\n",
           CSV_SAMPLE.replace("00128,2026-11-02,paused","00128,2026-11-02"),
           CSV_SAMPLE.replace("00127,2026-11-03,active","00155,2026-11-03,active"),
           CSV_SAMPLE.replace("00129,11/04/26,active","00129,2026-11-04,active")
        ]
        for bad in cases:
            with self.subTest(bad=bad[:42]),self.assertRaises(ValueError):
                inspect_example_csv(bad)

    def test_three_topics_three_different_voices_and_full_length_narration(self):
        validate_fixture()
        self.assertEqual([e.kind for e in EPISODES],["short","long","short"])
        self.assertEqual(len({e.theme for e in EPISODES}),3)
        self.assertEqual(len({e.voice for e in EPISODES}),3)
        self.assertEqual([len(e.scenes) for e in EPISODES],[7,14,7])
        self.assertNotIn("youtube",json.dumps([e.episode_id for e in EPISODES]))

    def test_long_is_more_substantive_than_shorts(self):
        words=lambda e:sum(len(s.narration.split()) for s in e.scenes)
        self.assertGreater(words(LONG),350)
        self.assertGreater(words(LONG),2*words(SHORT_AM))
        self.assertGreater(words(SHORT_PM),95)
        self.assertTrue(all(s.mode for e in EPISODES for s in e.scenes))
        self.assertEqual(sum(len(e.scenes) for e in EPISODES),28)

    def test_sentence_cues_retain_original_semantics(self):
        for e in EPISODES:
            for s in e.scenes:
                cues=sentence_chunks(s.narration)
                self.assertGreaterEqual(len(cues),1)
                self.assertEqual(" ".join(cues),s.narration)
                self.assertTrue(all(8<=len(x)<=235 for x in cues))

    def test_unbounded_spoken_cues_rejected(self):
        for text in ("", "Hi.", "A"*236):
            with self.assertRaises(PackError):
                sentence_chunks(text)

    def test_timestamp_format_and_invalid_numeric_time_rejected(self):
        self.assertEqual(ms_stamp(0),"00:00:00,000")
        self.assertEqual(ms_stamp(65.1203),"00:01:05,120")
        self.assertEqual(ms_stamp(150.999),"00:02:30,999")
        for invalid in (-1,3601,float("nan"),float("inf")):
            with self.assertRaises(PackError):
                ms_stamp(invalid)

    def test_scene_cues_exactly_timed_without_overlap(self):
        cues=[
            {"start":0.0,"end":3.7,"text":"Our source label includes leading zeroes."},
            {"start":3.8,"end":7.3,"text":"The integer conversion changes the label."},
            {"start":7.4,"end":11.8,"text":"Text identifiers retain the original digits."},
            {"start":11.9,"end":14.2,"text":"Check the source row carefully."},
            {"start":14.3,"end":16.3,"text":"Scan each import."},
            {"start":16.4,"end":19.1,"text":"Preserve the original copy."},
            {"start":19.2,"end":22.3,"text":"Flag inconsistent values for review."},
            {"start":22.4,"end":25.9,"text":"Keep a review log."},
        ]
        validate_cues(cues,26,8)
        with self.assertRaises(PackError):
            validate_cues(cues,26,9)
        with self.assertRaises(PackError):
            validate_cues(cues,24,8)
        bad=[dict(c) for c in cues]
        bad[2]["start"]=3.1
        with self.assertRaises(PackError):
            validate_cues(bad,26,8)

    def test_all_scanned_modes_derive_from_executed_demo(self):
        r=validate_fixture()
        for e in EPISODES:
            for scene in e.scenes:
                label=demo_messages(scene.mode,r)
                self.assertEqual(len(label),3)
                self.assertTrue(all(isinstance(x,str) and len(x)>8 for x in label))
        self.assertIn("127",demo_messages("cast",r)[0])
        self.assertIn("11/04/26",demo_messages("dates",r)[0])
        self.assertIn("00127",demo_messages("duplicates",r)[0])
        with self.assertRaises(PackError):
            demo_messages("release_authorized",r)

    def test_unapproved_media_status_cannot_be_confused_with_real_release(self):
        self.assertEqual(STATUS,"FULL_DURATION_EDUCATIONAL_TECHNICAL_BENCHMARK_NOT_PUBLISHABLE")
        self.assertNotEqual(STATUS,"SCHEDULED_VERIFIED")
        self.assertNotEqual(STATUS,"QA_APPROVED")
        self.assertFalse(hasattr(SHORT_AM,"youtube_video_id"))

    def test_full_pack_workflow_does_not_import_remote_upload_or_laptop_files(self):
        from autopilot import cloud_full_duration_pack as mod
        source=Path(mod.__file__).read_text(encoding="utf8")
        self.assertNotIn("youtube.upload",source)
        self.assertNotIn("Remote_Desktop",source)
        self.assertNotIn("Nirala",source)
        self.assertNotIn("googleapiclient",source)
        self.assertNotIn("C:\\Users\\Dell",source)


if __name__=="__main__":
    unittest.main()
