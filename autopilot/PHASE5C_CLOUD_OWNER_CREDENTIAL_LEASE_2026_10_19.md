# Phase 5C — Cloud owner read-only credential lease integration (19 October 2026)

**Source:** Existing public draft PR #5, branch `feature/flowminute-phase2-evidence-preflight`. **No cloud deployment or live provider authorization.** The credential custodianship is an **injection contract**, not a connected service.

## Problem solved in source

- Phase 5A could read the exact owner-channel, three-slot YouTube state using an access token but had no contract for obtaining that token from an isolated secret store.
- Phase 5B could screen strict OAuth lifetime, scopes, and ₹0 cost claim metadata, but had no link to the owner readback.
- Phase 5C's `autopilot/phase5c_cloud_owner_probe.py` connects those two staging modules: it accepts *sanitized OAuth and zero-cost claims*, validates the entire manifest **before** requesting a token, denies missing privileges before access, and calls a narrow `provider.borrow_readonly(channel_id, scope)` context manager.
- It reads only the FlowMinute owner channel and optional existing three video IDs. The token stays inside the lease context, and is never written to JSON, logs, a public repository, or a durable database. Exception messages from the credential provider are redacted. A lease must close after success, invalid input or reader exceptions.
- Output includes sanitized per-slot statuses without video ID, private titles or token values. A technically valid owner read is deliberately labelled `OWNER_READ_OBSERVED_UNATTESTED`, never a production attestation. Even all three reads succeeding cannot enable uploads or scheduling.

## Safety and integration requirements

Production-only adapter must be independently connected/approved and prove origin, isolated execution, encryption, short-lived access-token handling, expiration, secure refresh policy, owner channel identity, revoke/rotation, audit trail, scoped access, and a hard ₹0 no-overage budget. **No such adapter is installed here.**

No new Cloudflare service, D1 mutation, OAuth grant, R2 account, provider charge, Nirala access, private GitHub Actions secrets, YouTube upload or schedule in this implementation. Public CI uses synthetic tokens and fake account responses ONLY.

### Regression and next acceptance

`python -m unittest autopilot.test_phase5c_cloud_owner_probe -v`

Tests cover two-of-three and three-of-three local fake results, missing assets, provider failure with secrets in exceptions, bad/expired access token claims, consent Testing mode, wrong budget/laptop policy, manifest injection, duplicate video ID, lease release on error, and no false publication permission.

**Do not treat this component as confirmation that the real long video was scheduled**; the long video still requires separate authenticated owner readback. Phase 5 still awaits approved live integration, and total accepted major phases stay 2/8 (25%). Original 21 live acceptance subphases stay open.
