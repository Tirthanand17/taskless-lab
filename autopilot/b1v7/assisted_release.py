"""B1v7 assisted publishing entrypoint; no writes unless editorial and publisher checks pass.
Legacy releases remain unchanged. Use this wrapper, not the legacy CLI directly, for B1v7.
"""
from pathlib import Path
import argparse,json,sys,subprocess,tempfile,unittest
from quality_gate import check,sha
CHANNEL='UCCcL9Q_jqVq6LJmnYUSAFZA'
OPS={'upload':'--confirm-private-upload','assets':'--confirm-assets','schedule':'--confirm-schedule'}
def load(p):return json.loads(p.read_text(encoding='utf8'))
def bind(plan_path,manifest_path):
    plan=load(plan_path);m=load(manifest_path);base=manifest_path.parent;root=plan_path.parent
    errors=check(plan,root,release=True)
    def require(ok,msg):
        if not ok:errors.append(msg)
    require(m.get('creative_standard')=='B1v7','manifest not marked B1v7')
    require(m.get('editorial_plan_sha256')==sha(plan_path),'manifest not bound to editorial plan')
    require(m.get('expected_channel_id')==CHANNEL,'wrong channel')
    for k,mk,hk in [('video','video_path','video_sha256'),('captions','caption_path','caption_sha256'),('thumbnail','thumbnail_path','thumbnail_sha256')]:
        a=plan.get(k,{})
        if not isinstance(a,dict):errors.append('invalid artifact '+k);continue
        require(bool(m.get(mk)) and bool(a.get('path')) and (base/str(m.get(mk,''))).resolve()==(root/str(a.get('path',''))).resolve(),'path mismatch '+k)
        require(m.get(hk)==a.get('sha256'),'hash mismatch '+k)
    ep=(base/str(m.get('episode_path',''))).resolve()
    if not ep.is_relative_to(root.resolve()) or not ep.is_file():
        errors.append('metadata missing/outside review root')
    else:
        e=load(ep)
        require(e.get('id')==m.get('episode_id'),'episode ID mismatch')
        require(e.get('title')==plan.get('title'),'reviewed title mismatch')
        require(e.get('type')==plan.get('format'),'reviewed format mismatch')
        require(plan.get('review',{}).get('metadata_sha256')==sha(ep),'metadata not reviewed')
    review=plan.get('review',{})
    for k in ('captions','thumbnail','proof','audio_audit'):
        require(review.get(k+'_sha256')==plan.get(k,{}).get('sha256') and bool(review.get(k+'_sha256')),'review not bound to '+k)
    require(m.get('qa_approved') is True and m.get('captions_reviewed') is True,'publisher QA flags missing')
    return errors
def run(argv=None):
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['check','prepare',*OPS]);p.add_argument('plan',type=Path);p.add_argument('manifest',type=Path)
    p.add_argument('--publisher',type=Path);p.add_argument('--token-file',type=Path);p.add_argument('--ledger',type=Path);p.add_argument('--confirm',action='store_true')
    a=p.parse_args(argv);errors=bind(a.plan.resolve(),a.manifest.resolve())
    if errors:
        print(json.dumps({'pass':False,'issues':errors,'youtube_writes':0},indent=2));return 2
    print('B1V7_RELEASE_GATE_PASS',flush=True)
    if a.operation=='check':return 0
    if not a.publisher or not a.publisher.is_file():p.error('explicit existing publisher path required')
    args=[sys.executable,str(a.publisher),a.operation,str(a.manifest.resolve())]
    if a.operation in OPS:
        if not a.confirm or not a.token_file or not a.ledger:p.error('write requires explicit --confirm, token file and ledger')
        # No automatic retries or bypass; existing publisher verifies channel/ledger and exact bytes.
        args+=['--token-file',str(a.token_file),'--ledger',str(a.ledger),OPS[a.operation]]
    return subprocess.run(args,check=False).returncode
class GateTests(unittest.TestCase):
    def test_unreviewed_block(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);p=r/'plan.json';m=r/'manifest.json';p.write_text('{}');m.write_text('{}')
            self.assertTrue(bind(p,m))
    def test_binding_and_tamper(self):
        from quality_gate import REQUIRED_REVIEW
        with tempfile.TemporaryDirectory() as t:
            r=Path(t)
            def asset(n):
                f=r/n;f.write_text(n);return {'path':n,'sha256':sha(f)}
            assets={k:asset(k) for k in ('video','captions','thumbnail','proof','audio_audit')}
            e=r/'episode.json';e.write_text(json.dumps({'id':'pilot','title':'Test','type':'short'}))
            review={k:True for k in REQUIRED_REVIEW};review.update(reviewer='test fixture',metadata_sha256=sha(e),**{k+'_sha256':v['sha256'] for k,v in assets.items()})
            scenes=[dict(start=i,end=i+1,visual_kind='capture',layout='layout'+str(i),spoken='test',visual_action='show',learning_purpose='teach',focal_label='focus',evidence=assets['proof'],motion='annotation',role=role,shows_result=i<2,intro_logo=False,evidence_visible_at=0) for i,role in enumerate(('hook','result','takeaway'))]
            plan=dict(format='short',audience='test',promise='test',practical_takeaway='test',topic_evidence='test',hook_variant='result_first',title='Test',thumbnail_concept='test',research_sources=['https://example.org'],owner_release_authorized=True,review=review,scenes=scenes,**assets)
            p=r/'plan.json';p.write_text(json.dumps(plan))
            m=r/'manifest.json';doc=dict(creative_standard='B1v7',editorial_plan_sha256=sha(p),expected_channel_id=CHANNEL,episode_id='pilot',episode_path='episode.json',qa_approved=True,captions_reviewed=True)
            for k,mk,hk in [('video','video_path','video_sha256'),('captions','caption_path','caption_sha256'),('thumbnail','thumbnail_path','thumbnail_sha256')]:doc[mk]=assets[k]['path'];doc[hk]=assets[k]['sha256']
            m.write_text(json.dumps(doc));self.assertEqual(bind(p,m),[])
            e.write_text('{}');self.assertIn('metadata not reviewed',bind(p,m))
            (r/'video').write_text('tampered');self.assertIn('missing/altered final video',bind(p,m))
if __name__=='__main__':
    if '--self-test' in sys.argv:unittest.main(argv=['assisted_release'])
    else:raise SystemExit(run())
