import unittest
from datetime import date
from autopilot.preview_calendar import build_preview
from autopilot.calendar import CalendarError
class TestPreview(unittest.TestCase):
 def test_month_is_60_shorts_30_longs_no_upload(self):
  p=build_preview(date(2026,10,17),30)
  self.assertEqual((p['shorts_planned'],p['longs_planned']),(60,30))
  self.assertEqual(p['youtube_uploads_attempted'],0)
  self.assertEqual(len(p['slots']),90)
 def test_override_6_shorts_3_long(self):
  p=build_preview(date(2026,10,17),2,('Tomorrow upload 6 Shorts and 3 long videos',))
  self.assertEqual((p['shorts_planned'],p['longs_planned']),(8,4))
 def test_invalid_calendar_request_no_cloud_action(self):
  with self.assertRaises(CalendarError):build_preview(date(2026,10,17),32)
if __name__=='__main__':unittest.main()
