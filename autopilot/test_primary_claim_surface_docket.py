"""B3d4c2c3c adversarial original surface and public source readback tests.

All fake HTML here is invented to exercise parsing/security, NOT fetched
NASA/NIST/USGS evidence. The separate CI live job must really GET originals.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime,timezone,timedelta
from hashlib import sha256
from unittest.mock import patch
import unittest

import autopilot.primary_claim_surface_docket as gate
from autopilot.primary_claim_surface_docket import (
    ClaimSurfaceError,CLAIM_KINDS,DRAFT_METADATA,STATUS,
    make_unapproved_claim_surface_docket,
    require_exact_unapproved_claim_surface_docket,
    inspect_three_original_claim_dockets,
)
from autopilot.primary_sourced_storyboards import (
    SLOTS,THUMB_CONTENT,build_story,StoryboardError,
)
from autopilot.public_primary_readback import (
    ANCHOR_PATTERNS,STATUS as READBACK_STATUS,
    SourceReadbackError,parse_official_page,run_primary_readback,
    verify_unapproved_readback,
)
from autopilot.primary_sourced_storyboards import PRIMARY_REFERENCES,canonical

SYNTHETIC_MARKERS={
    "nasa_moon":"Moon is about 384,400 kilometers away. Moon fact.",
    "nist_light":"Speed of light 299 792 458 m/s exact.",
    "usgs_magnitude":"one whole step is a tenfold increase; 32 times more energy.",
    "usgs_energy":"Formula 10**1.5 is energy ratio.",
    "nist_binary":"one 1 MiB = 1 048 576 B; one B = 8 bit.",
    "nist_si":"The SI prefix mega M 10 6 means million.",
}
FILL=" Entirely fabricated research HTML for a deterministic unit test, never real independent news or agency evidence."


def fake_page(source_id:str)->bytes:
    txt=("<html><body><h1>Invented mocked source HTML</h1>"
         +FILL*18+"<p>"+SYNTHETIC_MARKERS[source_id]+"</p>"
         +"</body></html>")
    return txt.encode("utf-8")


def fake_fetcher(url:str):
    source_id=next(k for k,ref in PRIMARY_REFERENCES.items()
                   if ref["url"]==url)
    return url,"text/html",fake_page(source_id)


class UnapprovedClaimSurfaceTests(unittest.TestCase):
    def test_exact_original_70_cues_32_scenes_and_metadata_indexed(self):
        combined=inspect_three_original_claim_dockets()
        self.assertEqual(combined["exact_scene_count"],32)
        self.assertEqual(combined["exact_narration_sentence_cues"],70)
        self.assertEqual(combined["distinct_primary_source_ids"],6)
        self.assertEqual(combined["total_curated_atomic_claim_ids"],14)
        self.assertFalse(combined["release_authorized"])
        self.assertFalse(combined["real_independent_full_fact_accuracy_review"])
        for slot in SLOTS:
            d=make_unapproved_claim_surface_docket(slot)
            story=build_story(slot)
            require_exact_unapproved_claim_surface_docket(d,slot)
            self.assertEqual(d["source_draft_sha256"],story["draft_sha256"])
            self.assertEqual(d["original_scene_count"],story["scene_count"])
            self.assertEqual(d["claim_count"],len(CLAIM_KINDS[slot]))
            self.assertEqual(
                d["exact_literal_text_surface_count"],
                d["exact_original_narration_sentence_cue_count"]
                +4*story["scene_count"]+4,
            )
            self.assertFalse(d["source_pages_current_live_readback_completed"])
            self.assertFalse(d["every_atomic_claim_semantically_supported_by_human"])
            self.assertFalse(d["youtube_upload_enabled"])
            self.assertFalse(d["release_authorized"])

    def test_all_claimed_speech_and_svg_visible_text_has_specific_source_ids(self):
        for slot in SLOTS:
            d=make_unapproved_claim_surface_docket(slot)
            src=set(d["source_references"])
            claims={c["id"]:c for c in d["claims"]}
            self.assertEqual(src,set(x for c in d["claims"] for x in c["primary_reference_ids"]))
            for c in d["claims"]:
                self.assertGreaterEqual(len(c["used_in_exact_original_surfaces"]),2)
                self.assertTrue(set(c["primary_reference_ids"])<=src)
                self.assertIn(c["kind"],("primary","derived","illustrative_assumption","limitation"))
            for surf in d["exact_original_surface_manifest"]:
                self.assertFalse(surf["independently_human_reviewed"])
                self.assertFalse(surf["factually_true_semantics_established_by_matching_ids"])
                self.assertEqual(
                    sha256(surf["literal_unapproved_text"].encode("utf8")).hexdigest(),
                    surf["text_sha256"],
                )
                self.assertTrue(set(surf["curated_claim_ids"])<=set(claims))

    def test_every_spoken_srt_cue_and_actual_svg_text_coverages_differ(self):
        for slot in SLOTS:
            d=make_unapproved_claim_surface_docket(slot)
            rows=d["exact_original_surface_manifest"]
            scenes=d["original_scene_count"]
            self.assertEqual(len([r for r in rows if ":speech:" in r["location"]]),
                             d["exact_original_narration_sentence_cue_count"])
            self.assertEqual(len([r for r in rows if ":original_svg_tick_" in r["location"]]),
                             scenes*2)
            self.assertEqual(len([r for r in rows if r["location"].endswith(":display_value")]),
                             scenes)
            self.assertEqual(len([r for r in rows if r["location"].endswith(":display_title")]),
                             scenes)
            self.assertEqual(len([r for r in rows if r["location"].startswith("unapproved_thumbnail_line_")]),
                             2)

    def test_thumbnail_wording_matches_actual_original_media_source(self):
        for slot in SLOTS:
            d=make_unapproved_claim_surface_docket(slot)
            thumb=THUMB_CONTENT[build_story(slot)["theme"]]
            lines=[x["literal_unapproved_text"] for x in d["exact_original_surface_manifest"]
                   if x["location"].startswith("unapproved_thumbnail_line_")]
            self.assertEqual(tuple(lines),thumb["lines"])
            ids=set(x for x in d["claims"] for x in x["primary_reference_ids"])
            self.assertGreaterEqual(len(ids),2)
            self.assertEqual(
                set(DRAFT_METADATA[slot]["claim_ids"]),set(CLAIM_KINDS[slot])
            )

    def test_no_real_review_or_release_flags_even_after_structural_success(self):
        d=make_unapproved_claim_surface_docket("long")
        for key in (
            "source_pages_current_live_readback_completed",
            "every_atomic_claim_semantically_supported_by_human",
            "actual_onscreen_graphic_and_media_final_human_inspected",
            "genuine_owner_fact_and_rights_approvals",
            "human_full_watch_completed",
            "youtube_upload_enabled","release_authorized",
        ):
            with self.subTest(key=key):
                modified=deepcopy(d)
                modified[key]=True
                modified["unapproved_claim_surface_docket_sha256"]=sha256(
                    canonical({k:v for k,v in modified.items()
                               if k!="unapproved_claim_surface_docket_sha256"})
                ).hexdigest()
                with self.assertRaises(ClaimSurfaceError):
                    require_exact_unapproved_claim_surface_docket(modified,"long")

    def test_changing_exact_narration_fails_verified_source_rebuild(self):
        with patch.object(gate,"build_story",return_value=(
            lambda s: (s["scenes"][0].update({"narration":"Fraudulent claim after audit."}) or s)
        )(build_story("short_am"))):
            with self.assertRaises(StoryboardError):
                make_unapproved_claim_surface_docket("short_am")

    def test_changing_actual_scene_claim_id_after_docket_denied(self):
        d=make_unapproved_claim_surface_docket("short_pm")
        alt=deepcopy(d)
        alt["claims"][0]["primary_reference_ids"]=["fake_unlicensed_blog"]
        with self.assertRaises(ClaimSurfaceError):
            require_exact_unapproved_claim_surface_docket(alt,"short_pm")
        alt=deepcopy(d)
        alt["exact_original_surface_manifest"].pop(0)
        with self.assertRaises(ClaimSurfaceError):
            require_exact_unapproved_claim_surface_docket(alt,"short_pm")

    def test_wrong_dates_or_unknown_original_topic_cannot_reuse_docket(self):
        d=make_unapproved_claim_surface_docket("long")
        with self.assertRaises(ClaimSurfaceError):
            require_exact_unapproved_claim_surface_docket(d,"short_am")
        with self.assertRaises(ClaimSurfaceError):
            require_exact_unapproved_claim_surface_docket(d,"long","2026-11-13")
        with self.assertRaises(StoryboardError):
            make_unapproved_claim_surface_docket("invalid")

    def test_no_claim_can_be_backed_by_unknown_primary_source(self):
        d=make_unapproved_claim_surface_docket("short_am")
        self.assertEqual(d["claim_count"],3)
        for c in d["claims"]:
            self.assertTrue(c["primary_reference_ids"])
            self.assertTrue(c["used_in_exact_original_surfaces"])
        self.assertFalse(d["real_external_source_excerpt_archived_to_private_vault"])


class PrimarySourceReadbackTests(unittest.TestCase):
    def test_all_six_mocked_html_pages_match_coarse_patterns_but_no_live_approval(self):
        record=run_primary_readback(
            fetcher=fake_fetcher,
            now=datetime(2026,11,4,tzinfo=timezone.utc),
        )
        verify_unapproved_readback(record)
        self.assertEqual(record["official_page_count"],6)
        self.assertEqual(record["status"],READBACK_STATUS)
        self.assertEqual(record["method"],"MOCK_INJECTED_HTTP_NO_LIVE_PROOF")
        self.assertFalse(record["direct_live_https_readback_completed"])
        self.assertFalse(record["all_source_claims_independently_human_fact_checked"])
        self.assertFalse(record["immutable_private_primary_source_archive_connected"])
        self.assertFalse(record["release_authorized"])
        self.assertEqual(
            set(x["source_id"] for x in record["pages"]),set(ANCHOR_PATTERNS)
        )
        for page in record["pages"]:
            self.assertGreater(page["raw_html_bytes"],700)
            self.assertFalse(page["meaning_of_all_video_claims_verified"])
            self.assertFalse(page["full_page_archived_or_licensed"])

    def test_live_fetch_never_sends_production_youtube_secret(self):
        import autopilot.public_primary_readback as lib
        for name in ("youtube_upload","insert_video","gemini_client",
                     "request_owner_approval","get_oauth_refresh_token"):
            self.assertFalse(hasattr(lib,name))

    def test_html_tamper_removes_verified_primary_marker(self):
        for sid in PRIMARY_REFERENCES:
            with self.subTest(sid=sid):
                url=PRIMARY_REFERENCES[sid]["url"]
                body=("<html><body>"+FILL*18+"<p>No scientific figure here</p></body></html>").encode()
                with self.assertRaises(SourceReadbackError):
                    parse_official_page(source_id=sid,url=url,
                                        final_url=url,content_type="text/html",body=body)

    def test_fail_closed_on_downgrade_wrong_authority_redirect_and_external_endpoint(self):
        sid="nasa_moon"
        url=PRIMARY_REFERENCES[sid]["url"]
        for bad in ("http://science.nasa.gov/moon/facts/",
                    "https://attacker.example/moon/facts/",
                    "https://user:pw@science.nasa.gov/moon/facts/",
                    "https://science.nasa.gov:8080/moon/facts/"):
            with self.subTest(bad=bad),self.assertRaises(SourceReadbackError):
                parse_official_page(source_id=sid,url=url,
                                    final_url=bad,content_type="text/html",
                                    body=fake_page(sid))

    def test_huge_html_invalid_encoding_and_nonhtml_content_blocked(self):
        sid="nist_binary"
        url=PRIMARY_REFERENCES[sid]["url"]
        for content_type,body in (
            ("application/pdf",fake_page(sid)),
            ("text/html",b"\xff"*920),
            ("text/html",b"tiny"),
            ("text/html",b"x"*3_000_001),
        ):
            with self.subTest(content_type=content_type,size=len(body)):
                with self.assertRaises(SourceReadbackError):
                    parse_official_page(source_id=sid,url=url,
                                        final_url=url,content_type=content_type,body=body)

    def test_claim_extracted_text_digest_changes_after_nonsemantic_html_change(self):
        sid="usgs_magnitude"
        url=PRIMARY_REFERENCES[sid]["url"]
        one=parse_official_page(source_id=sid,url=url,final_url=url,
                                content_type="text/html",body=fake_page(sid))
        two=parse_official_page(source_id=sid,url=url,final_url=url,
                                content_type="text/html",body=fake_page(sid).replace(
                                    b"deterministic unit test",b"separately forged metadata"
                                ))
        self.assertNotEqual(one["raw_response_sha256"],two["raw_response_sha256"])
        self.assertNotEqual(one["visible_extracted_text_sha256"],
                            two["visible_extracted_text_sha256"])

    def test_external_packet_after_dummy_fact_promotion_rejected_even_with_rehashed_digest(self):
        packet=run_primary_readback(fetcher=fake_fetcher)
        for key in (
            "all_source_claims_independently_human_fact_checked",
            "release_authorized","youtube_upload_enabled",
        ):
            modified=deepcopy(packet)
            modified[key]=True
            modified["unapproved_source_readback_packet_sha256"]=sha256(canonical({
                k:v for k,v in modified.items()
                if k!="unapproved_source_readback_packet_sha256"
            })).hexdigest()
            with self.subTest(key=key),self.assertRaises(SourceReadbackError):
                verify_unapproved_readback(modified)

    def test_source_reference_id_replay_and_unknown_host_rejected(self):
        sid="nist_light"
        ref=PRIMARY_REFERENCES[sid]
        wrong=PRIMARY_REFERENCES["nasa_moon"]["url"]
        with self.assertRaises(SourceReadbackError):
            parse_official_page(source_id=sid,url=wrong,final_url=wrong,
                                content_type="text/html",body=fake_page(sid))
        with self.assertRaises(SourceReadbackError):
            parse_official_page(source_id="attacker",url=ref["url"],
                                final_url=ref["url"],
                                content_type="text/html",body=fake_page(sid))

    def test_mock_transport_bad_source_is_failure_not_implicit_approval(self):
        def fail(url):
            if url==PRIMARY_REFERENCES["usgs_energy"]["url"]:
                raise SourceReadbackError("Simulated official page outage")
            return fake_fetcher(url)
        with self.assertRaises(SourceReadbackError):
            run_primary_readback(fetcher=fail)

    def test_naive_source_fetch_time_rejected(self):
        with self.assertRaises(SourceReadbackError):
            run_primary_readback(
                fetcher=fake_fetcher,
                now=datetime(2026,11,4,12,0),
            )


if __name__=="__main__":
    unittest.main()
