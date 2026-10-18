"""Synthetic legacy/canonical ledger layout checks. No real D1 or video data."""
from copy import deepcopy
import unittest
from autopilot.phase4e_readonly_import import parse_d1_schema_observation
from autopilot.phase4e3_release_identity_risks import (
    inspect_release_identity_risks as audit,
)
from autopilot.phase4d_signed_observations import ObservationBlocked

def snapshot(columns, indexes=(), name="releases"):
    return parse_d1_schema_observation(
        table_list_rows=[{"name":name,"type":"table","schema":"main"}],
        table_details={name:{
            "columns":[{"name":x} for x in columns],
            "indexes":[{"columns":list(names),"unique":True} for names in indexes],
        }},
    )

LEGACY=("release_date","episode_id","stage","youtube_id",
        "media_sha256","publish_at_utc","updated_at")
CANONICAL=("channel_id","episode_id","planned_utc","media_sha256",
           "version","youtube_id","intent_id")
FIVE=(("channel_id","episode_id"),("channel_id","planned_utc"),
      ("channel_id","media_sha256"),("youtube_id",),("intent_id",))

class ReleaseIdentityRiskAuditTests(unittest.TestCase):
    def test_existing_private_code_legacy_shape_requires_explicit_crosswalk(self):
        r=audit(snapshot(LEGACY,(("release_date","episode_id"),)))
        self.assertEqual(r["legacy_date_key_table_count"],1)
        self.assertEqual(r["canonical_shape_candidate_count"],0)
        self.assertIn("LEGACY_RELEASE_DATE_KEY_REQUIRES_EXPLICIT_UTC_RECONCILIATION",
                      r["blockers"])
        self.assertFalse(r["date_to_utc_slot_mapping_verified"])

    def test_canonical_fields_without_indexes_cannot_claim_dedupe(self):
        r=audit(snapshot(CANONICAL))
        self.assertEqual(r["canonical_shape_candidate_count"],1)
        self.assertEqual(r["candidate_with_five_declared_unique_indexes_count"],0)
        self.assertEqual(r["missing_declared_unique_index_groups"],(1,1,1,1,1))
        self.assertIn("MISSING_DECLARED_RELEASE_COLLISION_CONSTRAINTS",
                      r["blockers"])

    def test_all_five_claimed_unique_indexes_still_not_verified_live(self):
        r=audit(snapshot(CANONICAL,FIVE))
        self.assertEqual(r["candidate_with_five_declared_unique_indexes_count"],1)
        self.assertEqual(r["missing_declared_unique_index_groups"],(0,0,0,0,0))
        self.assertFalse(r["real_global_uniqueness_verified"])
        self.assertFalse(r["migration_or_writes_authorized"])
        self.assertFalse(r["private_video_upload_approved"])
        self.assertEqual(r["network_calls"],0)
        self.assertEqual(r["database_writes"],0)
        self.assertEqual(r["generated_sql"],[])

    def test_lacking_media_hash_constraint_is_reported(self):
        r=audit(snapshot(CANONICAL,FIVE[:2]+FIVE[3:]))
        self.assertEqual(r["missing_declared_unique_index_groups"],(0,0,1,0,0))

    def test_wrong_index_fields_not_confused_for_exact_constraint(self):
        r=audit(snapshot(CANONICAL,(("channel_id","episode_id","version"),)))
        self.assertEqual(r["missing_declared_unique_index_groups"][0],1)

    def test_legacy_and_canonical_coexisting_remain_provisional(self):
        legacy=snapshot(LEGACY,(("release_date","episode_id"),),name="old_releases")
        canonical=snapshot(CANONICAL,FIVE,name="new_releases")
        mixed=deepcopy(legacy)
        mixed["objects"].extend(canonical["objects"])
        mixed["object_count"]=2
        r=audit(mixed)
        self.assertEqual(r["legacy_date_key_table_count"],1)
        self.assertEqual(r["canonical_shape_candidate_count"],1)
        self.assertFalse(r["historical_video_identity_reconciled"])

    def test_missing_owner_or_invalid_content_rejected(self):
        base=snapshot(CANONICAL,FIVE)
        for key,value in (
            ("origin","verified_live_d1"),
            ("saw_authenticated_provider_request",True),
            ("migration_authorized",True),
            ("contains_data_rows",True),
            ("production_writes",1),
            ("generated_sql",["CREATE TABLE bad"]),
        ):
            item=deepcopy(base)
            item[key]=value
            with self.subTest(key=key),self.assertRaises(ObservationBlocked):
                audit(item)

    def test_non_table_metadata_not_taken_for_release_table(self):
        s=snapshot(CANONICAL,FIVE)
        s["objects"][0]["kind"]="view"
        r=audit(s)
        self.assertEqual(r["canonical_shape_candidate_count"],0)

    def test_duplicate_claimed_columns_and_bad_index_denied(self):
        s=snapshot(CANONICAL,FIVE)
        s["objects"][0]["columns"].append({"name":"channel_id"})
        with self.assertRaises(ObservationBlocked):
            audit(s)
        s=snapshot(CANONICAL,FIVE)
        s["objects"][0]["indexes"].append(
            {"unique":True,"columns":["not_a_column"]})
        with self.assertRaises(ObservationBlocked):
            audit(s)

    def test_malformed_nested_index_payloads_rejected_consistently(self):
        # Includes a fake credential marker that must never appear in errors.
        for bad in ([], {}, None, 42, ["inner"], {"oauth_secret":"NEVER_ECHO"}):
            with self.subTest(value_type=type(bad).__name__):
                s=snapshot(CANONICAL,FIVE)
                s["objects"][0]["indexes"][0]["columns"]=["channel_id",bad]
                with self.assertRaises(ObservationBlocked) as cm:
                    audit(s)
                self.assertNotIn("NEVER_ECHO",str(cm.exception))
                self.assertNotIn("oauth_secret",str(cm.exception))

    def test_invalid_indexes_on_noncanonical_table_are_not_skipped(self):
        s=snapshot(("other_field",),name="unrelated_table")
        s["objects"][0]["indexes"]=[{"unique":True,"columns":[{}]}]
        with self.assertRaises(ObservationBlocked):
            audit(s)
        s["objects"][0]["kind"]="view"
        with self.assertRaises(ObservationBlocked):
            audit(s)

    def test_structural_schema_envelope_and_write_authority_forgeries_denied(self):
        for key,bad in (
            ("expected_channel_id","ANOTHER_CHANNEL"),
            ("object_count",99),
            ("object_count",True),
            ("skipped_protected_objects",-1),
            ("skipped_unsafe_objects",201),
            ("contains_data_rows",0),
            ("saw_authenticated_provider_request",0),
            ("migration_authorized",0),
            ("production_writes",False),
            ("generated_sql",None),
            ("requires_authorized_schema_provenance",False),
        ):
            with self.subTest(field=key):
                s=snapshot(CANONICAL,FIVE)
                s[key]=bad
                with self.assertRaises(ObservationBlocked):
                    audit(s)
        for forbidden in ("oauth_token","live_provider_attested","raw_sql"):
            with self.subTest(extra_field=forbidden):
                s=snapshot(CANONICAL,FIVE)
                s[forbidden]="NEVER_ECHO"
                with self.assertRaises(ObservationBlocked) as cm:
                    audit(s)
                self.assertNotIn("NEVER_ECHO",str(cm.exception))

    def test_missing_or_extra_nested_fields_and_protected_names_denied(self):
        s=snapshot(CANONICAL,FIVE)
        s["objects"][0]["columns"][0]["default_value"]="NEVER_ECHO"
        with self.assertRaises(ObservationBlocked) as cm:
            audit(s)
        self.assertNotIn("NEVER_ECHO",str(cm.exception))
        for name in ("oauth_refresh_token","sqlite_hidden","invalid name"):
            with self.subTest(object_name=name):
                s=snapshot(CANONICAL,FIVE)
                s["objects"][0]["name"]=name
                with self.assertRaises(ObservationBlocked):
                    audit(s)
        for field,bad in (("primary_key",1),("name",["unhashable"])):
            with self.subTest(column_field=field):
                s=snapshot(CANONICAL,FIVE)
                s["objects"][0]["columns"][0][field]=bad
                with self.assertRaises(ObservationBlocked):
                    audit(s)
        s=snapshot(CANONICAL,FIVE)
        s["objects"][0]["indexes"][0]["where"]="channel_id IS NOT NULL"
        with self.assertRaises(ObservationBlocked):
            audit(s)

    def test_duplicate_object_or_index_and_declaration_mismatch_denied(self):
        s=snapshot(CANONICAL,FIVE)
        s["objects"].append(deepcopy(s["objects"][0]))
        s["object_count"]=2
        with self.assertRaises(ObservationBlocked):
            audit(s)
        for indexes in (
            [{"unique":True,"columns":["channel_id","channel_id"]}],
            [{"unique":True,"columns":["channel_id","missing"]}],
            [{"unique":1,"columns":["channel_id","episode_id"]}],
            [{"unique":True,"columns":"channel_id"}],
        ):
            with self.subTest(indexes=indexes):
                s=snapshot(CANONICAL,FIVE)
                s["objects"][0]["indexes"]=indexes
                with self.assertRaises(ObservationBlocked):
                    audit(s)

    def test_valid_five_claimed_groups_remain_only_diagnostics(self):
        s=snapshot(CANONICAL,FIVE)
        r=audit(s)
        self.assertEqual(r["candidate_with_five_declared_unique_indexes_count"],1)
        self.assertEqual(r["missing_declared_unique_index_groups"],(0,0,0,0,0))
        self.assertNotIn("releases",str(r))
        self.assertNotIn("channel_id",str(r))
        self.assertFalse(r["live_schema_authenticated"])
        self.assertFalse(r["real_global_uniqueness_verified"])
        self.assertFalse(r["migration_or_writes_authorized"])
        self.assertEqual(r["network_calls"],0)
        self.assertEqual(r["database_writes"],0)

    def test_empty_schema_never_migrates_or_uploads(self):
        s=parse_d1_schema_observation(table_list_rows=[],table_details={})
        r=audit(s)
        self.assertEqual(r["canonical_shape_candidate_count"],0)
        self.assertFalse(r["migration_or_writes_authorized"])
        self.assertFalse(r["private_video_upload_approved"])

if __name__=="__main__":
    unittest.main()
