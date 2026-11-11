"""STDlib-only regression tests for mobile SRT reflow and timeline locking."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.rewrap_b1_srt_review import reflow,CaptionRefused

class ReviewOnlyCaptionTests(unittest.TestCase):
    def test_unaltered_times_spoken_words_and_mobile_line_width(self):
        src=(
          "1\n00:00:00,000 --> 00:00:06,379\n"
          "A fictional website sends notification after notification, even\n"
          "when its tab is closed.\n\n"
          "2\n00:00:06,439 --> 00:00:12,695\n"
          "You might think it is a virus, but first check whether the\n"
          "browser granted notification access.\n"
        )
        for kind,max_len in (("short",42),("long",44)):
            with self.subTest(kind=kind):
                out=reflow(src,kind)
                self.assertIn("00:00:00,000 --> 00:00:06,379",out)
                self.assertIn("00:00:06,439 --> 00:00:12,695",out)
                self.assertEqual(out.count("-->"),2)
                chunks=out.strip().split("\n\n")
                self.assertEqual([int(c.splitlines()[0]) for c in chunks],[1,2])
                for old,new in zip(src.strip().split("\n\n"),chunks):
                    before=" ".join(" ".join(old.splitlines()[2:]).split())
                    after=" ".join(" ".join(new.splitlines()[2:]).split())
                    self.assertEqual(after,before)
                    self.assertLessEqual(len(new.splitlines()[2:]),3)
                    self.assertTrue(all(len(x)<=max_len for x in new.splitlines()[2:]))

    def test_reject_overlap_fake_cue_bad_time_unknown_type(self):
        examples={
           "overlap":"1\n00:00:00,000 --> 00:00:02,000\nhi\n\n2\n00:00:01,000 --> 00:00:04,000\nbye",
           "missing_timestamp":"1\nhi\nthere",
           "nonsequential":"3\n00:00:00,000 --> 00:00:01,000\none",
           "reversed":"1\n00:00:08,000 --> 00:00:07,000\nbad",
           "oversized":"1\n00:00:00,000 --> 00:00:04,000\n"+("repeat " * 100),
        }
        for issue,txt in examples.items():
            with self.subTest(issue=issue):
                with self.assertRaises(CaptionRefused):
                    reflow(txt,"long")
        with self.assertRaises(CaptionRefused):
            reflow("1\n00:00:00,000 --> 00:00:01,000\nhello","unknown")

if __name__=="__main__":
    unittest.main()
