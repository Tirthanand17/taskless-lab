"""B4e0: adversarial source-locked actual voice preview planning and safety QA."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from autopilot.real_rehearsal_voice_media_b4e0 import (
    STATUS, SLOTS, VOICES, PhysicalPreviewRefused, prepare_preview_plan,
    original_preview_frame, inspect_physical_preview, _wrap,
)
from autopilot.nonfactual_narration_rehearsal import build_nonfactual_rehearsals
from autopilot.test_nonfactual_narration_rehearsal_b4d9 import pipeline


class PhysicalVoiceRehearsalPlanningTests(unittest.TestCase):
    def setUp(self):
        self.inputs=pipeline()
        self.rehearsals=build_nonfactual_rehearsals(*self.inputs)

    def plan(self,**updates):
        names=("original","aligned","board","scout","evidence","briefs",
               "passages","docket","rehearsals")
        vals=[*self.inputs,self.rehearsals]
        for key,value in updates.items():
            vals[names.index(key)]=value
        return prepare_preview_plan(*vals)

    def test_three_distinct_true_original_narration_excerpt_voice_plans(self):
        data=self.plan()
        self.assertEqual(data["three_previews_planned"],3)
        self.assertEqual(len(data["episodes"]),3)
        self.assertEqual([e["slot"] for e in data["episodes"]],list(SLOTS))
        self.assertEqual([e["kind"] for e in data["episodes"]],
                         ["short","long","short"])
        self.assertEqual([e["size"] for e in data["episodes"]],
                         [(1080,1920),(1920,1080),(1080,1920)])
        self.assertEqual([e["voice"] for e in data["episodes"]],
                         [VOICES[x] for x in SLOTS])
        self.assertEqual(len({x["rehearsal_sha256"] for x in data["episodes"]}),3)
        self.assertFalse(data["release_authorized"])
        self.assertEqual(data["source_quotations"],0)
        self.assertEqual(data["live_external_ai_calls"],0)
        self.assertEqual(data["approved_facts"],0)
        self.assertEqual(data["youtube_uploads"],0)
        for e in data["episodes"]:
            self.assertEqual(len(e["scenes"]),2)
            self.assertEqual(e["source_articles_quoted"],0)
            self.assertFalse(e["youtube_upload_allowed"])
            self.assertFalse(e["full_day_episode_rendered"])
            for i,part in enumerate(e["scenes"]):
                source=self.rehearsals["three_episodes"][list(SLOTS).index(
                    e["slot"])]["scenes"][i]
                self.assertEqual(part["scene"],i)
                self.assertTrue(source[
                    "original_voiceover_rehearsal_text"].startswith(
                    part["original_voiceover_text"]))
                self.assertGreaterEqual(len(part["original_voiceover_text"].split()),8)
                self.assertEqual(
                    part["original_text_sha256"],
                    sha256(part["original_voiceover_text"].encode()).hexdigest())
                self.assertEqual(part["scene_id"],source["scene_id"])

    def test_no_publisher_article_title_or_literal_snippet_in_voice_text(self):
        p=json.dumps(self.plan())
        for brief in self.inputs[5]["episodes"]:
            if brief["unverified_topic_title"]:
                self.assertNotIn(brief["unverified_topic_title"],p)
        for source in self.inputs[6]["sources"]:
            for record in source["passages"]:
                self.assertNotIn(record["literal_excerpt_unverified"],p)
        self.assertNotIn("http://",p)
        self.assertNotIn("https://",p)
        self.assertNotIn("bearer ",p.lower())

    def test_reordered_short_evening_and_morning_episodes_refused(self):
        b=deepcopy(self.rehearsals)
        b["three_episodes"][0],b["three_episodes"][2]=(
            b["three_episodes"][2],b["three_episodes"][0])
        with self.assertRaises(PhysicalPreviewRefused):
            self.plan(rehearsals=b)

    def test_forged_scene_text_or_word_source_sha_refused(self):
        for mutate in (
            lambda r:r["three_episodes"][0]["scenes"][0].update(
                original_voiceover_rehearsal_text="A model can safely control everything."),
            lambda r:r["three_episodes"][0].update(
                source_research_brief_sha256="f"*64),
            lambda r:r["three_episodes"][1].update(
                unverified_source_id="0"*24),
            lambda r:r["three_episodes"][2]["scenes"][0].update(
                source_quote_display_allowed=True),
            lambda r:r["three_episodes"][0].update(release_authorized=True),
            lambda r:r["three_episodes"][1].update(
                real_factual_script_approved=True),
        ):
            tampered=deepcopy(self.rehearsals)
            mutate(tampered)
            with self.subTest(mutation=str(mutate)),self.assertRaises(
                    PhysicalPreviewRefused):
                self.plan(rehearsals=tampered)

    def test_forged_fact_approval_and_any_media_model_provider_claim_refused(self):
        for k,v in (
            ("factual_news_scripts_completed",1),
            ("provider_model_calls",2),
            ("actual_video_files_created",3),
            ("release_authorized",True),
        ):
            r=deepcopy(self.rehearsals)
            r[k]=v
            with self.subTest(field=k),self.assertRaises(PhysicalPreviewRefused):
                self.plan(rehearsals=r)

    def test_changed_original_source_article_checksum_refused(self):
        evidence=deepcopy(self.inputs[4])
        evidence["sources"][0]["response_sha256"]="f"*64
        with self.assertRaises(PhysicalPreviewRefused):
            self.plan(evidence=evidence)

    def test_article_quote_rights_cannot_be_promoted(self):
        passages=deepcopy(self.inputs[6])
        passages["sources"][0]["passages"][0][
            "not_licensed_for_narration_or_public_reuse"]=False
        with self.assertRaises(PhysicalPreviewRefused):
            self.plan(passages=passages)

    def test_fake_reviewer_or_wrong_editorial_plan_refused(self):
        b=deepcopy(self.inputs[7])
        b["dockets"][0]["factual_script_exists"]=True
        with self.assertRaises(PhysicalPreviewRefused):
            self.plan(docket=b)
        aligned=deepcopy(self.inputs[1])
        aligned["youtube_schedule_enabled"]=True
        with self.assertRaises(PhysicalPreviewRefused):
            self.plan(aligned=aligned)

    def test_three_episodes_not_full_media_or_published(self):
        report=self.plan()
        self.assertEqual(report["status"],
                         "B4E0_EPHEMERAL_SOURCE_LOCKED_PREVIEW_PLAN_NO_PUBLISH")
        self.assertEqual(report["three_previews_planned"],3)
        self.assertFalse(report["release_authorized"])
        self.assertTrue(all(not x["full_day_episode_rendered"] for x in report[
            "episodes"]))
        self.assertTrue(all(x["youtube_upload_allowed"] is False for x in report[
            "episodes"]))

    def test_original_sentences_have_real_punctuation_and_are_not_unwritten(self):
        for ep in self.plan()["episodes"]:
            texts=[x["original_voiceover_text"] for x in ep["scenes"]]
            self.assertNotEqual(texts[0],texts[1])
            for t in texts:
                self.assertTrue(t.endswith((".", "!", "?")))
                self.assertNotIn("TODO",t)
                self.assertNotIn("[INSERT",t)

    def test_caption_layout_rejects_truncated_words(self):
        with self.assertRaises(PhysicalPreviewRefused):
            _wrap(" ".join(["UNUSABLY_LONG_SENTENCE"]*100),18,2)
        self.assertEqual(_wrap("This is one fully readable sentence.",24,3),
                         ["This is one fully","readable sentence."])

    def test_no_network_or_external_model_calls_during_rehearsal_preparation(self):
        import urllib.request
        with patch.object(urllib.request,"urlopen",
                          side_effect=AssertionError("External HTTP")):
            p=self.plan()
        self.assertEqual(p["live_external_ai_calls"],0)
        self.assertEqual(p["youtube_uploads"],0)

    @unittest.skipUnless(importlib.util.find_spec("PIL"),
                         "Pillow only available in production voice media job")
    def test_two_original_pixel_distinct_frames_portrait_and_landscape(self):
        from PIL import Image
        plan=self.plan()
        with TemporaryDirectory() as root:
            for e in plan["episodes"]:
                outputs=[]
                for i,scene in enumerate(e["scenes"]):
                    target=Path(root)/e["slot"]/f"scene{i}.png"
                    digest=original_preview_frame(e,scene,target)
                    self.assertEqual(len(digest),64)
                    with Image.open(target) as img:
                        img.load()
                        self.assertEqual(img.size,e["size"])
                        self.assertEqual(img.mode,"RGB")
                    outputs.append(digest)
                self.assertEqual(len(set(outputs)),2)

    def test_fake_nonexistent_mp4_never_accepted_as_real_av_decode(self):
        data=self.plan()["episodes"][0]
        with TemporaryDirectory() as root:
            with self.assertRaises(PhysicalPreviewRefused):
                inspect_physical_preview(
                    "/usr/bin/ffmpeg",Path(root)/"missing.mp4",data,
                    7.,[])

    def test_full_sample_text_is_still_4_9_4_not_fake_all_episode_media(self):
        p=self.plan()
        self.assertEqual([len(x["scenes"]) for x in p["episodes"]],[2,2,2])
        self.assertEqual([len(x["scenes"]) for x in self.rehearsals[
            "three_episodes"]],[4,9,4])


if __name__=="__main__":
    unittest.main()
