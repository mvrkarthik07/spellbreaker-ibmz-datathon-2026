from datetime import datetime
import math
from .state import PAYEES

def build_features(payload, profile, mule_scores=None, legit_median_mule=.05):
    now=datetime.fromisoformat(payload['timestamp'].replace('Z','+00:00')) if payload.get('timestamp') else datetime.now().astimezone()
    if now.tzinfo: now=now.astimezone()
    history=profile['transfers']; acct=payload['payee_account']; amount=float(payload['amount']); flags=payload.get('flags') or {}
    recent1=[x for x in history if (now-datetime.fromisoformat(x['time'].replace('Z','+00:00')).astimezone()).total_seconds()<=3600]
    recent24=[x for x in history if (now-datetime.fromisoformat(x['time'].replace('Z','+00:00')).astimezone()).total_seconds()<=86400]
    prior=[x for x in history if x['payee_account']==acct]
    baseline=max(float(profile.get('usual_amount',150)),1.)
    mule=(mule_scores or {}).get(acct,PAYEES.get(acct,{}).get('mule',legit_median_mule))
    hour=now.hour
    return {'on_call':float(bool(flags.get('on_call'))),'pasted_account':float(bool(flags.get('pasted_account'))),'rushed_score':float(flags.get('rushed_score',0)),'clicked_flagged_link_recent':float(bool(flags.get('clicked_flagged_link_recent'))),'new_payee':float(acct not in profile['saved_payees']),'payee_repeat_escalation':float(bool(prior) and amount>prior[-1]['amount']),'n_1h':len(recent1),'n_24h':len(recent24),'n_new_payees_7d':sum(x['payee_account'] not in profile['saved_payees'] for x in history[-50:]),'log_amount_ratio':math.log1p(amount/baseline),'balance_fraction':amount/max(float(profile['current_balance'] if payload.get('source_pot')!='savings' else profile['savings_balance']),1.),'from_long_term_savings':float(payload.get('source_pot')=='savings'),'receiver_mule_score':float(mule),'hour_sin':math.sin(2*math.pi*hour/24),'hour_cos':math.cos(2*math.pi*hour/24),'is_late_night':float(hour>=22 or hour<=5)}
