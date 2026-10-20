"""Run real Node built-in tests of the deployment-disabled Worker D1 adapter.

This stays entirely inside public synthetic CI. Neither a Cloudflare binding
nor a YouTube token/provider connection exists. Never shell-execute user data.
"""
from pathlib import Path
import shutil
import subprocess
import unittest


class D1WorkersPreparedCandidateNodeTests(unittest.TestCase):
    def test_native_node_d1_worker_cas_shape_and_fail_closed_contract(self):
        node=shutil.which("node")
        if node is None:
            self.skipTest("Node executable absent: Worker candidate not tested")
        testcase=Path(__file__).with_name("test_cloud_d1_worker_candidate.mjs")
        source=Path(__file__).with_name("cloud_d1_worker_candidate.mjs")
        self.assertTrue(testcase.is_file())
        self.assertTrue(source.is_file())
        run=subprocess.run(
            [node,"--test",str(testcase)],
            capture_output=True,text=True,timeout=45,
            cwd=str(testcase.parent),
            check=False,
        )
        self.assertEqual(
            run.returncode,0,
            "Native Node synthetic D1 candidate suite failed:\n"
            + (run.stdout+run.stderr)[-6000:],
        )
        self.assertIn("# pass 13",run.stdout)
        self.assertIn("# fail 0",run.stdout)


if __name__=="__main__":
    unittest.main()
