# Automation Architecture

## Goal

Turn research-backed ideas into publish-ready YouTube packages with consistent quality while preventing accidental personal-data exposure.

## Pipeline

1. **Research**
   - keyword demand
   - breakout videos/channels
   - viewer problems/comments
   - freshness check for named products

2. **Episode brief**
   - one problem
   - one promised outcome
   - hook
   - demonstration
   - payoff
   - CTA
   - source notes

3. **Script**
   - short sentences
   - no filler intro
   - first two seconds deliver title promise
   - materially original explanation

4. **Voice**
   - natural high-quality synthetic narration
   - never clone or imitate a real person's voice without authorization

5. **Visual production**
   - screen/demo frames or custom motion graphics
   - visual change every 1–3 seconds for Shorts where appropriate
   - avoid generic stock-only slideshows

6. **Captions**
   - burned-in readable captions for Shorts
   - separate UTF-8 SRT generated for YouTube accessibility

7. **Packaging**
   - three thumbnail concepts
   - three title variants
   - description
   - minimal relevant hashtags
   - source/claim notes

8. **Quality gate**
   - privacy scan
   - metadata limits
   - caption coverage
   - source freshness
   - no unsupported earnings claims
   - no duplicate/repetitive episode fingerprint

9. **Publish**
   - hard-disabled by default
   - only enabled with a separately authorized brand channel and stored OAuth secrets

10. **Learning loop**
   - after 24h/72h/7d record:
     - impressions / CTR for long-form
     - stayed-to-watch for Shorts
     - average view duration
     - average percentage viewed
     - likes/comments
     - subscribers gained
   - use results to update hooks, titles, thumbnails, pacing and topic mix.

## Repository directories

- `config/` — brand and privacy rules
- `content/` — episode manifests
- `scripts/` — validation/caption/build tooling
- `docs/` — research and operating rules
- `tests/` — automated tests
