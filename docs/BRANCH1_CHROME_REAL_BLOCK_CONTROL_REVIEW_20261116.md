# Branch 1 — Real Chrome notification Block control demonstration (review only)

**Reason for change:** Current main workflow [43833221959](https://github.com/Tirthanand17/taskless-lab/actions/runs/43833221959) successfully rendered the honest one-way Chrome navigation tutorial, but its independent exact-video audit [43835813182](https://github.com/Tirthanand17/taskless-lab/actions/runs/43835813182) **rejected the Chrome Short**: 86.7% of actual central Chrome application pixels nearly unchanged, a 11.5-second frozen segment, and no visible app change within the first three seconds. Its Calc sister video passed at 44.2%. This is a measured creative failure, not a YouTube shadowban, and the Chrome output must **not** be scheduled.

## Genuine application action, not fake motion

Google's official Chrome support (https://support.google.com/chrome/answer/3220216) documents **Settings → Privacy and security → Site settings → Notifications** and the option to change the browser's default notification behavior.

On a disposable GitHub Actions Ubuntu runner only:

1. Start Google Chrome with `--user-data-dir` under a newly created temporary run folder, with extensions, sync and external accounts disabled. Never use a user's profile.
2. Open the **real** `chrome://settings/content/notifications` page, look up its actual nested Web Component radio controls from the live Chrome DOM, and use **genuine Selenium pointer clicks** to select the **Block** default option.
3. Screen-record the real blocked outcome first. Demonstrate the selected **Ask** versus **Block** radio options in the throwaway profile, confirming the actual browser's selected value changes. The user-facing navigation remains one-way through Chrome Settings, Privacy, Site settings and Notifications. Do not return to page-flip loops.
4. Verify each real click by reading Chrome's `selectedValue` state; refuse if controls are not found or the selection does not persist. Fail closed on any unknown navigation, external domain, missing real settings UI or non-disposable profile.
5. Confirm the final selected option is `block` in the temporary profile, and that all recorded changes apply only to the ephemeral profile. The runner deletes the profile when the job finishes. **No real user account, connected desktop browser or persistent setting is touched.**
6. Re-record the physical H.264 source screen, re-narrate with the existing SHA-pinned free Kokoro voice, and re-run the independently separate source-pixel creative audit. Preserve all audio, caption, checksum and exact-source quality gates.

The visual story should teach how to stop **future site notification requests**, not claim it disables existing site permissions or modifies a personal Chrome configuration. It should accurately say that the demonstrated setting change happens only in the disposable test browser.

### Explicit limitations

A Chrome Web Component may change across versions; the source code must **fail** rather than forge a successful click, revert to a mock screenshot, or insert artificial motion. An actual selected radio option is better evidence than an animated graphic. Passing motion QA still does **not** guarantee a watchable Short or improved YouTube retention. Full mobile preview, factual voice review and final exact-MP4 authorization remain open.

**No purchases. No YouTube upload or schedule. No personal browser settings modified. All media is review-only and owner-release flags remain false.**
