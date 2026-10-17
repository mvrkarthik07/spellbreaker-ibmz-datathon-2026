import numpy as np
import pandas as pd
TEMPLATES={'on_call':"You're on an active phone call",'new_payee':"New payee you haven't paid before",'log_amount_ratio':'{x}× your usual transfer amount','balance_fraction':'Moves {p}% of your available balance','from_long_term_savings':'Drawn from your long-term savings','pasted_account':'Account number was pasted, not typed','rushed_score':'Unusually rushed or hesitant input','receiver_mule_score':'Receiving account shows money-mule behaviour ({s})','n_1h':'{n} transfers in the last hour','payee_repeat_escalation':'Payments to this payee keep increasing','clicked_flagged_link_recent':'You recently opened a link flagged as a scam','is_late_night':'Late-night transfer'}
def reasons(model,x,medians):
 drops=[]
 if model:
  keys=list(x); values=[float(x[k]) for k in keys]; base=float(model.predict_proba(pd.DataFrame([values],columns=keys))[0][1])
  rows=[]
  for k in keys:
   row=values.copy(); row[keys.index(k)]=float(medians.get(k,0)); rows.append(row)
  probs=model.predict_proba(pd.DataFrame(rows,columns=keys))[:,1]
  drops=[(base-float(p),k,x[k]) for k,p in zip(keys,probs) if base-float(p)>.02]
 keys=[k for _,k,_ in sorted(drops,reverse=True)[:4]]
 if not keys: keys=sorted(x,key=lambda k:abs(float(x[k])),reverse=True)[:4]
 # Keep observed on-call context visible when correlated features absorb its occlusion credit.
 if x.get('on_call',0) and 'on_call' not in keys: keys=keys[:3]+['on_call']
 out=[]
 for k in keys:
  v=x[k]; t=TEMPLATES.get(k,k)
  out.append(t.format(x=f'{np.expm1(float(v)):.1f}',p=f'{float(v)*100:.0f}',s=f'{float(v):.2f}',n=int(v)) if '{' in t else t)
 return out
