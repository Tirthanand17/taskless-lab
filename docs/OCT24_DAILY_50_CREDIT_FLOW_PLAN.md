# FlowMinute Lab — 50-credit daily video budget (October 23, 2026)

## Why

Google's official Flow credit guide lists **720p Gemini Omni Flash 8s = 12 credits** and **10s = 15 credits**, per generation. Google's free Flow tier advertises 50 daily credits. These are published allowances, **not a live balance check or a guarantee of account access**. See https://support.google.com/flow/answer/16526234 and https://labs.google/fx/tools/flow.

## Credit-capped staging plan

Use `python scripts/flow_pilot_plan.py --mode daily_50_credit`. Four original cinematic anchor clips, eight seconds each, each at an estimated 12 credits = **48 credits**, under the published daily-free cap. This plans **0 new paid purchases**, requires actual Flow account availability/credit checks, and does not start generation.

| Episode | Clips selected | AI footage budget | Remaining unproduced educational runtime |
|---|---|---:|---:|
| October 24 English Short | 01 (hook) | 8s | 40s |
| October 24 Hindi Short | 01 (hook) | 8s | 40s |
| October 24 Hindi 5-minute story | 01 (cold open), 06 (recap) | 16s | 284s |

The remaining time is **not** silently filled with blank screens, fake software UI, low-poly reject assets, or repeated B-roll. It requires verified practical demonstrations, 3D story explanation visuals, licensed narration and actual review. The shot planning does not satisfy YouTube release QA.

## No unexpected spending

The `daily_50_credit` mode rejects a custom estimated per-shot price above 12 credits for four clips. Do not click Generate if the actual account balance is less than the estimated total, the displayed model price is higher, or free credits are unavailable. Each retry would consume extra credits. One good 10s pilot may be a better use of credits before attempting any full batch.

## Remaining upload state

**Zero approved Google Flow clips and zero YouTube schedule receipts** for October 24; no desktop use, payments, generation or publishing performed by this change. The 48-credit number is a planning estimate, not observed consumption or output quality.
