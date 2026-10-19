# Phase 5D — Cloudflare read-only YouTube Worker candidate

**2026-10-19. Existing DRAFT PR #5. Software-only, not deployed.**

## Implemented

- `autopilot/phase5d_cloudflare_owner_readback.mjs` is an actual Cloudflare Worker-style `fetch` handler. This is distinct from the earlier synthetic Python provider-lease contract.
- `GET /health` is static and does not query credentials or Google.
- `POST /v1/owner-readback` is disabled unless the bound Cloudflare environment explicitly enables owner readback, fixes the Brand channel, insists that all upload/schedule flags equal `0`, asserts a hard zero-overage budget, and supplies a short-lived Worker-secret access token and high-entropy admin key.
- The endpoint validates the three planned slots and rejects duplicate video IDs, extra input fields, malformed dates, unexpected methods/paths and oversized JSON before contacting Google.
- After operator authentication, it performs one `channels.list(mine=true)` and at most three `videos.list` requests to the **fixed** Google endpoint, with `redirect:error` and bounded response streaming.
- Correct exact-channel, title, video ID, processing, private status and upcoming IST `publishAt` are required for `SCHEDULED_VERIFIED`. Public after the due time is `PUBLIC_STATUS_ONLY` and is **not** anonymous playability proof.
- The response never contains owner tokens, secret keys, private video IDs, video titles or raw Google errors. It never sends a mutating YouTube request.

## Runtime and testing

- `autopilot/test_phase5d_cloudflare_owner_readback.mjs` uses Node Request/Response and fake Google endpoints, without live internet or credentials. The branch's Content Quality Gate runs `node --test autopilot/test_phase5d_cloudflare_owner_readback.mjs` after Python tests.
- Valid coverage: disabled flags, zero-overage gating, admin authentication, 2-of-3 verified slots, withheld video IDs, fixed UTC times, duplicate IDs, invalid manifest, access token expiry, wrong owner channel, incomplete processing, raw errors, public-vs-private distinction, route refusal and cache/CORS restriction.

## Critical limits

1. The code has **not** been deployed on Cloudflare and does not authenticate the actual account. The Worker source status is explicitly `NOT_DEPLOYED_UNATTESTED_READONLY_SOURCE`.
2. The existing one-time Cloudflare D1 Brand OAuth proof does not supply a renewable access token. The new code accepts only a separately provided **short-lived** Worker secret and does not refresh it. **24/7 unattended operation is NOT possible** with this component alone.
3. The config assertion `FM_HARD_ZERO_OVERAGE_VERIFIED=1` is **not an independently proven** hard billing cap, request quota or rate limiter. The owner/provider must actually verify the plan, limits, absence of overage exposure and bounded request rate before any deployment.
4. The existing production D1 schema/history, writer leases, backups and migration must be independently reconciled. This Worker never reads or changes D1.
5. Explicit owner authorization is needed before using a new Google OAuth scope/consent, connecting any provider, provisioning Cloudflare infrastructure or deploying a real Worker. Do not bypass Cloudflare error 1010 or transfer tokens into public GitHub.
6. This is not an upload service. Unattended publishing, scheduling, media storage, rights review, real transcript QA and subscriber-growth analytics remain blocked.

## Progress accounting

**2 of 8 accepted major milestones = 25%.** Original 21 outstanding live-production acceptance subphases remain OPEN. Synthetic CI and source-only Worker code do not increase real autopilot readiness. No Nirala access, new account, charge, OAuth secret retrieval, D1 write, YouTube mutation, deployed Worker or completed long-video schedule claim in this software task.
