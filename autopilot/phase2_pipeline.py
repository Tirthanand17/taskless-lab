"""Source-backed research -> independent review -> creative -> bilingual staging.

This is a typed draft adapter for the existing agent_org.Workflow, not an AI
writer, fact-checking oracle, publisher, media renderer, or Google connector.
External sources and all free text are untrusted data. A review record describes
an assertion submitted by the designated role; it is NOT cryptographic proof
that a human or external provider verified factual accuracy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from ipaddress import ip_address
import json
import re
from typing import Any
from urllib.parse import urlsplit

from .agent_org import Handoff, State, Workflow, WorkflowError, episode_workflow

MAX_TEXT = 8000


def _required(value: str, minimum: int = 12) -> None:
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= MAX_TEXT:
        raise WorkflowError("Required bounded educational text missing")


def _https_source(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise WorkflowError("Malformed research source")
    try:
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        # Network is NEVER opened, but do not accept internal URLs as evidence.
        if (url.scheme != "https" or not host or not url.path
                or url.username or url.password or url.port not in (None, 443)
                or host in ("localhost", "localhost.localdomain")
                or host.endswith((".local", ".internal"))
                or host.startswith("127.")):
            raise WorkflowError("Research source must be public HTTPS")
        try:
            ip_address(host)
        except ValueError:
            pass
        else:
            raise WorkflowError("Numeric IP source not accepted")
        if "." not in host or len(host) > 253:
            raise WorkflowError("Invalid research source hostname")
    except ValueError as exc:
        raise WorkflowError("Malformed research source") from exc
    return host


def _stamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise WorkflowError("Date must be timezone aware")
    try:
        item = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WorkflowError("Invalid research timestamp") from exc
    if item.tzinfo is None or item.utcoffset() is None:
        raise WorkflowError("Research timestamp must be timezone aware")
    return item.astimezone(timezone.utc)


def digest(value: Any) -> str:
    """Exact content-addressed reference for plain, schema-checked artifacts."""
    return sha256(json.dumps(asdict(value), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CitationRecord:
    source_id: str
    url: str
    kind: str  # 'official' or 'independent'
    checked_at_utc: str
    checked_by: str  # recorded claimed reviewer, not validated identity

    def validate(self, *, now: datetime) -> str:
        if not re.fullmatch(r"src_[a-z0-9_]{2,40}", self.source_id):
            raise WorkflowError("Invalid source identifier")
        if self.kind not in ("official", "independent"):
            raise WorkflowError("Unclassified research evidence")
        _required(self.checked_by, 3)
        checked = _stamp(self.checked_at_utc)
        current = now.astimezone(timezone.utc)
        if not timedelta(0) <= current-checked <= timedelta(days=7):
            raise WorkflowError("Research evidence stale or future-dated")
        return _https_source(self.url)


@dataclass(frozen=True)
class SupportedClaim:
    claim_id: str
    statement: str
    source_ids: tuple[str, ...]

    def validate(self) -> None:
        if not re.fullmatch(r"c_[a-z0-9_]{2,40}", self.claim_id):
            raise WorkflowError("Invalid claim identifier")
        _required(self.statement, 15)
        if not self.source_ids or len(self.source_ids) > 5:
            raise WorkflowError("Claim lacks bounded source references")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise WorkflowError("Duplicate claim references")


@dataclass(frozen=True)
class ResearchPackage:
    episode_id: str
    topic: str
    viewer_problem: str
    demonstration: str
    sources: tuple[CitationRecord, ...]
    claims: tuple[SupportedClaim, ...]
    from_feed_only: bool = False

    def validate(self, *, now: datetime) -> None:
        for value in (self.topic, self.viewer_problem, self.demonstration):
            _required(value, 25)
        if self.from_feed_only:
            raise WorkflowError("Unverified RSS lead cannot become a research package")
        if not 2 <= len(self.sources) <= 12 or not 1 <= len(self.claims) <= 16:
            raise WorkflowError("Evidence or claims missing")
        source_ids = [x.source_id for x in self.sources]
        if len(set(source_ids)) != len(source_ids):
            raise WorkflowError("Duplicate research source identifiers")
        domains: dict[str, set[str]] = {"official": set(), "independent": set()}
        for source in self.sources:
            domains[source.kind].add(source.validate(now=now))
        if (not domains["official"] or not domains["independent"]
                or len(domains["official"] | domains["independent"]) < 2):
            raise WorkflowError("Independent and official domains required")
        claim_ids = [x.claim_id for x in self.claims]
        if len(set(claim_ids)) != len(claim_ids):
            raise WorkflowError("Duplicate claim identifier")
        for claim in self.claims:
            claim.validate()
            if not set(claim.source_ids) <= set(source_ids):
                raise WorkflowError("Claim references unknown source")
            if not any(x.source_id in claim.source_ids and x.kind == "official"
                       for x in self.sources):
                raise WorkflowError("Each claim requires an official reference")


@dataclass(frozen=True)
class FactReview:
    episode_id: str
    research_digest: str
    reviewer_role: str
    reviewed_claim_ids: tuple[str, ...]
    verdict: str  # independent role attestation; NEVER automatic truth finding
    review_notes: str

    def validate(self, research: ResearchPackage) -> None:
        if self.research_digest != digest(research):
            raise WorkflowError("Stale or wrong research review")
        if self.reviewer_role != "quality.fact_reviewer":
            raise WorkflowError("Only independent fact reviewer may attest")
        if self.verdict != "ATTESTED_FOR_DRAFT":
            raise WorkflowError("Research review rejected or incomplete")
        if (len(set(self.reviewed_claim_ids)) != len(self.reviewed_claim_ids)
                or set(self.reviewed_claim_ids) != {c.claim_id for c in research.claims}):
            raise WorkflowError("All source-backed claims require review")
        _required(self.review_notes, 20)


@dataclass(frozen=True)
class CreativeScript:
    episode_id: str
    research_digest: str
    fact_review_digest: str
    title: str
    opening: str
    steps: tuple[str, ...]
    viewer_payoff: str
    used_claim_ids: tuple[str, ...]
    original_demo: str

    def validate(self, research: ResearchPackage, review: FactReview) -> None:
        if self.research_digest != digest(research) or self.fact_review_digest != digest(review):
            raise WorkflowError("Script does not match reviewed research")
        for value in (self.title, self.opening, self.viewer_payoff, self.original_demo):
            _required(value, 12)
        if not 2 <= len(self.steps) <= 30:
            raise WorkflowError("Reproducible demonstration needs two or more steps")
        for step in self.steps:
            _required(step, 12)
        if not self.used_claim_ids or len(set(self.used_claim_ids)) != len(self.used_claim_ids):
            raise WorkflowError("Script claims missing or duplicated")
        if not set(self.used_claim_ids) <= set(review.reviewed_claim_ids):
            raise WorkflowError("Unreviewed script claim")
        if self.original_demo != research.demonstration:
            raise WorkflowError("Demonstration changed without research review")


@dataclass(frozen=True)
class HookVariants:
    episode_id: str
    fact_review_digest: str
    options: tuple[str, ...]
    promised_claim_ids: tuple[str, ...]

    def validate(self, review: FactReview) -> None:
        if self.fact_review_digest != digest(review):
            raise WorkflowError("Hook not based on reviewed claims")
        if not 1 <= len(self.options) <= 4:
            raise WorkflowError("Hook alternatives missing")
        for hook in self.options:
            _required(hook, 12)
        if len(set(self.options)) != len(self.options):
            raise WorkflowError("Duplicate hook alternative")
        if not self.promised_claim_ids or not set(self.promised_claim_ids) <= set(review.reviewed_claim_ids):
            raise WorkflowError("Unverified promise in hook")


@dataclass(frozen=True)
class LocalizedDraft:
    episode_id: str
    script_digest: str
    language: str
    narrated_text: str
    subtitle_draft: tuple[str, ...]
    terminology_notes: str
    translator_role: str
    label: str = "DRAFT_UNREVIEWED_LANGUAGE"

    def validate(self, script: CreativeScript, *, stage: str) -> None:
        expected = {"english": ("en", "language.english_editor"),
                    "hindi": ("hi", "language.hindi_editor")}
        if stage not in expected or (self.language, self.translator_role) != expected[stage]:
            raise WorkflowError("Wrong localized draft role or language")
        if self.script_digest != digest(script):
            raise WorkflowError("Localization based on stale creative script")
        if self.label != "DRAFT_UNREVIEWED_LANGUAGE":
            raise WorkflowError("Language reviewer cannot be impersonated by translator")
        _required(self.narrated_text, 45)
        if not 2 <= len(self.subtitle_draft) <= 60:
            raise WorkflowError("Subtitle segments missing")
        for item in self.subtitle_draft:
            _required(item, 6)
        _required(self.terminology_notes, 10)



@dataclass(frozen=True)
class LanguageReview:
    episode_id: str
    english_digest: str
    hindi_digest: str
    reviewer_role: str
    verdict: str
    review_notes: str

    def validate(self, english: LocalizedDraft, hindi: LocalizedDraft) -> None:
        if self.english_digest != digest(english) or self.hindi_digest != digest(hindi):
            raise WorkflowError("Language review does not match both current drafts")
        if self.reviewer_role != "language.language_reviewer":
            raise WorkflowError("Only the designated independent language reviewer may attest")
        if self.verdict != "ATTESTED_FOR_DRAFT":
            raise WorkflowError("Language review rejected or incomplete")
        _required(self.review_notes, 30)


STAGES: dict[str, type] = {
    "research": ResearchPackage,
    "fact_review": FactReview,
    "script": CreativeScript,
    "hooks": HookVariants,
    "english": LocalizedDraft,
    "hindi": LocalizedDraft,
    "language_review": LanguageReview
}

class Phase2Coordinator:
    """Accepts submitted artifacts and marks only seven DRAFT DAG steps complete.

    There is deliberately no local LLM generation, truth-validation oracle,
    video rendering, cloud publication, or language QA auto-approval.
    """

    def __init__(self, episode_id: str, *, kind: str, language: str,
                 now: datetime | None = None):
        self.workflow = episode_workflow(episode_id, kind=kind, language=language)
        self.now = now or datetime.now(timezone.utc)
        if self.now.tzinfo is None:
            raise WorkflowError("Explicit clock must be timezone aware")
        self.episode_id = episode_id
        self.kind = kind
        self.language = language
        self.artifacts: dict[str, object] = {}

    def submit(self, stage: str, artifact: object, *, actor: str) -> str:
        if stage not in STAGES or type(artifact) is not STAGES[stage]:
            raise WorkflowError("Unexpected phase-two artifact")
        task_id = f"{self.episode_id.lower()}:{stage}"
        contract = self.workflow.contracts[task_id]
        if actor != contract.owner or getattr(artifact, "episode_id", None) != self.episode_id:
            raise WorkflowError("Unauthorized role or episode mismatch")
        if self.workflow.runs[task_id].status != State.READY:
            raise WorkflowError("Dependencies unresolved; no handoff accepted")
        research = self.artifacts.get("research")
        review = self.artifacts.get("fact_review")
        script = self.artifacts.get("script")
        if stage == "research":
            artifact.validate(now=self.now)
            source_refs = tuple("sha256:" + digest(x) for x in artifact.sources)
        elif stage == "fact_review":
            artifact.validate(research)
            source_refs = ("sha256:" + digest(research),)
        elif stage == "script":
            artifact.validate(research, review)
            source_refs = ("sha256:" + digest(review),)
        elif stage == "hooks":
            artifact.validate(review)
            source_refs = ("sha256:" + digest(review),)
        elif stage == "language_review":
            english = self.artifacts.get("english")
            hindi = self.artifacts.get("hindi")
            artifact.validate(english, hindi)
            source_refs = ("sha256:" + digest(english), "sha256:" + digest(hindi))
        else:
            artifact.validate(script, stage=stage)
            source_refs = ("sha256:" + digest(script),)
        result_hash = digest(artifact)
        handoff = Handoff(task_id=task_id,artifact_type=contract.produces,
                          sha256_hex=result_hash,evidence_refs=source_refs,
                          produced_by=actor, recorded_at_utc=self.now.isoformat())
        # No side effects beyond the pure in-memory deterministic staging DAG.
        self.workflow.claim(task_id, actor=actor)
        self.workflow.complete(handoff, actor=actor)
        self.artifacts[stage] = artifact
        return result_hash

    def progress(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "completed_stages": tuple(x for x in STAGES
                                      if x in self.artifacts),
            "next_tasks": tuple(self.workflow.ready()),
            "research_factually_verified_by_external_system": False,
            "language_review_recorded_for_staging": "language_review" in self.artifacts,
            "language_independently_reviewed": False,
            "publishing_authorized": False,
            "publishing_enabled": False,
            "cloud_deployed": False
        }
