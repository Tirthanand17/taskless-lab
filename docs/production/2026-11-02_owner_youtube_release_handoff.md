# FLOWMINUTE LAB — owner-requested YouTube release handoff, November 2, 2026

Status: **RELEASE REQUEST RECORDED; NOT UPLOADED / NOT PUBLISHED / NO YOUTUBE VIDEO IDs.**

## Explicit owner request
The creator said: "i saw the good to upload for today. so continue to upload", referring to the last English V6 and Hindi V2 review videos shared in the project chat. Treat this as owner acceptance of the two *video previews* and express intent to publish on November 2, 2026. This sentence **does not independently establish separate voice naturalness, exact caption text, rights clearance and factual review sign-offs**.

## Exact, locally verified assets
English:
- `FLOWMINUTE_ENGLISH_V6_AUDIO_MASTER_REVIEW_ONLY.mp4`
- SHA256 `1f1a740002aa035a1eaed8c7a308831efe0ea6a8950c61337ceaafda3a9386fc`
- 1080x1920, H.264 video with AAC audio, 29.9 seconds; full FFmpeg decode PASSED (local verification 2026-11-02).
- English captions from bilingual source ZIP: 13 original phrase-aligned SRT cues.
- Production receipt source: `docs/production/2026-11-02_flow_explain_bilingual_motion_and_hindi_review.md`.
- Owner-approved metadata: `content/episodes/fm_20261102_agent_permissions_short_en.json`.
- Manifest: `state/approvals/fm_20261102_agent_permissions_short_en.json` (exact approved candidate hash; four remaining human gates deliberately FALSE).

Hindi:
- `FLOWMINUTE_HINDI_V2_AUDIO_MASTER_REVIEW_ONLY.mp4`
- SHA256 `ba27ed6b3af872b3c5973f4b371c6ff8abfb7885929def88d9e16dc890c0f772`
- 1080x1920, H.264 video with AAC audio, 37.1 seconds; full FFmpeg decode PASSED (local verification 2026-11-02).
- Hindi captions from bilingual source ZIP: 13 original phrase-aligned SRT cues.
- Owner-approved metadata: `content/episodes/fm_20261102_agent_permissions_short_hi.json`.
- Manifest: `state/approvals/fm_20261102_agent_permissions_short_hi.json` (four remaining human gates deliberately FALSE).

Note: The two exact approved mastered MP4s are currently **conversation sandbox assets**, not GitHub repository assets or GitHub Actions artifacts. The GitHub Actions original outputs have **different hashes** and must not be substituted for these files under the owner's approval.

## Publication and access verification
- The *strict* repo workflow `.github/workflows/publish-artifact-youtube.yml` requires an authorized manual workflow_dispatch from `main`, environment `youtube-production`, `vars.PUBLISH_ENABLED == 'true'`, exact future UTC `publishAt`, a source render artifact, five individual affirmative human approval flags, verified final MP4 SHA, expected channel ID `UCCcL9Q_jqVq6LJmnYUSAFZA`, and YouTube API readback.
- This chat's connected GitHub tools can read/write GitHub files, **but do not provide a workflow_dispatch action**. No direct authenticated YouTube video uploader connected to this chat was found.
- Live GitHub secret, repository variable and owner's YouTube OAuth state were **not readable or newly verified**.
- The control repo `Tirthanand17/flowminute-control-private/config/policy.json` at November 2 check contains `publishing_enabled:false`, `require_exact_publish_at:true`, `monthly_budget_inr:0` and `allow_laptop:false`. Versioned config is not proof of live GitHub variables or account state. We have **not toggled anything**.
- The older `.github/workflows/publish-youtube.yml` targets the unrelated `pilot_001` assets and bypasses the stricter exact-video approvals. Do not invoke it for these Shorts.
- The current Python uploader still hardcodes caption uploads as English. Hindi captions must be fixed/tested before using this pipeline; do not upload mislabeled Hindi captions.
- The project rules also require original rights-safe audio/video; synthetic speech must be disclosed where applicable. The videos demonstrate simulated action requests, not access to real files.
- No new paid credits, Desktop/Nirala, added providers or actual YouTube posting performed.

## Safe next release path
1. Confirm/record separate human approval of audible narration and precise captions for both languages; perform a verifiable factual and rights review of the exact two mastered MP4s.
2. Close GitHub main/PR integration and publishing policy gaps without weakening the fail-closed workflow. Preserve existing source artifacts and deduplicate unknown prior uploads.
3. Make exact mastered MP4 and captions available to authorized GitHub publication job with immutable SHA and durable retention or regenerate exact approved bytes with owner reapproval.
4. Authenticate the correct YouTube brand channel using existing OAuth infrastructure and verify write permission, budget, privacy and publishing environment.
5. Use only approved strict publishing path, scheduled in permitted time window; the current workflow rejects immediate public posts. Confirm remotely via YouTube video ID, correct channel, processing status, captions, private schedule and eventual public visibility.
6. Write back signed/corroborated release receipts and analytics triggers. Do not claim success based on workflow start or an uploaded browser screen alone.

## Owner's alternative today
A ready-to-upload convenience bundle `FLOWMINUTE_LAB_2026-11-02_OWNER_UPLOAD_HANDOFF.zip` was prepared and provided **in the conversation**, containing exactly the approved mastered MP4s, 13-phrase SRT per language, titles/descriptions, and still-image covers extracted from the video frames. It is **not in GitHub**. Owner can independently upload through their authenticated YouTube Studio after their own review. If they do, YouTube video ID(s), actual visibility and timestamp must be reported and reconciled in the repository. No such claim is currently made.

**This handoff is an honest blocked release record, not permission to fabricate gate completion or modify policy to force posting.**
