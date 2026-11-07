"""B4g3 regression: exact PCM-timed sound accents with no audio or rights approval."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import math
import unittest

from autopilot.original_pcm_sound_design_b4g3 import (
    OriginalSoundRefused,STATUS,SFX_PER_GRAMMAR,BED_COMPONENTS,
    SFX_GAIN,plan_pcm_cut_effects,mix_original_sound_design,
)
from autopilot.one_way_storyboard_timing_b4g2 import (
    active_focus_sequence, grammar_for_original_scene,stage_hold_seconds,
)

SCENES=("HOOK_QUESTION","SOURCE_SCOPE","DEMONSTRATION","VERIFY_AND_LIMIT")
DURATIONS=(8.25,11.5,10.75,9.5)


class ProceduralAudioSchedulingTests(unittest.TestCase):
    def test_real_pcm_focus_times_match_b4g2_ffconcat_stage_cuts(self):
        scene_ids=list(SCENES)
        scene_durations=list(DURATIONS)
        self.assertEqual(sum(scene_durations),40.)
        events=plan_pcm_cut_effects(scene_ids,scene_durations,24000)
        self.assertEqual(len(events),10)
        self.assertEqual([x["scene_number"] for x in events],
                         [1,1,2,2,2,3,3,3,4,4])
        start=0.
        for scene_number,(scene_id,duration) in enumerate(
                zip(scene_ids,scene_durations),1):
            grammar=grammar_for_original_scene(scene_id)
            phase=active_focus_sequence(grammar)
            holds=stage_hold_seconds(duration,len(phase),.36)
            for i in range(1,len(phase)):
                item=next(e for e in events if
                          e["scene_number"]==scene_number and
                          e["phase_number"]==i)
                exact=start+sum(holds[:i])
                self.assertLessEqual(abs(item["sample_index"]/24000-exact),
                                     1/24000)
                self.assertIn(item["effect"],(
                    "soft_tick","soft_ping","soft_sweep","reveal_pulse"))
                self.assertEqual(item["effect"],SFX_PER_GRAMMAR[grammar][i-1])
            start+=duration
        self.assertTrue(all(events[i]["sample_index"]<
                            events[i+1]["sample_index"]
                            for i in range(len(events)-1)))

    def test_long_nine_original_scenes_have_at_most_30_short_nonlooping_fx(self):
        ids=list(SCENES)+[
            "MECHANISM","BASELINE","EXAMPLE_1","EXAMPLE_2","COUNTEREXAMPLE",
        ]
        lengths=[22.0]*9
        events=plan_pcm_cut_effects(ids,lengths,24000)
        self.assertEqual(len(events),24)
        self.assertEqual([x["scene_number"] for x in events[:2]],[1,1])
        self.assertGreater(events[-1]["sample_index"],0)
        self.assertLess(events[-1]["sample_index"],sum(lengths)*24000)
        self.assertTrue(all(type(x["sample_index"]) is int for x in events))

    def test_empty_malformed_or_nonphysical_audio_phase_timing_rejected(self):
        variants=(
            ([],[],24000),
            (list(SCENES),list(DURATIONS),True),
            (list(SCENES),list(DURATIONS),12345),
            (["FAKE_NEWS_AUTHORIZED",*SCENES[1:]],list(DURATIONS),24000),
            (list(SCENES),list(DURATIONS[:-1]),24000),
            (list(SCENES),[8.25,float("nan"),10.75,9.5],24000),
            (list(SCENES),[8.25,-11.5,10.75,9.5],24000),
            (list(SCENES),[8.25,True,10.75,9.5],24000),
            (list(SCENES),[400.,11.5,10.75,9.5],24000),
        )
        for ids,lengths,rate in variants:
            with self.subTest(rate=rate,lengths=lengths),self.assertRaises(
                    OriginalSoundRefused):
                plan_pcm_cut_effects(ids,lengths,rate)

    def test_unmodified_external_asset_and_numerically_bounded_recipe(self):
        self.assertEqual(sum(x[1] for x in BED_COMPONENTS),.0024)
        self.assertLessEqual(SFX_GAIN,.35)
        self.assertEqual(set(SFX_PER_GRAMMAR),{"compare","steps","matrix","gate"})
        self.assertEqual(len(SFX_PER_GRAMMAR["matrix"]),3)


@unittest.skipUnless(importlib.util.find_spec("numpy") is not None,
                     "Physical PCM waveform test runs only in audio-enabled GitHub worker")
class ActualGeneratedPCMTests(unittest.TestCase):
    def _source(self):
        import numpy as np
        duration=sum(DURATIONS)
        sr=24000
        t=np.arange(round(duration*sr),dtype=np.float64)/sr
        # Original test-only computer-generated fake speech frequency,
        # not a supplied or published actual person's voice recording.
        signal=(.115*np.sin(2*np.pi*221*t)).astype(np.float32)
        return signal,sr

    def test_subtle_tones_only_near_cut_points_preserve_original_pcm_time(self):
        import numpy as np
        signal,sr=self._source()
        mixed,report=mix_original_sound_design(
            signal,sr,list(SCENES),list(DURATIONS))
        same_again,again=mix_original_sound_design(
            signal,sr,list(SCENES),list(DURATIONS))
        self.assertTrue(np.array_equal(mixed,same_again))
        self.assertEqual(report,again)
        self.assertEqual(mixed.dtype,np.float32)
        self.assertEqual(mixed.shape,signal.shape)
        self.assertEqual(report["status"],STATUS)
        self.assertEqual(report["original_pcm_samples"],len(signal))
        self.assertEqual(report["original_programmatic_visual_cut_sound_count"],10)
        self.assertEqual(report["original_physical_scene_count"],4)
        self.assertFalse(report["measured_integrated_lufs_or_true_peak"])
        self.assertFalse(report["human_audio_listening_completed"])
        self.assertFalse(report["youtube_release_authorized"])
        self.assertEqual(report["third_party_songs_samples_or_effects"],0)
        self.assertTrue(report["source_original_narration_words_unchanged"])
        self.assertTrue(report["mixed_peak_below_minus_0_35_dbfs"])
        self.assertLess(float(np.max(np.abs(mixed))),.96)
        self.assertGreater(float(np.max(np.abs(mixed-signal))),.0005)
        self.assertLess(float(np.max(np.abs(mixed-signal))),.022)
        self.assertEqual(len(report["original_programmatic_audio_recipe_sha256"]),64)
        # Physical SFX peaks near first actual focus cut, not at generic 1s
        # and not at narration end (which is kept original).
        first=report["sound_events"][0]["sample_index"]
        self.assertEqual(first,round(.36*sr))
        a=np.max(np.abs((mixed-signal)[first:first+int(.08*sr)]))
        b=np.max(np.abs((mixed-signal)[int(1*sr):int(1.05*sr)]))
        self.assertGreater(a,4*b)

    def test_anomalously_hot_voice_reduces_gain_without_pcm_clipping(self):
        import numpy as np
        source,sr=self._source()
        hot=source*8.0
        out,proof=mix_original_sound_design(hot,sr,list(SCENES),list(DURATIONS))
        self.assertEqual(out.shape,hot.shape)
        self.assertLess(proof["gain_applied_to_voice"],1.0)
        self.assertLess(float(np.max(np.abs(out))),.96)

    def test_corrupt_or_mismatched_physical_pcm_fails_closed(self):
        import numpy as np
        signal,sr=self._source()
        for sample,rate,durations in (
            (signal.astype(np.int16),sr,list(DURATIONS)),
            (signal,sr,list(DURATIONS[:-1])),
            (signal,True,list(DURATIONS)),
            (signal,sr,[*DURATIONS[:-1],DURATIONS[-1]+1.0]),
            (signal.copy(),sr,[*DURATIONS[:-1],float("nan")]),
            (np.zeros_like(signal),sr,list(DURATIONS)),
        ):
            with self.subTest(rate=rate),self.assertRaises(OriginalSoundRefused):
                mix_original_sound_design(sample,rate,list(SCENES),durations)
        broken=signal.copy()
        broken[12000]=float("nan")
        with self.assertRaises(OriginalSoundRefused):
            mix_original_sound_design(broken,sr,list(SCENES),list(DURATIONS))


if __name__=="__main__":
    unittest.main()
