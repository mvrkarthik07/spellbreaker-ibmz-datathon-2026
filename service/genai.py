import json
import os
import re
import threading
from urllib.request import Request, urlopen

LLM_URL = os.environ.get('SPELLBREAKER_LLM_URL', '').rstrip('/')
RUNTIME = 'local-llm' if LLM_URL else 'template'
CASE_FIELDS = ('level', 'risk', 'scam_type', 'reasons', 'amount_band', 'age_band')
_LLM_GATE = threading.Lock()

def template_note(case):
 reasons=', '.join(case.get('reasons',[])) or 'an unusual transfer pattern'
 return (f"A {case.get('level','HIGH').lower()} risk transfer of {case.get('amount_band','an undisclosed amount')} was detected. "
         f"Indicators include {reasons}. The likely typology is {case.get('scam_type','unknown').replace('_',' ')}. "
         "Call the customer using the bank's registered number; ask them to end any active call and independently verify the recipient. "
         "If the customer insists and coercion remains apparent, consider whether a Protection from Scams Act escalation is warranted.")
def generate_note(case):
 if LLM_URL:
  if not _LLM_GATE.acquire(blocking=False):
   return template_note(case)
  # An explicit allow-list prevents names, payee accounts or raw transfer details
  # from reaching the local language-model process.
  try:
   payload={key:case.get(key) for key in CASE_FIELDS}
   request=Request(LLM_URL+'/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
   try:
    with urlopen(request,timeout=25) as response:
     note=json.loads(response.read()).get('note','').strip()
    if note:
     summary=re.sub(r'^\s*\d+[\).]\s*','',note.replace('\n',' ')).strip().strip('"\'')
     summary=summary.split('. ',1)[0].strip()
     if summary and summary[-1] not in '.!?':summary+='.'
     if len(summary.split())>=5:
      scam_type=(case.get('scam_type') or 'unknown').replace('_',' ')
      level=(case.get('level') or 'HIGH').lower()
      amount=case.get('amount_band') or 'an undisclosed amount'
      return (f"A {level} transfer of {amount} was flagged. "
              f"The likely scam type is {scam_type}; {summary} "
              "Call the customer using the bank's registered number and independently verify the recipient. "
              "If coercion persists, consider Protection from Scams Act escalation.")
   except Exception:
    pass
  finally:
   _LLM_GATE.release()
 return template_note(case)
