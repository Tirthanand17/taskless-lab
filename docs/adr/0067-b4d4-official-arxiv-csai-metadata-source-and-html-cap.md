# ADR-0067 — B4d4 diversify legal first-party AI research sources

**Date:** 2026-11-06 IST. **Track:** Branch 2 GitHub-hosted low-cost research, no independent factual/rights approval or YouTube publish.

## Real measured need

The trusted B4d3 [daily run 42205343240](https://github.com/Tirthanand17/taskless-lab/actions/runs/42205343240) identified **0 complete article pages, 3 exact RSS entries only**, with exactly one `HTTP_ACCESS_DENIED`, one `REDIRECT_REJECTED` and one `EMPTY_OR_OVERSIZED_ARTICLE`. Rejecting out-of-origin redirects and publishers' bot protections was correct; allowing arbitrary domains/using CAPTCHA circumvention would be wrong. The size failure was ambiguous under the old combined status because a page may be too tiny *or* too large.

## Official primary-source alternative

arXiv's [official RSS spec](https://github.com/arXiv/arxiv-docs/blob/develop/source/help/rss_specifications.md) explicitly uses a daily category RSS feed, item title, `pubDate`, and `https://arxiv.org/abs/<id>` abstract URLs. Its [API terms](https://info.arxiv.org/help/api/tou.html) set **one request every three seconds**, one connection at a time, metadata can be used under CC0, and full e-print redistribution generally requires copyright-holder permission. These are **unreviewed preprints**, not automatically peer reviewed, fact verified, or licensed for copying their full paper, figures, abstract paragraphs into monetized YouTube videos.

This milestone adds **only the official** `https://rss.arxiv.org/rss/cs.AI` feed under a separate **arXiv AI** research publisher. Its code-review-pinned RSS origin is separate from allowed **article abstract-only** `https://arxiv.org/abs/YYYY.NNNN[N][vN]` origin. It does not permit arbitrary `arxiv.org/pdf`, `/html`, search API, unlisted subdomain, query secrets, HTTP port, paper content cache or an original article link pointing back to RSS. The feed fetch is low-frequency and sequential. The daily workflow explicitly holds at least **3.2 seconds** after the feed step before attempting source observations; after a failed arXiv abstract request the source agent holds another **3.2 seconds** before a single feed fallback. Only **one** arXiv paper is eligible for the daily bounded article probe even when the feed contains hundreds.

To prevent a burst of fresh research paper announcements from crowding out official companies/news sites, `scout.scout` retains at most six unverified leads per publisher and 24 total, while the source probe prioritizes at most one directly attributable arXiv first-party paper.

## Bounded HTML capacity and better cause data

Change `MAX_BODY_BYTES` for read-only public article HTML from **262,144 bytes to 1,048,576 bytes**. This remains below/at the independently enforced max source response size elsewhere. Full raw HTML stays in the ephemeral GitHub job and is **never put in public artifacts**; only the SHA-256 digest and byte count are saved temporarily. A source body under 96 bytes now yields `ARTICLE_TOO_SMALL` and over 1 MiB yields `ARTICLE_TOO_LARGE` (both safe constant error classes) instead of the opaque `EMPTY_OR_OVERSIZED_ARTICLE`. All existing source HTTP 200, exact publisher domain, same-publisher redirect restrictions, content-type and bot challenge refusal remain.

No source output is promoted to factual endorsement; a publisher-sealed RSS entry is not a fully read paper or independently corroborated scientific result. The original 2 Shorts+long `science_v7` videos are existing demonstration content, unrelated to any newly selected November 2026 arXiv paper.

## Offline tests and live acceptance

- Add deterministic fake official arXiv RSS item tests for title, date and abstract link; reject modified publisher/URL/port/path/token; confirm no more than one arXiv paper selected per daily probe and no more than six total arXiv candidate leads.
- Test a **real 600KB fake source response** now fits the 1 MiB cap, but neither fact nor rights nor upload approval turns true. Test >1 MiB failure with explicit constant code.
- Confirm RSS fallback on simulated 403 is still `RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED`, with publisher server error body not copied into a public receipt.
- Require exact-head Daily Foundation, Cloud Scout, Content Quality, Cloud Render Smoke and source gates green. After trusted main merge, inspect actual public feed candidate counts, direct article fetch counts and sanitized artifact. If arXiv refuses/has an empty feed, count that as an honest unavailable source; never manufacture a success.
- Only source metadata and hashes may leave temporary GitHub Actions; owner paid cloud or Google OAuth is not invoked.

## Remaining independence limitations

Authors often retain copyright of paper content; metadata citation does not grant permission to reproduce charts or figures. The scientific quality, methods, result interpretation, independent replication and fairness of model claims need explicit review. Production still requires a real approved script generator, source-grounded facts/rights checks, speaker and sound licensing review, fully viewed 2 Shorts + 1 long *new* videos, private cloud/OAuth publishing and 21 real unattended laptop-off YouTube releases.

**Score remains an approximate source-only baseline of 40/100, with independent YouTube release proof 0/21.**
