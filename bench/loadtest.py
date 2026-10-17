#!/usr/bin/env python3
import argparse,concurrent.futures,json,statistics,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://localhost:8000');p.add_argument('--requests',type=int,default=10000);p.add_argument('--concurrency',type=int,default=16);a=p.parse_args()
 def one(i):
  body=json.dumps({'customer_id':['C-TAN','C-LIM','C-RAJ'][i%3],'payee_account':f'MB-TEST-{i%37}','payee_name':'Demo payee','amount':100+(i%8000),'source_pot':'current' if i%2 else 'savings','flags':{'on_call':i%7==0,'pasted_account':i%11==0,'rushed_score':(i%100)/100,'clicked_flagged_link_recent':i%43==0}}).encode();req=urllib.request.Request(a.url+'/score',data=body,headers={'Content-Type':'application/json'});t=time.perf_counter()
  with urllib.request.urlopen(req,timeout=30) as r:d=json.load(r)
  return (time.perf_counter()-t)*1000,float(d['latency_ms'])
 t=time.perf_counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.concurrency) as pool: vals=list(pool.map(one,range(a.requests)))
 elapsed=time.perf_counter()-t;roundtrip=sorted(x[0] for x in vals);server=sorted(x[1] for x in vals)
 def pct(x,q):return x[min(len(x)-1,int((len(x)-1)*q))]
 report={'requests':a.requests,'concurrency':a.concurrency,'duration_s':elapsed,'rps':a.requests/elapsed,'client_round_trip_ms':{'p50':pct(roundtrip,.5),'p95':pct(roundtrip,.95),'p99':pct(roundtrip,.99)},'server_latency_ms':{'p50':pct(server,.5),'p95':pct(server,.95),'p99':pct(server,.99)}}
 (ROOT/'results/bench.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
