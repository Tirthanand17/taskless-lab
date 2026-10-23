# FlowMinute Lab — October 24 multi-character true-3D lesson phase

**Status: development branch / draft only. Nothing here claims an MP4, narration, subtitles, scheduling or a YouTube release.**

This is a GitHub-first, ₹0-infrastructure prototype implementing the requirements from the four bundled briefs: (1) learning and ethical growth; (2) cinematic 3D educational demonstrations; (3) adaptive content scheduling and verified launch research; (4) bounded specialist agents and independent QA.

## Educational format

Every episode must teach **problem → everyday analogy → visible demonstration → verification → repeatable takeaway**. The characters are not just talking heads: each full 3D shot gives them tangible props and a camera move. One character explains, one asks a realistic beginner question, and a specialist demonstrates or checks when useful. Each explanation must make one point, without a wall of jargon.

Scenes are planned as *true geometry-based 3D* with animated camera, animated characters and moving props. A still image animated with a parallax effect does **not** qualify. Readable real software steps must come from actual authorized captures; invented interfaces must carry a visible *ILLUSTRATIVE* label.

## Three episode plans (October 24, 2026, IST)

| Episode | Audience | Staging timing | Characters / set | Facts vs. fiction |
|---|---|---|---|---|
| OpenAI on Google Cloud: what really changes? | English Short | 48s, 6 shots | Asha + Jay; 3D model workshop and laboratory | Official partnership facts + metaphorical model cubes; Google Cloud product UI is **not** represented |
| Thousands of AI research agents and brain-cell data | Hindi Short | 48s, 6 shots | Kabir + Riya; 3D neuroscience lab and research library | Public research facts + imaginary laboratory presentation; **not a medical cure** |
| AI Agents and Software Security: a 3D story | Hindi long | 300s planned, 10 shots | Asha, Kabir, Riya + Omar; 3D security city, lab, developer workshop | Fictional characters illustrate a defensive reporting and patching sequence; no exploit methods |

Sources:
- https://openai.com/index/openai-models-google-cloud/
- https://openai.com/form/openai-on-google-cloud/
- https://openai.com/index/scaling-ai-research-for-complex-biological-data/
- https://openai.com/index/coordinated-disclosure-of-critical-vulnerabilities/

## What is actually implemented

1. `autopilot/story3d.py`: pure Python storyboard validation for two+ characters, role interactions, spoken dialogue, true 3D geometry intent, physical prop interaction, teaching beats, source URLs, and an explicit nine-gate QA state.
2. `content/storyboards/oct24_multicharacter_3d_plans.json`: three individual narrative scene graphs with safe, fictional illustrations and a separate learner takeaway per shot.
3. `autopilot/test_story3d.py`: regression cases for fake UI, absent evidence, slide-only scenes, single voices, incomplete QA, learner roles, missing objects, duplicate release states and wrong teaching order.
4. `scripts/validate_oct24_story3d.py`: offline CLI that validates all three plans and prints a truthful staged status.
5. `scripts/blender_story3d_preview.py`: optional **real 3D geometry** proof-of-concept, building a procedural lab, multiple stylized avatar placeholders, props and camera movement for a selected shot.

The Blender script is not equivalent to a polished film: the current generated models are stylized stand-ins without facial acting, lip synchronization, licensed human recordings or comprehensive shot-specific motion. Final model rigging and real media integration are outstanding. An image generated in chat is a static concept frame, not an animated video.

## Repeatable commands

From the repository root, with Python 3.11+:

```bash
python -m unittest autopilot.test_story3d -v
python -m scripts.validate_oct24_story3d
```

Optional local/offline Blender prototype **only on an explicitly authorized machine**, with an existing Blender installation and an output directory that already exists:

```bash
blender -b --python scripts/blender_story3d_preview.py -- --episode fm_20261024_short_en --shot 3 --output preview.mp4 --frames 96
```

This command is a manual demonstration, not a background render or upload. Do not install/run Blender on Nirala without separate permission. Cloud rendering can be considered only after verifying existing zero-cost capacity.

## Why the release is still blocked

The storyboards are **not rendered**. All nine independent QA gates are currently false: fact review, rights, character asset review, voice license, pronunciation, subtitle alignment, video decoding, visual motion review, and authenticated release receipt. The Hindi long-story dialogue has now been expanded to roughly 68–84 words per 30-second scene, but natural-voice delivery, pronunciation, exact scene synchronization and audiovisual review are still required. A preview cannot be labeled a ready-to-publish video.

No new API connection, recurring cloud bill, GitHub Actions-intensive render, upload or YouTube schedule is authorized by this draft. Merging code must not bypass the original publication controller or release ledger.

## Next engineering handoff

Connect the validated storyboard to the existing `autopilot/phase3_production.py` and Motion V2 interface without bypassing research/language gates. Source original/rights-cleared detailed rigged character models and environment props. Produce one representative voice-synced true-3D scene and inspect it, including Hindi text readability. Only then render each full video with accurate subtitles and run independent QA and authenticated YouTube reconciliation. Real screenshots should replace illustrative UI whenever the format is a practical tutorial.
