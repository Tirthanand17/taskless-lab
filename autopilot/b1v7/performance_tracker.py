"""Read-only matched-age tracking of FlowMinute Lab releases.
Public API counters only; Studio retention fields must come from actual Studio evidence.
Never publish, fabricate unavailable metrics, or count scheduled videos as age-zero performance.
"""
from pathlib import Path
import json,datetime as dt,sys,argparse,statistics,unittest,tempfile
UTC=dt.timezone.utc
CHANNEL='UCCcL9Q_jqVq6LJmnYUSAFZA'
MILESTONES=(24,48,168)
TOLERANCE={24:6,48:8,168:24}
def parse(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(UTC)
def observation(row,video,now):
    assert video['snippet']['channelId']==CHANNEL and video['id']==row['video_id']
    assert video['snippet']['title']==row['title'],'unexpected title; inspect registry'
    status=video['status']['privacyStatus'];publication=parse(row['scheduled_utc'])
    hours=(now-publication).total_seconds()/3600
    if status!='public' or hours<0:
        return {'video_id':row['video_id'],'status':status,'eligible':False,'age_hours':None,'reason':'not confirmed public'}
    stat=video.get('statistics',{})
    return {'video_id':row['video_id'],'cohort':row['cohort'],'format':row['format'],'hook':row.get('hook'),'status':status,'eligible':True,'age_hours':round(hours,2),'publication_basis':'verified planned schedule; actual publication may differ','milestone':next((m for m in MILESTONES if abs(hours-m)<=TOLERANCE[m]),None),'views':int(stat['viewCount']) if 'viewCount' in stat else None,'likes':int(stat['likeCount']) if 'likeCount' in stat else None,'comments':int(stat['commentCount']) if 'commentCount' in stat else None,'studio':None}
def summarize(snapshots):
    groups={}
    for snap in snapshots:
        for row in snap['rows']:
            if not row.get('eligible') or row.get('milestone') is None or row.get('views') is None:continue
            key=(row['cohort'],row['format'],row['milestone'],row['video_id'])
            prior=groups.get(key)
            if prior is None or abs(row['age_hours']-row['milestone'])<abs(prior['age_hours']-row['milestone']):groups[key]=row
    out={}
    for (cohort,fmt,age,vid),row in groups.items():
        out.setdefault((cohort,fmt,age),[]).append(row['views'])
    return [{'cohort':c,'format':f,'milestone_hours':a,'sample_n':len(v),'median_views':statistics.median(v),'range':[min(v),max(v)],'interpretation':'exploratory only; small sample' if len(v)<5 else 'descriptive matched-age comparison'} for (c,f,a),v in sorted(out.items())]
def run(args):
    import youtube_publisher as pub
    reg=json.loads(args.registry.read_text(encoding='utf8'))
    rows=reg['videos'];ids=[x['video_id'] for x in rows]
    assert len(ids)==len(set(ids)) and reg['channel_id']==CHANNEL
    api=pub.youtube_client(args.token,writable=False);pub.guard_channel(api,CHANNEL)
    remote={}
    for i in range(0,len(ids),50):
        for item in api.videos().list(part='snippet,status,statistics',id=','.join(ids[i:i+50])).execute().get('items',[]):remote[item['id']]=item
    now=dt.datetime.now(UTC)
    result={'observed_at':now.isoformat(),'channel_id':CHANNEL,'source':'official authenticated YouTube Data API; read only','rows':[observation(row,remote[row['video_id']],now) if row['video_id'] in remote else {'video_id':row['video_id'],'eligible':False,'status':'missing'} for row in rows]}
    args.output.mkdir(parents=True,exist_ok=True)
    path=args.output/(now.strftime('%Y%m%dT%H%M%S%fZ')+'.json');path.write_text(json.dumps(result,indent=2))
    history=[json.loads(p.read_text()) for p in args.output.glob('*Z.json')]
    summary=summarize(history)
    (args.output/'matched_age_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({'snapshot':result,'matched_age':summary},indent=2))
class Tests(unittest.TestCase):
    def test_excludes_private_and_selects_age(self):
        now=parse('2026-11-25T10:30:00Z')
        row={'video_id':'test','title':'title','scheduled_utc':'2026-11-24T10:30:00Z','cohort':'B1v6','format':'short'}
        v={'id':'test','snippet':{'channelId':CHANNEL,'title':'title'},'status':{'privacyStatus':'private'},'statistics':{'viewCount':'2'}}
        self.assertFalse(observation(row,v,now)['eligible'])
        v['status']['privacyStatus']='public';r=observation(row,v,now);self.assertEqual(r['milestone'],24)
        self.assertEqual(summarize([{'rows':[r]},{'rows':[r]}])[0]['sample_n'],1)
        self.assertIsNone(r['studio'])
    def test_missing_counts_not_zero(self):
        now=parse('2026-11-25T10:30:00Z');row={'video_id':'x','title':'t','scheduled_utc':'2026-11-24T10:30:00Z','cohort':'x','format':'long'}
        v={'id':'x','snippet':{'channelId':CHANNEL,'title':'t'},'status':{'privacyStatus':'public'}}
        self.assertIsNone(observation(row,v,now)['views'])
if __name__=='__main__':
    if '--self-test' in sys.argv:unittest.main(argv=['tracker'])
    else:
        p=argparse.ArgumentParser();p.add_argument('--registry',type=Path,required=True);p.add_argument('--token',type=Path,required=True);p.add_argument('--publisher-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
        a=p.parse_args();sys.path.insert(0,str(a.publisher_dir));run(a)
