"""FlowMinute Phase 3: typed production planning across reviewed script and media.

STAGING ONLY. Accepts proposed storyboards, voice directions, audio metadata,
subtitle timings and render recipes. Does not synthesize speech, claim that
audio was listened to, check commercial rights, render a video or publish.
All approvals below are typed *claims*, not independently authenticated reviews.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import re

from .agent_org import Handoff, State, WorkflowError
from .phase2_pipeline import (
    Phase2Coordinator, CreativeScript, HookVariants, LocalizedDraft,
    LanguageReview, digest
)

def required(text: str, min_chars: int = 10, max_chars: int = 2000) -> None:
    if not isinstance(text, str) or not min_chars <= len(text.strip()) <= max_chars:
        raise WorkflowError("Invalid bounded production description")

def hex_digest(value: str) -> None:
    if not isinstance(value,str) or not re.fullmatch("[0-9a-f]{64}", value):
        raise WorkflowError("Missing content-addressed media or artifact hash")

@dataclass(frozen=True)
class Scene:
    number: int
    start_ms: int
    end_ms: int
    mode: str
    visual_instruction: str
    claim_ids: tuple[str, ...]
    title_overlay: str
    safe_margin_percent: int = 10
    simulation_label_visible: bool = False
    assets: tuple[str, ...] = ()

    def validate(self, *, script: CreativeScript) -> None:
        if not isinstance(self.number,int) or self.number < 1:
            raise WorkflowError("Invalid scene number")
        if (not isinstance(self.start_ms,int) or not isinstance(self.end_ms,int)
                or self.start_ms < 0 or self.end_ms <= self.start_ms):
            raise WorkflowError("Invalid scene timing")
        if self.mode not in ("real_screen","motion_2d","animation_3d","explanatory_diagram","labeled_simulation"):
            raise WorkflowError("Unsupported scene treatment")
        if self.mode == "labeled_simulation" and not self.simulation_label_visible:
            raise WorkflowError("Unlabeled simulated application or demo")
        if not 8 <= self.safe_margin_percent <= 25:
            raise WorkflowError("Overlay must respect safe margins")
        required(self.visual_instruction,20)
        required(self.title_overlay,4,90)
        if len(set(self.claim_ids)) != len(self.claim_ids) or not set(self.claim_ids) <= set(script.used_claim_ids):
            raise WorkflowError("Story scene contains a claim not in the script")
        if len(self.assets) != len(set(self.assets)) or any(not re.fullmatch(r"asset_[a-z0-9_]{2,50}",x) for x in self.assets):
            raise WorkflowError("Scene asset manifest invalid")

@dataclass(frozen=True)
class Storyboard:
    episode_id: str
    script_digest: str
    hooks_digest: str
    kind: str
    language: str
    width: int
    height: int
    scenes: tuple[Scene, ...]
    stage_label: str = "STORYBOARD_DRAFT_ONLY"

    def validate(self, script: CreativeScript, hooks: HookVariants, *, kind: str, language: str) -> None:
        if self.script_digest != digest(script) or self.hooks_digest != digest(hooks):
            raise WorkflowError("Storyboard is not bound to the reviewed script and hook options")
        if self.kind != kind or self.language != language or self.stage_label != "STORYBOARD_DRAFT_ONLY":
            raise WorkflowError("Incorrect storyboard format or stage")
        expected=(1080,1920) if kind=="short" else (1920,1080)
        if (self.width,self.height) != expected:
            raise WorkflowError("Incorrect Short or long-form frame layout")
        if not 2 <= len(self.scenes) <= 80:
            raise WorkflowError("Storyboard needs multiple scenes")
        last=0
        has_demo=False
        for number,scene in enumerate(self.scenes,1):
            scene.validate(script=script)
            if scene.number!=number or scene.start_ms!=last:
                raise WorkflowError("Storyboard scene gap or sequence mismatch")
            last=scene.end_ms
            if scene.mode in ("real_screen","labeled_simulation"):
                has_demo=True
        limit=180000 if kind=="short" else 3600000
        if not 3000<=last<=limit or not has_demo:
            raise WorkflowError("Duration invalid or no demonstrative scene")

@dataclass(frozen=True)
class VoiceDirection:
    episode_id: str
    language_review_digest: str
    localized_text_digest: str
    language: str
    voice_profile: str
    narrator_id: str
    delivery_instructions: str
    provider_kind: str
    rights_reference: str
    stage_label: str = "VOICE_PLAN_NO_AUDIO_YET"

    def validate(self,review:LanguageReview,localized:LocalizedDraft) -> None:
        if (self.language_review_digest!=digest(review)
                or self.localized_text_digest!=digest(localized)
                or self.language!=localized.language
                or self.stage_label!="VOICE_PLAN_NO_AUDIO_YET"):
            raise WorkflowError("Voice directions not based on language-reviewed text")
        if self.language not in ("en","hi") or self.voice_profile not in ("energetic","explanatory"):
            raise WorkflowError("Unsupported voice language or profile")
        if not re.fullmatch(r"narrator_[a-z0-9_]{2,30}",self.narrator_id):
            raise WorkflowError("Voice narrator identifier missing")
        if self.provider_kind not in ("owned_recording","licensed_tts"):
            raise WorkflowError("Voice provider is not selected")
        hex_digest(self.rights_reference)
        required(self.delivery_instructions,20)
        # This describes claimed rights, not proof of licensing.
        # A separate asset-rights inspection is required before publishing.

@dataclass(frozen=True)
class NarrationAssetRecord:
    episode_id: str
    voice_plan_digest: str
    audio_sha256: str
    duration_ms: int
    audio_file_type: str
    source_recorded: str
    stage_label: str = "AUDIO_METADATA_UNVERIFIED"

    def validate(self,voice:VoiceDirection,storyboard:Storyboard|None=None) -> None:
        if self.voice_plan_digest!=digest(voice) or self.stage_label!="AUDIO_METADATA_UNVERIFIED":
            raise WorkflowError("Narration does not match authorized voice plan")
        hex_digest(self.audio_sha256)
        if self.audio_file_type not in ("wav","mp3","m4a"):
            raise WorkflowError("Audio encoding unknown")
        if not isinstance(self.duration_ms,int) or not 1000<=self.duration_ms<=3600000:
            raise WorkflowError("Narration duration invalid")
        if storyboard is not None and abs(self.duration_ms-storyboard.scenes[-1].end_ms)>1500:
            raise WorkflowError("Narration and planned visuals have incompatible durations")
        required(self.source_recorded,20)

@dataclass(frozen=True)
class SubtitleCue:
    start_ms: int
    end_ms: int
    text: str

    def validate(self)->None:
        if (type(self.start_ms) is not int or type(self.end_ms) is not int
                or self.start_ms<0 or self.end_ms<=self.start_ms):
            raise WorkflowError("Invalid subtitle cue time")
        if not isinstance(self.text,str) or not 2<=len(self.text.strip())<=90:
            raise WorkflowError("Subtitle text too long or missing")
        if "\n" in self.text or "\r" in self.text:
            raise WorkflowError("Single-line safe subtitles required")

@dataclass(frozen=True)
class SubtitleTimeline:
    episode_id: str
    narration_digest: str
    localized_text_digest: str
    language: str
    cues: tuple[SubtitleCue, ...]
    stage_label: str = "CAPTIONS_TIMING_DRAFT_NOT_ASR_VERIFIED"

    def validate(self,narration:NarrationAssetRecord,localized:LocalizedDraft)->None:
        if (self.narration_digest!=digest(narration)
                or self.localized_text_digest!=digest(localized)
                or self.language!=localized.language
                or self.stage_label!="CAPTIONS_TIMING_DRAFT_NOT_ASR_VERIFIED"):
            raise WorkflowError("Captions not bound to the recorded narration and selected language")
        if not 2<=len(self.cues)<=160:
            raise WorkflowError("Caption segmentation invalid")
        previous=0
        for cue in self.cues:
            cue.validate()
            if cue.start_ms<previous or cue.end_ms>narration.duration_ms:
                raise WorkflowError("Overlapping or out-of-range subtitle cue")
            previous=cue.end_ms
        if self.cues[0].start_ms>1500 or narration.duration_ms-previous>1500:
            raise WorkflowError("Subtitle leading/trailing gaps need review")

@dataclass(frozen=True)
class RenderRecipe:
    episode_id: str
    storyboard_digest: str
    narration_digest: str
    subtitle_digest: str
    render_engine: str
    selected_language: str
    output_format: str
    estimated_bytes: int
    target_width: int
    target_height: int
    manual_media_review_required: bool = True
    publish_permission: bool = False

    def validate(self,board:Storyboard,narration:NarrationAssetRecord,subtitles:SubtitleTimeline)->None:
        if (self.storyboard_digest!=digest(board)
                or self.narration_digest!=digest(narration)
                or self.subtitle_digest!=digest(subtitles)):
            raise WorkflowError("Render recipe does not match reviewed scene/audio/subtitles")
        if self.selected_language!=subtitles.language or self.render_engine not in ("ffmpeg_motion_v2","remotion_draft"):
            raise WorkflowError("Unsupported render engine or language")
        if self.output_format!="mp4_h264_aac" or (self.target_width,self.target_height)!=(board.width,board.height):
            raise WorkflowError("Incorrect video output contract")
        if (type(self.estimated_bytes) is not int or not 1<=self.estimated_bytes<=1_073_741_824
                or self.manual_media_review_required is not True or self.publish_permission is not False):
            raise WorkflowError("Cost, media QA or publishing safety gate violated")
        if abs(narration.duration_ms-board.scenes[-1].end_ms)>1500:
            raise WorkflowError("Render recipe narration and visuals timing mismatch")

STAGES:dict[str,type]={
    "storyboard":Storyboard,"voice_plan":VoiceDirection,
    "narration":NarrationAssetRecord,"subtitle_plan":SubtitleTimeline,
    "render_plan":RenderRecipe
}

class Phase3Coordinator:
    """Accept Phase 2 completed workflow and attach five DRAFT production handoffs."""
    def __init__(self,phase2:Phase2Coordinator):
        if not isinstance(phase2,Phase2Coordinator):
            raise WorkflowError("Phase 2 coordinator required")
        self.base=phase2
        self.workflow=phase2.workflow
        self.artifacts:dict[str,object]={}

    def submit(self,stage:str,artifact:object,*,actor:str)->str:
        if stage not in STAGES or type(artifact) is not STAGES[stage]:
            raise WorkflowError("Invalid Phase 3 artifact type")
        task_id=f"{self.base.episode_id.lower()}:{stage}"
        task=self.workflow.contracts[task_id]
        if actor!=task.owner or artifact.episode_id!=self.base.episode_id:
            raise WorkflowError("Wrong production specialist or episode")
        if self.workflow.runs[task_id].status!=State.READY:
            raise WorkflowError("Upstream storyboard/language review is incomplete")
        script=self.base.artifacts.get("script")
        hooks=self.base.artifacts.get("hooks")
        language_review=self.base.artifacts.get("language_review")
        if stage=="storyboard":
            artifact.validate(script,hooks,kind=self.base.workflow.contracts[f"{self.base.episode_id.lower()}:script"].owner.split(".")[1].replace("shorts_writer","short").replace("longform_writer","long"),language=self.base.workflow.contracts[f"{self.base.episode_id.lower()}:script"].episode_id and self.base.workflow.contracts[f"{self.base.episode_id.lower()}:script"].objective.split(" for ")[1].split(" ")[1])
            refs=(digest(script),digest(hooks))
        elif stage=="voice_plan":
            localized=self.base.artifacts.get("english" if artifact.language=="en" else "hindi")
            artifact.validate(language_review,localized)
            refs=(digest(language_review),digest(localized))
        elif stage=="narration":
            voice=self.artifacts.get("voice_plan")
            artifact.validate(voice,self.artifacts.get("storyboard"))
            refs=(digest(voice),)
        elif stage=="subtitle_plan":
            narration=self.artifacts.get("narration")
            localized=self.base.artifacts.get("english" if artifact.language=="en" else "hindi")
            if artifact.language!=self.artifacts["voice_plan"].language:
                raise WorkflowError("Subtitles and narrator language differ")
            artifact.validate(narration,localized)
            refs=(digest(narration),digest(localized))
        else:
            board=self.artifacts.get("storyboard")
            narration=self.artifacts.get("narration")
            subtitle=self.artifacts.get("subtitle_plan")
            artifact.validate(board,narration,subtitle)
            refs=(digest(board),digest(narration),digest(subtitle))
        h=Handoff(task_id=task_id,artifact_type=task.produces,
                  sha256_hex=digest(artifact),
                  evidence_refs=tuple("sha256:"+x for x in refs),
                  produced_by=actor,recorded_at_utc=self.base.now.isoformat())
        # A failed validation never claims the task, avoiding dirty workflow state.
        self.workflow.claim(task_id,actor=actor)
        self.workflow.complete(h,actor=actor)
        self.artifacts[stage]=artifact
        return h.sha256_hex

    def progress(self)->dict[str,Any]:
        return {"episode_id":self.base.episode_id,
                "production_stages_draft":tuple(x for x in STAGES if x in self.artifacts),
                "next_tasks":tuple(self.workflow.ready()),
                "narration_audio_verified_by_ffprobe":False,
                "subtitle_transcript_synced_by_listening":False,
                "asset_commercial_rights_authenticated":False,
                "actual_mp4_rendered":False,
                "publishing_authorized":False,
                "uploads_enabled":False,
                "scheduling_enabled":False,
                "cloud_deployed":False}
