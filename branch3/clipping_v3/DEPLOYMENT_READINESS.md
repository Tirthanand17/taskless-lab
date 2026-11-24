# CLIVOX V3 deployment readiness runbook

2026-11-24. Branch 3 only. This is a staging/smoke-test runbook, NOT authorization to ingest creator media, connect production credentials, or publish. Do not use GitHub hosted CI as a permanent commercial worker. No automatic billing. Existing V2 rights and release gates remain authoritative.

## Reproduce from repository root (Python 3.12, FFmpeg and FFprobe with H.264/AAC)
```sh
python -B -m unittest -v scripts.test_branch3_v3_multimodal_candidates scripts.test_branch3_v3_private_queue scripts.test_branch3_v2_p5_longform_local_signal_planner scripts.test_branch3_v2_p6_longform_editorial_intake
python -B -m scripts.branch3_v3_multimodal_candidates --synthetic
python -B -m scripts.branch3_v3_generated_media_smoke
```

The generated-media smoke writes an original 80s test pattern/tone to a temporary directory, encodes and decodes real MP4, measures audio RMS and sampled frame differences, identifies a scene cut and compares V2/V3 proposals. It accepts no source argument. Frame difference is not optical flow. Semantic features are absent, not invented. No external assets or outputs retained. The queue is a repeatable-computation journal only; caller-supplied SQLite connection must be private. It is not yet a worker dispatcher; no media paths, upload jobs or legal approvals are stored. Tests cover persistence, lease recovery, stale workers, retries and dedupe.

## Release checklist (check only with evidence)

| ID | Required checkpoint | State at this commit |
|---|---|---|
| 1 | Comparative research/master architecture | Documented |
| 2 | Numeric multimodal planner and V2 regression | Earlier PR #283 head 5e965c7 dedicated QA passed, new head recheck required |
| 3 | Decoded-media feature smoke | Implemented, new CI pending; not full real-media extractor |
| 4 | Durable compute queue | Implemented, new CI pending; dispatcher/backup restore not yet proven |
| 5 | Speech/semantic and word-boundary extraction integrated | Pending; separate PR #282 benchmark exists |
| 6 | Smart layouts/crop paths, original commentary, captions/audio, packaging and independent final QA | Pending V3 integration |
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
