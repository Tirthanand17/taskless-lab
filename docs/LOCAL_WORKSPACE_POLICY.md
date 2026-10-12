# FlowMinute Lab — local workspace rule

**Adopted 2026-10-12 at owner's request.**

All **non-secret** FlowMinute Lab YouTube files, projects, video/audio renders, thumbnails, captions, temporary QA outputs, scripts, screenshots, export packages and Git worktrees must live under the owner's EXISTING Windows directory:

`C:\Users\Dell\Desktop\youtube con\`

Never create new FlowMinute files or folders directly under Desktop or in other unrelated user locations. Prefer using existing subdirectories under `youtube con`; create a subdirectory only if essential for coherent organization.

Current project directories:
- `youtube con\flowminute-oct11\` — main Git working copy, render code, assets and release receipts.
- `youtube con\flowminute-publisher-worktree\` — API publisher integration worktree.
- `youtube con\flowminute-natural-voice-worktree\` — narration development worktree.
- `youtube con\FlowMinuteOct11Pack\` — existing production deliverable pack.
- `youtube con\oct11-v2\`, `oct12-production\`, `oct12-v2-final\` — original export and QA directories.
- `youtube con\FlowMinute_Natural_Voice_Preview.mp3` — the narration preview (listening review required before publication).
- `youtube con\FlowMinute_Natural_Voice_Preview_QA.json` — the corresponding QA receipt.

**Private credentials (secured, 2026-10-12):** OAuth client secrets, local refresh tokens and the private upload ledger were moved into `C:\Users\Dell\Desktop\youtube con\.flowminute-private\`, **outside all Git worktrees**. After relocation, Windows ACL inspection confirmed inheritance disabled on the private folder; only `NIRALA\Dell`, `NT AUTHORITY\SYSTEM` and `BUILTIN\Administrators` have Full Control. The publishing-token file inherits only those three permissions. The parent `youtube con` folder separately grants `NIRALA\CodexSandboxUsers` Read & Execute, so never copy private files into its unprotected directories. Never commit tokens or credentials to GitHub or public artifacts.

Git worktrees were relocated using `git worktree move`, with `git worktree repair` after the main repository relocation. Do not move them using Explorer without checking Git's worktree links.

When writing example Windows PowerShell commands, use quoted paths because `youtube con` contains a space. Use `$env:USERPROFILE` or `$HOME` rather than assuming a different account. Existing scripts must be updated if their hard-coded repository locations refer to the old Desktop paths.

This policy does not authorize uploading/scheduling videos automatically. Continue to respect FlowMinute's QA and publishing gates.
