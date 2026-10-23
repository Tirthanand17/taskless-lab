"""Focused negative and positive tests; no subscribers, views or releases are fabricated."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from autopilot.engagement_storyboard import validate_engagement_brief, EngagementBriefError

ROOT=Path(__file__).resolve().parents[1]
STORY=ROOT/"content"/"storyboards"/"oct24_multicharacter_3d_plans.json"
BRIEFS=ROOT/"content"/"storyboards"/"oct24_engagement_briefs.json"

def pairs():
    stories=json.loads(STORY.read_text(encoding="utf-8"))["episodes"]
    briefs=json.loads(BRIEFS.read_text(encoding="utf-8"))["episodes"]
    assert len(stories)==len(briefs)==3
    return [(deepcopy(b),deepcopy(s)) for b,s in zip(briefs,stories)]


class EngagementBriefTests(unittest.TestCase):
    def test_all_3_check_without_claiming_publication(self):
        for brief,story in pairs():
            output=validate_engagement_brief(brief,story)
            self.assertTrue(output["creative_coverage_passed"])
            self.assertFalse(output["publishing_authorized"])
            self.assertIsNone(output["observed_audience_improvement"])

    def test_wrong_episode_rejected(self):
        b,s=pairs()[0]
        b["episode_id"]="unrelated"
        with self.assertRaisesRegex(EngagementBriefError,"mismatch"):validate_engagement_brief(b,s)

    def test_logo_intro_does_not_pass(self):
        b,s=pairs()[0]
        b["first_seconds"]["physical_action"]="Logo swoops into studio with animation"
        with self.assertRaisesRegex(EngagementBriefError,"logo"):validate_engagement_brief(b,s)

    def test_hook_must_start_immediately(self):
        b,s=pairs()[0]
        b["first_seconds"]["start_second"]=5
        with self.assertRaisesRegex(EngagementBriefError,"immediately"):validate_engagement_brief(b,s)

    def test_decorative_information_overload_blocked(self):
        b,s=pairs()[0]
        b["instructional_moments"][0]["highlight_count"]=9
        with self.assertRaisesRegex(EngagementBriefError,"noisy HUD"):validate_engagement_brief(b,s)

    def test_disguised_fake_metric_not_allowed(self):
        b,s=pairs()[0]
        b["measurements"]["observed_values"]={"engaged_views":10000}
        with self.assertRaisesRegex(EngagementBriefError,"fabricate"):validate_engagement_brief(b,s)

    def test_unproven_growth_claim_blocked(self):
        b,s=pairs()[0]
        b["measurements"]["claim_of_lift"]=200
        with self.assertRaisesRegex(EngagementBriefError,"uplift"):validate_engagement_brief(b,s)

    def test_invalid_short_ab_testing(self):
        b,s=pairs()[0]
        b["packaging"]["youtube_native_ab_test"]="candidate_when_eligible"
        with self.assertRaisesRegex(EngagementBriefError,"long-only"):validate_engagement_brief(b,s)

    def test_short_does_not_use_long_end_screen(self):
        b,s=pairs()[0]
        b["cross_video_plan"]["end_screen"]="candidate_last_5_to_20_seconds"
        with self.assertRaisesRegex(EngagementBriefError,"related-video"):validate_engagement_brief(b,s)

    def test_invented_destination_blocked(self):
        b,s=pairs()[0]
        b["cross_video_plan"]["verified_destination_video_id"]="guessedId123"
        with self.assertRaisesRegex(EngagementBriefError,"invent"):validate_engagement_brief(b,s)

    def test_clickbait_comments_blocked(self):
        b,s=pairs()[0]
        b["audience_question"]="Subscribe to win free cash immediately"
        with self.assertRaisesRegex(EngagementBriefError,"genuine"):validate_engagement_brief(b,s)

    def test_self_attested_research_blocked(self):
        b,s=pairs()[0]
        b["packaging"]["claims_checked_for_clickbait"]=True
        with self.assertRaisesRegex(EngagementBriefError,"cannot self-attest"):validate_engagement_brief(b,s)

if __name__=="__main__":unittest.main()
