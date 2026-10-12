# FlowMinute Lab — local workspace rule

**Adopted 2026-10-12 at owner's request; revised after credential relocation.**

All FlowMinute Lab YouTube files, projects, video/audio renders, thumbnails, captions, temporary QA outputs, scripts, screenshots, export packages, private credentials and Git worktrees must live inside the owner's **existing** Windows folder:

`C:\Users\Dell\Desktop\youtube con\`

Never create new FlowMinute files or folders directly under Desktop or unrelated user locations. Prefer existing subdirectories under `youtube con`; create one only when essential for organized production.

Current project directories:
- `youtube con\flowminute-oct11\` — main Git working copy, render code, assets, and release receipts.
- `youtube con\flowminute-publisher-worktree\` — API publisher integration worktree.
- `youtube con\flowminute-natural-voice-worktree\` — narration development worktree.
- `youtube con\FlowMinuteOct11Pack\` — original production pack.
- `youtube con\oct11-v2\`, `oct12-production\`, `oct12-v2-final\` — original exports and QA artifacts.
- `youtube con\FlowMinute_Natural_Voice_Preview.mp3` — 19.3-second narration sample.
- `youtube con\FlowMinute_Natural_Voice_Preview_QA.json` — corresponding QA receipt.
- `youtube con\.flowminute-private\` — local OAuth credentials and ledger (NEVER Git-track or publish).

## Security: private directory is an exception to inherited ACLs, not an exception to folder location

On 2026-10-12, the private folder was moved inside `youtube con`, with inherited read access removed. ACL audit on the owner device confirmed `NT AUTHORITY\SYSTEM`, `BUILTIN\Administrators`, and `NIRALA\Dell` have full control on the private folder; the parent `youtube con` directory separately grants `CodexSandboxUsers` read-and-execute, **which must not be inherited by the private folder**. Recheck effective ACLs after any copying, restore, or permission change. No OAuth tokens, client secrets, or upload-ledger contents may enter Git, public artifacts, screenshots, or logs.

The authorizing browser and read-only verifier scripts resolve credentials relative to their own `.flowminute-private` directory. The publisher's default ledger and read-only daily preflight also resolve this protected workspace location.

Git worktrees were relocated using `git worktree move`, followed by `git worktree repair` after moving the main repository. Don't move worktrees casually in Explorer without checking the Git links.

Always quote Windows paths because `youtube con` contains a space. Update any newly introduced script that hard-codes old Desktop or home-directory paths.

This folder policy does not itself authorize unattended video uploading or scheduling. FlowMinute production and YouTube publication QA gates remain mandatory.
