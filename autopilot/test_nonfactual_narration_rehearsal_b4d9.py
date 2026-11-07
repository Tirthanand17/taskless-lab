"""B4d9 actual nonfactual original 3-video script rehearsal QA; no live network."""
from __future__ import annotations
from copy import deepcopy
from datetime import date,timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from autopilot.nonfactual_narration_rehearsal import (
    STATUS, RehearsalRefused, THEMES, CASEBOOK, _daily_case, _fresh_opening,
    _paragraphs, _frames_for, _words,
    build_nonfactual_rehearsals,
)
from autopilot.test_ephemeral_claim_review_docket_b4d7 import fixture
from autopilot.ephemeral_claim_review_docket import build_claim_review_docket
from autopilot.test_daily_editorial_board import inputs
from autopilot.daily_editorial_board import build_editorial_board
from autopilot.reconcile_daily_editorial_plan import align_plan_to_editorial_board
from autopilot.source_locked_script_briefs import build_episode_locked_research
from autopilot.public_article_passages import PASSAGE_STATUS


def pipeline():
    first=list(fixture())
    first.append(build_claim_review_docket(*first))
    return first


class ThreeVideoOriginalRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.values=pipeline()

    def run_script(self,**kwargs):
        names=("original","aligned","board","scout","evidence","briefs","passages","docket")
        vals=list(self.values)
        for k,v in kwargs.items():
            vals[names.index(k)]=v
        return build_nonfactual_rehearsals(*vals)

    def test_seven_consecutive_days_have_distinct_true_spoken_examples(self):
        # Same topic and same slot must not recycle the exact narration.
        self.assertEqual(set(CASEBOOK),set(THEMES))
        for family in THEMES:
            self.assertEqual(len(CASEBOOK[family]),7)
            self.assertEqual(len({r[0] for r in CASEBOOK[family]}),7)
            for slot in ("short_am","long","short_pm"):
                scripts=set()
                for n in range(7):
                    day=(date(2026,11,7)+timedelta(days=n)).isoformat()
                    theme,opening=_daily_case(family,slot,day)
                    paragraphs=_fresh_opening(slot,theme,opening)
                    script="\\n".join(paragraphs)
                    self.assertNotIn(script,scripts,
                        (family,slot,day,"recycled same 7-day spoken script"))
                    scripts.add(script)
                    self.assertIn("fictional",script.lower())
                    self.assertNotIn("https://",script)
                    self.assertNotIn("according to the article",script.lower())
                    self.assertEqual(len(paragraphs),9 if slot=="long" else 4)
                    words=_words(script)
                    self.assertTrue((340<=words<=660) if slot=="long"
                                    else (95<=words<=155),
                                    (family,slot,day,words))
                    frames=_frames_for(paragraphs,7200 if slot=="long" else 1740)
                    self.assertGreaterEqual(min(frames),180)
                    self.assertEqual(sum(frames),7200 if slot=="long" else 1740)
                self.assertEqual(len(scripts),7)

    def test_casebook_is_bounded_handcrafted_not_a_source_headline_generator(self):
        example_date="2026-11-07"
        for family,entries in CASEBOOK.items():
            for row in entries:
                self.assertEqual(len(row),6)
                for value in row:
                    self.assertIsInstance(value,str)
                    self.assertTrue(8<=len(value)<=180)
                    self.assertNotIn("https://",value)
                    self.assertNotIn("according to",value.lower())
            a,_=_daily_case(family,"short_am",example_date)
            b,_=_daily_case(family,"short_am","2026-11-08")
            self.assertNotEqual(a["story_name"],b["story_name"])
        for bad in ("2026-02-30","2026-13-01","2026-1-1","garbage"):
            with self.assertRaises(RehearsalRefused):
                _daily_case("agents","short_am",bad)
        with self.assertRaises(RehearsalRefused):
            _daily_case("unsupported","short_am",example_date)
        with self.assertRaises(RehearsalRefused):
            _daily_case("agents","unsanctioned",example_date)

    def test_three_distinct_original_complete_voiceover_rehearsals_exist(self):
        bundle=self.run_script()
        self.assertEqual(bundle["status"],STATUS)
        self.assertEqual(bundle["planned_video_count"],3)
        self.assertEqual(bundle["original_nonfactual_voiceover_rehearsals_written"],3)
        self.assertEqual(bundle["shorts_rehearsals_written"],2)
        self.assertEqual(bundle["long_rehearsals_written"],1)
        self.assertEqual(bundle["original_scene_count"],17)
        self.assertEqual([x["scene_count"] for x in bundle["three_episodes"]],[4,9,4])
        self.assertEqual([x["format"] for x in bundle["three_episodes"]],
                         ["short","long","short"])
        self.assertEqual([x["planned_local_ist"] for x in bundle["three_episodes"]],
                         ["11:00","16:00","20:30"])
        self.assertEqual(len({x["original_working_title_not_news_headline"]
                              for x in bundle["three_episodes"]}),3)
        for x in bundle["three_episodes"]:
            self.assertTrue(x["voiceover_text_written_for_rehearsal"])
            self.assertTrue(x["narration_rehearsal_nonfactual"])
            self.assertFalse(x["factual_news_narration_written"])
            self.assertFalse(x["release_authorized"])
            self.assertTrue(x["original_working_title_not_news_headline"].startswith("Synthetic "))
            self.assertLessEqual(len(x["original_working_title_not_news_headline"]),52,
                                 "Portrait native title card must not overflow")
            self.assertFalse(x["actual_recorded_voice_exists"])
            self.assertFalse(x["actual_video_rendered"])
            self.assertFalse(x["real_factual_script_approved"])
            self.assertFalse(x["real_rights_cleared"])
            self.assertFalse(x["independent_claim_review_approved"])
            self.assertFalse(x["owner_final_watch_approved"])
            self.assertFalse(x["youtube_uploaded"])
            self.assertFalse(x["youtube_scheduled"])
        for k in ("factual_news_scripts_completed","fact_checks_completed",
                  "source_rights_approvals","actual_voice_files_created",
                  "actual_video_files_created","provider_model_calls",
                  "youtube_uploads","youtube_scheduled"):
            self.assertEqual(bundle[k],0)
        self.assertFalse(bundle["release_authorized"])

    def test_short_and_long_frame_accurate_duration_and_original_motion(self):
        data=self.run_script()
        for x in data["three_episodes"]:
            seconds=58 if x["format"]=="short" else 240
            self.assertEqual(x["duration_target_seconds"],seconds)
            self.assertEqual(x["frame_count"],seconds*30)
            self.assertEqual(x["fps"],30)
            self.assertEqual([x["canvas_width"],x["canvas_height"]],
                             [1080,1920] if x["format"]=="short" else [1920,1080])
            self.assertTrue(95<=x["estimated_script_words"]<=155 if x["format"]=="short"
                            else 340<=x["estimated_script_words"]<=660)
            self.assertTrue(85<=x["estimated_narration_wpm"]<=165)
            prev=0
            for scene in x["scenes"]:
                self.assertEqual(scene["start_frame"],prev)
                self.assertEqual(scene["end_frame_exclusive"],
                                 prev+scene["duration_frames"])
                prev=scene["end_frame_exclusive"]
                self.assertGreaterEqual(scene["duration_frames"],180)
                self.assertNotIn("spinner",scene["motion_policy"])
                self.assertNotIn("loop",scene["motion_policy"])
                self.assertTrue(scene["static_safe_area_for_burned_in_captions"])
                self.assertTrue(scene["low_background_music_recommendation_only"])
                self.assertFalse(scene["source_quote_display_allowed"])
                self.assertFalse(scene["third_party_source_visual_allowed"])
                self.assertGreaterEqual(scene["word_count"],10)
            self.assertEqual(prev,x["frame_count"])
            self.assertIn("no third-party screenshots",x["visual_style"])

    def test_voices_are_real_sentences_not_outline_prompts_or_placeholder_strings(self):
        data=self.run_script()
        for x in data["three_episodes"]:
            raw=" ".join(scene["original_voiceover_rehearsal_text"] for scene in x["scenes"])
            self.assertEqual(_words(raw),x["estimated_script_words"])
            self.assertNotIn("[INSERT",raw)
            self.assertNotIn("TODO",raw)
            self.assertNotIn("claim pending:",raw)
            self.assertIn("fictional",raw.lower())
            self.assertNotIn("http",raw)
            self.assertNotIn("published",raw.lower())
            self.assertNotIn("the study proves",raw.lower())

    def test_untrusted_article_title_never_embedded_in_voices_or_working_titles(self):
        b=self.run_script()
        output=json.dumps(b)
        for original in self.values[5]["episodes"]:
            title=original["unverified_topic_title"]
            if title:
                self.assertNotIn(title,output)
        for d in self.values[7]["dockets"]:
            for excerpt in d["literal_passage_questions_needing_human_review"]:
                self.assertNotIn(excerpt["literal_excerpt_unverified"],output)
        self.assertNotIn("https://",output)

    def test_every_beat_bound_to_exact_original_research_brief_and_docket(self):
        result=self.run_script()
        for i,x in enumerate(result["three_episodes"]):
            b=self.values[5]["episodes"][i]
            docket=self.values[7]["dockets"][i]
            self.assertEqual(x["episode_id"],b["episode_id"])
            self.assertEqual(x["unverified_source_id"],b["source_id"])
            self.assertEqual(x["unverified_source_full_response_sha256"],
                             b["source_observation_sha256"])
            self.assertEqual(x["source_research_brief_sha256"],
                             sha256(json.dumps(b,ensure_ascii=True,
                                              sort_keys=True,
                                              separators=(",",":")).encode("ascii")).hexdigest())
            self.assertEqual(x["source_claim_docket_sha256"],
                             sha256(json.dumps(docket,ensure_ascii=True,
                                              sort_keys=True,
                                              separators=(",",":")).encode("ascii")).hexdigest())
            self.assertEqual(x["claim_review_passages_not_quoted"],
                             len(docket["literal_passage_questions_needing_human_review"]))

    def test_mismatched_episode_docket_or_source_forgery_refused(self):
        original_docket=self.values[7]
        for mutation in (
            lambda d:d["dockets"][0].update(episode_id="fm_20261107_long"),
            lambda d:d["dockets"][1].update(research_source_id="0"*24),
            lambda d:d["dockets"][0].update(claim_investigation_status="FACT_VERIFIED"),
            lambda d:d["dockets"][0].update(factual_script_exists=True),
            lambda d:d["dockets"][0].update(release_authorized=True),
            lambda d:d.update(semantic_claims_verified=1),
            lambda d:d.update(external_ai_calls=1),
            lambda d:d.update(rights_approvals=1),
        ):
            with self.subTest(mutation=str(mutation)):
                hacked=deepcopy(original_docket)
                mutation(hacked)
                with self.assertRaises(RehearsalRefused):
                    self.run_script(docket=hacked)

    def test_mutated_original_source_title_or_brief_article_digest_refused(self):
        board=deepcopy(self.values[2])
        board["slots"][1]["research_lead"]["unverified_title"]="Forged origin news"
        with self.assertRaises(RehearsalRefused):
            self.run_script(board=board)
        briefs=deepcopy(self.values[5])
        briefs["episodes"][0]["source_observation_sha256"]="e"*64
        with self.assertRaises(RehearsalRefused):
            self.run_script(briefs=briefs)

    def test_fake_quote_or_licensed_copy_in_excerpt_docket_refused(self):
        passages=deepcopy(self.values[6])
        passage=passages["sources"][0]["passages"][0]
        passage["not_licensed_for_narration_or_public_reuse"]=False
        with self.assertRaises(RehearsalRefused):
            self.run_script(passages=passages)

    def test_each_family_has_three_unique_original_demo_storylines(self):
        texts=[]
        for family,theme in THEMES.items():
            a=_paragraphs("short_am",theme)
            b=_paragraphs("long",theme)
            c=_paragraphs("short_pm",theme)
            self.assertEqual([len(a),len(b),len(c)],[4,9,4])
            for p in a+b+c:
                self.assertGreaterEqual(len(p),80)
                self.assertNotIn("https://",p)
            self.assertNotEqual(" ".join(a)," ".join(c))
            self.assertNotEqual(" ".join(a)," ".join(b))
            texts.append(" ".join(a+b+c))
        self.assertEqual(len(set(texts)),len(THEMES))

    def test_no_article_and_no_scout_still_rehearses_original_generic_example(self):
        original,scout,evidence=inputs()
        scout=deepcopy(scout)
        scout["leads"]=[]
        evidence=deepcopy(evidence)
        evidence["sources"]=[]
        evidence.update({
            "source_probes_attempted":0,"sources_observed_total":0,
            "sources_fetched":0,"feed_entries_observed_only":0,
            "sources_failed":0,"direct_article_fetch_failure_counts":{},
            "source_articles_with_bounded_publisher_redirect":0,
            "distinct_publishers_fetched":0,"failures":[],
        })
        from autopilot.daily_cloud_plan import build_plan
        from autopilot.test_daily_editorial_board import CLOCK
        original=build_plan("2026-11-07",scout_report=scout,
                            generated_at_utc=CLOCK)
        board=build_editorial_board(original,scout,evidence)
        aligned=align_plan_to_editorial_board(original,board,scout,evidence)
        briefs=build_episode_locked_research(original,aligned,board,scout,evidence)
        passages={
            "status":PASSAGE_STATUS,
            "source_observation_generated_at_utc":evidence["generated_at_utc"],
            "sources":[],"not_a_fact_check":True,
            "not_a_rights_clearance":True,"not_for_public_artifacts":True,
        }
        docket=build_claim_review_docket(
            original,aligned,board,scout,evidence,briefs,passages)
        result=build_nonfactual_rehearsals(
            original,aligned,board,scout,evidence,briefs,passages,docket)
        self.assertEqual(result["original_nonfactual_voiceover_rehearsals_written"],3)
        self.assertTrue(all(x["unverified_source_id"] is None
                            for x in result["three_episodes"]))
        self.assertTrue(all(x["claim_review_passages_not_quoted"]==0
                            for x in result["three_episodes"]))

    def test_all_scene_durations_contiguous_and_not_negative_for_each_family(self):
        for theme in THEMES.values():
            for slot in ("short_am","short_pm","long"):
                paragraphs=_paragraphs(slot,theme)
                frames=_frames_for(paragraphs,1740 if slot!="long" else 7200)
                self.assertEqual(len(frames),len(paragraphs))
                self.assertEqual(sum(frames),1740 if slot!="long" else 7200)
                self.assertTrue(all(x>=180 for x in frames))

    def test_no_network_voice_or_paid_model_calls_to_prepare_script(self):
        with patch("urllib.request.urlopen",
                   side_effect=AssertionError("Unexpected network call")):
            data=self.run_script()
        self.assertEqual(data["provider_model_calls"],0)
        self.assertEqual(data["actual_voice_files_created"],0)
        self.assertEqual(data["actual_video_files_created"],0)

    def test_cli_ephemeral_only_no_publish_text_in_stdout_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)/"out"
            folder.mkdir()
            names=("original-plan","aligned-plan","board","scout","evidence",
                   "briefs","passages","docket")
            args=[sys.executable,"-B","-m",
                  "autopilot.nonfactual_narration_rehearsal"]
            for key,data in zip(names,self.values):
                file=folder/(key+".json")
                file.write_text(json.dumps(data),encoding="utf8")
                args+=["--"+key,str(file)]
            target=folder/"flowminute-ephemeral-rehearsals.json"
            args+=["--output",str(target)]
            run=subprocess.run(args,capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            log=json.loads(run.stdout)
            self.assertEqual(log["nonfactual_original_voiceover_rehearsals"],3)
            self.assertEqual(log["individual_scenes"],17)
            self.assertEqual(log["paid_model_calls"],0)
            self.assertNotIn("fictional",run.stdout.lower())
            for title in self.values[5]["episodes"]:
                if title["unverified_topic_title"]:
                    self.assertNotIn(title["unverified_topic_title"],run.stdout)
            saved=json.loads(target.read_text("utf8"))
            self.assertEqual(len(saved["three_episodes"]),3)
            self.assertEqual(saved["factual_news_scripts_completed"],0)
            again=subprocess.run(args,capture_output=True,text=True,timeout=20)
            self.assertNotEqual(again.returncode,0)


if __name__=="__main__":
    unittest.main()
