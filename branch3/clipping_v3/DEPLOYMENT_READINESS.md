# CLIVOX V3 deployment readiness runbook

2026-11-24. Branch 3 only. This is a staging/smoke-test runbook, NOT authorization to ingest creator media, connect production credentials, or publish. Do not use GitHub hosted CI as a permanent commercial worker. No automatic billing. Existing V2 rights and release gates remain authoritative.

## Reproduce from repository root (Python 3.12, FFmpeg and FFprobe with H.264/AAC)
```sh
python -B -m unittest -v scripts.test_branch3_v3_multimodal_candidates scripts.test_branch3_v3_private_queue scripts.test_branch3_v2_p5_longform_local_signal_planner scripts.test_branch3_v2_p6_longform_editorial_intake
python -B -m scripts.branch3_v3_multimodal_candidates --synthetic
python -B -m scripts.branch3_v3_generated_media_smoke
python -B -m unittest -v scripts.test_branch3_v3_transcript_context scripts.test_branch3_v3_editorial_draft scripts.test_branch3_v3_subject_crop_plan
python -B -m scripts.branch3_v3_vertical_render_smoke
```

The generated-media smoke writes an original 80s test pattern/tone to a temporary directory, encodes and decodes real MP4, measures audio RMS and sampled frame differences, identifies a scene cut and compares V2/V3 proposals. It accepts no source argument. Frame difference is not optical flow. Semantic features are absent, not invented. No external assets or outputs retained. The queue is a repeatable-computation journal only; caller-supplied SQLite connection must be private. It is not yet a worker dispatcher; no media paths, upload jobs or legal approvals are stored. Tests cover persistence, lease recovery, stale workers, retries and dedupe.

## Release checklist (check only with evidence)

| ID | Required checkpoint | State at this commit |
|---|---|---|
| 1 | Comparative research/master architecture | Documented |
| 2 | Numeric multimodal planner and V2 regression | Dedicated V3 CI passed at 77b4c04; latest head recheck required |
| 3 | Decoded-media feature smoke | Dedicated V3 CI passed at 77b4c04; not full real-media extractor |
| 4 | Durable compute queue | Dedicated V3 CI passed at 77b4c04; dispatcher/backup restore not yet proven |
| 5 | Speech/semantic and word-boundary extraction integrated | Fixture unit tests passed in CI at 77b4c04; cached Faster Whisper base INT8 generated-speech test passed on Windows, 29.02s, 61 timed words, 6 segments; real-source ASR acceptance pending |
| 6 | Smart layouts/crop paths, original commentary, captions/audio, packaging and independent final QA | Partial: editorial draft, caption timings, 1080x1920 fit/stack fixture render and decoded audio/caption QA; crop-path planner unit tests passed. Automatic subject detection, actual dynamic crop rendering, original commentary and final packaging still pending |
| 7 | Deployable worker with bounded resource use, private filesystem, dependency/model pins and verified backup/restore | Pending |
| 8 | Real scoped creator rights, delivered source and private storage | Blocked on genuine evidence |
| 9 | Held-out real-media comparison, actual editor acceptance and first 3 reviewed private clips | Pending |
| 10 | Existing exact-release controller + Clivox OAuth, private-first readback, separate schedule approval | Blocked |
| 11 | Own-channel analytics and growth experiments | Pending real deployment |

No progress percentage for actual performance, revenue or hosting availability. The V2 real-roadmap tracker remains 2/12. Do not count test code as real source acceptance. Do not merge a draft until relevant CI is green and scope reviewed.

## Private worker activation (not performed)

Use an owner-approved host with commercial use permitted and zero incremental spend. Verify provider account entitlements, expiry, permitted usage, and hard spending limits before activating. GitHub Student Pack/Codespaces can support development within included quota; GitHub Actions runs software tests. Neither establishes an unattended commercial production host. Do not create paid Azure resources, attach payment method, or use credentials from other FlowMinute tracks. If no suitable host exists, report the dependency rather than falsely marking deployment ready.

Install only validated pinned dependencies; measure CPU/RAM/disk and model/runtime footprint on generated tests before sizing host. Private data directory outside public checkout, owner-only access, encrypted storage, no public artifacts, source hash and rights binding. Restrict network and keep uploader credentials out of compute worker. Set explicit disk/time limits, heartbeat, lease policy (long jobs require renewal or bounded chunks), and atomic output/receipt handoff. Test restart, corrupted input, quota exhaustion, denied rights, revocation and restore. No automatic retry of uncertain remote uploads.

After a genuine creator grant and approved worker exist, use existing V2 P4 and production activation handoff, integrate V3 without bypassing the P4/P6/P8 gate, benchmark 40–60 human-labelled moments, watch each preview on a phone, verify captions/quotes/HUD/audio/original commentary and exact metadata. Only then consider private upload using existing controller, owner approval and remote verification. Publication requires separate approval. Analytics only for authorized own-channel data; no artificial engagement.

## Next engineering tasks

Integrate or port validated parts of PR #282 after code/CI review; build actual ASR/VAD and motion adapter with consistent source timebase; repair clip boundaries against words and scene context; connect queue to bounded compute dispatcher; add crop/layout and editorial EDL; verify independent render and packaging QA. Preserve all existing permissions and FlowMinute tracks.

## Verified staging evidence (2026-11-24)

- PR #283 commit 77b4c04424f43a1997c9c0fb4f0febf2dba68961: dedicated CI run 45356922091 and channel QA 45356922100 succeeded; repository Content Quality Gate 45356922136 failed at the FFmpeg installation step, not an observed test failure. Do not mark full CI green.
- Local Windows detached-worktree test of exact commit 37b43e0aad6ccd06a11fce4d0435bdf89fe04247 succeeded (exit 0). Two generated 24-second 1080x1920 H.264/AAC outputs, fit and game_facecam_stack, decoded caption pixels and audio/video timing checked; peak 6524 PCM16 for both. Synthetic tone and generated caption text, not spoken words or licensed gameplay. Temporary files cleaned. No real media retained, published or processed.
- Three new crop-plan tests passed locally on files fetched from branch at commit a6d6834812d00d292bdbc905fafd3a8e815ac60b. Subject boxes are input observations, not actual detections; ambiguity, rapid motion and inadequate coverage cause full-frame fit. Render integration and interpolation verification remain pending.
- Five of eleven staging checkpoint-specific validations have evidence. Checkpoint 6 is partial; production activation remains blocked. No change to V2 real milestone count or legal gates. No automatic spend or publishing.
