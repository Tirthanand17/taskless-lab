import unittest
from datetime import date,timedelta
from autopilot.calendar import PublishingCalendar,DayRule,CalendarError

TODAY=date(2026,10,17)
class TestAdaptiveCalendar(unittest.TestCase):
    def test_default_daily_three(self):
        c=PublishingCalendar();a=c.plan(TODAY)
        self.assertEqual((len(a),[x.kind for x in a]),(3,['short','long','short']))
        self.assertEqual([x.planned_utc for x in a],['2026-10-17T05:30:00+00:00','2026-10-17T10:30:00+00:00','2026-10-17T15:00:00+00:00'])
        self.assertEqual([x.voice for x in a if x.kind=='short'],['energetic','explanatory'])
        self.assertTrue(all(x.status.startswith('DRAFT_') for x in a))
    def test_tomorrow_6_and_3(self):
        c=PublishingCalendar();self.assertIn('RECORDED',c.apply('Tomorrow upload 6 Shorts and 3 long videos.',today=TODAY))
        a=c.plan(TODAY+timedelta(days=1));self.assertEqual((len(a),sum(x.kind=='short' for x in a)),(9,6))
        self.assertEqual(len({x.planned_utc for x in a}),9)
        self.assertEqual(len(c.plan(TODAY+timedelta(days=2))),3)
    def test_weekend_increase(self):
        c=PublishingCalendar();c.apply('Every weekend upload 4 Shorts and 2 long videos.',today=TODAY)
        self.assertEqual(len(c.plan(TODAY)),6);self.assertEqual(len(c.plan(date(2026,10,19))),3)
    def test_seven_day_override_expires(self):
        c=PublishingCalendar();c.apply('For the next seven days upload 3 Shorts and 2 long videos.',today=TODAY)
        self.assertEqual(len(c.plan(TODAY+timedelta(days=6))),5)
        self.assertEqual(len(c.plan(TODAY+timedelta(days=7))),3)
    def test_one_extra_short(self):
        c=PublishingCalendar();c.apply('Publish an extra Short today.',today=TODAY)
        self.assertEqual(len(c.plan(TODAY)),4)
    def test_pause_looks_only_tomorrow(self):
        c=PublishingCalendar();c.apply('Pause all videos tomorrow.',today=TODAY)
        self.assertEqual(c.plan(TODAY+timedelta(days=1)),[])
        self.assertEqual(len(c.plan(TODAY+timedelta(days=2))),3)
    def test_only_ai_tutorials_this_weekend(self):
        c=PublishingCalendar();c.apply('Make only AI tutorials this weekend.',today=TODAY)
        self.assertEqual({x.category for x in c.plan(TODAY)}, {'AI tutorials'})
        self.assertEqual({x.category for x in c.plan(date(2026,10,19))}, {None})
    def test_normal_reset(self):
        c=PublishingCalendar();c.apply('Every weekend upload 4 Shorts and 2 long videos.',today=TODAY)
        c.apply('Return to the normal schedule.',today=TODAY)
        self.assertEqual(len(c.plan(TODAY)),3)
    def test_conflict_does_not_modify(self):
        c=PublishingCalendar();c.apply('Pause all videos tomorrow.',today=TODAY)
        with self.assertRaises(CalendarError):c.apply('Tomorrow upload 6 Shorts and 3 long videos.',today=TODAY)
        self.assertEqual(c.plan(TODAY+timedelta(days=1)),[])
    def test_unknown_and_excessive_fail_closed(self):
        c=PublishingCalendar()
        for command in ['Set 25 shorts tomorrow','Tomorrow upload 25 Shorts and 3 long videos','Buy subscribers']:
            with self.assertRaises(CalendarError):c.apply(command,today=TODAY)
        self.assertEqual(c.overrides,[])
    def test_collision_with_existing_release_blocks(self):
        c=PublishingCalendar();day=TODAY
        reserved=c.plan(day)[0].planned_utc
        with self.assertRaises(CalendarError):c.plan(day,reserved_utc=(reserved,))
    def test_18_slot_limit_and_duplicate_utc(self):
        c=PublishingCalendar(default=DayRule(12,6))
        slots=c.plan(TODAY)
        self.assertEqual(len(slots),18)
        self.assertEqual(len({s.planned_utc for s in slots}),18)
    def test_no_publishing_flags_in_preview(self):
        c=PublishingCalendar();self.assertFalse(hasattr(c,'publish'))
        self.assertTrue(all(s.status=='DRAFT_ONLY_NO_PUBLISH_PERMISSION' for s in c.plan(TODAY)))
if __name__=='__main__':unittest.main()
