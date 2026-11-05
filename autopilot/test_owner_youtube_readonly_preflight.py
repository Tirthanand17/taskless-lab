"""B4c1 no-secret/no-network owner YouTube read-only provenance tests.

All AWS and Google clients are synthetic injected objects with recorded calls.
Passing these tests is NEVER evidence of live owner consent or real OAuth.
"""
from __future__ import annotations

from dataclasses import replace
import json
import unittest

from autopilot.owner_youtube_readonly_preflight import (
    OwnerPublisherScope, OwnerChannelBoundaryError,
    verify_owner_youtube_readonly, verify_scope,
    REQUIRED_SCOPES, STATUS,
)

ACCOUNT="123456789012"
REGION="ap-south-1"
CHANNEL="UC"+"X"*22
ROLE="flowminute_fake_owner_reader"
SECRET="arn:aws:secretsmanager:ap-south-1:123456789012:secret:flowminute/owner-youtube-oauth/fakeproof-AbCd12"
KMS="arn:aws:kms:ap-south-1:123456789012:key/12345678-1234-1234-1234-123456789abc"
CLIENT_ID="123456789012-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com"
CHANGE="OWNER-B4C1-FAKE-20261105"
TOKEN="fakeRefreshTokenDoNotUse_ABC_12345678900"
PASS="fakeClientSecretNeverUse_12345678900"
VERSION="ciVersionCurrent1"


def scope():
    return OwnerPublisherScope(
        aws_account_id=ACCOUNT,aws_region=REGION,
        aws_assumed_role_name=ROLE,
        oauth_secret_arn=SECRET,oauth_secret_kms_arn=KMS,
        google_oauth_client_id=CLIENT_ID,
        youtube_channel_id=CHANNEL,
        owner_change_reference=CHANGE,
    )


def secret_data():
    return {
        "type":"authorized_user",
        "client_id":CLIENT_ID,
        "client_secret":PASS,
        "refresh_token":TOKEN,
        "token_uri":"https://oauth2.googleapis.com/token",
        "scopes":sorted(REQUIRED_SCOPES),
    }


class FakeOwnerClients:
    def __init__(self):
        self.calls=[]
        self.identity={
            "Account":ACCOUNT,
            "Arn":f"arn:aws:sts::{ACCOUNT}:assumed-role/{ROLE}/read_only_test",
        }
        self.metadata={
            "ARN":SECRET,"KmsKeyId":KMS,
            "VersionIdsToStages":{
                VERSION:["AWSCURRENT"],"ciVersionOlder1":["AWSPREVIOUS"]
            },
            "Tags":[
                {"Key":"FlowMinute","Value":"owner-youtube-oauth"},
                {"Key":"ReleaseStatus","Value":"owner-readonly-no-publish"},
                {"Key":"OwnerChangeReference","Value":CHANGE},
            ],
        }
        self.key={
            "KeyMetadata":{
                "Arn":KMS,"AWSAccountId":ACCOUNT,
                "KeyManager":"CUSTOMER","KeyUsage":"ENCRYPT_DECRYPT",
                "KeySpec":"SYMMETRIC_DEFAULT","KeyState":"Enabled",
                "Enabled":True,
            }
        }
        self.value={
            "ARN":SECRET,"VersionId":VERSION,
            "VersionStages":["AWSCURRENT"],
            "SecretString":json.dumps(secret_data()),
        }
        self.response={
            "kind":"youtube#channelListResponse",
            "items":[{"id":CHANNEL}],
            "pageInfo":{"totalResults":1,"resultsPerPage":1},
        }
        self.raise_on=None

    def _call(self,name):
        self.calls.append(name)
        if self.raise_on==name:
            raise RuntimeError("Fake secret material: "+TOKEN)

    def get_caller_identity(self):
        self._call("sts.get_caller_identity")
        return self.identity

    def describe_secret(self,*,SecretId):
        self._call("secretsmanager.describe_secret")
        assert SecretId==SECRET
        return self.metadata

    def get_secret_value(self,*,SecretId,VersionStage):
        self._call("secretsmanager.get_secret_value")
        assert SecretId==SECRET
        assert VersionStage=="AWSCURRENT"
        return self.value

    def describe_key(self,*,KeyId):
        self._call("kms.describe_key")
        assert KeyId==KMS
        return self.key

    def channels(self):
        self._call("youtube.channels")
        return self

    def list(self,*,part,mine,maxResults):
        self._call("youtube.channels.list")
        assert (part,mine,maxResults)==("id",True,50)
        return self

    def execute(self):
        self._call("youtube.channels.list.execute")
        return self.response

    def google_client_from_credential(self,content):
        self._call("google_factory_from_secret")
        assert content==secret_data()
        assert content["refresh_token"]==TOKEN
        return self

    def verify(self):
        return verify_owner_youtube_readonly(
            sts=self,secretsmanager=self,kms=self,
            make_youtube_client_from_secret=self.google_client_from_credential,
            scope=scope(),
        )


class OwnerReadOnlyGateTests(unittest.TestCase):
    def test_verified_synthetic_readback_is_not_release_approval(self):
        f=FakeOwnerClients()
        result=f.verify()
        self.assertEqual(result["status"],STATUS)
        self.assertTrue(result["owner_supplied_google_client_exact_channel_readback_matched"])
        self.assertTrue(result["secret_current_version_and_kms_metadata_matched"])
        self.assertTrue(result["requested_google_oauth_scopes_structurally_matched"])
        self.assertEqual(f.calls,[
            "sts.get_caller_identity",
            "secretsmanager.describe_secret",
            "kms.describe_key",
            "secretsmanager.get_secret_value",
            "google_factory_from_secret",
            "youtube.channels",
            "youtube.channels.list",
            "youtube.channels.list.execute",
        ])
        for key in (
            "aws_signed_identity_verified_independently_by_this_module",
            "google_signed_token_scopes_verified_independently_by_this_module",
            "owner_consent_or_change_ticket_cryptographically_verified",
            "production_credentials_connected_in_this_public_ci",
            "production_cloud_database_or_vault_deployed_by_this_module",
            "content_rights_or_video_release_review_approved",
            "actual_youtube_video_insert_performed",
            "actual_youtube_video_scheduled",
            "release_authorized",
        ):
            self.assertIs(result[key],False,key)
        serialized=json.dumps(result)
        self.assertNotIn(TOKEN,serialized)
        self.assertNotIn(PASS,serialized)
        self.assertNotIn(SECRET,serialized)
        self.assertNotIn(CLIENT_ID,serialized)
        self.assertNotIn(CHANNEL,serialized)
        self.assertNotIn(CHANGE,serialized)

    def test_scopes_are_exact_and_do_not_include_broad_account_management(self):
        self.assertEqual(REQUIRED_SCOPES,{
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
        })

    def test_reject_cross_account_wrong_role_secret_or_kms_scope(self):
        good=scope()
        for changes in (
            dict(aws_account_id="111111111111"),
            dict(aws_region="not-a-real-region"),
            dict(aws_assumed_role_name="bad/path"),
            dict(oauth_secret_arn=SECRET.replace("ap-south-1","us-west-2")),
            dict(oauth_secret_arn=SECRET.replace("123456789012","000000000000")),
            dict(oauth_secret_arn="arn:aws:secretsmanager:ap-south-1:123456789012:secret:other"),
            dict(oauth_secret_kms_arn=KMS.replace("ap-south-1","eu-west-1")),
            dict(oauth_secret_kms_arn=KMS.replace("123456789012","000000000000")),
            dict(google_oauth_client_id="not-an-oauth-client"),
            dict(youtube_channel_id="not-channel"),
            dict(owner_change_reference="APPROVED_BY_BOT"),
        ):
            with self.subTest(changes=changes),self.assertRaises(OwnerChannelBoundaryError):
                verify_scope(replace(good,**changes))

    def test_reject_root_writer_or_cross_account_sts_principals_before_secret_read(self):
        for arn,account in (
            (f"arn:aws:iam::{ACCOUNT}:root",ACCOUNT),
            (f"arn:aws:sts::{ACCOUNT}:assumed-role/other_role/test",ACCOUNT),
            (f"arn:aws:sts::{ACCOUNT}:assumed-role/{ROLE}/nested/session",ACCOUNT),
            (f"arn:aws:sts::{ACCOUNT}:assumed-role/{ROLE}/",ACCOUNT),
            (f"arn:aws:sts::{ACCOUNT}:assumed-role/{ROLE}/x","999999999999"),
        ):
            with self.subTest(arn=arn):
                f=FakeOwnerClients()
                f.identity={"Account":account,"Arn":arn}
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertEqual(f.calls,["sts.get_caller_identity"])

    def test_missing_wrong_or_deleted_secret_fails_before_value_retrieval(self):
        for changes in (
            {"ARN":"arn:aws:secretsmanager:elsewhere"},
            {"KmsKeyId":"arn:aws:kms:us-east-1:000000000000:key/none"},
            {"DeletedDate":"fake-pending-deletion"},
        ):
            with self.subTest(changes=changes):
                f=FakeOwnerClients()
                f.metadata.update(changes)
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertNotIn("secretsmanager.get_secret_value",f.calls)

    def test_secret_requires_single_current_version(self):
        for versions in (
            {},{"old":["AWSPREVIOUS"]},
            {"v1":["AWSCURRENT"],"v2":["AWSCURRENT"]},
            {"bad":["AWSCURRENT"],"old":["AWSPREVIOUS"]},
            {"currentVersion1":"AWSCURRENT"},
            {"currentVersion1":["AWSCURRENT","AWSPREVIOUS"],"dupVersion1":["AWSCURRENT"]},
        ):
            with self.subTest(versions=versions):
                f=FakeOwnerClients()
                f.metadata["VersionIdsToStages"]=versions
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertNotIn("secretsmanager.get_secret_value",f.calls)

    def test_secret_tags_are_not_a_signature_but_are_required_for_scope_match(self):
        for tags in (
            [],None,[{"Key":"FlowMinute","Value":"wrong"}],
            [{"Key":"FlowMinute","Value":"owner-youtube-oauth"}],
            [
                {"Key":"FlowMinute","Value":"owner-youtube-oauth"},
                {"Key":"FlowMinute","Value":"owner-youtube-oauth"},
                {"Key":"ReleaseStatus","Value":"owner-readonly-no-publish"},
                {"Key":"OwnerChangeReference","Value":CHANGE},
            ],
        ):
            with self.subTest(tags=tags):
                f=FakeOwnerClients()
                f.metadata["Tags"]=tags
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertNotIn("secretsmanager.get_secret_value",f.calls)

    def test_secret_customer_kms_mismatch_disabled_wrong_account_or_type(self):
        baseline=FakeOwnerClients().key["KeyMetadata"]
        for changes in (
            {"Arn":KMS+"-changed"},
            {"AWSAccountId":"999999999999"},
            {"KeyManager":"AWS"},
            {"KeyUsage":"SIGN_VERIFY"},
            {"KeySpec":"RSA_2048"},
            {"KeyState":"Disabled"},
            {"Enabled":False},
        ):
            with self.subTest(changes=changes):
                f=FakeOwnerClients()
                f.key["KeyMetadata"]={**baseline,**changes}
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertNotIn("secretsmanager.get_secret_value",f.calls)

    def test_secret_version_replay_binary_or_metadata_race_denied(self):
        for changes in (
            {"VersionId":"not-the-current-version"},
            {"VersionStages":["AWSPREVIOUS"]},
            {"SecretBinary":b"fake-binary"},
            {"ARN":SECRET+"-other"},
        ):
            with self.subTest(changes=list(changes)):
                f=FakeOwnerClients()
                f.value.update(changes)
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertNotIn("google_factory_from_secret",f.calls)

    def test_secret_duplicate_json_fields_and_invalid_json_denied(self):
        for raw in (
            '{"type":"authorized_user","refresh_token":"ABC","refresh_token":"DIFFERENT"}',
            '{"type":',
            '"just-text-not-object"',
            "null",
            "true",
            "[1,2,3]",
            '{"not":"oauth"}',
        ):
            with self.subTest(length=len(raw)):
                f=FakeOwnerClients()
                f.value["SecretString"]=raw
                with self.assertRaises(OwnerChannelBoundaryError) as cm:
                    f.verify()
                self.assertNotIn(TOKEN,str(cm.exception))
                self.assertNotIn("google_factory_from_secret",f.calls)

    def test_secret_wrong_client_broad_scopes_missing_refresh_and_token_uri(self):
        base=secret_data()
        for change in (
            {"client_id":"000000-other.apps.googleusercontent.com"},
            {"type":"service_account"},
            {"token_uri":"https://fake-token.local"},
            {"client_secret":""},
            {"refresh_token":"short"},
            {"scopes":["https://www.googleapis.com/auth/youtube"]},
            {"scopes":list(REQUIRED_SCOPES)+["https://www.googleapis.com/auth/youtube"]},
            {"scopes":list(REQUIRED_SCOPES)+[list(REQUIRED_SCOPES)[0]]},
            {"scopes":" ".join(REQUIRED_SCOPES)},
            {"token":"fake-access-token-leak"},
        ):
            with self.subTest(change=list(change)):
                f=FakeOwnerClients()
                f.value["SecretString"]=json.dumps({**base,**change})
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertNotIn("google_factory_from_secret",f.calls)

    def test_google_mine_channel_and_page_mismatch_deny(self):
        good=FakeOwnerClients().response
        bads=(
            {"kind":"not-channel","items":[{"id":CHANNEL}],"pageInfo":{"totalResults":1}},
            {"kind":"youtube#channelListResponse","items":[],"pageInfo":{"totalResults":0}},
            {"kind":"youtube#channelListResponse","items":[{"id":"UC"+"Y"*22}],"pageInfo":{"totalResults":1}},
            {"kind":"youtube#channelListResponse","items":[{"id":CHANNEL}],"pageInfo":{"totalResults":2}},
            {"kind":"youtube#channelListResponse","items":[{"id":CHANNEL},{"id":"UC"+"Y"*22}],
                "pageInfo":{"totalResults":2}},
            {"kind":"youtube#channelListResponse","items":[{"id":CHANNEL}],
                "pageInfo":{"totalResults":1},"nextPageToken":"more"},
            {"kind":"youtube#channelListResponse","items":[{"id":CHANNEL}],"pageInfo":{"totalResults":True}},
            {"kind":"youtube#channelListResponse","items":[CHANNEL],"pageInfo":{"totalResults":1}},
        )
        for case in bads:
            with self.subTest(case=case):
                f=FakeOwnerClients()
                f.response=case
                with self.assertRaises(OwnerChannelBoundaryError):
                    f.verify()
                self.assertIn("youtube.channels.list.execute",f.calls)

    def test_provider_exception_secret_value_never_appears_to_caller(self):
        for method in (
            "sts.get_caller_identity",
            "secretsmanager.describe_secret",
            "kms.describe_key",
            "secretsmanager.get_secret_value",
            "google_factory_from_secret",
            "youtube.channels.list.execute",
        ):
            with self.subTest(method=method):
                f=FakeOwnerClients()
                f.raise_on=method
                with self.assertRaises(OwnerChannelBoundaryError) as cm:
                    f.verify()
                self.assertNotIn(TOKEN,str(cm.exception))
                self.assertNotIn(PASS,str(cm.exception))
                self.assertNotIn(SECRET,str(cm.exception))
                self.assertIsNone(cm.exception.__cause__)

    def test_owner_role_policy_template_has_no_write_or_wildcard_resources(self):
        from pathlib import Path
        path=Path(__file__).parent.parent/"infra"/"aws"/"owner-youtube-readonly-role-policy.example.json"
        policy=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(policy["Version"],"2012-10-17")
        stmts=policy["Statement"]
        self.assertEqual(len(stmts),3)
        grants={s["Sid"]:s for s in stmts}
        self.assertEqual(set(grants),{
            "OnlyOwnerApprovedOAuthSecretMetadataAndValue",
            "OnlyOwnerOAuthKmsKeyMetadata",
            "DecryptOwnerOAuthOnlyThroughSecretsManager",
        })
        actions=set()
        for st in stmts:
            self.assertEqual(st["Effect"],"Allow")
            self.assertNotEqual(st["Resource"],"*")
            self.assertIn("${AWS_REGION}",st["Resource"])
            self.assertIn("${AWS_ACCOUNT_ID}",st["Resource"])
            a=st["Action"]
            actions.update(a if isinstance(a,list) else [a])
            self.assertNotIn("Principal",st)
        self.assertEqual(actions,{
            "secretsmanager:DescribeSecret","secretsmanager:GetSecretValue",
            "kms:DescribeKey","kms:Decrypt",
        })
        self.assertEqual(grants["DecryptOwnerOAuthOnlyThroughSecretsManager"]["Condition"],{
            "StringEquals":{
                "kms:ViaService":"secretsmanager.${AWS_REGION}.amazonaws.com",
                "kms:CallerAccount":"${AWS_ACCOUNT_ID}",
            }
        })

    def test_no_untrusted_google_client_factory(self):
        f=FakeOwnerClients()
        with self.assertRaises(OwnerChannelBoundaryError):
            verify_owner_youtube_readonly(
                sts=f,secretsmanager=f,kms=f,
                make_youtube_client_from_secret=None,scope=scope())
        self.assertEqual(f.calls,[])


if __name__=="__main__":
    unittest.main()
