"""Offline-only tests for a manually gated, never-auto-live source capture CLI."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import unittest
from unittest.mock import patch

from autopilot.phase2_public_capture_preflight import (
    OWNER_PHRASE, ENV_APPROVAL_KEY, ENV_APPROVAL_VALUE, TARGET_BRANCH,
    _fixture_topic, _live_gates_ok, main, run_capture_preflight,
)
from autopilot.phase2_public_collector import CaptureDenied

NOW=datetime(2026,10,17,16,0,tzinfo=timezone.utc)
AUTHORIZED={
    ENV_APPROVAL_KEY:ENV_APPROVAL_VALUE,
    "GITHUB_ACTIONS":"true",
    "GITHUB_EVENT_NAME":"workflow_dispatch",
    "RUNNER_OS":"Linux",
    "GITHUB_REF_NAME":TARGET_BRANCH,
}


class CaptureOperatorTests(unittest.TestCase):
    def test_preview_default_has_no_network(self):
        with patch("autopilot.phase2_public_capture_preflight.collect_csv_research_sources") as fetch:
            result=run_capture_preflight()
            fetch.assert_not_called()
        self.assertEqual(result["status"],"PREVIEW_ONLY_NO_NETWORK")
        self.assertFalse(result["network_attempted"])
        self.assertFalse(result["publishing_authorized"])
        self.assertEqual(result["monthly_spend_inr"],0)

    def test_preview_ignores_approval_flags(self):
        data=run_capture_preflight(mode="preview",env=AUTHORIZED,phrase=OWNER_PHRASE)
        self.assertFalse(data["network_attempted"])

    def test_wrong_mode_denied(self):
        with self.assertRaises(CaptureDenied):
            run_capture_preflight(mode="continuous")

    def test_normal_cli_outputs_preview_json(self):
        out=io.StringIO()
        with redirect_stdout(out), patch(
            "autopilot.phase2_public_capture_preflight.collect_csv_research_sources"
        ) as fetch:
            self.assertEqual(main([]),0)
            fetch.assert_not_called()
        result=json.loads(out.getvalue())
        self.assertEqual(result["status"],"PREVIEW_ONLY_NO_NETWORK")

    def test_live_cli_without_permission_denied_without_network(self):
        out=io.StringIO()
        with redirect_stdout(out),patch.dict("os.environ",{},clear=True),patch(
            "autopilot.phase2_public_capture_preflight.collect_csv_research_sources"
        ) as fetch:
            code=main(["--mode","live"])
            fetch.assert_not_called()
        self.assertEqual(code,2)
        result=json.loads(out.getvalue())
        self.assertEqual(result["status"],"BLOCKED_NO_FURTHER_FETCHES")
        self.assertNotIn("token",out.getvalue().lower())

    def test_each_live_gate_must_be_present(self):
        for key in AUTHORIZED:
            env=dict(AUTHORIZED)
            env.pop(key)
            with self.subTest(missing=key),self.assertRaises(CaptureDenied):
                run_capture_preflight(mode="live",phrase=OWNER_PHRASE,env=env,now=NOW)

    def test_wrong_confirmation_never_executes(self):
        self.assertFalse(_live_gates_ok(env=AUTHORIZED,phrase="approve"))
        with self.assertRaises(CaptureDenied):
            run_capture_preflight(mode="live",phrase="approve",env=AUTHORIZED,now=NOW)

    def test_wrong_branch_never_executes(self):
        env={**AUTHORIZED,"GITHUB_REF_NAME":"main"}
        self.assertFalse(_live_gates_ok(env=env,phrase=OWNER_PHRASE))

    def test_normal_test_runner_cannot_trigger_live(self):
        env={**AUTHORIZED,"GITHUB_EVENT_NAME":"pull_request"}
        with self.assertRaises(CaptureDenied):
            run_capture_preflight(mode="live",phrase=OWNER_PHRASE,env=env,now=NOW)

    def test_local_windows_cannot_trigger_live(self):
        env={**AUTHORIZED,"RUNNER_OS":"Windows"}
        self.assertFalse(_live_gates_ok(env=env,phrase=OWNER_PHRASE))

    def test_fake_collector_forbidden_even_with_approval_without_test_guard(self):
        with self.assertRaises(CaptureDenied):
            run_capture_preflight(mode="live",phrase=OWNER_PHRASE,env=AUTHORIZED,
                                  now=NOW,_test_collector=lambda *args, **kw: ())
    
    def test_provisional_topic_does_not_claim_fact_review(self):
        r=_fixture_topic(now=NOW)
        self.assertTrue(all("not_fact_reviewed" in s.checked_by for s in r.sources))
        self.assertEqual(len(r.sources),2)
        r.validate(now=NOW)

    def test_naive_clock_rejected_after_all_manual_gates(self):
        with self.assertRaises(CaptureDenied):
            run_capture_preflight(mode="live",phrase=OWNER_PHRASE,
                                  env=AUTHORIZED,now=datetime(2026,10,17,16))

    def test_mock_source_is_only_allowed_in_test_mode_and_untrusted(self):
        from autopilot.test_phase2_public_collector import fake_transport
        from autopilot.phase2_public_collector import collect_csv_research_sources
        def synthetic(research, *, now, allow_live_network):
            self.assertTrue(allow_live_network)
            transport,_=fake_transport()
            return collect_csv_research_sources(research,now=now,
                                                _test_transport=transport)
        env={**AUTHORIZED,"FLOWMINUTE_TEST_ONLY":"1"}
        result=run_capture_preflight(mode="live",phrase=OWNER_PHRASE,env=env,
                                     now=NOW,_test_collector=synthetic)
        self.assertTrue(result["simulation_present"])
        self.assertFalse(result["real_provider_provenance_verified"])
        self.assertFalse(result["publishing_authorized"])


if __name__=="__main__":
    unittest.main()
