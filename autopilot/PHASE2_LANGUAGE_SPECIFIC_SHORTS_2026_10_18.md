# FlowMinute Lab — one Hindi Short for Hindi viewers, one English Short for English viewers

**18 October 2026. User-approved content-language strategy. Draft policy and media QA only — no audience targeting or upload carried out.**

## What the owner wants

Make **two independent original Shorts per day**, each intentionally optimized for a viewer's language rather than one confusing multilingual Short:

| Video lane | Primary spoken language | Primary captions | Native title/description | Planned narrator | Follow-up |
|---|---|---|---|---|---|
| Hindi Short | Hindi/Hinglish (hi), conversational, Hindi-first | Hindi/Devanagari (hi) | Hindi/Devanagari | narrator_hindi_a | Hindi long-form lesson, if its quality is approved |
| English Short | English (en) | English (en) | English | narrator_english_b | Another English lesson; do **not** claim the Hindi long is an English lesson |
| Current long tutorial | Hindi/Hinglish (hi) | Hindi/Devanagari (hi) | Hindi/Devanagari | narrator_hindi_long_c | Not an English full lesson |

Keep all educational code names (CSV, Python, DictReader) accurate; using an English API token inside a Hindi lesson does not turn the spoken instruction English. Preserve original examples and localized explanations for each language. More localized titles, thumbnails and description copy must be independently checked before the actual upload.

## Platform-supported signals, NOT guaranteed delivery

- YouTube's **original video language** setting helps viewers find videos in their language: https://support.google.com/youtube/answer/6304325
- The official Data API defines `snippet.defaultLanguage` for the language of title/description, while `snippet.defaultAudioLanguage` describes actual spoken default audio: https://developers.google.com/youtube/data/reference/rest/v3/videos
- YouTube determines whether to present translated language metadata using viewer signals including language, location and watch history. Language settings **do not create a guaranteed or exclusive routing rule**: https://support.google.com/youtube/answer/7296123
- YouTube supports multi-language audio on a single video/Short, and optional translated metadata, but this project chooses **two separately scripted Shorts** per the owner's audience preference: https://support.google.com/youtube/answer/13338784
- Do **not** hard-code geo fences: Hindi viewers may live anywhere and English viewers may be in India. Do not claim a particular country or a viewer's personal language identity from location.
- No automatic dubbing or translated audio setting was enabled. No `defaultAudioLanguage` should be asserted for current SILENT drafts because **no real narrator audio exists**.

## Implemented policy/validation

- `autopilot/phase2r3_audience_language_lanes.py` constructs three **draft metadata lanes** using the actual authored script sections, exact original spoken bytes, intended narrator IDs and script-derived SRT checksums. Hindi titles/descriptions must use Devanagari; English titles/descriptions must not contain Devanagari. Spoken language is bounded conservatively with a script-character check, not semantic or independent native-speaker approval.
- The Hindi Short may have a language-matched Hindi long tutorial recommendation. The English Short has **no** link to the current Hindi-only long as an English follow-up; its end CTA was corrected in the authored draft to offer more English tutorials. Any future English long-form tutorial must be separately authored, narrated, fact-reviewed, rendered and approved, not invented in metadata.
- Both Short narrator IDs are distinct and both have correct-language SRT plans; actual genuine licensed distinct recordings, spoken audio/SRT synchronization and human bilingual review are still missing.
- `autopilot/phase3_quarantined_video_receipt.py` now hashes each lane's planned title, description, narrator identity, intended spoken language, caption/thumbnail language and authored script digest into each **unsigned local quarantine receipt**. It rejects an edited receipt that swaps a Hindi video into the English lane even if someone recomputes its unsigned SHA-256 hash. These receipts are technically useful but still unauthenticated, never publishing proof.
- `autopilot/test_phase2r3_audience_language_lanes.py` and extended `autopilot/test_phase3_quarantined_video_receipt.py` verify no cross-language captions/metadata, wrong narration, mismatched CTA, forged target language, or fake publishing approval.
- No account, OAuth, external source collector, voice model, billing, Analytics, or YouTube publisher is connected by this step. All records remain draft and `publishing_authorized=false`.

## Separate optimization/measurement later

When official YouTube Analytics access has been separately approved and verified, compare **Hindi Short performance against other Hindi Shorts** and **English Short performance against English Shorts**, using available per-video impressions, viewed-vs-swiped, average view duration, percentage watched, retention and subscribers. Do not pretend Analytics reveals each individual viewer's preferred spoken language or that Shorts reach can be restricted exclusively to a language group. None of those metrics exist in this draft; no fake growth numbers.

Potential review responsibilities: Hindi script/pronunciation/native metadata, English script/pronunciation/native metadata, fact/rights audit, clip sound-caption sync, and engagement analytics. These are planned roles; they are **not** autonomous connected agents or human reviews already executed.

## Remaining hard restrictions

**₹0/month recurring infrastructure**, public standard GitHub runners only, no Nirala/laptop, new account/provider/voice model download or charge without separate permission. No media-upload artifact or production D1 mutation, Google OAuth change, YouTube publishing, public scheduling or automatic audience-routing API call. Public PR #5 and release-controller PR #4 remain DRAFT and unmerged.

**21 tracked production acceptance subphases remain unfinished.** Correct separate-language packaging is one piece of authentic Hindi+English media production; it is not finished professional narration, human editorial approval, nor guaranteed delivery to a particular audience.
