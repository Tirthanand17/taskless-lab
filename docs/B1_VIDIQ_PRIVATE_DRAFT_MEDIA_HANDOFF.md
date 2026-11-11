# Branch 1 — private GitHub-to-vidIQ media import bridge (Nov 13–17)

Owner has completed YouTube MFA on November 11. Connected vidIQ now reports `status=verified`, channel `UCCcL9Q_jqVq6LJmnYUSAFZA` and `canPublish=true`. This **does not** schedule any video. Previous GitHub owner OAuth token returned `OAUTH_REFRESH_FAILED`; do not assume those are the same channel credentials.

## Why a bridge is required

The 15 successful final B1v4 review runs (`42980029138`, `42980034017`, `42980038709`, `42980042798`, `42980047435`) yielded exact source-hash verified original MP4 files. The `vidiq_video_upload` connector accepts a public HTTPS MP4 download or an OpenAI client file input; generated local sandbox file paths cannot be sent as its accepted file object. A direct file-reference string was rejected. We therefore seek a controlled video delivery route **without storing media on the owner's Windows laptop**, publishing GitHub releases, or exposing YouTube OAuth.

## Cloud-only experimental transfer

The workflow `.github/workflows/flowminute-b1-private-vidiq-handoff.yml` is manual, main-only, and restricted to exactly five immutable B1v4 GitHub Actions run IDs and one expected main source SHA.

For one date, it verifies the original run from GitHub API, downloads the expected GitHub artifact, SHA-256 verifies all 3 exact MP4/SRT/thumbnail/contact files and original source episode scripts, and uploads **only the three verified MP4s** to the already-created **GitHub DRAFT** release `fm-b1-owner-private-handoff-2026-11-13-17`. It checks the release is still `draft=true`. A GitHub draft is not publicly listed; do **not** publish it, and do not reveal its assets as public downloads.

The videos remain original, source-linked fictional illustrations with synthetic narration. There is no upload to YouTube and no owner-signed final release.

**Strict export test:** First verify GitHub can produce a time-limited, nonpublic and downloadable HTTPS MP4 URL for just the owner's vidIQ import. If not, do not switch the release from draft to published. Avoid introducing a publicly fetchable prerelease to work around the access gate. If the direct import requires an intentionally public video link or manual file picker, stop and ask the owner how to proceed.

**After import:** Use `vidiq_social_account_list` to bind `UCCcL9Q_jqVq6LJmnYUSAFZA`, create a draft per intended video with the full exact immutable MP4 and private `publishAt`, inspect draft status/duplicates, show each draft/revision to owner, then publish **only with owner exact-draft approval**; verify YouTube readback before claiming `scheduled`. Source approval does not substitute for exact-file rights/voice/caption approval.

**No direct public asset links, no GitHub publishing, no credentials in chat, no automatic YouTube insert, and zero fake schedule receipts.**
