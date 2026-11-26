# EvidencePath

EvidencePath: Analyzing Candidate Coverage and Ranking in Cross-Cancer Drug Retrieval.

[Main paper](docs/papers/evidencepath_v1.0.pdf) | [Technical companion S1](docs/papers/supplement_s1_v1.0.pdf)

This release studies how candidate access, shared membership and source ordering relate to retrieval of later qualifying CIViC annotations. It follows a GA09-style separation of immutable derived inputs, runnable code, generated results and documentation.

## Start here

The main evaluation is a retrospective new-context replay: 45 query instances and 46 positive query-drug pairs. January development has 41 queries and 43 pairs. The three cutoff-defined queries/pairs and one augmentation are separate populations.

| Replay policy | Query MRR | HR@5 |
| --- | ---: | ---: |
| Context, same candidate union | 0.3460 | 27/45 |
| Shared-first Context control | 0.4265 | 27/45 |
| Standard RRF, frozen default | 0.3895 | 27/45 |

RRF's observed difference from Context is +0.0435, but both drug- and source-component 95% bootstrap intervals span zero. Shared-first is a post hoc diagnostic, not a validated new default; development reverses its ordering with RRF. These data concern annotation retrieval, not treatment efficacy or prospective discovery.

## Install and reproduce

Tested with Python 3.12.13 on Windows AMD64, using CPU only. The pinned runtime dependencies require Python 3.11 or newer; Python 3.12.13 is the tested version.

    python -m pip install -r code/requirements.txt
    python code/scripts/reproduce.py

The second command works from a clean downloaded artifact without the original workstation, a GitHub account, a GPU or database access. It writes new outputs to code/results/generated and verifies that all registered derived inputs remain unchanged.

For a complete static-file integrity check, run:

    python code/scripts/check_manifest.py

The reproduction command:
- recomputes ten policies per cohort, coverage, normalized Borda and the current seven-policy HR-at-K figure;
- reconstructs the historical interleaving ceilings, temporal endpoints and omission summaries;
- recomputes the 54-setting grid and checks it against the saved strong-baseline analysis;
- verifies 32 confidence intervals, all saved component-weighted paired means, 12 permutation tails/Holm values, 46 source-overlap classifications and 45 displacement identities.

It does not re-extract raw KG features, retrain models, or generate new bootstrap/graph-shuffle draws. Saved diagnostic draws and replicates are checked rather than presented as new independent experiments. Detailed scope and implementation are in [reproducibility.md](docs/notes/reproducibility.md).

Optional historical CIViC-shuffle rerun and legacy plots:

    python code/scripts/reproduce.py --with-live-baseline-shuffles

The historical five-policy HR plot is explicitly a baseline plot, not the current paper's Figure 2. Runtime is measured in the generated report; no hardware-independent speed claim is made.

## Directory map

| Path | Contents |
| --- | --- |
| [data/raw/](data/raw/) | Original-resource acquisition notes; no raw KG or complete snapshot redistribution |
| [data/processed/frozen_analysis/](data/processed/frozen_analysis/) | Current E0-E6 derived inputs and archived diagnostic evidence |
| [data/processed/baseline_reference/](data/processed/baseline_reference/) | Historical immutable inputs/checkpoints needed by labelled baseline workflows |
| [code/src/](code/src/) | Current artifact builder, independent verifier and baseline implementations |
| [code/scripts/reproduce.py](code/scripts/reproduce.py) | One-command orchestration |
| [code/configs/](code/configs/) | Frozen settings, tested environment and immutable-input hashes |
| [code/results/reference/](code/results/reference/) | Reference tables/figures; never overwritten |
| [code/results/generated/](code/results/generated/) | Fresh reproduction outputs and stage logs |
| [docs/notes/](docs/notes/) | Data dictionary, paper mapping, provenance, sources and reproduction details |
| [docs/papers/](docs/papers/) | Final main PDF, S1 and exact LaTeX source |
| [notebooks](code/notebooks/), [slides](docs/slides/), [warehouse](warehouse/) | Explicit empty placeholders; no private working history |

## Data preparation

No download is required for the supported frozen-ranking reproduction. The included candidate matrices, labels, query evidence, saved draws and summaries are derived research records, not copies of the original PrimeKG/CIViC databases.

For full source reconstruction, obtain the exact registered original resources separately and verify their hashes. Current live database responses are not substitutes for historical opening/endpoint snapshots. See [third-party sources](docs/notes/third_party_sources.md) and [raw-resource notes](data/raw/README.md). Full raw-source extraction/training is not an entry point of this release.

Core field meanings are in the [data dictionary](docs/notes/data_dictionary.md). The complete [CSV schema index](docs/notes/csv_schema_index.json) and [field listing](docs/notes/csv_fields.csv) enumerate all distributed CSV columns and row counts.

## Inspect results

Primary artifacts are in code/results/generated/primary. verification_report.json describes the numerical evidence checks; reproduction_report.json records completed stages and the immutable-input check. Historical outputs remain under generated/baseline.

The current [paper-to-code/data/output mapping](docs/notes/artifact_map.md) uses the final paper's table numbers; legacy filenames retain their original names only inside the baseline namespace.

## Troubleshooting

- Missing modules: install the pinned requirements using the same Python interpreter used for reproduction.
- Input checksum mismatch: restore the untouched distributed data; do not edit frozen evidence to make checks pass.
- Output path rejected: choose a generated-results directory, not data, docs, source or reference outputs.
- PDF timestamps differ: compare numeric tables or rendered figures rather than requiring byte-identical newly generated PDF metadata.
- Trying the old S1 working-directory commands: use this release's README; the [path mapping](docs/notes/path_mapping.md) explains the relocated historical paths.
- Need raw extraction or retraining: this release intentionally documents that separate boundary rather than claiming the included frozen-input commands perform it.

## Version, provenance and contact

RELEASE_v1.0.json records the scientific source run and baseline commit. MANIFEST.sha256.json inventories distributed file content; code/configs/immutable_inputs_v1.0.json defines protected derived inputs. Earlier repository states belong in Git history, not duplicated private folders.

Anonymous authors; identifying contact details are withheld during double-blind review.

No project license is invented by this reorganization. Third-party source and access notes are in [third_party_sources.md](docs/notes/third_party_sources.md).
