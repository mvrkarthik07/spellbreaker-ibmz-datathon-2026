def template_note(case):
 reasons=', '.join(case.get('reasons',[])) or 'an unusual transfer pattern'
 return (f"A {case.get('level','HIGH').lower()} risk transfer of {case.get('amount_band','an undisclosed amount')} was detected. "
         f"Indicators include {reasons}. The likely typology is {case.get('scam_type','unknown').replace('_',' ')}. "
         "Call the customer using the bank's registered number; ask them to end any active call and independently verify the recipient. "
         "If the customer insists and coercion remains apparent, consider whether a Protection from Scams Act escalation is warranted.")
async def generate(case): return template_note(case)
RUNTIME='template'
