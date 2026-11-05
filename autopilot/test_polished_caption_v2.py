"""B4e1 actual timing and native-canvas subtitle layout tests.

Pure stdlib. The FFmpeg physical pixel proof is in the dedicated hosted job.
"""
from __future__ import annotations

import re
import unittest

from autopilot.polished_caption_v2 import (
    CaptionQualityRejected,CONFIG,STATUS,caption_cards,compose_ass,
)
from autopilot.primary_sourced_storyboards import SLOTS,build_story
from autopilot.cloud_full_duration_pack import sentence_chunks


class ReferenceInformedCaptionSafetyTests(unittest.TestCase):
    def test_original_voice_phrase_preserved_but_displayed_as_fast_microcards(self):
        text=("Before they can answer your voice becomes an electronic "
              "signal racing across space. Even a perfect signal cannot arrive instantly.")
        cue={"start":0.1,"end":8.2,"text":text}
        source,cards=compose_ass([cue],"short","lunar_signal")
        self.assertGreaterEqual(len(cards),3)
        self.assertEqual(" ".join(c.text for c in cards),text)
        self.assertTrue(all(len(c.lines)<=2 for c in cards))
        self.assertTrue(all(all(len(s)<=29 for s in c.lines) for c in cards))
        self.assertEqual(cards[0].start,0.1)
        self.assertEqual(cards[-1].end,8.2)
        self.assertIn("PlayResX: 1080",source)
        self.assertIn("PlayResY: 1920",source)
        self.assertIn("Style: Caption,DejaVu Sans,49",source)
        self.assertIn(r"\pos(540,1420)",source)
        self.assertIn(r"\fad(65,80)",source)
        self.assertNotIn("FontSize=23",source)
        self.assertNotIn("Outline=2,FontSize",source)
        self.assertEqual(source.count("Dialogue: "),len(cards))
        self.assertLess(len(source),7500)
        self.assertIn("&H0066D9FF&",source)

    def test_actual_three_original_narration_sources_fit_microcards(self):
        for slot in SLOTS:
            story=build_story(slot)
            kind=story["format"]
            cues=[]
            time=0.0
            for scene in story["scenes"]:
                for sentence in sentence_chunks(scene["narration"]):
                    duration=max(3.5,len(sentence.split())*.46)
                    cues.append({"start":time,"end":time+duration,"text":sentence})
                    time+=duration+.1
            source,cards=compose_ass(cues,kind,story["theme"])
            self.assertGreater(len(cards),len(cues))
            self.assertLessEqual(max(len(c.lines) for c in cards),2)
            self.assertLessEqual(
                max(len(line) for c in cards for line in c.lines),
                CONFIG[kind]["line_chars"],
            )
            self.assertEqual(" ".join(c.text for c in cards),
                             " ".join(c["text"] for c in cues))
            self.assertEqual(source.count("Dialogue: "),len(cards))
            self.assertFalse(any(x.end<=x.start for x in cards))
            self.assertTrue(all(x.start+0.2<=x.end for x in cards))

    def test_paired_native_canvas_coordinates_are_inside_reserved_safe_band(self):
        portrait=CONFIG["short"]
        landscape=CONFIG["long"]
        for c,H in ((portrait,1920),(landscape,1080)):
            self.assertGreater(c["y"]-65,c["safe_top"])
            self.assertLess(c["y"]+65,c["safe_bottom"])
            self.assertLess(c["safe_bottom"],H*.9)
            self.assertLessEqual(c["font"],52)
        source,_=compose_ass(
            [{"start":0.0,"end":3.0,"text":"Eight bits equal one byte."}],
            "long","file_transfer",
        )
        self.assertIn("PlayResX: 1920",source)
        self.assertIn("PlayResY: 1080",source)
        self.assertIn(r"\pos(960,845)",source)

    def test_time_ranges_monotonic_no_more_than_two_lines_even_dense_cues(self):
        cue={"start":0.0,"end":10.0,
             "text":" ".join(["accurate","explanation","without","copying"]*8)}
        cards=caption_cards([cue],"short")
        self.assertGreater(len(cards),4)
        self.assertTrue(all(len(x.lines)<=2 for x in cards))
        for prev,after in zip(cards,cards[1:]):
            self.assertLessEqual(prev.end,after.start+.00011)
        self.assertLess(cards[-1].end,10.001)

    def test_bare_ass_markup_or_subtitle_injection_hard_fails(self):
        phrases=("hello {\\pos(0,0)}","bad}markup","hi\\Nline",
                 "secret\nnew_line","bad\x00null","", "a"*302)
        for phrase in phrases:
            with self.subTest(text=phrase[:15]),self.assertRaises(CaptionQualityRejected):
                compose_ass([{"start":0,"end":3,"text":phrase}],
                            "short","lunar_signal")

    def test_too_fast_captions_and_overlap_fail_before_rendering(self):
        failures=(
            [{"start":0,"end":.1,"text":"Too fast!"}],
            [{"start":0,"end":2,"text":"First sentence."},
             {"start":1,"end":3,"text":"Overlapping second."}],
            [{"start":5,"end":4,"text":"Reverse clock"}],
            [{"start":0,"end":400,"text":"Too late"}],
            [{"start":0,"end":float("nan"),"text":"Missing clock"}],
            [{"start":True,"end":4,"text":"Bad boolean number"}],
        )
        for cues in failures:
            with self.subTest(cues=cues),self.assertRaises(CaptionQualityRejected):
                compose_ass(cues,"short","quake_energy")

    def test_theme_keyword_highlights_are_selective_not_rainbow_whole_sentence(self):
        src,cards=compose_ass([
            {"start":0,"end":5,"text":"Moon signal delay is about 1.28 seconds."}],
            "short","lunar_signal")
        self.assertIn(r"{\1c&H0066D9FF&}Moon",src)
        self.assertIn("seconds.",src)
        self.assertNotIn("Dialogue: 0,0:00:00.00,0:00:05.00,Caption,,0,0,0,,Moon signal",src)
        self.assertTrue(all(len(x.lines)<=2 for x in cards))

    def test_invalid_theme_kind_and_unbounded_words_fails(self):
        base=[{"start":0,"end":4,"text":"One precise fact."}]
        for kind,theme in (("portrait","lunar_signal"),("short","fake-theme")):
            with self.subTest(kind=kind,theme=theme),self.assertRaises(CaptionQualityRejected):
                compose_ass(base,kind,theme)
        with self.assertRaises(CaptionQualityRejected):
            compose_ass([{"start":0,"end":30,"text":"a "*100}],
                        "short","lunar_signal")

    def test_native_ass_has_no_foreign_video_reference_or_release_claim(self):
        s,c=compose_ass([{"start":1,"end":3,"text":"Check the units."}],
                        "short","file_transfer")
        self.assertIn("B4E1_PIXEL_EXACT_CAPTION_SAFE_TWO_LINES_NO_RELEASE",STATUS)
        self.assertNotIn("samjho.exe",s)
        self.assertNotIn("youtube.com",s)
        self.assertNotIn("PUBLISH",s)
        self.assertEqual(len(c),1)


if __name__=="__main__":
    unittest.main()
