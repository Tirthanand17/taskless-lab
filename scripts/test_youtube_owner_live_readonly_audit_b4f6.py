"""B4f6 read-only real-OAuth-capable workflow: deterministic no-secret CI mock."""
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from autopilot.branch1_owner_schedule_readonly_v6 import RELEASE_STATUS
from scripts.test_owner_youtube_readback_b4f2 import youtube_fake,CHANNEL,OTHER
from scripts.youtube_owner_live_readonly_audit_b4f6 import (
    OwnerLiveAuditRefused, ReadOnlyYoutubeClient,
    audit_live_owner_readonly, require_manual_owner_context,
    classify_oauth_secret_shape, _failed_readback,
    EXPECTED_CHANNEL, EXPECTED_WORKFLOW, STATUS,
)

NOW=datetime(2026,11,7,4,45,tzinfo=timezone.utc)
ENV={
    "GITHUB_ACTIONS":"true",
    "GITHUB_EVENT_NAME":"workflow_dispatch",
    "GITHUB_REF":"refs/heads/main",
    "GITHUB_REPOSITORY":"Tirthanand17/taskless-lab",
    "GITHUB_WORKFLOW":EXPECTED_WORKFLOW,
    "GITHUB_SHA":"a"*40,
    "FM_EXPLICIT_OWNER_READONLY_AUDIT":"true",
}


def scan_receipt():
    return {
        "status":RELEASE_STATUS,
        "channel_owned_by_authenticated_oauth":True,
        "owner_uploads_pagination_exhausted":True,
        "only_readonly_channels_playlistitems_videos_list_called":True,
        "video_uploaded_or_edited_or_deleted":False,
        "safe_to_change_any_scheduled_video":False,
        "slots_checked":21,
        "original_git_receipts_count":4,
        "private_scheduled_slots_found":8,
        "historical_ids_same_private_schedule_count":3,
        "slot_conflicts":1,
        "private_schedule_outside_standard_time_count":2,
        "current_youtube_uploads_scanned":15,
        "slots":[{"owner_video_id":"sensitive-not-to-export",
                  "title":"not for public git reports"}],
    }


class LiveOwnerReadOnlyMocks(unittest.TestCase):
    def test_sanitized_success_owner_plus_real_slot_scan_contract(self):
        service=youtube_fake(channel=EXPECTED_CHANNEL)
        with patch("scripts.youtube_owner_live_readonly_audit_b4f6.read_owner_nov_schedule",
                   return_value=scan_receipt()) as scan:
            report=audit_live_owner_readonly(service,root=Path.cwd(),
                                             checked_at_utc=NOW)
        self.assertEqual(report["status"],STATUS)
        self.assertTrue(report["owner_authenticated_youtube_channel_readback_verified"])
        self.assertTrue(report["schedule_scan_complete"])
        self.assertEqual(report["slots_checked"],21)
        self.assertEqual(report["private_scheduled_slots_found"],8)
        self.assertEqual(report["slot_conflicts"],1)
        self.assertEqual(report["youtube_video_insert_update_delete_requests"],0)
        self.assertFalse(report["unattended_7_day_21_video_release_proof"])
        self.assertFalse(report["independent_owner_signature_or_fact_or_rights_clearance"])
        self.assertNotIn(EXPECTED_CHANNEL,str(report))
        self.assertNotIn("sensitive-not-to-export",str(report))
        self.assertNotIn("title",str(report))
        self.assertNotIn("token",str(report).lower())
        service.videos.return_value.insert.assert_not_called()
        service.videos.return_value.update.assert_not_called()
        service.videos.return_value.delete.assert_not_called()
        scan.assert_called_once()

    def test_wrong_authenticated_channel_stops_before_schedule_scan(self):
        service=youtube_fake(channel=OTHER)
        with patch("scripts.youtube_owner_live_readonly_audit_b4f6.read_owner_nov_schedule") as scan:
            with self.assertRaises(OwnerLiveAuditRefused) as caught:
                audit_live_owner_readonly(service,root=Path.cwd(),
                                          checked_at_utc=NOW)
            scan.assert_not_called()
        self.assertNotIn(OTHER,str(caught.exception))

    def test_unavailable_schedule_status_never_means_zero_scheduled(self):
        service=youtube_fake(channel=EXPECTED_CHANNEL)
        with patch("scripts.youtube_owner_live_readonly_audit_b4f6.read_owner_nov_schedule",
                   side_effect=RuntimeError("secret token data in SDK error")):
            report=audit_live_owner_readonly(service,root=Path.cwd(),
                                             checked_at_utc=NOW)
        self.assertTrue(report["owner_authenticated_youtube_channel_readback_verified"])
        self.assertFalse(report["schedule_scan_complete"])
        self.assertEqual(report["schedule_scan_outcome"],
                         "INCOMPLETE_STOP_NO_MUTATION")
        self.assertNotIn("private_scheduled_slots_found",report)
        self.assertNotIn("secret",str(report).lower())

    def test_malformed_or_forged_owner_slot_count_is_not_accepted(self):
        for bad in (
            dict(slots_checked=18),dict(slot_conflicts=-1),
            dict(owner_uploads_pagination_exhausted=False),
            dict(video_uploaded_or_edited_or_deleted=True),
            dict(current_youtube_uploads_scanned="15"),
            dict(safe_to_change_any_scheduled_video=True),
        ):
            service=youtube_fake(channel=EXPECTED_CHANNEL)
            with patch("scripts.youtube_owner_live_readonly_audit_b4f6.read_owner_nov_schedule",
                       return_value={**scan_receipt(),**bad}):
                result=audit_live_owner_readonly(service,root=Path.cwd(),
                                                checked_at_utc=NOW)
            with self.subTest(bad=bad):
                self.assertFalse(result["schedule_scan_complete"])
                self.assertNotIn("private_scheduled_slots_found",result)

    def test_only_whitelisted_get_list_apis_exposed_no_insert(self):
        service=youtube_fake(channel=EXPECTED_CHANNEL)
        restricted=ReadOnlyYoutubeClient(service)
        self.assertTrue(callable(restricted.videos().list))
        self.assertTrue(callable(restricted.channels().list))
        self.assertTrue(callable(restricted.playlistItems().list))
        for prohibited in (
            lambda:restricted.videos().insert,
            lambda:restricted.videos().update,
            lambda:restricted.videos().delete,
            lambda:restricted.captions,
            lambda:restricted.thumbnails,
        ):
            with self.subTest(fn=str(prohibited)),self.assertRaises(AttributeError):
                prohibited()

    def test_live_env_credential_format_has_only_coarse_safe_categories(self):
        self.assertEqual(classify_oauth_secret_shape(None),
                         "OAUTH_SECRET_NOT_INJECTED")
        self.assertEqual(classify_oauth_secret_shape("not JSON"),
                         "OAUTH_SECRET_NOT_JSON_OBJECT")
        self.assertEqual(classify_oauth_secret_shape('{"token":"sensitive"}'),
                         "OAUTH_REQUIRED_CREDENTIAL_FIELDS_MISSING")
        valid='{"client_id":"SENSITIVE_ID","client_secret":"SENSITIVE_SECRET",' + (
            '"refresh_token":"SENSITIVE_REFRESH"}')
        self.assertEqual(classify_oauth_secret_shape(valid),
                         "OAUTH_SHAPE_PRESENT_NOT_YET_AUTHENTICATED")
        for code in ("OAUTH_SECRET_NOT_JSON_OBJECT",
                     "OAUTH_REQUIRED_CREDENTIAL_FIELDS_MISSING",
                     "OAUTH_CHANNEL_API_READBACK_UNAVAILABLE",
                     "OWNER_CHANNEL_MISMATCH_OR_AMBIGUOUS"):
            report=_failed_readback(code)
            self.assertEqual(report["safe_failure_category"],code)
            self.assertFalse(report["owner_authenticated_youtube_channel_readback_verified"])
            self.assertFalse(report["schedule_scan_complete"])
            self.assertNotIn("SENSITIVE",str(report))
            self.assertEqual(report["youtube_video_insert_update_delete_requests"],0)

    def test_real_owner_wrong_channel_or_api_exception_returns_safe_enum(self):
        fake=youtube_fake(channel=OTHER)
        with self.assertRaisesRegex(
                OwnerLiveAuditRefused,"OWNER_CHANNEL_MISMATCH_OR_AMBIGUOUS"):
            audit_live_owner_readonly(fake,root=Path.cwd(),checked_at_utc=NOW)
        fake=youtube_fake(channel=EXPECTED_CHANNEL)
        fake.channels.return_value.list.return_value.execute.side_effect=RuntimeError(
            "OAuth bearer private refresh token must never escape")
        with self.assertRaisesRegex(
                OwnerLiveAuditRefused,"OAUTH_CHANNEL_API_READBACK_UNAVAILABLE") as err:
            audit_live_owner_readonly(fake,root=Path.cwd(),checked_at_utc=NOW)
        self.assertNotIn("bearer",str(err.exception).lower())

    def test_numeric_youtube_http_errors_use_secret_free_actionable_buckets(self):
        from types import SimpleNamespace
        cases=(
            (400,"YOUTUBE_CHANNEL_HTTP_400_INVALID_REQUEST"),
            (401,"YOUTUBE_CHANNEL_HTTP_401_OAUTH_REJECTED"),
            (403,"YOUTUBE_CHANNEL_HTTP_403_SCOPE_QUOTA_OR_FORBIDDEN"),
            (404,"YOUTUBE_CHANNEL_HTTP_404_NOT_FOUND"),
            (408,"YOUTUBE_CHANNEL_HTTP_408_TIMEOUT"),
            (429,"YOUTUBE_CHANNEL_HTTP_429_THROTTLED"),
            (500,"YOUTUBE_CHANNEL_HTTP_5XX_UPSTREAM"),
            (502,"YOUTUBE_CHANNEL_HTTP_5XX_UPSTREAM"),
            (503,"YOUTUBE_CHANNEL_HTTP_5XX_UPSTREAM"),
            (504,"YOUTUBE_CHANNEL_HTTP_5XX_UPSTREAM"),
        )
        for status,safe_code in cases:
            fake=youtube_fake(channel=EXPECTED_CHANNEL)
            error=RuntimeError("SECRET_CREDENTIALS_AND_PRIVATE_URL_MUST_NOT_LEAK")
            error.resp=SimpleNamespace(status=status,content=b"PRIVATE_REFRESH_TOKEN")
            fake.channels.return_value.list.return_value.execute.side_effect=error
            with self.subTest(http_status=status),patch(
                "scripts.youtube_owner_live_readonly_audit_b4f6.read_owner_nov_schedule"
            ) as scan:
                with self.assertRaisesRegex(OwnerLiveAuditRefused,safe_code) as caught:
                    audit_live_owner_readonly(
                        fake,root=Path.cwd(),checked_at_utc=NOW)
                scan.assert_not_called()
                fake.videos.return_value.insert.assert_not_called()
                self.assertNotIn("SECRET_CREDENTIALS",str(caught.exception))
                self.assertNotIn("PRIVATE_REFRESH",str(caught.exception))
                self.assertNotIn(EXPECTED_CHANNEL,str(caught.exception))
                report=_failed_readback(str(caught.exception))
                self.assertFalse(
                    report["owner_authenticated_youtube_channel_readback_verified"])
                self.assertFalse(report["schedule_scan_complete"])
                self.assertEqual(report["youtube_video_insert_update_delete_requests"],0)

    def test_known_refresh_failure_class_is_a_safe_enum_not_a_secret(self):
        RefreshError=type("RefreshError",(RuntimeError,),
                          {"__module__":"google.auth.exceptions"})
        fake=youtube_fake(channel=EXPECTED_CHANNEL)
        fake.channels.return_value.list.return_value.execute.side_effect=RefreshError(
            "refresh_token=PRIVATE_SECRET invalid_grant")
        with self.assertRaisesRegex(OwnerLiveAuditRefused,
                                    "OAUTH_REFRESH_FAILED") as caught:
            audit_live_owner_readonly(fake,root=Path.cwd(),checked_at_utc=NOW)
        self.assertNotIn("PRIVATE_SECRET",str(caught.exception))
        fake.videos.return_value.insert.assert_not_called()

    def test_untrusted_status_values_must_not_be_echoed_or_escalated(self):
        from types import SimpleNamespace
        for status in (True,"401",12345,-1,None):
            fake=youtube_fake(channel=EXPECTED_CHANNEL)
            err=RuntimeError("BEARER_DO_NOT_REPRINT")
            err.resp=SimpleNamespace(status=status)
            fake.channels.return_value.list.return_value.execute.side_effect=err
            with self.subTest(status=status),self.assertRaisesRegex(
                  OwnerLiveAuditRefused,
                  "OAUTH_CHANNEL_API_READBACK_UNAVAILABLE") as caught:
                audit_live_owner_readonly(fake,root=Path.cwd(),checked_at_utc=NOW)
            self.assertNotIn("BEARER",str(caught.exception))

    def test_main_only_manual_optin_and_sha_guards(self):
        require_manual_owner_context(ENV)
        for key,value in (
            ("GITHUB_ACTIONS","false"),
            ("GITHUB_EVENT_NAME","pull_request"),
            ("GITHUB_REF","refs/heads/other"),
            ("GITHUB_REPOSITORY","other/repo"),
            ("GITHUB_WORKFLOW","other audit"),
            ("FM_EXPLICIT_OWNER_READONLY_AUDIT","false"),
            ("GITHUB_SHA","no-valid-sha"),
        ):
            with self.subTest(key=key),self.assertRaises(OwnerLiveAuditRefused):
                require_manual_owner_context({**ENV,key:value})

    def test_workflow_only_manual_protected_read_only_no_content_write(self):
        src=(Path(__file__).resolve().parents[1]/
             ".github/workflows/flowminute-owner-readonly-channel-audit-b4f6.yml").read_text()
        self.assertIn("  workflow_dispatch:",src)
        for absent in ("  schedule:","  push:","  pull_request:",
                       "contents: write","git push","videos().insert("):
            self.assertNotIn(absent,src)
        self.assertIn("  contents: read",src)
        self.assertIn("environment: youtube-production",src)
        self.assertIn("persist-credentials: false",src)
        self.assertIn("secrets.YOUTUBE_TOKEN_JSON",src)
        self.assertIn("inputs.confirm_readonly_channel_audit == true",src)
        self.assertIn("FM_EXPLICIT_OWNER_READONLY_AUDIT",src)
        self.assertIn("retention-days: 1",src)
        self.assertNotIn("scripts.publish_youtube.main",src)


if __name__=="__main__":
    unittest.main()
