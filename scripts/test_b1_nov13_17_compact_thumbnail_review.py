"""Fail-closed thumbnail quality and release-safety tests for Nov13-17 B1."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

# Generic repository quality CI has no Pillow. The dedicated thumbnail
# workflow installs it and always executes all actual fifteen image tests.
try:
    from PIL import Image
except ModuleNotFoundError:
    Image = None

if Image is not None:
    from autopilot.branch1_nov13_17_original_batch import read_day
    from scripts.b1_nov13_17_compact_thumbnail_review import (
        COPY, TYPE_SIZE, MAX_BYTES, generate, render, ThumbnailRefused,
    )


@unittest.skipIf(Image is None, "Pillow is tested in the dedicated thumbnail CI")
class CompactThumbnailReviewTests(unittest.TestCase):
    def test_every_episode_source_locked_and_original_script_untouched(self):
        ids=set()
        for n in range(13,18):
            date=f"2026-11-{n:02d}"
            d,_=read_day(date)
            self.assertEqual([x["kind"] for x in d["episodes"]],
                             ["short","short","long"])
            for ep in d["episodes"]:
                self.assertNotIn(ep["id"],ids)
                ids.add(ep["id"])
                self.assertIn(ep["id"].split(date.replace("-","")+"_",1)[1],COPY)
                img=render(ep)
                self.assertEqual(img.size,TYPE_SIZE[ep["kind"]])
                self.assertFalse(ep["approval"]["owner_final_watch"])
                self.assertFalse(ep["approval"]["youtube_scheduled"])
        self.assertEqual(len(ids),15)
        self.assertEqual(len(COPY),15)

    def test_fifteen_unique_small_correct_aspect_images_with_provenance(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)/"optimized"
            dates=[f"2026-11-{i:02d}" for i in range(13,18)]
            result=generate(folder,dates)
            self.assertEqual(len(result),15)
            self.assertEqual(len(set(x["jpg_sha256"] for x in result)),15)
            self.assertEqual(sum(x["kind"]=="short" for x in result),10)
            self.assertEqual(sum(x["kind"]=="long" for x in result),5)
            for row in result:
                file=folder/row["file"]
                raw=file.read_bytes()
                self.assertTrue(15_000<=len(raw)<=MAX_BYTES)
                self.assertEqual(hashlib.sha256(raw).hexdigest(),row["jpg_sha256"])
                self.assertFalse(row["owner_thumbnail_approved"])
                self.assertFalse(row["youtube_thumbnail_updated"])
                self.assertFalse(row["youtube_scheduled_by_job"])
                with Image.open(file) as im:
                    self.assertEqual(im.format,"JPEG")
                    self.assertEqual(im.size,TYPE_SIZE[row["kind"]])
                    im.thumbnail((180,320))
                    self.assertGreater(im.getextrema()[0][1],120)
            manifest=json.loads(
                (folder/"MANIFEST_COMPACT_REVIEW_NOT_YOUTUBE.json").read_text())
            self.assertEqual(manifest["count"],15)
            self.assertEqual(manifest["human_approval_count"],0)
            self.assertEqual(manifest["youtube_thumbnail_updates"],0)
            self.assertEqual(manifest["youtube_schedule_changes"],0)

    def test_refuse_forged_owner_approval_wrong_subject_and_overwrite(self):
        day,_=read_day("2026-11-14")
        src=day["episodes"][0]
        for attribute,value in (("date_ist","2026-11-12"),
                                ("kind","new-format"),
                                ("id","fm_20261114_fake_video_short_en")):
            altered={**src,attribute:value}
            with self.subTest(attribute=attribute):
                with self.assertRaises(ThumbnailRefused):
                    render(altered)
        altered={**src,"approval":{**src["approval"],"owner_final_watch":True}}
        with self.assertRaises(ThumbnailRefused):
            render(altered)
        altered={**src,"approval":{**src["approval"],"youtube_scheduled":True}}
        with self.assertRaises(ThumbnailRefused):
            render(altered)
        with TemporaryDirectory() as temp:
            p=Path(temp)/"out"
            generate(p,["2026-11-14"])
            with self.assertRaises(ThumbnailRefused):
                generate(p,["2026-11-14"])


if __name__=="__main__":
    unittest.main()
