# Phase 3R2 — independently supplied SRT timecode candidate intake

**18 October 2026 | Source branch PR #5 remains DRAFT / UNMERGED.** No publishing, no external service, no AI voice download and no user laptop used.

## Implemented, bounded software gate

- \`autopilot/phase3_caption_candidate_intake.py\` validates an explicitly supplied, local, ordinary UTF-8 SRT for each existing *original* Hindi Short (42s), English Short (42s), Hindi long (432s). No caption generation is claimed here.
- A candidate must be linked to the original episode ID, narrator plan, audience spoken language, bounded *full-duration* WAV technical receipt and actual WAV hash, plus exact SRT-byte SHA-256. The three-video wrapper re-inspects all three separately supplied WAVs using the Phase 3R1 full-take gate.
- The exact original spoken source text must be preserved **word for word** in the same order, across every submitted subtitle cue. The current source draft itself and its SHA-256 are checked; changing the screenplay makes the old receipt invalid.
- Cues require strict sequential SRT numbering, exactly one text line, UTF-8 without BOM, no unsafe markup/bidi override/control text, non-overlapping monotonic timestamps, max 90 characters, 250 ms–6 s cue durations, bounded gaps and actual WAV runtime. The parser rejects extremely early subtitle cutoff.
- The directly screenplay-estimated \`.draft_estimated.srt\` must **not** be relabeled as real aligned speech; an identical draft hash is denied. The SRT is never copied to a public CI artifact by this module, and the inspection report contains hashes and metadata only.
- All results retain \`actual_spoken_words_recognized=false\`, \`true_speech_to_caption_alignment_verified=false\`, \`independent_language_listening_review_verified=false\`, \`licensed_voice_and_asset_rights_verified=false\`, \`ready_for_mux=false\`, \`ready_for_upload=false\` and \`publishing_authorized=false\`.

## Crucial evidence boundary

Changing a cue by 50 milliseconds **does not** establish speech-to-text synchronization. A malicious submitter can calculate new file hashes and forge unreviewed source claims. This gate validates **structure and binding**, not actual speech/audio synchronization, identity, naturalness, pronunciation, legal rights or signed human approval.

Tests deliberately use a **shifted screenplay-derived SRT** and *fake WAV hashes* to check code paths, and never assert that those fixtures are genuine recordings. No voice has been synthesized or acquired; no actual human-reviewed subtitle file has been obtained.

## Required subsequent work (unchanged)

1. Owner-approved legally commercial-reusable separate English/Hindi natural narrations with **two audibly distinct Shorts voices**; actual complete WAV files from a permitted source (not currently available).
2. Inspect final audio + actual caption timing with a legitimate, independently checked human/forced alignment method; compare heard words/pronunciation and on-screen timing to the original source. External model/providers/accounts require separate authorization.
3. Obtain independent bilingual editorial verification, evidence that rights for all narration/visuals/music are legitimate, and a trustworthy signed/reviewed final muxed MP4 before considering a production release.
4. Resolve authenticated owner-held Cloudflare/YouTube OAuth/storage and durable publication-status readback on the independent release-controller branch. Until then, no YouTube upload, scheduling or publishing.

The owner's cloud recurring infrastructure budget is **₹0**. GitHub-hosted public standard runners only; no Nirala/desktop, new payment, external provider connection, storage purchase, OAuth scope, remote publishing or account mutation. **The existing 21 production acceptance subphases remain open** (a technical partial subgate does not close any whole subphase).
