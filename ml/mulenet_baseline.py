#!/usr/bin/env python3
"""Compare receiver-mule models and optionally export XGBoost account scores."""
import argparse
import json
import platform
import re
from pathlib import Path
from importlib.metadata import version

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]


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
        'collab_pr_auc': None, 'oracle_pr_auc': None, 'exposure_percent': 0.0,
    }
    predictions = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        predictions[name] = proba
        report['models'][name] = {
            'pr_auc': float(average_precision_score(y_test, proba)),
            'roc_auc': float(roc_auc_score(y_test, proba)),
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
