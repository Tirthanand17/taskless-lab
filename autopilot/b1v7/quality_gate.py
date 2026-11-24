"""B1v7 editorial preflight. Verifies declared scene plan and local evidence hashes.
Does not infer subjective quality, licensing, comprehension or human review from a JSON flag.
Run before any new assisted release; existing scheduled videos are untouched.
"""
from pathlib import Path
import argparse, hashlib, json, math, re, tempfile, unittest

ALLOWED={'capture','real_footage','diagram','typography','comparison'}
EVIDENCE={'capture','real_footage'}
REQUIRED_REVIEW=('first_frame_hook','one_clear_promise','plain_language','explanation_matches_visual','mobile_legibility','varied_compositions','meaningful_motion','audio_balance','factual_accuracy','rights','thumbnail_matches_promise','complete_playback')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def artifact(root, entry):
    if not isinstance(entry,dict) or not isinstance(entry.get('path'),str):return False
    p=(root/entry['path']).resolve()
    return p.is_relative_to(root.resolve()) and p.is_file() and sha(p)==entry.get('sha256')
def check(doc,root,release=False):
    errors=[]
    def need(x,msg):
        if not x:errors.append(msg)
    def num(x):return type(x) in (int,float) and math.isfinite(x)
    need(doc.get('format') in ('short','long'),'format invalid')
    for k in ('audience','promise','practical_takeaway','topic_evidence','hook_variant','title','thumbnail_concept'):
        need(isinstance(doc.get(k),str) and bool(doc[k].strip()),'missing '+k)
    need(doc.get('hook_variant') in ('result_first','problem_first'),'unsupported hook variant')
    need(doc.get('research_sources') and all(isinstance(x,str) and x.startswith('https://') for x in doc.get('research_sources',[])),'missing research source')
    ss=doc.get('scenes',[])
    if not isinstance(ss,list) or len(ss)<3:return errors+['at least three semantic scenes required']
    end=0; kinds=set(); layouts=set(); proof_time=0; real_seconds=0
    for i,s in enumerate(ss):
        label=f'scene {i+1}'
        if not isinstance(s,dict):errors.append(label+' invalid');continue
        a=s.get('start');b=s.get('end')
        if not num(a) or not num(b) or b<=a or abs(a-end)>.1:
            errors.append(label+' invalid or non-contiguous timing');continue
        end=b
        k=s.get('visual_kind')
        need(k in ALLOWED,label+' visual kind invalid')
        kinds.add(k);layouts.add(s.get('layout'))
        for field in ('spoken','visual_action','learning_purpose','layout','focal_label'):
            need(isinstance(s.get(field),str) and bool(s[field].strip()),label+' missing '+field)
        if k in EVIDENCE:
            need(artifact(root,s.get('evidence')),label+' missing/altered evidence')
            real_seconds+=b-a
        if s.get('shows_result') is True and proof_time==0:proof_time=b
        need(s.get('motion') in ('actual_action','annotation','comparison_reveal','hold_for_reading','none'),label+' motion not described')
        need(s.get('role') in ('hook','setup','action','result','takeaway','explanation'),label+' unknown role')
        need(s.get('visual_action') not in ('generic stock','logo intro','decorative zoom'),label+' no semantic demonstration')
    first=ss[0] if isinstance(ss[0],dict) else {}
    need(first.get('role')=='hook','first scene is not hook')
    need(first.get('shows_result') is True or first.get('shows_problem') is True,'opening must visibly show a result or problem')
    need(first.get('intro_logo') is False,'logo intro prohibited')
    need(num(first.get('evidence_visible_at')) and first['evidence_visible_at']<=1,'evidence not visible in first second')
    need(any(isinstance(s,dict) and s.get('role')=='result' for s in ss),'no explicit result')
    need(any(isinstance(s,dict) and s.get('role')=='takeaway' for s in ss),'no practical takeaway')
    need(len(layouts-{None,''})>=3,'fewer than three scene compositions')
    need(real_seconds>=end*.45,'insufficient genuine evidence time (internal design floor, not ranking rule)')
    need(artifact(root,doc.get('proof')),'missing/altered proof record')
    if release:
        for k in ('video','captions','thumbnail','audio_audit'):
            need(artifact(root,doc.get(k)),'missing/altered final '+k)
        review=doc.get('review',{})
        need(isinstance(review.get('reviewer'),str) and bool(review['reviewer'].strip()),'reviewer not recorded')
        need(review.get('video_sha256')==doc.get('video',{}).get('sha256'),'review not bound to final bytes')
        for k in REQUIRED_REVIEW:need(review.get(k) is True,'review pending: '+k)
        need(doc.get('owner_release_authorized') is True,'owner release authorization absent')
    return errors
class Tests(unittest.TestCase):
 def test_gates(self):
    with tempfile.TemporaryDirectory() as d:
      r=Path(d);(r/'proof').write_text('proof');a={'path':'proof','sha256':sha(r/'proof')}
      scenes=[dict(start=i,end=i+1,visual_kind='capture',layout='layout'+str(i),spoken='say',visual_action='show',learning_purpose='teach',focal_label='focus',evidence=a,motion='annotation',role=role,shows_result=i in (0,1),intro_logo=False,evidence_visible_at=0) for i,role in enumerate(('hook','result','takeaway'))]
      plan=dict(format='short',audience='beginner',promise='one result',practical_takeaway='one action',topic_evidence='channel data',hook_variant='result_first',title='title',thumbnail_concept='proof',research_sources=['https://example.org'],proof=a,scenes=scenes)
      self.assertEqual(check(plan,r),[])
      self.assertTrue(check(plan,r,True))
      scenes[0]['intro_logo']=True;self.assertIn('logo intro prohibited',check(plan,r));scenes[0]['intro_logo']=False
      scenes[2]['layout']=scenes[1]['layout'];self.assertIn('fewer than three scene compositions',check(plan,r));scenes[2]['layout']='layout2'
      (r/'proof').write_text('tampered');self.assertIn('missing/altered proof record',check(plan,r))
 def test_empty(self):
    self.assertTrue(check({},Path('.')))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',nargs='?');p.add_argument('--release',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:unittest.main(argv=['quality_gate'],exit=True)
    if not a.plan:p.error('plan required')
    f=Path(a.plan).resolve();issues=check(json.loads(f.read_text(encoding='utf8')),f.parent,a.release)
    print(json.dumps({'mode':'release' if a.release else 'editorial_preflight','pass':not issues,'issues':issues},indent=2))
    raise SystemExit(bool(issues))
