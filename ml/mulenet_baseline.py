#!/usr/bin/env python3
"""Optional receiver-side AMLworld baseline. Skips cleanly when the dataset is absent."""
import argparse,json,re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,roc_auc_score
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default='data/HI-Small_Trans.csv');p.add_argument('--nrows',type=int,default=None);p.add_argument('--export-scores',default=None);a=p.parse_args();src=ROOT/a.data
 if not src.exists():print(f'SKIP: dataset absent: {src}');return 0
 df=pd.read_csv(src,nrows=a.nrows)
 normalize=lambda c:re.sub(r'[^a-z0-9]','',str(c).lower())
 target=next((c for c in df.columns if normalize(c) in {'islaundering','label'}),None)
 if not target:raise ValueError(f'No laundering label column found; columns={list(df.columns)}')
 # HI-Small repeats "Account" for sender and receiver; pandas names the latter Account.1.
 acct=next((c for c in df.columns if normalize(c) in {'toaccount','destaccount','destinationaccount','receiveraccount','account1'}),None)
 if not acct:raise ValueError(f'No destination account column found; columns={list(df.columns)}')
 cols=[c for c in df.select_dtypes(include='number').columns if c!=target and normalize(c) not in {'label','islaundering'}]
 if not cols:raise ValueError('No numeric transaction features found')
 X=df[cols].fillna(0); y=df[target].astype(int); cut=int(len(df)*.8); model=HistGradientBoostingClassifier(max_iter=80,random_state=42).fit(X.iloc[:cut],y.iloc[:cut]); pr=model.predict_proba(X.iloc[cut:])[:,1]; test=df.iloc[cut:].copy();test['_score']=pr
 if acct and a.export_scores:
  out=test.assign(_label=y.iloc[cut:].values).groupby(acct,dropna=False).agg(score=('_score','mean'),is_mule=('_label','max')).reset_index().rename(columns={acct:'account'}); (ROOT/a.export_scores).parent.mkdir(exist_ok=True);out.to_csv(ROOT/a.export_scores,index=False)
  metrics={'siloed_pr_auc':float(average_precision_score(y.iloc[cut:],pr)),'collab_pr_auc':None,'oracle_pr_auc':None,'exposure_percent':0.0,'accounts':len(out),'rows_read':len(df),'train_rows':cut,'test_rows':len(y)-cut,'target_column':target,'receiver_account_column':acct,'features':cols,'nrows_limit':a.nrows}
 else:metrics={'siloed_pr_auc':float(average_precision_score(y.iloc[cut:],pr)),'collab_pr_auc':None,'oracle_pr_auc':None,'exposure_percent':0.0,'rows_read':len(df),'train_rows':cut,'test_rows':len(y)-cut,'target_column':target,'receiver_account_column':acct,'features':cols,'nrows_limit':a.nrows}
 (ROOT/'results/mulenet_report.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
