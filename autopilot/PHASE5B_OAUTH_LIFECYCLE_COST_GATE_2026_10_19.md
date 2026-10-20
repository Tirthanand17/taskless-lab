# FlowMinute Phase 5B — cloud OAuth lifecycle & ₹0 cost readiness (offline)

**Date:** 19 October 2026. Added to the existing **DRAFT PR #5**. This is a security-sensitive **sanitized observation classifier**, not a credential manager, YouTube connection, live channel verification or publisher.

## Why now

The authorized one-off October 20 **local YouTube** workflow needed a fresh Google authorization after an expired/revoked refresh token. A laptop-independent cloud system cannot assume access tokens work forever or silently fall back to the laptop. External/Testing consent can have much shorter refresh-token validity than properly configured published OAuth clients, but even a Production app may lose grants through revocation or policy and still requires actual provider-side refresh and owner-channel checks.

## Implemented software

- `autopilot/cloud_oauth_lifecycle_gate.py` screens strict **sanitized, caller-asserted fields only**, with an injected UTC clock for deterministic testing.
- Checks exact FlowMinute channel ID, explicit **user OAuth rather than service account**, Google app mode (reject Testing / unknown), least-privilege scope specific to the intended read-only or owner-reviewed private-pilot action, access TTL with 20-minute margin, refresh/channel observation maximum age (24 hours) and nonfuture timestamps.
- Checks explicit owner approval for a connection, stated provider-managed encryption, isolated laptop-independent cloud runtime, durable private media storage and a verified **hard zero-overage** cost ceiling.
- Rejects unexpected or secret-bearing JSON field names and invalid input types. Never accepts OAuth token string, refresh token, client secret, password, bearer header, cookies, session URI, personal account identifier or private key. Does not log dynamic errors.
- If all **untrusted claims** are internally consistent, returns `ELIGIBLE_FOR_LIVE_READONLY_PROBE` or `ELIGIBLE_FOR_OWNER_APPROVED_PRIVATE_PILOT_REVIEW`, **not production approval**. It always explicitly sets `actual_provider_authenticated=false`, `unattended_upload_authorized=false`, `unattended_scheduling_authorized=false`, `cloud_autopilot_ready=false` and lists the independently required evidence.
- The gate is never an OAuth refresh implementation. A real credential custodian must keep tokens in an approved cloud secret store and independently verify owner-channel, granted scopes, quota, API status, token viability, request origin, revocation/freshness and cost controls.

## Test evidence and development constraints

`python -m unittest autopilot.test_cloud_oauth_lifecycle_gate -v` and full standard public-repository CI, with **no secrets or API calls**. Adversarial fixtures cover Testing consent, 20-minute expiry margin, revoked/old/future refresh claims, owner mismatch, scope creep, bad secret storage, missing owner permission, laptop runtime, unverified durable storage and zero-rupee overage.

The existing Phase 5A read-only owner videos guard is a separate candidate: combining two software screens does **not** authenticate source claims or authorize a YouTube mutation.

## Still blocked

- Live owner-approved Cloudflare D1 schema/history inventory, migration/rollback and trusted single-writer deployment.
- Provider-native OAuth account/consent resolution with stable permitted scopes, secured independently from public GitHub runners and the owner's laptop.
- Durable private source media and natural multilingual narrator rights; true spoken subtitle alignment and human/factual/rights review on complete original files.
- Cloud-owned compliant render/orchestration capacity with a genuinely enforced ₹0 ceiling; private YouTube **resumable** uploader pilot with channel-identity and remote-status readback.
- Authenticated analytics; full unattended 3/day operation. **Keep upload/schedule disabled** until all independent gates pass.

**Roadmap status remains 2/8 major phases (25%) accepted in software/audit scope and 21 production acceptance subphases open.** PR #5 stays DRAFT. No laptops accessed, new provider connected, token transferred, charge, upload, schedule or YouTube mutation from this source work.
