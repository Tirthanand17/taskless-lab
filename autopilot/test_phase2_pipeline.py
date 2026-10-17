"""Phase 2 real typed adapter tests. Examples are SYNTHETIC, not real fact audits."""
from dataclasses import replace
from datetime import datetime, timezone, timedelta
import unittest

from autopilot.agent_org import State, WorkflowError
from autopilot.phase2_pipeline import (
    CitationRecord, SupportedClaim, ResearchPackage, FactReview,
    CreativeScript, HookVariants, LocalizedDraft, LanguageReview, Phase2Coordinator, digest
)

NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
EP = "demo_research_01"
SCOPE = "This sample shows an offline CSV workflow with no real account access."


def fixtures():
    now = NOW.isoformat()
    research = ResearchPackage(
        episode_id=EP,
        topic="Safely read a CSV file and inspect the dataset",
        viewer_problem="New Python learners need a simple offline CSV reading example",
        demonstration="Create a synthetic CSV dataset, then inspect parsed columns on screen",
        sources=(
            CitationRecord("src_python_docs", "https://docs.python.org/3/library/csv.html",
                           "official", now, "named_source_reviewer"),
            CitationRecord("src_independent_csv", "https://realpython.com/python-csv/",
                           "independent", now, "named_source_reviewer")
        ),
        claims=(SupportedClaim("c_csv_reader",
                 "The example uses the Python CSV reader on a synthetic file",
                 ("src_python_docs", "src_independent_csv")),)
    )
    review = FactReview(EP, digest(research), "quality.fact_reviewer",
                        ("c_csv_reader",), "ATTESTED_FOR_DRAFT",
                        "Mock reviewer record for test input; not genuine external fact checking")
    script = CreativeScript(
        EP, digest(research), digest(review),
        "Read a CSV example with Python",
        "Here is an offline CSV workflow with a clear practical example",
        ("Create a small synthetic CSV file containing sample rows",
         "Run the standard CSV parser and display the extracted columns"),
        "You can now understand the file contents without sending data online",
        ("c_csv_reader",), research.demonstration
    )
    hooks = HookVariants(
        EP, digest(review),
        ("See the result of this simple Python CSV demo first",
         "Open a synthetic CSV file and inspect its contents in Python"),
        ("c_csv_reader",)
    )
    english = LocalizedDraft(
        EP, digest(script), "en",
        "We will open a sample CSV file, run the Python reader, and inspect its contents.",
        ("Create a sample CSV with test rows",
         "Use Python to inspect parsed columns"),
        "Use CSV consistently; pronounce the letters C S V.",
        "language.english_editor"
    )
    hindi = LocalizedDraft(
        EP, digest(script), "hi",
        "हम एक उदाहरण सीएसवी फ़ाइल बनाएँगे और पाइथन की सहायता से उसके कॉलम पढ़कर परिणाम देखेंगे।",
        ("पहले एक उदाहरण सीएसवी फ़ाइल बनाएँ",
         "पाइथन की सहायता से कॉलम पढ़कर परिणाम देखें"),
        "CSV और Python के शब्दों के उच्चारण की जाँच आगे अलग से ज़रूरी है।",
        "language.hindi_editor"
    )
    language_review = LanguageReview(EP, digest(english), digest(hindi),
                                     'language.language_reviewer', 'ATTESTED_FOR_DRAFT',
                                     'Mock independent language-review attestation for tests only')
    return research, review, script, hooks, english, hindi, language_review


def submit_all(c):
    objects = fixtures()
    for stage, obj, actor in zip(
        ("research", "fact_review", "script", "hooks", "english", "hindi", "language_review"),
        objects,
        ("research.launch_researcher", "quality.fact_reviewer",
         "creative.shorts_writer", "creative.hook_writer",
         "language.english_editor", "language.hindi_editor", "language.language_reviewer")
    ):
        c.submit(stage, obj, actor=actor)


class Phase2Tests(unittest.TestCase):
    def setUp(self):
        self.c = Phase2Coordinator(EP, kind="short", language="hi", now=NOW)
        self.research, self.review, self.script, self.hooks, self.english, self.hindi, self.language_review = fixtures()

    def test_full_research_to_bilingual_handoff(self):
        submit_all(self.c)
        result = self.c.progress()
        self.assertEqual(len(result["completed_stages"]), 7)
        self.assertIn(EP + ":storyboard", result["next_tasks"])
        self.assertIn(EP + ":voice_plan", result["next_tasks"])
        self.assertFalse(result["publishing_authorized"])
        self.assertFalse(result["language_independently_reviewed"])
        self.assertTrue(result["language_review_recorded_for_staging"])
        self.assertFalse(result["research_factually_verified_by_external_system"])
        for stage in ("research", "fact_review", "script", "hooks", "english", "hindi", "language_review"):
            self.assertEqual(self.c.workflow.runs[EP + ":" + stage].status, State.COMPLETE)
            self.assertEqual(self.c.workflow.runs[EP + ":" + stage].artifact.review_state,
                             "UNVERIFIED_STAGING_ARTIFACT")

    def test_fact_check_cannot_come_before_research(self):
        with self.assertRaises(WorkflowError):
            self.c.submit("fact_review", self.review, actor="quality.fact_reviewer")
        self.assertEqual(self.c.progress()["completed_stages"], ())

    def test_wrong_actor_and_episode_cannot_claim(self):
        with self.assertRaises(WorkflowError):
            self.c.submit("research", self.research, actor="creative.shorts_writer")
        with self.assertRaises(WorkflowError):
            self.c.submit("research", replace(self.research, episode_id="other_ep"), actor="research.launch_researcher")
        self.assertEqual(self.c.progress()["completed_stages"], ())

    def test_feed_lead_never_submitted_as_verified_research(self):
        with self.assertRaises(WorkflowError):
            self.c.submit("research", replace(self.research, from_feed_only=True), actor="research.launch_researcher")

    def test_official_and_independent_sources_required(self):
        with self.assertRaises(WorkflowError):
            self.c.submit("research", replace(self.research, sources=self.research.sources[:1]),
                          actor="research.launch_researcher")

    def test_reject_private_network_and_insecure_urls(self):
        for url in ("http://docs.python.org/3/library/csv.html",
                    "https://127.0.0.1/internal", "https://localhost/private",
                    "https://user:pass@example.com/article", "https://intranet.internal/article",
                    "https://192.168.1.3/private"):
            with self.subTest(url=url):
                r = replace(self.research, sources=(replace(self.research.sources[1],url=url),self.research.sources[0]))
                with self.assertRaises(WorkflowError):
                    self.c.submit("research", r, actor="research.launch_researcher")

    def test_stale_and_future_source_check_rejected(self):
        for checked_at_utc in ((NOW - timedelta(days=9)).isoformat(),
                               (NOW + timedelta(seconds=1)).isoformat()):
            research = replace(self.research, sources=(replace(self.research.sources[0],checked_at_utc=checked_at_utc),
                                                       self.research.sources[1]))
            with self.assertRaises(WorkflowError):
                self.c.submit("research", research, actor="research.launch_researcher")

    def test_unsupported_claim_source_blocks(self):
        wrong = replace(self.research.claims[0],source_ids=("src_missing_thing",))
        with self.assertRaises(WorkflowError):
            self.c.submit("research",replace(self.research,claims=(wrong,)),actor="research.launch_researcher")

    def test_each_claim_needs_official_backing(self):
        wrong = replace(self.research.claims[0],source_ids=("src_independent_csv",))
        with self.assertRaises(WorkflowError):
            self.c.submit("research",replace(self.research,claims=(wrong,)),actor="research.launch_researcher")

    def test_research_hash_is_bound_to_fact_review(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        r=replace(self.review,research_digest="0"*64)
        with self.assertRaises(WorkflowError):
            self.c.submit("fact_review",r,actor="quality.fact_reviewer")
        self.assertEqual(self.c.workflow.runs[EP+":fact_review"].status,State.READY)

    def test_review_role_is_independent(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        with self.assertRaises(WorkflowError):
            self.c.submit("fact_review",
                replace(self.review,reviewer_role="research.launch_researcher"),
                actor="quality.fact_reviewer")

    def test_review_not_attested_cannot_progress(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        with self.assertRaises(WorkflowError):
            self.c.submit("fact_review",replace(self.review,verdict="REJECT"),
                          actor="quality.fact_reviewer")
        self.assertEqual(self.c.workflow.runs[EP+":script"].status,State.BLOCKED)

    def test_claim_subset_review_rejected(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        with self.assertRaises(WorkflowError):
            self.c.submit("fact_review",replace(self.review,reviewed_claim_ids=()),
                          actor="quality.fact_reviewer")

    def test_script_from_changed_sources_rejected(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        with self.assertRaises(WorkflowError):
            self.c.submit("script",replace(self.script,research_digest="f"*64),
                          actor="creative.shorts_writer")

    def test_creative_cannot_introduce_unverified_claim(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        with self.assertRaises(WorkflowError):
            self.c.submit("script",replace(self.script,used_claim_ids=("c_missing",)),
                          actor="creative.shorts_writer")

    def test_original_demonstration_change_requires_review(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        with self.assertRaises(WorkflowError):
            self.c.submit("script",replace(self.script,original_demo="Different unapproved demonstration"),
                          actor="creative.shorts_writer")

    def test_honest_hooks_require_reviewed_claim(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        with self.assertRaises(WorkflowError):
            self.c.submit("hooks",replace(self.hooks,promised_claim_ids=("c_unapproved",)),
                          actor="creative.hook_writer")

    def test_cannot_forge_language_review_status(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        self.c.submit("script",self.script,actor="creative.shorts_writer")
        with self.assertRaises(WorkflowError):
            self.c.submit("english",replace(self.english,label="INDEPENDENTLY_APPROVED"),
                          actor="language.english_editor")

    def test_hindi_only_by_hindi_specialist(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        self.c.submit("script",self.script,actor="creative.shorts_writer")
        with self.assertRaises(WorkflowError):
            self.c.submit("hindi",replace(self.hindi,translator_role="language.english_editor"),
                          actor="language.hindi_editor")

    def test_no_english_claim_when_hindi_only_draft_supplied(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        self.c.submit("script",self.script,actor="creative.shorts_writer")
        self.c.submit("hindi",self.hindi,actor="language.hindi_editor")
        self.assertNotIn("english",self.c.progress()["completed_stages"])
        self.assertNotIn(EP+":voice_plan",self.c.workflow.ready())

    def test_stale_translation_hash_rejected(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        self.c.submit("script",self.script,actor="creative.shorts_writer")
        with self.assertRaises(WorkflowError):
            self.c.submit("hindi",replace(self.hindi,script_digest="f"*64),
                          actor="language.hindi_editor")

    def test_voice_plan_stays_blocked_until_language_review_recorded(self):
        for stage,obj,actor in (
            ("research",self.research,"research.launch_researcher"),
            ("fact_review",self.review,"quality.fact_reviewer"),
            ("script",self.script,"creative.shorts_writer"),
            ("english",self.english,"language.english_editor"),
            ("hindi",self.hindi,"language.hindi_editor")):
            self.c.submit(stage,obj,actor=actor)
        self.assertNotIn(EP+":voice_plan",self.c.workflow.ready())
        self.c.submit("language_review",self.language_review,actor="language.language_reviewer")
        self.assertIn(EP+":voice_plan",self.c.workflow.ready())
        self.assertFalse(self.c.progress()["language_independently_reviewed"])

    def test_language_review_wrong_role_rejected(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        self.c.submit("script",self.script,actor="creative.shorts_writer")
        self.c.submit("english",self.english,actor="language.english_editor")
        self.c.submit("hindi",self.hindi,actor="language.hindi_editor")
        bad=replace(self.language_review,reviewer_role="language.english_editor")
        with self.assertRaises(WorkflowError):
            self.c.submit("language_review",bad,actor="language.language_reviewer")

    def test_review_rejects_changed_hindi_draft_digest(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        self.c.submit("script",self.script,actor="creative.shorts_writer")
        self.c.submit("english",self.english,actor="language.english_editor")
        changed=replace(self.hindi,narrated_text=self.hindi.narrated_text+" और एक पंक्ति भी जोड़ते हैं।")
        self.c.submit("hindi",changed,actor="language.hindi_editor")
        with self.assertRaises(WorkflowError):
            self.c.submit("language_review",self.language_review,actor="language.language_reviewer")

    def test_language_review_rejects_explicit_failure(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        self.c.submit("fact_review",self.review,actor="quality.fact_reviewer")
        self.c.submit("script",self.script,actor="creative.shorts_writer")
        self.c.submit("english",self.english,actor="language.english_editor")
        self.c.submit("hindi",self.hindi,actor="language.hindi_editor")
        rejected=replace(self.language_review,verdict="REJECT")
        with self.assertRaises(WorkflowError):
            self.c.submit("language_review",rejected,actor="language.language_reviewer")
        self.assertEqual(self.c.workflow.runs[EP+":voice_plan"].status,State.BLOCKED)

    def test_duplicate_stage_submission_rejected(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        with self.assertRaises(WorkflowError):
            self.c.submit("research",self.research,actor="research.launch_researcher")

    def test_handoff_refs_are_sha256_not_source_urls(self):
        self.c.submit("research",self.research,actor="research.launch_researcher")
        handoff=self.c.workflow.runs[EP+":research"].artifact
        self.assertEqual(len(handoff.evidence_refs),2)
        self.assertTrue(all(x.startswith("sha256:") for x in handoff.evidence_refs))
        self.assertTrue(all("https" not in x for x in handoff.evidence_refs))


if __name__ == "__main__":
    unittest.main()
