# FlowMinute Lab · 10 October 2026 · Research + premium visual production brief

## Research decision
Choose a closely related but non-repetitive three-video cluster based on demonstrated viewer pain and official documentation:
- **pilot_011 / 11:00 AM IST** — “Power Automate Says SUCCESS. Your Excel Data Is Still OLD!” Reveal the silent refresh limitation in a cloud Office Script.
- **long_005 / 4:00 PM IST** — “Why Excel Power Query Won't Auto-Refresh (3 Fixes That Work)” Compare desktop refresh-on-open, supported cloud data refresh, upstream ingestion and folder-combination.
- **pilot_012 / 8:30 PM IST** — “Stop Copy-Pasting CSV Files. Use Power Query From Folder.” Provide an accessible, concrete, repeatable transformation.

No guarantee of a viral result. Prioritize high-stakes viewer problem + compelling first-second contrast + practical verified payoff over generic feature announcements.

## Strong evidence and claim boundary
Microsoft Office Scripts in Power Automate: https://learn.microsoft.com/en-us/office/dev/scripts/testing/power-automate-troubleshooting
- Microsoft explicitly says most refresh operations are not supported through Power Automate. `Workbook.refreshAllDataConnections` returns successfully but only actually refreshes when Power BI is the source. This is not a general statement that Power Query can never refresh automatically in any environment.

Excel Desktop connections: https://support.microsoft.com/en-us/excel/refresh-an-external-data-connection-in-excel
- Excel supports data refresh when the workbook is opened and periodic refresh for supported connections, in the application's execution context. Do not imply that interval settings mean a closed workbook self-refreshes unattended in the cloud.

Power Query From Folder: https://support.microsoft.com/en-us/excel/import-data-from-a-folder-with-multiple-files-power-query
- A dedicated folder containing consistently structured files can be combined via Data > Get Data > From File > From Folder. A later refresh processes matching files. Beware unrelated files and subfolders; same schema/headers/types are recommended.

Cloud architecture: https://learn.microsoft.com/en-us/power-bi/transform-model/dataflows/dataflows-configure-consume
- Power BI dataflows can have scheduled refresh with appropriate credentials and gateway; availability and licensing must be qualified.

Community demand, directional signal only:
- https://www.reddit.com/r/excel/comments/1pgkdwm/i_legitimately_feel_like_ive_wasted_years_of_my/ (large interest in From Folder)
- https://www.reddit.com/r/excel/comments/1vs2mnu/excel_power_query_and_power_automate/ (recent failure mode)
- https://www.reddit.com/r/excel/comments/1wwgrzu/wanting_advice_automation_pathways/ (new automation demand)

## Example consistency
All examples are fictional and labeled, not actual customer data or captured Microsoft account screens.
Old records: 12 orders = $18,400. New source: 16 orders = $24,600.
Demonstration regions: North four orders × $1,500 = $6,000; South four × $1,550 = $6,200; West four × $1,550 = $6,200; East four × $1,550 = $6,200. Reconciled output: $24,600.

## Visual system
- Actual question must be visible in the first second: green flow badge next to old dashboard values.
- Grid-constrained layouts, safe margins and sans-serif typography; mobile-first closeups large enough to read at phone size.
- Use clean real-software-like illustrative reconstructions, correctly labeled as demo scenes. Never fake a live Microsoft Copilot/Power Automate session.
- Motion should direct attention to the row-count and output change; use deliberate match cuts and comparison.
- Third-party cinematic imagery is optional and must never invent software behavior. No arbitrary rotations or oversized subtitles.
- Long-form thumbnail built at 1920 × 1080 with only two focal statuses: green SUCCESS vs red STALE; short, contrastive headline.
- The thumbnail is an asset until YouTube Studio confirms it was accepted; do not call it active beforehand.

## Hard release gates
Narration timing, privacy validation, render success, visual contact-sheet inspection, platform check, Studio native schedule confirmation, real YouTube ID and per-item GitHub receipt. Never duplicate an existing upload. Store files primarily in GitHub; when Studio upload requires the authorized PC, use only `C:\Users\Dell\Desktop\youtube con` as a temporary bridge; delete files afterward.

## Publishing
10 October 2026 Asia/Kolkata: 11:00 Short, 16:00 long, 20:30 Short. Channel optimization after release should use impressions/CTR, first 30-second retention, Shorts viewed-versus-swiped, watch duration, and subscription gains, not “viral” predictions.
