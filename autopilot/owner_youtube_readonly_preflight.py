"""B4c1: owner-supplied AWS + OAuth read-only YouTube channel preflight.

Production-CAPABLE interface (unlike B4a/B4b fake protocols) but disabled in
all public CI. An independently owner-authorized *protected* runtime must
inject already authenticated AWS STS/KMS/Secrets Manager clients and a trusted
factory that creates a Google API client from an in-memory OAuth credential.

This module makes ONLY read/describe/get-secret and channels.list calls. It
does NOT create cloud resources, acquire credentials, upload, schedule, change
metadata, persist tokens, modify GitHub or certify human owner approval.

Important: source-level structural validation cannot prove trust of an injected
client, secret factory, account owner, billable provider or rights. CI mocks
are never evidence of real connections. Never log exceptions containing
tokens/secret payloads (even chains); all external errors are sanitized.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Callable

ACCOUNT = re.compile(r"^[0-9]{12}$")
REGION = re.compile(r"^(?:us|eu|ap|sa|ca|me|af|il)-[a-z]+-[1-9][0-9]?$")
ROLE = re.compile(r"^[A-Za-z0-9+=,.@_-]{3,64}$")
SESSION = re.compile(r"^[A-Za-z0-9+=,.@_-]{1,64}$")
SECRET = re.compile(
    r"^arn:aws:secretsmanager:([a-z0-9-]+):([0-9]{12}):"
    r"secret:flowminute/owner-youtube-oauth/[a-z0-9_-]{4,40}-[A-Za-z0-9]{6}$"
)
KMS = re.compile(r"^arn:aws:kms:([a-z0-9-]+):([0-9]{12}):key/([0-9a-fA-F-]{36})$")
CLIENT = re.compile(r"^[0-9]{6,21}-[A-Za-z0-9_-]{8,100}\.apps\.googleusercontent\.com$")
CHANNEL = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
CHANGE = re.compile(r"^OWNER-[A-Z0-9-]{8,64}$")
TOKEN_URI = "https://oauth2.googleapis.com/token"
READ_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
CAPTION_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
REQUIRED_SCOPES = frozenset((READ_SCOPE, UPLOAD_SCOPE, CAPTION_SCOPE))
STATUS = "OWNER_INJECTED_READ_ONLY_PREFLIGHT_NO_RELEASE_OR_PUBLIC_CI_ATTESTATION"


class OwnerChannelBoundaryError(ValueError):
    """Indeterminate or mismatched account/channel; forbid publisher activation."""


@dataclass(frozen=True)
class OwnerPublisherScope:
    """Actual values must be selected out-of-band by a real authorized owner."""
    aws_account_id: str
    aws_region: str
    aws_assumed_role_name: str
    oauth_secret_arn: str
    oauth_secret_kms_arn: str
    google_oauth_client_id: str
    youtube_channel_id: str
    owner_change_reference: str


def verify_scope(scope: OwnerPublisherScope) -> None:
    if (type(scope) is not OwnerPublisherScope
        or not isinstance(scope.aws_account_id,str) or not ACCOUNT.fullmatch(scope.aws_account_id)
        or not isinstance(scope.aws_region,str) or not REGION.fullmatch(scope.aws_region)
        or not isinstance(scope.aws_assumed_role_name,str)
        or not ROLE.fullmatch(scope.aws_assumed_role_name)
        or not isinstance(scope.google_oauth_client_id,str)
        or not CLIENT.fullmatch(scope.google_oauth_client_id)
        or not isinstance(scope.youtube_channel_id,str)
        or not CHANNEL.fullmatch(scope.youtube_channel_id)
        or not isinstance(scope.owner_change_reference,str)
        or not CHANGE.fullmatch(scope.owner_change_reference)):
        raise OwnerChannelBoundaryError("Owner-selected provider/channel scope malformed")
    sm=SECRET.fullmatch(scope.oauth_secret_arn) if isinstance(scope.oauth_secret_arn,str) else None
    key=KMS.fullmatch(scope.oauth_secret_kms_arn) if isinstance(scope.oauth_secret_kms_arn,str) else None
    if (not sm or not key or sm.group(1)!=scope.aws_region
        or sm.group(2)!=scope.aws_account_id
        or key.group(1)!=scope.aws_region or key.group(2)!=scope.aws_account_id):
        raise OwnerChannelBoundaryError("Owner secret and KMS must be region/account pinned")


def _require_dict(raw: object, failure: str) -> dict:
    if type(raw) is not dict:
        raise OwnerChannelBoundaryError(failure)
    return raw


def _version_current(meta: dict) -> str:
    stages=_require_dict(meta.get("VersionIdsToStages"),"Missing secret version stages")
    if len(stages)>50:
        raise OwnerChannelBoundaryError("Too many secret versions, manual audit required")
    current=[version for version,labels in stages.items()
             if isinstance(version,str) and isinstance(labels,list) and "AWSCURRENT" in labels]
    if (len(current)!=1 or not re.fullmatch(r"[A-Za-z0-9-]{8,80}",current[0])
        or any(not isinstance(k,str) or not isinstance(v,list)
               or any(not isinstance(label,str) for label in v)
               for k,v in stages.items())):
        raise OwnerChannelBoundaryError("Exactly one owned AWSCURRENT OAuth secret version required")
    return current[0]


def _tags(raw: object) -> dict:
    if not isinstance(raw,list) or len(raw)>30:
        raise OwnerChannelBoundaryError("No trusted OAuth secret metadata tags")
    m={}
    for pair in raw:
        if type(pair) is not dict:
            raise OwnerChannelBoundaryError("Malformed secret tag")
        key,value=pair.get("Key"),pair.get("Value")
        if (not isinstance(key,str) or not isinstance(value,str)
            or key in m):
            raise OwnerChannelBoundaryError("Duplicate/malformed OAuth secret tags")
        m[key]=value
    return m


def _secret_object(raw: str, scope: OwnerPublisherScope) -> dict:
    """Parse in-memory OAuth material. NEVER return into user-visible result."""
    if not isinstance(raw,str) or not 60 <= len(raw) <= 16000:
        raise OwnerChannelBoundaryError("Owner OAuth secret missing or wrong size")
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:
                raise OwnerChannelBoundaryError("Duplicate key in owner OAuth secret")
            d[k]=v
        return d
    try:
        obj=json.loads(raw,object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(
                           OwnerChannelBoundaryError("Invalid numeric OAuth secret")))
    except OwnerChannelBoundaryError:
        raise
    except (ValueError,TypeError):
        raise OwnerChannelBoundaryError("Malformed owner OAuth credential JSON") from None
    if type(obj) is not dict:
        raise OwnerChannelBoundaryError("OAuth secret must be a JSON object")
    if (obj.get("type") not in (None,"authorized_user")
        or obj.get("client_id")!=scope.google_oauth_client_id
        or obj.get("token_uri")!=TOKEN_URI
        or not isinstance(obj.get("client_secret"),str)
        or not 8 <= len(obj["client_secret"]) <= 1000
        or not isinstance(obj.get("refresh_token"),str)
        or not 16 <= len(obj["refresh_token"]) <= 5000):
        raise OwnerChannelBoundaryError("Wrong OAuth application/client/refresh configuration")
    scopes=obj.get("scopes")
    if (type(scopes) is not list
        or len(scopes)!=len(REQUIRED_SCOPES)
        or any(not isinstance(s,str) for s in scopes)
        or frozenset(scopes)!=REQUIRED_SCOPES):
        raise OwnerChannelBoundaryError("Only exact owner-approved three OAuth scopes accepted")
    allowed={"type","client_id","client_secret","refresh_token","token_uri","scopes"}
    if set(obj)!=allowed and set(obj)!=(allowed-{"type"}):
        raise OwnerChannelBoundaryError("Unexpected fields in OAuth secret, manual audit required")
    return obj


def _external_read(call: Callable, failure: str):
    """Do not chain provider exceptions: they may contain bearer credentials."""
    try:
        return call()
    except Exception:
        raise OwnerChannelBoundaryError(failure) from None


def verify_owner_youtube_readonly(
    *, sts, secretsmanager, kms,
    make_youtube_client_from_secret: Callable[[dict], object],
    scope: OwnerPublisherScope,
) -> dict:
    """Read-only control check for owner-provided real clients or fake CI fixtures.

    The trusted factory receives an in-memory OAuth secret object. It must use
    Google's OAuth refresh flow securely in an owner environment; never print,
    persist or leak it. This function never returns credentials, secret values,
    client IDs, session URL, API response body, or a permission to publish.
    """
    verify_scope(scope)
    if not callable(make_youtube_client_from_secret):
        raise OwnerChannelBoundaryError("Trusted owner-only Google client factory required")
    identity=_require_dict(
        _external_read(lambda:sts.get_caller_identity(),"Owner STS identity unavailable"),
        "Invalid owner STS response",
    )
    arn=identity.get("Arn")
    prefix=f"arn:aws:sts::{scope.aws_account_id}:assumed-role/{scope.aws_assumed_role_name}/"
    if (identity.get("Account")!=scope.aws_account_id or not isinstance(arn,str)
        or not arn.startswith(prefix)
        or not SESSION.fullmatch(arn[len(prefix):])):
        raise OwnerChannelBoundaryError("Caller is not owner-selected least-privilege STS role")

    meta=_require_dict(_external_read(
        lambda:secretsmanager.describe_secret(SecretId=scope.oauth_secret_arn),
        "Owner OAuth secret metadata unavailable"),
        "Malformed OAuth secret metadata",
    )
    if (meta.get("ARN")!=scope.oauth_secret_arn
        or meta.get("KmsKeyId")!=scope.oauth_secret_kms_arn
        or meta.get("DeletedDate") is not None):
        raise OwnerChannelBoundaryError("Missing/destroying or incorrectly encrypted owner OAuth secret")
    version=_version_current(meta)
    tags=_tags(meta.get("Tags"))
    if (tags.get("FlowMinute")!="owner-youtube-oauth"
        or tags.get("ReleaseStatus")!="owner-readonly-no-publish"
        or tags.get("OwnerChangeReference")!=scope.owner_change_reference):
        raise OwnerChannelBoundaryError("OAuth resource label mismatch (not proof of real consent)")

    key=_require_dict(_external_read(
        lambda:kms.describe_key(KeyId=scope.oauth_secret_kms_arn),
        "Owner OAuth KMS description unavailable"),
        "Malformed OAuth KMS key metadata",
    ).get("KeyMetadata")
    if (key.get("Arn")!=scope.oauth_secret_kms_arn
        or key.get("AWSAccountId")!=scope.aws_account_id
        or key.get("KeyManager")!="CUSTOMER"
        or key.get("KeyUsage")!="ENCRYPT_DECRYPT"
        or key.get("KeySpec")!="SYMMETRIC_DEFAULT"
        or key.get("KeyState")!="Enabled"
        or key.get("Enabled") is not True):
        raise OwnerChannelBoundaryError("Secret is not protected by expected enabled customer KMS key")

    value=_require_dict(_external_read(
        lambda:secretsmanager.get_secret_value(
            SecretId=scope.oauth_secret_arn,VersionStage="AWSCURRENT"
        ),"Protected AWSCURRENT owner OAuth secret could not be read"),
        "Malformed OAuth secret readback",
    )
    if (value.get("ARN")!=scope.oauth_secret_arn
        or value.get("VersionId")!=version
        or "AWSCURRENT" not in (
            value.get("VersionStages") if isinstance(value.get("VersionStages"),list) else []
        )
        or "SecretBinary" in value):
        raise OwnerChannelBoundaryError("Secret current version changed or binary content not allowed")
    oauth=_secret_object(value.get("SecretString"),scope)
    youtube=_external_read(lambda:make_youtube_client_from_secret(oauth),
                           "Trusted Google OAuth credential refresh/client creation failed")
    # The client comes from the exact in-memory current AWS secret; no unrelated
    # global Google credential or API key is accepted by this code path.
    response=_require_dict(
        _external_read(lambda:youtube.channels().list(
            part="id",mine=True,maxResults=50
        ).execute(),"Google owned channel readback unavailable"),
        "Invalid Google channels.list response",
    )
    items=response.get("items")
    page=response.get("pageInfo")
    if (response.get("kind")!="youtube#channelListResponse"
        or type(items) is not list or len(items)!=1
        or type(items[0]) is not dict
        or items[0].get("id")!=scope.youtube_channel_id
        or type(page) is not dict
        or type(page.get("totalResults")) is not int
        or page["totalResults"]!=1
        or "nextPageToken" in response):
        raise OwnerChannelBoundaryError(
            "Authenticated channel ownership mismatched or ambiguous; deny publishing"
        )
    # Do not return even a secret hash: secret fingerprints can be correlated
    # with leaked credential dumps. A config-only fingerprint is sufficient.
    config=(scope.aws_account_id+"|"+scope.aws_region+"|"+
            scope.youtube_channel_id+"|"+scope.owner_change_reference)
    return {
        "status":STATUS,
        "owner_supplied_aws_clients_read_only_checks_matched":True,
        "owner_supplied_google_client_exact_channel_readback_matched":True,
        "secret_current_version_and_kms_metadata_matched":True,
        "requested_google_oauth_scopes_structurally_matched":True,
        "config_only_scope_sha256":sha256(config.encode("utf-8")).hexdigest(),
        "aws_signed_identity_verified_independently_by_this_module":False,
        "google_signed_token_scopes_verified_independently_by_this_module":False,
        "owner_consent_or_change_ticket_cryptographically_verified":False,
        "production_credentials_connected_in_this_public_ci":False,
        "production_cloud_database_or_vault_deployed_by_this_module":False,
        "content_rights_or_video_release_review_approved":False,
        "actual_youtube_video_insert_performed":False,
        "actual_youtube_video_scheduled":False,
        "release_authorized":False,
    }
