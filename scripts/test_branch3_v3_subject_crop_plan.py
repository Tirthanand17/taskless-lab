import unittest
from scripts.branch3_v3_subject_crop_plan import crop_plan


def shot(boxes,start=0,end=1500):
    return {"start_ms":start,"end_ms":end,"samples":[
        {"time_ms":start+i*500,"boxes":box} for i,box in enumerate(boxes)]}


class SubjectCropTests(unittest.TestCase):
    def test_subject_preserved_and_speed_bounded(self):
        bs=[[[100,300,200,250,900]],[[220,300,200,250,900]],[[350,300,200,250,900]]]
        r=crop_plan(1920,1080,1500,[shot(bs)])
        s=r["shots"][0]
        self.assertEqual(s["mode"],"tracked_crop")
        cw,ch=s["crop_size"]
        self.assertEqual(cw*16,ch*9)
        for p,boxes in zip(s["keyframes"],bs):
            x,y,w,h,_=boxes[0]
            self.assertLessEqual(p["x"],x)
            self.assertGreaterEqual(p["x"]+cw,x+w)
            self.assertLessEqual(p["y"],y)
            self.assertGreaterEqual(p["y"]+ch,y+h)
        for p,q in zip(s["keyframes"],s["keyframes"][1:]):
            self.assertLessEqual(abs(q["x"]-p["x"]),cw//4)
        self.assertFalse(r["render_authorized"])
        self.assertFalse(r["speaker_verified"])

    def test_ambiguous_and_fast_movement_fallback(self):
        a=[100,300,200,250,900]
        b=[1600,300,200,250,900]
        for boxes,reason in [([[a],[a,b],[a]],"MISSING_OR_AMBIGUOUS_SUBJECT"),
                             ([[a],[b],[b]],"UNSAFE_FAST_MOTION"),
                             ([[a],[],[a]],"MISSING_OR_AMBIGUOUS_SUBJECT"),
                             ([[a]],"INSUFFICIENT_COVERAGE")]:
            s=crop_plan(1920,1080,1500,[shot(boxes)])["shots"][0]
            self.assertEqual(s["mode"],"fit")
            self.assertEqual(s["fallback_reason"],reason)
            self.assertEqual(s["keyframes"],[])

    def test_scene_reset_and_invalid_coordinates(self):
        a=[100,300,200,250,900];b=[1600,300,200,250,900]
        p=crop_plan(1920,1080,2000,[shot([[a],[a]],0,1000),shot([[b],[b]],1000,2000)])
        self.assertTrue(all(s["mode"]=="tracked_crop" for s in p["shots"]))
        with self.assertRaises(ValueError):
            crop_plan(1920,1080,1500,[shot([[[1800,0,500,100,900]]])])
        with self.assertRaises(ValueError):
            crop_plan(1920,1080,1500,[shot([[a]],500,1500)])


if __name__=="__main__":
    unittest.main()
