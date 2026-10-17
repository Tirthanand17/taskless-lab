"""FFmpeg-based sandbox fixtures are synthetic and may never be published."""
import tempfile,unittest,subprocess
from pathlib import Path
from autopilot.render_inspection import inspect_media

class RenderMediaTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory()
    root=Path(cls.tmp.name)
    cls.good=root/'colored_with_audio.mp4'
    cls.mute=root/'no_audio.mp4'
    cls.black=root/'black_with_audio.mp4'
    def make(path,color,audio):
       cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
            '-i',f'color=c={color}:size=320x480:rate=25:d=2']
       if audio:cmd+=['-f','lavfi','-i','sine=frequency=440:duration=2']
       cmd+=['-map','0:v:0']
       if audio:cmd+=['-map','1:a:0']
       cmd+=['-c:v','libx264','-pix_fmt','yuv420p']
       if audio:cmd+=['-c:a','aac']
       cmd+=['-t','2',str(path)]
       p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
       if p.returncode:raise RuntimeError(p.stderr)
    make(cls.good,'blue',True);make(cls.mute,'blue',False);make(cls.black,'black',True)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def call(self,path,**kwargs):
    defaults=dict(expected_width=320,expected_height=480,min_duration_s=1,max_duration_s=3)
    defaults.update(kwargs)
    return inspect_media(path,**defaults)
 def test_technical_valid_but_never_publish_cleared(self):
    out=self.call(self.good)
    self.assertEqual(out.status,'PASS_TECHNICAL_ONLY')
    self.assertEqual((out.width,out.height,out.fps),(320,480,25.0))
    self.assertEqual(len(out.video_sha256),64)
    self.assertFalse(out.publishing_cleared)
 def test_missing_audio_blocks(self):
    out=self.call(self.mute)
    self.assertIn('VIDEO_AUDIO_STREAM_COUNT_INVALID',out.issues)
 def test_wrong_dimension_blocks(self):
    out=self.call(self.good,expected_width=1080)
    self.assertIn('DIMENSIONS_INCORRECT',out.issues)
 def test_black_segment_flagged_for_review(self):
    out=self.call(self.black)
    self.assertIn('BLACK_VIDEO_SEGMENT_REVIEW',out.issues)
 def test_too_short_duration_blocks(self):
    self.assertIn('DURATION_INCORRECT',self.call(self.good,min_duration_s=10,max_duration_s=30).issues)
 def test_missing_file_blocks(self):
    self.assertIn('MISSING_OR_UNSAFE_MEDIA',self.call(self.good.parent/'nonexistent.mp4').issues)
 def test_invalid_policy_blocks(self):
    self.assertIn('INVALID_INSPECTION_POLICY',self.call(self.good,expected_width=0).issues)
 def test_file_size_limit_blocks(self):
    self.assertIn('MEDIA_SIZE_OUT_OF_BOUNDS',self.call(self.good,max_bytes=10).issues)
if __name__=='__main__':unittest.main()
