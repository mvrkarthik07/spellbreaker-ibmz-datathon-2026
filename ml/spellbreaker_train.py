#!/usr/bin/env python3
"""Synthetic manipulated-customer transfer risk model for SpellBreaker."""
from __future__ import annotations
import argparse, json, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, recall_score, precision_score
from sklearn.model_selection import train_test_split

ROOT=Path(__file__).resolve().parents[1]
FEATS=['on_call','pasted_account','rushed_score','clicked_flagged_link_recent','new_payee','payee_repeat_escalation','n_1h','n_24h','n_new_payees_7d','log_amount_ratio','balance_fraction','from_long_term_savings','receiver_mule_score','hour_sin','hour_cos','is_late_night']
TYPES=['gov_impersonation','investment','job','phishing_led']

def synthesize(customers=5000, difficulty='realistic', seed=42):
    rng=np.random.default_rng(seed); n=max(6000,customers*5)
    y=(rng.random(n)<0.075).astype(int)
    typ=np.where(y==1,rng.choice(TYPES,n), 'none')
    age=rng.choice(['18-34','35-49','50-64','65+'],n,p=[.30,.30,.25,.15])
    # Victim representation is intentionally calibrated to ~15% 65+.
    victims=np.flatnonzero(y==1); old=rng.random(len(victims))<.15
    age[victims[old]]='65+'; age[victims[~old & (age[victims]=='65+')]]='50-64'
    scam=y.astype(bool); gov=typ=='gov_impersonation'; inv=typ=='investment'; job=typ=='job'; ph=typ=='phishing_led'
    oncall=rng.random(n)<np.where(scam,.28,.12 if difficulty=='realistic' else .05)
    pasted=rng.random(n)<np.where(gov,.32 if difficulty=='realistic' else .80,np.where(scam,.16,.08))
    rushed=np.clip(rng.beta(2,4,n)+scam*rng.normal(.08,.20,n),0,1)
    link=rng.random(n)<np.where(ph,.42,np.where(scam,.08,.025))
    newpay=rng.random(n)<np.where(scam,.40,.25)
    escalation=rng.random(n)<np.where(inv,.28,np.where(job,.18,.08))
    n1h=rng.poisson(np.where(scam,1.3,.16)); n24h=n1h+rng.poisson(np.where(scam,1.8,.55))
    nnew=rng.poisson(np.where(scam,1.2,.12))
    amount_ratio=np.exp(rng.normal(np.where(gov,np.log(5),np.where(inv,np.log(2.8),np.where(job,np.log(2),np.where(ph,np.log(2.8),np.log(2))))),1.05))
    amount_ratio=np.clip(amount_ratio,.1,100)
    balance=np.clip(rng.beta(1.5,9,n),0,1)
    balance=np.where(gov,rng.uniform(.4,1,n),balance)
    # Legitimate high-balance transfers are a small but meaningful overlap group.
    ordinary=(~scam)&(rng.random(n)<.10); balance[ordinary]=rng.uniform(.2,.75,ordinary.sum()); balance=np.where(inv,np.clip(rng.beta(2,3,n),.08,.9),balance)
    # Contractors and urgent family transfers create realistic hard negatives.
    hard=(~scam)&(rng.random(n)<.04)
    balance=np.where(hard,rng.uniform(.2,.7,n),balance)
    savings=rng.random(n)<np.where(gov,.55,np.where(inv,.35,np.where(hard,.25,.03)))
    mule=np.clip(rng.beta(np.where(scam,1.8,1.4),np.where(scam,4.5,6),n),0,1)
    hour=rng.integers(0,24,n); late=((hour>=22)|(hour<=5)).astype(int)
    # Explicit 3% behavioral label noise: scam behavior is drawn from ordinary sessions.
    noise=scam&(rng.random(n)<.03)
    for arr,p in [(oncall,.12),(pasted,.08),(link,.025),(newpay,.18),(escalation,.025),(savings,.03)]: arr[noise]=rng.random(noise.sum())<p
    rushed[noise]=rng.beta(2,5,noise.sum()); mule[noise]=rng.beta(1,18,noise.sum())
    # Realistic transfer-value basis; 65+ losses skew higher.
    median=np.where(age=='65+',37053, np.where(age=='50-64',9000,5000))
    amount=np.exp(rng.normal(np.log(median*amount_ratio),.25))
    amount=np.clip(amount,15,250000)
    df=pd.DataFrame(dict(on_call=oncall.astype(float),pasted_account=pasted.astype(float),rushed_score=rushed,clicked_flagged_link_recent=link.astype(float),new_payee=newpay.astype(float),payee_repeat_escalation=escalation.astype(float),n_1h=n1h,n_24h=n24h,n_new_payees_7d=nnew,log_amount_ratio=np.log1p(amount_ratio),balance_fraction=balance,from_long_term_savings=savings.astype(float),receiver_mule_score=mule,hour_sin=np.sin(2*np.pi*hour/24),hour_cos=np.cos(2*np.pi*hour/24),is_late_night=late,age_band=age,scam_type=typ,label=y,amount=amount,day=rng.integers(30,90,n)))
    return df

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--customers',type=int,default=5000); ap.add_argument('--loto',action='store_true'); ap.add_argument('--difficulty',choices=['realistic','easy'],default='realistic'); ap.add_argument('--seed',type=int,default=42); ap.add_argument('--mule-scores',default='results/mule_scores.csv'); a=ap.parse_args()
    t0=time.perf_counter(); ROOT.joinpath('results').mkdir(exist_ok=True); ROOT.joinpath('models').mkdir(exist_ok=True)
    df=synthesize(a.customers,a.difficulty,a.seed)
    mule_path=ROOT/a.mule_scores
    if mule_path.exists():
        try:
            ext=pd.read_csv(mule_path); vals=ext['score'].to_numpy(); df['receiver_mule_score']=np.resize(vals,len(df))
        except Exception as e: print(f'Mule scores ignored: {e}')
    train=df[df.day<=64].copy(); valid=df[(df.day>=65)&(df.day<=76)].copy(); test=df[df.day>=77].copy()
    med=train.loc[train.label==0,FEATS].median().to_dict()
    X=train[FEATS]; y=train.label
    model=HistGradientBoostingClassifier(max_iter=130,learning_rate=.08,max_leaf_nodes=12,l2_regularization=2,random_state=a.seed).fit(X,y)
    xt=test[FEATS]; yt=test.label; prob=model.predict_proba(xt)[:,1]
    vp=model.predict_proba(valid[FEATS])[:,1]; legit=vp[valid.label.to_numpy()==0]
    thresholds={f'T{i+1}':float(np.quantile(legit,q)) for i,q in enumerate([.99,.997,.999])}
    pred=prob>=thresholds['T1']; full={'pr_auc':float(average_precision_score(yt,prob)),'roc_auc':float(roc_auc_score(yt,prob)),'recall_at_t1':float(recall_score(yt,pred)),'precision_at_t1':float(precision_score(yt,pred,zero_division=0)),'legit_interruption_rate':float(np.mean(prob[yt.to_numpy()==0]>=thresholds['T1']))}
    # Calibrated rules baseline and per-scam metrics.
    rules=(test.on_call.astype(bool)&test.pasted_account.astype(bool)) | (test.receiver_mule_score>.78) | ((test.log_amount_ratio>2.1)&test.from_long_term_savings.astype(bool))
    rule_risk=rules.astype(float).to_numpy(); rules_full={'recall':float(np.mean(rules[yt.to_numpy()==1])),'legit_interruption_rate':float(np.mean(rules[yt.to_numpy()==0]))}
    bytype={}
    for typ in TYPES:
        m=(test.scam_type==typ); bytype[typ]=float(np.mean(prob[m]>=thresholds['T1'])) if m.any() else 0.
    fairness={}
    for band in ['18-34','35-49','50-64','65+']:
        m=test.age_band==band; legitm=m&(test.label==0); scam=m&(test.label==1)
        fairness[band]={'legit_interruption_rate':float(np.mean(prob[legitm]>=thresholds['T1'])) if legitm.any() else 0.,'scam_recall':float(np.mean(prob[scam]>=thresholds['T1'])) if scam.any() else 0.,'n_legit':int(legitm.sum()),'n_scam':int(scam.sum())}
    ablations={}
    for name,drop in [('no_behaviour',['on_call','pasted_account','rushed_score','clicked_flagged_link_recent']),('no_mule_score',['receiver_mule_score'])]:
        cols=[f for f in FEATS if f not in drop]; am=HistGradientBoostingClassifier(max_iter=90,learning_rate=.08,max_leaf_nodes=12,l2_regularization=2,random_state=a.seed).fit(train[cols],train.label); ablations[name]=float(average_precision_score(yt,am.predict_proba(test[cols])[:,1]))
    ablations['full']=full['pr_auc']
    loto={}
    if a.loto:
        for typ in TYPES:
            tr=train[train.scam_type!=typ]; te=test[test.scam_type==typ]
            mm=HistGradientBoostingClassifier(max_iter=100,learning_rate=.08,max_leaf_nodes=12,l2_regularization=2,random_state=a.seed).fit(tr[FEATS],tr.label)
            loto[typ]=float(np.mean(mm.predict_proba(te[FEATS])[:,1]>=thresholds['T1'])) if len(te) else 0.
    curve=[]
    for friction in np.linspace(.001,.05,20):
        threshold=float(np.quantile(prob[yt.to_numpy()==0],1-friction)); curve.append({'friction':float(friction),'ml_loss_prevented':float(np.mean(prob[(yt==1).to_numpy()]>=threshold)),'rules_loss_prevented':float(rules_full['recall'] if rules_full['legit_interruption_rate']<=friction else rules_full['recall']*friction/max(rules_full['legit_interruption_rate'],1e-6))})
    report={'full':full,'rules_baseline':rules_full,'thresholds':thresholds,'per_type_recall':bytype,'fairness_by_age_band':fairness,'ablations':ablations,'leave_one_type_out_recall':loto,'generation_parameters':{'difficulty':a.difficulty,'customers':a.customers,'rows':len(df),'scam_fraction':float(df.label.mean()),'hard_negative_rate':.04 if a.difficulty=='realistic' else .02,'behavioral_label_noise':.03 if a.difficulty=='realistic' else 0.,'overlap_adjustment':'on_call scam .28, pasted gov .32, new payee scam .40, 10% legit high-balance transfers','seed':a.seed},'latency_ms_per_score':float((time.perf_counter()-t0)*1000/max(len(test),1))}
    report['effectiveness_assumption']='Risk flags trigger a friction/interruption; prevented-loss curves assume interrupted scams are prevented.'
    bundle={'risk_model':model,'type_model':RandomForestClassifier(n_estimators=100,min_samples_leaf=3,class_weight='balanced',random_state=a.seed).fit(train[FEATS],train.scam_type),'features':FEATS,'thresholds':thresholds,'legit_medians':med,'effectiveness_assumption':report['effectiveness_assumption'],'difficulty':a.difficulty,'version':'0.1.0','trained_on':platform.machine(),'trained_at':datetime.now(timezone.utc).isoformat()}
    dump(bundle,ROOT/'models/spellbreaker_model.joblib')
    (ROOT/'results/model_report.json').write_text(json.dumps(report,indent=2))
    (ROOT/'results/curves.json').write_text(json.dumps({'loss_prevented_vs_friction':curve,'ablations':ablations,'per_type_recall':bytype,'leave_one_type_out_recall':loto,'fairness_by_age_band':fairness},indent=2))
    print(json.dumps({'full':full,'fairness_by_age_band':fairness,'elapsed_s':time.perf_counter()-t0},indent=2))
if __name__=='__main__': main()
