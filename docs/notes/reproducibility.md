# Reproducibility details

This companion records implementation and integrity checks moved out of the
manuscript's experimental-design narrative. It accompanies the local revised
source package. The review-facing mirror should be matched to RELEASE_v1.0.json. Generating this
artifact and refreshing a remote anonymous mirror are separate operations.

All paths below are relative to the distributed source-package root. The
data/processed/frozen_analysis directory contains frozen rankings, diagnostic outputs and
portable table-generation and verification scripts. Original raw knowledge
graph and full snapshot reconstruction require the separately identified source
resources. The retained run identifier is 20261123T004441Z.

## Training and validation evidence exclusion

The frozen supervision contains 84 training pairs from 31 queries and 16
validation pairs from seven queries, with disjoint molecular profiles. Each
candidate's full registered label-defining EID union is excluded from that
candidate's visible evidence in both splits.

The independent audit found that all 100 candidate-specific anchor unions match
the full evidence registry, with zero intersections between the excluded EIDs
and consumed evidence links. All 300 consumed CIViC count-feature values were
recomputed; the maximum absolute difference was
8.881784197001252e-16. These checks cover the three derived count features used
by the frozen SF and AltGraph models. They do not extend the exclusion to all
items from the same publication, certify unused legacy features, or validate
clinical outcomes. Unlabelled pairs were not converted into negative labels.

Evidence:
- data/processed/frozen_analysis/e6/training_validation_validation.json
- data/processed/frozen_analysis/e6/training_validation_anchor_count_audit.csv
- docs/notes/source_independent_audit.json

## Frozen resource identity

The original run's 39 registered input files had unchanged SHA-256 hashes before
and after the added diagnostics. Recorded and actual resource hashes agree for
the graph, evidence snapshots, gene vocabulary, mappings and frozen model
resources. Resource identity is distinct from a claim that every possible
source of leakage has been excluded.

The copied bundle replaces personal paths with anonymous markers. The original
resource hashes remain intact; a packaged file's hash can differ from its
original artifact hash after path sanitization or line-ending normalization.

Evidence:
- docs/notes/source_input_manifest.json
- docs/notes/source_independent_audit.json
- data/processed/frozen_analysis/e6/resource_versions.csv
- docs/notes/source_copy_manifest.json

## Replay paired cluster bootstrap

Queries are partitioned into connected components under shared positive drugs
or shared canonical positive-label sources. The drug partition contains 19
components and the source partition 24; their largest components contain seven
and six queries, respectively.

Each partition uses an independently initialized NumPy PCG64 stream and 10,000
draws. The drug seed is 2026112301 and the source seed is 2026112302. Each round
samples C whole components with replacement from C components. Repeated
components contribute all their queries with the sampled multiplicity.

The paired mean divides the sum of sampled query-level differences by the
actual sampled query count. Components are not assigned equal weight in the
final mean regardless of size. The 95% percentile interval uses the empirical
2.5th and 97.5th percentiles with linear quantile interpolation. Saved component
memberships, sampling indices and replicates support the reported intervals and
leave-one-component analyses.

Evidence:
- docs/notes/source_execution_config.json
- data/processed/frozen_analysis/e1/cluster_memberships.csv
- data/processed/frozen_analysis/e1/drug_bootstrap_draws.npz
- data/processed/frozen_analysis/e1/source_bootstrap_draws.npz
- data/processed/frozen_analysis/e1/bootstrap_replicates.csv
- data/processed/frozen_analysis/e1/bootstrap_confidence_intervals.csv
- data/processed/frozen_analysis/e1/leave_one_component_out.csv

## Archived development comparison

The historical January RRF-minus-AltAppend comparison uses 2,000 whole-component
bootstrap draws with seed 7147 and recomputes the query denominator in every
replicate. Its 17 drug components and 18 source components, intervals and
leave-one-component results belong to that development cohort and comparator.
They are separate from replay's 10,000-draw comparisons against Context. No
random-number-generator family is inferred here for the archived development
calculation.

The companion S1 retains this historical protocol and its numerical results.

## Conditional order permutations

The new graph-order experiment uses 5,000 NumPy PCG64 draws per cohort, with seed
7147 reset separately for development and replay. Queries use a stable sorted
window/query order. Within each round, the full graph list is independently
permuted within every query.

Candidate support, memberships, labels, the other branch's complete clinical
order, the RRF parameters and the final tie rule remain fixed. Each candidate's
number of contributing branches remains one or two; the rank-dependent score
terms themselves are recomputed. The clinical order includes its terminal SF
key. The clinical-order experiment reuses the hashed archived 5,000-round
metrics rather than recomputing them from raw resources in the portable bundle.

Upper tails count statistics at least as large as observed and use
(b + 1) / 5001. Holm correction covers the full 12-test family: two shuffled
branches, two cohorts and three metrics. Saved indices, permutations and
round-level metrics retain the implementation details.

Evidence:
- docs/notes/source_execution_config.json
- data/processed/frozen_analysis/e3/permutation_invariants.json
- data/processed/frozen_analysis/e3/permutation_tail_tests.csv
- data/processed/frozen_analysis/e3/development_graph_permutations.npz
- data/processed/frozen_analysis/e3/replay_graph_permutations.npz
- data/processed/frozen_analysis/archived_inputs/diagnostics/civic_shuffle_round_metrics.csv

## Graph-to-Mix score invariance

A single frozen SF prediction vector on the complete union supplies both the
Graph subset and Mix's full-pool ranking. The historical-export cross-check
covers all 1,262 retained graph candidates, with zero missing scores and maximum
absolute score difference zero. Their relative order is unchanged; additions
can change absolute positions. Code inspection and the stored score ledger
confirm the shared prediction path.

Consequently, the measured displacement is caused by placing additions ahead
of old positives under the same scores, rather than by fitting or invoking a
different ranking model. The exact query-level decomposition was checked for
all 45 replay queries.

Evidence:
- data/processed/frozen_analysis/e5/scoring_implementation_evidence.json
- data/processed/frozen_analysis/e5/old_candidate_score_invariance.csv
- data/processed/frozen_analysis/e5/replay_displacement_summary.csv
- data/processed/frozen_analysis/e5/query_displacement_decomposition.csv
- data/processed/frozen_analysis/e5/decomposition_validation.json

## Insertion implementation

Both insertion policies preserve their specified old and addition sequences.
The penalty is lambda = 4, selected on January development and held fixed in
replay. When two dynamic-programming transitions differ by at most 1e-12, the
solver ends the current prefix with an old item. The companion S1 states the
priority definition, objective and sequence constraints. This implementation
tolerance does not change the mathematical conditional-oracle bound.

Evidence:
- data/processed/frozen_analysis/e6/reproduction_settings.csv
- data/processed/frozen_analysis/e6/archived_insertion_lambda_tuning.csv
- Supplement_S1.tex

## Regenerate tables and verify the frozen evidence

From the source-package root:

    python -m pip install -r code/requirements.txt
    python code/src/build_revision_tables.py --run data/processed/frozen_analysis --out code/results/generated/primary
    python code/src/verify_evidence.py --run data/processed/frozen_analysis --generated code/results/generated/primary

See README.md for the complete bundle scope and file inventory.
The commands regenerate tables and figures from frozen analysis inputs and
verify the archived diagnostic evidence. They do not retrain models or rebuild
the full raw biomedical data pipeline. All manuscript figure and table captions
remain short names; explanations belong in the surrounding prose.
