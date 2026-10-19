"""Local Unix-domain staging command service: isolated process, NO network API.

This offline prototype owns the SQLite coordinator, signing-key registry and
admin gateway in one *separate* service process. Clients send ONLY a single
bounded, pre-signed JSON command on AF_UNIX. No TCP, HTTP, generic Python,
SQL, arbitrary command, uploads or paid operations are exposed.

OS process separation here does NOT enforce different OS users/file ACLs;
a hostile client running as the same UID can open the DB path if it learns
it. Linux sandboxing, secret management and production cloud identity are
NOT implemented. Never treat this as a deployed secure cloud service.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping
import json
import os
import socket
import socketserver
import stat

from .agent_org import EpisodeSpec, WorkflowError
from .agent_staging_unified import UnifiedStagingCoordinator
from .agent_staging_command_boundary import StagingLocalCommandBoundary

MAX_IPC_FRAME = 8192
MAX_IPC_REPLY = 8192


def _require_socket_path(location: Path) -> Path:
    p=Path(location)
    if (not p.is_absolute() or not p.parent.is_dir()
            or p.parent.is_symlink() or p.exists() or p.is_symlink()
            or len(os.fsencode(p)) >= 99):
        raise WorkflowError("IPC needs a fresh local Unix socket path")
    return p


class _SignedIPCHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.request.settimeout(2.0)
        try:
            payload=self.rfile.readline(MAX_IPC_FRAME + 2)
            if (not payload.endswith(b"\n") or len(payload) > MAX_IPC_FRAME+1):
                raise WorkflowError("Invalid bounded Unix command frame")
            raw=payload[:-1].decode("utf-8",errors="strict")
            result=self.server.command_boundary.execute(raw)
            response={"ok":True,"result":result}
        except (WorkflowError, UnicodeError, ValueError, TypeError,
                OSError, TimeoutError):
            # Never expose role validation diagnostics, file paths,
            # SQLite details, or keys to unauthenticated clients.
            response={"ok":False,"error":"STAGING_COMMAND_DENIED"}
        wire=json.dumps(response,sort_keys=True,separators=(",",":")).encode()
        if len(wire) > MAX_IPC_REPLY:
            wire=b'{"error":"STAGING_REPLY_TOO_LARGE","ok":false}'
        try:
            self.wfile.write(wire+b"\n")
            self.wfile.flush()
        except (OSError, TimeoutError):
            pass


class OfflineStagingIPCService(socketserver.ThreadingMixIn,
                               socketserver.UnixStreamServer):
    """A bounded AF_UNIX request socket owned by the coordinator process."""
    daemon_threads=True
    allow_reuse_address=False
    request_queue_size=4

    def __init__(self,location:Path,
                 boundary:StagingLocalCommandBoundary):
        if not isinstance(boundary,StagingLocalCommandBoundary):
            raise WorkflowError("Signed command boundary is required")
        self.location=_require_socket_path(location)
        self.command_boundary=boundary
        super().__init__(str(self.location),_SignedIPCHandler)
        os.chmod(self.location,0o600)
        saved=self.location.stat()
        self._identity=(saved.st_dev,saved.st_ino)

    def server_close(self) -> None:
        super().server_close()
        try:
            current=self.location.lstat()
            if ((current.st_dev,current.st_ino)==self._identity
                    and stat.S_ISSOCK(current.st_mode)):
                self.location.unlink()
        except FileNotFoundError:
            pass


def serve_offline_staging(db_path:Path,episodes:tuple[EpisodeSpec,...],
                          socket_path:Path,worker_keys:Mapping[str,tuple],
                          admin_id:str,admin_secret:bytes,
                          ready_pipe=None)->None:
    """Separate OS process entrypoint for *offline test harness only*.

    In-memory HMAC keys are passed by the trusted test parent at process
    start; never placed on the socket, in the worker subprocess, or in SQLite.
    """
    try:
        core=UnifiedStagingCoordinator(Path(db_path),episodes=episodes)
        core.reconcile()
        boundary=StagingLocalCommandBoundary(
            core,worker_keys=worker_keys,
            admin_id=admin_id,admin_secret=admin_secret,
        )
        with OfflineStagingIPCService(Path(socket_path),boundary) as service:
            if ready_pipe is not None:
                ready_pipe.send(True)
                ready_pipe.close()
            service.serve_forever(poll_interval=0.05)
    except Exception:
        if ready_pipe is not None:
            try:
                ready_pipe.send(False)
                ready_pipe.close()
            except (BrokenPipeError,EOFError,OSError):
                pass
        raise


def send_signed_ipc(location:Path,command:str)->dict:
    """Send pre-signed staging JSON with no secrets or generic execution."""
    if (type(command) is not str or not 0<len(command.encode("utf-8"))
            <=MAX_IPC_FRAME):
        raise WorkflowError("Signed IPC command too large or malformed")
    location=Path(location)
    if not location.is_absolute():
        raise WorkflowError("Unix staging socket path must be absolute")
    wire=command.encode("utf-8")+b"\n"
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(2)
        client.connect(str(location))
        client.sendall(wire)
        with client.makefile("rb") as response:
            msg=response.readline(MAX_IPC_REPLY+2)
    if not msg.endswith(b"\n") or len(msg)>MAX_IPC_REPLY+1:
        raise WorkflowError("Invalid server reply")
    try:
        parsed=json.loads(msg)
    except (ValueError,UnicodeError) as exc:
        raise WorkflowError("Staging service replied with malformed JSON") from exc
    if (not isinstance(parsed,dict) or parsed.get("ok") is not True
            or set(parsed)!={"ok","result"}
            or not isinstance(parsed["result"],dict)):
        raise WorkflowError("Signed staging command was denied")
    return parsed["result"]
