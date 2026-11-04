"""B3d4c2c3b fast no-network preflight and replay-safe animation tests.

Actual 3 Kokoro CPU real voice + SVG/FFmpeg files are executed in a separate
GitHub-hosted integration job; these unit tests never pretend to be real audio.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.full_topic_narrated_pack import (
    FRAMES_PER_SCENE,STATUS,TopicRenderError,
    episode_from_research_story,variable_frame_concat_lines,
    prepare_story_timing,visible_topic_motion_pulse,
)
from autopilot.primary_sourced_storyboards import (
    SLOTS,build_story,require_exact_draft,StoryboardError,
)
from autopilot.signed_narrated_cloud_pack import VOICE_FOR_SLOT


def fixture_timeline(slot: str):
    story=build_story(slot)
    root=Path("/tmp/flowminute-b3d4c2c3b-immutable-test")
    groups=[
        [
            root/f"moving_{i+1:02d}_{j:02d}.png"
            for j in range(FRAMES_PER_SCENE)
        ] for i in range(story["scene_count"])
    ]
    times=[]
    t=0.0
    for i in range(story["scene_count"]):
        d=6.0+i*.02
        times.append({"start":t,"duration":d})
        t+=d
    return story,root,groups,times


class TopicFullNarrationPreflightTests(unittest.TestCase):
    def test_new_stories_are_real_topic_narration_not_generic_csv_fixture(self):
        seen=set()
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            episode=episode_from_research_story(story)
            self.assertEqual(episode.voice,VOICE_FOR_SLOT[slot])
            self.assertEqual(episode.kind,story["format"])
            self.assertEqual(len(episode.scenes),story["scene_count"])
            self.assertEqual(tuple(x.narration for x in episode.scenes),
                             tuple(x["narration"] for x in story["scenes"]))
            self.assertEqual(episode.episode_id,story["episode_id"])
            self.assertIn("source_linked",STATUS.lower())
            self.assertNotIn("member_id", " ".join(s.narration for s in episode.scenes))
            seen.add(episode.theme)
        self.assertEqual(len(seen),3)

    def test_all_real_source_claim_narrations_are_usable_for_pcm_srt(self):
        for slot in SLOTS:
            item=prepare_story_timing(build_story(slot))
            self.assertEqual(item["voice"],VOICE_FOR_SLOT[slot])
            self.assertEqual(item["scene_count"],20 if slot=="long" else 6)
            self.assertGreaterEqual(item["caption_chunk_count"],8)
            self.assertFalse(item["source_human_fact_review_verified"])
            self.assertFalse(item["tts_output_or_video_generated"])
            self.assertFalse(item["youtube_upload_enabled"])
            self.assertFalse(item["release_authorized"])

    def test_timeline_is_exact_5_unique_motion_frames_per_spoken_scene(self):
        for slot in SLOTS:
            story,root,groups,times=fixture_timeline(slot)
            scene,animated=variable_frame_concat_lines(
                story,times,groups,scene_index_dir=root,
            )
            self.assertEqual(scene.count("\nfile "),len(groups)+1)
            self.assertEqual(scene.count("\nduration "),len(groups))
            self.assertEqual(animated.count("\nfile "),
                             len(groups)*FRAMES_PER_SCENE+1)
            self.assertEqual(animated.count("\nduration "),
                             len(groups)*FRAMES_PER_SCENE)
            self.assertTrue(scene.startswith("ffconcat version 1.0\n"))
            self.assertTrue(animated.startswith("ffconcat version 1.0\n"))
            self.assertEqual(animated.count("moving_"),
                             len(groups)*FRAMES_PER_SCENE+1)

    def test_wrong_timing_overlap_gap_nonfinite_and_truncated_rejected(self):
        story,root,groups,times=fixture_timeline("short_am")
        for i,bad in (
            (0,{"start":0.0,"duration":0.0}),
            (0,{"start":0.0,"duration":41.0}),
            (0,{"start":float("nan"),"duration":6.0}),
            (1,{"start":999.0,"duration":6.02}),
            (2,{"start":0.0,"duration":6.04}),
        ):
            t=deepcopy(times)
            t[i]=bad
            with self.subTest(idx=i,bad=bad),self.assertRaises(TopicRenderError):
                variable_frame_concat_lines(story,t,groups,scene_index_dir=root)

    def test_every_original_topic_has_five_distinct_motion_positions_above_captions(self):
        for slot in SLOTS:
            story=build_story(slot)
            positions=[visible_topic_motion_pulse(story,j*24)
                       for j in range(FRAMES_PER_SCENE)]
            self.assertEqual(len(set(positions)),FRAMES_PER_SCENE)
            width,height=(1080,1920) if slot!="long" else (1920,1080)
            caption_panel_top=height-(380 if slot!="long" else 265)
            for x,y in positions:
                self.assertGreater(x,65)
                self.assertLess(x,width-65)
                self.assertLess(y+30,caption_panel_top)
        for bad in (-1,121,True,False,1.5):
            with self.subTest(tick=bad),self.assertRaises(TopicRenderError):
                visible_topic_motion_pulse(build_story("long"),bad)

    def test_mismatched_scene_frame_count_or_duplicated_asset_path_rejected(self):
        story,root,groups,times=fixture_timeline("short_pm")
        with self.assertRaises(TopicRenderError):
            variable_frame_concat_lines(story,times,groups[:-1],scene_index_dir=root)
        g=deepcopy(groups)
        g[0]=g[0][:-1]
        with self.assertRaises(TopicRenderError):
            variable_frame_concat_lines(story,times,g,scene_index_dir=root)
        g=deepcopy(groups)
        g[1][0]=g[0][0]
        with self.assertRaises(TopicRenderError):
            variable_frame_concat_lines(story,times,g,scene_index_dir=root)

    def test_unsafe_foreign_frame_or_changed_order_rejected(self):
        story,root,groups,times=fixture_timeline("long")
        for wrong in (
            root.parent/"foreign.png",
            root/"moving_02_01.png",
            root/"../../danger.png",
            root/"moving_01_00.jpg",
        ):
            g=deepcopy(groups)
            g[0][0]=wrong
            with self.subTest(asset=wrong),self.assertRaises(TopicRenderError):
                variable_frame_concat_lines(story,times,g,scene_index_dir=root)

    def test_no_source_story_cannot_bypass_canonical_signed_draft(self):
        original=build_story("long")
        for key,value in (
            ("youtube_upload_enabled",True),
            ("independent_claim_by_claim_human_review_passed",True),
            ("voice_music_image_rights_approved",True),
            ("human_full_watch_listen_completed",True),
            ("release_authorized",True),
            ("draft_sha256","0"*64),
        ):
            s=deepcopy(original)
            s[key]=value
            with self.subTest(field=key),self.assertRaises(StoryboardError):
                episode_from_research_story(s)
        broken=deepcopy(original)
        broken["scenes"][1]["narration"]="The model made up this line."
        with self.assertRaises(StoryboardError):
            episode_from_research_story(broken)

    def test_wrong_episode_date_and_scene_beat_reuse_rejected(self):
        s=build_story("short_am")
        s["episode_id"]="fm_20261113_long"
        with self.assertRaises(StoryboardError):
            episode_from_research_story(s)
        s=build_story("long")
        s["scenes"][3]["scene_id"]=s["scenes"][0]["scene_id"]
        with self.assertRaises(StoryboardError):
            episode_from_research_story(s)

    def test_distinct_voices_original_topics_and_ist_slots(self):
        voices=set()
        themes=set()
        for slot in SLOTS:
            s=build_story(slot)
            ep=episode_from_research_story(s)
            voices.add(ep.voice)
            themes.add(ep.theme)
            self.assertEqual(s["time_ist"],SLOTS[slot]["time_ist"])
        self.assertEqual(len(voices),3)
        self.assertEqual(len(themes),3)

    def test_no_publishing_or_external_model_client_exposed(self):
        import autopilot.full_topic_narrated_pack as impl
        for callable_name in (
            "videos_insert","upload_to_youtube","create_gemini_client",
            "publish_video","get_paid_provider_key","create_production_cloud_db",
        ):
            self.assertFalse(hasattr(impl,callable_name))


if __name__=="__main__":
    unittest.main()
