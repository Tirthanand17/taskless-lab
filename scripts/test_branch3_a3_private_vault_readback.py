"""No-network adversarial tests for Clivox A3 private repository readback."""
from __future__ import annotations

import copy
import json
import unittest

from scripts.branch3_a3_private_vault_readback import (
    APPROVAL_ENV, CHANNEL, CONTROLLER, OWNER, TOKEN_ENV, VAULT_NAME_ENV,
    WORKFLOW_REF, VaultReadbackDenied, expected_paths, fixture_report,
    run_owner_readback, validate_collaborators, validate_manual_context,
    validate_private_repository,
)

VAULT = "clivox-owner-media-vault"
TOKEN = "ghp_FAKE_ONLY_FOR_UNIT_TEST_NEVER_A_REAL_TOKEN_1234567890"


def env() -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": CONTROLLER,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_WORKFLOW_REF": WORKFLOW_REF,
        "GITHUB_ACTOR": OWNER,
        "GITHUB_TRIGGERING_ACTOR": OWNER,
        "GITHUB_RUN_ATTEMPT": "1",
        VAULT_NAME_ENV: VAULT,
        TOKEN_ENV: TOKEN,
        APPROVAL_ENV: "approved-a3-readonly-v1",
    }


def repo_data() -> dict:
    return {
        "id": 123456789,
        "name": VAULT,
        "full_name": OWNER + "/" + VAULT,
        "owner": {"login": OWNER, "type": "User"},
        "private": True,
        "visibility": "private",
        "archived": False,
        "disabled": False,
        "fork": False,
        "is_template": False,
    }


def owner_collaborators() -> list[dict]:
    return [{"login": OWNER, "role_name": "admin",
             "permissions": {"admin": True, "pull": True}}]


def transport(calls: list, *, repo=None, collaborators=None,
              repo_link="", users_link=""):
    r = repo_data() if repo is None else repo
    users = owner_collaborators() if collaborators is None else collaborators
    paths = expected_paths(VAULT)
    def fake(path, token):
        calls.append((path, token))
        if path == paths[0]:
            return copy.deepcopy(r), repo_link
        if path == paths[1]:
            return copy.deepcopy(users), users_link
        raise AssertionError("Unexpected GitHub path")
    return fake


class PrivateVaultReadbackTests(unittest.TestCase):
    def test_fixture_requires_zero_calls_and_zero_authorization(self):
        f = fixture_report()
        self.assertFalse(f["live_github_private_metadata_readback"])
        self.assertEqual(f["api_get_count"], 0)
        self.assertFalse(f["source_media_download_authorized"])
        self.assertFalse(f["youtube_upload_authorized"])

    def test_owner_only_metadata_live_mock_reports_private_snapshot_not_approval(self):
        calls = []
        result = run_owner_readback(env(), http_get=transport(calls))
        self.assertEqual(result["target_channel_id"], CHANNEL)
        self.assertTrue(result["live_github_private_metadata_readback"])
        self.assertTrue(result["repo_private_observed_at_readback"])
        self.assertTrue(result["owner_only_collaborator_page_observed"])
        self.assertFalse(result["owner_storage_usage_approval_verified"])
        self.assertFalse(result["app_installations_and_external_object_access_audited"])
        self.assertEqual(result["rights_holder_grants_verified"], 0)
        for flag in ("source_media_download_authorized",
                     "vault_media_write_authorized",
                     "licensed_media_render_authorized",
                     "youtube_upload_authorized",
                     "youtube_schedule_authorized",
                     "youtube_publish_authorized"):
            self.assertFalse(result[flag])
        self.assertEqual(result["api_get_count"], 2)
        self.assertEqual(result["github_api_write_count"], 0)
        self.assertEqual(result["youtube_api_write_count"], 0)
        self.assertEqual([v[0] for v in calls], list(expected_paths(VAULT)))
        self.assertTrue(all(v[1] == TOKEN for v in calls))
        serialized = json.dumps(result)
        for forbidden in (TOKEN, VAULT, "ghp_", "permissions", "login"):
            self.assertNotIn(forbidden, serialized)

    def test_wrong_actions_context_denied_before_any_get(self):
        for key, value in (
            ("GITHUB_ACTIONS", "false"),
            ("GITHUB_REPOSITORY", "other/repo"),
            ("GITHUB_EVENT_NAME", "pull_request"),
            ("GITHUB_REF", "refs/heads/feature"),
            ("GITHUB_WORKFLOW_REF", WORKFLOW_REF.replace("main", "branch")),
            ("GITHUB_ACTOR", "AnotherPerson"),
            ("GITHUB_TRIGGERING_ACTOR", "AnotherPerson"),
            ("GITHUB_RUN_ATTEMPT", "2"),
        ):
            e = env()
            e[key] = value
            calls = []
            with self.subTest(key=key), self.assertRaises(VaultReadbackDenied):
                run_owner_readback(e, http_get=transport(calls))
            self.assertEqual(calls, [])

    def test_missing_or_bad_owner_environment_secrets_deny(self):
        for key in (TOKEN_ENV, VAULT_NAME_ENV, APPROVAL_ENV):
            e = env()
            e.pop(key)
            with self.subTest(key=key), self.assertRaises(VaultReadbackDenied):
                validate_manual_context(e)
        for bad in ("true", "read-only", "approved-a3-readonly-v2"):
            e = env()
            e[APPROVAL_ENV] = bad
            with self.assertRaises(VaultReadbackDenied):
                validate_manual_context(e)
        for bad in ("short", "abc\nInjected", "A" * 2000):
            e = env()
            e[TOKEN_ENV] = bad
            with self.assertRaises(VaultReadbackDenied):
                validate_manual_context(e)

    def test_private_repo_name_is_exact_and_never_public_controller(self):
        for name in (
            "taskless-lab", "../other", "clivox-vault/other",
            "clivox_", "clivox-", "clivox-abc?", "clivox-%2Fother",
            "clivox-abc?access_token=secret", "CLIVOX-SECRET",
        ):
            e = env()
            e[VAULT_NAME_ENV] = name
            with self.subTest(name=name), self.assertRaises(VaultReadbackDenied):
                validate_manual_context(e)

    def test_public_repo_or_changed_visibility_denied_before_collaborators(self):
        for key, value in (
            ("private", False), ("visibility", "public"),
            ("archived", True), ("disabled", True), ("fork", True),
            ("is_template", True), ("id", 0),
            ("full_name", CONTROLLER), ("name", "wrong-name"),
        ):
            r = repo_data()
            r[key] = value
            calls = []
            with self.subTest(key=key), self.assertRaises(VaultReadbackDenied):
                run_owner_readback(env(), http_get=transport(calls, repo=r))
            self.assertEqual(len(calls), 1)

    def test_cross_owner_or_organization_repo_denied(self):
        for owner in (
            {"login": "SomeoneElse", "type": "User"},
            {"login": OWNER, "type": "Organization"},
            {},
        ):
            r = repo_data()
            r["owner"] = owner
            calls = []
            with self.subTest(owner=owner), self.assertRaises(VaultReadbackDenied):
                run_owner_readback(env(), http_get=transport(calls, repo=r))
            self.assertEqual(len(calls), 1)

    def test_extra_or_untrusted_collaborator_denied(self):
        for collaborators in (
            [], [{"login": "SomeoneElse", "role_name": "admin",
                  "permissions": {"admin": True}}],
            owner_collaborators() + [{"login": "Untrusted", "role_name": "write",
                                    "permissions": {"admin": False}}],
            [{"login": OWNER, "role_name": "write",
              "permissions": {"admin": False}}],
            [{"login": OWNER, "role_name": "custom",
              "permissions": {"admin": True}}],
        ):
            calls = []
            with self.subTest(collaborators=collaborators), self.assertRaises(VaultReadbackDenied):
                run_owner_readback(env(),
                    http_get=transport(calls, collaborators=collaborators))
            self.assertEqual(len(calls), 2)

    def test_pagination_or_unexpected_repo_link_denied(self):
        calls = []
        with self.assertRaises(VaultReadbackDenied):
            run_owner_readback(env(), http_get=transport(
                calls, users_link='<https://api.github.com/foo>; rel="next"'))
        with self.assertRaises(VaultReadbackDenied):
            run_owner_readback(env(), http_get=transport(
                [], repo_link='<https://api.github.com/foo>; rel="next"'))

    def test_api_error_fails_closed(self):
        def bad_transport(path, token):
            raise VaultReadbackDenied("SIMULATED_GITHUB_403")
        with self.assertRaises(VaultReadbackDenied):
            run_owner_readback(env(), http_get=bad_transport)

    def test_no_cross_channel_or_credentials_fallback(self):
        e = env()
        e["FLOWMINUTE_YOUTUBE_TOKEN"] = "do not read"
        e[TOKEN_ENV] = ""
        with self.assertRaises(VaultReadbackDenied):
            validate_manual_context(e)
        self.assertFalse(fixture_report()["youtube_publish_authorized"])


if __name__ == "__main__":
    unittest.main()
