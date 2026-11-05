"""FlowMinute OFFLINE zero-rupee monthly render-capacity admission estimate.

All evidence in this module is caller-supplied. It never authenticates a
provider entitlement, grants an upload credential, executes rendering, or
permits billing. Source-backed platform *limitations* may be encoded as
fail-closed rules, but numerical fit is ALWAYS a hypothetical rehearsal.

Native 1080p examples from the existing HD benchmark:
    short English: 42s at 1080x1920, H.264 + AAC
    short Hindi:   42s at 1080x1920, H.264 + AAC
    long Hindi:   432s at 1920x1080, H.264 + AAC
A 30-day 2-Short + 1-long plan has 90 distinct media jobs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math

from .agent_org import WorkflowError

DAYS = 30
FPS = 24
HEADROOM_NUM = 5
HEADROOM_DEN = 4
RETENTION_COPIES = 2
MAX_TRIAL_AGE_DAYS = 14
FREE_WORKER_INVOCATION_CPU_MS = 10  # Cloudflare docs, 12 Oct 2026

@dataclass(frozen=True)
class MediaLane:
    lane: str
    daily_jobs: int
    duration_s: int
    width: int
    height: int

LANES = (
    MediaLane("short_en",1,42,1080,1920),
    MediaLane("short_hi",1,42,1080,1920),
    MediaLane("long_hi",1,432,1920,1080),
)

@dataclass(frozen=True)
class FullLengthTrial:
    lane: str
    duration_s: int
    frames: int
    width: int
    height: int
    wall_seconds: float
    final_bytes: int
    peak_memory_mib: int
    video_codec: str
    audio_codec: str
    full_decode_passed: bool
    narration_and_caption_qa_passed: bool
    rights_review_passed: bool
    measured_at: datetime

@dataclass(frozen=True)
class ZeroRupeeCapacity:
    backend: str
    monthly_render_seconds_available: int
    private_storage_bytes_available: int
    available_worker_ram_mib: int
    monthly_base_cost_inr: int
    automatic_overage_disabled: bool
    privately_stored_media: bool
    persistent_storage_verified: bool
    free_allowance_independently_verified: bool
    valid_until: datetime


def _aware(value: datetime)->bool:
    return (isinstance(value,datetime) and value.tzinfo is not None
            and value.utcoffset() is not None)

def _ceil_div(a:int,b:int)->int:
    return (a+b-1)//b

def workload_manifest()->dict:
    """Fixed demand, no reliance on publishing or unbounded scheduling."""
    rows=[]
    for lane in LANES:
        videos=lane.daily_jobs*DAYS
        rows.append({
            "lane":lane.lane,
            "monthly_videos":videos,
            "per_video_seconds":lane.duration_s,
            "monthly_media_seconds":videos*lane.duration_s,
            "monthly_frames":videos*lane.duration_s*FPS,
            "native_dimensions":f"{lane.width}x{lane.height}",
        })
    return {
        "days":DAYS,
        "videos_per_day":sum(x.daily_jobs for x in LANES),
        "monthly_videos":sum(x["monthly_videos"] for x in rows),
        "monthly_media_seconds":sum(x["monthly_media_seconds"] for x in rows),
        "monthly_native_hd_frames":sum(x["monthly_frames"] for x in rows),
        "lanes":rows,
        "actual_videos_produced":0,
        "publishing_authorized":False,
    }


def evaluate_capacity(trials:tuple[FullLengthTrial,...],
                      capacity:ZeroRupeeCapacity|None,*,
                      now:datetime)->dict:
    """Evaluate hypothetical numbers, NEVER certify production capacity.

    Do not accept 1-second sample extrapolations as full-length trials,
    free-tier *advertising* as account entitlement, or booleans as legally
    signed rights/narration approval. A fit cannot authorize deployment.
    """
    if not _aware(now):
        raise WorkflowError("Capacity clock requires aware datetime")
    if not isinstance(trials,tuple):
        raise WorkflowError("Capacity trials must be a bounded immutable tuple")
    if len(trials)>len(LANES):
        raise WorkflowError("Only one full-duration test per lane is accepted")
    if capacity is not None and not isinstance(capacity,ZeroRupeeCapacity):
        raise WorkflowError("Malformed cloud allowance contract")
    demand=workload_manifest()
    blockers=[]
    by_lane={}
    specs={x.lane:x for x in LANES}
    for trial in trials:
        if not isinstance(trial,FullLengthTrial):
            raise WorkflowError("Typed full-length render test required")
        spec=specs.get(trial.lane)
        if spec is None or trial.lane in by_lane:
            raise WorkflowError("Duplicated or unknown full-HD trial lane")
        by_lane[trial.lane]=trial
        if (any(type(x) is not int or x<=0 for x in (
                trial.duration_s,trial.frames,trial.width,trial.height,
                trial.final_bytes,trial.peak_memory_mib))
                or type(trial.wall_seconds) not in (int,float)
                or not math.isfinite(trial.wall_seconds)
                or not 0<trial.wall_seconds<=86400*2
                or not _aware(trial.measured_at)):
            raise WorkflowError("Invalid trial measurement or timestamp")
        if (trial.duration_s!=spec.duration_s
                or trial.frames!=spec.duration_s*FPS
                or (trial.width,trial.height)!=(spec.width,spec.height)):
            blockers.append(f"{trial.lane}:NOT_FULL_LENGTH_NATIVE_HD")
        if (trial.video_codec!="h264" or trial.audio_codec!="aac"
                or trial.full_decode_passed is not True):
            blockers.append(f"{trial.lane}:FULL_AV_DECODE_NOT_VERIFIED")
        if (trial.narration_and_caption_qa_passed is not True
                or trial.rights_review_passed is not True):
            blockers.append(f"{trial.lane}:NARRATION_CAPTION_RIGHTS_NOT_VERIFIED")
        if not now-timedelta(days=MAX_TRIAL_AGE_DAYS)<=trial.measured_at<=now:
            blockers.append(f"{trial.lane}:TRIAL_TOO_OLD_OR_FUTURE")
    for lane in LANES:
        if lane.lane not in by_lane:
            blockers.append(f"{lane.lane}:FULL_LENGTH_TRIAL_MISSING")
    estimated_render_s=None
    estimated_storage_bytes=None
    required_ram=None
    if len(by_lane)==len(LANES):
        raw_s=sum(
            _ceil_div(math.ceil(by_lane[x.lane].wall_seconds*1000)
                      *x.daily_jobs*DAYS,1000)
            for x in LANES
        )
        raw_bytes=sum(
            by_lane[x.lane].final_bytes*x.daily_jobs*DAYS for x in LANES
        )
        estimated_render_s=_ceil_div(raw_s*HEADROOM_NUM,HEADROOM_DEN)
        estimated_storage_bytes=_ceil_div(
            raw_bytes*RETENTION_COPIES*HEADROOM_NUM,HEADROOM_DEN
        )
        required_ram=max(by_lane[x.lane].peak_memory_mib for x in LANES)
    if capacity is None:
        blockers.append("PROVIDER_ZERO_OVERAGE_CONTRACT_MISSING")
    else:
        if (capacity.backend not in (
                "cloudflare-workers-free","github-public-standard-ci",
                "private-verified-zero-overage-worker")
                or any(type(x) is not int or x<0 for x in (
                    capacity.monthly_render_seconds_available,
                    capacity.private_storage_bytes_available,
                    capacity.available_worker_ram_mib,
                    capacity.monthly_base_cost_inr))
                or not _aware(capacity.valid_until)):
            raise WorkflowError("Invalid provider capacity allowance")
        if capacity.backend=="cloudflare-workers-free":
            blockers.append("CLOUDFLARE_FREE_CPU_INSUFFICIENT_FOR_VIDEO_ENCODING")
        if capacity.backend=="github-public-standard-ci":
            blockers.append("PUBLIC_CI_NOT_AUTHORIZED_FOR_PRIVATE_MEDIA_AND_OAUTH")
        if (capacity.monthly_base_cost_inr!=0
                or capacity.automatic_overage_disabled is not True):
            blockers.append("NONZERO_COST_OR_BILLABLE_OVERAGE_NOT_DISABLED")
        if (capacity.free_allowance_independently_verified is not True
                or capacity.valid_until<=now):
            blockers.append("ACCOUNT_SPECIFIC_FREE_CAPACITY_NOT_VERIFIED")
        if (capacity.privately_stored_media is not True
                or capacity.persistent_storage_verified is not True):
            blockers.append("PRIVATE_DURABLE_MEDIA_STORAGE_NOT_VERIFIED")
        if estimated_render_s is not None and (
            capacity.monthly_render_seconds_available<estimated_render_s
        ):
            blockers.append("MONTHLY_RENDER_RUNTIME_ALLOWANCE_INSUFFICIENT")
        if estimated_storage_bytes is not None and (
            capacity.private_storage_bytes_available<estimated_storage_bytes
        ):
            blockers.append("MONTHLY_PRIVATE_STORAGE_ALLOWANCE_INSUFFICIENT")
        if required_ram is not None and (
            capacity.available_worker_ram_mib<required_ram
        ):
            blockers.append("WORKER_PEAK_RAM_ALLOWANCE_INSUFFICIENT")
    blockers=tuple(sorted(set(blockers)))
    return {
        "status":("HYPOTHETICAL_RESOURCE_FIT_NOT_AUTHORIZED"
                  if not blockers else "NO_VERIFIED_ZERO_COST_CAPACITY"),
        "demand":demand,
        "assumed_estimate_render_seconds_with_25_percent_headroom":
            estimated_render_s,
        "assumed_estimate_private_storage_bytes_two_copies_with_headroom":
            estimated_storage_bytes,
        "assumed_peak_worker_ram_mib":required_ram,
        "blocking_reasons":blockers,
        "self_reported_evidence_only":True,
        "independent_provider_authority_verified_by_software":False,
        "full_hd_publishing_capacity_verified":False,
        "licensed_voice_or_rights_verified_by_software":False,
        "new_service_connection_authorized":False,
        "youtube_upload_authorized":False,
        "publishing_authorized":False,
        "cloud_deployed":False,
        "recurring_budget_cap_inr":0,
        "cloudflare_workers_free_invocation_cpu_ms":
            FREE_WORKER_INVOCATION_CPU_MS,
    }
