"""B4e1 offline adversarial full physical narration plan/source/audio QA."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from autopilot.full_original_rehearsal_media_b4e1 import (
    PLAN_STATUS,STATUS,FullRehearsalRefused,
    prepare_full_rehearsal_plan,split_original_voice_to_cues,
    _draw_original_full_scene,_stamp,_inspect_full,
)
from autopilot.nonfactual_narration_rehearsal import (
    build_nonfactual_rehearsals,THEMES,_paragraphs,
)
from autopilot.test_nonfactual_narration_rehearsal_b4d9 import pipeline


class FullOriginalNarrationSourceSafetyTests(unittest.TestCase):
    def setUp(self):
        self.original_documents=pipeline()
        self.rehearsals=build_nonfactual_rehearsals(*self.original_documents)

    def plan(self,**updates):
        names=("original","aligned","board","scout","evidence","briefs",
               "passages","docket","rehearsals")
        args=[*self.original_documents,self.rehearsals]
        for key,value in updates.items():
            args[names.index(key)]=value
        return prepare_full_rehearsal_plan(*args)

    def test_actual_complete_original_17_scene_script_handoff(self):
        plan=self.plan()
        self.assertEqual(plan["status"],PLAN_STATUS)
        self.assertEqual(plan["three_original_complete_rehearsals_planned"],3)
        self.assertEqual(plan["original_full_scene_count"],17)
        self.assertEqual([x["all_scene_count"] for x in plan["episodes"]],[4,9,4])
        self.assertEqual([x["slot"] for x in plan["episodes"]],
                         ["short_am","long","short_pm"])
        self.assertEqual([x["voice"] for x in plan["episodes"]],
                         ["af_heart","am_michael","bf_emma"])
        self.assertEqual([x["size"] for x in plan["episodes"]],
                         [[1080,1920],[1920,1080],[1080,1920]])
        self.assertEqual([x["target_seconds_not_audio_verified"] for x in
                          plan["episodes"]],[58.,240.,58.])
        self.assertFalse(plan["release_authorized"])
        self.assertEqual(plan["approved_news_facts"],0)
        self.assertEqual(plan["paid_model_calls"],0)
        self.assertEqual(plan["youtube_uploads"],0)
        ids=[]
        for episode in plan["episodes"]:
            self.assertFalse(episode["source_quote_reuse_allowed"])
            self.assertFalse(episode["real_world_factual_claim_approved"])
            self.assertFalse(episode["release_authorized"])
            self.assertFalse(episode["youtube_upload_allowed"])
            self.assertTrue(8<=episode["total_original_caption_phrases"]<=100)
            self.assertEqual(len(episode["scenes"]),episode["all_scene_count"])
            for j,scene in enumerate(episode["scenes"]):
                self.assertEqual(scene["scene"],j)
                ids.append((episode["episode_id"],scene["scene_id"]))
                self.assertFalse(scene["news_claim_fact_checked"])
                self.assertFalse(scene["source_quote_display_allowed"])
                self.assertTrue(scene["original_voiceover_text"])
                self.assertEqual(
                    " ".join(scene["caption_cues"]),
                    " ".join(scene["original_voiceover_text"].split()),
                )
                self.assertEqual(scene["cap_count"],len(scene["caption_cues"]))
                self.assertEqual(
                    scene["spoken_text_sha256"],
                    sha256(scene["original_voiceover_text"].encode()).hexdigest(),
                )
        self.assertEqual(len(set(ids)),17)

    def test_no_article_text_copied_into_actual_speech(self):
        content=json.dumps(self.plan())
        self.assertNotIn("https://",content)
        for brief in self.original_documents[5]["episodes"]:
            title=brief["unverified_topic_title"]
            if title:
                self.assertNotIn(title,content)
        for group in self.original_documents[6]["sources"]:
            for passage in group["passages"]:
                self.assertNotIn(passage["literal_excerpt_unverified"],content)

    def test_all_six_topic_theme_17_sentence_paragraphs_split_without_loss(self):
        for category,theme in THEMES.items():
            for slot in ("short_am","long","short_pm"):
                for original in _paragraphs(slot,theme):
                    cues=split_original_voice_to_cues(original)
                    self.assertGreaterEqual(len(cues),1)
                    self.assertLessEqual(len(cues),9)
                    self.assertTrue(all(8<=len(x)<=152 for x in cues))
                    self.assertEqual(" ".join(cues)," ".join(original.split()))

    def test_long_sentence_does_not_truncate_critical_end(self):
        msg=("This entirely fictional educational example compares a carefully "
             "labeled sample baseline against a separate synthetic workflow and "
             "describes the exact reversible steps that the reviewer would need "
             "to check before attempting a real-world release or publication.")
        parts=split_original_voice_to_cues(msg)
        self.assertGreaterEqual(len(parts),2)
        self.assertEqual(" ".join(parts),msg)
        self.assertTrue(parts[-1].endswith("publication."))

    def test_unsafe_newlines_or_blank_input_refused(self):
        for case in ("", "words "*2, "a"*2000, "This contains\nnewlines "+
                     "and unsafe unstructured input."*4):
            with self.assertRaises(FullRehearsalRefused):
                split_original_voice_to_cues(case)

    def test_mismatched_live_source_hash_or_review_docket_refused(self):
        evidence=deepcopy(self.original_documents[4])
        evidence["sources"][0]["response_sha256"]="0"*64
        with self.assertRaises(FullRehearsalRefused):
            self.plan(evidence=evidence)
        docket=deepcopy(self.original_documents[7])
        docket["dockets"][0]["release_authorized"]=True
        with self.assertRaises(FullRehearsalRefused):
            self.plan(docket=docket)

    def test_script_mutation_and_forged_release_refused(self):
        for mutate in (
            lambda obj:obj["three_episodes"][0]["scenes"][2].update(
                original_voiceover_rehearsal_text="A new unreviewed claim."),
            lambda obj:obj["three_episodes"][1].update(
                actual_video_rendered=True),
            lambda obj:obj.update(youtube_uploads=1),
            lambda obj:obj["three_episodes"][2].update(
                real_factual_script_approved=True),
            lambda obj:obj["three_episodes"][0]["scenes"][1].update(
                source_quote_display_allowed=True),
        ):
            attempt=deepcopy(self.rehearsals)
            mutate(attempt)
            with self.subTest(mutation=str(mutate)),self.assertRaises(
                    FullRehearsalRefused):
                self.plan(rehearsals=attempt)

    def test_would_not_generate_tts_with_publisher_fact_privileges(self):
        original=deepcopy(self.original_documents[1])
        original["youtube_schedule_enabled"]=True
        with self.assertRaises(FullRehearsalRefused):
            self.plan(aligned=original)

    def test_all_scene_ids_cannot_be_substituted_across_long_and_short(self):
        attempt=deepcopy(self.rehearsals)
        attempt["three_episodes"][1]["scenes"][3]["scene_id"]=(
            attempt["three_episodes"][0]["scenes"][1]["scene_id"])
        with self.assertRaises(FullRehearsalRefused):
            self.plan(rehearsals=attempt)

    def test_actual_script_contains_no_loop_spinner_or_third_party_visual(self):
        text=json.dumps(self.plan())
        self.assertNotIn("continuously-rotating-spinner",text)
        self.assertNotIn("paper_figure.png",text)
        self.assertNotIn("commercial_bgm.mp3",text)
        for episode in self.plan()["episodes"]:
            for s in episode["scenes"]:
                self.assertEqual(s["motion_policy"],"single-entry-reveal-static")
                self.assertFalse(s["source_quote_display_allowed"])

    def test_srt_real_time_format_from_pcm_samples(self):
        self.assertEqual(_stamp(0),"00:00:00,000")
        self.assertEqual(_stamp(61.234),"00:01:01,234")
        self.assertEqual(_stamp(239.99),"00:03:59,990")
        with self.assertRaises(FullRehearsalRefused):
            _stamp(float("nan"))
        with self.assertRaises(FullRehearsalRefused):
            _stamp(-0.1)

    def test_absent_video_never_accepted_as_successful_full_h264_decode(self):
        with TemporaryDirectory() as temp:
            ep=self.plan()["episodes"][0]
            with self.assertRaises(FullRehearsalRefused):
                _inspect_full("/does/not/exist",Path(temp)/"absent.mp4",
                              ep,[],0.,[])

    @unittest.skipUnless(importlib.util.find_spec("PIL"),
                         "Pillow physical PNG available only in media CI")
    def test_real_drawn_png_unique_at_every_story_scene_and_correct_geometry(self):
        from PIL import Image
        with TemporaryDirectory() as tmp:
            for ep in self.plan()["episodes"]:
                hashes=[]
                for scene in ep["scenes"]:
                    file=Path(tmp)/ep["slot"]/f"slide{scene['scene']}.png"
                    sha=_draw_original_full_scene(ep,scene,file)
                    with Image.open(file) as im:
                        im.load()
                        self.assertEqual(im.size,tuple(ep["size"]))
                        self.assertEqual(im.mode,"RGB")
                    hashes.append(sha)
                self.assertEqual(len(set(hashes)),len(ep["scenes"]))

    def test_script_preparation_cannot_access_web_or_paid_model(self):
        with patch("urllib.request.urlopen",side_effect=AssertionError("HTTP")):
            p=self.plan()
        self.assertEqual(p["paid_model_calls"],0)
        self.assertEqual(p["approved_news_facts"],0)


if __name__=="__main__":
    unittest.main()
