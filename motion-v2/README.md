# Motion V2

GitHub-only rendering pipeline for FlowMinute Lab.

## Design rules

- Continuous animated scene, not slide cards.
- 2.5D depth using CSS perspective and transforms.
- Main teaching visual stays in the center.
- Captions are one short line in the lower safe area.
- Integrated labels explain objects without covering them.
- Every problem is animated in context.
- Natural neural narration is generated inside GitHub Actions.
- Final MP4, SRT and 9:16 thumbnail are committed under `assets/v2/`.

## Local-storage rule

This pipeline must not require a Desktop clone or render folder. GitHub Actions is the renderer and GitHub is the artifact source of truth.

Render generation is performed by the repository workflow; no Desktop working copy is required.
