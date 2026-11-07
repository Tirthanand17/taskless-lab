"""B4h2: 42 original case-specific three-step infographic diagrams.

All text is authored synthetic education, NEVER news headlines, article
passages, licensed data, real benchmarks or inferred source facts.
This module is Pillow-free so the no-media safety gate can validate labels.
"""
from __future__ import annotations

from autopilot.nonfactual_narration_rehearsal import CASEBOOK

# Every entry is exactly three short, original visible educational labels.
# The opening/source/rights cards still carry their prior editorial meaning.
CASE_STEPS = {
    "Wrong task owner": [
        "TASK",
        "ROUTE",
        "OWNER"
    ],
    "Double booking": [
        "SLOT",
        "CONFLICT",
        "CHECK"
    ],
    "Incomplete checklist": [
        "LIST",
        "MISSING",
        "SIGNOFF"
    ],
    "Ambiguous message": [
        "NOTE",
        "AMBIG",
        "ASK"
    ],
    "Approval chain": [
        "REQUEST",
        "APPROVE",
        "SEND"
    ],
    "Wrong language": [
        "TEXT",
        "LABEL",
        "VERIFY"
    ],
    "Late handoff": [
        "SHIFT",
        "RECEIPT",
        "ACK"
    ],
    "Mixed-up sentiment": [
        "TEXT",
        "GUESS",
        "REVIEW"
    ],
    "Missing training label": [
        "ROW",
        "NO TAG",
        "CHECK"
    ],
    "Rare category": [
        "COMMON",
        "RARE",
        "REVIEW"
    ],
    "Conflicting instructions": [
        "RULE A",
        "RULE B",
        "PRIORITY"
    ],
    "Overconfident answer": [
        "INPUT",
        "GUESS",
        "ABSTAIN"
    ],
    "Wrong evaluation split": [
        "TRAIN",
        "COPY",
        "HOLDOUT"
    ],
    "Broken input format": [
        "FIELD",
        "MISSING",
        "REFUSE"
    ],
    "Duplicate row": [
        "ROW",
        "DUP ROW",
        "REVIEW"
    ],
    "Missing age": [
        "CELL",
        "EMPTY",
        "NOTE"
    ],
    "Inconsistent units": [
        "COUNT",
        "UNITS",
        "COMPARE"
    ],
    "Date formatting": [
        "DATE",
        "FORMAT",
        "PARSE"
    ],
    "Category typo": [
        "LABEL",
        "TYPO",
        "REVIEW"
    ],
    "Outlier check": [
        "VALUE",
        "FLAG",
        "INSPECT"
    ],
    "Join mismatch": [
        "KEY",
        "JOIN",
        "VERIFY"
    ],
    "Guest document": [
        "GUEST",
        "REQUEST",
        "DENY"
    ],
    "Expired session": [
        "SESSION",
        "EXPIRE",
        "SIGN IN"
    ],
    "Wrong group": [
        "USER",
        "ROLE",
        "SCOPE"
    ],
    "Broad permission": [
        "ASK",
        "SCOPE",
        "REDUCE"
    ],
    "Public link": [
        "PRIVATE",
        "PUBLIC",
        "CONFIRM"
    ],
    "Role inheritance": [
        "READER",
        "INHERIT",
        "PREVIEW"
    ],
    "Lost device": [
        "DEVICE",
        "SESSION",
        "REVOKE"
    ],
    "Wrong sort order": [
        "INPUT",
        "SORT",
        "EXPECT"
    ],
    "Double-click bug": [
        "CLICK",
        "RETRY",
        "DEDUPE"
    ],
    "Empty form": [
        "FORM",
        "EMPTY",
        "BLOCK"
    ],
    "Undo failure": [
        "EDIT",
        "UNDO",
        "CHECK"
    ],
    "Wrong filter": [
        "QUERY",
        "FILTER",
        "MATCH"
    ],
    "Slow state": [
        "LOAD",
        "TIMEOUT",
        "RETRY"
    ],
    "Stale cache": [
        "UPDATE",
        "CACHE",
        "REFRESH"
    ],
    "Unfair comparison": [
        "TIME A",
        "TIME B",
        "MATCH"
    ],
    "Changing two things": [
        "LIGHT",
        "TIME",
        "ISOLATE"
    ],
    "Missing baseline": [
        "BEFORE",
        "AFTER",
        "COMPARE"
    ],
    "Small sample": [
        "ONE",
        "REPEAT",
        "UNCERT"
    ],
    "Confounded order": [
        "FIRST",
        "SECOND",
        "SWAP"
    ],
    "Unclear success": [
        "RULE",
        "TEST",
        "PASS"
    ],
    "Hidden exception": [
        "CASE",
        "FAIL",
        "LOG"
    ]
}
CASE_APPLICATION_SCENES = frozenset({
    "HOOK_QUESTION","DEMONSTRATION","VERIFY_AND_LIMIT","MECHANISM",
    "BASELINE","EXAMPLE_1","EXAMPLE_2","COUNTEREXAMPLE",
    "NEXT_VIEWER_ACTION",
})
GENERIC_SAFETY_SCENES = frozenset({"SOURCE_SCOPE","FACT_AND_RIGHTS_GATE"})
STEP_HINTS = ("START","RISK","CHECK")


class CaseDiagramRefused(ValueError):
    """Unknown source-independent case or malformed diagram contract."""


def _validate_hand_authored_labels() -> None:
    known={row[0] for theme in CASEBOOK.values() for row in theme}
    if len(known)!=42 or set(CASE_STEPS)!=known:
        raise CaseDiagramRefused("Case diagram labels not aligned to source stories")
    for key,items in CASE_STEPS.items():
        if (type(key) is not str or type(items) is not list
            or len(items)!=3 or len(set(items))!=3
            or any(type(label) is not str or
                   not 2<=len(label)<=8 or
                   any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ " for ch in label)
                   or label.strip()!=label
                   for label in items)):
            raise CaseDiagramRefused("Unsafe or unreadable authored diagram words")


_validate_hand_authored_labels()


def diagram_words_for_case(title:object,scene_id:object,defaults:object)->tuple:
    """Source-only labels replace generic cards only in example beats.

    Preserve the two research/permission gates exactly as reviewed.
    A named fictional case is an *illustration*, never a fact or release.
    """
    if (type(scene_id) is not str
        or scene_id not in CASE_APPLICATION_SCENES|GENERIC_SAFETY_SCENES
        or type(defaults) is not tuple or len(defaults)!=3):
        raise CaseDiagramRefused("Unknown educational storyboard grammar")
    if scene_id in GENERIC_SAFETY_SCENES:
        return defaults
    if type(title) is not str or title not in CASE_STEPS:
        raise CaseDiagramRefused("Untrusted or missing original case title")
    return tuple((label,hint) for label,hint in zip(CASE_STEPS[title],STEP_HINTS))
