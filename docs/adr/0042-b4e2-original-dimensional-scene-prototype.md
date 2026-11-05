# ADR-0042 — B4e2 original cinematic 2.5D science scenes: physical art proof only

Date: 2026-11-05 IST. Track: Branch 2. Status: original source/Pillow prototype on GitHub; **not integrated into full MP4 renderer or YouTube**.

## Why the second phase is essential

The owner's rating of the previous technically passing three videos was **0/10**, supported by screenshots showing giant overlapping subtitles, low-quality simple diagrams and presentation-like thumbnails. B4e1 PR #46 has now merged the native ASS caption, new original editorial thumbnails and synthesized UI SFX after eight exact-head green CI runs, including real full three-topic narrated media. That fixes measured typography and sound plumbing, **NOT** the central diagram's basic 2D appearance or authentic owner visual approval. Real post-merge two-Short preview run 41982440785 is independently checked before claiming any new sample video bytes exist.

The uploaded 147.533-s, 30fps reference was analyzed in private; do not commit, copy or imitate its copyrighted subjects, branding or soundtrack. Major subject-change reveals measured at approximately 5.5, 28.5, 41.5, 69.5, 82, 88, 101.5, 116.5, 126.5, 136.5 and 141.5 seconds. At 2fps, the central normalized image motion difference median was 0.0129 and 95th percentile 0.210, showing a mix of quiet holds and deliberate reveals rather than random motion. Audio roughly -22.1 LUFS, 2.5 LU loudness range; waveform measurements do not prove any exact typing/notification sound or narrator identity.

## Source-only independent cinematic panel prototype

The new autopilot/cinematic_scene_v3.py uses original PIL/CairoSVG drawings at native 1080x1920 Short or 1920x1080 long resolution. It draws shaded topic-specific, isometric/2.5D-style objects with separate layers, soft radial studio lighting, shadow, restrained kinetic indicator and original UI labels:

- NASA Moon signal — spherical shaded Earth and cratered Moon, luminous beam and moving radio packet, no NASA image.
- USGS earthquake — extruded M5/M6/M7 magnitude-energy diagram columns, top surfaces, dark sides and staged highlight, not a real measured damage map.
- NIST bits and bytes — original perspective laptop/screen, progress meter and dynamically highlighted digital bit tiles, no copied app interface.

Source spoken claims and their public science storyboards are not altered. Original context labels and scene sequence are bounded to the existing authored stories. The compositing region in portrait is x74..1006/y533..1220 (captions start y1295), and in landscape x130..1790/y280..720 (captions start y756). Strict physical pixel comparisons REFUSE drawing in either native subtitle band. This is simulated shaded **2.5D**, not an actual Blender/3D animation render. The source still uses a sparse five-frame-per-scene sampling when later integrated; seamless 30fps object choreography is future work.

The dedicated autopilot/test_cinematic_scene_v3.py checks real Pillow pixels/motion, separate scene theme identity, no modification outside art region, exact original 1080p/landscape images, no approvals/secret imports and safe source scene indices. Dedicated read-only GitHub PR workflow flowminute-b4e2-scene-pixel-prototype.yml actually renders THREE original PNG scenes and retains them as a temporary 7-day public **UNAPPROVED** technical visual review artifact. It uses no model, OAuth, paid provider, copyright external image or YouTube uploader. All subject/source/SFX content remains unapproved.

## Acceptance before integration

1. Run all prototype pixel security and artwork tests in the PR. Inspect actual retained three source scene images as composition, not just hash/test logs.
2. Owner should compare the actual images with the uploaded reference for depth, visual hierarchy, contrast, professional look and text/graphic placement. Reject if they still look like slides.
3. Only after artwork proof, attach the original compositor to the full original media renderer in a separate quality-gated change; rerender two complete source-locked Shorts, independent FFmpeg/TTS/caption/audio QA and new temporary media artifact.
4. Human full watch/listen, every scientific claim and licensing/voice rights review, actual owner credentialed release and YouTube scheduling remain separate, all FALSE. No fake approval.

Official references: [YouTube Shorts visual guides](https://support.google.com/youtube/answer/16215842), [YouTube Shorts editing](https://support.google.com/youtube/answer/13380879), [FFmpeg/libass native drawing](https://ffmpeg.org/ffmpeg-filters.html), [W3C video and audio accessibility](https://www.w3.org/WAI/media/av/av-content/).

Production rubric: **40/100**, real unattended YouTube proof **0/21**. Branch 1 untouched. Code and preview bytes only through GitHub-hosted runners; no owner's laptop memory.
