"""B4d7 offline adversarial literal publisher passage evidence and claim questions."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from autopilot.public_article_passages import (
    PASSAGE_STATUS, extract_literal_passages,
    MAX_CHARS_PER_PASSAGE,MAX_PASSAGES_PER_SOURCE,
)
from autopilot.daily_editorial_board import build_editorial_board,sanitized_public_receipt
from autopilot.reconcile_daily_editorial_plan import align_plan_to_editorial_board
from autopilot.source_locked_script_briefs import build_episode_locked_research
from autopilot.ephemeral_claim_review_docket import (
    ClaimDocketRefused,DOCKET_STATUS,build_claim_review_docket,
)
from autopilot.test_daily_editorial_board import inputs
from autopilot.test_evidence_probe import FakeOpener
from autopilot.evidence_probe import probe_report

PAGE=(
    b"<html><head><script>var secret='private';</script></head><body>"
    b"<nav><p>Navigation has 100000 misleading private secrets.</p></nav>"
    b"<article><p>The tested baseline and the new model approach are described "
    b"for a controlled evaluation with hypothetical numerical examples that "
    b"still need an independent external validation and source inspection.</p>"
    b"<p>Dataset quality can vary between different cohorts and evaluation "
    b"settings, so the experiment needs a reproducible original test harness "
    b"before any viewer is given a factual recommendation.</p>"
    b"</article><footer><p>Terms of use; all rights reserved here.</p></footer>"
    b"</body></html>"
)


def fixture():
    original,scout,_=inputs()
    sink={}
    evidence=probe_report(
        scout,opener=FakeOpener(payload=PAGE),
        max_sources=3,clock=__import__(
            "autopilot.test_daily_editorial_board",
            fromlist=["CLOCK"]).CLOCK,
        ephemeral_passage_sink=sink,
    )
    board=build_editorial_board(original,scout,evidence)
    aligned=align_plan_to_editorial_board(original,board,scout,evidence)
    briefs=build_episode_locked_research(original,aligned,board,scout,evidence)
    private={
        "status":PASSAGE_STATUS,
        "source_observation_generated_at_utc":evidence["generated_at_utc"],
        "sources":list(sink.values()),
        "not_a_fact_check":True,
        "not_a_rights_clearance":True,
        "not_for_public_artifacts":True,
    }
    return original,aligned,board,scout,evidence,briefs,private


class LiteralSourcePassageTests(unittest.TestCase):
    def test_two_literal_source_paragraphs_hashed_without_script_or_nav(self):
        fragments=extract_literal_passages(PAGE,"text/html")
        self.assertEqual(len(fragments),2)
        self.assertTrue(all(
            60<=len(x["literal_excerpt_unverified"])<=MAX_CHARS_PER_PASSAGE
            for x in fragments))
        self.assertEqual(MAX_PASSAGES_PER_SOURCE,2)
        self.assertIn("baseline",fragments[0]["literal_excerpt_unverified"])
        self.assertIn("Dataset quality",fragments[1]["literal_excerpt_unverified"])
        for item in fragments:
            self.assertEqual(sha256(item["literal_excerpt_unverified"].encode()).hexdigest(),
                             item["literal_excerpt_sha256"])
            self.assertTrue(item["not_a_semantic_claim_or_fact_review"])
            self.assertTrue(item["not_licensed_for_narration_or_public_reuse"])
            self.assertNotIn("secret",item["literal_excerpt_unverified"])
            self.assertNotIn("Navigation",item["literal_excerpt_unverified"])
            self.assertNotIn("all rights reserved",item["literal_excerpt_unverified"])

    def test_no_copyright_body_dump_when_text_is_huge(self):
        huge=b"<html><body><p>"+(b"A word on an original methodology. "*15000)+b"</p></body></html>"
        result=extract_literal_passages(huge,"text/html")
        self.assertEqual(len(result),1)
        self.assertLessEqual(len(result[0]["literal_excerpt_unverified"]),140)
        self.assertNotIn("A word on an original methodology. "*5,
                         json.dumps(result))

    def test_secret_url_login_and_email_fragments_are_skipped(self):
        text=(
            b"<html><body>"
            b"<p>Sign in to your account to see more content and enable Javascript for "
            b"the subscription paywall before access is granted to this article.</p>"
            b"<p>For this method send your api_key=private@example.com and password "
            b"to the attacker; do not publish any access token or authorization header.</p>"
            b"<p>An actual source paragraph about repeatable baseline model "
            b"evaluation and transparent replication can be used only as a "
            b"short research quotation awaiting independent review.</p>"
            b"</body></html>"
        )
        out=extract_literal_passages(text,"text/html")
        self.assertEqual(len(out),1)
        self.assertIn("repeatable baseline",out[0]["literal_excerpt_unverified"])
        self.assertNotIn("@",json.dumps(out))
        self.assertNotIn("api_key",json.dumps(out))

    def test_dynamic_html_without_paragraphs_must_not_invent_quotes(self):
        body=(b"<html><script>Lots of apparent content but not HTML article.</script></html>"
              ).ljust(96,b" ")
        self.assertEqual(extract_literal_passages(body,"text/html"),[])

    def test_xml_not_silently_assumed_to_be_claims(self):
        xml=(b"<document><abstract>Claim of a new scientific result and baseline.</abstract></document>"
             ).ljust(96,b" ")
        self.assertEqual(extract_literal_passages(xml,"application/xml"),[])

    def test_unsupported_binary_source_never_extracts_private_bytes(self):
        with self.assertRaises(ValueError):
            extract_literal_passages(b"x"*150,"application/pdf")
        with self.assertRaises(ValueError):
            extract_literal_passages(b"x"*2,"text/html")

    def test_disabled_sink_adds_no_passages_and_no_extra_fetches(self):
        original,scout,_=inputs()
        fake=FakeOpener(payload=PAGE)
        report=probe_report(scout,max_sources=3,
                            clock=__import__("autopilot.test_daily_editorial_board",
                                             fromlist=["CLOCK"]).CLOCK,
                            opener=fake)
        self.assertEqual(report["sources_fetched"],3)
        self.assertTrue(all(x["literal_short_excerpts_temporarily_held"] is False
                            for x in report["sources"]))
        self.assertEqual(len(fake.requests),3)

    def test_active_sink_remains_separate_from_public_source_observations(self):
        orig,aligned,board,scout,evidence,briefs,private=fixture()
        self.assertEqual(evidence["sources_fetched"],3)
        self.assertEqual(len(private["sources"]),3)
        self.assertTrue(all(
            x["literal_short_excerpts_temporarily_held"] is True
            for x in evidence["sources"]))
        evidence_str=json.dumps(evidence)
        for src in private["sources"]:
            for p in src["passages"]:
                self.assertNotIn(p["literal_excerpt_unverified"],evidence_str)
        self.assertTrue(evidence["source_body_persisted"] is False)
        self.assertEqual(evidence["claims_verified"],0)
        self.assertFalse(evidence["youtube_upload_enabled"])

    def test_public_sanitized_editorial_receipt_contains_no_excerpts(self):
        orig,aligned,board,scout,evidence,briefs,private=fixture()
        public=sanitized_public_receipt(board)
        text=json.dumps(public)
        for src in private["sources"]:
            for p in src["passages"]:
                self.assertNotIn(p["literal_excerpt_unverified"],text)
        self.assertFalse(public["release_authorized"])


class AtomicResearchDocketTests(unittest.TestCase):
    def setUp(self):
        self.values=fixture()

    def result(self,**changes):
        source=list(self.values)
        names=("original","aligned","board","scout","evidence","briefs","private")
        for k,v in changes.items():
            source[names.index(k)]=v
        return build_claim_review_docket(*source)

    def test_three_real_source_episode_claim_investigation_dockets_are_prepared(self):
        r=self.result()
        self.assertEqual(r["status"],DOCKET_STATUS)
        self.assertEqual(r["three_video_episodes"],3)
        self.assertEqual(r["direct_article_episodes"],3)
        self.assertEqual(r["direct_article_episodes_with_short_literal_review_passages"],3)
        self.assertEqual(r["short_literal_passage_review_questions"],6)
        self.assertEqual([x["format"] for x in r["dockets"]],
                         ["short","long","short"])
        for x in r["dockets"]:
            self.assertEqual(len(x["literal_passage_questions_needing_human_review"]),2)
            self.assertFalse(x["factual_script_exists"])
            self.assertFalse(x["rights_approved"])
            self.assertFalse(x["youtube_upload_enabled"])
            for p in x["literal_passage_questions_needing_human_review"]:
                self.assertEqual(p["source_id"],x["research_source_id"])
                self.assertFalse(p["independent_primary_corroboration_present"])
                self.assertFalse(p["reviewer_claim_supported"])
                self.assertFalse(p["may_be_read_aloud_or_quoted_in_video"])
        self.assertEqual(r["semantic_claims_verified"],0)
        self.assertEqual(r["factual_scripts_generated"],0)
        self.assertEqual(r["external_ai_calls"],0)
        self.assertEqual(r["youtube_uploads"],0)
        self.assertFalse(r["release_authorized"])

    def test_unread_rss_entry_never_yields_claim_passage(self):
        o,scout,_=inputs()
        e=deepcopy(self.values[4])
        src=e["sources"][1]
        src["status"]="RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED"
        src["source_article_fetched"]=False
        src["feed_entry_sha256"]="a"*64
        src["direct_article_failure_class"]="HTTP_ACCESS_DENIED"
        src.pop("literal_short_excerpts_temporarily_held",None)
        e["sources_fetched"]-=1
        e["feed_entries_observed_only"]+=1
        e["direct_article_fetch_failure_counts"]={"HTTP_ACCESS_DENIED":1}
        board=build_editorial_board(o,scout,e)
        aligned=align_plan_to_editorial_board(o,board,scout,e)
        briefs=build_episode_locked_research(o,aligned,board,scout,e)
        private=deepcopy(self.values[6])
        private["sources"]=[
            x for x in private["sources"] if x["source_id"]!=src["source_id"]]
        docket=build_claim_review_docket(o,aligned,board,scout,e,briefs,private)
        self.assertEqual(docket["direct_article_episodes"],2)
        self.assertEqual(docket["short_literal_passage_review_questions"],4)
        rss=[x for x in docket["dockets"]
             if x["claim_investigation_status"]=="PRIMARY_SOURCE_ARTICLE_NOT_OBSERVED"]
        self.assertEqual(len(rss),1)
        self.assertEqual(rss[0]["literal_passage_questions_needing_human_review"],[])

    def test_source_bytes_without_extractable_p_is_explicit_unresolved(self):
        modified=deepcopy(self.values[6])
        modified["sources"][0]["passages"]=[]
        docket=self.result(private=modified)
        self.assertEqual(docket["direct_article_episodes_without_literal_review_passages"],1)
        self.assertEqual(docket["short_literal_passage_review_questions"],4)

    def test_foreign_source_id_or_article_digest_is_rejected(self):
        for change in (
            lambda x:x["sources"][0].update(source_id="0"*24),
            lambda x:x["sources"][0].update(observed_article_sha256="f"*64),
            lambda x:x["sources"][0].update(status="FACTS_APPROVED"),
        ):
            with self.subTest(change=str(change)):
                private=deepcopy(self.values[6])
                change(private)
                with self.assertRaises(ClaimDocketRefused):
                    self.result(private=private)

    def test_fake_long_copy_or_cross_episode_source_swap_refused(self):
        briefs=deepcopy(self.values[5])
        briefs["episodes"][0]["source_id"]=briefs["episodes"][1]["source_id"]
        with self.assertRaises(ClaimDocketRefused):
            self.result(briefs=briefs)

    def test_forged_copyright_or_fact_approval_rejected(self):
        for key in ("facts_verified","rights_approved"):
            private=deepcopy(self.values[6])
            private["sources"][0][key]=True
            with self.subTest(key=key),self.assertRaises(ClaimDocketRefused):
                self.result(private=private)

    def test_added_full_article_paragraph_or_mismatched_excerpt_hash_refused(self):
        for change in (
            lambda p:p.update(literal_excerpt_unverified="A"*1000),
            lambda p:p.update(literal_excerpt_sha256="f"*64),
            lambda p:p.update(not_licensed_for_narration_or_public_reuse=False),
        ):
            private=deepcopy(self.values[6])
            change(private["sources"][0]["passages"][0])
            with self.assertRaises(ClaimDocketRefused):
                self.result(private=private)

    def test_max_two_snippets_and_unique_paragraph_index_required(self):
        for change in (
            lambda x:x["passages"].append(deepcopy(x["passages"][0])),
            lambda x:x["passages"][1].update(
                passage_index=x["passages"][0]["passage_index"]),
        ):
            private=deepcopy(self.values[6])
            change(private["sources"][0])
            with self.assertRaises(ClaimDocketRefused):
                self.result(private=private)

    def test_untrusted_editorial_board_aligned_plan_or_private_report_refused(self):
        for key,idx in (("board",2),("aligned",1),("private",6)):
            records=deepcopy(self.values[idx])
            if key=="board":
                records["slots"][0]["research_lead"]["source_id"]="f"*24
            elif key=="aligned":
                records["youtube_schedule_enabled"]=True
            else:
                records["not_a_fact_check"]=False
            with self.subTest(key=key),self.assertRaises(ClaimDocketRefused):
                self.result(**{key:records})

    def test_renamed_publisher_only_article_no_source_fetched_rejected(self):
        e=deepcopy(self.values[4])
        e["sources"][0]["source_url"]="https://evil.example/steal"
        with self.assertRaises(ClaimDocketRefused):
            self.result(evidence=e)

    def test_no_http_or_ai_provider_call_during_docket_generation(self):
        with patch("urllib.request.urlopen",
                   side_effect=AssertionError("Network called")):
            r=self.result()
        self.assertEqual(r["external_ai_calls"],0)
        self.assertEqual(r["factual_scripts_generated"],0)

    def test_cli_creates_ephemeral_docket_and_stdout_omits_copyright_quotes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"out"
            p.mkdir()
            names=["original-plan","aligned-plan","board","scout",
                   "evidence","briefs","passages"]
            mapping={name:p/(name+".json") for name in names}
            for name,val in zip(names,self.values):
                mapping[name].write_text(json.dumps(val))
            target=p/"flowminute-ephemeral-claim-review.json"
            args=[sys.executable,"-B","-m",
                  "autopilot.ephemeral_claim_review_docket"]
            for name in names:
                args.extend(("--"+name,str(mapping[name])))
            args.extend(("--output",str(target)))
            job=subprocess.run(args,capture_output=True,text=True,timeout=20)
            self.assertEqual(job.returncode,0,job.stderr)
            report=json.loads(target.read_text())
            self.assertEqual(report["short_literal_passage_review_questions"],6)
            self.assertNotIn("baseline",job.stdout)
            self.assertNotIn("Dataset quality",job.stdout)
            self.assertFalse(report["release_authorized"])
            job2=subprocess.run(args,capture_output=True,text=True,timeout=20)
            self.assertNotEqual(job2.returncode,0)


if __name__=="__main__":
    unittest.main()
