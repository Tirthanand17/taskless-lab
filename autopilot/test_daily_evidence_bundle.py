"""B4d1 real cloud artifact-boundary checks without any network or credentials."""
from __future__ import annotations

from copy import deepcopy
import datetime as dt
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from autopilot.daily_cloud_plan import build_plan
from autopilot.daily_evidence_bundle import (
    DailyEvidenceRefused,STATUS,build_retained_draft_receipt,
    MAX_OUTPUT_BYTES,
)

CLOCK=dt.datetime(2026,11,4,9,30,tzinfo=dt.timezone.utc)
DAY="2026-11-05"
FAKE_PRIVATE="do-not-put-a-raw-secret-in-public-artifact-TESTONLY123"


def draft():
    report={
        "status":"leads_only_no_publish_authorization",
        "leads":[{
            "publisher":"OpenAI",
            "title":"An original educational headline deliberately with "+FAKE_PRIVATE,
            "url":"https://openai.com/news/abc?raw_token="+FAKE_PRIVATE,
            "status":"unverified_lead",
        }],
    }
    return build_plan(DAY,scout_report=report,generated_at_utc=CLOCK)


def observations(*,count=0):
    records=[{
        "source_id":"aa"*12,"publisher":"OpenAI",
        "title":"Original external headline with "+FAKE_PRIVATE,
        "source_url":"https://openai.com/news/abc?secret="+FAKE_PRIVATE,
        "status":"SOURCE_FETCHED_NOT_FACT_CHECKED",
        "http_status":200,
        "response_sha256":"a"*64,
        "facts_verified":False,
        "rights_verified":False,
        "source_text_or_image_stored":False,
        "youtube_release_authorized":False,
    }] if count else []
    return {
        "schema_version":1,
        "generated_at_utc":CLOCK.isoformat(),
        "status":"PUBLIC_SOURCE_METADATA_ONLY_NOT_FACT_VERIFIED",
        "source_probes_attempted":count,
        "sources_fetched":count,
        "feed_entries_observed_only":0,
        "sources_observed_total":count,
        "sources_failed":0,
        "distinct_publishers_fetched":count,
        "sources":records,
        "failures":[],
        "claims_verified":0,
        "semantic_corroboration_performed":False,
        "source_body_persisted":False,
        "scripts_generated":0,
        "audio_or_video_generated":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "production_credentials_used":False,
        "billed_provider_calls":0,
    }


class RealGitHubDraftEvidenceTests(unittest.TestCase):
    def test_real_draft_becomes_metadata_only_three_slot_receipt(self):
        orig=draft()
        obs=observations(count=1)
        r=build_retained_draft_receipt(orig,obs)
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(r["plan_day_ist"],DAY)
        self.assertEqual(len(r["slots"]),3)
        self.assertEqual([x["format"] for x in r["slots"]],["short","long","short"])
        self.assertEqual([x["release_local_ist"] for x in r["slots"]],
                         ["11:00","16:00","20:30"])
        self.assertEqual([x["planned_utc"] for x in r["slots"]],[
            "2026-11-05T05:30:00+00:00",
            "2026-11-05T10:30:00+00:00",
            "2026-11-05T15:00:00+00:00",
        ])
        self.assertEqual(r["source_observations"]["direct_pages_seen_not_fact_checked"],1)
        self.assertTrue(r["slots"][0]["research_lead_present"])
        self.assertFalse(r["slots"][1]["research_lead_present"])
        self.assertEqual(r["independently_verified_unattended_youtube_releases"],0)
        self.assertFalse(r["release_authorized"])
        self.assertFalse(r["real_fact_or_rights_review_performed"])
        self.assertTrue(r["sha256_is_content_integrity_only_not_owner_signature"])
        text=json.dumps(r,sort_keys=True)
        self.assertLess(len(text),MAX_OUTPUT_BYTES)
        self.assertNotIn(FAKE_PRIVATE,text)
        self.assertNotIn("https://",text)
        self.assertNotIn("Original external headline",text)
        self.assertNotIn("original educational headline",text.lower())
        self.assertEqual(len(r["receipt_sha256"]),64)
        self.assertEqual(build_retained_draft_receipt(orig,obs),r)

    def test_new_official_archive_lead_can_be_retained_without_paper_text(self):
        from autopilot.daily_evidence_bundle import ALLOWED_PUBLISHERS
        from autopilot.daily_cloud_plan import APPROVED_RESEARCH_ORIGINS
        self.assertEqual(ALLOWED_PUBLISHERS,
                         frozenset(APPROVED_RESEARCH_ORIGINS))
        fake={
            "status":"leads_only_no_publish_authorization",
            "leads":[{
                "publisher":"arXiv AI",
                "title":"A research paper about models and automation",
                "url":"https://arxiv.org/abs/2611.12345",
                "status":"unverified_lead",
            }],
        }
        p=build_plan(DAY,scout_report=fake,generated_at_utc=CLOCK)
        result=build_retained_draft_receipt(p,observations())
        self.assertEqual(result["slots"][0]["lead_publisher_public_only"],
                         "arXiv AI")
        self.assertTrue(result["slots"][0]["research_lead_present"])
        self.assertFalse(result["real_fact_or_rights_review_performed"])
        self.assertFalse(result["youtube_publishing_enabled"])
        text=json.dumps(result)
        self.assertNotIn("https://arxiv.org/abs",text)
        self.assertNotIn("A research paper",text)

    def test_forged_arxiv_pdf_or_nonpublisher_link_refused_by_retention(self):
        fake={
            "status":"leads_only_no_publish_authorization",
            "leads":[{
                "publisher":"arXiv AI",
                "title":"A research paper about models and automation",
                "url":"https://arxiv.org/abs/2611.12345",
                "status":"unverified_lead",
            }],
        }
        p=build_plan(DAY,scout_report=fake,generated_at_utc=CLOCK)
        for url in ("https://arxiv.org/pdf/2611.12345",
                    "https://rss.arxiv.org/rss/cs.AI",
                    "https://evil.example/abs/2611.12345"):
            with self.subTest(url=url):
                x=deepcopy(p)
                x["slots"][0]["research_lead"]["url"]=url
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(x,observations())

    def test_empty_public_scout_and_no_eligible_web_still_generate_safe_receipt(self):
        p=build_plan(DAY,scout_report={
            "status":"leads_only_no_publish_authorization","leads":[]},
            generated_at_utc=CLOCK)
        r=build_retained_draft_receipt(p,observations())
        self.assertEqual(sum(s["research_lead_present"] for s in r["slots"]),0)
        self.assertEqual(r["source_observations"]["attempted"],0)
        self.assertEqual(len(r["slots"]),3)

    def test_never_promote_plan_release_or_media_progress_flags(self):
        for key in (
            "approved_provider_credentials_connected",
            "cloud_media_renderer_connected",
            "production_release_ledger_connected",
            "cloud_publisher_connected",
            "youtube_upload_enabled","youtube_schedule_enabled",
            "any_content_verified","new_billable_resources_enabled",
        ):
            with self.subTest(key=key):
                p=draft()
                p[key]=True
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(p,observations())
        p=draft()
        p["maximum_incremental_spend_inr"]=1
        with self.assertRaises(DailyEvidenceRefused):
            build_retained_draft_receipt(p,observations())

    def test_any_episode_approval_media_upload_or_hidden_handoff_denied(self):
        keys=("real_script_exists","real_narration_exists","real_media_exists",
              "rights_approved","real_media_qa_passed","youtube_uploaded",
              "youtube_scheduled","release_authorized")
        for key in keys:
            with self.subTest(key=key):
                p=draft()
                p["slots"][1][key]=True
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(p,observations())
        p=draft()
        p["slots"][2]["agent_handoffs_completed"]=1
        with self.assertRaises(DailyEvidenceRefused):
            build_retained_draft_receipt(p,observations())

    def test_wrong_next_day_slot_timestamp_format_and_duplicate_episode_refused(self):
        cases=(
            ("day",lambda p:p.update(plan_date_ist="2026-11-06")),
            ("too old",lambda p:p.update(plan_date_ist="2026-11-04")),
            ("time",lambda p:p["slots"][0].update(local_ist="10:00")),
            ("utc",lambda p:p["slots"][1].update(release_utc="2026-11-05T10:00:00+00:00")),
            ("format",lambda p:p["slots"][1].update(format="short")),
            ("id",lambda p:p["slots"][0].update(episode_id=p["slots"][1]["episode_id"])),
            ("slots",lambda p:p.update(slots=p["slots"][:2])),
            ("role",lambda p:p.update(specialist_roles=47)),
            ("channel",lambda p:p.update(channel_id="UC"+"Y"*22)),
            ("status",lambda p:p.update(plan_kind="RELEASE_READY")),
        )
        for label,change in cases:
            with self.subTest(label=label):
                p=draft()
                change(p)
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(p,observations())

    def test_source_count_and_false_review_forgery_denied(self):
        mods=(
            lambda e:e.update(sources_fetched=2),
            lambda e:e.update(source_probes_attempted=4),
            lambda e:e.update(sources_failed=1),
            lambda e:e.update(claims_verified=1),
            lambda e:e.update(scripts_generated=1),
            lambda e:e.update(audio_or_video_generated=True),
            lambda e:e.update(source_body_persisted=True),
            lambda e:e.update(semantic_corroboration_performed=True),
            lambda e:e.update(billed_provider_calls=1),
            lambda e:e.update(youtube_upload_enabled=True),
            lambda e:e.update(production_credentials_used=True),
            lambda e:e.update(status="FACT_REVIEW_APPROVED"),
            lambda e:e.update(sources=[]),
        )
        for change in mods:
            with self.subTest(mod=str(change)):
                e=observations(count=1)
                change(e)
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(draft(),e)

    def test_delayed_or_future_observation_rejected(self):
        for when in ("2026-11-03T09:30:00+00:00",
                     "2026-11-07T09:30:00+00:00",
                     "2026-11-04T08:00:00+00:00",
                     "2026-11-04T09:30:00", "not-a-date"):
            with self.subTest(when=when):
                e=observations()
                e["generated_at_utc"]=when
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(draft(),e)

    def test_wrong_publisher_or_approved_lead_blocks_public_receipt(self):
        mods=(
            {"publisher":"Other"},
            {"status":"approved"},
            {"fact_checked":True},
            {"video_ready":True},
        )
        for change in mods:
            with self.subTest(change=change):
                p=draft()
                p["slots"][0]["research_lead"].update(change)
                with self.assertRaises(DailyEvidenceRefused):
                    build_retained_draft_receipt(p,observations())

    def test_cli_writes_only_short_bounded_sanitized_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            r=Path(root)
            plan=r/"plan.json"
            src=r/"observations.json"
            out=r/"github_public_draft_receipt.json"
            plan.write_text(json.dumps(draft()))
            src.write_text(json.dumps(observations(count=1)))
            cmd=[
                sys.executable,"-B","-m","autopilot.daily_evidence_bundle",
                "--plan",str(plan),"--evidence",str(src),"--output",str(out)
            ]
            job=subprocess.run(cmd,text=True,capture_output=True,timeout=15)
            self.assertEqual(job.returncode,0,job.stderr)
            data=json.loads(out.read_text())
            self.assertEqual(len(data["slots"]),3)
            self.assertNotIn(FAKE_PRIVATE,out.read_text())
            self.assertFalse(data["youtube_publishing_enabled"])
            # Refuse overwrite rather than silently mutate evidence proof.
            again=subprocess.run(cmd,text=True,capture_output=True,timeout=15)
            self.assertNotEqual(again.returncode,0)
            self.assertEqual(json.loads(job.stdout)["actual_uploads"],0)


if __name__=="__main__":
    unittest.main()
