# Data dictionary

All bundled experiment inputs are derived or archival research records. No file in data/processed should be interpreted as an unmodified copy of the original full PrimeKG graph or CIViC monthly database.

## Evaluation keys and units

| Field | Meaning |
| --- | --- |
| window_id | Evaluation window; Jul25_Jan26 denotes development, W1-W3 quarterly windows |
| query_id | Canonical disease and molecular-profile key; does not include the replay window |
| qid | Window-qualified query-instance key, required when grouping replay records |
| drug_norm | Frozen canonical single-drug identity |
| positive_drug | Canonical drug of an eligible positive query-drug pair |
| evaluation_group | Frozen population assignment; do not mix replay, cutoff-defined and augmentation denominators |
| origin | Branch membership, not novelty or biological discovery |
| R0_primekg | Graph-only membership |
| R0_and_CIViC_retrieved | Shared graph/evidence membership |
| CIViC_retrieved_new | Evidence-exclusive relative to the graph pool at cutoff; not a new drug or newly discovered effect |
| rg, re | One-based graph and clinical-branch rank; missing means absent from that branch |
| b0_rank ... b6_rank | Graph, Mix, Append-SF, AltGraph, AltAppend, RRF and Context respectively |
| shared_first_rank | Stable shared-first Context ranking on the full candidate union |
| best_rank | First eligible positive rank for a query; absent positives contribute RR zero |
| rr, query_mrr | Query-best reciprocal rank and its mean across eligible query instances |
| pair_mrr | Mean reciprocal rank across all eligible positive pairs, including unretrieved pairs as zero |
| hit1, hit3, hit5, hit10 | Query indicator for at least one eligible positive at or before K |
| hrK_hits | Number of query hits, not a percentage unless the displayed table explicitly scales it |
| covered_pairs | Number of positive pairs in a candidate support |
| canonical_source | Typed normalized publication/source identifier; distinct from evidence-item ID |
| same_source | Confirmed intersection between actually consumed cutoff sources and eligible label sources |
| evidence_id / EID | CIViC evidence-item identifier, not a publication identifier |
| criterion | Drug- or source-linked connected-component partition |
| component_id | Connected component under the specified dependence criterion |
| round | One-based saved bootstrap/permutation replicate number |
| query_denominator | Actual number of query instances sampled in a bootstrap round |
| delta_mrr / delta_hitK | Paired method difference using the recorded query denominator |
| ci_lower_95, ci_upper_95 | Paired percentile confidence-interval endpoints |
| central95_lower, central95_upper | Conditional permutation distribution quantiles; not confidence intervals for a method difference |
| upper_tail_count | Number of 5,000 permutation values at least as large as observed |
| p_raw | Add-one upper-tail estimate (count+1)/5001 |
| p_holm_12 | Holm-adjusted value over the fixed 12-comparison family |
| displacement | Mix old-positive RR minus Graph RR, at full union positions |
| coverage_gain | Best Mix RR minus old-positive Mix RR |
| net_change | Mix RR minus Graph RR; equals displacement plus coverage_gain |
| k, alpha | RRF rank constant and graph weight in the saved 54-setting grid |

## Complete schema index

csv_schema_index.json records every distributed CSV's relative path, row count, fields and inferred storage types. csv_fields.csv gives one row per field occurrence. The table above defines shared scientific meanings; file-local names remain unchanged to preserve traceability.

NPZ files hold saved component draws, graph permutations or best-positive ranks. They are read with allow_pickle=False. JSON files hold settings, validation results and source/hash metadata. Model/vocabulary files in baseline_reference/models are archival inputs, not live training dependencies.

## Missing values and denominators

A missing source rank denotes absence from that source list. A missing positive rank denotes unretrieved relevance and contributes zero RR. Unknown unlabeled relevance is not silently treated as a negative clinical label. Development uses 41 queries/43 positive pairs; main replay 45/46; cutoff-defined 3/3 remains separate. Source exclusion removes overlapping labels only and leaves 39/39 at unchanged rankings.

Use qid for replay grouping and drug_norm for candidate identity. Source-exclusion and dependence analyses have different grouping/denominator rules; see reproducibility.md and artifact_map.md.
