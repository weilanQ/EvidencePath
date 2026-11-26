#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical development RRF-minus-AltAppend sensitivity audit.

Reads the archived confidence intervals, component definitions and
leave-one-component summaries. It checks the 17-drug/18-source component
analysis retained in Section 5.4 and companion S1, with 35 omission comparisons.
This is an audit of saved summaries, not a fresh 2,000-round bootstrap.
It is distinct from the revised replay RRF-minus-Context analysis.

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
    print("Historical development cluster sensitivity (RRF minus AltAppend; S1)")
    print("=" * 80)

    f_boot = DATA_DIR / 'bootstrap_confidence_intervals.csv'
    f_defs = DATA_DIR / 'cluster_definitions_summary.csv'
    f_loco = DATA_DIR / 'leave_one_cluster_out_sensitivity.csv'

    df_boot = pd.read_csv(f_boot)
    df_defs = pd.read_csv(f_defs)
    df_loco = pd.read_csv(f_loco)

    # 1. Cluster counts and largest component
    drug_clusters = df_defs[df_defs['structure_type'] == 'Drug_Structure']
    source_clusters = df_defs[df_defs['structure_type'] == 'Source_Structure']

    num_drug_c = len(drug_clusters)
    num_source_c = len(source_clusters)
    max_drug_size = drug_clusters['cluster_size'].max()
    max_source_size = source_clusters['cluster_size'].max()

    print(f"  Drug-defined clusters:   {num_drug_c} (largest cluster: {max_drug_size} queries, entrectinib)")
    print(f"  Source-defined clusters: {num_source_c} (largest cluster: {max_source_size} queries)")

    assert num_drug_c == 17, f"Expected 17 drug clusters, got {num_drug_c}"
    assert num_source_c == 18, f"Expected 18 source clusters, got {num_source_c}"
    assert max_drug_size == 14, f"Expected largest drug cluster of size 14, got {max_drug_size}"
    assert max_source_size == 14, f"Expected largest source cluster of size 14, got {max_source_size}"

    # 2. Primary B5 vs B4 MRR delta and 95% bootstrap intervals
    drug_b5_b4 = df_boot[(df_boot['structure'] == 'Drug_Clusters') & (df_boot['comparison_code'] == 'B5_vs_B4') & (df_boot['metric'] == 'MRR')].iloc[0]
    source_b5_b4 = df_boot[(df_boot['structure'] == 'Source_Clusters') & (df_boot['comparison_code'] == 'B5_vs_B4') & (df_boot['metric'] == 'MRR')].iloc[0]

    tab6_rows = [
        {
            'Clustering criterion': 'Shared positive drug',
            'Clusters': num_drug_c,
            'ΔMRR': f"{drug_b5_b4['point_estimate']:+.4f}",
            '95% percentile interval': f"[{drug_b5_b4['ci_lower_95']:+.4f}, {drug_b5_b4['ci_upper_95']:+.4f}]"
        },
        {
            'Clustering criterion': 'Shared evidence source',
            'Clusters': num_source_c,
            'ΔMRR': f"{source_b5_b4['point_estimate']:+.4f}",
            '95% percentile interval': f"[{source_b5_b4['ci_lower_95']:+.4f}, {source_b5_b4['ci_upper_95']:+.4f}]"
        }
    ]

    df_tab6 = pd.DataFrame(tab6_rows)
    print("\n" + "=" * 80)
    print("Development sensitivity retained in Section 5.4 and S1")
    print("=" * 80)
    print(df_tab6.to_string(index=False))

    out_tab6 = TABLES_DIR / 'table6_cluster_sensitivity.csv'
    df_tab6.to_csv(out_tab6, index=False, encoding='utf-8')
    print(f"Saved: {display_path(out_tab6)} (development RRF minus AltAppend; S1)")

    # Assertions matching development sensitivity in S1 in paper
    assert tab6_rows[0]['ΔMRR'] == '+0.0448' and tab6_rows[0]['95% percentile interval'] == '[+0.0102, +0.1099]'
    assert tab6_rows[1]['ΔMRR'] == '+0.0448' and tab6_rows[1]['95% percentile interval'] == '[+0.0108, +0.1095]'
    print(">>> Archived development bootstrap-interval summaries checked.")

    # 3. Leave-one-cluster-out sensitivity
    loco_deltas = df_loco['B5_vs_B4_diff_mrr']
    min_loco = loco_deltas.min()
    max_loco = loco_deltas.max()
    print(f"\nLeave-One-Cluster-Out Sensitivity (35 total comparisons):")
    print(f"  ΔMRR range: {min_loco:.4f} -- {max_loco:.4f} (Supplement S1: 0.0251 -- 0.0540)")

    assert len(df_loco) == 35, f"Expected 35 LOCO comparisons, got {len(df_loco)}"
    assert round(min_loco, 4) == 0.0251, f"Expected min LOCO 0.0251, got {min_loco:.4f}"
    assert round(max_loco, 4) == 0.0540, f"Expected max LOCO 0.0540, got {max_loco:.4f}"
    print(">>> Leave-one-cluster-out range verified against Supplement S1!")

if __name__ == '__main__':
    main()
