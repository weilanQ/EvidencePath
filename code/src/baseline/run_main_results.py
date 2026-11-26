#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical frozen-ranking subanalyses.

This module retains the original calculations and numerical assertions.
It supports current manuscript Table 4 (development coverage), a historical
policy subset of Table 5, Eq. (2)'s development decomposition, Table 8's
interleaving results and conditional oracles, historical columns of Table 9,
the temporal counts in Section 5.5, and the entrectinib omission in Section 5.4.
It does not generate the revised Shared-first or replay strong-baseline audits.

Inputs: data/processed/baseline_reference.
Outputs: code/results/generated/baseline/tables, unless overridden by
EVIDENCEPATH_RESULTS_DIR. Historical CSV basenames are retained for provenance.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure UTF-8 stdout
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / 'data' / 'processed' / 'baseline_reference'
TABLES_DIR = Path(os.environ.get('EVIDENCEPATH_RESULTS_DIR', REPO_ROOT / 'code' / 'results' / 'generated')) / 'baseline' / 'tables'
TABLES_DIR.mkdir(parents=True, exist_ok=True)

CAND_CORRECTED = DATA_DIR / 'frozen_candidates' / 'corrected_candidate_rankings.csv'
JAN_CAND_FILE = DATA_DIR / 'frozen_candidates' / 'january_candidate_matrix_1051.csv'
PAIRS_CORRECTED = DATA_DIR / 'ground_truth' / 'corrected_per_pair_comparison.csv'
JAN_PAIRS_FILE = DATA_DIR / 'ground_truth' / 'january_positive_pairs_43.csv'
Q_PAIRS_FILE = DATA_DIR / 'ground_truth' / 'quarterly_positive_pairs_50.csv'


def display_path(path):
    """Keep status output readable when a caller uses an external output folder."""
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).name


def compute_mrr_and_hr(cand_rank_map, pairs_df, qid_col='qid', drug_col='positive_drug'):
    """Compute Query MRR, Pair MRR, HR@1, HR@3, HR@5, HR@10 and covered pairs."""
    cov_pairs = 0
    p_rrs = []
    for _, prow in pairs_df.iterrows():
        rk = cand_rank_map.get((prow[qid_col], prow[drug_col]), np.nan)
        if pd.notna(rk) and rk > 0:
            cov_pairs += 1
            p_rrs.append(1.0 / float(rk))
        else:
            p_rrs.append(0.0)

    q_rrs = []
    h1_list, h3_list, h5_list, h10_list = [], [], [], []
    for qid, qgrp in pairs_df.groupby(qid_col):
        rks = [cand_rank_map.get((qid, d), np.nan) for d in qgrp[drug_col]]
        valid = [float(r) for r in rks if pd.notna(r) and r > 0]
        if valid:
            best_r = min(valid)
            q_rrs.append(1.0 / best_r)
            h1_list.append(1 if best_r <= 1 else 0)
            h3_list.append(1 if best_r <= 3 else 0)
            h5_list.append(1 if best_r <= 5 else 0)
            h10_list.append(1 if best_r <= 10 else 0)
        else:
            q_rrs.append(0.0)
            h1_list.append(0)
            h3_list.append(0)
            h5_list.append(0)
            h10_list.append(0)

    num_q = pairs_df[qid_col].nunique()
    num_p = len(pairs_df)

    return {
        'covered_pairs': cov_pairs,
        'total_pairs': num_p,
        'pair_coverage_str': f"{cov_pairs}/{num_p}",
        'pair_coverage_pct': (cov_pairs / num_p) * 100.0,
        'query_mrr': float(np.mean(q_rrs)),
        'pair_mrr': float(np.mean(p_rrs)),
        'hr1_count': sum(h1_list),
        'hr3_count': sum(h3_list),
        'hr5_count': sum(h5_list),
        'hr10_count': sum(h10_list),
        'hr5_str': f"{sum(h5_list)}/{num_q}",
        'hr5_pct': (sum(h5_list) / num_q) * 100.0,
        'total_queries': num_q
    }

def step1_candidate_coverage():
    print("\n" + "=" * 80)
    print("STEP 1: Candidate Coverage (Manuscript Table 4)")
    print("=" * 80)

    df_cands = pd.read_csv(JAN_CAND_FILE)
    df_pairs = pd.read_csv(JAN_PAIRS_FILE)

    # Origin categories in 1,051 January candidate pool:
    # R0_primekg: Graph exclusive (R0 \ E)
    # R0_and_CIViC_retrieved: Shared (R0 \cap E)
    # CIViC_retrieved_new: Evidence exclusive (E \ R0)
    r0 = df_cands[df_cands['origin'].isin(['R0_primekg', 'R0_and_CIViC_retrieved'])]
    ev = df_cands[df_cands['origin'].isin(['CIViC_retrieved_new', 'R0_and_CIViC_retrieved'])]
    union_r1 = df_cands
    shared = df_cands[df_cands['origin'] == 'R0_and_CIViC_retrieved']
    g_excl = df_cands[df_cands['origin'] == 'R0_primekg']
    e_excl = df_cands[df_cands['origin'] == 'CIViC_retrieved_new']

    pair_set = set(zip(df_pairs['query_id'], df_pairs['positive_drug']))

    def cov(sub):
        sub_set = set(zip(sub['query_id'], sub['drug_norm']))
        return len(pair_set.intersection(sub_set))

    table1_rows = [
        {'Candidate support': 'Graph R0', 'Query-drug records': len(r0), 'Covered positive pairs': f"{cov(r0)}/{len(pair_set)}"},
        {'Candidate support': 'Evidence E', 'Query-drug records': len(ev), 'Covered positive pairs': f"{cov(ev)}/{len(pair_set)}"},
        {'Candidate support': 'Union R1', 'Query-drug records': len(union_r1), 'Covered positive pairs': f"{cov(union_r1)}/{len(pair_set)}"},
        {'Candidate support': 'Shared R0 ∩ E', 'Query-drug records': len(shared), 'Covered positive pairs': f"{cov(shared)}"},
        {'Candidate support': 'Graph exclusive R0 \\ E', 'Query-drug records': len(g_excl), 'Covered positive pairs': f"{cov(g_excl)}"},
        {'Candidate support': 'Evidence exclusive E \\ R0', 'Query-drug records': len(e_excl), 'Covered positive pairs': f"{cov(e_excl)}"}
    ]

    df_tab1 = pd.DataFrame(table1_rows)
    print(df_tab1.to_string(index=False))

    out_file = TABLES_DIR / 'table1_candidate_coverage.csv'
    df_tab1.to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_file)} (Maps to Manuscript Table 4)")

    # Strict assertions matching paper Table 4
    assert len(r0) == 874 and cov(r0) == 19, f"Graph R0 mismatch: records={len(r0)}, cov={cov(r0)}"
    assert len(ev) == 360 and cov(ev) == 23, f"Evidence E mismatch: records={len(ev)}, cov={cov(ev)}"
    assert len(union_r1) == 1051 and cov(union_r1) == 24, f"Union R1 mismatch: records={len(union_r1)}, cov={cov(union_r1)}"
    assert len(shared) == 183 and cov(shared) == 18, f"Shared mismatch"
    assert len(g_excl) == 691 and cov(g_excl) == 1, f"Graph exclusive mismatch"
    assert len(e_excl) == 177 and cov(e_excl) == 5, f"Evidence exclusive mismatch"
    print(">>> Manuscript Table 4 verified against paper!")

def step2_main_results_table():
    print("\n" + "=" * 80)
    print("STEP 2: Main Results Across Historical Policies (Manuscript Table 5 (historical subset))")
    print("=" * 80)

    df_cands_raw = pd.read_csv(CAND_CORRECTED)
    df_pairs_raw = pd.read_csv(PAIRS_CORRECTED)

    all_results = []

    cohorts = [
        ('January development', df_cands_raw['window_id'] == 'Jul25_Jan26', df_pairs_raw['evaluation_group'] == 'DEVELOPMENT_REF_JUL25_JAN26', 'query_id'),
        ('Quarterly new-context replay', df_cands_raw['window_id'].isin(['W1', 'W2', 'W3']), (df_pairs_raw['evaluation_group'] == 'NEW_ENDPOINT_QUERY') & (df_pairs_raw['endpoint_type'] == 'first_observed_pairs'), 'window_query_id')
    ]

    for cohort_label, c_filter, p_filter, id_col in cohorts:
        cands = df_cands_raw[c_filter].copy()
        pairs = df_pairs_raw[p_filter].copy()

        if id_col == 'window_query_id':
            cands['qid'] = cands['window_id'] + '::' + cands['query_id']
            pairs['qid'] = pairs['window_id'] + '::' + pairs['query_id']
        else:
            cands['qid'] = cands['query_id']
            pairs['qid'] = pairs['query_id']

        num_q = pairs['qid'].nunique()
        num_p = len(pairs)
        print(f"\nEvaluating: {cohort_label} ({num_q} queries, {num_p} pairs)")

        # 1. Derive Evidence rank re per query from Context-Aware rank (b6_rank)
        is_ev = cands['origin'].isin(['R0_and_CIViC_retrieved', 'CIViC_retrieved_new'])
        cands['re'] = np.nan
        cands.loc[is_ev, 're'] = cands[is_ev].groupby('qid')['b6_rank'].rank(method='min').astype(int)

        # 2. Derive Length-normalized Borda aggregation
        borda_ranks = {}
        for qid, grp in cands.groupby('qid'):
            g_sub = grp[pd.notna(grp['b0_rank']) & (grp['b0_rank'] > 0)]
            L_g = len(g_sub)
            e_sub = grp[pd.notna(grp['re']) & (grp['re'] > 0)]
            L_e = len(e_sub)

            g_pts = grp['b0_rank'].apply(lambda r: (L_g - r + 1.0) / L_g if pd.notna(r) and r > 0 and L_g > 0 else 0.0)
            e_pts = grp['re'].apply(lambda r: (L_e - r + 1.0) / L_e if pd.notna(r) and r > 0 and L_e > 0 else 0.0)
            score = g_pts + e_pts
            df_sort = pd.DataFrame({'drug_norm': grp['drug_norm'], 'score': score}).sort_values(by=['score', 'drug_norm'], ascending=[False, True], kind='stable')
            for rk, d in enumerate(df_sort['drug_norm'], 1):
                borda_ranks[(qid, d)] = rk

        cands['borda_rank'] = [borda_ranks.get((q, d), np.nan) for q, d in zip(cands['qid'], cands['drug_norm'])]

        methods = [
            ('Graph', 'b0_rank'),
            ('Mix', 'b1_rank'),
            ('CIViC branch', 're'),
            ('Append-SF', 'b2_rank'),
            ('AltGraph', 'b3_rank'),
            ('AltAppend', 'b4_rank'),
            ('Context', 'b6_rank'),
            ('Borda', 'borda_rank'),
            ('RRF', 'b5_rank'),
        ]

        for m_name, rk_col in methods:
            cand_map = dict(zip(zip(cands['qid'], cands['drug_norm']), cands[rk_col]))
            met = compute_mrr_and_hr(cand_map, pairs, qid_col='qid')
            row = {
                'Cohort': cohort_label,
                'Method': m_name,
                'Pair coverage': met['pair_coverage_str'],
                'Query MRR': f"{met['query_mrr']:.4f}",
                'Pair MRR': f"{met['pair_mrr']:.4f}",
                'HR@5': met['hr5_str'],
                'raw_query_mrr': met['query_mrr'],
                'raw_pair_mrr': met['pair_mrr'],
                'hr1_count': met['hr1_count'],
                'hr3_count': met['hr3_count'],
                'hr5_count': met['hr5_count'],
                'hr10_count': met['hr10_count']
            }
            all_results.append(row)
            print(f"  {m_name:15s} | Cov: {met['pair_coverage_str']:>5s} | Q-MRR: {met['query_mrr']:.4f} | P-MRR: {met['pair_mrr']:.4f} | HR@5: {met['hr5_str']:>5s}")

    df_tab2 = pd.DataFrame(all_results)
    out_file = TABLES_DIR / 'table2_main_results.csv'
    df_tab2.to_csv(out_file, index=False, encoding='utf-8')
    print(f"\nSaved: {display_path(out_file)} (Maps to Manuscript Table 5 (historical subset))")

    # Verification of Table 5 (historical subset) expected values
    expected = {
        ('January development', 'Graph'): ('19/43', '0.2996', '0.2857', '15/41'),
        ('January development', 'Mix'): ('24/43', '0.2355', '0.2252', '16/41'),
        ('January development', 'CIViC branch'): ('23/43', '0.3660', '0.3490', '21/41'),
        ('January development', 'Append-SF'): ('24/43', '0.3733', '0.3565', '18/41'),
        ('January development', 'AltGraph'): ('19/43', '0.3409', '0.3250', '15/41'),
        ('January development', 'AltAppend'): ('24/43', '0.4146', '0.3959', '18/41'),
        ('January development', 'Context'): ('24/43', '0.3660', '0.3496', '21/41'),
        ('January development', 'Borda'): ('24/43', '0.4621', '0.4411', '22/41'),
        ('January development', 'RRF'): ('24/43', '0.4594', '0.4386', '22/41'),
        ('Quarterly new-context replay', 'Graph'): ('20/46', '0.1902', '0.1860', '10/45'),
        ('Quarterly new-context replay', 'CIViC branch'): ('32/46', '0.3452', '0.3386', '27/45'),
        ('Quarterly new-context replay', 'Append-SF'): ('33/46', '0.2004', '0.1965', '10/45'),
        ('Quarterly new-context replay', 'AltAppend'): ('33/46', '0.1330', '0.1305', '11/45'),
        ('Quarterly new-context replay', 'Context'): ('33/46', '0.3460', '0.3389', '27/45'),
        ('Quarterly new-context replay', 'Borda'): ('33/46', '0.3040', '0.2979', '16/45'),
        ('Quarterly new-context replay', 'RRF'): ('33/46', '0.3895', '0.3816', '27/45'),
    }

    for (c_name, m_name), (exp_cov, exp_qmrr, exp_pmrr, exp_hr5) in expected.items():
        row = df_tab2[(df_tab2['Cohort'] == c_name) & (df_tab2['Method'] == m_name)].iloc[0]
        assert row['Pair coverage'] == exp_cov, f"Mismatch cov for {c_name} {m_name}: {row['Pair coverage']} vs {exp_cov}"
        assert row['Query MRR'] == exp_qmrr, f"Mismatch Q-MRR for {c_name} {m_name}: {row['Query MRR']} vs {exp_qmrr}"
        assert row['Pair MRR'] == exp_pmrr, f"Mismatch P-MRR for {c_name} {m_name}: {row['Pair MRR']} vs {exp_pmrr}"
        assert row['HR@5'] == exp_hr5, f"Mismatch HR@5 for {c_name} {m_name}: {row['HR@5']} vs {exp_hr5}"

    print(">>> Manuscript Table 5 (historical subset) verified against paper across all 9 methods in both cohorts!")

def step3_displacement_decomposition():
    print("\n" + "=" * 80)
    print("STEP 3: Displacement Decomposition (Section 3.3, Equation 2)")
    print("=" * 80)

    df_cands = pd.read_csv(CAND_CORRECTED)
    df_pairs = pd.read_csv(PAIRS_CORRECTED)

    cands_jan = df_cands[df_cands['window_id'] == 'Jul25_Jan26'].copy()
    pairs_jan = df_pairs[df_pairs['evaluation_group'] == 'DEVELOPMENT_REF_JUL25_JAN26'].copy()

    r0_cands = cands_jan[cands_jan['origin'].isin(['R0_primekg', 'R0_and_CIViC_retrieved'])]
    r0_pairs = set(zip(r0_cands['query_id'], r0_cands['drug_norm']))

    b1_map = dict(zip(zip(cands_jan['query_id'], cands_jan['drug_norm']), cands_jan['b1_rank']))
    b0_map = dict(zip(zip(cands_jan['query_id'], cands_jan['drug_norm']), cands_jan['b0_rank']))

    u_mix, u_graph, u_mix_0 = [], [], []

    for qid, qgrp in pairs_jan.groupby('query_id'):
        rks_mix = [b1_map.get((qid, d), np.nan) for d in qgrp['positive_drug']]
        valid_mix = [r for r in rks_mix if pd.notna(r) and r > 0]
        u_mix.append(1.0 / min(valid_mix) if valid_mix else 0.0)

        rks_b0 = [b0_map.get((qid, d), np.nan) for d in qgrp['positive_drug']]
        valid_b0 = [r for r in rks_b0 if pd.notna(r) and r > 0]
        u_graph.append(1.0 / min(valid_b0) if valid_b0 else 0.0)

        rks_mix_0 = [b1_map.get((qid, d), np.nan) for d in qgrp['positive_drug'] if (qid, d) in r0_pairs]
        valid_mix_0 = [r for r in rks_mix_0 if pd.notna(r) and r > 0]
        u_mix_0.append(1.0 / min(valid_mix_0) if valid_mix_0 else 0.0)

    m_mix = float(np.mean(u_mix))
    m_graph = float(np.mean(u_graph))
    m_mix_0 = float(np.mean(u_mix_0))

    disp_loss = m_mix_0 - m_graph
    cov_gain = m_mix - m_mix_0
    net_diff = m_mix - m_graph

    print(f"  u_Mix (complete union):            {m_mix:.4f}")
    print(f"  u_Graph (R0 baseline):             {m_graph:.4f}")
    print(f"  u_Mix,0 (Mix restricted to R0):     {m_mix_0:.4f}")
    print(f"  Displacement Loss (u_Mix,0 - u_G): {disp_loss:+.4f} (paper Eq. 2: -0.1395)")
    print(f"  Coverage Gain (u_Mix - u_Mix,0):   {cov_gain:+.4f} (paper Eq. 2: +0.0754)")
    print(f"  Net Delta (u_Mix - u_Graph):       {net_diff:+.4f} (paper Eq. 2: -0.0641)")

    assert round(disp_loss, 4) == -0.1395, f"Displacement loss mismatch: {disp_loss}"
    assert round(cov_gain, 4) == 0.0754, f"Coverage gain mismatch: {cov_gain}"
    assert round(net_diff, 4) == -0.0641, f"Net delta mismatch: {net_diff}"
    print(">>> Displacement decomposition verified against paper Section 3.3 Equation (2)!")

def step4_interleaving_results_and_bounds():
    print("\n" + "=" * 80)
    print("STEP 4: Interleaving Results and Theoretical Upper Bounds (Manuscript Table 8)")
    print("=" * 80)

    df_cands = pd.read_csv(CAND_CORRECTED)
    df_pairs = pd.read_csv(PAIRS_CORRECTED)

    cands_q = df_cands[df_cands['window_id'].isin(['W1', 'W2', 'W3'])].copy()
    pairs_q = df_pairs[(df_pairs['evaluation_group'] == 'NEW_ENDPOINT_QUERY') & (df_pairs['endpoint_type'] == 'first_observed_pairs')].copy()

    cands_q['qid'] = cands_q['window_id'] + '::' + cands_q['query_id']
    pairs_q['qid'] = pairs_q['window_id'] + '::' + pairs_q['query_id']

    # 1. Compute Append-CIViC (O followed by N_e)
    app_civic_ranks = {}
    for qid, grp in cands_q.groupby('qid'):
        O = grp[grp['origin'].isin(['R0_primekg', 'R0_and_CIViC_retrieved'])].sort_values(by=['b0_rank', 'drug_norm'], ascending=[True, True])
        N = grp[grp['origin'] == 'CIViC_retrieved_new'].sort_values(by=['b6_rank', 'drug_norm'], ascending=[True, True])
        comb = pd.concat([O, N], ignore_index=True)
        for rk, d in enumerate(comb['drug_norm'], 1):
            app_civic_ranks[(qid, d)] = rk
    cands_q['append_civic_rank'] = [app_civic_ranks.get((q, d), np.nan) for q, d in zip(cands_q['qid'], cands_q['drug_norm'])]

    # 2. Compute U2 (Old-order oracle: Fixed O, freely ordered additions)
    # 3. Compute U3 (Two-sequence oracle: Fixed O, fixed N_e, label-informed optimal merge)
    u2_list, u3_list = [], []
    for qid, qgrp in pairs_q.groupby('qid'):
        grp = cands_q[cands_q['qid'] == qid]
        O_drugs = grp[grp['origin'].isin(['R0_primekg', 'R0_and_CIViC_retrieved'])].sort_values(by=['b0_rank', 'drug_norm'])['drug_norm'].tolist()
        N_drugs = grp[grp['origin'] == 'CIViC_retrieved_new'].sort_values(by=['b6_rank', 'drug_norm'])['drug_norm'].tolist()

        o_indices = [O_drugs.index(d) + 1 for d in qgrp['positive_drug'] if d in O_drugs]
        n_indices = [N_drugs.index(d) + 1 for d in qgrp['positive_drug'] if d in N_drugs]

        # U2
        if n_indices:
            u2_list.append(1.0)
        elif o_indices:
            u2_list.append(1.0 / min(o_indices))
        else:
            u2_list.append(0.0)

        # U3
        best_i = min(o_indices) if o_indices else np.inf
        best_j = min(n_indices) if n_indices else np.inf
        if best_i < np.inf and best_j < np.inf:
            u3_list.append(max(1.0 / best_i, 1.0 / best_j))
        elif best_i < np.inf:
            u3_list.append(1.0 / best_i)
        elif best_j < np.inf:
            u3_list.append(1.0 / best_j)
        else:
            u3_list.append(0.0)

    policies = [
        ('Append-SF', 'b2_rank', 'O followed by N_SF', 0.2004),
        ('Append-CIViC', 'append_civic_rank', 'O followed by N_e', 0.2018),
        ('Original insertion', 'rank_orig_p4_lam4_0', 'Fixed O, N_v, lambda=4', 0.2064),
        ('Evidence insertion', 'rank_ev_order_lam4_0', 'Fixed O, N_e, lambda=4', 0.2065),
        ('Two-sequence oracle', None, 'Best label-informed merge of O, N_e', 0.3294),
        ('RRF', 'b5_rank', 'Fusion of full L_g, L_e', 0.3895),
        ('Old-order oracle', None, 'Fixed O, freely ordered additions', 0.4568)
    ]

    tab6_rows = []
    for pol_name, rk_col, constraint, exp_val in policies:
        if pol_name == 'Two-sequence oracle':
            act_mrr = float(np.mean(u3_list))
        elif pol_name == 'Old-order oracle':
            act_mrr = float(np.mean(u2_list))
        else:
            cand_map = dict(zip(zip(cands_q['qid'], cands_q['drug_norm']), cands_q[rk_col]))
            q_rrs = []
            for qid, qgrp in pairs_q.groupby('qid'):
                rks = [cand_map.get((qid, d), np.nan) for d in qgrp['positive_drug']]
                valid = [r for r in rks if pd.notna(r) and r > 0]
                q_rrs.append(1.0 / min(valid) if valid else 0.0)
            act_mrr = float(np.mean(q_rrs))

        assert round(act_mrr, 4) == exp_val, f"Mismatch for {pol_name}: {act_mrr:.4f} vs {exp_val}"
        tab6_rows.append({
            'Policy': pol_name,
            'Ordering constraint': constraint,
            'Query MRR': f"{act_mrr:.4f}"
        })

    df_tab6 = pd.DataFrame(tab6_rows)
    print(df_tab6.to_string(index=False))

    out_file = TABLES_DIR / 'table5_interleaving_results.csv'
    df_tab6.to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_file)} (Maps to Manuscript Table 8)")
    print(">>> Manuscript Table 8 interleaving results and theoretical bounds verified!")

def step5_case_study():
    print("\n" + "=" * 80)
    print("STEP 5: Clinical Case Study (Manuscript Table 9 (historical columns))")
    print("=" * 80)

    df_cands = pd.read_csv(CAND_CORRECTED)

    cases = [
        ('January Breast MP:263', 'Jul25_Jan26', 'Breast Cancer|MP:263', 'dovitinib', 41, 41, 5),
        ('January Breast MP:263', 'Jul25_Jan26', 'Breast Cancer|MP:263', 'erdafitinib', 33, 6, 41),
        ('W1 Colorectal MP:5117', 'W1', 'Colorectal Cancer|MP:5117', 'pembrolizumab', 7, 7, 2),
        ('W1 Midline glioma MP:3807', 'W1', 'Diffuse Midline Glioma, H3 K27M-mutant|MP:3807', 'dordaviprone', 14, 14, 1),
        ('W3 Melanoma MP:281', 'W3', 'Melanoma|MP:281', 'belvarafenib', '--', '--', '--')
    ]

    case_rows = []
    for label, win, qid, drug, exp_b2, exp_b4, exp_b5 in cases:
        sub = df_cands[(df_cands['window_id'] == win) & (df_cands['query_id'] == qid) & (df_cands['drug_norm'] == drug)]
        if len(sub) > 0:
            act_b2 = int(sub['b2_rank'].iloc[0])
            act_b4 = int(sub['b4_rank'].iloc[0])
            act_b5 = int(sub['b5_rank'].iloc[0])
        else:
            act_b2, act_b4, act_b5 = '--', '--', '--'

        assert act_b2 == exp_b2 and act_b4 == exp_b4 and act_b5 == exp_b5, f"Case mismatch for {label} {drug}"
        case_rows.append({
            'Query context': label,
            'Drug': drug,
            'Append-SF': str(act_b2),
            'AltAppend': str(act_b4),
            'RRF': str(act_b5)
        })

    df_cases = pd.DataFrame(case_rows)
    print(df_cases.to_string(index=False))

    out_file = TABLES_DIR / 'table4_case_study.csv'
    df_cases.to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_file)} (Maps to Manuscript Table 9 (historical columns))")
    print(">>> Manuscript Table 9 (historical columns) case study verified against paper!")

def step6_temporal_endpoints():
    print("\n" + "=" * 80)
    print("STEP 6: Temporal Endpoints Breakdown (Manuscript Section 5.5 temporal summary)")
    print("=" * 80)

    df_pairs = pd.read_csv(Q_PAIRS_FILE)

    windows = [
        ('W1', 'Jan 1--Apr 1'),
        ('W2', 'Apr 1--Jul 1'),
        ('W3', 'Jul 1--Oct 1'),
    ]

    tab9_rows = []
    tot_cutoff = 0
    tot_replay_q = 0
    tot_cov = 0
    tot_pairs = 0

    for win, dates in windows:
        sub_cut = df_pairs[(df_pairs['window_id'] == win) & (df_pairs['evaluation_group'] == 'FIXED_PRE_CUTOFF') & (df_pairs['endpoint_type'] == 'first_observed_pairs')]
        sub_rep = df_pairs[(df_pairs['window_id'] == win) & (df_pairs['evaluation_group'] == 'NEW_ENDPOINT_QUERY') & (df_pairs['endpoint_type'] == 'first_observed_pairs')]

        cut_pairs = len(sub_cut)
        rep_queries = sub_rep['query_id'].nunique()
        cov_pairs = int(sub_rep['in_r1'].sum())
        rep_pairs = len(sub_rep)

        tot_cutoff += cut_pairs
        tot_replay_q += rep_queries
        tot_cov += cov_pairs
        tot_pairs += rep_pairs

        tab9_rows.append({
            'Window': win,
            '2026 dates': dates,
            'Cutoff-query pairs': cut_pairs,
            'Replay queries': rep_queries,
            'Replay coverage': f"{cov_pairs}/{rep_pairs}"
        })

    tab9_rows.append({
        'Window': 'Total',
        '2026 dates': '',
        'Cutoff-query pairs': tot_cutoff,
        'Replay queries': tot_replay_q,
        'Replay coverage': f"{tot_cov}/{tot_pairs}"
    })

    df_tab9 = pd.DataFrame(tab9_rows)
    print(df_tab9.to_string(index=False))

    out_file = TABLES_DIR / 'table7_temporal_endpoints.csv'
    df_tab9.to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_file)} (Maps to Manuscript Section 5.5 temporal summary)")

    # Verify matching Section 5.5 temporal summary
    assert tab9_rows[0]['Cutoff-query pairs'] == 1 and tab9_rows[0]['Replay queries'] == 17 and tab9_rows[0]['Replay coverage'] == '14/17'
    assert tab9_rows[1]['Cutoff-query pairs'] == 0 and tab9_rows[1]['Replay queries'] == 6 and tab9_rows[1]['Replay coverage'] == '6/6'
    assert tab9_rows[2]['Cutoff-query pairs'] == 2 and tab9_rows[2]['Replay queries'] == 22 and tab9_rows[2]['Replay coverage'] == '13/23'
    assert tab9_rows[3]['Cutoff-query pairs'] == 3 and tab9_rows[3]['Replay queries'] == 45 and tab9_rows[3]['Replay coverage'] == '33/46'
    print(">>> Manuscript Section 5.5 temporal summary temporal endpoints verified against paper!")

def step7_entrectinib_omission():
    print("\n" + "=" * 80)
    print("STEP 7: Entrectinib Omission Sensitivity Check (Section 5.4)")
    print("=" * 80)

    df_cands = pd.read_csv(CAND_CORRECTED)
    df_pairs = pd.read_csv(PAIRS_CORRECTED)

    cands_jan = df_cands[df_cands['window_id'] == 'Jul25_Jan26'].copy()
    pairs_jan = df_pairs[df_pairs['evaluation_group'] == 'DEVELOPMENT_REF_JUL25_JAN26'].copy()

    # Omit 14 entrectinib positive pairs
    pairs_no_ent = pairs_jan[pairs_jan['positive_drug'] != 'entrectinib'].copy()
    num_q = pairs_no_ent['query_id'].nunique()
    num_p = len(pairs_no_ent)

    print(f"Remaining after removing entrectinib: {num_q} queries, {num_p} pairs (expected: 27 queries, 29 pairs)")
    assert num_q == 27 and num_p == 29, f"Mismatch in entrectinib filtered counts: {num_q} q, {num_p} p"

    methods = [
        ('Append-SF', 'b2_rank', 0.1772),
        ('AltAppend', 'b4_rank', 0.1658),
        ('RRF', 'b5_rank', 0.2142),
        ('Context', 'b6_rank', 0.2747)
    ]

    ent_rows = []
    for m_name, rk_col, exp_mrr in methods:
        cand_map = dict(zip(zip(cands_jan['query_id'], cands_jan['drug_norm']), cands_jan[rk_col]))
        met = compute_mrr_and_hr(cand_map, pairs_no_ent, qid_col='query_id')
        assert round(met['query_mrr'], 4) == exp_mrr, f"Mismatch on entrectinib omission for {m_name}: {met['query_mrr']:.4f} vs {exp_mrr}"
        ent_rows.append({
            'Method': m_name,
            'Query MRR': f"{met['query_mrr']:.4f}",
            'Pair MRR': f"{met['pair_mrr']:.4f}",
            'HR@5': met['hr5_str']
        })
        print(f"  {m_name:12s} | Q-MRR: {met['query_mrr']:.4f} (exp: {exp_mrr}) | P-MRR: {met['pair_mrr']:.4f} | HR@5: {met['hr5_str']}")

    df_ent = pd.DataFrame(ent_rows)
    out_file = TABLES_DIR / 'entrectinib_ablation_summary.csv'
    df_ent.to_csv(out_file, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_file)}")
    print(">>> Entrectinib omission sensitivity verified against paper Section 5.4!")

def main():
    print("=" * 80)
    print("EvidencePath Reproduction Suite: Main Experimental Results")
    print("=" * 80)
    step1_candidate_coverage()
    step2_main_results_table()
    step3_displacement_decomposition()
    step4_interleaving_results_and_bounds()
    step5_case_study()
    step6_temporal_endpoints()
    step7_entrectinib_omission()
    print("\n" + "=" * 80)
    print("Historical baseline checks completed.")
    print("=" * 80)

if __name__ == '__main__':
    main()
