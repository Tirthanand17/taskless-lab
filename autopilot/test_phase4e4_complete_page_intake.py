"""Adversarial offline Phase 4E4 pagination + PRAGMA uniqueness checks."""
from copy import deepcopy
import unittest

from autopilot.core import CHANNEL_ID
from autopilot.phase4b_readonly_audit import AuditBlocked
from autopilot.phase4e_readonly_import import parse_d1_schema_observation
from autopilot.phase4e4_complete_page_intake import assemble_untrusted_youtube_pages
from autopilot.phase4e2_signed_snapshot_bridge import _checked_youtube
from autopilot.phase4e3_release_identity_risks import inspect_release_identity_risks

CH={"items":[{"id":CHANNEL_ID,"snippet":{"title":"DO_NOT_DISCLOSE_CHANNEL"}}]}
FIELDS=(
    "channel_id","episode_id","planned_utc","media_sha256","version",
    "youtube_id","intent_id",
)
INDEXES=(
    ("channel_id","episode_id"),
    ("channel_id","planned_utc"),
    ("channel_id","media_sha256"),
    ("youtube_id",),("intent_id",),
)


def schema_with_indexes(indexes):
    return parse_d1_schema_observation(
        table_list_rows=[{"name":"releases","schema":"main","type":"table"}],
        table_details={"releases":{
            "columns":[{"name":v} for v in FIELDS],
            "indexes":indexes,
        }},
    )


def video(n):
    return {
        "id":f"abc{n:08d}",
        "snippet":{"channelId":CHANNEL_ID,"title":"PRIVATE_UNPUBLISHED_TITLE"},
        "status":{"privacyStatus":"private"},
        "processingDetails":{"processingStatus":"succeeded"},
        "description":"DO_NOT_DISCLOSE_TEXT",
    }


def page(items, req=None, nxt=None):
    response={"items":items}
    if nxt is not None:
        response["nextPageToken"]=nxt
    return {"requested_page_token":req,"response":response}


class DeclaredD1UniqueIndexSafety(unittest.TestCase):
    def test_sqlite_pragma_numeric_unique_one_is_understood(self):
        s=schema_with_indexes([{"unique":1,"partial":0,"columns":list(v)}
                               for v in INDEXES])
        report=inspect_release_identity_risks(s)
        self.assertEqual(report["candidate_with_five_declared_unique_indexes_count"],1)
        self.assertFalse(report["real_global_uniqueness_verified"])
        self.assertFalse(report["migration_or_writes_authorized"])

    def test_partial_numeric_unique_index_is_dropped(self):
        indexes=[{"unique":True,"partial":0,"columns":list(v)} for v in INDEXES]
        indexes[2]["partial"]=1
        s=schema_with_indexes(indexes)
        report=inspect_release_identity_risks(s)
        self.assertEqual(report["candidate_with_five_declared_unique_indexes_count"],0)
        self.assertEqual(report["missing_declared_unique_index_groups"],(0,0,1,0,0))
        self.assertFalse(report["real_global_uniqueness_verified"])

    def test_partial_where_predicate_does_not_prove_global_uniqueness(self):
        ix=[{"unique":True,"partial":0,"columns":list(v)} for v in INDEXES]
        ix[1]["where"]="state='queued'"
        report=inspect_release_identity_risks(schema_with_indexes(ix))
        self.assertEqual(report["missing_declared_unique_index_groups"],(0,1,0,0,0))

    def test_unrecognized_partial_metadata_does_not_promote_index(self):
        ix=[{"unique":1,"partial":0,"columns":list(v)} for v in INDEXES]
        ix[0]["partial"]="0"
        report=inspect_release_identity_risks(schema_with_indexes(ix))
        self.assertEqual(report["missing_declared_unique_index_groups"],(1,0,0,0,0))

    def test_unexpected_unique_flag_does_not_approve_index(self):
        ix=[{"unique":1,"partial":0,"columns":list(v)} for v in INDEXES]
        ix[0]["unique"]="true"
        report=inspect_release_identity_risks(schema_with_indexes(ix))
        self.assertEqual(report["missing_declared_unique_index_groups"],(1,0,0,0,0))

    def test_partial_constraint_metadata_never_authorizes_cloud_operations(self):
        s=schema_with_indexes([{"unique":1,"partial":1,"columns":list(v)}
                               for v in INDEXES])
        self.assertEqual(s["objects"][0]["indexes"],[])
        self.assertFalse(s["migration_authorized"])
        self.assertEqual(s["production_writes"],0)


class CompletePageChainSafety(unittest.TestCase):
    def collect(self,pages):
        return assemble_untrusted_youtube_pages(
            channel_response=CH,pages=pages)

    def test_realistic_two_page_chain_sanitized_and_bridge_compatible(self):
        pages=[page([video(1)],nxt="continuation_a"),
               page([video(2)],req="continuation_a")]
        output=self.collect(pages)
        self.assertTrue(output["pagination_complete"])
        self.assertEqual(output["video_count"],2)
        self.assertFalse(output["saw_authenticated_provider_request"])
        self.assertFalse(output["publication_authorized"])
        self.assertEqual(_checked_youtube(output),(2,0,False))
        self.assertNotIn("continuation_a",str(output))
        self.assertNotIn("PRIVATE_UNPUBLISHED_TITLE",str(output))
        self.assertNotIn("DO_NOT_DISCLOSE_CHANNEL",str(output))
        self.assertNotIn("DO_NOT_DISCLOSE_TEXT",str(output))
        self.assertEqual(output["network_calls"],0)

    def test_single_empty_terminal_page_still_unverified(self):
        s=self.collect([page([])])
        self.assertEqual(s["video_count"],0)
        self.assertTrue(s["pagination_complete"])
        self.assertFalse(s["saw_authenticated_provider_request"])
        self.assertFalse(s["publication_authorized"])

    def test_missing_last_page_is_not_complete(self):
        with self.assertRaisesRegex(AuditBlocked,"Missing final"):
            self.collect([page([video(1)],nxt="another")])

    def test_swapped_or_forged_requested_token_rejected(self):
        with self.assertRaises(AuditBlocked):
            self.collect([page([video(1)],nxt="next"),
                          page([video(2)],req="wrong")])

    def test_duplicate_video_across_pages_refused(self):
        with self.assertRaisesRegex(AuditBlocked,"Duplicate channel video"):
            self.collect([page([video(1)],nxt="p2"),
                          page([video(1)],req="p2")])

    def test_reused_next_token_cycle_rejected(self):
        with self.assertRaises(AuditBlocked):
            self.collect([page([video(1)],nxt="p2"),
                          page([video(2)],req="p2",nxt="p2")])

    def test_extra_page_after_terminal_refused(self):
        with self.assertRaises(AuditBlocked):
            self.collect([page([video(1)]),page([video(2)],req=None)])

    def test_wrong_channel_not_sanitized_as_ours(self):
        wrong=video(1)
        wrong["snippet"]["channelId"]="NOT_OUR_CHANNEL"
        with self.assertRaises(AuditBlocked):
            self.collect([page([wrong])])

    def test_missing_first_page_token_none_required(self):
        with self.assertRaises(AuditBlocked):
            self.collect([page([video(1)],req="already_started")])

    def test_malformed_page_token_refused(self):
        for token in ("", "bad token", "X"*300, 12):
            with self.subTest(token=token),self.assertRaises(AuditBlocked):
                self.collect([page([video(1)],nxt=token)])

    def test_more_than_supported_page_length_refused(self):
        with self.assertRaises(AuditBlocked):
            self.collect([page([video(i) for i in range(51)])])

    def test_max_total_page_count_fail_closed(self):
        pages=[]
        for i in range(13):
            pages.append(page([],req=None if i==0 else f"p{i}",
                              nxt=None if i==12 else f"p{i+1}"))
        with self.assertRaises(AuditBlocked):
            self.collect(pages)

    def test_page_with_wrong_shape_or_secret_key_refused(self):
        bad=page([video(1)])
        bad["oauth_token"]="secret"
        with self.assertRaises(AuditBlocked):
            self.collect([bad])

    def test_output_preserves_unknown_processing_as_uncertain(self):
        v=video(1)
        del v["processingDetails"]
        x=self.collect([page([v])])
        self.assertTrue(x["has_conflicting_state"])
        self.assertTrue(x["videos"][0]["uncertain_metadata"])
        self.assertEqual(_checked_youtube(x),(1,1,False))

    def test_repeat_same_order_is_deterministic(self):
        pages=[page([video(2),video(1)])]
        self.assertEqual(self.collect(pages),self.collect(deepcopy(pages)))

if __name__=="__main__":
    unittest.main()
