import unittest
from datetime import date,timedelta
from dataclasses import replace
from autopilot.editorial_gate import ResearchEvidence,LicensedAsset,Lesson,verify_lesson
DAY=date(2026,10,17)
def good():
    return Lesson(
        'Build a Python data cleaning workflow','short','beginner',
        'Viewers will reproduce a working CSV cleanup with clear step by step instructions',
        ('Create a sample CSV file with missing values','Run the documented pandas cleanup and inspect output'),
        (ResearchEvidence('https://pandas.pydata.org/docs/',DAY,True,True),
         ResearchEvidence('https://realpython.com/python-data-cleaning-numpy-pandas/',DAY,False,True)),
        (LicensedAsset('screen_capture','original demo','owned',True,True),
         LicensedAsset('voice','original narration','owned',True,True)),
        1.0,True,True,False,False,'energetic',True,True)
class EditorialGateTests(unittest.TestCase):
    def assert_blocked(self,lesson,expected):
        result=verify_lesson(lesson,reviewed_on=DAY)
        self.assertEqual(result.status,'BLOCKED_REVIEW')
        self.assertIn(expected,result.reasons)
        self.assertFalse(result.publishing_enabled)
    def test_valid_preproduction_not_upload(self):
        r=verify_lesson(good(),reviewed_on=DAY)
        self.assertEqual(r.status,'PASS_FOR_RENDER_ONLY');self.assertFalse(r.publishing_enabled)
    def test_invalid_course_steps(self):
        self.assert_blocked(replace(good(),steps=('Do it',)),'MISSING_REPRODUCIBLE_STEPS')
    def test_stale_product_features(self):
        e=list(good().sources)
        e[0]=replace(e[0],checked_on=DAY-timedelta(days=15))
        self.assert_blocked(replace(good(),sources=tuple(e)),'STALE_RESEARCH')
    def test_missing_independent_source(self):
        self.assert_blocked(replace(good(),sources=(good().sources[0],)),'INSUFFICIENT_INDEPENDENT_EVIDENCE')
    def test_rights_unverified(self):
        self.assert_blocked(replace(good(),assets=(replace(good().assets[0],commercial_use_verified=False),)),'ASSET_RIGHTS_NOT_VERIFIED')
    def test_fake_ui_requires_label(self):
        self.assert_blocked(replace(good(),real_interface_capture=False,simulated_interface=True),'UNLABELED_SIMULATED_UI')
    def test_reconstruction_clearly_labelable(self):
        r=verify_lesson(replace(good(),real_interface_capture=False,simulated_interface=True,simulation_disclosed=True),reviewed_on=DAY)
        self.assertEqual(r.status,'PASS_FOR_RENDER_ONLY')
    def test_unverified_real_demo(self):
        self.assert_blocked(replace(good(),practical_demonstration=False),'NO_REAL_DEMONSTRATION')
    def test_transaction_without_approval(self):
        self.assert_blocked(replace(good(),transactions_completed=True),'UNAUTHORIZED_TRANSACTION_CLAIM')
    def test_missing_captions(self):
        self.assert_blocked(replace(good(),captions_checked=False),'CAPTION_OR_PRIVACY_QA_MISSING')
    def test_voice_profile(self):
        self.assert_blocked(replace(good(),voice_profile='unknown'),'VOICE_PROFILE_UNVERIFIED')
    def test_no_asset_license(self):
        self.assert_blocked(replace(good(),assets=()),'NO_LICENSED_ASSET_RECORDS')
    def test_non_https_source(self):
        a=list(good().sources);a[1]=replace(a[1],url='http://127.0.0.1/private')
        self.assert_blocked(replace(good(),sources=tuple(a)),'UNVERIFIED_RESEARCH_SOURCE')
    def test_future_research_date(self):
        a=list(good().sources);a[1]=replace(a[1],checked_on=DAY+timedelta(days=1))
        self.assert_blocked(replace(good(),sources=tuple(a)),'STALE_RESEARCH')
if __name__=='__main__':unittest.main()
