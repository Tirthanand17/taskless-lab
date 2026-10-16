# FlowMinute Autopilot — gated v1 prototype

This **is not a deployed or continuously running agent yet**. It is an isolated, standard-library **control-plane foundation** for the already working Remotion/FFmpeg/YouTube systems.

Implemented here:
- Explicit 11:00, 16:00 and 20:30 IST release slot conversion and no scheduling in the past.
- Editorial candidate novelty/benefit/source checks.
- Media quality gates covering hash, format, caption verification, rights, source facts, audio and thumbnail.
- Approved provider routing with budget limits, 403 disable, 429 cooling-off and no provider/account limit evasion.
- Durable SQLite reservations with UNIQUE media/time constraints and irreversible fail-closed YouTube transitions, so uncertain uploads are never silently repeated.

Not implemented yet: live research connectors, actual quality scoring/forced word-alignment, YouTube adapter, Releases/object storage, cloud runtime, end-to-end unattended production, analytics optimizer, dashboards or alert delivery. **Do not connect a secret-bearing runner to this public repository.**

Run:
    python -m unittest discover -s autopilot -p 'test_*.py' -v

Follow docs/FLOWMINUTE_AUTOPILOT_ARCHITECTURE.md for deployment plan and security safeguards. Existing October 16 scheduled/active jobs are untouched.
