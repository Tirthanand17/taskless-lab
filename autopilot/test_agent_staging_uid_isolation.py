"""Linux separate-UID permission proof on a disposable no-secret runner.

ONLY the dedicated existing GitHub CI sudo step executes this test as root
to set temporary numeric POSIX worker and service identities. This test does
NOT add users, system accounts, sudoers entries, network ports, services,
paid runners, production files, or any local-user-machine action.

Regular unit tests skip this privileged test. The sudo CI step runs only
on pushes to the authorized public draft branch and receives NO secrets.
"""
from __future__ import annotations

from datetime import timedelta
from multiprocessing import get_context
from pathlib import Path
from secrets import token_bytes
from tempfile import TemporaryDirectory
from dataclasses import asdict
import grp
import json
import os
import pwd
import shutil
import stat
import subprocess
import sys
import unittest

from autopilot.agent_org import EpisodeSpec, WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator
from autopilot.agent_staging_admin_gateway import (
    SignedStagingAdminCommand, sign_admin_command,
)
from autopilot.agent_staging_auth_gateway import (
    SignedStagingRequest, sign_staging_request,
)
from autopilot.agent_staging_ipc_service import serve_offline_staging
from autopilot.agent_staging_command_boundary import SQLiteHostClock

IPCCLIENT=Path(__file__).with_name("phase1_synthetic_ipc_client.py")
DENYPROBE=Path(__file__).with_name("phase1_synthetic_db_denial.py")


def _ephemeral_numeric_ids() -> tuple[int,int,int]:
    """Pick unused high numeric UID/GIDs; never create or modify accounts."""
    choices=[]
    for value in range(61000,61500):
        try:
            pwd.getpwuid(value)
            continue
        except KeyError:
            pass
        try:
            grp.getgrgid(value)
            continue
        except KeyError:
            pass
        choices.append(value)
        if len(choices)==3:
            break
    if len(choices)!=3:
        raise RuntimeError("No unused numeric test IDs")
    return tuple(choices)


def _run_as_service(db,episodes,socket_path,registry,admin,secret,ready,uid,gid):
    """Drop from CI-root harness to the isolated test service identity."""
    os.setgroups([])
    os.setgid(gid)
    os.setuid(uid)
    serve_offline_staging(
        db,episodes,socket_path,registry,admin,secret,ready,
        socket_group_gid=gid,
    )


@unittest.skipUnless(sys.platform.startswith("linux") and os.geteuid()==0,
                     "Explicit Linux root-only disposable CI isolation proof")
class DistinctUIDStagingTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        # Root test harness is NOT worker: allow traversal to public socket
        # directory while preserving private DB directory mode 0700.
        self.root.chmod(0o755)
        self.service_uid,self.worker_uid,self.outsider_uid=_ephemeral_numeric_ids()
        self.group_gid=self.worker_uid
        self.dbdir=self.root/"db"
        self.ipcdir=self.root/"ipc"
        self.publicdir=self.root/"client"
        self.dbdir.mkdir(mode=0o700)
        self.ipcdir.mkdir(mode=0o710)
        self.publicdir.mkdir(mode=0o755)
        self.db=self.dbdir/"unified.sqlite3"
        self.sock=self.ipcdir/"task.sock"
        self.episodes=(EpisodeSpec("uid_case_001","short","hi",90),)
        self.core=UnifiedStagingCoordinator(
            self.db,episodes=self.episodes,create=True,
        )
        self.core.reconcile()
        self.db.chmod(0o600)
        os.chown(self.db,self.service_uid,self.service_uid)
        os.chown(self.dbdir,self.service_uid,self.service_uid)
        os.chown(self.ipcdir,self.service_uid,self.group_gid)
        self.dbdir.chmod(0o700)
        self.ipcdir.chmod(0o710)
        shutil.copyfile(IPCCLIENT,self.publicdir/"client.py")
        shutil.copyfile(DENYPROBE,self.publicdir/"deny.py")
        for filename in ("client.py","deny.py"):
            (self.publicdir/filename).chmod(0o644)
        self.worker_key=token_bytes(32)
        self.admin_key=token_bytes(32)
        self.worker_id="worker_research"
        self.admin_id="admin_flowminute"
        self.actor="research.launch_researcher"
        self.key_id="key_research_001"
        self.process=None
        self._start_service()
        self.addCleanup(self._stop_service)

    def _start_service(self):
        ctx=get_context("fork")
        receiving,sending=ctx.Pipe(duplex=False)
        self.process=ctx.Process(
            target=_run_as_service,
            args=(
                self.db,self.episodes,self.sock,
                {self.worker_id:(self.actor,self.key_id,self.worker_key)},
                self.admin_id,self.admin_key,sending,
                self.service_uid,self.group_gid,
            ),
        )
        self.process.start()
        sending.close()
        ready=receiving.poll(8)
        ok=receiving.recv() if ready else False
        receiving.close()
        if not ok:
            self._stop_service()
        self.assertTrue(ok,"Separate-UID offline service failed to start")

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
        self.sock.unlink(missing_ok=True)

    def _invoke_as(self,uid:int,gid:int,script:Path,*
                   args:tuple[str,...]=(),stdin:str="")->subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable,"-I","-B",str(script),*args],
            input=stdin,text=True,capture_output=True,timeout=5,
            cwd=self.publicdir,
            env={"PYTHONIOENCODING":"utf-8","PYTHONDONTWRITEBYTECODE":"1"},
            user=uid,group=gid,extra_groups=(),
        )

    def _admin_command(self)->str:
        expiry=int((SQLiteHostClock(self.core).now()+
                    timedelta(seconds=60)).timestamp())
        signed=sign_admin_command(
            SignedStagingAdminCommand(
                self.admin_id,"enroll",self.worker_id,self.actor,
                self.key_id,"","admin_uid_enroll_0001",expiry,
            ),secret=self.admin_key,
        )
        return json.dumps({
            "action":"admin.apply","signed":asdict(signed),"handoff":None
        },sort_keys=True,separators=(",",":"))+"\n"

    def _worker_command(self)->str:
        expiry=int((SQLiteHostClock(self.core).now()+
                    timedelta(seconds=60)).timestamp())
        signed=sign_staging_request(
            SignedStagingRequest(
                self.worker_id,"claim","uid_case_001",
                "uid_case_001:research",0,expiry,120,
                "","",self.key_id,
            ),key=self.worker_key,
        )
        return json.dumps({
            "action":"worker.claim","signed":asdict(signed),"handoff":None
        },sort_keys=True,separators=(",",":"))+"\n"

    def test_worker_reads_no_database_but_executes_signed_socket_claim(self):
        self.assertEqual(os.geteuid(),0)
        self.assertNotEqual(self.service_uid,self.worker_uid)
        self.assertEqual(stat.S_IMODE(self.sock.stat().st_mode),0o660)
        self.assertEqual(self.sock.stat().st_uid,self.service_uid)
        self.assertEqual(self.sock.stat().st_gid,self.group_gid)
        denial=self._invoke_as(
            self.worker_uid,self.group_gid,self.publicdir/"deny.py",
            args=(str(self.db),),
        )
        self.assertEqual(denial.returncode,0,denial.stderr)
        signed_admin=self._invoke_as(
            self.worker_uid,self.group_gid,self.publicdir/"client.py",
            args=(str(self.sock),),stdin=self._admin_command(),
        )
        self.assertEqual(signed_admin.returncode,0,signed_admin.stderr)
        signed_task=self._invoke_as(
            self.worker_uid,self.group_gid,self.publicdir/"client.py",
            args=(str(self.sock),),stdin=self._worker_command(),
        )
        self.assertEqual(signed_task.returncode,0,signed_task.stderr)
        self.assertEqual(json.loads(signed_task.stdout)["generation"],1)
        self.assertEqual(self.core.report()["running_tasks"],1)
        self.assertFalse(self.core.report()["publish_enabled"])

    def test_unrelated_linux_uid_cannot_open_socket_or_database(self):
        forbidden_db=self._invoke_as(
            self.outsider_uid,self.outsider_uid,
            self.publicdir/"deny.py",args=(str(self.db),),
        )
        self.assertEqual(forbidden_db.returncode,0,forbidden_db.stderr)
        forbidden_socket=self._invoke_as(
            self.outsider_uid,self.outsider_uid,
            self.publicdir/"client.py",args=(str(self.sock),),
            stdin=self._worker_command(),
        )
        self.assertNotEqual(forbidden_socket.returncode,0)
        self.assertEqual(self.core.report()["running_tasks"],0)
        self.assertFalse(self.core.report()["publish_enabled"])


if __name__=="__main__":
    unittest.main()
