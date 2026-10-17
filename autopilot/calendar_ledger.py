"""Bridge adaptive DRAFT calendar to atomic local release reservations.

The bridge never contacts YouTube and never marks any video uploaded/published.
The caller must provide a RECENT authorized YouTube release-slot snapshot and
full media/topic QA metadata. Snapshot attestations are an interface contract;
deployment must independently bind them to the authenticated API adapter.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Mapping
from .calendar import PublishingCalendar, Slot
from .core import CHANNEL_ID, GateError, MediaQA, ReleaseLedger, Topic

@dataclass(frozen=True)
class AuthorizedSnapshot:
    channel: str
    checked_utc: str
    occupied_utc: tuple[str,...]
    source: str

    def validate(self, *, now: datetime) -> None:
        if self.channel != CHANNEL_ID or self.source != 'authenticated_youtube_api':
            raise GateError('Authenticated expected-channel snapshot required')
        try:
            checked = datetime.fromisoformat(self.checked_utc)
        except (ValueError, TypeError) as exc:
            raise GateError('Invalid snapshot timestamp') from exc
        if checked.tzinfo is None or now.tzinfo is None:
            raise GateError('Timezone-aware snapshot and clock required')
        elapsed = now.astimezone(timezone.utc)-checked.astimezone(timezone.utc)
        if elapsed < timedelta(0) or elapsed > timedelta(minutes=10):
            raise GateError('Stale or future-dated channel snapshot')
        for utc in self.occupied_utc:
            try:
                instant = datetime.fromisoformat(utc)
            except (ValueError, TypeError) as exc:
                raise GateError('Invalid reserved UTC') from exc
            if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
                raise GateError('Snapshot release timestamp must be UTC')

@dataclass(frozen=True)
class PreparedEpisode:
    episode: str
    sha256: str
    topic: Topic
    qa: MediaQA

def commit_calendar_drafts(*, calendar: PublishingCalendar, day: date,
                           prepared: Mapping[tuple[str,int],PreparedEpisode],
                           snapshot: AuthorizedSnapshot, ledger: ReleaseLedger,
                           now: datetime, recent_titles: tuple[str,...] = ()) -> dict[str,bool]:
    """Atomically reserve PREPARED and QA-validated media locally only.

    Reservation is neither publication authorization nor proof of a YouTube
    upload. Existing schedules and ledger rows are immutable. No partial
    release reservations if any video in the batch conflicts or fails QA.
    """
    snapshot.validate(now=now)
    slots: list[Slot] = calendar.plan(day,reserved_utc=snapshot.occupied_utc)
    expected = {(item.kind,item.ordinal) for item in slots}
    if not expected:
        raise GateError('Paused day: no video reservations permitted')
    if set(prepared)!=expected:
        raise GateError('Every draft slot requires one distinct prepared episode')
    entries = []
    titles = list(recent_titles)
    for slot in slots:
        video = prepared[(slot.kind,slot.ordinal)]
        video.topic.validate(tuple(titles))
        titles.append(video.topic.title)
        video.qa.validate(slot.kind)
        if video.sha256 != video.qa.sha256:
            raise GateError('Prepared media hash mismatch')
        entries.append((video.episode,slot.kind,slot.planned_utc,video.sha256))
    return ledger.reserve_prepared_batch(entries,now=now)
