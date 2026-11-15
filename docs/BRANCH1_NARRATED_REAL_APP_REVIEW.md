# Branch 1 — Narrated real-software Shorts, review only

**Purpose:** finish the next free-first growth-recovery engineering integration, using **actual** first-party LibreOffice Calc and Chrome recordings as every app-related video pixel source, rather than simulated screenshot cards. Output is a proof-first original narrated Short with complete SRT + burned-in ASS captions, no YouTube publication.

**Current user boundary:** Do not schedule new videos. Do not change the already scheduled November 14–18 uploads. Do not purchase software or store project media on a user laptop. No owner approval, final creative signoff, rights signoff or upload consent is inferred from a passing test.

## What is implemented

- Existing real GUI captures from PR #240 are re-created *on the same ephemeral GitHub runner*, with first-party dummy data and rigorous app state checks: an actual LibreOffice Calc text match and real Chrome built-in Notification Settings (without modifying permissions).
- `autopilot/branch1_narrated_real_app_short.py` validates exact source receipt before recording narration, hashes original source and complete created media. The source-based story uses distinct proof, before, cause, fix, payoff chapters with true app recording underneath, not synthetic product UI.
- Voice: existing Kokoro ONNX 0.6.1 `af_heart`; only upstream pinned model and voice binaries with SHA-256 checks. No subscription.
- Story: five individually written chapters per app, with a result visible at frame zero, then the actual before/action/after source windows. Original chapter headers and safe captions overlay the real software. Real source footage is only **10 seconds**; this pilot may hold genuine frames for longer than source actions. This is **not** proof of ideal pacing and should be rejected if human review finds it dull.
- The original **PCM voice**, source timed SRT, native ASS captions and original H.264/AAC narrated MP4 are generated with FFmpeg. The final encoded AAC is measured independently for integrated loudness/true peak using the existing strict B4G5 verifier; one source-preserving remaster is permitted only for the verifier's specific out-of-band loudness failure.
- Media proof uses SHA-256 of exact original app screen MP4, app receipt, voice model identifiers, generated WAV, captions and narrated MP4; checks real video dimensions, one AAC audio stream, full decode, duration agreement and strict no-release flags.
- Separate `.github/workflows/branch1-narrated-real-app-review.yml`: on PR, source-only unit tests and refusal of forged release; manually dispatched on **main**, physically captures both apps, produces voice/edited video, verifies final files, stores **3-day review-only artifacts**; no OAuth, channel uploads, scheduling, analytics exports, personal information or user PC media.
- Adversarial tests forbid fake story, malformed chapter labels, impossible source windows, altered receipts, false consent and local/laptop execution.

## Review and factual integrity

This is **LibreOffice Calc**, not Microsoft Excel; the Calc example shows an actual leading-space mismatch and a `TRIM` correction. Chrome example **opens** the actual Notifications Settings page but does **not** change any notification permission. The voice makes only those limited claims. Neither example contains real account data.

Use the GitHub Actions artifact to visually check that the **source app is legible on a phone**, the subtitles do not obstruct critical controls, synthetic speech sounds natural and exactly matches the displayed action, and the payoff arrives early. A successful audio checksum or CI score is not a substitute for a person watching the entire resulting video. Review may require lengthening the real software recording and reshooting the narration/visual timings to remove frozen frames.

## Local source-only command (for CI)

`python -B -m unittest -v autopilot.test_branch1_narrated_real_app_short autopilot.test_branch1_real_app_capture autopilot.test_branch1_recovery`

After a successful authorized main-branch render, the exact resulting media can be independently checked with:

`python -B -m autopilot.branch1_narrated_real_app_short --app calc --verify --source /tmp/flowminute-actual-calc --out /tmp/flowminute-b1-narrated-calc`

`python -B -m autopilot.branch1_narrated_real_app_short --app chrome --verify --source /tmp/flowminute-actual-chrome --out /tmp/flowminute-b1-narrated-chrome`

## Remaining before any future release

1. Inspect and listen to both complete videos. Verify no misleading words, source visual mismatch, unreadable zoom, inappropriate loudness or long static shots.
2. Improve genuine action coverage with longer custom real-app recordings and real cursor zoom/highlight where it helps. Do not substitute decorative motion.
3. Verify product-specific claims against current official vendor documentation and accurate brand identities.
4. Create a separate, explicit **exact-final-media** human signoff for facts, rights, voice and YouTube scheduling authorization.
5. Evaluate success only after real YouTube publication with accurate per-video **Shorts stayed-to-watch**, retention and subscriptions, at comparable age windows. The baseline 21.2% is a past channel observation, **not** evidence this prototype has improved distribution.

**Cost incurred in purchased tools: ₹0. Scheduled videos from this workflow: 0.**
