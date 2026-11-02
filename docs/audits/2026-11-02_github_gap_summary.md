# FLOWMINUTE LAB — GitHub production gap audit summary, 2026-11-02

Read-only audit of public source Tirthanand17/taskless-lab and private control Tirthanand17/flowminute-control-private.

## Current source layout
- main SHA 82edd9455045716c92d29feab3dbfd387c8cf50c
- draft PR #5 feature/flowminute-phase2-evidence-preflight: 286 changed files; 1335 passed, 4 skipped, 997 subtests on CI 39381973259, 2026-10-20. Major phase/cloud ledger work *not merged*.
- draft PR #6 feature/oct24-multicharacter-3d-lesson-contract: 93 changed files; 412 passed + 6 subtests CI 40048686329, 2026-10-24. New cinematic work *not merged*.
- Cloud Scout main failed repeatedly through 2026-11-01; the latest failure logs show missing ffmpeg and cryptography in its media and reviewer tests. PR #6 Cloud Scout includes install steps, main does not.
- Private control's historical D1 production ledger was not backfilled and there was no unique release-slot constraint; do not deploy synthetic CAS to a mismatched live schema.
- Older publish-youtube.yml still offered immediate publication with less stringent gating; fail-closed schedule path in PR #6 must become the only reviewed production writer. Hindi captions metadata is hardcoded English in the current publisher and needs repair.
- The folder C:\Users\Dell\Desktop\youtube con is an archival laptop path, not a GitHub media folder. Do not access Nirala without new specific approval.
- Approved October 24 Asha/Jay 8-second intro hash 536652db768052c69e640d0bcd5c950cafcfcee37cc062286dcef2e2d4938517, 24-second Kokoro narration hash f81dba668732b01b4fc4bbad0e54414f01765e13ec47879dbdb789a334e7d203, but missing scenes 02–04 and approval.
- No verified production cloud-only YouTube publisher, final 32s movie or fresh credential access confirmed in audit.

## Implementation order
T01 resolve PR #5 / #6 integration; T02 repair Scout; T03 legacy publishing guard + Hindi captions; T04 policy alignment; T05 authentic media and voice storage; T06 free-credit verification; T07–T09 make and review real 32s English cinematic Short; T10 Hindi premium productions; T11–T13 read-only Cloudflare/D1/OAuth/budget verification then approved remediation; T14 integration CI; T15 private upload pilot with separate approval; T16 schedule readback/reconciliation; T17 analytics; T18 laptop-independent zero-budget release reliability.

## Safety
This document is an audit, not an approval manifesto or deployment receipt. There are historical authenticated YouTube receipts for earlier releases, but current account status needs fresh owner-side verification. Do not fabricate YouTube video IDs or use code test results as evidence of publishing.
