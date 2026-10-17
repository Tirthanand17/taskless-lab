import unittest
from dataclasses import replace
from datetime import datetime,timezone,timedelta
from autopilot.launch_gate import Launch,Citation,check_launch
NOW=datetime(2026,10,17,12,tzinfo=timezone.utc)
def good():
 return Launch('New AI tool feature demonstrated', NOW-timedelta(hours=3),NOW-timedelta(hours=2),
  (Citation('https://openai.com/index/new',True,True,True),Citation('https://www.theverge.com/news/example',False,True,True)),
  'People need a stepwise reproducible example for this feature',True,True,
  'Reproduce the feature on a dummy spreadsheet and verify outputs',True,True)
class LaunchGateTests(unittest.TestCase):
 def assert_blocked(self,obj,reason):
  result=check_launch(obj,now=NOW)
  self.assertEqual(result.state,'BLOCKED_UNVERIFIED');self.assertIn(reason,result.reasons)
  self.assertFalse(result.upload_authorized)
 def test_same_day_priority_no_publish(self):
  r=check_launch(good(),now=NOW);self.assertEqual((r.state,r.review_priority,r.upload_authorized),('READY_FOR_EDITORIAL_REVIEW',1,False))
 def test_unconfirmed_rss_not_evidence(self):
  self.assert_blocked(replace(good(),citations=(replace(good().citations[0],reviewed=False),)), 'MISSING_OFFICIAL_AND_INDEPENDENT_EVIDENCE')
 def test_no_independent_review(self):
  self.assert_blocked(replace(good(),citations=(good().citations[0],)), 'MISSING_OFFICIAL_AND_INDEPENDENT_EVIDENCE')
 def test_no_release_date(self):
  self.assert_blocked(replace(good(),released_at=None),'RELEASE_OR_ACCESS_NOT_CONFIRMED')
 def test_unverified_price_or_location(self):
  self.assert_blocked(replace(good(),pricing_confirmed=False),'AVAILABILITY_UNCONFIRMED')
 def test_no_real_demo(self):
  self.assert_blocked(replace(good(),demonstration_possible=False),'NO_ORIGINAL_DEMONSTRATION')
 def test_duplicate_topic(self):
  r=check_launch(good(),now=NOW,prior_titles=(good().title,));self.assertIn('DUPLICATE_EXISTING_STORY',r.reasons)
 def test_bad_url(self):
  c=list(good().citations);c[1]=replace(c[1],url='http://local.invalid/news')
  self.assert_blocked(replace(good(),citations=tuple(c)),'CITATION_NOT_VERIFIED')
 def test_future_announcement(self):
  self.assert_blocked(replace(good(),announced_at=NOW+timedelta(minutes=1)),'UNVERIFIED_ANNOUNCEMENT_DATE')
 def test_research_age_review_priority(self):
  x=replace(good(),announced_at=NOW-timedelta(hours=49))
  self.assertEqual(check_launch(x,now=NOW).review_priority,2)
if __name__=='__main__':unittest.main()
