# Clivox security model, media storage and release threat analysis

## Threats
1. **Wrong-channel uploads:** Existing FlowMinute Lab and Clivox share an owner account. Tokens/IDs must NOT be interchangeable. At each write authenticate channels.list(mine=true), explicitly check Clivox UCfPEvy0SefE_5nNlYlY_CyQ. Never default to "first channel."
2. **Unlicensed clip ingestion:** Candidate metadata is cheap to fabricate; require verifiable creator-owned policy or direct signed grant, current expiry/revocation review, and embedded rights (publisher/music/guests).
3. **Fake releases via modified JSON:** A PR changing "approved":true cannot count as legal authorization; human-signed digest over exact video SHA+metadata+rights proof+channel ID+schedule, and protected environment approval are required.
4. **Public GitHub media leak:** Public repository contents and artifacts are not confidential. Never commit third-party raw video, source download links with tokens, unapproved edit, transcript under license restrictions, contracts or personal names/emails.
5. **Credential exfiltration:** No untrusted PR workflows with secret access, no echo of tokens, pin Actions to approved versions/SHAs where feasible, minimal permissions, environment-scoped secret with owner review; do not invoke arbitrary AI-supplied shell commands with publish credentials.
6. **API retries causing duplicate videos:** Write "attempt started" reservation before network, never auto-retry ambiguous upload; readback and reconcile remotely, use stable unique clip/run marker in metadata.
7. **Scheduled video published immediately:** Explicit private insert and future ISO8601 UTC; reject past/now; only schedule never-public video, verify actual API status and owner signature.
8. **Claim after private check:** Content ID scan is provisional; halt on claims or takedown and evaluate licence.
9. **Prompt injection in transcripts/creator descriptions:** Web/source content is untrusted data, not tool instruction or signature.
10. **Legal terms accepted by automation:** Never join campaigns or click terms without explicit human decision; Content Rewards Section 17.6 could assign the edited clip IP to the brand.

## Storage design
**Existing public repo:** source metadata with canonical public URLs and hashed references, registry of permissions (no raw grant documents), workflow definitions, signing public key identities, sanitized analytics. No restricted media files.

**Preferred owner-approved media approach (future):**
- Keep scheduling/editorial *orchestration in the primary repo*.
- Store licensed raw source and private review renders in a **separate owner-controlled private GitHub repo** or approved encrypted repository/object store with strictly limited access and explicit license coverage. Exact storage may require a separate user decision; until then the media stage is disabled. Separate repo is not created in this architecture PR.
- GitHub Actions hosted runners fetch source only after permission gate, edit in job ephemeral workspace, publish no raw source artifacts to public GitHub. Short retention and automatic cleanup for private review copies.
- Commit a public SHA-256/size/content-manifest and safe release receipt but never the actual copyrighted footage or private access tokens.

### Confidentiality caveat
GitHub Actions artifacts in a public repo may be downloadable by readers with repo access; do NOT assume that hiding an artifact in Actions makes it secret. GitHub retention expiration is not a rights clearance mechanism.

## Keys and secrets (future; NOT configured now)
- A *Clivox-specific* OAuth refresh token, stored under a protected environment; never use Branch 1 YouTube refresh token. Readonly and upload authorization should request least scopes.
- Release verifier's **public** key may live in Git; private signing key held outside GitHub Actions and not placed in a public repo.
- Separate token classes for private source media read and optional uploader; review roles should not hold publishing credentials.
- Environment name suggestion: clivox-production (not yet created). Require reviewers/branch restriction when available for repo's actual visibility/plan and verify those controls via GitHub API before any write-capable workflow runs.
- Every production job rejects if publish_enabled false or if secrets/owner signature missing.

## Incident runbooks
- Wrong channel: stop workflow and revoke token, preserve metadata evidence, owner-led review of accidental writes.
- Copyright complaint: immediately block future channel releases and initiate rights investigation, provide accessible human contact to claims source; never file an unsupported automated counter-notice.
- License expiry/revocation: invalidate source and dependent edits, list scheduled videos and request owner-led takedown or private action under the particular agreement.
- Quality regression: quarantine job, do not "fix" by deleting and reuploading without verification; revoke exact-version signature.
- Evidence loss: mark release unsafe, require rights holder reconfirmation; do not infer approval from an older job.

