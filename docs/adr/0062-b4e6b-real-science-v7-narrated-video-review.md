# ADR-0062 — B4e6b real full narrated source-action videos, still unapproved

**2026-11-06 IST. Scope:** original NASA/NIST/USGS demonstration media only. Production readiness still 40/100; **0/21** unattended owner-verified YouTube releases.

## What the previous milestones actually proved

B4e5 merged all 32 source beats / 96 source-motion frames contact review, revealing generic repeated diagrams. B4e6 merged 19 original science-action hero redesigns, retaining 13 appropriate scenes and preserving source science narrations and caption-safe top/bottom regions. Actual scene-art and frame bridge tests do **not** imply that full voice+AAC+H264 videos with these new illustrations have been encoded. The old B4e4c media are genuine full-length **floating v6** demos, not newly improved B4e6 videos.

## New physical proof

- `autopilot/retain_science_v7_three_v8.py` renders **the same three source-locked original science demos** into three complete fully spoken `science_v7` H.264/AAC videos, physical SRT/native ASS-caption overlays, original scene SFX, thumbnails and sampled actual encoded MP4 screenshots. It uses the previously validated `autopilot.full_topic_narrated_pack.render_full_topic_video()` and independently checks encoded speech, caption alignment, audio loudness and final codec/decode through existing quality reports. This is a real working render path; only a **successful main-branch run** can demonstrate real physical execution, not the PR alone.
- For each video it compares one source-action scene index with identical source narration/heading (Moon Short scene 3, data long scene 8, earthquake Short scene 3), drawing old `floating_v6` and new `science_v7` on matching original full native source canvases. Source visuals have not silently become a copied third-party video.
- `autopilot/test_retain_science_v7_three_v8.py` exercises physical native old/new illustration comparison, frozen story/source safety, file receipts and ensures nonpublish flags remain false.
- New PR workflow `.github/workflows/flowminute-b4e6b-real-science-v7-three-video-review.yml`: PRs run only **unprivileged local source/visual tests**, without AWS, YouTube, Google OAuth, paid LLM or model downloads. On **merged `main` push** it runs a physically rendered, **one-time proof** using SHA256-pinned public Kokoro model and voices, local FFmpeg/espeak/NumPy/Pillow/CairoSVG, bounded install, real three demos and independent file SHA rehashing. Retains media+proof in a **7-day public GitHub Actions artifact**, deletes temporary voices/media thereafter. GitHub-hosted runner storage and Actions minutes depend on account quotas, not unlimited free compute.
- The original source narrative remains unchanged, including date 2026-11-12 and facts curated Nov 4. We intentionally do **not** rename or claim these are independently researched **fresh stories** for each future day; no source-fact or human rights approvals are signed by technical tests.

## Important gaps: source QA is not viewer approval

Even when a full encoded MP4 is technically valid, an owner must actually watch/listen to **all** content, check real narrated text and voice license, scientific claim interpretation, copyrighted material and caption readability from mobile, and approve intentional creative pacing. A set of samples does not prove no distracting circles or generic motion remain, or any uplift in YouTube engaged views. The visual artwork includes source-correct Earth/Moon planetary geometry where needed, distinct from a needless loading spinner.

The current static review and source sound/effect recipes are **not** a new live story generator, a fact checker, a private escrow, approved AWS IAM/billing, real Google OAuth, or an actual YouTube video insert. A full generated artifact is publicly viewable/temporary. Do not place private scripts, sensitive accounts, owner OAuth, or unlicensed proprietary recordings in public Actions.

**Production target remains:** 2 actually fresh, differentiated, reviewed Shorts at 11:00/20:30 IST and 1 long at 16:00 IST every day, owner-authorized private cloud/storage/publisher plus 21 consecutive independent verified laptop-off releases. No B4e6b job may authorize release or alter Branch 1 existing scheduled video IDs.

## Source references

- `docs/adr/0061-b4e6-original-action-specific-visual-polish.md`
- `autopilot/action_specific_floating_v7.py`
- `autopilot/independent_av_review.py`
- `autopilot/retain_science_v7_three_v8.py`
- `.github/workflows/flowminute-b4e6b-real-science-v7-three-video-review.yml`
