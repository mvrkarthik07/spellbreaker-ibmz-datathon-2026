const $ = id => document.getElementById(id);

let lastDecision = null;
let typed = [];
let holdTimer = null;
let balancesHidden = false;

const profiles = {
  'C-TAN': { name: 'Mdm Tan', initial: 'T', current: 9000, savings: 85000 },
  'C-LIM': { name: 'Mr Lim', initial: 'L', current: 25000, savings: 40000 },
  'C-RAJ': { name: 'Raj', initial: 'R', current: 3000, savings: 6000 }
};

const money = amount => `S$${Number(amount).toLocaleString('en-SG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[char]));

function updateGreeting() {
  const hour = new Date().getHours();
  const part = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening';
  $('greeting').textContent = `Good ${part}, ${profiles[$('customer').value].name}`;
  $('today').textContent = new Intl.DateTimeFormat('en-SG', {
    weekday: 'long', day: 'numeric', month: 'long'
  }).format(new Date()).toUpperCase();
}

function displayBalance(amount) {
  return balancesHidden ? '••••••' : money(amount);
}

function updateCustomer() {
  const profile = profiles[$('customer').value];
  $('avatar').textContent = profile.initial;
  $('current').textContent = displayBalance(profile.current);
  $('savings').textContent = displayBalance(profile.savings);
  $('total-balance').textContent = displayBalance(profile.current + profile.savings);
  $('current-number').textContent = $('customer').value === 'C-TAN' ? '•• 2846' : $('customer').value === 'C-LIM' ? '•• 3418' : '•• 1906';
  $('savings-number').textContent = $('customer').value === 'C-TAN' ? '•• 5721' : $('customer').value === 'C-LIM' ? '•• 6620' : '•• 4472';
  updateGreeting();
  refreshRecent();
}

function rushedSignal() {
  if (typed.length < 3) return 0.15;
  const gaps = typed.slice(1).map((time, index) => time - typed[index]);
  const average = gaps.reduce((sum, gap) => sum + gap, 0) / gaps.length;
  return Math.max(0, Math.min(1, (700 - average) / 600));
}

function setPayee(name, account, choice = 'new') {
  $('payeeChoice').value = choice;
  $('name').value = name;
  $('account').value = account;
  const saved = choice !== 'new';
  $('name').readOnly = saved;
  $('account').readOnly = saved;
  $('account').dataset.pasted = 'false';
}

function refreshRecent() {
  fetch('/decisions?limit=50')
    .then(response => response.json())
    .then(decisions => {
      const rows = decisions.filter(item => item.customer_id === $('customer').value).slice(0, 4);
      if (!rows.length) {
        $('recent').innerHTML = '<div class="empty-state"><span class="empty-icon" aria-hidden="true">↗</span><div><strong>No recent transfers</strong><p>Payments you review will appear here.</p></div></div>';
        return;
      }
      $('recent').innerHTML = rows.map(item => {
        const status = item.outcome || item.level.toLowerCase();
        const time = item.created_at ? new Intl.DateTimeFormat('en-SG', { hour: '2-digit', minute: '2-digit' }).format(new Date(item.created_at)) : 'Recently';
        return `<article class="activity-item">
          <span class="activity-icon" aria-hidden="true">↗</span>
          <span class="activity-details"><strong>${escapeHtml(item.payee_name)}</strong><small>${escapeHtml(time)} · ${escapeHtml(item.payee_account)}</small></span>
          <span class="activity-amount"><strong>${escapeHtml(money(item.amount))}</strong><small>${escapeHtml(status)}</small></span>
        </article>`;
      }).join('');
    })
    .catch(() => {
      $('recent').innerHTML = '<div class="empty-state"><span class="empty-icon" aria-hidden="true">↗</span><div><strong>Activity is unavailable</strong><p>Please try again in a moment.</p></div></div>';
    });
}

function showScreen(id) {
  ['home', 'form', 'result'].forEach(screenId => $(screenId).classList.toggle('hidden', screenId !== id));
  if (id === 'form') {
    typed = [];
    $('form-error').hidden = true;
    $('form-error').textContent = '';
  }
}

async function scoreScenario(preset) {
  if (preset === 'S4' || preset === 'S5') {
    await fetch('/demo/reset', { method: 'POST' });
    const sequence = preset === 'S4'
      ? [['MB-554-310-1207', 'Apex Wealth Desk', 500], ['MB-554-310-1207', 'Apex Wealth Desk', 1200]]
      : [['MB-201-889-4410', 'TaskHub Rewards', 30], ['MB-201-889-4410', 'TaskHub Rewards', 80], ['MB-201-889-4410', 'TaskHub Rewards', 160]];
    for (const [account, name, amount] of sequence) {
      const response = await fetch('/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: 'C-RAJ', payee_account: account, payee_name: name, amount, source_pot: 'current', flags: {} })
      });
      const decision = await response.json();
      await fetch('/transfer/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision_id: decision.decision_id, user_choice: 'proceed' })
      });
    }
  }

  if (preset === 'S1') {
    $('customer').value = 'C-TAN'; setPayee('Secure Govt Account', 'MB-778-201-9931');
    $('amount').value = 20000; $('pot').value = 'savings'; $('call').checked = true; $('account').dataset.pasted = 'true';
  } else if (preset === 'S2') {
    $('customer').value = 'C-TAN'; setPayee('Landlord', 'MB-LANDLORD', 'MB-LANDLORD');
    $('amount').value = 1800; $('pot').value = 'current'; $('call').checked = true;
  } else if (preset === 'S3') {
    $('customer').value = 'C-LIM'; setPayee('New contractor', 'MB-CONTRACTOR-NEW');
    $('amount').value = 8000; $('pot').value = 'current'; $('call').checked = false;
  } else if (preset === 'S4') {
    $('customer').value = 'C-RAJ'; setPayee('Apex Wealth Desk', 'MB-554-310-1207');
    $('amount').value = 2800; $('pot').value = 'current'; $('call').checked = false;
  } else if (preset === 'S5') {
    $('customer').value = 'C-RAJ'; setPayee('TaskHub Rewards', 'MB-201-889-4410');
    $('amount').value = 400; $('pot').value = 'current'; $('call').checked = false;
  }
  updateCustomer();
  showScreen('form');
  $('controls').open = false;
}

function resultCopy(decision) {
  if (decision.level === 'LOW') return {
    label: 'SECURITY CHECK COMPLETE',
    title: 'This transfer can proceed',
    description: 'No high-risk pattern was identified in this review.'
  };
  if (decision.level === 'MEDIUM') return {
    label: 'PLEASE REVIEW',
    title: 'Pause and check before sending',
    description: decision.question || 'Do you know and trust this recipient?'
  };
  if (decision.level === 'HIGH') return {
    label: '30-MINUTE SAFETY PAUSE',
    title: 'Take time to verify this request',
    description: 'This transfer is paused for 30 minutes. If someone is guiding you, end the call and verify the request another way.'
  };
  return {
    label: 'ADDITIONAL VERIFICATION',
    title: 'We need to verify this transfer',
    description: 'This transfer is on hold. Contact Merlion Bank using the number on your card before trying again.'
  };
}

function render(decision) {
  lastDecision = decision;
  showScreen('result');
  if (holdTimer) clearInterval(holdTimer);
  const copy = resultCopy(decision);
  const amount = money($('amount').value);
  const recipient = escapeHtml($('name').value);
  const reasons = (decision.reasons || []).map(reason => `<div class="reason">${escapeHtml(reason)}</div>`).join('');
  const question = decision.level === 'LOW' ? '' : `<p class="result-question">${escapeHtml(decision.question || '')}</p>`;
  const timer = decision.level === 'HIGH' ? '<div class="hold-timer" id="countdown">30:00</div><p class="trusted-contact">Use this time to speak with someone you trust, using a contact method you already know.</p>' : '';
  const actions = decision.level === 'LOW'
    ? '<div class="result-actions"><button class="done-button" onclick="finish(\'proceed\')">Done</button></div>'
    : '<div class="result-actions"><button onclick="finish(\'cancel\')">Stop this transfer</button><button class="continue-button" onclick="finish(\'proceed\')">Continue transfer</button></div>';

  $('result').innerHTML = `<article class="result-card ${escapeHtml(decision.level)}">
    <p class="result-status"><span aria-hidden="true">●</span>${copy.label}</p>
    <h1>${copy.title}</h1>
    <p class="result-description">${copy.description}</p>
    <div class="transfer-summary"><span><small>Recipient</small><strong>${recipient}</strong></span><span class="summary-amount">${escapeHtml(amount)}</span></div>
    ${question}
    ${timer}
    <details class="result-reasons"><summary>Why this transfer was reviewed</summary>${reasons}</details>
    ${actions}
    <p class="stop-guidance">If you are in Singapore and believe you are being scammed, call ScamShield at <strong>1799</strong>.</p>
  </article>`;

  if (decision.level === 'HIGH') {
    let remaining = 1800;
    holdTimer = setInterval(() => {
      remaining = Math.max(0, remaining - 1);
      const clock = $('countdown');
      if (clock) clock.textContent = `${String(Math.floor(remaining / 60)).padStart(2, '0')}:${String(remaining % 60).padStart(2, '0')}`;
      if (!remaining) clearInterval(holdTimer);
    }, 1000);
  }
}

async function finish(choice) {
  if (!lastDecision) return;
  try {
    await fetch('/transfer/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision_id: lastDecision.decision_id, user_choice: choice })
    });
  } finally {
    lastDecision = null;
    if (holdTimer) clearInterval(holdTimer);
    showScreen('home');
    refreshRecent();
  }
}

$('start').addEventListener('click', () => showScreen('form'));
$('back').addEventListener('click', () => { showScreen('home'); refreshRecent(); });
$('customer').addEventListener('change', updateCustomer);
$('gear').addEventListener('click', () => { $('controls').open = !$('controls').open; });
$('toggle-balance').addEventListener('click', event => {
  balancesHidden = !balancesHidden;
  event.currentTarget.setAttribute('aria-pressed', String(balancesHidden));
  event.currentTarget.setAttribute('aria-label', balancesHidden ? 'Show balances' : 'Hide balances');
  updateCustomer();
});
$('payeeChoice').addEventListener('change', () => {
  const savedPayees = {
    'MB-LANDLORD': ['Landlord', 'MB-LANDLORD'],
    'MB-DAUGHTER': ['Daughter', 'MB-DAUGHTER'],
    'MB-SP': ['SP Group', 'MB-SP'],
    'MB-CONTRACTOR': ['Known contractor', 'MB-CONTRACTOR'],
    'MB-FRIEND': ['Friend', 'MB-FRIEND']
  };
  const recipient = savedPayees[$('payeeChoice').value];
  if (recipient) setPayee(recipient[0], recipient[1], $('payeeChoice').value);
  else setPayee('', '');
});
document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => scoreScenario(button.dataset.preset)));
$('reset').addEventListener('click', async () => {
  await fetch('/demo/reset', { method: 'POST' });
  location.reload();
});
['amount', 'account'].forEach(id => $(id).addEventListener('keydown', () => {
  typed.push(Date.now());
  if (typed.length > 12) typed.shift();
}));
$('account').addEventListener('paste', () => { $('account').dataset.pasted = 'true'; });
$('transfer-form').addEventListener('submit', async event => {
  event.preventDefault();
  const amount = Number($('amount').value);
  if (!$('name').value.trim() || !$('account').value.trim() || !Number.isFinite(amount) || amount <= 0 || amount > 1000000) {
    $('form-error').textContent = 'Enter the recipient name, account number and a valid amount to continue.';
    $('form-error').hidden = false;
    return;
  }

  const submit = $('send');
  submit.disabled = true;
  submit.textContent = 'Checking transfer…';
  try {
    const response = await fetch('/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: $('customer').value,
        payee_account: $('account').value,
        payee_name: $('name').value,
        amount,
        source_pot: $('pot').value,
        flags: {
          on_call: $('call').checked,
          pasted_account: $('account').dataset.pasted === 'true',
          rushed_score: rushedSignal(),
          clicked_flagged_link_recent: $('link').checked
        }
      })
    });
    if (!response.ok) throw new Error('Transfer review is unavailable. Please try again.');
    render(await response.json());
  } catch (error) {
    $('form-error').textContent = error.message || 'Transfer review is unavailable. Please try again.';
    $('form-error').hidden = false;
  } finally {
    submit.disabled = false;
    submit.innerHTML = 'Review transfer <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';
  }
});

updateCustomer();
