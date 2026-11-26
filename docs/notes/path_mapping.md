# Paths preserved in the final manuscript

The final main paper and companion are preserved without changing their scientific text or numbers. Their reproduction narrative refers in places to a pre-release working archive. The reorganized artifact uses these paths:

| Earlier working-archive path | Current release path |
| --- | --- |
| analysis_evidence/analysis_outputs/e0 ... e6 | data/processed/frozen_analysis/e0 ... e6 |
| analysis_evidence/analysis_outputs/archived_inputs | data/processed/frozen_analysis/archived_inputs |
| analysis_evidence/provenance/input_manifest.json | docs/notes/source_input_manifest.json |
| analysis_evidence/copy_manifest.json | docs/notes/source_copy_manifest.json |
| analysis_evidence/scripts/build_revision_tables.py | code/src/build_revision_tables.py |
| analysis_evidence/scripts/verify_evidence.py | code/src/verify_evidence.py |
| analysis_evidence/regenerated | code/results/reference/primary |
| Top-level reproduction command | python code/scripts/reproduce.py |

The old full local archive's run_experiments.py sequence requires original resources outside this portable release. It is not the command for this reorganized frozen-input artifact. The supported entry point, output scope and optional historical analyses are defined in the root README.

## Historical manifest paths

The preserved data/processed/baseline_reference/manifest/input_manifest.csv records paths relative to the earlier baseline repository. Replace its leading data/ with data/processed/baseline_reference/ to locate the identical current file. Its hashes remain original-resource provenance; MANIFEST.sha256.json is the authoritative current-tree inventory. Likewise, source_copy_manifest.json uses analysis_outputs/ for the former portable bundle, now data/processed/frozen_analysis/. These historical records are preserved rather than silently rewritten.
