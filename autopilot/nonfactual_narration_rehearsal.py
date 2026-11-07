"""B4d9: three ORIGINAL non-factual narration rehearsals with precise scene timing.

These are actually written original voiceover rehearsal TEXTS, NOT an AI/model
call and NOT a fact-checked story about an unverified current headline.

Only source-independent, synthetic educational demonstrations appear in the
spoken text. Never narrate RSS titles, scraped excerpts, claims or proprietary
figure content. Factual editorial, rights, final-watch and publishing stay OFF.
The scripts exist only ephemerally on the Github runner and are deleted.
"""
from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re

from autopilot.ephemeral_claim_review_docket import (
    DOCKET_STATUS,build_claim_review_docket,ClaimDocketRefused,
)
from autopilot.source_locked_script_briefs import ORIGINAL_VISUALS

STATUS = "B4D9_EPISODE_LOCKED_ORIGINAL_NONFACTUAL_NARRATION_REHEARSAL_NO_RELEASE"
MAX_JSON_BYTES = 120_000
FPS = 30
SHORT_FRAMES = 58 * FPS
LONG_FRAMES = 240 * FPS
VISUAL_STYLE = (
    "Original labeled 2D diagrams and synthetic sample tables; no "
    "third-party screenshots, paper charts, repeating radial spinner or loop."
)
SOURCE_RIGHTS = (
    "Publisher article passage cannot be narrated, quoted, reproduced, "
    "shown, or paraphrased as factual news before independent rights "
    "and claim-by-claim reviews."
)
SAFE_SFX = ("soft-enter","single-click","subtle-change","gentle-end")
SHOT_MOTIONS = ("one-time-slide","single-build","one-time-compare","hold-with-label")

# Every voiced assertion below describes a *made-up exercise*. None is
# obtained from an unverified publisher headline, HTML or quote.
THEMES = {
    "agents": {
        "label":"Delegation",
        "thing":"a pretend assistant sorting three sample tasks",
        "input":"a colored sticky note with a sample task and a made-up priority",
        "comparison":"one task goes directly to a human, while another is routed through an imaginary helper",
        "measure":"which step required confirmation and where a mistaken handoff could occur",
        "failure":"the pretend helper sends a task to the wrong person",
        "next":"a visible human approval checkpoint before any handoff",
        "visual":"hand-drawn branching task cards",
    },
    "models": {
        "label":"Model comparisons",
        "thing":"two imaginary text classifiers sorting made-up support messages",
        "input":"a set of synthetic messages whose labels were written by us",
        "comparison":"a simple baseline rule and a fictional model guess displayed side by side",
        "measure":"the disagreement count, with an empty results box until you perform the test",
        "failure":"a fictional classifier mistakes a complaint for praise",
        "next":"a fixed evaluation rubric and a second person checking the labels",
        "visual":"original baseline-versus-example table",
    },
    "data": {
        "label":"Data quality",
        "thing":"a pretend spreadsheet containing six invented rows",
        "input":"a small made-up table with blank cells and repeated labels",
        "comparison":"a visibly marked raw table and a copy with a proposed cleaning rule",
        "measure":"which rows changed, why they changed, and whether the rule altered the intended meaning",
        "failure":"a missing value is silently replaced by an invented answer",
        "next":"a written change log and a side-by-side original table",
        "visual":"synthetic input-and-output grid",
    },
    "security": {
        "label":"Permissions",
        "thing":"a fictional app letting a sample user open a pretend document",
        "input":"two illustrated request cards, one approved and one missing permission",
        "comparison":"a request that asks first and a request that skips an explicit checkpoint",
        "measure":"whether each request was allowed by our invented access rule",
        "failure":"the imaginary app opens a document without asking permission",
        "next":"a clear permission decision before data can appear on screen",
        "visual":"original request-and-decision flowchart",
    },
    "developer_tools": {
        "label":"Testing a feature",
        "thing":"a made-up app button that sorts fictional color tags",
        "input":"a tiny sample test with three labeled color cards",
        "comparison":"the expected order written before the test and an observed order left blank",
        "measure":"whether the imagined output matches our own sample test case",
        "failure":"the example button changes a card that was not selected",
        "next":"a reversible change and a clearly labeled test failure",
        "visual":"simple original test-case cards",
    },
    "general": {
        "label":"Testing a claim",
        "thing":"a hypothetical experiment comparing two made-up study methods",
        "input":"a fictional set of sample steps and a prewritten baseline",
        "comparison":"two clearly labeled imaginary choices tested by the same rule",
        "measure":"the stated test method rather than a number borrowed from a headline",
        "failure":"the imagined test compares two cases with different starting conditions",
        "next":"a baseline that both examples must share before comparison",
        "visual":"original illustrated experimental timeline",
    },
}

# B4h0: hand-authored fictional case studies, never untrusted source text.
# A single family must NOT yield the identical narrated story every day.
# These 7 distinct cases per family are combined with three editorial
# openings; the finite repertoire is disclosed, not falsely sold as
# limitless human originality or a verified real news explanation.
CASEBOOK = {
    "agents": [
        [
            "Wrong task owner",
            "a pretend assistant routing a customer note between two imaginary teammates",
            "a purple request card with a fake owner field",
            "a direct human assignment versus an automatic assignment that might pick the wrong inbox",
            "the invented assistant sends a request to the wrong sample inbox",
            "a visible owner-confirmation card before the handoff"
        ],
        [
            "Double booking",
            "an imaginary scheduling helper placing two sample meetings",
            "two handmade calendar cards sharing a fictional time slot",
            "a calendar conflict warning versus a silent automatic booking",
            "the imaginary helper books both sample meetings at once",
            "a check for overlapping time slots before confirming"
        ],
        [
            "Incomplete checklist",
            "a mock helper preparing a pretend equipment checklist",
            "three fictional checklist cards, including one blank field",
            "a fast unchecked checklist versus a slower reviewed checklist",
            "the fictional helper marks a missing item complete",
            "a required-fields check and a final human signoff"
        ],
        [
            "Ambiguous message",
            "an invented assistant sorting a vague sample team message",
            "a synthetic note that can mean either urgent or routine",
            "one interpretation chosen instantly versus asking one clarifying question",
            "the pretend assistant treats an uncertain note as a firm instruction",
            "a clarification checkpoint for ambiguous sample messages"
        ],
        [
            "Approval chain",
            "a simulated assistant forwarding a made-up purchase request",
            "a fake request card with an empty approval square",
            "direct forwarding versus routing through a clearly marked human approval gate",
            "the imaginary helper forwards a request with no signature",
            "a stop-and-confirm gate before any pretend purchase"
        ],
        [
            "Wrong language",
            "a fictional helper matching invented messages to language labels",
            "three sample cards using made-up language tags",
            "auto-routing by a guessed tag versus asking the author to confirm",
            "the helper files the deliberately mislabeled card in the wrong queue",
            "a visible language-label confirmation before routing"
        ],
        [
            "Late handoff",
            "a pretend assistant passing a fictional task between two time slots",
            "a paper timeline with two invented shift labels",
            "a handoff with a receipt versus a handoff with no acknowledgment",
            "the made-up helper loses a task between example shifts",
            "a receipt card that the next pretend teammate must acknowledge"
        ]
    ],
    "models": [
        [
            "Mixed-up sentiment",
            "two imaginary text classifiers ranking three invented comments",
            "three original comment cards with handwritten pretend labels",
            "a keyword guess versus a labeled reference answer",
            "the pretend classifier calls a complaint a compliment",
            "a visible confusion table checked against the sample labels"
        ],
        [
            "Missing training label",
            "a fictional classifier predicting a tag for an invented message",
            "a small made-up dataset with one deliberately blank tag",
            "discarding uncertain rows versus assigning a guessed label",
            "the hypothetical model treats an unlabeled sample as a proven example",
            "a missing-label warning before any scoring"
        ],
        [
            "Rare category",
            "two pretend models sorting common and uncommon fake ticket types",
            "four invented tickets, one from a tiny minority category",
            "overall agreement versus separate checks for the rare category",
            "a made-up model ignores the uncommon sample tag",
            "a category-by-category error tally with no invented accuracy claims"
        ],
        [
            "Conflicting instructions",
            "a pretend text model following contradictory invented sorting rules",
            "two fake instruction cards that disagree about the same message",
            "the old rule versus the revised rule on one example",
            "the fictional model silently follows the wrong rule",
            "an explicit instruction-priority test using one fixed sample"
        ],
        [
            "Overconfident answer",
            "a hypothetical classifier giving a confident label on nonsense text",
            "a made-up sentence with no meaningful category",
            "a forced prediction versus an explicit cannot-decide option",
            "the pretend model shows certainty about an unclassifiable sample",
            "an abstain option and a reviewer for unclear examples"
        ],
        [
            "Wrong evaluation split",
            "two fictional models tested on copied sample rows",
            "an invented table containing the same row twice",
            "retesting repeated examples versus a separated toy holdout set",
            "the example evaluation counts the same practice row twice",
            "a visible duplicate-row check before the mock comparison"
        ],
        [
            "Broken input format",
            "an imaginary classifier reading handmade message fields",
            "a synthetic message missing its subject line",
            "a strict input check versus silently accepting an incomplete message",
            "the model gives a pretend label without the required input",
            "a simple input-schema checkpoint before any prediction"
        ]
    ],
    "data": [
        [
            "Duplicate row",
            "a pretend six-row spreadsheet with repeated identifiers",
            "a small handmade table where one fictional row appears twice",
            "counting all entries versus counting unique sample identifiers",
            "a repeated sample row is mistaken for a new record",
            "a duplicate-key inspection before updating the toy table"
        ],
        [
            "Missing age",
            "an invented worksheet with one missing age entry",
            "five imaginary records, including an intentionally empty age cell",
            "leaving the gap explicit versus filling it with a guess",
            "an empty sample value is replaced with a plausible but invented number",
            "a missing-value note and an audit trail instead of guessing"
        ],
        [
            "Inconsistent units",
            "a synthetic inventory table mixing counts and weights",
            "three pretend rows with two deliberately different unit labels",
            "combining unlike units versus converting only after checking definitions",
            "the imaginary spreadsheet adds kilograms to item counts",
            "a unit-validation column alongside the original sample values"
        ],
        [
            "Date formatting",
            "a mock attendance sheet containing ambiguous sample dates",
            "four made-up dates written in two incompatible styles",
            "parsing dates as written versus asking which calendar format applies",
            "an ambiguous invented date shifts into the wrong month",
            "an explicit date-format decision before sorting records"
        ],
        [
            "Category typo",
            "a fictional purchase log with nearly identical sample categories",
            "a small table using blue-tag and blu-tag labels",
            "merging by appearance versus checking the original label definitions",
            "the toy cleanup merges two different categories by mistake",
            "a reviewed lookup table for the permitted labels"
        ],
        [
            "Outlier check",
            "a hypothetical sensor worksheet containing an odd sample value",
            "a synthetic five-reading table with one extreme entry",
            "deleting the surprising row versus investigating the input rule",
            "the fictional analyst removes the example outlier without recording why",
            "a flag-for-review column and the unchanged source row"
        ],
        [
            "Join mismatch",
            "two made-up tables linked by synthetic customer IDs",
            "a tiny pair of grids with a missing matching example ID",
            "joining every row versus matching only validated pretend keys",
            "a sample entry attaches to an unrelated invented customer",
            "a key-matching inspection before combining the toy grids"
        ]
    ],
    "security": [
        [
            "Guest document",
            "a fictional file app deciding if a guest may open a toy report",
            "two handmade guest request cards with different pretend permissions",
            "showing a report immediately versus checking the sample access rule",
            "the imaginary app opens the sample report for an unapproved guest",
            "a visible allow-or-deny decision before displaying any data"
        ],
        [
            "Expired session",
            "a pretend app with a deliberately expired sample access pass",
            "a paper login card and a fictional expiry clock",
            "accepting an old session versus asking for a new simulated sign-in",
            "the example app treats an expired session as still active",
            "an expiry check before processing the fake request"
        ],
        [
            "Wrong group",
            "a mock workspace where two invented teams share a file list",
            "illustrated request cards assigned to different pretend groups",
            "matching a group label versus granting everyone the same access",
            "the sample app exposes the team-one file to a team-two role",
            "a group-scope check before showing the requested card"
        ],
        [
            "Broad permission",
            "a fictional permissions panel asking for more than it needs",
            "a toy photo-reader form requesting unrelated fake contacts permission",
            "granting every request versus accepting only the required sample scope",
            "the imaginary app requests a pretend address book without reason",
            "a least-privilege decision with each permission explained"
        ],
        [
            "Public link",
            "an invented document-share screen with a confusing link toggle",
            "two illustrated sharing cards, private and anyone-with-link",
            "displaying a warning versus silently enabling wide sharing",
            "the pretend app turns a private sample link into a public one",
            "a clear sharing-scope confirmation before saving"
        ],
        [
            "Role inheritance",
            "a sample team app assigning imaginary editor and reader roles",
            "a diagram with two fictional accounts and inherited role arrows",
            "checking effective roles versus trusting the visible label alone",
            "the example reader unexpectedly inherits pretend edit rights",
            "an effective-permissions preview for the example account"
        ],
        [
            "Lost device",
            "a made-up account panel with a simulated missing device",
            "a paper device list showing one invented unknown session",
            "leaving every session active versus reviewing which sessions belong",
            "the fictional account keeps a pretend lost device signed in",
            "a sign-out checkpoint for the unrecognized sample session"
        ]
    ],
    "developer_tools": [
        [
            "Wrong sort order",
            "a toy app sorting four invented color tags",
            "four colored sample labels arranged in a deliberately mixed order",
            "a predetermined expected order versus the button output",
            "the fictional sorting button puts the orange tag before blue unexpectedly",
            "a one-click regression test with a visible expected list"
        ],
        [
            "Double-click bug",
            "a pretend save button that receives two quick sample clicks",
            "a drawn interface with a fake save counter",
            "single-action expected behavior versus a duplicated test action",
            "the invented button creates two example records from one intention",
            "an idempotency check in the toy click test"
        ],
        [
            "Empty form",
            "an imaginary app submitting a blank sample field",
            "a hand-drawn demo form with a required color label",
            "validating the empty input versus accepting it silently",
            "the fake submit action stores an example with no required label",
            "a required-field warning before the pretend submit"
        ],
        [
            "Undo failure",
            "a pretend editor changing two fictional tags",
            "two colored cards and an illustrated undo control",
            "the expected reversible edit versus the irreversible sample behavior",
            "the mock undo function restores only one of two modified cards",
            "an explicit before-and-after undo regression test"
        ],
        [
            "Wrong filter",
            "a fictional dashboard filtering made-up task cards",
            "a toy list with two labels that share a similar prefix",
            "exact matching versus loose substring filtering",
            "the sample filter hides a valid card with a neighboring label",
            "a fixed test for inclusive and exclusive filter examples"
        ],
        [
            "Slow state",
            "a demo web button with an imaginary delayed response",
            "an illustrated progress placeholder and a finished-state card",
            "one-time loading feedback versus a control that appears permanently busy",
            "the pretend button never exits its illustrated loading state",
            "a bounded timeout and a clearly labeled retry state"
        ],
        [
            "Stale cache",
            "a fictional app showing a sample counter that was just changed",
            "two handmade counter panels representing old and new values",
            "showing a cached example versus the latest pretend state",
            "the toy page displays the old counter after the update",
            "a deterministic refresh test with both values visible"
        ]
    ],
    "general": [
        [
            "Unfair comparison",
            "two invented study routines evaluated on unequal pretend sessions",
            "a toy timeline where one method gets twice as much practice",
            "equal-time sample trials versus two mismatched examples",
            "the imaginary comparison credits a method for extra practice time",
            "a matched-duration baseline before comparing imaginary outcomes"
        ],
        [
            "Changing two things",
            "a hypothetical study test where lighting and timing both vary",
            "two handmade session cards with different light and time settings",
            "changing one variable versus changing both at once",
            "the pretend trial cannot tell which of two changes mattered",
            "a one-variable-at-a-time sample plan"
        ],
        [
            "Missing baseline",
            "a fictional reading challenge with no recorded starting point",
            "a paper worksheet containing an empty before column",
            "a result without baseline versus a properly labeled toy starting score",
            "the invented evaluation claims an improvement with no starting value",
            "a blank-but-required baseline slot before the example begins"
        ],
        [
            "Small sample",
            "a make-believe test drawing conclusions from one imagined attempt",
            "a toy result card containing a single trial",
            "one isolated observation versus several planned sample trials",
            "the hypothetical tester calls one pretend result a universal rule",
            "a repeatable trial plan with uncertainty noted"
        ],
        [
            "Confounded order",
            "a pretend memory task always done second in the sample sequence",
            "two fake session cards presented in the same order",
            "fixed order versus swapping the order between imagined trials",
            "the example attributes a practice effect to the wrong activity",
            "a balanced presentation order for the made-up comparison"
        ],
        [
            "Unclear success",
            "a mock experiment using an undefined success label",
            "a fictional checklist with no rule for marking a pass",
            "a vague success word versus a prewritten testable criterion",
            "the invented reviewer changes the meaning of success after the trial",
            "a clear pass-or-fail definition before any demonstration"
        ],
        [
            "Hidden exception",
            "an imaginary routine comparison ignoring a difficult sample case",
            "a handmade result table with one flagged exception row",
            "dropping inconvenient examples versus keeping a visible exception count",
            "the make-believe test quietly hides the failed sample condition",
            "an explicit exception log beside the invented results"
        ]
    ]
}


def _daily_case(family: str, slot: str, day: str) -> tuple[dict, int]:
    if family not in THEMES or slot not in ("short_am","short_pm","long"):
        raise RehearsalRefused("Unknown original creative scene identity")
    try:
        ordinal=date.fromisoformat(day).toordinal()
    except (TypeError,ValueError):
        raise RehearsalRefused("Missing valid daily fictional scene date") from None
    if len(day)!=10 or day!=date.fromordinal(ordinal).isoformat():
        raise RehearsalRefused("Noncanonical daily scene date")
    rows=CASEBOOK[family]
    if len(rows)!=7 or any(len(row)!=6 for row in rows):
        raise RehearsalRefused("Incomplete handcrafted safe fictional casebook")
    offset={"short_am":0,"long":2,"short_pm":4}[slot]
    family_index=sorted(THEMES).index(family)
    selection=(ordinal+offset+family_index)%len(rows)
    opening=(ordinal//len(rows)+offset+family_index)%3
    title,thing,input_,comparison,failure,next_step=rows[selection]
    theme={**THEMES[family], "story_name":title, "thing":thing,
           "input":input_, "comparison":comparison, "failure":failure,
           "next":next_step}
    return theme,opening


def _fresh_opening(slot: str, data: dict, style:int) -> list[str]:
    paragraphs=_paragraphs(slot,data)
    if style==0:
        return paragraphs
    thing=data["thing"]
    if style==1:
        if slot=="short_am":
            paragraphs[0]=(f"Before we trust {thing}, look for the invisible mistake. "
                "This is a fictional demonstration, not a verified claim about a real system.")
        elif slot=="short_pm":
            paragraphs[0]=(f"What would change your mind about {thing}? "
                "A fictional demonstration can be clear and still fail as evidence about the real world.")
        else:
            paragraphs[0]=(f"Here is an uncomfortable question: when does {thing} "
                "appear to work while its own test is incomplete? In this fictional "
                "lesson every object and result is imaginary. We will show the "
                "mechanism, challenge its assumptions, and leave all real-news "
                "claims unapproved.")
    elif style==2:
        if slot=="short_am":
            paragraphs[0]=(f"Freeze the next decision in {thing}. "
                "Can you identify the weak link before it happens? "
                "Our scenario is fictional and no actual product has been tested.")
        elif slot=="short_pm":
            paragraphs[0]=(f"Imagine a convincing screenshot of {thing}. "
                "Which part is merely drawn, and which part was ever measured? "
                "This fictional lesson makes the distinction visible.")
        else:
            paragraphs[0]=(f"Start with a surprising failure in {thing}, then "
                "work backward to the decision that allowed it. This is a "
                "fictional controlled example with imaginary inputs, not a "
                "verified story from a real company. We will compare paths, "
                "examine missing evidence, and keep the conclusions conditional.")
    else:
        raise RehearsalRefused("Unknown original educational hook style")
    return paragraphs


# The narration is truly written, including 4 original sections per Short
# and 9 per long. It deliberately cannot state a vendor's new factual news.
def _paragraphs(slot: str, data: dict) -> list[str]:
    thing,input_,comparison,measure,failure,next_step = (
        data[k] for k in ("thing","input","comparison","measure","failure","next"))
    if slot == "short_am":
        return [
            f"Can you spot the weakest step in {thing}? "
            "We will test the idea with a fictional example, not a claim about a real product.",
            f"Start with {input_}. Draw the expected steps before anything moves. "
            "That way, a surprising result has a clear starting point for comparison.",
            f"Now compare two paths: {comparison}. Watch closely for {measure}. "
            "The boxes are examples, not measured results; we have not tested a live system.",
            f"What if {failure}? Do not hide that possibility behind flashy animation. "
            f"Try {next_step}. Save this mini test and check any real-world claim against its original source.",
        ]
    if slot == "short_pm":
        return [
            f"One picture can make an untested idea look convincing. Imagine {thing}. "
            "Could a neat animation trick us into thinking the example already proved something?",
            f"Set up {input_}. Write down what you expect first, and leave the actual result blank. "
            "This is fictional, not evidence from today's headlines.",
            f"Now picture this mistake: {failure}. Instead of spinning a graphic forever, "
            f"show {comparison}, and pause on the exact point that needs checking.",
            f"The useful next move is {next_step}. Ask what would count as a fair test, "
            f"including {measure}. Treat catchy claims as unverified questions.",
        ]
    if slot == "long":
        return [
            f"Suppose a story sounds too impressive to question. Today we are not endorsing any "
            f"headline. Instead, let us build a small original test around {thing}, "
            "so you can see exactly where a claim could fail. All the sample objects "
            "are fictional, and we will keep real-world conclusions out of the demo.",
            f"Begin by naming the question. Does the imagined workflow behave as intended "
            f"under one transparent rule? We need a baseline before any result. "
            f"Use {input_}. Write the sample inputs on screen and label every field "
            "as synthetic, so nobody mistakes a prop for live research data.",
            f"Next draw the mechanism as a series of distinct steps. First the input, "
            f"then the proposed action, then a decision that can be reviewed. "
            f"Our illustration uses {data['visual']}. Each element appears once and "
            "stays still after its reveal; no endless spinning circles or visual clutter.",
            f"Now choose a control case. Keep the first example unchanged and describe "
            f"the rule it should follow. Beside it, place {comparison}. "
            "This is an exercise in comparing processes, not a report about a "
            "company's actual model, performance, price, scientific result or launch.",
            f"Run a pretend walkthrough slowly. Read each invented input, show the "
            f"decision it would trigger, and highlight the place where a person "
            f"might ask a follow-up question. The quantity we would want to inspect is "
            f"{measure}. We leave the outcome unfilled because no real measurement was taken.",
            f"Here comes a second invented example. Change only one condition and "
            f"repeat the diagram, so the viewer can identify what changed and what "
            "did not. Label the second path as hypothetical. A thoughtful comparison "
            "is more useful than dramatic numbers when the underlying evidence is still missing.",
            f"Now test a failure case: {failure}. Point to the exact checkpoint "
            "that could catch it, and ask what other explanation might fit the same picture. "
            "A short animation can suggest an answer, but it cannot independently "
            "verify a fact. That requires checking the original report and its limits.",
            f"Before calling this a real news explanation, a reviewer would need "
            "the dated source, the specific sentence being claimed, an independent "
            "corroborating record where appropriate, and permission for every outside "
            "visual or quotation. We have deliberately copied none of those passages "
            "into this rehearsal. The honest status today is: research still needs review.",
            f"So take the practice away from the headline. Try {next_step}, "
            "then repeat the miniature example with your own invented values. "
            "Write down your expectation before revealing a result, compare each step, "
            "and explain any uncertainty. Once the evidence is independently checked, "
            "a future final script can discuss the real story without guessing.",
        ]
    raise ValueError("Unsupported creative rehearsal slot")


def _words(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b",value))


def _frames_for(paragraphs: list[str], total: int) -> list[int]:
    # Duration is an actual frame-accurate storyboard target, not measured
    # TTS audio duration. Later voice QA must retime from physical waveforms.
    counts=[_words(p) for p in paragraphs]
    w=sum(counts)
    alloc=[round(total*n/w) for n in counts[:-1]]
    alloc.append(total-sum(alloc))
    if any(n < FPS*6 for n in alloc):
        raise ValueError("Scene too short for readable voice and caption pacing")
    return alloc


def _canonical(value: object) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False).encode("ascii")


class RehearsalRefused(ValueError):
    """A forged claim review, mismatched episode or publishable script fails."""


def build_nonfactual_rehearsals(
    original: object,aligned: object,board: object,scout: object,
    evidence: object,briefs: object,passages: object,docket: object,
) -> dict:
    try:
        expected=build_claim_review_docket(
            original,aligned,board,scout,evidence,briefs,passages)
    except (ClaimDocketRefused,ValueError,TypeError,KeyError):
        raise RehearsalRefused("Could not reconstruct source-locked claim review") from None
    if (type(docket) is not dict or docket != expected
        or docket.get("status") != DOCKET_STATUS
        or docket.get("semantic_claims_verified")!=0
        or docket.get("factual_scripts_generated")!=0
        or docket.get("rights_approvals")!=0
        or docket.get("external_ai_calls")!=0
        or docket.get("youtube_uploads")!=0
        or docket.get("release_authorized") is not False):
        raise RehearsalRefused("Unapproved source-claim docket was changed")
    if (type(briefs) is not dict or type(briefs.get("episodes")) is not list
        or len(briefs["episodes"])!=3 or len(docket["dockets"])!=3):
        raise RehearsalRefused("Missing canonical three-episode structure")
    episodes=[]
    sources=[]
    for idx,(brief,review) in enumerate(zip(briefs["episodes"],docket["dockets"])):
        slot=brief["slot"]
        if (slot not in ("short_am","long","short_pm")
            or review["episode_id"]!=brief["episode_id"]
            or review["research_source_id"]!=brief["source_id"]
            or review["research_evidence_tier"]!=brief["evidence_tier"]):
            raise RehearsalRefused("Claim review misassigned to a video")
        family=(board["slots"][idx]["research_lead"] or {}).get("topic_family","general")
        if family not in THEMES or family not in ORIGINAL_VISUALS:
            raise RehearsalRefused("Unsupported or forged rehearsal family")
        if (brief["factual_script_drafted"] is not False
            or brief["model_permission_granted"] is not False
            or brief["release_authorized"] is not False):
            raise RehearsalRefused("Source brief claimed unearned publication rights")
        source=brief["source_id"]
        if source is not None and source in sources:
            raise RehearsalRefused("Repeated source assigned to distinct videos")
        sources.append(source)
        theme,opening=_daily_case(family,slot,briefs["plan_day_ist"])
        paragraphs=_fresh_opening(slot,theme,opening)
        is_short=brief["format"]=="short"
        total=SHORT_FRAMES if is_short else LONG_FRAMES
        if (len(paragraphs)!=(4 if is_short else 9)
            or len(brief["narrative_structure_not_written_script"])!=len(paragraphs)):
            raise RehearsalRefused("Physical scene count and source outline differ")
        all_words=sum(_words(p) for p in paragraphs)
        if not ((95<=all_words<=155) if is_short else (340<=all_words<=660)):
            raise RehearsalRefused("Original narration rehearsal is outside safe duration range")
        allocation=_frames_for(paragraphs,total)
        if not (85<=all_words*60/(total/FPS)<=165):
            raise RehearsalRefused("Voice pacing inappropriate for a sample rehearsal")
        scenes=[]
        at=0
        for j,(paragraph,frames,outline) in enumerate(zip(
                paragraphs,allocation,brief["narrative_structure_not_written_script"])):
            if any(x in paragraph.lower() for x in ("according to the article",
                  "the study proves","research confirms","the company announced")):
                raise RehearsalRefused("Factual news narration appeared without evidence")
            scenes.append({
                "scene_index":j,
                "scene_id":outline["beat"],
                "start_frame":at,
                "duration_frames":frames,
                "end_frame_exclusive":at+frames,
                "original_voiceover_rehearsal_text":paragraph,
                "word_count":_words(paragraph),
                "original_visual_design": (
                    brief["proposed_original_visuals"][j%3]),
                "motion_policy":SHOT_MOTIONS[j%len(SHOT_MOTIONS)],
                "single_transition_sfx":SAFE_SFX[j%len(SAFE_SFX)],
                "low_background_music_recommendation_only":True,
                "static_safe_area_for_burned_in_captions":True,
                "source_quote_display_allowed":False,
                "story_claims_semantically_verified":False,
                "third_party_source_visual_allowed":False,
            })
            at+=frames
        if at!=total or len(scenes)!=(4 if is_short else 9):
            raise RehearsalRefused("Scene timing does not match target video length")
        raw=theme["label"]+" — "+theme["story_name"]+" — "+slot.replace("_"," ").title()+" synthetic test"
        episodes.append({
            "episode_id":brief["episode_id"], "slot":slot,
            "format":brief["format"],"planned_local_ist":brief["time_ist"],
            "original_working_title_not_news_headline":raw,
            "unverified_source_id":source,
            "unverified_source_full_response_sha256":brief["source_observation_sha256"],
            "observed_evidence_tier":brief["evidence_tier"],
            "claim_review_passages_not_quoted":len(
                review["literal_passage_questions_needing_human_review"]),
            "source_research_brief_sha256":sha256(_canonical(brief)).hexdigest(),
            "source_claim_docket_sha256":sha256(_canonical(review)).hexdigest(),
            "narration_rehearsal_nonfactual":True,
            "voiceover_text_written_for_rehearsal":True,
            "factual_news_narration_written":False,
            "duration_target_seconds":total/FPS,
            "fps":FPS,
            "frame_count":total,
            "canvas_width":1080 if is_short else 1920,
            "canvas_height":1920 if is_short else 1080,
            "visual_style":VISUAL_STYLE,
            "source_rights_block":SOURCE_RIGHTS,
            "estimated_script_words":all_words,
            "estimated_narration_wpm":round(all_words*60/(total/FPS),1),
            "scene_count":len(scenes),
            "scenes":scenes,
            "actual_recorded_voice_exists":False,
            "actual_video_rendered":False,
            "real_factual_script_approved":False,
            "real_rights_cleared":False,
            "independent_claim_review_approved":False,
            "owner_final_watch_approved":False,
            "model_inference_performed":False,
            "youtube_uploaded":False,
            "youtube_scheduled":False,
            "release_authorized":False,
        })
    if len(set(x["original_working_title_not_news_headline"] for x in episodes))!=3:
        raise RehearsalRefused("Three synthetic rehearsal titles must be distinct")
    return_value={
        "status":STATUS,
        "research_day_ist":briefs["plan_day_ist"],
        "planned_video_count":3,
        "original_nonfactual_voiceover_rehearsals_written":3,
        "original_scene_count":sum(x["scene_count"] for x in episodes),
        "shorts_rehearsals_written":2,
        "long_rehearsals_written":1,
        "factual_news_scripts_completed":0,
        "fact_checks_completed":0,
        "source_rights_approvals":0,
        "actual_voice_files_created":0,
        "actual_video_files_created":0,
        "provider_model_calls":0,
        "youtube_uploads":0,
        "youtube_scheduled":0,
        "release_authorized":False,
        "three_episodes":episodes,
    }
    if len(_canonical(return_value))>MAX_JSON_BYTES:
        raise RehearsalRefused("Unbounded rehearsal source/output")
    return return_value


def _read(path: Path) -> object:
    if (not path.is_file() or path.is_symlink()
        or not 2<=path.stat().st_size<=512_000):
        raise RehearsalRefused("Missing or unbounded ephemeral script input")
    try:
        return json.loads(path.read_text("utf8"),
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              RehearsalRefused("Nonfinite script JSON")))
    except (UnicodeError,json.JSONDecodeError):
        raise RehearsalRefused("Malformed private script input") from None


def main() -> None:
    ap=argparse.ArgumentParser(description="Original three-video NONFACTUAL voiceover rehearsal ONLY")
    for name in ("original-plan","aligned-plan","board","scout","evidence",
                 "briefs","passages","docket"):
        ap.add_argument("--"+name,required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    if (args.output.exists() or args.output.is_symlink()
        or args.output.parent.name!="out"
        or not args.output.name.startswith("flowminute-ephemeral-")):
        raise RehearsalRefused("Write once to a new runner-local ephemeral script only")
    names=("original-plan","aligned-plan","board","scout","evidence",
           "briefs","passages","docket")
    result=build_nonfactual_rehearsals(*[
        _read(getattr(args,name.replace("-","_"))) for name in names])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=True,indent=2)+"\n",encoding="utf8")
    # Log only counts. The original narration itself stays ephemeral.
    print(json.dumps({
        "status":STATUS,
        "nonfactual_original_voiceover_rehearsals":3,
        "individual_scenes":result["original_scene_count"],
        "frame_accurate_shorts":2,
        "frame_accurate_long":1,
        "real_fact_checked_scripts":0,
        "actual_voice_files":0,
        "actual_video_files":0,
        "paid_model_calls":0,
        "youtube_uploads":0,
        "release_authorized":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
