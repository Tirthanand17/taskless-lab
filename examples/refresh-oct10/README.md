# Reproduce the FlowMinute Lab refresh example

These records are fictional. They contain no real people, accounts, financial transactions or personal data.

| Files | Orders | Sum |
|---|---:|---:|
| North.csv | 4 | $6,000 |
| South.csv | 4 | $6,200 |
| West.csv | 4 | $6,200 |
| Initial three files | **12** | **$18,400** |
| East.csv (added later) | 4 | $6,200 |
| After refreshing four files | **16** | **$24,600** |

In Excel Desktop use **Data > Get Data > From File > From Folder**. Put North, South and West in a dedicated folder, choose Combine and Transform Data, inspect the data types, and load. Add East.csv to the same folder and **refresh the query in Excel**. The new rows should appear.

This demonstrates folder combination and manual query refresh, **not cloud scheduling**.

Do not assume a Power Automate cloud flow calling `workbook.refreshAllDataConnections()` will refresh this Excel CSV Power Query connection. Microsoft documents that the method only refreshes when Power BI is the source when run from Power Automate.

Sources:
- https://support.microsoft.com/en-us/excel/import-data-from-a-folder-with-multiple-files-power-query
- https://learn.microsoft.com/en-us/office/dev/scripts/testing/power-automate-troubleshooting
