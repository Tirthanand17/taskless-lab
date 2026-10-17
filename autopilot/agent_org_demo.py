"""FlowMinute staging preview only: no API, model, media or billing operations.

Usage: python -m autopilot.agent_org_demo --count 9
"""
from __future__ import annotations
import argparse
import json
from .agent_org import EpisodeSpec,MasterOrchestrator

def preview(count:int=3)->dict:
    if count not in (1,3,9):
        raise ValueError("Only 1, 3 or 9 demonstration episodes allowed")
    items=tuple(EpisodeSpec(f"demo_{i+1:02d}",
                             "long" if (i+1)%3==0 else "short",
                             "hi" if i%2 else "en")
                for i in range(count))
    master=MasterOrchestrator(items)
    return {**master.summary(),
            "first_assignments":[{"episode":ep,"task":task,"specialist":owner}
                                 for ep,task,owner in master.ready_assignments()],
            "preview_note":"SIMULATED DAG ONLY; no AI model, source fetch, rendering or YouTube upload",
            "videos_uploaded":0,"videos_scheduled":0}

def main()->None:
    p=argparse.ArgumentParser(description="Zero-cost staging DAG preview")
    p.add_argument("--count",type=int,choices=(1,3,9),default=3)
    args=p.parse_args()
    print(json.dumps(preview(args.count),indent=2,sort_keys=True))

if __name__=="__main__":main()
