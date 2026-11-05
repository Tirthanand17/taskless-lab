"""No-network subprocess worker cancellation checks on disposable CI."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic, sleep
import os
import subprocess
import sys
import unittest

from autopilot.agent_org import EpisodeSpec,Handoff,WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator
from autopilot.agent_staging_command_boundary import SQLiteHostClock
from autopilot.agent_staging_process_supervisor import LocalStagingProcessSupervisor

FIXTURE=Path(__file__).with_name("phase1_synthetic_supervisor_crash.py")


def _linux_pid_running(pid):
    """A kill can leave a briefly unreaped zombie, which is not executing."""
    stat=Path("/proc")/str(pid)/"stat"
    try:
        fields=stat.read_text().split(") ",1)[1].split()
        return bool(fields) and fields[0] not in ("Z","X","x")
    except (FileNotFoundError,ProcessLookupError):
        return False



class LocalWorkerProcessTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        parent=Path(tmp.name)
        self.sandbox=parent/"child_workspace"
        self.sandbox.mkdir()
        self.eid="worker_probe_01"
        self.episodes=(EpisodeSpec(self.eid,"short","en",95),)
        self.core=UnifiedStagingCoordinator(
            parent/"staging.sqlite3",episodes=self.episodes,create=True
        )
        self.core.reconcile()
        self.clock=SQLiteHostClock(self.core)
        self.supervisor=LocalStagingProcessSupervisor(
            self.core,sandbox=self.sandbox
        )
        self.research=self.eid+":research"
        self.actor="research.launch_researcher"

    def claim(self,stage,actor,*,lease=30):
        return self.core.claim(
            self.eid,stage,actor=actor,now=None,lease_seconds=lease
        )

    def complete_stage(self,stage,actor,generation,parents=()):
        contract=self.core.contracts[self.eid][stage]
        digest=sha256(stage.encode()).hexdigest()
        refs=tuple("sha256:"+item for item in parents)+("sha256:"+digest,)
        h=Handoff(stage,contract.produces,digest,refs,
                  actor,self.clock.now().isoformat())
        self.core.complete(
            self.eid,h,actor=actor,generation=generation,now=None
        )
        return digest

    def ready_parallel(self):
        g=self.claim(self.research,self.actor)
        d=self.complete_stage(self.research,self.actor,g)
        review=self.eid+":fact_review"
        role=self.core.contracts[self.eid][review].owner
        g=self.claim(review,role)
        self.complete_stage(review,role,g,(d,))
        return self.eid+":script",self.eid+":hooks"

    def test_normal_child_exits_and_never_completes_staging_task(self):
        g=self.claim(self.research,self.actor)
        result=self.supervisor.run(
            self.eid,self.research,actor=self.actor,generation=g,
            mode="brief",duration=0.02,
        )
        self.assertTrue(result["local_synthetic_child_exited"])
        self.assertFalse(result["task_completed_in_coordinator"])
        self.assertFalse(result["video_rendered"])
        self.assertFalse(result["youtube_publishing_authorized"])
        self.assertIsNotNone(self.supervisor.last_process.poll())
        self.assertEqual(self.core.report()["running_tasks"],1)
        self.assertEqual(list(self.sandbox.iterdir()),[])

    def test_stale_generation_rejected_before_child_start(self):
        with self.assertRaises(WorkflowError):
            self.supervisor.run(
                self.eid,self.research,actor=self.actor,generation=1
            )
        self.assertIsNone(self.supervisor.last_process)
        self.assertFalse(self.core.report()["publish_enabled"])

    def test_failed_task_revokes_running_child_and_reaps_process(self):
        g=self.claim(self.research,self.actor)
        started=Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut=pool.submit(
                self.supervisor.run,self.eid,self.research,
                actor=self.actor,generation=g,mode="block",
                timeout=5.0,started=started,
            )
            self.assertTrue(started.wait(2))
            self.core.fail(
                self.eid,self.research,actor=self.actor,generation=g,
                now=None,category="PROBE_RETRY"
            )
            with self.assertRaises(WorkflowError):
                fut.result(timeout=3)
        self.assertIsNotNone(self.supervisor.last_process.poll())
        self.assertEqual(self.core.report()["running_tasks"],0)
        self.assertFalse(self.core.report()["publish_enabled"])

    def test_parallel_sibling_cancellation_triggers_real_child_kill(self):
        script,hooks=self.ready_parallel()
        actor=self.core.contracts[self.eid][hooks].owner
        g=self.claim(hooks,actor)
        started=Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            f=pool.submit(
                self.supervisor.run,self.eid,hooks,
                actor=actor,generation=g,mode="block",timeout=5.0,
                started=started,
            )
            self.assertTrue(started.wait(2))
            script_owner=self.core.contracts[self.eid][script].owner
            for _ in range(3):
                token=self.claim(script,script_owner)
                self.core.fail(
                    self.eid,script,actor=script_owner,generation=token,
                    now=None,category="PROBE_RETRY"
                )
            with self.assertRaises(WorkflowError):
                f.result(timeout=3)
        self.assertIsNotNone(self.supervisor.last_process.poll())
        outcome=self.core.report()
        self.assertEqual(outcome["quarantined"],[self.eid])
        self.assertEqual(outcome["running_tasks"],0)
        self.assertFalse(outcome["publish_enabled"])

    def test_cancelled_worker_kills_fixed_descendant_in_same_group(self):
        if not sys.platform.startswith("linux"):
            self.skipTest("Linux-only process-group test")
        g=self.claim(self.research,self.actor)
        started=Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            result=pool.submit(
                self.supervisor.run,self.eid,self.research,
                actor=self.actor,generation=g,mode="tree",
                timeout=5.0,started=started,
            )
            self.assertTrue(started.wait(2))
            proc=self.supervisor.last_process
            child_line=proc.stdout.readline().strip()
            self.assertTrue(child_line.startswith("CHILD_PID:"))
            grandchild=int(child_line.split(":",1)[1])
            self.assertTrue(_linux_pid_running(grandchild))
            self.core.fail(
                self.eid,self.research,actor=self.actor,generation=g,
                now=None,category="PROBE_RETRY",
            )
            with self.assertRaises(WorkflowError):
                result.result(timeout=3)
        self.assertIsNotNone(self.supervisor.last_process.poll())
        for _ in range(50):
            if not _linux_pid_running(grandchild):
                break
            sleep(0.02)
        self.assertFalse(_linux_pid_running(grandchild))
        self.assertFalse(self.core.report()["publish_enabled"])

    def test_parent_crash_stops_child_without_monitor_polling(self):
        if not sys.platform.startswith("linux"):
            self.skipTest("Linux-only parent death test")
        proc=subprocess.run(
            [sys.executable,"-I","-B",str(FIXTURE)],
            capture_output=True,text=True,timeout=4,
            env={"PYTHONIOENCODING":"utf-8","PYTHONDONTWRITEBYTECODE":"1"},
        )
        self.assertEqual(proc.returncode,0,proc.stderr)
        pid=int(proc.stdout.strip())
        for _ in range(75):
            if not _linux_pid_running(pid):
                break
            sleep(0.02)
        self.assertFalse(_linux_pid_running(pid))
        self.assertFalse(self.core.report()["publish_enabled"])

    def test_execution_deadline_terminates_unresponsive_child(self):
        g=self.claim(self.research,self.actor)
        before=monotonic()
        with self.assertRaises(WorkflowError):
            self.supervisor.run(
                self.eid,self.research,actor=self.actor,generation=g,
                mode="block",timeout=0.15,
            )
        self.assertLess(monotonic()-before,3.0)
        self.assertIsNotNone(self.supervisor.last_process.poll())
        self.assertFalse(self.core.report()["publish_enabled"])

    def test_child_failure_is_not_reported_as_success(self):
        g=self.claim(self.research,self.actor)
        with self.assertRaises(WorkflowError):
            self.supervisor.run(
                self.eid,self.research,actor=self.actor,generation=g,
                mode="error",duration=0,
            )
        self.assertIsNotNone(self.supervisor.last_process.poll())
        self.assertEqual(self.core.report()["completed_tasks"],0)

    def test_unsupported_command_and_missing_safe_sandbox_denied(self):
        g=self.claim(self.research,self.actor)
        for mode in ("upload","publish","shell"):
            with self.subTest(mode=mode),self.assertRaises(WorkflowError):
                self.supervisor.run(
                    self.eid,self.research,actor=self.actor,generation=g,
                    mode=mode,
                )
        with self.assertRaises(WorkflowError):
            LocalStagingProcessSupervisor(self.core,sandbox=self.sandbox/"not_found")
        self.assertEqual(self.core.report()["completed_tasks"],0)


if __name__=="__main__":
    unittest.main()
