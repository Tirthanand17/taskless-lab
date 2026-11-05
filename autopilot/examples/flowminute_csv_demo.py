"""Executable synthetic CSV lesson for FlowMinute Lab; no accounts, disk or network.

This supports an ORIGINAL educational screen-demo candidate, not a rendered
video and not a grant of fact, audio, media or publishing approval.
"""
from __future__ import annotations
from csv import DictReader, DictWriter
from io import StringIO

COLUMNS = ("product", "units", "price")
ROWS = (
    {"product": "Pen", "units": "2", "price": "10"},
    {"product": "Notebook", "units": "1", "price": "30"},
    {"product": "Eraser", "units": "4", "price": "2"},
)


def demonstrate_csv_total() -> dict:
    """Use Python standard-library CSV on deliberately fictional test rows."""
    output = StringIO(newline="")
    writer = DictWriter(output, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(ROWS)
    csv_text = output.getvalue()
    with StringIO(csv_text, newline="") as source:
        reader = DictReader(source)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("Unexpected synthetic data headers")
        total = 0
        extracted = []
        for row in reader:
            if set(row) != set(COLUMNS):
                raise ValueError("Unexpected row shape")
            units, price = int(row["units"]), int(row["price"])
            if units < 0 or price < 0:
                raise ValueError("Synthetic units and price must be nonnegative")
            value = units * price
            total += value
            extracted.append({"product": row["product"], "line_total": value})
    return {
        "dataset_is_fictional": True,
        "code_executed_without_network_or_personal_files": True,
        "csv_text": csv_text,
        "rows": extracted,
        "total": total,
        "currency": "example_units_no_real_transaction",
        "purchased_anything": False,
        "youtube_uploaded": False,
        "publishing_authorized": False,
    }


if __name__ == "__main__":
    result = demonstrate_csv_total()
    print("SYNTHETIC_CSV_LESSON_TOTAL", result["total"])
    print("NO_PERSONAL_FILES_OR_NETWORK_USED")
