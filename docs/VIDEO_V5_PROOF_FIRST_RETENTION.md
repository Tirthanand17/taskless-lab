# FlowMinute Lab — V5 Proof-First Retention Design

Date: 2026-10-02

## Decision

V5 keeps realistic software demonstration as the primary visual mode, but changes the edit grammar from “explain then prove” to **proof → action → failure → cause → fix → side-by-side verification**.

## Why this changes now

YouTube currently describes Shorts performance around appeal, engagement and satisfaction. For Shorts, useful ranking signals include whether viewers choose to watch, average view duration and average percentage viewed. Since 24 August 2026, a public view starts when playback starts, so raw starts are less useful than engaged-view and retention metrics for creative decisions.

Official sources:
- https://support.google.com/youtube/answer/11914225
- https://support.google.com/youtube/answer/12220281
- https://support.google.com/youtube/answer/16559650
- https://support.google.com/youtube/answer/9314415

## V5 editing rules

- proof of the surprising failure in the first 1–1.5 seconds;
- first real UI action by ~3 seconds;
- no title card or branded intro;
- target runtime ~30 seconds;
- use animated row movement, selection and before/after state changes instead of decorative motion;
- use a brief camera push only on the failure reveal and verification;
- captions stay one line and below the teaching surface;
- after the fix, show wrong and correct outputs side-by-side before the memory rule;
- every animation must communicate data state, cursor action, cause, or verification.

## Topic

Power Query can keep an unexpected duplicate after sorting.

Microsoft documents that Table.Distinct does not guarantee which duplicate is preserved because folding/optimization can alter evaluation, and recommends Table.Buffer when predictable duplicate removal is needed.

Source:
- https://learn.microsoft.com/en-us/powerquery-m/table-distinct

## Visual story

0–1.5s: immediate proof strip — newest row is 01 Oct, but 12 Sep survives duplicate removal.

1.5–5s: realistic Power Query table sorted newest first.

5–9s: click Remove Duplicates and animate the wrong survivor.

9–13s: compact cause overlay over the real UI; no cutaway slideshow.

13–22s: formula-bar fix using Table.Buffer then Table.Distinct.

22–27s: rerun and show 01 Oct surviving.

27–29s: side-by-side WRONG vs FIXED comparison.

29–30s: compact memory rule.

## Experiment hypothesis

Compared with V4, proof-first failure plus a shorter runtime should improve stayed-to-watch and average percentage viewed. The side-by-side verification is intended to create a clear payoff without adding narration time.

Do not declare the design successful from raw views or tiny samples. Compare engaged views, stayed-to-watch, average view duration and average percentage viewed after enough meaningful traffic is available.
