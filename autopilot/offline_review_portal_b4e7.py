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


def build_portal(manifest: dict, worksheet: dict, *, diagnostics: dict | None = None) -> str:
    """Emit a self-contained local playback/checklist UI; never approve release."""
    evidence = inspect(manifest, worksheet)
    if (evidence["self_reported_reviewed_scenes"] != 0
            or evidence["individual_checks_not_reviewed"] != 47
            or evidence["individual_checks_fail"] != 0
            or evidence["individual_checks_pass"] != 0
            or any(x.get("overall_human_decision") != "NOT_REVIEWED"
                   for x in worksheet["videos"])):
        raise ReviewValidationError("Portal must start from a blank official worksheet")
    # Validate actual FFmpeg-derived signal hints against exact original
    # MP4 identities. UI never changes NOT_REVIEWED statuses automatically.
    if diagnostics is not None:
        from autopilot.owner_signal_timeline_b4f5 import validate_signal_timeline
        signals = validate_signal_timeline(manifest, worksheet, diagnostics)
        signal_json = json.dumps(signals, ensure_ascii=True, separators=(",", ":"))
        signal_json = (signal_json.replace("&", "\\u0026")
                       .replace("<", "\\u003c").replace(">", "\\u003e"))
        signal_block = (
            '<script type="application/json" id="signal-data">' +
            signal_json + '</script>\n'
        )
    else:
        signal_block = ""
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
.scene-jump{margin:8px 0;padding:10px 14px;background:#244b76;border:1px solid #557fa8}
.scene-jump:focus-visible{outline:3px solid #ffcf64;outline-offset:3px}

.signal-panel{background:#101f36;border:1px solid #3d6284;border-radius:12px;padding:14px;margin:16px 0}
.signal-panel h3{margin:0 0 5px;color:#dbedfc}
.signal-panel .signal-list{margin:8px 0 0;padding:0;list-style:none}
.signal-panel li{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:7px 0;border-top:1px solid #30445c}
.signal-panel li span{font-size:13px;line-height:1.45}
.signal-panel .signal-seek{flex-shrink:0;background:#3b638b}
.signal-panel .signal-seek:focus-visible{outline:3px solid #ffd36b;outline-offset:3px}
.signal-panel small{display:block;margin-top:5px}
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
""" + signal_block + """<script>
"use strict";
const data=JSON.parse(document.getElementById("review-data").textContent);
const signalElement=document.getElementById("signal-data");
const signals=signalElement ? JSON.parse(signalElement.textContent) : null;
const states=["NOT_REVIEWED","PASS","FAIL"];
function formatSignalTime(seconds) {
  const n=Math.max(0,Math.floor(seconds));
  return String(Math.floor(n/60)).padStart(2,"0")+":"+
    String(n%60).padStart(2,"0");
}
function addSignalReview(section,player,index) {
  const panel=document.createElement("aside");panel.className="signal-panel";
  const title=document.createElement("h3");title.textContent="Encoded MP4 signal review";
  panel.appendChild(title);
  const notice=document.createElement("small");
  notice.textContent="Automated hints only. A static diagram or pause can be intentional. Click to seek; no review status changes automatically.";
  panel.appendChild(notice);
  if (!signals) {
    const empty=document.createElement("p");
    empty.className="muted";
    empty.textContent="Technical warnings not yet attached. This is not a quality pass.";
    panel.appendChild(empty);section.querySelector(".review-inputs").prepend(panel);
    return;
  }
  const item=signals.videos[index];
  const summary=document.createElement("p");summary.className="muted";
  summary.textContent=item.seek_hints.length+
    " timecoded checks; encoded sample peak "+item.sample_peak_dbfs_not_true_peak+
    " dBFS (not true peak), mean "+item.sample_mean_dbfs_not_lufs+
    " dBFS (not LUFS).";
  panel.appendChild(summary);
  const list=document.createElement("ul");list.className="signal-list";
  for(const hint of item.seek_hints) {
    const li=document.createElement("li");
    const label=document.createElement("span");
    label.textContent=hint.label+" · "+formatSignalTime(hint.start_seconds)+
      "–"+formatSignalTime(hint.end_seconds)+
      " ("+hint.duration_seconds+" s)";
    li.appendChild(label);
    const button=document.createElement("button");
    button.type="button";button.className="signal-seek";
    button.textContent="Seek "+formatSignalTime(hint.start_seconds);
    button.setAttribute("aria-label","Seek "+hint.label+" at "+
      formatSignalTime(hint.start_seconds));
    button.addEventListener("click",()=>{
      // Do not auto-play or mark PASS. Only the actual human may review.
      const seek=()=>{
        const playable=Number.isFinite(player.duration)
          ? player.duration : item.duration_seconds;
        player.currentTime=Math.max(0,Math.min(hint.start_seconds,playable-0.1));
        player.pause();player.focus();
      };
      if(player.readyState>=1) seek();
      else {
        player.addEventListener("loadedmetadata",seek,{once:true});
        player.load();
      }
    });
    li.appendChild(button);list.appendChild(li);
  }
  if(item.seek_hints.length===0) {
    const quiet=document.createElement("p");quiet.className="muted";
    quiet.textContent="No timed signal detected. Still requires full human playback.";
    panel.appendChild(quiet);
  }
  if(item.warning_codes.length) {
    const codes=document.createElement("small");
    codes.textContent="Technical warning codes: "+item.warning_codes.join(", ");
    panel.appendChild(codes);
  }
  panel.appendChild(list);
  section.querySelector(".review-inputs").prepend(panel);
}
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
  addSignalReview(section,player,i);
  const headline=document.createElement("h3"); headline.textContent="10 quality checks";target.appendChild(headline);
  for(const key of Object.keys(video.checks)) {
    rowLabel(key.replaceAll("_"," "),selectStatus(video.checks[key],x=>video.checks[key]=x),target);
  }
  const sceneTitle=document.createElement("h3");sceneTitle.textContent="Scene-by-scene review";
  target.appendChild(sceneTitle);
  for(const scene of video.scenes) {
    const div=document.createElement("div");div.className="scene";
    if(Number.isFinite(scene.source_start_seconds) &&
       Number.isFinite(scene.source_end_seconds)) {
      const seek=document.createElement("button");
      seek.type="button";seek.className="scene-jump";
      seek.textContent="Jump to scene "+scene.scene_number+" · "+
        formatSignalTime(scene.source_start_seconds);
      seek.setAttribute("aria-label","Seek original scene "+scene.scene_number+
        " at "+formatSignalTime(scene.source_start_seconds));
      seek.addEventListener("click",()=>{
        const focusScene=()=>{
          const playable=Number.isFinite(player.duration) && player.duration>0
            ? player.duration : video.duration_seconds_measured_pcm;
          const timestamp=Math.min(scene.source_start_seconds+0.12,
            scene.source_end_seconds-0.1,playable-0.1);
          player.currentTime=Math.max(0,timestamp);
          player.pause();player.focus();
          // Seeking never changes a worksheet status or signs review.
        };
        if(player.readyState>=1) focusScene();
        else {
          player.addEventListener("loadedmetadata",focusScene,{once:true});
          player.load();
        }
      });
      div.appendChild(seek);
    }
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
