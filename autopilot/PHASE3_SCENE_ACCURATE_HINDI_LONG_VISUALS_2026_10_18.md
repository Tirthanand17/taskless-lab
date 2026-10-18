# FlowMinute — original Hindi long video scene-accurate graphics

**18 October 2026 · public Draft PR #5 · research/QA render only**

## Actual content problem fixed

The previously implemented 432-second / 24-scene Hindi long tutorial reused just four generic chart/card layouts in a strict `scene_number % 4` cycle. It was technically full-length HD and decoded cleanly, but that did not mean **scene visuals matched their actual spoken subject**. Narration about consent/privacy could display an unrelated total; lessons on CSV quoting or `newline=""` could show pen/notebook bars.

## 24 original storyboard contexts

`autopilot/phase3_hindi_visual_preview.py` now contains exactly 24 separately mapped storyboard entries, with short Devanagari topic headers for the original fixed script. It preserves four foundational displays while adding two new graphics types and scene-specific content:

- **Source rows:** CSV input, named headers, fictional product example, and source parsing.
- **Privacy:** no real customer/purchase records, fictional local sample teaching context, and a separate shield/lock-like graphic.
- **Code:** different examples for `import csv`, in-memory `io.StringIO`, `DictWriter`, `DictReader`, string-to-number conversion, escaped/quoted comma fields, documentation's `newline=""` setting and source code exercise. Each is a labeled **illustrative simulation**, not executed UI or an authenticated screenshot.
- **Math:** correct row-focus and progressive totals for pen `2×10=20`, notebook `20+30=50`, eraser `50+8=58`; the final total is clearly **fictional example units**, never a real bill.
- **Process:** clean source, read named columns, validate inputs, check results, and follow-up topic prompts; no claim that the viewer's purchases or records were processed.
- **Recap:** original numerical outcome and final education takeaway with the existing FM brand and captions.

All diagrams are custom motion graphics drawn with existing Pillow/System Noto Devanagari fonts/FFmpeg, not photorealistic assets. Their layout semantics are improved, but **independent human visual/art direction**, actual native-language voiced timing, real professional 3D/VFX, genuine licensed narration, publication and analytics remain unverified.

Existing caption rendering, full-HD smoke, original voice/source script, SHA-bound media receipt checks, no-audio/no-publish controls, sample data and consistent branding stay in place. Regression tests prove 24 unique textual scene topics and actual code/maths/privacy/process frame drawing. Synthetic cloud smoke renders remain ephemeral and should be checked separately on exact commit. No real media stored, no external graphics/models/download, no user's PC/Nirala, new service or paid charges. Both PRs remain DRAFT/unmerged; budget recurring ₹0; **21 production acceptance subphases across six major incomplete phases remain**.


## Landscape code-card typography safety

During the 24-scene rewrite, the landscape panel was found to have inherited a four-line code layout whose fourth line extended below the content card and could overlap its `ILLUSTRATIVE SIMULATION` provenance label. Code was moved higher, its line spacing tightened and its Latin font moderately reduced **only for the landscape long-video code scenes**. The short-video code panel is unchanged. The added test evaluates all scene-specific code samples against the installed Latin font's actual text widths and verifies the fourth line fits above the footer with a measurable vertical gap. The render still requires independent human review at native HD.
