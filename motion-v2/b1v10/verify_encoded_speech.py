"""Compare the encoded mix transcript with the original observed narration."""
import argparse,json
from pathlib import Path
from narration_review import normalized,compare,sha
from faster_whisper import WhisperModel

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory",type=Path);a=p.parse_args();d=a.directory
    root=Path(__file__).resolve().parent
    mix=json.loads((d/"SOUND_MIX_QA.json").read_text())
    original=json.loads((root/"NARRATION_REVIEW_QA.json").read_text())
    if sha(d/"mix.m4a")!=mix["artifacts_sha256"]["mix.m4a"]:raise ValueError("encoded hash mismatch")
    engine=WhisperModel("base",device="cpu",compute_type="int8",local_files_only=True,cpu_threads=4)
    segments,_=engine.transcribe(str(d/"decoded.wav"),language="en",beam_size=3,condition_on_previous_text=False,vad_filter=False)
    text=" ".join(s.text.strip() for s in segments)
    expected=" ".join(s["expected"] for s in original["scene_timeline"])
    prior=" ".join(s["recognized"] for s in original["scene_timeline"])
    result={"encoded_sha256":sha(d/"mix.m4a"),"recognized":text,"expected_token_similarity":round(compare(expected,text),4),"prior_raw_asr_token_similarity":round(compare(prior,text),4),"exact_expected_match":normalized(expected)==normalized(text),"human_listening_approved":False,"release_authorized":False}
    result["screen_pass"]=result["expected_token_similarity"]>=.95 and result["prior_raw_asr_token_similarity"]>=.95
    (d/"ENCODED_SPEECH_QA.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
