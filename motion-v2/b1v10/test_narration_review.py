import unittest
import numpy as np
from narration_review import compare, frame_samples, validate_words, cues, timestamp, energy, SPF
class NarrationTests(unittest.TestCase):
    def test_match(self):
        self.assertEqual(compare("One byte.","one byte"),1)
        self.assertLess(compare("one byte is safe","one byte is not safe"),1)
    def test_frame_alignment(self):
        for n in (1,1599,1600,42001):
            m=frame_samples(n,220)
            self.assertEqual(m%SPF,0)
            self.assertGreaterEqual(m,n+10560)
    def test_words(self):
        validate_words([{"start":.1,"end":.3,"word":"one"},{"start":.3,"end":.5,"word":"byte"}],1)
    def test_overlap(self):
        with self.assertRaises(ValueError):validate_words([{"start":.1,"end":.4,"word":"one"},{"start":.3,"end":.5,"word":"byte"}],1)
    def test_bounds(self):
        with self.assertRaises(ValueError):validate_words([{"start":.1,"end":1.1,"word":"one"}],1)
    def test_empty(self):
        with self.assertRaises(ValueError):validate_words([],1)
    def test_cues(self):
        w=[{"start":i*.2,"end":(i+1)*.2,"word":"word"} for i in range(12)]
        out=cues(w)
        self.assertEqual(sum(len(g["words"]) for g in out),12)
        self.assertTrue(all(len(g["words"])<=5 for g in out))
    def test_timestamp(self):
        self.assertEqual(timestamp(61.234),"00:01:01,234")
    def test_clipping(self):
        self.assertEqual(energy(np.array([32767,-32768,0],dtype=np.int16))["clipped_samples"],2)
if __name__=="__main__":unittest.main()
