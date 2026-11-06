# ADR-0066 — B4d3 source fetcher diagnosis and publisher-only redirect policy

**Date:** 2026-11-06 (IST). **Track:** Branch 2, unprivileged GitHub daily source observation. No provider auth, billable model calls, human truth certification or YouTube uploads.

## Measured gap

The first real B4d2 daily workflow, [run 42202574661](https://github.com/Tirthanand17/taskless-lab/actions/runs/42202574661), observed **zero** complete article pages and retained three exact-publisher RSS entry observations. The 3-topic editorial planner accurately labelled all as headline-level leads. The previous `autopilot.evidence_probe.probe_source` configured a deny-all redirect handler, and also rejected any final URL other than the original. More importantly, `probe_report` silently swallowed every article-fetch failure and retried the feed without describing whether the publisher blocked access or a link changed. The prior run cannot establish which cause dominates.

## B4d3 implementation

- Add a strictly bounded `PublisherOnlyArticleRedirect` with **at most two HTTP 301/302/303/307/308 redirects**, **GET requests only**, each validated *before* following against the publisher's existing **exact HTTPS hostname allowlist**, mandatory slash path, no URL credentials, no IP literal, no unsupported port, no fragments, no loops. Do not accept an arbitrary Google result, unlisted domain, third-party CDN, FTP, plain HTTP or arbitrary redirect. A fake injected test opener cannot forge redirect provenance.
- Preserve fail-closed restrictions: HTTP 200, approved textual MIME, **96–262,144 response bytes**, bounded timeouts, no copied third-party source body in public GitHub artifacts, and exact source identity bound to the *original allowlisted RSS link*. The observed publisher and original URL hash are not silently overwritten by a canonical redirect target. A simple Cloudflare/interstitial 200 response is explicitly **not a fetched article**.
- Classify direct-fetch failures using **13 fixed constant codes** (e.g. `HTTP_ACCESS_DENIED`, `REDIRECT_REJECTED`, `HTTP_RATE_LIMITED`, `UNSUPPORTED_CONTENT_TYPE`, `BOT_CHALLENGE_PAGE`), never remote error messages, full URLs or response bodies. When the publisher article request fails, the matching RSS record can still be observed and remains labelled **`RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED`**. Preserve that honest fallback without promoting the article to read.
- Reconcile per-source failure categories and redirect counters in the independent editorial board. The tiny public 14-day editorial receipt retains only **aggregated safe category counts** and bounded redirect totals. Reject forged diagnostic strings or invented success numbers before writing a public receipt.
- Extend the existing `.github/workflows/flowminute-daily-cloud-foundation.yml` with additional offline publisher-redirect/adversarial HTTP response tests and aggregate-safe GitHub summaries. No new paid dependencies, user laptop, GitHub credential persistence, remote secrets, OAuth or YouTube methods.

## CI dependency reliability (observed blocked check)

The PR source/Cloud Scout/Quality gates passed, but the independent Cloud Render Smoke [PR run 42204252917](https://github.com/Tirthanand17/taskless-lab/actions/runs/42204252917) **failed with exit 124** after waiting exactly 150 seconds for Ubuntu's unavailable FFmpeg apt mirror, before running Remotion. The smoke was NOT considered passed or waived. B4d3 also changes the **separate** `.github/workflows/flowminute-cloud-render-smoke.yml` to install `imageio-ffmpeg==0.6.0` as an exact-version binary wheel (the package's public wheels bundle FFmpeg). It symlinks the local unprivileged binary into the job and validates the resulting original Remotion Short using a real full FFmpeg decode, checked H.264 + AAC codecs, 1080x1920 dimensions and SHA256. The ffprobe command is replaced with parsing the same independent FFmpeg stream metadata. It does not rely on sudo, system apt indexes or a private laptop. A source-only regression test makes removal of the decode or reintroduction of apt fail CI.

The pinned wheel is a **new public package dependency**, not a claim of owner-approved production licensing or private media handling; the main publishing pipeline is unchanged. A live green Cloud Render Smoke run is required before merging.

## Verification and falsification

Synthetic tests prove policy behavior and no raw text/URLs in error categories. They cannot prove that live publishers will permit automated downloads. The decisive acceptance is a **real trusted main-branch daily GitHub run**, reconciling its safe failure counts to its actual source fetch/fallback totals. At minimum it should reveal **whether** zero-page evidence is due to allowed redirects, access denial, rate limit, unsupported MIME, oversized pages, or transport. If all publishers respond with 403 or bot challenge, **do not evade site controls**: document this accurately and add legitimate accessible first-party/public-data alternatives in a separate reviewed iteration.

**Do not claim:** fact verification from an article hash, independent corroboration from different publisher labels, rights clearance, a model-written script, fresh fully produced video, or upload/schedule authorization. All remain explicitly blocked.

## Practical downstream goal

Once approved accessible primary text exists and editorial observations are linked accurately, a distinct factual claim/visual proof and reviewer workflow may prepare source-grounded narration drafts without plagiarizing articles. Provider inference remains subject to explicit owner approval and bounded budget; publishing needs protected Google OAuth/owner cloud and a signed final creative/rights approval. The historical successful 2-Shorts/1-long `science_v7` videos are **static demos**, not new day-to-day media.

Production readiness stays approximately **40/100**, independently proven 7-day laptop-off YouTube releases **0/21** until independent owner-channel evidence exists.
