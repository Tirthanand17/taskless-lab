"""Fully synthetic Phase 2R3 Hindi/English text-only package tests."""
from dataclasses import replace
from datetime import datetime, timezone
import unittest

from autopilot.test_phase2_pipeline import fixtures, NOW
from autopilot.phase2_pipeline import digest
from autopilot.agent_org import WorkflowError
from autopilot.phase2r3_bilingual_scripts import (
    LABEL, SpokenBeat, VideoTextDraft, review_three_video_text_drafts,
)

EN = ("We use a small synthetic CSV table to understand every column, "
      "check the sample rows and explain each step clearly.")
HI = ("हम एक छोटी सी उदाहरण CSV फ़ाइल बनाते हैं, हर कॉलम देखते हैं और "
      "समझते हैं कि नकली डेटा को सुरक्षित तरीके से कैसे पढ़ें।")


def entry(kind="short",lang="en",ep="draft_en_01",narrator="narrator_english_one"):
    base_research,base_review,base_script,_,base_en,base_hi,_=fixtures()
    research=replace(base_research,episode_id=ep)
    review=replace(base_review,episode_id=ep,research_digest=digest(research))
    script=replace(base_script,episode_id=ep,research_digest=digest(research),
                   fact_review_digest=digest(review))
    template=base_en if lang=="en" else base_hi
    n=4 if kind=="short" else 24
    duration=10_000 if kind=="short" else 15_000
    phrase=EN if lang=="en" else HI
    localized=replace(template,episode_id=ep,script_digest=digest(script),
                      narrated_text=" ".join([phrase]*n))
    beats=tuple(SpokenBeat(
        start_ms=i*duration,end_ms=(i+1)*duration,
        spoken_text=phrase,subtitle_text=phrase,
        overlay="Synthetic CSV demonstration",
        visual_mode="labeled_simulation" if i==1 else "explanatory_diagram",
        claim_ids=("c_csv_reader",),simulation_label_visible=i==1,
    ) for i in range(n))
    plan=VideoTextDraft(
        episode_id=ep,kind=kind,language=lang,
        research_sha256=digest(research),script_sha256=digest(script),
        localized_sha256=digest(localized),
        narrator_id=narrator,
        narrator_direction="Speak naturally with a distinct, conversational voice and educational pacing.",
        beats=beats)
    return (plan,research,review,script,localized)


def package():
    return [
        entry("short","hi","draft_hi_01","narrator_hindi_one"),
        entry("short","en","draft_en_01","narrator_english_two"),
        entry("long","hi","draft_long_01","narrator_long_three"),
    ]


class Phase2R3TextTests(unittest.TestCase):
    def setUp(self):
        self.entries=package()

    def validate(self,entries=None):
        return review_three_video_text_drafts(self.entries if entries is None else entries,now=NOW)

    def changed(self,position,**updates):
        edited=list(self.entries)
        old=edited[position]
        edited[position]=(replace(old[0],**updates),*old[1:])
        return edited

    def test_three_drafts_valid_but_not_production_approved(self):
        r=self.validate()
        self.assertEqual(r["status"],"THREE_BILINGUAL_TEXT_DRAFTS_STRUCTURALLY_READY_ONLY")
        self.assertEqual(len(r["episodes"]),3)
        self.assertFalse(r["ready_for_rendering"])
        self.assertFalse(r["publishing_authorized"])
        self.assertFalse(r["voice_or_audio_created"])
        self.assertFalse(r["narrator_difference_audibly_confirmed"])
        self.assertFalse(r["subtitle_speech_alignment_verified"])
        self.assertEqual(r["spend_inr"],0)

    def test_series_order_invariant(self):
        self.assertEqual(self.validate(),self.validate(list(reversed(self.entries))))

    def test_two_shorts_have_different_planned_narrators(self):
        x=self.changed(1,narrator_id="narrator_hindi_one")
        with self.assertRaises(WorkflowError):
            self.validate(x)

    def test_no_real_voice_license_can_be_forged(self):
        for field in ("audio_exists","provider_rights_verified",
                      "externally_fact_approved","publishing_authorized"):
            with self.subTest(field=field),self.assertRaises(WorkflowError):
                self.validate(self.changed(0,**{field:True}))

    def test_staging_label_cannot_be_escalated(self):
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,label="PRODUCTION_APPROVED"))

    def test_script_hash_change_denied(self):
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,script_sha256="f"*64))

    def test_localized_hash_change_denied(self):
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,localized_sha256="f"*64))

    def test_research_hash_change_denied(self):
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,research_sha256="f"*64))

    def test_unreviewed_claim_denied(self):
        old=self.entries[0][0]
        beats=list(old.beats)
        beats[0]=replace(beats[0],claim_ids=("c_unreviewed",))
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,beats=tuple(beats)))

    def test_subtitle_must_match_exact_narration_words(self):
        old=self.entries[1][0]
        beats=list(old.beats)
        beats[0]=replace(beats[0],subtitle_text="This altered subtitle never matches narration.")
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(1,beats=tuple(beats)))

    def test_narration_cannot_differ_from_reviewed_language_draft(self):
        old=self.entries[1][0]
        beats=list(old.beats)
        message=beats[0].spoken_text+" Here is a stealth new promise."
        beats[0]=replace(beats[0],spoken_text=message,subtitle_text=message)
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(1,beats=tuple(beats)))

    def test_visual_simulation_must_be_visibly_disclosed(self):
        old=self.entries[0][0]
        beats=list(old.beats)
        beats[1]=replace(beats[1],simulation_label_visible=False)
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,beats=tuple(beats)))

    def test_real_screen_cannot_be_claimed_without_media(self):
        old=self.entries[0][0]
        beats=list(old.beats)
        beats[1]=replace(beats[1],visual_mode="real_screen")
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,beats=tuple(beats)))

    def test_no_demonstration_disclosed_denied(self):
        old=self.entries[0][0]
        beats=tuple(replace(b,visual_mode="motion_2d",simulation_label_visible=False)
                    for b in old.beats)
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,beats=beats))

    def test_timing_overlap_denied(self):
        old=self.entries[0][0]
        beats=list(old.beats)
        beats[2]=replace(beats[2],start_ms=15_000)
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,beats=tuple(beats)))

    def test_timing_gap_denied(self):
        old=self.entries[0][0]
        beats=list(old.beats)
        beats[2]=replace(beats[2],start_ms=21_000)
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,beats=tuple(beats)))

    def test_long_story_under_six_minutes_denied(self):
        old=self.entries[2][0]
        beats=tuple(replace(b,start_ms=i*10000,end_ms=(i+1)*10000)
                    for i,b in enumerate(old.beats))
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(2,beats=beats))

    def test_unnatural_speech_rate_denied(self):
        plan,research,review,script,localized=self.entries[1]
        # Keep Short duration within its allowed range, but double narration
        # to force an actual speaking rate beyond the 235 WPM ceiling.
        beats=tuple(replace(b,start_ms=i*6250,end_ms=(i+1)*6250,
                            spoken_text=b.spoken_text+" "+b.spoken_text,
                            subtitle_text=b.subtitle_text+" "+b.subtitle_text)
                    for i,b in enumerate(plan.beats))
        localized=replace(localized,narrated_text=" ".join(b.spoken_text for b in beats))
        plan=replace(plan,beats=beats,localized_sha256=digest(localized))
        with self.assertRaises(WorkflowError):
            self.validate([self.entries[0],(plan,research,review,script,localized),self.entries[2]])

    def test_fewer_than_four_short_segments_denied(self):
        old=self.entries[0][0]
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,beats=old.beats[:3]))

    def test_hindi_must_contain_real_devanagari_script(self):
        item=list(self.entries)
        plan,research,review,script,localized=item[0]
        spoken=EN
        beats=tuple(replace(b,spoken_text=spoken,subtitle_text=spoken) for b in plan.beats)
        localized=replace(localized,narrated_text=" ".join([spoken]*len(beats)))
        plan=replace(plan,beats=beats,localized_sha256=digest(localized))
        item[0]=(plan,research,review,script,localized)
        with self.assertRaises(WorkflowError):
            self.validate(item)

    def test_duplicate_episode_id_denied(self):
        first=self.entries[0]
        other=entry("short","en",first[0].episode_id,"narrator_different_two")
        items=[first,other,self.entries[2]]
        with self.assertRaises(WorkflowError):
            self.validate(items)

    def test_wrong_three_format_mix_denied(self):
        replaced=entry("short","en","draft_three_en","narrator_third")
        with self.assertRaises(WorkflowError):
            self.validate([*self.entries[:2],replaced])

    def test_unknown_narrator_id_rejected(self):
        with self.assertRaises(WorkflowError):
            self.validate(self.changed(0,narrator_id="same_voice"))

    def test_untrusted_marketing_promises_blocked(self):
        base=self.entries[1]
        plan,research,review,script,localized=base
        beats=list(plan.beats)
        harmful="This video guarantees guaranteed earnings without any effort."
        beats[0]=replace(beats[0],spoken_text=harmful,subtitle_text=harmful)
        localized=replace(localized,narrated_text=" ".join(b.spoken_text for b in beats))
        plan=replace(plan,beats=tuple(beats),localized_sha256=digest(localized))
        with self.assertRaises(WorkflowError):
            self.validate([self.entries[0],(plan,research,review,script,localized),self.entries[2]])

    def test_bilingual_long_is_hindi_with_english_terms(self):
        r=self.validate()
        long=[x for x in r["episodes"] if x["kind"]=="long"][0]
        self.assertEqual(long["language"],"hi")
        self.assertTrue(long["has_labeled_simulation"])
        self.assertTrue(360000<=long["duration_ms"]<=540000)

    def test_raw_video_text_not_exposed_in_report(self):
        r=self.validate()
        self.assertNotIn(EN,str(r))
        self.assertNotIn(HI,str(r))
        self.assertNotIn("Speak naturally with a distinct",str(r))

    def test_wrong_creator_language_binding_denied(self):
        # Existing language draft role must align with its EN/HI assigned specialist.
        entry0=list(self.entries[0])
        entry0[-1]=replace(entry0[-1],translator_role="language.english_editor")
        with self.assertRaises(WorkflowError):
            self.validate([tuple(entry0),*self.entries[1:]])


if __name__=="__main__":
    unittest.main()
