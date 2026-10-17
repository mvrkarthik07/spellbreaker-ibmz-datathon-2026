import numpy as np

TEMPLATES={'on_call':"You're on an active phone call",'new_payee':"New payee you haven't paid before",'log_amount_ratio':'{x}× your usual transfer amount','balance_fraction':'Moves {p}% of your available balance','from_long_term_savings':'Drawn from your long-term savings','pasted_account':'Account number was pasted, not typed','rushed_score':'Unusually rushed or hesitant input','receiver_mule_score':'Receiving account shows money-mule behaviour ({s})','n_1h':'{n} transfers in the last hour','payee_repeat_escalation':'Payments to this payee keep increasing','clicked_flagged_link_recent':'You recently opened a link flagged as a scam','is_late_night':'Late-night transfer'}
HIDDEN_EXPLANATION_FEATURES={'hour_sin','hour_cos'}

def reasons(model,x,medians):
    keys=list(x)
    values=np.asarray([float(x[k]) for k in keys],dtype=np.float64)
    drops=[]
    if model is not None and len(keys):
        # First row is the observed transfer; each following row occludes one feature.
        matrix=np.tile(values,(len(keys)+1,1))
        for i,key in enumerate(keys):
            matrix[i+1,i]=float(medians.get(key,0.0))
        probabilities=model.predict_proba(matrix)[:,1]
        base=float(probabilities[0])
        drops=[(base-float(probabilities[i+1]),key,x[key]) for i,key in enumerate(keys) if key not in HIDDEN_EXPLANATION_FEATURES and base-float(probabilities[i+1])>.02]
    selected=[key for _,key,_ in sorted(drops,reverse=True)[:4]]
    if not selected:
        selected=sorted((k for k in x if k not in HIDDEN_EXPLANATION_FEATURES),key=lambda k:abs(float(x[k])),reverse=True)[:4]
    # Keep the call context visible even when correlated features absorb its occlusion credit.
    if x.get('on_call',0) and 'on_call' not in selected:
        selected=selected[:3]+['on_call']
    out=[]
    for key in selected:
        value=x[key]; template=TEMPLATES.get(key,key)
        out.append(template.format(x=f'{np.expm1(float(value)):.1f}',p=f'{float(value)*100:.0f}',s=f'{float(value):.2f}',n=int(value)) if '{' in template else template)
    return out
