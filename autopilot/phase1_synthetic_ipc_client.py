"""Fixed unprivileged-style local socket CLIENT test; not a live agent.

Reads one PRE-SIGNED JSON command from stdin, not secret keys or DB paths.
Only a Unix socket path is provided. Executes no arbitrary user program.
This client runs under the same test OS UID and is not an OS-security proof.
"""
from __future__ import annotations
import json
from pathlib import Path
import socket
import sys

def main()->int:
    if len(sys.argv)!=2 or not sys.platform.startswith("linux"):
        return 2
    payload=sys.stdin.buffer.read(8194)
    if not payload.endswith(b"\n") or len(payload)>8193:
        return 2
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(2)
        client.connect(str(Path(sys.argv[1])))
        client.sendall(payload)
        output=b""
        while b"\n" not in output and len(output)<8193:
            piece=client.recv(2048)
            if not piece:
                break
            output+=piece
    if not output.endswith(b"\n") or len(output)>8193:
        return 3
    reply=json.loads(output)
    if not isinstance(reply,dict) or reply.get("ok") is not True:
        return 4
    print(json.dumps(reply["result"],sort_keys=True,separators=(",",":")))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
