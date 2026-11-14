# CLIVOX V2 P2 — Public Creator Prospect Intake / Unsent Partnership Pilot

**Date:** 2026-11-14. **Scope:** Verified *research engineering* only. No creator outreach, publisher agreement, commercial right to clip, third-party media acquisition, API contact actions or YouTube publishing.

## What this actually implements

- Five manually researched public **creator-branded business page references** with creator self-descriptions, possible editorial fit and source evidence. Three to five is the shortlist *research size*, not human identity/permission verification. These are not a ranked YouTube-view/likes leaderboard and contain no creator contact email or phone.
- Four initial **potential small/mid-size partnership research leads**: Ankitt (PS5 livestream), Eggmilk (variety streams), Mr JD Gaming (gaming), MandarriaXL (unconventional gaming). **CaseOh** is a famous format-research comparator only and not presumed willing to license CLIVOX footage.
- An offline Python strict validator, \`scripts/branch3_v2_creator_prospect_intake.py\`, that rejects unauthenticated consent claims, email/phone/private details, dangerous URLs, external hosts, duplicate leads, noncurrent research (older than 30 days), fake platform-derived popularity metrics and invalid authorizations.
- A disposable JSON **owner-review packet** with exact SHA of public research, current \`NOT_CONTACTED\` / \`UNVERIFIED\` flags and **five recipient-less UNSENT partnership inquiry drafts**. No email sending integration or external network operations exist. Output is in protected/private temporary runner path only, not committed or uploaded as an artifact.
- A dedicated GitHub Actions PR/main CI \`branch3-clivox-v2-p2-prospect-intake.yml\`, all-no-secrets: unit tests + actual full fixture intake + independent "zero contacts, zero rights, zero uploads" assertions.

## Public creator business page research sources

These are **creator-branded public pages**, not independently authenticated license-owner identities. Reverify each page and the relationship to the actual video channel before any real action.

| Prospect | Public branded research reference | Observed business entry | Critical limitation |
|---|---|---|---|
| Ankitt | https://ankitt.com/ | Public form for collaborations and creator projects; site links to Twitch and YouTube | Identity of legal video owner and deliverability not verified |
| Eggmilk | https://eggmilk.carrd.co/ | Public partnership and business inquiry contact section; site links Twitch and YouTube | Carrd branding is self-asserted; not a verified commercial rights grant |
| Mr JD Gaming | https://mrjdgaming.com/contact/ | Search-indexed business inquiry section | Direct page returned **403** during the research browser check; must reverify manually before considering outreach |
| MandarriaXL | https://www.mandarriaxl.com/ | Public creator branded business partnerships section | No identified specific licensed long-form source or authenticated authority |
| CaseOh | https://caseoh.com/pages/about-me | Public creator business inquiry section, gaming and streaming links | Famous creator reference only; no assumed openness to cross-channel footage licensing |

**Important:** The presence of a business form or business email is an invitation to make a business inquiry at most; **not consent to replicate the media, re-edit it or monetize it**. In addition, Twitch's standard Clips settings allow a broadcaster to enable social sharing, but this **must not be confused with a separate commercial grant** for a CLIVOX-branded YouTube redistribution business: https://help.twitch.tv/s/article/clips-settings

## How to generate a private owner review package

Run only in an ephemeral runner or separately owner-approved secure private workspace. No use of owner's PC assumed.

Example (read-only input in public repo; unique existing empty output directory outside repo):

~~~bash
mkdir -p "$RUNNER_TEMP/clivox-p2-review"
python -B -m scripts.branch3_v2_creator_prospect_intake \
  --input branch3/clipping_v2/prospects/public-business-pages-2026-11-14.json \
  --output "$RUNNER_TEMP/clivox-p2-review/clivox-p2-owner-review-UNSENT.json"
~~~

The output contains public website links, clearly unverified identity and rights fields, and proposed email *text without a recipient address*. This CLI **cannot actually send an email or issue a legal permission grant**, and no YouTube Media API / OAuth / retrieval endpoint is used. The input must be refreshed/reverified within 30 days; don't keep stale contact routes as verified indefinitely.

## What a real CLIVOX operator must manually verify before outreach

1. Does the business page belong to the actual creator/representative who can negotiate **the source recording's rights**? Confirm channel relationships and business inquiry route through the relevant creator's latest authenticated account. The public page may be false, compromised or obsolete.
2. Is the creator actually recording consistent long livestreams/vlogs or interviews that would yield standalone Shorts? Review the content directly through normal web playback. **No source downloading yet.**
3. Is the form genuinely intended for editorial/media partnership inquiries? A generic merchandise support page or fan Discord isn't the business contract route.
4. Does the creator already have official Shorts/clips partners, exclusivity clauses or publisher rights limitations? Ask them; don't infer from a channel upload. Verify no minor/guest/music/TV IP issues.
5. The owner decides which **3–5 prospects** should receive individualized inquiries, business terms and any outreach. Current research names are not an owner-approved shortlist.
6. Only after **explicit authorization** may a real human or connected send tool submit selected inquiries. No automation may bypass legal acceptance, hallucinate a response or assert a brand deal.
7. If they respond, start the existing A2 actual rights review; owner verifies signed consent and scope for commercial **YouTube** redistribution, creative edits, monetization, video IDs/segments, attribution, owner channel, territory, expiry/revocation, game/music/guest rights, original file delivery, claims handling, edit IP and potential revenue share. Until then: **0 grants, 0 file acquisition, 0 clip exports**.

## Proposed pilot terms (for negotiation, not agreement)

A three-Short private demonstration for one willing creator, 25–55 sec each only as an editorial starting point. Creator delivers the original licensed source file through a separately owner-approved private handoff. CLIVOX adds meaningful narration/commentary, edits, captions and accessibility checks; owner/editor and rightsholder approve the exact final media before any publication. Contract explicitly addresses rights, editorial accuracy, claims, compensation and revocation. Avoid exclusivity or transfer of CLIVOX-created edits without informed human review.

**Never promise virality, monetization, traffic, partner payouts or access to private most-replayed data.** A creator collaboration form and a generic fan-clipping setting do not automatically authorize a separate monetized YouTube clipping channel.

## P2 technical acceptance / roadmap accounting

Engineering acceptance:
- Input is sourced, fresh, canonical, bounded, no public personal contacts or YouTube API-derived viral analytics;
- All leads remain \`NOT_CONTACTED\` with \`rights_state=UNVERIFIED\`;
- Deterministic pending owner-review packet + five **unsent** drafts;
- Complete offline unit/integration tests and PR + merged-main CI;
- No private Google, YouTube, Twitch, creator-mail or source-media credentials in CI.
- No media, licensed grants, uploads, scheduling or public assets.

**P2 human milestone remains open** until an actual trusted CLIVOX human re-verifies creator identities/routes and selects 3–5 legitimate outreach prospects; technical CI success is not that human action. Therefore overall **V2 roadmap completed 2/12 phases = 17%** until this additional acceptance, even when P2 engineering groundwork tests pass.

## Next separate integration

When owner explicitly authorizes and genuine business contacts are selected: start P3 human-authenticated licensing/consent case. No clip-source processing until a real P3 rights grant **and P4 private media storage** exist. P5 detection can still be developed separately against first-party synthetic demo video, without pretending licensed creator clip output.
