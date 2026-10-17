from copy import deepcopy
from datetime import datetime, timezone

SEED={
'C-TAN':{'name':'Mdm Tan','age_band':'65+','usual_amount':300,'current_balance':9000,'savings_balance':85000,'saved_payees':{'MB-LANDLORD':1800,'MB-DAUGHTER':250,'MB-SP':180},'transfers':[]},
'C-LIM':{'name':'Mr Lim','age_band':'35-49','usual_amount':900,'current_balance':25000,'savings_balance':40000,'saved_payees':{'MB-LANDLORD':1800,'MB-CONTRACTOR':2500},'transfers':[]},
'C-RAJ':{'name':'Raj','age_band':'18-34','usual_amount':150,'current_balance':3000,'savings_balance':6000,'saved_payees':{'MB-FRIEND':60},'transfers':[]}}
PAYEES={'MB-778-201-9931':{'name':'Secure Govt Account','mule':.91},'MB-554-310-1207':{'name':'Apex Wealth Desk','mule':.8},'MB-201-889-4410':{'name':'TaskHub Rewards','mule':.75}}
class Store:
 def __init__(self): self.reset()
 def reset(self): self.customers=deepcopy(SEED); self.decisions=[]; self.counter=0
 def profile(self,cid): return self.customers.get(cid,self.customers['C-RAJ'])
 def add_decision(self,d): self.counter+=1; d['decision_id']=f'd_{self.counter:06d}'; d['created_at']=datetime.now(timezone.utc).isoformat(); d['outcome']=None; self.decisions.insert(0,d); return d
 def confirm(self,did,choice):
  d=next((x for x in self.decisions if x['decision_id']==did),None)
  if not d:return None
  d['outcome']='proceeded' if choice=='proceed' else 'cancelled'
  p=self.profile(d['customer_id']); p['transfers'].append({'payee_account':d['payee_account'],'amount':d['amount'],'time':d['timestamp']})
  if choice=='proceed':p['saved_payees'][d['payee_account']]=d['amount']
  return d
store=Store()
