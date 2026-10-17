"""CLI preview for safe user-driven schedule proposals (never deploys)."""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import date,timedelta
import json
from autopilot.calendar import PublishingCalendar,CalendarError

def build_preview(today: date, days: int, commands: tuple[str,...] = ()) -> dict:
    if not 1 <= days <= 31:
        raise CalendarError('Preview horizon must be 1..31 days')
    calendar=PublishingCalendar()
    for command in commands:
        calendar.apply(command,today=today)
    items=[asdict(slot) for offset in range(days) for slot in calendar.plan(today+timedelta(days=offset))]
    return {'status':'DRAFT_ONLY_NO_PUBLISH_PERMISSION', 'timezone':'Asia/Kolkata',
            'days':days,'shorts_planned':sum(x['kind']=='short' for x in items),
            'longs_planned':sum(x['kind']=='long' for x in items),
            'slots':items,'youtube_uploads_attempted':0,'releases_modified':0,
            'requires_live_authorization_and_media_QA':True}

def main() -> None:
    p=argparse.ArgumentParser(description='FlowMinute dry-run ONLY; no network or uploads')
    p.add_argument('--date',required=True,help='YYYY-MM-DD local Asia/Kolkata')
    p.add_argument('--days',type=int,default=30)
    p.add_argument('--command',action='append',default=[])
    a=p.parse_args()
    report=build_preview(date.fromisoformat(a.date),a.days,tuple(a.command))
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=='__main__':main()
