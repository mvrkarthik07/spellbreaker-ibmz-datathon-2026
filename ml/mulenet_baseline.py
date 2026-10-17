#!/usr/bin/env python3
"""Compare receiver-mule models and optionally export XGBoost account scores."""
import argparse
import json
import math
import os
import platform
import re
import sys
from pathlib import Path
from importlib.metadata import version

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ml.mule_share import receiver_token

ROOT = Path(__file__).resolve().parents[1]


def topk_metrics(labels, scores):
    labels = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(scores, dtype=np.float64)
    total = int(labels.sum())
    out = {'account_count': int(len(labels)), 'mule_accounts': total,
           'base_mule_rate': float(labels.mean()) if len(labels) else 0.0,
           'roc_auc': float(roc_auc_score(labels, scores)) if len(np.unique(labels)) == 2 else None}
    for percent in (1, 5):
        k = max(1, math.ceil(len(labels) * percent / 100))
        top = np.argpartition(scores, -k)[-k:]
        found = int(labels[top].sum())
        precision = found / k
        recall = found / total if total else 0.0
        out[f'precision_at_top_{percent}pct'] = precision
        out[f'recall_at_top_{percent}pct'] = recall
        out[f'lift_at_top_{percent}pct'] = precision / out['base_mule_rate'] if out['base_mule_rate'] else None
        out[f'accounts_exposed_at_top_{percent}pct'] = k
        out[f'accounts_exposed_percent_at_top_{percent}pct'] = 100 * k / len(labels) if len(labels) else 0.0
    return out


def silo_collaboration(test_frame, target, account_col, bank_col, scores):
    """Offline two-silo simulation: HMAC join keys and 5% within-silo red flags."""
    labels_by_account = test_frame.groupby(account_col, dropna=False)[target].max()
    scores_by_account = pd.Series(scores, index=test_frame.index).groupby(
        test_frame[account_col], dropna=False).mean()
    accounts = list(labels_by_account.index)
    account_labels = labels_by_account.to_numpy(dtype=np.int8)
    siloed_scores = scores_by_account.reindex(accounts).fillna(0).to_numpy(dtype=np.float64)
    result = {
        'siloed': topk_metrics(account_labels, siloed_scores),
        'collaborative': None,
        'oracle': topk_metrics(account_labels, account_labels.astype(np.float64)),
        'sharing_protocol': 'HMAC-SHA256 account tokens; only top-5%-within-source-bank red flags are shared; tokens/key are not exported',
        'red_flag_gate_percent': 5,
        'exposure_percent': {'siloed': 0.0, 'collaborative': 0.0,
                             'oracle': 100 * float(account_labels.mean()) if len(account_labels) else 0.0},
        'simulation': 'source bank ids split by parity into two evaluator silos; home silo assigned by ephemeral HMAC token parity; collaboration exposes only matched non-home red flags',
    }
    if not bank_col or bank_col not in test_frame.columns:
        result['collaborative_unavailable_reason'] = 'source bank column unavailable'
        return result

    # Use an ephemeral key. Only aggregate metrics survive this function.
    key = os.urandom(32)
    acct_tokens = {acct: receiver_token(str(acct), key=key) for acct in accounts}
    silo = pd.to_numeric(test_frame[bank_col], errors='coerce').fillna(0).astype('int64') % 2
    per_silo = {}
    for silo_id in (0, 1):
        subset = test_frame.loc[silo == silo_id, [account_col, target]].copy()
        subset['_score'] = pd.Series(scores, index=test_frame.index).loc[subset.index].to_numpy()
        per_silo[silo_id] = subset.groupby(account_col, dropna=False).agg(
            score=('_score', 'mean'), label=(target, 'max'))

    home_scores = np.zeros(len(accounts), dtype=np.float64)
    collab_scores = np.zeros(len(accounts), dtype=np.float64)
    exposed = np.zeros(len(accounts), dtype=bool)
    for i, acct in enumerate(accounts):
        home = int(acct_tokens[acct][-1], 16) % 2
        local = per_silo[home].get('score')
        local_score = float(local.loc[acct]) if local is not None and acct in local.index else 0.0
        home_scores[i] = local_score
        collab_scores[i] = local_score
        remote = per_silo[1 - home].get('score')
        if remote is None or acct not in remote.index:
            continue
        remote_score = float(remote.loc[acct])
        cutoff = float(remote.quantile(.95)) if len(remote) else float('inf')
        # HMAC lookup is explicit even in this local simulation: only a matching
        # pseudonym and a red-flag-gated score can cross the silo boundary.
        token = acct_tokens[acct]
        if remote_score >= cutoff and token == receiver_token(str(acct), key=key):
            collab_scores[i] = max(local_score, remote_score)
            exposed[i] = True

    result['siloed'] = topk_metrics(account_labels, home_scores)
    result['collaborative'] = topk_metrics(account_labels, collab_scores)
    result['exposure_percent']['siloed'] = 100 * float(np.count_nonzero(home_scores >= np.quantile(home_scores, .95))) / len(home_scores) if len(home_scores) else 0.0
    result['exposure_percent']['collaborative'] = 100 * float(exposed.mean()) if len(exposed) else 0.0
    result['accounts_exposed_collaborative'] = int(exposed.sum())
    result['accounts_matched_by_hmac'] = int(sum(1 for acct in accounts if acct in per_silo[0].index and acct in per_silo[1].index))
    result['collaborative_red_flags_shared'] = int(exposed.sum())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='data/HI-Small_Trans.csv')
    parser.add_argument('--nrows', type=int, default=None)
    parser.add_argument('--export-scores', default=None)
    parser.add_argument('--xgb-threads', type=int, default=3)
    args = parser.parse_args()
    src = ROOT / args.data
    if not src.exists():
        print(f'SKIP: dataset absent: {src}')
        return 0

    df = pd.read_csv(src, nrows=args.nrows)
    normalize = lambda c: re.sub(r'[^a-z0-9]', '', str(c).lower())
    target = next((c for c in df.columns if normalize(c) in {'islaundering', 'label'}), None)
    if not target:
        raise ValueError(f'No laundering label column found; columns={list(df.columns)}')
    acct = next((c for c in df.columns if normalize(c) in {'toaccount', 'destaccount', 'destinationaccount', 'receiveraccount', 'account1'}), None)
    if not acct:
        raise ValueError(f'No destination account column found; columns={list(df.columns)}')
    cols = [c for c in df.select_dtypes(include='number').columns
            if c != target and normalize(c) not in {'label', 'islaundering'}]
    if not cols:
        raise ValueError('No numeric transaction features found')

    cut = int(len(df) * .8)
    # Convert to contiguous NumPy once: identical training/evaluation rows for both models.
    X = np.ascontiguousarray(df[cols].fillna(0).to_numpy(dtype=np.float32))
    y = np.ascontiguousarray(df[target].to_numpy(dtype=np.int8))
    X_train, X_test, y_train, y_test = X[:cut], X[cut:], y[:cut], y[cut:]

    models = {
        'sklearn_histgradientboosting': HistGradientBoostingClassifier(max_iter=80, random_state=42),
    }
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError('XGBoost must be preinstalled in the official LinuxONE Jupyter image') from exc
    models['xgboost'] = XGBClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.12, subsample=0.9,
        colsample_bytree=1.0, objective='binary:logistic', eval_metric='logloss',
        tree_method='hist', n_jobs=max(1, args.xgb_threads), random_state=42,
        verbosity=0, use_label_encoder=False,
    )

    report = {
        'trained_on': platform.machine(), 'rows_read': len(df), 'train_rows': cut,
        'test_rows': len(y_test), 'target_column': target,
        'receiver_account_column': acct, 'features': cols, 'nrows_limit': args.nrows,
        'evaluation': 'same chronological 80/20 split for both models',
        'models': {}, 'score_export_model': 'xgboost',
        'transaction_level': {
            'base_mule_rate': float(y_test.mean()),
            'base_mule_rate_percent': float(y_test.mean() * 100),
            'holdout_rows': int(len(y_test)),
            'metric_scope': 'chronological 20% transaction holdout',
        },
    }
    predictions = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        predictions[name] = proba
        report['models'][name] = {
            'pr_auc': float(average_precision_score(y_test, proba)),
            'roc_auc': float(roc_auc_score(y_test, proba)),
            'base_mule_rate': float(y_test.mean()),
        }

    # Compatibility field consumed by existing docs/tools; selected output is XGBoost.
    report['siloed_pr_auc'] = report['models']['xgboost']['pr_auc']
    report['comparison'] = {
        'xgboost_minus_histgradientboosting_pr_auc':
            report['models']['xgboost']['pr_auc'] - report['models']['sklearn_histgradientboosting']['pr_auc'],
        'xgboost_version': version('xgboost'),
        'scikit_learn_version': version('scikit-learn'),
        'xgboost_threads': max(1, args.xgb_threads),
    }
    bank_col = next((c for c in df.columns if normalize(c) in {'frombank', 'sourcebank', 'originbank'}), None)
    report['account_level'] = {
        'unit': 'unique receiving account in the chronological test window',
        'base_mule_rate': None,
        'models': {},
        'siloed_collaborative_oracle': None,
    }
    account_models = {}
    for name, prediction in predictions.items():
        scored = pd.Series(prediction, index=df.index[cut:])
        acct_labels = df.iloc[cut:].groupby(acct, dropna=False)[target].max()
        acct_scores = scored.groupby(df.iloc[cut:][acct], dropna=False).mean().reindex(acct_labels.index).fillna(0)
        metrics = topk_metrics(acct_labels.to_numpy(dtype=np.int8), acct_scores.to_numpy(dtype=np.float64))
        account_models[name] = metrics
        report['account_level']['models'][name] = metrics
    report['account_level']['base_mule_rate'] = account_models['xgboost']['base_mule_rate']
    report['account_level']['siloed_collaborative_oracle'] = silo_collaboration(
        df.iloc[cut:], target, acct, bank_col, predictions['xgboost'])
    report['account_level']['collaboration'] = report['account_level']['siloed_collaborative_oracle']
    if args.export_scores:
        test = df.iloc[cut:]
        score_rows = pd.DataFrame({
            'account': test[acct].to_numpy(),
            '_score': predictions['xgboost'],
            '_label': y_test,
        })
        out = score_rows.groupby('account', dropna=False, sort=False).agg(
            score=('_score', 'mean'), is_mule=('_label', 'max')
        ).reset_index()
        export = ROOT / args.export_scores
        export.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(export, index=False)
        report['accounts'] = len(out)
        report['export_path'] = args.export_scores
    report['runtime'] = {
        'python': platform.python_version(), 'numpy': np.__version__,
        'pandas': pd.__version__, 'scikit_learn': version('scikit-learn'),
        'xgboost': version('xgboost'),
    }
    (ROOT / 'results/mulenet_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
