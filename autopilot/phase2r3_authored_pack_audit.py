"""Read the ACTUALLY AUTHORED CSV three-video text pack and run Phase2R3 checks.

This imports a fixed repository Markdown file, not an external document.
All Phase2 research, fact-review and localization objects created here are
EXPLICIT MOCK SCAFFOLDS for structural tests; their check times/role names
must never be mistaken for real retrieval, human approval or source licensing.
No HTTP, media generation, accounts, paid services, uploads or publishing.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from .agent_org import WorkflowError
from .phase2_pipeline import (
    CitationRecord, CreativeScript, FactReview, LocalizedDraft,
    ResearchPackage, SupportedClaim, digest,
)
from .phase2r3_bilingual_scripts import (
    SpokenBeat, VideoTextDraft, review_three_video_text_drafts,
)
from .examples.flowminute_csv_demo import demonstrate_csv_total

SOURCE = Path(__file__).parent / "research_briefs" / "2026-10-17_csv_bilingual_one_day_scripts_DRAFT.md"
HEADERS = ("## SHORT 1", "## SHORT 2", "## LONG VIDEO")
TIME = re.compile(r"^\| (\d\d):(\d\d)–(\d\d):(\d\d) \| (.+?) \| (.+?) \|$", re.M)
LABEL = "FICTIONAL SAMPLE DATA"
SECTIONS = (
    ("short", "hi", "csv_tutorial_short_hi", "narrator_hindi_a", 42, 4),
    ("short", "en", "csv_tutorial_short_en", "narrator_english_b", 42, 4),
    ("long", "hi", "csv_tutorial_long_hi", "narrator_hindi_long_c", 432, 24),
)


def _seconds(mm: str, ss: str) -> int:
    minute,second=int(mm),int(ss)
    if not 0 <= second < 60:
        raise WorkflowError("Invalid authored scene time")
    return 60*minute+second


def _sections(markdown: str) -> list[str]:
    if not isinstance(markdown,str) or not 1000 <= len(markdown) <= 50000:
        raise WorkflowError("Bounded actual source Markdown required")
    if any(markdown.count(header)!=1 for header in HEADERS):
        raise WorkflowError("Exactly three authored video sections required")
    points=[markdown.index(marker) for marker in HEADERS]
    if points != sorted(points):
        raise WorkflowError("Authored Short/long video section order invalid")
    if LABEL not in markdown or "ILLUSTRATIVE SIMULATION" not in markdown:
        raise WorkflowError("Simulation and fictional dataset labels are required")
    if "UNREVIEWED WRITING" not in markdown:
        raise WorkflowError("Authored content must disclose the unreviewed status")
    return [markdown[points[i]:points[i+1] if i<2 else len(markdown)] for i in range(3)]


def _mock_phase2_objects(episode: str, language: str,
                         utterances: tuple[str,...],
                         *, now: datetime) -> tuple:
    """Only satisfy typed referential-integrity contract in an offline test.

    The citation.checked_at_utc is a SYNTHETIC scaffolding timestamp, NOT an
    observed HTTP/source fetch. The FactReview attestation is also synthetic.
    """
    instant=now.astimezone(timezone.utc).isoformat()
    research=ResearchPackage(
        episode_id=episode,
        topic="Learn safe Python CSV reading and arithmetic with fictional data",
        viewer_problem="New Python learners want to understand CSV columns with no private data exposure",
        demonstration="Write three synthetic CSV rows in memory, use DictReader and add example totals",
        sources=(
            CitationRecord("src_python_docs","https://docs.python.org/3/library/csv.html",
                           "official",instant,"synthetic_scaffold_not_real_review"),
            CitationRecord("src_independent_csv","https://realpython.com/python-csv/",
                           "independent",instant,"synthetic_scaffold_not_real_review"),
        ),
        claims=(SupportedClaim("c_csv_reader",
            "Use Python csv DictReader and synthetic rows to understand column totals",
            ("src_python_docs","src_independent_csv")),),
    )
    review=FactReview(episode, digest(research), "quality.fact_reviewer",
                      ("c_csv_reader",), "ATTESTED_FOR_DRAFT",
                      "SYNTHETIC_ROLE_RECORD_NOT_AN_INDEPENDENT_FACT_REVIEW")
    script=CreativeScript(
        episode,digest(research),digest(review),
        "Python CSV learning exercise with imaginary data",
        "Understand a sample CSV using Python's standard-library reader",
        ("Create a small fictional CSV with three product rows",
         "Read named columns and calculate a fictional sample total"),
        "Learn one useful CSV workflow with no real purchase or private information",
        ("c_csv_reader",),research.demonstration,
    )
    spoken=" ".join(utterances)
    localized=LocalizedDraft(
        episode,digest(script),language,spoken,
        tuple(utterances[:2]),
        "Draft terminology: CSV, Python, DictReader, synthetic, example totals",
        "language.hindi_editor" if language=="hi" else "language.english_editor",
    )
    return research, review, script, localized


def audit_authored_csv_pack(*, now:datetime|None=None, markdown:str|None=None) -> dict[str,Any]:
    """Check 3 actual authored script sections; output an unprivileged summary."""
    if now is None:
        now=datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise WorkflowError("Verifier clock requires UTC-aware time")
    raw=SOURCE.read_text(encoding="utf-8") if markdown is None else markdown
    sections=_sections(raw)
    entries=[]
    for section,(kind,language,episode,narrator,duration,count) in zip(sections,SECTIONS):
        scenes=TIME.findall(section)
        if len(scenes)!=count:
            raise WorkflowError("Actual authored scene count does not match declared video format")
        beats=[]
        previous=0
        for i,(a,b,c,d,spoken,visual) in enumerate(scenes):
            start,end=_seconds(a,b),_seconds(c,d)
            if start != previous or end <= start:
                raise WorkflowError("Actual written scene timing is not contiguous")
            previous=end
            # One mandatory labeled simulation per video; other scenes are
            # illustrative explanations, not forged live UI/screen recordings.
            demo=(i==1)
            beats.append(SpokenBeat(
                start_ms=start*1000,end_ms=end*1000,
                spoken_text=spoken,subtitle_text=spoken,
                overlay="ILLUSTRATIVE SIMULATION — " + LABEL if demo
                        else "ORIGINAL EDUCATIONAL CONCEPT",
                visual_mode="labeled_simulation" if demo else "explanatory_diagram",
                claim_ids=("c_csv_reader",) if i>0 else (),
                simulation_label_visible=demo,
            ))
        if previous!=duration:
            raise WorkflowError("Authored video runtime differs from published text draft")
        research,review,script,localized=_mock_phase2_objects(
            episode,language,tuple(b.spoken_text for b in beats),now=now)
        plan=VideoTextDraft(
            episode_id=episode,kind=kind,language=language,
            research_sha256=digest(research),script_sha256=digest(script),
            localized_sha256=digest(localized),
            narrator_id=narrator,
            narrator_direction="Original natural educational narrator direction; no human voice or licensed audio recorded.",
            beats=tuple(beats),
        )
        entries.append((plan,research,review,script,localized))
    result=review_three_video_text_drafts(entries,now=now)
    executable=demonstrate_csv_total()
    if executable["total"]!=58 or not executable["dataset_is_fictional"]:
        raise WorkflowError("Actual executable CSV demo disagrees with editorial data")
    return {
        **result,
        "source":"FIXED_REPOSITORY_AUTHORED_MARKDOWN_DRAFT",
        "live_source_capture_verified":False,
        "fact_review_synthetic_scaffolding":True,
        "human_language_review_synthetic_scaffolding":True,
        "narration_subtitles_equal_only_as_written_text":True,
        "original_example_executed_locally":True,
        "fictional_example_total":executable["total"],
        "actual_narration_recorded":False,
        "youtube_published":False,
    }


if __name__=="__main__":
    import json
    print(json.dumps(audit_authored_csv_pack(),sort_keys=True,
                     separators=(",",":"),ensure_ascii=True))
