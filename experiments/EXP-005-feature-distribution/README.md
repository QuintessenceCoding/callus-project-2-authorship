# EXP-005 - Feature Distribution Sanity Check

## Status

Completed.

## Scope

This experiment summarizes feature distributions for paired human and AI text from the DAIGT External dataset.

It does not:

- train a classifier
- select thresholds
- remove outliers
- promote or reject features
- modify raw data
- modify production/application code

## Dataset

- Source: `data/raw/daigt_external/daigt_external_dataset.csv`
- Columns used:
  - `id`: source row identifier
  - `text`: human/student writing
  - `source_text`: AI-generated text from the same source row
  - `instructions`: task/generation context, recorded only by character count
- Total scanned rows: `2421`
- Usable paired rows: `2421`
- Unusable rows: `0`
- Raw CSV SHA-256 before and after run: `3a1ba6c2ba557b83a13022efadb3239185cda05b50a9d31017fcf7967f33bb18`

## Sampling

- Target sample size: `200`
- Selected pair count: `200`
- Deterministic seed: `20260813`
- Pairing rule: each selected CSV row contributes one human text from `text` and one AI text from `source_text`
- Selected row indices and IDs are recorded in `results/results.json`

## Feature Implementation

EXP-005 reuses EXP-004 feature implementations:

- `sentence_length_cv`: `EXP-004` `sentence_length_cv`
- `mattr`: `EXP-004` `mattr`
- `pos_3gram_entropy`: `EXP-004` `pos_trigram_entropy`
- lexical tokenization: `EXP-004` `tokenize_for_lexical_features`
- perplexity: `EXP-001` `calculate_perplexity`, loaded through `EXP-004` `load_exp001_module`

Document-level perplexity is summarized as the median of valid sentence perplexities. This aggregation is recorded in `results.json`; it is a distribution-summary choice, not a detector threshold.

## Results

Results file: `results/results.json`

Runtime: `683.744290` seconds on CPU.

### Class Distribution Summary

| Feature | Class | Valid | Missing/abstained | Mean | Median | Stdev | IQR | Min | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| perplexity | human | 200 | 0 | 118.607749 | 98.196951 | 87.340346 | 56.245147 | 33.789711 | 799.672791 |
| perplexity | AI | 200 | 0 | 44.676744 | 42.932217 | 12.743399 | 14.562595 | 20.824144 | 120.996506 |
| sentence_length_cv | human | 199 | 1 | 0.527162 | 0.489799 | 0.179204 | 0.194288 | 0.153779 | 1.188102 |
| sentence_length_cv | AI | 200 | 0 | 0.300048 | 0.297963 | 0.089636 | 0.124705 | 0.053878 | 0.624626 |
| MATTR | human | 200 | 0 | 0.845757 | 0.850048 | 0.034253 | 0.043237 | 0.713290 | 0.916962 |
| MATTR | AI | 200 | 0 | 0.903339 | 0.905364 | 0.024655 | 0.029848 | 0.811667 | 0.947191 |
| POS 3-gram entropy | human | 200 | 0 | 7.236224 | 7.249802 | 0.393334 | 0.550990 | 6.267128 | 8.025335 |
| POS 3-gram entropy | AI | 200 | 0 | 6.631243 | 6.665574 | 0.325549 | 0.450480 | 5.821791 | 7.396942 |

### Human vs AI Summary

| Feature | Human median | AI median | Median diff, AI - human | Paired valid | Paired missing | Paired median diff | Cohen's d, AI - human | Range overlap | IQR overlap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| perplexity | 98.196951 | 42.932217 | -55.264734 | 200 | 0 | -53.462189 | -1.184548 | 0.111969 | 0.000000 |
| sentence_length_cv | 0.489799 | 0.297963 | -0.191836 | 199 | 1 | -0.211034 | -1.604178 | 0.415126 | 0.000000 |
| MATTR | 0.850048 | 0.905364 | 0.055316 | 200 | 0 | 0.056470 | 1.929558 | 0.450171 | 0.000000 |
| POS 3-gram entropy | 7.249802 | 6.665574 | -0.584228 | 200 | 0 | -0.609158 | -1.675681 | 0.512726 | 0.000000 |

### Paired Direction Counts

| Feature | AI > human | AI < human | AI = human |
| --- | ---: | ---: | ---: |
| perplexity | 12 | 188 | 0 |
| sentence_length_cv | 18 | 181 | 0 |
| MATTR | 190 | 10 | 0 |
| POS 3-gram entropy | 14 | 186 | 0 |

## Observations

- All four features produced valid values for both classes except human `sentence_length_cv`, where 1 of 200 human rows had insufficient sentence count for CV.
- The observed class medians differ for all four features in this paired sample.
- The observed IQR overlap ratio is `0.0` for all four features, while min-max ranges still overlap for all features.
- Outliers were retained. Human perplexity ranges up to `799.672791`; AI perplexity ranges up to `120.996506`.
- These observations describe this DAIGT External paired sample only. They do not establish thresholds, classifier performance, production evidence rules, or target-domain generalization.

## Validation

All validation checks passed:

- expected sample size reached
- selected row indices are unique
- selected row IDs are unique
- pair count equals selected count
- pair results match selected row indices and IDs
- raw dataset checksum unchanged
- finite feature values when present
- MATTR values in `[0, 1]`
- distribution summary counts match pair-level feature availability

Expected outputs:

- `experiments/EXP-005-feature-distribution/results/results.json`
- `experiments/EXP-005-feature-distribution/README.md`

## Decision

`PROCEED TO BASELINE MODELING`

EXP-005 supports continuing to a classifier/baseline experiment because the feature extraction pipeline produced measurable paired distributions with explicit overlap and validation. No feature is promoted or rejected from this experiment alone.

## Recommended Next Experiment

Run a bounded baseline experiment on paired data with explicit train/validation separation, starting with a perplexity-only baseline and then the four-feature set. Record accuracy-style metrics only after the split protocol is fixed, and keep threshold/model selection out of final test data.
