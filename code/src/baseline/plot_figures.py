#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical baseline plots.

Generates the archived absolute-MRR grid and the original five-policy HR plot
from historical baseline tables. The five-policy HR plot omits Context and
Shared-first, and must not replace the revised manuscript Figure 2.
The current table/figure generator supplies the revised seven-policy figure.

Inputs: code/results/generated/baseline/tables by default.
Outputs: code/results/generated/baseline/figures, unless overridden by
EVIDENCEPATH_RESULTS_DIR.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[3]
TABLES_DIR = Path(os.environ.get('EVIDENCEPATH_RESULTS_DIR', REPO_ROOT / 'code' / 'results' / 'generated')) / 'baseline' / 'tables'
FIGURES_DIR = Path(os.environ.get('EVIDENCEPATH_RESULTS_DIR', REPO_ROOT / 'code' / 'results' / 'generated')) / 'baseline' / 'figures'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Set matplotlib fonts and styling
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.autolayout'] = False


def display_path(path):
    """Keep status output readable when a caller uses an external output folder."""
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).name


def plot_rrf_sensitivity_heatmap():
    f_grid = TABLES_DIR / 'rrf_grid_scan_54_summary.csv'
    assert f_grid.is_file(), f"Missing {f_grid}. Please run run_parameter_grid.py first!"
    df_grid = pd.read_csv(f_grid)

    k_vals = sorted(df_grid['k'].unique())
    alpha_vals = sorted(df_grid['alpha'].unique())

    # Build 2D matrices
    jan_mat = np.zeros((len(k_vals), len(alpha_vals)))
    new_mat = np.zeros((len(k_vals), len(alpha_vals)))
    jan_delta_mat = np.zeros((len(k_vals), len(alpha_vals)))
    new_delta_mat = np.zeros((len(k_vals), len(alpha_vals)))

    for _, r in df_grid.iterrows():
        i = k_vals.index(int(r['k']))
        j = alpha_vals.index(round(float(r['alpha']), 1))
        jan_mat[i, j] = r['jan_query_mrr']
        new_mat[i, j] = r['new_query_mrr']
        jan_delta_mat[i, j] = r['jan_delta_vs_b2']
        new_delta_mat[i, j] = r['new_delta_vs_b2']

    vmin_round = 0.20
    vmax_round = 0.48

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), dpi=300)
    cmap = plt.cm.viridis

    # Left: January Development
    im0 = axes[0].imshow(jan_mat, cmap=cmap, vmin=vmin_round, vmax=vmax_round, aspect='auto')
    axes[0].set_title("Panel A: January Development Set (N=41 queries)\nBaseline B2 Query MRR = 0.3733", fontsize=13, fontweight='bold', pad=12)
    axes[0].set_xlabel(r"Graph Branch Weight $\alpha$ (Evidence Weight = $1 - \alpha$)", fontsize=11, labelpad=8)
    axes[0].set_ylabel(r"Smoothing Constant $k$", fontsize=11, labelpad=8)
    axes[0].set_xticks(range(len(alpha_vals)))
    axes[0].set_xticklabels([f"{a:.1f}" for a in alpha_vals], fontsize=10)
    axes[0].set_yticks(range(len(k_vals)))
    axes[0].set_yticklabels(k_vals, fontsize=10)

    # Right: Quarterly New Queries
    im1 = axes[1].imshow(new_mat, cmap=cmap, vmin=vmin_round, vmax=vmax_round, aspect='auto')
    axes[1].set_title("Panel B: Quarterly New Queries W1-W3 (N=45 queries)\nBaseline B2 Query MRR = 0.2004", fontsize=13, fontweight='bold', pad=12)
    axes[1].set_xlabel(r"Graph Branch Weight $\alpha$ (Evidence Weight = $1 - \alpha$)", fontsize=11, labelpad=8)
    axes[1].set_ylabel(r"Smoothing Constant $k$", fontsize=11, labelpad=8)
    axes[1].set_xticks(range(len(alpha_vals)))
    axes[1].set_xticklabels([f"{a:.1f}" for a in alpha_vals], fontsize=10)
    axes[1].set_yticks(range(len(k_vals)))
    axes[1].set_yticklabels(k_vals, fontsize=10)

    # Annotations
    for i in range(len(k_vals)):
        for j in range(len(alpha_vals)):
            val_j = jan_mat[i, j]
            del_j = jan_delta_mat[i, j]
            txt_color_j = "white" if val_j < 0.35 else "black"
            axes[0].text(j, i, f"{val_j:.3f}\n({del_j:+.3f})", ha='center', va='center',
                         color=txt_color_j, fontsize=8.5, fontweight='normal')

            val_n = new_mat[i, j]
            del_n = new_delta_mat[i, j]
            txt_color_n = "white" if val_n < 0.35 else "black"
            axes[1].text(j, i, f"{val_n:.3f}\n({del_n:+.3f})", ha='center', va='center',
                         color=txt_color_n, fontsize=8.5, fontweight='normal')

    # Highlight default point (k=60, alpha=0.5)
    def_i = k_vals.index(60)
    def_j = alpha_vals.index(0.5)

    for ax in [axes[0], axes[1]]:
        rect = patches.Rectangle((def_j - 0.48, def_i - 0.48), 0.96, 0.96,
                                 linewidth=3.0, edgecolor='#E63946', facecolor='none', linestyle='-')
        ax.add_patch(rect)
        ax.plot(def_j, def_i - 0.28, marker='*', color='#E63946', markersize=10)

    fig.subplots_adjust(bottom=0.15, right=0.88, wspace=0.25)
    cbar_ax = fig.add_axes([0.90, 0.18, 0.02, 0.65])
    cbar = fig.colorbar(im1, cax=cbar_ax)
    cbar.set_label("Query MRR (Shared Color Scale)", fontsize=11, labelpad=10)
    cbar.ax.tick_params(labelsize=10)

    caption_text = (
        "Note: Across both evaluation groups, all 54 parameter combinations strictly outperform their respective B2 baselines (Δ vs B2 > 0).\n"
        "Red box marks the frozen default benchmark point (k = 60, α = 0.5; starred). "
        "In the Quarterly New Queries group, the 3×3 default neighborhood (k ∈ [40, 80], α ∈ [0.4, 0.6])\n"
        "exhibits an empirical variation range of Query MRR from 0.3128 to 0.4279 and HR@5 from 19/45 to 30/45 (42.2% to 66.7%)."
    )
    fig.text(0.46, 0.03, caption_text, ha='center', fontsize=9.2, color='#2B2D42',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA', edgecolor='#CED4DA', alpha=0.95))

    out_fig = FIGURES_DIR / 'figure_rrf_sensitivity_heatmap.png'
    plt.savefig(out_fig, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Emitted: {display_path(out_fig)}")

def plot_quarterly_new_hr_at_k():
    f_tab2 = TABLES_DIR / 'table2_main_results.csv'
    assert f_tab2.is_file(), f"Missing {f_tab2}. Please run run_main_results.py first!"
    df_tab2 = pd.read_csv(f_tab2)

    sub = df_tab2[df_tab2['Cohort'] == 'Quarterly new-context replay']

    methods_order = [
        ('RRF', '#D62828', '*', 12, 2.8, '-', 'RRF (k=60) [Frozen Benchmark]'),
        ('CIViC branch', '#F77F00', 's', 8, 2.0, '-.', 'CIViC branch (re only)'),
        ('Borda', '#003049', 'd', 8, 2.0, '--', 'Normalized Borda'),
        ('Append-SF', '#2A9D8F', '^', 8, 2.0, ':', 'Append-SF'),
        ('Graph', '#6C757D', 'o', 8, 1.8, ':', 'Graph (rg only)')
    ]

    k_vals = [1, 3, 5, 10]
    denom = 45

    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)

    for m_code, color, marker, ms, lw, ls, label in methods_order:
        row = sub[sub['Method'] == m_code].iloc[0]
        hits = [row['hr1_count'], row['hr3_count'], row['hr5_count'], row['hr10_count']]
        rates = [h / denom for h in hits]

        ax.plot(k_vals, rates, label=label, color=color, marker=marker,
                markersize=ms, linewidth=lw, linestyle=ls)

        if m_code in ['RRF', 'CIViC branch', 'Append-SF']:
            for k, r, h in zip(k_vals, rates, hits):
                offset_y = 0.022 if m_code == 'RRF' else (-0.028 if m_code == 'CIViC branch' else -0.025)
                if k == 5:
                    ax.annotate(f"{h}/{denom}\n({r*100:.1f}%)", xy=(k, r),
                                xytext=(k, r + offset_y * 1.3),
                                ha='center', fontsize=8.5, fontweight='bold', color=color)

    ax.set_title("Quarterly New Queries: Hit Rate across Ranking Thresholds (HR@K)\nN = 45 Non-overlapping Prospective Queries (W1-W3)",
                 fontsize=13, fontweight='bold', pad=14)
    ax.set_xlabel("Ranking Threshold K (Top-K Cutoff)", fontsize=11, labelpad=8)
    ax.set_ylabel("Hit Rate HR@K (Query Recall@K)", fontsize=11, labelpad=8)
    ax.set_xticks(k_vals)
    ax.set_xticklabels([f"K = {k}" for k in k_vals], fontsize=10)
    ax.set_ylim(-0.02, 0.78)
    ax.set_yticks(np.arange(0.0, 0.81, 0.1))
    ax.set_yticklabels([f"{y*100:.0f}%" for y in np.arange(0.0, 0.81, 0.1)], fontsize=10)

    ax.axvline(x=5, color='gray', linestyle='--', alpha=0.5, linewidth=1.2)
    ax.text(5.08, 0.03, 'Primary Endpoint Cutoff (K=5)', color='#495057', fontsize=9, style='italic')

    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, framealpha=0.95, fontsize=9.5)

    out_fig = FIGURES_DIR / 'figure_quarterly_new_hr_at_k.png'
    plt.savefig(out_fig, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Emitted: {display_path(out_fig)}")

def main():
    print("=" * 80)
    print("EvidencePath Reproduction Suite: Regenerating Figures")
    print("=" * 80)
    plot_rrf_sensitivity_heatmap()
    plot_quarterly_new_hr_at_k()
    print("All figures successfully regenerated!")

if __name__ == '__main__':
    main()
