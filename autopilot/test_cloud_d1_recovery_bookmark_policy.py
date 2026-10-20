"""Adversarial untrusted D1 GET-bookmark policy tests (no provider calls)."""
from copy import deepcopy
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_d1_recovery_bookmark_policy import (
    screen_untrusted_d1_time_travel_bookmarks,
)

ONE="00000001-00000002-00004e2f-0a83ea2fceebc654de0640c422be4653"
TWO="00000002-00000003-00004e2f-0a83ea2fceebc654de0640c422be4653"


def response(bookmark=ONE):
    return {"success":True,"errors":[],"messages":[],
            "result":{"bookmark":bookmark}}


_UNSET=object()


def check(one=_UNSET,two=_UNSET,mode="workers_free"):
    # None is an invalid caller-supplied response, not a default alias.
    return screen_untrusted_d1_time_travel_bookmarks(
        initial_response=response() if one is _UNSET else one,
        final_response=response() if two is _UNSET else two,
        recovery_plan=mode,
    )


class CloudflareFreeBookmarkSafetyTests(unittest.TestCase):
    def test_two_equal_bookmarks_never_claim_real_recovery_or_source(self):
        result=check()
        self.assertTrue(result["two_bookmark_responses_well_formed"])
        self.assertFalse(result["bookmark_changed_between_reads"])
        self.assertEqual(result["documented_free_plan_recovery_days"],7)
        self.assertEqual(result["modeled_workers_plan"],"free")
        self.assertIn("D1_BOOKMARK_EQUALITY_DOES_NOT_PROVE_SNAPSHOT",
                      result["blocker_codes"])
        self.assertFalse(result["d1_restore_post_authorized"])
        self.assertFalse(result["d1_export_post_authorized"])
        self.assertFalse(result["youtube_upload_retry_authorized"])
        self.assertFalse(result["youtube_publishing_authorized"])
        self.assertFalse(result["live_source_verified"])
        self.assertFalse(result["real_historical_restore_verified"])
        self.assertEqual(result["provider_api_requests"],0)
        self.assertEqual(result["cloud_database_writes"],0)
        self.assertNotIn(ONE,str(result))
        self.assertNotIn("Bearer",str(result))

    def test_bookmark_drift_requires_hold_not_restore_or_reupload(self):
        result=check(two=response(TWO))
        self.assertTrue(result["bookmark_changed_between_reads"])
        self.assertIn("D1_BOOKMARK_CHANGED_BETWEEN_READS_QUARANTINE",
                      result["blocker_codes"])
        self.assertFalse(result["recovery_bookmark_freshness_verified"])
        self.assertFalse(result["d1_restore_post_authorized"])
        self.assertFalse(result["youtube_upload_retry_authorized"])
        self.assertNotIn(TWO,str(result))

    def test_wrong_pricing_plan_is_denied_not_assumed(self):
        for plan in ("workers_paid","free",None,True,7):
            with self.subTest(plan=plan),self.assertRaises(WorkflowError):
                check(mode=plan)

    def test_missing_result_success_or_errors_denied(self):
        for body in (
            {},[],None,{"success":True},
            {"success":False,"result":{"bookmark":ONE}},
            {"success":True,"errors":[{"message":"SECRET"}],
             "result":{"bookmark":ONE}},
            {"success":True,"errors":{},"result":{"bookmark":ONE}},
        ):
            with self.subTest(body_type=type(body)),self.assertRaises(WorkflowError):
                check(one=body)

    def test_extra_private_data_in_result_rejected_without_echoing(self):
        body=response()
        body["result"]["oauth_refresh_token"]="DO_NOT_LOG"
        with self.assertRaises(WorkflowError) as err:
            check(one=body)
        self.assertNotIn("DO_NOT_LOG",str(err.exception))

    def test_invalid_bookmark_and_secret_text_denied(self):
        for value in ("",None,123,True,"abcd",
                      "x"*257,"ABC 123 foo",
                      "SECRET?token=token",["x"]):
            with self.subTest(val_type=type(value)),self.assertRaises(WorkflowError):
                check(one=response(value))
        with self.assertRaises(WorkflowError):
            check(two=response("evil\ninjection0123456789"))

    def test_error_messages_are_not_echoed(self):
        payload=response()
        payload["errors"]=[{"message":"SECRET_PROVIDER_OAUTH"}]
        with self.assertRaises(WorkflowError) as err:
            check(one=payload)
        self.assertNotIn("SECRET_PROVIDER_OAUTH",str(err.exception))

    def test_bounded_messages_and_no_permission_escalation(self):
        good=response()
        good["messages"]=[{"message":"untrusted"}]*20
        result=check(one=good)
        self.assertFalse(result["d1_schema_migration_authorized"])
        bad=deepcopy(good)
        bad["messages"]=[{}]*21
        with self.assertRaises(WorkflowError):
            check(one=bad)
        bad["messages"]="unexpected"
        with self.assertRaises(WorkflowError):
            check(two=bad)

    def test_changed_string_shape_does_not_mean_historical_recoverability(self):
        result=check(one=response("0"*24),two=response("1"*24))
        self.assertTrue(result["bookmark_changed_between_reads"])
        self.assertFalse(result["full_database_backup_available_verified"])
        self.assertFalse(result["event_log_restore_verified"])

    def test_mutation_attempts_never_involved_in_policy(self):
        result=check()
        self.assertEqual(result["provider_api_requests"],0)
        self.assertEqual(result["cloud_database_writes"],0)
        for label in (
            "d1_restore_post_authorized","d1_export_post_authorized",
            "d1_schema_migration_authorized",
            "youtube_publishing_authorized",
        ):
            self.assertIs(result[label],False)


if __name__=="__main__":
    unittest.main()
