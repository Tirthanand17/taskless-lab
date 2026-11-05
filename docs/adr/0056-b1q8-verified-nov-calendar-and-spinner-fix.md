# ADR-0056 — B1q8 exact-source spinner diagnosis, verified owner Nov 5–11 release state, and no-write remediation

**2026-11-05 IST, Branch 1. GitHub-only durable code, read-only YouTube API observation, NO remote mutation.**

## Live YouTube observation (replaces stale repository-only interpretation)

After the owner explicitly approved securely configuring the encrypted production environment secret, the GitHub cloud read-only workflow [42043506591](https://github.com/Tirthanand17/taskless-lab/actions/runs/42043506591) passed its offline tests and credential-shape preflight but **failed at the actual Google request**. The previously authorized *read-only* credential, originally last used October 16, returned HTTP **400 when tested for refresh**, so **that workflow did not verify any video state**. **Do not count its tests as a live audit.**

An owner-authenticated newer credential was then used **only in memory on the authorized online Nirala device** for official Google HTTPS token refresh and **GET-only** YouTube Data API calls. The stronger existing credential was **not copied to GitHub or logged**, and the device made **no YouTube mutation**. The authenticated owner channel ID was verified against the expected channel, the entire owner uploads playlist was paginated to completion, and all returned uploads were fetched in video-status batches:

| Observation from actual live authenticated read | Value |
|---|---:|
| Owner uploaded videos scanned | **89** |
| Upload playlist pages fetched and exhausted | **2** |
| Uploaded video details checked | **89** |
| Nov 5–11 expected IST slots (11:00 Short, 16:00 long, 20:30 Short) | **21** |
| Nov 5 releases already public when queried | **2** |
| Nov 5–11 private scheduled video statuses confirmed | **19** |
| Still-scheduled Shorts | **13** |
| Still-scheduled long videos | **6** |

**Crucial correction:** the **4 of 21** number in old GitHub receipts is *historical repository evidence only*. The **actual owner calendar had 19 private scheduled + 2 already public** when checked. **Never fill 17 allegedly empty YouTube slots.** This time-stamped result is an owner read-only observation, NOT a current perpetual guarantee or evidence of approval to modify YouTube. This page intentionally contains **no private video IDs, titles, source OAuth, descriptions or Google API response bodies**.

## Exact rotating arc culprit proven against actual scheduled uploaded masters

The authorized device already contained privately staged source scripts, final MP4s, original media QA and verified upload-receipt JSON for each of the thirteen still-scheduled Shorts. All were examined **read-only**, with no local file writes.

**Eleven of the thirteen** use the identical generic code in an original render function:

```python
phase=.5+.5*math.sin(t*7)
d.arc((242,573,480,801),int(15+130*phase),int(155+130*phase),fill=c,width=5)
```

This draws an unrelated moving **central circular arc every frame**, persistently overlaying all eight source story scenes. The native 720×1280 artwork is upscaled to final 1080×1920, making the decorative curve conspicuous. Those eleven original final MP4s were **independently SHA-256 checked against BOTH** the local `render_qa.json` and the recorded YouTube `verified_youtube_schedule.json` receipts. **All eleven matched exactly**, establishing a specific defective upload *source*, not merely a hypothetical template. The other two future Shorts have separate renderers; they need individual editorial inspection and must not be falsely classified as having this exact arc.

Affected scheduled slots (IST; source file names and old video IDs intentionally excluded):

| Date | Source-confirmed curved-animation slots |
| --- | --- |
| Nov 5 | 20:30 |
| Nov 6 | 20:30 |
| Nov 7 | 20:30 |
| Nov 8 | 11:00, 20:30 |
| Nov 9 | 11:00, 20:30 |
| Nov 10 | 11:00, 20:30 |
| Nov 11 | 11:00, 20:30 |

Other-visual-source scheduled Shorts: Nov 6 and Nov 7 at 11:00 IST.

## Narrow reusable repair and fail-closed contract

- `autopilot/branch1_legacy_arc_remediation_v7.py` is an **in-memory** helper, not a scheduler, uploader or file overwriter. It accepts an exact original renderer source, verifies the literal two-line animated-arc block and its scene/progress context appear exactly once, and returns a source-only patch that removes the circular drawing. Original photo/diagram art, one-shot camera motion, narration, voice processing, caption files, footer and finite story progress rail are kept unchanged.
- The helper proves exact original MP4 bytes match the old archived master SHA and uploader receipt SHA, and refuses all other source or media variants. It **cannot** establish the new output is fully reviewed or a valid future scheduled upload by itself.
- New synthetic CI tests validate exact source differential, strict single-match, CRLF handling, changed-source rejection, original SHA mismatch rejection, observed 11/2/13 counts, and no video mutation/approval claims.
- The dedicated `.github/workflows/flowminute-b1q8-confirmed-arc-guard.yml` runs **without any GitHub secret or owner token**. All durable modifications stay in GitHub; existing owner media remains on the authorized device **unmodified**.
- Existing B1q7 shared science-source orbit correction is a *different* renderer. It is not proof that the thirteen specific scheduled Shorts were corrected by the earlier merge.
- Previously GitHub-rendered three no-spinner topic previews differ in narration, script, visual art or duration from some original uploaded masters; do not substitute by topic alone without approved exact new media, full watch, and owner checks.

## Why no automatic replacement despite confirming the culprit

YouTube **does not support replacing a video's binary under the same ID/URL** (see <https://support.google.com/youtube/answer/55770>). Any corrected video must be rendered and independently reviewed as a **new private upload with a new video ID**. For each still-private future slot, the safe process is:

1. Read the existing original ID, status and precise IST publish time from authenticated owner API immediately before work.
2. Stage only the corresponding *private, SHA-matched* original source/assets in an appropriately protected cloud runner—not in this **public** repository or a publicly downloadable review artifact. Apply the exact arc patch only to that matched source.
3. Render/re-encode a corrected original portrait H264/AAC file, preserve the exact original source PCM/caption text and title, independently verify full FFmpeg decode, sync, subtitles, full visual frames and rights. Record new SHA and have owner approve the specific corrected candidate.
4. Upload corrected master **privately**, confirm YouTube processed status, captions and owner channel, and then carefully coordinate the old private schedule and new private publishAt with authorization. Avoid duplicate same-time releases, never auto-delete or invalidate the old video.
5. Re-read both exact IDs, check exactly one intended future scheduled release, record signed new receipt, then continue to the next Short.

Already published videos must **not** be silently unpublished or deleted; a separate corrected release is a separate URL. A past publishAt can cause immediate public release, so no retroactive scheduling.

**Current verified state:** actual owner calendar known; repeated moving-arc source and exact old upload SHA identity for 11 future Shorts known; pure patch code & tests prepared; **no current YouTube video changed**, no new corrected 11 media packages, no approved releases, and GitHub's read-only OAuth secret is still not refreshable. Full repair is still pending.
