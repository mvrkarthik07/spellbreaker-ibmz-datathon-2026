#!/usr/bin/env python3
"""Optional receiver-side AMLworld baseline. Skips cleanly when the dataset is absent."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,roc_auc_score
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default='data/HI-Small_Trans.csv');p.add_argument('--nrows',type=int,default=None);p.add_argument('--export-scores',default=None);a=p.parse_args();src=ROOT/a.data
 if not src.exists():print(f'SKIP: dataset absent: {src}');return 0
 df=pd.read_csv(src,nrows=a.nrows); cols=[c for c in df.select_dtypes(include='number').columns if c.lower() not in {'is_laundering','label'}]; target=next((c for c in df.columns if c.lower() in {'is_laundering','label'}),None)
 if not target:print('SKIP: no laundering label column found');return 0
 X=df[cols].fillna(0); y=df[target].astype(int); cut=int(len(df)*.8); model=HistGradientBoostingClassifier(max_iter=80,random_state=42).fit(X.iloc[:cut],y.iloc[:cut]); pr=model.predict_proba(X.iloc[cut:])[:,1]; test=df.iloc[cut:].copy();test['_score']=pr
 acct=next((c for c in df.columns if 'account' in c.lower() and ('to' in c.lower() or 'dest' in c.lower())),None)
 if acct and a.export_scores:
  out=test.assign(_label=y.iloc[cut:].values).groupby(acct).agg(score=('_score','mean'),is_mule=('_label','max')).reset_index().rename(columns={acct:'account'}); (ROOT/a.export_scores).parent.mkdir(exist_ok=True);out.to_csv(ROOT/a.export_scores,index=False)
  metrics={'siloed_pr_auc':float(average_precision_score(y.iloc[cut:],pr)),'collab_pr_auc':None,'oracle_pr_auc':None,'exposure_percent':0.0,'accounts':len(out)}
 else:metrics={'siloed_pr_auc':float(average_precision_score(y.iloc[cut:],pr)),'collab_pr_auc':None,'oracle_pr_auc':None,'exposure_percent':0.0}
 (ROOT/'results/mulenet_report.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
