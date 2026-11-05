"""B4e1 original non-copyrighted procedural sound-effect QA.

This test actually synthesizes numeric PCM audio and checks it remains quiet,
short, bounded, speech-timed, and refuses invalid source/voice. It does not
purport to measure subjective human narration performance or licensed assets.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest

from autopilot.polished_sound_design_v2 import (
    AudioPolishRejected,SCHEDULE,STATUS,_sfx,enrich_original_wav,
)


def _mock_voice(path,scene_count,rate=24000):
    import numpy as np
    import soundfile as sf
    duration=scene_count*7.0
    t=np.arange(round(duration*rate))/rate
    x=(.043*np.sin(2*np.pi*225*t)).astype("float32")
    sf.write(str(path),x,rate,subtype="PCM_16")
    return [{"start":i*7.0,"duration":7.0} for i in range(scene_count)],x


@unittest.skipUnless(importlib.util.find_spec('numpy') is not None and
                     importlib.util.find_spec('soundfile') is not None,
                     'Physical waveform QA runs in dedicated B4e1 job with NumPy and soundfile installed')
class ProceduralSoundQA(unittest.TestCase):
    def test_each_scene_effect_is_synthetic_bounded_without_external_music(self):
        import numpy as np
        for name in ("soft_tick","soft_ping","soft_sweep","reveal_pulse"):
            with self.subTest(name=name):
                wave=_sfx(name,24000,seed=912)
                self.assertGreater(len(wave),500)
                self.assertLess(len(wave),8000)
                self.assertTrue(np.isfinite(wave).all())
                self.assertGreater(np.max(abs(wave)),.0004)
                self.assertLessEqual(np.max(abs(wave)),.05)

    def test_exact_two_short_and_long_story_beat_sound_counts(self):
        import numpy as np
        import soundfile as sf
        for theme,count,scene_count in (
            ("lunar_signal",5,6),("quake_energy",5,6),
            ("file_transfer",8,20),
        ):
            with self.subTest(theme=theme),tempfile.TemporaryDirectory() as t:
                p=Path(t)/"original.wav"
                timings,before=_mock_voice(p,scene_count)
                report=enrich_original_wav(p,theme,timings)
                after,rate=sf.read(p,dtype="float32")
                self.assertEqual(after.size,before.size)
                self.assertEqual(rate,24000)
                self.assertEqual(report["original_programmatic_effects"],count)
                self.assertEqual(report["status"],STATUS)
                self.assertGreater(np.max(abs(after-before)),.0002)
                self.assertLess(np.max(abs(after-before)),.06)
                self.assertLess(np.max(abs(after)),.13)
                self.assertLess(report["seconds_original_ui_sfx_total"],3.0)
                self.assertFalse(report["external_sound_effects_or_music_imported"])
                self.assertFalse(report["actual_human_listening_and_license_review"])
                self.assertFalse(report["release_authorized"])
                self.assertEqual(len(report["sound_design_recipe_sha256"]),64)

    def test_no_clip_and_timing_inconsistency_refuse(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"voice.wav"
            timing,_=_mock_voice(p,6)
            for wrong in (
                timing[:-1],
                [{"start":99.0,"duration":7.0}]+timing[1:],
                timing[:-1]+[{"start":35,"duration":8.0}],
                timing[:-1]+[{"start":35,"duration":-7.0}],
                timing[:-1]+[{"start":float("nan"),"duration":7.0}],
            ):
                with self.subTest(wrong=str(wrong[-1])),self.assertRaises(AudioPolishRejected):
                    enrich_original_wav(p,"lunar_signal",wrong)

    def test_missing_audio_invalid_theme_or_path_denied(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"missing.wav"
            with self.assertRaises(AudioPolishRejected):
                enrich_original_wav(p,"lunar_signal",[])
            timings,_=_mock_voice(p,6)
            with self.assertRaises(AudioPolishRejected):
                enrich_original_wav(p,"imitation_movie_studio",timings)
            p.unlink()
            p.symlink_to(Path(t)/"no-file")
            with self.assertRaises(AudioPolishRejected):
                enrich_original_wav(p,"lunar_signal",timings)

    def test_only_finite_synthetic_sfx_recipes_not_music_samples(self):
        self.assertEqual(len(SCHEDULE),3)
        self.assertLessEqual(max(len(x) for x in SCHEDULE.values()),8)
        self.assertTrue(all(len(x)>=5 for x in SCHEDULE.values()))


if __name__=="__main__":
    unittest.main()
