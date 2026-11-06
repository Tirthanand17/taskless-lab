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

# The narration is truly written, including 4 original sections per Short
# and 9 per long. It deliberately cannot state a vendor's new factual news.
def _paragraphs(slot: str, data: dict) -> list[str]:
    thing,input_,comparison,measure,failure,next_step = (
        data[k] for k in ("thing","input","comparison","measure","failure","next"))
    if slot == "short_am":
        return [
            f"Here is a challenge: could you spot the weakest step in {thing}? "
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
            "This is a synthetic demonstration, not evidence from today's headlines.",
            f"Now picture this mistake: {failure}. Instead of spinning a graphic forever, "
            f"show {comparison}, and pause on the exact point that needs checking.",
            f"The useful next move is {next_step}. Ask what would count as a fair test, "
            f"including {measure}. A catchy claim is a question until someone verifies it independently.",
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
        theme=THEMES[family]
        paragraphs=_paragraphs(slot,theme)
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
        raw=theme["label"]+" — "+slot.replace("_"," ").title()+" synthetic test"
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
