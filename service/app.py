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
from fastapi.responses import RedirectResponse
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
from .genai import template_note, RUNTIME

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
if DEBUG_TIMINGS:
 logging.basicConfig(level=logging.INFO)
 LOGGER.setLevel(logging.INFO)
class ScoreIn(BaseModel):
 customer_id:str; payee_account:str; payee_name:str='Payee'; amount:float; source_pot:str='current'; flags:dict[str,Any]={}; timestamp:Optional[str]=None
class ConfirmIn(BaseModel): decision_id:str; user_choice:str
@app.get('/')
def root():return RedirectResponse('/bank/')
@app.get('/health')
def health():return {'status':'ok','model_version':BUNDLE.get('version') if BUNDLE else 'stub-0','arch':platform.machine(),'trained_on':BUNDLE.get('trained_on') if BUNDLE else 'not-trained','genai':RUNTIME}
def prepare_case_note(decision_id: str, case_data: dict[str, Any]):
 # FastAPI runs this after the response has been sent.
 note=template_note(case_data)
 store.set_case_note(decision_id,note)

@app.post('/score')
async def score(p:ScoreIn, background_tasks:BackgroundTasks, request:Request):
 start=getattr(request.state,'spellbreaker_started',time.perf_counter()); marks={}; profile=store.profile(p.customer_id); stamp=p.timestamp or time.strftime('%Y-%m-%dT%H:%M:%S%z')
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
 d=store.add_decision({'customer_id':p.customer_id,'payee_account':p.payee_account,'payee_name':p.payee_name,'amount':p.amount,'timestamp':stamp,'risk':risk,'level':level,'scam_type':typ,'scam_type_confidence':type_confidence,'action':action,'question':question,'message':message,'reasons':rs,'features_used':vec})
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
  LOGGER.info('score_stage_timings_ms=%s',json.dumps(timings,separators=(',',':')))
 return d
@app.post('/transfer/confirm')
def confirm(p:ConfirmIn):
 d=store.confirm(p.decision_id,p.user_choice)
 if not d:raise HTTPException(404,'decision not found')
 return {'status':'ok','outcome':d['outcome']}
@app.get('/decisions')
def decisions(limit:int=50):return list(islice(store.decisions,max(0,min(limit,500))))
@app.get('/case/{decision_id}')
def case(decision_id:str):
 d=store.get_decision(decision_id)
 if not d:raise HTTPException(404,'decision not found')
 if d['level'] not in ('HIGH','CRITICAL'):return {'note':'Case notes are prepared for HIGH and CRITICAL decisions.','runtime':RUNTIME}
 return {'note':d.get('case_note'),'status':'ready' if d.get('case_note') else 'pending','runtime':RUNTIME}
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
