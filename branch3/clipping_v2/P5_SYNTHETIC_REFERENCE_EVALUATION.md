# CLIVOX V2 — P5 synthetic reference evaluation (no real editor labels)

**Scope and trust boundary (2026-11-14):** This is a deterministic test harness for **self-generated synthetic source-free footage only**. It is NOT the rights-gated evaluation of authentic creator clips, and it cannot establish editorial quality, real top-five performance, commercial media rights, creator agreement, publish permission, monetization or viral prediction.

## Real code and test handoff

- New \`scripts/branch3_v2_p5_synthetic_editorial_evaluation.py\` reuses the existing **actual closed A3/P4/P5 controls**. It rejects any purported real creator/source/human license, real speech transcript, third-party YouTube API stats, forged verified rights, fabricated "most replayed" or live analytics values.
- Strong allowlists for the existing P5 detector response and interval fields; only two observed event kinds are allowed (local audio RMS rise and low-resolution luma cut). Candidate timestamps and counts must match the detector's exact generated synthetic contract.
- Synthetic golden references are defined by the controlled test signal itself. The primary GitHub Actions fixture has black video 0–2 s, white 2–3 s, black 3–6 s plus silence/tone/silence. Its synthetic golden review interval is 1.2–4.2 s. It has **not been watched or validated by a real independent editor**, and it is not a representative viral short.
- Calculate one-to-one temporal overlap against known synthetic reference intervals using intersection-over-union ≥ 0.50. Count true matching proposals, false-positive suggestions and missed synthetic reference windows; prevent duplicate suggestions from counting as multiple matches.
- Strictly source-separated evaluation: each fixture has a unique \`synthetic_...\` identity; no training occurs or cross-owner public API metrics are aggregated. Every metric is labeled synthetic only. \`precision_of_available_top_five\` divides matches by up to five actual suggestions (not always 5); \`recall_of_synthetic_reference_events\` divides matches by synthetic reference count. Missing denominators produce \`null\`, not a fabricated zero.
- Read-only/no-secret GitHub workflow consumes the **already-generated P5 ephemeral detector JSON** and evaluates it against the **known synthetic reference**, then asserts genuine matched event plus all real-source/human/release flags still false. Neither MP4 nor candidate/evaluation JSON is uploaded to a public artifact.
- Includes adversarial offline tests for wrong CLIVOX channel, extra keys, forged rights/media, fake transcripts, platform stats, duplicate source identities, missing positives, false-positive windows, overlap/ordering errors, time/denominator bounds, unsafe paths and oversized inputs.

## Evidence and precision limitations

A technically successful sample can report a perfect match for one **prearranged** six-second synthetic cut. Such a result **must never** be called 100% actual detector precision, creator engagement prediction, human editorial agreement or return on publishing.

The outcome is an engineering test for the **evaluator wiring**, not validated detection quality. Even if no known event is suggested, the harness records missing synthetic reference events; if there are no proposals, precision is \`null\` rather than an inferred failure rate. If there are no reference labels, recall is \`null\` rather than a free pass.

The P5 prototype's acoustic/scene features are neither Silero VAD nor Whisper ASR nor PySceneDetect. Authenticated real-rights review, approved private source vault/delivery, actual speech/event context, independently labeled moments and legal/editorial signoff remain missing.

## Actual acceptance still blocked

P2 needs owner-selected verified creator business contacts; P3 requires real authenticated signed commercial clipping rights plus third-party publisher/music/guest clearance and live revocation evidence. P4 requires approved private storage and actual authorized file delivery. P5 needs genuine licensed-source inference with explicit model-processing rights, 40–60 human-labeled authorized moments across multiple creators/streams, held-out-by-source top-five evaluation, agreement and mistake analysis. P6–P9 require actual original commentary, editing QA, exact-media human review/signature and channel-restricted YouTube release.

**Never put licensed video, contracts, creator contacts, transcript content, private-media URLs, thumbnails or tokens in public taskless-lab source, PRs, issues, logs, or workflow artifacts.** Never download arbitrary YouTube creator footage.

## Commands and QA

- Run the closed gate: \`python -B -m scripts.branch3_v2_p5_synthetic_editorial_evaluation --mode closed\`.
- Run source-free unit tests: \`python -B -m unittest -v scripts.test_branch3_v2_p5_synthetic_editorial_evaluation\`.
- The connected GitHub workflow \`.github/workflows/branch3-clivox-v2-p5-synthetic-candidates-qa.yml\` produces the generated P5 detector output in private runner temp and executes \`--mode synthetic --scratch "$RUNNER_TEMP/clivox-p5-synthetic" --report-file quarantined-signals-only.json\`.
- Full implementation needs green dedicated PR CI, regression CI, and independently verified merged-main runs; do not represent engineering as complete before checks pass.

**Overall real V2 roadmap remains 2/12 (17%)** until actual human/creator milestones are fulfilled. Branch 1 and Branch 2 FlowMinute remain unchanged.

## Verified merged-main engineering evidence (2026-11-14)

- [PR #214](https://github.com/Tirthanand17/taskless-lab/pull/214) passed **4/4 PR workflows**; dedicated [P5 source-free evaluator PR QA #43586077074](https://github.com/Tirthanand17/taskless-lab/actions/runs/43586077074) passed.
- Merged main implementation SHA: `87eea71ac1f581072b96d4b1bdde18f5cd6e21d5`; [P5 synthetic signal→golden-event evaluation QA #43586169756](https://github.com/Tirthanand17/taskless-lab/actions/runs/43586169756) **success**.
- [P4 media integrity regression #43586169769](https://github.com/Tirthanand17/taskless-lab/actions/runs/43586169769) and [Content Quality Gate #43586169748](https://github.com/Tirthanand17/taskless-lab/actions/runs/43586169748) **success** after the feature merge.
- These test passes only verify small synthetic fixture wiring, exact report contracts and failure behavior. They prove **zero** actual editor labels, zero real licensed source, zero creator reuse grants, zero actual video uploads and **no real precision/viral result**.
