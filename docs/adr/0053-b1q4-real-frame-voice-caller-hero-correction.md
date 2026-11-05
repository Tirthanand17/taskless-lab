# ADR-0053 — Branch 1 B1q4: replace generic waveform with original visual caller-provenance hero

**2026-11-05, Branch 1, review only. No YouTube remote changes.**

## Evidence from latest ACTUAL encoded MP4s

After PR #56 (audio-to-scene pause alignment) and PR #58 (bounded 12% hero zoom), the protected `main` GitHub workflow run [42019740264](https://github.com/Tirthanand17/taskless-lab/actions/runs/42019740264) succeeded. I downloaded artifact **13410588536** containing three genuine 1080×1920 24fps H264/AAC full-length MP4s, original PCM-synced SRTs, nine FFmpeg-decoded frame PNGs and one top-level manifest. All 21 subordinate files independently matched their manifest SHA256 and size. Read-only `ffprobe` confirms **38.686s** voice / **39.875s** photo / **46.517s** incognito.

Each video reports zero inter-cue hero-vs-original-PCM scene-start drift; visual ffconcat duration matches source PCM. Three real AAC diagnostics: voice **-18.37 LUFS / -4.65 dBTP**, photo **-17.89 LUFS / -3.01 dBTP**, incognito **-18.12 LUFS / -4.60 dBTP**. All three stream/container and source-captions checks passed. These are technical samples, NOT human full-watch, listening, fact or release approval.

## Actual visual critique

Nine independently viewed **ACTUAL decoded MP4** opening/proof/takeaway frames show that B1q3b did enlarge the topic art and eliminate the doubled full narration text, but the voice-safety opening still displays a free-floating, contextless waveform occupying only a small portion of a large empty canvas. It communicates generic sound, not the immediately recognizable phone-caller impersonation scenario. The other two topic openers are still schematic but distinct; do not simultaneously change multiple topics before visual review and matched audience measurements.

## This single visual change

- For original `fm_20261105_ai_voice_cloning_callback_short_en` first-third scene beats only, replace the anonymous waveform with an **original fictional incoming voice-call phone scene** and a separate static **IDENTITY / UNVERIFIED / CALL BACK FIRST** annotation. Within the phone, the original waveform is a subordinate *finite* audio clue, not a stock loading ring or central animation.
- The composed phone uses dark dimensional layers, warm pink-vs-neutral highlights, bounded phase-based finite slide/reveal motion, no `arc`/`ellipse`, no copied app interface, contact name, or claim that software detects AI voices.
- Do **not** change original exact source episode, narration words, fact approvals, SRT/ASS implementation, third-party licensing, original writer voice profiles, 24fps encoder, B1q2b pause-inclusive visual timestamps, other video titles, or private YouTube video IDs.
- Existing source visual proof safely crops only y495–1383, leaving top heading and bottom native ASS y1410–1650 unchanged. The call panel fits within the hero crop at all finite motion phases.
- Added physical 1080×1920 tests for three actual animation phases, topic diversity and native subtitle-safe top/bottom; integrate in existing B1q3b PR CI to avoid duplicate expensive jobs.
- Once *green*, trusted main-only existing three-MP4 CI may rerender, retain nine genuine encoded review frames. Do not claim improved encoded art until physically reviewed.

## Release and evidence boundary

All revised source art and real MP4s are **owner-unapproved**. The original Nov5–7 scheduled videos are not modified, deleted, reuploaded, canceled or rescheduled by this code. GitHub has only four historical Nov5–11 scheduling receipts of 21 expected slots; the remaining 17 are UNKNOWN, not proof of a YouTube scheduling gap. Existing future private uploaded files cannot be binary swapped at same YouTube video ID. Actual current-owner read-only `videos.list` and owner exact-new-MP4 fact/rights/voice/full-watch approval are still required before any private replacement and old-schedule change.

### Next single-factor engagement loop

Once release rights and remote state are known, compare age/topic-matched engaged views, average view duration and retention using genuine account metrics; don't infer increased retention from visual appearance alone. Avoid repeated changing of the scene style before one observation cycle. Engineering readiness stays conservatively at **40/100**; **0 actual unattended replacement publications verified**.
