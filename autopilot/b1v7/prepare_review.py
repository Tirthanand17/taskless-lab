"""Prepare review-only B1v7 manifests from exact rendered plans. Never sets approval flags."""
from pathlib import Path
import json,html,hashlib,datetime
from quality_gate import check
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plans=[('incognito','pilot_v2_plan.json','fm_b1v7_incognito_download_short_en'),('notification_short','notification_short_plan.json','fm_b1v7_chrome_notifications_short_en'),('notification_long','notification_long_plan.json','fm_b1v7_chrome_notifications_long_en')]
cards=[];rows=[]
for key,name,eid in plans:
 p=R/name
 if not p.exists():continue
 d=read(p);assert not check(d,R),key
 ep={'id':eid,'title':d['title'],'type':d['format'],'language':'en','description':d['promise']+'. '+d['practical_takeaway']+'.\n\nControlled test using a separate Chrome profile. Actual captured browser states and annotated explanations; no personal browser data or live notification messages used.\n\nSources:\n'+'\n'.join(d['research_sources'])+'\n\nNarration generated locally with Kokoro (Apache-2.0). Original audio and graphics.\n\n#Chrome #TechTips'+(' #Shorts' if d['format']=='short' else ''),'tags':['Chrome','Chrome privacy','browser settings','tech tips','digital privacy']}
 ep_path=R/(eid+'.json');ep_path.write_text(json.dumps(ep,ensure_ascii=False,indent=2),encoding='utf8')
 m={'creative_standard':'B1v7','editorial_plan_sha256':sha(p),'expected_channel_id':'UCCcL9Q_jqVq6LJmnYUSAFZA','episode_id':eid,'episode_path':ep_path.name,'publish_at':None,'qa_approved':False,'captions_reviewed':False,'made_for_kids':False,'synthetic_media':None,'release_state':'REVIEW_ONLY_NO_RELEASE_AUTHORIZATION'}
 for k,mk,hk in [('video','video_path','video_sha256'),('captions','caption_path','caption_sha256'),('thumbnail','thumbnail_path','thumbnail_sha256')]:m[mk]=d[k]['path'];m[hk]=d[k]['sha256']
 manifest=R/(eid+'.release_LOCKED.json');manifest.write_text(json.dumps(m,indent=2),encoding='utf8')
 rows.append({'key':key,'title':d['title'],'format':d['format'],'hook_variant':d['hook_variant'],'duration':d['scenes'][-1]['end'],'sha256':d['video']['sha256'],'plan':name,'manifest':manifest.name,'status':'review only'})
 cards.append('<article><h2>'+html.escape(d['title'])+'</h2><p>'+str(round(d['scenes'][-1]['end'],1))+' seconds · '+d['hook_variant']+' · not scheduled</p><video controls preload="metadata" src="'+html.escape(d['video']['path'])+'" poster="'+html.escape(d['thumbnail']['path'])+'" width="'+('380' if d['format']=='short' else '820')+'"></video><p><a href="'+html.escape(d['captions']['path'])+'">English captions</a> · <a href="'+name+'">Evidence and scene plan</a> · <a href="'+manifest.name+'">Locked manifest</a></p></article>')
(R/'B1V7_REVIEW_START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>B1v7 quality review</title><style>body{font:18px/1.5 Segoe UI,sans-serif;background:#111c2a;color:#edf5fc;max-width:1050px;margin:30px auto;padding:20px}article{padding:24px 0;border-top:1px solid #41546b}a{color:#70e4bd}video{max-width:100%;max-height:670px}</style><h1>B1v7 demonstration-first batch</h1><p>Watch the exact final videos, verify factual explanations, pacing, on-screen text, audio and rights. All releases locked; existing Nov 24 schedule remains unchanged.</p>'+''.join(cards),encoding='utf8')
(R/'B1V7_BATCH_REVIEW.json').write_text(json.dumps({'rows':rows,'count':len(rows),'published':0,'scheduled':0,'review_pending':True},indent=2),encoding='utf8')
print('REVIEW_READY',len(rows),json.dumps(rows),flush=True)
