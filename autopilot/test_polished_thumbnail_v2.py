"""B4e1 real PIL thumbnail art and constrained review identity tests.

Unlike only mocking a text label, these actually render original 1280x720
bitmap artwork on the hosted runner and inspect physical PNG bytes.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest

from autopilot.polished_thumbnail_v2 import (
    SPEC,ThumbnailQualityRejected,render_editorial_thumbnail,
)
from autopilot.primary_sourced_storyboards import build_story


@unittest.skipUnless(importlib.util.find_spec('PIL') is not None,
                     'Physical PIL thumbnail QA runs in dedicated B4e1 job with Pillow installed')
class OriginalEditorialThumbnailTests(unittest.TestCase):
    def test_three_real_editorial_thumbnails_have_distinct_original_art(self):
        from PIL import Image
        records=[]
        with tempfile.TemporaryDirectory() as t:
            for slot in ("short_am","long","short_pm"):
                story=build_story(slot)
                out=Path(t)/f"{slot}.png"
                digest=render_editorial_thumbnail(story,out)
                with Image.open(out) as im:
                    im.load()
                    self.assertEqual(im.size,(1280,720))
                    self.assertEqual(im.mode,"RGB")
                    # Central left typography has room; right illustration
                    # has separate accent/halo and must not be blank.
                    self.assertNotEqual(im.getpixel((110,250)),im.getpixel((1000,400)))
                    self.assertNotEqual(im.getpixel((110,640)),im.getpixel((960,380)))
                    self.assertLess(im.getpixel((400,660))[0],240)
                self.assertGreater(out.stat().st_size,12000)
                self.assertEqual(len(digest),64)
                records.append(digest)
            self.assertEqual(len(set(records)),3)

    def test_no_authorized_thumbnail_and_no_overwrite_existing_artifact(self):
        with tempfile.TemporaryDirectory() as t:
            story=build_story("short_am")
            p=Path(t)/"cover.png"
            render_editorial_thumbnail(story,p)
            with self.assertRaises(ThumbnailQualityRejected):
                render_editorial_thumbnail(story,p)
            for name in ("release_authorized","youtube_upload_enabled"):
                s=deepcopy(story)
                s[name]=True
                with self.subTest(name=name),self.assertRaises(ThumbnailQualityRejected):
                    render_editorial_thumbnail(s,Path(t)/f"changed-{name}.png")

    def test_source_topics_headlines_and_accent_objects_are_distinct(self):
        self.assertEqual(set(SPEC),{"lunar_signal","file_transfer","quake_energy"})
        self.assertEqual(len({tuple(x["title"]) for x in SPEC.values()}),3)
        self.assertEqual(len({tuple(x["accent"]) for x in SPEC.values()}),3)
        self.assertTrue(all(len(x["title"])==2 for x in SPEC.values()))
        self.assertTrue(all(len(x["stat"])<=22 for x in SPEC.values()))
        self.assertNotIn("UNAPPROVED · HUMAN FACT / RIGHTS REVIEW PENDING",
                         " ".join(x["stat"] for x in SPEC.values()))


if __name__=="__main__":
    unittest.main()
