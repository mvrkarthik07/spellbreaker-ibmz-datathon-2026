from __future__ import annotations
import os
# Set native math-library limits before joblib loads a scikit-learn model.
for _thread_var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_thread_var] = '1'

import csv, json, logging, platform, time
from itertools import islice
from pathlib import Path
from typing import Any, Optional
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import numpy as np
from joblib import load
from threadpoolctl import threadpool_limits

# Small batch inference is faster and more stable without OpenMP oversubscription.
_INFERENCE_THREADS = threadpool_limits(limits=1)
from .state import store, PAYEES
from .features import build_features
from .policy import decide
from .explain import reasons
from .genai import generate_note, RUNTIME

ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title='SpellBreaker — Merlion Bank')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
@app.middleware('http')
async def mark_request_start(request:Request, call_next):
 request.state.spellbreaker_started=time.perf_counter()
 return await call_next(request)
for path,name in [(ROOT/'web/bank','bank'),(ROOT/'web/dashboard','dashboard')]:
 app.mount('/'+name,StaticFiles(directory=str(path),html=True),name=name)
try: BUNDLE=load(ROOT/'models/spellbreaker_model.joblib')
except Exception: BUNDLE=None
RISK_MODEL=BUNDLE.get('risk_model') if BUNDLE else None
TYPE_MODEL=BUNDLE.get('type_model') if BUNDLE else None
FEATURES=BUNDLE.get('features') if BUNDLE else None
THRESHOLDS=BUNDLE.get('thresholds') if BUNDLE else {'T1':.48,'T2':.65,'T3':.82}
LEGIT_MEDIANS=BUNDLE.get('legit_medians',{}) if BUNDLE else {}
try: REPORT=json.loads((ROOT/'results/model_report.json').read_text())
except Exception: REPORT={}
try: CURVES=json.loads((ROOT/'results/curves.json').read_text())
except Exception: CURVES={}
try:
 with (ROOT/'results/mule_scores.csv').open(newline='') as f:
  MULE_SCORES={str(row['account']):float(row['score']) for row in csv.DictReader(f) if row.get('account') and row.get('score')}
except Exception: MULE_SCORES={}
DEBUG_TIMINGS=os.getenv('SPELLBREAKER_DEBUG_TIMINGS','0').lower() in ('1','true','yes')
LOGGER=logging.getLogger('spellbreaker.score')
LOGGER.setLevel(logging.INFO)
LOGGER.propagate=False
if not LOGGER.handlers:
 _handler=logging.StreamHandler()
 _handler.setFormatter(logging.Formatter('%(message)s'))
 LOGGER.addHandler(_handler)
if DEBUG_TIMINGS:
 logging.basicConfig(level=logging.INFO)
class ScoreIn(BaseModel):
 customer_id:str; payee_account:str; payee_name:str='Payee'; amount:float; source_pot:str='current'; flags:dict[str,Any]={}; timestamp:Optional[str]=None
class ConfirmIn(BaseModel): decision_id:str; user_choice:str
@app.get('/')
def root():return RedirectResponse('/bank/')
@app.get('/health')
def health():return {'status':'ok','model_version':BUNDLE.get('version') if BUNDLE else 'stub-0','arch':platform.machine(),'trained_on':BUNDLE.get('trained_on') if BUNDLE else 'not-trained','genai':RUNTIME}
def prepare_case_note(decision_id: str, case_data: dict[str, Any]):
 # FastAPI runs this after the response has been sent.
 result=generate_note(case_data)
 if result.get('fallback_reason'):
  logging.getLogger('spellbreaker.genai').warning(
   'case_note_fallback decision_id=%s reason=%s generation_ms=%s',
   decision_id,result['fallback_reason'],result.get('generation_ms'))
 store.set_case_note(decision_id,result)

@app.post('/score')
async def score(p:ScoreIn, background_tasks:BackgroundTasks, request:Request):
 start=getattr(request.state,'spellbreaker_started',time.perf_counter()); marks={}; profile=store.profile(p.customer_id)
 if p.amount<=0:raise HTTPException(status_code=422,detail='Enter a transfer amount greater than zero.')
 balance_key='savings_balance' if p.source_pot=='savings' else 'current_balance'; available=float(profile.get(balance_key,0.))
 if p.amount>available:raise HTTPException(status_code=422,detail=f'Insufficient funds. Selected account has S${available:,.2f} available.')
 stamp=p.timestamp or time.strftime('%Y-%m-%dT%H:%M:%S%z')
 payload=(p.model_dump() if hasattr(p,'model_dump') else p.dict());payload['timestamp']=stamp
 marks['parse']=time.perf_counter()
 x=build_features(payload,profile,MULE_SCORES); feats=FEATURES if BUNDLE else list(x)
 vec={k:x.get(k,0) for k in feats}; row=np.asarray([[vec[k] for k in feats]],dtype=np.float64)
 marks['features']=time.perf_counter()
 if BUNDLE:
  risk=float(RISK_MODEL.predict_proba(row)[0][1]); thresholds=THRESHOLDS; med=LEGIT_MEDIANS
 else:
  risk=min(.999, .02 + .26*x['on_call']+.22*x['pasted_account']+.23*x['receiver_mule_score']+.15*x['from_long_term_savings']+.12*x['new_payee']+.08*x['rushed_score']);typ='gov_impersonation' if x['on_call'] and x['pasted_account'] else 'none';thresholds=THRESHOLDS;med=LEGIT_MEDIANS
 marks['m1']=time.perf_counter()
 if BUNDLE:
  type_probabilities=TYPE_MODEL.predict_proba(row)[0]
  typ=str(TYPE_MODEL.classes_[int(np.argmax(type_probabilities))]); type_confidence=float(np.max(type_probabilities))
 else: type_confidence=.7
 marks['m2']=time.perf_counter()
 rs=reasons(RISK_MODEL,vec,med)
 marks['explain']=time.perf_counter()
 level,action,question,message=decide(risk,thresholds,typ)
 marks['policy']=time.perf_counter()
 d=store.add_decision({'customer_id':p.customer_id,'payee_account':p.payee_account,'payee_name':p.payee_name,'amount':p.amount,'source_pot':p.source_pot,'timestamp':stamp,'risk':risk,'level':level,'scam_type':typ,'scam_type_confidence':type_confidence,'action':action,'question':question,'message':message,'reasons':rs,'features_used':vec,'model_version':BUNDLE.get('version') if BUNDLE else 'stub-0'})
 if level in ('HIGH','CRITICAL'):
  age_band=profile.get('age_band','unknown'); amount=p.amount
  amount_band='under S$1k' if amount<1000 else 'S$1k–10k' if amount<10000 else 'S$10k–50k' if amount<50000 else 'over S$50k'
  background_tasks.add_task(prepare_case_note,d['decision_id'],{'level':level,'risk':risk,'scam_type':typ,'reasons':rs,'amount_band':amount_band,'age_band':age_band})
 marks['logging']=time.perf_counter()
 d['latency_ms']=(marks['logging']-start)*1000
 d['scored_on']='IBM LinuxONE (s390x)' if platform.machine()=='s390x' else f'local dev ({platform.machine()})'
 if DEBUG_TIMINGS:
  timings={name:round((marks[name]- (start if i==0 else marks[list(marks)[i-1]]))*1000,3) for i,name in enumerate(marks)}
  timings['total']=round((time.perf_counter()-start)*1000,3)
  d['debug_timings_ms']=timings
 trace={'event':'score_decision','decision_id':d['decision_id'],'model_version':d['model_version'],'scored_on':d['scored_on'],'level':level,'risk':round(risk,6),'scam_type':typ,'action':action,'latency_ms':round(d['latency_ms'],3)}
 if DEBUG_TIMINGS:trace['debug_timings_ms']=d['debug_timings_ms']
 LOGGER.info(json.dumps(trace,separators=(',',':')))
 return d
@app.post('/transfer/confirm')
def confirm(p:ConfirmIn):
 if p.user_choice not in ('proceed','cancel'):raise HTTPException(422,'Choose proceed or cancel.')
 decision=store.get_decision(p.decision_id)
 if not decision:raise HTTPException(404,'decision not found')
 if decision['level']=='CRITICAL' and p.user_choice=='proceed':
  raise HTTPException(409,'Critical transfers are held for bank verification and cannot be continued here.')
 d=store.confirm(p.decision_id,p.user_choice)
 return {'status':'ok','outcome':d['outcome']}
@app.get('/decisions')
def decisions(limit:int=50):return list(islice(store.decisions,max(0,min(limit,500))))

def redacted_trace(d):
 keys=('decision_id','model_version','scored_on','created_at','timestamp','risk','level','scam_type','scam_type_confidence','action','question','message','reasons','latency_ms','debug_timings_ms','outcome')
 return {key:d[key] for key in keys if key in d}

@app.get('/trace',response_class=HTMLResponse)
def trace_viewer():
 return HTMLResponse('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SpellBreaker request traces</title><style>
:root{color-scheme:light;--ink:#172b3a;--muted:#617887;--line:#dce5eb;--bg:#f4f7f9;--blue:#176d83}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:1180px;margin:36px auto;padding:0 22px}header{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:20px}h1{font-size:25px;line-height:1.2;margin:0 0 6px}p{margin:0;color:var(--muted)}#status{white-space:nowrap;color:var(--blue);font-weight:650}.panel{background:white;border:1px solid var(--line);border-radius:12px;overflow:hidden}.notice{padding:12px 16px;border-bottom:1px solid var(--line);color:var(--muted);font-size:13px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#f9fbfc;color:var(--muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase}tr:last-child td{border-bottom:0}.id{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--blue);text-decoration:none}.id:hover{text-decoration:underline}.level{font-weight:750}.risk,.latency{font-variant-numeric:tabular-nums;white-space:nowrap}.reason{color:var(--muted);max-width:330px}.empty{padding:35px;text-align:center;color:var(--muted)}@media(max-width:750px){main{margin:18px auto;padding:0 12px}.wide{display:none}th,td{padding:10px 8px;font-size:12px}}
</style><main><header><div><h1>Request traces</h1><p>Recent scored transfers · redacted · refreshes every 2 seconds</p></div><div id="status">Connecting…</div></header><section class="panel"><div class="notice">Trace records are held in service memory and clear on reset or restart. For retained server output, use <code>docker logs -f spellbreaker</code> on LinuxONE.</div><table><thead><tr><th>Scored</th><th>Decision ID</th><th>Level</th><th>Risk</th><th>Scam type</th><th>Latency</th><th class="wide">Reasons</th></tr></thead><tbody id="rows"><tr><td colspan="7" class="empty">Loading recent requests…</td></tr></tbody></table></section></main><script>
const rows=document.querySelector('#rows'),status=document.querySelector('#status');function cell(text,cls){const e=document.createElement('td');e.textContent=text??'—';if(cls)e.className=cls;return e}function refresh(){fetch('/trace/recent?limit=100',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(data=>{rows.replaceChildren();if(!data.traces.length){const tr=document.createElement('tr'),td=cell('No scored requests in memory yet.','empty');td.colSpan=7;tr.append(td);rows.append(tr)}for(const d of data.traces){const tr=document.createElement('tr'),time=d.created_at?new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date(d.created_at)):'—',link=document.createElement('a');link.className='id';link.href='/trace/'+encodeURIComponent(d.decision_id);link.textContent=d.decision_id;const id=cell('');id.append(link);tr.append(cell(time),id,cell(d.level,'level'),cell((Number(d.risk)*100).toFixed(2)+'%','risk'),cell(d.scam_type),cell(Number(d.latency_ms).toFixed(2)+' ms','latency'),cell((d.reasons||[]).join(' · '),'reason'));rows.append(tr)}status.textContent='Live · '+new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date())}).catch(e=>{status.textContent='Trace service unavailable';console.error(e)})}refresh();setInterval(refresh,2000);
</script></html>''')

@app.get('/trace/recent')
def recent_traces(limit:int=50):
 limit=max(1,min(limit,100))
 records=[redacted_trace(d) for d in islice(store.decisions,limit)]
 return {'count':len(records),'traces':records}

@app.get('/trace/{decision_id}')
def trace(decision_id:str):
 d=store.get_decision(decision_id)
 if not d:raise HTTPException(404,'decision not found')
 return redacted_trace(d)
@app.get('/case/{decision_id}')
def case(decision_id:str):
 d=store.get_decision(decision_id)
 if not d:raise HTTPException(404,'decision not found')
 if d['level'] not in ('HIGH','CRITICAL'):return {'note':'Case notes are prepared for HIGH and CRITICAL decisions.','runtime':RUNTIME,'validated':False}
 return {'note':d.get('case_note'),'status':'ready' if d.get('case_note') else 'pending','runtime':d.get('case_note_runtime',RUNTIME),'validated':d.get('case_note_validated',False),'fallback_reason':d.get('case_note_fallback_reason'),'generation_ms':d.get('case_note_generation_ms')}
@app.get('/report')
def report():
 out=dict(REPORT);out['curves']=CURVES
 bp=ROOT/'results/bench.json'
 if bp.exists():out['bench']=json.loads(bp.read_text())
 return out
@app.get('/privacy')
def privacy():return {'sent':['on_call (yes/no)','pasted_account (yes/no)','rushed_score (0–1)','clicked_flagged_link_recent (yes/no)','transfer details'],'never_sent':['caller number','call audio','contacts','messages','clipboard contents','raw keystroke timings','location'],'processing':'Scoring and case-note generation are designed to run locally on the bank platform.'}
@app.post('/demo/reset')
def reset():store.reset();return {'status':'ok'}
