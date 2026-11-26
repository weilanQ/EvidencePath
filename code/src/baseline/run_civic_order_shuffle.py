#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical fixed-membership CIViC-order permutation rerun.

Recomputes the archived 5,000-round CIViC-only order perturbation per cohort
using NumPy PCG64 seed 7147, exact rational RRF scores, fixed memberships,
fixed graph order, fixed labels and deterministic name ties.
It supports the CIViC rows of current manuscript Table 7 and the matching
companion S1 comparison and positive-origin stratum summaries.
It does not perform the newly added graph shuffles or their joint 12-test
Holm correction. Use the current release verifier for those archived results.

Inputs: data/processed/baseline_reference.
Outputs: code/results/generated/baseline/tables, unless overridden by
EVIDENCEPATH_RESULTS_DIR.
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


def build_exact_rrf_score_table(k=60, max_rank=80):
    """
    Precomputes exact rational RRF scores for all combinations of (rg, re)
    and maps them to an integer rank representing the exact fraction order.
    """
    score_fracs = {}
    rank_domain = list(range(1, max_rank + 1)) + [None]
    for r1 in rank_domain:
        for r2 in rank_domain:
            if r1 is None and r2 is None:
                continue
            sc = Fraction(0, 1)
            if r1 is not None:
                sc += Fraction(1, k + r1)
            if r2 is not None:
                sc += Fraction(1, k + r2)
            score_fracs[(r1, r2)] = sc

    unique_fracs = sorted(list(set(score_fracs.values())))
    frac_to_rank = {f: i for i, f in enumerate(unique_fracs)}
    score_table = {k_tuple: frac_to_rank[v] for k_tuple, v in score_fracs.items()}
    return score_table

def main():
    print("=" * 80)
    print("EvidencePath Reproduction Suite: Fixed-Membership CIViC Order Shuffle")
    print("=" * 80)
    print("Random Seed:         7147 (NumPy PCG64)")
    print("Permutation Rounds:  5,000")
    print("Fusion Rule:         RRF (k=60, equal weights 1.0, tie-break: exact score DESC, drug_norm ASC)")
    print("=" * 80)

    score_table = build_exact_rrf_score_table(k=60, max_rank=80)

    # 1. Load canonical datasets
    df_jan_cand = pd.read_csv(JAN_CAND_FILE)
    df_jan_pairs = pd.read_csv(JAN_PAIRS_FILE)

    df_q_cand = pd.read_csv(Q_CAND_FILE)
    df_q_pairs = pd.read_csv(Q_PAIRS_FILE)
    df_new_pairs = df_q_pairs[(df_q_pairs['evaluation_group'] == 'NEW_ENDPOINT_QUERY') & (df_q_pairs['endpoint_type'] == 'first_observed_pairs')].copy()

    # Compile query structures
    jan_query_order = sorted(df_jan_cand['query_id'].unique().tolist())
    jan_query_structs = []
    for qid in jan_query_order:
        grp = df_jan_cand[df_jan_cand['query_id'] == qid].copy().reset_index(drop=True)
        ev_indices = grp.index[grp['re'].notna()].tolist()
        pairs_sub = df_jan_pairs[df_jan_pairs['query_id'] == qid]
        cand_drugs = grp['drug_norm'].tolist()
        rg_list = [int(r) if pd.notna(r) and r > 0 else None for r in grp['rg']]
        re_list = [int(r) if pd.notna(r) and r > 0 else None for r in grp['re']]
        jan_query_structs.append({
            'query_key': qid,
            'cand_drugs': cand_drugs,
            'pairs': pairs_sub[['positive_drug', 'pair_key', 'candidate_origin']].to_dict('records'),
            'rg_list': rg_list,
            're_list': re_list,
            'ev_indices': ev_indices,
            'n_ev': len(ev_indices),
            'n_cands': len(cand_drugs)
        })

    q_query_order = sorted(df_new_pairs['window_query_id'].unique().tolist())
    q_query_structs = []
    for wqid in q_query_order:
        grp = df_q_cand[df_q_cand['window_query_id'] == wqid].copy().reset_index(drop=True)
        ev_indices = grp.index[grp['re'].notna()].tolist()
        pairs_sub = df_new_pairs[df_new_pairs['window_query_id'] == wqid]
        cand_drugs = grp['drug_norm'].tolist()
        rg_list = [int(r) if pd.notna(r) and r > 0 else None for r in grp['rg']]
        re_list = [int(r) if pd.notna(r) and r > 0 else None for r in grp['re']]
        q_query_structs.append({
            'query_key': wqid,
            'cand_drugs': cand_drugs,
            'pairs': pairs_sub[['positive_drug', 'pair_key', 'candidate_origin']].to_dict('records'),
            'rg_list': rg_list,
            're_list': re_list,
            'ev_indices': ev_indices,
            'n_ev': len(ev_indices),
            'n_cands': len(cand_drugs)
        })

    N_ROUNDS = 5000
    SEED = 7147

    def run_shuffle(group_name, query_structs, all_pairs_df, orig_qmrr, orig_h3, orig_h5, seed):
        print(f"\nRunning 5,000 rounds for: {group_name}...")
        t0 = time.time()
        rng = np.random.default_rng(seed)

        round_qmrr = np.zeros(N_ROUNDS, dtype=np.float64)
        round_hr3 = np.zeros(N_ROUNDS, dtype=np.float64)
        round_hr5 = np.zeros(N_ROUNDS, dtype=np.float64)

        n_queries = len(query_structs)
        pair_rr_accum = {r['pair_key']: 0.0 for _, r in all_pairs_df.iterrows()}

        for round_idx in range(N_ROUNDS):
            q_rrs = []
            h3_cnt, h5_cnt = 0, 0

            for q in query_structs:
                n_ev = q['n_ev']
                new_re = list(q['re_list'])
                if n_ev > 1:
                    perm = rng.permutation(n_ev) + 1
                    for idx, rk in zip(q['ev_indices'], perm):
                        new_re[idx] = int(rk)

                items = []
                for i in range(q['n_cands']):
                    sc_idx = score_table[(q['rg_list'][i], new_re[i])]
                    items.append((-sc_idx, q['cand_drugs'][i]))

                sorted_indices = sorted(range(q['n_cands']), key=lambda i: items[i])
                rank_map = {q['cand_drugs'][idx]: rk for rk, idx in enumerate(sorted_indices, start=1)}

                pos_rks = []
                for p_info in q['pairs']:
                    d = p_info['positive_drug']
                    rk = rank_map.get(d, np.nan)
                    if pd.notna(rk) and rk > 0:
                        rr = 1.0 / rk
                        pos_rks.append(int(rk))
                    else:
                        rr = 0.0
                    pair_rr_accum[p_info['pair_key']] += rr

                if pos_rks:
                    best_rk = min(pos_rks)
                    q_rr = 1.0 / best_rk
                    is_h3 = 1 if best_rk <= 3 else 0
                    is_h5 = 1 if best_rk <= 5 else 0
                else:
                    q_rr = 0.0
                    is_h3 = 0
                    is_h5 = 0

                q_rrs.append(q_rr)
                h3_cnt += is_h3
                h5_cnt += is_h5

            round_qmrr[round_idx] = np.mean(q_rrs)
            round_hr3[round_idx] = h3_cnt / n_queries
            round_hr5[round_idx] = h5_cnt / n_queries

        elapsed = time.time() - t0
        print(f"  Done in {elapsed:.2f}s ({elapsed/N_ROUNDS*1000:.3f} ms/round)")

        mean_qmrr = float(np.mean(round_qmrr))
        ci_qmrr = [float(np.percentile(round_qmrr, 2.5)), float(np.percentile(round_qmrr, 97.5))]

        mean_hr3 = float(np.mean(round_hr3))
        ci_hr3 = [float(np.percentile(round_hr3, 2.5)), float(np.percentile(round_hr3, 97.5))]

        mean_hr5 = float(np.mean(round_hr5))
        ci_hr5 = [float(np.percentile(round_hr5, 2.5)), float(np.percentile(round_hr5, 97.5))]

        # Pair level analysis
        pair_res = []
        for _, prow in all_pairs_df.iterrows():
            pk = prow['pair_key']
            qk = prow['window_query_id'] if 'Replay' in group_name else prow['query_id']
            d = prow['positive_drug']
            orig_rk = prow['rank_b5']
            orig_rr = 1.0 / orig_rk if pd.notna(orig_rk) and orig_rk > 0 else 0.0
            shuff_rr = pair_rr_accum[pk] / N_ROUNDS

            if 'Replay' in group_name:
                cand_sub = df_q_cand[(df_q_cand['window_query_id'] == qk) & (df_q_cand['drug_norm'] == d)]
            else:
                cand_sub = df_jan_cand[(df_jan_cand['query_id'] == qk) & (df_jan_cand['drug_norm'] == d)]
            b_origin = cand_sub['origin'].iloc[0] if len(cand_sub) > 0 else 'UNRECALLED'

            pair_res.append({
                'pair_key': pk,
                'origin': b_origin,
                'orig_rr': orig_rr,
                'shuff_rr': shuff_rr,
                'delta_rr': orig_rr - shuff_rr
            })
        df_pair_res = pd.DataFrame(pair_res)

        return {
            'qmrr': (orig_qmrr, mean_qmrr, ci_qmrr, orig_qmrr - mean_qmrr),
            'hr3': (orig_h3, mean_hr3, ci_hr3, orig_h3 - mean_hr3),
            'hr5': (orig_h5, mean_hr5, ci_hr5, orig_h5 - mean_hr5),
            'pair_df': df_pair_res,
            'round_metrics': pd.DataFrame({'round': range(1, N_ROUNDS + 1), 'query_mrr': round_qmrr, 'hr3': round_hr3, 'hr5': round_hr5})
        }

    res_jan = run_shuffle('Development', jan_query_structs, df_jan_pairs, 0.459414, 20.0/41.0, 22.0/41.0, SEED)
    res_q = run_shuffle('Replay', q_query_structs, df_new_pairs, 0.389538, 21.0/45.0, 27.0/45.0, SEED)

    # Format the historical CIViC-shuffle summary
    tab3_rows = [
        {'Set': 'Development', 'Metric': 'Query MRR', 'Original': f"{res_jan['qmrr'][0]:.4f}", 'Permuted mean': f"{res_jan['qmrr'][1]:.4f}", 'Central 95%': f"[{res_jan['qmrr'][2][0]:.4f}, {res_jan['qmrr'][2][1]:.4f}]", 'Gap': f"{res_jan['qmrr'][3]:+.4f}"},
        {'Set': 'Development', 'Metric': 'HR@3 (%)', 'Original': f"{res_jan['hr3'][0]*100:.2f}", 'Permuted mean': f"{res_jan['hr3'][1]*100:.2f}", 'Central 95%': f"[{res_jan['hr3'][2][0]*100:.2f}, {res_jan['hr3'][2][1]*100:.2f}]", 'Gap': f"{res_jan['hr3'][3]*100:+.2f}"},
        {'Set': 'Development', 'Metric': 'HR@5 (%)', 'Original': f"{res_jan['hr5'][0]*100:.2f}", 'Permuted mean': f"{res_jan['hr5'][1]*100:.2f}", 'Central 95%': f"[{res_jan['hr5'][2][0]*100:.2f}, {res_jan['hr5'][2][1]*100:.2f}]", 'Gap': f"{res_jan['hr5'][3]*100:+.2f}"},
        {'Set': 'Replay', 'Metric': 'Query MRR', 'Original': f"{res_q['qmrr'][0]:.4f}", 'Permuted mean': f"{res_q['qmrr'][1]:.4f}", 'Central 95%': f"[{res_q['qmrr'][2][0]:.4f}, {res_q['qmrr'][2][1]:.4f}]", 'Gap': f"{res_q['qmrr'][3]:+.4f}"},
        {'Set': 'Replay', 'Metric': 'HR@3 (%)', 'Original': f"{res_q['hr3'][0]*100:.2f}", 'Permuted mean': f"{res_q['hr3'][1]*100:.2f}", 'Central 95%': f"[{res_q['hr3'][2][0]*100:.2f}, {res_q['hr3'][2][1]*100:.2f}]", 'Gap': f"{res_q['hr3'][3]*100:+.2f}"},
        {'Set': 'Replay', 'Metric': 'HR@5 (%)', 'Original': f"{res_q['hr5'][0]*100:.2f}", 'Permuted mean': f"{res_q['hr5'][1]*100:.2f}", 'Central 95%': f"[{res_q['hr5'][2][0]*100:.2f}, {res_q['hr5'][2][1]*100:.2f}]", 'Gap': f"{res_q['hr5'][3]*100:+.2f}"},
    ]

    df_tab3 = pd.DataFrame(tab3_rows)
    print("\n" + "=" * 80)
    print("CIViC order-shuffle rows of Table 7 and S1 (5,000 rounds)")
    print("=" * 80)
    print(df_tab3.to_string(index=False))

    out_tab3 = TABLES_DIR / 'table3_civic_order_shuffle.csv'
    df_tab3.to_csv(out_tab3, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_tab3)} (current Table 7 CIViC rows and S1)")

    # Check assertions matching paper Table 7 (CIViC rows)
    # Development:
    assert round(res_jan['qmrr'][1], 4) == 0.4461, f"Jan Q-MRR mean mismatch: {res_jan['qmrr'][1]}"
    assert round(res_jan['hr3'][1]*100, 2) == 48.27, f"Jan HR@3 mean mismatch: {res_jan['hr3'][1]*100}"
    assert round(res_jan['hr5'][1]*100, 2) == 50.72, f"Jan HR@5 mean mismatch: {res_jan['hr5'][1]*100}"
    # Replay:
    assert round(res_q['qmrr'][1], 4) == 0.3514, f"Replay Q-MRR mean mismatch: {res_q['qmrr'][1]}"
    assert round(res_q['hr3'][1]*100, 2) == 42.82, f"Replay HR@3 mean mismatch: {res_q['hr3'][1]*100}"
    assert round(res_q['hr5'][1]*100, 2) == 50.85, f"Replay HR@5 mean mismatch: {res_q['hr5'][1]*100}"

    # Stratified origin gains
    print("\nStratified Pair Reciprocal Rank Analysis (Replay):")
    rep_pairs_df = res_q['pair_df']
    shared_gain = rep_pairs_df[rep_pairs_df['origin'] == 'R0_and_CIViC_retrieved']['delta_rr'].mean()
    civic_gain = rep_pairs_df[rep_pairs_df['origin'] == 'CIViC_retrieved_new']['delta_rr'].mean()
    print(f"  Shared positives (N=19):            ΔRR = {shared_gain:+.4f} (Supplement S1: +0.0517)")
    print(f"  CIViC-exclusive positives (N=13):  ΔRR = {civic_gain:+.4f} (Supplement S1: +0.0560)")

    assert round(shared_gain, 4) == 0.0517, f"Shared gain mismatch: {shared_gain}"
    assert round(civic_gain, 4) == 0.0560, f"CIViC gain mismatch: {civic_gain}"

    out_origins = TABLES_DIR / 'civic_shuffle_pair_origins.csv'
    rep_pairs_df.to_csv(out_origins, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_origins)}")

    # Save round level metrics
    out_rounds = TABLES_DIR / 'civic_shuffle_round_metrics.csv'
    res_q['round_metrics'].to_csv(out_rounds, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_rounds)}")

    print("\n>>> Manuscript Table 7 (CIViC rows) and Supplement S1 shuffle ablations verified!")

if __name__ == '__main__':
    main()
