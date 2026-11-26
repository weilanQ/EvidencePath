# Third-party sources and reconstruction boundary

This document preserves source identifiers and registered hashes from the baseline artifact while correcting its outdated prospective-discovery and runtime wording.

## Reproduction boundary

The bundled workflows use derived frozen candidate rankings, eligible positive labels, query-evidence records, saved diagnostic draws and summary artifacts. They do not include live raw feature extraction, LightGBM scoring/training, or a complete redistribution of the original biomedical databases. No GPU or database network call is needed for the supported scope.

The main 45-query/46-pair evaluation is retrospective later-annotation retrieval. Its cancer/profile descriptors are endpoint-defined while retrieval uses opening evidence. Three cutoff-defined queries/pairs are separate. The sealed pilot contains two eligible positives and no qualifying hard cases; it does not establish a formal prospective performance estimate.

## PrimeKG

- Official project: https://zitniklab.hms.harvard.edu/projects/PrimeKG/
- Harvard Dataverse identifier: https://doi.org/10.7910/DVN/IXA7BM
- Registered original kg.csv: 981,751,236 bytes.
- Registered SHA-256: 0a5a010fcd88dcec572a573d98c26c1c244a11567092b6161d3ded611cfb5c69.
- Role: graph-pool candidate retrieval through targets, indications and shared pathways.
- The complete original graph is not redistributed. Consult the upstream record for the applicable resource license and constituent-source terms; this release does not assign a replacement license.
- Frozen gene vocabulary, preserved for archival provenance: data/processed/baseline_reference/models/primekg_genes.json, SHA-256 c2d524ba4d887bd6d6fb62dce54fc6cbc8244d3de012f18dbc2f3376110358f1.

## CIViC

- Official downloads: https://civicdb.org/downloads
- Official licensing: https://civicdb.org/releases/licensing
- CIViC's official data-licensing page identifies its released data as CC0 1.0 Universal.
- Registered January 2026 snapshot: 01-Jan-2026-AcceptedClinicalEvidenceSummaries.tsv, 3,916,170 bytes; SHA-256 973a23cf7175a5942db2a21f093ec763a4df79baadb330afb5b8b9ce4b43443d.
- Registered July 2026 snapshot: 01-Jul-2026-AcceptedClinicalEvidenceSummaries.tsv, 4,085,714 bytes; SHA-256 7277812e373f9489f3232f032378b94dc50474307e476c4d07bb891d8e31ce33.
- Opening snapshots supply visible evidence; closing snapshots supply eligible annotation labels. Current live API responses are not historical substitutes.
- The source manifest and resource-version CSV retain the remaining graph/snapshot/mapping/model resource identities.

## Models and derived records

The frozen SF model is an archival LightGBM LambdaMART checkpoint: 4 trees, learning rate .05, 7 leaves, maximum depth 3, minimum leaf size 3, L2=1 and seed 7147. It uses five KG and three CIViC count features. The checkpoint is preserved in baseline_reference/models with SHA-256 40dfd92427aa99406f394bbef3870faaa4732872aef3a5faf55c7d15d6ccd0dc. AltGraph outputs are preserved in the frozen rank columns; the released one-command workflow does not retrain or rescore either model.

The 84 training pairs/31 queries and 16 validation pairs/seven queries have disjoint profiles. Candidate-specific label-EID exclusion is not publication-wide removal. Source overlap sensitivity also does not certify absence of every form of leakage.

## Licensing and source-document status

The baseline repository did not contain a project LICENSE file. This reorganization does not invent a new licensing decision. Upstream data terms and attribution should be checked at the listed official sources. The original internal GA09 reference PDF, personal working history and private contact details are not redistributed.

The LaTeX class in docs/papers/latex retains its upstream class header and provenance; third-party author names in scholarly citations are not identities of this artifact's anonymous authors.
