"""FlowMinute 5J: offline inventory review. No provider connection or mutations."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from autopilot.phase5j_full_workflow_inventory import enumerate_workflows, SourceHold
from autopilot.phase5j_multi_worker_inventory import inspect_workers, UnsafeInventory

CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
WORKFLOWS={
 "publish-youtube.yml":"PUBLISH_ENABLED",
 "publish-artifact-youtube.yml":"PUBLISH_ENABLED",
 "configure-youtube.yml":"CHANNEL_CONFIG_ENABLED",
 "collect-metrics.yml":"ANALYTICS_ENABLED",
}
class InvalidEvidence(ValueError):
    pass

def assess(data, repository, *, now, runtime_worker_evidence=None):
    expected={"channel","checked_at_utc","cloudflare","github","backup","budget"}
    if type(data) is not dict or set(data)!=expected: raise InvalidEvidence("SCHEMA")
    if data["channel"]!=CHANNEL: raise InvalidEvidence("CHANNEL")
    if not isinstance(repository,Path): raise InvalidEvidence("REPOSITORY")
    if not isinstance(now,datetime) or now.tzinfo is None: raise InvalidEvidence("CLOCK")
    try:
        seen=datetime.fromisoformat(data["checked_at_utc"].replace("Z","+00:00"))
    except (ValueError,TypeError,AttributeError):
        raise InvalidEvidence("TIMESTAMP") from None
    if seen.utcoffset()!=timedelta(0):raise InvalidEvidence("UTC")
    rules={
      "cloudflare":{"worker_seen","uploads_off","budget_flag_zero",
                    "all_workers_seen","cron_triggers_checked","no_other_d1_writer_proven"},
      "github":{"live_publish_variable_off","environment_rules_verified",
                "other_writer_repos_reviewed"},
      "backup":{"seven_day_window_seen","bookmark_custodied","backend_verified",
                "independent_restore_tested"},
      "budget":{"free_plan_verified","free_d1_limits_verified",
                "paid_services_excluded","hard_zero_charge_cap_verified"}
    }
    for group,fields in rules.items():
        entry=data[group]
        if type(entry) is not dict or set(entry)!=fields:raise InvalidEvidence("FIELDS")
        if any(type(entry[k]) is not bool for k in fields):raise InvalidEvidence("BOOLEANS")
    source=[]
    for filename,gate in WORKFLOWS.items():
        file=repository/".github"/"workflows"/filename
        try:
            if file.is_symlink() or file.stat().st_size>50000:raise OSError()
            text=file.read_text(encoding="utf-8")
            ok=("workflow_dispatch:" in text and
                ("vars."+gate+" == 'true'") in text and
                "environment: youtube-production" in text and
                "schedule:" not in text)
        except (OSError,UnicodeError):
            ok=False
        source.append({"name":filename,"source_guard_present":ok})
    issues=[]
    if now.astimezone(timezone.utc)-seen>timedelta(hours=24) or seen>now:
        issues.append("EVIDENCE_STALE")
    if not all(data["cloudflare"][k] for k in (
        "worker_seen","uploads_off","budget_flag_zero")):
        issues.append("WORKER_RUNTIME_FLAGS_NOT_CONFIRMED")
    if not all(data["cloudflare"][k] for k in (
        "all_workers_seen","cron_triggers_checked","no_other_d1_writer_proven")):
        issues.append("CLOUDFLARE_WRITER_INVENTORY_INCOMPLETE")
    if not all(x["source_guard_present"] for x in source):
        issues.append("GITHUB_PUBLISH_SOURCE_GUARD_MISSING")
    try:
        full_source=enumerate_workflows(repository)
        full_source_ok=full_source["source_guards_passed"]
    except SourceHold:
        full_source={"total_workflows":0,"video_upload_workflows":0,
                     "repo_write_workflows":0,"scheduled_research_workflows":0}
        full_source_ok=False
    if not full_source_ok:
        issues.append("FULL_GITHUB_WORKFLOW_INVENTORY_NOT_VERIFIED")
    multi_worker_source=None
    if runtime_worker_evidence is None:
        issues.append("CLOUDFLARE_THREE_WORKER_RUNTIME_EVIDENCE_MISSING")
    else:
        try:
            multi_worker_source=inspect_workers(runtime_worker_evidence,now=now)
            if multi_worker_source["risk_codes"]:
                issues.append("CLOUDFLARE_MULTIPLE_WORKER_WRITE_SURFACES_NOT_VERIFIED")
        except UnsafeInventory:
            issues.append("CLOUDFLARE_MULTIPLE_WORKER_EVIDENCE_MALFORMED")
    # Even a synthetically clean multi-worker packet is untrusted. Only
    # separately authenticated account/provider evidence can close this gate.
    if not all(data["github"].values()):
        issues.append("GITHUB_PRODUCTION_VARIABLES_OR_WRITERS_UNVERIFIED")
    if not all(data["backup"].values()):
        issues.append("BACKUP_AND_DISPOSABLE_RESTORE_UNVERIFIED")
    if not all(data["budget"].values()):
        issues.append("ACCOUNT_WIDE_ZERO_SPEND_NOT_PROVEN")
    return {"state":"HOLD_WRITER_BACKUP_AND_COST","issues":issues,
       "workflows":source,"full_source_inventory_reviewed":full_source_ok,
       "full_source_workflow_count":full_source["total_workflows"],
       "full_source_video_upload_workflows":full_source["video_upload_workflows"],
       "full_source_repo_write_workflows":full_source["repo_write_workflows"],
       "full_source_research_cron_workflows":full_source["scheduled_research_workflows"],
       "multi_worker_observations_supplied":runtime_worker_evidence is not None,
       "multi_worker_risk_codes":multi_worker_source["risk_codes"] if multi_worker_source else [],
       "caller_evidence_not_authenticated":True,
       "production_d1_writes":0,"youtube_upload_attempts":0,
       "production_migration_authorized":False,
       "cloud_publishing_authorized":False,"cloud_autopilot_ready":False}
