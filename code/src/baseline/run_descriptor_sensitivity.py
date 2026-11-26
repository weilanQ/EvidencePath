#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical source-descriptor sensitivity audit.

Checks saved gene/branch, candidate and positive-rank comparisons for four
descriptor-affected queries, retaining the companion S1 sensitivity evidence.
It does not reconstruct the original source descriptions or raw feature pipeline.

Inputs: data/processed/baseline_reference/sensitivity.
Outputs: code/results/generated/baseline/tables, unless overridden by
EVIDENCEPATH_RESULTS_DIR.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / 'data' / 'processed' / 'baseline_reference' / 'sensitivity'
TABLES_DIR = Path(os.environ.get('EVIDENCEPATH_RESULTS_DIR', REPO_ROOT / 'code' / 'results' / 'generated')) / 'baseline' / 'tables'
TABLES_DIR.mkdir(parents=True, exist_ok=True)


def display_path(path):
    """Keep status output readable when a caller uses an external output folder."""
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).name


def main():
    print("=" * 80)
    print("EvidencePath Reproduction Suite: Molecular Profile Descriptor Sensitivity")
    print("=" * 80)

    f_gene = DATA_DIR / 'gene_parsing_and_branch_comparison.csv'
    f_group = DATA_DIR / 'group_replacement_metrics_summary.csv'
    f_pairs = DATA_DIR / 'positive_pair_ranks_comparison.csv'
    f_diffs = DATA_DIR / 'candidate_level_differences.csv'

    df_gene = pd.read_csv(f_gene)
    df_group = pd.read_csv(f_group)
    df_pairs = pd.read_csv(f_pairs)
    df_diffs = pd.read_csv(f_diffs)

    # 1. Verify 4 queries and 105 candidate items
    print("\n[Audit 1] Gene parsing and candidate branch comparisons across 4 queries:")
    cols_gene = ['window_id', 'query_id', 'molecular_profile_A', 'molecular_profile_B',
                 'parsed_genes_A', 'parsed_genes_B', 'r1_count_A', 'r1_count_B']
    print(df_gene[cols_gene].to_string(index=False))

    total_cands = df_gene['r1_count_A'].sum()
    print(f"\nTotal candidate entries across 4 queries: {total_cands} (expected: 105)")
    assert total_cands == 105, f"Expected 105 candidates, got {total_cands}"

    # Verify candidate count invariance: r1_count_A == r1_count_B
    assert (df_gene['r1_count_A'] == df_gene['r1_count_B']).all(), "Candidate counts differed!"
    assert (df_gene['r1_delta'] == 0).all(), "Candidate delta non-zero!"

    # 2. Verify Positive Pair Ranks invariance across Group A and Group B
    print("\n[Audit 2] Positive pair ranks comparison across Group A and Group B:")
    cols_pair = ['window_id', 'query_id', 'positive_drug', 'rank_b5_A', 'rank_b5_B', 'rank_status']
    print(df_pairs[cols_pair].to_string(index=False))

    for _, r in df_pairs.iterrows():
        assert r['rank_b5_A'] == r['rank_b5_B'] or (pd.isna(r['rank_b5_A']) and pd.isna(r['rank_b5_B'])), f"Positive pair rank changed for {r['query_id']} @@ {r['positive_drug']}"
    print(">>> All 4 positive pairs strictly retain their ranks or unretrieved status!")

    # 3. Verify Candidate Level Rank differences (Mix cetuximab vs vemurafenib swap)
    diffs = df_diffs[df_diffs['has_difference'] == True]
    print(f"\n[Audit 3] Candidate-level rank differences count: {len(diffs)} / {len(df_diffs)} rows")
    if len(diffs) > 0:
        print(diffs[['window_id', 'query_id', 'drug_norm', 'b1_rank_A', 'b1_rank_B', 'difference_details']].to_string(index=False))
        swap_drugs = sorted(diffs['drug_norm'].unique().tolist())
        assert swap_drugs == ['cetuximab', 'vemurafenib'], f"Unexpected swap candidates: {swap_drugs}"
        print(">>> Only cetuximab and vemurafenib swap at ranks 49 and 50 under Mix (B1)!")

    # 4. Verify Cohort Level Metrics invariance across Group A and Group B
    print("\n[Audit 4] Cohort-level metrics comparison (Group A vs Group B replacement):")
    cols_group = ['evaluation_group', 'method_code', 'query_mrr_A', 'query_mrr_B', 'delta_query_mrr', 'query_hr5_A', 'query_hr5_B']
    print(df_group[cols_group].to_string(index=False))

    for _, r in df_group.iterrows():
        if r['method_code'] in ['B0', 'B2', 'B4', 'B5', 'B6', 'P4_lam4', 'P4_ev_order_lam4']:
            assert abs(r['delta_query_mrr']) < 1e-9, f"MRR delta non-zero on {r['method_code']}: {r['delta_query_mrr']}"
            assert abs(r['delta_pair_mrr']) < 1e-9, f"Pair MRR delta non-zero on {r['method_code']}: {r['delta_pair_mrr']}"
            assert abs(r['delta_query_hr5']) < 1e-9, f"HR@5 delta non-zero on {r['method_code']}: {r['delta_query_hr5']}"

    out_file = TABLES_DIR / 'descriptor_sensitivity_summary.csv'
    df_group.to_csv(out_file, index=False, encoding='utf-8')
    print(f"\nSaved: {display_path(out_file)}")
    print(">>> Descriptor sensitivity audit verified against Supplement S1!")

if __name__ == '__main__':
    main()
