"""Synthetic Phase3 records only; NO real speech, video, licenses or uploads."""
from dataclasses import replace
import unittest

from autopilot.agent_org import State, WorkflowError
from autopilot.phase2_pipeline import Phase2Coordinator, digest
from autopilot.test_phase2_pipeline import EP, NOW, fixtures, submit_all
from autopilot.phase3_production import (
    Scene, Storyboard, VoiceDirection, NarrationAssetRecord,
    SubtitleCue, SubtitleTimeline, RenderRecipe, Phase3Coordinator
)

def plan_data():
    research,review,script,hooks,en,hi,language_review=fixtures()
    storyboard=Storyboard(
        EP,digest(script),digest(hooks),"short","hi",1080,1920,
        (Scene(1,0,4000,"motion_2d",
               "Display an animated illustration of an offline sample CSV file",
               ("c_csv_reader",),"CSV in Python",12),
         Scene(2,4000,10000,"real_screen",
               "Show the locally created CSV file and parsed Python columns",
               ("c_csv_reader",),"Parse the example",12,assets=("asset_screen_capture_01",))))
    voice=VoiceDirection(
        EP,digest(language_review),digest(hi),"hi","energetic","narrator_hi_b",
        "Use measured pauses and a natural Hindi explanation, not rushed sales language",
        "owned_recording","a"*64)
    narration=NarrationAssetRecord(
        EP,digest(voice),"b"*64,10000,"wav",
        "Synthetic fixture representing metadata, not an inspected real audio recording")
    subtitles=SubtitleTimeline(
        EP,digest(narration),digest(hi),"hi",
        (SubtitleCue(0,4800,"CSV फ़ाइल का उदाहरण"),SubtitleCue(4900,10000,"पाइथन से कॉलम पढ़ें")))
    recipe=RenderRecipe(
        EP,digest(storyboard),digest(narration),digest(subtitles),
        "ffmpeg_motion_v2","hi","mp4_h264_aac",16_000_000,1080,1920)
    return storyboard,voice,narration,subtitles,recipe

def add_all(p:Phase3Coordinator):
    for stage,record,actor in zip(
        ("storyboard","voice_plan","narration","subtitle_plan","render_plan"),
        plan_data(),("production.storyboard_designer","language.voice_director",
                     "production.audio_specialist","language.subtitle_specialist",
                     "production.renderer")):
        p.submit(stage,record,actor=actor)

class Phase3Tests(unittest.TestCase):
    def setUp(self):
        base=Phase2Coordinator(EP,kind="short",language="hi",now=NOW)
        submit_all(base)
        self.p=Phase3Coordinator(base)
        self.board,self.voice,self.audio,self.subtitles,self.recipe=plan_data()

    def test_five_stage_dag_staging_success(self):
        add_all(self.p)
        state=self.p.progress()
        self.assertEqual(len(state["production_stages_draft"]),5)
        self.assertIn(EP+":media_review",state["next_tasks"])
        self.assertIn(EP+":rights_review",state["next_tasks"])
        self.assertFalse(state["uploads_enabled"])
        self.assertFalse(state["cloud_deployed"])
        self.assertFalse(state["actual_mp4_rendered"])
        self.assertFalse(state["subtitle_transcript_synced_by_listening"])
        for stage in ("storyboard","voice_plan","narration","subtitle_plan","render_plan"):
            h=self.p.workflow.runs[EP+":"+stage].artifact
            self.assertEqual(h.review_state,"UNVERIFIED_STAGING_ARTIFACT")

    def test_voice_without_language_review_forbidden(self):
        base=Phase2Coordinator(EP,kind="short",language="hi",now=NOW)
        self.p=Phase3Coordinator(base)
        with self.assertRaises(WorkflowError):
            self.p.submit("voice_plan",self.voice,actor="language.voice_director")

    def test_board_before_script_and_hooks_forbidden(self):
        base=Phase2Coordinator(EP,kind="short",language="hi",now=NOW)
        self.p=Phase3Coordinator(base)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",self.board,actor="production.storyboard_designer")

    def test_cannot_change_reviewed_script_digest(self):
        bad=replace(self.board,script_digest="0"*64)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",bad,actor="production.storyboard_designer")

    def test_cannot_change_approved_hooks_digest(self):
        bad=replace(self.board,hooks_digest="0"*64)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",bad,actor="production.storyboard_designer")

    def test_short_landscape_rejected(self):
        bad=replace(self.board,width=1920,height=1080)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",bad,actor="production.storyboard_designer")

    def test_animation_without_real_or_labeled_demo_rejected(self):
        scenes=(replace(self.board.scenes[0],mode="animation_3d"),
                replace(self.board.scenes[1],mode="explanatory_diagram"))
        bad=replace(self.board,scenes=scenes)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",bad,actor="production.storyboard_designer")

    def test_unlabeled_fake_screen_rejected(self):
        scene=replace(self.board.scenes[1],mode="labeled_simulation",simulation_label_visible=False)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",replace(self.board,scenes=(self.board.scenes[0],scene)),
                          actor="production.storyboard_designer")

    def test_labeled_simulated_demo_permitted_only_for_staging(self):
        scene=replace(self.board.scenes[1],mode="labeled_simulation",simulation_label_visible=True)
        self.p.submit("storyboard",replace(self.board,scenes=(self.board.scenes[0],scene)),
                      actor="production.storyboard_designer")
        self.assertFalse(self.p.progress()["publishing_authorized"])

    def test_gaps_or_overlaps_between_scenes_rejected(self):
        scene=replace(self.board.scenes[1],start_ms=4001)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",replace(self.board,scenes=(self.board.scenes[0],scene)),
                          actor="production.storyboard_designer")

    def test_visual_claim_must_be_reviewed(self):
        scene=replace(self.board.scenes[1],claim_ids=("c_nonexistent",))
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",replace(self.board,scenes=(self.board.scenes[0],scene)),
                          actor="production.storyboard_designer")

    def test_safe_caption_margin_mandatory(self):
        scene=replace(self.board.scenes[0],safe_margin_percent=3)
        with self.assertRaises(WorkflowError):
            self.p.submit("storyboard",replace(self.board,scenes=(scene,self.board.scenes[1])),
                          actor="production.storyboard_designer")

    def test_wrong_language_voice_or_unreviewed_text_rejected(self):
        for candidate in (replace(self.voice,language="en"),
                          replace(self.voice,localized_text_digest="c"*64),
                          replace(self.voice,language_review_digest="d"*64)):
            with self.assertRaises(WorkflowError):
                self.p.submit("voice_plan",candidate,actor="language.voice_director")

    def test_invalid_voice_rights_and_actor_rejected(self):
        bad=replace(self.voice,rights_reference="not_a_digest")
        with self.assertRaises(WorkflowError):
            self.p.submit("voice_plan",bad,actor="language.voice_director")
        with self.assertRaises(WorkflowError):
            self.p.submit("voice_plan",self.voice,actor="production.audio_specialist")

    def test_narration_metadata_requires_voice_plan(self):
        with self.assertRaises(WorkflowError):
            self.p.submit("narration",self.audio,actor="production.audio_specialist")

    def test_bad_audio_hash_and_duration_rejected(self):
        self.p.submit("storyboard",self.board,actor="production.storyboard_designer")
        self.p.submit("voice_plan",self.voice,actor="language.voice_director")
        for candidate in (replace(self.audio,audio_sha256="x"*64),
                          replace(self.audio,duration_ms=25000)):
            with self.assertRaises(WorkflowError):
                self.p.submit("narration",candidate,actor="production.audio_specialist")

    def test_subtitle_cues_cannot_overlap(self):
        self.p.submit("voice_plan",self.voice,actor="language.voice_director")
        self.p.submit("narration",self.audio,actor="production.audio_specialist")
        bad=replace(self.subtitles,cues=(
            SubtitleCue(0,5200,"CSV फ़ाइल का उदाहरण"),SubtitleCue(4900,10000,"पाइथन से कॉलम पढ़ें")))
        with self.assertRaises(WorkflowError):
            self.p.submit("subtitle_plan",bad,actor="language.subtitle_specialist")

    def test_subtitle_timing_must_fit_narration(self):
        self.p.submit("voice_plan",self.voice,actor="language.voice_director")
        self.p.submit("narration",self.audio,actor="production.audio_specialist")
        bad=replace(self.subtitles,cues=(
            SubtitleCue(0,4800,"CSV फ़ाइल का उदाहरण"),SubtitleCue(4900,12000,"पाइथन से कॉलम पढ़ें")))
        with self.assertRaises(WorkflowError):
            self.p.submit("subtitle_plan",bad,actor="language.subtitle_specialist")

    def test_subtitles_cannot_switch_voice_language(self):
        self.p.submit("voice_plan",self.voice,actor="language.voice_director")
        self.p.submit("narration",self.audio,actor="production.audio_specialist")
        with self.assertRaises(WorkflowError):
            self.p.submit("subtitle_plan",replace(self.subtitles,language="en"),
                          actor="language.subtitle_specialist")

    def test_stale_subtitle_narration_hash_rejected(self):
        self.p.submit("voice_plan",self.voice,actor="language.voice_director")
        self.p.submit("narration",self.audio,actor="production.audio_specialist")
        with self.assertRaises(WorkflowError):
            self.p.submit("subtitle_plan",replace(self.subtitles,narration_digest="3"*64),
                          actor="language.subtitle_specialist")

    def test_render_recipe_requires_subtitle_stage(self):
        self.p.submit("storyboard",self.board,actor="production.storyboard_designer")
        self.p.submit("voice_plan",self.voice,actor="language.voice_director")
        self.p.submit("narration",self.audio,actor="production.audio_specialist")
        with self.assertRaises(WorkflowError):
            self.p.submit("render_plan",self.recipe,actor="production.renderer")
        self.assertEqual(self.p.workflow.runs[EP+":render_plan"].status,State.BLOCKED)

    def test_render_recipe_refuses_publish_permission_and_big_storage(self):
        self.p.submit("storyboard",self.board,actor="production.storyboard_designer")
        self.p.submit("voice_plan",self.voice,actor="language.voice_director")
        self.p.submit("narration",self.audio,actor="production.audio_specialist")
        self.p.submit("subtitle_plan",self.subtitles,actor="language.subtitle_specialist")
        for bad in (replace(self.recipe,publish_permission=True),
                    replace(self.recipe,estimated_bytes=2_000_000_000),
                    replace(self.recipe,subtitle_digest="a"*64)):
            with self.assertRaises(WorkflowError):
                self.p.submit("render_plan",bad,actor="production.renderer")

    def test_cannot_claim_media_review_automatically_after_recipe(self):
        add_all(self.p)
        self.assertEqual(self.p.workflow.runs[EP+":media_review"].status,State.READY)
        self.assertIsNone(self.p.workflow.runs[EP+":media_review"].artifact)
        self.assertFalse(self.p.progress()["narration_audio_verified_by_ffprobe"])
        self.assertFalse(self.p.progress()["asset_commercial_rights_authenticated"])

if __name__=="__main__":
    unittest.main()
