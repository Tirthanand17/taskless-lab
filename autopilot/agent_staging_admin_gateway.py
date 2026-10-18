"""Signed, expiring, one-time admin operations for OFFLINE staging only.

The administrator HMAC secret is injected at runtime and never persisted.
The admin gateway's verified request nonce is written in the same
BEGIN IMMEDIATE transaction as a key enroll/rotate/revoke mutation.

This is NOT a remotely authenticated, protected administrative service:
trusted-local StagingKeyPolicy methods are still directly callable, and local
SQLite access can bypass this façade. No deployment or publishing capability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable
import hmac
import json
import re

from .agent_org import WorkflowError
from .agent_staging_key_policy import (
    ADMIN_NONCE_RE, ADMIN_ID_RE, KEY_ID_RE, WORKER_ID_RE, StagingKeyPolicy,
)

TTL_SECONDS = 120


@dataclass(frozen=True)
class SignedStagingAdminCommand:
    admin_id: str
    action: str
    worker_id: str
    role: str
    key_id: str
    new_key_id: str
    nonce: str
    expires_epoch: int
    signature: str = ""

    def unsigned(self) -> dict:
        return {k:v for k,v in asdict(self).items() if k!="signature"}


def _payload(command:SignedStagingAdminCommand)->bytes:
    return json.dumps(command.unsigned(),sort_keys=True,
                      separators=(",",":"),ensure_ascii=True).encode("utf-8")


def sign_admin_command(command:SignedStagingAdminCommand,*,
                       secret:bytes)->SignedStagingAdminCommand:
    """No-secret-in-source offline operator signature test helper."""
    if (not isinstance(command,SignedStagingAdminCommand)
            or command.signature
            or type(secret) is not bytes or len(secret)<32):
        raise WorkflowError("Invalid fresh staging admin signing input")
    return replace(command,signature=hmac.new(
        secret,_payload(command),sha256,
    ).hexdigest())


class SignedStagingAdminGateway:
    """One explicit trusted admin ID, not a production KMS or remote API."""

    def __init__(self,policy:StagingKeyPolicy,*,admin_id:str,
                 secret:bytes,clock:Callable[[],datetime]|None=None):
        if (not isinstance(policy,StagingKeyPolicy)
                or not isinstance(admin_id,str)
                or ADMIN_ID_RE.fullmatch(admin_id) is None
                or type(secret) is not bytes or len(secret)<32
                or (clock is not None and not callable(clock))):
            raise WorkflowError("Invalid test-only staging admin registration")
        self._policy=policy
        self._admin_id=admin_id
        self._secret=secret
        self._clock=clock or (lambda:datetime.now(timezone.utc))

    def _authorize(self,command:SignedStagingAdminCommand):
        if (not isinstance(command,SignedStagingAdminCommand)
                or command.admin_id!=self._admin_id
                or command.action not in ("enroll","rotate","revoke")
                or not isinstance(command.worker_id,str)
                or WORKER_ID_RE.fullmatch(command.worker_id) is None
                or not isinstance(command.role,str)
                or not isinstance(command.key_id,str)
                or KEY_ID_RE.fullmatch(command.key_id) is None
                or not isinstance(command.new_key_id,str)
                or not isinstance(command.nonce,str)
                or ADMIN_NONCE_RE.fullmatch(command.nonce) is None
                or type(command.expires_epoch) is not int
                or not isinstance(command.signature,str)
                or re.fullmatch(r"[0-9a-f]{64}",command.signature) is None):
            raise WorkflowError("Invalid signed admin envelope")
        expected=hmac.new(self._secret,_payload(command),sha256).hexdigest()
        if not hmac.compare_digest(expected,command.signature):
            raise WorkflowError("Admin signature/identity verification failed")
        now=self._clock()
        if (not isinstance(now,datetime) or now.tzinfo is None
                or now.utcoffset() is None):
            raise WorkflowError("Staging admin clock must be timezone aware")
        stamp=now.timestamp()
        if (stamp!=int(stamp) or command.expires_epoch<=int(stamp)
                or command.expires_epoch-int(stamp)>TTL_SECONDS):
            raise WorkflowError("Signed admin command expired or TTL too long")
        if command.action=="enroll":
            if command.new_key_id!="":
                raise WorkflowError("Enrollment signed scope contains new key")
        elif command.action=="rotate":
            if (command.role!="" or KEY_ID_RE.fullmatch(command.new_key_id)
                    is None or command.key_id==command.new_key_id):
                raise WorkflowError("Rotation signed scope invalid")
        elif command.role!="" or command.new_key_id!="":
            raise WorkflowError("Revocation signed scope invalid")
        digest=sha256(_payload(command)).hexdigest()

        def one_time_guard(db):
            self._policy.consume_admin_nonce(
                db,nonce=command.nonce,admin_id=command.admin_id,
                action=command.action,request_sha=digest,
            )

        return one_time_guard

    def apply(self,command:SignedStagingAdminCommand)->dict:
        guard=self._authorize(command)
        if command.action=="enroll":
            self._policy.enroll(
                command.worker_id,command.role,command.key_id,
                _admin_guard=guard,
            )
            generation=1
        elif command.action=="rotate":
            generation=self._policy.rotate(
                command.worker_id,old_key_id=command.key_id,
                new_key_id=command.new_key_id,_admin_guard=guard,
            )
        else:
            self._policy.revoke(
                command.worker_id,expected_key_id=command.key_id,
                _admin_guard=guard,
            )
            generation=None
        return {
            "action":command.action,
            "worker_id":command.worker_id,
            "key_generation":generation,
            "signed_admin_command_committed":True,
            "publishing_authorized":False,
            "monthly_recurring_infrastructure_inr":0,
        }

    def status(self)->dict:
        return {
            "offline_admin_hmac_authenticated":True,
            "durable_command_nonce_atomic":True,
            "remote_admin_identity_authenticated":False,
            "direct_local_admin_policy_methods_blocked":False,
            "admin_hmac_secret_stored_in_db":False,
            "trusted_cloud_database_time":False,
            "production_deployment":False,
            "youtube_publishing_authorized":False,
            "monthly_recurring_infrastructure_inr":0,
        }
