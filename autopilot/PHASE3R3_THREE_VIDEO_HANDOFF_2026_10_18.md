# Phase 3R3/3R4 — Three original HD video / WAV / SRT handoff contract

**18 October 2026 | DRAFT technical gate; never upload or publish.**

## Source-checked integration

New \`autopilot/phase3_three_video_handoff.py\` creates an **immutable-by-digest technical input inventory** for the three currently authored CSV educational episodes:

| Episode | Visual | Narration lane | SRT |
| --- | --- | --- | --- |
| \`csv_tutorial_short_hi\` | 42s, 1080×1920, 24fps, 1,008 frames | Hindi narrator A | Hindi candidate |
| \`csv_tutorial_short_en\` | 42s, 1080×1920, 24fps, 1,008 frames | English narrator B | English candidate |
| \`csv_tutorial_long_hi\` | 432s, 1920×1080, 24fps, 10,368 frames | Hindi long narrator C | Hindi long candidate |

\`prepare_three_video_technical_handoff(...)\` takes **existing** local original silent MP4s, the unsiged quarantined actual-HD visual receipts, three declared full WAV takes with local rights documents, and separately supplied candidate SRTs with the exact original source words. It refuses missing or duplicate episodes, reused/missing/symlink input/output paths, cross-language metadata, wrong dimensions/frame counts, changed bytes and unauthorized release claims.

The call rechecks all three complete WAV receipts, rehashes every actual original silent MP4 and re-verifies the pixel/screenplay/lang-lane receipt, then passes each candidate SRT through the separate strict structural/text-binding gate. The result has SHA-256 for each input plus the whole episode bundle. It returns **no raw spoken scripts, caption content, private rights documents, access tokens or filesystem paths**.

**Important:** This function never creates or muxes media; it does not run voices, model downloads or outside connections. Its result is a technical intake boundary for later, explicitly authorized local-only full-duration mux testing.

## What this does NOT prove

- Three distinct WAV byte strings and three narrator labels **do not prove** different human voices, correct language, natural human narration, ownership, model/speaker consent, and legally reusable licensed commercial assets.
- A correct and plausible SRT with a valid digest **does not prove** accurate spoken-word/phoneme timing. Fake/recomputed SHA-256 can be supplied.
- Silent HD media with decoded signal samples does not prove quality of VFX, real-world demos, thumbnail professionalism, factual correctness, depiction rights or suitability for revenue.
- Local video/media receipt SHA and bundle SHA are **not trusted authentication or independent reviewer signatures**. No production transition is permitted based solely on this gate.

All source and results insist: \`mux_permitted=false\`, \`actual_word_audio_alignment_verified=false\`, \`legal_rights_authenticated=false\`, \`final_mux_generated=false\`, \`youtube_upload_or_publishing_authorized=false\`. Neither current public draft PR #5 nor separate release-controller PR #4 should be merged into automatic publishing by this result.

## Test boundary

\`autopilot/test_phase3_three_video_handoff.py\` uses explicitly **fake** video/audio/SRT bytes and mock low-level inspectors to test orchestration, source/episode binding and release authority. The existing independent standalone FFmpeg/FFprobe and PCM tests remain the evidence for actual media parsing. This is **not** proof of a complete full-HD narrated batch. Do not claim one.

## Remaining delivery gates

1. Source legitimate, naturally human-sounding three narration recordings in Hindi and English, with two audibly distinct Short voices and independently checked commercial reuse permissions.
2. Obtain true spoken caption timing, bilingual listening/editing reviews and signed editorial/media-rights approval. Retain owner restrictions.
3. Only then implement/test local **full-duration** quarantined mux technical adapter; inspect real MP4 H.264 + AAC, safely time-aligned subtitles, pronunciation, audio levels and full decode.
4. Authorize zero-cost sustainable cloud storage handoff, owner-bound OAuth/cloud state, publication idempotency and readback separately before ever scheduling/uploading to the intended FlowMinute channel.

Constraints: **₹0/month recurring cloud infrastructure**, standard public GitHub-hosted runner for existing isolated technical checks only; NO Nirala/laptop access, other desktop folders, external account/model connection, secrets in public CI, production D1 mutation, charge, OAuth scope, YouTube upload/scheduling/publishing. **21 remaining production acceptance subphases remain unfinished**; added gate is part of 3R3/3R4, not a subphase closure.
