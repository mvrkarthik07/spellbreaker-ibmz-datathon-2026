from __future__ import annotations
import json, platform, time
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from joblib import load
from .state import store, PAYEES
from .features import build_features
from .policy import decide
from .explain import reasons
from .genai import generate, RUNTIME

ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title='SpellBreaker — Merlion Bank')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
for path,name in [(ROOT/'web/bank','bank'),(ROOT/'web/dashboard','dashboard')]:
 app.mount('/'+name,StaticFiles(directory=str(path),html=True),name=name)
try: BUNDLE=load(ROOT/'models/spellbreaker_model.joblib')
except Exception: BUNDLE=None
try: REPORT=json.loads((ROOT/'results/model_report.json').read_text())
except Exception: REPORT={}
try: CURVES=json.loads((ROOT/'results/curves.json').read_text())
except Exception: CURVES={}
try:
 import pandas as pd
 df=pd.read_csv(ROOT/'results/mule_scores.csv'); MULE_SCORES={str(i):float(v) for i,v in zip(df.get('account',[]),df['score'])}
except Exception: MULE_SCORES={}
class ScoreIn(BaseModel):
 customer_id:str; payee_account:str; payee_name:str='Payee'; amount:float; source_pot:str='current'; flags:dict[str,Any]={}; timestamp:str|None=None
class ConfirmIn(BaseModel): decision_id:str; user_choice:str
@app.get('/')
def root():return RedirectResponse('/bank/')
@app.get('/health')
def health():return {'status':'ok','model_version':BUNDLE.get('version') if BUNDLE else 'stub-0','arch':platform.machine(),'trained_on':BUNDLE.get('trained_on') if BUNDLE else 'not-trained','genai':RUNTIME}
@app.post('/score')
def score(p:ScoreIn):
 start=time.perf_counter(); profile=store.profile(p.customer_id); stamp=p.timestamp or time.strftime('%Y-%m-%dT%H:%M:%S%z')
 payload=p.model_dump();payload['timestamp']=stamp
 x=build_features(payload,profile,MULE_SCORES); feats=BUNDLE['features'] if BUNDLE else list(x)
 vec={k:x.get(k,0) for k in feats}
 if BUNDLE:
  model=BUNDLE['risk_model']; risk=float(model.predict_proba([[vec[k] for k in feats]])[0][1]); typ=str(BUNDLE['type_model'].predict([[vec[k] for k in feats]])[0]); thresholds=BUNDLE['thresholds']; med=BUNDLE.get('legit_medians',{})
 else:
  risk=min(.999, .02 + .26*x['on_call']+.22*x['pasted_account']+.23*x['receiver_mule_score']+.15*x['from_long_term_savings']+.12*x['new_payee']+.08*x['rushed_score']);typ='gov_impersonation' if x['on_call'] and x['pasted_account'] else 'none';thresholds={'T1':.48,'T2':.65,'T3':.82};med={}
 level,action,question,message=decide(risk,thresholds,typ)
 rs=reasons(BUNDLE['risk_model'] if BUNDLE else None,vec,med)
 d=store.add_decision({'customer_id':p.customer_id,'payee_account':p.payee_account,'payee_name':p.payee_name,'amount':p.amount,'timestamp':stamp,'risk':risk,'level':level,'scam_type':typ,'scam_type_confidence':float(max(BUNDLE['type_model'].predict_proba([[vec[k] for k in feats]])[0])) if BUNDLE else .7,'action':action,'question':question,'message':message,'reasons':rs,'features_used':vec})
 d['latency_ms']=(time.perf_counter()-start)*1000
 d['scored_on']='IBM LinuxONE (s390x)' if platform.machine()=='s390x' else f'local dev ({platform.machine()})'
 return d
@app.post('/transfer/confirm')
def confirm(p:ConfirmIn):
 d=store.confirm(p.decision_id,p.user_choice)
 if not d:raise HTTPException(404,'decision not found')
 return {'status':'ok','outcome':d['outcome']}
@app.get('/decisions')
def decisions(limit:int=50):return store.decisions[:max(0,min(limit,500))]
@app.get('/case/{decision_id}')
async def case(decision_id:str):
 d=next((x for x in store.decisions if x['decision_id']==decision_id),None)
 if not d:raise HTTPException(404,'decision not found')
 if d['level'] not in ('HIGH','CRITICAL'):return {'note':'Case notes are prepared for HIGH and CRITICAL decisions.','runtime':RUNTIME}
 band=store.profile(d['customer_id']).get('age_band','unknown'); a=d['amount']; amt='under S$1k' if a<1000 else 'S$1k–10k' if a<10000 else 'S$10k–50k' if a<50000 else 'over S$50k'
 return {'note':await generate({'level':d['level'],'risk':d['risk'],'scam_type':d['scam_type'],'reasons':d['reasons'],'amount_band':amt,'age_band':band}),'runtime':RUNTIME}
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
