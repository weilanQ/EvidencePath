# Final paper to artifact map

The main paper is the 16-page Analyzing revision; S1 is the 8-page companion. Numeric source files retain unrounded values. Generated captions are short names only.

| Final item | Implementation/evidence | Fresh output or verification |
| --- | --- | --- |
| Table 1, populations | frozen_analysis/e0 labels; baseline_reference/ground_truth/quarterly_positive_pairs_50.csv | Counts checked by main/baseline workflows; 45/46 replay and 3/3 cutoff-defined stay separate |
| Tables 2-3, policies/settings | code/configs/frozen_analysis_v1.0.json; e6/reproduction_settings.csv | Configuration/protocol, not an estimated performance table |
| Table 4, candidate coverage | code/src/build_revision_tables.py; e0/frozen_analysis_bundle | primary/table_candidate_coverage.tex; audited_candidate_coverage.csv |
| Table 5, ten-policy main comparison | Current builder, same frozen candidates/labels; e2 shared-first rankings | primary/table_main_results.tex; audited_main_results.csv |
| Table 6, paired replay comparisons | e1/bootstrap_replicates, cluster memberships and saved draws | primary/table_paired_replay.tex; verifier reconstructs all saved weighted means and 32 intervals |
| Table 7, conditional shuffles | e3 graph rounds plus archived_inputs/diagnostics/civic_shuffle_round_metrics.csv | primary/table_shuffle_replay.tex; 12 tails/Holm corrections verified |
| Table 8, insertion and U2/U3 ceilings | code/src/baseline/run_main_results.py; baseline_reference candidates/positives | baseline/tables/table5_interleaving_results.csv |
| Table 9, original five cases plus Context/Shared-first | Current builder; e6/case_rankings_with_context.csv | primary/table_cases_with_context.tex; audited_case_comparison.csv |
| Table 10, source-excluded sensitivity | e4 actual query evidence, label support sources and retained labels | primary/table_source_excluded.tex; 46 classifications and 39/39 retained labels checked |
| Figure 1, workflow | docs/papers/latex/assets/evidencepath-framework.png | Preserved illustrative asset, not a computed performance result |
| Figure 2, query HR-at-K | Current builder, seven policies | primary/replay_hr_at_k_with_context.pdf and .png |
| Eq. (2), replay displacement | e0 frozen ranks; e5 query decomposition | Independent exact-fraction checks for all 45 queries |
| Eq. (3), two-sequence ceiling | baseline/run_main_results.py | Table 8 historical result; not a generally optimal deployable ranker |
| Section 5.4, parameter sensitivity | baseline/run_parameter_grid.py; e6 strong-baseline grid | Fresh baseline/tables/rrf_grid_scan_54_summary.csv, checked against e6 |
| Section 5.4, old development cluster/omission results | baseline/run_cluster_sensitivity.py and run_main_results.py | Labelled historical outputs, distinct from replay Context comparison |
| Section 5.5, windows/candidate ceiling | baseline/run_main_results.py | baseline/tables/table7_temporal_endpoints.csv |
| S1, descriptors | baseline/run_descriptor_sensitivity.py; baseline_reference/sensitivity | Stored descriptor comparisons audited; not raw descriptor re-extraction |
| S1, full shuffle/branch/retention tables | Current builder | primary/table_shuffle_all_supp.tex; table_branch_lengths.tex; table_new_old_tradeoff.tex |
| S1, sealed pilot | baseline_reference/sealed_pilot | Archival protocol/result inspection; not a new evaluation in this release |

Paths starting e0-e6 or archived_inputs are relative to data/processed/frozen_analysis. Baseline input paths are relative to data/processed/baseline_reference. Outputs are relative to code/results/generated. Source data/labels and manuscript numbers are unchanged by this directory reorganization.
