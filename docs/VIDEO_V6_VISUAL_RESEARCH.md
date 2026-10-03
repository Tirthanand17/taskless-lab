# FlowMinute Lab — V6 Hidden Character / X-Ray Research

Date: 2026-10-03

## Decision

V6 will teach a common Excel failure that feels impossible at first:

**Two IDs look identical, but XLOOKUP returns #N/A because one value contains a non-breaking space (Unicode 160).**

The visual language must be different from V4 and V5. The primary surface stays a realistic Excel worksheet, but a brief **X-ray sweep** exposes the invisible character before returning immediately to the real formula workflow.

## Evidence

### Microsoft: TRIM does not remove non-breaking space 160

Microsoft documents that TRIM removes the normal ASCII space character 32 but, by itself, does not remove the non-breaking space character with decimal value 160.

Source:
- https://support.microsoft.com/en-us/excel/functions/trim-function

### Microsoft: hidden characters can cause lookup failures

Microsoft documents hidden spaces and unexpected characters as a reason lookup/match operations can fail even when the visible text appears present.

Source:
- https://support.microsoft.com/en-us/excel/how-to-correct-a-n-a-error-in-index-match-functions

### Microsoft: diagnose and replace the character

UNICODE returns the code point for a character. SUBSTITUTE replaces chosen text within a string. For this episode, the diagnostic path is:

- compare LEN values;
- inspect the final character with UNICODE;
- reveal 160;
- replace UNICHAR(160) with a normal space;
- TRIM the result;
- rerun XLOOKUP.

Sources:
- https://support.microsoft.com/en-us/excel/functions/unicode-function
- https://support.microsoft.com/en-us/excel/functions/substitute-function
- https://support.microsoft.com/en-us/excel/functions/unichar-function

### Current community signal

Recent Excel community discussion continues to surface web-imported non-breaking spaces as a practical cause of TRIM and lookup problems.

Reference:
- https://www.reddit.com/r/ExcelTips/comments/1wsvh4q/quick_tip_combining_image_with_xlookup_for/

## Signature visual: Excel X-Ray

The hidden-character reveal lasts less than two seconds:

1. two IDs are shown as visually identical;
2. a narrow scanner line passes over the source ID;
3. the normal worksheet remains visible underneath;
4. a small callout reveals "NBSP · U+00A0 · 160";
5. the overlay labels itself as explanatory and disappears;
6. the real Excel formulas prove the diagnosis.

This is explanatory motion graphics, not fake Excel UI.

## Pacing target

- 0.0–2.5s: show the impossible-looking #N/A immediately.
- 2.5–6.0s: X-ray sweep reveals an invisible trailing character.
- 6.0–10.0s: LEN shows 7 versus 8; UNICODE shows 160.
- 10.0–14.0s: demonstrate that TRIM alone still leaves the mismatch.
- 14.0–22.0s: replace UNICHAR(160), then TRIM.
- 22.0–27.0s: rerun XLOOKUP and show a successful match.
- 27.0–30.0s: memory rule.

## Design constraints

- Realistic Excel UI should occupy at least 70% of teaching time.
- X-ray overlay maximum: 2 seconds.
- X-ray must be explicitly labeled explanatory.
- No giant centered subtitles.
- Captions: one line, below the worksheet.
- Keep visible cursor/click behavior.
- Show actual before → diagnose → formula fix → after.
- No random particles, unrelated 3D, or decorative motion.
