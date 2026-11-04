"""B3d4c2b3b: actual disposable Postgres pg_dump -> independent DB restore.

NEVER a production backup or cloud storage. This only reads/creates CI-named
PostgreSQL databases on a Github-hosted service. Only invented owner lease
records and CI credentials. Public SQL role tests must initialize fm_private_ci
first. Backup files are deleted by TemporaryDirectory. Restored SECURITY
DEFINER functions become superuser-owned with --no-owner: DO NOT EXECUTE them.
"""
from __future__ import annotations

import base64
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from autopilot.ci_protected_pg_boundary import ProtectedMockGateway
from autopilot.private_cloud_recovery_preflight import (
    DOMAIN,MockAuditEvent,ReadinessError,
    build_mock_recovery_manifest,verify_mock_restored_backup,canonical,
)
from autopilot.test_ci_protected_pg_boundary import (
    connect_admin,connect_gateway,
)
from autopilot.test_atomic_mock_inference_fence import kwargs_for
from autopilot.test_owner_provider_lease_gate import NOW,make

SOURCE_DB = "flowminute_fence_ci"
RESTORE_DB = "flowminute_restore_ci"
TEST_ROLE = "flowminute_test"


def _db_rows(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT lease_id,episode_id,day_key,status,token_sha256,"
            "external_anchor_sha256 FROM fm_private_ci.burns ORDER BY lease_id"
        )
        leases=[list(row) for row in cur.fetchall()]
        cur.execute(
            "SELECT event_id,lease_id,event_action,event_at "
            "FROM fm_private_ci.audit_events ORDER BY event_id"
        )
        events=[
            [
                event_id,lease_id,action,created.isoformat()
            ]
            for event_id,lease_id,action,created in cur.fetchall()
        ]
        cur.execute("SELECT day_key,owner_id,burns "
                    "FROM fm_private_ci.day_ledger ORDER BY day_key")
        days=[list(row) for row in cur.fetchall()]
    if not leases or not events or not days:
        raise AssertionError("Expected real mock database content")
    return {"leases":leases,"events":events,"days":days}


def _derive_events(snapshot: dict) -> list[MockAuditEvent]:
    identity={row[0]:row[1] for row in snapshot["leases"]}
    return [
        MockAuditEvent(
            sequence=int(row[0]),
            lease_id=row[1],
            episode_id=identity[row[1]],
            action=row[2],
            value_sha256=sha256(
                canonical({
                    "event_id":row[0],"lease_id":row[1],
                    "event_action":row[2],"event_at":row[3],
                })
            ).hexdigest(),
        )
        for row in snapshot["events"]
    ]


def _cmd(args: list[str], *, private_env: dict) -> None:
    result=subprocess.run(
        args,env=private_env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,timeout=70,check=False,
    )
    if result.returncode:
        # No SQL contents, DSNs or environment variables in public CI logs.
        raise AssertionError(
            "A CI-only PostgreSQL backup or restore command failed: "
            +str(args[0])+" status "+str(result.returncode)
        )


def run_restore_drill() -> dict:
    if (
        os.environ.get("FLOWMINUTE_B3D4C2B3A_ADMIN_DSN","").split("@")[-1]
        != "127.0.0.1:5432/flowminute_fence_ci"
        or os.environ.get("CI") not in ("true","1")
        or os.environ.get("FLOWMINUTE_ENABLE_GEMINI")!="0"
        or os.environ.get("FLOWMINUTE_ENABLE_PUBLISH")!="0"
    ):
        raise AssertionError("Only explicitly disabled-provider disposable CI service allowed")
    import psycopg
    from psycopg import sql

    with connect_admin() as admin:
        with admin.cursor() as cur:
            cur.execute("SELECT current_database(),current_user")
            if tuple(cur.fetchone())!=(SOURCE_DB,TEST_ROLE):
                raise AssertionError("CI source database/user identity changed")
            cur.execute(
                "TRUNCATE fm_private_ci.audit_events,fm_private_ci.burns,"
                "fm_private_ci.day_ledger RESTART IDENTITY CASCADE"
            )
    gateway=ProtectedMockGateway(connect_gateway)
    mock=[make(i) for i in range(3)]
    tickets=[gateway.reserve_synthetic_signed_intent(**kwargs_for(x)) for x in mock]
    gateway.close_mock(
        tickets[0],mock_output_sha256=sha256(b"fixture").hexdigest(),
        structurally_valid=True,now=NOW,
    )
    with connect_admin() as source:
        source_snapshot=_db_rows(source)
    if (
        len(source_snapshot["leases"])!=3
        or len(source_snapshot["events"])!=4
        or source_snapshot["days"][0][2]!=3
    ):
        raise AssertionError("Pre-restore isolated signed fixture missing")

    private_env=dict(os.environ)
    # This is an invented *public CI* password; never a real owner vault secret.
    private_env["PGPASSWORD"]="disposable_ci_service_only"
    client=["-h","127.0.0.1","-p","5432","-U",TEST_ROLE]
    with TemporaryDirectory(prefix="flowminute-ci-unapproved-backup-") as temp:
        backup=Path(temp)/"ci_lease_backup.dump"
        _cmd(
            ["pg_dump",*client,"-d",SOURCE_DB,"--format=custom",
             "--schema=fm_private_ci","--file="+str(backup)],
            private_env=private_env,
        )
        raw=backup.read_bytes()
        if not 3000<len(raw)<=2_000_000:
            raise AssertionError("Actual Postgres custom archive empty or oversized")
        historical_events=_derive_events(source_snapshot)
        manifest=build_mock_recovery_manifest(
            events=historical_events,snapshot_bytes=raw,
            backup_id="mock_ci_postgres_backup",generation=1,
        )
        # The test's independent signer is an ephemeral private KEY created
        # inside this job, NOT the real owner or cloud WORM authority.
        signer=Ed25519PrivateKey.generate()
        public=signer.public_key().public_bytes(
            serialization.Encoding.Raw,serialization.PublicFormat.Raw,
        )
        anchor=sha256(canonical(asdict(manifest))).hexdigest()
        signature=base64.b64encode(
            signer.sign(DOMAIN+bytes.fromhex(anchor))
        ).decode()
        expected=dict(
            manifest=manifest,restored_bytes=raw,
            restored_events=historical_events,parent=None,
            externally_pinned_manifest_sha256=anchor,
            detached_external_signature_b64=signature,
            trusted_external_anchor_public_key_b64=base64.b64encode(public).decode(),
            expected_generation=1,expected_event_count=4,
        )
        receipt=verify_mock_restored_backup(**expected)
        if not receipt["restored_mock_bytes_match_external_signature"]:
            raise AssertionError("Backup archive integrity not checked")
        corrupted=raw[:max(1,len(raw)//2)]+bytes([raw[len(raw)//2]^1])+raw[len(raw)//2+1:]
        try:
            verify_mock_restored_backup(**dict(expected,restored_bytes=corrupted))
        except ReadinessError:
            pass
        else:
            raise AssertionError("Tampered PostgreSQL archive passed external hash")
        # Second database is independent of the source data. Only test
        # bootstrap administrator can create it; no persisted cloud account.
        with psycopg.connect(
            os.environ["FLOWMINUTE_B3D4C2B3A_ADMIN_DSN"],
            autocommit=True,connect_timeout=4,
        ) as admin:
            with admin.cursor() as cur:
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(RESTORE_DB))
                )
        _cmd(
            ["pg_restore",*client,"-d",RESTORE_DB,
             "--no-owner","--no-acl",str(backup)],
            private_env=private_env,
        )
        with psycopg.connect(
            host="127.0.0.1",port=5432,dbname=RESTORE_DB,
            user=TEST_ROLE,password="disposable_ci_service_only",
            connect_timeout=4,
        ) as recovered:
            restored_snapshot=_db_rows(recovered)
        if canonical(source_snapshot)!=canonical(restored_snapshot):
            raise AssertionError("Actual PostgreSQL restored mock audit/day/leases differ")
        if _derive_events(source_snapshot)!=_derive_events(restored_snapshot):
            raise AssertionError("Restored ledger event ordering changed")
        return {
            "status": "REAL_POSTGRES_CI_ARCHIVE_RESTORED_AND_COMPARE_ONLY",
            "archived_bytes":len(raw),
            "archive_sha256":sha256(raw).hexdigest(),
            "rows_restored":len(restored_snapshot["leases"]),
            "audit_events_restored":len(restored_snapshot["events"]),
            "original_day_count":restored_snapshot["days"][0][2],
            "independent_second_test_database_used":True,
            "modified_archive_detected":True,
            "ephemeral_disposable_anchor_signature_verified":True,
            "real_external_worm_backup_anchor_deployed":False,
            "real_private_cloud_persistent_restore_proven":False,
            "private_secrets_or_provider_account_connected":False,
            "provider_live_call_enabled":False,
            "youtube_upload_enabled":False,
            "release_authorized":False,
        }


def main() -> None:
    print(
        "B3D4C2B3B_ACTUAL_CI_POSTGRES_PGDUMP_PGRESTORE_VERIFY_NO_PUBLISH",
        json.dumps(run_restore_drill(),sort_keys=True),
        flush=True,
    )


if __name__=="__main__":
    main()
