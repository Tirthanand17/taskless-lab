"""Correct only a predeclared technical homophone, retaining ASR evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from narration_review import normalized, validate_words, timestamp

def correct(cues, report):
    result=copy.deepcopy(cues)
    timeline=report["scene_timeline"]
    hook=timeline[0]
    if hook["id"]!="hook" or normalized(hook["expected"])!=normalized("What happens when you change just one byte?"):
        raise ValueError("unexpected hook script")
    if normalized(hook["recognized"])!=normalized("What happens when you change just one bite?"):
        raise ValueError("unexpected ASR; manual review required")
    if not all(s["exact_token_match"] for s in timeline[1:]):
        raise ValueError("additional ASR differences; manual review required")
    matches=[(c,w) for c in result for w in c["words"] if w["start"]<hook["end_frame"]/30 and normalized(w["word"])==["bite"]]
    if len(matches)!=1: raise ValueError("ambiguous homophone timing")
    c,w=matches[0]
    prior=w["word"]
    w["word"]="byte"+("?" if prior.endswith("?") else "")
    c["text"]=" ".join(x["word"] for x in c["words"])
    words=[w for c in result for w in c["words"]]
    validate_words(words,report["duration_seconds"])
    expected=normalized(" ".join(s["expected"] for s in timeline))
    if normalized(" ".join(w["word"] for w in words))!=expected:
        raise ValueError("corrected captions still differ")
    return result,{"asr_token":prior,"caption_token":w["word"],"start":w["start"],"end":w["end"],
        "reason":"byte and bite are homophones; correct technical spelling from locked script; pronunciation still requires listening"}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory",type=Path);a=p.parse_args();d=a.directory
    report=json.loads((d/"NARRATION_REVIEW_QA.json").read_text(encoding="utf-8"))
    source=d/"word_captions.json"
    if sha(source)!=report["word_captions_sha256"]: raise ValueError("raw caption digest mismatch")
    revised,entry=correct(json.loads(source.read_text(encoding="utf-8")),report)
    dest=d/"word_captions_review.json"
    srt=d/"captions_review.srt"
    dest.write_text(json.dumps(revised,indent=2)+"\n",encoding="utf-8")
    srt.write_text("\n\n".join(f"{i}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['text']}" for i,c in enumerate(revised,1))+"\n",encoding="utf-8")
    proof={"raw_report_sha256":sha(d/"NARRATION_REVIEW_QA.json"),"raw_asr_screen_pass":report["asr_screen_pass"],
           "corrected_word_captions_sha256":sha(dest),"corrected_srt_sha256":sha(srt),
           "correction":entry,"caption_text_matches_script":True,"timings_changed":False,
           "human_listening_approved":False,"release_authorized":False}
    (d/"CAPTION_CORRECTION_QA.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(proof,indent=2))
if __name__=="__main__":main()
