# FlowMinute Lab: standing voice casting & quality policy (effective October 18, 2026)

Every daily pack MUST use different identifiable narration voices on the morning and evening Shorts: **Short A voice != Short B voice**, confirmed by the generated per-episode voice QA JSON and consistent with the actual encoded audio.

The audio remains SYNTHETIC: describe it as natural-style, not as a human recording. Avoid impersonation of real people, brands or celebrities. Use approved Kokoro Apache-2.0 offline TTS voice IDs (or another authorized provider without paid billing). Examples Oct18: morning Short `af_bella`, evening Short `am_michael`, long `af_heart`.

## Readability and speech direction
- Distinct speakers should sound conversational and have different delivery: warm curious voice on the first Short, grounded explanatory voice on the second.
- Short scripts should sound spoken (contractions, pauses and concrete nouns), not a list of formal sentences. Aim approximately 32-55s including breathing room.
- Narration should fully finish before the last MP4 sample; voice QA and decoded MP4 length with a 0.75s minimum intended tail.
- Full encoded media decode, peak level, clipping/silence gates, sampled frame inspection and title/source QA before upload.
- **Last card must match the actual spoken comment question verbatim.** Oct17 had a mismatch; future checks need to compare editorial script question to final visual card.
- Long uses another approved voice and a practical task with clear visual contrast; no misleading simulated UI described as a live product test.
- Each Short must stand alone; never reuse identical filler just to hit quota. Avoid overused topic repeats.
- Every publishing job independently confirms remote channel ID, private status, processingSucceeded, thumbnail where required, exact publishAt via authenticated YouTube read-only API, preserving idempotency.
- Final source files and receipts live in GitHub, production media only under `youtube con`.
