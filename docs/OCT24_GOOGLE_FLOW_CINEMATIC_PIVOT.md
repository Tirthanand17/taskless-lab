# FlowMinute Lab — Pivot to Google Flow cinematic AI video (23 October 2026)

## Decision

Stop using the procedural VTK spherical mannequins for **public-facing** FlowMinute videos. Keep numerical IK tests and draft renderer only as a motion/blocking reference, if useful. The user's reference screenshot clearly misses premium human anatomy, believable faces, clothes, lighting and cinematic voice.

**Recommended default: Google Flow's Characters feature + Gemini Omni 1.1 Flash.** Supplement with Veo 3.1 in Flow for particularly cinematic shots only if available within existing credits. Set style using original reference images, saved consistent characters, voice reference and an actual story action in every scene. These tools produce raster video that can *look like cinematic 3D*; they do not automatically provide editable rigged Blender mesh assets or guarantee perfect continuity.

### Why this is grounded in primary sources

- Official Google Flow help: Characters can package visual and voice references for reuse in clips: https://support.google.com/flow/answer/16935308
- Official Google Flow help: Flow supports Ingredients, reference images, saved voices, and directions per clip: https://support.google.com/flow/answer/16353334
- Official Google Flow models: Gemini Omni Flash 1.1 supports 4/6/8/10 seconds, both aspect ratios, image references, first/last frame, and 10s video-to-video: https://support.google.com/flow/answer/16352836
- Google's August 2026 Omni update: upscaling and video editing controls: https://blog.google/innovation-and-ai/models-and-research/google-labs/new-creative-controls-google-flow/
- Flow credits: 50 daily credits even without subscription; Pro has 1,000 additional monthly credits; Omni 720p 10s is 15 credits, 360p 10s is 7 credits; platform UI costs may change: https://support.google.com/flow/answer/16526234
- Project Genie is Ultra-only and builds interactive worlds, **not the practical solution** to repeatedly generate educational YouTube explainers: https://support.google.com/labs/answer/16875695
- The old Veo 3.1 **Preview API** retired on **22 October 2026**, while consumer Flow has Veo/Omni. API generative-video usage is separately metered and not included in the Pro UI credit pool: https://ai.google.dev/gemini-api/docs/video and https://ai.google.dev/gemini-api/docs/pricing

## Existing ₹0-new-spend constraint

User has said they have a Gemini/Google AI Pro subscription. **Do not assert the subscription or balance is currently verified**; check the same Google account in Flow before generating. Existing subscription benefits don't authorize purchasing API video generation, Google Cloud credits, new subscriptions, or a paid upgrade.

Initial reference **pilot:** one 10-second Omni Flash 720p clip (15 Flow credits at published current rate). Higher-quality drafts can use 360p (7 credits for 10s), with upscaling if user plan permits. Do not let one click generate multiple variations unnoticed.

Three-episode **creative full-key-shot plan** is in `content/flow/oct24_cinematic_flow_scene_package.json`: 5 clips English Short + 5 clips Hindi Short + 6 clips Hindi long = **16 ten-second clips**, ~240 Flow credits before retries. All shots are **NOT_GENERATED** and have null provider asset IDs. That is a quality-test scenario, **not sustainable daily generation**. To maintain a three-video-per-day cadence, use fewer AI-generated cinematic anchor shots per day (e.g., one clip per Short and three for the long video = 5 ten-second clips, ~75 credits/day before retries) and fill teaching beats with real screen demonstrations, reviewed narrated diagrams, motion graphics and illustrations. At 50 daily credits plus 1,000 monthly (when Pro active), about ~83 credits/day averaged over a 30-day month is a theoretical ceiling assuming no unused days; not a verified available balance or guaranteed quality.

Do not spend all credits on the first video. No guarantee that model availability, daily/monthly pool usage, retries or video output quality will match these estimates.

## Workflow for real engagement

1. In `https://labs.google/fx/tools/flow`, verify Google account, active Pro benefits and actual available credits. No second signup or payment method.
2. Use **Characters** to create original canonical Asha, Jay, Kabir, Riya, Omar from reference stills; preserve voice, face, wardrobe and rights. Start with only two characters in the 10-second pilot. Keep wide/closeup avatar reference shots saved.
3. Generate pilot by **Gemini Omni 1.1 Flash → Ingredients/References**. Upload reference characters plus a clean set photo. Explicitly request 10s, appropriate 9:16/16:9, one meaningful moving physical prop and a single short spoken sentence (language-specific).
4. Inspect video in mobile-size view for face consistency, hands, object geometry, believable physics, natural voice, exact claims, and correct identity. Reject if clip drifts or invents unsupported details. Avoid raw on-screen caption generation because it frequently produces typographic artifacts; add reviewed subtitles in compositing.
5. If pilot good, create a small number of cinematic anchor shots and edit/reuse consistent characters. For English/Hindi versions, create independently reviewed narration and subtitles; do not machine-translate unreviewed factual claims.
6. Combine with real software demonstrations and visually honest explanatory diagrams for learning value. Cinematic scenes should support actual teaching, not replace it.
7. Cross-check independent fact/visual QA, rights, final 1080p media decode and real YouTube receipt; only then publish/schedule.

### What this does NOT solve

Flow web/UI creative credits are **not a validated 24/7 cloud API**. The channel's laptop-independent daily auto-render-and-upload remains an engineering workstream. Using paid Gemini API, Flow browser automation, credit-bearing background work, or a new third-party video service requires explicit additional authorization and budget confirmation. No credentials were requested or stored here.

**Release status:** 0/16 Flow clips generated; 0 uploaded; October 24 videos not scheduled. The prior low-poly previews remain technical experiments only.
