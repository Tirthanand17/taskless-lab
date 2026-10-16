"""Preflight to forbid laptop-dependent, unbudgeted or unauthorized publishing.

This module deliberately does NOT handle OAuth token values or perform uploads.
A privileged adapter lives only in a separate private cloud environment.
"""
from dataclasses import dataclass
from pathlib import PurePath
from typing import Mapping
import re

class CloudGateError(RuntimeError):
    pass

@dataclass(frozen=True)
class Preflight:
    authorized: bool
    status: str
    missing: tuple[str, ...]
    daily_spend_cap_usd: float

REQUIRED = (
    "FLOWMINUTE_CLOUD_DEPLOYMENT",
    "FLOWMINUTE_PRIVATE_WORKER",
    "FLOWMINUTE_OBJECT_STORAGE",
    "FLOWMINUTE_DURABLE_LEDGER",
    "FLOWMINUTE_YOUTUBE_OAUTH_SECRET_REF",
    "FLOWMINUTE_YOUTUBE_ANALYTICS_SCOPE",
    "FLOWMINUTE_MEDIA_QA",
)

def preflight(env: Mapping[str,str], workdir: str) -> Preflight:
    """External sources supply values; NEVER log token or secret contents."""
    missing = tuple(k for k in REQUIRED if not env.get(k,"").strip())
    if env.get("FLOWMINUTE_CLOUD_DEPLOYMENT") != "1":
        missing += ("CLOUD_DEPLOYMENT_MUST_EQUAL_1",)
    if env.get("FLOWMINUTE_PRIVATE_WORKER") != "1":
        missing += ("PRIVATE_WORKER_MUST_EQUAL_1",)
    if env.get("FLOWMINUTE_MEDIA_QA") != "1":
        missing += ("MEDIA_QA_MUST_EQUAL_1",)
    if env.get("FLOWMINUTE_ALLOW_LAPTOP") not in ("", "0"):
        missing += ("LAPTOP_USE_NOT_AUTHORIZED",)
    normalized=workdir.replace("\\","/").lower()
    if not workdir.startswith("/") or re.search(r"(^|/)(users|desktop|onedrive)(/|$)",normalized):
        missing += ("WORKDIR_MUST_BE_ISOLATED_LINUX_CLOUD_PATH",)
    try: budget = float(env.get("FLOWMINUTE_DAILY_SPEND_CAP_USD", "0"))
    except (TypeError,ValueError):
        budget = -1
    if budget < 0 or budget > 10_000:
        missing += ("INVALID_SPEND_CAP",)
    if env.get("FLOWMINUTE_ENABLE_PUBLISH") != "1":
        missing += ("PRIVILEGED_PUBLISH_DISABLED",)
    # Ref must be a name in a vault, not a raw refresh token or JSON string.
    token_ref = env.get("FLOWMINUTE_YOUTUBE_OAUTH_SECRET_REF","")
    if token_ref and not re.fullmatch(r"[A-Za-z0-9_.:/-]{8,160}",token_ref):
        missing += ("USE_SECRET_MANAGER_REFERENCE_NOT_TOKEN",)
    return Preflight(not missing, "authorized" if not missing else "blocked",
                     tuple(dict.fromkeys(missing)), max(budget,0))

def validate_distinct_short_voices(first_voice: str, second_voice: str):
    if not first_voice or not second_voice or first_voice == second_voice:
        raise CloudGateError("Morning and evening Shorts require distinct voice IDs")

def require_approval_for_spend(estimated_usd: float, approved_remaining_usd: float):
    if estimated_usd < 0 or estimated_usd > approved_remaining_usd:
        raise CloudGateError("Spend exceeds explicitly approved remaining budget")

def public_worker_can_publish() -> bool:
    """Hard invariant. Public repositories never have an upload credential."""
    return False
