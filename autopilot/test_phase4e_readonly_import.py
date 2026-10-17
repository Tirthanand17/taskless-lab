"""Synthetic Phase 4E.1 provider-response shape tests; no provider queries."""
import unittest
from copy import deepcopy
from autopilot.core import CHANNEL_ID
from autopilot.phase4b_readonly_audit import AuditBlocked
from autopilot.phase4e_readonly_import import (
    parse_d1_schema_observation, parse_youtube_channel_video_observation,
)

VID="abc123def45"


def d1(*,table_list_rows=None,table_details=None):
    return parse_d1_schema_observation(
        table_list_rows=table_list_rows if table_list_rows is not None else [
            {"schema":"main","name":"releases","type":"table"},
            {"schema":"main","name":"oauth_grants","type":"table"}],
        table_details=table_details if table_details is not None else {
            "releases":{"columns":[
                {"name":"channel_id","type":"TEXT","pk":1},
                {"name":"episode_id","type":"TEXT","pk":2},
                {"name":"refresh_token","type":"BLOB","dflt_value":"'very_private'"},
            ],"indexes":[{"unique":True,"columns":["channel_id","episode_id"]},
                          {"unique":True,"columns":["refresh_token"]}]},
            "oauth_grants":{"columns":[{"name":"refresh_token","type":"BLOB"}]}
        })


def yt(*,channels=None,videos=None,**kwargs):
    ch={"items":[{"id":CHANNEL_ID,"snippet":{"title":"Hidden channel title"}}]}
    vr={"items":[{
        "id":VID,
        "snippet":{"channelId":CHANNEL_ID,"title":"PRIVATE VIDEO NAME"},
        "status":{"privacyStatus":"private","publishAt":"2026-10-20T05:30:00Z"},
        "processingDetails":{"processingStatus":"succeeded"},
        "description":"SENSITIVE CONTENT MUST NOT APPEAR",
    }]}
    vr.update(kwargs)
    return parse_youtube_channel_video_observation(
        channel_response=ch if channels is None else channels,
        video_response=vr if videos is None else videos,
    )


class ProviderShapeTests(unittest.TestCase):
    def test_schema_contains_no_data_or_protected_tables(self):
        report=d1()
        self.assertEqual(report["object_count"],1)
        self.assertEqual(report["skipped_protected_objects"],1)
        self.assertEqual(report["objects"][0]["name"],"releases")
        self.assertNotIn("oauth_grants",str(report))
        self.assertNotIn("refresh_token",str(report))
        self.assertNotIn("very_private",str(report))
        self.assertFalse(report["saw_authenticated_provider_request"])
        self.assertFalse(report["migration_authorized"])

    def test_schema_excludes_sensitive_column_index(self):
        item=d1()["objects"][0]
        self.assertEqual(len(item["indexes"]),1)
        self.assertEqual(item["indexes"][0]["columns"],["channel_id","episode_id"])

    def test_schema_disallows_duplicate_objects(self):
        with self.assertRaises(AuditBlocked):
            d1(table_list_rows=[
                {"schema":"main","name":"releases","type":"table"},
                {"schema":"main","name":"releases","type":"table"}],table_details={})

    def test_schema_disallows_duplicate_columns(self):
        with self.assertRaises(AuditBlocked):
            d1(table_list_rows=[{"schema":"main","name":"releases","type":"table"}],
                table_details={"releases":{"columns":[{"name":"id"},{"name":"id"}]}})

    def test_schema_ignores_unsafe_identifiers_not_echoed(self):
        unsafe="unsafe; DROP TABLE secret"
        report=d1(table_list_rows=[{"schema":"main","name":unsafe,"type":"table"}],
                  table_details={unsafe:{}})
        self.assertEqual(report["object_count"],0)
        self.assertEqual(report["skipped_unsafe_objects"],1)
        self.assertNotIn(unsafe,str(report))

    def test_schema_skips_virtual_system_and_non_main(self):
        rows=[{"schema":"temp","name":"temporary","type":"table"},
              {"schema":"main","name":"sqlite_stat1","type":"table"},
              {"schema":"main","name":"_cf_internal","type":"table"}]
        report=d1(table_list_rows=rows,table_details={})
        self.assertEqual(report["object_count"],0)

    def test_schema_input_bounded(self):
        with self.assertRaises(AuditBlocked):
            d1(table_list_rows=[{"schema":"main","name":f"table_{i}","type":"table"} for i in range(201)],
               table_details={})

    def test_schema_no_sql_or_network_authority(self):
        r=d1()
        self.assertEqual(r["generated_sql"],[])
        self.assertEqual(r["production_writes"],0)
        self.assertEqual(r["origin"],"UNAUTHENTICATED_D1_SHAPED_METADATA")

    def test_youtube_minimized_video_readback(self):
        report=yt()
        self.assertEqual(report["video_count"],1)
        self.assertEqual(report["videos"][0]["youtube_id"],VID)
        self.assertEqual(report["videos"][0]["publish_at_utc"],"2026-10-20T05:30:00+00:00")
        self.assertTrue(report["pagination_complete"])
        self.assertFalse(report["contains_titles_or_descriptions"])
        self.assertNotIn("PRIVATE VIDEO NAME",str(report))
        self.assertNotIn("SENSITIVE CONTENT MUST NOT APPEAR",str(report))
        self.assertFalse(report["saw_authenticated_provider_request"])
        self.assertFalse(report["publication_authorized"])

    def test_wrong_channel_rejected(self):
        with self.assertRaises(AuditBlocked):
            yt(channels={"items":[{"id":"wrong_channel"}]})

    def test_videos_must_belong_to_expected_channel(self):
        with self.assertRaises(AuditBlocked):
            yt(videos={"items":[{"id":VID,"snippet":{"channelId":"wrong"},
                                  "status":{"privacyStatus":"public"}}]})

    def test_invalid_video_id_and_duplicates_rejected(self):
        with self.assertRaises(AuditBlocked):
            yt(videos={"items":[{"id":"bad","snippet":{"channelId":CHANNEL_ID},
                                  "status":{"privacyStatus":"private"}}]})
        sample={"id":VID,"snippet":{"channelId":CHANNEL_ID},
                "status":{"privacyStatus":"private"}}
        with self.assertRaises(AuditBlocked):
            yt(videos={"items":[sample,sample]})

    def test_processing_unavailable_stays_unknown(self):
        v={"id":VID,"snippet":{"channelId":CHANNEL_ID},
           "status":{"privacyStatus":"private"}}
        r=yt(videos={"items":[v]})
        self.assertEqual(r["videos"][0]["processing"],"unknown")
        self.assertTrue(r["has_conflicting_state"])

    def test_public_with_unexpected_future_schedule_is_uncertain(self):
        v={"id":VID,"snippet":{"channelId":CHANNEL_ID},
           "status":{"privacyStatus":"public","publishAt":"2026-10-20T05:30:00Z"}}
        r=yt(videos={"items":[v]})
        self.assertTrue(r["videos"][0]["uncertain_metadata"])

    def test_video_pagination_does_not_imply_exhaustive_inventory(self):
        v={"id":VID,"snippet":{"channelId":CHANNEL_ID},
           "status":{"privacyStatus":"private"}}
        r=yt(videos={"items":[v],"nextPageToken":"more_pages"})
        self.assertFalse(r["pagination_complete"])
        self.assertIn("VIDEO_PAGINATION_INCOMPLETE",r["blockers"])

    def test_fake_verified_property_cannot_authorize(self):
        v={"id":VID,"snippet":{"channelId":CHANNEL_ID},
           "status":{"privacyStatus":"private"}}
        r=yt(videos={"items":[v],"verified":True,"publisher_authorized":True})
        self.assertFalse(r["saw_authenticated_provider_request"])
        self.assertFalse(r["publication_authorized"])

    def test_timezone_normalization_is_exact_utc(self):
        v={"id":VID,"snippet":{"channelId":CHANNEL_ID},
           "status":{"privacyStatus":"private","publishAt":"2026-10-20T11:00:00+05:30"}}
        r=yt(videos={"items":[v]})
        self.assertEqual(r["videos"][0]["publish_at_utc"],"2026-10-20T05:30:00+00:00")

    def test_naive_or_invalid_schedule_is_rejected(self):
        for ts in ("2026-10-20T11:00:00","not_a_date"):
            with self.subTest(ts=ts),self.assertRaises(AuditBlocked):
                yt(videos={"items":[{"id":VID,"snippet":{"channelId":CHANNEL_ID},
                                     "status":{"privacyStatus":"private","publishAt":ts}}]})

    def test_bad_privacy_is_rejected(self):
        with self.assertRaises(AuditBlocked):
            yt(videos={"items":[{"id":VID,"snippet":{"channelId":CHANNEL_ID},
                                  "status":{"privacyStatus":"future"}}]})

    def test_unexpected_processing_is_rejected(self):
        with self.assertRaises(AuditBlocked):
            yt(videos={"items":[{"id":VID,"snippet":{"channelId":CHANNEL_ID},
                                  "status":{"privacyStatus":"private"},
                                  "processingDetails":{"processingStatus":"artificial"}}]})

    def test_unbounded_responses_rejected(self):
        with self.assertRaises(AuditBlocked):
            yt(videos={"items":[{}]*501})

if __name__=="__main__":
    unittest.main()
