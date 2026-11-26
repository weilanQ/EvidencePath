#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical 54-setting exact-rational RRF grid rerun.

Recomputes k in {10,20,40,60,80,100} crossed with graph weight
alpha in {0.1,...,0.9}, with fixed candidate pools and source ranks.
It checks the archived comparison against Append-SF and the default neighborhood
retained in Section 5.4 and the companion S1 parameter-sensitivity figure.
The historical script does not test every setting against Shared-first.
Current strong-baseline grid comparisons are separately included in the release.

Inputs: data/processed/baseline_reference.
Outputs: code/results/generated/baseline/tables, unless overridden by
EVIDENCEPATH_RESULTS_DIR. Runtime is measured when executed, not guaranteed.
"""

import os
import sys
import time
from pathlib import Path
from fractions import Fraction
import numpy as np
import pandas as pd

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / 'data' / 'processed' / 'baseline_reference'
TABLES_DIR = Path(os.environ.get('EVIDENCEPATH_RESULTS_DIR', REPO_ROOT / 'code' / 'results' / 'generated')) / 'baseline' / 'tables'
TABLES_DIR.mkdir(parents=True, exist_ok=True)

JAN_CAND_FILE = DATA_DIR / 'frozen_candidates' / 'january_candidate_matrix_1051.csv'
JAN_PAIRS_FILE = DATA_DIR / 'ground_truth' / 'january_positive_pairs_43.csv'
Q_CAND_FILE = DATA_DIR / 'frozen_candidates' / 'quarterly_candidate_matrix_2762.csv'
Q_PAIRS_FILE = DATA_DIR / 'ground_truth' / 'quarterly_positive_pairs_50.csv'


def display_path(path):
    """Keep status output readable when a caller uses an external output folder."""
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).name


def main():
    print("=" * 80)
    print("EvidencePath Reproduction Suite: 54-Setting RRF Parameter Grid Scan")
    print("=" * 80)
    t0 = time.time()

    # Load canonical datasets
    df_jan_cand = pd.read_csv(JAN_CAND_FILE)
    df_jan_pairs = pd.read_csv(JAN_PAIRS_FILE)
    df_q_cand = pd.read_csv(Q_CAND_FILE)
    df_q_pairs = pd.read_csv(Q_PAIRS_FILE)
    df_new_pairs = df_q_pairs[(df_q_pairs['evaluation_group'] == 'NEW_ENDPOINT_QUERY') & (df_q_pairs['endpoint_type'] == 'first_observed_pairs')].copy()

    # Pre-parse candidate groups
    jan_groups = {qid: grp.copy().reset_index(drop=True) for qid, grp in df_jan_cand.groupby('query_id')}
    q_groups = {wqid: grp.copy().reset_index(drop=True) for wqid, grp in df_q_cand.groupby('window_query_id')}

    k_values = [10, 20, 40, 60, 80, 100]
    alpha_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    B2_JAN_MRR = 0.3733
    B2_REPLAY_MRR = 0.2004

    grid_results = []
    print(f"Scanning {len(k_values)} x {len(alpha_values)} = 54 parameter combinations using exact rational scoring...")

    for k in k_values:
        for alpha in alpha_values:
            a_frac = Fraction(round(alpha * 10), 10)
            one_minus_a_frac = Fraction(10 - round(alpha * 10), 10)

            # Precompute rational scores for ranks 1..80
            g_lookup = {r: a_frac / Fraction(k + r, 1) for r in range(1, 81)}
            e_lookup = {r: one_minus_a_frac / Fraction(k + r, 1) for r in range(1, 81)}
            g_lookup[None] = Fraction(0, 1)
            e_lookup[None] = Fraction(0, 1)

            # Evaluate January Development (41 queries)
            jan_q_rrs, jan_q_h5 = [], []
            for qid, qgrp in df_jan_pairs.groupby('query_id'):
                cands = jan_groups[qid]
                scores = []
                for _, r in cands.iterrows():
                    rg = int(r['rg']) if pd.notna(r['rg']) and r['rg'] > 0 else None
                    re = int(r['re']) if pd.notna(r['re']) and r['re'] > 0 else None
                    sc = g_lookup[rg] + e_lookup[re]
                    scores.append((-sc, r['drug_norm']))

                sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i])
                rk_map = {cands.iloc[idx]['drug_norm']: rk for rk, idx in enumerate(sorted_indices, 1)}

                pos_rks = [rk_map.get(d, np.nan) for d in qgrp['positive_drug']]
                valid = [r for r in pos_rks if pd.notna(r) and r > 0]
                if valid:
                    best_r = min(valid)
                    jan_q_rrs.append(1.0 / best_r)
                    jan_q_h5.append(1 if best_r <= 5 else 0)
                else:
                    jan_q_rrs.append(0.0)
                    jan_q_h5.append(0)

            jan_qmrr = float(np.mean(jan_q_rrs))
            jan_h5_hits = sum(jan_q_h5)

            # Evaluate Quarterly Replay (45 queries)
            q_q_rrs, q_q_h5 = [], []
            for wqid, qgrp in df_new_pairs.groupby('window_query_id'):
                cands = q_groups[wqid]
                scores = []
                for _, r in cands.iterrows():
                    rg = int(r['rg']) if pd.notna(r['rg']) and r['rg'] > 0 else None
                    re = int(r['re']) if pd.notna(r['re']) and r['re'] > 0 else None
                    sc = g_lookup[rg] + e_lookup[re]
                    scores.append((-sc, r['drug_norm']))

                sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i])
                rk_map = {cands.iloc[idx]['drug_norm']: rk for rk, idx in enumerate(sorted_indices, 1)}

                pos_rks = [rk_map.get(d, np.nan) for d in qgrp['positive_drug']]
                valid = [r for r in pos_rks if pd.notna(r) and r > 0]
                if valid:
                    best_r = min(valid)
                    q_q_rrs.append(1.0 / best_r)
                    q_q_h5.append(1 if best_r <= 5 else 0)
                else:
                    q_q_rrs.append(0.0)
                    q_q_h5.append(0)

            q_qmrr = float(np.mean(q_q_rrs))
            q_h5_hits = sum(q_q_h5)

            grid_results.append({
                'k': k,
                'alpha': alpha,
                'jan_query_mrr': jan_qmrr,
                'jan_hr5_hits': jan_h5_hits,
                'jan_delta_vs_b2': jan_qmrr - B2_JAN_MRR,
                'new_query_mrr': q_qmrr,
                'new_hr5_hits': q_h5_hits,
                'new_delta_vs_b2': q_qmrr - B2_REPLAY_MRR
            })

    elapsed = time.time() - t0
    print(f"54-setting scan completed in {elapsed:.2f} seconds.")

    df_grid = pd.DataFrame(grid_results)
    out_file = TABLES_DIR / 'rrf_grid_scan_54_summary.csv'
    df_grid.to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_file)}")

    # 1. Verification of default benchmark point (k=60, alpha=0.5)
    def_row = df_grid[(df_grid['k'] == 60) & (df_grid['alpha'] == 0.5)].iloc[0]
    print(f"\nDefault point (k=60, alpha=0.5):")
    print(f"  January MRR: {def_row['jan_query_mrr']:.4f} (exp: 0.4594), HR@5: {int(def_row['jan_hr5_hits'])}/41 (exp: 22/41)")
    print(f"  Replay MRR:  {def_row['new_query_mrr']:.4f} (exp: 0.3895), HR@5: {int(def_row['new_hr5_hits'])}/45 (exp: 27/45)")

    assert round(def_row['jan_query_mrr'], 4) == 0.4594, "Default January MRR mismatch!"
    assert int(def_row['jan_hr5_hits']) == 22, "Default January HR@5 mismatch!"
    assert round(def_row['new_query_mrr'], 4) == 0.3895, "Default Replay MRR mismatch!"
    assert int(def_row['new_hr5_hits']) == 27, "Default Replay HR@5 mismatch!"

    # 2. Verify all 54 points outperform B2
    jan_above_b2 = (df_grid['jan_delta_vs_b2'] > 0).all()
    q_above_b2 = (df_grid['new_delta_vs_b2'] > 0).all()
    print(f"\nAll 54 parameter combinations exceed B2 in January: {jan_above_b2} (min Δ: {df_grid['jan_delta_vs_b2'].min():+.4f})")
    print(f"All 54 parameter combinations exceed B2 in Replay:  {q_above_b2} (min Δ: {df_grid['new_delta_vs_b2'].min():+.4f})")
    assert jan_above_b2 and q_above_b2, "Assertion failed: not all points exceed B2!"

    # 3. Verify default 3x3 neighborhood (k in {40, 60, 80}, alpha in {0.4, 0.5, 0.6})
    hood = df_grid[(df_grid['k'].isin([40, 60, 80])) & (df_grid['alpha'].isin([0.4, 0.5, 0.6]))]
    min_hood_mrr = hood['new_query_mrr'].min()
    max_hood_mrr = hood['new_query_mrr'].max()
    min_hood_h5 = int(hood['new_hr5_hits'].min())
    max_hood_h5 = int(hood['new_hr5_hits'].max())

    print(f"\nDefault 3x3 neighborhood variation (k in [40, 80], alpha in [0.4, 0.6]):")
    print(f"  Replay MRR range: {min_hood_mrr:.4f} -- {max_hood_mrr:.4f} (Supplement S1: 0.3128 -- 0.4279)")
    print(f"  Replay HR@5 range: {min_hood_h5} -- {max_hood_h5} of 45 (Supplement S1: 19 -- 30 of 45)")

    assert round(min_hood_mrr, 4) == 0.3128, f"Neighborhood min MRR mismatch: {min_hood_mrr:.4f}"
    assert round(max_hood_mrr, 4) == 0.4279, f"Neighborhood max MRR mismatch: {max_hood_mrr:.4f}"
    assert min_hood_h5 == 19, f"Neighborhood min HR@5 mismatch: {min_hood_h5}"
    assert max_hood_h5 == 30, f"Neighborhood max HR@5 mismatch: {max_hood_h5}"

    print(">>> 54-setting parameter grid scan and neighborhood verified against paper and Supplement S1!")

if __name__ == '__main__':
    main()
