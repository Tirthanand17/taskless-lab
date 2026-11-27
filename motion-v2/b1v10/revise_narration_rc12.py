"""Explicit narration revisions for selected November 30 topics; preserve originals."""
import argparse,shutil
from pathlib import Path
from select_topics_rc12 import load,sha,need,D
from run_daily_rc10 import save,spec
REVISIONS={
"bounded_deque":{1:"Items arrive in order.",2:"This container has a fixed capacity.",3:"Set a maximum length, as shown."},
"count_missing":{0:"Why did the report miss records?",1:"Our local table contains records with and without numbers. We want to count every record that arrived, not just those that contain a number. Look at the missing values in the table.",2:"Counting a column skips missing values. The other records still exist in the table, even though the count is smaller.",3:"To count every record, use the star form shown on screen. It counts rows even when a value is missing. Subtract the column count from the row count to find the missing values.",4:"The result shows the total records, the recorded values and the missing values. We check the actual results against the original data.",5:"Both forms are useful. Use the row count for records received and the column count for values recorded. Choose the measure your report needs."}
}
def revised(original):
    import copy
    t=copy.deepcopy(original)
    for i,line in REVISIONS[t["id"]].items():t["scenes"][i][2]=line
    return t
def apply(work,key):
    need(key in REVISIONS,"unregistered revision")
    r=load(work/"SELECTION_QA.json");need(r["day"]=="2026-11-30","revision date")
    row=next(x for x in r["selected"] if x["topic"]==key);f=work/key
    need(not (f/"capture").exists() and not (f/"render").exists(),"media already exists")
    t=load(f/"topic.json");need(sha(f/"topic.json")==row["topic_sha256"] and sha(f/"narration_spec.json")==row["spec_sha256"],"original identity")
    old=f/"editorial-original";old.mkdir()
    for n in ("topic.json","narration_spec.json"):shutil.copyfile(f/n,old/n)
    if (f/"audio").exists():
        n=load(f/"audio/NARRATION_REVIEW_QA.json");need(n["asr_screen_pass"] is False,"do not replace passed narration")
        shutil.move(str(f/"audio"),str(old/"audio"))
    new=revised(t);save(f/"topic.json",new);save(f/"narration_spec.json",spec(new))
    save(f/"NARRATION_REVISION_QA.json",{"day":r["day"],"topic":key,"selection_sha256":sha(work/"SELECTION_QA.json"),"original_topic_sha256":row["topic_sha256"],"original_spec_sha256":row["spec_sha256"],"new_topic_sha256":sha(f/"topic.json"),"new_spec_sha256":sha(f/"narration_spec.json"),"revision_source_sha256":sha(Path(__file__)),"reason":"Simplify speech and avoid ambiguous automatic transcription; underlying experiment unchanged.","release_authorized":False})
def verify(work,row):
    f=work/row["topic"];r=load(f/"NARRATION_REVISION_QA.json");old=f/"editorial-original"
    need(r["day"]=="2026-11-30" and r["topic"]==row["topic"] and r["release_authorized"] is False and r["selection_sha256"]==sha(work/"SELECTION_QA.json") and r["revision_source_sha256"]==sha(Path(__file__)),"revision scope")
    need(sha(old/"topic.json")==r["original_topic_sha256"]==row["topic_sha256"] and sha(old/"narration_spec.json")==r["original_spec_sha256"]==row["spec_sha256"],"original evidence")
    need(sha(f/"topic.json")==r["new_topic_sha256"] and sha(f/"narration_spec.json")==r["new_spec_sha256"],"revised evidence")
    need(load(f/"topic.json")==revised(load(old/"topic.json")) and load(f/"narration_spec.json")==spec(load(f/"topic.json")),"revision mismatch")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--workspace",type=Path,required=True);p.add_argument("--topic",choices=list(REVISIONS),required=True);a=p.parse_args();apply(a.workspace,a.topic)
