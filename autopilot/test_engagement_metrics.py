import unittest
from dataclasses import replace
from autopilot.engagement_metrics import Observation,rates,comparable_cohort
def data(i=0):
 return Observation('video_'+str(i),'short','AI tutorials',72,400,300,12,6,3,2,80.0,'official_api')
class MetricsTests(unittest.TestCase):
 def test_rates_calculated_from_engaged_only(self):
  r=rates(data());self.assertEqual(r['likes_per_1000_engaged'],40)
  self.assertEqual(r['comments_per_1000_engaged'],20)
  self.assertEqual(r['shares_per_1000_engaged'],10)
 def test_missing_metric_never_invented(self):
  r=rates(replace(data(),shares=None));self.assertIsNone(r['shares_per_1000_engaged'])
 def test_zero_engagement_no_divide_by_zero(self):
  r=rates(replace(data(),engaged_views=0));self.assertIsNone(r['likes_per_1000_engaged'])
 def test_missing_engaged_no_derived_data(self):
  r=rates(replace(data(),engaged_views=None));self.assertIsNone(r['subscribers_gained_per_1000_engaged'])
 def test_ghost_engaged_rejected(self):
  with self.assertRaises(ValueError):rates(replace(data(),engaged_views=600))
 def test_negative_engagement_rejected(self):
  with self.assertRaises(ValueError):rates(replace(data(),comments=-1))
 def test_manual_not_entered_as_official_cohort(self):
  items=[replace(data(i),source='manual_observation') for i in range(10)]
  self.assertEqual(comparable_cohort(items,kind='short')['status'],'INSUFFICIENT_AUTHENTIC_DATA')
 def test_age_matched_threshold(self):
  items=[data(i) for i in range(6)]
  self.assertEqual(comparable_cohort(items,kind='short')['status'],'BASELINE_ONLY_NOT_CAUSAL')
  self.assertEqual(comparable_cohort(items,kind='long')['status'],'INSUFFICIENT_AUTHENTIC_DATA')
 def test_baseline_is_not_improvement_claim(self):
  report=comparable_cohort([data(i) for i in range(6)],kind='short')
  self.assertIsNone(report['estimated_improvement']);self.assertEqual(report['median_engaged_views'],300)
if __name__=='__main__':unittest.main()
