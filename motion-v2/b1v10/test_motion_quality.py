import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from motion_quality import validate_asset, motion_stats, sha
class MotionQA(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"asset.png"
        pattern=np.indices((256,256)).sum(axis=0)%2*255
        Image.fromarray(pattern.astype("uint8")).save(self.path)
        self.record={"sha256":sha(self.path),"origin":"original","rights_evidence":"generated test fixture","review_only":True,"display_pixels":[256,256]}
    def tearDown(self):self.tmp.cleanup()
    def test_asset(self):self.assertEqual(validate_asset(self.path,self.record)["dimensions"],[256,256])
    def test_hash(self):
        self.record["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"hash"):validate_asset(self.path,self.record)
    def test_rights(self):
        self.record["rights_evidence"]=""
        with self.assertRaisesRegex(ValueError,"rights"):validate_asset(self.path,self.record)
    def test_upscale(self):
        self.record["display_pixels"]=[512,512]
        with self.assertRaisesRegex(ValueError,"upscaling"):validate_asset(self.path,self.record)
    def test_blur(self):
        Image.new("L",(256,256),128).save(self.path)
        self.record["sha256"]=sha(self.path)
        with self.assertRaisesRegex(ValueError,"edge-detail"):validate_asset(self.path,self.record)
    def test_freeze(self):
        f=np.zeros((64,64),np.uint8)
        self.assertTrue(motion_stats([f]*90)["freeze_review_hold"])
    def test_loop(self):
        f=[np.full((64,64),i*10,np.uint8) for i in range(15)]
        self.assertTrue(motion_stats(f*6)["repeat_review_hold"])
    def test_nonrepeat(self):
        f=[np.full((64,64),i*2,np.uint8) for i in range(90)]
        r=motion_stats(f)
        self.assertFalse(r["freeze_review_hold"]);self.assertFalse(r["repeat_review_hold"])
if __name__=="__main__":unittest.main()
