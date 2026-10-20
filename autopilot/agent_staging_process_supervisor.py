"""Bounded process lifecycle test for FlowMinute draft worker cancellation.

This supervisor runs ONLY the fixed stdlib synthetic probe, no arbitrary
commands, shell, models, media, keys, DB path, YouTube or network. It polls
a live generation-fenced local SQLite task lease while the child runs,
terminates and reaps the child upon cancellation or timeout, and returns
only unverified synthetic status, not a completed task handoff.

It proves cooperative local process control in a no-secrets CI runner,
NOT production distributed cancellation, OS-user security isolation or
safety against malicious descendants that escape their process group.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import threading
import time

from .agent_org import WorkflowError
from .agent_staging_unified import UnifiedStagingCoordinator

PROBE_SCRIPT=Path(__file__).with_name("phase1_synthetic_subprocess.py")


class LocalStagingProcessSupervisor:
    def __init__(self,core:UnifiedStagingCoordinator,*,sandbox:Path):
        self.sandbox=Path(sandbox)
        if (not sys.platform.startswith("linux")
                or not isinstance(core,UnifiedStagingCoordinator)
                or not self.sandbox.is_dir()
                or self.sandbox.is_symlink()
                or not PROBE_SCRIPT.is_file()
                or PROBE_SCRIPT.is_symlink()):
            raise WorkflowError("Offline worker requires safe existing sandbox")
        self.core=core
        self.last_process:subprocess.Popen|None=None

    def run(self,episode_id:str,task_id:str,*,actor:str,generation:int,
            mode:str="brief",duration:float=0.05,
            timeout:float=2.0,started:threading.Event|None=None)->dict:
        if (mode not in ("brief","block","error","tree")
                or type(duration) not in (int,float)
                or not 0<=duration<=2
                or type(timeout) not in (int,float)
                or not 0.1<=timeout<=8
                or (started is not None and not isinstance(started,threading.Event))):
            raise WorkflowError("Unsafe or unbounded offline synthetic worker")
        if not self.core.is_current_worker_lease(
            episode_id,task_id,actor=actor,generation=generation
        ):
            raise WorkflowError("Refusing subprocess without current fenced task")
        # Fixed argv, no shell, no user-supplied executable, no tokens/DB
        # identifiers in environment, and sandbox never contains media.
        argv=[
            sys.executable,"-I","-B",str(PROBE_SCRIPT),
            task_id,mode,str(duration),str(os.getpid()),
        ]
        proc=subprocess.Popen(
            argv,cwd=self.sandbox,
            env={"PYTHONIOENCODING":"utf-8","PYTHONDONTWRITEBYTECODE":"1"},
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,start_new_session=True,
        )
        self.last_process=proc
        if started is not None:
            started.set()
        began=time.monotonic()
        try:
            while proc.poll() is None:
                if not self.core.is_current_worker_lease(
                    episode_id,task_id,actor=actor,generation=generation
                ):
                    raise WorkflowError("Staging lease revoked; worker terminated")
                if time.monotonic()-began>=timeout:
                    raise WorkflowError("Offline worker hit hard execution deadline")
                time.sleep(0.02)
            stdout,stderr=proc.communicate(timeout=0.5)
            if not self.core.is_current_worker_lease(
                episode_id,task_id,actor=actor,generation=generation
            ):
                raise WorkflowError("Staging lease lost before accepting output")
            if (proc.returncode!=0 or stderr
                    or len(stdout.encode("utf-8"))>1024):
                raise WorkflowError("Synthetic worker failed or produced excess output")
            try:
                result=json.loads(stdout)
            except (ValueError,UnicodeError) as exc:
                raise WorkflowError("Synthetic worker returned invalid JSON") from exc
            if (not isinstance(result,dict)
                    or result!={ "kind":"SYNTHETIC_STAGING_PROBE",
                                  "task_id":task_id,
                                  "marker_sha256":sha256(task_id.encode()).hexdigest(),
                                  "publishing_authorized":False}):
                raise WorkflowError("Synthetic worker output scope mismatch")
            return {
                "local_synthetic_child_exited":True,
                "task_id":task_id,
                "generation":generation,
                "staging_probe_sha256":result["marker_sha256"],
                "task_completed_in_coordinator":False,
                "video_rendered":False,
                "youtube_publishing_authorized":False,
            }
        finally:
            if proc.poll() is None:
                # New Linux session/process group is anchored at this
                # not-yet-reaped child's PID. Never signal an arbitrary PID
                # provided by an agent; fixed child can only spawn a fixed
                # synthetic grandchild in the same process group.
                try:
                    os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                # Fail closed if a peer left pipes open unexpectedly.
                try:
                    os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.kill()
                proc.communicate(timeout=2)
