"""Print or export a Google Flow plan; no provider/browser/network connection."""
from pathlib import Path
import argparse
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autopilot.flow_cinematic_handoff import build_plan

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("pilot","lean_day","full_keyshots","daily_50_credit"),default="pilot")
    parser.add_argument("--estimated-credits-per-clip",type=int,default=None,
                        help="Override provider UI estimate; defaults to duration-sensitive official price")
    parser.add_argument("--out",type=Path)
    opt=parser.parse_args()
    path=ROOT/"content"/"flow"/"oct24_cinematic_flow_scene_package.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    planned=build_plan(data,mode=opt.mode,price=opt.estimated_credits_per_clip)
    rendered=json.dumps(planned,ensure_ascii=False,indent=2)+"\n"
    if opt.out is not None:
        if not opt.out.parent.is_dir(): parser.error("Output parent must already exist")
        opt.out.write_text(rendered,encoding="utf-8")
    print(rendered,end="")

if __name__=="__main__":
    main()
