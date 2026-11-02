# FlowMinute Lab — October 24 cinematic pilot execution handoff

Status: **one-shot production package prepared, zero generated Flow clips, zero YouTube scheduling receipts**.

## Why this path
Retire the earlier rounded mannequin / low-poly renderer from final media. Reusable Google Flow Characters plus Gemini Omni Flash is the proposed real-cinematic method. The user's Asha and Jay portraits are in the conversation download **FlowMinute_Google_Flow_10s_Pilot_Kit.zip**. Those binary images are not in GitHub.

## Credit and authorization guardrail
Use the existing signed-in Google account at https://labs.google/fx/tools/flow . Confirm the actual available balance, character-creation image generation cost, and a single 10-second 720p Omni Flash cost before generation. Current documented rate is 15 credits per 10-second 720p generation, but Flow UI takes precedence. Do not make more than one variation, use bought credits, connect new services, activate paid API billing, charge any money, or access Nirala.

## First shot
Create two reusable Characters from the original portraits: Asha (navy jacket with cyan piping) and Jay (navy hoodie, round glasses). Choose two distinct conversational English voices.

Exact pilot prompt:
> A single continuous ten-second 9:16 cinematic 3D-looking AI workshop shot. Keep exact visual appearance, outfits and natural voices of saved Asha and Jay. Jay holds a physical teal cube with believable five-finger grip, looks curious, and asks, 'Does this replace Gemini?' Asha gently smiles, moves a second distinct amber AI-model cube from the shelf to a neighboring slot in a physical workflow console, and replies, 'No. Developers get another choice.' Both cubes remain visible; a single cyan workflow rail lights up. Natural eye contact, subtle blinking, realistic anatomy, brushed metal and glass, soft cinematic lighting, navy/teal/amber color palette, restrained slow dolly. Exactly two voices, no extra speech, no music, captions, fabricated app screens, logos, hard scene cuts, melting faces, low-poly mannequins or unwanted graphics.

## Go/no-go quality check
Review the actual downloaded ten-second MP4 for character identity continuity, right words and speakers, convincing lips/eyes, grip and object physics, stable cube count, accurate single-scene camera and readable visual payoff. No automatic credit-consuming retry.

## Offline post-generation quality gate
From an authorized machine/container with repository and FFmpeg, run:

    python scripts/flow_clip_intake.py --file /authorized/path/flow_pilot.mp4 --episode fm_20261024_short_en --clip 01 --mode pilot

This yields only technical draft metadata (SHA-256, aspect, full decode, streams). It cannot verify actual Flow provenance, creative realism, rights, lip sync, subtitles, factual accuracy or publishing.

## Why not scheduled
The first ten-second clip has not been generated. For the three planned October 24 videos, another 38 seconds of the English Short, 38 seconds of the Hindi Short and 270 seconds of the Hindi long video would still require production under the five-anchor-clip plan. Narration, subtitles and independent QA are also missing. No Google Flow credits spent; no videos uploaded.

## Cloud-browser option
If Work mode is available and supports navigating Google Flow, give it the attached starter kit and the requirement to use ONLY existing credits to generate ONE pilot with no retries, no paid signup, no Nirala access, no YouTube upload or publication. A cloud-browser account connection and site compatibility need the user's own authorization.

Official sources:
https://support.google.com/flow/answer/16935308
https://support.google.com/flow/answer/16353334
https://support.google.com/flow/answer/16526234

PR: https://github.com/Tirthanand17/taskless-lab/pull/6
