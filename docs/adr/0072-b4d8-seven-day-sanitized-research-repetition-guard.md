# ADR-0072 — B4d8 Read-only seven-day previous research de-duplication

**Date:** 2026-11-06 IST. **Track:** Branch 2, GitHub-only unattended editorial research. **No YouTube publish authority.**

## Verified problem

The live B4d7 main run ([GitHub 42232848389](https://github.com/Tirthanand17/taskless-lab/actions/runs/42232848389)) demonstrated two actually fetched article pages and four small unverified passage review questions, but not semantic fact approval, source licensing, narration or upload. The daily editor has an optional `previous_subject_hashes` feature but the scheduled daily workflow never supplies previous-day history. Multiple successful research plans in consecutive days could therefore reselect the **same source URL and subject**, causing repeated AI/science topics. The user's requirement is two genuinely distinct Shorts and one long daily, not three repeated headline-based concepts.

## Design and implemented code

New `autopilot/recent_research_history.py` reads ONLY past **successful, authenticated main-branch FlowMinute Daily Cloud Foundation** GitHub Actions artifacts. It uses the GitHub-hosted official `gh` CLI with only `actions: read` and `contents: read` permissions; no new application secret or paid provider. It filters by exact workflow path, original repository, main branch, successful conclusion and `push` / scheduled / owner-dispatched event. It rejects pull requests and foreign forks. It bounds to 100 run list records, 14 archive attempts maximum, 100KB compressed ZIP, exactly two known sub-12KB original sanitized receipt JSON files, at most seven previous **distinct plan days**. The oldest allowed prior plan date is target day minus seven days. Failed/missing/outdated/forged receipts **do not count as covered days**.

The workflow's existing two public JSON receipts already contain **opaque** `subject_sha256` and 24-hex `source_id` for all three selected unverified research topics. The GitHub collector validates the receipt SHA256 and both JSON envelopes and their false approval/publish flags. This is **research history, NOT published content readback**. For same-day reruns, it explicitly excludes receipts with the **same target IST plan date** to avoid blanking repeated runs for an unchanged next-day plan.

A new filtering step runs **before** any article-source probing, aligned editorial planning or storyboarding. It hashes each current scout headline and exact URL with the prior algorithm, rejects either exact repeated subject SHA or exact repeated source ID and removes duplicate URLs from a given scout. It preserves the original report's status and published date metadata; the downstream B4d3 → B4d7 source/reconciliation/gated-research pipeline now consumes **only the filtered scout**. If fewer than three new topics remain, it leaves unfinished research slots. It does not invent an unrelated replacement or falsely call two similar-but-not-identical headlines unique. It never uploads the filter output, old titles, source URLs or article passages. The normal unconditional GitHub runner cleanup removes its ephemeral hashes and filtered unverified scout.

The step summary reports only safe counts: how many previous **research** plan days had valid receipts, number of candidate source/topic repeats removed and remaining new headlines, with an explicit **incomplete coverage** warning. No 7-day authenticity guarantee when days are missing or artifacts have expired. No owner-channel YouTube OAuth or already published-content check is performed. The GitHub read-only token never enters a generation prompt, artifact, issue, log or source file. Requests do not contain public article bodies.

## Tradeoffs

- Stored hashes from published research receipts aren't human-verified or YouTube published, and are only valid until artifact retention (currently 14 days). A future authenticated owner-channel metadata readback will be needed to de-duplicate **actually published** videos as well.
- Exact subject SHA and URL identity cannot catch genuinely related articles with different headlines or URLs. Future editorial semantic similarity + independent human approval required.
- The history uses only successful stored runs. The GitHub API or CLI can fail, which must be reported explicitly; no claim of full coverage when unavailable. Research-only jobs can fail rather than invent historical uniqueness; no YouTube upload can result.
- This is an editorial reliability prerequisite to stable, truly fresh factual/video scripts. It does not produce claims verified, production narration, 1080x1920 media or channel upload; those remain independent future gates.

## Required proof

Exact PR head must pass the Daily Foundation offline adversarial tests, Content Quality, public Cloud Scout and real H.264/AAC cloud render smoke. On merging into trusted default branch, inspect the real main-run GitHub Actions summary and logs for historical day count / removed topics, all three episode source provenance results and zero model/script/media/uploads. Download and inspect the **same two small sanitized JSON receipts only**, not snippets. Zero independent 21-video YouTube publication proof remains until actual signed owner-channel readback.
