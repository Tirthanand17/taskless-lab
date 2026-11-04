"""Offline negative tests for independent *encoded* media review; no real video files."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from autopilot.full_pack_fixture import EPISODES
from autopilot.cloud_full_duration_pack import STATUS, sentence_chunks, ms_stamp
from autopilot.independent_av_review import (
    AUDIO_TECHNICAL_STATUS, ReviewerError, parse_loudnorm,
    parse_silence_observations, verify_srt_against_script, review_full_pack,
)

LOUDNORM_SAMPLE = """[Parsed_loudnorm_0] {
        "input_i" : "-17.90",
        "input_tp" : "-3.45",
        "input_lra" : "2.80",
        "input_thresh" : "-28.00",
        "output_i" : "-16.20"
}"""


def srt_for_episode(ep) -> str:
    lines=[]
    seconds=0
    for scene in ep.scenes:
        for spoken in sentence_chunks(scene.narration):
            idx=len(lines)//4+1
            start,end=seconds,seconds+2.5
            lines.extend([str(idx),f"{ms_stamp(start)} --> {ms_stamp(end)}",spoken,""])
            seconds+=2.55
    return "\n".join(lines)+"\n"


class IndependentAVReviewTests(unittest.TestCase):
    def test_genuine_ffmpeg_measurement_parsing(self):
        r=parse_loudnorm(LOUDNORM_SAMPLE)
        self.assertEqual(r["integrated_lufs"],-17.9)
        self.assertEqual(r["true_peak_dbtp"],-3.45)
        self.assertEqual(r["loudness_range_lu"],2.8)
        self.assertTrue(r["typical_online_video_target_diagnostic"])
        self.assertIs(r["independent_human_listening_completed"],False)

    def test_loudness_rejects_silent_overloaded_nonfinite_and_spoofed_json(self):
        cases=[
            LOUDNORM_SAMPLE.replace("-17.90","-inf"),
            LOUDNORM_SAMPLE.replace("-17.90","-42.10"),
            LOUDNORM_SAMPLE.replace("-17.90","-2.20"),
            LOUDNORM_SAMPLE.replace("-3.45","0.75"),
            LOUDNORM_SAMPLE.replace('"input_lra" : "2.80"','"input_lra" : "nan"'),
            "Not a json block",
            LOUDNORM_SAMPLE+LOUDNORM_SAMPLE,
        ]
        for sample in cases:
            with self.subTest(sample=sample[:35]),self.assertRaises(ReviewerError):
                parse_loudnorm(sample)

    def test_loudness_diagnostic_band_not_release_gate(self):
        report=parse_loudnorm(LOUDNORM_SAMPLE.replace("-17.90","-25.90"))
        self.assertFalse(report["typical_online_video_target_diagnostic"])
        self.assertFalse(report["independent_human_listening_completed"])

    def test_actual_silence_observation_parser(self):
        r=parse_silence_observations("silence_start: 2.3\nsilence_end: 3.66 | silence_duration: 1.36")
        self.assertEqual(r["long_silence_count"],1)
        self.assertEqual(r["longest_silence_seconds"],1.36)
        self.assertTrue(r["human_audio_inspection_required"])
        self.assertEqual(parse_silence_observations("")["long_silence_count"],0)

    def test_srt_matches_every_sentence_of_all_original_three_scripts(self):
        for e in EPISODES:
            text=srt_for_episode(e)
            cue_count=sum(len(sentence_chunks(scene.narration)) for scene in e.scenes)
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/"captions_scene_aligned.srt"
                path.write_text(text,encoding="utf8")
                r=verify_srt_against_script(path,e,cue_count*2.55)
                self.assertEqual(r["verified_srt_cue_count"],cue_count)
                self.assertTrue(r["every_caption_matches_original_spoken_text"])
                self.assertTrue(r["all_cues_monotone_and_in_video"])
                self.assertFalse(r["human_spoken_word_accuracy_approved"])

    def test_truncated_or_rewritten_caption_cannot_be_claimed_matching(self):
        e=EPISODES[0]
        s=srt_for_episode(e)
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"captions.srt"
            p.write_text(s.replace("Here is a sample", "YouTube video has been approved"),encoding="utf8")
            with self.assertRaises(ReviewerError):
                verify_srt_against_script(p,e,90)
            p.write_text(s.split("\n\n",1)[0]+"\n",encoding="utf8")
            with self.assertRaises(ReviewerError):
                verify_srt_against_script(p,e,90)

    def test_out_of_order_or_bad_caption_times_rejected(self):
        e=EPISODES[0]
        raw=srt_for_episode(e)
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"bad.srt"
            p.write_text(raw.replace("00:00:00,000","00:02:10,000",1),encoding="utf8")
            with self.assertRaises(ReviewerError):
                verify_srt_against_script(p,e,90)
            p.write_text(raw.replace("00:00:00,000","00:99:00,000",1),encoding="utf8")
            with self.assertRaises(ReviewerError):
                verify_srt_against_script(p,e,90)

    def test_duplicate_or_absent_technical_fixtures_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/"technical_report.json").write_text(json.dumps({"status":"SCHEDULED_VERIFIED","videos":[]}))
            with self.assertRaises(ReviewerError):
                review_full_pack(p)
            (p/"technical_report.json").write_text(json.dumps({"status":STATUS,"videos":[]}))
            with self.assertRaises(ReviewerError):
                review_full_pack(p)

    def test_malformed_time_protection_and_report_scope(self):
        from autopilot.independent_av_review import _timestamp
        for bad in ("00:60:12,000","00:00:60,500","1:02:03,444","00:01:10.222"):
            with self.assertRaises(ReviewerError):
                _timestamp(bad)
        self.assertEqual(_timestamp("00:03:06,350"),186.35)
        self.assertEqual(AUDIO_TECHNICAL_STATUS,"MEASURED_TECHNICAL_QA_ONLY_NOT_EDITORIAL_APPROVAL")

    def test_no_publishing_or_laptop_dependencies_in_reviewer_code(self):
        from autopilot import independent_av_review
        text=Path(independent_av_review.__file__).read_text(encoding="utf8")
        for bad in ("googleapiclient","youtube.upload","Remote_Desktop_Commander","C:\\Users\\Dell","Nirala"):
            self.assertNotIn(bad,text)


if __name__=="__main__":
    unittest.main()
