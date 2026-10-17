# FlowMinute Lab — Phase 3B: real file integrity and independent rights-review preparation

**17 October 2026 | Software staging | No publisher integration | Extra monthly budget ₹0**

## Verified software milestone

- Phase 3A already established typed script/reviewer-bound storyboard, voice direction, narration metadata, subtitles and render recipe handoffs. Its workflow does **not** authorize a YouTube upload.
- New `autopilot/media_rights_review.py` performs **real FFprobe/FFmpeg video and narration inspections**, compares the measured audio SHA-256 to the narration record, verifies output geometry/duration against the storyboard and render recipe, revalidates current Phase 2 reviewed script and localization digests, confirms each explicitly storyboard-referenced asset has a declared rights record, and hashes each local license-evidence document to detect missing/changed evidence. The voice-plan's evidence hash must match the declared voice rights file.
- Improved `autopilot/render_inspection.py` independently checks the actual video/audio codecs are **H.264/AAC** and the file container is MP4. Merely detecting a stream is insufficient.
- Rights records include declared commercial/derivative permission, attribution readiness, evidence file hash, source description and optional expiration. These are **claims, not proof of lawful commercial permission**. Full rights review requires a trusted reviewer to inspect the actual license or original asset chain.
- For a technically complete file/evidence set the return status is `INSPECTED_AWAITING_INDEPENDENT_REVIEW`; otherwise `BLOCKED_TECHNICAL_PREFLIGHT`. Even on complete results, `publishing_authorized=False`, `human_qa_completed=False`, `license_legality_verified=False` and `cloud_deployed=False` always.
- The review packet records the SHA-256 of the final inspected video; **no prior video hash exists in the draft recipe to compare against**, so a measured video hash does not independently prove visual/script accuracy or authorize publication.

## Test evidence and limits

GitHub software CI [run 39038547204](https://github.com/Tirthanand17/taskless-lab/actions/runs/39038547204) passed **221 tests plus 6 subtests**.

New fixtures use **actual locally generated synthetic video/audio bytes**, not mock inspection outputs:
- 1080×1920, three-second synthetic H.264/AAC MP4 and three-second sine-wave PCM WAV
- Local plaintext synthetic test claims hashed as rights-evidence files, not actual third-party licenses
- 17 test cases covering hash/timing matching and mismatches, missing/duplicated asset declarations, missing voice evidence, expired/changed license documents, wrong channel format/language/plan, and fail-closed outcomes
- Two additional file-level codec tests: actual H.264/AAC identification and a deliberately invalid MPEG-4-in-MP4 stream rejected

The tests prove the validator logic works on small files only. They **do not** prove a licensed Hindi/English voice is natural, that subtitles match pronunciation, that visuals depict accurate steps, that music/images may be used commercially, or that 90 videos per month can be rendered and stored for ₹0. No real production media was generated.

## Structural trust boundary

Production source script and localized draft are revalidated with their original digest and specialist-stage review markers before the media packet is inspected. But actor fields and `ATTESTED_FOR_DRAFT` review inputs are **not authenticated external human review decisions**. No specialist may self-authorize production or turn a rights declaration into a verified license.

The next independent reviewer integration needs:
1. A stable artifact identity, actual file hashes and a signed/authorized reviewer identity rather than a self-declared role string.
2. An explicit real-media audio listen-through, pronunciation/Hindi-English caption transcript and frame-level UI/claim audit.
3. Documented and independently checked licensed assets/consent, visible on-screen simulated-interface labels, original/demo evidence.
4. A separate final release approval that cannot be issued by the original author, publisher or voice generator.
5. An idempotent durable cloud ledger, measured policy-compliant and truly no-cost compute/storage, and stable YouTube OAuth before a **separately approved** private upload pilot.

## Commands

From the existing public repository root (requires FFmpeg, FFprobe and pytest):

```bash
python -m pytest -q autopilot/test_media_rights_review.py autopilot/test_render_inspection.py
python -m pytest -q
```

The process creates synthetic media only in temporary test directories and makes no remote requests or user-account changes. GitHub Actions is used for legitimate software testing, **not as an unlimited hosted video-rendering service**.

**Operational result:** Phase 3B's *technical validator* is implemented and GitHub CI verified, but trustworthy commercial rights and language/creative QA are still incomplete. YouTube uploading/scheduling and paid resources remain disabled.
