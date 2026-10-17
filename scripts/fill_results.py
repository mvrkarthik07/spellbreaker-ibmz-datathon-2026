#!/usr/bin/env python3
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
report = json.loads((root / 'results/model_report.json').read_text())
bench_path = root / 'results/bench.json'
bench = json.loads(bench_path.read_text()) if bench_path.exists() else {'status': 'pending; LinuxONE unavailable'}
(root / 'docs/RESULTS.md').write_text(
    '# Results\n\nSynthetic victim-side simulator, temporal holdout; not a real-world effectiveness estimate.\n\n'
    '## Model report\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n\n'
    '## Benchmark\n\n```json\n' + json.dumps(bench, indent=2) + '\n```\n'
)
readme = root / 'README.md'
text = readme.read_text()
start, end = '<!-- RESULTS:START -->', '<!-- RESULTS:END -->'
content = (
    f"<!-- RESULTS:START -->\nLocal synthetic PR-AUC: {report['full']['pr_auc']:.3f}; "
    f"legit interruption rate at T1: {report['full']['legit_interruption_rate']:.2%}.\n\n"
    f"Benchmark: {bench.get('rps', 'pending')} requests/s; server p50 "
    f"{bench.get('server_latency_ms', {}).get('p50', 'pending')} ms, p95 "
    f"{bench.get('server_latency_ms', {}).get('p95', 'pending')} ms. "
    "These figures are local and synthetic, not LinuxONE evidence.\n\n"
    "See [full model results](docs/RESULTS.md).\n<!-- RESULTS:END -->"
)
if start in text and end in text:
    readme.write_text(text.split(start)[0] + content + text.split(end, 1)[1])
