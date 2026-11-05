"""Run D1-native Node fixture tests as part of ordinary pytest CI."""
from pathlib import Path
import shutil
import subprocess
import unittest
class D1NativeNodeBridge(unittest.TestCase):
 def test_native_node_suite(self):
  node=shutil.which("node")
  if not node:self.skipTest("Node missing, no false pass")
  f=Path(__file__).with_name("test_phase4_d1_native_reservation_candidate.mjs")
  r=subprocess.run([node,"--test",str(f)],cwd=f.parent,text=True,capture_output=True,timeout=45)
  self.assertEqual(r.returncode,0,(r.stdout+r.stderr)[-5000:])
  self.assertIn("# pass 15",r.stdout)
  self.assertIn("# fail 0",r.stdout)
