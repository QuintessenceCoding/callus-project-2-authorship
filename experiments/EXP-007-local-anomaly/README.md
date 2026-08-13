# EXP-007 - Hybrid Local-Anomaly Feasibility

## Status

Completed.

## Scope

This is a bounded synthetic hybrid experiment. It tests whether a known AI-written passage inserted into an otherwise human DAIGT essay tends to receive a high within-document local anomaly score.

It does not:

- implement the production local-anomaly scorer
- train a classifier
- create thresholds
- process the full DAIGT dataset
- model every form of real AI-assisted writing
- establish admissions-domain performance
- modify raw data or application code

## Inputs

- Raw dataset: `data/raw/daigt_external/daigt_external_dataset.csv`
- Dataset semantics:
  - `text`: human/student-written text
  - `source_text`: AI-generated text
  - `instructions`: shared task/generation context
- Source selection: first 20 `pair_results` from `experiments/EXP-005-feature-distribution/results/results.json`
- No resampling and no new random seed.

Selected pair IDs:

```text
616C3D5795E8
61E85C09E36D
62E5030D1A59
638D7F913AAB
63E2278271E4
642CB997325C
653620381DB3
65B7FDE783F2
674F5DA988D2
67D58F9FA53C
68004683BC3C
69241D10E69A
694C96A1E9A0
6AB122D640E1
6B3B3CB54EB9
6CD1B8B6BEA8
6D6E937C3A67
6E90DC70B7A9
6F30733E6B4B
6FEF6D46714D
```

Raw CSV SHA-256 before and after the run:

```text
3a1ba6c2ba557b83a13022efadb3239185cda05b50a9d31017fcf7967f33bb18
```

## Hybrid Construction

For each selected pair:

- Segment the human `text` into sentences with the EXP-004 spaCy model.
- Segment the AI `source_text` into sentences with the same spaCy model.
- Require at least 2 human sentences and at least 3 AI sentences.
- Select exactly 2 contiguous AI sentences from the middle of the AI text.
- Insert that AI block at human sentence boundary `floor(human_sentence_count / 2)`.
- Preserve the segmented human sentence order and the selected AI sentence strings.

Ground-truth inserted AI sentence indices are recorded as zero-based hybrid sentence indices in `results/results.json`.

## Feature Reuse

EXP-007 reuses EXP-004/EXP-001 implementations:

- sentence segmentation: spaCy `en_core_web_sm` from EXP-004
- perplexity: EXP-001 `calculate_perplexity`, loaded through EXP-004
- lexical tokenization: EXP-004 `tokenize_for_lexical_features`
- MATTR: EXP-004 `mattr`, window size `25`
- POS 3-gram entropy: EXP-004 `pos_trigram_entropy`

For each hybrid sentence:

- sentence perplexity is computed on the sentence itself
- sentence length is the spaCy token count excluding space and punctuation
- local MATTR is computed on a sentence window
- local POS 3-gram entropy is computed on the same sentence window

Window behavior:

- interior sentences use `[i-1, i, i+1]`
- the first sentence uses `[0, 1]`
- the last sentence uses `[n-2, n-1]`

## Robust Anomaly Definition

For each feature, EXP-007 compares a sentence/window value to other sentence/window values in the same hybrid essay:

```text
robust_z = 0.6745 * (value - median(reference_values)) / MAD(reference_values)
```

The reference set excludes the current sentence/window. If `MAD == 0`, that component z-score is unavailable and no value is fabricated.

The experimental local anomaly score is:

```text
mean(abs(available component z-scores))
```

This is a ranking score only. No production threshold is introduced.

## Results

Results file: `results/results.json`

Runtime: `46.854110` seconds.

### Construction Summary

| Measure | Value |
| --- | ---: |
| Selected pairs | 20 |
| Eligible pairs | 20 |
| Successful hybrids | 20 |
| Rejected pairs | 0 |
| Total inserted AI sentences | 40 |

### Aggregate Capture

| Capture band | Rate | Count |
| --- | ---: | ---: |
| Top 50% | 0.550 | 22 / 40 |
| Top 25% | 0.150 | 6 / 40 |
| Top 10% | 0.025 | 1 / 40 |

### AI vs Human Anomaly Scores

| Class | Count | Mean | Median | Stdev | IQR | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Inserted AI sentences | 40 | 1.032682 | 0.977125 | 0.461367 | 0.614979 | 0.312276 | 2.184944 |
| Human sentences | 383 | 3.422957 | 0.869977 | 44.140034 | 0.719832 | 0.154095 | 864.776786 |

Median difference, AI minus human: `0.107147`.

The human mean and maximum are dominated by retained high-anomaly human outliers. No outliers were removed.

### Per-Hybrid Summary

| Pair ID | Hybrid sentences | AI indices | AI ranks | Top 50 count | Top 25 count | Top 10 count | AI median | Human median | Human above least AI |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 616C3D5795E8 | 10 | [4, 5] | [6, 4] | 1 | 0 | 0 | 1.450332 | 1.117743 | 4 |
| 61E85C09E36D | 12 | [5, 6] | [12, 8] | 0 | 0 | 0 | 0.732415 | 1.414686 | 10 |
| 62E5030D1A59 | 27 | [12, 13] | [27, 13] | 1 | 0 | 0 | 0.675648 | 0.899227 | 25 |
| 638D7F913AAB | 26 | [12, 13] | [12, 11] | 2 | 0 | 0 | 1.007004 | 0.855000 | 10 |
| 63E2278271E4 | 10 | [4, 5] | [4, 8] | 1 | 0 | 0 | 0.921764 | 1.014041 | 6 |
| 642CB997325C | 26 | [12, 13] | [2, 7] | 2 | 2 | 1 | 1.879115 | 0.906292 | 5 |
| 653620381DB3 | 13 | [5, 6] | [4, 8] | 1 | 1 | 0 | 1.239741 | 0.845132 | 6 |
| 65B7FDE783F2 | 17 | [7, 8] | [6, 4] | 2 | 1 | 0 | 2.079948 | 1.130489 | 4 |
| 674F5DA988D2 | 8 | [3, 4] | [3, 5] | 1 | 0 | 0 | 1.059415 | 0.842025 | 3 |
| 67D58F9FA53C | 24 | [11, 12] | [18, 20] | 0 | 0 | 0 | 0.679010 | 0.853940 | 18 |
| 68004683BC3C | 35 | [16, 17] | [18, 10] | 2 | 0 | 0 | 0.807683 | 0.666560 | 16 |
| 69241D10E69A | 12 | [5, 6] | [5, 4] | 2 | 0 | 0 | 0.976196 | 0.616309 | 3 |
| 694C96A1E9A0 | 36 | [17, 18] | [30, 19] | 0 | 0 | 0 | 0.692668 | 0.819467 | 28 |
| 6AB122D640E1 | 22 | [10, 11] | [8, 7] | 2 | 0 | 0 | 1.290338 | 0.856212 | 6 |
| 6B3B3CB54EB9 | 28 | [13, 14] | [8, 24] | 1 | 0 | 0 | 0.862444 | 1.062887 | 22 |
| 6CD1B8B6BEA8 | 22 | [10, 11] | [17, 14] | 0 | 0 | 0 | 0.631045 | 0.817576 | 15 |
| 6D6E937C3A67 | 23 | [10, 11] | [19, 22] | 0 | 0 | 0 | 0.761987 | 1.193419 | 20 |
| 6E90DC70B7A9 | 13 | [5, 6] | [4, 6] | 2 | 1 | 0 | 1.174435 | 0.922109 | 4 |
| 6F30733E6B4B | 29 | [13, 14] | [5, 9] | 2 | 1 | 0 | 1.238889 | 0.713519 | 7 |
| 6FEF6D46714D | 30 | [14, 15] | [30, 23] | 0 | 0 | 0 | 0.493559 | 0.841632 | 28 |

## Observations

- All first-20 EXP-005 pairs satisfied the construction requirements.
- Inserted AI sentences were captured in the top half of anomaly rankings in 22 of 40 cases.
- Top-quarter and top-tenth capture were much lower: 6 of 40 and 1 of 40.
- Aggregate inserted-AI median anomaly was slightly higher than aggregate human median anomaly.
- The sentence-level distributions overlap substantially, and some human sentences received much larger anomaly scores than the inserted AI sentences.

These observations are not detection accuracy and do not establish thresholds.

## Validation

All validation checks passed:

- no duplicate pair IDs
- raw dataset unchanged
- every hybrid has exactly 2 inserted AI sentences
- inserted AI text matches the selected source-text sentence strings
- ground-truth indices are valid
- human sentence sequence is preserved
- finite anomaly values are finite
- unavailable features have explicit reasons
- result counts are internally consistent

## Decision

`PROCEED WITH REVISION`

The within-document robust anomaly idea is feasible to compute and sometimes ranks inserted AI sentences relatively high, but the observed overlap and high human outliers mean this exact experimental score is not sufficient as a standalone detector.

## Recommended Next Experiment

Run a local-window sensitivity experiment comparing window sizes and component feature contributions on the same synthetic hybrids before considering any production scoring design.
