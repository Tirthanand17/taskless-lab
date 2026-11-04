# ADR-0019 — B3d4c2a: externally anchored owner inference consent lease, not a provider entitlement

**Decision:** 2026-11-04, Asia/Kolkata. **Track:** Branch 2, cloud-only engineering. **Status:** read-only independent owner-record integrity preflight, *not* live AI, externally verified account consent, content clearance, or YouTube publishing.

## Reason

B3d4c1 demonstrates real original Python educational graphics, thumbnails and signed-script Kokoro-voiced three-pack MP4s on GitHub-hosted runners. However all tested scripts and source records are invented fixtures. To create genuinely varied AI-authored episodes, the legacy optional Gemini adapter needs an external provider key, verified billing/project tier, owner-accepted provider data-use policy, and one-use request budget. Existing ModelGrant was only a dataclass of caller-provided booleans, and with any string API key it could initiate a real HTTP request if transport was omitted. The source/claim/rights and image/audio review gates elsewhere cannot correct that authorization weakness.

**Decision:** Make the unqualified legacy live network request pathway refuse all real provider connections. Replace owner-intent assertions with an *Ed25519-signed detached owner-lease verification preflight*, bound to the exact episode and sanitized research context. This module does not actually contact Gemini; it is not a new private identity service or quota ledger, and cannot on its own unlock inference.

## Relevant official research

- [YouTube monetization policies](https://support.google.com/youtube/answer/1311392?hl=en): originality, material variation and educational viewer value cannot be supplied merely by repeated templates or cosmetic topic swaps; a generated script must undergo independent editorial quality review.
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing): pricing depends on an actual provider project/tier; no public repository can establish a user's free-tier entitlement or the availability of zero-cost requests, and provider data use terms vary. **A signed claim that a project is free is NOT account-side verification and cannot be treated as a charge cap.**
- [Google AI Studio and Gemini API data use](https://ai.google.dev/gemini-api/terms): the account holder must review the current applicable data use terms, what request content is submitted and whether project settings allow provider use; sensitive/private source body text is disallowed from this public CI workflow.
- [NIST FIPS 186-5 EdDSA](https://csrc.nist.gov/pubs/fips/186-5/final): digital signatures bind attested records to keys and detect tampering, not the real-world identity or truth of the signer without separately secured enrollment.
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use): untrusted pull request jobs must have read-only permissions and no private secrets, live inference entitlement or privileged token.

## Integrity and scope

1. The lease is a strictly versioned purpose-specific dataclass. It covers FlowMinute's exact YouTube channel ID, one of three release episode IDs, the complete SHA256 of a rederived B3a safe metadata-only draft input, one explicitly allowlisted provider+model and one zero-incremental-paid-cost request.
2. Require a separately anchored SHA256 of the complete owner lease, owner record ID/key ID and an Ed25519 detached signature matching an independently supplied owner public-key registry. This repo must not self-enroll the owner using a model result, public pull request, CI fixture, or header. Automated/publisher agent IDs are excluded; a real owner who is also a creator remains eligible.
3. Lease requires content-addressed protected records for the actual billing project fingerprint, free-tier entitlement/account review, current provider data-use terms snapshot, owner's explicit consent record, and private secret-custody policy. The owner must specifically sign that they accept the applicable data use terms and draft inference. All fields have exact SHA256 format, but **the code cannot verify that those private records exist or are accurate**.
4. Limit issued/expiry to max two hours and current freshness to 45 minutes. Refuse future-dated, replayed cross-episode/slot, changed headlines, wrong provider, changed digest, forged cost, multi-request allowance, unknown/revoked owner or changed signature. Reject truthy strings/integers in ModelGrant as consent, and float request counts.
5. The three-slot consistency function checks that all three separately signed owner preflights use different request context/episode/lease IDs but the same day. This is a *structural consistency test*, not a real atomic one-time paid quota ledger.
6. The technical output **always** indicates: no real-world enrollment verified by code, no account entitlement verification, no private budget/fencing ledger, no secret vault, no real consent verification, no actual inference, no uploader and release_authorized=false.

## Source and future deployment boundary

The current unprivileged PR workflow generates and verifies only **synthetic throwaway Ed25519 keys and reference-only invented headline observations**, never reaches a provider endpoint and cannot authorize actual billing. No live script content, voice model, local laptop, customer data, source article, generated video or YouTube metadata is sent outside the GitHub Actions job. The historical B3a Gemini response tests continue to use in-process FakeTransport objects; that mock path cannot serve as proof of provider capability or project access.

**This PR does not deploy a real owner registry, signer, current data-use consent, Google billing project, private API key, zero-spend cap, or durable atomic lease consumption.** A later authorized private runtime must integrate these components, confirm project-specific quotas and current provider terms, and consume the lease atomically before a single allowed inference request. The default code must remain fail-closed while those controls are absent.

## Tests and acceptance

- autopilot/owner_provider_lease_gate.py: crypto-only owner-intent validation and three-slot structural check.
- autopilot/test_owner_provider_lease_gate.py: synthetic signer positive/negative cases with wrong slot, revoked key, altered consent, stale grant, duplicate lease, forged zero-cost, hidden model/provider and untrusted automation identities.
- autopilot/script_draft_agent.py: existing legacy self-reported ModelGrant cannot make network requests absent an explicitly provided mock/test transport; strict boolean and integral bounds.
- autopilot/test_script_draft_agent.py: regression against self-asserted real HTTP pathway, truthy/float/complex grant spoofing, while previous FakeTransport compatibility remains.
- .github/workflows/flowminute-b3d4c2a-owner-lease.yml: read-only standard pull_request GitHub-hosted CI with synthetic keys, no paid model, cloud publishing, YouTube OAuth, or persistent source/video artifacts.
- Existing repository quality, public scout and cloud render smoke must pass. Merge only after all GitHub checks are green.

## Next: actual owner authorization, creative originality and production

**B3d4c2b:** With explicit owner approval outside this public PR, enroll and authenticate owner signing keys, verify provider data-use terms/privacy, configure a *separate private credential vault* and externally enforced zero-spend/account quotas with one-time atomic lease consumption. Evaluate genuine model output from three distinct topics, preserving raw original source provenance and independent claim-by-claim human review. No account/key exists just because a test receipt was signed.

**B3d4c2c:** Create truly distinct nonrepeating topics, scripts, executed demonstrations and visual/thumbnail/sound-design direction anchored to real checked facts; re-run all B3d1→B3d4c1 signed script and media QA, add actual signed independent editorial/source/rights/full-playback receipts bound to the final MP4, captions, graphics, thumbnail and metadata. Generated speech may not be legally monetizable without a confirmed current voice license and disclosures.

**B4:** Only after separate user authorization, use private cloud durable media and ledger, protected YouTube OAuth, fenced single publisher, private video upload + actual processing and caption/thumbnail remote readback, then schedule the exact IST slots safely.

**B5:** Demonstrate 21 actually reviewed, distinct releases over seven consecutive days with laptop off. Branch 1 assisted releases remain independent and unchanged.
