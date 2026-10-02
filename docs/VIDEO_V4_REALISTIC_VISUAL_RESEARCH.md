# FlowMinute Lab — V4 Realistic Visual Research Standard

Date: 2026-10-02

## Decision

FlowMinute Lab will move from **motion-graphics-first** to **realistic task demonstration + selective motion graphics**.

The main visual should look like the viewer is watching a polished software workflow, not a deck of slides or a generic AI animation.

## Why

### YouTube recommendation / retention guidance

YouTube says the opening seconds are where viewers decide whether to stay, for both Shorts and long-form video. The beginning should immediately deliver on the title/thumbnail promise.

YouTube also recommends using retention dips, spikes, top moments and intros to determine what to move earlier, remove, or expand.

Sources:
- https://support.google.com/youtube/answer/16559650
- https://support.google.com/youtube/answer/9314415
- https://support.google.com/youtube/answer/12942217

### Monetization / authenticity

YouTube's monetization policy warns against generic, repetitive and template-like content, including slide-show-like videos and generic AI content that looks mass produced.

Therefore:
- do not reuse one fixed scene template for every episode;
- do not build videos from text cards;
- each video needs a distinct visual story tied to the actual problem;
- UI interactions, examples and verification should materially differ by topic.

Sources:
- https://support.google.com/youtube/answer/1311392
- https://support.google.com/youtube/answer/2490020

### Instructional-video research

A large meta-analysis of signaling in multimedia found that relevant visual cues improve retention/transfer and reduce cognitive load. Newer video-learning research also warns that irrelevant visual cues can make viewers miss important information.

Sources:
- https://www.sciencedirect.com/science/article/pii/S1747938X17300581
- https://www.sciencedirect.com/science/article/abs/pii/S0360131524000769

## Visual hierarchy for FlowMinute Lab

### Tier 1 — realistic software demonstration (default)

Use for:
- Excel
- CSV
- Power Query
- automation workflows
- data cleaning
- formulas

Visuals:
- realistic spreadsheet/application window;
- visible cursor movement and clicks;
- selected cells and menus;
- real values changing in place;
- before/after comparison;
- raw-file validation where useful.

This should occupy ~65–80% of tutorial screen time.

### Tier 2 — explanatory overlays

Use only to guide attention:
- arrow;
- outline;
- glow around one cell/menu;
- small label;
- zoom;
- split comparison;
- short callout.

Never cover the object being explained.

### Tier 3 — metaphor / 3D / AI-generated B-roll

Use sparingly, normally 1–3 seconds:
- invisible data transformation;
- scale;
- pipeline;
- corruption;
- validation concept.

Do not use an AI-generated visual when a real screen action explains the idea better.

Gemini/Veo or another generator may be used for these short metaphor inserts, but not for generating fake Excel instructions or UI text because generated interfaces can be inaccurate.

## Short-form explanation structure

1. **Proof hook (0–2s)** — show the failure/result before explaining it.
2. **Consequence (2–5s)** — why the viewer should care.
3. **Cause (5–9s)** — one sentence, visually demonstrated.
4. **Fix (9–22s)** — realistic UI action.
5. **Verification (22–28s)** — prove that the fix worked.
6. **Memory rule (last 2–4s)** — one sentence worth remembering.

## Long-form explanation structure

- Cold open with problem + payoff, no branded intro.
- Demonstrate before defining.
- Every chapter must answer one question.
- Return to the real application after any conceptual animation.
- Show verification before moving to the next chapter.
- Use chapters and search-intent phrasing.
- Remove dead transitions over ~0.7s unless intentionally used for a reveal.

## Caption standard

- one line whenever possible;
- lower safe area;
- 34–44 px at 1080x1920;
- caption must not repeat large integrated UI text;
- no karaoke / word-by-word animation by default;
- highlight at most one keyword;
- do not center a paragraph over the teaching visual.

## Pacing standard

Shorts:
- visible proof in first 1 second;
- first meaningful transformation by 2 seconds;
- a meaningful visual change every ~2–4 seconds, but never motion just for motion;
- prefer 24–35 seconds unless the concept genuinely needs more time.

Long-form:
- show useful content immediately;
- make the first 30 seconds match the title/thumbnail promise;
- move later retention spikes earlier when Analytics identifies them.

## Sound standard

- natural narration;
- subtle UI click for real actions;
- error tone only at failure reveal;
- subtle transition sound at major state change;
- no constant loud music competing with instruction.

## Packaging

For long-form, use YouTube's title/thumbnail A/B testing when channel advanced features are available. YouTube can test up to three variants and select based on watch time.

Source:
- https://support.google.com/youtube/answer/16391400

## Analytics loop

Do not optimize on raw views alone.

Shorts:
- engaged views;
- stayed-to-watch / swiped-away;
- average view duration;
- average percentage viewed;
- likes/comments/subscribers;
- replay behavior if available.

Long-form:
- impressions CTR;
- first-30-second retention;
- average view duration;
- retention dips/spikes;
- search terms;
- returning viewers;
- watch hours.

Do not overfit a style from fewer than ~100 meaningful views. Use low-volume early uploads primarily as qualitative tests.
