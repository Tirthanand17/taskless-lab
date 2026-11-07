# ADR-0106 — B4h4 numerical AAC readback before ephemeral media deletion

**2026-11-07 IST | Branch 2 | no publication, no new encode**

## Evidence gap
The normal full-episode workflow already measures and validates *actual final encoded* AAC (B4g5), including SHA-matched media, EBU R128 LUFS, 192-kHz oversampled true-peak and cross-video spread. However, GitHub's normal daily run summary exposed mostly full H264/AAC decode and PCM scene counts; the separate B4f4 signal and B4g4 owner reports were intentionally restricted to explicit one-day public MP4 artifact opt-in. A reader could wrongly interpret their skipped state as no final audio measurement at all.

## Decision
- After the existing three-video full physical render and B4g5 checks, verify the **existing** ephemeral B4e1 JSON on the GitHub runner in a short numeric-only step. No additional TTS, FFmpeg encode, network, copyrighted audio, or external API.
- Independently reconcile three distinct MP4 SHA-256 identities against the nested post-encode measurements, real PCM durations, exact 4/9/4 scenes, finite LUFS/true peak/LRA within the already-established *internal engineering* limits, and the <=4 LU cross-episode spread.
- Report only AM Short / Long / PM Short and numeric final AAC loudness/peak/range, real PCM durations, and peak caption reading rates to GitHub Actions **step summary**. Never print or retain MP4 hashes, source titles, article URLs, scripts, audio, captions, or source text.
- A fast-caption pacing number is only a **human-review warning**. Original owner's approval, media rights, evidence-linked claims, real-world accuracy and platform compliance are *not* inferred.
- The existing explicit human video review remains manual and separate; no artifacts or secret variables are added. The old B4f4/B4g4 optional owner diagnostics stay protected. Data and pinned model weights are purged as before, including after errors.

## Required evidence
Four exact-head CI checks (including mock rejecting forged authority, mismatched digest, re-used same MP4 hash, fake R128/LUFS and NaN), then a real main-branch no-publish three-MP4 run displaying numeric results. Never claim it ran in production from PR tests. No progress/readiness increment without new owner/protected YouTube evidence.

**Readiness remains 45/100; actual verified unattended 21-release target remains 0/21.**
