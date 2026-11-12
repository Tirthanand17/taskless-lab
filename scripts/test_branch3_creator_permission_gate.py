"""Adversarial fail-closed checks for Clivox creator permission eligibility."""
from datetime import datetime,timezone
import copy
import unittest

from scripts.branch3_creator_permission_gate import (
    eligible_source, ClipRightsBlocked,
)

NOW=datetime(2026,11,12,7,0,tzinfo=timezone.utc)
SOURCE_ID="0123456789A"
CHANNEL_ID="UC"+"a"*22

def fixtures():
    creator={
        "creator_id":"synthetic_creator_for_tests",
        "source_channel_id":CHANNEL_ID,
        "proof_kind":"direct_written_creator_grant",
        "permission_proof_url":"https://example.org/rights/grant",
        "permission_evidence_sha256":"c"*64,
        "creator_identity_manually_verified":True,
        "permission_scope_manually_verified":True,
        "permission_currently_active":True,
        "rights_holder_has_necessary_underlying_rights":True,
        "permission_revoked":False,
        "scope":{
            "clipping_allowed":True,
            "editing_allowed":True,
            "youtube_shorts_allowed":True,
            "youtube_regular_allowed":True,
            "youtube_redistribution_allowed":True,
            "commercial_use_allowed":True,
            "all_territories_allowed":True,
        },
        "source_video_ids":[SOURCE_ID],
        "verified_at_utc":"2026-11-10T00:00:00Z",
        "expires_at_utc":"2026-12-12T00:00:00Z",
    }
    registry={"schema_version":1,"policy":"EXPLICIT_CREATOR_GRANT_ONLY","creators":[creator]}
    clip={
       "creator_id":"synthetic_creator_for_tests",
       "source_channel_id":CHANNEL_ID,
       "source_video_id":SOURCE_ID,
       "source_url":f"https://www.youtube.com/watch?v={SOURCE_ID}",
       "video_format":"short",
       "content_category":"podcast_interview",
       "contains_video_game_footage":False,
       "game_publisher_commercial_use_manually_verified":False,
       "pre_release_or_leaked_game_footage":False,
       "isolated_game_spoiler_or_in_game_show":False,
       "third_party_embedded_media_cleared":True,
       "source_content_context_reviewed":True,
    }
    return registry,clip

class PermissionGateTests(unittest.TestCase):
    def test_empty_real_allowlist_denies(self):
        r,c=fixtures()
        r["creators"]=[]
        with self.assertRaises(ClipRightsBlocked):
            eligible_source(r,c,now=NOW)
    def test_synthetic_valid_permission_only_eligible_for_more_review(self):
        r,c=fixtures()
        result=eligible_source(r,c,now=NOW)
        self.assertIn("MANUAL",result["status"])
        for field in ("copyright_risk_eliminated","signed_release_authorized",
                      "youtube_upload_authorized","youtube_scheduled",
                      "rights_legal_verification_performed_by_this_script"):
            self.assertIs(result[field],False)
    def test_public_creator_policy_still_requires_full_scopes(self):
        r,c=fixtures()
        r["creators"][0]["proof_kind"]="verified_creator_public_clipping_policy"
        self.assertIn("MANUAL",eligible_source(r,c,now=NOW)["status"])
        r["creators"][0]["scope"]["commercial_use_allowed"]=False
        with self.assertRaises(ClipRightsBlocked):
            eligible_source(r,c,now=NOW)
    def test_every_viral_pillar_is_eligible_only_with_existing_permission(self):
        for pillar in ("gaming","livestream","comedy","entertainment","podcast_interview"):
            r,c=fixtures()
            c["content_category"]=pillar
            c["contains_video_game_footage"]=(pillar=="gaming")
            c["game_publisher_commercial_use_manually_verified"]=(pillar=="gaming")
            with self.subTest(pillar=pillar):
                result=eligible_source(r,c,now=NOW)
                self.assertEqual(result["content_category"],pillar)
                self.assertFalse(result["youtube_upload_authorized"])

    def test_game_clips_require_separate_publisher_rights_and_no_leaks(self):
        for bad in (
            {"content_category":"gaming","contains_video_game_footage":True},
            {"content_category":"livestream","contains_video_game_footage":True},
            {"content_category":"gaming","contains_video_game_footage":True,
             "game_publisher_commercial_use_manually_verified":True,
             "pre_release_or_leaked_game_footage":True},
            {"content_category":"gaming","contains_video_game_footage":True,
             "game_publisher_commercial_use_manually_verified":True,
             "isolated_game_spoiler_or_in_game_show":True},
            {"content_category":"gaming","contains_video_game_footage":False,
             "game_publisher_commercial_use_manually_verified":True},
            {"content_category":"unknown"},
        ):
            r,c=fixtures()
            c.update(bad)
            with self.subTest(bad=bad),self.assertRaises(ClipRightsBlocked):
                eligible_source(r,c,now=NOW)

    def test_reject_ambiguous_or_missing_permission(self):
        for change in (
            lambda r,c:r["creators"].clear(),
            lambda r,c:r["creators"].append(copy.deepcopy(r["creators"][0])),
            lambda r,c:r["creators"][0].update(proof_kind="fair_use"),
            lambda r,c:r["creators"][0].update(proof_kind="creative_commons_only"),
            lambda r,c:r["creators"][0].update(permission_proof_url="http://example.org"),
            lambda r,c:r["creators"][0].update(permission_proof_url="https://user:secret@example.org/"),
            lambda r,c:r["creators"][0].update(permission_evidence_sha256="unknown"),
            lambda r,c:r["creators"][0].update(creator_identity_manually_verified=False),
            lambda r,c:r["creators"][0].update(permission_scope_manually_verified=False),
            lambda r,c:r["creators"][0].update(rights_holder_has_necessary_underlying_rights=False),
            lambda r,c:r["creators"][0].update(permission_currently_active=False),
            lambda r,c:r["creators"][0].update(permission_revoked=True),
            lambda r,c:r["creators"][0].update(expires_at_utc="2026-11-11T00:00:00Z"),
            lambda r,c:r["creators"][0].update(verified_at_utc="2026-11-13T00:00:00Z"),
            lambda r,c:r["creators"][0]["source_video_ids"].clear(),
            lambda r,c:r["creators"][0]["scope"].update(clipping_allowed=False),
            lambda r,c:r["creators"][0]["scope"].update(youtube_redistribution_allowed=False),
            lambda r,c:r["creators"][0]["scope"].update(all_territories_allowed=False),
            lambda r,c:c.update(third_party_embedded_media_cleared=False),
            lambda r,c:c.update(source_content_context_reviewed=False),
            lambda r,c:c.update(source_url="https://www.youtube.com/watch?v=ABCDEFGHIJK"),
            lambda r,c:c.update(source_channel_id="UC"+"b"*22),
            lambda r,c:c.update(video_format="TikTok"),
        ):
            r,c=fixtures()
            change(r,c)
            with self.subTest(case=str(change)),self.assertRaises(ClipRightsBlocked):
                eligible_source(r,c,now=NOW)

if __name__=="__main__":
    unittest.main()
