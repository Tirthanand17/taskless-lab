"""Process-separated AF_UNIX staging service with HMAC-only client calls."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import timedelta
from hashlib import sha256
from multiprocessing import get_context
from pathlib import Path
from secrets import token_bytes
from tempfile import TemporaryDirectory
import json
import os
import sqlite3
import stat
import subprocess
import sys
import unittest

from autopilot.agent_org import EpisodeSpec,Handoff,WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator
from autopilot.agent_staging_command_boundary import SQLiteHostClock
from autopilot.agent_staging_auth_gateway import (
    SignedStagingRequest,sign_staging_request,handoff_digest
)
from autopilot.agent_staging_admin_gateway import (
    SignedStagingAdminCommand,sign_admin_command
)
from autopilot.agent_staging_ipc_service import (
    OfflineStagingIPCService,serve_offline_staging,send_signed_ipc,
    preflight_offline_staging,
)

CLIENT_PROBE=Path(__file__).with_name("phase1_synthetic_ipc_client.py")


@unittest.skipUnless(sys.platform.startswith("linux"),"Linux CI IPC proof only")
class StagingIPCBoundaryTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir=Path(tmp.name)
        self.db=self.dir/"staging.sqlite3"
        self.socket=self.dir/"staging.sock"
        self.episodes=(EpisodeSpec("ipc_video_01","short","en",88),)
        self.core=UnifiedStagingCoordinator(
            self.db,episodes=self.episodes,create=True
        )
        self.core.reconcile()
        self.worker_key=token_bytes(32)
        self.admin_secret=token_bytes(32)
        self.worker="worker_research"
        self.role="research.launch_researcher"
        self.key_id="key_research_001"
        self.admin="admin_flowminute"
        self.ep="ipc_video_01"
        self.task=self.ep+":research"
        self.process=None
        self._start_service()

    def _start_service(self):
        ctx=get_context("spawn")
        receiving,sending=ctx.Pipe(duplex=False)
        self.process=ctx.Process(
            target=serve_offline_staging,
            args=(
                self.db,self.episodes,self.socket,
                {self.worker:(self.role,self.key_id,self.worker_key)},
                self.admin,self.admin_secret,sending,
            ),
        )
        self.process.start()
        sending.close()
        success=receiving.poll(8)
        result=receiving.recv() if success else False
        receiving.close()
        if not result:
            self._stop_service()
        self.assertTrue(result,"offline IPC service failed to become ready")
        self.addCleanup(self._stop_service)

    def _stop_service(self):
        if self.process is not None:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=3)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=3)
            self.process.close()
            self.process=None
        if self.socket.exists() or self.socket.is_symlink():
            self.socket.unlink()

    def _now(self):
        return SQLiteHostClock(self.core).now()

    def _send(self,action,signed,handoff=None):
        payload=json.dumps({
            "action":action,"signed":asdict(signed),
            "handoff":asdict(handoff) if handoff is not None else None,
        },sort_keys=True,separators=(",",":"))
        return send_signed_ipc(self.socket,payload)

    def _enroll(self,nonce="admin_ipc_enroll_001"):
        command=SignedStagingAdminCommand(
            self.admin,"enroll",self.worker,self.role,
            self.key_id,"",nonce,int((self._now()+timedelta(seconds=60)).timestamp())
        )
        signed=sign_admin_command(command,secret=self.admin_secret)
        return self._send("admin.apply",signed)

    def _claim(self,*,generation=0):
        request=SignedStagingRequest(
            self.worker,"claim",self.ep,self.task,generation,
            int((self._now()+timedelta(seconds=60)).timestamp()),
            120,"","",self.key_id,
        )
        return sign_staging_request(request,key=self.worker_key)

    def _output(self):
        digest=sha256(self.task.encode()).hexdigest()
        return Handoff(self.task,"research.package",digest,
                       ("sha256:"+digest,),self.role,self._now().isoformat())

    def test_crashed_worker_lease_recovered_before_socket_accepts_claim(self):
        self._enroll()
        # At the first service restart, the original claimed worker is no
        # longer alive. Simulate a lease that expired while the service was
        # offline, without sleeping or altering the machine clock.
        self._stop_service()
        generation=self.core.claim(
            self.ep,self.task,actor=self.role,now=None,
            lease_seconds=10,expected_generation=0,
        )
        self.assertEqual(generation,1)
        # Unit-test-only crash/time passage fixture: backdate the running
        # lease, NOT the coordinator's monotonic clock. This models a
        # worker lease that actually expired while service was offline.
        with sqlite3.connect(self.db) as db:
            db.execute(
                "UPDATE stage_tasks SET expires="
                "CAST(strftime('%s','now') AS INTEGER)-1 "
                "WHERE episode=? AND task_id=?",
                (self.ep,self.task),
            )
            db.commit()
        self.assertEqual(self.core.report()["running_tasks"],1)
        self._start_service()
        self.assertEqual(self.core.report()["running_tasks"],0)
        new_token=self._send("worker.claim",self._claim(generation=2))
        self.assertEqual(new_token["generation"],3)
        self.assertEqual(self.core.report()["running_tasks"],1)
        # A second preflight does not charge the now live claim a failure.
        safe=preflight_offline_staging(self.core)
        self.assertEqual(safe["expired_lease_count"],0)
        self.assertFalse(safe["publishing_authorized"])

    def test_preflight_rejects_future_clock_without_opening_socket(self):
        self._stop_service()
        with sqlite3.connect(self.db) as db:
            db.execute(
                "UPDATE queue_policy SET last_now = "
                "CAST(strftime('%s','now') AS INTEGER) + 86400"
            )
            db.commit()
        with self.assertRaises(AssertionError):
            self._start_service()
        self.assertFalse(self.socket.exists())

    def test_preflight_rejects_corrupt_task_inventory_before_admission(self):
        self._stop_service()
        with sqlite3.connect(self.db) as db:
            db.execute(
                "UPDATE stage_tasks SET owner='unauthorized_actor' "
                "WHERE task_id=?",(self.task,)
            )
            db.commit()
        with self.assertRaises(AssertionError):
            self._start_service()
        self.assertFalse(self.socket.exists())

    def test_preflight_fences_third_expired_claim_before_next_video_admitted(self):
        # Test the full atomic quarantine handoff with two videos using a
        # separate private database and no extra process/subprocess.
        with TemporaryDirectory() as d:
            path=Path(d)/"recovery.sqlite3"
            specs=(
                EpisodeSpec("recover_one_01","short","hi",99),
                EpisodeSpec("recover_two_02","short","en",98),
            )
            core=UnifiedStagingCoordinator(path,episodes=specs,create=True)
            core.reconcile()
            task="recover_one_01:research"
            actor="research.launch_researcher"
            old=SQLiteHostClock(core).now()-timedelta(seconds=40)
            for i in range(2):
                at=old+timedelta(seconds=i*4)
                gen=core.claim("recover_one_01",task,actor=actor,now=at)
                core.fail("recover_one_01",task,actor=actor,generation=gen,
                          now=at+timedelta(seconds=1),category="CRASH_RETRY")
            final_gen=core.claim("recover_one_01",task,actor=actor,
                                 now=old+timedelta(seconds=9),
                                 lease_seconds=10)
            self.assertEqual(final_gen,5)
            recovered=preflight_offline_staging(core)
            self.assertEqual(recovered["expired_lease_count"],1)
            state=core.report()
            self.assertEqual(state["quarantined"],["recover_one_01"])
            self.assertEqual(state["active"],["recover_two_02"])
            self.assertEqual(state["running_tasks"],0)
            self.assertFalse(state["publish_enabled"])
            self.assertEqual(
                preflight_offline_staging(core)["expired_lease_count"],0
            )

    def test_restricted_local_socket_with_no_tcp_or_secrets(self):
        mode=self.socket.stat().st_mode
        self.assertTrue(stat.S_ISSOCK(mode))
        self.assertEqual(stat.S_IMODE(mode),0o600)
        self.assertFalse(self.core.report()["publish_enabled"])
        outcome=self._enroll()
        self.assertFalse(outcome["publish_enabled"])
        self.assertEqual(outcome["admin_outcome"]["key_generation"],1)

    def test_signed_worker_claim_completion_replay_and_service_restart(self):
        self._enroll()
        grant=self._send("worker.claim",self._claim())
        self.assertEqual(grant["generation"],1)
        h=self._output()
        signed=sign_staging_request(
            SignedStagingRequest(
                self.worker,"complete",self.ep,self.task,1,
                int((self._now()+timedelta(seconds=60)).timestamp()),0,
                handoff_digest(h),"signed_ipc_receipt_001",self.key_id,
            ),key=self.worker_key,
        )
        first=self._send("worker.complete",signed,h)
        self.assertEqual(first["outcome"]["completed_tasks"],1)
        self._stop_service()
        self._start_service()
        self.assertEqual(self._send("worker.complete",signed,h),first)
        self.assertEqual(self.core.report()["completed_tasks"],1)

    def test_unsigned_or_publish_command_return_generic_denial(self):
        self._enroll()
        for payload in (
            '{"action":"publish_video","signed":{},"handoff":null}',
            '{"action":"worker.claim","signed":{},"handoff":null}',
            '{"action":"worker.claim","signed":{},"handoff":null,"sql":"DROP"}',
        ):
            with self.subTest(payload=payload),self.assertRaises(WorkflowError):
                send_signed_ipc(self.socket,payload)
        self.assertEqual(self.core.report()["running_tasks"],0)

    def test_concurrent_socket_clients_claim_only_once(self):
        self._enroll()
        signed=self._claim()
        def attempt(_):
            try:
                return self._send("worker.claim",signed)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(attempt,range(3)))
        self.assertEqual(sum(v is not None for v in results),1)
        self.assertEqual(self.core.report()["running_tasks"],1)

    def test_fixed_client_process_gets_only_signed_command_no_db_credential(self):
        self._enroll()
        command=json.dumps({
            "action":"worker.claim","signed":asdict(self._claim()),
            "handoff":None,
        },sort_keys=True,separators=(",",":"))+"\n"
        client=subprocess.run(
            [sys.executable,"-I","-B",str(CLIENT_PROBE),str(self.socket)],
            input=command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,timeout=5,cwd=self.dir,
            env={"PYTHONIOENCODING":"utf-8","PYTHONDONTWRITEBYTECODE":"1"},
        )
        self.assertEqual(client.returncode,0,client.stderr)
        self.assertEqual(json.loads(client.stdout)["generation"],1)
        self.assertNotIn(str(self.db),command)
        self.assertNotIn(self.worker_key.hex(),command)
        self.assertFalse(self.core.report()["publish_enabled"])

    def test_service_crash_does_not_silently_report_completed_work(self):
        self._enroll()
        self._stop_service()
        with self.assertRaises((WorkflowError,OSError,ConnectionError)):
            self._send("worker.claim",self._claim())
        self.assertEqual(self.core.report()["running_tasks"],0)
        self._start_service()
        self.assertEqual(self._send("worker.claim",self._claim())["generation"],1)


if __name__=="__main__":
    unittest.main()
