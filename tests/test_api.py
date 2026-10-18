import os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from service.app import app
import urllib.request,json as _json
from service.state import store,SEED
from service.features import build_features
from ml.spellbreaker_train import training_live_features

BASE=os.getenv('BASE_URL')
if BASE:
 class RemoteResponse:
  def __init__(self,r):self.status_code=r.status;self._body=r.read()
  def json(self):return _json.loads(self._body)
 class RemoteClient:
  def get(self,path):return RemoteResponse(urllib.request.urlopen(BASE.rstrip('/')+path))
  def post(self,path,json=None):
   req=urllib.request.Request(BASE.rstrip('/')+path,data=_json.dumps(json or {}).encode(),headers={'Content-Type':'application/json'})
   return RemoteResponse(urllib.request.urlopen(req))
 client=RemoteClient()
else:client=TestClient(app)
def reset():client.post('/demo/reset')
def score(cid,acct,name,amount,pot='current',flags=None):
 return client.post('/score',json={'customer_id':cid,'payee_account':acct,'payee_name':name,'amount':amount,'source_pot':pot,'flags':flags or {}}).json()
def confirm(d,choice='proceed'):client.post('/transfer/confirm',json={'decision_id':d['decision_id'],'user_choice':choice})
def test_s1():
 reset();d=score('C-TAN','MB-778-201-9931','Secure Govt Account',20000,'savings',{'on_call':True,'pasted_account':True,'rushed_score':.8});assert d['level']=='CRITICAL' and d['scam_type']=='gov_impersonation';assert any('active phone call' in x for x in d['reasons'])
 deadline=time.monotonic()+30
 while True:
  note=client.get('/case/'+d['decision_id']).json()
  if note['status']=='ready' or time.monotonic()>=deadline:break
  time.sleep(.25)
 assert note['status']=='ready' and note['runtime'] in ('template (fallback)','granite (validated)')
 if note['validated']:
  assert len(note['note'].splitlines())==4 and note['note'].splitlines()[2]=='Likely scam: gov_impersonation'
 else:assert len(note['note'].split('. '))>=4
def test_s2():
 reset();d=score('C-TAN','MB-LANDLORD','Landlord',1800,'current',{'on_call':True,'pasted_account':False,'rushed_score':.2});assert d['level']=='LOW'
def test_s3():
 reset();d=score('C-LIM','MB-CONTRACTOR-NEW','New contractor',8000);assert d['level'] in ('LOW','MEDIUM')
def test_s4():
 reset()
 for amount in (500,1200,2800):d=score('C-RAJ','MB-554-310-1207','Apex Wealth Desk',amount);confirm(d)
 assert d['level'] in ('MEDIUM','HIGH','CRITICAL') and d['scam_type']=='investment'
def test_s5():
 reset()
 for amount in (30,80,160,400):d=score('C-RAJ','MB-201-889-4410','TaskHub Rewards',amount);confirm(d)
 assert d['level'] in ('MEDIUM','HIGH','CRITICAL') and d['scam_type']=='job'
def test_health_and_reset():
 reset();h=client.get('/health').json();assert h['status']=='ok' and h['arch'];assert client.post('/demo/reset').json()['status']=='ok'
def test_trace_endpoint_returns_a_redacted_decision_record():
 reset();d=score('C-TAN','MB-SP','SP Group',180)
 r=client.get('/trace/'+d['decision_id']);assert r.status_code==200
 trace=r.json();assert trace['decision_id']==d['decision_id'] and trace['level']==d['level']
 assert trace['model_version'] and 'latency_ms' in trace and trace['reasons']
 assert not {'customer_id','payee_account','payee_name','features_used'}.intersection(trace)
def test_live_trace_viewer_and_recent_endpoint_are_redacted():
 reset();first=score('C-TAN','MB-SP','SP Group',500,flags={});second=score('C-LIM','MB-NEW','New payee',200,flags={})
 page=client.get('/trace');assert page.status_code==200 and 'Request traces' in page.text and 'setInterval(refresh,2000)' in page.text
 response=client.get('/trace/recent?limit=1');assert response.status_code==200
 data=response.json();assert data['count']==1 and data['traces'][0]['decision_id']==second['decision_id']
 assert data['traces'][0]['created_at'] and not {'customer_id','payee_account','payee_name','features_used'}.intersection(data['traces'][0])
 assert client.get('/trace/'+first['decision_id']).json()['decision_id']==first['decision_id']
def test_trace_explanations_use_singapore_time_without_raw_hour_features():
 from service.explain import reasons
 profile=SEED['C-TAN'];payload={'timestamp':'2026-10-18T12:00:00+08:00','payee_account':'MB-SP','amount':500,'source_pot':'current','flags':{}}
 features=build_features(payload,profile,{})
 assert features['is_late_night']==0
 text=' '.join(reasons(None,features,{}))
 assert 'hour_sin' not in text and 'hour_cos' not in text and 'Late-night transfer' not in text
def test_trace_does_not_claim_absent_signals():
 reset();d=score('C-TAN','MB-SP','SP Group',500,flags={})
 assert not any('active phone call' in reason for reason in d['reasons'])
 assert d['message']=='This transfer is ready for your confirmation.'
def test_static_pages():assert client.get('/bank/').status_code==200 and client.get('/dashboard/').status_code==200

def test_feature_parity_100_sessions():
 from datetime import datetime,timezone,timedelta
 now=datetime(2026,10,18,12,tzinfo=timezone.utc)
 for i in range(100):
  profile={'usual_amount':100+i,'current_balance':10000+i,'savings_balance':50000+i,'saved_payees':({'P-0':50} if i%2 else {}),'transfers':[{'payee_account':'P-0','amount':20,'time':(now-timedelta(minutes=30+j)).isoformat()} for j in range(i%4)]}
  payload={'payee_account':f'P-{i%3}','amount':200+i,'source_pot':'savings' if i%2 else 'current','flags':{'on_call':bool(i%2),'pasted_account':bool(i%3),'rushed_score':i/100,'clicked_flagged_link_recent':bool(i%5)},'timestamp':now.isoformat()}
  assert build_features(payload,profile,{'P-1':.8})==training_live_features(payload,profile,{'P-1':.8})

def test_genai_fact_validator():
 from service.genai import validate_note, _expected_lines
 fact={'level':'CRITICAL','risk':.999,'scam_type':'gov_impersonation','reasons':['active call','new receiver (0.91)'],'amount_band':'S$10k–50k','age_band':'65+'}
 good='\n'.join(_expected_lines(fact))
 assert validate_note(good,fact)==(True,None)
 wrong=good.replace('Likely scam: gov_impersonation','Likely scam: investment')
 assert validate_note(wrong,fact)[1]=='predicted_scam_type_mismatch'
 extra=good.replace('99.9% risk','100% risk')
 assert validate_note(extra,fact)[1]=='number_not_in_fact_sheet'
 assert validate_note(good.replace('Next step:',''),fact)[1]=='missing_or_misordered_line'
 assert validate_note(good.replace('registered channel','Alice'),fact)[1]=='name_or_account_identifier'
 assert validate_note(good.replace('registered channel','MB-12345678'),fact)[1]=='name_or_account_identifier'
 assert validate_note(good.replace('registered channel','investment'),fact)[1]=='additional_scam_type'
