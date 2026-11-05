"""B4b3: encrypted mock YouTube session checkpoint in real disposable PostgreSQL.

NO real upload URI accepted. No HTTPS, API, OAuth, KMS, cloud deployment or
publish authority. The only allowed input is an imaginary fake-session handle.
AES-256-GCM with 96-bit random nonce encrypts test bytes *before* SQL storage;
auth-data binds exact B4a context/channel/media/length and synthetic key version.
The mock key only exists in CI memory; a production owner-operated vault and
actual key lifecycle are entirely unimplemented.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import hmac
import json
import re
import secrets
from typing import Callable

from autopilot.ci_protected_pg_boundary import (
    _strict_role, GATEWAY_ROLE, AUDITOR_ROLE
)
from autopilot.ci_youtube_attempt_fence import (
    MockPgUploadTicket, validate_mock_intent
)
from autopilot.youtube_private_first_contract import DryRunUploadIntent
from autopilot.youtube_resumable_recovery_contract import (
    MAX_MEDIA_BYTES, RecoveryInstruction, FakeSession,
    fake_persisted_session, make_status_probe
)

FAKE_HANDLE = re.compile(r"^fake-session:[A-Za-z0-9_-]{12,120}$")
KEY_VERSION = re.compile(r"^ci_v[0-9]{1,2}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class SealedSessionRefused(ValueError):
    """No upload / fresh-session retry may follow a rejected/ambiguous write."""


@dataclass(frozen=True)
class MockCiEnvelopeKey:
    version: str
    material: bytes = field(repr=False)
    fake_only: bool = True

    @staticmethod
    def generate() -> "MockCiEnvelopeKey":
        """Ephemeral in-memory test key only, NOT durable owner-owned KMS."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return MockCiEnvelopeKey("ci_v1", AESGCM.generate_key(bit_length=256))


@dataclass(frozen=True)
class MockSealReceipt:
    channel_id: str
    episode_id: str
    state: str = "CI_MOCK_ENCRYPTED_SESSION_SEALED_NO_RELEASE"
    simulated_only: bool = True
    real_encrypted_owner_vault_deployed: bool = False
    actual_session_authenticated: bool = False
    release_authorized: bool = False


@dataclass(frozen=True)
class RecoveredFakeSession:
    """Dangerous material is excluded from repr and auditor/status outputs."""
    fake_handle: str = field(repr=False)
    fake_status_probe_session: FakeSession
    instruction: RecoveryInstruction
    real_youtube_session: bool = False
    owner_identity_authenticated: bool = False
    release_authorized: bool = False


def _require_key(key: MockCiEnvelopeKey) -> None:
    if (type(key) is not MockCiEnvelopeKey or key.fake_only is not True
        or not isinstance(key.version,str) or not KEY_VERSION.fullmatch(key.version)
        or not isinstance(key.material,bytes) or len(key.material)!=32):
        raise SealedSessionRefused("Only a 256-bit synthetic CI envelope key")


def _require_ticket(ticket: MockPgUploadTicket, intent: DryRunUploadIntent) -> str:
    if (type(ticket) is not MockPgUploadTicket
        or ticket.simulated_only is not True
        or ticket.release_authorized is not False
        or ticket.channel_id!=intent.channel_id
        or ticket.episode_id!=intent.episode_id
        or ticket.context_sha256!=intent.context_sha256
        or not isinstance(ticket.ephemeral_token,str)
        or not HEX64.fullmatch(ticket.ephemeral_token)):
        raise SealedSessionRefused("Exact previously fenced mock attempt ticket required")
    return sha256(ticket.ephemeral_token.encode("ascii")).hexdigest()


def _aad(intent: DryRunUploadIntent, length: int, version: str) -> bytes:
    return json.dumps(
        {
            "schema":"flowminute-b4b3-ci-aes-gcm-v1",
            "channel_id":intent.channel_id,
            "episode_id":intent.episode_id,
            "intent_context_sha256":intent.context_sha256,
            "mp4_sha256":intent.final_mp4_sha256,
            "total_bytes":length,
            "key_version":version,
        },
        sort_keys=True,separators=(",",":"),ensure_ascii=True,
    ).encode("ascii")


class ProtectedCiMockSessionVault:
    """PG16 writer function and ciphertext-only reload; no YouTube API."""

    def __init__(self, connect: Callable):
        _strict_role(connect,GATEWAY_ROLE)
        self._connect=connect

    def seal_before_any_transfer(
        self, *, intent: DryRunUploadIntent, ticket: MockPgUploadTicket,
        fake_handle: str, total_bytes: int, key: MockCiEnvelopeKey,
    ) -> MockSealReceipt:
        validate_mock_intent(intent)
        token_hash=_require_ticket(ticket,intent)
        _require_key(key)
        if type(total_bytes) is not int or not 0 < total_bytes <= MAX_MEDIA_BYTES:
            raise SealedSessionRefused("Invalid exact media byte length")
        if not isinstance(fake_handle,str) or not FAKE_HANDLE.fullmatch(fake_handle):
            raise SealedSessionRefused("NEVER accept a real YouTube resumable URL or bearer token")
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce=secrets.token_bytes(12)
        aad=_aad(intent,total_bytes,key.version)
        ciphertext=AESGCM(key.material).encrypt(
            nonce,fake_handle.encode("ascii"),aad,
        )
        try:
            with self._connect() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT fm_private_ci.seal_youtube_mock_session_once("
                            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (
                                intent.channel_id,intent.episode_id,token_hash,
                                intent.context_sha256,intent.final_mp4_sha256,
                                total_bytes,key.version,nonce,ciphertext,
                                sha256(aad).hexdigest(),
                                sha256(fake_handle.encode("ascii")).hexdigest(),
                            ),
                        )
                        if cur.fetchone()[0]!="CI_MOCK_ENCRYPTED_SESSION_SEALED_NO_RELEASE":
                            raise SealedSessionRefused("Unknown mock storage status")
        except Exception as exc:
            raise SealedSessionRefused(
                "Ambiguous/replayed/unauthorized mock envelope seal: NO RETRY OR UPLOAD"
            ) from exc
        return MockSealReceipt(intent.channel_id,intent.episode_id)

    def load_after_simulated_restart(
        self, *, intent: DryRunUploadIntent, ticket: MockPgUploadTicket,
        key: MockCiEnvelopeKey,
    ) -> RecoveredFakeSession:
        validate_mock_intent(intent)
        token_hash=_require_ticket(ticket,intent)
        _require_key(key)
        try:
            with self._connect() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT saved_context_sha256,saved_mp4_sha256,media_size,"
                            "saved_key_version,saved_nonce,saved_ciphertext,"
                            "saved_aad_sha256,saved_mock_handle_sha256 "
                            "FROM fm_private_ci.retrieve_youtube_mock_session(%s,%s,%s,%s,%s)",
                            (
                                intent.channel_id,intent.episode_id,token_hash,
                                intent.context_sha256,intent.final_mp4_sha256,
                            ),
                        )
                        row=cur.fetchone()
            if row is None:
                raise SealedSessionRefused("No unique mock encrypted checkpoint")
            context_hash,mp4_hash,total_bytes,version,nonce,ciphertext,aad_hash,handle_hash=row
            nonce,ciphertext=bytes(nonce),bytes(ciphertext)
            if (context_hash!=intent.context_sha256
                or mp4_hash!=intent.final_mp4_sha256
                or type(total_bytes) is not int or not 0 < total_bytes <= MAX_MEDIA_BYTES
                or version!=key.version
                or len(nonce)!=12 or not 32<=len(ciphertext)<=4096
                or not isinstance(aad_hash,str) or not HEX64.fullmatch(aad_hash)
                or not isinstance(handle_hash,str) or not HEX64.fullmatch(handle_hash)):
                raise SealedSessionRefused("Encrypted mock checkpoint metadata changed")
            aad=_aad(intent,total_bytes,version)
            if not hmac.compare_digest(sha256(aad).hexdigest(),aad_hash):
                raise SealedSessionRefused("Encrypted mock checkpoint AAD changed")
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            plaintext=AESGCM(key.material).decrypt(nonce,ciphertext,aad)
            fake_handle=plaintext.decode("ascii")
            if (not FAKE_HANDLE.fullmatch(fake_handle)
                or not hmac.compare_digest(
                    sha256(plaintext).hexdigest(),handle_hash)):
                raise SealedSessionRefused("Recovered mock handle identity changed")
            synthetic=fake_persisted_session(
                intent=intent,total_bytes=total_bytes,
                encrypted_session_reference_sha256=sha256(ciphertext).hexdigest(),
                synthetic_checkpoint_saved=True,
            )
            instruction=make_status_probe(synthetic)
            return RecoveredFakeSession(fake_handle,synthetic,instruction)
        except Exception as exc:
            raise SealedSessionRefused(
                "Unknown/corrupted/expired mock checkpoint: DO NOT START NEW SESSION"
            ) from exc


class CiMockSessionAuditor:
    """Redacted role-only count. No decrypt, nonce, hash, context or bearer link."""

    def __init__(self,connect: Callable):
        _strict_role(connect,AUDITOR_ROLE)
        self._connect=connect

    def inspect(self,channel_id: str,episode_id: str) -> dict:
        if (not isinstance(channel_id,str)
            or not re.fullmatch(r"UC[A-Za-z0-9_-]{22}",channel_id)
            or not isinstance(episode_id,str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{8,100}",episode_id)):
            raise SealedSessionRefused("Unknown mock audit scope")
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT sealed,event_count,encrypted_version "
                        "FROM fm_private_ci.inspect_youtube_mock_session(%s,%s)",
                        (channel_id,episode_id),
                    )
                    row=cur.fetchone()
        except Exception as exc:
            raise SealedSessionRefused("Mock auditor unable to read redacted status") from exc
        return {
            "sealed_in_disposable_postgres":row is not None and row[0] is True,
            "audit_event_count":0 if row is None else row[1],
            "synthetic_encryption_version":None if row is None else row[2],
            "contains_session_handle":False,
            "contains_encryption_secret":False,
            "real_cloud_persistence":False,
            "real_owner_oauth":False,
            "real_youtube_upload":False,
            "release_authorized":False,
        }
