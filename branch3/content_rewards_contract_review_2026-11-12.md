# Clivox — Content Rewards contract and rights review

Date: 2026-11-12. Research notes; not legal advice. The actual user/owner must review and decide whether to accept any third-party agreement. No agreement was accepted, and no creator footage was acquired.

## Verified platform terms
The current Creator Terms on Content Rewards, updated 2026-10-26, explicitly state that opening a creator account, linking a social account, joining a campaign or uploading a clip means accepting the Terms:
https://contentrewards.com/terms
Alternate live copy: https://b4e0vdqv6zgqeqj4pfgm.apps.whop.com/terms

### Important clauses
- **Section 2.1: 18+ only.** Do not assume eligibility. The owner must confirm privately before creating any account.
- **Section 17.1: Brand footage license** is limited, revocable and specific to that campaign.
- **Section 17.2: participant warranties** put responsibility for third-party rights (music, guests and other media) on the clipper.
- **Section 17.3:** approved clips grant the platform and brand a perpetual, worldwide, royalty-free, sublicensable promotional use license in covered cases.
- **Section 17.6:** when a brand provides underlying footage, the **brand owns the final edited approved clip**, with rights assigned by the participant. This is material to Clivox's long-term ownership and possible monetization strategy.
- **Marketing and likeness permissions** apply to campaign-related materials. Review Section 17.7 and disclosure terms before joining.
- A publicly advertised campaign is not a universal third-party copyright license. Specific rights and terms may be behind login/join.

## Practical recommendation for Clivox
Prefer a direct, written independent clipping license from the verified creator/rights holder that explicitly allows commercial YouTube Shorts, significant editing and ongoing channel use, with no contradictory assignment, if ownership preservation is the priority.

The official **YMH Clipping** community publicly invites editors and clippers to its program:
https://whop.com/ymhclipping/
The November YMH campaign also lists YouTube and original edits:
https://contentrewards.com/c/campaigns/51fa8c57-fb2f-44e0-b3a8-158f96cbf018
Its episode-specific source link for Ep. 347 is:
https://www.youtube.com/watch?v=i6pmnpaOaZQ

This makes YMH a credible **creator-published permission pathway**, but not yet an approved license for the owner. Full campaign rules/restricted topics, the assignment provision, any revenue rights and a required join/consent remain pending.

For the second IShowSpeed Expedia lead, official Reach rules require >=50% audience in designated native-English-speaking countries, an exact Nov 6 stream segment, campaign-specific sponsor presentation and #IShowSpeed. A new channel with no audience history **cannot substantiate that targeting threshold**. Demote until proven:
https://reachclipping.com/Expedia-IShowSpeed

For FaZe tournament, public campaign requires >=60% US viewers; Clivox has no evidence meeting that threshold. Avoid participation until independently proven:
https://dev-b4e0vdqv6zgqeqj4pfgm.apps.whop.com/c/campaigns/200ea21b-be80-4db8-b552-8e32b148604e

## Decision gate: no click-through consent without owner action
1. Owner reviews actual third-party contract (including IP assignment and payout rules), confirms 18+ eligibility, and personally accepts only if comfortable.
2. Verify the campaign operator is authorized by the source creator to grant the intended commercial YouTube usage.
3. Review source-specific exclusions; don't use celebrity speech, copyrighted music, in-show footage, guests or brand marks beyond their licensed scope.
4. Keep all receipts/contracts privately; commit only non-sensitive proof metadata, exact source IDs and hashes to the repo.
5. Until all permissions pass, maintain empty `creator_permissions.json`; do not download, render with source media, or schedule.

## First episode research
YMH's official 2 Bears site lists **Bert Has Sexy Lady Legs**, released 2026-11-09 (Ep. 347): https://ymhstudios.com/2bears/
A podcast episode chapter index independently places an '80s restaurant discussion around **01:04:52–01:09:36**, suggesting an editing hypothesis, not a verified short quote:
https://www.ondacast.com/podcast/2-bears-1-cave-with-tom-segura-bert-kreischer

See `pilot_ymh_ep347.json` for a wholly original, **source-free** hook/storyboard. Do not assert transcript, actual speaker lines or viral outcome before watching and clearing the source.
