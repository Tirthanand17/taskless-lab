# Branch 1 — Assisted YouTube releases: final five recovery plan

**Status date:** November 4, 2026 (IST)  
**Branch:** `track/assisted-youtube-releases`  
**Channel:** `UCCcL9Q_jqVq6LJmnYUSAFZA`

## Verified scope of this GitHub-only continuation

Latest *previously authenticated* YouTube production snapshot (not newly rechecked in this GitHub-only session):
- 24 total original media masters prepared.
- 18 YouTube schedules verified, one November 4 Excel tutorial already public.
- **Five still incomplete:** Nov 7 website-loading long (privately uploaded as [8XBAHM0s9j0](https://youtu.be/8XBAHM0s9j0), unscheduled last observed); Nov 10 AI fact-checking long; Nov 11 Chrome extensions Short; Nov 11 extension security audit long; Nov 11 restrict-extension-access Short. The latter four were not uploaded at the last authenticated check.
- The private control policy still has five matching SHA-pinned one-time scopes (`owner_requested_single_release_ready`, `max_uploads: 1`), and general `publishing_enabled: false`.

**Canonical exact release inventory (private; contains full hashes and times):**
`Tirthanand17/flowminute-control-private/state/assisted_releases/remaining_2026-11-04.json`.

### Blocking discovery

The official GitHub-only repository tree and sampled Actions release artifacts do **not** contain the five November 7–11 final MP4 masters and their matching caption/thumbnail bytes. The available November 2 staging artifacts are **different videos**. Don't substitute old artifacts or regenerate an approximate MP4: the private per-video owner authorization is tied to the exact SHA-256 and would not match.

Current connector can review/write repository files and inspect Actions runs, but has **no supported workflow_dispatch action** or direct authenticated YouTube write action. The existing protected publisher on `main` is `workflow_dispatch` only, requires complete source render artifacts, original captions, final QA/rights approvals, `youtube-production` environment and `YOUTUBE_TOKEN_JSON`; simply pushing a branch document does not schedule a video.

The user specifically required **no laptop-memory access for the GitHub-only work**. Do not access Nirala to silently retrieve private masters or OAuth tokens. The separate autonomous cloud Branch 2 remains strictly independent of the laptop.

## Concrete safe completion sequence (one release at a time)

1. **Secure original artifacts in cloud.** An authorized owner/provider must transfer each exact already-reviewed MP4, SRT, long-form cover and QA receipt into the *protected* artifact or approved private cloud media store. Do not commit MP4, OAuth refresh token or private assets into the public Git repository. Verify exact SHA against the private inventory before accepting any upload.
2. **Live YouTube reconciliation.** Use pre-authorized OAuth `videos.list` and `captions.list` on the intended channel. For Nov 7 [8XBAHM0s9j0](https://youtu.be/8XBAHM0s9j0), query remote state first; don't upload that MP4 again. Any ambiguous caption or schedule write becomes `UNRESOLVED` until read-back.
3. **Build exact release receipts.** Validate immutable SHA-256, original topic/source rights, captions matching audio, decode and loudness QA, target release time and maximum one video ID per slot. Do **not** assert full human viewing if it has not occurred.
4. **Publish with existing protected workflow**, once the owner has approved required signoffs and cloud artifacts. Upload new releases *privately*, verify complete processing, original thumbnail/captions serving, schedule for the exact approved **future** UTC, then independently read back twice. If a target time has passed, stop instead of accidentally publishing immediately.
5. **Close individual scopes**, record authenticated video IDs and replay-safe immutable receipts in the private ledger; reconcile all 24 planned slots, including the already-public Nov 4 exception.

## Exact remaining intended release times (IST)

| Date | Time | Format | Subject | Latest state |
|---|---|---|---|---|
| Nov 7 | 16:00 | Long | How Websites Load: DNS & HTTPS | Private video exists; needs assets and schedule |
| Nov 10 | 16:00 | Long | AI Fact-Checking Workflow | Local master only; secure cloud staging required |
| Nov 11 | 11:00 | Short | Chrome Extension Permissions | Local master only; secure cloud staging required |
| Nov 11 | 16:00 | Long | Browser Extension Safety Audit | Local master only; secure cloud staging required |
| Nov 11 | 20:30 | Short | Restrict Extension Access to One Site | Local master only; secure cloud staging required |

**GitHub-only status:** No media has been uploaded or scheduled during this repository audit. GitHub tasks #6 and the private release inventory preserve the exact next step. Do not claim these five are scheduled based on scoped permissions, drafts or this document.

Owner decision needed for actual completion: **provide/authorize a one-time secure staging path for the existing exact media files and suitable authenticated GitHub Actions workflow dispatch**, or separately permit completing Branch 1 through the previously authorized assisted computer path. Branch 2's no-laptop rule remains unchanged under either option.
