# FLOWMINUTE LAB — Motion, Voice and Sound Finishing Standard
Updated 2026-11-03 after original QR-fraud Short `fm_20261104_parking_qr_sticker_scam_short_en`

**Purpose:** Make future vertical Shorts and 16:9 explainers more watchable, paced and professional, without borrowing copyrighted music or waiving the project's fact-check, ownership, review or publishing controls.

## 1. Verified source-driven story
- Start with a verifiable, surprising single takeaway; gather primary sources before scripting. For the November 4 QR-scams episode, FTC's September 2026 public notice and FBI/IC3 QR tampering advice directly support the sticker/URL/official-site claims.
- Narrate conditional risks accurately: a QR image itself does not steal credentials; following a malicious URL and providing information can do harm.
- Label illustrations as synthetic/nonfunctional. Never put a scannable payment QR code, live phishing URL, personal information or fake "actual demo" claim on screen.
- Put primary source links in the description. No implied endorsement by named companies or agencies.

## 2. Visual animation by format
| Aspect | Shorts (9:16) | Long (16:9) |
|---|---|---|
| Delivery size | 1080 × 1920 | 1920 × 1080 |
| Narrative beats | 1 distinct beat per ~3–7 seconds | ~10–30 seconds with chapter transitions |
| Text | Very short kinetic hook, 1–2 lines of bold large text | More room for diagrams, comparisons, labels and transitions |
| UI safe space | Keep headline/art away from right-edge icons and bottom overlay; place subtitle cards inside safe central lower third | Keep captions and chapter labels inside 5–8% screen margins |
| Motion | Scene-locked scan beams, wipe/reveal, subtle parallax, sticker peel and 0.14 s cross-dissolves | Restrained pans/zooms, clear diagrams, scene transitions tied to narration |
| QA evidence | Storyboard contact sheet, visual check of every scene, exact frame count | Key chapter contact sheet + narrative/text QA |

Use original drawn graphics or properly licensed assets. Avoid repetitive static slides: subtle motion should explain the concept, not distract.

## 3. Voice and original sound design
- Use original/approved narration with correct locale. Available Kokoro voice weights are Apache-2.0 according to the publisher's model card: https://huggingface.co/hexgrad/Kokoro-82M.
- Preserve a conversational voice; prefer subtle high-pass filtering (around 90 Hz), gentle compression or gain and natural spoken pauses. Do **not** make claims of a real human voice recording.
- Write a different, appropriate original ambient harmony and rhythm for each episode. For cyber-safety Shorts, the November 4 example uses a fully original 96-BPM, D-minor electronic pad/soft pluck bed with smoothly faded chord boundaries. For instructional long videos, repeat a quieter recurring motif across chapters and remove it under technical audio examples.
- Keep soundtrack clearly below the voice (commonly 18–24 dB softer in level, judged by ear and verified with rendered audio). Duck ambient music while the narrator speaks; add only subtle synced SFX on meaningful visual events, e.g. scanner ping, sticker peel, URL preview tap, caution tone and resolution.
- Synthetic sound effects use procedural synthesis (no third-party samples); original musical notes and composition were authored for the episode. A YouTube Audio Library source is an alternative only after checking attribution/license requirements: https://support.google.com/youtube/answer/3376882.
- Working internal finishing goals (not platform requirements): short-form integrated loudness near `-15 LUFS`, long-form around `-18 to -16 LUFS`, and true peak comfortably below `-1.5 dBTP`. Don't apply aggressive normalization to speech-only examples; always inspect actual output.
- Final November 4 2026 Short measured **-15.0 LUFS**, **-3.4 dB true peak**, duration **35.9 seconds**, AAC stereo at 192 kb/s. It used 7 precisely aligned sound cues and no external audio sample.

## 4. Captions, rights and technical QA
- Generate phrase-timed SRT from the actual narration segments; verify every sentence against the supplied narration, each timestamp increasing and within the final film duration.
- Use H.264 MP4 + AAC stereo; full video/audio decode must pass. Preserve a recorded SHA-256 of the **final** mastered MP4, not an earlier pre-master version.
- Check subtitle language and remote caption `serving` status on YouTube. Respect vertical/horizontal distinction: Shorts custom-thumbnail API changes are not generally equivalent to long-form thumbnail handling.
- Save original script, source verification, rendered QC, exact MP4 hash, audio loudness measurements, source-rights note and contact sheet; never mark human listening/watching as completed unless the user actually confirms it.
- The QR short's 7 original motion scenes, generated WAV mix, storyboard and exact SRT are in `C:\Users\Dell\Desktop\youtube con\nov04-qr-trap-production`; the final approved hash is `8f097faad8b224999c86b844474e2c2156497e188cba3a5ca14047710bcf007c`.

## 5. Fail-closed publishing and evidence
- Follow the private control repo. If general publishing is disabled, do not change it; new publication requires a fresh, narrowly-scoped, exact-hash authorization.
- Pre-check exact title/topic duplicates and collisions with `publishAt` on the correct authenticated channel.
- Upload privately. Wait until `uploadStatus=processed` and processing is successful; then schedule the exact future UTC release time.
- YouTube may momentarily return missing/stale `publishAt` after a successful schedule update. **Never blindly repeat a schedule or upload**. Reconcile through read-only authenticated `videos.list`, then update the local release ledger from that response.
- Upload SRT only after verified narration/caption QA; confirm `captions.list` language and `serving` state.
- Commit a concrete video ID, scheduled time, privacy, processing and caption receipt. Consume/close the one-time permission. After the scheduled time, independently confirm the video became public; a private scheduled receipt alone does not prove public release.

## 6. November 4 reference result
- Episode: `fm_20261104_parking_qr_sticker_scam_short_en`
- Final title: "Fake QR Code at Parking? Spot THIS Before You Pay! #Shorts"
- YouTube ID: `6kSCllTcrDo`
- Scheduled: **2026-11-04T15:00:00Z = Nov 4, 2026, 8:30 PM IST**, private until scheduled release
- Original rendered duration 35.9 sec; 7 animated scenes and 7 accurate English SRT captions; authenticated remote processing and caption status verified; no copyright-bearing external music
- Correct channel: `UCCcL9Q_jqVq6LJmnYUSAFZA`

*This is a production and security quality baseline, not an instruction to enable unrestricted publishing.*
