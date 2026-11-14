"""Adversarial, pure-offline CLIVOX owner scene-review link tests."""
from __future__ import annotations

import copy
import json
import unittest

from scripts.branch3_a5_scene_review_index import (
    SceneReviewIndexDenied, make_scene_review_index
)
from scripts.branch3_a6_original_handoff import CATALOG
from scripts.branch3_original_arcade_pilots import validate_catalog


def clock(second: int) -> str:
    return f"{second // 3600:02d}:{(second // 60) % 60:02d}:{second % 60:02d},000"


def synthetic_srt(episode: dict) -> str:
    return "\n".join(
        f"{n}\n{clock(b['start_s'])} --> {clock(b['end_s'])}\n{b['spoken']}\n"
        for n, b in enumerate(episode["beats"], 1)
    ) + "\n"


class SceneReviewIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.episodes = validate_catalog(json.loads(CATALOG.read_text("utf-8")))

    def build(self, episode, srt=None, video=None):
        return make_scene_review_index(
            episode,
            synthetic_srt(episode) if srt is None else srt,
            video or (episode["id"] + "/original-review-preview.mp4"),
        )

    def test_all_23_scene_links_and_script_text(self):
        total = 0
        for episode in self.episodes:
            html, scenes = self.build(episode)
            self.assertEqual(scenes, len(episode["beats"]))
            self.assertEqual(html.count('class="scene-row"'), scenes)
            self.assertEqual(html.count("#t="), scenes)
            self.assertIn("Draft caption text:", html)
            self.assertIn("NOT evidence", html)
            self.assertNotIn("<script", html.lower())
            self.assertNotIn("https://", html.lower())
            self.assertNotIn("youtube_upload_authorized", html)
            total += scenes
        self.assertEqual(total, 23)

    def test_nonmatching_caption_fails_closed(self):
        ep = self.episodes[0]
        corrupted = synthetic_srt(ep).replace(
            ep["beats"][2]["spoken"], "A fake different sentence."
        )
        with self.assertRaisesRegex(
            SceneReviewIndexDenied, "CAPTIONS_DIFFER"
        ):
            self.build(ep, srt=corrupted)

    def test_cross_scene_extra_and_missing_cues_denied(self):
        ep = self.episodes[0]
        content = synthetic_srt(ep)
        # A syntactically valid first cue that straddles beat 1 and beat 2.
        crossed = content.replace(
            f"{clock(0)} --> {clock(3)}",
            f"{clock(0)} --> {clock(4)}"
        )
        with self.assertRaisesRegex(
            SceneReviewIndexDenied, "SCENE_WITHOUT_CAPTIONS"
        ):
            self.build(ep, srt=crossed)
        missing = "\n".join(content.split("\n\n")[:-1])
        with self.assertRaises(Exception):
            self.build(ep, srt=missing)

    def test_wrong_remote_or_parent_media_path_rejected(self):
        ep = self.episodes[0]
        for path in (
            "../private/file.mp4",
            "https://example.com/video.mp4",
            "clivox_original_other/original-review-preview.mp4",
            ep["id"] + "/../original-review-preview.mp4",
        ):
            with self.subTest(path=path), self.assertRaisesRegex(
                SceneReviewIndexDenied, "LOCAL_MEDIA_ONLY"
            ):
                self.build(ep, video=path)

    def test_html_escaped_and_unapproved_even_with_script_injection(self):
        ep = copy.deepcopy(self.episodes[0])
        ep["beats"][0]["headline"] = "<img src=x onerror=alert(1)>"
        ep["beats"][0]["spoken"] = "Say <script>alert(1)</script> literally."
        html, count = self.build(ep)
        self.assertEqual(count, 5)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;img", html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("<img", html.lower())

    def test_missing_or_tampered_storyboard_structure_rejected(self):
        ep = copy.deepcopy(self.episodes[0])
        ep["beats"][1]["start_s"] += 1
        with self.assertRaisesRegex(SceneReviewIndexDenied, "BEAT_CLOCK_GAP"):
            self.build(ep)
        ep = copy.deepcopy(self.episodes[0])
        ep["beats"][1]["spoken"] = None
        with self.assertRaises(SceneReviewIndexDenied):
            self.build(ep)


if __name__ == "__main__":
    unittest.main()
