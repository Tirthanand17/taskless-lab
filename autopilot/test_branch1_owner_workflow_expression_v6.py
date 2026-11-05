"""Regression proof: GitHub must expand owner OAuth expression, not pass a literal."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/flowminute-b1-owner-youtube-readonly-nov.yml"


class ProtectedGithubExpressionTests(unittest.TestCase):
    def test_secret_and_artifact_metadata_use_real_github_double_brace_expressions(self):
        source=WORKFLOW.read_text(encoding="utf8")
        expect=(
            "$"+"{{ secrets.YOUTUBE_TOKEN_JSON }}",
            "$"+"{{ github.ref }}",
            "$"+"{{ github.run_id }}",
            "$"+"{{ github.run_attempt }}",
            "$"+"{{ runner.temp }}",
        )
        for expression in expect:
            with self.subTest(expression=expression):
                self.assertIn(expression,source)
        for broken in ("$"+"{ secrets.YOUTUBE_TOKEN_JSON }}",
                       "$"+"{ github.ref }}",
                       "$"+"{ github.run_id }}",
                       "$"+"{ github.run_attempt }}",
                       "$"+"{ runner.temp }}"):
            self.assertNotIn(broken,source)
        self.assertIn("environment: youtube-production",source)
        self.assertIn("permissions:\n  contents: read",source)
        self.assertIn("OWNER_SECRET_SYNTAX_OK_NOT_YET_OWNER_API_AUTHENTICATED",source)
        self.assertIn("github.ref == 'refs/heads/main'",source)
        self.assertIn("if: github.repository == 'Tirthanand17/taskless-lab'",source)


if __name__=="__main__":
    unittest.main()
