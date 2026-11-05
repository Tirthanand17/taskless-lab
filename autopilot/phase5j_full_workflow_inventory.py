"""Phase 5J: exhaustive source-only GitHub workflow writer inventory.

Never calls GitHub, YouTube, Cloudflare, D1, OAuth or a shell. No authority
to migrate, restore, upload, publish or change production settings. Heuristic
workflow text inspection is not a YAML execution proof or a live variable read.
"""
from pathlib import Path
import re

EXPECTED = frozenset((
    "collect-metrics.yml", "configure-youtube.yml",
    "flowminute-agent-foundation-ci.yml",
    "flowminute-cloud-render-smoke.yml",
    "flowminute-cloud-scout.yml",
    "flowminute-full-pack-benchmark.yml",
    "publish-artifact-youtube.yml", "publish-youtube.yml",
    "qa-tomorrow-pack.yml", "qa-v6.yml", "quality.yml",
    "render-brand.yml", "render-formula-pack.yml", "render-gemini-agent.yml",
    "render-long-001.yml", "render-long-002.yml", "render-long-003.yml",
    "render-motion-v2.yml", "render-motion-v3.yml", "render-motion-v4.yml",
    "render-motion-v5.yml", "render-motion-v6.yml", "render-motion-v7.yml",
    "render-motion-v8.yml", "render-oct12.yml", "render-pilot.yml",
    "render-refresh-pack.yml", "render-short-002.yml"
))
PUBLISHERS=frozenset(("publish-youtube.yml","publish-artifact-youtube.yml"))
CONFIGURERS=frozenset(("configure-youtube.yml",))
ANALYTICS=frozenset(("collect-metrics.yml",))
SCOUTS=frozenset(("flowminute-cloud-scout.yml",))
WRITE_LINE=re.compile(r"(?m)^\s*contents:\s*write\s*(?:#.*)?$")
CRON_LINE=re.compile(r"(?m)^\s*-\s*cron\s*:")
SCHEDULE_HEADER=re.compile(r"(?m)^  schedule:\s*(?:#.*)?$")
PUBLISH_GUARD="vars.PUBLISH_ENABLED == 'true'"
CONFIG_GUARD="vars.CHANNEL_CONFIG_ENABLED == 'true'"
ANALYTICS_GUARD="vars.ANALYTICS_ENABLED == 'true'"

class SourceHold(ValueError):
    pass

def enumerate_workflows(repo_root:Path)->dict:
    if not isinstance(repo_root,Path):raise SourceHold("BAD_REPO_ROOT")
    location=repo_root/".github"/"workflows"
    try:
        if location.is_symlink() or not location.is_dir():raise OSError()
        entries=list(location.iterdir())
        if len(entries)>64:raise OSError()
    except OSError:
        raise SourceHold("WORKFLOW_DIR_UNVERIFIED") from None
    risk=[]
    names={p.name for p in entries if p.suffix in (".yml",".yaml")}
    if names!=EXPECTED:risk.append("WORKFLOW_SET_CHANGED_REQUIRES_REVIEW")
    if any(p.suffix not in (".yml",".yaml") for p in entries):
        risk.append("UNREVIEWED_WORKFLOW_DIR_ENTRY")
    tracked=[]
    for name in sorted(names):
        path=location/name
        try:
            if path.is_symlink() or not path.is_file():raise OSError()
            if path.stat().st_size>60000:raise OSError()
            content=path.read_text(encoding="utf-8")
        except (OSError,UnicodeError):
            risk.append("WORKFLOW_SOURCE_UNREADABLE")
            tracked.append({"name":name,"role":"UNREADABLE","has_repo_write":False,
                            "has_cron":False,"source_guards_present":False})
            continue
        dispatch="workflow_dispatch:" in content
        cron=bool(CRON_LINE.search(content) or SCHEDULE_HEADER.search(content))
        write=bool(WRITE_LINE.search(content) or
                   re.search(r"\bgit\s+push\b",content))
        uses_owner=("secrets.YOUTUBE_TOKEN_JSON" in content)
        invokes_upload=("scripts/publish_youtube.py" in content or
                        "videos.insert" in content or
                        "youtube.videos().insert(" in content)
        source_guards=True
        if name in PUBLISHERS:
            role="YOUTUBE_UPLOAD_WRITER"
            source_guards=(dispatch and not cron and uses_owner and invokes_upload and
               PUBLISH_GUARD in content and "environment: youtube-production" in content)
        elif name in CONFIGURERS:
            role="CHANNEL_CONFIGURATION_WRITER"
            source_guards=(dispatch and not cron and uses_owner and
              CONFIG_GUARD in content and "environment: youtube-production" in content)
        elif name in ANALYTICS:
            role="METRICS_REPOSITORY_WRITER"
            source_guards=(dispatch and not cron and uses_owner and
              ANALYTICS_GUARD in content and "environment: youtube-production" in content)
        elif name in SCOUTS:
            role="SCHEDULED_RESEARCH_ONLY"
            source_guards=(cron and not uses_owner and not invokes_upload and
                           not write and "contents: read" in content)
        elif write:
            role="REPOSITORY_CONTENTS_WRITER"
        else:
            role="CI_OR_RENDER_NO_DIRECT_WRITER_DETECTED"
        if (invokes_upload and name not in PUBLISHERS) or (
            uses_owner and name not in PUBLISHERS|CONFIGURERS|ANALYTICS):
            risk.append("UNEXPECTED_YOUTUBE_OWNER_ACCESS_IN_WORKFLOW")
            source_guards=False
        if cron and (write or uses_owner or invokes_upload):
            risk.append("SCHEDULED_WRITER_REQUIRES_REVIEW")
            source_guards=False
        if not source_guards:risk.append("WORKFLOW_GUARDS_NOT_CONFIRMED")
        if "pull_request_target:" in content and (uses_owner or write):
            risk.append("PR_TARGET_WRITE_PRIVILEGE_REQUIRES_REVIEW")
        tracked.append({"name":name,"role":role,
                        "has_repo_write":write,"has_cron":cron,
                        "source_guards_present":bool(source_guards)})
    return {
      "source_review":"STATIC_HEURISTIC_ONLY_NOT_RUNTIME_PROOF",
      "total_workflows":len(tracked),
      "workflow_source_set_exactly_reviewed":names==EXPECTED,
      "source_guards_passed":len(risk)==0,
      "video_upload_workflows":sum(x["role"]=="YOUTUBE_UPLOAD_WRITER" for x in tracked),
      "repo_write_workflows":sum(x["has_repo_write"] for x in tracked),
      "scheduled_research_workflows":sum(x["role"]=="SCHEDULED_RESEARCH_ONLY" for x in tracked),
      "workflows":tracked,
      "risk_codes":sorted(set(risk)),
      "production_github_variables_read":False,
      "production_environment_protection_read":False,
      "real_cloudflare_writers_enumerated":False,
      "account_wide_zero_spend_verified":False,
      "production_d1_writes":0,
      "youtube_api_writes":0,
      "production_migration_authorized":False,
      "unattended_publishing_authorized":False,
      "cloud_autopilot_ready":False
    }
