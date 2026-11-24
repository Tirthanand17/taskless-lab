"""Isolated Chrome notification settings test, no user profile or external site touched."""
from pathlib import Path
import json, tempfile, subprocess, threading, time, base64, hashlib, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import websocket
R=Path(__file__).resolve().parent/'notifications';R.mkdir(exist_ok=True)
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  data=b'<!doctype html><meta charset=utf-8><title>Local notification test</title><style>body{font:36px Segoe UI;padding:60px;background:#f1f5f9;color:#16243b}strong{font-size:68px;display:block;margin-top:30px}</style><h1>Notification permission</h1><p>Actual browser API result for this local test site:</p><strong id="state"></strong><p>No actual notifications are sent.</p><script>document.querySelector("#state").textContent=Notification.permission;</script>'
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(data)
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
origin='http://127.0.0.1:'+str(server.server_port)
chrome=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
with tempfile.TemporaryDirectory(prefix='fm-notification-proof-') as profile:
 default=Path(profile)/'Default';default.mkdir()
 # Only the isolated test profile, preconfigure one known allowed origin.
 (default/'Preferences').write_text(json.dumps({'profile':{'content_settings':{'exceptions':{'notifications':{origin+',*':{'setting':1}}}}}}))
 proc=subprocess.Popen([chrome,'--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-extensions','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 ws=None
 try:
  p=Path(profile)/'DevToolsActivePort'
  for _ in range(100):
   if p.exists():break
   time.sleep(.1)
  port,path=p.read_text().splitlines()[:2];ws=websocket.create_connection('ws://127.0.0.1:'+port+path,timeout=15,suppress_origin=True)
  seq=0
  def cdp(method,params=None,sid=None):
   global seq
   seq+=1;m={'id':seq,'method':method,'params':params or {}}
   if sid:m['sessionId']=sid
   ws.send(json.dumps(m))
   while True:
    v=json.loads(ws.recv())
    if v.get('id')==seq:
     if 'error' in v:raise RuntimeError(str(v['error']))
     return v.get('result',{})
  tid=cdp('Target.createTarget',{'url':'about:blank'})['targetId'];sid=cdp('Target.attachToTarget',{'targetId':tid,'flatten':True})['sessionId']
  cdp('Page.enable',sid=sid);cdp('Emulation.setDeviceMetricsOverride',{'width':1280,'height':900,'deviceScaleFactor':1,'mobile':False},sid)
  def ev(expr):return cdp('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True},sid)['result'].get('value')
  def nav(u):cdp('Page.navigate',{'url':u},sid);time.sleep(2.2)
  def snap(n): (R/n).write_bytes(base64.b64decode(cdp('Page.captureScreenshot',{'format':'png','fromSurface':True},sid)['data']))
  def inspect():
   return ev("""(()=>{const a=[];function scan(root){for(const el of root.querySelectorAll('*')){if(el.shadowRoot)scan(el.shadowRoot);if(['SELECT','BUTTON','CR-ICON-BUTTON','CR-BUTTON','SETTINGS-DROPDOWN-MENU','OPTION','SITE-LIST-ENTRY','CR-ACTION-MENU'].includes(el.tagName)){let b=el.getBoundingClientRect();if(b.width&&b.height)a.push({tag:el.tagName,id:el.id,txt:(el.innerText||el.textContent||'').slice(0,160),aria:el.getAttribute('aria-label'),value:el.value,x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)})}}}scan(document);return a})()""")
  nav(origin);before=ev('Notification.permission');assert before=='granted',before;snap('01_granted.png')
  nav('chrome://settings/content/siteDetails?site='+__import__('urllib.parse',fromlist=['quote']).quote(origin,safe=''))
  snap('02_site_details.png');items=inspect();(R/'ui_inspect.json').write_text(json.dumps(items,indent=2));print('BEFORE',before,'UI',json.dumps(items,ensure_ascii=True),flush=True)
  # Native settings select: identify notifications row by label within its shadow host.
  target=ev("""(()=>{const a=[];function scan(r){for(const e of r.querySelectorAll('*')){if(e.shadowRoot)scan(e.shadowRoot);if(e.tagName==='SITE-DETAILS-PERMISSION'){const s=e.shadowRoot;const q=s&&s.querySelector('select');if(q){let b=q.getBoundingClientRect();a.push({label:q.getAttribute('aria-label'),options:[...q.options].map(x=>({text:x.text,value:x.value})),value:q.value,x:b.x+b.width/2,y:b.y+b.height/2})}}}}scan(document);return a})()""")
  print('PERMISSION_SELECTS',json.dumps(target,ensure_ascii=True),flush=True)
  (R/'permission_selects.json').write_text(json.dumps(target,indent=2))
  candidates=[x for x in target if 'notifications' in x['label'].lower() and x['value']=='allow']
  if len(candidates)!=1:raise RuntimeError('Native notification selector not uniquely located; no mutation')
  # Native DOM change in controlled profile only, using actual Settings element event.
  changed=ev("""(()=>{const a=[];function scan(r){for(const e of r.querySelectorAll('*')){if(e.shadowRoot)scan(e.shadowRoot);if(e.tagName==='SITE-DETAILS-PERMISSION'){const s=e.shadowRoot;const q=s&&s.querySelector('select');if(q&&q.getAttribute('aria-label')==='Notifications'&&q.value==='allow')a.push(q)}}}scan(document);if(a.length!==1)return false;const q=a[0];if(![...q.options].some(o=>o.value==='block'))return false;q.value='block';q.dispatchEvent(new Event('change',{bubbles:true,composed:true}));return true})()""")
  assert changed;time.sleep(2);snap('03_site_blocked.png')
  nav(origin);after=ev('Notification.permission');snap('04_denied.png');assert after=='denied',after
  evidence={'before':before,'after':after,'origin':origin,'isolated_profile':True,'method':'native Chrome settings select change via DOM event; local page reads actual Notification.permission','source':'https://support.google.com/chrome/answer/114662','captures':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(R.glob('*.png'))}}
  (R/'proof.json').write_text(json.dumps(evidence,indent=2));print('PROOF',json.dumps(evidence),flush=True)
 finally:
  if ws:ws.close()
  proc.terminate()
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.kill()
server.shutdown()
