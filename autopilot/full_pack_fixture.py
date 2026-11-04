"""Original, synthetic educational benchmark fixtures (NOT reviewed video scripts).

Three distinct demonstration topics: preserve text identifiers, review duplicate
ID conflicts, and a longer inspect-validate-export workflow. The graphics are
generated from actually executed Python standard-library CSV/date functions.
No real member data, product screenshots, ads, copyrighted stock or external news.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from io import StringIO

CSV_SAMPLE = (
    "member_id,joined_on,status\n"
    "00127,2026-11-01,active\n"
    "00128,2026-11-02,paused\n"
    "00127,2026-11-03,active\n"
    "00129,11/04/26,active\n"
)
EXPECTED_COLUMNS = ("member_id", "joined_on", "status")


@dataclass(frozen=True)
class Scene:
    title: str
    narration: str
    mode: str
    focus_row: int = -1


@dataclass(frozen=True)
class ExampleEpisode:
    episode_id: str
    kind: str
    voice: str
    theme: str
    scenes: tuple[Scene, ...]


def inspect_example_csv(source: str = CSV_SAMPLE) -> dict:
    """Actually execute the example; never invent graphic table outcomes."""
    reader = csv.DictReader(StringIO(source), restkey="_extra")
    if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
        raise ValueError("Unexpected CSV header")
    rows = list(reader)
    if len(rows) != 4 or any(set(x) != set(EXPECTED_COLUMNS) for x in rows):
        raise ValueError("Benchmark fixture must contain exactly four consistent rows")
    seen = {}
    duplicates, invalid_dates = [], []
    for index, row in enumerate(rows, 1):
        member_id = row["member_id"]
        if not member_id.isascii() or not member_id.isdigit() or len(member_id) != 5:
            raise ValueError("Expected exactly five ASCII digits in synthetic member ID")
        if member_id in seen:
            duplicates.append({"member_id": member_id, "first_row": seen[member_id],
                               "conflicting_row": index,
                               "status_changed": rows[seen[member_id] - 1]["status"] != row["status"],
                               "date_changed": rows[seen[member_id] - 1]["joined_on"] != row["joined_on"]})
        else:
            seen[member_id] = index
        try:
            date.fromisoformat(row["joined_on"])
        except ValueError:
            invalid_dates.append({"row": index, "raw_value": row["joined_on"]})
    if (len(duplicates),len(invalid_dates)) != (1,1):
        raise ValueError("Demo changed; require fresh script review before rendering")
    if duplicates[0]["member_id"] != "00127" or invalid_dates[0]["raw_value"] != "11/04/26":
        raise ValueError("Expected synthetic demonstration changed")
    return {"rows": rows, "row_count": len(rows), "ids_preserved": [x["member_id"] for x in rows],
            "duplicate_ids": duplicates, "invalid_iso_dates": invalid_dates,
            "int_conversion_example": {"raw": "00127", "numeric": int("00127")},
            "potential_review_rows": sorted({duplicates[0]["conflicting_row"],invalid_dates[0]["row"]}),
            "review_before_export": True}


SHORT_AM = ExampleEpisode(
    episode_id="benchmark_20261104_short_am",kind="short",voice="af_heart",
    theme="Keep identifiers as text",
    scenes=(
        Scene("Your ID is not a quantity",
              "Here is a sample member I D: zero zero one two seven. Those two leading zeroes belong to the identifier.", "identity",0),
        Scene("Look at the source CSV",
              "The original C S V really contains zero zero one two seven, not just one hundred and twenty seven.", "raw",0),
        Scene("A risky conversion",
              "If you convert that value to an integer, Python returns one two seven. The original label is different.", "cast",0),
        Scene("Preserve the label",
              "Read the column as text when the digits are identifiers instead of numbers you need to calculate with.", "text",0),
        Scene("Run a real check",
              "Our little C S V reader returns a string containing all five characters. The source and the result agree.", "inspect",0),
        Scene("Test before importing",
              "Compare the first few identifiers before and after any transformation. Do not silently change your keys.", "comparison",1),
        Scene("Practical takeaway",
              "Keep identifiers as text, validate their expected length, and keep the original file for a reversible workflow.", "report"),
    )
)

SHORT_PM = ExampleEpisode(
    episode_id="benchmark_20261104_short_pm",kind="short",voice="bf_emma",
    theme="Review duplicate IDs safely",
    scenes=(
        Scene("Same ID, different row",
              "This sample has two rows with the same member I D. That is a warning, not automatically permission to delete one.", "duplicates",2),
        Scene("Inspect both records",
              "One row joined on November first. The second uses November third. They share an I D, but not the same date.", "raw",2),
        Scene("Compare the fields",
              "When two records disagree, compare the fields that matter. A simple remove duplicates command may hide a conflict.", "comparison",2),
        Scene("Flag, don't destroy",
              "Our check identifies the repeated identifier, keeps both rows, and adds the conflicting row to a review list.", "inspect",2),
        Scene("Separate validation",
              "The last row also uses a non standard date format for this demo. That is a different quality problem.", "dates",3),
        Scene("Review and decide",
              "Fix those issues with an explicit rule and an audit trail. Save the unchanged original for reference.", "report"),
        Scene("Quick takeaway",
              "Treat duplicate identifiers as a review task, not as a shortcut to deleting valuable information.", "workflow"),
    )
)

LONG = ExampleEpisode(
    episode_id="benchmark_20261104_long",kind="long",voice="am_michael",
    theme="CSV quality walkthrough: inspect, preserve, validate",
    scenes=(
        Scene("One small file, three useful checks",
              "In this worked example, we will take a tiny membership C S V file and validate it before importing. The goal is not to clean blindly. It is to preserve meaning, find inconsistencies, and produce a reviewable report.", "workflow"),
        Scene("Start with the raw rows",
              "The sample has four records. Each row contains a member identifier, a joining date, and a status. The rows are synthetic. Notice the identifiers begin with zeroes, and notice that one identifier appears in two different rows.", "raw",0),
        Scene("Read without rewriting values",
              "Python's standard C S V reader loads each field as text. That matters here, because our identifiers are labels. Converting the identifier to an integer would strip the leading zeroes and change the label.", "text",0),
        Scene("Prove the conversion problem",
              "For a quick demonstration, converting the text zero zero one two seven to an integer gives one two seven. Both contain the same mathematical quantity, but they are not the same identifier string. Preserve the original text.", "cast",0),
        Scene("Check the header contract",
              "Before inspecting rows, our demo confirms that three expected column names are present, in order. A different header should stop this example rather than letting a later calculation use the wrong field.", "headers"),
        Scene("Validate the identifier shape",
              "The sample rule expects exactly five A S C I I digits per identifier. That is a business rule for this invented data, not a universal rule. We apply it consistently while keeping each original value unchanged.", "identity",1),
        Scene("Detect repeating keys",
              "Next, we scan the member I D column and record the first occurrence of each key. When the same identifier appears again, we flag the later row rather than removing either record.", "duplicates",2),
        Scene("Look at the conflicting values",
              "The identifier zero zero one two seven appears in rows one and three of our data. The joining dates differ. A human or a documented business rule must decide whether these are updates or genuinely conflicting records.", "comparison",2),
        Scene("Validate ISO-format dates",
              "Now inspect the joining dates. For this example, our accepted representation is year, month, then day. Python's date parsing confirms three sample rows and reports one value that does not fit that particular rule.", "dates",3),
        Scene("Keep the rejected original",
              "The unmatched value is eleven slash zero four slash twenty six. Our check does not assume which day or month the writer intended. We retain the original and request clarification instead of guessing.", "raw",3),
        Scene("Build a transparent exception report",
              "The program produces an exception list. One repeated identifier is detected, and one row has an unexpected date format. An exception is a question for review, not permission to silently erase the data.", "report"),
        Scene("Separate normal from suspicious",
              "Our four original rows remain available. We mark rows needing review and leave the remaining rows untouched. It is safer to create a reviewed output later than to overwrite the only copy now.", "inspect",2),
        Scene("Document the rules and owner",
              "A useful data check explains which rule was applied, which row triggered it, the raw source value, and who must decide the correction. Without that trail, automated cleanup can become difficult to reverse.", "workflow"),
        Scene("Recap the three checkpoints",
              "The complete workflow is simple. Keep identifiers as text, identify repeated keys, and validate dates against an explicit contract. After review, write a new output file and retain the source for verification.", "summary"),
    )
)

EPISODES = (SHORT_AM, LONG, SHORT_PM)
ALLOWED_MODES = frozenset({
    "identity","raw","cast","text","inspect","comparison","report",
    "duplicates","dates","headers","workflow","summary",
})


def validate_fixture() -> dict:
    report = inspect_example_csv()
    if len(EPISODES) != 3 or [x.kind for x in EPISODES] != ["short","long","short"]:
        raise ValueError("Must contain exactly two distinct Shorts and one long")
    if len({x.voice for x in EPISODES}) != 3 or len({x.theme for x in EPISODES}) != 3:
        raise ValueError("All three voice assignments and topics must be distinct")
    for episode in EPISODES:
        if not 6 <= len(episode.scenes) <= 20:
            raise ValueError("Insufficient scenes")
        words = 0
        for scene in episode.scenes:
            if scene.mode not in ALLOWED_MODES or not 8 <= len(scene.title) <= 74:
                raise ValueError("Invalid scene label/mode")
            if not 60 <= len(scene.narration) <= 450:
                raise ValueError("Insufficient or excessive spoken content")
            words += len(scene.narration.split())
        minimum, maximum = (85,165) if episode.kind == "short" else (270,650)
        if not minimum <= words <= maximum:
            raise ValueError(f"Benchmark narration length invalid for {episode.episode_id}: {words}")
    return report
