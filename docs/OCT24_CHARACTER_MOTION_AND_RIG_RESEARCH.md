# FlowMinute Lab: real character animation and premium rig replacement

**Checkpoint:** 2026-10-23; draft development branch only. Existing OAuth/publishing safeguards remain intact.

## What changed

The earlier 3D preview relied on fixed arm positions and a self-moving floating warning object. This new deterministic motion engine specifies an exact physical handoff by using a 2-bone analytical inverse-kinematics solver, smooth trajectories, face-on cube contacts, independent blinking timing and a verification moment. Its tests reject arm stretching and inconsistent object custody.

- \`autopilot/character_motion.py\`: validated mathematical hand/object positions, elbows, blinks and separate grasp windows.
- \`autopilot/test_character_motion.py\`: eight new tests including unreachable targets and precise grasp alignment.
- Actual isolated runtime demonstration: 8.000-second H.264/AAC 960×540 MP4; 12 fps, 96 frames; 971,858 bytes. FFmpeg full decode PASS.
- Preview SHA256: \`ff7cca14482b44ab1e12899e42c3ceb9f751ec2a8a7bda0162a2fe798679e04d\`.
- Kinematic QA: evaluated 97 timestamps including endpoint, maximum calculated grasp error 5.6×10⁻¹⁷ scene-local units. **Numerical contact is not proof of natural-looking hand anatomy, rig quality or speech**.
- Audio contains original synthetic sound effects only. No voiceover, lip sync, rights signoff or finished episode.
- The preview MP4 remains a conversation artifact and **is not a GitHub-hosted or scheduled video**.

## Reproducible no-upload render runner

The implementation is now also versioned as `scripts/render_character_contact.py`. It consumes the tested `autopilot.character_motion.sample()` poses and produces an actual 3D VTK mesh MP4, with physical limb transforms. It does **not** generate narration, run YouTube upload, or pretend its procedural models are premium-quality assets.

Run only on an explicitly allowed renderer with VTK, NumPy, Pillow and FFmpeg installed; provide an existing non-Desktop folder:

```bash
python scripts/render_character_contact.py --out /existing/allowed/render-folder
```

One isolated test run of the reproducible renderer produced a separate 8.000-second, 854×480 H.264 technical proof (96 frames, 130,386 bytes), FFmpeg full decode PASS. SHA256: `b49cbfd943b0ad55987349030b713b505f939f0a2de20d6cc5eb3ef30e5b17d4`. This is not the same artifact as the larger 960×540 sound-effects demonstration; the simplified reproducible proof has no audio. Neither is publish-ready.

## Premium rig research

See \`content/asset_research/free_character_rig_candidates.json\`. Official free Blender Studio *Rain* and *Einar* rigs (CC-BY attribution required) are higher-detail prospects than procedural mannequin characters. Kenney's animated character pack is CC0, but deliberately low-poly; not comparable to premium 3D faces. Older Quaternius character packs may be usable but exact pack licenses must be checked against its newer license policy.

**None of these assets has been downloaded, modified, imported, licensed by an on-file pack manifest or QA-cleared.** Do not claim production is running with them.

Sources:
- https://studio.blender.org/characters/rain/v3/
- https://studio.blender.org/characters/einar/v1/
- https://kenney-assets.itch.io/animated-characters-3
- https://quaternius.com/

## Why the videos remain unscheduled

The native Blender application is not installed in the isolated execution environment, and the Runway workspace had no available video generation models/credits. Therefore this is **genuine 3D geometry animation** but not the desired polished professionally rigged cinematic cast. A free character model cannot replace verified assets, compatible rendering and performance direction by itself.

Next acceptance step: obtain a permitted Blender runtime (cloud, ₹0 verified), download one rights-cleared rig with its actual license file/hash, run a 5–10 second expressive face/hands/prop shot with human-quality voice and independent QA, then expand the three episodes. Until then, no YouTube upload or publish authorization.
