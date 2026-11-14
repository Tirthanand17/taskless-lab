# CLIVOX V2 P3 — Commercial Rights Scope Quarantine (technical integration)

**Date:** 2026-11-14. **Status:** technical intake only; real creator rights NOT granted, owner/rights-holder identity NOT verified, no source acquisition or YouTube publishing.

## Verified GitHub integration evidence

[PR #208](https://github.com/Tirthanand17/taskless-lab/pull/208) passed **4/4 PR checks** and merged at `2338958ed20a3f273b58c46a6455d4208612e7a7`. The dedicated [merged-main P3 GitHub Actions run #43580815591](https://github.com/Tirthanand17/taskless-lab/actions/runs/43580815591) **succeeded**: 5 pending unsigned scope questionnaires, 30 unchecked conditions each, two synthetic A2 case IDs explicitly unlinked to any real prospect, and no real owner signing/creator grant, source video, email, Google API or upload. **P3 engineering is verified; actual legal permission has not been obtained.** The overall V2 roadmap remains **2/12 fully accepted phases = 17%**.

## Why this integration is necessary

P2 lists public creator-branded inquiry pages, not authenticated rights holders, commercial licenses, or proof the person owns any particular recording. Existing A2 signed-review modules implement offline signature and revocation mathematics but deliberately do not enroll real owner keys or approve a legal agreement. A forged GitHub field claiming "approved" or a test-signed synthetic A2 receipt cannot grant permission to download, edit, monetize or reupload Twitch/YouTube content.

P3 makes legal and business terms explicit, auditable and impossible to self-approve using public metadata.

## Source components and links

- [P3 scope/quarantine implementation](../../scripts/branch3_v2_p3_licensing_scope_quarantine.py).
- [P3 adversarial tests](../../scripts/test_branch3_v2_p3_licensing_scope_quarantine.py).
- [Zero-secret P3 GitHub workflow](../../.github/workflows/branch3-clivox-v2-p3-licensing-scope.yml).
- [Existing original A2 review and revocation policy](../rights_review/README.md).
- [P2 source-referenced prospect research](prospects/public-business-pages-2026-11-14.json).

P3 composes two separate existing components:

1. **P2 public creator prospects:** five branded research references, none contacted, with identity, partnership, terms, rights and media approvals FALSE. Each generates a proposed three-Short private-trial **request for negotiation**, not the creator's agreement. No actual YouTube source video ID is attached to a named prospect.
2. **A1→A2 pending source cases:** two completely synthetic source records passed through the existing A1 discovery fixture, A2 pending-case creation and A2 signed-review pending-case verifier. The synthetic video IDs remain UNLINKED from every real creator name. No ownership or legal relationship is inferred or invented.

The module reuses A2's existing signed-review zero-grant policy and empty creator permissions registry validator. Any forged "approved creator", production reviewer key, source download flag or revocation authority fails closed.

## Proposed written contract scope to negotiate

Before a real grant, human rights reviewers and the CLIVOX owner should obtain:

- Actual rights-holder identity and authority to license the source recording, plus proof of the link to the specific channel/video.
- Explicit **commercial YouTube Shorts redistribution** on CLIVOX, advertising monetization, cropping/subtitles, original commentary, production permissions, approved source video and timestamps, clips limit, territory and expiry.
- Authorized *creator-delivered original source media* or editor-approved legal source access. A public viewing link is not permission to download via an unrelated tool.
- Publisher rights for GTA/game footage, in-game music, guests, stream background songs, movie/TV overlays, sponsor and other embedded material, with excluded segments where clearance is missing.
- Attribution, accurately preserved quote context, permitted use of face/voice, originality requirements and nonimpersonation.
- Review and final approval process for the exact new clip, claims/revocation response, rights assignment/exclusivity, creator compensation/revenue split, tax/invoicing and sponsor disclosures.
- A secure confidential storage solution for actual agreements and private media, independently verified real human signers, and a durable current revocation feed.

The code emits **30 pending-authentication requirements per prospect**. Every status is PENDING_HUMAN_AUTHENTICATION_NO_GRANT. Requested items like monetization=TRUE mean **CLIVOX would like to negotiate that permission**, not that a creator granted it. The request always keeps no_license_granted=TRUE, no_terms_accepted=TRUE and request_only_not_agreement=TRUE. Extra approval fields, email/contact details, contract bodies, evidence hashes or illegal source downloads are rejected.

## GitHub-only technical verification

The P3 Actions workflow:

1. Runs adversarial P3 tests plus previous P2 intake and A2 review tests with test-only cryptographic keys.
2. Runs the real P3 Python command on the GitHub runner, using no external creator source and no Google/Twitch OAuth credentials.
3. Independently verifies zero actual contract signatures, contacts, grants, private evidence, licensed media, upload rights and public YouTube API calls.
4. Verifies that A2 fixture source IDs remain separate from named creator prospects.
5. Stores the ephemeral unsigned questionnaire outside the public repository and **never uploads a review artifact**. No use of laptop storage is required.

Example in a properly initialized ephemeral GitHub runner:

    mkdir -p "$RUNNER_TEMP/clivox-p3-quarantine"
    python -B -m scripts.branch3_v2_p3_licensing_scope_quarantine --input branch3/clipping_v2/prospects/public-business-pages-2026-11-14.json --out "$RUNNER_TEMP/clivox-p3-quarantine/clivox-v2-p3-unsigned-license-scope-HOLD.json"

The command cannot contact a creator, accept a contract, sign legal approval, access a source video or publish.

## Real-world blockers to completing P3

1. A trusted owner must finish P2 human verification of public creator identity, legal authority and business inquiry route, and select 3–5 legitimate outreach targets.
2. The owner must separately approve any actual outreach. Sending a message, receiving a reply or viewing a Twitch clip is not a media license.
3. An authentic rightsholder must issue a written commercial YouTube redistribution license with scope, underlying publisher/music/guest clearance, limitations, file delivery, expiry and revocation.
4. A real reviewer identity and key, nonrollbackable revocation anchor, complete up-to-date revocation state and private owner-approved contract vault must be established. Offline mathematical signatures and self-reported human checkboxes are not legal authority.
5. P4 media storage and a real secure source handoff must be approved before any P5 creator-video processing.

**Progress accounting:** P0 and P1 fully accepted = 2 of 12 roadmap phases, **17%**. P2 human acceptance and P3 real licensing remain pending. Completing this **P3 technical intake** does not increase the roadmap count or mean that clipping/upload is operational.

**Next engineering work after green P3 CI:** owner-controlled private legal evidence intake and independently authenticated, source-specific rights grant/revocation verification. Do not flip publishing flags merely because the unsigned scope checklist passes.
