"""B4c4 source boundary tests for real GitHub-hosted OCI smoke; no Docker here.

Real Docker build/run tests execute in a separate GitHub Actions job. These
source tests prevent the build workflow from becoming a publisher.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

DOCKERFILE=Path("infra/aws/B4C4.inert.Dockerfile")
WORKFLOW=Path(".github/workflows/flowminute-b4c4-inert-oci-build-test.yml")


class InertOwnerContainerContract(unittest.TestCase):
    def test_inert_dockerfile_requires_registry_resolved_digest(self):
        s=DOCKERFILE.read_text(encoding="utf8")
        lines=[x.strip() for x in s.splitlines() if x.strip() and not x.lstrip().startswith("#")]
        self.assertIn("ARG BASE_IMAGE",lines)
        self.assertIn("FROM ${BASE_IMAGE}",lines)
        self.assertNotRegex(s,r"(?im)^\s*FROM\s+[^$\s]+:latest")
        self.assertFalse(any(re.match(r"(?i)^RUN\s",x) for x in lines))
        self.assertFalse(any(re.match(r"(?i)^(ADD|VOLUME|EXPOSE|HEALTHCHECK|ONBUILD)\s",x) for x in lines))
        self.assertIn("USER 65532:65532",lines)
        self.assertIn("WORKDIR /app",lines)
        self.assertIn("COPY --chown=65532:65532 autopilot /app/autopilot",lines)
        self.assertIn('ENTRYPOINT ["python","-B","-m","autopilot.b4c2_runtime_boot_guard"]',lines)
        for flag in ("FLOWMINUTE_ENABLE_PUBLISH=0","PUBLISH_ENABLED=false",
                     "FLOWMINUTE_ALLOW_LAPTOP=0","FLOWMINUTE_ENABLE_GEMINI=0",
                     "FLOWMINUTE_MODEL_PAID_SPEND_USD=0",
                     "FLOWMINUTE_RUNTIME_NETWORK_AUTHORIZED=0",
                     "FLOWMINUTE_OWNER_RELEASE_AUTHORIZED=0",
                     "PYTHONDONTWRITEBYTECODE=1"):
            with self.subTest(flag=flag):
                self.assertIn(flag,s)
        self.assertNotIn("YOUTUBE_TOKEN",s)
        self.assertNotIn("GOOGLE_OAUTH",s)

    def test_actual_hosted_container_test_is_not_cloud_deployment(self):
        s=WORKFLOW.read_text(encoding="utf8")
        self.assertIn("permissions:\n  contents: read",s)
        self.assertNotIn("id-token: write",s)
        self.assertNotRegex(s,r"(?im)^\s+schedule:")
        self.assertNotIn("pull_request_target",s)
        self.assertIn("persist-credentials: false",s)
        self.assertIn("docker pull docker.io/library/python:3.11-slim-bookworm",s)
        self.assertIn("BASE_IMAGE=",s)
        self.assertIn("--iidfile",s)
        self.assertIn("--network=none",s)
        self.assertIn("--read-only",s)
        self.assertIn("--user=65532:65532",s)
        self.assertIn("--cap-drop=ALL",s)
        self.assertIn("--security-opt=no-new-privileges",s)
        self.assertIn("--env FLOWMINUTE_ENABLE_PUBLISH=1",s)
        self.assertIn('test "$rc" = 70',s)
        for forbidden in (
            "docker push ", "aws ecs run-task", "aws ecr",
            "secrets.", "secrets[", "youtube.googleapis.com",
            "videos().insert(", "run_task(", "assignPublicIp: ENABLED",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,s)
        self.assertIn("owner_signed_attestation",s)
        self.assertIn('"ecr_image_pushed":False',s)
        self.assertIn('"aws_cloud_task_launched":False',s)
        self.assertIn('"youtube_upload_performed":False',s)
        self.assertIn('"release_authorized":False',s)
        self.assertIn("retention-days: 7",s)

    def test_base_digest_is_not_pretended_to_be_owner_signed(self):
        s=WORKFLOW.read_text(encoding="utf8")
        self.assertIn("@sha256:",s)
        self.assertIn("actual_local_image_config_digest",s)
        self.assertIn('"owner_signed_attestation":False',s)
        self.assertIn("UNSIGNED_TECHNICAL_IMAGE_BUILD_EVIDENCE.json",s)
        self.assertNotIn('"actual_oci_ecr_signer_signature_independently_verified":True',s)


if __name__=="__main__":
    unittest.main()
