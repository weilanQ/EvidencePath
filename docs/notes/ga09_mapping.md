# GA09 organization mapping

GA09 is used as a project-organization reference. It is not an authorization to send artifacts to contacts or cloud services.

| GA09 location | Requirement | This release |
| --- | --- | --- |
| Pages 2-3, section 2.1 | Physically separate immutable data, source, configurations and outputs | data/raw, data/processed, code/src, code/configs, code/results |
| Page 2 | Never overwrite original data during processing | Manifest-checked immutable derived inputs; separate generated outputs |
| Pages 2-3 | Common code/docs/warehouse hierarchy and root README | Standard tree, with explicit empty notebook/slides/warehouse placeholders |
| Page 3, section 2.2 | Readable English names, underscores, vX.Y where applicable, YYYYMMDD dates | Stable permanent source filenames plus release_version 1.0 and release date 20261123 |
| Page 3, section 2.3 | Explain complex code inputs/outputs/parameters; record dependencies | Documented current/baseline scopes, pinned code/requirements.txt and environment configuration |
| Page 4, section 2.4 | Stranger-readable README: overview, environment, data, commands, FAQ and results | Root README and linked notes/data dictionary/artifact map |
| Page 5, section 2.5 | Organize, package and archive handoff materials | A versioned, manifest-selected research export; remote publishing is handled separately |

## Anonymous-review adaptations

GA09's author-initial filename suggestion and identified-contact row are not copied into the anonymous release. Identifying contact details are withheld during double-blind review. Private local paths, browser caches, internal chats and Git history are not artifact contents.

A separate machine-readable schema index, SHA-256 manifest and commit-pinned export are additional reproducibility practices, not claims of extra GA09 rules. No project license or raw-resource redistribution permission is inferred from GA09.

The internal reference PDF itself is not included.
