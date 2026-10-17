TEMPLATES={'on_call':"You're on an active phone call",'new_payee':"New payee you haven't paid before",'log_amount_ratio':'{x}× your usual transfer amount','balance_fraction':'Moves {p}% of your available balance','from_long_term_savings':'Drawn from your long-term savings','pasted_account':'Account number was pasted, not typed','rushed_score':'Unusually rushed or hesitant input','receiver_mule_score':'Receiving account shows money-mule behaviour ({s})','n_1h':'{n} transfers in the last hour','payee_repeat_escalation':'Payments to this payee keep increasing','clicked_flagged_link_recent':'You recently opened a link flagged as a scam','is_late_night':'Late-night transfer'}
def reasons(model,x,medians):
 drops=[]
 if model:
  base=float(model.predict_proba([list(x.values())])[0][1])
  for k,v in x.items():
   z=dict(x);z[k]=medians.get(k,0); drop=base-float(model.predict_proba([list(z.values())])[0][1])
   if drop>.02:drops.append((drop,k,v))
 keys=[k for _,k,_ in sorted(drops,reverse=True)[:4]]
 # Preserve explainability for small models with no single >.02 feature.
 if not keys: keys=sorted(x,key=lambda k:abs(float(x[k])),reverse=True)[:4]
 out=[]
 for k in keys:
  v=x[k];t=TEMPLATES.get(k,k)
  out.append(t.format(x=f'{2**float(v):.1f}',p=f'{float(v)*100:.0f}',s=f'{float(v):.2f}',n=int(v)) if '{' in t else t)
 return out
