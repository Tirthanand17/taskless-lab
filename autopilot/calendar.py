"""Deterministic FlowMinute publishing calendar; planning only, NEVER uploads.

Respects Asia/Kolkata, temporary overrides and existing release reservations.
User commands here are parsed offline. Changes are not applied to cloud resources.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re

IST = ZoneInfo('Asia/Kolkata')
MAX_SHORTS, MAX_LONGS = 12, 6
WORDS = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,
         'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12}

class CalendarError(ValueError):
    pass

@dataclass(frozen=True)
class DayRule:
    shorts: int = 2
    longs: int = 1
    category: str | None = None
    def __post_init__(self):
        if type(self.shorts) is not int or type(self.longs) is not int or not (0 <= self.shorts <= MAX_SHORTS and 0 <= self.longs <= MAX_LONGS):
            raise CalendarError('Unverified or excessive daily release count')
        if self.shorts+self.longs > 18:
            raise CalendarError('Insufficient daily planning capacity')
        if self.category not in (None, 'AI tutorials'):
            raise CalendarError('Unsupported category filter')

@dataclass(frozen=True)
class Override:
    start: date
    end: date
    rule: DayRule
    kind: str = 'exact'
    def __post_init__(self):
        if self.end < self.start or self.kind not in ('exact','category'):
            raise CalendarError('Invalid temporary override')
    def matches(self, day: date) -> bool:
        return self.start <= day <= self.end

@dataclass(frozen=True)
class Slot:
    day: str
    kind: str
    ordinal: int
    planned_utc: str
    voice: str | None
    category: str | None
    status: str = 'DRAFT_ONLY_NO_PUBLISH_PERMISSION'

@dataclass
class PublishingCalendar:
    default: DayRule = field(default_factory=DayRule)
    weekend: DayRule | None = None
    overrides: list[Override] = field(default_factory=list)

    def effective(self, day: date) -> DayRule:
        rule = self.weekend if day.weekday() >= 5 and self.weekend is not None else self.default
        for override in self.overrides:
            if override.matches(day):
                if override.kind == 'category':
                    rule = DayRule(rule.shorts, rule.longs, override.rule.category)
                else:
                    rule = override.rule
        return rule

    def apply(self, command: str, *, today: date) -> str:
        """Apply a single EXACTLY recognized user command, atomically.

        Unknown text is rejected rather than guessed. This is an offline local
        configuration preview; it cannot authorize live cloud changes.
        """
        if not isinstance(today,date) or isinstance(today,datetime):
            raise CalendarError('Explicit local calendar date required')
        clean = ' '.join(command.lower().strip().rstrip('.!').split())
        if clean == 'return to the normal schedule':
            self.weekend = None
            self.overrides = []
            return 'DEFAULT_RESTORED_FUTURE_PLANS_ONLY'
        if clean == 'publish an extra short today':
            now = self.effective(today)
            new = Override(today,today,DayRule(now.shorts+1,now.longs,now.category))
        elif clean == 'pause all videos tomorrow':
            day = today+timedelta(days=1)
            new = Override(day,day,DayRule(0,0))
        elif clean == 'make only ai tutorials this weekend':
            saturday = today+timedelta(days=(5-today.weekday())%7)
            new = Override(saturday,saturday+timedelta(days=1),DayRule(category='AI tutorials'),kind='category')
        else:
            n = r'(\d{1,2}|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)'
            suffix = rf'{n} shorts? and {n} long videos?'
            tomorrow = re.fullmatch(rf'tomorrow upload {suffix}',clean)
            weekend = re.fullmatch(rf'every weekend upload {suffix}',clean)
            next_days = re.fullmatch(rf'for the next {n} days? upload {suffix}',clean)
            if tomorrow:
                sh,lo = _count(tomorrow[1]),_count(tomorrow[2])
                day = today+timedelta(days=1)
                new = Override(day,day,DayRule(sh,lo))
            elif weekend:
                sh,lo = _count(weekend[1]),_count(weekend[2])
                self.weekend = DayRule(sh,lo)
                return 'WEEKEND_RULE_UPDATED_FUTURE_PLANS_ONLY'
            elif next_days:
                days,sh,lo = _count(next_days[1]),_count(next_days[2]),_count(next_days[3])
                if not 1 <= days <= 31:
                    raise CalendarError('Temporary duration must be 1..31 days')
                new = Override(today,today+timedelta(days=days-1),DayRule(sh,lo))
            else:
                raise CalendarError('Unsupported command; no setting changed')
        if any(new.start <= x.end and x.start <= new.end for x in self.overrides):
            raise CalendarError('Overlapping temporary overrides; no setting changed')
        self.overrides.append(new)
        return 'TEMPORARY_RULE_RECORDED_NO_PUBLISH_PERMISSION'

    def plan(self, day: date, *, reserved_utc: tuple[str,...] = ()) -> list[Slot]:
        """Produce draft slots; conflicting authenticated reservations stop plans.

        Existing YouTube schedules are inputs; this method never changes them.
        """
        if not isinstance(day,date) or isinstance(day,datetime):
            raise CalendarError('Date required')
        rule = self.effective(day)
        anchors: list[tuple[int,str,int]] = []
        if rule.shorts:
            anchors.append((11*60,'short',1))
        if rule.longs:
            anchors.append((16*60,'long',1))
        if rule.shorts>=2:
            anchors.append((20*60+30,'short',2))
        available = [t for t in range(9*60,23*60,30) if t not in {x[0] for x in anchors}]
        for kind,start,count in (('short',3,rule.shorts),('long',2,rule.longs)):
            for ordinal in range(start,count+1):
                if not available: raise CalendarError('No available draft slot')
                # Deterministic stagger without claiming it is analytics-optimized.
                desired = (12*60 if kind=='short' else 17*60)+(ordinal-start)*90
                minute = min(available,key=lambda x:(abs(x-desired),x))
                available.remove(minute)
                anchors.append((minute,kind,ordinal))
        output=[]
        for minute,kind,ordinal in sorted(anchors):
            time=datetime(day.year,day.month,day.day,minute//60,minute%60,tzinfo=IST).astimezone(timezone.utc).isoformat()
            if time in reserved_utc:
                raise CalendarError('Existing release already occupies proposed UTC slot')
            output.append(Slot(day.isoformat(),kind,ordinal,time,
                               ('energetic' if ordinal%2 else 'explanatory') if kind=='short' else 'explanatory',rule.category))
        return output

def _count(value: str) -> int:
    return WORDS.get(value,int(value)) if value.isdigit() else WORDS[value]
