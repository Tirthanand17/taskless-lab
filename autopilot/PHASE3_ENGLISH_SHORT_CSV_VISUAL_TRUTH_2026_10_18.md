# FlowMinute Lab — English Short fictional-data visual truth

**18 October 2026 | Phase 3 real content quality, existing public Draft PR #5 | Not publishable**

## Actual defect fixed

The English 42-second portrait Short's first visual card previously paired unrelated labels such as PRODUCT/UNITS/PRICE with product names and totals. The following three-product panel showed standalone amounts but did not clearly show **quantity × price**. Its DictReader overlay displayed `csv.DictReader(rows)` without explaining a real input stream, even though the executable educational demo actually reads the written CSV text back through an in-memory `StringIO`.

## Current behavior

The original `autopilot/phase3_csv_visual_preview.py` renderer now binds all four visual scenes to the same **executable, in-memory, fictional** dataset already used in the Hindi tutorial: Pen 2×10=20, Notebook 1×30=30, Eraser 4×2=8, total 58 non-currency example units. This is not made-up content copied into a secondary graphic ledger; rows, numeric totals, original item labels, and non-purchase/no-publishing declarations are verified against `examples/flowminute_csv_demo.py` on every frame. The renderer fails closed if its basic original lesson invariants drift.

- Scene 1 (0–10s): a correctly structured **product / units / price** three-column fictional CSV table.
- Scene 2 (10–20s): three distinct fictional products with each **units × example price = row total**.
- Scene 3 (20–30s): the conceptual in-memory sequence **output.getvalue() → StringIO(csv_text) → csv.DictReader(source)**, marked as an illustration, not code executed in a captured real application.
- Scene 4 (30–42s): dynamically derived **20 + 30 + 8 = 58** in explicit non-currency example units, with the original English CTA/caption plan unchanged.

Tests now compare the actual code demo source rows and computed line totals with the visual data, exercise tampered/contradictory numeric claims, and render one distinctive frame from each of the four script scenes. Existing silent H.264 FFmpeg media tests, script-derived estimated English SRT, SHA-bound receipts and public cloud runner media smoke remain in place.

## Still not complete

Actual licensed natural English and Hindi narrations, two audibly distinct Shorts voices, genuine native language editorial checking, voice-to-caption synchronization, professional cinematic 3D/VFX, final safe multimedia rights, source verification, account-authenticated YouTube release and growth analytics are **not provided** by this code. Both existing GitHub PRs remain DRAFT/unmerged. No laptop/Nirala, new account/provider, paid subscription, private CI, production D1, actual YouTube API read/write, uploaded assets, scheduled publish or charges. ₹0 monthly infrastructure budget remains unchanged, with **21 incomplete production acceptance subphases** across six unfinished major phases.
