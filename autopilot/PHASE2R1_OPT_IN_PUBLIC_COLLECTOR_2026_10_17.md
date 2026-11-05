# FlowMinute Lab Phase 2R1 — opt-in public HTTPS source collector

**17 October 2026 | OFF by default, no live fetch performed by these commits, no publisher, no new provider account or OAuth.**

## Progress

The existing `scout.py` still returns RSS topic **leads** only. Earlier `phase2_source_evidence.py` tests whether text and quotations supplied by a caller match structural research requirements, but it does not perform HTTP requests. The new `phase2_public_collector.py` supplies a narrow, **opt-in** transport for a single established teaching example:

| Source ID | Exact allowed article | Role in existing synthetic teaching fixture |
| --- | --- | --- |
| `src_python_docs` | `https://docs.python.org/3/library/csv.html` | Official language documentation |
| `src_independent_csv` | `https://realpython.com/python-csv/` | Separate publisher, NOT guaranteed independently corroborating every claim |

No other URL, source ID, private IP, redirected site, user credential, arbitrary Google/YouTube page, or page discovered by RSS can be fetched using this function. The exact-URL allowlist is intentionally hardcoded and checked against the existing typed `ResearchPackage`.

## Network policy

- Calls to `collect_csv_research_sources()` **refuse all live network by default**. An explicit `allow_live_network=True` is required to use its real HTTPS transport; this has **not** been done here.
- Uses standard-library HTTPS with normal TLS certificate validation. `ProxyHandler({})` avoids environment proxy configuration; it does not install a privileged/browser plugin. All HTTP redirects are denied, even if nominally same-host. No cookies, login, tokens, JavaScript or arbitrary DNS endpoints.
- Before requesting each article, retrieve and validate **that same host's** `/robots.txt` over HTTPS, then require the parser to permit the article for FlowMinute's declared User-Agent. Missing, redirected, inaccessible, malformed/denied robots -> stop; do **not** bypass by changing the agent or retrying.
- Maximum one robots request plus one article request per exact allowlisted source per invocation, sequentially, with bounded six-second request timeouts, **no retry** after 401/403/429/503, unapproved response type, redirects or failures.
- Maximum 32 KiB robots response and 128 KiB **complete UTF-8 article response**. Too-large webpages stop cleanly: content must never be silently truncated or treated as complete. Responses must have status 200 and identity encoding; gzip, PDF, binary media, HTML challenge pages and unusual encodings are not bypassed. An ordinary HTML challenge with status 200 could still be captured but will fail downstream quote matching.
- Captures include SHA-256 of the complete bounded UTF-8 source content. Raw text is available **only to the in-process reviewer**, while `public_capture_summary()` includes only source IDs, hashes and explicit nonapproval flags.
- Actual public-source licensing/copyright, relevant content, independent corroboration, author identity and true claim semantics are **NOT** established by HTTPS and robots alone. `phase2_source_evidence.py` still requires per-claim quote matches, and separate independent editorial assessment is mandatory.

## Current validation boundary

New regression file: `autopilot/test_phase2_public_collector.py` with **20** fully simulated tests of default-off network, source allowlist, robots deny, redirects, HTTP errors, bytes/UTF-8/content restrictions, hash capture, source excerpt preflight and no publicity authorization. Injected fake transport **cannot** be combined with `allow_live_network=True`; test fixtures never contact a real external network.

**Do not mark 2R1 complete yet.** The actual live HTTP run, source-access/permitted-use review, provider throttle policies and authenticated evidence storage remain unverified. The two fixed sources merely establish a narrow first vertical slice. Expanding to independent current-trend research would require a separately reviewed allowlist and bounded compliance logic.

## Operational TODO for a later explicitly approved, zero-spend live proof

1. Confirm that the exact two host robots rules and published site terms permit the narrowly scoped read. The URLs are public learning resources, but robots allowance is not a content-republication license. Do not embed full copyrighted text in YouTube videos.
2. Run one **explicit** controlled `allow_live_network=True` from a permitted cloud job, not from Nirala, and check whether both complete pages fit 128 KiB. If not, record `SOURCE_TOO_LARGE`; do not automatically raise the cap.
3. Compare SHA-256 source captures and short supporting excerpts against the actual source claims in an externally authenticated source-backed ResearchPackage. Examples and tests currently use **synthetic** facts and synthetic quote text.
4. Preserve only privacy-safe bounded receipt metadata, do not publish raw article text in CI log or GitHub commit.
5. Require independent claim/source review before fact-review attestation, script preparation, Hindi/English QA and rendering. Videos must not be automatically scheduled or published.

**Project boundaries:** ₹0 recurring budget; no private GitHub Actions jobs without quota proof; no new external service connection, payment or OAuth scopes; no Nirala/laptop; no Cloudflare D1 migration, YouTube uploads/schedules, media render or publishing. PR remains draft. Existing 21 outstanding production acceptance subphases remain unchanged until real source collection and QA are demonstrated.


## Phase 2R1 operator preview and explicit owner gate — continuation

Implementation addition: autopilot/phase2_public_capture_preflight.py and autopilot/test_phase2_public_capture_preflight.py.

- Default invocation: python -m autopilot.phase2_public_capture_preflight
- Preview does **not open the network**, even when suspicious environment variables contain approval-like strings. It prints only allowed source IDs, limits and fact/publishing false.
- A future live invocation requires, simultaneously, an exact confirmation phrase, exact owner-approval environment marker, GITHUB_ACTIONS=true, GITHUB_EVENT_NAME=workflow_dispatch, RUNNER_OS=Linux, and the reviewed Phase 2 research branch name. Any missing condition fails closed **before** the transport is called. These string checks are not actual signed owner authentication or GitHub required-reviewer settings; they must not replace explicit permission and independent review.
- The normal pull_request CI Cloud Scout task now tests all these policy gates and runs only --mode preview. Its scheduled run likewise does not turn on the live collector. No live input or HTTP fetch has been triggered.
- No new live-fetch workflow or cross-repo OAuth connection has been deployed. Creating a manual GitHub Actions workflow in a nondefault branch alone would not make it generally dispatchable; activation requires separate review and approval.
- A real live attempt, if later authorized, must run once with exactly the two restricted public article URLs and their robots.txt files; no retries. The result contains hashes/IDs and explicit negative factual/rights/publishing authorization; neither raw article text nor quoted webpage text is written to CI logs.
- Source copyright/public-use terms, robots constraints, article byte sizes and semantic claim verification remain independent blocking gates. Do not increase network quotas or paid services automatically.

**STOP:** The completion of this CLI and its tests does NOT complete 2R1. No real public-source runner result, source-side server receipts, live fact review, voice/video or YouTube release is established. Keep the prior 21 production subphase count unchanged.
