# V3 Research — Excel Leading Zeros / Identifier Integrity

## Why this topic

A recent r/excel discussion posted on 2026-09-29 received hundreds of upvotes from users frustrated that Excel removes leading zeros. This is a current, concrete pain point rather than a generic "Excel tip."

Discussion:
- https://www.reddit.com/r/excel/comments/1wthj0w/i_hate_how_excel_removes_leading_zeroes/

Additional historical discussions show the same problem causes risk when CSV files are prepared for database imports:
- https://www.reddit.com/r/excel/comments/1jg77wc/leading_zeroes_in_csvs/
- https://www.reddit.com/r/excel/comments/1cbzdxc/how_to_keep_leading_zeros_from_dropping_in_csv/

## Microsoft documentation

Microsoft confirms that Excel can:
- remove leading zeros from numerical text;
- truncate numerical data beyond 15 digits;
- display large numeric-looking values in scientific notation;
- convert some text-like values automatically.

Microsoft's recommended safer import path includes:
1. Data;
2. From Text/CSV;
3. Transform Data / Query Editor;
4. set identifier columns to Text;
5. Close & Load.

Sources:
- https://support.microsoft.com/en-us/excel/keeping-leading-zeros-and-large-numbers
- https://support.microsoft.com/en-us/excel/data-import-and-analysis-options-in-excel
- https://support.microsoft.com/en-us/excel/format-numbers-as-text

## Content angle

Do not frame this as "Excel is broken."

Frame it as a data-type problem:
- identifiers can contain only digits while still not representing quantities;
- product codes, phone numbers, postal codes and IDs may need text semantics;
- the viewer should preserve original data before transformations.

## V3 visual language

V3 intentionally differs from V2:
- CSV file card rather than spreadsheet cleanup dashboard;
- red auto-conversion beam;
- visible 00123 → 123 mutation;
- long ID → scientific notation mutation;
- protected four-stage import pipeline;
- final preserved identifier card.

## Safety / accuracy

The Short does not claim every Excel version behaves identically. It demonstrates documented automatic-conversion behavior and a supported import workflow.
