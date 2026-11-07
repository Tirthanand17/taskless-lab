"""B4g1 exact 17 original PCM scene navigation, no media release.

All fixtures contain synthetic bytes and no authenticated YouTube operation.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import autopilot.manual_rehearsal_review_export_b4e3 as review
from autopilot.audio_scene_navigation_b4g1 import (
    SceneTimecodeRefused,build_audio_scene_timeline,validate_audio_scene_timeline,
)
from autopilot.review_worksheet_validator_b4e6 import (
    ReviewValidationError,inspect,
)
from autopilot.test_manual_rehearsal_review_export_b4e3 import (
    qa_and_three_original_mp4s,
)


class PreciseSyntheticPCMClockTests(unittest.TestCase):
    def test_synthetic_timeline_exact_original_duration_and_order(self):
        for count,total in ((4,57.8),(9,241.5),(4,57.3)):
            rows=build_audio_scene_timeline([total/count]*count,total,count)
            self.assertEqual(len(rows),count)
            self.assertEqual(rows[0]["start_seconds"],0)
            self.assertEqual(rows[-1]["end_seconds"],round(total,3))
            self.assertEqual([x["scene_number"] for x in rows],
                             list(range(1,count+1)))
            self.assertEqual(validate_audio_scene_timeline(rows,total,count),rows)
            for earlier,later in zip(rows,rows[1:]):
                self.assertEqual(earlier["end_seconds"],later["start_seconds"])

    def test_missing_gap_overlaps_bad_duration_and_spoofed_flags_rejected(self):
        for durations,total,count in (
            ([1.,3.,3.,50.],57.,4),
            ([14.]*4,57.3,4),
            ([14.,float("nan"),14.,14.],57.3,4),
            ([14.,14.,14.],42.,4),
            ([True,14.,14.,14.],42.,4),
            ([27.]*10,270.,10),
        ):
            with self.subTest(duration=durations),self.assertRaises(SceneTimecodeRefused):
                build_audio_scene_timeline(durations,total,count)
        rows=build_audio_scene_timeline([14.45]*4,57.8,4)
        edits=(
            lambda r:r[0].update(start_seconds=1),
            lambda r:r[1].update(start_seconds=r[1]["start_seconds"]+1),
            lambda r:r[2].update(scene_number=2),
            lambda r:r[3].update(end_seconds=999),
            lambda r:r[0].update(start_seconds=True),
            lambda r:r[0].update(start_seconds=-0.01),
            lambda r:r[0].update(start_seconds=float("inf")),
            lambda r:r[0].update(extra_permission=True),
        )
        for edit in edits:
            other=deepcopy(rows)
            edit(other)
            with self.subTest(edit=str(edit)),self.assertRaises(SceneTimecodeRefused):
                validate_audio_scene_timeline(other,57.8,4)


class SHAOriginalOwnerSceneReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.root=Path(self.tmp.name)/"source"
        self.root.mkdir()
        self.out=Path(self.tmp.name)/"owner"
        self.report=qa_and_three_original_mp4s(self.root)
        self.settings=patch.multiple(review,ROOT=self.root,TARGET=self.out)
        self.settings.start()

    def tearDown(self):
        self.settings.stop()
        self.tmp.cleanup()

    def test_exact_17_seeks_bound_to_three_original_mp4_digests(self):
        manifest=review.prepare_review_export(self.root,self.out,self.report)
        worksheet=json.loads((self.out/"HUMAN_REVIEW_WORKSHEET_UNFILLED.json").read_text())
        summary=inspect(manifest,worksheet)
        self.assertEqual(summary["individual_checks_not_reviewed"],47)
        self.assertEqual(summary["self_reported_reviewed_scenes"],0)
        self.assertFalse(summary["youtube_release_authorized"])
        self.assertEqual([len(v["scene_timeline_from_original_pcm"])
                          for v in manifest["videos"]],[4,9,4])
        for video,entry in zip(worksheet["videos"],manifest["videos"]):
            for scene,point in zip(video["scenes"],entry["scene_timeline_from_original_pcm"]):
                self.assertEqual(scene["source_start_seconds"],point["start_seconds"])
                self.assertEqual(scene["source_end_seconds"],point["end_seconds"])
                self.assertEqual(scene["review_status"],"NOT_REVIEWED")
        html=(self.out/"OPEN_LOCAL_REVIEW_DASHBOARD.html").read_text()
        self.assertIn('className="scene-jump"',html)
        self.assertIn('formatSignalTime(scene.source_start_seconds)',html)
        self.assertIn('player.currentTime=Math.max(0,timestamp)',html)
        self.assertIn('player.pause();player.focus();',html)
        self.assertNotIn('player.play(',html)
        self.assertNotIn("fetch(",html)
        self.assertIn("connect-src 'none'",html)

    def test_tampered_manifest_and_private_notes_cannot_shift_scene_identity(self):
        manifest=review.prepare_review_export(self.root,self.out,self.report)
        worksheet=json.loads((self.out/"HUMAN_REVIEW_WORKSHEET_UNFILLED.json").read_text())
        broken=deepcopy(worksheet)
        broken["videos"][0]["scenes"][1]["source_start_seconds"]+=1
        with self.assertRaises(ReviewValidationError):
            inspect(manifest,broken)
        broken=deepcopy(worksheet)
        broken["videos"][1]["scenes"][0].pop("source_start_seconds")
        with self.assertRaises(ReviewValidationError):
            inspect(manifest,broken)
        m=deepcopy(manifest)
        m["videos"][1]["scene_timeline_from_original_pcm"][1]["end_seconds"]+=2
        with self.assertRaises(ReviewValidationError):
            inspect(m,worksheet)
        broken=deepcopy(worksheet)
        broken["videos"][0]["scenes"][0]["review_status"]="PASS"
        with self.assertRaises(ReviewValidationError):
            inspect(manifest,broken)

    def test_source_missing_or_forged_audio_clock_rejected_before_artifact(self):
        for edit in (
            lambda e:e.pop("pcm_derived_scene_timeline_seconds"),
            lambda e:e.update(scene_timeline_derived_from_actual_pcm=False),
            lambda e:e["pcm_derived_scene_timeline_seconds"][2].update(
                start_seconds=100),
        ):
            obj=deepcopy(self.report)
            edit(obj["episodes"][0])
            with self.subTest(edit=str(edit)),self.assertRaises(review.ReviewExportRefused):
                review.prepare_review_export(self.root,self.out,obj)
            self.assertFalse(self.out.exists())


if __name__=="__main__":
    unittest.main()
