"""FlowMinute Phase 2R1 public capture operator preflight, network OFF by default.

Preview is a deterministic read-only policy report with no network.
Live is for a separately owner-approved manual GitHub Actions invocation
and fails CLOSED unless multiple explicit gates are present.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Callable, Mapping, Sequence

from .phase2_pipeline import CitationRecord, ResearchPackage, SupportedClaim
from .phase2_public_collector import (
    PAGE_MAX_BYTES, ROBOTS_MAX_BYTES, TIMEOUT_S, _ALLOWED,
    CaptureDenied, collect_csv_research_sources, public_capture_summary,
)

OWNER_PHRASE = "I_APPROVE_ONE_READONLY_CSV_PUBLIC_FETCH"
ENV_APPROVAL_KEY = "FLOWMINUTE_PUBLIC_FETCH_APPROVED"
ENV_APPROVAL_VALUE = "OWNER_EXPLICIT_ONE_TIME_CSV_APPROVAL"
TARGET_BRANCH = "feature/flowminute-phase2-evidence-preflight"
SAFE_MODE = "PREVIEW_ONLY_NO_NETWORK"
PUBLIC_FETCH_MAX_REQUESTS = 4


def _fixture_topic(*, now: datetime) -> ResearchPackage:
    """Metadata scaffold; NOT independent fact or publisher review."""
    when = now.isoformat()
    return ResearchPackage(
        episode_id="public_csv_research_01",
        topic="Safely inspect a synthetic CSV file with Python standard library",
        viewer_problem="Beginners need a concrete privacy preserving explanation of working with CSV data.",
        demonstration="Create a fake CSV dataset locally, inspect rows, and explain the two source references.",
        sources=(
            CitationRecord("src_python_docs", _ALLOWED["src_python_docs"],
                           "official", when, "cli_provisional_capture_not_fact_reviewed"),
            CitationRecord("src_independent_csv", _ALLOWED["src_independent_csv"],
                           "independent", when, "cli_provisional_capture_not_fact_reviewed"),
        ),
        claims=(SupportedClaim(
            "c_csv_reader",
            "A Python CSV reader can be demonstrated using synthetic sample data.",
            ("src_python_docs", "src_independent_csv")),),
    )


def _preview_result() -> dict:
    return {
        "status": SAFE_MODE,
        "phase": "2R1_MANUAL_PUBLIC_SOURCE_PREFLIGHT",
        "network_attempted": False,
        "source_count": len(_ALLOWED),
        "approved_source_ids": sorted(_ALLOWED),
        "max_total_http_requests_if_approved": PUBLIC_FETCH_MAX_REQUESTS,
        "per_request_timeout_seconds": TIMEOUT_S,
        "max_article_bytes_each": PAGE_MAX_BYTES,
        "max_robots_bytes_each": ROBOTS_MAX_BYTES,
        "requires_owner_approval": True,
        "requires_manual_github_workflow_dispatch": True,
        "stores_raw_page_text": False,
        "uses_paid_provider": False,
        "monthly_spend_inr": 0,
        "factually_verified": False,
        "publishing_authorized": False,
    }


def _live_gates_ok(*, env: Mapping[str, str], phrase: str | None) -> bool:
    """Env inputs are gates, not cryptographically authenticated approvals."""
    return (phrase == OWNER_PHRASE
            and env.get(ENV_APPROVAL_KEY) == ENV_APPROVAL_VALUE
            and env.get("GITHUB_ACTIONS") == "true"
            and env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and env.get("RUNNER_OS") == "Linux"
            and env.get("GITHUB_REF_NAME") == TARGET_BRANCH)


def run_capture_preflight(
    *,
    mode: str = "preview",
    phrase: str | None = None,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
    _test_collector: Callable[..., tuple] | None = None,
) -> dict:
    if mode not in ("preview", "live"):
        raise CaptureDenied("Only preview and explicit one-shot live modes exist")
    if mode == "preview":
        return _preview_result()
    env = env if env is not None else os.environ
    if not _live_gates_ok(env=env, phrase=phrase):
        raise CaptureDenied("Owner-approved manual GitHub dispatch required; network not attempted")
    if _test_collector is not None and env.get("FLOWMINUTE_TEST_ONLY") != "1":
        raise CaptureDenied("Injected test collector forbidden in live operator mode")
    clock = now if now is not None else datetime.now(timezone.utc)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise CaptureDenied("UTC-aware clock required")
    clock = clock.astimezone(timezone.utc)
    research = _fixture_topic(now=clock)
    collector = _test_collector or collect_csv_research_sources
    captures = collector(research, now=clock, allow_live_network=True)
    report = public_capture_summary(captures)
    return {
        "status": "PUBLIC_SOURCE_FETCH_ATTEMPT_FINISHED_BUT_FACTS_NOT_VERIFIED",
        "mode": "live_one_shot",
        "source_count": report["source_count"],
        "captured_source_hashes": report["source_hashes"],
        "simulation_present": report["simulation_present"],
        "real_provider_provenance_verified": False,
        "quotes_reviewed": False,
        "factually_verified": False,
        "rights_verified": False,
        "script_authorized": False,
        "publishing_authorized": False,
        "max_http_requests": PUBLIC_FETCH_MAX_REQUESTS,
        "spend_inr": 0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Public CSV capture PREVIEW by default")
    parser.add_argument("--mode", choices=("preview", "live"), default="preview")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        data = run_capture_preflight(mode=args.mode, phrase=args.confirm)
    except (CaptureDenied, OSError, TimeoutError, ValueError):
        print(json.dumps({
            "status": "BLOCKED_NO_FURTHER_FETCHES",
            "publishing_authorized": False,
            "raw_pages_logged": False,
        }, sort_keys=True))
        return 2
    print(json.dumps(data, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
