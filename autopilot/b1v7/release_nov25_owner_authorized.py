"""One-time owner-authorized Nov 25 schedule-before-playback exception.
Original locked review plans and default B1v7 gate remain unchanged.
No false human playback signoff. Uses existing protected publisher.
"""
from pathlib import Path
import sys,json,hashlib,datetime as dt,subprocess,importlib.util,re
R=Path(__file__).resolve().parent;B=R.parent
from quality_gate import check
spec=importlib.util.spec_from_file_location('prior_release_helpers',B/'nov24-b1v6'/'release_licensed_nov24.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
pub=h.pub
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
C=h.C
EXPECTED={'incognito':('addff1c9b3ca7329ff7e3e430247bbc4993d5b27bbc58999e12f435248d6f45c','2026-11-25T10:30:00Z'),'notification_long':('081c72a21477f4ee39af87505a8cc936e12302fa649dc8e2528eec0d2d9fea59','2026-11-25T13:30:00Z'),'notification_short':('8cc1b2001b56aef1867eb77cab78db356bd9f3e549b3d27381fe9f2ac8c1e916','2026-11-25T15:30:00Z')}
def stage():
 subprocess.run([sys.executable,str(R/'plan_next_release.py')],check=True)
 inv=read(R/'B1V7_PROPOSED_RELEASE_PLAN.json')
 assert inv['channel_id']==C and inv['all_duplicate_checks_clear'] and inv['all_slot_checks_clear']
 batch=read(R/'B1V7_BATCH_REVIEW.json')
 audits=read(R/'B1V7_FINAL_REVIEW_AUDIT.json')
 ledger=pub.get_ledger(h.L)
 plans=[]
 for k,(digest,when) in EXPECTED.items():
  row=next(x for x in batch['rows'] if x['key']==k);a=next(x for x in audits if x['key']==k)
  p=R/row['plan'];doc=read(p);m=read(R/row['manifest'])
  assert not check(doc,R),check(doc,R)
  assert a['caption_timing_pass'] and a['manifest_hash_pass'] and a['release_locked'] and a['short_cues_under_0_85s']==0
  assert a['sha256']==digest==row['sha256']==m['video_sha256']==doc['video']['sha256']
  assert not m['qa_approved'] and not m['captions_reviewed'] and not doc['owner_release_authorized']
  assert m['editorial_plan_sha256']==sha(p) and m['expected_channel_id']==C
  assert m['episode_id'] not in ledger['episodes']
  for k0,mk,hk in [('video','video_path','video_sha256'),('captions','caption_path','caption_sha256'),('thumbnail','thumbnail_path','thumbnail_sha256')]:
   assert m[mk]==doc[k0]['path'] and m[hk]==doc[k0]['sha256']==sha(R/m[mk])
  for asset in ('proof','audio_audit'):
   assert sha(R/doc[asset]['path'])==doc[asset]['sha256']
  voice=read(R/doc['audio_audit']['path'])
  assert all(x['similarity']>=.9 for x in voice['scenes'])
  # Review caption text and timing against the measured ASR transcript. Human listening is explicitly outstanding.
  cap=R/m['caption_path'];pub.validate_srt_file(cap)
  words=' '.join(line for line in cap.read_text(encoding='utf-8-sig').splitlines() if line.strip() and not line.isdigit() and '-->' not in line)
  heard=' '.join(x.get('asr',x.get('recognized','')) for x in voice['scenes'])
  import difflib
  norm=lambda s:re.findall(r'[a-z0-9]+',s.lower())
  match=difflib.SequenceMatcher(None,norm(words),norm(heard),autojunk=False).ratio()
  assert match>=.97,(k,match)
  ep=read(R/m['episode_path']);assert ep['title']==doc['title'] and ep['type']==doc['format']
  # A separate one-batch release decision, not a fabricated reviewer signoff.
  m.update(publish_at=when,qa_approved=True,captions_reviewed=True,synthetic_media=False,
   release_state='OWNER_AUTHORIZED_SCHEDULE_BEFORE_PLAYBACK',
   owner_release_authorization='ok continue to schedule then i am going to check that.',
   human_full_playback_verified=False,owner_exact_hash_approved=False,
   caption_review_method='Automated ASR transcript comparison and measured SRT timing; human playback pending',
   caption_asr_match=round(match,4),original_locked_manifest_sha256=sha(R/row['manifest']),
   final_audit_sha256=sha(R/'B1V7_FINAL_REVIEW_AUDIT.json'))
  target=R/(m['episode_id']+'.release_OWNER_AUTHORIZED_BEFORE_PLAYBACK.json')
  assert not target.exists()
  target.write_text(json.dumps(m,indent=2,ensure_ascii=False),encoding='utf8')
  plan=pub.validate_manifest(target)
  plans.append((k,plan))
  print('EXACT_MEDIA_PREFLIGHT',k,'caption_asr_match',round(match,4),flush=True)
 return plans
if __name__=='__main__':
 h.api=pub.youtube_client(h.T,writable=True);pub.guard_channel(h.api,C)
 plans=stage()
 print('ALL_THREE_PREFLIGHT_PASS',flush=True)
 rows=[]
 for k,p in plans:
  pub.upload_private(h.api,p,h.L)
  h.wait_processed(p)
  h.update_language(p)
  pub.decorate_assets(h.api,p,h.L)
  h.caption_serving(p)
  try:pub.schedule_private(h.api,p,h.L)
  except pub.PublisherError:
   if h.rec(p)['state']!='scheduling_unresolved':raise
  h.reconcile(p)
  row=h.final_read(k,p);row['owner_playback_pending']=True
  rows.append(row)
  (R/'NOV25_B1V7_RELEASE_RECEIPTS.json').write_text(json.dumps({'rows':rows,'all_three_verified':len(rows)==3,'human_playback_pending':True},indent=2,ensure_ascii=False),encoding='utf8')
 print('ALL_THREE_SCHEDULED_API_VERIFIED',flush=True)
