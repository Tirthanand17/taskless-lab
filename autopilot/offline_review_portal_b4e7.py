"""B4e7 local-only review dashboard for the 3 original UNAPPROVED MP4s.

No HTTP dependencies, external assets, outgoing network, YouTube operations,
private facts, or actual owner watch claims. A browser must open the downloaded
HTML next to the actual three SHA-bound local MP4 files.
"""
from __future__ import annotations

from html import escape
import json

from autopilot.manual_rehearsal_review_export_b4e3 import SLOT_NAMES
from autopilot.review_worksheet_validator_b4e6 import inspect, ReviewValidationError

PORTAL_FILE = "OPEN_LOCAL_REVIEW_DASHBOARD.html"


def build_portal(manifest: dict, worksheet: dict) -> str:
    """Emit a self-contained local playback/checklist UI; never approve release."""
    evidence = inspect(manifest, worksheet)
    if (evidence["self_reported_reviewed_scenes"] != 0
            or evidence["individual_checks_not_reviewed"] != 47
            or evidence["individual_checks_fail"] != 0
            or evidence["individual_checks_pass"] != 0
            or any(x.get("overall_human_decision") != "NOT_REVIEWED"
                   for x in worksheet["videos"])):
        raise ReviewValidationError("Portal must start from a blank official worksheet")
    labels = ("Morning Short", "Long video", "Evening Short")
    players = "".join(
        '<section class="episode" data-index="' + str(i) + '">'
        '<h2>' + escape(labels[i]) + '</h2>'
        '<p class="muted">' + str(count) + ' original scenes &middot; UNAPPROVED</p>'
        '<video controls playsinline preload="metadata" src="' +
        escape(filename, quote=True) + '"></video>'
        '<p class="sha">SHA-256: ' + escape(worksheet["videos"][i]["sha256"]) +
        '</p><div class="review-inputs"></div></section>'
        for i, (_, filename, count) in enumerate(SLOT_NAMES)
    )
    # Source records only contain canonical video basenames, SHA values, and
    # blank note fields; escaping script delimiters guards even against future
    # schema extensions including unsafe prose.
    raw = json.dumps(worksheet, ensure_ascii=True, separators=(",", ":"))
    raw = (raw.replace("&", "\\u0026").replace("<", "\\u003c")
           .replace(">", "\\u003e").replace("\u2028", "\\u2028")
           .replace("\u2029", "\\u2029"))
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; media-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; img-src data:; object-src 'none'; form-action 'none'; base-uri 'none'">
<title>Flowminute Lab | Offline MP4 Review (NO PUBLISH)</title>
<style>
:root{color-scheme:dark;font-family:system-ui,Segoe UI,Arial,sans-serif}
body{background:#0b1320;color:#e8f0fc;margin:0;padding:clamp(14px,4vw,38px)}
main{max-width:1280px;margin:0 auto}
h1{font-size:clamp(1.7rem,4vw,2.6rem)}h2{margin:.3rem 0}
p{line-height:1.55}.muted,.sha{color:#a8b5c8}.sha{font:11px ui-monospace,monospace;overflow-wrap:anywhere}
.warning{border-left:4px solid #f7b955;background:#212332;padding:14px;border-radius:6px}
.layout{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:18px}
.episode{min-width:0;background:#152137;border:1px solid #31415b;border-radius:16px;padding:18px}
video{display:block;max-width:100%;width:100%;max-height:520px;background:black;border-radius:10px}
.episode[data-index="1"] video{max-height:360px}
label{display:block;margin:12px 0 4px;font-size:13px;color:#e6ecfc}
select,input,textarea,button{font:inherit;border-radius:7px;padding:9px;max-width:100%;box-sizing:border-box}
select,input,textarea{color:#fff;background:#0e192a;border:1px solid #59687d;width:100%}
textarea{resize:vertical;min-height:55px}
button{border:0;color:#fff;background:#2860c2;cursor:pointer}
.scene{border-top:1px solid #38485e;margin-top:14px;padding-top:10px}
.capture{margin-top:5px;background:#4b5e7f}
#save{margin:24px 0;background:#19856f;font-weight:700}
#status{font-size:1.1rem;font-weight:700}
small{color:#b4bfce}
</style></head><body><main>
<h1>Flowminute Lab · 3-video offline review</h1>
<p class="warning"><strong>NOT FOR PUBLISHING.</strong> These are synthetic educational rehearsals, not fact-checked news. Every checklist and scene is NOT_REVIEWED at start. This local page does not transmit video, review notes, or credentials. Download a copy of your notes; independent facts, asset rights and final release approval remain blocked.</p>
<p id="status" aria-live="polite">0 / 47 assessments entered (self-reported; not authenticated)</p>
<p>Play each MP4 with sound, then select review results. Capture a current-video timestamp for each reviewed scene and write actionable notes when failing. A complete mark is never a YouTube release approval.</p>
<div class="layout">""" + players + """</div>
<button type="button" id="save">Download my local review JSON</button>
<p><small>Keep this JSON private and validate it with: python -m autopilot.review_worksheet_validator_b4e6 --manifest REVIEW_ONLY_NO_PUBLISH.json --worksheet YOUR_REVIEW.json. No upload or automated pass is performed.</small></p>
<script type="application/json" id="review-data">""" + raw + """</script>
<script>
"use strict";
const data=JSON.parse(document.getElementById("review-data").textContent);
const states=["NOT_REVIEWED","PASS","FAIL"];
function selectStatus(value,change) {
  const s=document.createElement("select");
  for (const name of states) {
    const option=document.createElement("option"); option.value=name;
    option.textContent=name.replaceAll("_"," "); s.appendChild(option);
  }
  s.value=value;s.addEventListener("change",()=>{change(s.value);updateProgress()});
  return s;
}
function rowLabel(text,child,container) {
  const lbl=document.createElement("label");lbl.textContent=text;
  lbl.appendChild(child);container.appendChild(lbl);
}
function updateProgress() {
  let completed=0;
  for(const video of data.videos) {
    for(const status of Object.values(video.checks)) if(status!=="NOT_REVIEWED") completed++;
    for(const scene of video.scenes) if(scene.review_status!=="NOT_REVIEWED") completed++;
  }
  document.getElementById("status").textContent=
    completed+" / 47 assessments entered (self-reported; not authenticated)";
}
for(const section of document.querySelectorAll("section.episode")) {
  const i=Number(section.dataset.index), video=data.videos[i];
  const player=section.querySelector("video"), target=section.querySelector(".review-inputs");
  const headline=document.createElement("h3"); headline.textContent="10 quality checks";target.appendChild(headline);
  for(const key of Object.keys(video.checks)) {
    rowLabel(key.replaceAll("_"," "),selectStatus(video.checks[key],x=>video.checks[key]=x),target);
  }
  const sceneTitle=document.createElement("h3");sceneTitle.textContent="Scene-by-scene review";
  target.appendChild(sceneTitle);
  for(const scene of video.scenes) {
    const div=document.createElement("div");div.className="scene";
    rowLabel("Scene "+scene.scene_number,
      selectStatus(scene.review_status,x=>{
        scene.review_status=x;
        if(x==="NOT_REVIEWED"){scene.timecode_mm_ss=null;scene.defect_notes=null;stamp.value="";note.value=""}
      }),div);
    const stamp=document.createElement("input");stamp.readOnly=true;
    stamp.placeholder="Capture timestamp";stamp.value=scene.timecode_mm_ss||"";
    rowLabel("Timecode (mm:ss)",stamp,div);
    const capture=document.createElement("button");capture.type="button";
    capture.className="capture";capture.textContent="Capture playback time";
    capture.addEventListener("click",()=>{
      if(scene.review_status==="NOT_REVIEWED")return;
      const t=Math.min(Math.max(player.currentTime||0,0),video.duration_seconds_measured_pcm);
      const sec=Math.floor(t);
      scene.timecode_mm_ss=String(Math.floor(sec/60)).padStart(2,"0")+":"+
        String(sec%60).padStart(2,"0");
      stamp.value=scene.timecode_mm_ss;
    });
    div.appendChild(capture);
    const note=document.createElement("textarea");
    note.maxLength=500;note.placeholder="When FAIL: describe expected vs observed (at least 8 chars)";
    note.value=scene.defect_notes||"";
    note.addEventListener("input",()=>scene.defect_notes=note.value.trim()||null);
    rowLabel("Defect note (private)",note,div);
    target.appendChild(div);
  }
  rowLabel("Overall human review decision (manual, not release approval)",
    selectStatus(video.overall_human_decision,x=>video.overall_human_decision=x),target);
}
document.getElementById("save").addEventListener("click",()=>{
  // Never allow an offline worksheet to assert independently authenticated
  // publication, owner signature, or factual/rights approval.
  data.human_review_completed=false;
  data.factual_news_approved=false; data.rights_approved=false;
  data.youtube_publish_authorized=false;
  const blob=new Blob([JSON.stringify(data,null,2)+"\\n"],{type:"application/json"});
  const u=URL.createObjectURL(blob);
  const a=document.createElement("a");a.href=u;a.download="FLOWMINUTE_PRIVATE_HUMAN_REVIEW.json";
  document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(u);
});
updateProgress();
</script></main></body></html>
"""


if __name__ == "__main__":
    raise SystemExit("Use through explicit manual review artifact generation; no stand-alone network server")
