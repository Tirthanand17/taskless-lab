# Requested three-video YouTube publication — 2026-11-02

**CURRENT STATUS: BLOCKED; NO UPLOAD, SCHEDULE OR VIDEO ID.**
The owner explicitly requested: "i already provided api so directly trough that publish one by one 2 shorts and one long video." They previously watched the most recent English and Hindi Short previews and accepted them for upload.

## Release queue (owner-requested order)
1. **English Short (approved preview)**
   - Content manifest: `content/episodes/fm_20261102_agent_permissions_short_en.json`
   - Owner consent/remaining gate record: `state/approvals/fm_20261102_agent_permissions_short_en.json`
   - Exactly owner-reviewed mastered video: `FLOWMINUTE_ENGLISH_V6_AUDIO_MASTER_REVIEW_ONLY.mp4`; SHA256 `1f1a740002aa035a1eaed8c7a308831efe0ea6a8950c61337ceaafda3a9386fc`; 1080x1920 H.264/AAC, 29.9s.
   - Caption track: `flow-explain-english-phrase-captions.srt`; 13 phrases; exact timing in review ZIP; independent caption approval not separately completed.
   - Status: OWNER_PREVIEW_ACCEPTED; credential/publishing gate BLOCKED; YouTube video ID: NONE.
2. **Hindi Short (approved preview)**
   - Content manifest: `content/episodes/fm_20261102_agent_permissions_short_hi.json`
   - Owner consent/remaining gate record: `state/approvals/fm_20261102_agent_permissions_short_hi.json`
   - Exactly owner-reviewed mastered video: `FLOWMINUTE_HINDI_V2_AUDIO_MASTER_REVIEW_ONLY.mp4`; SHA256 `ba27ed6b3af872b3c5973f4b371c6ff8abfb7885929def88d9e16dc890c0f772`; 1080x1920 H.264/AAC, 37.1s.
   - Caption track: `flow-explain-hindi-phrase-captions.srt`; 13 phrases. Publisher currently hardcodes English caption language, so correct that before upload.
   - Status: OWNER_PREVIEW_ACCEPTED; credential/publishing gate BLOCKED; YouTube video ID: NONE.
3. **Hindi long-form explainer on the same AI-agent permissions topic**
   - Editorial concept: "AI Agent को कितनी Permission दें? Read-only, Approval और Backup का practical demo".
   - Desired release: original, independent 16:9 tutorial with genuine detailed worked example and natural spoken Hindi; NOT the previous silent 90-second panel draft; must have separate factual/rights/creative approval.
   - No verified completed long-form MP4, SRT, hash-pinned release manifest, or signed approval from this task. Existing older long-form records are different episodes and MUST NOT be substituted or republished.
   - Status: NOT RENDERED/NOT APPROVED; YouTube video ID: NONE.

## The user's API credentials
The project has a GitHub Actions uploader that uses `YOUTUBE_TOKEN_JSON` from a protected environment. Credentials are not exposed to the ChatGPT runtime or GitHub code connector. There is no connected YouTube write/upload action or connected GitHub workflow-dispatch action available to this conversation. Do **not** ask user to paste a token into chat or expose it to public code.
- Private control repository `Tirthanand17/flowminute-control-private/config/policy.json` has `publishing_enabled: false` on 2026-11-02.
- Source repo workflow `.github/workflows/publish-artifact-youtube.yml` on `main` currently offers manual `workflow_dispatch` inputs; older direct publisher offers potential fail-open public uploads. Do not select it.
- Stricter production workflow on the draft PR #6 branch requires exact hash, complete five real human approvals, correct target channel, future UTC private schedule and YouTube API readback; it is not merged to main.
- App-level GitHub connector supports source edits and read-only workflow evidence, but not GitHub Actions workflow dispatch or GitHub production secret materialization. No API POST / YouTube write call was made.
- The reviewed mastered binaries are present only in the ChatGPT conversation sandbox / the owner's upload ZIP, not in authorized GitHub Actions published artifacts with matching SHA. GitHub-generated review originals have **different hashes** and cannot be substituted.
- Existing control policy also mandates `require_exact_publish_at:true`, `require_licensed_media:true`, `require_remote_youtube_processing:true`, `allow_unreviewed_srt:false`, budget INR 0, and no laptop.

## Safe follow-through without bypass
- Do not turn on global publishing or add a push-triggered production-secret job on an unreviewed branch.
- First resolve the already-identified publisher gates, owner review of exact two files, immutable artifact staging, correct Hindi SRT language and main/branch integration with test coverage.
- Obtain the third long-form approved media, not an old or silent prototype.
- Use existing authenticated protected environment to schedule each approved video serially, with exact channel ID `UCCcL9Q_jqVq6LJmnYUSAFZA`, SHA-pinned content and idempotent receipts.
- Reconcile via authenticated YouTube API for each video ID, processing status, correct captions, scheduled/published visibility, then write the confirmed receipts.

**Never assert "uploaded" or "published" without a real authenticated YouTube response and readback. Owner consent is recorded; technical and mandatory release controls are still in force.**

## Follow-through update: caption safety fixed and Hindi long-form production started

- Fix committed `6cdd8ab3597d7e8659da9a2b212f298d360b92d9` to `scripts/publish_youtube.py`: YouTube caption tracks now derive `language` and `name` from `meta.language` ('en' -> English, 'hi' -> Hindi), and missing/unsupported SRT configurations fail before a remote upload.
- No-secret regression tests `scripts/test_publish_youtube_preflight.py` and `.github/workflows/flowminute-youtube-publisher-preflight.yml` confirmed successful on PR/push for commit `de76f35a869aee880309dd47f4d200ab010b3f13`. The tests confirm both desired Shorts remain fail-closed because four individual approval gates are still false.
- Original Hindi longer-form lesson script `content/flow/agent_permissions_long_hi_narration.json` includes 6 chapters and 29 distinct spoken paragraphs; simulated files only. Long-form Remotion component `motion-v2/src/AgentPermissionLongHi.tsx` is a separate 1920x1080, 24 fps dashboard lesson rather than a stretched Short.
- `scripts/generate_flow_explain_long_hindi_voice.py` emits a separate `hf_alpha` synthetic Hindi narration, phrase-based SRT and chapter timings; `.github/workflows/flowminute-hi-long-full-render.yml` is **review-only** and has no publication action/secret. The dedicated layout smoke passed: https://github.com/Tirthanand17/taskless-lab/actions/runs/41431664151 .
- Full Hindi long-form audiovisual build started here: https://github.com/Tirthanand17/taskless-lab/actions/runs/41431772149 . **Build initiation is not proof of success; final media, voice performance and approvals must still be independently checked.**
- Existing production control `publishing_enabled:false` not changed. All three release requests remain in owner-requested order, with **zero confirmed new YouTube video IDs**.
