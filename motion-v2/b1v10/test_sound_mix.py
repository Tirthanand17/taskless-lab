import unittest,json
from pathlib import Path
import numpy as np
from sound_mix import mix,duck_gain,plan,SR
class MixTests(unittest.TestCase):
    def test_duck(self):
        v=np.r_[np.zeros(SR),np.full(SR,.12),np.zeros(SR)]
        g=duck_gain(v)
        self.assertLess(g[SR+SR//2],.4)
        self.assertGreater(g[-1],.9)
    def test_length(self):
        v=.14*np.sin(2*np.pi*200*np.arange(SR*3)/SR)
        y,b,e=mix(v,[{"sample":SR,"effect":"soft_tick"}])
        self.assertEqual(len(y),len(v))
        np.testing.assert_allclose(y-b-e,v,atol=1e-12)
    def test_silence(self):
        with self.assertRaises(ValueError):mix(np.zeros(SR*2),[])
    def test_hot(self):
        with self.assertRaises(ValueError):mix(np.full(SR*2,.98),[])
    def test_bounds(self):
        with self.assertRaises(ValueError):mix(np.full(SR*2,.1),[{"sample":SR*2,"effect":"soft_tick"}])
    def test_real_events(self):
        root=Path(__file__).parent
        r=json.loads((root/"NARRATION_REVIEW_QA.json").read_text())
        c=json.loads((root/"word_captions_review.json").read_text())
        e=plan(r,c)
        self.assertEqual(len(e),4)
        self.assertTrue(all(x["sample"]==x["frame"]*1600 for x in e))
if __name__=="__main__":unittest.main()
