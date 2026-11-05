# FlowMinute Lab — Separate-process local Unix command service (no deployment)

**19 Oct 2026 | Public DRAFT PR #5 | Local no-network IPC proof only**

## What materially changes

The previous authenticated staging command gateway lived in the exact same Python process as its users. There was no proof that a client could submit signed tasks without receiving a coordinator object, raw key-registration map, or a database handle.

`autopilot/agent_staging_ipc_service.py` offers a *local Linux AF_UNIX service* designed to run in a **separate OS process**. That process alone instantiates the existing one-database coordinator, HMAC worker-key registry, signed administrator and exact three-route `StagingLocalCommandBoundary`. Remote-style clients receive a **Unix socket path only**, send exactly one UTF-8 newline-delimited signed command (≤8 KiB), and receive a bounded JSON response. Unknown operations, unsigned payloads and malformed JSON receive a single redacted `STAGING_COMMAND_DENIED` response, without stack traces, DB details or raw secrets. The socket is created in an existing non-symlink local directory, refused if preexisting, and restricted to file mode **0600**. No TCP listener, HTTP server, outbound web traffic, YouTube API, billing, arbitrary shell, file or production release API is added.

New `autopilot/phase1_synthetic_ipc_client.py` is a fixed subprocess that reads a **pre-signed** worker claim through stdin and communicates with the local socket without a signing key, service configuration, SQLite path or OAuth credential. Offline CI uses Python multiprocessing `spawn` to start an actual separate coordinator-service process and exercises signed admin enrollment, signed worker claim, exact-Handoff completion with durable receipt replay after killing/restarting the service, rejected unsigned/publishing commands, three competing socket clients racing for the same lease, fixed worker client subprocess with scrubbed environment, and a service crash that must never falsely report a successful stage.

## What this does NOT prove

The service and test client still run under the SAME Linux user, so a hostile worker could open the local DB by learning its path or bypass the socket's policy through file access. A mode 0600 socket proves access for that user only, **not protection against other processes of the same UID**. Production needs process/container isolation with separate Linux users, hardened DB ACLs or remote storage exclusively owned by the service, externally attested trusted clock, host/secret manager, authenticated TLS ingress, durable event/cancellation signalling and a real cloud deployment review. Client process having no key in argv/env is not proof no key could leak through some future application. There is NO continuously running worker service in the user's account, no Cloudflare D1, OAuth/YouTube connection, uploaded media or real generated narration, and no persistent production queue. The original release ledger PR #4 is unchanged.

Original **21 tracked production acceptance subphases across six major incomplete phases OPEN**. PR #4/#5 remain DRAFT/unmerged, no Nirala access, no new external service or billable resource, ₹0 recurring monthly budget unchanged.
