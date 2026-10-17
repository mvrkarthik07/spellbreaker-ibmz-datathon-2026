from copy import deepcopy
from collections import deque
from datetime import datetime, timezone
from uuid import uuid4

SEED={
'C-TAN':{'name':'Mdm Tan','age_band':'65+','usual_amount':300,'current_balance':9000,'savings_balance':85000,'saved_payees':{'MB-LANDLORD':1800,'MB-DAUGHTER':250,'MB-SP':180},'transfers':[]},
'C-LIM':{'name':'Mr Lim','age_band':'35-49','usual_amount':900,'current_balance':25000,'savings_balance':40000,'saved_payees':{'MB-LANDLORD':1800,'MB-CONTRACTOR':2500},'transfers':[]},
'C-RAJ':{'name':'Raj','age_band':'18-34','usual_amount':150,'current_balance':3000,'savings_balance':6000,'saved_payees':{'MB-FRIEND':60},'transfers':[]}}
PAYEES={'MB-778-201-9931':{'name':'Secure Govt Account','mule':.91},'MB-554-310-1207':{'name':'Apex Wealth Desk','mule':.8},'MB-201-889-4410':{'name':'TaskHub Rewards','mule':.75}}
class Store:
 def __init__(self): self.reset()
 def reset(self): self.customers=deepcopy(SEED); self.decisions=deque(maxlen=10000); self.by_id={}; self.counter=0
 def profile(self,cid): return self.customers.get(cid,self.customers['C-RAJ'])
 def add_decision(self,d):
  self.counter+=1; d['decision_id']=f'd_{uuid4().hex}'; d['created_at']=datetime.now(timezone.utc).isoformat(); d['outcome']=None
  if len(self.decisions)==self.decisions.maxlen: self.by_id.pop(self.decisions[-1]['decision_id'],None)
  self.decisions.appendleft(d); self.by_id[d['decision_id']]=d; return d
 def get_decision(self,did): return self.by_id.get(did)
 def set_case_note(self,did,result):
  d=self.by_id.get(did)
  if d is not None:
   d['case_note']=result['note']
   d['case_note_runtime']=result['runtime']
   d['case_note_validated']=bool(result.get('validated'))
   d['case_note_fallback_reason']=result.get('fallback_reason')
   d['case_note_generation_ms']=result.get('generation_ms')
 def confirm(self,did,choice):
  d=self.by_id.get(did)
  if not d:return None
  d['outcome']='proceeded' if choice=='proceed' else 'cancelled'
  p=self.profile(d['customer_id'])
  if choice=='proceed':
   p['transfers'].append({'payee_account':d['payee_account'],'amount':d['amount'],'time':d['timestamp']})
   p['saved_payees'][d['payee_account']]=d['amount']
  return d
store=Store()
def seed_demo():
 store.reset()
 return store
