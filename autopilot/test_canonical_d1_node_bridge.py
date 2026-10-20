"""Execute real Node.js regression suite in repository Python CI. No provider calls."""
from pathlib import Path
import shutil
import subprocess
import unittest

class CanonicalD1NodeBridge(unittest.TestCase):
    def test_synthetic_canonical_d1_node_adapter(self):
        node=shutil.which('node')
        if node is None:
            self.skipTest('Node unavailable; no false green result')
        root=Path(__file__).parent
        run=subprocess.run([node,'--test',str(root/'test_canonical_d1_readback_candidate.mjs')],
                           cwd=root,capture_output=True,text=True,timeout=45,check=False)
        self.assertEqual(run.returncode,0,(run.stdout+run.stderr)[-4500:])
        self.assertIn('# pass 15',run.stdout)
        self.assertIn('# fail 0',run.stdout)
