# CLIVOX V2 — Moment Evaluation, Originality & Experimental Learning

**Planning only.** A model can rank human-reviewed moments in licensed footage; it cannot measure the private replay graph of another creator, predict virality deterministically, self-license a clip or fabricate engagement.

## 1. Three independent decision gates (do not merge into one numeric score)

### Gate R — Authenticated rights (hard binary)

\`PASS\` requires real A2 human-validated creator control and signed commercial grant, exact source scope, publisher/game/music/guest clearance, source delivery channel, territory, duration, revocation-current status, attribution and requested transformation; no outstanding disputes/expiry. \`FAIL / PENDING / UNKNOWN\` means **NO MEDIA ACQUISITION, NO RENDER OF THIRD-PARTY SOURCE, NO UPLOAD**. This gate can never be overridden by estimated viral likelihood.

### Gate S — Honest subject/editorial value

Explicit CLIVOX original commentary/criticism/explanation/new storytelling **with meaningful qualitative difference** from the source, no fake facts/quote, no edited-context deception, no personality impersonation, no bullying or privacy harm, no mislabeled GTA VI leak, branded-content notices where needed. A montage of someone's footage with emoji/captions/zoom only **fails** CLIVOX originality review even if authorized by creator.

### Gate Q — Technical and owner release

Real licensed video, voice, captions, rights and final metadata are human-watched; audio/video quality checks passed, exact MP4/WAV/SRT/title hashes created, true owner signature obtained, Clivox-only OAuth and protected environment approved, private-first remote readback reconciled. A QA passed flag is **never** the human's identity or signature.

**All three gates must pass independently before any public/scheduled YouTube release.**

## 2. Candidate evidence, not prediction magic

Sources of candidate timestamps in descending confidence:
1. **Partner-provided** clip timecodes and their authorized private retention insights (scoped only to that partner, no cross-owner aggregation). Label \`SOURCE_OWNER_PROVIDED\`.
2. **Twitch official clip references** / VOD offset and clip view count from permitted Helix, where available; label \`TWITCH_OFFICIAL_CLIP_METADATA\`, not a license or YouTube retention.
3. **Human editor** watches licensed source and annotates moment boundaries; label \`HUMAN_SOURCE_WATCHED\`.
4. **Computer-proposed** ASR/VAD/event/scene candidates on authorized raw file; label \`MODEL_ESTIMATE_FROM_LICENSED_SOURCE\`.
5. Unusable data \`UNAVAILABLE\` (never zero or a made-up most-replayed peak).

Do not label any candidate \`YOUTUBE_MOST_REPLAYED_VERIFIED\` unless a genuine authorized creator Analytics report exists and is actually accessible and permitted for this use. Public \`videos.list\` does not contain it. Do not program a private heatmap scrape.

## 3. Offline editorial rubric for *already licensed* candidate segments

Each category gets an explicitly **human/multimodal source-observation score** from 0 to 4, with evidence anchors. A one-pass rubric can be \`sum(weight * rating / 4)\` as a **local CLIVOX editorial prioritization**, not an API-data-derived platform performance metric. Missing assessments are \`null\`, not 0; do not rank incomplete candidates as though fully reviewed.

| Source-observation criterion | Weight | What earns 4/4 | Counterexample |
|---|---:|---|---|
| Clear opening hook in first 1–2 sec | 22 | Instantly obvious surprise/question/stakes from licensed footage or truthful new explanation | Long intro or "wait for it" without context |
| Complete setup and standalone context | 18 | Viewer who has not seen 2-hour stream understands the people and event | Inside joke with no explanation |
| Payoff/twist/comedy/emotion | 16 | Measurable narrative reversal and an actual ending | Cut right before important reveal; deceptive cliffhanger |
| Visible genuine reaction / action | 12 | Recognizable reaction/game maneuver supported by source | Arbitrary zoom and explosion with no story relevance |
| Speech/visual clarity / facecam | 10 | Legible at 9:16, sound not clipping, original speaker accurately subtitled | Music drowns dialogue, face cropped |
| Original CLIVOX transformative angle | 12 | Specific new reaction, comparison, teaching, narrative setup or analysis | Only subtitles/emoji/stickers |
| Accurate/brand-safe source context | 10 | Truthful, nonsensitive, no minors/harassment, sources credited | Quote misrepresentation, slur, public embarrassment |
| **Total** | **100** | **Editorial only—not a probability** | Rights can still be zero |

**This score must never use public YouTube API statistics** (views, likes, comments, subscriber counts, duration-derived velocity), public-view ranking aggregation or private third-party retention. API developer policy on derived measures is stricter than common creator advice. Seek platform-policy verification before production use of any source selection derived from API Data. Use source media and human observations after a **real rights grant**.

Initial production logic is **transparent deterministic filtering and human ranking**, not an expensive ML model. Only train a learned ranking model after enough genuinely licensed examples with explicit creator permission for model training, adequate holdouts, deletion provisions and real own-channel outcomes.

## 4. Candidate algorithm — context-preserving (proposed, not implemented)

\`\`\`python
def propose_moments(licensed_source, verified_rights, independent_observations):
    if not verified_rights.current_for_this_source_and_use:
        return DENIED_NO_MEDIA_PROCESSING

    transcript = ASR(licensed_source.audio)          # untrusted hypotheses
    speech = VAD(licensed_source.audio)
    scenes = detect_scene_changes(licensed_source.video)
    events = human_or_bounded_rule_based_suggestions(
        transcript, speech, scenes,
        reaction_audio_peaks=True, surprise_language=True
    )
    windows = merge_overlaps_and_preserve_before_after_context(events)
    windows = filter_complete_arc_no_quote_distortion(windows)
    return CANDIDATE_EVIDENCE_ONLY(windows[:20])
\`\`\`

Data requirement: timestamped original spoken text with confidence/warning for laughter or speech overlap; licensed source SHA; start/end; scene, audio and transcript anchors; human review notes separate and private; valid source permissions when input was accessed. Never feed arbitrary creator speech as a command to agents.

## 5. Format experiments (hypotheses, not "algorithm secrets")

Initial hypotheses, to test in real original editorial clips after permissions:
- Hook in first ~1 second vs context-first 2–3 seconds, both accurately describing the scene.
- Facecam above gameplay vs side-by-side after viewer recognizability checks.
- Original commentary **brief explanatory intro** vs original humorous critique before clip.
- 25–35s vs 40–55s if both contain complete honest payoff.
- Selectively captioned punchlines vs full synchronized captions, subject to accessibility and actual spoken words.
- Global English commentary vs Hindi/Hinglish commentary for **different genuinely licensed content cohorts**, not deceptive redubs of an unapproved person's voice.
- Conversational clear CTAs vs no CTA when plot already complete. No aggressive/forced engagement.

At launch, do not publish two near-identical copies of the same clip to fake an A/B experiment, and do not use copyrighted songs just to follow a trend.

## 6. Training/evaluation dataset design

**Pilot dataset only after first actual commercial source grants:**
- 2–3 legitimately licensed creator-supplied long-form pieces; source owner allows private ASR and clip analysis, specified explicitly in grant.
- Human editors independently label at least 40–60 candidate segments with narrative setup, payoff, time bounds, audio issues, original-value potential and reasons for rejection; no labels copied from third-party private retention.
- Annotate 20 source excerpts with exact human-corrected transcripts, including laughter, slang, accents, music overlap; build WER/CER only where ASR is licensed for processing.
- Split by **source/creator**, not randomly by adjacent seconds of same stream, to prevent leakage. Maintain held-out creator or stream and disagreements.
- Document false positives: screaming without payoff, loud background music, abrupt cut that loses context, staged clip, dangerous stunt, licensed guest with unlicensed media.
- Report human inter-reviewer agreement on a representative sample and at least 10% full-source-context verification. If sample small, state "unvalidated" rather than claim 90% predictive accuracy.
- Human thumbs-up on a source moment is **not monetization approval**. Final video must separately pass originality and rights QA.

**Offline acceptance for candidate detector** (proposals): recall of editor-accepted moments, precision among top-5 suggestions, average search time saved and miss-type taxonomy. Performance targets are determined after real labels, not fabricated now.

## 7. Real CLIVOX channel performance (only after lawful publication)

Keep platform ownership scoped: only CLIVOX official OAuth/Studio data. Distinguish **public starts/replays** from official engaged views. Use official actual supplied metrics:
- engaged views (source of qualified-view analysis)
- Stayed-to-watch versus swiped away, when accessible
- average percentage viewed and average view duration
- retention timeline (where account Analytics/Studio supports it)
- shares, subscriber growth, comments, repeat viewers where available
- claim/restriction rate, strikes/appeals, manual editor time, cost per approved clip (independently measured labor/compute)
- creator-license and valid-current-revocation status before any future publication

**Do not derive disallowed engagement scores/ratios from public YouTube API statistics.** For own-channel Analytics, present official returned ratios and scores unchanged. Independent editorial metrics (timing drift, frames, text legibility, worker runtime) come from our actual authored files, not from YouTube API Data.

**Missing value policy:** \`{"value":null,"reason":"NOT_AUTHORIZED_OR_NOT_SUPPORTED"}\`; never invent 0, replay spike, view-through, RPM or revenue.

### Evaluation cadence

First 1–3 approved clips: manual qualitative feedback and policy/copyright check, no statistical "winner". After 10+ sufficiently viewed uploads, compare cohorts stratified by source, niche, day, duration and original commentary class; label comparisons **observational** unless YouTube offers actual randomization. At 24h, 72h, 7d and 14d collect official metrics when authorized. Avoid decisions on tiny sample sizes; use confidence intervals with explicit statistical method only on lawful *own-channel* metrics as permitted. Owner reviews each proposed format change. Delete/refresh API cache on required cadence and honor creator rights revocations.

**YouTube Studio does not support native title/thumbnail A/B tests for Shorts as of research date.** Never claim one is running. Native A/B for eligible regular videos may be used later only as documented.

## 8. How to evaluate monetization realistically

A technically good clip with big source reach can earn **₹0** if YPP is not approved, reused-content standards fail, rights claimant monetizes or the uploaded video is private/blocked. Do not model revenue solely from total views. To forecast later, require:
1. Channel accepted in applicable YPP tier, monetization module active and creator payout requirements met;
2. Per-video qualified engaged views and eligible revenue after claims/Shorts-pool mechanics (actual authoritative data);
3. Written partner fee/revenue share and sponsorship obligations;
4. Paid expenses if any, cloud/private storage, human editorial/rights review and dispute cost;
5. Actual net proceeds to CLIVOX. Do not create "viral earnings calculators" with invented fixed RPM.

Review market-level hypotheses only as hypotheses. The channel should ultimately develop its own recognizable explanatory/comedic voice rather than become an uncredited fan repost account.
