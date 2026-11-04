"""B3d4c2b3c1 offline identity boundary tests; all identities are FAKE fixtures.

The selected AWS account and GCP project are deliberately invented. Tests
never exchange an OIDC token, create or access a cloud secret, connect to a
production DB, call Gemini, use YouTube OAuth or spend any money.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import unittest

from autopilot.offline_cloud_identity_lint import (
    REPO,REPO_ID,OWNER_ID,BRANCH,ENVIRONMENT,WORKFLOW,OIDC_ISSUER,
    AWS_AUDIENCE,AWS_ROLE_SUBJECT,IdentityBoundaryError,ProductionIdentityIntent,
    SecretAccessIntent,PostgresConnectionIntent,ROLE_NAMES,
    inspect_claim_shape,inspect_offline_deployment_intent,
    lint_aws_oidc_trust,lint_gcp_oidc_provider,lint_secret_scopes,
    lint_postgres_tls,
)
from autopilot.private_cloud_recovery_preflight import ROLE_PURPOSE


def digest(name):
    return sha256(("invented test only: "+name).encode()).hexdigest()


def intent(backend="aws_secrets_manager"):
    project = "000000000000" if backend=="aws_secrets_manager" else "111122223333"
    aud = AWS_AUDIENCE if backend=="aws_secrets_manager" else (
        f"//iam.googleapis.com/projects/{project}/"
        "locations/global/workloadIdentityPools/flowminute-production/providers/github"
    )
    return ProductionIdentityIntent(
        provider=backend,cloud_project=project,
        repository=REPO,repository_id=REPO_ID,repository_owner_id=OWNER_ID,
        branch_ref=BRANCH,environment=ENVIRONMENT,workflow_ref=WORKFLOW,
        oidc_issuer=OIDC_ISSUER,token_audience=aud,
        project_spend_cap_verified_independently=False,
        owner_account_data_use_consent_verified_independently=False,
        real_environment_protection_verified=False,
        private_ledger_connected=False,
        actual_api_key_in_vault=False,
    )


def trust(i):
    if i.provider == "aws_secrets_manager":
        return {
            "Version":"2012-10-17",
            "Statement":[{
                "Effect":"Allow",
                "Principal":{"Federated":(
                    f"arn:aws:iam::{i.cloud_project}:"
                    "oidc-provider/token.actions.githubusercontent.com"
                )},
                "Action":"sts:AssumeRoleWithWebIdentity",
                "Condition":{"StringEquals":{
                    "token.actions.githubusercontent.com:aud":AWS_AUDIENCE,
                    "token.actions.githubusercontent.com:sub":AWS_ROLE_SUBJECT,
                }},
            }],
        }
    return {
        "issuer_uri":OIDC_ISSUER,
        "allowed_audiences":[i.token_audience],
        "attribute_mapping":{
            "google.subject":"assertion.repository_id + '/' + assertion.workflow_ref",
            "attribute.repository_id":"assertion.repository_id",
            "attribute.repository_owner_id":"assertion.repository_owner_id",
        },
        "attribute_condition":(
            f"assertion.repository_id == '{REPO_ID}'"
            f" && assertion.repository_owner_id == '{OWNER_ID}'"
            f" && assertion.ref == '{BRANCH}'"
            f" && assertion.environment == '{ENVIRONMENT}'"
            f" && assertion.workflow_ref == '{WORKFLOW}'"
            " && (assertion.event_name == 'schedule'"
            " || assertion.event_name == 'workflow_dispatch')"
        ),
        "scoped_service_account_only":True,
        "disable_persistent_service_account_keys":True,
    }


def claims(i):
    return {
        "iss":OIDC_ISSUER,"aud":i.token_audience,"sub":AWS_ROLE_SUBJECT,
        "repository":REPO,"repository_id":REPO_ID,
        "repository_owner_id":OWNER_ID,"ref":BRANCH,
        "environment":ENVIRONMENT,"workflow_ref":WORKFLOW,
        "event_name":"schedule",
    }


def secrets(i):
    result=[]
    for role in ROLE_NAMES:
        purpose=ROLE_PURPOSE[role]
        if i.provider=="aws_secrets_manager":
            action="secretsmanager:GetSecretValue"
            resource=(
                f"arn:aws:secretsmanager:ap-south-1:{i.cloud_project}:"
                f"secret:flowminute/{role}/{purpose}-fixture"
            )
        else:
            action="secretmanager.versions.access"
            resource=(
                f"projects/{i.cloud_project}/secrets/"
                f"flowminute-{role}-{purpose}/versions/1"
            )
        result.append(SecretAccessIntent(
            role,purpose,resource,action,digest("principal "+role)
        ))
    return tuple(result)


def database_tls():
    return PostgresConnectionIntent(
        db_hostname="pg.flowminute.private.example",
        database_name="flowminute_private_ledger",
        runtime_db_role="fm_runtime_gateway",
        tls_minimum_version="TLS1.3",
        sslmode="verify-full",
        trusted_ca_certificate_sha256=digest("fictional CA"),
        private_endpoint_policy_sha256=digest("fictional private network"),
        server_hostname_verification_required=True,
        live_tls_handshake_verified=False,
    )


def checked(i):
    return inspect_offline_deployment_intent(
        identity=i,oidc_policy=trust(i),simulated_claims=claims(i),
        secrets=secrets(i),database_tls=database_tls(),
    )


class OfflineCloudIdentityTests(unittest.TestCase):
    def test_strict_aws_and_gcp_hypothetical_paths_never_unlock_secrets(self):
        for backend in ("aws_secrets_manager","gcp_secret_manager"):
            with self.subTest(backend=backend):
                result=checked(intent(backend))
                self.assertTrue(result["three_separate_secret_scopes_linted"])
                self.assertTrue(result["postgres_client_tls_verify_full_required"])
                for k in (
                    "independently_authenticated_oidc_claims",
                    "real_cloud_iam_policy_readback_verified",
                    "actual_github_protected_environment_rules_verified",
                    "actual_cloud_vault_credentials_accessed",
                    "owner_consent_or_project_entitlement_verified",
                    "account_actual_zero_charge_guaranteed",
                    "production_database_connected",
                    "external_immutable_backup_anchor_connected",
                    "real_generative_provider_called",
                    "youtube_upload_enabled",
                    "release_authorized",
                    "cloud_deployment_authorized",
                ):
                    self.assertIs(result[k],False,k)

    def test_owner_or_service_account_claims_cannot_self_certify_real_access(self):
        i=intent()
        for name in (
            "project_spend_cap_verified_independently",
            "owner_account_data_use_consent_verified_independently",
            "real_environment_protection_verified",
            "private_ledger_connected",
            "actual_api_key_in_vault",
        ):
            for forged in (True,1,"true"):
                with self.subTest(name=name,forged=forged):
                    with self.assertRaises(IdentityBoundaryError):
                        checked(replace(i,**{name:forged}))

    def test_untrusted_repo_id_owner_id_main_ref_env_workflow_always_rejected(self):
        i=intent()
        bad={
            "repository":"UntrustedEvil/fork",
            "repository_id":"11111111",
            "repository_owner_id":"000001",
            "branch_ref":"refs/heads/feature/attack",
            "environment":"ci-nonprotected",
            "workflow_ref":"other/repo/.github/workflows/exfil.yml@refs/heads/main",
            "oidc_issuer":"https://evil.example.com",
        }
        for key,spoof in bad.items():
            with self.subTest(field=key):
                with self.assertRaises(IdentityBoundaryError):
                    checked(replace(i,**{key:spoof}))

    def test_fake_cloud_project_account_and_audience_scope_denied(self):
        for backend in ("aws_secrets_manager","gcp_secret_manager"):
            i=intent(backend)
            wrong=replace(i,token_audience="https://widened-audience.example")
            with self.assertRaises(IdentityBoundaryError):
                checked(wrong)
            wrong=replace(i,cloud_project="*")
            with self.assertRaises(IdentityBoundaryError):
                checked(wrong)

    def test_aws_iam_sub_aud_federated_issuer_principal_and_extra_statement_fails(self):
        i=intent()
        for variant in (
            lambda x:x["Statement"][0]["Condition"]["StringEquals"].update(
                {"token.actions.githubusercontent.com:sub":"repo:*"}
            ),
            lambda x:x["Statement"][0]["Condition"]["StringEquals"].update(
                {"token.actions.githubusercontent.com:aud":"*"}
            ),
            lambda x:x["Statement"][0].update({"Principal":"*"}),
            lambda x:x["Statement"][0].update({"Action":"sts:*"}),
            lambda x:x["Statement"][0].update({"Effect":"Deny"}),
            lambda x:x["Statement"][0]["Principal"].update(
                {"Federated":"arn:aws:iam::000000000000:oidc-provider/evil.example"}
            ),
            lambda x:x["Statement"][0]["Condition"].update(
                {"StringLike":{"token.actions.githubusercontent.com:sub":"repo:*"}}
            ),
            lambda x:x["Statement"].append(deepcopy(x["Statement"][0])),
        ):
            with self.subTest(number=variant):
                policy=trust(i)
                variant(policy)
                with self.assertRaises(IdentityBoundaryError):
                    lint_aws_oidc_trust(i,policy)

    def test_aws_identity_policy_does_not_claim_branch_guarantee(self):
        i=intent()
        out=inspect_claim_shape(i,claims(i))
        self.assertFalse(out["protected_environment_current_rules_verified"])
        self.assertFalse(out["cryptographic_jwt_signature_verified"])
        self.assertFalse(out["allow_assume_cloud_role"])
        self.assertFalse(out["allow_secret_read"])

    def test_gcp_weak_wif_mapping_condition_or_extra_audience_rejected(self):
        i=intent("gcp_secret_manager")
        for change in (
            lambda x:x.update({"attribute_condition":"assertion.repository == 'Tirthanand17/taskless-lab'"}),
            lambda x:x.update({"allowed_audiences":["*"]}),
            lambda x:x.update({"allowed_audiences":[i.token_audience,"another"]}),
            lambda x:x["attribute_mapping"].update({"google.subject":"assertion.actor"}),
            lambda x:x["attribute_mapping"].update({"attribute.repository_id":"assertion.repository"}),
            lambda x:x.update({"disable_persistent_service_account_keys":False}),
            lambda x:x.update({"scoped_service_account_only":False}),
            lambda x:x.update({"issuer_uri":"https://malicious.example"}),
            lambda x:x["attribute_mapping"].update({"attribute.extra":"assertion.actor"}),
        ):
            with self.subTest(change=change):
                policy=trust(i)
                change(policy)
                with self.assertRaises(IdentityBoundaryError):
                    lint_gcp_oidc_provider(i,policy)

    def test_pull_request_and_fork_claims_never_count_as_deployment_identity(self):
        for backend in ("aws_secrets_manager","gcp_secret_manager"):
            i=intent(backend)
            for field,value in (
                ("event_name","pull_request"),
                ("event_name","pull_request_target"),
                ("event_name","push"),
                ("event_name","workflow_run"),
                ("repository","someone-else/taskless-lab"),
                ("repository_id","9999"),
                ("repository_owner_id","9999"),
                ("ref","refs/pull/27/merge"),
                ("ref","refs/heads/feature/new"),
                ("environment","ci-only"),
                ("workflow_ref","attacker/repo/.github/workflows/bad.yml@main"),
                ("sub","repo:Tirthanand17/taskless-lab:pull_request"),
                ("aud","api://AzureADTokenExchange"),
                ("iss","https://malicious.example"),
            ):
                with self.subTest(backend=backend,field=field,value=value):
                    item=claims(i)
                    item[field]=value
                    with self.assertRaises(IdentityBoundaryError):
                        inspect_claim_shape(i,item)

    def test_manual_event_shape_still_never_verifies_jwt(self):
        i=intent()
        c=claims(i)
        c["event_name"]="workflow_dispatch"
        result=inspect_claim_shape(i,c)
        self.assertFalse(result["allow_assume_cloud_role"])
        self.assertFalse(result["cloud_security_principal_authenticated"])
        self.assertFalse(result["allow_provider_call"])
        self.assertFalse(result["allow_youtube_upload"])

    def test_extra_or_missing_claim_and_wrong_type_denied(self):
        i=intent()
        for test in (
            dict(claims(i),unexpected="owner-ok"),
            {k:v for k,v in claims(i).items() if k!="ref"},
            dict(claims(i),repository_id=1400950275),
            dict(claims(i),event_name=True),
        ):
            with self.subTest(item=test), self.assertRaises(IdentityBoundaryError):
                inspect_claim_shape(i,test)

    def test_secret_roles_are_per_purpose_and_per_resource_for_both_providers(self):
        for backend in ("aws_secrets_manager","gcp_secret_manager"):
            i=intent(backend)
            lint_secret_scopes(i,secrets(i))
            x=list(secrets(i))
            x[1]=replace(x[1],principal_digest_sha256=x[0].principal_digest_sha256)
            with self.assertRaises(IdentityBoundaryError):
                lint_secret_scopes(i,tuple(x))
            x=list(secrets(i))
            x[1]=replace(x[1],resource=x[0].resource)
            with self.assertRaises(IdentityBoundaryError):
                lint_secret_scopes(i,tuple(x))
            x=list(secrets(i))
            x[1]=replace(x[1],secret_purpose=x[0].secret_purpose)
            with self.assertRaises(IdentityBoundaryError):
                lint_secret_scopes(i,tuple(x))

    def test_wildcard_or_mutable_secret_resource_never_passes(self):
        for backend in ("aws_secrets_manager","gcp_secret_manager"):
            i=intent(backend)
            for field,value in (
                ("resource","*"),("resource","arn:aws:secretsmanager:*"),
                ("resource","projects/-/secrets/-/versions/latest"),
                ("action","*"),("action","secretsmanager:*"),
                ("action","secretmanager.versions.add"),
                ("workload_role","owner_admin"),
                ("principal_digest_sha256","malformed"),
            ):
                with self.subTest(backend=backend,field=field):
                    slots=list(secrets(i))
                    slots[0]=replace(slots[0],**{field:value})
                    with self.assertRaises(IdentityBoundaryError):
                        lint_secret_scopes(i,tuple(slots))

    def test_missing_duplicate_and_mutated_secret_scope_collection_denied(self):
        i=intent()
        for bad in (secrets(i)[:2],secrets(i)+(secrets(i)[0],),list(secrets(i))):
            with self.assertRaises(IdentityBoundaryError):
                lint_secret_scopes(i,bad)

    def test_client_must_require_verified_hostname_and_private_root_ca(self):
        lint_postgres_tls(database_tls())
        for field,bad in (
            ("sslmode","require"),("sslmode","verify-ca"),
            ("sslmode","disable"),("tls_minimum_version","TLS1.2"),
            ("database_name","public"),
            ("runtime_db_role","flowminute_test"),
            ("trusted_ca_certificate_sha256",""),
            ("trusted_ca_certificate_sha256","a"*63),
            ("private_endpoint_policy_sha256","000"),
            ("db_hostname","127.0.0.1"),
            ("db_hostname","localhost"),
            ("db_hostname","evil.example"),
            ("db_hostname","pg.flowminute.private.example."),
            ("db_hostname","pg..flowminute.private.example"),
            ("server_hostname_verification_required",False),
            ("live_tls_handshake_verified",True),
        ):
            with self.subTest(field=field,bad=bad):
                with self.assertRaises(IdentityBoundaryError):
                    lint_postgres_tls(replace(database_tls(),**{field:bad}))

    def test_hypothetical_production_workflow_is_not_this_unprivileged_ci(self):
        path=(Path(__file__).parent.parent/".github"/"workflows"/
              "flowminute-b3d4c2b3c1-identity-lint.yml")
        raw=path.read_text(encoding="utf-8")
        for forbidden in (
            "id-token: write","pull_request_target","secrets.",
            "environment: flowminute-prod","aws-actions/configure-aws-credentials",
            "google-github-actions/auth","deploy-cloud","publish_youtube",
        ):
            self.assertNotIn(forbidden,raw)
        self.assertIn("permissions:\n  contents: read",raw)
        self.assertIn("pull_request:",raw)
        self.assertNotIn("uses: github",raw)

    def test_identity_code_has_no_network_vault_or_jwt_verification_helpers(self):
        import autopilot.offline_cloud_identity_lint as module
        for symbol in (
            "exchange_oidc_token","fetch_secret","deploy_cloud",
            "generate_live_script","upload_youtube_video","create_cloud_db",
            "verify_jwt_signature","authorize_release",
        ):
            self.assertFalse(hasattr(module,symbol))
        assert not hasattr(module, "boto3")
        assert not hasattr(module, "requests")


if __name__=="__main__":
    unittest.main()
