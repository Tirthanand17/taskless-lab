# FlowMinute Lab — Hindi Short source-accurate lesson cards

**18 October 2026 | Existing public Draft PR #5, offline QA only.**

The 42-second original Hindi/Hinglish Short shares the same fictional Python CSV teaching dataset as the 42-second English Short and the 432-second Hindi tutorial. The original narrated Hindi Short scene 10–20 seconds explicitly introduces **pen, notebook and eraser with their quantities and prices**, but the previous Hindi renderer displayed only generic per-item total bars. The Hindi Short's 20–30 second DictReader visual also used `csv.DictReader(rows)` without a meaningful reader source.

This update leaves all source text, 42-second timing, language-specific SRT and original video publishing blockers untouched, but fixes the content illustration:

- At 0–10s show the actual executable `product, units, price` fictional CSV columns and rows, derived from the existing `autopilot/examples/flowminute_csv_demo.py` output.
- At 10–20s show **पेन, नोटबुक, इरेज़र** with the corresponding source quantities and prices, `2 × 10 = 20`, `1 × 30 = 30`, `4 × 2 = 8`. All values are derived from the executable in-memory synthetic dataset, not newly invented numerical claims. Explicitly label the example as fictional and not a purchase.
- At 20–30s show the source-matched conceptual `output.getvalue()`, `StringIO(csv_text)`, `csv.DictReader(source)` and product-key example. These code lines illustrate consecutive real operations performed by the existing teaching demo; they are not an actual execution screenshot.
- At 30–42s the Short retains the original numerically checked `20 + 30 + 8 = 58` example-unit total and non-release disclaimers.

The implementation adds a four-scene Hindi Short storyboard without affecting the 24-scene Hindi long storyboard or English Short. New regression checks verify original source-derived Hindi product mapping, real runnable row totals, all four visual scene pixels, the absence of `DictReader(rows)` and actual font-metric horizontal bounds on the Short's item/code cards.

No voice recordings, new fonts, image downloads, paid tools, personal files, Nirala/desktop, Google/YouTube access, production D1, server writes, media persistence, or actual YouTube upload/schedule/publish. All media is intentionally **silent and unapproved**. The two draft PRs remain unmerged. Budget recurring ₹0. The original 21 production acceptance subphases across six unfinished major phases remain OPEN; this is one technical/content subgate, not production readiness.
