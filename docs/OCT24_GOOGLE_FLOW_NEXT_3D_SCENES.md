# Google Flow 3D generation — next action and real-footage acceptance

The Oct 24 English Short's old 48-second geometric explainer was **rejected** by its owner. It must not be published. The new cut is 32 seconds: the real approved 8s Asha/Jay introduction, plus **three genuinely new 8s cinematic 3D scenes** and an independently verified continuous 24s narration.

## Generation using the user's EXISTING Google Flow account

Official website: https://labs.google/fx/tools/flow

1. Open the existing Flow project. Check remaining credits beneath the account profile. **Do not purchase or upgrade.**
2. Select **Video**, **Gemini Omni Flash 720p**, **9:16 portrait**, **8 seconds** and exactly **1 output**. Confirm the current onscreen price before submitting. Google currently lists 12 credits per 8-second 720p generation, so three scenes would use 36 credits if those settings remain correct.
3. For scene 02, choose **Ingredients**. Add `Approved_Characters_Frame.jpg` (identity + outfits) and `Approved_Opener_Final_Frame.jpg` (camera + environment). These are in the existing `FlowMinute_Oct24_32s_Cinematic_3D_Production_Kit.zip`. Prompt: `content/flow/oct24_english_v2_cinematic_scene_02.txt`.
4. Generate **only scene 02 first**. Inspect its whole eight seconds, not just one frame. Reject low-poly/cartoon people, identity changes, inanimate slides, finger deformities, fake interfaces, or scene discontinuity. If rejected, do not silently regenerate and spend additional credits.
5. After scene 02 is visually approved, add its final frame as a continuity reference for scene 03; use prompt `scene_03`. Do the same for scene 04, preserving the approved original characters and tactile physical workshop. Model-dependent support for ingredients and frames must be confirmed in the active Flow interface.
6. Export the three **real MP4 files** as `scene_02_real.mp4`, `scene_03_real.mp4`, `scene_04_real.mp4`. Keep the approved opening as `Asha_Jay_Approved_8s_Reference.mp4`.
7. Run clip checks from an authorized cloud environment with FFmpeg installed:

```bash
python -m scripts.qa_oct24_cinematic_clip --file /clips/scene_02_real.mp4 --scene cinematic_02 --report /clips/qa_02.json
python -m scripts.qa_oct24_cinematic_clip --file /clips/scene_03_real.mp4 --scene cinematic_03 --report /clips/qa_03.json
python -m scripts.qa_oct24_cinematic_clip --file /clips/scene_04_real.mp4 --scene cinematic_04 --report /clips/qa_04.json
python -m scripts.stage_oct24_cinematic_v2 --directory /clips --manifest /clips/cinematic_v2_manifest.json
python -m scripts.assemble_oct24_cinematic_v2 --manifest /clips/cinematic_v2_manifest.json --voice /clips/FlowMinute_Oct24_V2_24s_CONTINUOUS_VOICE_REVIEW_ONLY.wav --output /clips/FlowMinute_Cinematic_V2_32s_REVIEW_ONLY.mp4 --report /clips/FlowMinute_Cinematic_V2_32s_QA.json
```

These scripts check hashes, duration, audio/video decode, frozen images and unique clips. **They cannot judge character identity, cinematic quality, rights or commercial accuracy:** those require human viewing and sign-off. Do not label MP4s "AI-generated 3D scenes" before real files exist.

## Credit and provider reality

Official Google Help: https://support.google.com/flow/answer/16526234 and https://support.google.com/flow/answer/16353334 . Credits are charged **per generated output**. Daily free 50-credit allowance exists, subscriber allocations depend on the actual account, and price/feature compatibility can change. Runway account presently has 0 credits and no video model on Free. HeyGen's free monthly-video limit was previously exhausted. Neither is an approved ₹0 substitute. Google Flow is not a callable connector in this ChatGPT conversation. **No generation, purchase, new external connection, laptop use, or YouTube upload was performed** by preparing these files.

## Publication state

Only 1/4 actual cinematic scene MP4s exist. The continuous voice WAV is generated but not human approved. The fully edited 32s visual file does not exist. No Oct 24 YouTube scheduling has been verified.
