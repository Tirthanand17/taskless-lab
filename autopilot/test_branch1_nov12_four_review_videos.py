"""Nov 12 growth-reset: honest zero-upload original four-video quality tests."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.branch1_nov12_four_review_videos import (
    STATUS,BRIEF,ALLOWED_SOURCES,IDENTIFIERS,SLOTS,VIDEO_SIZE,
    FourVideoRefused,load_brief,split_script,secs_stamp,
)


class Nov12OriginalBriefTests(unittest.TestCase):
    def test_real_content_four_slots_three_distinct_shorts_and_one_long(self):
        brief,digest=load_brief()
        self.assertEqual(len(digest),64)
        self.assertEqual([x["id"] for x in brief["episodes"]],list(IDENTIFIERS))
        self.assertEqual([x["time"] for x in brief["episodes"]],list(SLOTS))
        self.assertEqual([x["type"] for x in brief["episodes"]],
                         ["short","short","long","short"])
        self.assertEqual(brief["date_ist"],"2026-11-12")
        self.assertFalse(brief["safety"]["actual_publishing_allowed"])
        self.assertFalse(brief["safety"]["owner_final_watch"])
        self.assertTrue(brief["safety"]["mock_app_ui_labeled"])
        self.assertEqual(len({x["title"] for x in brief["episodes"]}),4)
        self.assertEqual({x["source"] for x in brief["episodes"]},
                         ALLOWED_SOURCES)
        shorts=[x for x in brief["episodes"] if x["type"]=="short"]
        self.assertEqual(len({x["source"] for x in shorts}),3)
        self.assertEqual([len(x["scenes"]) for x in brief["episodes"]],
                         [5,5,12,5])
        for ep in brief["episodes"]:
            joined=" ".join(s[-1] for s in ep["scenes"])
            self.assertEqual(len(joined.split()),
                             sum(len(s[3].split()) for s in ep["scenes"]))
            self.assertTrue(ep["description"].startswith(
                "Illustrative" if ep["id"].startswith("nov12_short_a") else
                "AI models" if "fake_citations" in ep["id"] else
                "Original" if ep["type"]=="long" else "Demonstrated"))
            for scene in ep["scenes"]:
                parts=split_script(scene[3],ep["type"])
                self.assertEqual(" ".join(parts)," ".join(scene[3].split()))
                self.assertTrue(all(len(p)>7 for p in parts))
        self.assertFalse(any("guaranteed viral" in x["description"].lower()
                             for x in brief["episodes"]))

    def test_all_scripts_cite_only_official_vendor_evidence_not_generated_news(self):
        brief,_=load_brief()
        for ep in brief["episodes"]:
            self.assertIn(ep["source"],ALLOWED_SOURCES)
            self.assertIn(ep["source"],ep["description"])
            self.assertNotIn("I tested",ep["description"])
            self.assertNotIn("captured your account",ep["description"])
            self.assertTrue(ep["title"].endswith("#Shorts")
                            if ep["type"]=="short" else len(ep["title"])<85)
        self.assertEqual(VIDEO_SIZE,{"short":(1080,1920),"long":(1920,1080)})

    def test_tampered_source_brief_rejected_without_publish_permissions(self):
        from unittest.mock import patch
        for invalid in (BRIEF.parent/"wrong_file.json",
                        Path("/tmp/nov12-untested-input.json")):
            with self.assertRaises(FourVideoRefused):
                load_brief(invalid)
        original,_=load_brief()
        self.assertFalse(original["safety"]["actual_publishing_allowed"])

    def test_actual_pcm_stamps_bounded_and_synchronized(self):
        self.assertEqual(secs_stamp(61.345),"00:01:01,345")
        self.assertEqual(secs_stamp(61.345,True),"0:01:01.34")
        for wrong in (-1,3601,float("nan"),float("inf")):
            with self.assertRaises(FourVideoRefused):
                secs_stamp(wrong)


@unittest.skipUnless(importlib.util.find_spec("PIL"),
                     "Physical Pillow source only on no-publish render runner")
class Nov12ActualOriginalPixelTests(unittest.TestCase):
    def test_all_four_mobile_and_landscape_story_frames_are_not_template_duplicates(self):
        from PIL import Image,ImageChops
        from autopilot.branch1_nov12_four_review_videos import render_frame,PALETTE
        brief,_=load_brief()
        seen=set()
        for ep,color in zip(brief["episodes"],PALETTE):
            portrait=ep["type"]=="short"
            frame_hashes=[]
            for i,scene in enumerate(ep["scenes"]):
                base=render_frame(ep,scene,i,0,color)
                end=render_frame(ep,scene,i,2,color)
                self.assertEqual(base.size,VIDEO_SIZE[ep["type"]])
                self.assertEqual(end.size,base.size)
                self.assertEqual(base.mode,"RGB")
                self.assertEqual(end.mode,"RGB")
                import hashlib
                key=hashlib.sha256(end.tobytes()).hexdigest()
                self.assertNotIn(key,seen)
                seen.add(key)
                frame_hashes.append(key)
                self.assertIsNotNone(ImageChops.difference(base,end).getbbox())
                # The native subtitle panel stays steady across transitions.
                mid=(540,1634) if portrait else (960,910)
                self.assertEqual(base.getpixel(mid),end.getpixel(mid))
            self.assertEqual(len(set(frame_hashes)),len(ep["scenes"]))
        self.assertEqual(len(seen),27)

    def test_purposeful_visual_one_way_states_do_not_loop_or_spin(self):
        from PIL import ImageChops
        from autopilot.branch1_nov12_four_review_videos import render_frame,PALETTE
        brief,_=load_brief()
        for ep,color in zip(brief["episodes"],PALETTE):
            scene=ep["scenes"][0]
            p0=render_frame(ep,scene,0,0,color)
            p1=render_frame(ep,scene,0,1,color)
            p2=render_frame(ep,scene,0,2,color)
            self.assertIsNotNone(ImageChops.difference(p0,p1).getbbox())
            self.assertIsNotNone(ImageChops.difference(p1,p2).getbbox())
            # Re-rendering same source and phase is deterministic, not a
            # time-based perpetual animation or random filler.
            self.assertFalse(ImageChops.difference(
                p2,render_frame(ep,scene,0,2,color)).getbbox())
        for invalid in (-1,3,True,"1",None):
            with self.assertRaises(FourVideoRefused):
                render_frame(brief["episodes"][0],
                             brief["episodes"][0]["scenes"][0],0,
                             invalid,PALETTE[0])

    def test_long_video_uses_original_synthetic_data_workbook_not_empty_half_screen(self):
        from PIL import ImageChops
        from autopilot.branch1_nov12_four_review_videos import render_frame,PALETTE
        brief,_=load_brief()
        ep=brief["episodes"][2]
        self.assertEqual(ep["type"],"long")
        self.assertEqual(ep["scenes"][0][0],"EXCEL CHANGED AN ID")
        for scene_index in (0,4,7):
            scene=ep["scenes"][scene_index]
            early=render_frame(ep,scene,scene_index,0,PALETTE[2])
            after=render_frame(ep,scene,scene_index,2,PALETTE[2])
            left_area=(108,355,747,790)
            region_before=early.crop(left_area)
            region_after=after.crop(left_area)
            self.assertIsNotNone(ImageChops.difference(
                region_before,region_after).getbbox(),
                "Fictional spreadsheet demonstration must visibly advance")
            self.assertNotEqual(early.getpixel((320,475)),(8,17,30),
                "No blank left half: visible illustration must cover screen")
            self.assertEqual(early.getpixel((960,910)),after.getpixel((960,910)),
                             "Actual subtitle-safe panel must never animate")

    def test_first_frames_name_the_actual_software_or_failure_before_brand(self):
        brief,_=load_brief()
        hooks=[ep["scenes"][0][0] for ep in brief["episodes"]]
        self.assertEqual(hooks,["EXCEL CHANGED IT","AI CITATION: FAKE?",
                                "EXCEL CHANGED AN ID","DRIVE LINK PUBLIC?"])
        self.assertTrue(all(len(hook)<=22 for hook in hooks))

    def test_all_covers_are_original_high_resolution(self):
        from PIL import Image
        from autopilot.branch1_nov12_four_review_videos import build_cover,PALETTE
        brief,_=load_brief()
        with TemporaryDirectory() as d:
            for ep,accent in zip(brief["episodes"],PALETTE):
                path=build_cover(ep,accent,Path(d))
                with Image.open(path) as frame:
                    frame.load()
                    self.assertEqual(frame.size,
                                     (1080,1920) if ep["type"]=="short"
                                     else (1280,720))


if __name__=="__main__":
    unittest.main()
