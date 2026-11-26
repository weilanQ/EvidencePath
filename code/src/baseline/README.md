# Historical subanalyses

These scripts preserve the earlier frozen-ranking calculations and assertions.
Their CSV basenames remain unchanged for traceability; their old table numbers
are not the revised manuscript's numbering.

The current release entry point and its table/figure builder are authoritative
for the revised main results, Shared-first control, paired replay uncertainty,
graph shuffles, joint Holm tests and actual-use source exclusion.

| Script | Current use | Execution type |
| --- | --- | --- |
| `run_main_results.py` | Development coverage (Table 4); original policy subset of Table 5; development Eq. (2) decomposition; interleaving/oracles (Table 8); original columns of Table 9; Section 5.5 temporal counts; Section 5.4 entrectinib omission. | Recomputes from frozen candidate and label tables. |
| `run_cluster_sensitivity.py` | Development RRF minus AltAppend, 17 drug / 18 source components and 35 omissions, retained in Section 5.4 and S1. | Checks saved intervals/component/omission summaries; does not regenerate bootstrap draws. |
| `run_descriptor_sensitivity.py` | Companion S1 source-descriptor sensitivity. | Checks saved comparisons; does not reconstruct raw gene/profile descriptors. |
| `run_civic_order_shuffle.py` | CIViC-only rows of current Table 7 and S1, plus archived positive-origin stratum summaries. | Optional live 5,000-round permutation rerun per cohort. No new graph-order control or joint 12-test Holm correction. |
| `run_parameter_grid.py` | Section 5.4 and S1 exact-rational 54-setting grid against Append-SF. | Recomputed in the default one-command run; its MRR/HR@5 values are checked against the archived stronger-baseline diagnostic. |
| `plot_figures.py` | Historical parameter heatmap and original five-policy HR plot. | Historical plotting only. The old HR plot omits Context/Shared-first and is not the revised Figure 2. |

Inputs are read from `data/processed/baseline_reference/`.
Default outputs are written under
`code/results/generated/baseline/{tables,figures}/`.
The wrapper can set `EVIDENCEPATH_RESULTS_DIR` to select a separate output root;
these scripts append `baseline/tables` or `baseline/figures`.

Run from the repository root, for example:

```sh
python code/src/baseline/run_main_results.py
python code/src/baseline/run_cluster_sensitivity.py
python code/src/baseline/run_descriptor_sensitivity.py
```

The historical live routines can also be invoked separately:

```sh
python code/src/baseline/run_civic_order_shuffle.py
python code/src/baseline/run_parameter_grid.py
```

The code does not retrain models, download original knowledge-graph/snapshot
resources or create a prospective evaluation. Candidate and label inputs are
unchanged historical records. Runtime varies with the machine; no total-runtime
guarantee is made.
